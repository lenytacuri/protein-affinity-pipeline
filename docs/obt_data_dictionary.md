# Diccionario de las 280 columnas de la OBT

Tabla: `PROTEIN_AFFINITY.ANALYTICS.OBT_AFFINITY`. **12062 filas × 280 columnas**.
Ejecución documentada: `20261113T214845538920Z`. Esquema y ausencias contrastados con Snowflake: `2026-11-13T21:50:36.258313+00:00`.

Cada entrada describe una columna real, en el orden de la OBT. Las indicaciones de uso en ML son orientación para organizar los datos, no una selección de variables ya ejecutada.
Buscar con Ctrl+F/Cmd+F el nombre exacto de la columna. El JSON compañero ofrece la misma información para usarla desde código.

## Cómo leer los nombres

- `LIGAND_`: grupo de cadenas L; `RECEPTOR_`: grupo R. Ambos participantes pueden ser proteínas y tener varias cadenas.
- `CHEM_`: composición de residuos. `BACKBONE_`: geometría del esqueleto peptídico.
- `N_`: cantidad. `FRACTION_`/`COVERAGE`: proporción entre 0 y 1, no porcentaje 0–100.
- `MEAN`: media. `STD_POP`: desviación estándar poblacional. `MEAN_SIN`/`MEAN_COS`: componentes de una media circular.
- `RAW`: valor original conservado como texto. `KEY`/`ID`/`SHA256`: claves o huellas, no magnitudes químicas.

## Reglas que se aplican a todo el diccionario

1. **Una fila es una observación experimental**. Varias filas pueden compartir geometría y, por eso, compartir features.
2. Q1 se calcula sobre la distancia mínima Cα de cada residuo al otro participante, por separado para L y R. Se selecciona con `< Q1`, no `≤ Q1` ni 25 Å.
3. Las características describen la estructura observada; no aplican las mutaciones del Excel. Los vecinos necesarios para φ/ψ/ω pueden estar fuera de Q1.
4. Las fracciones químicas usan **N_SUPPORTED**. La cobertura química usa **N_SELECTED**. Las medias geométricas usan solo mediciones válidas.
5. `NULL` no equivale a 0. Los conteos de NULL son de esta versión de la OBT; no son una regla de nulabilidad futura ni un conteo de geometrías únicas.
6. `PKD` es y. `KD_M` y `KD_M_RAW` contienen la etiqueta de forma directa: excluirlos de X. `MEAN_KD_HYDROPATHY` significa Kyte–Doolittle y no contiene el Kd experimental.
7. No se ejecutó selección de features, imputación ni split. Identificadores y controles de calidad no entran automáticamente en X.

## Función de las columnas

| Función | Cantidad | Interpretación |
|---|---:|---|
| identifier | 11 | Identificador para uniones, trazabilidad o agrupación; no incluir directamente en X. |
| provenance | 22 | Información de procedencia/configuración; no incluir por defecto en X. |
| context | 10 | Contexto descriptivo o experimental; requiere interpretación/selección antes de cualquier uso en X. |
| target_leakage | 2 | Contiene la afinidad experimental o su transformación directa: excluir de X para predecir pKd. |
| target | 1 | Variable objetivo (y) que queremos predecir; no incluir en X. |
| quality_control | 59 | Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X. |
| predictor_candidate | 174 | Característica candidata: evaluar selección y redundancia; no inclusión automática en X. |
| conditional_predictor | 1 | Contexto candidato solo si se conocerá al predecir y se controla su calidad. |

## Índice

- [Identificadores, afinidad y contexto](#general) — 50 columnas
- [Geometría general Cα](#geometry) — 14 columnas
- [Ligando: selección y composición química](#ligand_chemistry) — 65 columnas
- [Ligando: geometría interna](#ligand_backbone) — 43 columnas
- [Receptor: selección y composición química](#receptor_chemistry) — 65 columnas
- [Receptor: geometría interna](#receptor_backbone) — 43 columnas

<a id="general"></a>
## Identificadores, afinidad y contexto

### 001. `OBSERVATION_ID`

Identificador de la fila original, generado con el hash del archivo, nombre de hoja y número de fila.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `identifier`.
- **Uso:** Identificador para uniones, trazabilidad o agrupación; no incluir directamente en X.
- **Ausencias:** No se permite NULL: es la clave única de la OBT. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.OBSERVATION_ID`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>), [source_inputs.py](<../scripts/source_inputs.py>).
- **Interpretación:** Repetir PDB no implica repetir este ID.

### 002. `SOURCE_KEY`

Clave SHA-256 de la combinación de archivo/version, hoja y dataset de procedencia.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `identifier`.
- **Uso:** Identificador para uniones, trazabilidad o agrupación; no incluir directamente en X.
- **Ausencias:** Ausencia en la fuente; SOURCE_KEY y EXPERIMENT_KEY se generan y deben estar presentes. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.SOURCE_KEY`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>), [gold_keys.sql](<../dbt/macros/gold_keys.sql>).

### 003. `EXPERIMENT_KEY`

Clave SHA-256 de los campos de contexto experimental reportados; compartirla no demuestra que sea el mismo ensayo.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `identifier`.
- **Uso:** Identificador para uniones, trazabilidad o agrupación; no incluir directamente en X.
- **Ausencias:** Ausencia en la fuente; SOURCE_KEY y EXPERIMENT_KEY se generan y deben estar presentes. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.EXPERIMENT_KEY`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>), [gold_keys.sql](<../dbt/macros/gold_keys.sql>).

### 004. `GEOMETRY_ID`

Clave del archivo estructural, PDB, grupos L/R, código y parámetros del cálculo; no es una proteína ni interfaz biológica universal.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `identifier`.
- **Uso:** Identificador para uniones, trazabilidad o agrupación; no incluir directamente en X.
- **Ausencias:** NULL si no se asignó geometría. NULL observados: **3 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.GEOMETRY_ID`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>), [run_silver.py](<../scripts/run_silver.py>).

### 005. `LIGAND_PARTICIPANT_KEY`

Referencia al participante L de la geometría: GEOMETRY_ID seguido de :L.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `identifier`.
- **Uso:** Identificador para uniones, trazabilidad o agrupación; no incluir directamente en X.
- **Ausencias:** NULL si no se asignó geometría. NULL observados: **3 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.LIGAND_PARTICIPANT_KEY`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).

### 006. `RECEPTOR_PARTICIPANT_KEY`

Referencia al participante R de la geometría: GEOMETRY_ID seguido de :R.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `identifier`.
- **Uso:** Identificador para uniones, trazabilidad o agrupación; no incluir directamente en X.
- **Ausencias:** NULL si no se asignó geometría. NULL observados: **3 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.RECEPTOR_PARTICIPANT_KEY`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).

### 007. `PDB_ID`

Identificador de la entrada estructural del PDB asociada a la observación; no identifica una proteína única.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `identifier`.
- **Uso:** Identificador para uniones, trazabilidad o agrupación; no incluir directamente en X.
- **Ausencias:** Ausencia en la fuente; SOURCE_KEY y EXPERIMENT_KEY se generan y deben estar presentes. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.PDB_ID`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).

### 008. `COMPLEX_ID`

Identificador de complejo que aporta el Excel original; se conserva sin redefinirlo.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `identifier`.
- **Uso:** Identificador para uniones, trazabilidad o agrupación; no incluir directamente en X.
- **Ausencias:** Ausencia en la fuente; SOURCE_KEY y EXPERIMENT_KEY se generan y deben estar presentes. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.COMPLEX_ID`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).

### 009. `SOURCE_ROW`

Número de fila de origen en el Excel, contando el encabezado como fila 1.

- **Tipo:** `NUMBER(38,0)`. **Unidad:** fila de archivo. **Función ML:** `provenance`.
- **Uso:** Información de procedencia/configuración; no incluir por defecto en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.SOURCE_ROW`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>), [source_inputs.py](<../scripts/source_inputs.py>).
- **Interpretación:** No es la posición actual ni un orden biológico.

### 010. `SOURCE_INDEX_RAW`

Valor textual de la columna sin nombre _unnamed_0 del Excel; es un índice de origen, no la clave principal.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `provenance`.
- **Uso:** Información de procedencia/configuración; no incluir por defecto en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.SOURCE_INDEX_RAW`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>), [source_inputs.py](<../scripts/source_inputs.py>).

### 011. `LIGAND_NAME`

Nombre descriptivo del ligando reportado en el Excel.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `context`.
- **Uso:** Contexto descriptivo o experimental; requiere interpretación/selección antes de cualquier uso en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.LIGAND_NAME`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).
- **Interpretación:** Puede representar un grupo de cadenas; no se transforma en identidad molecular global.

### 012. `RECEPTOR_NAME`

Nombre descriptivo del receptor reportado en el Excel.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `context`.
- **Uso:** Contexto descriptivo o experimental; requiere interpretación/selección antes de cualquier uso en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.RECEPTOR_NAME`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).
- **Interpretación:** Puede representar un grupo de cadenas; no se transforma en identidad molecular global.

### 013. `LIGAND_CHAINS_RAW`

Texto original de las cadenas asignadas al ligando.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `context`.
- **Uso:** Contexto descriptivo o experimental; requiere interpretación/selección antes de cualquier uso en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.LIGAND_CHAINS_RAW`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).
- **Interpretación:** Se preservan identificadores de cadena de autor y mayúsculas/minúsculas.

### 014. `RECEPTOR_CHAINS_RAW`

Texto original de las cadenas asignadas al receptor.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `context`.
- **Uso:** Contexto descriptivo o experimental; requiere interpretación/selección antes de cualquier uso en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.RECEPTOR_CHAINS_RAW`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).
- **Interpretación:** Se preservan identificadores de cadena de autor y mayúsculas/minúsculas.

### 015. `MUTATIONS_RAW`

Anotación original de mutaciones; el cálculo estructural no aplica estas sustituciones.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `context`.
- **Uso:** Contexto descriptivo o experimental; requiere interpretación/selección antes de cualquier uso en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **5230 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.MUTATIONS_RAW`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).
- **Interpretación:** Consultar MUTATION_STRUCTURE_STATUS; no asumir que las features corresponden al mutante.

### 016. `SUBGROUP_RAW`

Etiqueta original Subgroup del dataset; se conserva sin asignarle un significado nuevo.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `context`.
- **Uso:** Contexto descriptivo o experimental; requiere interpretación/selección antes de cualquier uso en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **9209 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.SUBGROUP_RAW`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).

### 017. `KD_M`

Constante de disociación experimental Kd convertida a número en mol/L.

- **Tipo:** `FLOAT`. **Unidad:** mol/L. **Función ML:** `target_leakage`.
- **Uso:** Contiene la afinidad experimental o su transformación directa: excluir de X para predecir pKd.
- **Cálculo:** TRY_TO_DOUBLE(KD_M_RAW)
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.KD_M`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).
- **Interpretación:** Contiene la misma información objetivo que pKd; no introducirla como predictor.

### 018. `PKD`

Afinidad objetivo expresada como pKd; un pKd mayor corresponde a un Kd menor.

- **Tipo:** `FLOAT`. **Unidad:** adimensional. **Función ML:** `target`.
- **Uso:** Variable objetivo (y) que queremos predecir; no incluir en X.
- **Cálculo:** −log10(KD_M / (1 mol/L)); numéricamente −log10(KD_M)
- **Ausencias:** NULL cuando Kd está ausente, no es interpretable, no es positivo o no es finito. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.PKD`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).

### 019. `KD_STATUS`

Resultado de la validación numérica de Kd.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.KD_STATUS`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).
- **Valores:** `valid`: Kd positivo y finito.; `invalid`: Kd interpretado pero no válido.; `missing_or_unparsed`: Kd ausente o no convertible a número.
- **Valores observados no nulos:** `valid`
- **Interpretación:** Validación de formato/valor; no verifica la exactitud experimental.

### 020. `KD_M_RAW`

Texto original de KD(M) en el Excel.

- **Tipo:** `TEXT`. **Unidad:** mol/L según encabezado original. **Función ML:** `target_leakage`.
- **Uso:** Contiene la afinidad experimental o su transformación directa: excluir de X para predecir pKd.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.KD_M_RAW`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).

### 021. `STRUCTURE_METHOD_RAW`

Método de determinación estructural reportado en el Excel.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `context`.
- **Uso:** Contexto descriptivo o experimental; requiere interpretación/selección antes de cualquier uso en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **10 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.STRUCTURE_METHOD_RAW`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).
- **Interpretación:** No confundir con AFFINITY_METHOD.

### 022. `RESOLUTION_ANGSTROM`

Resolución estructural convertida a número a partir del Excel.

- **Tipo:** `FLOAT`. **Unidad:** Å. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** TRY_TO_DOUBLE(RESOLUTION_ANGSTROM_RAW)
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **302 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.RESOLUTION_ANGSTROM`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).
- **Interpretación:** Indicador de la estructura, no distancia entre proteínas; puede no aplicar a ciertos métodos.

### 023. `RESOLUTION_ANGSTROM_RAW`

Resolución estructural en su formato textual original.

- **Tipo:** `TEXT`. **Unidad:** Å según encabezado original. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **302 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.RESOLUTION_ANGSTROM_RAW`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).

### 024. `STRUCTURE_REFERENCE_RAW`

Referencia bibliográfica asociada a la estructura en el Excel; se conserva como texto.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `provenance`.
- **Uso:** Información de procedencia/configuración; no incluir por defecto en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **117 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.STRUCTURE_REFERENCE_RAW`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).

### 025. `STRUCTURE_RELEASE_DATE_RAW`

Fecha reportada de publicación/liberación estructural, conservada como texto sin normalizar.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `provenance`.
- **Uso:** Información de procedencia/configuración; no incluir por defecto en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.STRUCTURE_RELEASE_DATE_RAW`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).

### 026. `GEOMETRY_STATUS`

Estado de asignación/cálculo de la geometría Cα para la observación.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.GEOMETRY_STATUS`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).
- **Valores:** `computed`: Geometría Cα calculada.; `structure_not_usable`: El cálculo encontró un problema estructural.; `invalid_chain_groups`: Grupos de cadenas ausentes, vacíos o solapados.; `structure_missing`: No se encontró archivo estructural disponible.; `assigned`: Asignación de estructura presente, pero sin resultado de cálculo asociado (estado de respaldo, no equivalente a computed).; `mapping_missing`: Falta el vínculo de la observación con la geometría.
- **Valores observados no nulos:** `computed`, `structure_not_usable`, `invalid_chain_groups`

### 027. `GEOMETRY_ISSUE`

Motivo textual de fallo del cálculo estructural, cuando existe.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Ausencias:** Normalmente NULL cuando la geometría se calculó; también puede faltar si el problema ocurrió antes de crear la geometría. NULL observados: **11930 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.GEOMETRY_ISSUE`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).

### 028. `STRUCTURE_VERSIONS`

Cantidad de archivos estructurales con SHA-256 distintos disponibles para la combinación de versión de fuente y PDB.

- **Tipo:** `NUMBER(38,0)`. **Unidad:** versiones. **Función ML:** `provenance`.
- **Uso:** Información de procedencia/configuración; no incluir por defecto en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.STRUCTURE_VERSIONS`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>), [07_silver_inputs.sql](<../sql/07_silver_inputs.sql>).
- **Interpretación:** El pipeline selecciona el más reciente disponible. No cuenta modelos, cadenas ni conformaciones dentro del archivo.

