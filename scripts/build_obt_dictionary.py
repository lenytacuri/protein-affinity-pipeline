"""Document every OBT column from reviewed definitions, lineage and a read-only profile.

Run with --refresh to read the live Snowflake schema and NULL counts.
Without --refresh, rebuild both documents from the saved profile (offline).
Unknown columns fail explicitly instead of receiving a guessed definition.
"""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
# El Markdown vive en docs/: enlaces portables en GitHub y VS Code.
LINK_ROOT=Path('..')
TABLE='PROTEIN_AFFINITY.ANALYTICS.OBT_AFFINITY'
PROFILE=ROOT/'reports/obt_dictionary_profile.json'
ROLES={
 'predictor_candidate':'Característica candidata: evaluar selección y redundancia; no inclusión automática en X.',
 'conditional_predictor':'Contexto candidato solo si se conocerá al predecir y se controla su calidad.',
 'target':'Variable objetivo (y) que queremos predecir; no incluir en X.',
 'target_leakage':'Contiene la afinidad experimental o su transformación directa: excluir de X para predecir pKd.',
 'identifier':'Identificador para uniones, trazabilidad o agrupación; no incluir directamente en X.',
 'provenance':'Información de procedencia/configuración; no incluir por defecto en X.',
 'quality_control':'Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.',
 'context':'Contexto descriptivo o experimental; requiere interpretación/selección antes de cualquier uso en X.'}
CHEM_STATUS={
 'complete':'Todos los residuos Q1 tienen propiedades soportadas.',
 'partial_coverage':'Solo parte de los residuos Q1 tiene propiedades soportadas.',
 'no_supported_residues':'Hay selección Q1, pero ningún residuo soportado.',
 'empty_selection':'El filtro estricto Q1 no seleccionó residuos.',
 'geometry_unavailable':'La geometría no pudo calcularse.'}
BACK_STATUS={
 'complete':'Todos los residuos Q1 tienen φ, ψ, ω y τ calculables.',
 'partial_angles':'Falta al menos uno de esos ángulos en parte de los residuos Q1.',
 'no_valid_angles':'No hay valores válidos de φ, ψ, ω ni τ.',
 'empty_selection':'No hay residuos Q1 seleccionados.',
 'geometry_unavailable':'No hay geometría utilizable.'}
MUT_STATUS={
 'not_annotated':'No hay anotación de mutación interpretable como tal; no demuestra ausencia biológica de mutaciones.',
 'target_residues_present':'Todos los sitios anotados contienen la identidad objetivo. No valida la conformación completa del mutante.',
 'reference_geometry_only':'Hay residuos de referencia en sitios anotados; puede haber también algunos objetivos. Las features no modelan esos cambios.',
 'needs_review':'Anotación no interpretada, sitio ausente o identidad no coincidente.',
 'structure_unavailable':'Hay anotación de mutación, pero no geometría calculada para comprobarla.'}
GEO_STATUS={'computed':'Geometría Cα calculada.', 'structure_not_usable':'El cálculo encontró un problema estructural.',
 'invalid_chain_groups':'Grupos de cadenas ausentes, vacíos o solapados.', 'structure_missing':'No se encontró archivo estructural disponible.',
 'assigned':'Asignación de estructura presente, pero sin resultado de cálculo asociado (estado de respaldo, no equivalente a computed).',
 'mapping_missing':'Falta el vínculo de la observación con la geometría.'}
AA={'A':('alanina','ALA'),'C':('cisteína','CYS'),'D':('aspartato / ácido aspártico','ASP'),
'E':('glutamato / ácido glutámico','GLU'),'F':('fenilalanina','PHE'),'G':('glicina','GLY'),
'H':('histidina','HIS'),'I':('isoleucina','ILE'),'K':('lisina','LYS'),'L':('leucina','LEU'),
'M':('metionina','MET'),'N':('asparagina','ASN'),'P':('prolina','PRO'),'Q':('glutamina','GLN'),
'R':('arginina','ARG'),'S':('serina','SER'),'T':('treonina','THR'),'V':('valina','VAL'),
'W':('triptófano','TRP'),'Y':('tirosina','TYR')}
GROUPS={'NONPOLAR':('no polares','G,A,V,L,I,M,P,F,W'),
'POLAR_UNCHARGED':('polares sin carga, según la clasificación convencional','S,T,C,N,Q,Y'),
'ACIDIC':('ácidos','D,E'),'BASIC':('básicos','K,R,H'),
'AROMATIC_RING':('con anillo aromático','F,W,Y,H'),
'SULFUR_CONTAINING':('con azufre','C,M'),'ALIPHATIC_AVIL':('del subconjunto alifático AVIL','A,V,I,L')}
TORSIONS={'PHI':('φ','C(i−1), N(i), Cα(i), C(i)'),
'PSI':('ψ','N(i), Cα(i), C(i), N(i+1)'),
'OMEGA':('ω','Cα(i), C(i), N(i+1), Cα(i+1)')}
LINEAR={'TAU_DEG':('ángulo τ del esqueleto N(i)–Cα(i)–C(i)','grados'),
'N_CA_LENGTH':('longitud N(i)–Cα(i)','Å'),
'CA_C_LENGTH':('longitud Cα(i)–C(i)','Å'),
'PEPTIDE_CN_LENGTH':('longitud del enlace peptídico saliente C(i)–N(i+1)','Å')}
COUNT_NULL='NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos.'
MEAN_NULL='NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero.'
BASE={}
def entry(description,role='provenance',unit='No aplica',formula=None,null_meaning='NULL indica que no se recibió o no pudo interpretarse ese dato.',values=None,notes=None,**extra):
 return dict(description=description,ml_role=role,ml_guidance=ROLES[role],unit=unit,formula=formula,
             null_meaning=null_meaning,allowed_values=values,notes=notes or [],**extra)
