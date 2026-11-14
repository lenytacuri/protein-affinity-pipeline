"""Parallel backbone extraction from original structures, followed by dbt summaries."""
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
from datetime import datetime,timezone
import fcntl
import gzip
import json
import os
from pathlib import Path
import re
import time
from dotenv import load_dotenv

from backbone_core import calculate_backbone,PARAMETERS,MEASUREMENTS
from geometry_core import digest_file
from check_snowflake import connect
from run_bronze import fingerprints,RAW_TABLES,TABLES as BRONZE_TABLES
from run_silver import run_dbt,SILVER_TABLES,available_cpus,canonical_hash,Shards

ROOT=Path(__file__).resolve().parents[1]
TABLES=('BACKBONE_RESIDUES','BACKBONE_FEATURES')


def source_fingerprints():
    return {'RAW':fingerprints('RAW',RAW_TABLES),'BRONZE':fingerprints('BRONZE',BRONZE_TABLES),'SILVER':fingerprints('SILVER',SILVER_TABLES)}


def inputs(cache,code_sha):
    with connect() as conn,conn.cursor() as cur:
        cur.execute((ROOT/'sql/11_backbone_inputs.sql').read_text())
        rows=cur.fetchall()
    jobs=[];files={}
    for gid,pdb,sha,residues in rows:
        if not re.fullmatch('[a-f0-9]{64}',sha):raise ValueError('Invalid structure hash')
        residues=json.loads(residues) if isinstance(residues,str) else residues
        identity={'geometry_id':gid,'structure_sha256':sha,'residues':residues,'code_sha256':code_sha,'parameters':PARAMETERS}
        path=ROOT/'data/rcsb/objects'/f'{sha}.cif.gz';files[sha]=path
        jobs.append(dict(identity,pdb_id=pdb,job_key=canonical_hash(identity),path=str(path),cache=str(cache)))
    with connect() as conn,conn.cursor() as cur:
        for sha,path in files.items():
            if not path.exists() or digest_file(path)!=sha:
                path.parent.mkdir(parents=True,exist_ok=True)
                uri=('file://'+str(path.parent)).replace("'","''")
                cur.execute(f"GET @RAW.SOURCE_FILES/objects/{sha}.cif.gz '{uri}' PARALLEL=8");cur.fetchall()
                if not path.exists() or digest_file(path)!=sha:raise ValueError('Structure integrity failed')
    if len({j['geometry_id'] for j in jobs})!=len(jobs):raise ValueError('Duplicate geometry inputs')
    return jobs


