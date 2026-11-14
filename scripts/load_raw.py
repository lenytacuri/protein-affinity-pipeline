"""Carga un batch extraido a Snowflake RAW sin duplicar filas al repetirlo.

Los originales quedan en SOURCE_FILES. COPY carga tablas temporales;
MERGE agrega solo claves nuevas. No se deduplica por PDB ID.
"""
import argparse
from collections import Counter
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from check_snowflake import connect
from source_inputs import sha256_file, write_jsonl

ROOT = Path(__file__).resolve().parents[1]
STAGE = '@RAW.SOURCE_FILES'
AVAILABLE = {'downloaded', 'cached'}


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def require_unique(values, label):
    if len(values) != len(set(values)):
        raise ValueError(f'Claves repetidas en {label}; se cancela antes de cargar.')


def inspect_batch(batch, cache):
    summary = json.loads((batch/'summary.json').read_text())
    run_id = summary['run_id']
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', run_id) or run_id != batch.name:
        raise ValueError('Identificador de batch invalido.')
    if summary['status'] not in {'SUCCESS', 'COMPLETE', 'PARTIAL'}:
        raise ValueError('La extraccion no ha terminado.')
    records = read_jsonl(batch/'records.jsonl')
    resources = read_jsonl(batch/'download_manifest.jsonl')
    require_unique([r['source_record_id'] for r in records], 'filas originales')
    require_unique([(r['pdb_id'], r['resource']) for r in resources], 'manifiesto')
    if len(records) != summary['records']:
        raise ValueError('Conteo de filas distinto al resumen.')
    ids = set(json.loads((batch/'requested_ids.json').read_text()))
    expected = {(pdb, kind) for pdb in ids for kind in ('entry', 'structure')}
    if {(r['pdb_id'], r['resource']) for r in resources} != expected:
        raise ValueError('El manifiesto no cubre exactamente los recursos solicitados.')
    if any(r['status'] not in AVAILABLE | {'not_found'} for r in resources):
        raise ValueError('Hay fallos tecnicos pendientes en el batch.')
    original = batch/('source' + Path(summary['source_file']).suffix.lower())
    if sha256_file(original) != summary['source_sha256']:
        raise ValueError('El original no coincide con su SHA-256.')
    if any(r['source_sha256'] != summary['source_sha256'] for r in records):
        raise ValueError('Hay filas ajenas a la version del archivo original.')
    objects = {}
    entries = []
    for row in resources:
        if row['status'] not in AVAILABLE:
            continue
        sha = row['sha256']
        suffix = '.json' if row['resource'] == 'entry' else '.cif.gz'
        if not re.fullmatch('[0-9a-f]{64}', sha) or row['path'] != f'objects/{sha}{suffix}':
            raise ValueError('Ruta de objeto invalida.')
        path = cache/row['path']
        if path.stat().st_size != row['bytes'] or sha256_file(path) != sha:
            raise ValueError(f'Integridad local incorrecta: {row["pdb_id"]}/{row["resource"]}')
        objects[row['path']] = path
        if row['resource'] == 'entry':
            entries.append({'sha256': sha, 'pdb_id': row['pdb_id'],
                            'payload': json.loads(path.read_text())})
    files = [original, batch/'records.jsonl', batch/'requested_ids.json',
             batch/'download_manifest.jsonl', batch/'summary.json']
    digest = hashlib.sha256('\n'.join(f'{p.name}:{sha256_file(p)}' for p in files).encode()).hexdigest()
    return summary, records, resources, objects, entries, files, digest


