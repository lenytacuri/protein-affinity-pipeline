"""Contraste independiente del perfil SQL contra el Excel principal original.

Ejecutar tras profile_raw.py. No consulta ni modifica Snowflake.
Esta verificacion corresponde al snapshot principal unico; no mezcla versiones.
"""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

from openpyxl import load_workbook


def main():
    root=Path(__file__).resolve().parents[1]
    latest=json.loads((root/'reports/profiling/latest.json').read_text())
    folder=root/'reports/profiling'/latest['run']
    results=json.loads((folder/'profile.json').read_text())['results']
    source=root/'data/reference/PPB-Affinity.zenodo-14271435.xlsx'
    sha=hashlib.sha256(source.read_bytes()).hexdigest()
    assert {r['source_sha256'] for r in results['source_versions']}=={sha}, 'El perfil incluye otras versiones.'
    wb=load_workbook(source,read_only=True,data_only=True)
    stream=wb.active.iter_rows(values_only=True)
    headers=[str(v) if v is not None else f'_unnamed_{i}' for i,v in enumerate(next(stream))]
    rows=[dict(zip(headers,row)) for row in stream if any(v is not None for v in row)]
    wb.close()
    assert len(rows)==results['overview'][0]['rows_total']
    assert len({x['PDB'] for x in rows})==results['overview'][0]['unique_pdb_ids']
    for item in results['completeness']:
        actual=sum(x.get(item['field']) is None or str(x.get(item['field'])).strip()=='' for x in rows)
        assert actual==item['missing_total'],(item['field'],actual,item['missing_total'])
    counts=Counter(x['Source Data Set'] for x in rows)
    assert counts=={x['source_dataset']:x['rows_total'] for x in results['source_versions']}
    positive=sum(isinstance(x['KD(M)'],(int,float)) and math.isfinite(x['KD(M)']) and x['KD(M)']>0 for x in rows)
    assert positive==results['numeric_validity'][0]['kd_positive_finite']
    assert sum('assum' in str(x['Temperature(K)']).lower() for x in rows)==results['numeric_validity'][0]['temperature_assumed_label']
    complex_ids=Counter(x['Complex ID'] for x in rows)
    paper=results['paper_complex_id_uniqueness'][0]
    assert len(complex_ids)==paper['unique_complex_ids']
    assert sum(n-1 for n in complex_ids.values())==paper['repeated_complex_ids']
    exact=Counter(json.dumps({k:v for k,v in x.items() if k!='_unnamed_0'},sort_keys=True,default=str) for x in rows)
    assert sum(n>1 for n in exact.values())==len(results['exact_duplicate_groups'])
    checks=['source_file_hash','row_count','distinct_pdb','all_19_field_missing_counts','source_counts',
            'positive_finite_affinities','assumed_temperatures','exact_duplicate_groups','paper_complex_id_uniqueness']
    result={'check':'independent_original_excel','status':'PASS','rows':len(rows),'fields_checked':len(headers),
            'source_counts':dict(counts),'kd_positive_finite':positive,'checks':checks}
    (folder/'excel_crosscheck.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