### 029. `MUTATION_STRUCTURE_STATUS`

Resultado de comparar las mutaciones anotadas con las identidades observadas en los sitios estructurales.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.MUTATION_STRUCTURE_STATUS`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [geometry_core.py](<../scripts/geometry_core.py>), [silver_structure_geometry.sql](<../dbt/models/silver/silver_structure_geometry.sql>), [run_silver.py](<../scripts/run_silver.py>).
- **Valores:** `not_annotated`: No hay anotación de mutación interpretable como tal; no demuestra ausencia biológica de mutaciones.; `target_residues_present`: Todos los sitios anotados contienen la identidad objetivo. No valida la conformación completa del mutante.; `reference_geometry_only`: Hay residuos de referencia en sitios anotados; puede haber también algunos objetivos. Las features no modelan esos cambios.; `needs_review`: Anotación no interpretada, sitio ausente o identidad no coincidente.; `structure_unavailable`: Hay anotación de mutación, pero no geometría calculada para comprobarla.
- **Valores observados no nulos:** `needs_review`, `reference_geometry_only`, `not_annotated`, `structure_unavailable`, `target_residues_present`

### 030. `USES_REFERENCE_FOR_MUTATION`

Bandera trivalente que indica si los sitios anotados requieren usar geometría de referencia para una mutación.

- **Tipo:** `BOOLEAN`. **Unidad:** No aplica. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Ausencias:** No equivale a false; incluye not_annotated, needs_review y structure_unavailable. NULL observados: **9311 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.USES_REFERENCE_FOR_MUTATION`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).
- **Valores:** `true`: Estado reference_geometry_only.; `false`: Estado target_residues_present.; `NULL`: Otros estados; no se puede concluir true/false.
- **Valores observados no nulos:** `True`, `False`

### 031. `HAS_CA_CONTACTS_10`

Existe al menos un par Cα–Cα entre participantes a menos de 10 Å, considerando todos los Cα utilizables.

- **Tipo:** `BOOLEAN`. **Unidad:** booleano. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** MIN_DISTANCE_ANGSTROM < 10
- **Ausencias:** NULL si no pudo calcularse geometría. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.HAS_CA_CONTACTS_10`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [geometry_core.py](<../scripts/geometry_core.py>), [silver_structure_geometry.sql](<../dbt/models/silver/silver_structure_geometry.sql>).
- **Interpretación:** No demuestra unión experimental ni identifica un enlace químico.

### 032. `BIOLOGICAL_ASSEMBLY_VALIDATED`

Indica si el pipeline validó el ensamblaje biológico.

- **Tipo:** `BOOLEAN`. **Unidad:** booleano. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Ausencias:** Puede ser NULL cuando no hay una geometría asociada. NULL observados: **3 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.BIOLOGICAL_ASSEMBLY_VALIDATED`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).
- **Valores observados no nulos:** `False`
- **Interpretación:** Esta versión no hace esa validación. false significa no validado, no que sea biológicamente incorrecto.

### 033. `HAS_VALID_LABEL`

Indica si KD_STATUS es valid.

- **Tipo:** `BOOLEAN`. **Unidad:** booleano. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** KD_STATUS = 'valid'
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.HAS_VALID_LABEL`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).
- **Interpretación:** Es información sobre la etiqueta; usar para control de elegibilidad, no como predictor de la etiqueta.

### 034. `HAS_COMPUTED_GEOMETRY`

Indica si GEOMETRY_STATUS es computed.

- **Tipo:** `BOOLEAN`. **Unidad:** booleano. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** GEOMETRY_STATUS = 'computed'
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.HAS_COMPUTED_GEOMETRY`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).

### 035. `HAS_Q1_BOTH_PARTNERS`

Indica si ambos participantes tienen al menos un residuo seleccionado por Q1.

- **Tipo:** `BOOLEAN`. **Unidad:** booleano. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** COALESCE(N_SELECTED_Q1_LIGAND > 0 AND N_SELECTED_Q1_RECEPTOR > 0, false)
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.HAS_Q1_BOTH_PARTNERS`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).
- **Interpretación:** false también cubre geometrías no disponibles; revisar GEOMETRY_STATUS.

### 036. `NEEDS_VARIANT_REVIEW`

Bandera de revisión de variante definida por el estado de mutación.

- **Tipo:** `BOOLEAN`. **Unidad:** booleano. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** true salvo not_annotated o target_residues_present; estado NULL también produce true
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.FACT_AFFINITY.NEEDS_VARIANT_REVIEW`.
- **Código:** [fact_affinity.sql](<../dbt/models/gold/fact_affinity.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).
- **Interpretación:** false no significa que toda la observación esté aprobada para entrenamiento.

### 037. `SOURCE_SHA256`

Huella SHA-256 del archivo de entrada del que procede la observación.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `provenance`.
- **Uso:** Información de procedencia/configuración; no incluir por defecto en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_SOURCE.SOURCE_SHA256`.
- **Código:** [dim_source.sql](<../dbt/models/gold/dim_source.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>), [source_inputs.py](<../scripts/source_inputs.py>).

### 038. `SOURCE_FILE`

Nombre del archivo de entrada.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `provenance`.
- **Uso:** Información de procedencia/configuración; no incluir por defecto en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_SOURCE.SOURCE_FILE`.
- **Código:** [dim_source.sql](<../dbt/models/gold/dim_source.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).

### 039. `SOURCE_SHEET`

Hoja del Excel de origen.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `provenance`.
- **Uso:** Información de procedencia/configuración; no incluir por defecto en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_SOURCE.SOURCE_SHEET`.
- **Código:** [dim_source.sql](<../dbt/models/gold/dim_source.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).

### 040. `SOURCE_DATASET`

Nombre del dataset de procedencia reportado en Source Data Set.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `provenance`.
- **Uso:** Información de procedencia/configuración; no incluir por defecto en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_SOURCE.SOURCE_DATASET`.
- **Código:** [dim_source.sql](<../dbt/models/gold/dim_source.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).

### 041. `AFFINITY_METHOD`

Método de medición de afinidad, recortado y con marcadores de desconocido convertidos a NULL.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `context`.
- **Uso:** Contexto descriptivo o experimental; requiere interpretación/selección antes de cualquier uso en X.
- **Cálculo:** TRIM del texto; unknown/n/a/na/none/null/vacío → NULL
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **4019 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_EXPERIMENT.AFFINITY_METHOD`.
- **Código:** [dim_experiment.sql](<../dbt/models/gold/dim_experiment.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).
- **Interpretación:** Puede reflejar sesgo entre ensayos; no se propone como entrada automática a un predictor previo al experimento.

### 042. `AFFINITY_METHOD_RAW`

Método de medición de afinidad en su texto original.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `context`.
- **Uso:** Contexto descriptivo o experimental; requiere interpretación/selección antes de cualquier uso en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **3765 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_EXPERIMENT.AFFINITY_METHOD_RAW`.
- **Código:** [dim_experiment.sql](<../dbt/models/gold/dim_experiment.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).

### 043. `TEMPERATURE_K`

Temperatura de la medición interpretada como número de kelvin; puede proceder de una temperatura anotada como supuesta.

- **Tipo:** `FLOAT`. **Unidad:** K. **Función ML:** `conditional_predictor`.
- **Uso:** Contexto candidato solo si se conocerá al predecir y se controla su calidad.
- **Cálculo:** Extraer número si el texto coincide con el formato decimal reconocido, opcionalmente seguido de (assumed); la validez se informa en TEMPERATURE_STATUS.
- **Ausencias:** NULL si el texto está ausente o no tiene el formato reconocido. NULL observados: **4535 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_EXPERIMENT.TEMPERATURE_K`.
- **Código:** [dim_experiment.sql](<../dbt/models/gold/dim_experiment.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).
- **Interpretación:** Consultar TEMPERATURE_STATUS y TEMPERATURE_ASSUMED. Solo usar si se conoce la temperatura del escenario que se va a predecir.

### 044. `TEMPERATURE_RAW`

Texto original de Temperature(K), incluidas anotaciones como (assumed).

- **Tipo:** `TEXT`. **Unidad:** K según encabezado original. **Función ML:** `context`.
- **Uso:** Contexto descriptivo o experimental; requiere interpretación/selección antes de cualquier uso en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **4535 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_EXPERIMENT.TEMPERATURE_RAW`.
- **Código:** [dim_experiment.sql](<../dbt/models/gold/dim_experiment.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).

### 045. `TEMPERATURE_STATUS`

Estado de interpretación de la temperatura.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_EXPERIMENT.TEMPERATURE_STATUS`.
- **Código:** [dim_experiment.sql](<../dbt/models/gold/dim_experiment.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).
- **Valores:** `missing`: Texto NULL.; `unparsed`: No se pudo extraer el número.; `invalid`: Número interpretado ≤ 0 K.; `assumed`: Valor interpretable con anotación de supuesto.; `reported`: Valor interpretable sin anotación de supuesto.
- **Valores observados no nulos:** `reported`, `assumed`, `missing`

### 046. `TEMPERATURE_ASSUMED`

El texto original contiene assumed, ignorando mayúsculas.

- **Tipo:** `BOOLEAN`. **Unidad:** booleano. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_EXPERIMENT.TEMPERATURE_ASSUMED`.
- **Código:** [dim_experiment.sql](<../dbt/models/gold/dim_experiment.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).
- **Interpretación:** false no demuestra medición real: también ocurre cuando no hay temperatura.

### 047. `AFFINITY_REFERENCE_RAW`

Referencia bibliográfica de la medición de afinidad tal como viene en el Excel; puede ser PMID, texto o TBD.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `provenance`.
- **Uso:** Información de procedencia/configuración; no incluir por defecto en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **183 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_EXPERIMENT.AFFINITY_REFERENCE_RAW`.
- **Código:** [dim_experiment.sql](<../dbt/models/gold/dim_experiment.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).

### 048. `AFFINITY_REFERENCE_STATUS`

Clasificación del texto de referencia de afinidad.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **0 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_EXPERIMENT.AFFINITY_REFERENCE_STATUS`.
- **Código:** [dim_experiment.sql](<../dbt/models/gold/dim_experiment.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).
- **Valores:** `missing`: NULL o vacío.; `placeholder`: TBD.; `pmid`: Solo dígitos.; `text_reference`: Otro texto.
- **Valores observados no nulos:** `pmid`, `placeholder`, `text_reference`, `missing`
- **Interpretación:** pmid identifica un formato; no se verificó el artículo con esta regla.

### 049. `AFFINITY_PMID`

Identificador numérico PubMed interpretado de la referencia de afinidad cuando contiene solo dígitos.

- **Tipo:** `NUMBER(38,0)`. **Unidad:** No aplica. **Función ML:** `identifier`.
- **Uso:** Identificador para uniones, trazabilidad o agrupación; no incluir directamente en X.
- **Ausencias:** NULL si no contiene solo dígitos o si no se convierte a NUMBER. No implica que no exista publicación. NULL observados: **1304 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_EXPERIMENT.AFFINITY_PMID`.
- **Código:** [dim_experiment.sql](<../dbt/models/gold/dim_experiment.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).

### 050. `AFFINITY_RELEASE_DATE_RAW`

Fecha reportada de la referencia/medición de afinidad; se conserva como texto sin normalizar.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `provenance`.
- **Uso:** Información de procedencia/configuración; no incluir por defecto en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **549 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_EXPERIMENT.AFFINITY_RELEASE_DATE_RAW`.
- **Código:** [dim_experiment.sql](<../dbt/models/gold/dim_experiment.sql>), [silver_affinity_observations.sql](<../dbt/models/silver/silver_affinity_observations.sql>), [bronze_affinity_observations.sql](<../dbt/models/bronze/bronze_affinity_observations.sql>).


<a id="geometry"></a>
## Geometría general Cα

### 051. `STRUCTURE_SHA256`

Huella SHA-256 del archivo estructural exacto utilizado, en su representación almacenada.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `provenance`.
- **Uso:** Información de procedencia/configuración; no incluir por defecto en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **3 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_GEOMETRY.STRUCTURE_SHA256`.
- **Código:** [dim_geometry.sql](<../dbt/models/gold/dim_geometry.sql>), [geometry_core.py](<../scripts/geometry_core.py>), [silver_structure_geometry.sql](<../dbt/models/silver/silver_structure_geometry.sql>).

### 052. `CODE_SHA256`

Huella del código/dependencias que identifica la versión del cálculo Cα; no es una versión global de todos los componentes.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `provenance`.
- **Uso:** Información de procedencia/configuración; no incluir por defecto en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **3 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_GEOMETRY.CODE_SHA256`.
- **Código:** [dim_geometry.sql](<../dbt/models/gold/dim_geometry.sql>), [geometry_core.py](<../scripts/geometry_core.py>), [silver_structure_geometry.sql](<../dbt/models/silver/silver_structure_geometry.sql>), [run_silver.py](<../scripts/run_silver.py>).

### 053. `LIGAND_CHAINS_JSON`

Lista JSON de cadenas de autor usadas como ligando en la geometría.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `identifier`.
- **Uso:** Identificador para uniones, trazabilidad o agrupación; no incluir directamente en X.
- **Ausencias:** NULL si no existe GEOMETRY_ID; una geometría fallida puede conservar su lista de cadenas. NULL observados: **3 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_GEOMETRY.LIGAND_CHAINS_JSON`.
- **Código:** [dim_geometry.sql](<../dbt/models/gold/dim_geometry.sql>), [geometry_core.py](<../scripts/geometry_core.py>), [silver_structure_geometry.sql](<../dbt/models/silver/silver_structure_geometry.sql>).

### 054. `RECEPTOR_CHAINS_JSON`

Lista JSON de cadenas de autor usadas como receptor en la geometría.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `identifier`.
- **Uso:** Identificador para uniones, trazabilidad o agrupación; no incluir directamente en X.
- **Ausencias:** NULL si no existe GEOMETRY_ID; una geometría fallida puede conservar su lista de cadenas. NULL observados: **3 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_GEOMETRY.RECEPTOR_CHAINS_JSON`.
- **Código:** [dim_geometry.sql](<../dbt/models/gold/dim_geometry.sql>), [geometry_core.py](<../scripts/geometry_core.py>), [silver_structure_geometry.sql](<../dbt/models/silver/silver_structure_geometry.sql>).

### 055. `N_LIGAND`

Número de residuos del ligando con Cα utilizable en el modelo y grupos de cadenas seleccionados, antes del filtro Q1.

- **Tipo:** `NUMBER(38,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_GEOMETRY.N_LIGAND`.
- **Código:** [dim_geometry.sql](<../dbt/models/gold/dim_geometry.sql>), [geometry_core.py](<../scripts/geometry_core.py>), [silver_structure_geometry.sql](<../dbt/models/silver/silver_structure_geometry.sql>).
- **Interpretación:** No es necesariamente la longitud completa de secuencia: excluye residuos no observados o sin Cα utilizable.

### 056. `N_RECEPTOR`

