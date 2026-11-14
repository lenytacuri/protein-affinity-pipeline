# PSet 2 — Afinidad proteína-proteína

Proyecto de aprendizaje guiado. Estado: **extraccion, carga RAW, perfilado, Bronze, Silver, Gold y OBT con Spark completos mediante Kestra**.
El acceso automático usa PPA_SERVICE con el rol PPA_PIPELINE. Kestra y PostgreSQL están activos.
La extracción RCSB completa terminó en Kestra: 12 062 filas, 3 032 mmCIF y 3 026 JSON.
Seis consultas de metadatos devolvieron 404; todas las filas y estructuras se conservan.
Resumen: `reports/extraction.md`.
RAW ya contiene las 12 062 filas; repetir MERGE mantuvo los conteos de las cinco tablas.
Los originales estan en el stage RAW.SOURCE_FILES. Evidencia: `reports/raw_load.md`.
Perfil SQL ejecutado sobre todas las filas: `reports/raw_profile.md`.
Consultas guardadas en `sql/05_profile_raw.sql`; guia en `docs/07_perfilado_raw.md`.
Bronze creada con dbt: en la primera carga, 12 062 observaciones, 3 026 metadatos y 6 064 resultados de descarga.
Los recibos de descarga aumentan con cada nueva extraccion; no implican nuevas mediciones.
Las 28 pruebas pasaron; reconstruccion con contenido identico y RAW intacta verificadas.
Reporte: `reports/bronze.md`. Guia: `docs/08_bronze_dbt.md`.
Silver inicial: cinco tablas, 35 pruebas aprobadas y reconstruccion identica verificada.
Silver actual: ocho tablas, con INTERFACE_CHEMISTRY y dos tablas de geometria interna agregadas despues.
Se conservaron las 12 062 observaciones. Geometria CA calculada con 8 procesos y seleccion Q1 por participante; sin corte fijo de 25 A.
11 927 observaciones tienen geometria calculada; 135 quedan marcadas por problemas de estructura o cadenas. Las mutaciones tienen estados independientes.
Reporte: `reports/silver.md`. Guia: `docs/09_silver.md`.
Ampliacion quimica: `SILVER.INTERFACE_CHEMISTRY`, una fila por geometria/participante; incluida en futuras construcciones de Silver.
12 pruebas adicionales aprobadas y reconstruccion identica; tablas anteriores intactas.
Reporte: `reports/chemistry.md`. Diccionario: `docs/10_chemical_features.md`. Consulta: `sql/10_view_chemistry.sql`.
Geometria interna: `SILVER.BACKBONE_RESIDUES` conserva 575 774 residuos Q1; `SILVER.BACKBONE_FEATURES` contiene 9 596 resumenes por geometria/participante.
Python calcula phi, psi, omega, tau y longitudes con 8 procesos; dbt resume y valida en Snowflake. Kestra integra ambas etapas.
Reporte y evidencia de pruebas: `reports/backbone.md`. Guia: `docs/11_backbone.md`. Consultas: `sql/12_view_backbone.sql`.
Gold creada con dbt: cinco tablas en estrella, 12 062 hechos, 29 pruebas aprobadas y reconstruccion identica. RAW, Bronze y las ocho tablas Silver permanecen intactas.
Reporte: `reports/gold.md`. Modelo y diagrama: `docs/12_gold.md`. Consultas: `sql/13_view_gold.sql`.
OBT construida con Spark 4.0.1 local[8]: `ANALYTICS.OBT_AFFINITY`, 12 062 filas y 280 columnas.
Reporte: `reports/obt.md`. Codigo: `spark/obt_transform.py` y `spark/build_obt.py`. Guia: `docs/13_obt.md`. Consultas: `sql/14_view_obt.sql`. Los casos estructurales y las mutaciones senaladas requieren revision antes de entrenamiento. No es la entrega terminada.

Conexión: `docs/03_conexion_snowflake.md`. Kestra: `docs/04_kestra.md`.
Extracción: `docs/05_extraccion_rcsb.md`. Carga RAW: `docs/06_carga_raw.md`.

**Alcance vigente:** 12 062 registros principales y 3 032 códigos PDB.
La colección AlphaFold se excluye por decisión del usuario; los reportes antiguos
que la mencionan son inventarios históricos. No se han borrado sus archivos.

## Ejecutar el pipeline completo

El flujo principal recibe **un lote curado bajo demanda** y ejecuta hasta la OBT.
La curación de papers es manual; la descarga, carga, transformación y validación
posteriores son automáticas. No se requiere un calendario de nuevas mediciones.

En esta máquina ya configurada, desde la raíz del proyecto:

```sh
python3 scripts/project.py run
```

Para otro lote: `python3 scripts/project.py run --mode curated --input data/incoming/lote_002.xlsx`.
Para repetir un lote existente: `python3 scripts/project.py run --mode replay --input data/rcsb/batches/IDENTIFICADOR`.

**Evaluador / otra cuenta de Snowflake:** seguir [la guía de reproducción](docs/14_pipeline_reproducible.md).
Incluye bootstrap, configuración propia, construcción ordenada de imágenes, plantilla
para nuevas mediciones y criterios de repetición. No necesita los datos locales del autor.

