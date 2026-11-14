"""Contrato del Excel curado: columnas reconocidas por Bronze, sin inventar afinidades."""
from pathlib import Path
from openpyxl import Workbook
from source_inputs import read_source, normalize_pdb

COLUMNS = ['Source Data Set', 'Complex ID', 'PDB', 'Mutations', 'Ligand Chains',
           'Receptor Chains', 'Ligand Name', 'Receptor Name', 'KD(M)', 'Affinity Method',
           'Structure Method', 'Temperature(K)', 'Resolution(Å)', 'PDB PubMed ID',
           'PDB Release Date', 'Affinity PubMed ID', 'Affinity Release Date', 'Subgroup']
REQUIRED = {'Source Data Set', 'Complex ID', 'PDB', 'Ligand Chains', 'Receptor Chains', 'KD(M)'}


def validate_measurements(path):
    if Path(path).suffix.lower() != '.xlsx':
        raise ValueError('El pipeline de afinidad requiere Excel .xlsx; una lista PDB no contiene mediciones.')
    rows, ids, sha = read_source(path, 'excel')
    missing = REQUIRED - rows[0]['payload'].keys()
    if missing:
        raise ValueError('Faltan columnas del contrato: ' + ', '.join(sorted(missing)))
    seen = set()
    for row in rows:
        payload = row['payload']
        # Estos campos tienen restricciones not_null en Bronze. Los demás faltantes
        # o valores experimentales inválidos se conservan y se perfilan, no se imputan.
        if not normalize_pdb(payload.get('PDB')) or any(
                payload.get(k) is None or not str(payload[k]).strip()
                for k in ('Source Data Set', 'Complex ID')):
            raise ValueError(f"Fila {row['source_row']}: revisar PDB, Source Data Set y Complex ID antes de ingresar.")
        key = str(payload['Complex ID'])
        if key in seen:
            raise ValueError(f"Fila {row['source_row']}: Complex ID repetido dentro del lote; distinguir las observaciones.")
        seen.add(key)
    return {'records': len(rows), 'unique_pdb_ids': len(ids), 'source_sha256': sha}


def template(path):
    path = Path(path)
    if path.exists():
        raise FileExistsError('La plantilla no sobrescribe un archivo existente.')
    path.parent.mkdir(parents=True, exist_ok=True)
    book = Workbook(); book.active.title = 'Measurements'; book.active.append(COLUMNS)
    book.save(path)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--template', required=True, type=Path)
    args = parser.parse_args(); template(args.template)
    print('Plantilla vacia creada:', args.template)
