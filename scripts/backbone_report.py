"""Readable report for the validated backbone extension."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def write_report(s):
    lines=['# Geometria interna: detalle y resumen','',f"Ejecucion `{s['run']}`: **SUCCESS**.",
      f"CPU local: **{s['workers']} procesos**; calculo de {s['geometries']} geometrias en {s['compute_seconds']} segundos.",
      f"Pruebas dbt: **{s['tests_passed']}/{s['tests']}**. Reconstruccion identica; tablas anteriores intactas.",'',
      '| Tabla | Filas | Significado |','|---|---:|---|',
      f"| BACKBONE_RESIDUES | {s['tables']['BACKBONE_RESIDUES']['rows']} | Una fila por residuo Q1; medidas individuales, motivos de ausencia y atomos usados. |",
      f"| BACKBONE_FEATURES | {s['tables']['BACKBONE_FEATURES']['rows']} | Una fila por geometria y participante; resumen y cobertura para ML clasico. |",'',
      '## Disponibilidad de medidas','','| Medida | Valores disponibles | Residuos Q1 |','|---|---:|---:|']
    for name,n in s['coverage'].items():
        if name!='residues':lines.append(f"| {name} | {n} | {s['coverage']['residues']} |")
    lines+=['','## Estado de los resúmenes','','| Estado | Participantes | Significado |','|---|---:|---|']
    meanings={'complete':'Todos los seleccionados tienen phi, psi, omega y tau calculables.',
      'partial_angles':'Hay angulos ausentes: extremos, atomos no observados/compatibles o enlaces no verificables.',
      'no_valid_angles':'Se conserva la seleccion, pero no hay angulos calculables.',
      'empty_selection':'Q1 estricto no selecciono residuos.',
      'geometry_unavailable':'No hubo geometria CA; conteos y medidas son NULL.'}
    for status,n in sorted(s['statuses'].items()):lines.append(f'| {status} | {n} | {meanings[status]} |')
    lines+=['','## Interpretacion','',
      'Phi y psi describen el residuo actual; omega se asigna al enlace peptidico saliente hacia el siguiente residuo.',
      'Los vecinos pueden estar fuera de Q1. Se comprueba su continuidad en la cadena y una distancia C-N de 0.8 a 1.8 A.',
      'Los atomos deben usar la etiqueta de conformacion del CA original o ser compartidos sin etiqueta. Un CA sin etiqueta solo usa atomos sin etiqueta.',
      'Las torsiones se resumen con medias de seno/coseno y varianza circular. Las longitudes y tau usan media y desviacion poblacional. Se informa cobertura sin imputar valores.',
      'Las coordenadas siguen siendo las observadas; no se construyen mutantes ni ensamblajes biologicos. El criterio Q1 no cambia.',
      '', 'Guia: docs/11_backbone.md. Consulta: sql/12_view_backbone.sql.',
      'Calculo: scripts/backbone_core.py. Resumen: dbt/models/backbone/backbone_features.sql.',
      f"Detalle de motivos y logs: reports/backbone/{s['run']}/."]
    (ROOT/'reports/backbone.md').write_text('\n'.join(lines)+'\n')