Número de residuos del receptor con Cα utilizable en el modelo y grupos de cadenas seleccionados, antes del filtro Q1.

- **Tipo:** `NUMBER(38,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_GEOMETRY.N_RECEPTOR`.
- **Código:** [dim_geometry.sql](<../dbt/models/gold/dim_geometry.sql>), [geometry_core.py](<../scripts/geometry_core.py>), [silver_structure_geometry.sql](<../dbt/models/silver/silver_structure_geometry.sql>).
- **Interpretación:** No es necesariamente la longitud completa de secuencia: excluye residuos no observados o sin Cα utilizable.

### 057. `MIN_DISTANCE_ANGSTROM`

Menor distancia Cα–Cα entre ambos participantes, considerando todos los residuos utilizables.

- **Tipo:** `FLOAT`. **Unidad:** Å. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** min_{i en L, j en R} ||Cα_i−Cα_j||
- **Ausencias:** NULL si no se calculó geometría. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_GEOMETRY.MIN_DISTANCE_ANGSTROM`.
- **Código:** [dim_geometry.sql](<../dbt/models/gold/dim_geometry.sql>), [geometry_core.py](<../scripts/geometry_core.py>), [silver_structure_geometry.sql](<../dbt/models/silver/silver_structure_geometry.sql>).
- **Interpretación:** No es distancia entre átomos pesados cualesquiera; no demuestra un enlace.

### 058. `Q1_LIGAND_ANGSTROM`

Primer cuartil de las distancias mínimas Cα de cada residuo del ligando a cualquier residuo del otro participante.

- **Tipo:** `FLOAT`. **Unidad:** Å. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** percentil 25 con interpolación lineal de {min_j ||Cα_i−Cα_j||} del ligando
- **Ausencias:** NULL si no hay geometría calculada. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_GEOMETRY.Q1_LIGAND_ANGSTROM`.
- **Código:** [dim_geometry.sql](<../dbt/models/gold/dim_geometry.sql>), [geometry_core.py](<../scripts/geometry_core.py>), [silver_structure_geometry.sql](<../dbt/models/silver/silver_structure_geometry.sql>).
- **Interpretación:** Umbral propio del participante; se selecciona con distancia estrictamente menor. No es 25 Å ni el cuartil de todos los pares.

### 059. `Q1_RECEPTOR_ANGSTROM`

Primer cuartil de las distancias mínimas Cα de cada residuo del receptor a cualquier residuo del otro participante.

- **Tipo:** `FLOAT`. **Unidad:** Å. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** percentil 25 con interpolación lineal de {min_j ||Cα_i−Cα_j||} del receptor
- **Ausencias:** NULL si no hay geometría calculada. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_GEOMETRY.Q1_RECEPTOR_ANGSTROM`.
- **Código:** [dim_geometry.sql](<../dbt/models/gold/dim_geometry.sql>), [geometry_core.py](<../scripts/geometry_core.py>), [silver_structure_geometry.sql](<../dbt/models/silver/silver_structure_geometry.sql>).
- **Interpretación:** Umbral propio del participante; se selecciona con distancia estrictamente menor. No es 25 Å ni el cuartil de todos los pares.

### 060. `N_SELECTED_Q1_LIGAND`

Número de residuos del ligando cuya distancia mínima al otro participante es estrictamente menor que su Q1.

- **Tipo:** `NUMBER(38,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_GEOMETRY.N_SELECTED_Q1_LIGAND`.
- **Código:** [dim_geometry.sql](<../dbt/models/gold/dim_geometry.sql>), [geometry_core.py](<../scripts/geometry_core.py>), [silver_structure_geometry.sql](<../dbt/models/silver/silver_structure_geometry.sql>).
- **Equivalencias de conteo:** `LIGAND_N_SELECTED`, `LIGAND_CHEM_N_SELECTED`, `LIGAND_BACKBONE_N_MEASURED_ROWS`
- **Interpretación:** Los empates pueden hacer que se seleccione menos del 25 %.

### 061. `N_SELECTED_Q1_RECEPTOR`

Número de residuos del receptor cuya distancia mínima al otro participante es estrictamente menor que su Q1.

- **Tipo:** `NUMBER(38,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_GEOMETRY.N_SELECTED_Q1_RECEPTOR`.
- **Código:** [dim_geometry.sql](<../dbt/models/gold/dim_geometry.sql>), [geometry_core.py](<../scripts/geometry_core.py>), [silver_structure_geometry.sql](<../dbt/models/silver/silver_structure_geometry.sql>).
- **Equivalencias de conteo:** `RECEPTOR_N_SELECTED`, `RECEPTOR_CHEM_N_SELECTED`, `RECEPTOR_BACKBONE_N_MEASURED_ROWS`
- **Interpretación:** Los empates pueden hacer que se seleccione menos del 25 %.

### 062. `SELECTED_PAIRS_LT10`

Cantidad de pares L–R con ambos residuos seleccionados por Q1 y distancia Cα–Cα menor que 10 Å.

- **Tipo:** `NUMBER(38,0)`. **Unidad:** pares. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_GEOMETRY.SELECTED_PAIRS_LT10`.
- **Código:** [dim_geometry.sql](<../dbt/models/gold/dim_geometry.sql>), [geometry_core.py](<../scripts/geometry_core.py>), [silver_structure_geometry.sql](<../dbt/models/silver/silver_structure_geometry.sql>).
- **Interpretación:** Cuenta pares, no residuos ni enlaces de hidrógeno.

### 063. `SELECTED_PAIR_COUNT`

Número de todos los pares entre los residuos Q1 de L y los residuos Q1 de R, sin corte adicional de distancia.

- **Tipo:** `NUMBER(38,0)`. **Unidad:** pares. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** N_SELECTED_Q1_LIGAND × N_SELECTED_Q1_RECEPTOR
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_GEOMETRY.SELECTED_PAIR_COUNT`.
- **Código:** [dim_geometry.sql](<../dbt/models/gold/dim_geometry.sql>), [geometry_core.py](<../scripts/geometry_core.py>), [silver_structure_geometry.sql](<../dbt/models/silver/silver_structure_geometry.sql>).
- **Interpretación:** Puede incluir pares lejanos; seleccionar cada residuo por su vecino más próximo no hace cercanos todos los pares.

### 064. `GEOMETRY_PARAMETERS_JSON`

Parámetros versionados del cálculo Cα, serializados como texto JSON.

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `provenance`.
- **Uso:** Información de procedencia/configuración; no incluir por defecto en X.
- **Ausencias:** NULL indica que no se recibió o no pudo interpretarse ese dato. NULL observados: **3 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_GEOMETRY.GEOMETRY_PARAMETERS_JSON`.
- **Código:** [dim_geometry.sql](<../dbt/models/gold/dim_geometry.sql>), [geometry_core.py](<../scripts/geometry_core.py>), [silver_structure_geometry.sql](<../dbt/models/silver/silver_structure_geometry.sql>).


<a id="ligand_chemistry"></a>
## Ligando: selección y composición química

### 065. `LIGAND_N_SELECTED`

Número de residuos Q1 del ligando (L). Copia del conteo de selección geométrica.

- **Tipo:** `NUMBER(38,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** N_SELECTED_Q1_LIGAND
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.N_SELECTED` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [geometry_core.py](<../scripts/geometry_core.py>).
- **Equivalencias de conteo:** `N_SELECTED_Q1_LIGAND`, `LIGAND_CHEM_N_SELECTED`, `LIGAND_BACKBONE_N_MEASURED_ROWS`

### 066. `LIGAND_CHEM_FEATURE_VERSION`

Versión de las reglas químicas aplicadas al ligando (L).

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `provenance`.
- **Uso:** Información de procedencia/configuración; no incluir por defecto en X.
- **Ausencias:** NULL si no existe participante asociado. NULL observados: **3 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FEATURE_VERSION` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Valores:** `chemistry_v1`: Mapa de 20 aminoácidos y categorías definido en el proyecto.

### 067. `LIGAND_CHEM_FEATURE_BASIS`

Base estructural de las características químicas del ligando (L).

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `provenance`.
- **Uso:** Información de procedencia/configuración; no incluir por defecto en X.
- **Ausencias:** NULL si no existe participante asociado. NULL observados: **3 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FEATURE_BASIS` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Valores:** `observed_structure_q1`: Residuos observados seleccionados por Q1, sin construir mutantes.

### 068. `LIGAND_CHEM_CHEMISTRY_STATUS`

Estado de cobertura de las propiedades químicas del ligando (L).

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Ausencias:** NULL si no hay participante asociado; geometry_unavailable si existe pero su geometría falló. NULL observados: **3 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_CHEMISTRY_STATUS` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Valores:** `complete`: Todos los residuos Q1 tienen propiedades soportadas.; `partial_coverage`: Solo parte de los residuos Q1 tiene propiedades soportadas.; `no_supported_residues`: Hay selección Q1, pero ningún residuo soportado.; `empty_selection`: El filtro estricto Q1 no seleccionó residuos.; `geometry_unavailable`: La geometría no pudo calcularse.
- **Valores observados no nulos:** `complete`, `partial_coverage`, `geometry_unavailable`

### 069. `LIGAND_CHEM_N_SELECTED`

Cantidad de todos los residuos seleccionados por Q1 en el ligando (L).

- **Tipo:** `NUMBER(18,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_SELECTED` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Equivalencias de conteo:** `N_SELECTED_Q1_LIGAND`, `LIGAND_N_SELECTED`, `LIGAND_BACKBONE_N_MEASURED_ROWS`

### 070. `LIGAND_CHEM_N_SUPPORTED`

Cantidad de residuos Q1 canónicos cuyo nombre/código coincide con el mapa de los 20 aminoácidos en el ligando (L).

- **Tipo:** `NUMBER(18,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_SUPPORTED` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).

### 071. `LIGAND_CHEM_N_NONSTANDARD`

Cantidad de residuos Q1 marcados como no estándar por su nombre estructural en el ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_NONSTANDARD` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).

### 072. `LIGAND_CHEM_N_UNSUPPORTED`

Cantidad de residuos Q1 sin propiedades asignadas, incluidos los no estándar en el ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** LIGAND_CHEM_N_SELECTED − LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_UNSUPPORTED` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).

### 073. `LIGAND_CHEM_MEAN_KD_HYDROPATHY`

Hidropatía media Kyte–Doolittle de los residuos soportados Q1 del ligando (L). Valores mayores indican mayor hidropatía en esta escala.

- **Tipo:** `NUMBER(12,6)`. **Unidad:** escala adimensional Kyte–Doolittle. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** SUM(hidropatía de cada residuo soportado) / LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_MEAN_KD_HYDROPATHY` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Rango definido:** [−4.5, 4.5] cuando hay valores
- **Interpretación:** KD aquí significa Kyte–Doolittle; NO es el Kd experimental ni una fuga directa de la etiqueta. No es energía de unión. Media almacenada con 6 decimales.

### 074. `LIGAND_CHEM_AA_ENTROPY_BITS`

Diversidad de composición de los 20 aminoácidos soportados Q1 del ligando (L).

- **Tipo:** `NUMBER(32,12)`. **Unidad:** bits. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** −Σ p_a log2(p_a), p_a=N_AA_a/N_SUPPORTED; sumar solo p_a>0
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_AA_ENTROPY_BITS` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Rango definido:** [0, log2(20)] ≈ [0, 4.322]
- **Interpretación:** Es entropía de Shannon de la composición, no entropía termodinámica ni flexibilidad. Cada término se redondea a 12 decimales.

### 075. `LIGAND_CHEM_N_AA_A`

Cantidad de alanina (A, ALA) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos ALA con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_A` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 076. `LIGAND_CHEM_N_AA_C`

Cantidad de cisteína (C, CYS) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos CYS con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_C` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 077. `LIGAND_CHEM_N_AA_D`

Cantidad de aspartato / ácido aspártico (D, ASP) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos ASP con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_D` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 078. `LIGAND_CHEM_N_AA_E`

Cantidad de glutamato / ácido glutámico (E, GLU) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos GLU con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_E` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 079. `LIGAND_CHEM_N_AA_F`

Cantidad de fenilalanina (F, PHE) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos PHE con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_F` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 080. `LIGAND_CHEM_N_AA_G`

Cantidad de glicina (G, GLY) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos GLY con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_G` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 081. `LIGAND_CHEM_N_AA_H`

Cantidad de histidina (H, HIS) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos HIS con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_H` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 082. `LIGAND_CHEM_N_AA_I`

Cantidad de isoleucina (I, ILE) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos ILE con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_I` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 083. `LIGAND_CHEM_N_AA_K`

Cantidad de lisina (K, LYS) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos LYS con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_K` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 084. `LIGAND_CHEM_N_AA_L`

Cantidad de leucina (L, LEU) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos LEU con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_L` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 085. `LIGAND_CHEM_N_AA_M`

Cantidad de metionina (M, MET) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos MET con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_M` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 086. `LIGAND_CHEM_N_AA_N`

Cantidad de asparagina (N, ASN) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos ASN con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_N` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 087. `LIGAND_CHEM_N_AA_P`

Cantidad de prolina (P, PRO) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos PRO con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_P` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 088. `LIGAND_CHEM_N_AA_Q`

Cantidad de glutamina (Q, GLN) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos GLN con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_Q` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 089. `LIGAND_CHEM_N_AA_R`

Cantidad de arginina (R, ARG) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos ARG con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_R` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 090. `LIGAND_CHEM_N_AA_S`

Cantidad de serina (S, SER) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos SER con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_S` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 091. `LIGAND_CHEM_N_AA_T`

Cantidad de treonina (T, THR) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos THR con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_T` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 092. `LIGAND_CHEM_N_AA_V`

Cantidad de valina (V, VAL) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos VAL con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_V` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 093. `LIGAND_CHEM_N_AA_W`

Cantidad de triptófano (W, TRP) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos TRP con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_W` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 094. `LIGAND_CHEM_N_AA_Y`

Cantidad de tirosina (Y, TYR) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos TYR con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_Y` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 095. `LIGAND_CHEM_N_NONPOLAR`

Cantidad de aminoácidos no polares (G,A,V,L,I,M,P,F,W) soportados Q1 del ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Suma de los conteos N_AA de G,A,V,L,I,M,P,F,W
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_NONPOLAR` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).

### 096. `LIGAND_CHEM_N_POLAR_UNCHARGED`

Cantidad de aminoácidos polares sin carga, según la clasificación convencional (S,T,C,N,Q,Y) soportados Q1 del ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Suma de los conteos N_AA de S,T,C,N,Q,Y
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_POLAR_UNCHARGED` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** Clasificación por identidad; no representa cargas medidas ni estados de protonación.

### 097. `LIGAND_CHEM_N_ACIDIC`

Cantidad de aminoácidos ácidos (D,E) soportados Q1 del ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Suma de los conteos N_AA de D,E
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_ACIDIC` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** Clasificación por identidad; no representa cargas medidas ni estados de protonación.

### 098. `LIGAND_CHEM_N_BASIC`

Cantidad de aminoácidos básicos (K,R,H) soportados Q1 del ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Suma de los conteos N_AA de K,R,H
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_BASIC` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** Clasificación por identidad; no representa cargas medidas ni estados de protonación. Incluye H; no se asume que toda histidina esté protonada.

### 099. `LIGAND_CHEM_N_AROMATIC_RING`

Cantidad de aminoácidos con anillo aromático (F,W,Y,H) soportados Q1 del ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Suma de los conteos N_AA de F,W,Y,H
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AROMATIC_RING` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** Incluye H. No cuenta interacciones π–π. Grupo solapado con clases de polaridad; no sumar todos los grupos como una partición.

### 100. `LIGAND_CHEM_N_SULFUR_CONTAINING`

Cantidad de aminoácidos con azufre (C,M) soportados Q1 del ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Suma de los conteos N_AA de C,M
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_SULFUR_CONTAINING` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** Cuenta residuos C y M, no átomos de azufre ni enlaces disulfuro. Grupo solapado con clases de polaridad; no sumar todos los grupos como una partición.

### 101. `LIGAND_CHEM_N_ALIPHATIC_AVIL`

Cantidad de aminoácidos del subconjunto alifático AVIL (A,V,I,L) soportados Q1 del ligando (L).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Suma de los conteos N_AA de A,V,I,L
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_ALIPHATIC_AVIL` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** Grupo solapado con clases de polaridad; no sumar todos los grupos como una partición.

### 102. `LIGAND_CHEM_PROPERTY_COVERAGE`

Fracción de los residuos Q1 del ligando (L) para los que hay propiedades químicas soportadas.

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** LIGAND_CHEM_N_SUPPORTED / LIGAND_CHEM_N_SELECTED
- **Ausencias:** NULL si falta geometría/participante o N_SELECTED=0. Cero significa selección existente sin residuos soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_PROPERTY_COVERAGE` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).

### 103. `LIGAND_CHEM_FRACTION_AA_A`

Fracción de alanina (A, ALA) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** LIGAND_CHEM_N_AA_A / LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_A` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 104. `LIGAND_CHEM_FRACTION_AA_C`

Fracción de cisteína (C, CYS) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** LIGAND_CHEM_N_AA_C / LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_C` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 105. `LIGAND_CHEM_FRACTION_AA_D`

Fracción de aspartato / ácido aspártico (D, ASP) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** LIGAND_CHEM_N_AA_D / LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_D` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 106. `LIGAND_CHEM_FRACTION_AA_E`

Fracción de glutamato / ácido glutámico (E, GLU) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** LIGAND_CHEM_N_AA_E / LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_E` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 107. `LIGAND_CHEM_FRACTION_AA_F`

Fracción de fenilalanina (F, PHE) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** LIGAND_CHEM_N_AA_F / LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_F` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 108. `LIGAND_CHEM_FRACTION_AA_G`

Fracción de glicina (G, GLY) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** LIGAND_CHEM_N_AA_G / LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_G` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 109. `LIGAND_CHEM_FRACTION_AA_H`

Fracción de histidina (H, HIS) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** LIGAND_CHEM_N_AA_H / LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_H` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 110. `LIGAND_CHEM_FRACTION_AA_I`

Fracción de isoleucina (I, ILE) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** LIGAND_CHEM_N_AA_I / LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_I` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 111. `LIGAND_CHEM_FRACTION_AA_K`

Fracción de lisina (K, LYS) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** LIGAND_CHEM_N_AA_K / LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_K` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 112. `LIGAND_CHEM_FRACTION_AA_L`

Fracción de leucina (L, LEU) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** LIGAND_CHEM_N_AA_L / LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_L` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 113. `LIGAND_CHEM_FRACTION_AA_M`

Fracción de metionina (M, MET) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** LIGAND_CHEM_N_AA_M / LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_M` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 114. `LIGAND_CHEM_FRACTION_AA_N`

Fracción de asparagina (N, ASN) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** LIGAND_CHEM_N_AA_N / LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_N` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 115. `LIGAND_CHEM_FRACTION_AA_P`

Fracción de prolina (P, PRO) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** LIGAND_CHEM_N_AA_P / LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_P` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 116. `LIGAND_CHEM_FRACTION_AA_Q`

Fracción de glutamina (Q, GLN) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** LIGAND_CHEM_N_AA_Q / LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_Q` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 117. `LIGAND_CHEM_FRACTION_AA_R`

Fracción de arginina (R, ARG) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** LIGAND_CHEM_N_AA_R / LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_R` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 118. `LIGAND_CHEM_FRACTION_AA_S`

Fracción de serina (S, SER) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** LIGAND_CHEM_N_AA_S / LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_S` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 119. `LIGAND_CHEM_FRACTION_AA_T`

Fracción de treonina (T, THR) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** LIGAND_CHEM_N_AA_T / LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_T` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 120. `LIGAND_CHEM_FRACTION_AA_V`

Fracción de valina (V, VAL) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** LIGAND_CHEM_N_AA_V / LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_V` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 121. `LIGAND_CHEM_FRACTION_AA_W`

Fracción de triptófano (W, TRP) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** LIGAND_CHEM_N_AA_W / LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_W` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 122. `LIGAND_CHEM_FRACTION_AA_Y`

Fracción de tirosina (Y, TYR) entre los residuos soportados Q1 del ligando (L).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** LIGAND_CHEM_N_AA_Y / LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_Y` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 123. `LIGAND_CHEM_FRACTION_NONPOLAR`

Fracción de aminoácidos no polares (G,A,V,L,I,M,P,F,W) soportados Q1 del ligando (L).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** LIGAND_CHEM_N_NONPOLAR / LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; el denominador son los residuos soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_NONPOLAR` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).

### 124. `LIGAND_CHEM_FRACTION_POLAR_UNCHARGED`

Fracción de aminoácidos polares sin carga, según la clasificación convencional (S,T,C,N,Q,Y) soportados Q1 del ligando (L).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** LIGAND_CHEM_N_POLAR_UNCHARGED / LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; el denominador son los residuos soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_POLAR_UNCHARGED` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** Clasificación por identidad; no representa cargas medidas ni estados de protonación.

### 125. `LIGAND_CHEM_FRACTION_ACIDIC`

Fracción de aminoácidos ácidos (D,E) soportados Q1 del ligando (L).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** LIGAND_CHEM_N_ACIDIC / LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; el denominador son los residuos soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_ACIDIC` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** Clasificación por identidad; no representa cargas medidas ni estados de protonación.

### 126. `LIGAND_CHEM_FRACTION_BASIC`

Fracción de aminoácidos básicos (K,R,H) soportados Q1 del ligando (L).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** LIGAND_CHEM_N_BASIC / LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; el denominador son los residuos soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_BASIC` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** Clasificación por identidad; no representa cargas medidas ni estados de protonación. Incluye H; no se asume que toda histidina esté protonada.

### 127. `LIGAND_CHEM_FRACTION_AROMATIC_RING`

Fracción de aminoácidos con anillo aromático (F,W,Y,H) soportados Q1 del ligando (L).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** LIGAND_CHEM_N_AROMATIC_RING / LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; el denominador son los residuos soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AROMATIC_RING` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** Incluye H. No cuenta interacciones π–π. Grupo solapado con clases de polaridad; no sumar todos los grupos como una partición.

### 128. `LIGAND_CHEM_FRACTION_SULFUR_CONTAINING`

Fracción de aminoácidos con azufre (C,M) soportados Q1 del ligando (L).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** LIGAND_CHEM_N_SULFUR_CONTAINING / LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; el denominador son los residuos soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_SULFUR_CONTAINING` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** Cuenta residuos C y M, no átomos de azufre ni enlaces disulfuro. Grupo solapado con clases de polaridad; no sumar todos los grupos como una partición.

### 129. `LIGAND_CHEM_FRACTION_ALIPHATIC_AVIL`

Fracción de aminoácidos del subconjunto alifático AVIL (A,V,I,L) soportados Q1 del ligando (L).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** LIGAND_CHEM_N_ALIPHATIC_AVIL / LIGAND_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; el denominador son los residuos soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_ALIPHATIC_AVIL` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** Grupo solapado con clases de polaridad; no sumar todos los grupos como una partición.


<a id="ligand_backbone"></a>
## Ligando: geometría interna

### 130. `LIGAND_BACKBONE_FEATURE_VERSION`

Versión del cálculo y resumen del esqueleto peptídico del ligando (L).

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `provenance`.
- **Uso:** Información de procedencia/configuración; no incluir por defecto en X.
- **Ausencias:** NULL si no existe participante asociado. NULL observados: **3 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_FEATURE_VERSION` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Valores:** `backbone_v1`: φ, ψ, ω saliente, τ y tres longitudes.

### 131. `LIGAND_BACKBONE_FEATURE_BASIS`

Base del resumen geométrico interno del ligando (L).

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `provenance`.
- **Uso:** Información de procedencia/configuración; no incluir por defecto en X.
- **Ausencias:** NULL si no existe participante asociado. NULL observados: **3 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_FEATURE_BASIS` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Valores:** `observed_structure_q1`: Residuos Q1 de la estructura observada; vecinos pueden estar fuera de Q1.

### 132. `LIGAND_BACKBONE_N_MEASURED_ROWS`

Cantidad de filas de mediciones individuales del ligando (L); incluye residuos Q1 con ángulos ausentes.

- **Tipo:** `NUMBER(18,0)`. **Unidad:** residuos. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** LIGAND_N_SELECTED
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_N_MEASURED_ROWS` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Equivalencias de conteo:** `N_SELECTED_Q1_LIGAND`, `LIGAND_N_SELECTED`, `LIGAND_CHEM_N_SELECTED`
- **Interpretación:** No cuenta únicamente residuos con todos los ángulos válidos.

### 133. `LIGAND_BACKBONE_N_PHI_PSI_COMPLETE`

Cantidad de residuos Q1 del ligando (L) con φ y ψ simultáneamente disponibles.

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** COUNT_IF(PHI_DEG IS NOT NULL AND PSI_DEG IS NOT NULL)
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_N_PHI_PSI_COMPLETE` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).

