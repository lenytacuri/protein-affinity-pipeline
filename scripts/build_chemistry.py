"""Construye solo la tabla quimica usando Silver existente; no recalcula distancias."""
from datetime import datetime,timezone
import fcntl
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from check_snowflake import connect
from run_bronze import fingerprints,RAW_TABLES,TABLES as BRONZE_TABLES
from run_silver import run_dbt,SILVER_TABLES

ROOT=Path(__file__).resolve().parents[1]

def main():
    load_dotenv(ROOT/'.env')
    key=Path(os.environ['SNOWFLAKE_PRIVATE_KEY_FILE']);os.environ['DBT_PRIVATE_KEY_PATH']=str(key if key.is_absolute() else ROOT/key)
    out=ROOT/'reports/chemistry';out.mkdir(parents=True,exist_ok=True)
    # Same lock as full Silver; avoid overlapping dbt builds on shared tables/artifacts.
    with (ROOT/'reports/silver/.build.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        run=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');folder=out/run;folder.mkdir()
        latest=json.loads((ROOT/'reports/silver/latest.json').read_text())['run']
        previous=json.loads((ROOT/'reports/silver'/latest/'summary.json').read_text())
        prefix=previous['geometry_prefix']
        parents=tuple(t for t in SILVER_TABLES if t!='INTERFACE_CHEMISTRY')
        before={'RAW':fingerprints('RAW',RAW_TABLES),'BRONZE':fingerprints('BRONZE',BRONZE_TABLES),'SILVER':fingerprints('SILVER',parents)}
        try:
            run_dbt(folder,prefix,['build'],'build','tag:chemistry')
            first=fingerprints('SILVER',('INTERFACE_CHEMISTRY',))
            run_dbt(folder,prefix,['build'],'replay','tag:chemistry')
            if fingerprints('SILVER',('INTERFACE_CHEMISTRY',))!=first:raise ValueError('Reconstruccion diferente')
            after={'RAW':fingerprints('RAW',RAW_TABLES),'BRONZE':fingerprints('BRONZE',BRONZE_TABLES),'SILVER':fingerprints('SILVER',parents)}
            if before!=after:raise ValueError('Tablas de entrada cambiaron')
            run_dbt(folder,prefix,['docs','generate'],'docs','tag:chemistry')
            with connect() as conn,conn.cursor() as cur:
                cur.execute('SELECT CHEMISTRY_STATUS,COUNT(*) FROM SILVER.INTERFACE_CHEMISTRY GROUP BY 1')
                statuses=dict(cur.fetchall())
                cur.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='SILVER' AND TABLE_NAME='INTERFACE_CHEMISTRY'")
                columns=cur.fetchone()[0]
            results=json.loads((folder/'build_run_results.json').read_text())['results']
            tests=[r for r in results if r['unique_id'].startswith('test.')]
            summary={'run':run,'status':'SUCCESS','tables':first,'columns':columns,'statuses':statuses,
                'tests':len(tests),'tests_passed':sum(t['status']=='pass' for t in tests),
                'parent_tables_unchanged':True,'replay_verified':True,'geometry_prefix':prefix,'source_silver_run':latest}
            (folder/'summary.json').write_text(json.dumps(summary,indent=2));(out/'latest.json').write_text(json.dumps({'run':run}))
            lines=['# Caracteristicas quimicas de la seleccion Q1','',
                f"Tabla: **PROTEIN_AFFINITY.SILVER.INTERFACE_CHEMISTRY**. Filas: **{first['INTERFACE_CHEMISTRY']['rows']}**. Columnas: **{columns}**.",
                'Una fila por geometria y participante (L/R), no por observacion experimental.',
                f"Pruebas: **{summary['tests_passed']}/{summary['tests']}**. Repeticion identica. Las tablas anteriores permanecen intactas.",'',
                '| Estado | Filas | Significado |','|---|---:|---|']
            definitions={'complete':'Todos los residuos seleccionados tienen propiedades soportadas.',
                'partial_coverage':'Parte de la seleccion tiene residuos modificados o no soportados.',
                'no_supported_residues':'Hay seleccion, pero no residuos con propiedades soportadas.',
                'empty_selection':'El criterio estricto < Q1 no selecciono residuos; fracciones y medias son NULL.',
                'geometry_unavailable':'No fue posible calcular geometria; los conteos son NULL, no cero.'}
            for status,n in sorted(statuses.items()):lines.append(f'| {status} | {n} | {definitions[status]} |')
            lines += ['', 'Las fracciones usan N_SUPPORTED como denominador. PROPERTY_COVERAGE=N_SUPPORTED/N_SELECTED informa cobertura.',
                'Las clases basica y acida no son cargas medidas. La histidina se incluye en la clase basica y en el grupo con anillo aromatico.',
                'La hidropatia media usa Kyte-Doolittle; AA_ENTROPY_BITS describe diversidad composicional, no entropia termodinamica.',
                'Las propiedades corresponden a residuos observados en la estructura, sin aplicar mutaciones anotadas en el Excel.',
                '', 'Guia y diccionario: docs/10_chemical_features.md. Consulta: sql/10_view_chemistry.sql.',
                'Modelo: dbt/models/silver/silver_interface_chemistry.sql. Propiedades: dbt/macros/amino_acid_properties.sql.']
            (ROOT/'reports/chemistry.md').write_text('\n'.join(lines)+'\n')
            print(json.dumps(summary,indent=2),flush=True)
        except Exception as exc:
            (folder/'failure.json').write_text(json.dumps({'error':str(exc),'run':run},indent=2));raise

if __name__=='__main__':main()
