"""Build a reproducible Gold star schema from existing Silver; no feature recomputation."""
from datetime import datetime,timezone
import fcntl
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from check_snowflake import connect
from run_bronze import fingerprints,RAW_TABLES,TABLES as BRONZE_TABLES
from run_silver import run_dbt,SILVER_TABLES
from build_backbone import TABLES as BACKBONE_TABLES

ROOT=Path(__file__).resolve().parents[1]
TABLES=('DIM_SOURCE','DIM_EXPERIMENT','DIM_GEOMETRY','DIM_PARTICIPANT_FEATURES','FACT_AFFINITY')

def parents():
    return {'RAW':fingerprints('RAW',RAW_TABLES),'BRONZE':fingerprints('BRONZE',BRONZE_TABLES),
            'SILVER':fingerprints('SILVER',(*SILVER_TABLES,*BACKBONE_TABLES))}

def latest_summary(layer):
    run=json.loads((ROOT/'reports'/layer/'latest.json').read_text())['run']
    return json.loads((ROOT/'reports'/layer/run/'summary.json').read_text())

def main():
    load_dotenv(ROOT/'.env')
    key=Path(os.environ['SNOWFLAKE_PRIVATE_KEY_FILE'])
    os.environ['DBT_PRIVATE_KEY_PATH']=str(key if key.is_absolute() else ROOT/key)
    out=ROOT/'reports/gold';out.mkdir(parents=True,exist_ok=True)
    with (ROOT/'reports/silver/.build.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        run=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');folder=out/run;folder.mkdir()
        try:
            silver=latest_summary('silver');backbone=latest_summary('backbone')
            before=parents()
            for label in ('build','replay'):
                run_dbt(folder,silver['geometry_prefix'],['build'],label,'tag:gold',{'backbone_prefix':backbone['backbone_prefix']})
                if label=='build':first=fingerprints('GOLD',TABLES)
                elif first!=fingerprints('GOLD',TABLES):raise ValueError('Gold replay changed content')
            run_dbt(folder,silver['geometry_prefix'],['docs','generate'],'docs','tag:gold',{'backbone_prefix':backbone['backbone_prefix']})
            after=parents()
            if before!=after:raise ValueError('Input tables changed during Gold build')
            results=json.loads((folder/'build_run_results.json').read_text())['results']
            tests=[r for r in results if r['unique_id'].startswith('test.')]
            with connect() as conn,conn.cursor() as cur:
                cur.execute("SELECT TABLE_NAME,COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='GOLD' GROUP BY 1")
                columns=dict(cur.fetchall())
                cur.execute('SELECT GEOMETRY_STATUS,COUNT(*) FROM GOLD.FACT_AFFINITY GROUP BY 1')
                statuses=dict(cur.fetchall())
                cur.execute('SELECT COUNT(*),COUNT(DISTINCT OBSERVATION_ID),COUNT_IF(GEOMETRY_ID IS NULL),COUNT_IF(HAS_VALID_LABEL),COUNT_IF(NEEDS_VARIANT_REVIEW) FROM GOLD.FACT_AFFINITY')
                facts=dict(zip(['observations','unique_ids','no_geometry_key','valid_labels','variant_review'],cur.fetchone()))
                cur.execute("SELECT COUNT(*) FROM GOLD.FACT_AFFINITY f LEFT JOIN GOLD.DIM_SOURCE s USING(SOURCE_KEY) LEFT JOIN GOLD.DIM_EXPERIMENT e USING(EXPERIMENT_KEY) LEFT JOIN GOLD.DIM_GEOMETRY g ON f.GEOMETRY_ID=g.GEOMETRY_ID LEFT JOIN GOLD.DIM_PARTICIPANT_FEATURES l ON f.LIGAND_PARTICIPANT_KEY=l.PARTICIPANT_KEY LEFT JOIN GOLD.DIM_PARTICIPANT_FEATURES r ON f.RECEPTOR_PARTICIPANT_KEY=r.PARTICIPANT_KEY")
                joined=cur.fetchone()[0]
            if facts['observations']!=before['SILVER']['AFFINITY_OBSERVATIONS']['rows'] or joined!=facts['observations']:raise ValueError('Observation count changed')
            summary={'run':run,'status':'SUCCESS','tables':first,'columns':columns,'tests':len(tests),'tests_passed':sum(t['status']=='pass' for t in tests),
                'parents_unchanged':True,'replay_verified':True,'facts':facts,'joined_rows':joined,'geometry_statuses':statuses,
                'source_silver_run':silver['run'],'source_backbone_run':backbone['run'],'parent_fingerprints':before}
            (folder/'summary.json').write_text(json.dumps(summary,indent=2))
            (out/'latest.json').write_text(json.dumps({'run':run}))
            from gold_report import write_report
            write_report(summary)
            print(json.dumps(summary,indent=2),flush=True)
        except Exception as exc:
            (folder/'failure.json').write_text(json.dumps({'run':run,'error':str(exc)},indent=2));raise

if __name__=='__main__':main()
