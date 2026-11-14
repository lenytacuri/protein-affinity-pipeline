"""Descarga HTTP con reintentos, validacion de formato y cache por contenido."""
import gzip
import json
import os
from pathlib import Path
import random
import tempfile
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests

from source_inputs import normalize_pdb, sha256_file


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', dir=path.parent, delete=False, encoding='utf-8') as stream:
        temp = Path(stream.name)
        json.dump(data, stream, ensure_ascii=False, indent=2)
    os.replace(temp, path)


def validate_download(path, kind, pdb_id):
    if kind == 'entry':
        body = json.loads(Path(path).read_text())
        if not isinstance(body, dict) or normalize_pdb(body.get('rcsb_id')) != pdb_id:
            raise ValueError('El JSON no identifica la entrada PDB solicitada.')
        return
    # Es validacion de transporte/formato, no certifica el complejo biologico.
    tags, entry, pending_id = set(), None, False
    with gzip.open(path, 'rt', encoding='utf-8') as stream:
        for line in stream:
            parts = line.split()
            if not parts:
                continue
            if pending_id:
                entry, pending_id = normalize_pdb(parts[0].strip("'\"")), False
            if parts[0] == '_entry.id':
                if len(parts) > 1:
                    entry = normalize_pdb(parts[1].strip("'\""))
                else:
                    pending_id = True
            if parts[0] in {'_atom_site.Cartn_x', '_atom_site.Cartn_y', '_atom_site.Cartn_z'}:
                tags.add(parts[0])
        # Leer hasta EOF tambien comprueba el CRC del gzip.
    if entry != pdb_id or len(tags) != 3:
        raise ValueError('mmCIF sin ID esperado o sin columnas de coordenadas atomicas.')


def retry_delay(response, attempt):
    header = response.headers.get('Retry-After') if response is not None else None
    if header:
        try:
            seconds = float(header)
        except ValueError:
            try:
                seconds = (parsedate_to_datetime(header) - datetime.now(timezone.utc)).total_seconds()
            except (ValueError, TypeError):
                seconds = 0
        return max(0, seconds)
    return min(30, 2 ** (attempt - 1)) + random.uniform(0, 0.5)


def fetch_resource(session, root, pdb_id, kind, *, refresh=False, attempts=4):
    root = Path(root)
    extension = 'json' if kind == 'entry' else 'cif.gz'
    url = (f'https://data.rcsb.org/rest/v1/core/entry/{pdb_id}' if kind == 'entry'
           else f'https://files.rcsb.org/download/{pdb_id}.cif.gz')
    index = root / 'index' / pdb_id / f'{kind}.json'
    if index.exists() and not refresh:
        try:
            cached = json.loads(index.read_text())
            artifact = root / cached['path']
            if artifact.is_file() and sha256_file(artifact) == cached['sha256']:
                return {**cached, 'status': 'cached', 'attempts_this_run': 0}
        except (OSError, ValueError, KeyError):
            pass
    (root / 'objects').mkdir(parents=True, exist_ok=True)
    base = {'pdb_id': pdb_id, 'resource': kind, 'source_url': url}
    last_error, last_status = '', None
    for attempt in range(1, attempts + 1):
        response, temp = None, None
        try:
            response = session.get(url, stream=True, timeout=(15, 60),
                                   headers={'User-Agent': 'protein-affinity-course-project/1.0',
                                            'Accept-Encoding': 'identity'})
            last_status = response.status_code
            if last_status in {404, 410}:
                return {**base, 'status': 'not_found', 'http_status': last_status,
                        'checked_at': utc_now(), 'attempts_this_run': attempt,
                        'error': 'Entrada no disponible; no se sustituye por otro PDB automaticamente.'}
            if 400 <= last_status < 500 and last_status not in {408, 429}:
                return {**base, 'status': 'failed', 'http_status': last_status,
                        'checked_at': utc_now(), 'attempts_this_run': attempt,
                        'error': f'HTTP {last_status} no recuperable con reintentos.'}
            response.raise_for_status()
            with tempfile.NamedTemporaryFile('wb', dir=root / 'objects', delete=False) as stream:
                temp = Path(stream.name)
                for block in response.iter_content(chunk_size=1024 * 1024):
                    stream.write(block)
            validate_download(temp, kind, pdb_id)
            sha = sha256_file(temp)
            artifact = root / 'objects' / f'{sha}.{extension}'
            size = temp.stat().st_size
            os.replace(temp, artifact)
            temp = None
            receipt = {**base, 'path': str(artifact.relative_to(root)), 'sha256': sha,
                       'bytes': size, 'retrieved_at': utc_now(), 'http_status': last_status,
                       'response_url': response.url, 'etag': response.headers.get('ETag'),
                       'last_modified': response.headers.get('Last-Modified')}
            atomic_json(index, receipt)
            return {**receipt, 'status': 'downloaded', 'attempts_this_run': attempt}
        except (requests.RequestException, OSError, ValueError, EOFError) as error:
            last_error = f'{type(error).__name__}: {error}'
            if attempt < attempts:
                delay = retry_delay(response, attempt)
                # No bloquear un worker indefinidamente; el siguiente batch reintentara.
                if delay > 120:
                    last_error += '; Retry-After largo: pospuesto al siguiente batch.'
                    break
                time.sleep(delay)
        finally:
            if response is not None:
                response.close()
            if temp is not None:
                temp.unlink(missing_ok=True)
    return {**base, 'status': 'failed', 'http_status': last_status,
            'checked_at': utc_now(), 'attempts_this_run': attempt, 'error': last_error}
