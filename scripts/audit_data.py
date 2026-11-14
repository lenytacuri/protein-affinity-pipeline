"""Auditoría de presencia, no de validez geométrica. No modifica las fuentes."""
import argparse
import csv
import hashlib
import json
import zipfile
import zlib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import load_workbook

OFFICIAL_MD5 = '032a5ce1f24212aef5cdedf8117ef084'
SOURCES = {
    'SKEMPI v2.0': ('SKEMPI v2.0', str.upper, '.pdb'),
    'ATLAS': ('ATLAS', str.upper, '.pdb'),
    'SAbDab': ('SAbDab', str.lower, '.pdb'),
    'Affinity Benchmark v5.5': ('Affinity Benchmark v5.5', str.upper, '.pdb'),
    'PDBbind v2020': ('PDBbind v2020', str.lower, '.ent.pdb'),
}


def read_table(path):
    book = load_workbook(path, read_only=True, data_only=True)
    sheet = book.worksheets[0]
    iterator = sheet.iter_rows(values_only=True)
    headers = [str(v) if v is not None else '_source_index' for v in next(iterator)]
    rows = [dict(zip(headers, row)) for row in iterator if any(v is not None for v in row)]
    book.close()
    return headers, rows


def write_csv(path, rows, fields):
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-root', type=Path, default=Path('/data'))
    parser.add_argument('--reference-dir', type=Path, default=Path('/reference'))
    parser.add_argument('--output-dir', type=Path, default=Path('/reports'))
    args = parser.parse_args()
    root, ref, out = args.data_root, args.reference_dir, args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    official = ref / 'PPB-Affinity.zenodo-14271435.xlsx'
    md5 = hashlib.md5(official.read_bytes()).hexdigest()
    if md5 != OFFICIAL_MD5:
        raise ValueError('La tabla oficial no coincide con la huella publicada por Zenodo.')
    headers, rows = read_table(official)
    coverage = []
    for number, row in enumerate(rows, start=2):
        source, pdb = str(row['Source Data Set']).strip(), str(row['PDB']).strip()
        if source not in SOURCES:
            raise ValueError(f'Fuente sin regla de localización: {source}')
        folder, casing, suffix = SOURCES[source]
        relative = Path('PDB') / folder / (casing(pdb) + suffix)
        path = root / relative
        status = 'present' if path.is_file() and path.stat().st_size else 'missing_or_empty'
        coverage.append({'dataset': 'main', 'source_row': number, 'source': source,
                         'structure_id': pdb, 'expected_path': str(relative), 'status': status})
    af_path = root / 'PPB-Affinity-AF' / 'PPB-Affinity-AF.xlsx'
    af_rows = None
    if af_path.exists():
        _, af_rows = read_table(af_path)
        for number, row in enumerate(af_rows, start=2):
            pdb = str(row['PDB']).strip()
            relative = Path('PPB-Affinity-AF/PDB') / (pdb + '.pdb')
            path = root / relative
            status = 'present' if path.is_file() and path.stat().st_size else 'missing_or_empty'
            coverage.append({'dataset': 'af_local', 'source_row': number, 'source': 'alphafold3',
                             'structure_id': pdb, 'expected_path': str(relative), 'status': status})
    write_csv(out/'coverage.csv', coverage, list(coverage[0]))
    unique = {r['expected_path']: {k:v for k,v in r.items() if k!='source_row'} for r in coverage}
    missing = [r for r in unique.values() if r['status']!='present']
    write_csv(out/'missing_structures.csv', missing,
              ['dataset','source','structure_id','expected_path','status'])
    inventory = []
    for folder in ['PDB','PPB-Affinity-AF','sabdab_search_structures_20260911T200227','splits_final']:
        base = root/folder
        if not base.exists(): continue
        for path in sorted(base.rglob('*')):
            if path.is_file() and path.name!='.DS_Store':
                inventory.append({'collection': folder, 'relative_path': str(path.relative_to(root)),
                                  'bytes': path.stat().st_size, 'extension': path.suffix.lower()})
    write_csv(out/'inventory.csv', inventory, ['collection','relative_path','bytes','extension'])
    differences = []
    local = ref/'PPB-Affinity.local-copy.xlsx'
    comparison = {'local_copy_present': local.exists()}
    if local.exists():
        local_headers, local_rows = read_table(local)
        comparison.update({'local_md5':hashlib.md5(local.read_bytes()).hexdigest(),
                           'local_rows':len(local_rows), 'headers_equal':headers==local_headers,
                           'comparison_method':'cell_by_cell_in_source_order'})
        for i in range(max(len(rows),len(local_rows))):
            a = rows[i] if i < len(rows) else {}
            b = local_rows[i] if i < len(local_rows) else {}
            for key in sorted(set(headers)|set(local_headers)):
                if a.get(key)!=b.get(key):
                    differences.append({'source_row':i+2,'column':key,
                                        'official_value':a.get(key),'local_value':b.get(key)})
        comparison['different_cells_in_source_order'] = len(differences)
    write_csv(out/'workbook_differences.csv',differences,
              ['source_row','column','official_value','local_value'])
    summary = {
        'generated_at_utc':datetime.now(timezone.utc).isoformat(),
        'scope':'Presence and nonempty files only; chain validity and structural equivalence not checked.',
        'official_record':'https://zenodo.org/records/14271435', 'official_md5':md5,
        'main_records':len(rows), 'main_unique_pdb_ids':len({str(r['PDB']).upper() for r in rows}),
        'af_local_records':None if af_rows is None else len(af_rows),
        'by_source':{}, 'missing_unique_paths':len(missing), 'workbook_comparison':comparison,
        'inventory_files':len(inventory), 'inventory_bytes':sum(r['bytes'] for r in inventory),
    }
    archive_path = ref/'PPB-Affinity-AF.zip'
    if archive_path.exists():
        if hashlib.md5(archive_path.read_bytes()).hexdigest()!='9d9fee20ba63f71117772a996e635d7e':
            raise ValueError('El paquete AF no coincide con Zenodo.')
        with zipfile.ZipFile(archive_path) as archive:
            members=[i for i in archive.infolist() if i.filename.endswith('.pdb') and not i.filename.startswith('__MACOSX')]
            names={Path(i.filename).stem for i in members}
            bad=[]
            for item in members:
                local_path=root/'PPB-Affinity-AF/PDB'/Path(item.filename).name
                if not local_path.exists() or zlib.crc32(local_path.read_bytes())!=item.CRC:
                    bad.append(Path(item.filename).name)
            summary['official_af_archive']={
                'structure_files':len(members),'local_missing_or_crc_mismatch':bad,
                'table_ids_without_own_structure':sorted({str(r['PDB']) for r in (af_rows or [])}-names),
                'interpretation':'Own mutant files absent from official archive; do not treat as download loss or silently substitute wild type.'}
    for source in sorted({r['source'] for r in coverage}):
        subset=[r for r in coverage if r['source']==source]
        summary['by_source'][source]={
            'records':len(subset),'unique_paths':len({r['expected_path'] for r in subset}),
            'records_with_file':sum(r['status']=='present' for r in subset),
            'missing_unique_paths':len({r['expected_path'] for r in subset if r['status']!='present'})}
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    lines=['# Auditoría inicial de archivos','',
           'Comprueba presencia y tamaño no nulo. No certifica cadenas, geometría ni equivalencia estructural.',
           '',f'Registros principales: {len(rows)}. PDB distintos: {summary["main_unique_pdb_ids"]}.',
           '', '| Fuente | Registros | Rutas únicas | Registros con archivo | Rutas faltantes |',
           '|---|---:|---:|---:|---:|']
    for source,stats in summary['by_source'].items():
        lines.append(f'| {source} | {stats["records"]} | {stats["unique_paths"]} | {stats["records_with_file"]} | {stats["missing_unique_paths"]} |')
    af_status=summary.get('official_af_archive')
    af_note=('El paquete oficial AF contiene '+str(af_status['structure_files'])+
             ' PDB. Archivos locales ausentes o con CRC diferente: '+str(len(af_status['local_missing_or_crc_mismatch']))+
             '. Las 25 variantes HER2 no tienen archivo propio en el paquete oficial; no son 25 descargas perdidas. '
             'La correspondencia biológica con la referencia HER2-data-wt requiere validación posterior.'
             if af_status else 'La cobertura AF se compara con la tabla local; falta contrastarla con el paquete oficial.')
    lines += ['', af_note,
              '', 'Las otras colecciones se inventarían, pero no se incorporan automáticamente al universo de afinidades.',
              '', '## Comparación de tablas', '', json.dumps(comparison,ensure_ascii=False,indent=2),
              '', 'Una huella diferente no implica valores diferentes. La comparación de celdas usa el orden de las filas.',
              '', 'Archivos detallados: coverage.csv, missing_structures.csv, workbook_differences.csv, inventory.csv, summary.json.']
    (out/'audit.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
