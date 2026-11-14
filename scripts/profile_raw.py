"""Ejecuta sql/05_profile_raw.sql en Snowflake y guarda evidencia y reporte local.

Python coordina y escribe archivos. Las metricas del perfil se calculan con SQL.
No modifica datos persistentes ni crea Bronze.
"""
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

from snowflake.connector.util_text import split_statements
from check_snowflake import connect

ROOT = Path(__file__).resolve().parents[1]


def json_default(value):
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    return str(value)


def table(rows, columns):
    def cell(value):
        if value is None:
            return 'NULL'
        return str(value).replace('|', '\\|').replace('\n',' ')
    return ['| ' + ' | '.join(label for _,label in columns) + ' |',
            '|' + '|'.join('---' for _ in columns) + '|'] + [
                '| ' + ' | '.join(cell(row.get(key)) for key,_ in columns) + ' |' for row in rows]


def make_report(results, stamp, folder, unchanged):
    overview=results['overview'][0]
    numeric=results['numeric_validity'][0]
    complete={row['field']:row for row in results['completeness']}
    chains=results['chain_annotations'][0]
    exact=results['exact_duplicate_groups']
    candidates=results['candidate_measurement_groups']
    broad=results['broad_candidate_groups']
    incidents=results['resource_coverage']
    resolution=results['metadata_resolution_comparison'][0]
    n=overview['rows_total']
    def missing(field):
        row=complete[field]
        return f"{row['missing_total']} / {n} ({row['missing_pct']}%)"
    paper=results['paper_complex_id_uniqueness']
    actions=[
      {'problem':'Unicidad segun Complex ID del paper',
       'evidence':f"{sum(r['unique_complex_ids'] for r in paper)} claves distintas por version, {sum(r['repeated_complex_ids'] for r in paper)} repeticiones y {sum(r['missing_complex_ids'] for r in paper)} ausencias.",
       'action':'Conservar los registros con Complex ID distinto. Usar esta clave como control de unicidad de cada version del dataset.',
       'why':'Es el criterio declarado por los autores. La clave incluye la referencia de afinidad; no prueba por si sola independencia experimental.'},
      {'problem':'Temperatura ausente','evidence':missing('Temperature(K)'),
       'action':'Mantener NULL y bandera de ausencia. No rellenar con 298 K automaticamente.',
       'why':'No conocemos la condicion experimental.'},
      {'problem':'Temperatura con anotacion de supuesto',
       'evidence':f"{numeric['temperature_assumed_label']} filas con texto assum. {numeric['temperature_not_plain_number']} valores no convertibles directamente a numero.",
       'action':'Conservar texto. Extraer numero solo con regla documentada y marcar temperature_is_assumed.',
       'why':'Una temperatura supuesta no es una medicion reportada.'},
      {'problem':'Metodo de afinidad ausente','evidence':missing('Affinity Method'),
       'action':'Mantener NULL y bandera de ausencia. Conservar la afinidad si pasa sus propios controles.',
       'why':'La falta de metodo limita comparabilidad, pero no invalida por si sola el Kd.'},
      {'problem':'Validez numerica de afinidad',
       'evidence':f"{numeric['kd_positive_finite']} positivas finitas. {numeric['kd_missing']} ausentes, {numeric['kd_not_numeric']} no numericas, {numeric['kd_nonpositive']} no positivas, {numeric['kd_nonfinite']} no finitas.",
       'action':'Usar DOUBLE para Kd, conservar unidades M y texto original. Solo Kd positivo finito permite calcular pKd.',
       'why':'La notacion cientifica es valida. Pasar el control numerico no certifica exactitud experimental.'},
      {'problem':'Filas con todos los valores iguales salvo indice exportado',
       'evidence':f"{len(exact)} grupos, {sum(r['n'] for r in exact)} filas involucradas, {sum(r['n']-1 for r in exact)} repeticiones adicionales.",
       'action':'Marcar grupos y revisar procedencia antes de decidir su tratamiento en Silver. No borrar RAW.',
       'why':'La igualdad de valores no prueba que el experimento sea el mismo.'},
      {'problem':'Coincidencias en ocho campos seleccionados (control exploratorio propio)',
       'evidence':f"{len(candidates)} grupos, {sum(r['n'] for r in candidates)} filas. {sum(r['n_sources']>1 for r in candidates)} grupos abarcan mas de una fuente.",
       'action':'Revisar PDB, cadenas, mutacion, Kd, temperatura, metodo y referencia. No deduplicar por PDB.',
       'why':'Campos incompletos pueden agrupar experimentos distintos. Es una señal para revision, no una clave cientifica definitiva.'},
      {'problem':'Coincidencias al ignorar referencia, metodo y temperatura (no son duplicados confirmados)',
       'evidence':f"{len(broad)} grupos, {sum(r['n'] for r in broad)} filas. {sum(r['n_sources']>1 for r in broad)} grupos con varias fuentes.",
       'action':'Conservar las filas por su Complex ID. Consultar broad_candidate_groups.csv para estudiar coincidencias; no fusionarlas por este resultado.',
       'why':'Esta agrupacion omite la referencia que el paper usa para distinguir registros. No demuestra un fallo en su deduplicacion.'},
      {'problem':'Referencias y fechas heterogeneas',
       'evidence':f"{complete['Affinity PubMed ID']['placeholder_tokens']} referencias con tokens por revisar. Fechas y referencias detalladas abajo.",
       'action':'Separar PMID, referencia textual y estado pendiente; conservar precision de fechas parciales.',
       'why':'No inventar DOI/PMID ni completar un año con una fecha diaria ficticia.'},
      {'problem':'Metadatos o estructuras no disponibles',
       'evidence':f"{len(incidents)} PDB afectados, {sum(r['affected_rows'] for r in incidents)} filas. Ver cobertura al final.",
       'action':'Conservar observaciones y estado de cobertura. Recuperar campos del mmCIF cuando sea posible.',
       'why':'Un JSON ausente no implica que falten coordenadas o afinidad.'},
      {'problem':'Mutaciones anotadas',
       'evidence':f"{chains['mutation_annotated']} filas con anotacion no vacia.",
       'action':'Validar variante frente a la estructura. Marcar cuando las features provengan de una estructura de referencia.',
       'why':'Un mismo PDB no garantiza que represente la geometria de cada mutante. Ausencia de anotacion no demuestra tipo silvestre.'},
      {'problem':'Grupos de cadenas y solapamientos',
       'evidence':f"{chains['multichain_ligand']} ligandos y {chains['multichain_receptor']} receptores con varias cadenas. {len(results['chain_overlap_cases'])} filas comparten al menos un identificador entre grupos.",
       'action':'Interpretar listas de cadenas y validar su existencia y separacion en el modelo estructural.',
       'why':'No asumir que cada socio es una sola cadena, ni que las anotaciones bastan para probar un complejo.'},
      {'problem':'Resolucion del Excel frente al JSON RCSB',
       'evidence':f"{resolution['different_over_001_a']} filas ({resolution['pdb_with_difference']} PDB) difieren mas de 0.01 A, entre {resolution['comparable_rows']} comparables.",
       'action':'Conservar ambos valores y procedencia. Revisar versiones antes de elegir una fuente.',
       'why':'El JSON actual puede reflejar revisiones posteriores al paper. La tolerancia de 0.01 A es operativa, no un criterio de calidad estructural.'},
    ]
    lines=['# Perfil de calidad antes de limpiar', '', f'Generado: {stamp} (America/Guayaquil).', '',
           '**Estado: RAW. No se ha creado Bronze ni se han corregido o eliminado observaciones.**', '',
           f"Se analizaron **{n} filas**, **{overview['unique_pdb_ids']} PDB**, **{overview['source_datasets']} fuentes** y **{overview['source_versions']} version(es) del Excel**.",
           f"Claves tecnicas duplicadas: {overview['duplicated_technical_keys']}. Formatos PDB invalidos: {overview['invalid_pdb_format']}. Indice PDB distinto al valor de origen normalizado: {overview['pdb_index_differences']}.",
           f'La huella agregada y los conteos de las cinco tablas RAW permanecieron iguales: **{unchanged}**.', '',
           'Grano: una fila del archivo de origen. Un RECORD_ID identifica version de archivo, hoja y fila; no un experimento independiente.',
           'Alcance: todas las filas measurement_table cargadas. Si se cargan varias versiones del mismo Excel, se perfilan separadamente por version y el total incluye todas. No se selecciona automaticamente la ultima.', '',
           '## Criterio del articulo y correccion de interpretacion', '',
           'Los autores describen una deduplicacion por Complex ID, formado con PDB, cadenas ordenadas, mutaciones ordenadas y referencia de afinidad. Conservan registros de referencias distintas aunque compartan estructura. [Articulo original, Methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC11615212/).', '',
           'La etiqueta anterior candidatos amplios podia sugerir un problema de deduplicacion. Se corrige: son coincidencias bajo una agrupacion nuestra que omite la referencia. No hay evidencia suficiente para calificarlas como errores del dataset.', '',
           'Fila = registro del Excel. Grupo = conjunto de al menos dos filas que coincide en los campos indicados. Fuente = coleccion de origen (por ejemplo SKEMPI o SAbDab), no el articulo experimental.', '',
           f"La regla amplia encuentra {len(broad)} grupos y {sum(r['n'] for r in broad)} filas; {sum(r['n_sources']>1 for r in broad)} grupos tienen varias fuentes. No significa que haya que eliminar esas filas.", '',
           '### Control de Complex ID por version', '']
    lines += table(paper,[('rows_total','Filas'),('unique_complex_ids','Complex ID distintos'),('repeated_complex_ids','Repeticiones'),('missing_complex_ids','Ausentes')])
    lines += ['', '### Ejemplo real: 3G6D', '',
              'Estas filas comparten PDB, grupos de cadenas, ausencia de mutacion anotada y Kd. Sus referencias son diferentes o pendientes (TBD). TBD no acredita un experimento independiente ni uno repetido.', '']
    lines += table(results['paper_example_3g6d'],[('source_dataset','Coleccion'),('affinity_reference','Referencia de afinidad'),('kd_m','Kd (M)'),('affinity_method','Metodo'),('temperature_text','Temperatura')])
    lines += ['', '## Problema, evidencia, accion y justificacion', '']
    lines += table(actions,[('problem','Problema o control'),('evidence','Evidencia'),('action','Accion propuesta'),('why','Justificacion')])
    lines += ['', 'Las acciones son propuestas para las siguientes capas. No se aplicaron en este perfil.', '',
              '## Completitud por campo', '',
              'Ausente = clave que falta, null JSON o cadena vacia/solo espacios. Los tokens TBD, NA, N/A, ?, NULL, NONE y NAN se cuentan aparte para revision; no se sustituyen automaticamente.',
              'Mutations y Subgroup pueden estar vacios por razones de dominio. No todos los campos ausentes constituyen un error.', '']
    lines += table(results['completeness'],[('field','Campo'),('missing_total','Ausentes'),('missing_pct','%'),('placeholder_tokens','Tokens a revisar'),('distinct_non_null','Valores distintos')])
    lines += ['', '## Distribucion por fuente y version', '']
    lines += table(results['source_versions'],[('source_dataset','Fuente'),('rows_total','Filas'),('unique_pdb_ids','PDB distintos'),('source_sha256','SHA-256 del archivo')])
    lines += ['', '## Faltantes y mutaciones por fuente', '']
    lines += table(results['missing_by_source'],[('source_dataset','Fuente'),('rows_total','Filas'),('kd_missing','Kd ausente'),('temperature_missing','Temperatura ausente'),('method_missing','Metodo ausente'),('mutation_annotated','Mutacion anotada')])
    lines += ['', '## Distribuciones numericas', '',
              'Solo conversiones directas y valores finitos. Temperaturas anotadas como assumed no se incluyen en estos estadisticos. Los extremos son candidatos a revisar, no errores automaticos.', '']
    lines += table(results['numeric_distribution'],[('field','Variable'),('n_finite','N'),('minimum','Minimo'),('p25','P25'),('median','Mediana'),('p75','P75'),('maximum','Maximo')])
    lines += ['', '## Formatos de temperatura observados', '']
    lines += table(results['temperature_values'],[('temperature_text','Valor original'),('n','Filas')])
    lines += ['', '## Fechas y referencias', '',
              'Una fecha parcial o una referencia textual requiere conservar su precision y tipo, no descartarla por no ser ISO o un PMID numerico.', '']
    lines += table(results['date_formats'],[('field','Campo'),('missing','Ausentes'),('valid_iso_day','ISO valido'),('invalid_iso_day','ISO invalido'),('year_only','Solo año'),('other_format','Otro formato'),('future_iso_day','ISO futuro')])
    lines += ['']+table(results['reference_formats'],[('field','Campo'),('missing','Ausentes'),('single_numeric_id','Un ID numerico'),('other_reference_format','Otro formato')])
    lines += ['', '## Cobertura de recursos', '',
              'Existencia registrada en las tablas de ingesta. La carga previa verifico archivos en el stage; este perfil no vuelve a abrir los mmCIF ni certifica sus cadenas o coordenadas.', '']
    lines += table(incidents,[('pdb_id','PDB'),('affected_rows','Filas'),('has_structure','Estructura: 1=si'),('has_metadata','JSON: 1=si')]) if incidents else ['No se detectaron recursos faltantes.']
    lines += ['', '## Diferencias de resolucion para revisar', '']
    lines += table(results['metadata_resolution_cases'],[('pdb_id','PDB'),('source_dataset','Fuente'),('excel_resolution','Excel (A)'),('rcsb_resolution','RCSB (A)'),('record_id','RECORD_ID')])
    lines += ['', '## Limites de exactitud', '',
              '- Completitud, formatos, consistencia y cobertura se miden directamente. No equivalen a exactitud cientifica.',
              '- No se han contrastado los Kd con los articulos experimentales, ni validado ensamblajes, cadenas o mutaciones.',
              '- La comparacion de resolucion usa el primer valor resolution_combined del JSON seleccionado. No garantiza equivalencia de muestras ni versiones.',
              '- Los grupos de duplicados y candidatos se solapan. Sus conteos no deben sumarse.',
              '- No se mezclaron los datos de AlphaFold.', '',
              '## Evidencia reproducible', '',
              '- SQL: `sql/05_profile_raw.sql`.',
              '- Ejecutor: `scripts/profile_raw.py`. Python solo ejecuta consultas y escribe el informe.',
              f'- Resultados completos CSV/JSON, identificadores de consulta, huella del SQL y comprobaciones: `reports/profiling/{folder}/`.',
              '- Los CSV de duplicados incluyen RECORD_IDS para recuperar cada fila original.',
              '- SQL crea vistas temporales en la sesion. Desaparecen al cerrarla; no crean la capa Bronze.', '',
              'Referencias de sintaxis: [TRY_TO_DOUBLE](https://docs.snowflake.com/en/sql-reference/functions/try_to_double) y [IS_NULL_VALUE](https://docs.snowflake.com/en/sql-reference/functions/is_null_value).']
    return '\n'.join(lines)+'\n'