def upload(artifacts,prefix,manifest):
    with connect() as conn,conn.cursor() as cur:
        cur.execute('CREATE STAGE IF NOT EXISTS SILVER.BACKBONE_FILES')
        cur.execute('CREATE FILE FORMAT IF NOT EXISTS SILVER.BACKBONE_JSON TYPE=JSON STRIP_NULL_VALUES=FALSE')
        uri=('file://'+str(artifacts/'backbone_*.jsonl.gz')).replace("'","''")
        cur.execute(f"PUT '{uri}' @SILVER.BACKBONE_FILES/{prefix}/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE PARALLEL=8")
        keys=[c[0].lower() for c in cur.description];statuses=[dict(zip(keys,r)) for r in cur.fetchall()]
        if len(statuses)!=len(manifest['files']) or any(r['status'] not in ('UPLOADED','SKIPPED') for r in statuses):raise ValueError('Incomplete upload')
        cur.execute(f"SELECT COUNT(*) FROM @SILVER.BACKBONE_FILES/{prefix}/ (FILE_FORMAT=>'SILVER.BACKBONE_JSON',PATTERN=>'.*backbone_[0-9]+[.]jsonl[.]gz')")
        if cur.fetchone()[0]!=manifest['rows']:raise ValueError('Stage row count mismatch')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pilot',type=int,default=0);args=parser.parse_args()
    load_dotenv(ROOT/'.env');key=Path(os.environ['SNOWFLAKE_PRIVATE_KEY_FILE']);os.environ['DBT_PRIVATE_KEY_PATH']=str(key if key.is_absolute() else ROOT/key)
    out=ROOT/'reports/backbone';out.mkdir(parents=True,exist_ok=True)
    with (ROOT/'reports/silver/.build.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        run=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');folder=out/run;folder.mkdir();start=time.monotonic()
        try:
            before=source_fingerprints()
            code_sha=canonical_hash({p:digest_file(ROOT/p) for p in ['scripts/backbone_core.py','geometry/requirements.txt']})
            cache=ROOT/'data/backbone/cache';jobs=inputs(cache,code_sha)
            if args.pilot:jobs=jobs[:args.pilot]
            workers=available_cpus();results={};compute_start=time.monotonic()
            print(f'{len(jobs)} geometrias; {sum(len(j["residues"]) for j in jobs)} residuos Q1; {workers} procesos CPU',flush=True)
            with ProcessPoolExecutor(max_workers=workers) as pool:
                futures=[pool.submit(calculate_backbone,j) for j in jobs]
                for i,future in enumerate(as_completed(futures),1):
                    r=future.result();results[r['geometry_id']]=r
                    if i%200==0 or i==len(jobs):print(f'Backbone {i}/{len(jobs)}',flush=True)
            computation={'run':run,'workers':workers,'geometries':len(jobs),'residues':sum(r['rows'] for r in results.values()),'compute_seconds':round(time.monotonic()-compute_start,2),'parameters':PARAMETERS,'code_sha256':code_sha}
            (folder/'computation.json').write_text(json.dumps(computation,indent=2));print(json.dumps(computation,indent=2),flush=True)
            if args.pilot:return
            prefix=canonical_hash({'jobs':sorted(j['job_key'] for j in jobs),'code':code_sha})
            artifacts=ROOT/'data/backbone/runs'/prefix;artifacts.mkdir(parents=True,exist_ok=True);writer=Shards(artifacts,'backbone')
            for gid in sorted(results):
                with gzip.open(results[gid]['path'],'rb') as f:
                    for line in f:writer.add(line)
            manifest=writer.close();(artifacts/'manifest.json').write_text(json.dumps(manifest,indent=2))
            if manifest['rows']!=computation['residues']:raise ValueError('Lost residue rows')
            upload(artifacts,prefix,manifest)
            latest=json.loads((ROOT/'reports/silver/latest.json').read_text())['run']
            geometry_prefix=json.loads((ROOT/'reports/silver'/latest/'summary.json').read_text())['geometry_prefix']
            for command,label in [(['build'],'build'),(['build'],'replay'),(['docs','generate'],'docs')]:
                run_dbt(folder,geometry_prefix,command,label,'tag:backbone',{'backbone_prefix':prefix})
                if label=='build':first=fingerprints('SILVER',TABLES)
                if label=='replay' and fingerprints('SILVER',TABLES)!=first:raise ValueError('Backbone replay content changed')
            if before!=source_fingerprints():raise ValueError('Parent tables changed')
            build=json.loads((folder/'build_run_results.json').read_text())['results'];tests=[r for r in build if r['unique_id'].startswith('test.')]
            with connect() as conn,conn.cursor() as cur:
                cur.execute('SELECT BACKBONE_STATUS,COUNT(*) FROM SILVER.BACKBONE_FEATURES GROUP BY 1');statuses=dict(cur.fetchall())
                cur.execute('SELECT COUNT(*),COUNT(PHI_DEG),COUNT(PSI_DEG),COUNT(OMEGA_DEG),COUNT(TAU_DEG),COUNT(N_CA_LENGTH),COUNT(CA_C_LENGTH),COUNT(PEPTIDE_CN_LENGTH) FROM SILVER.BACKBONE_RESIDUES')
                coverage=dict(zip(['residues',*MEASUREMENTS],cur.fetchone()))
                reasons={}
                for angle in ['phi','psi','omega','tau']:
                    cur.execute(f'SELECT {angle}_STATUS,COUNT(*) FROM SILVER.BACKBONE_RESIDUES GROUP BY 1');reasons[angle]=dict(cur.fetchall())
            summary=dict(computation,status='SUCCESS',tables=first,backbone_prefix=prefix,tests=len(tests),tests_passed=sum(r['status']=='pass' for r in tests),parent_tables_unchanged=True,replay_verified=True,coverage=coverage,statuses=statuses,reasons=reasons,seconds=round(time.monotonic()-start,2))
            (folder/'summary.json').write_text(json.dumps(summary,indent=2));(out/'latest.json').write_text(json.dumps({'run':run}))
            from backbone_report import write_report
            write_report(summary)
            print(json.dumps(summary,indent=2),flush=True)
        except Exception as exc:
            (folder/'failure.json').write_text(json.dumps({'error':str(exc),'run':run},indent=2));raise

if __name__=='__main__':main()
