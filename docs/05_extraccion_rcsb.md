# Extraccion batch desde RCSB

## Alcance vigente

Por decision del usuario se excluye PPB-Affinity-AF de la entrega. El universo
inicial es el Excel principal: 12 062 registros y 3 032 PDB ID distintos.
Los archivos AF descargados anteriormente se conservan, pero no participan
en este flujo. Los inventarios anteriores incluyen AF como auditoria historica.

## Responsabilidades del codigo

| Archivo | Responsabilidad |
|---|---|
| scripts/source_inputs.py | Leer filas originales y obtener PDB distintos. |
| scripts/rcsb_download.py | Descargar, reintentar, validar formato y mantener cache. |
| scripts/extract_rcsb.py | Ejecutar el batch y registrar resultados. |
| kestra/extract_rcsb.yml | Coordinar Python desde Kestra y reintentar fallos tecnicos. |

## Que se extrae

Para cada PDB se consulta `https://data.rcsb.org/rest/v1/core/entry/<PDB>`
y se descarga `https://files.rcsb.org/download/<PDB>.cif.gz`.
Se preservan el JSON y mmCIF originales. No se calculan features ni se limpia
la tabla de afinidades en este paso. Esta etapa escribe en disco local; la
carga a Snowflake Raw se implementa a continuacion.

El mmCIF corresponde a la entrada depositada. No siempre equivale al ensamblaje
biologico completo. Descargarlo no certifica una interaccion ni que represente
las cadenas o mutaciones de la medicion. Estas comprobaciones son posteriores.
No se sustituyen automaticamente entradas obsoletas por nuevos identificadores.

## Ejecutar

Todos los registros principales:

```sh
docker compose build pipeline
docker compose run --rm pipeline python scripts/extract_rcsb.py
```

Desde Kestra:

```sh
docker compose run --rm pipeline python scripts/kestra_flow.py kestra/extract_rcsb.yml --run --wait
```

El ayudante espera hasta dos horas (configurable con --wait-timeout en segundos); si se agota ese tiempo la ejecucion de
Kestra sigue activa. Consultar su ID en Kestra; no lanzar otra mientras sigue.

Otra tabla con mediciones (requiere columna PDB):

```sh
docker compose run --rm pipeline python scripts/extract_rcsb.py --input data/nuevas_mediciones.xlsx
```

Lista de codigos, uno por linea:

```sh
docker compose run --rm pipeline python scripts/extract_rcsb.py --mode ids --input data/nuevos_pdb.txt
```

Una lista de codigos genera solicitudes de estructuras, no mediciones de
afinidad. Para ampliar datos de entrenamiento se necesitan ademas Kd o pKd,
unidades, participantes/cadenas y condiciones disponibles. pKa mide acidez.
El extractor no asigna una afinidad inexistente. El registro source_record_id
identifica una fila de un snapshot; no deduplica mediciones entre fuentes ni
entre versiones del Excel. Esa politica pertenece al modelado posterior.

## Resultados y reejecucion

Leer primero `reports/extraction.md`. `data/rcsb/latest_batch.json` localiza el ultimo batch completado.
En `data/rcsb/batches/<run_id>/`:

- summary.json: resumen que debe leerse primero.
- records.jsonl: todas las filas, incluyendo codigos invalidos.
- requested_ids.json: IDs distintos solicitados.
- download_manifest.jsonl: estado, URL, fecha, bytes y SHA-256 por recurso.
- source.xlsx o source.txt: copia intacta de la entrada.

En `data/rcsb/objects/` quedan los archivos nombrados por su SHA-256. El indice
`data/rcsb/index/<PDB>/` relaciona el codigo legible con esos archivos. Esto
permite conservar versiones anteriores cuando una entrada cambia.

Una reejecucion valida la huella y reutiliza los archivos existentes. No duplica
estructuras. Cada ejecucion deja su propio manifiesto. `--refresh` vuelve a
consultar RCSB y conserva objetos anteriores si cambiaron. `--plan-only` produce
el plan y las filas sin hacer solicitudes de red.

HTTP 404/410: se registra not_found y se conserva la observacion. No se reintenta
esa respuesta ni se inventa un reemplazo. Timeouts, 429 y errores del servidor:
hasta cuatro intentos por recurso, respetando Retry-After cuando es razonable.
Si Retry-After supera dos minutos, se pospone al siguiente batch. Fallos tecnicos
persistentes hacen fallar la tarea y Kestra reintenta con la cache ya descargada.
Un bloqueo de archivos y concurrencia de Kestra=1 evitan dos escritores simultaneos.

COMPLETE significa cobertura de descargas, no validacion biologica. PARTIAL
significa que faltan recursos o hay IDs invalidos; revisar motivos en el manifiesto.

El flujo principal `affinity_pipeline` integra la carga y las capas hasta OBT.
Se ejecuta bajo demanda al entregar un lote curado, sin cron. Backfill y replay
se documentan en `docs/14_pipeline_reproducible.md`.

Documentacion:
- https://data.rcsb.org/
- https://www.rcsb.org/docs/programmatic-access/file-download-services

## Ejecucion verificada

Flujo Kestra: protein.affinity/extract_rcsb.
Ejecucion: 3LtX7phQhN7vfeKtyazbcg, estado SUCCESS.
Batch: 2026-11-11T205145.939819_0000_b001c712.
12 062 filas originales, 12 062 claves de fila unicas, 3 032 PDB distintos.
6 064 solicitudes logicas: 3 032 estructuras disponibles y 3 026 JSON disponibles.
Cuatro recursos se reutilizaron de la prueba inicial y 6 054 se descargaron.
Seis JSON respondieron 404: 1A2K, 3L5Y, 3OHM, 3PVM, 3RVV y 3RVW.
Cobertura PARTIAL, sin fallos tecnicos pendientes. No hay filas de AlphaFold.
Tamano de recursos disponibles: aproximadamente 1 015 MB comprimidos/JSON.

En RCSB se verifico que 1A2K esta obsoleto y fue sustituido por 5BXQ:
https://www.rcsb.org/structure/removed/1A2K
No se ha aplicado esa sustitucion ni se ha inferido el motivo de los otros cinco
404. Las coordenadas historicas de los seis codigos si se descargaron.

Pruebas automatizadas: nueve casos, incluidos duplicados, IDs invalidos,
HTTP 404, 429 con Retry-After, cache, corrupcion y respuestas inesperadas.