def put(cur, path, prefix, expected_count):
    # Ruta local SQL escapada; el prefijo solo procede de run_id validado o constantes.
    uri = ('file://' + str(path)).replace("'", "''")
    cur.execute(f"PUT '{uri}' {STAGE}/{prefix} AUTO_COMPRESS=FALSE SOURCE_COMPRESSION=NONE OVERWRITE=FALSE PARALLEL=8")
    columns = [col[0].lower() for col in cur.description]
    results = [dict(zip(columns, row)) for row in cur.fetchall()]
    statuses = Counter(row['status'] for row in results)
    if len(results) != expected_count or any(row['status'] not in {'UPLOADED', 'SKIPPED'} for row in results):
        raise RuntimeError(f'Carga de archivos incompleta: {dict(statuses)}')
    print(f'Archivos {prefix}: {dict(statuses)}', flush=True)
    return dict(statuses)


def copy_json(cur, table, prefix, filename):
    cur.execute(f'CREATE OR REPLACE TEMPORARY TABLE {table} (DOC VARIANT)')
    cur.execute(f"COPY INTO {table} FROM {STAGE}/{prefix}/ FILES=('{filename}') "
                "FILE_FORMAT=(TYPE=JSON STRIP_NULL_VALUES=FALSE) ON_ERROR=ABORT_STATEMENT")


def counts(cur):
    result = {}
    for table in ('SOURCE_RECORDS', 'RCSB_ENTRIES', 'RESOURCE_FILES', 'BATCH_RESOURCES', 'INGESTION_BATCHES'):
        cur.execute(f'SELECT COUNT(*) FROM RAW.{table}')
        result[table] = cur.fetchone()[0]
    return result


def merge(cur, run_id, source_sha, digest, prefix, summary):
    cur.execute('''MERGE INTO RAW.SOURCE_RECORDS t USING TMP_RECORDS s
        ON t.RECORD_ID = s.DOC:source_record_id::VARCHAR
        WHEN NOT MATCHED THEN INSERT (RECORD_ID,SOURCE_SHA256,PDB_ID,INPUT_KIND,RAW_RECORD)
        VALUES (s.DOC:source_record_id::VARCHAR,s.DOC:source_sha256::VARCHAR,
                s.DOC:pdb_id::VARCHAR,s.DOC:input_kind::VARCHAR,s.DOC)''')
    cur.execute('''MERGE INTO RAW.RCSB_ENTRIES t USING TMP_ENTRIES s
        ON t.CONTENT_SHA256 = s.DOC:sha256::VARCHAR
        WHEN NOT MATCHED THEN INSERT (CONTENT_SHA256,PDB_ID,PAYLOAD)
        VALUES (s.DOC:sha256::VARCHAR,s.DOC:pdb_id::VARCHAR,s.DOC:payload)''')
    cur.execute('''MERGE INTO RAW.RESOURCE_FILES t USING
        (SELECT DISTINCT DOC:sha256::VARCHAR AS SHA,
         '@RAW.SOURCE_FILES/' || DOC:path::VARCHAR AS PATH, DOC:bytes::NUMBER AS BYTES
         FROM TMP_RESOURCES WHERE DOC:status::VARCHAR IN ('cached','downloaded')) s
        ON t.CONTENT_SHA256=s.SHA
        WHEN NOT MATCHED THEN INSERT (CONTENT_SHA256,STAGE_PATH,BYTE_COUNT)
        VALUES (s.SHA,s.PATH,s.BYTES)''')
    cur.execute('''MERGE INTO RAW.BATCH_RESOURCES t USING
        (SELECT %s AS BATCH_ID,DOC FROM TMP_RESOURCES) s
        ON t.BATCH_ID=s.BATCH_ID AND t.PDB_ID=s.DOC:pdb_id::VARCHAR
           AND t.RESOURCE=s.DOC:resource::VARCHAR
        WHEN NOT MATCHED THEN INSERT (BATCH_ID,PDB_ID,RESOURCE,RECEIPT)
        VALUES (s.BATCH_ID,s.DOC:pdb_id::VARCHAR,s.DOC:resource::VARCHAR,s.DOC)''', (run_id,))
    cur.execute('''MERGE INTO RAW.INGESTION_BATCHES t USING
        (SELECT %s AS ID,%s AS SHA,%s AS SOURCE_SHA,%s AS PREFIX,PARSE_JSON(%s) AS SUMMARY) s
        ON t.BATCH_ID=s.ID
        WHEN NOT MATCHED THEN INSERT
        (BATCH_ID,BATCH_SHA256,SOURCE_SHA256,STAGE_PREFIX,EXTRACTION_SUMMARY,STATUS)
        VALUES (s.ID,s.SHA,s.SOURCE_SHA,s.PREFIX,s.SUMMARY,'LOADED')''',
        (run_id, digest, source_sha, prefix, json.dumps(summary)))


