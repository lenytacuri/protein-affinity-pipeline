# Carga de un lote a Snowflake RAW

Un lote es una ejecucion de extraccion con una entrada concreta (Excel o lista
 de IDs). Su carpeta conserva la entrada, filas originales, manifiesto y resumen.
El primer lote completo contiene 12 062 filas, 3 032 PDB distintos y 6 064 resultados
 de descarga: un JSON y una estructura solicitados por PDB.

## Que significa evitar duplicados

- PDB ID compartido: **se conserva**. Puede haber mediciones, cadenas o mutaciones diferentes.
- Misma fila del mismo Excel cargada dos veces: **se inserta una sola vez**.
- Mismo objeto RCSB descargado en varios lotes: se guarda una vez por SHA-256.
- Cada nuevo lote conserva su propio manifiesto, incluso cuando reutiliza objetos.

RECORD_ID se calcula con SHA-256 del archivo de entrada, hoja y numero de fila.
Es una identidad tecnica de una fila de una version del archivo; NO demuestra
que dos filas sean mediciones cientificamente independientes. Cambiar el Excel
produce una nueva version y nuevas claves, incluso si algunas filas no cambian.
La seleccion de versiones y los duplicados reales entre fuentes se resolveran
explicitamente en las capas de transformacion. RAW conserva la evidencia original.

## Archivos del proyecto

- `scripts/load_raw.py`: valida integridad, sube archivos, carga temporales y ejecuta MERGE.
- `sql/03_raw.sql`: definicion de stage y tablas RAW; no borra ni reemplaza datos existentes.
- `sql/04_verify_raw.sql`: consultas de comprobacion para ejecutar en Snowflake.
- `kestra/load_raw.yml`: flujo con batch_path explicito, dos intentos y una ejecucion simultanea.
- `tests/test_raw_load.py`: pruebas locales de claves e integridad.
- `reports/raw_load.json`: evidencia de la ultima carga y repeticion.

## Que queda en Snowflake

| Objeto en PROTEIN_AFFINITY.RAW | Contenido / unidad de registro |
|---|---|
| SOURCE_FILES (stage) | Originales Excel, JSON y mmCIF.gz; manifiesto y archivos del lote |
| SOURCE_RECORDS | Una fila por version del archivo + hoja + numero de fila; RAW_RECORD conserva todos los valores |
| RCSB_ENTRIES | Una respuesta JSON original interpretada como VARIANT por hash de contenido |
| RESOURCE_FILES | Ubicacion en stage, hash y tamano de cada objeto RCSB disponible |
| BATCH_RESOURCES | Un resultado por lote + PDB + tipo de recurso; incluye los 404 |
| INGESTION_BATCHES | Un lote cargado correctamente, con version de origen y resumen de extraccion |

LOADED significa que la carga completa de lo disponible termino. No significa
que la cobertura de RCSB sea total: la primera extraccion tiene estado PARTIAL
por seis JSON no disponibles. Las 3 032 estructuras si estan disponibles.
Todavia no se certifican ensamblajes biologicos, cadenas, mutaciones ni interfaces.

## Ejecucion y recuperacion

Desde la carpeta del proyecto, ejecutar:

```sh
docker compose run --rm pipeline python scripts/kestra_flow.py kestra/load_raw.yml --run --wait
```

Para otro lote, pasar `--input batch_path=/workspace/data/rcsb/batches/IDENTIFICADOR`.
Esto tambien permite cargar lotes historicos sin volver a descargarlos.
Para la primera carga, el valor por defecto apunta al lote completo ya extraido.

El flujo activa `--verify-replay`: ejecuta MERGE, comprueba los originales, vuelve a
 ejecutar MERGE y exige que los cinco conteos permanezcan iguales.

La carga usa COPY INTO sobre tablas temporales y MERGE con claves tecnicas sobre
RAW. Todas las inserciones se confirman juntas. Si alguna validacion falla, se
revierte esa transaccion. Los archivos ya subidos permanecen reutilizables en el
stage, porque las transferencias no forman parte de la transaccion SQL.
Un bloqueo local compartido entre contenedores impide dos cargas concurrentes.
Esto supone un unico host/volumen de ejecucion; antes de distribuir workers en
varios hosts se necesita un mecanismo de exclusión compartido. Las tablas
Snowflake normales no garantizan unicidad por declarar PRIMARY KEY.

PUT preserva los bytes (AUTO_COMPRESS=FALSE) y usa nombres derivados del SHA-256.
Cada archivo local se verifica contra su hash antes de transferirlo. Se comprueba
la presencia de todos los objetos remotos. Un lote cargado no puede reutilizar su
ID con contenidos distintos; esa discrepancia se rechaza.

Referencias oficiales:
- [PUT: transferencia al stage interno](https://docs.snowflake.com/en/sql-reference/sql/put)
- [MERGE: insercion por claves](https://docs.snowflake.com/en/sql-reference/sql/merge)

Las hojas del navegador se llaman `01_bootstrap.sql` y `02_service_user.sql`.
Son documentos SQL guardados; renombrarlas no cambia tablas ni conexiones.
