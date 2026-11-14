"""Export Gold, join with local Spark, validate and atomically publish the OBT."""
from datetime import datetime,timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from dotenv import load_dotenv
import pyarrow.parquet as pq
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from check_snowflake import connect
from run_bronze import fingerprints,RAW_TABLES,TABLES as BRONZE_TABLES
from run_silver import SILVER_TABLES,available_cpus
from build_backbone import TABLES as BACKBONE_TABLES
from build_gold import TABLES as GOLD_TABLES
from obt_transform import TABLES,KEYS,JOINS,projection,validate_inputs,assemble,validate_output


def ident(value):
    if not re.fullmatch('[A-Z][A-Z0-9_]*',value):raise ValueError('Unsafe identifier')
    return '"'+value+'"'

def parents():
    return {'RAW':fingerprints('RAW',RAW_TABLES),'BRONZE':fingerprints('BRONZE',BRONZE_TABLES),
      'SILVER':fingerprints('SILVER',(*SILVER_TABLES,*BACKBONE_TABLES)),'GOLD':fingerprints('GOLD',GOLD_TABLES)}

def export_gold(folder):
    columns={};types={};manifest={}
    with connect() as conn,conn.cursor() as cur:
        for table in GOLD_TABLES:
            cur.execute("SELECT COLUMN_NAME,DATA_TYPE,NUMERIC_PRECISION,NUMERIC_SCALE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='GOLD' AND TABLE_NAME=%s ORDER BY ORDINAL_POSITION",(table,))
            meta=cur.fetchall();columns[table]=[r[0] for r in meta];types[table]={}
            for name,typ,precision,scale in meta:
                types[table][name]=f'NUMBER({precision},{scale})' if typ=='NUMBER' else {'TEXT':'VARCHAR','FLOAT':'DOUBLE','BOOLEAN':'BOOLEAN'}[typ]
            target=folder/table;target.mkdir(parents=True)
            cur.execute('SELECT '+','.join(ident(c) for c in columns[table])+' FROM GOLD.'+ident(table))
            count=0;files=[]
            for i,batch in enumerate(cur.fetch_arrow_batches()):
                path=target/f'part-{i:05}.parquet';pq.write_table(batch,path,compression='snappy');count+=batch.num_rows
                files.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
            if not files:raise ValueError('Empty Gold table: '+table)
            manifest[table]={'rows':count,'files':files}
    return columns,types,manifest

def expected_sql(mapping):
    fields=','.join(m['alias']+'.'+ident(m['column'])+' AS '+ident(m['output']) for m in mapping)
    query='SELECT '+fields+' FROM GOLD.FACT_AFFINITY f'
    for alias,fk,pk in JOINS:query+=' LEFT JOIN GOLD.'+TABLES[alias]+' '+alias+' ON f.'+ident(fk)+'='+alias+'.'+ident(pk)
    return query

def validate_snowflake(cur,table,mapping,expected_rows):
    cur.execute(f'SELECT COUNT(*),COUNT(DISTINCT OBSERVATION_ID),COUNT_IF(OBSERVATION_ID IS NULL),HASH_AGG(*) FROM ANALYTICS.{ident(table)}')
    count,unique,nulls,digest=cur.fetchone()
    if count!=expected_rows or unique!=expected_rows or nulls:raise ValueError('Loaded OBT cardinality failed')
    fields=','.join(ident(m['output']) for m in mapping)
    expected=expected_sql(mapping)
    # SQL is an independent audit of Spark output, not the transformation used to build it.
    for left,right in [(f'SELECT {fields} FROM ANALYTICS.{ident(table)}',expected),(expected,f'SELECT {fields} FROM ANALYTICS.{ident(table)}')]:
        cur.execute('SELECT COUNT(*) FROM (('+left+') MINUS ('+right+'))')
        if cur.fetchone()[0]:raise ValueError('Loaded values differ from Gold, including NULL or decimals')
    return {'rows':count,'unique_ids':unique,'hash':digest,'all_columns_equal_to_gold_join':True}

def load_candidate(output,run,mapping,types,rows):
    table='OBT_BUILD_'+run.upper();stage='OBT_FILES'
    with connect() as conn,conn.cursor() as cur:
        cur.execute('CREATE STAGE IF NOT EXISTS ANALYTICS.'+stage)
        cur.execute('CREATE FILE FORMAT IF NOT EXISTS ANALYTICS.OBT_PARQUET TYPE=PARQUET USE_LOGICAL_TYPE=TRUE BINARY_AS_TEXT=FALSE NULL_IF=()')
        defs=','.join(ident(m['output'])+' '+types[m['table']][m['column']] for m in mapping)
        cur.execute('CREATE TABLE ANALYTICS.'+ident(table)+' ('+defs+')')
        uri=('file://'+str(output/'part-*.parquet')).replace("'","''")
        cur.execute(f"PUT '{uri}' @ANALYTICS.{stage}/{run}/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE PARALLEL=8")
        labels=[c[0].lower() for c in cur.description];status=[dict(zip(labels,r)) for r in cur.fetchall()]
        if len(status)!=len(list(output.glob('part-*.parquet'))) or any(r['status'] not in ('UPLOADED','SKIPPED') for r in status):raise ValueError('Incomplete Parquet upload')
        cur.execute(f"COPY INTO ANALYTICS.{ident(table)} FROM @ANALYTICS.{stage}/{run}/ FILE_FORMAT=(FORMAT_NAME='ANALYTICS.OBT_PARQUET') MATCH_BY_COLUMN_NAME=CASE_SENSITIVE ON_ERROR=ABORT_STATEMENT")
        copy=cur.fetchall()
        validated=validate_snowflake(cur,table,mapping,rows)
        return table,validated

