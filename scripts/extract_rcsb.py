"""Batch: Excel/listado -> filas originales + JSON/mmCIF de RCSB + manifiesto."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import fcntl
import json
import os
from pathlib import Path
import shutil
import threading
import uuid

import requests

from rcsb_download import atomic_json, fetch_resource, utc_now
from source_inputs import read_source, write_jsonl


def write_report(summary, batch):
    available, incidents = Counter(), []
    with (batch/'download_manifest.jsonl').open() as stream:
        for line in stream:
            row = json.loads(line)
            if row['status'] in {'cached', 'downloaded'}:
                available[row['resource']] += 1
            else:
                incidents.append(row)
    lines = ['# Extraccion RCSB', '', f"Estado de cobertura: **{summary['status']}**.",
             '', '| Comprobacion | Resultado |', '|---|---:|',
             f"| Filas conservadas | {summary['records']} |",
             f"| Codigos PDB distintos solicitados | {summary['unique_pdb_ids']} |",
             f"| Estructuras mmCIF disponibles | {available['structure']} |",
             f"| JSON de metadatos disponibles | {available['entry']} |",
             f"| Recursos no disponibles | {len(incidents)} |", '',
             'AlphaFold excluido. Las filas originales se conservan aunque falte algun recurso.',
             'Esta etapa comprueba descarga y formato; no certifica cadenas, mutaciones ni interfaces.',
             'Este reporte describe la extraccion local; consultar reports/raw_load.md para el estado de carga en Snowflake.',
             '', f"Batch: `{summary['run_id']}`. Modo de entrada: `{summary['input_mode']}`.",
             '', '## Incidencias', '', '| PDB | Recurso | Estado | HTTP |', '|---|---|---|---:|']
    for row in incidents:
        lines.append(f"| {row['pdb_id']} | {row['resource']} | {row['status']} | {row.get('http_status', '')} |")
    if not incidents:
        lines.append('| Ninguna | | | |')
    lines += ['', 'El manifiesto conserva URL, fecha, SHA-256 y ubicacion de cada archivo.',
              'Consultar `data/rcsb/latest_batch.json` para localizar el batch y su manifiesto.']
    text = '\n'.join(lines) + '\n'
    (batch/'summary.md').write_text(text)
    reports = Path(__file__).resolve().parents[1]/'reports'
    reports.mkdir(exist_ok=True)
    (reports/'extraction.md').write_text(text)


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['excel', 'ids'], default='excel')
    parser.add_argument('--input', type=Path, default=root/'data/reference/PPB-Affinity.zenodo-14271435.xlsx')
    parser.add_argument('--output', type=Path, default=root/'data/rcsb')
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--refresh', action='store_true', default=os.environ.get('RCSB_REFRESH', '').lower()=='true')
    parser.add_argument('--result-file', type=Path, help='Recibo de esta ejecucion; evita depender de latest_batch.json.')
    parser.add_argument('--plan-only', action='store_true', help='Guardar entradas y plan, sin descargar.')
    args = parser.parse_args()
    if not 1 <= args.workers <= 8:
        parser.error('--workers debe estar entre 1 y 8.')
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output/'.extract.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit('Ya hay una extraccion usando esta cache; reintentar al terminar.')
        records, pdb_ids, source_sha = read_source(args.input, args.mode)
        run_id = utc_now().replace(':', '').replace('+', '_') + '_' + uuid.uuid4().hex[:8]
        batch = args.output/'batches'/run_id
        batch.mkdir(parents=True)
        shutil.copyfile(args.input, batch/('source' + args.input.suffix.lower()))
        write_jsonl(batch/'records.jsonl', records)
        atomic_json(batch/'requested_ids.json', pdb_ids)
        summary = {'run_id': run_id, 'started_at': utc_now(), 'input_mode': args.mode,
                   'source_file': str(args.input), 'source_sha256': source_sha,
                   'records': len(records), 'unique_pdb_ids': len(pdb_ids),
                   'invalid_pdb_rows': sum(not row['pdb_id_valid'] for row in records),
                   'scope': 'RCSB experimental entries; excludes the authors AlphaFold collection.',
                   'coordinate_representation': 'Deposited entry (not necessarily biological assembly).',
                   'structure_validation': 'Transport/format only; chains, mutations and interfaces not yet validated.',
                   'status': 'PLANNED' if args.plan_only else 'RUNNING'}
        atomic_json(batch/'summary.json', summary)
        print(f'Batch {run_id}: {len(records)} filas; {len(pdb_ids)} PDB distintos.', flush=True)
        if args.plan_only:
            print(f'Plan: {batch}', flush=True)
            return
        thread_local, sessions = threading.local(), []
        session_lock = threading.Lock()

        def download(pdb_id):
            if not hasattr(thread_local, 'session'):
                thread_local.session = requests.Session()
                with session_lock:
                    sessions.append(thread_local.session)
            return [fetch_resource(thread_local.session, args.output, pdb_id, kind, refresh=args.refresh)
                    for kind in ['entry', 'structure']]

        counts, unavailable = Counter(), set()
        try:
            with (batch/'download_manifest.jsonl').open('w') as manifest:
                with ThreadPoolExecutor(max_workers=args.workers) as pool:
                    futures = {pool.submit(download, pdb_id): pdb_id for pdb_id in pdb_ids}
                    for number, future in enumerate(as_completed(futures), 1):
                        for result in future.result():
                            manifest.write(json.dumps(result, ensure_ascii=False) + '\n')
                            counts[result['status']] += 1
                            if result['status'] in {'not_found', 'failed'}:
                                unavailable.add(result['pdb_id'])
                        manifest.flush()
                        if number % 100 == 0 or number == len(pdb_ids):
                            print(f'Procesados {number}/{len(pdb_ids)} PDB; recursos: {dict(counts)}', flush=True)
        except BaseException:
            summary.update(status='INTERRUPTED', finished_at=utc_now(), resource_statuses=dict(counts))
            atomic_json(batch/'summary.json', summary)
            raise
        finally:
            for session in sessions:
                session.close()
        summary.update(finished_at=utc_now(), resource_statuses=dict(counts),
                       pdb_ids_with_unavailable_resources=sorted(unavailable),
                       status='PARTIAL' if unavailable or summary['invalid_pdb_rows'] else 'COMPLETE')
        atomic_json(batch/'summary.json', summary)
        atomic_json(args.output/'latest_batch.json', {'run_id': run_id, 'batch_path': str(batch.relative_to(args.output)),
                                                     'status': summary['status']})
        write_report(summary, batch)
        print(json.dumps(summary, indent=2), flush=True)
        # 404/410 quedan documentados y permiten continuar conservando todas las filas.
        # Fallos tecnicos persistentes hacen que Kestra reintente usando la cache.
        if counts['failed']:
            raise SystemExit(1)
        if args.result_file:
            args.result_file.parent.mkdir(parents=True, exist_ok=True)
            atomic_json(args.result_file, {'batch_path': str(batch.resolve()), 'run_id': run_id})


if __name__ == '__main__':
    main()