def add(name,description,**kwargs):BASE[name]=entry(description,**kwargs)
add('OBSERVATION_ID','Identificador de la fila original, generado con el hash del archivo, nombre de hoja y número de fila.',role='identifier',null_meaning='No se permite NULL: es la clave única de la OBT.',notes=['Repetir PDB no implica repetir este ID.'])
for name,desc in {
'SOURCE_KEY':'Clave SHA-256 de la combinación de archivo/version, hoja y dataset de procedencia.',
'EXPERIMENT_KEY':'Clave SHA-256 de los campos de contexto experimental reportados; compartirla no demuestra que sea el mismo ensayo.',
'GEOMETRY_ID':'Clave del archivo estructural, PDB, grupos L/R, código y parámetros del cálculo; no es una proteína ni interfaz biológica universal.',
'LIGAND_PARTICIPANT_KEY':'Referencia al participante L de la geometría: GEOMETRY_ID seguido de :L.',
'RECEPTOR_PARTICIPANT_KEY':'Referencia al participante R de la geometría: GEOMETRY_ID seguido de :R.',
'PDB_ID':'Identificador de la entrada estructural del PDB asociada a la observación; no identifica una proteína única.',
'COMPLEX_ID':'Identificador de complejo que aporta el Excel original; se conserva sin redefinirlo.'}.items():
 add(name,desc,role='identifier',null_meaning='NULL si no se asignó geometría.' if name in ['GEOMETRY_ID','LIGAND_PARTICIPANT_KEY','RECEPTOR_PARTICIPANT_KEY'] else 'Ausencia en la fuente; SOURCE_KEY y EXPERIMENT_KEY se generan y deben estar presentes.')
add('SOURCE_ROW','Número de fila de origen en el Excel, contando el encabezado como fila 1.',unit='fila de archivo',notes=['No es la posición actual ni un orden biológico.'])
add('SOURCE_INDEX_RAW','Valor textual de la columna sin nombre _unnamed_0 del Excel; es un índice de origen, no la clave principal.')
for p,label in [('LIGAND','ligando'),('RECEPTOR','receptor')]:
 add(p+'_NAME',f'Nombre descriptivo del {label} reportado en el Excel.',role='context',notes=['Puede representar un grupo de cadenas; no se transforma en identidad molecular global.'])
 add(p+'_CHAINS_RAW',f'Texto original de las cadenas asignadas al {label}.',role='context',notes=['Se preservan identificadores de cadena de autor y mayúsculas/minúsculas.'])
 add(p+'_CHAINS_JSON',f'Lista JSON de cadenas de autor usadas como {label} en la geometría.',role='identifier',null_meaning='NULL si no existe GEOMETRY_ID; una geometría fallida puede conservar su lista de cadenas.')
