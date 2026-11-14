"""Extrae geometria en CPU local, conserva originales y construye Silver con dbt.

--pilot N calcula N grupos sin publicar tablas. Sin --pilot procesa todo Bronze.
Los artefactos se cachean por contenido estructural, cadenas, codigo y parametros.
"""
import argparse
from collections import Counter,defaultdict
from concurrent.futures import ProcessPoolExecutor,as_completed
from datetime import datetime,timezone
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

from dotenv import load_dotenv
from check_snowflake import connect
from geometry_core import PARAMETERS,parse_chains,digest_file,calculate_job,mutation_check
from run_bronze import fingerprints,RAW_TABLES,TABLES as BRONZE_TABLES

ROOT=Path(__file__).resolve().parents[1]
SILVER_TABLES=('AFFINITY_OBSERVATIONS','OBSERVATION_GEOMETRY','STRUCTURE_GEOMETRY','INTERFACE_RESIDUES','RESIDUE_PAIRS','INTERFACE_CHEMISTRY')


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def available_cpus():
    cores=len(os.sched_getaffinity(0)) if hasattr(os,'sched_getaffinity') else os.cpu_count() or 1
    quota=Path('/sys/fs/cgroup/cpu.max')
    if quota.exists():
        amount,period=quota.read_text().split()
        if amount!='max': cores=min(cores,max(1,int(amount)//int(period)))
    return cores


def fetch_inputs():
    with connect() as conn,conn.cursor() as cur:
        cur.execute((ROOT/'sql/07_silver_inputs.sql').read_text())
        keys=[c[0].lower() for c in cur.description]
        rows=[dict(zip(keys,row)) for row in cur.fetchall()]
    if not rows or len({r['observation_id'] for r in rows})!=len(rows):
        raise ValueError('Entradas vacias o multiplicadas por joins.')
    return rows


def prepare_jobs(rows,code_sha,cache):
    jobs={};mappings=[];files={}
    for row in rows:
        left,right=parse_chains(row['ligand_chains_raw']),parse_chains(row['receptor_chains_raw'])
        mapping=dict(row,geometry_id=None)
        if not row['structure_sha256']:
            mapping['mapping_status']='structure_missing'
        elif not left or not right or set(left)&set(right):
            mapping['mapping_status']='invalid_chain_groups'
        else:
            sha=row['structure_sha256']
            if not re.fullmatch('[a-f0-9]{64}',sha): raise ValueError('Hash estructural invalido')
            path=ROOT/'data/rcsb/objects'/f'{sha}.cif.gz'
            files[sha]=(path,row['stage_path'])
            identity={'pdb_id':row['pdb_id'],'structure_sha256':sha,'ligand_chains':left,
                      'receptor_chains':right,'code_sha256':code_sha,'parameters':PARAMETERS}
            gid=canonical_hash(identity)
            jobs[gid]=dict(identity,geometry_id=gid,path=str(path),output_dir=str(cache))
            mapping.update(geometry_id=gid,mapping_status='assigned')
        mappings.append(mapping)
    # A cache is optional: a new machine retrieves the exact content-hashed files from RAW.
    with connect() as conn,conn.cursor() as cur:
        for sha,(path,stage_path) in files.items():
            if not path.exists() or digest_file(path)!=sha:
                expected=f'@RAW.SOURCE_FILES/objects/{sha}.cif.gz'
                if stage_path!=expected: raise ValueError('Stage path inesperado')
                path.parent.mkdir(parents=True,exist_ok=True)
                uri=('file://'+str(path.parent)).replace("'","''")
                cur.execute(f"GET {expected} '{uri}' PARALLEL=8")
                cur.fetchall()
                if not path.exists() or digest_file(path)!=sha: raise ValueError('Archivo estructural corrupto')
    return jobs,mappings


class Shards:
    def __init__(self,folder,kind):
        self.folder=folder;self.kind=kind;self.handle=None;self.n=0;self.part=0;self.bytes=0;self.paths=[]
    def add(self,line):
        if self.handle is None or self.bytes>64*1024*1024:
            if self.handle:self.handle.close()
            path=self.folder/f'{self.kind}_{self.part:04}.jsonl.gz';self.paths.append(path);self.part+=1
            self.handle=gzip.open(path,'wb',compresslevel=3);self.bytes=0
        self.handle.write(line);self.bytes+=len(line);self.n+=1
    def row(self,row):self.add((json.dumps(row,separators=(',',':'),allow_nan=False)+'\n').encode())
    def close(self):
        if self.handle:self.handle.close()
        return {'rows':self.n,'files':{p.name:digest_file(p) for p in self.paths}}


def assemble(folder,results,mappings,cache):
    writers={k:Shards(folder,k) for k in ['jobs','observations','residues','pairs']}
    grouped=defaultdict(list)
    for row in mappings:grouped[row['geometry_id']].append(row)
    for gid in sorted(results):
        result=results[gid];writers['jobs'].row(result)
        residues=[]
        if result['status']=='computed':
            with gzip.open(cache/gid/'residues.jsonl.gz','rb') as f:
                for line in f:
                    writers['residues'].add(line);residues.append(json.loads(line))
            with gzip.open(cache/gid/'pairs.jsonl.gz','rb') as f:
                for line in f:writers['pairs'].add(line)
        for row in grouped[gid]:
            writers['observations'].row(dict(row,mutation_check=mutation_check(row['mutations_raw'],residues,result['status'])))
    for row in grouped[None]:
        writers['observations'].row(dict(row,mutation_check=mutation_check(row['mutations_raw'],[],'unavailable')))
    manifest={k:w.close() for k,w in writers.items()}
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2))
    return manifest


