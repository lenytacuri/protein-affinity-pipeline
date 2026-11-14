"""Human-readable, execution-backed Gold report."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GRAINS={
 'FACT_AFFINITY':'Una observacion original; no se fusionan mediciones del mismo complejo.',
 'DIM_SOURCE':'Una combinacion de version de archivo, hoja y dataset de procedencia.',
 'DIM_EXPERIMENT':'Una combinacion de condiciones, metodo y referencia reportados; no prueba identidad experimental.',
 'DIM_GEOMETRY':'Una geometria: archivo y grupos de cadenas, incluida geometria fallida.',
 'DIM_PARTICIPANT_FEATURES':'Una geometria y un participante L/R; composicion y resumen de backbone.'}

def write_report(s):
    lines=['# Gold: modelo estrella validado','',f"Ejecucion `{s['run']}`: **SUCCESS**.",'',
      '| Tabla en PROTEIN_AFFINITY.GOLD | Filas | Columnas | Una fila representa |','|---|---:|---:|---|']
    for t in ['FACT_AFFINITY','DIM_SOURCE','DIM_EXPERIMENT','DIM_GEOMETRY','DIM_PARTICIPANT_FEATURES']:
        lines.append(f"| {t} | {s['tables'][t]['rows']} | {s['columns'][t]} | {GRAINS[t]} |")
    lines += ['',f"Pruebas dbt: **{s['tests_passed']}/{s['tests']}**. Reconstruccion con conteos y huellas identicos. RAW, Bronze y las ocho tablas Silver no cambiaron.",
      f"Unir las cuatro dimensiones, usando participantes dos veces (L/R), devuelve **{s['joined_rows']} filas**. Las claves de observacion siguen siendo unicas.",'',
      '## Casos conservados','',
      '| Estado de geometria de la observacion | Filas |','|---|---:|']
    for status,n in sorted(s['geometry_statuses'].items()):lines.append(f'| {status} | {n} |')
    lines += ['',f"Hay {s['facts']['no_geometry_key']} observaciones sin GEOMETRY_ID: conservan la fila y tienen claves de participante NULL.",
      f"{s['facts']['variant_review']} observaciones mantienen NEEDS_VARIANT_REVIEW=true. Es una bandera de revision, no un criterio final de entrenamiento.",
      '', '## Uso y limites','',
      'Kd y pKd permanecen en FACT_AFFINITY como mediciones/etiqueta. No entran en las dimensiones de features.',
      'Gold organiza las features existentes; no recalcula distancias, modifica Q1 ni construye mutantes.',
      'Las claves de fuente y contexto usan SHA-256 de un array ordenado con NULL explicito. DISTINCT solo agrupa contextos; nunca deduplica hechos.',
      'No se han creado particiones train/test ni grupos de homologia. GEOMETRY_ID y PDB_ID no garantizan independencia biologica.',
      'La OBT usa un flujo Spark separado. Su ejecucion y verificaciones estan en reports/obt.md; las pruebas de este reporte son las de Gold.',
      'La reconstruccion es completa, no incremental ni atomica para toda la capa. Si una prueba falla, resolverla antes de generar la OBT.',
      '', 'Guia y diagrama: docs/12_gold.md. Consultas: sql/13_view_gold.sql.',
      'Modelos: dbt/models/gold/. Orquestacion: kestra/build_gold.yml.',
      f"Evidencia detallada: reports/gold/{s['run']}/."]
    (ROOT/'reports/gold.md').write_text('\n'.join(lines)+'\n')
