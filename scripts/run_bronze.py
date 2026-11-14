"""Construye Bronze con dbt, verifica conservacion e idempotencia y guarda evidencia."""
import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess

from dotenv import load_dotenv
from check_snowflake import connect

ROOT=Path(__file__).resolve().parents[1]
TABLES=('AFFINITY_OBSERVATIONS','STRUCTURE_METADATA','RESOURCE_RECEIPTS')
RAW_TABLES=('SOURCE_RECORDS','RCSB_ENTRIES','RESOURCE_FILES','BATCH_RESOURCES','INGESTION_BATCHES')


def fingerprints(schema,tables):
    with connect() as conn, conn.cursor() as cur:
        result={}
        for name in tables:
            cur.execute(f'SELECT COUNT(*),HASH_AGG(*) FROM {schema}.{name}')
            count,digest=cur.fetchone()
            result[name]={'rows':count,'hash':digest}
        return result


def dbt_command(args,folder,label):
    command=['dbt',*args,'--project-dir',str(ROOT/'dbt'),'--profiles-dir',str(ROOT/'dbt')]
    env=os.environ.copy()
    env['DBT_SEND_ANONYMOUS_USAGE_STATS']='false'
    env['DBT_USE_COLORS']='false'
    print('Ejecutando dbt '+ ' '.join(args),flush=True)
    with (folder/f'{label}.log').open('w') as log:
        process=subprocess.Popen(command,cwd=ROOT/'dbt',env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        for line in process.stdout:
            print(line,end='',flush=True)
            log.write(line)
        code=process.wait()
    if code:
        raise RuntimeError(f'dbt fallo en {label}. Revisar {folder.name}/{label}.log')
    for name in ('manifest.json','run_results.json','catalog.json'):
        path=ROOT/'dbt/target'/name
        if path.exists():
            shutil.copyfile(path,folder/f'{label}_{name}')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-replay',action='store_true',help='Repite dbt build y compara contenido de Bronze.')
    args=parser.parse_args()
    load_dotenv(ROOT/'.env')
    key=Path(os.environ['SNOWFLAKE_PRIVATE_KEY_FILE'])
    os.environ['DBT_PRIVATE_KEY_PATH']=str(key if key.is_absolute() else ROOT/key)
    lockdir=ROOT/'reports/bronze'
    lockdir.mkdir(parents=True,exist_ok=True)
    with (lockdir/'.build.lock').open('w') as lock:
        try:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit('Ya hay otra construccion de Bronze en este volumen.')
        run=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        folder=lockdir/run
        folder.mkdir()
        before=fingerprints('RAW',RAW_TABLES)
        try:
            dbt_command(['debug'],folder,'connection')
            dbt_command(['build','--select','tag:bronze','--indirect-selection','buildable'],folder,'build')
            first=fingerprints('BRONZE',TABLES)
            second=None
            if args.verify_replay:
                dbt_command(['build','--select','tag:bronze','--indirect-selection','buildable'],folder,'replay')
                second=fingerprints('BRONZE',TABLES)
                if first!=second:
                    raise RuntimeError('La repeticion cambio conteos o contenido de Bronze.')
            dbt_command(['docs','generate','--select','tag:bronze'],folder,'docs')
            after=fingerprints('RAW',RAW_TABLES)
            if before!=after:
                raise RuntimeError('RAW cambio durante la construccion; revisar concurrencia.')
            with connect() as conn,conn.cursor() as cur:
                cur.execute('''SELECT COUNT(*),COUNT(DISTINCT OBSERVATION_ID),COUNT(DISTINCT PDB_ID),
                    COUNT_IF(TEMPERATURE_RAW IS NULL),COUNT_IF(TEMPERATURE_RAW ILIKE '%assum%'),
                    COUNT_IF(AFFINITY_REFERENCE_RAW='TBD') FROM BRONZE.AFFINITY_OBSERVATIONS''')
                values=cur.fetchone()
                annotations=dict(zip(('observations','unique_observation_ids','unique_pdb_ids',
                    'temperature_missing','temperature_assumed','reference_tbd'),values))
                cur.execute('SELECT DOWNLOAD_STATUS,COUNT(*) FROM BRONZE.RESOURCE_RECEIPTS GROUP BY 1')
                resources=dict(cur.fetchall())
            build=json.loads((folder/'build_run_results.json').read_text())
            tests=[r for r in build['results'] if r['unique_id'].startswith('test.')]
            summary={'run':run,'status':'SUCCESS','tables':first,'raw_unchanged':before==after,
                     'replay_verified':first==second if second is not None else None,
                     'annotations':annotations,'download_statuses':resources,
                     'tests':len(tests),'tests_passed':sum(r['status']=='pass' for r in tests),
                     'raw_before':before,'raw_after':after}
            (folder/'summary.json').write_text(json.dumps(summary,indent=2,default=str))
            (lockdir/'latest.json').write_text(json.dumps({'run':run},indent=2))
            lines=['# Bronze creada con dbt','',f'Ejecucion: `{run}`. Estado: **SUCCESS**.','',
                   '| Tabla en PROTEIN_AFFINITY.BRONZE | Filas | Grano |','|---|---:|---|',
                   f"| AFFINITY_OBSERVATIONS | {first['AFFINITY_OBSERVATIONS']['rows']} | Una fila original de medicion |",
                   f"| STRUCTURE_METADATA | {first['STRUCTURE_METADATA']['rows']} | Una version del JSON de RCSB |",
                   f"| RESOURCE_RECEIPTS | {first['RESOURCE_RECEIPTS']['rows']} | Un resultado por lote, PDB y recurso |",'',
                   f"Pruebas dbt: **{summary['tests_passed']}/{summary['tests']} aprobadas**.",
                   f"RAW conserva su conteo y huella agregada: **{summary['raw_unchanged']}**.",
                   f"Repetir dbt build mantiene conteos y contenido de Bronze: **{summary['replay_verified']}**.",'',
                   '## Anotaciones conservadas','',
                   f"- {annotations['temperature_missing']} temperaturas ausentes.",
                   f"- {annotations['temperature_assumed']} temperaturas con anotacion de supuesto.",
                   f"- {annotations['reference_tbd']} referencias TBD.",
                   f"- {resources.get('not_found',0)} resultados de descarga no encontrados.",'',
                   'No se eliminaron observaciones por compartir complejo o afinidad. Complex ID se verifica por version del archivo.',
                   'PAYLOAD y RECEIPT conservan los originales. Se proyectaron campos y se tiparon Kd y resolucion; las reglas de limpieza quedan para Silver.',
                   'Las estructuras 3D siguen como archivos en RAW.SOURCE_FILES. Bronze no contiene distancias ni features geometricas todavia.','',
                   '## Archivos para revisar','',
                   '- Modelo principal: `dbt/models/bronze/bronze_affinity_observations.sql`.',
                   '- Pruebas: `dbt/models/bronze/schema.yml` y `dbt/tests/`.',
                   '- Consulta de visualizacion: `sql/06_view_bronze.sql`.',
                   f'- Logs, manifest y resultados de pruebas: `reports/bronze/{run}/`.',
                   '- Catalogo dbt: `dbt/target/index.html`, `manifest.json` y `catalog.json`.',
                   '', '## Alcance de la reconstruccion', '',
                   'Cada build reconstruye estas tres tablas derivadas a partir de RAW. Si llegan nuevos lotes, se incorporan en el siguiente build.',
                   'No es una carga incremental ni una transaccion atomica de toda la capa. Si una prueba falla, no continuar a Silver hasta corregirla y repetir build.',
                   'Se mantienen todas las versiones de archivos. Para modelado se decidira explicitamente que versiones usar y como agrupar complejos al separar entrenamiento y prueba.']
            text='\n'.join(lines)+'\n'
            (folder/'summary.md').write_text(text)
            (ROOT/'reports/bronze.md').write_text(text)
            print(json.dumps(summary,indent=2,default=str),flush=True)
        except Exception as exc:
            (folder/'failure.json').write_text(json.dumps({'run':run,'status':'FAILED','error':str(exc)},indent=2))
            raise


if __name__=='__main__':
    main()
