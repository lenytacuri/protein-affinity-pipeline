"""Publica un flujo local y opcionalmente lo ejecuta; nunca imprime credenciales."""
import argparse
import json
import os
from pathlib import Path
import time

from dotenv import load_dotenv
import requests


def wait_for_api(session, endpoint, timeout=180):
    """Docker puede estar iniciado antes de que la API de Kestra este lista."""
    deadline = time.monotonic() + timeout
    while True:
        try:
            response = session.get(endpoint, timeout=10)
            if response.status_code in {200, 404}:
                return response
            if response.status_code in {401, 403}:
                raise RuntimeError('Kestra rechazo el acceso; revisar KESTRA_USER/KESTRA_PASSWORD en .env.')
        except (requests.ConnectionError, requests.Timeout):
            pass
        if time.monotonic() >= deadline:
            raise TimeoutError('Kestra no respondio a tiempo; revisar docker compose logs kestra.')
        time.sleep(3)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('flow', type=Path)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--wait', action='store_true')
    parser.add_argument('--wait-timeout', type=int, default=7200)
    parser.add_argument('--input', action='append', default=[], help='Entrada del flujo: clave=valor')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    load_dotenv(root / '.env')
    base = os.environ.get('KESTRA_URL', 'http://kestra:8080').rstrip('/')
    session = requests.Session()
    session.auth = (os.environ['KESTRA_USER'], os.environ['KESTRA_PASSWORD'])
    source = args.flow.read_text()
    # Las dos claves se leen de lineas superiores, sin interpretar plantillas Pebble.
    fields = dict(line.split(':', 1) for line in source.splitlines()
                  if line.startswith(('id:', 'namespace:')))
    flow_id, namespace = fields['id'].strip(), fields['namespace'].strip()
    endpoint = f'{base}/api/v1/main/flows/{namespace}/{flow_id}'
    existing = wait_for_api(session, endpoint)
    if existing.status_code == 404:
        response = session.post(f'{base}/api/v1/main/flows', data=source.encode(),
                                headers={'Content-Type': 'application/x-yaml'}, timeout=30)
    else:
        existing.raise_for_status()
        response = session.put(endpoint, data=source.encode(),
                               headers={'Content-Type': 'application/x-yaml'}, timeout=30)
    if not response.ok:
        raise RuntimeError(f'Kestra rechazo el flujo ({response.status_code}): {response.text[:2000]}')
    print(f'Flujo publicado: {namespace}/{flow_id}', flush=True)
    if not args.run:
        return
    inputs = {}
    for item in args.input:
        if '=' not in item:
            parser.error('--input requiere clave=valor')
        key, value = item.split('=', 1)
        inputs[key] = (None, value)
    execution = session.post(f'{base}/api/v1/main/executions/{namespace}/{flow_id}',
                             files=inputs or None, timeout=30)
    execution.raise_for_status()
    result = execution.json()
    execution_id = result['id']
    print(f'Execution ID: {execution_id}', flush=True)
    if args.wait:
        deadline = time.monotonic() + args.wait_timeout
        while time.monotonic() < deadline:
            response = session.get(f'{base}/api/v1/main/executions/{execution_id}', timeout=30)
            response.raise_for_status()
            result = response.json()
            state = result['state']['current']
            if state in {'SUCCESS', 'FAILED', 'KILLED', 'WARNING', 'CANCELLED'}:
                output = root / 'reports' / f'kestra_{flow_id}_{execution_id}.json'
                output.parent.mkdir(exist_ok=True)
                output.write_text(json.dumps(result, indent=2))
                print(f'Estado final: {state}. Evidencia: {output}', flush=True)
                if state != 'SUCCESS':
                    raise SystemExit(1)
                return
            time.sleep(2)
        raise TimeoutError(f'Ejecucion aun en curso; consultar Kestra: {execution_id}')


if __name__ == '__main__':
    main()
