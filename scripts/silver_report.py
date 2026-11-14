"""Reporte legible de una ejecucion Silver ya validada, sin consultar credenciales."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

DEFINITIONS={
 'computed':'Se pudieron calcular distancias con las cadenas y CA disponibles; no confirma el ensamblaje biologico.',
 'structure_not_usable':'La estructura no permite este calculo: revisar el motivo en STRUCTURE_GEOMETRY.ISSUE.',
 'structure_missing':'No se encontro una estructura disponible para la version de entrada.',
 'invalid_chain_groups':'Los grupos de cadenas estan vacios, repetidos, superpuestos o no se pudieron interpretar.',
 'not_annotated':'No hay mutacion anotada; no demuestra que la proteina sea tipo silvestre.',
 'structure_unavailable':'No se pudo contrastar la mutacion porque la geometria no pudo obtenerse.',
 'target_residues_present':'Las posiciones anotadas contienen los aminoacidos destino. No valida toda la conformacion del mutante.',
 'reference_geometry_only':'Al menos una posicion conserva el aminoacido anterior a la mutacion; la geometria es una referencia.',
 'needs_review':'Hay anotaciones no interpretadas, posiciones ausentes o residuos que no coinciden con origen ni destino.'}


def write_report(summary):
    s=summary
    lines=['# Silver: resultado y significado','',f"Ejecucion `{s['run']}`: **SUCCESS**.",'',
       f"Se conservaron **{s['observations']:,} observaciones**. Calculo local con **{s['workers']} procesos CPU**.",
       f"Las **{s['tests_passed']}/{s['tests']} pruebas dbt** pasaron. RAW y Bronze permanecen intactas.",
       f"Reconstruccion con contenido identico: **{s['replay_verified']}**.",'',
       '## Que contiene cada tabla','', '| Tabla | Filas | Significado |','|---|---:|---|']
    meanings={'INTERFACE_CHEMISTRY':'Composicion, polaridad e hidropatia por geometria y participante seleccionado por Q1.',
      'AFFINITY_OBSERVATIONS':'Observaciones originales con pKd, temperatura interpretada y estados.',
      'OBSERVATION_GEOMETRY':'Relacion de cada observacion con su geometria; conserva mediciones separadas.',
      'STRUCTURE_GEOMETRY':'Grupos de cadenas por archivo/version, incluidos casos no calculables.',
      'INTERFACE_RESIDUES':'Todos los CA utilizables; SELECTED_Q1 indica cuales cumplen el criterio.',
      'RESIDUE_PAIRS':'Todos los pares entre los residuos seleccionados de ambos participantes, sin corte fijo de distancia.'}
    for name,counts in s['tables'].items():lines.append(f"| {name} | {counts['rows']:,} | {meanings[name]} |")
    lines += ['', '## Criterio de seleccion', '',
       '**Q1 del minimo por residuo, separado por participante.** Se calcula la distancia de cada CA a su vecino mas cercano del otro grupo; despues su percentil 25. Se selecciona usando `< Q1` e interpolacion lineal.',
       'No se usa un corte de 25 angstroms. Los empates pueden producir menos de 25% de seleccionados o ninguno. Los pares guardados no tienen que estar todos cerca entre si.',
       'WITHIN_10 queda como comparacion con el criterio de 10 A; no define la seleccion principal.']
    for title,key in [('Estado geometrico de las observaciones','observation_geometry_status'),('Mutaciones frente a la estructura','mutations')]:
        lines += ['',f'## {title}','','| Estado | Observaciones | Definicion |','|---|---:|---|']
        for status,count in sorted(s[key].items()):lines.append(f'| {status} | {count:,} | {DEFINITIONS.get(status,"Revisar detalle.")} |')
    lines += ['', '## Alcance', '',
      'Se usa el primer modelo depositado y las cadenas de autor. No se reconstruyen ensamblajes biologicos, residuos ausentes ni estructuras mutantes. Un contacto CA no demuestra union experimental.',
      'La composicion corresponde a aminoacidos observados en la estructura. Para entrenar faltara decidir la elegibilidad de cada caso y separar complejos relacionados entre entrenamiento y prueba.',
      '', '## Donde revisar', '',
      '- `docs/09_silver.md`: reglas y reproduccion.',
      '- `sql/08_view_silver.sql`: visualizar observaciones y residuos.',
      '- `sql/09_silver_quality.sql`: estados y pares con identidad de ambas cadenas.',
      '- `scripts/geometry_core.py`: calculo y validacion estructural.',
      '- `dbt/models/silver/`: transformaciones y diccionario de columnas.',
      f"- `reports/silver/{s['run']}/`: logs y evidencia."]
    (ROOT/'reports/silver.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':
    latest=json.loads((ROOT/'reports/silver/latest.json').read_text())['run']
    write_report(json.loads((ROOT/'reports/silver'/latest/'summary.json').read_text()))