Flujo: `kestra/affinity_pipeline.yml`. Evidencia: `reports/pipeline/<ID_Kestra>/summary.md`.
Validación completa: [resumen de ejecución y backfill](docs/15_pipeline_validation.md): 11 tareas SUCCESS, 123 pruebas dbt aprobadas y OBT de 12 062 × 280 sin duplicar observaciones.
Los informes individuales anteriores siguen disponibles; el principal los enlaza por ejecución.

## Cómo trabajaremos

Cada etapa explica el concepto, muestra una ejecución pequeña y verificable,
y propone repetirla y entender su resultado. El alcance de datos es completo;
el avance por etapas se refiere a las herramientas, no a recortar registros.

## Auditoría local inicial (etapa histórica, opcional)

Abre Docker Desktop. Después, en una terminal:

```sh
# Desde la carpeta donde clonaste este repositorio
docker compose config --quiet
docker compose build audit
docker compose run --rm audit
```

1. `config --quiet` valida la configuración sin imprimir valores de `.env`.
2. `build` prepara una imagen con Python, las bibliotecas y nuestro programa.
3. `run` crea un contenedor, ejecuta el programa y termina. `--rm` elimina ese
   contenedor al finalizar. Los informes permanecen en `reports/` porque es
   una carpeta de tu Mac compartida con el contenedor.

Lee `docs/01_primer_paso.md` y luego `reports/audit.md`.

## Datos

Las estructuras permanecen fuera del proyecto, en la carpeta superior.
Se comparten en modo de solo lectura; no se copian dentro de la imagen.
La tabla de referencia oficial está en `data/reference/` y se valida con la
huella MD5 publicada en https://zenodo.org/records/14271435.
La copia de Downloads se conserva aparte para comparar los valores.
Los datos, reportes completos, .env y .secrets están excluidos de Git. No compartir las credenciales locales.

El flujo principal descarga la referencia y los archivos RCSB por sí mismo.
La auditoría histórica opcional sí requiere las carpetas antiguas de estructuras.
El inventario no requiere una copia antigua de la tabla, pero sí la referencia oficial.
Para datos en otro lugar copia `.env.example` a `.env` y ajusta `PROTEIN_DATA_DIR`.

## Ruta de trabajo

1. Inventario y primer contenedor: reconocer archivos y registros, comprobar cobertura.
2. Kestra + PostgreSQL: primer flujo, reintentos, programación y backfill.
3. Snowflake Raw: cargar originales y procedencia desde Kestra.
4. dbt Bronze/Silver: limpieza, relaciones, calidad y características.
5. dbt Gold: tabla de hechos y dimensiones en estrella.
6. Spark: construir OBT desde Gold y devolverla a Snowflake.
7. Ejecución completa y documento técnico de hasta seis páginas.

PostgreSQL guardará el estado interno de Kestra; no sustituye a Snowflake.
Spark y dbt estan definidos como servicios de ejecucion de trabajos. Snowflake
es un servicio externo, no un contenedor local.

## Ejecutar Gold despues de Silver y backbone

```sh
docker compose run --rm pipeline python scripts/kestra_flow.py kestra/build_gold.yml --run --wait
```

Los modelos estan en `dbt/models/gold/`. El flujo construye y verifica cinco tablas en `PROTEIN_AFFINITY.GOLD`; no recalcula geometria ni crea todavia la OBT. `reports/gold.md` contiene conteos, significado de cada tabla y evidencia de conservacion. La capa conserva todas las observaciones y sus estados, sin decidir aun la particion de entrenamiento/prueba.

## Construir la OBT con Spark

Con Gold validada, construir las imagenes base en orden si es una maquina nueva:

```sh
docker compose build audit dbt
docker compose build geometry
docker compose build spark
docker compose up -d postgres kestra
docker compose run --rm pipeline python scripts/kestra_flow.py kestra/build_obt.yml --run --wait
```

Las cinco uniones se ejecutan en Spark local, usando Parquet como transporte entre Snowflake y el contenedor. El flujo valida el resultado antes de reemplazar la OBT; no agrega filas por append. Las cinco pruebas pequenas estan en `tests/test_obt.py` y su ultima ejecucion en `reports/obt_unit_tests.log`.

El paso de datos hasta la OBT esta implementado. La entrega del curso aun requiere revisar el conjunto de evidencias y preparar el documento tecnico final; el entrenamiento y la separacion train/test quedan para otra etapa.

## Diccionario de las 280 columnas

- `docs/obt_data_dictionary.md`: lectura por columna, con significado, unidades, fórmulas, NULL, origen y función para ML.
- `docs/obt_data_dictionary.json`: las mismas definiciones en formato estructurado.
- `scripts/build_obt_dictionary.py`: generador; `--refresh` consulta el esquema y las ausencias de Snowflake sin modificar tablas.

El diccionario distingue la etiqueta PKD de sus representaciones KD_M/KD_M_RAW y de la hidropatía Kyte–Doolittle. No ejecuta selección de features.

## Qué contiene el repositorio

Se versionan Python, SQL, modelos y pruebas de dbt, flujos de Kestra, Dockerfiles,
configuración de ejemplo, documentación y evidencia resumida. Las estructuras,
metadatos descargados, archivos Excel, cachés, reportes completos y credenciales
permanecen locales y están excluidos por `.gitignore`. No se necesita Git LFS.

El flujo `reference` obtiene nuevamente el Excel publicado y los recursos de RCSB.
Para repetir exactamente un lote histórico, conservar además sus originales y
manifiestos fuera de Git: RCSB puede actualizar las estructuras entre descargas.
La guía de reproducción explica ambos casos.