add('MUTATIONS_RAW','Anotación original de mutaciones; el cálculo estructural no aplica estas sustituciones.',role='context',notes=['Consultar MUTATION_STRUCTURE_STATUS; no asumir que las features corresponden al mutante.'])
add('SUBGROUP_RAW','Etiqueta original Subgroup del dataset; se conserva sin asignarle un significado nuevo.',role='context')
add('KD_M','Constante de disociación experimental Kd convertida a número en mol/L.',role='target_leakage',unit='mol/L',formula='TRY_TO_DOUBLE(KD_M_RAW)',notes=['Contiene la misma información objetivo que pKd; no introducirla como predictor.'])
add('PKD','Afinidad objetivo expresada como pKd; un pKd mayor corresponde a un Kd menor.',role='target',unit='adimensional',formula='−log10(KD_M / (1 mol/L)); numéricamente −log10(KD_M)',null_meaning='NULL cuando Kd está ausente, no es interpretable, no es positivo o no es finito.')
add('KD_STATUS','Resultado de la validación numérica de Kd.',role='quality_control',values={'valid':'Kd positivo y finito.','invalid':'Kd interpretado pero no válido.','missing_or_unparsed':'Kd ausente o no convertible a número.'},notes=['Validación de formato/valor; no verifica la exactitud experimental.'])
add('KD_M_RAW','Texto original de KD(M) en el Excel.',role='target_leakage',unit='mol/L según encabezado original')
add('STRUCTURE_METHOD_RAW','Método de determinación estructural reportado en el Excel.',role='context',notes=['No confundir con AFFINITY_METHOD.'])
add('RESOLUTION_ANGSTROM','Resolución estructural convertida a número a partir del Excel.',role='quality_control',unit='Å',formula='TRY_TO_DOUBLE(RESOLUTION_ANGSTROM_RAW)',notes=['Indicador de la estructura, no distancia entre proteínas; puede no aplicar a ciertos métodos.'])
add('RESOLUTION_ANGSTROM_RAW','Resolución estructural en su formato textual original.',role='quality_control',unit='Å según encabezado original')
add('STRUCTURE_REFERENCE_RAW','Referencia bibliográfica asociada a la estructura en el Excel; se conserva como texto.')
add('STRUCTURE_RELEASE_DATE_RAW','Fecha reportada de publicación/liberación estructural, conservada como texto sin normalizar.')
add('GEOMETRY_STATUS','Estado de asignación/cálculo de la geometría Cα para la observación.',role='quality_control',values=GEO_STATUS)
add('GEOMETRY_ISSUE','Motivo textual de fallo del cálculo estructural, cuando existe.',role='quality_control',null_meaning='Normalmente NULL cuando la geometría se calculó; también puede faltar si el problema ocurrió antes de crear la geometría.')
add('STRUCTURE_VERSIONS','Cantidad de archivos estructurales con SHA-256 distintos disponibles para la combinación de versión de fuente y PDB.',unit='versiones',notes=['El pipeline selecciona el más reciente disponible. No cuenta modelos, cadenas ni conformaciones dentro del archivo.'])
add('MUTATION_STRUCTURE_STATUS','Resultado de comparar las mutaciones anotadas con las identidades observadas en los sitios estructurales.',role='quality_control',values=MUT_STATUS)
add('USES_REFERENCE_FOR_MUTATION','Bandera trivalente que indica si los sitios anotados requieren usar geometría de referencia para una mutación.',role='quality_control',values={'true':'Estado reference_geometry_only.','false':'Estado target_residues_present.','NULL':'Otros estados; no se puede concluir true/false.'},null_meaning='No equivale a false; incluye not_annotated, needs_review y structure_unavailable.')
add('HAS_CA_CONTACTS_10','Existe al menos un par Cα–Cα entre participantes a menos de 10 Å, considerando todos los Cα utilizables.',role='predictor_candidate',unit='booleano',formula='MIN_DISTANCE_ANGSTROM < 10',null_meaning='NULL si no pudo calcularse geometría.',notes=['No demuestra unión experimental ni identifica un enlace químico.'])
add('BIOLOGICAL_ASSEMBLY_VALIDATED','Indica si el pipeline validó el ensamblaje biológico.',role='quality_control',unit='booleano',notes=['Esta versión no hace esa validación. false significa no validado, no que sea biológicamente incorrecto.'],null_meaning='Puede ser NULL cuando no hay una geometría asociada.')
add('HAS_VALID_LABEL','Indica si KD_STATUS es valid.',role='quality_control',unit='booleano',formula="KD_STATUS = 'valid'",notes=['Es información sobre la etiqueta; usar para control de elegibilidad, no como predictor de la etiqueta.'])
add('HAS_COMPUTED_GEOMETRY','Indica si GEOMETRY_STATUS es computed.',role='quality_control',unit='booleano',formula="GEOMETRY_STATUS = 'computed'")
add('HAS_Q1_BOTH_PARTNERS','Indica si ambos participantes tienen al menos un residuo seleccionado por Q1.',role='quality_control',unit='booleano',formula='COALESCE(N_SELECTED_Q1_LIGAND > 0 AND N_SELECTED_Q1_RECEPTOR > 0, false)',notes=['false también cubre geometrías no disponibles; revisar GEOMETRY_STATUS.'])
add('NEEDS_VARIANT_REVIEW','Bandera de revisión de variante definida por el estado de mutación.',role='quality_control',unit='booleano',formula="true salvo not_annotated o target_residues_present; estado NULL también produce true",notes=['false no significa que toda la observación esté aprobada para entrenamiento.'])
for n,d in {'SOURCE_SHA256':'Huella SHA-256 del archivo de entrada del que procede la observación.',
'SOURCE_FILE':'Nombre del archivo de entrada.', 'SOURCE_SHEET':'Hoja del Excel de origen.',
'SOURCE_DATASET':'Nombre del dataset de procedencia reportado en Source Data Set.',
'STRUCTURE_SHA256':'Huella SHA-256 del archivo estructural exacto utilizado, en su representación almacenada.',
'CODE_SHA256':'Huella del código/dependencias que identifica la versión del cálculo Cα; no es una versión global de todos los componentes.',
'GEOMETRY_PARAMETERS_JSON':'Parámetros versionados del cálculo Cα, serializados como texto JSON.'}.items():add(n,d)
add('AFFINITY_METHOD','Método de medición de afinidad, recortado y con marcadores de desconocido convertidos a NULL.',role='context',formula='TRIM del texto; unknown/n/a/na/none/null/vacío → NULL',notes=['Puede reflejar sesgo entre ensayos; no se propone como entrada automática a un predictor previo al experimento.'])
add('AFFINITY_METHOD_RAW','Método de medición de afinidad en su texto original.',role='context')
add('TEMPERATURE_K','Temperatura de la medición interpretada como número de kelvin; puede proceder de una temperatura anotada como supuesta.',role='conditional_predictor',unit='K',formula='Extraer número si el texto coincide con el formato decimal reconocido, opcionalmente seguido de (assumed); la validez se informa en TEMPERATURE_STATUS.',null_meaning='NULL si el texto está ausente o no tiene el formato reconocido.',notes=['Consultar TEMPERATURE_STATUS y TEMPERATURE_ASSUMED. Solo usar si se conoce la temperatura del escenario que se va a predecir.'])
add('TEMPERATURE_RAW','Texto original de Temperature(K), incluidas anotaciones como (assumed).',role='context',unit='K según encabezado original')
add('TEMPERATURE_STATUS','Estado de interpretación de la temperatura.',role='quality_control',values={'missing':'Texto NULL.','unparsed':'No se pudo extraer el número.','invalid':'Número interpretado ≤ 0 K.','assumed':'Valor interpretable con anotación de supuesto.','reported':'Valor interpretable sin anotación de supuesto.'})
add('TEMPERATURE_ASSUMED','El texto original contiene assumed, ignorando mayúsculas.',role='quality_control',unit='booleano',notes=['false no demuestra medición real: también ocurre cuando no hay temperatura.'])
add('AFFINITY_REFERENCE_RAW','Referencia bibliográfica de la medición de afinidad tal como viene en el Excel; puede ser PMID, texto o TBD.')
add('AFFINITY_REFERENCE_STATUS','Clasificación del texto de referencia de afinidad.',role='quality_control',values={'missing':'NULL o vacío.','placeholder':'TBD.','pmid':'Solo dígitos.','text_reference':'Otro texto.'},notes=['pmid identifica un formato; no se verificó el artículo con esta regla.'])
add('AFFINITY_PMID','Identificador numérico PubMed interpretado de la referencia de afinidad cuando contiene solo dígitos.',role='identifier',null_meaning='NULL si no contiene solo dígitos o si no se convierte a NUMBER. No implica que no exista publicación.')
add('AFFINITY_RELEASE_DATE_RAW','Fecha reportada de la referencia/medición de afinidad; se conserva como texto sin normalizar.')
for p,label in [('LIGAND','ligando'),('RECEPTOR','receptor')]:
 add('N_'+p,f'Número de residuos del {label} con Cα utilizable en el modelo y grupos de cadenas seleccionados, antes del filtro Q1.',role='predictor_candidate',unit='residuos',null_meaning=COUNT_NULL,notes=['No es necesariamente la longitud completa de secuencia: excluye residuos no observados o sin Cα utilizable.'])
 add('Q1_'+p+'_ANGSTROM',f'Primer cuartil de las distancias mínimas Cα de cada residuo del {label} a cualquier residuo del otro participante.',role='predictor_candidate',unit='Å',formula=f'percentil 25 con interpolación lineal de {{min_j ||Cα_i−Cα_j||}} del {label}',null_meaning='NULL si no hay geometría calculada.',notes=['Umbral propio del participante; se selecciona con distancia estrictamente menor. No es 25 Å ni el cuartil de todos los pares.'])
 add('N_SELECTED_Q1_'+p,f'Número de residuos del {label} cuya distancia mínima al otro participante es estrictamente menor que su Q1.',role='predictor_candidate',unit='residuos',null_meaning=COUNT_NULL,notes=['Los empates pueden hacer que se seleccione menos del 25 %.'])