def verify(cur, run_id, records, resources, entries):
    for table, key in [('SOURCE_RECORDS','RECORD_ID'), ('RCSB_ENTRIES','CONTENT_SHA256'),
                       ('RESOURCE_FILES','CONTENT_SHA256'), ('INGESTION_BATCHES','BATCH_ID')]:
        cur.execute(f'SELECT COUNT(*)-COUNT(DISTINCT {key}) FROM RAW.{table}')
        if cur.fetchone()[0]:
            raise RuntimeError(f'Claves duplicadas: {table}')
    cur.execute('''SELECT COUNT(*) FROM (SELECT BATCH_ID,PDB_ID,RESOURCE
        FROM RAW.BATCH_RESOURCES GROUP BY 1,2,3 HAVING COUNT(*)>1)''')
    if cur.fetchone()[0]:
        raise RuntimeError('Claves duplicadas: BATCH_RESOURCES')
    cur.execute('''SELECT COUNT(*) FROM RAW.SOURCE_RECORDS t JOIN TMP_RECORDS s
        ON t.RECORD_ID=s.DOC:source_record_id::VARCHAR WHERE t.RAW_RECORD=s.DOC''')
    if cur.fetchone()[0] != len(records):
        raise RuntimeError('No se conservaron todas las filas originales.')
    cur.execute('SELECT COUNT(*) FROM RAW.BATCH_RESOURCES WHERE BATCH_ID=%s', (run_id,))
    if cur.fetchone()[0] != len(resources):
        raise RuntimeError('Manifiesto incompleto en RAW.')
    cur.execute('''SELECT COUNT(*) FROM RAW.RCSB_ENTRIES t JOIN TMP_ENTRIES s
        ON t.CONTENT_SHA256=s.DOC:sha256::VARCHAR WHERE t.PAYLOAD=s.DOC:payload''')
    if cur.fetchone()[0] != len(entries):
        raise RuntimeError('JSON RCSB incompletos o diferentes en RAW.')