### 134. `LIGAND_BACKBONE_N_PHI`

Número de residuos Q1 del ligando (L) con torsión φ calculable.

- **Tipo:** `NUMBER(18,0)`. **Unidad:** ángulos válidos. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** COUNT(PHI_DEG) no NULL
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_N_PHI` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión φ: C(i−1), N(i), Cα(i), C(i). Se usan vecinos reales de la cadena, aunque no sean Q1.

### 135. `LIGAND_BACKBONE_PHI_MEAN_SIN`

Media del seno de los ángulos φ válidos del ligando (L). Componente de la representación circular.

- **Tipo:** `NUMBER(18,12)`. **Unidad:** adimensional [−1,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** media(sin(φ × π/180)); términos redondeados a 12 decimales
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **137 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PHI_MEAN_SIN` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión φ: C(i−1), N(i), Cα(i), C(i). Se usan vecinos reales de la cadena, aunque no sean Q1. Usar junto con la otra componente; no es el seno/coseno de la media aritmética de ángulos.

### 136. `LIGAND_BACKBONE_PHI_MEAN_COS`

Media del coseno de los ángulos φ válidos del ligando (L). Componente de la representación circular.

- **Tipo:** `NUMBER(18,12)`. **Unidad:** adimensional [−1,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** media(cos(φ × π/180)); términos redondeados a 12 decimales
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **137 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PHI_MEAN_COS` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión φ: C(i−1), N(i), Cα(i), C(i). Se usan vecinos reales de la cadena, aunque no sean Q1. Usar junto con la otra componente; no es el seno/coseno de la media aritmética de ángulos.

### 137. `LIGAND_BACKBONE_PHI_RESULTANT_LENGTH`

Longitud R del vector circular medio de φ del ligando (L): cerca de 1 indica ángulos concentrados; cerca de 0, cancelación de direcciones.

- **Tipo:** `NUMBER(18,12)`. **Unidad:** adimensional [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** min(1, sqrt(LIGAND_BACKBONE_PHI_MEAN_SIN² + LIGAND_BACKBONE_PHI_MEAN_COS²))
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **137 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PHI_RESULTANT_LENGTH` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión φ: C(i−1), N(i), Cα(i), C(i). Se usan vecinos reales de la cadena, aunque no sean Q1. Una distribución multimodal también puede dar R bajo; no mide flexibilidad dinámica.

### 138. `LIGAND_BACKBONE_N_PSI`

Número de residuos Q1 del ligando (L) con torsión ψ calculable.

- **Tipo:** `NUMBER(18,0)`. **Unidad:** ángulos válidos. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** COUNT(PSI_DEG) no NULL
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_N_PSI` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión ψ: N(i), Cα(i), C(i), N(i+1). Se usan vecinos reales de la cadena, aunque no sean Q1.

### 139. `LIGAND_BACKBONE_PSI_MEAN_SIN`

Media del seno de los ángulos ψ válidos del ligando (L). Componente de la representación circular.

- **Tipo:** `NUMBER(18,12)`. **Unidad:** adimensional [−1,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** media(sin(ψ × π/180)); términos redondeados a 12 decimales
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **137 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PSI_MEAN_SIN` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión ψ: N(i), Cα(i), C(i), N(i+1). Se usan vecinos reales de la cadena, aunque no sean Q1. Usar junto con la otra componente; no es el seno/coseno de la media aritmética de ángulos.

### 140. `LIGAND_BACKBONE_PSI_MEAN_COS`

Media del coseno de los ángulos ψ válidos del ligando (L). Componente de la representación circular.

- **Tipo:** `NUMBER(18,12)`. **Unidad:** adimensional [−1,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** media(cos(ψ × π/180)); términos redondeados a 12 decimales
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **137 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PSI_MEAN_COS` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión ψ: N(i), Cα(i), C(i), N(i+1). Se usan vecinos reales de la cadena, aunque no sean Q1. Usar junto con la otra componente; no es el seno/coseno de la media aritmética de ángulos.

### 141. `LIGAND_BACKBONE_PSI_RESULTANT_LENGTH`

Longitud R del vector circular medio de ψ del ligando (L): cerca de 1 indica ángulos concentrados; cerca de 0, cancelación de direcciones.

- **Tipo:** `NUMBER(18,12)`. **Unidad:** adimensional [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** min(1, sqrt(LIGAND_BACKBONE_PSI_MEAN_SIN² + LIGAND_BACKBONE_PSI_MEAN_COS²))
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **137 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PSI_RESULTANT_LENGTH` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión ψ: N(i), Cα(i), C(i), N(i+1). Se usan vecinos reales de la cadena, aunque no sean Q1. Una distribución multimodal también puede dar R bajo; no mide flexibilidad dinámica.

### 142. `LIGAND_BACKBONE_N_OMEGA`

Número de residuos Q1 del ligando (L) con torsión ω calculable.

- **Tipo:** `NUMBER(18,0)`. **Unidad:** ángulos válidos. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** COUNT(OMEGA_DEG) no NULL
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_N_OMEGA` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión ω: Cα(i), C(i), N(i+1), Cα(i+1). Se usan vecinos reales de la cadena, aunque no sean Q1. Es el enlace saliente hacia i+1, no el entrante.

### 143. `LIGAND_BACKBONE_OMEGA_MEAN_SIN`

Media del seno de los ángulos ω válidos del ligando (L). Componente de la representación circular.

- **Tipo:** `NUMBER(18,12)`. **Unidad:** adimensional [−1,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** media(sin(ω × π/180)); términos redondeados a 12 decimales
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **138 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_OMEGA_MEAN_SIN` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión ω: Cα(i), C(i), N(i+1), Cα(i+1). Se usan vecinos reales de la cadena, aunque no sean Q1. Es el enlace saliente hacia i+1, no el entrante. Usar junto con la otra componente; no es el seno/coseno de la media aritmética de ángulos.

### 144. `LIGAND_BACKBONE_OMEGA_MEAN_COS`

Media del coseno de los ángulos ω válidos del ligando (L). Componente de la representación circular.

- **Tipo:** `NUMBER(18,12)`. **Unidad:** adimensional [−1,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** media(cos(ω × π/180)); términos redondeados a 12 decimales
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **138 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_OMEGA_MEAN_COS` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión ω: Cα(i), C(i), N(i+1), Cα(i+1). Se usan vecinos reales de la cadena, aunque no sean Q1. Es el enlace saliente hacia i+1, no el entrante. Usar junto con la otra componente; no es el seno/coseno de la media aritmética de ángulos.

### 145. `LIGAND_BACKBONE_OMEGA_RESULTANT_LENGTH`

Longitud R del vector circular medio de ω del ligando (L): cerca de 1 indica ángulos concentrados; cerca de 0, cancelación de direcciones.

- **Tipo:** `NUMBER(18,12)`. **Unidad:** adimensional [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** min(1, sqrt(LIGAND_BACKBONE_OMEGA_MEAN_SIN² + LIGAND_BACKBONE_OMEGA_MEAN_COS²))
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **138 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_OMEGA_RESULTANT_LENGTH` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión ω: Cα(i), C(i), N(i+1), Cα(i+1). Se usan vecinos reales de la cadena, aunque no sean Q1. Es el enlace saliente hacia i+1, no el entrante. Una distribución multimodal también puede dar R bajo; no mide flexibilidad dinámica.

### 146. `LIGAND_BACKBONE_N_TAU_DEG`

Cantidad de mediciones válidas de ángulo τ del esqueleto N(i)–Cα(i)–C(i) del ligando (L).

- **Tipo:** `NUMBER(18,0)`. **Unidad:** mediciones válidas. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** COUNT(TAU_DEG) no NULL
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_N_TAU_DEG` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan.

### 147. `LIGAND_BACKBONE_TAU_DEG_MEAN`

Media de ángulo τ del esqueleto N(i)–Cα(i)–C(i) entre mediciones válidas del ligando (L).

- **Tipo:** `NUMBER(18,8)`. **Unidad:** grados. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** SUM(x_i)/n_valid; media lineal, no circular
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_TAU_DEG_MEAN` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan.

### 148. `LIGAND_BACKBONE_TAU_DEG_STD_POP`

Desviación estándar poblacional de ángulo τ del esqueleto N(i)–Cα(i)–C(i) del ligando (L); describe dispersión entre residuos.

- **Tipo:** `NUMBER(18,8)`. **Unidad:** grados. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** sqrt(SUM((x_i − media)²)/n_valid)
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_TAU_DEG_STD_POP` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan. Con una sola medición válida es 0. No divide por n−1 ni es error estándar experimental.

### 149. `LIGAND_BACKBONE_N_N_CA_LENGTH`

Cantidad de mediciones válidas de longitud N(i)–Cα(i) del ligando (L).

- **Tipo:** `NUMBER(18,0)`. **Unidad:** mediciones válidas. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** COUNT(N_CA_LENGTH) no NULL
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_N_N_CA_LENGTH` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan.

### 150. `LIGAND_BACKBONE_N_CA_LENGTH_MEAN`

Media de longitud N(i)–Cα(i) entre mediciones válidas del ligando (L).

- **Tipo:** `NUMBER(18,8)`. **Unidad:** Å. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** SUM(x_i)/n_valid; media lineal, no circular
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_N_CA_LENGTH_MEAN` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan.

### 151. `LIGAND_BACKBONE_N_CA_LENGTH_STD_POP`

Desviación estándar poblacional de longitud N(i)–Cα(i) del ligando (L); describe dispersión entre residuos.

- **Tipo:** `NUMBER(18,8)`. **Unidad:** Å. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** sqrt(SUM((x_i − media)²)/n_valid)
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_N_CA_LENGTH_STD_POP` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan. Con una sola medición válida es 0. No divide por n−1 ni es error estándar experimental.

### 152. `LIGAND_BACKBONE_N_CA_C_LENGTH`

Cantidad de mediciones válidas de longitud Cα(i)–C(i) del ligando (L).

- **Tipo:** `NUMBER(18,0)`. **Unidad:** mediciones válidas. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** COUNT(CA_C_LENGTH) no NULL
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_N_CA_C_LENGTH` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan.

### 153. `LIGAND_BACKBONE_CA_C_LENGTH_MEAN`

Media de longitud Cα(i)–C(i) entre mediciones válidas del ligando (L).

- **Tipo:** `NUMBER(18,8)`. **Unidad:** Å. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** SUM(x_i)/n_valid; media lineal, no circular
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_CA_C_LENGTH_MEAN` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan.

### 154. `LIGAND_BACKBONE_CA_C_LENGTH_STD_POP`

Desviación estándar poblacional de longitud Cα(i)–C(i) del ligando (L); describe dispersión entre residuos.

- **Tipo:** `NUMBER(18,8)`. **Unidad:** Å. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** sqrt(SUM((x_i − media)²)/n_valid)
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_CA_C_LENGTH_STD_POP` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan. Con una sola medición válida es 0. No divide por n−1 ni es error estándar experimental.

### 155. `LIGAND_BACKBONE_N_PEPTIDE_CN_LENGTH`

Cantidad de mediciones válidas de longitud del enlace peptídico saliente C(i)–N(i+1) del ligando (L).

- **Tipo:** `NUMBER(18,0)`. **Unidad:** mediciones válidas. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** COUNT(PEPTIDE_CN_LENGTH) no NULL
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_N_PEPTIDE_CN_LENGTH` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan. Se exige continuidad de cadena y C–N entre 0.8 y 1.8 Å; no se incluyen enlaces rechazados por esa regla.

### 156. `LIGAND_BACKBONE_PEPTIDE_CN_LENGTH_MEAN`

Media de longitud del enlace peptídico saliente C(i)–N(i+1) entre mediciones válidas del ligando (L).

- **Tipo:** `NUMBER(18,8)`. **Unidad:** Å. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** SUM(x_i)/n_valid; media lineal, no circular
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **137 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PEPTIDE_CN_LENGTH_MEAN` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan. Se exige continuidad de cadena y C–N entre 0.8 y 1.8 Å; no se incluyen enlaces rechazados por esa regla.

### 157. `LIGAND_BACKBONE_PEPTIDE_CN_LENGTH_STD_POP`

Desviación estándar poblacional de longitud del enlace peptídico saliente C(i)–N(i+1) del ligando (L); describe dispersión entre residuos.

- **Tipo:** `NUMBER(18,8)`. **Unidad:** Å. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** sqrt(SUM((x_i − media)²)/n_valid)
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **137 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PEPTIDE_CN_LENGTH_STD_POP` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan. Se exige continuidad de cadena y C–N entre 0.8 y 1.8 Å; no se incluyen enlaces rechazados por esa regla. Con una sola medición válida es 0. No divide por n−1 ni es error estándar experimental.

### 158. `LIGAND_BACKBONE_BACKBONE_STATUS`

Estado de disponibilidad de los cuatro ángulos en los residuos Q1 del ligando (L).

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Ausencias:** NULL si no existe participante asociado. NULL observados: **3 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_BACKBONE_STATUS` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Valores:** `complete`: Todos los residuos Q1 tienen φ, ψ, ω y τ calculables.; `partial_angles`: Falta al menos uno de esos ángulos en parte de los residuos Q1.; `no_valid_angles`: No hay valores válidos de φ, ψ, ω ni τ.; `empty_selection`: No hay residuos Q1 seleccionados.; `geometry_unavailable`: No hay geometría utilizable.
- **Valores observados no nulos:** `partial_angles`, `complete`, `geometry_unavailable`
- **Interpretación:** complete se refiere a φ, ψ, ω y τ; no es aprobación global de calidad experimental.

### 159. `LIGAND_BACKBONE_FRACTION_PHI_PSI_COMPLETE`

Fracción de residuos Q1 del ligando (L) con φ y ψ simultáneamente disponibles.

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** LIGAND_BACKBONE_N_PHI_PSI_COMPLETE / LIGAND_N_SELECTED
- **Ausencias:** NULL sin geometría/participante o si N_SELECTED=0. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_FRACTION_PHI_PSI_COMPLETE` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).

### 160. `LIGAND_BACKBONE_PHI_COVERAGE`

Fracción de residuos Q1 del ligando (L) con torsión φ calculable.

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** LIGAND_BACKBONE_N_PHI / LIGAND_N_SELECTED
- **Ausencias:** NULL sin geometría/participante o si N_SELECTED=0. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PHI_COVERAGE` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión φ: C(i−1), N(i), Cα(i), C(i). Se usan vecinos reales de la cadena, aunque no sean Q1.

### 161. `LIGAND_BACKBONE_PHI_CIRCULAR_MEAN_DEG`

Dirección media circular de la torsión φ del ligando (L), en grados.

- **Tipo:** `NUMBER(18,8)`. **Unidad:** grados. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** atan2(LIGAND_BACKBONE_PHI_MEAN_SIN, LIGAND_BACKBONE_PHI_MEAN_COS) × 180/π, solo si R>1e−8
- **Ausencias:** NULL si no hay ángulos válidos o R≤1e−8, porque la dirección media no está bien definida. NULL observados: **137 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PHI_CIRCULAR_MEAN_DEG` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Rango definido:** [−180,180]
- **Interpretación:** Torsión φ: C(i−1), N(i), Cα(i), C(i). Se usan vecinos reales de la cadena, aunque no sean Q1. ±180° representan la misma dirección; seno/coseno evitan ese salto al usar modelos clásicos.

### 162. `LIGAND_BACKBONE_PHI_CIRCULAR_VARIANCE`

Dispersión circular de φ del ligando (L); cero indica máxima concentración.

- **Tipo:** `NUMBER(19,12)`. **Unidad:** adimensional [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** 1 − LIGAND_BACKBONE_PHI_RESULTANT_LENGTH
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **137 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PHI_CIRCULAR_VARIANCE` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión φ: C(i−1), N(i), Cα(i), C(i). Se usan vecinos reales de la cadena, aunque no sean Q1. No es varianza en grados cuadrados ni mide movilidad de una trayectoria.

### 163. `LIGAND_BACKBONE_PSI_COVERAGE`

Fracción de residuos Q1 del ligando (L) con torsión ψ calculable.

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** LIGAND_BACKBONE_N_PSI / LIGAND_N_SELECTED
- **Ausencias:** NULL sin geometría/participante o si N_SELECTED=0. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PSI_COVERAGE` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión ψ: N(i), Cα(i), C(i), N(i+1). Se usan vecinos reales de la cadena, aunque no sean Q1.

### 164. `LIGAND_BACKBONE_PSI_CIRCULAR_MEAN_DEG`

Dirección media circular de la torsión ψ del ligando (L), en grados.

- **Tipo:** `NUMBER(18,8)`. **Unidad:** grados. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** atan2(LIGAND_BACKBONE_PSI_MEAN_SIN, LIGAND_BACKBONE_PSI_MEAN_COS) × 180/π, solo si R>1e−8
- **Ausencias:** NULL si no hay ángulos válidos o R≤1e−8, porque la dirección media no está bien definida. NULL observados: **137 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PSI_CIRCULAR_MEAN_DEG` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Rango definido:** [−180,180]
- **Interpretación:** Torsión ψ: N(i), Cα(i), C(i), N(i+1). Se usan vecinos reales de la cadena, aunque no sean Q1. ±180° representan la misma dirección; seno/coseno evitan ese salto al usar modelos clásicos.

### 165. `LIGAND_BACKBONE_PSI_CIRCULAR_VARIANCE`

Dispersión circular de ψ del ligando (L); cero indica máxima concentración.

- **Tipo:** `NUMBER(19,12)`. **Unidad:** adimensional [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** 1 − LIGAND_BACKBONE_PSI_RESULTANT_LENGTH
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **137 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PSI_CIRCULAR_VARIANCE` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión ψ: N(i), Cα(i), C(i), N(i+1). Se usan vecinos reales de la cadena, aunque no sean Q1. No es varianza en grados cuadrados ni mide movilidad de una trayectoria.

### 166. `LIGAND_BACKBONE_OMEGA_COVERAGE`

Fracción de residuos Q1 del ligando (L) con torsión ω calculable.

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** LIGAND_BACKBONE_N_OMEGA / LIGAND_N_SELECTED
- **Ausencias:** NULL sin geometría/participante o si N_SELECTED=0. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_OMEGA_COVERAGE` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión ω: Cα(i), C(i), N(i+1), Cα(i+1). Se usan vecinos reales de la cadena, aunque no sean Q1. Es el enlace saliente hacia i+1, no el entrante.

### 167. `LIGAND_BACKBONE_OMEGA_CIRCULAR_MEAN_DEG`

Dirección media circular de la torsión ω del ligando (L), en grados.

- **Tipo:** `NUMBER(18,8)`. **Unidad:** grados. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** atan2(LIGAND_BACKBONE_OMEGA_MEAN_SIN, LIGAND_BACKBONE_OMEGA_MEAN_COS) × 180/π, solo si R>1e−8
- **Ausencias:** NULL si no hay ángulos válidos o R≤1e−8, porque la dirección media no está bien definida. NULL observados: **138 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_OMEGA_CIRCULAR_MEAN_DEG` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Rango definido:** [−180,180]
- **Interpretación:** Torsión ω: Cα(i), C(i), N(i+1), Cα(i+1). Se usan vecinos reales de la cadena, aunque no sean Q1. Es el enlace saliente hacia i+1, no el entrante. ±180° representan la misma dirección; seno/coseno evitan ese salto al usar modelos clásicos.

### 168. `LIGAND_BACKBONE_OMEGA_CIRCULAR_VARIANCE`

Dispersión circular de ω del ligando (L); cero indica máxima concentración.

- **Tipo:** `NUMBER(19,12)`. **Unidad:** adimensional [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** 1 − LIGAND_BACKBONE_OMEGA_RESULTANT_LENGTH
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **138 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_OMEGA_CIRCULAR_VARIANCE` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión ω: Cα(i), C(i), N(i+1), Cα(i+1). Se usan vecinos reales de la cadena, aunque no sean Q1. Es el enlace saliente hacia i+1, no el entrante. No es varianza en grados cuadrados ni mide movilidad de una trayectoria.

### 169. `LIGAND_BACKBONE_TAU_DEG_COVERAGE`

Fracción de residuos Q1 del ligando (L) con ángulo τ del esqueleto N(i)–Cα(i)–C(i) calculable.

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** LIGAND_BACKBONE_N_TAU_DEG / LIGAND_N_SELECTED
- **Ausencias:** NULL sin geometría/participante o si N_SELECTED=0. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_TAU_DEG_COVERAGE` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan.

### 170. `LIGAND_BACKBONE_N_CA_LENGTH_COVERAGE`

Fracción de residuos Q1 del ligando (L) con longitud N(i)–Cα(i) calculable.

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** LIGAND_BACKBONE_N_N_CA_LENGTH / LIGAND_N_SELECTED
- **Ausencias:** NULL sin geometría/participante o si N_SELECTED=0. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_N_CA_LENGTH_COVERAGE` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan.

### 171. `LIGAND_BACKBONE_CA_C_LENGTH_COVERAGE`

Fracción de residuos Q1 del ligando (L) con longitud Cα(i)–C(i) calculable.

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** LIGAND_BACKBONE_N_CA_C_LENGTH / LIGAND_N_SELECTED
- **Ausencias:** NULL sin geometría/participante o si N_SELECTED=0. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_CA_C_LENGTH_COVERAGE` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan.

### 172. `LIGAND_BACKBONE_PEPTIDE_CN_LENGTH_COVERAGE`

Fracción de residuos Q1 del ligando (L) con longitud del enlace peptídico saliente C(i)–N(i+1) calculable.

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** LIGAND_BACKBONE_N_PEPTIDE_CN_LENGTH / LIGAND_N_SELECTED
- **Ausencias:** NULL sin geometría/participante o si N_SELECTED=0. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PEPTIDE_CN_LENGTH_COVERAGE` · participante L.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan. Se exige continuidad de cadena y C–N entre 0.8 y 1.8 Å; no se incluyen enlaces rechazados por esa regla.


<a id="receptor_chemistry"></a>
## Receptor: selección y composición química

### 173. `RECEPTOR_N_SELECTED`

Número de residuos Q1 del receptor (R). Copia del conteo de selección geométrica.

- **Tipo:** `NUMBER(38,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** N_SELECTED_Q1_RECEPTOR
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.N_SELECTED` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [geometry_core.py](<../scripts/geometry_core.py>).
- **Equivalencias de conteo:** `N_SELECTED_Q1_RECEPTOR`, `RECEPTOR_CHEM_N_SELECTED`, `RECEPTOR_BACKBONE_N_MEASURED_ROWS`

### 174. `RECEPTOR_CHEM_FEATURE_VERSION`

Versión de las reglas químicas aplicadas al receptor (R).

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `provenance`.
- **Uso:** Información de procedencia/configuración; no incluir por defecto en X.
- **Ausencias:** NULL si no existe participante asociado. NULL observados: **3 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FEATURE_VERSION` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Valores:** `chemistry_v1`: Mapa de 20 aminoácidos y categorías definido en el proyecto.

### 175. `RECEPTOR_CHEM_FEATURE_BASIS`

Base estructural de las características químicas del receptor (R).

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `provenance`.
- **Uso:** Información de procedencia/configuración; no incluir por defecto en X.
- **Ausencias:** NULL si no existe participante asociado. NULL observados: **3 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FEATURE_BASIS` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Valores:** `observed_structure_q1`: Residuos observados seleccionados por Q1, sin construir mutantes.

### 176. `RECEPTOR_CHEM_CHEMISTRY_STATUS`

Estado de cobertura de las propiedades químicas del receptor (R).

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Ausencias:** NULL si no hay participante asociado; geometry_unavailable si existe pero su geometría falló. NULL observados: **3 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_CHEMISTRY_STATUS` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Valores:** `complete`: Todos los residuos Q1 tienen propiedades soportadas.; `partial_coverage`: Solo parte de los residuos Q1 tiene propiedades soportadas.; `no_supported_residues`: Hay selección Q1, pero ningún residuo soportado.; `empty_selection`: El filtro estricto Q1 no seleccionó residuos.; `geometry_unavailable`: La geometría no pudo calcularse.
- **Valores observados no nulos:** `complete`, `partial_coverage`, `geometry_unavailable`

### 177. `RECEPTOR_CHEM_N_SELECTED`

Cantidad de todos los residuos seleccionados por Q1 en el receptor (R).

- **Tipo:** `NUMBER(18,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_SELECTED` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Equivalencias de conteo:** `N_SELECTED_Q1_RECEPTOR`, `RECEPTOR_N_SELECTED`, `RECEPTOR_BACKBONE_N_MEASURED_ROWS`

### 178. `RECEPTOR_CHEM_N_SUPPORTED`

Cantidad de residuos Q1 canónicos cuyo nombre/código coincide con el mapa de los 20 aminoácidos en el receptor (R).

- **Tipo:** `NUMBER(18,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_SUPPORTED` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).

### 179. `RECEPTOR_CHEM_N_NONSTANDARD`

Cantidad de residuos Q1 marcados como no estándar por su nombre estructural en el receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_NONSTANDARD` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).

### 180. `RECEPTOR_CHEM_N_UNSUPPORTED`

Cantidad de residuos Q1 sin propiedades asignadas, incluidos los no estándar en el receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** RECEPTOR_CHEM_N_SELECTED − RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_UNSUPPORTED` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).

### 181. `RECEPTOR_CHEM_MEAN_KD_HYDROPATHY`

Hidropatía media Kyte–Doolittle de los residuos soportados Q1 del receptor (R). Valores mayores indican mayor hidropatía en esta escala.

- **Tipo:** `NUMBER(12,6)`. **Unidad:** escala adimensional Kyte–Doolittle. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** SUM(hidropatía de cada residuo soportado) / RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_MEAN_KD_HYDROPATHY` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Rango definido:** [−4.5, 4.5] cuando hay valores
- **Interpretación:** KD aquí significa Kyte–Doolittle; NO es el Kd experimental ni una fuga directa de la etiqueta. No es energía de unión. Media almacenada con 6 decimales.

### 182. `RECEPTOR_CHEM_AA_ENTROPY_BITS`

Diversidad de composición de los 20 aminoácidos soportados Q1 del receptor (R).

- **Tipo:** `NUMBER(32,12)`. **Unidad:** bits. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** −Σ p_a log2(p_a), p_a=N_AA_a/N_SUPPORTED; sumar solo p_a>0
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_AA_ENTROPY_BITS` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Rango definido:** [0, log2(20)] ≈ [0, 4.322]
- **Interpretación:** Es entropía de Shannon de la composición, no entropía termodinámica ni flexibilidad. Cada término se redondea a 12 decimales.

### 183. `RECEPTOR_CHEM_N_AA_A`

Cantidad de alanina (A, ALA) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos ALA con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_A` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 184. `RECEPTOR_CHEM_N_AA_C`

Cantidad de cisteína (C, CYS) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos CYS con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_C` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 185. `RECEPTOR_CHEM_N_AA_D`

Cantidad de aspartato / ácido aspártico (D, ASP) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos ASP con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_D` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 186. `RECEPTOR_CHEM_N_AA_E`

Cantidad de glutamato / ácido glutámico (E, GLU) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos GLU con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_E` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 187. `RECEPTOR_CHEM_N_AA_F`

Cantidad de fenilalanina (F, PHE) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos PHE con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_F` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 188. `RECEPTOR_CHEM_N_AA_G`

Cantidad de glicina (G, GLY) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos GLY con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_G` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 189. `RECEPTOR_CHEM_N_AA_H`

Cantidad de histidina (H, HIS) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos HIS con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_H` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 190. `RECEPTOR_CHEM_N_AA_I`

Cantidad de isoleucina (I, ILE) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos ILE con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_I` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 191. `RECEPTOR_CHEM_N_AA_K`

Cantidad de lisina (K, LYS) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos LYS con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_K` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 192. `RECEPTOR_CHEM_N_AA_L`

Cantidad de leucina (L, LEU) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos LEU con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_L` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 193. `RECEPTOR_CHEM_N_AA_M`

Cantidad de metionina (M, MET) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos MET con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_M` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 194. `RECEPTOR_CHEM_N_AA_N`

Cantidad de asparagina (N, ASN) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos ASN con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_N` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 195. `RECEPTOR_CHEM_N_AA_P`

Cantidad de prolina (P, PRO) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos PRO con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_P` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 196. `RECEPTOR_CHEM_N_AA_Q`

Cantidad de glutamina (Q, GLN) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos GLN con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_Q` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 197. `RECEPTOR_CHEM_N_AA_R`

Cantidad de arginina (R, ARG) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos ARG con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_R` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 198. `RECEPTOR_CHEM_N_AA_S`

Cantidad de serina (S, SER) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos SER con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_S` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 199. `RECEPTOR_CHEM_N_AA_T`

Cantidad de treonina (T, THR) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos THR con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_T` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 200. `RECEPTOR_CHEM_N_AA_V`

Cantidad de valina (V, VAL) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos VAL con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_V` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 201. `RECEPTOR_CHEM_N_AA_W`

Cantidad de triptófano (W, TRP) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos TRP con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_W` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 202. `RECEPTOR_CHEM_N_AA_Y`

Cantidad de tirosina (Y, TYR) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Contar residuos canónicos TYR con SELECTED_Q1=true
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AA_Y` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** No se incluyen residuos modificados por equivalencia nominal.

### 203. `RECEPTOR_CHEM_N_NONPOLAR`

Cantidad de aminoácidos no polares (G,A,V,L,I,M,P,F,W) soportados Q1 del receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Suma de los conteos N_AA de G,A,V,L,I,M,P,F,W
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_NONPOLAR` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).

### 204. `RECEPTOR_CHEM_N_POLAR_UNCHARGED`

Cantidad de aminoácidos polares sin carga, según la clasificación convencional (S,T,C,N,Q,Y) soportados Q1 del receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Suma de los conteos N_AA de S,T,C,N,Q,Y
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_POLAR_UNCHARGED` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** Clasificación por identidad; no representa cargas medidas ni estados de protonación.

### 205. `RECEPTOR_CHEM_N_ACIDIC`

Cantidad de aminoácidos ácidos (D,E) soportados Q1 del receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Suma de los conteos N_AA de D,E
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_ACIDIC` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** Clasificación por identidad; no representa cargas medidas ni estados de protonación.

### 206. `RECEPTOR_CHEM_N_BASIC`

Cantidad de aminoácidos básicos (K,R,H) soportados Q1 del receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Suma de los conteos N_AA de K,R,H
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_BASIC` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** Clasificación por identidad; no representa cargas medidas ni estados de protonación. Incluye H; no se asume que toda histidina esté protonada.

### 207. `RECEPTOR_CHEM_N_AROMATIC_RING`

Cantidad de aminoácidos con anillo aromático (F,W,Y,H) soportados Q1 del receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Suma de los conteos N_AA de F,W,Y,H
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_AROMATIC_RING` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** Incluye H. No cuenta interacciones π–π. Grupo solapado con clases de polaridad; no sumar todos los grupos como una partición.

### 208. `RECEPTOR_CHEM_N_SULFUR_CONTAINING`

Cantidad de aminoácidos con azufre (C,M) soportados Q1 del receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Suma de los conteos N_AA de C,M
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_SULFUR_CONTAINING` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** Cuenta residuos C y M, no átomos de azufre ni enlaces disulfuro. Grupo solapado con clases de polaridad; no sumar todos los grupos como una partición.

### 209. `RECEPTOR_CHEM_N_ALIPHATIC_AVIL`

Cantidad de aminoácidos del subconjunto alifático AVIL (A,V,I,L) soportados Q1 del receptor (R).

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** Suma de los conteos N_AA de A,V,I,L
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_N_ALIPHATIC_AVIL` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** Grupo solapado con clases de polaridad; no sumar todos los grupos como una partición.

### 210. `RECEPTOR_CHEM_PROPERTY_COVERAGE`

Fracción de los residuos Q1 del receptor (R) para los que hay propiedades químicas soportadas.

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** RECEPTOR_CHEM_N_SUPPORTED / RECEPTOR_CHEM_N_SELECTED
- **Ausencias:** NULL si falta geometría/participante o N_SELECTED=0. Cero significa selección existente sin residuos soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_PROPERTY_COVERAGE` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).

### 211. `RECEPTOR_CHEM_FRACTION_AA_A`

Fracción de alanina (A, ALA) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** RECEPTOR_CHEM_N_AA_A / RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_A` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 212. `RECEPTOR_CHEM_FRACTION_AA_C`

Fracción de cisteína (C, CYS) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** RECEPTOR_CHEM_N_AA_C / RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_C` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 213. `RECEPTOR_CHEM_FRACTION_AA_D`

Fracción de aspartato / ácido aspártico (D, ASP) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** RECEPTOR_CHEM_N_AA_D / RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_D` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 214. `RECEPTOR_CHEM_FRACTION_AA_E`

Fracción de glutamato / ácido glutámico (E, GLU) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** RECEPTOR_CHEM_N_AA_E / RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_E` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 215. `RECEPTOR_CHEM_FRACTION_AA_F`

Fracción de fenilalanina (F, PHE) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** RECEPTOR_CHEM_N_AA_F / RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_F` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 216. `RECEPTOR_CHEM_FRACTION_AA_G`

Fracción de glicina (G, GLY) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** RECEPTOR_CHEM_N_AA_G / RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_G` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 217. `RECEPTOR_CHEM_FRACTION_AA_H`

Fracción de histidina (H, HIS) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** RECEPTOR_CHEM_N_AA_H / RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_H` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 218. `RECEPTOR_CHEM_FRACTION_AA_I`

Fracción de isoleucina (I, ILE) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** RECEPTOR_CHEM_N_AA_I / RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_I` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 219. `RECEPTOR_CHEM_FRACTION_AA_K`

Fracción de lisina (K, LYS) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** RECEPTOR_CHEM_N_AA_K / RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_K` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 220. `RECEPTOR_CHEM_FRACTION_AA_L`

Fracción de leucina (L, LEU) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** RECEPTOR_CHEM_N_AA_L / RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_L` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 221. `RECEPTOR_CHEM_FRACTION_AA_M`

Fracción de metionina (M, MET) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** RECEPTOR_CHEM_N_AA_M / RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_M` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 222. `RECEPTOR_CHEM_FRACTION_AA_N`

Fracción de asparagina (N, ASN) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** RECEPTOR_CHEM_N_AA_N / RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_N` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 223. `RECEPTOR_CHEM_FRACTION_AA_P`

Fracción de prolina (P, PRO) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** RECEPTOR_CHEM_N_AA_P / RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_P` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 224. `RECEPTOR_CHEM_FRACTION_AA_Q`

Fracción de glutamina (Q, GLN) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** RECEPTOR_CHEM_N_AA_Q / RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_Q` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 225. `RECEPTOR_CHEM_FRACTION_AA_R`

Fracción de arginina (R, ARG) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** RECEPTOR_CHEM_N_AA_R / RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_R` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 226. `RECEPTOR_CHEM_FRACTION_AA_S`

Fracción de serina (S, SER) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** RECEPTOR_CHEM_N_AA_S / RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_S` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 227. `RECEPTOR_CHEM_FRACTION_AA_T`

Fracción de treonina (T, THR) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** RECEPTOR_CHEM_N_AA_T / RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_T` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 228. `RECEPTOR_CHEM_FRACTION_AA_V`

Fracción de valina (V, VAL) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** RECEPTOR_CHEM_N_AA_V / RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_V` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 229. `RECEPTOR_CHEM_FRACTION_AA_W`

Fracción de triptófano (W, TRP) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** RECEPTOR_CHEM_N_AA_W / RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_W` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 230. `RECEPTOR_CHEM_FRACTION_AA_Y`

Fracción de tirosina (Y, TYR) entre los residuos soportados Q1 del receptor (R).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** RECEPTOR_CHEM_N_AA_Y / RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; 0 significa que este aminoácido no aparece entre los soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AA_Y` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** El denominador es N_SUPPORTED, no todos los residuos seleccionados.

### 231. `RECEPTOR_CHEM_FRACTION_NONPOLAR`

Fracción de aminoácidos no polares (G,A,V,L,I,M,P,F,W) soportados Q1 del receptor (R).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** RECEPTOR_CHEM_N_NONPOLAR / RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; el denominador son los residuos soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_NONPOLAR` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).

### 232. `RECEPTOR_CHEM_FRACTION_POLAR_UNCHARGED`

Fracción de aminoácidos polares sin carga, según la clasificación convencional (S,T,C,N,Q,Y) soportados Q1 del receptor (R).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** RECEPTOR_CHEM_N_POLAR_UNCHARGED / RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; el denominador son los residuos soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_POLAR_UNCHARGED` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** Clasificación por identidad; no representa cargas medidas ni estados de protonación.

### 233. `RECEPTOR_CHEM_FRACTION_ACIDIC`

Fracción de aminoácidos ácidos (D,E) soportados Q1 del receptor (R).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** RECEPTOR_CHEM_N_ACIDIC / RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; el denominador son los residuos soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_ACIDIC` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** Clasificación por identidad; no representa cargas medidas ni estados de protonación.

### 234. `RECEPTOR_CHEM_FRACTION_BASIC`

Fracción de aminoácidos básicos (K,R,H) soportados Q1 del receptor (R).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** RECEPTOR_CHEM_N_BASIC / RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; el denominador son los residuos soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_BASIC` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** Clasificación por identidad; no representa cargas medidas ni estados de protonación. Incluye H; no se asume que toda histidina esté protonada.

### 235. `RECEPTOR_CHEM_FRACTION_AROMATIC_RING`

Fracción de aminoácidos con anillo aromático (F,W,Y,H) soportados Q1 del receptor (R).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** RECEPTOR_CHEM_N_AROMATIC_RING / RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; el denominador son los residuos soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_AROMATIC_RING` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** Incluye H. No cuenta interacciones π–π. Grupo solapado con clases de polaridad; no sumar todos los grupos como una partición.

### 236. `RECEPTOR_CHEM_FRACTION_SULFUR_CONTAINING`

Fracción de aminoácidos con azufre (C,M) soportados Q1 del receptor (R).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** RECEPTOR_CHEM_N_SULFUR_CONTAINING / RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; el denominador son los residuos soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_SULFUR_CONTAINING` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** Cuenta residuos C y M, no átomos de azufre ni enlaces disulfuro. Grupo solapado con clases de polaridad; no sumar todos los grupos como una partición.

### 237. `RECEPTOR_CHEM_FRACTION_ALIPHATIC_AVIL`

Fracción de aminoácidos del subconjunto alifático AVIL (A,V,I,L) soportados Q1 del receptor (R).

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** RECEPTOR_CHEM_N_ALIPHATIC_AVIL / RECEPTOR_CHEM_N_SUPPORTED
- **Ausencias:** NULL si falta geometría/participante o N_SUPPORTED=0; el denominador son los residuos soportados. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.CHEM_FRACTION_ALIPHATIC_AVIL` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [silver_interface_chemistry.sql](<../dbt/models/silver/silver_interface_chemistry.sql>), [amino_acid_properties.sql](<../dbt/macros/amino_acid_properties.sql>).
- **Interpretación:** Grupo solapado con clases de polaridad; no sumar todos los grupos como una partición.


<a id="receptor_backbone"></a>
## Receptor: geometría interna

### 238. `RECEPTOR_BACKBONE_FEATURE_VERSION`

Versión del cálculo y resumen del esqueleto peptídico del receptor (R).

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `provenance`.
- **Uso:** Información de procedencia/configuración; no incluir por defecto en X.
- **Ausencias:** NULL si no existe participante asociado. NULL observados: **3 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_FEATURE_VERSION` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Valores:** `backbone_v1`: φ, ψ, ω saliente, τ y tres longitudes.

### 239. `RECEPTOR_BACKBONE_FEATURE_BASIS`

Base del resumen geométrico interno del receptor (R).

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `provenance`.
- **Uso:** Información de procedencia/configuración; no incluir por defecto en X.
- **Ausencias:** NULL si no existe participante asociado. NULL observados: **3 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_FEATURE_BASIS` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Valores:** `observed_structure_q1`: Residuos Q1 de la estructura observada; vecinos pueden estar fuera de Q1.

### 240. `RECEPTOR_BACKBONE_N_MEASURED_ROWS`

Cantidad de filas de mediciones individuales del receptor (R); incluye residuos Q1 con ángulos ausentes.

- **Tipo:** `NUMBER(18,0)`. **Unidad:** residuos. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** RECEPTOR_N_SELECTED
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_N_MEASURED_ROWS` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Equivalencias de conteo:** `N_SELECTED_Q1_RECEPTOR`, `RECEPTOR_N_SELECTED`, `RECEPTOR_CHEM_N_SELECTED`
- **Interpretación:** No cuenta únicamente residuos con todos los ángulos válidos.

### 241. `RECEPTOR_BACKBONE_N_PHI_PSI_COMPLETE`

Cantidad de residuos Q1 del receptor (R) con φ y ψ simultáneamente disponibles.

- **Tipo:** `NUMBER(13,0)`. **Unidad:** residuos. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** COUNT_IF(PHI_DEG IS NOT NULL AND PSI_DEG IS NOT NULL)
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_N_PHI_PSI_COMPLETE` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).

### 242. `RECEPTOR_BACKBONE_N_PHI`

Número de residuos Q1 del receptor (R) con torsión φ calculable.

- **Tipo:** `NUMBER(18,0)`. **Unidad:** ángulos válidos. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** COUNT(PHI_DEG) no NULL
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_N_PHI` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión φ: C(i−1), N(i), Cα(i), C(i). Se usan vecinos reales de la cadena, aunque no sean Q1.

### 243. `RECEPTOR_BACKBONE_PHI_MEAN_SIN`

Media del seno de los ángulos φ válidos del receptor (R). Componente de la representación circular.

- **Tipo:** `NUMBER(18,12)`. **Unidad:** adimensional [−1,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** media(sin(φ × π/180)); términos redondeados a 12 decimales
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **148 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PHI_MEAN_SIN` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión φ: C(i−1), N(i), Cα(i), C(i). Se usan vecinos reales de la cadena, aunque no sean Q1. Usar junto con la otra componente; no es el seno/coseno de la media aritmética de ángulos.

### 244. `RECEPTOR_BACKBONE_PHI_MEAN_COS`

Media del coseno de los ángulos φ válidos del receptor (R). Componente de la representación circular.

- **Tipo:** `NUMBER(18,12)`. **Unidad:** adimensional [−1,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** media(cos(φ × π/180)); términos redondeados a 12 decimales
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **148 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PHI_MEAN_COS` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión φ: C(i−1), N(i), Cα(i), C(i). Se usan vecinos reales de la cadena, aunque no sean Q1. Usar junto con la otra componente; no es el seno/coseno de la media aritmética de ángulos.

### 245. `RECEPTOR_BACKBONE_PHI_RESULTANT_LENGTH`

Longitud R del vector circular medio de φ del receptor (R): cerca de 1 indica ángulos concentrados; cerca de 0, cancelación de direcciones.

- **Tipo:** `NUMBER(18,12)`. **Unidad:** adimensional [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** min(1, sqrt(RECEPTOR_BACKBONE_PHI_MEAN_SIN² + RECEPTOR_BACKBONE_PHI_MEAN_COS²))
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **148 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PHI_RESULTANT_LENGTH` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión φ: C(i−1), N(i), Cα(i), C(i). Se usan vecinos reales de la cadena, aunque no sean Q1. Una distribución multimodal también puede dar R bajo; no mide flexibilidad dinámica.

### 246. `RECEPTOR_BACKBONE_N_PSI`

Número de residuos Q1 del receptor (R) con torsión ψ calculable.

- **Tipo:** `NUMBER(18,0)`. **Unidad:** ángulos válidos. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** COUNT(PSI_DEG) no NULL
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_N_PSI` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión ψ: N(i), Cα(i), C(i), N(i+1). Se usan vecinos reales de la cadena, aunque no sean Q1.

### 247. `RECEPTOR_BACKBONE_PSI_MEAN_SIN`

Media del seno de los ángulos ψ válidos del receptor (R). Componente de la representación circular.

- **Tipo:** `NUMBER(18,12)`. **Unidad:** adimensional [−1,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** media(sin(ψ × π/180)); términos redondeados a 12 decimales
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **147 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PSI_MEAN_SIN` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión ψ: N(i), Cα(i), C(i), N(i+1). Se usan vecinos reales de la cadena, aunque no sean Q1. Usar junto con la otra componente; no es el seno/coseno de la media aritmética de ángulos.

### 248. `RECEPTOR_BACKBONE_PSI_MEAN_COS`

Media del coseno de los ángulos ψ válidos del receptor (R). Componente de la representación circular.

- **Tipo:** `NUMBER(18,12)`. **Unidad:** adimensional [−1,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** media(cos(ψ × π/180)); términos redondeados a 12 decimales
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **147 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PSI_MEAN_COS` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión ψ: N(i), Cα(i), C(i), N(i+1). Se usan vecinos reales de la cadena, aunque no sean Q1. Usar junto con la otra componente; no es el seno/coseno de la media aritmética de ángulos.

### 249. `RECEPTOR_BACKBONE_PSI_RESULTANT_LENGTH`

Longitud R del vector circular medio de ψ del receptor (R): cerca de 1 indica ángulos concentrados; cerca de 0, cancelación de direcciones.

- **Tipo:** `NUMBER(18,12)`. **Unidad:** adimensional [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** min(1, sqrt(RECEPTOR_BACKBONE_PSI_MEAN_SIN² + RECEPTOR_BACKBONE_PSI_MEAN_COS²))
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **147 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PSI_RESULTANT_LENGTH` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión ψ: N(i), Cα(i), C(i), N(i+1). Se usan vecinos reales de la cadena, aunque no sean Q1. Una distribución multimodal también puede dar R bajo; no mide flexibilidad dinámica.

### 250. `RECEPTOR_BACKBONE_N_OMEGA`

Número de residuos Q1 del receptor (R) con torsión ω calculable.

- **Tipo:** `NUMBER(18,0)`. **Unidad:** ángulos válidos. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** COUNT(OMEGA_DEG) no NULL
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_N_OMEGA` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión ω: Cα(i), C(i), N(i+1), Cα(i+1). Se usan vecinos reales de la cadena, aunque no sean Q1. Es el enlace saliente hacia i+1, no el entrante.

### 251. `RECEPTOR_BACKBONE_OMEGA_MEAN_SIN`

Media del seno de los ángulos ω válidos del receptor (R). Componente de la representación circular.

- **Tipo:** `NUMBER(18,12)`. **Unidad:** adimensional [−1,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** media(sin(ω × π/180)); términos redondeados a 12 decimales
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **147 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_OMEGA_MEAN_SIN` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión ω: Cα(i), C(i), N(i+1), Cα(i+1). Se usan vecinos reales de la cadena, aunque no sean Q1. Es el enlace saliente hacia i+1, no el entrante. Usar junto con la otra componente; no es el seno/coseno de la media aritmética de ángulos.

### 252. `RECEPTOR_BACKBONE_OMEGA_MEAN_COS`

Media del coseno de los ángulos ω válidos del receptor (R). Componente de la representación circular.

- **Tipo:** `NUMBER(18,12)`. **Unidad:** adimensional [−1,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** media(cos(ω × π/180)); términos redondeados a 12 decimales
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **147 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_OMEGA_MEAN_COS` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión ω: Cα(i), C(i), N(i+1), Cα(i+1). Se usan vecinos reales de la cadena, aunque no sean Q1. Es el enlace saliente hacia i+1, no el entrante. Usar junto con la otra componente; no es el seno/coseno de la media aritmética de ángulos.

### 253. `RECEPTOR_BACKBONE_OMEGA_RESULTANT_LENGTH`

Longitud R del vector circular medio de ω del receptor (R): cerca de 1 indica ángulos concentrados; cerca de 0, cancelación de direcciones.

- **Tipo:** `NUMBER(18,12)`. **Unidad:** adimensional [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** min(1, sqrt(RECEPTOR_BACKBONE_OMEGA_MEAN_SIN² + RECEPTOR_BACKBONE_OMEGA_MEAN_COS²))
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **147 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_OMEGA_RESULTANT_LENGTH` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión ω: Cα(i), C(i), N(i+1), Cα(i+1). Se usan vecinos reales de la cadena, aunque no sean Q1. Es el enlace saliente hacia i+1, no el entrante. Una distribución multimodal también puede dar R bajo; no mide flexibilidad dinámica.

### 254. `RECEPTOR_BACKBONE_N_TAU_DEG`

Cantidad de mediciones válidas de ángulo τ del esqueleto N(i)–Cα(i)–C(i) del receptor (R).

- **Tipo:** `NUMBER(18,0)`. **Unidad:** mediciones válidas. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** COUNT(TAU_DEG) no NULL
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_N_TAU_DEG` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan.

### 255. `RECEPTOR_BACKBONE_TAU_DEG_MEAN`

Media de ángulo τ del esqueleto N(i)–Cα(i)–C(i) entre mediciones válidas del receptor (R).

- **Tipo:** `NUMBER(18,8)`. **Unidad:** grados. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** SUM(x_i)/n_valid; media lineal, no circular
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_TAU_DEG_MEAN` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan.

### 256. `RECEPTOR_BACKBONE_TAU_DEG_STD_POP`

Desviación estándar poblacional de ángulo τ del esqueleto N(i)–Cα(i)–C(i) del receptor (R); describe dispersión entre residuos.

- **Tipo:** `NUMBER(18,8)`. **Unidad:** grados. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** sqrt(SUM((x_i − media)²)/n_valid)
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_TAU_DEG_STD_POP` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan. Con una sola medición válida es 0. No divide por n−1 ni es error estándar experimental.

### 257. `RECEPTOR_BACKBONE_N_N_CA_LENGTH`

Cantidad de mediciones válidas de longitud N(i)–Cα(i) del receptor (R).

- **Tipo:** `NUMBER(18,0)`. **Unidad:** mediciones válidas. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** COUNT(N_CA_LENGTH) no NULL
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_N_N_CA_LENGTH` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan.

### 258. `RECEPTOR_BACKBONE_N_CA_LENGTH_MEAN`

Media de longitud N(i)–Cα(i) entre mediciones válidas del receptor (R).

- **Tipo:** `NUMBER(18,8)`. **Unidad:** Å. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** SUM(x_i)/n_valid; media lineal, no circular
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_N_CA_LENGTH_MEAN` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan.

### 259. `RECEPTOR_BACKBONE_N_CA_LENGTH_STD_POP`

Desviación estándar poblacional de longitud N(i)–Cα(i) del receptor (R); describe dispersión entre residuos.

- **Tipo:** `NUMBER(18,8)`. **Unidad:** Å. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** sqrt(SUM((x_i − media)²)/n_valid)
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_N_CA_LENGTH_STD_POP` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan. Con una sola medición válida es 0. No divide por n−1 ni es error estándar experimental.

### 260. `RECEPTOR_BACKBONE_N_CA_C_LENGTH`

Cantidad de mediciones válidas de longitud Cα(i)–C(i) del receptor (R).

- **Tipo:** `NUMBER(18,0)`. **Unidad:** mediciones válidas. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** COUNT(CA_C_LENGTH) no NULL
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_N_CA_C_LENGTH` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan.

### 261. `RECEPTOR_BACKBONE_CA_C_LENGTH_MEAN`

Media de longitud Cα(i)–C(i) entre mediciones válidas del receptor (R).

- **Tipo:** `NUMBER(18,8)`. **Unidad:** Å. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** SUM(x_i)/n_valid; media lineal, no circular
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_CA_C_LENGTH_MEAN` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan.

### 262. `RECEPTOR_BACKBONE_CA_C_LENGTH_STD_POP`

Desviación estándar poblacional de longitud Cα(i)–C(i) del receptor (R); describe dispersión entre residuos.

- **Tipo:** `NUMBER(18,8)`. **Unidad:** Å. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** sqrt(SUM((x_i − media)²)/n_valid)
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_CA_C_LENGTH_STD_POP` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan. Con una sola medición válida es 0. No divide por n−1 ni es error estándar experimental.

### 263. `RECEPTOR_BACKBONE_N_PEPTIDE_CN_LENGTH`

Cantidad de mediciones válidas de longitud del enlace peptídico saliente C(i)–N(i+1) del receptor (R).

- **Tipo:** `NUMBER(18,0)`. **Unidad:** mediciones válidas. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** COUNT(PEPTIDE_CN_LENGTH) no NULL
- **Ausencias:** NULL si falta el vínculo estructural o la geometría no es utilizable; 0 significa que se calculó el conteo y no hubo elementos. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_N_PEPTIDE_CN_LENGTH` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan. Se exige continuidad de cadena y C–N entre 0.8 y 1.8 Å; no se incluyen enlaces rechazados por esa regla.

### 264. `RECEPTOR_BACKBONE_PEPTIDE_CN_LENGTH_MEAN`

Media de longitud del enlace peptídico saliente C(i)–N(i+1) entre mediciones válidas del receptor (R).

- **Tipo:** `NUMBER(18,8)`. **Unidad:** Å. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** SUM(x_i)/n_valid; media lineal, no circular
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **147 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PEPTIDE_CN_LENGTH_MEAN` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan. Se exige continuidad de cadena y C–N entre 0.8 y 1.8 Å; no se incluyen enlaces rechazados por esa regla.

### 265. `RECEPTOR_BACKBONE_PEPTIDE_CN_LENGTH_STD_POP`

Desviación estándar poblacional de longitud del enlace peptídico saliente C(i)–N(i+1) del receptor (R); describe dispersión entre residuos.

- **Tipo:** `NUMBER(18,8)`. **Unidad:** Å. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** sqrt(SUM((x_i − media)²)/n_valid)
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **147 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PEPTIDE_CN_LENGTH_STD_POP` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan. Se exige continuidad de cadena y C–N entre 0.8 y 1.8 Å; no se incluyen enlaces rechazados por esa regla. Con una sola medición válida es 0. No divide por n−1 ni es error estándar experimental.

### 266. `RECEPTOR_BACKBONE_BACKBONE_STATUS`

Estado de disponibilidad de los cuatro ángulos en los residuos Q1 del receptor (R).

- **Tipo:** `TEXT`. **Unidad:** No aplica. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Ausencias:** NULL si no existe participante asociado. NULL observados: **3 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_BACKBONE_STATUS` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Valores:** `complete`: Todos los residuos Q1 tienen φ, ψ, ω y τ calculables.; `partial_angles`: Falta al menos uno de esos ángulos en parte de los residuos Q1.; `no_valid_angles`: No hay valores válidos de φ, ψ, ω ni τ.; `empty_selection`: No hay residuos Q1 seleccionados.; `geometry_unavailable`: No hay geometría utilizable.
- **Valores observados no nulos:** `complete`, `partial_angles`, `geometry_unavailable`
- **Interpretación:** complete se refiere a φ, ψ, ω y τ; no es aprobación global de calidad experimental.

### 267. `RECEPTOR_BACKBONE_FRACTION_PHI_PSI_COMPLETE`

Fracción de residuos Q1 del receptor (R) con φ y ψ simultáneamente disponibles.

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** RECEPTOR_BACKBONE_N_PHI_PSI_COMPLETE / RECEPTOR_N_SELECTED
- **Ausencias:** NULL sin geometría/participante o si N_SELECTED=0. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_FRACTION_PHI_PSI_COMPLETE` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).

### 268. `RECEPTOR_BACKBONE_PHI_COVERAGE`

Fracción de residuos Q1 del receptor (R) con torsión φ calculable.

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** RECEPTOR_BACKBONE_N_PHI / RECEPTOR_N_SELECTED
- **Ausencias:** NULL sin geometría/participante o si N_SELECTED=0. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PHI_COVERAGE` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión φ: C(i−1), N(i), Cα(i), C(i). Se usan vecinos reales de la cadena, aunque no sean Q1.

### 269. `RECEPTOR_BACKBONE_PHI_CIRCULAR_MEAN_DEG`

Dirección media circular de la torsión φ del receptor (R), en grados.

- **Tipo:** `NUMBER(18,8)`. **Unidad:** grados. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** atan2(RECEPTOR_BACKBONE_PHI_MEAN_SIN, RECEPTOR_BACKBONE_PHI_MEAN_COS) × 180/π, solo si R>1e−8
- **Ausencias:** NULL si no hay ángulos válidos o R≤1e−8, porque la dirección media no está bien definida. NULL observados: **148 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PHI_CIRCULAR_MEAN_DEG` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Rango definido:** [−180,180]
- **Interpretación:** Torsión φ: C(i−1), N(i), Cα(i), C(i). Se usan vecinos reales de la cadena, aunque no sean Q1. ±180° representan la misma dirección; seno/coseno evitan ese salto al usar modelos clásicos.

### 270. `RECEPTOR_BACKBONE_PHI_CIRCULAR_VARIANCE`

Dispersión circular de φ del receptor (R); cero indica máxima concentración.

- **Tipo:** `NUMBER(19,12)`. **Unidad:** adimensional [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** 1 − RECEPTOR_BACKBONE_PHI_RESULTANT_LENGTH
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **148 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PHI_CIRCULAR_VARIANCE` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión φ: C(i−1), N(i), Cα(i), C(i). Se usan vecinos reales de la cadena, aunque no sean Q1. No es varianza en grados cuadrados ni mide movilidad de una trayectoria.

### 271. `RECEPTOR_BACKBONE_PSI_COVERAGE`

Fracción de residuos Q1 del receptor (R) con torsión ψ calculable.

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** RECEPTOR_BACKBONE_N_PSI / RECEPTOR_N_SELECTED
- **Ausencias:** NULL sin geometría/participante o si N_SELECTED=0. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PSI_COVERAGE` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión ψ: N(i), Cα(i), C(i), N(i+1). Se usan vecinos reales de la cadena, aunque no sean Q1.

### 272. `RECEPTOR_BACKBONE_PSI_CIRCULAR_MEAN_DEG`

Dirección media circular de la torsión ψ del receptor (R), en grados.

- **Tipo:** `NUMBER(18,8)`. **Unidad:** grados. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** atan2(RECEPTOR_BACKBONE_PSI_MEAN_SIN, RECEPTOR_BACKBONE_PSI_MEAN_COS) × 180/π, solo si R>1e−8
- **Ausencias:** NULL si no hay ángulos válidos o R≤1e−8, porque la dirección media no está bien definida. NULL observados: **147 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PSI_CIRCULAR_MEAN_DEG` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Rango definido:** [−180,180]
- **Interpretación:** Torsión ψ: N(i), Cα(i), C(i), N(i+1). Se usan vecinos reales de la cadena, aunque no sean Q1. ±180° representan la misma dirección; seno/coseno evitan ese salto al usar modelos clásicos.

### 273. `RECEPTOR_BACKBONE_PSI_CIRCULAR_VARIANCE`

Dispersión circular de ψ del receptor (R); cero indica máxima concentración.

- **Tipo:** `NUMBER(19,12)`. **Unidad:** adimensional [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** 1 − RECEPTOR_BACKBONE_PSI_RESULTANT_LENGTH
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **147 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PSI_CIRCULAR_VARIANCE` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión ψ: N(i), Cα(i), C(i), N(i+1). Se usan vecinos reales de la cadena, aunque no sean Q1. No es varianza en grados cuadrados ni mide movilidad de una trayectoria.

### 274. `RECEPTOR_BACKBONE_OMEGA_COVERAGE`

Fracción de residuos Q1 del receptor (R) con torsión ω calculable.

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** RECEPTOR_BACKBONE_N_OMEGA / RECEPTOR_N_SELECTED
- **Ausencias:** NULL sin geometría/participante o si N_SELECTED=0. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_OMEGA_COVERAGE` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión ω: Cα(i), C(i), N(i+1), Cα(i+1). Se usan vecinos reales de la cadena, aunque no sean Q1. Es el enlace saliente hacia i+1, no el entrante.

### 275. `RECEPTOR_BACKBONE_OMEGA_CIRCULAR_MEAN_DEG`

Dirección media circular de la torsión ω del receptor (R), en grados.

- **Tipo:** `NUMBER(18,8)`. **Unidad:** grados. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** atan2(RECEPTOR_BACKBONE_OMEGA_MEAN_SIN, RECEPTOR_BACKBONE_OMEGA_MEAN_COS) × 180/π, solo si R>1e−8
- **Ausencias:** NULL si no hay ángulos válidos o R≤1e−8, porque la dirección media no está bien definida. NULL observados: **147 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_OMEGA_CIRCULAR_MEAN_DEG` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Rango definido:** [−180,180]
- **Interpretación:** Torsión ω: Cα(i), C(i), N(i+1), Cα(i+1). Se usan vecinos reales de la cadena, aunque no sean Q1. Es el enlace saliente hacia i+1, no el entrante. ±180° representan la misma dirección; seno/coseno evitan ese salto al usar modelos clásicos.

### 276. `RECEPTOR_BACKBONE_OMEGA_CIRCULAR_VARIANCE`

Dispersión circular de ω del receptor (R); cero indica máxima concentración.

- **Tipo:** `NUMBER(19,12)`. **Unidad:** adimensional [0,1]. **Función ML:** `predictor_candidate`.
- **Uso:** Característica candidata: evaluar selección y redundancia; no inclusión automática en X.
- **Cálculo:** 1 − RECEPTOR_BACKBONE_OMEGA_RESULTANT_LENGTH
- **Ausencias:** NULL si falta el vínculo/geometría o no hay valores válidos para resumir; no equivale a cero. NULL observados: **147 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_OMEGA_CIRCULAR_VARIANCE` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Torsión ω: Cα(i), C(i), N(i+1), Cα(i+1). Se usan vecinos reales de la cadena, aunque no sean Q1. Es el enlace saliente hacia i+1, no el entrante. No es varianza en grados cuadrados ni mide movilidad de una trayectoria.

### 277. `RECEPTOR_BACKBONE_TAU_DEG_COVERAGE`

Fracción de residuos Q1 del receptor (R) con ángulo τ del esqueleto N(i)–Cα(i)–C(i) calculable.

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** RECEPTOR_BACKBONE_N_TAU_DEG / RECEPTOR_N_SELECTED
- **Ausencias:** NULL sin geometría/participante o si N_SELECTED=0. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_TAU_DEG_COVERAGE` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan.

### 278. `RECEPTOR_BACKBONE_N_CA_LENGTH_COVERAGE`

Fracción de residuos Q1 del receptor (R) con longitud N(i)–Cα(i) calculable.

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** RECEPTOR_BACKBONE_N_N_CA_LENGTH / RECEPTOR_N_SELECTED
- **Ausencias:** NULL sin geometría/participante o si N_SELECTED=0. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_N_CA_LENGTH_COVERAGE` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan.

### 279. `RECEPTOR_BACKBONE_CA_C_LENGTH_COVERAGE`

Fracción de residuos Q1 del receptor (R) con longitud Cα(i)–C(i) calculable.

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** RECEPTOR_BACKBONE_N_CA_C_LENGTH / RECEPTOR_N_SELECTED
- **Ausencias:** NULL sin geometría/participante o si N_SELECTED=0. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_CA_C_LENGTH_COVERAGE` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan.

### 280. `RECEPTOR_BACKBONE_PEPTIDE_CN_LENGTH_COVERAGE`

Fracción de residuos Q1 del receptor (R) con longitud del enlace peptídico saliente C(i)–N(i+1) calculable.

- **Tipo:** `FLOAT`. **Unidad:** fracción [0,1]. **Función ML:** `quality_control`.
- **Uso:** Indicador de disponibilidad o calidad; conservar para auditoría, no incluir automáticamente en X.
- **Cálculo:** RECEPTOR_BACKBONE_N_PEPTIDE_CN_LENGTH / RECEPTOR_N_SELECTED
- **Ausencias:** NULL sin geometría/participante o si N_SELECTED=0. NULL observados: **135 / 12062**.
- **Origen Gold:** `PROTEIN_AFFINITY.GOLD.DIM_PARTICIPANT_FEATURES.BACKBONE_PEPTIDE_CN_LENGTH_COVERAGE` · participante R.
- **Código:** [dim_participant_features.sql](<../dbt/models/gold/dim_participant_features.sql>), [backbone_core.py](<../scripts/backbone_core.py>), [backbone_features.sql](<../dbt/models/backbone/backbone_features.sql>).
- **Interpretación:** Valores individuales proceden de residuos Q1. Se excluyen medidas no calculables; no se rellenan. Se exige continuidad de cadena y C–N entre 0.8 y 1.8 Å; no se incluyen enlaces rechazados por esa regla.

## Actualizar el diccionario

Desde la carpeta del proyecto:

```sh
docker compose run --rm pipeline python scripts/build_obt_dictionary.py --refresh
```

`--refresh` solo consulta Snowflake: lee esquema, conteos de NULL y estados, y comprueba la huella frente a la ejecución OBT documentada. No modifica tablas.
Sin `--refresh`, usa `reports/obt_dictionary_profile.json` y puede regenerarse sin conexión. Una columna desconocida detiene el generador para exigir una definición explícita.
Definiciones revisadas en `scripts/build_obt_dictionary.py`; linaje en `reports/obt/<run>/column_lineage.json`. El generador también verifica que ninguna columna falte o aparezca duplicada.