def upload(folder,prefix,manifest):
    with connect() as conn,conn.cursor() as cur:
        cur.execute('CREATE STAGE IF NOT EXISTS SILVER.GEOMETRY_FILES')
        cur.execute('CREATE FILE FORMAT IF NOT EXISTS SILVER.GEOMETRY_JSON TYPE=JSON STRIP_NULL_VALUES=FALSE')
        uri=('file://'+str(folder/'*.jsonl.gz')).replace("'","''")
        cur.execute(f"PUT '{uri}' @SILVER.GEOMETRY_FILES/{prefix}/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE PARALLEL=8")
        columns=[c[0].lower() for c in cur.description];uploaded=[dict(zip(columns,row)) for row in cur.fetchall()]
        expected=sum(len(m['files']) for m in manifest.values())
        if len(uploaded)!=expected or any(r['status'] not in ['UPLOADED','SKIPPED'] for r in uploaded):
            raise ValueError('Carga de artefactos incompleta')
        for kind,meta in manifest.items():
            cur.execute(f"SELECT COUNT(*) FROM @SILVER.GEOMETRY_FILES/{prefix}/ (FILE_FORMAT=>'SILVER.GEOMETRY_JSON', PATTERN=>'.*{kind}_[0-9]+[.]jsonl[.]gz')")
            count=cur.fetchone()[0]
            if count!=meta['rows']:raise ValueError(f'Conteo de {kind} distinto en stage: {count}')
        print(f'Artefactos verificados en Snowflake: {expected} archivos',flush=True)