add('MIN_DISTANCE_ANGSTROM','Menor distancia Cα–Cα entre ambos participantes, considerando todos los residuos utilizables.',role='predictor_candidate',unit='Å',formula='min_{i en L, j en R} ||Cα_i−Cα_j||',null_meaning='NULL si no se calculó geometría.',notes=['No es distancia entre átomos pesados cualesquiera; no demuestra un enlace.'])
add('SELECTED_PAIRS_LT10','Cantidad de pares L–R con ambos residuos seleccionados por Q1 y distancia Cα–Cα menor que 10 Å.',role='predictor_candidate',unit='pares',null_meaning=COUNT_NULL,notes=['Cuenta pares, no residuos ni enlaces de hidrógeno.'])
add('SELECTED_PAIR_COUNT','Número de todos los pares entre los residuos Q1 de L y los residuos Q1 de R, sin corte adicional de distancia.',role='predictor_candidate',unit='pares',formula='N_SELECTED_Q1_LIGAND × N_SELECTED_Q1_RECEPTOR',null_meaning=COUNT_NULL,notes=['Puede incluir pares lejanos; seleccionar cada residuo por su vecino más próximo no hace cercanos todos los pares.'])


def participant_definition(name):
    p,rest=name.split('_',1);label='ligando (L)' if p=='LIGAND' else 'receptor (R)'
    prefix=p+'_';null_count=COUNT_NULL
    if rest=='N_SELECTED':
        return entry(f'Número de residuos Q1 del {label}. Copia del conteo de selección geométrica.',role='predictor_candidate',unit='residuos',null_meaning=null_count,formula='N_SELECTED_Q1_'+p)
    if rest.startswith('CHEM_'):
        key=rest[5:];base=prefix+'CHEM_'
        if key=='FEATURE_VERSION':return entry(f'Versión de las reglas químicas aplicadas al {label}.',values={'chemistry_v1':'Mapa de 20 aminoácidos y categorías definido en el proyecto.'},null_meaning='NULL si no existe participante asociado.')
        if key=='FEATURE_BASIS':return entry(f'Base estructural de las características químicas del {label}.',values={'observed_structure_q1':'Residuos observados seleccionados por Q1, sin construir mutantes.'},null_meaning='NULL si no existe participante asociado.')
        if key=='CHEMISTRY_STATUS':return entry(f'Estado de cobertura de las propiedades químicas del {label}.',role='quality_control',values=CHEM_STATUS,null_meaning='NULL si no hay participante asociado; geometry_unavailable si existe pero su geometría falló.')
        descs={'N_SELECTED':'todos los residuos seleccionados por Q1','N_SUPPORTED':'residuos Q1 canónicos cuyo nombre/código coincide con el mapa de los 20 aminoácidos',
               'N_NONSTANDARD':'residuos Q1 marcados como no estándar por su nombre estructural',
               'N_UNSUPPORTED':'residuos Q1 sin propiedades asignadas, incluidos los no estándar'}
        if key in descs:
            return entry(f'Cantidad de {descs[key]} en el {label}.',role='predictor_candidate' if key in ['N_SELECTED','N_SUPPORTED'] else 'quality_control',unit='residuos',null_meaning=null_count,formula=base+'N_SELECTED − '+base+'N_SUPPORTED' if key=='N_UNSUPPORTED' else None)
        if key=='MEAN_KD_HYDROPATHY':return entry(f'Hidropatía media Kyte–Doolittle de los residuos soportados Q1 del {label}. Valores mayores indican mayor hidropatía en esta escala.',role='predictor_candidate',unit='escala adimensional Kyte–Doolittle',formula='SUM(hidropatía de cada residuo soportado) / '+base+'N_SUPPORTED',null_meaning=MEAN_NULL,notes=['KD aquí significa Kyte–Doolittle; NO es el Kd experimental ni una fuga directa de la etiqueta. No es energía de unión. Media almacenada con 6 decimales.'],expected_range='[−4.5, 4.5] cuando hay valores')
        if key=='AA_ENTROPY_BITS':return entry(f'Diversidad de composición de los 20 aminoácidos soportados Q1 del {label}.',role='predictor_candidate',unit='bits',formula='−Σ p_a log2(p_a), p_a=N_AA_a/N_SUPPORTED; sumar solo p_a>0',null_meaning=MEAN_NULL,notes=['Es entropía de Shannon de la composición, no entropía termodinámica ni flexibilidad. Cada término se redondea a 12 decimales.'],expected_range='[0, log2(20)] ≈ [0, 4.322]')
        if key=='PROPERTY_COVERAGE':return entry(f'Fracción de los residuos Q1 del {label} para los que hay propiedades químicas soportadas.',role='quality_control',unit='fracción [0,1]',formula=base+'N_SUPPORTED / '+base+'N_SELECTED',null_meaning='NULL si falta geometría/participante o N_SELECTED=0. Cero significa selección existente sin residuos soportados.')
        if key.startswith(('N_AA_','FRACTION_AA_')):
            aa=key.rsplit('_',1)[1];full,three=AA[aa];is_fraction=key.startswith('FRACTION')
            return entry(f"{'Fracción' if is_fraction else 'Cantidad'} de {full} ({aa}, {three}) entre los residuos soportados Q1 del {label}.",
              role='predictor_candidate',unit='fracción [0,1]' if is_fraction else 'residuos',
              formula=base+'N_AA_'+aa+' / '+base+'N_SUPPORTED' if is_fraction else f'Contar residuos canónicos {three} con SELECTED_Q1=true',
              null_meaning='NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados.' if is_fraction else null_count,
              notes=['El denominador es N_SUPPORTED, no todos los residuos seleccionados.'] if is_fraction else ['No se incluyen residuos modificados por equivalencia nominal.'])
        is_fraction=key.startswith('FRACTION_');group=key.removeprefix('FRACTION_') if is_fraction else key.removeprefix('N_')
        if group in GROUPS:
            groupname,members=GROUPS[group]
            notes=['Clasificación por identidad; no representa cargas medidas ni estados de protonación.'] if group in ('ACIDIC','BASIC','POLAR_UNCHARGED') else []
            if group=='BASIC':notes+=['Incluye H; no se asume que toda histidina esté protonada.']
            if group=='AROMATIC_RING':notes+=['Incluye H. No cuenta interacciones π–π.']
            if group=='SULFUR_CONTAINING':notes+=['Cuenta residuos C y M, no átomos de azufre ni enlaces disulfuro.']
            if group in ['AROMATIC_RING','SULFUR_CONTAINING','ALIPHATIC_AVIL']:notes+=['Grupo solapado con clases de polaridad; no sumar todos los grupos como una partición.']
            return entry(f"{'Fracción' if is_fraction else 'Cantidad'} de aminoácidos {groupname} ({members}) soportados Q1 del {label}.",role='predictor_candidate',unit='fracción [0,1]' if is_fraction else 'residuos',formula=base+'N_'+group+' / '+base+'N_SUPPORTED' if is_fraction else 'Suma de los conteos N_AA de '+members,
              null_meaning='NULL si falta geometría/participante o N_SUPPORTED=0; el denominador son los residuos soportados.' if is_fraction else null_count,notes=notes)
    if rest.startswith('BACKBONE_'):
        key=rest[9:];base=prefix+'BACKBONE_'
        if key=='FEATURE_VERSION':return entry(f'Versión del cálculo y resumen del esqueleto peptídico del {label}.',values={'backbone_v1':'φ, ψ, ω saliente, τ y tres longitudes.'},null_meaning='NULL si no existe participante asociado.')
        if key=='FEATURE_BASIS':return entry(f'Base del resumen geométrico interno del {label}.',values={'observed_structure_q1':'Residuos Q1 de la estructura observada; vecinos pueden estar fuera de Q1.'},null_meaning='NULL si no existe participante asociado.')
        if key=='BACKBONE_STATUS':return entry(f'Estado de disponibilidad de los cuatro ángulos en los residuos Q1 del {label}.',role='quality_control',values=BACK_STATUS,null_meaning='NULL si no existe participante asociado.',notes=['complete se refiere a φ, ψ, ω y τ; no es aprobación global de calidad experimental.'])
        if key=='N_MEASURED_ROWS':return entry(f'Cantidad de filas de mediciones individuales del {label}; incluye residuos Q1 con ángulos ausentes.',role='quality_control',unit='residuos',null_meaning=null_count,formula=prefix+'N_SELECTED',notes=['No cuenta únicamente residuos con todos los ángulos válidos.'])
        if key=='N_PHI_PSI_COMPLETE':return entry(f'Cantidad de residuos Q1 del {label} con φ y ψ simultáneamente disponibles.',role='quality_control',unit='residuos',formula='COUNT_IF(PHI_DEG IS NOT NULL AND PSI_DEG IS NOT NULL)',null_meaning=null_count)
        if key=='FRACTION_PHI_PSI_COMPLETE':return entry(f'Fracción de residuos Q1 del {label} con φ y ψ simultáneamente disponibles.',role='quality_control',unit='fracción [0,1]',formula=base+'N_PHI_PSI_COMPLETE / '+prefix+'N_SELECTED',null_meaning='NULL sin geometría/participante o si N_SELECTED=0.')
        for angle,(symbol,atoms) in TORSIONS.items():
            atom_note=f'Torsión {symbol}: {atoms}. Se usan vecinos reales de la cadena, aunque no sean Q1.'
            if angle=='OMEGA':atom_note+=' Es el enlace saliente hacia i+1, no el entrante.'
            if key=='N_'+angle:return entry(f'Número de residuos Q1 del {label} con torsión {symbol} calculable.',role='quality_control',unit='ángulos válidos',formula=f'COUNT({angle}_DEG) no NULL',null_meaning=null_count,notes=[atom_note])
            if key==angle+'_COVERAGE':return entry(f'Fracción de residuos Q1 del {label} con torsión {symbol} calculable.',role='quality_control',unit='fracción [0,1]',formula=base+'N_'+angle+' / '+prefix+'N_SELECTED',null_meaning='NULL sin geometría/participante o si N_SELECTED=0.',notes=[atom_note])
            if key in (angle+'_MEAN_SIN',angle+'_MEAN_COS'):
                fn='sin' if key.endswith('SIN') else 'cos'
                return entry(f'Media del {"seno" if fn=="sin" else "coseno"} de los ángulos {symbol} válidos del {label}. Componente de la representación circular.',role='predictor_candidate',unit='adimensional [−1,1]',formula=f'media({fn}({symbol} × π/180)); términos redondeados a 12 decimales',null_meaning=MEAN_NULL,notes=[atom_note,'Usar junto con la otra componente; no es el seno/coseno de la media aritmética de ángulos.'])
            if key==angle+'_RESULTANT_LENGTH':return entry(f'Longitud R del vector circular medio de {symbol} del {label}: cerca de 1 indica ángulos concentrados; cerca de 0, cancelación de direcciones.',role='predictor_candidate',unit='adimensional [0,1]',formula=f'min(1, sqrt({base}{angle}_MEAN_SIN² + {base}{angle}_MEAN_COS²))',null_meaning=MEAN_NULL,notes=[atom_note,'Una distribución multimodal también puede dar R bajo; no mide flexibilidad dinámica.'])
            if key==angle+'_CIRCULAR_MEAN_DEG':return entry(f'Dirección media circular de la torsión {symbol} del {label}, en grados.',role='predictor_candidate',unit='grados',formula=f'atan2({base}{angle}_MEAN_SIN, {base}{angle}_MEAN_COS) × 180/π, solo si R>1e−8',null_meaning='NULL si no hay ángulos válidos o R≤1e−8, porque la dirección media no está bien definida.',notes=[atom_note,'±180° representan la misma dirección; seno/coseno evitan ese salto al usar modelos clásicos.'],expected_range='[−180,180]')
            if key==angle+'_CIRCULAR_VARIANCE':return entry(f'Dispersión circular de {symbol} del {label}; cero indica máxima concentración.',role='predictor_candidate',unit='adimensional [0,1]',formula='1 − '+base+angle+'_RESULTANT_LENGTH',null_meaning=MEAN_NULL,notes=[atom_note,'No es varianza en grados cuadrados ni mide movilidad de una trayectoria.'])
        for measure,(desc,unit) in LINEAR.items():
            notes=['Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan.']
            if measure=='PEPTIDE_CN_LENGTH':notes+=['Se exige continuidad de cadena y C–N entre 0.8 y 1.8 Å; no se incluyen enlaces rechazados por esa regla.']
            if key=='N_'+measure:return entry(f'Cantidad de mediciones válidas de {desc} del {label}.',role='quality_control',unit='mediciones válidas',formula='COUNT('+measure+') no NULL',null_meaning=null_count,notes=notes)
            if key==measure+'_COVERAGE':return entry(f'Fracción de residuos Q1 del {label} con {desc} calculable.',role='quality_control',unit='fracción [0,1]',formula=base+'N_'+measure+' / '+prefix+'N_SELECTED',null_meaning='NULL sin geometría/participante o si N_SELECTED=0.',notes=notes)
            if key==measure+'_MEAN':return entry(f'Media de {desc} entre mediciones válidas del {label}.',role='predictor_candidate',unit=unit,formula='SUM(x_i)/n_valid; media lineal, no circular',null_meaning=MEAN_NULL,notes=notes)
            if key==measure+'_STD_POP':return entry(f'Desviación estándar poblacional de {desc} del {label}; describe dispersión entre residuos.',role='predictor_candidate',unit=unit,formula='sqrt(SUM((x_i − media)²)/n_valid)',null_meaning=MEAN_NULL,notes=notes+['Con una sola medición válida es 0. No divide por n−1 ni es error estándar experimental.'])
    raise KeyError('No definition for '+name)