@contextmanager
def loader_lock(cache):
    # Kestra y ejecuciones manuales usan el mismo volumen: un solo escritor.
    with (cache/'.load_raw.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('Hay otra carga RAW en curso; reintentar al terminar.')
        yield


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', type=Path, help='Carpeta de batch. Por defecto: latest_batch.json.')
    parser.add_argument('--cache', type=Path, default=ROOT/'data/rcsb')
    parser.add_argument('--verify-replay', action='store_true', help='Repite MERGE y comprueba conteos.')
    args = parser.parse_args()
    batch = args.batch or args.cache/json.loads((args.cache/'latest_batch.json').read_text())['batch_path']
    with loader_lock(args.cache):
        summary, records, resources, objects, entries, files, digest = inspect_batch(batch, args.cache)
        run_id = summary['run_id']
        prefix = f'batches/{run_id}'
        print(f'Cargando {run_id}: {len(records)} filas y {len(objects)} archivos originales.', flush=True)
        with connect() as conn, conn.cursor() as cur, tempfile.TemporaryDirectory(dir=args.cache, prefix='.upload_') as temp:
            for statement in (ROOT/'sql/03_raw.sql').read_text().split(';'):
                if statement.strip():
                    cur.execute(statement)
            cur.execute('SELECT BATCH_SHA256 FROM RAW.INGESTION_BATCHES WHERE BATCH_ID=%s', (run_id,))
            previous = cur.fetchone()
            if previous and previous[0] != digest:
                raise ValueError('El contenido de un batch ya cargado fue modificado.')
            before = counts(cur)
            temp = Path(temp)
            object_dir = temp/'objects'
            object_dir.mkdir()
            for path in objects.values():
                os.link(path, object_dir/path.name)
            # Los enlaces no duplican el GB de estructuras en disco.
            uploads = put(cur, object_dir/'*', 'objects', len(objects)) if objects else {}
            for path in files:
                put(cur, path, prefix, 1)
            entry_file = temp/'entries.jsonl'
            write_jsonl(entry_file, entries)
            if entries:
                put(cur, entry_file, prefix, 1)
                copy_json(cur, 'TMP_ENTRIES', prefix, entry_file.name)
            else:
                cur.execute('CREATE OR REPLACE TEMPORARY TABLE TMP_ENTRIES (DOC VARIANT)')
            copy_json(cur, 'TMP_RECORDS', prefix, 'records.jsonl')
            copy_json(cur, 'TMP_RESOURCES', prefix, 'download_manifest.jsonl')
            cur.execute(f'LIST {STAGE}/objects/')
            remote_names = {Path(row[0]).name for row in cur.fetchall()}
            if not {p.name for p in objects.values()}.issubset(remote_names):
                raise RuntimeError('Faltan archivos originales en el stage RAW.')
            cur.execute('BEGIN')
            try:
                merge(cur, run_id, summary['source_sha256'], digest, prefix, summary)
                verify(cur, run_id, records, resources, entries)
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            after = counts(cur)
            replay = None
            if args.verify_replay:
                cur.execute('BEGIN')
                try:
                    merge(cur, run_id, summary['source_sha256'], digest, prefix, summary)
                    verify(cur, run_id, records, resources, entries)
                    replay = counts(cur)
                    if replay != after:
                        raise RuntimeError('Repetir MERGE cambio los conteos.')
                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise
            result = {'batch_id': run_id, 'status': 'LOADED', 'before': before, 'after': after,
                      'after_replay': replay, 'replay_verified': replay == after if replay else None,
                      'object_uploads': uploads, 'original_files_verified': len(objects),
                      'source_records': len(records), 'distinct_pdb_ids': summary['unique_pdb_ids'],
                      'unavailable_resources': sum(r['status']=='not_found' for r in resources)}
            reports = ROOT/'reports'
            reports.mkdir(exist_ok=True)
            (reports/f'raw_load_{run_id}.json').write_text(json.dumps(result, indent=2))
            (reports/'raw_load.json').write_text(json.dumps(result, indent=2))
            lines = ['# Carga RAW', '', f'Lote: `{run_id}`.', '',
                     '| Comprobacion | Resultado |', '|---|---:|',
                     f'| Filas originales conservadas | {len(records)} |',
                     f"| PDB distintos | {summary['unique_pdb_ids']} |",
                     f'| Archivos RCSB en el stage | {len(objects)} |',
                     f'| JSON interpretados en RCSB_ENTRIES | {len(entries)} |',
                     f"| Recursos no disponibles registrados | {result['unavailable_resources']} |",
                     f"| Repeticion sin cambios en conteos | {result['replay_verified']} |", '',
                     '## Conteos globales', '',
                     '| Tabla | Antes | Despues | Tras repetir MERGE |', '|---|---:|---:|---:|']
            for table in after:
                lines.append(f"| {table} | {before[table]} | {after[table]} | {replay[table] if replay else 'No solicitado'} |")
            lines += ['', 'Los PDB repetidos se conservan. Se evitan duplicados por clave de fila de origen.',
                      'Los originales estan en PROTEIN_AFFINITY.RAW.SOURCE_FILES.',
                      'RAW no limpia valores ni certifica ensamblajes, cadenas o mutaciones.',
                      '', 'Codigo: scripts/load_raw.py. Consultas: sql/04_verify_raw.sql.']
            (reports/'raw_load.md').write_text('\n'.join(lines)+'\n')
            print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