def raw_state(cur):
    result={}
    for table_name in ('SOURCE_RECORDS','RCSB_ENTRIES','RESOURCE_FILES','BATCH_RESOURCES','INGESTION_BATCHES'):
        cur.execute(f'SELECT COUNT(*),HASH_AGG(*) FROM RAW.{table_name}')
        row=cur.fetchone()
        result[table_name]={'count':row[0],'hash':row[1]}
    return result


def validate_results(results):
    n=results['overview'][0]['rows_total']
    if not n:
        raise RuntimeError('No hay observaciones para perfilar.')
    if sum(r['rows_total'] for r in results['source_versions']) != n:
        raise RuntimeError('Los conteos por fuente no reconcilian.')
    if len(results['completeness']) != 19 or any(r['rows_total']!=n for r in results['completeness']):
        raise RuntimeError('La completitud no cubre todos los campos y filas.')
    v=results['numeric_validity'][0]
    if sum(v[k] for k in ('kd_missing','kd_not_numeric','kd_nonfinite','kd_nonpositive','kd_positive_finite')) != n:
        raise RuntimeError('Las categorias de afinidad no reconcilian.')
    for field in ('Temperature(K)','Affinity Method','KD(M)'):
        x=next(r for r in results['completeness'] if r['field']==field)
        if x['missing_total'] != x['absent_keys']+x['json_nulls']+x['blank_strings']:
            raise RuntimeError('Los tipos de faltantes no reconcilian.')