def refresh_profile(lineage,summary):
    from check_snowflake import connect
    names=[m['output'] for m in lineage]
    if not all(re.fullmatch('[A-Z][A-Z0-9_]*',n) for n in names):raise ValueError('Unexpected identifiers')
    with connect() as conn,conn.cursor() as cur:
        cur.execute("SELECT COLUMN_NAME,ORDINAL_POSITION,DATA_TYPE,NUMERIC_PRECISION,NUMERIC_SCALE,IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_CATALOG='PROTEIN_AFFINITY' AND TABLE_SCHEMA='ANALYTICS' AND TABLE_NAME='OBT_AFFINITY' ORDER BY ORDINAL_POSITION")
        meta=[dict(zip(['name','ordinal_position','data_type','precision','scale','nullable'],row)) for row in cur.fetchall()]
        if [m['name'] for m in meta]!=names:raise ValueError('Live schema differs from the verified OBT run')
        cur.execute('SELECT COUNT(*),HASH_AGG(*),'+','.join('COUNT(*)-COUNT("'+n+'")' for n in names)+' FROM '+TABLE)
        values=cur.fetchone();rows,digest=values[:2]
        if rows!=summary['rows'] or digest!=summary['loaded']['hash']:raise ValueError('Live OBT content differs from the verified run')
        for m,n in zip(meta,values[2:]):m['null_count']=n
        enum_names=[n for n in names if n.endswith('_STATUS') or n in ['USES_REFERENCE_FOR_MUTATION','BIOLOGICAL_ASSEMBLY_VALIDATED']]
        cur.execute('SELECT '+','.join('ARRAY_AGG(DISTINCT "'+n+'")' for n in enum_names)+' FROM '+TABLE)
        enum_data=cur.fetchone();observed={n:json.loads(v) if isinstance(v,str) else v for n,v in zip(enum_names,enum_data)}
    profile={'table':TABLE,'checked_at_utc':datetime.now(timezone.utc).isoformat(),'run':summary['run'],'rows':rows,'hash':digest,'columns':meta,'observed_values':observed}
    PROFILE.write_text(json.dumps(profile,indent=2,ensure_ascii=False)+'\n')
    return profile


