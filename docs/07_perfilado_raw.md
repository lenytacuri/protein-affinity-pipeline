# Perfilado previo a Bronze

## Que abrir primero

1. `reports/raw_profile.md`: informe legible con problema, evidencia, accion propuesta y justificacion.
2. `sql/05_profile_raw.sql`: consultas que calcularon los resultados en Snowflake.
3. `reports/profiling/latest.json`: indica la carpeta de evidencia de la ultima ejecucion.

El SQL se guarda en VS Code, pero se ejecuta en Snowflake con PPA_WH.
`scripts/profile_raw.py` se conecta, ejecuta ese archivo y escribe CSV, JSON y Markdown.
Python no sustituye las consultas de perfilado: coordina su ejecucion y prepara el reporte.

## Como repetirlo

Desde la carpeta `/Users/lenytacuri/protein affinity/pset_2`:

```sh
docker compose run --rm pipeline python scripts/profile_raw.py
```

O mediante Kestra, que es la ruta automatizada:

```sh
docker compose run --rm pipeline python scripts/kestra_flow.py kestra/profile_raw.yml --run --wait
```

Tambien puedes copiar el archivo SQL a una hoja de Snowflake y ejecutar Run all.
Las vistas PROFILE_BASE y PROFILE_FIELDS son temporales. Solo ayudan a consultar
los campos del JSON durante esa sesion; no crean Bronze ni cambian las tablas RAW.
La hoja mostrara los resultados de las consultas; para guardar automaticamente
el informe local usa el ejecutor Python o Kestra.

## Que significa cada bloque del SQL

- `setup`: contexto de warehouse/base y vistas temporales para leer los campos.
- `overview` y `source_versions`: universo, claves y cantidades por fuente/version.
- `completeness`, `field_types`, `common_values`: faltantes, tipos y valores frecuentes.
- `numeric_validity` y `numeric_distribution`: afinidades, temperaturas y resoluciones.
- `numeric_cases`, `temperature_values`, `affinity_methods`: detalle de formatos observados.
- `missing_by_source`: localiza en que colecciones faltan datos.
- `exact_duplicate_groups`: compara todos los valores salvo el indice exportado.
- `candidate_measurement_groups`: compara ocho campos experimentales seleccionados.
- `paper_complex_id_uniqueness` y `paper_complex_id_duplicates`: verifican la clave declarada por los autores, por version del archivo.
- `paper_example_3g6d`: muestra el ejemplo de coincidencias con referencias diferentes o pendientes.
- `broad_candidate_groups`: compara PDB, cadenas, mutacion y Kd, omitiendo referencia, metodo y temperatura. No implementa la deduplicacion del paper.
- `resource_coverage`: vincula las observaciones con los recursos de sus lotes cargados.
- `chain_annotations` y `chain_overlap_cases`: revisa las anotaciones, no el archivo 3D.
- `date_formats` y `reference_formats`: distingue fechas y referencias con formatos diferentes.
- `metadata_resolution_comparison` y `metadata_resolution_cases`: contrasta resolucion con RCSB.

El articulo usa Complex ID (incluye referencia de afinidad) para deduplicar.
No sumar los grupos exploratorios: pueden solaparse. Una coincidencia sin considerar
la referencia no demuestra que dos filas sean el mismo experimento y no autoriza
borrarlas. Fuente: https://pmc.ncbi.nlm.nih.gov/articles/PMC11615212/ (Methods).
El reporte actualizado corrige la etiqueta anterior candidatos amplios.

## Verificacion

El ejecutor reconcilia los conteos y compara cantidad y HASH_AGG de las cinco
tablas RAW antes/despues. Deben permanecer iguales. Cada resultado conserva su
identificador de consulta de Snowflake y la huella del SQL usado.

Se contrastan ademas los resultados principales con el Excel original mediante:

```sh
docker compose run --rm pipeline python tests/verify_profile_excel.py
```

Esta verificacion independiente corresponde al snapshot principal unico del
paper. Si el perfil incluye otras versiones, se detiene para evitar comparar
universos distintos. La evidencia se guarda como `excel_crosscheck.json`.

## Estado

Perfil completo ejecutado en Kestra: `54HDZS8MYnQEartHPFgBCn` (SUCCESS).
RAW conserva 12 062 filas. Las acciones del reporte aun no se han aplicado.
El siguiente paso es construir Bronze con dbt, manteniendo trazabilidad y
separando los campos originales en columnas consultables.