def run_dbt(folder,prefix,command,label,selector="tag:silver",extra_vars=None):

    args=['dbt',*command,'--select',selector,'--vars',json.dumps({'geometry_prefix':prefix,**(extra_vars or {})}),
        '--project-dir',str(ROOT/'dbt'),'--profiles-dir',str(ROOT/'dbt')]
    if command == ['build']: args.extend(['--indirect-selection','buildable'])
    # Backbone is a subsequent stage with its own Python artifacts.
    if selector=='tag:silver': args.extend(['--exclude','tag:backbone','tag:gold'])
    elif selector!='tag:gold': args.extend(['--exclude','tag:gold'])
    with (folder/f'{label}.log').open('w') as log:
        p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,env=dict(os.environ,DBT_USE_COLORS='false',DBT_SEND_ANONYMOUS_USAGE_STATS='false'))
        for line in p.stdout:log.write(line);log.flush();print(line,end='',flush=True)
        if p.wait():raise RuntimeError(f'dbt fallo: {label}.log')
    for name in ['manifest.json', 'catalog.json' if label=='docs' else 'run_results.json']:
        path=ROOT/'dbt/target'/name
        if path.exists():shutil.copyfile(path,folder/f'{label}_{name}')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workers',type=int,default=0)
    parser.add_argument('--pilot',type=int,default=0)
    parser.add_argument('--verify-replay',action='store_true')
    args=parser.parse_args();load_dotenv(ROOT/'.env')
    key=Path(os.environ['SNOWFLAKE_PRIVATE_KEY_FILE']);os.environ['DBT_PRIVATE_KEY_PATH']=str(key if key.is_absolute() else ROOT/key)
    out=ROOT/'reports/silver';out.mkdir(parents=True,exist_ok=True)
    with (out/'.build.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        started=time.monotonic();run=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        folder=out/run;folder.mkdir();cache=ROOT/'data/silver/cache';cache.mkdir(parents=True,exist_ok=True)
        try:
            before={'raw':fingerprints('RAW',RAW_TABLES),'bronze':fingerprints('BRONZE',BRONZE_TABLES)}
            rows=fetch_inputs()
            code_sha=canonical_hash({p:digest_file(ROOT/p) for p in ['scripts/geometry_core.py','geometry/requirements.txt']})
            jobs,mappings=prepare_jobs(rows,code_sha,cache)
            if args.pilot:
                jobs=dict(list(sorted(jobs.items()))[:args.pilot]);mappings=[r for r in mappings if r['geometry_id'] in jobs]
            workers=min(args.workers or available_cpus(),available_cpus())
            if workers<1:raise ValueError('workers debe ser positivo')
            print(f'{len(rows)} observaciones; {len(jobs)} geometrias; {workers} procesos CPU',flush=True)
            results={};compute_start=time.monotonic()
            with ProcessPoolExecutor(max_workers=workers) as pool:
                futures={pool.submit(calculate_job,j):gid for gid,j in jobs.items()}
                for i,future in enumerate(as_completed(futures),1):
                    result=future.result();results[result['geometry_id']]=result
                    if i%100==0 or i==len(jobs):print(f'Geometrias {i}/{len(jobs)}',flush=True)
            metrics={'run':run,'workers':workers,'observations':len(mappings),'geometry_jobs':len(jobs),
                'statuses':dict(Counter(r['status'] for r in results.values())),
                'reasons':dict(Counter(r.get('reason') for r in results.values() if r['status']!='computed')),
                'residues':sum(r.get('n_ligand',0)+r.get('n_receptor',0) for r in results.values()),
                'selected_pairs':sum(r.get('selected_pair_count',0) for r in results.values()),
                'compute_seconds':round(time.monotonic()-compute_start,2),'code_sha256':code_sha}
            (folder/'computation.json').write_text(json.dumps(metrics,indent=2))
            print(json.dumps(metrics,indent=2),flush=True)
            if args.pilot:return
            prefix=canonical_hash({'inputs':rows,'code':code_sha})
            artifacts=ROOT/'data/silver/runs'/prefix;artifacts.mkdir(parents=True,exist_ok=True)
            print('Preparando artefactos comprimidos para Snowflake',flush=True)
            manifest=assemble(artifacts,results,mappings,cache)
            if manifest['observations']['rows']!=len(rows):raise ValueError('Se perdieron observaciones')
            print('Cargando y verificando artefactos',flush=True)
            upload(artifacts,prefix,manifest)
            run_dbt(folder,prefix,['build'],'build')
            first=fingerprints('SILVER',SILVER_TABLES)
            replay=None
            if args.verify_replay:
                run_dbt(folder,prefix,['build'],'replay');replay=fingerprints('SILVER',SILVER_TABLES)
                if first!=replay:raise ValueError('La reconstruccion cambio el contenido')
            run_dbt(folder,prefix,['docs','generate'],'docs')
            after={'raw':fingerprints('RAW',RAW_TABLES),'bronze':fingerprints('BRONZE',BRONZE_TABLES)}
            if before!=after:raise ValueError('RAW o Bronze cambiaron durante el trabajo')
            build=json.loads((folder/'build_run_results.json').read_text())
            tests=[r for r in build['results'] if r['unique_id'].startswith('test.')]
            with connect() as conn,conn.cursor() as cur:
                cur.execute('SELECT MUTATION_STRUCTURE_STATUS,COUNT(*) FROM SILVER.AFFINITY_OBSERVATIONS GROUP BY 1')
                mutations=dict(cur.fetchall())
                cur.execute('SELECT GEOMETRY_STATUS,COUNT(*) FROM SILVER.AFFINITY_OBSERVATIONS GROUP BY 1')
                geometry_status=dict(cur.fetchall())
            summary=dict(metrics,status='SUCCESS',geometry_prefix=prefix,tables=first,raw_bronze_unchanged=True,
                replay_verified=first==replay if replay else None,tests=len(tests),tests_passed=sum(r['status']=='pass' for r in tests),
                mutations=mutations,observation_geometry_status=geometry_status,seconds=round(time.monotonic()-started,2))
            (folder/'summary.json').write_text(json.dumps(summary,indent=2));(out/'latest.json').write_text(json.dumps({'run':run}))
            from silver_report import write_report
            write_report(summary)
            print(json.dumps(summary,indent=2),flush=True)
        except Exception as exc:
            (folder/'failure.json').write_text(json.dumps({'error':str(exc),'run':run},indent=2));raise

if __name__=='__main__':main()