def code_origins(m):
    table=m['table'];name=m['output'];base=['spark/obt_transform.py']
    gold={'FACT_AFFINITY':'fact_affinity','DIM_SOURCE':'dim_source','DIM_EXPERIMENT':'dim_experiment','DIM_GEOMETRY':'dim_geometry','DIM_PARTICIPANT_FEATURES':'dim_participant_features'}
    base.append('dbt/models/gold/'+gold[table]+'.sql')
    if table=='DIM_PARTICIPANT_FEATURES':
        base+=['dbt/models/silver/silver_interface_chemistry.sql','dbt/macros/amino_acid_properties.sql'] if '_CHEM_' in name else ['scripts/backbone_core.py','dbt/models/backbone/backbone_features.sql'] if '_BACKBONE_' in name else ['scripts/geometry_core.py']
    elif table=='DIM_GEOMETRY' or name in ['HAS_CA_CONTACTS_10','MUTATION_STRUCTURE_STATUS']:
        base+=['scripts/geometry_core.py','dbt/models/silver/silver_structure_geometry.sql']
    else:base+=['dbt/models/silver/silver_affinity_observations.sql','dbt/models/bronze/bronze_affinity_observations.sql']
    if name in ['SOURCE_KEY','EXPERIMENT_KEY']:base.append('dbt/macros/gold_keys.sql')
    if name in ['OBSERVATION_ID','SOURCE_ROW','SOURCE_INDEX_RAW','SOURCE_SHA256']:base.append('scripts/source_inputs.py')
    if name=='STRUCTURE_VERSIONS':base.append('sql/07_silver_inputs.sql')
    if name in ['GEOMETRY_ID','CODE_SHA256','MUTATION_STRUCTURE_STATUS']:base.append('scripts/run_silver.py')
    return list(dict.fromkeys(base))