def main():
    sql_path=ROOT/'sql/05_profile_raw.sql'
    sql=sql_path.read_text()
    run=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder=ROOT/'reports/profiling'/run
    folder.mkdir(parents=True)
    sections=re.split(r'^-- @section ([a-z][a-z0-9_]*)\s*$',sql,flags=re.MULTILINE)
    results, queries={},[]
    with connect() as conn, conn.cursor() as cur:
        before=raw_state(cur)
        for index in range(1,len(sections),2):
            name,body=sections[index:index+2]
            for statement,_ in split_statements(io.StringIO(body)):
                cur.execute(statement)
                queries.append({'section':name,'query_id':cur.sfqid})
                if name!='setup':
                    columns=[x[0].lower() for x in cur.description]
                    rows=[dict(zip(columns,row)) for row in cur.fetchall()]
                    results[name]=rows
                    with (folder/f'{name}.csv').open('w',newline='') as stream:
                        writer=csv.DictWriter(stream,fieldnames=columns)
                        writer.writeheader()
                        writer.writerows(rows)
            print(f'Perfil: {name}',flush=True)
        after=raw_state(cur)
    if before!=after:
        raise RuntimeError('RAW cambio durante el perfil; revisar concurrencia antes de aceptar el reporte.')
    validate_results(results)
    stamp=datetime.now(ZoneInfo('America/Guayaquil')).isoformat(timespec='seconds')
    evidence={'generated_at':stamp,'sql_sha256':hashlib.sha256(sql.encode()).hexdigest(),
              'raw_before':before,'raw_after':after,'raw_unchanged':before==after,
              'query_ids':queries,'results':results}
    (folder/'profile.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2,default=json_default))
    report=make_report(results,stamp,run,before==after)
    (folder/'profile.md').write_text(report)
    (ROOT/'reports/raw_profile.md').write_text(report)
    (ROOT/'reports/profiling/latest.json').write_text(json.dumps({'run':run,'report':'reports/raw_profile.md'},indent=2))
    print(json.dumps({'report':'reports/raw_profile.md','rows':results['overview'][0]['rows_total'],
                      'raw_unchanged':before==after,'run':run},indent=2))


if __name__=='__main__':
    main()
