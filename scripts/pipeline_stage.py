"""Etapas del flujo principal. Cada ejecución conserva entradas, logs y recibos propios."""
import argparse
from datetime import datetime, timezone
import json
import hashlib
import tempfile
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
STAGES = ('prepare', 'extract', 'raw', 'profile', 'bronze', 'silver', 'backbone', 'gold', 'obt', 'dictionary', 'finish')
COMMANDS = {
    'raw': ['scripts/load_raw.py', '--verify-replay'],
    'profile': ['scripts/profile_raw.py'],
    'bronze': ['scripts/run_bronze.py', '--verify-replay'],
    'silver': ['scripts/run_silver.py', '--verify-replay'],
    'backbone': ['scripts/build_backbone.py'],
    'gold': ['scripts/build_gold.py'],
    'obt': ['spark/build_obt.py'],
    'dictionary': ['scripts/build_obt_dictionary.py', '--refresh'],
}


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', dir=path.parent, delete=False) as stream:
        json.dump(value, stream, indent=2)
        temporary = stream.name
    os.replace(temporary, path)


def project_path(value):
    path = Path(value)
    path = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError('La entrada debe estar dentro de la carpeta del proyecto compartida con Docker.')
    return path


def read(path):
    return json.loads(path.read_text())


def run(command, folder, stage):
    with (folder / (stage + '.log')).open('a') as log:
        process = subprocess.Popen([sys.executable, *command], cwd=ROOT,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            log.write(line); log.flush(); print(line, end='', flush=True)
        if process.wait():
            raise RuntimeError(f'Fallo en {stage}; consultar el log de esta ejecucion.')


def validate_replay(batch):
    from batch_contract import validate_measurements
    from load_raw import inspect_batch
    summary, *_ = inspect_batch(batch, ROOT / 'data/rcsb')
    if summary['input_mode'] != 'excel':
        raise ValueError('El lote debe contener mediciones, no solo solicitudes de estructuras.')
    validate_measurements(batch / 'source.xlsx')
    return summary


def prepare(folder, mode, input_path, refresh):
    from batch_contract import validate_measurements
    if mode == 'replay' and (not input_path or refresh):
        raise ValueError('replay requiere la carpeta del lote y refresh=false.')
    destination = folder / 'input.json'
    requested = {'mode': mode, 'input_path': input_path, 'refresh': refresh}
    if destination.exists():
        info = read(destination)
        if info['requested'] != requested:
            raise ValueError('La ejecucion ya tiene otros parametros; iniciar una nueva.')
        if mode == 'replay':
            validate_replay(project_path(info['batch_path']))
        elif sha256_file(project_path(info['source_path'])) != info['source_sha256']:
            raise ValueError('La copia de entrada fue modificada.')
        return info
    if mode == 'replay':
        batch = project_path(input_path)
        summary = validate_replay(batch)
        info = {'batch_path': str(batch), 'source_sha256': summary['source_sha256'], 'records': summary['records']}
    else:
        if mode == 'reference':
            if input_path:
                raise ValueError('reference descarga la referencia oficial; usar curated para otro Excel.')
            run(['scripts/fetch_reference.py'], folder, 'prepare')
            source = ROOT / 'data/reference/PPB-Affinity.zenodo-14271435.xlsx'
        else:
            if not input_path:
                raise ValueError('curated requiere input_path con el Excel curado.')
            source = project_path(input_path)
        snapshot = folder / source.name
        shutil.copyfile(source, snapshot)
        info = validate_measurements(snapshot)
        info['source_path'] = str(snapshot)
    info.update(requested=requested, prepared_at=now())
    atomic_json(destination, info)
    return info


def now():
    return datetime.now(timezone.utc).isoformat()


def capture(stage, folder, batch):
    if stage in {'bronze', 'silver', 'backbone', 'gold', 'obt', 'profile'}:
        layer = 'profiling' if stage == 'profile' else stage
        latest = read(ROOT / 'reports' / layer / 'latest.json')['run']
        source = ROOT / 'reports' / layer / latest / ('profile.json' if stage == 'profile' else 'summary.json')
    elif stage == 'raw':
        source = ROOT / 'reports' / f'raw_load_{batch.name}.json'
    elif stage == 'dictionary':
        source = ROOT / 'reports/obt_dictionary_validation.json'
    else:
        return None
    target = folder / (stage + '_evidence.json')
    shutil.copyfile(source, target)
    return {'path': str(source.relative_to(ROOT)), 'sha256': sha256_file(target)}


def finish(folder):
    receipts = [read(folder / (s + '.json')) for s in STAGES[:-1]]
    if any(x['status'] != 'SUCCESS' for x in receipts):
        raise ValueError('No todas las etapas estan validadas.')
    obt = read(folder / 'obt_evidence.json')
    raw = read(folder / 'raw_evidence.json')
    batch = read(folder / 'extraction.json')
    info = read(folder / 'input.json')
    if raw['batch_id'] != batch['run_id'] or raw['source_records'] != info['records']:
        raise ValueError('El recibo RAW no corresponde al lote de esta ejecucion.')
    counts = {'bronze': read(folder/'bronze_evidence.json')['tables']['AFFINITY_OBSERVATIONS']['rows'],
              'silver': read(folder/'silver_evidence.json')['tables']['AFFINITY_OBSERVATIONS']['rows'],
              'gold': read(folder/'gold_evidence.json')['tables']['FACT_AFFINITY']['rows'],
              'obt': obt['rows']}
    if len(set(counts.values())) != 1:
        raise ValueError('Las capas no conservan el mismo numero de observaciones.')
    for layer in ('bronze', 'silver', 'backbone', 'gold'):
        evidence = read(folder / (layer + '_evidence.json'))
        if evidence['tests'] != evidence['tests_passed'] or not evidence['replay_verified']:
            raise ValueError('Pruebas o repeticion sin verificar en ' + layer)
    if not raw['replay_verified'] or not read(folder/'profile_evidence.json')['raw_unchanged']:
        raise ValueError('RAW no tiene evidencia completa de conservacion.')
    if read(folder/'dictionary_evidence.json')['documented_columns'] != obt['columns']:
        raise ValueError('El diccionario no cubre la OBT.')
    result = {'execution_id': folder.name, 'status': 'SUCCESS', 'finished_at': now(),
              'input': read(folder / 'input.json'), 'batch': read(folder / 'extraction.json'),
              'stages': receipts, 'observation_counts': counts, 'raw': raw, 'obt': obt}
    atomic_json(folder / 'summary.json', result)
    lines = ['# Ejecucion completa del pipeline', '', f'Ejecucion Kestra: `{folder.name}`.',
             f"Lote: `{raw['batch_id']}`. Filas en el lote: {raw['source_records']}.",
             f"Repeticion del MERGE verificada: {raw['replay_verified']}.",
             f"OBT: **{obt['rows']} filas × {obt['columns']} columnas**. Bronze, Silver y Gold conservan el mismo numero de observaciones.", '',
             '| Etapa | Estado | Segundos |', '|---|---|---:|']
    lines += [f"| {x['stage']} | {x['status']} | {x['seconds']} |" for x in receipts]
    lines += ['', 'El detalle de conteos, huellas y pruebas esta en los recibos *_evidence.json de esta carpeta.',
              'Esta ejecucion usa la cuenta configurada en .env. No prueba por si sola una cuenta nueva.',
              'No hay cron: el lote curado se entrega manualmente; las etapas posteriores son automaticas.',
              'RAW conserva lotes previos. Bronze, Silver, Gold y OBT se reconstruyen sobre el historial acumulado.']
    (folder / 'summary.md').write_text('\n'.join(lines) + '\n')
    atomic_json(ROOT / 'reports/pipeline/latest.json', {'execution_id': folder.name})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=STAGES)
    parser.add_argument('--execution', default=os.getenv('PIPELINE_EXECUTION_ID'), required=False)
    args = parser.parse_args()
    if not args.execution or not re.fullmatch(r'[A-Za-z0-9_-]+', args.execution):
        parser.error('execution debe ser un identificador de Kestra valido')
    load_dotenv(ROOT / '.env')
    if os.getenv('SNOWFLAKE_DATABASE') != 'PROTEIN_AFFINITY':
        raise ValueError('Este proyecto usa la base PROTEIN_AFFINITY; ejecutar su bootstrap en la cuenta elegida.')
    folder = ROOT / 'reports/pipeline' / args.execution
    folder.mkdir(parents=True, exist_ok=True)
    stage = args.stage; start = time.monotonic()
    index = STAGES.index(stage)
    if index and read(folder / (STAGES[index-1] + '.json'))['status'] != 'SUCCESS':
        raise ValueError('La etapa anterior no termino correctamente.')
    receipt = {'stage': stage, 'started_at': now(), 'status': 'RUNNING'}
    atomic_json(folder / (stage + '.json'), receipt)
    try:
        if stage == 'prepare':
            mode = os.environ.get('PIPELINE_MODE', 'reference')
            if mode not in {'reference', 'curated', 'replay'}:
                raise ValueError('Modo invalido')
            prepare(folder, mode, os.environ.get('PIPELINE_INPUT', ''), os.environ.get('RCSB_REFRESH', 'false') == 'true')
            run(['scripts/check_snowflake.py'], folder, stage)
        elif stage == 'extract':
            info = read(folder / 'input.json'); mode = info['requested']['mode']
            output = folder / 'extraction.json'
            if mode == 'replay':
                batch = project_path(info['batch_path']); validate_replay(batch)
                atomic_json(output, {'batch_path': str(batch), 'run_id': batch.name})
            elif not output.exists():
                source = project_path(info['source_path'])
                if sha256_file(source) != info['source_sha256']:
                    raise ValueError('La entrada cambio despues de validarla.')
                command = ['scripts/extract_rcsb.py', '--input', str(source), '--result-file', str(output)]
                if info['requested']['refresh']: command.append('--refresh')
                run(command, folder, stage)
            validate_replay(project_path(read(output)['batch_path']))
        elif stage == 'finish':
            finish(folder)
        else:
            batch = project_path(read(folder / 'extraction.json')['batch_path'])
            command = list(COMMANDS[stage])
            if stage == 'raw': command.extend(['--batch', str(batch)])
            run(command, folder, stage)
            receipt['evidence'] = capture(stage, folder, batch)
        receipt.update(status='SUCCESS', finished_at=now(), seconds=round(time.monotonic()-start, 2))
    except Exception as exc:
        receipt.update(status='FAILED', error=str(exc), finished_at=now(), seconds=round(time.monotonic()-start, 2))
        raise
    finally:
        atomic_json(folder / (stage + '.json'), receipt)
    print('::' + json.dumps({'outputs': {'execution_id': folder.name, 'stage': stage, 'status': 'SUCCESS'}}) + '::', flush=True)


if __name__ == '__main__':
    main()