def render(doc):
    sections=[('general','Identificadores, afinidad y contexto'),('geometry','Geometría general Cα'),
      ('ligand_chemistry','Ligando: selección y composición química'),('ligand_backbone','Ligando: geometría interna'),
      ('receptor_chemistry','Receptor: selección y composición química'),('receptor_backbone','Receptor: geometría interna')]
    lines=['# Diccionario de las 280 columnas de la OBT','',f"Tabla: `{doc['table']}`. **{doc['row_count']} filas × {doc['column_count']} columnas**.",
      f"Ejecución documentada: `{doc['obt_run']}`. Esquema y ausencias contrastados con Snowflake: `{doc['profile_checked_at_utc']}`.",'',
      'Cada entrada describe una columna real, en el orden de la OBT. Las indicaciones de uso en ML son orientación para organizar los datos, no una selección de variables ya ejecutada.',
      'Buscar con Ctrl+F/Cmd+F el nombre exacto de la columna. El JSON compañero ofrece la misma información para usarla desde código.', '',
      '## Cómo leer los nombres','',
      '- `LIGAND_`: grupo de cadenas L; `RECEPTOR_`: grupo R. Ambos participantes pueden ser proteínas y tener varias cadenas.',
      '- `CHEM_`: composición de residuos. `BACKBONE_`: geometría del esqueleto peptídico.',
      '- `N_`: cantidad. `FRACTION_`/`COVERAGE`: proporción entre 0 y 1, no porcentaje 0–100.',
      '- `MEAN`: media. `STD_POP`: desviación estándar poblacional. `MEAN_SIN`/`MEAN_COS`: componentes de una media circular.',
      '- `RAW`: valor original conservado como texto. `KEY`/`ID`/`SHA256`: claves o huellas, no magnitudes químicas.',
      '', '## Reglas que se aplican a todo el diccionario','',
      '1. **Una fila es una observación experimental**. Varias filas pueden compartir geometría y, por eso, compartir features.',
      '2. Q1 se calcula sobre la distancia mínima Cα de cada residuo al otro participante, por separado para L y R. Se selecciona con `< Q1`, no `≤ Q1` ni 25 Å.',
      '3. Las características describen la estructura observada; no aplican las mutaciones del Excel. Los vecinos necesarios para φ/ψ/ω pueden estar fuera de Q1.',
      '4. Las fracciones químicas usan **N_SUPPORTED**. La cobertura química usa **N_SELECTED**. Las medias geométricas usan solo mediciones válidas.',
      '5. `NULL` no equivale a 0. Los conteos de NULL son de esta versión de la OBT; no son una regla de nulabilidad futura ni un conteo de geometrías únicas.',
      '6. `PKD` es y. `KD_M` y `KD_M_RAW` contienen la etiqueta de forma directa: excluirlos de X. `MEAN_KD_HYDROPATHY` significa Kyte–Doolittle y no contiene el Kd experimental.',
      '7. No se ejecutó selección de features, imputación ni split. Identificadores y controles de calidad no entran automáticamente en X.',
      '', '## Función de las columnas','', '| Función | Cantidad | Interpretación |','|---|---:|---|']
    for role,n in doc['role_counts'].items():lines.append(f'| {role} | {n} | {ROLES[role]} |')
    lines+=['','## Índice','']
    for group,title in sections:lines.append(f'- [{title}](#{group}) — {sum(c["group"]==group for c in doc["columns"])} columnas')
    for group,title in sections:
        lines+=['',f'<a id="{group}"></a>',f'## {title}','']
        for c in doc['columns']:
            if c['group']!=group:continue
            lines += [f"### {c['ordinal_position']:03d}. `{c['name']}`",'',c['description'],'',
              f"- **Tipo:** `{c['type_snowflake']}`. **Unidad:** {c['unit']}. **Función ML:** `{c['ml_role']}`.",
              '- **Uso:** '+c['ml_guidance']]
            if c['formula']:lines.append('- **Cálculo:** '+c['formula'])
            lines.append(f"- **Ausencias:** {c['null_meaning']} NULL observados: **{c['null_count_observed']} / {doc['row_count']}**.")
            lines.append(f"- **Origen Gold:** `{c['origin']['table']}.{c['origin']['column']}`"+(' · participante '+c['participant'] if c['participant'] else '')+'.')
            links=', '.join(f'[{Path(f).name}](<{LINK_ROOT/f}>)' for f in c['origin']['code_files'][1:])
            lines.append('- **Código:** '+links+'.')
            if c.get('expected_range'):lines.append('- **Rango definido:** '+c['expected_range'])
            if c['allowed_values']:lines.append('- **Valores:** '+'; '.join(f'`{k}`: {v}' for k,v in c['allowed_values'].items()))
            if c.get('observed_values') is not None:lines.append('- **Valores observados no nulos:** '+', '.join('`'+str(x)+'`' for x in c['observed_values']))
            if c['redundant_with']:lines.append('- **Equivalencias de conteo:** '+', '.join('`'+n+'`' for n in c['redundant_with']))
            if c['notes']:lines.append('- **Interpretación:** '+' '.join(c['notes']))
            lines.append('')
    lines+=['## Actualizar el diccionario','',
      'Desde la carpeta del proyecto:', '', '```sh',
      'docker compose run --rm pipeline python scripts/build_obt_dictionary.py --refresh', '```','',
      '`--refresh` solo consulta Snowflake: lee esquema, conteos de NULL y estados, y comprueba la huella frente a la ejecución OBT documentada. No modifica tablas.',
      'Sin `--refresh`, usa `reports/obt_dictionary_profile.json` y puede regenerarse sin conexión. Una columna desconocida detiene el generador para exigir una definición explícita.',
      'Definiciones revisadas en `scripts/build_obt_dictionary.py`; linaje en `reports/obt/<run>/column_lineage.json`. El generador también verifica que ninguna columna falte o aparezca duplicada.','']
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--refresh',action='store_true');args=parser.parse_args()
    run=json.loads((ROOT/'reports/obt/latest.json').read_text())['run'];folder=ROOT/'reports/obt'/run
    summary=json.loads((folder/'summary.json').read_text());lineage=json.loads((folder/'column_lineage.json').read_text())
    profile=refresh_profile(lineage,summary) if args.refresh else json.loads(PROFILE.read_text())
    if profile['run']!=run or profile['hash']!=summary['loaded']['hash']:raise ValueError('Refresh required: profile belongs to another OBT snapshot')
    meta={m['name']:m for m in profile['columns']};columns=[]
    for m in lineage:
        n=m['output'];pm=None
        d=BASE.get(n)
        if d is None:d=participant_definition(n)
        d=dict(d);d['notes']=list(d['notes'])
        if m['table']=='DIM_PARTICIPANT_FEATURES':
            pm='L' if n.startswith('LIGAND_') else 'R'
            group=('ligand_' if pm=='L' else 'receptor_')+('backbone' if '_BACKBONE_' in n else 'chemistry')
        else:group='geometry' if m['table']=='DIM_GEOMETRY' else 'general'
        info=meta[n];typ=info['data_type']
        if typ=='NUMBER':typ+=f"({info['precision']},{info['scale']})"
        redundancies=[]
        for side in ['LIGAND','RECEPTOR']:
            equivalent=['N_SELECTED_Q1_'+side,side+'_N_SELECTED',side+'_CHEM_N_SELECTED',side+'_BACKBONE_N_MEASURED_ROWS']
            if n in equivalent:redundancies=[x for x in equivalent if x!=n]
        d.update(name=n,ordinal_position=info['ordinal_position'],type_snowflake=typ,nullable_schema=info['nullable']=='YES',
          null_count_observed=info['null_count'],group=group,participant=pm,
          origin={'table':'PROTEIN_AFFINITY.GOLD.'+m['table'],'column':m['column'],'join_alias':m['alias'],'code_files':code_origins(m)},
          redundant_with=redundancies)
        if n in profile['observed_values']:d['observed_values']=profile['observed_values'][n]
        columns.append(d)
    names=[c['name'] for c in columns]
    assert len(columns)==summary['columns']==len(meta)==len(set(names))
    assert names==[c['name'] for c in profile['columns']]
    assert all(c['description'] and c['unit'] and c['null_meaning'] for c in columns)
    assert all(0<=c['null_count_observed']<=profile['rows'] for c in columns)
    for c in columns:
        assert all((ROOT/f).is_file() for f in c['origin']['code_files'])
        assert all(n in names for n in c['redundant_with'])
        if c['allowed_values'] and 'observed_values' in c:
            observed={str(v).lower() if isinstance(v,bool) else str(v) for v in c['observed_values']}
            assert observed<=set(c['allowed_values']), (c['name'],observed)
    doc={'dictionary_version':'1.0','language':'es','table':TABLE,'obt_run':run,'row_count':profile['rows'],
       'column_count':len(columns),'profile_checked_at_utc':profile['checked_at_utc'],
       'source_obt_hash_agg':profile['hash'],'grain':'Una observación experimental original por OBSERVATION_ID.',
       'role_definitions':ROLES,'role_counts':dict(Counter(c['ml_role'] for c in columns)),
       'ml_selection_executed':False,'columns':columns}
    out=ROOT/'docs';(out/'obt_data_dictionary.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
    (out/'obt_data_dictionary.md').write_text(render(doc))
    validation={'status':'PASS','documented_columns':len(columns),'schema_order_matches':True,'all_definitions_present':True,
       'all_code_references_exist':True,'obt_run':run,'live_profile_hash_matches_run':True,'role_counts':doc['role_counts']}
    (ROOT/'reports/obt_dictionary_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(validation,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
