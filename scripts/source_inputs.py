"""Lee la fuente sin limpiar ni descartar mediciones; separa filas de PDB distintos."""
import hashlib
import json
import re
from datetime import date, datetime
from pathlib import Path

from openpyxl import load_workbook


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def normalize_pdb(value):
    text = str(value or '').strip()
    if re.fullmatch(r'[0-9][a-zA-Z0-9]{3}', text):
        return text.upper()
    if re.fullmatch(r'pdb_[a-zA-Z0-9]{8}', text, re.I):
        if re.fullmatch(r'pdb_0000[0-9][a-zA-Z0-9]{3}', text, re.I):
            return text[-4:].upper()
        return text.lower()
    return None


def json_value(value):
    # JSON no tiene un tipo fecha. La copia del Excel conserva el tipo original.
    return value.isoformat() if isinstance(value, (date, datetime)) else value


def read_source(path, mode):
    path = Path(path)
    digest = sha256_file(path)
    records, ids = [], set()
    if mode == 'excel':
        book = load_workbook(path, read_only=True, data_only=True)
        try:
            sheet = book.worksheets[0]
            sheet_name = sheet.title
            iterator = sheet.iter_rows(values_only=True)
            header = next(iterator)
            names = [str(x) if x is not None else f'_unnamed_{i}' for i, x in enumerate(header)]
            if len(names) != len(set(names)):
                raise ValueError('El Excel tiene columnas repetidas; no se puede serializar sin perder campos.')
            if 'PDB' not in names:
                raise ValueError('El Excel necesita una columna PDB.')
            source_rows = [(number, dict(zip(names, map(json_value, row))))
                           for number, row in enumerate(iterator, 2) if any(x is not None for x in row)]
        finally:
            book.close()
    else:
        sheet_name = None
        source_rows = [(number, {'PDB': line.strip()})
                       for number, line in enumerate(path.read_text().splitlines(), 1)
                       if line.strip() and not line.lstrip().startswith('#')]
    for number, payload in source_rows:
        pdb_id = normalize_pdb(payload.get('PDB'))
        record_id = hashlib.sha256(f'{digest}\0{sheet_name}\0{number}'.encode()).hexdigest()
        records.append({'source_record_id': record_id, 'source_sha256': digest,
                        'source_file': path.name, 'sheet': sheet_name, 'source_row': number,
                        'input_kind': 'measurement_table' if mode == 'excel' else 'structure_request',
                        'pdb_id': pdb_id, 'pdb_id_valid': pdb_id is not None, 'payload': payload})
        if pdb_id:
            ids.add(pdb_id)
    if not records:
        raise ValueError('La fuente no contiene registros.')
    return records, sorted(ids), digest


def write_jsonl(path, records):
    with Path(path).open('w', encoding='utf-8') as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + '\n')
