# Bronze: tres tablas creadas con dbt en Snowflake

Ubicación: `PROTEIN_AFFINITY.BRONZE`. Es un esquema de la misma base de datos.
El resultado de la última ejecución validada está en `reports/bronze.md`.

| Tabla | Una fila representa | Modelo SQL en el proyecto |
|---|---|---|
| AFFINITY_OBSERVATIONS | Una observación del Excel original | dbt/models/bronze/bronze_affinity_observations.sql |
| STRUCTURE_METADATA | Una versión del JSON de metadatos de RCSB | dbt/models/bronze/bronze_structure_metadata.sql |
| RESOURCE_RECEIPTS | El resultado de solicitar un recurso para un PDB dentro de un lote | dbt/models/bronze/bronze_resource_receipts.sql |

## Qué cambia respecto a RAW

El modelo principal convierte los campos del objeto PAYLOAD en columnas que podemos consultar directamente: fuente, cadenas, mutaciones, afinidad, temperatura y referencias. Convierte Kd y resolución a números y conserva sus valores originales. PAYLOAD sigue disponible completo.

No se eliminan observaciones por compartir PDB, cadenas o afinidad. Tampoco se rellenan temperaturas, referencias o métodos ausentes. Las anotaciones `assumed` y `TBD` permanecen visibles. La selección de versiones y agrupación para separar entrenamiento y prueba quedan pendientes.

STRUCTURE_METADATA contiene información sobre las estructuras, no sus coordenadas. Los archivos 3D siguen en `PROTEIN_AFFINITY.RAW.SOURCE_FILES`. RESOURCE_RECEIPTS permite localizar esos archivos y conserva también las solicitudes que devolvieron 404.

## Cómo se ejecuta

Desde `/Users/lenytacuri/protein affinity/pset_2`:

```sh
docker compose build dbt
docker compose up -d postgres kestra
docker compose run --rm pipeline python scripts/kestra_flow.py kestra/build_bronze.yml --run --wait
```

Kestra inicia el contenedor de dbt. `scripts/run_bronze.py` comprueba la conexión, ejecuta los modelos SQL en Snowflake, corre las pruebas y repite la construcción para verificar que el contenido sea igual. También compara RAW antes y después para comprobar que no cambió.

El SQL está guardado en VS Code; Snowflake ejecuta las consultas y almacena las tablas. El contenedor no descarga los datos para hacer estas transformaciones.

Para ver las observaciones en Snowflake, usa `sql/06_view_bronze.sql`.

## Archivos de control

- `dbt/models/bronze/schema.yml`: descripción de columnas y pruebas básicas.
- `dbt/tests/`: pruebas de conservación, claves y vínculos con archivos.
- `dbt/profiles.yml`: configuración de conexión mediante variables, sin claves privadas.
- `kestra/build_bronze.yml`: flujo de ejecución.
- `reports/bronze/`: logs y resultados de cada ejecución.

Cada ejecución reconstruye las tres tablas desde RAW, incorporando los nuevos lotes ya cargados. No es una carga incremental ni una transacción única de toda la capa: si falla una prueba, se corrige y repite antes de continuar a Silver.