def main():
    load_dotenv(ROOT/'.env')
    out=ROOT/'reports/obt';out.mkdir(parents=True,exist_ok=True)
    with (ROOT/'reports/silver/.build.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        run=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');report=out/run;report.mkdir()
        data=ROOT/'data/obt'/run;data.mkdir(parents=True)
        spark=None;started=time.monotonic()
        try:
            before=parents()
            columns,types,manifest=export_gold(data/'inputs')
            if fingerprints('GOLD',GOLD_TABLES)!=before['GOLD']:raise ValueError('Gold changed during export')
            for t,v in manifest.items():
                if v['rows']!=before['GOLD'][t]['rows']:raise ValueError('Incomplete export: '+t)
            mapping=projection(columns)
            (report/'input_manifest.json').write_text(json.dumps(manifest,indent=2))
            (report/'column_lineage.json').write_text(json.dumps(mapping,indent=2))
            workers=available_cpus();master=os.getenv('SPARK_MASTER',f'local[{workers}]')
            partitions=int(os.getenv('SPARK_SHUFFLE_PARTITIONS',str(workers)))
            events=report/'spark-events';events.mkdir()
            spark=(SparkSession.builder.master(master).appName('protein-affinity-obt')
              .config('spark.sql.shuffle.partitions',str(partitions))
              .config('spark.sql.adaptive.enabled','true')
              .config('spark.sql.session.timeZone','UTC')
              .config('spark.ui.enabled','false')
              .config('spark.eventLog.enabled','true').config('spark.eventLog.dir','file://'+str(events))
              .config('spark.sql.debug.maxToStringFields','400').getOrCreate())
            spark.sparkContext.setLogLevel('WARN')
            print(f'Spark {spark.version}, {spark.sparkContext.master}, parallelism={spark.sparkContext.defaultParallelism}',flush=True)
            frames={t:spark.read.parquet(str(data/'inputs'/t)) for t in GOLD_TABLES}
            counts=validate_inputs(frames)
            obt=assemble(frames,mapping).persist()
            checks=validate_output(obt,frames['FACT_AFFINITY'])
            (report/'spark_plan.txt').write_text(obt._jdf.queryExecution().toString())
            # Rebuild after changing input partitioning. Do not reuse the joined output.
            replay=assemble({t:df.repartition(max(2,partitions//2)) for t,df in frames.items()},mapping)
            if obt.exceptAll(replay).limit(1).count() or replay.exceptAll(obt).limit(1).count():raise ValueError('Spark replay differs')
            output=data/'output';obt.repartition(partitions,'OBSERVATION_ID').write.mode('errorifexists').parquet(str(output))
            roundtrip=spark.read.parquet(str(output))
            if obt.exceptAll(roundtrip).limit(1).count() or roundtrip.exceptAll(obt).limit(1).count():raise ValueError('Parquet changed data')
            (report/'spark_schema.json').write_text(obt.schema.json())
            spark_version=spark.version;parallelism=spark.sparkContext.defaultParallelism
            obt.unpersist();spark.stop();spark=None
            candidate,loaded=load_candidate(output,run,mapping,types,checks['rows'])
            if before!=parents():raise ValueError('Input tables changed before publication')
            previous=None
            if (out/'latest.json').exists():
                prior_run=json.loads((out/'latest.json').read_text())['run']
                previous=json.loads((out/prior_run/'summary.json').read_text())
                if previous['parent_fingerprints']==before and previous['column_lineage']==mapping and previous['loaded']['hash']!=loaded['hash']:
                    raise ValueError('Same inputs produced different OBT content')
            with connect() as conn,conn.cursor() as cur:
                # Atomic publication: readers keep the previous OBT until the validated clone is ready.
                cur.execute(f'CREATE OR REPLACE TABLE ANALYTICS.OBT_AFFINITY CLONE ANALYTICS.{ident(candidate)} COPY GRANTS')
                cur.execute('SELECT COUNT(*),HASH_AGG(*) FROM ANALYTICS.OBT_AFFINITY')
                published=cur.fetchone()
                if published!=(loaded['rows'],loaded['hash']):raise ValueError('Publication differs from candidate')
                cur.execute('DROP TABLE ANALYTICS.'+ident(candidate))
            summary={'run':run,'status':'SUCCESS','table':'PROTEIN_AFFINITY.ANALYTICS.OBT_AFFINITY',
              'rows':checks['rows'],'columns':len(mapping),'spark_version':spark_version,'master':master,'parallelism':parallelism,
              'input_counts':counts,'spark_checks':checks,'spark_replay_identical':True,'parquet_roundtrip_identical':True,
              'loaded':loaded,'parents_unchanged':True,'parent_fingerprints':before,'column_lineage':mapping,
              'previous_same_inputs_verified':bool(previous and previous['parent_fingerprints']==before),
              'seconds':round(time.monotonic()-started,2)}
            (report/'summary.json').write_text(json.dumps(summary,indent=2));(out/'latest.json').write_text(json.dumps({'run':run}))
            from obt_report import write_report
            write_report(summary)
            print(json.dumps({k:v for k,v in summary.items() if k not in ('column_lineage','parent_fingerprints')},indent=2),flush=True)
        except Exception as exc:
            (report/'failure.json').write_text(json.dumps({'run':run,'error':str(exc)},indent=2));raise
        finally:
            if spark is not None:spark.stop()

if __name__=='__main__':main()
