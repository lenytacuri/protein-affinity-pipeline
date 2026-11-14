# Evidencia de la ejecución completa

Flujo: `protein.affinity/affinity_pipeline`. Ejecución: `1PoNtg6X5ukSm0ftJi4VpX`. Estado: **SUCCESS**.

Se verificó el recorrido completo en la cuenta existente del proyecto: entrada del lote, RAW, perfilado, Bronze, Silver, geometría interna, Gold, OBT y diccionario. Las once tareas de Kestra finalizaron correctamente.

## Resultado

| Comprobación | Resultado |
|---|---|
| Observaciones en Bronze, Silver, Gold y OBT | 12 062 en cada capa |
| OBT | 12 062 filas × 280 columnas; 12 062 identificadores únicos |
| Pruebas dbt | 123 de 123 aprobadas |
| Repetición de RAW | Conteos idénticos antes, después y tras repetir MERGE |
| Reconstrucción dbt | Contenido idéntico en Bronze, Silver, backbone y Gold |
| Spark | Repetición y lectura de Parquet con resultado idéntico |
| Contraste independiente de OBT | Las 280 columnas coinciden con el join SQL de Gold |
| Huella agregada de OBT | 4138267215546828772; coincide con la OBT validada anteriormente |
| Diccionario | 280 columnas documentadas |
| Pruebas del controlador | 10 aprobadas; contrato, aislamiento, integridad y arranque de Kestra |

Pruebas dbt por etapa: Bronze 28, Silver 47, geometría interna 19 y Gold 29.

## Qué prueba el backfill y la repetición

Se volvió a ingresar la fuente histórica completa, con 12 062 mediciones y 3 032 códigos PDB. La extracción reutilizó los objetos íntegros disponibles y registró otra vez las seis ausencias de metadatos; se conservan las estructuras y las observaciones.
El lote generado fue `2026-11-13T212905.751312_0000_44c85b0f`.

La primera ejecución (`2EZWh6pTKzVwPpVKVOPlRW`) completó la extracción, RAW y el perfilado. Al iniciar Bronze se detectó que el controlador importaba el lector de Excel en el contenedor de dbt. Se corrigió separando esas dependencias y se comprobó el arranque en las imágenes de dbt, geometría y Spark.

La ejecución completa posterior usó `mode=replay` sobre ese mismo lote. No agregó otra extracción ni otra copia de las observaciones. RAW conservó 12 062 registros, 3 026 metadatos, 6 058 archivos, 12 128 recibos de recursos y 2 lotes registrados. Los recibos y lotes adicionales proceden de la reingesta histórica anterior, no del replay.

## Alcance y reproducción

Esta prueba se realizó con la cuenta y los datos ya existentes. No afirma que se haya ejecutado en una cuenta nueva del evaluador. La guía de arranque prepara sus propios accesos y objetos de Snowflake. La curación científica sigue siendo manual; el flujo se dispara bajo demanda y no tiene cron.

La prueba no agrega observaciones ficticias para simular un lote nuevo. La entrada de Excel curado se valida con pruebas locales; el recorrido de producción se verificó con todas las observaciones originales.

- [Guía para otra cuenta y nuevos lotes](14_pipeline_reproducible.md).
- [Resumen estructurado sin credenciales ni datos por observación](evidence/pipeline_validation.json).
- Evidencia local detallada: `reports/pipeline/1PoNtg6X5ukSm0ftJi4VpX/summary.json` y `summary.md`.
- Recibo de Kestra: `reports/kestra_affinity_pipeline_1PoNtg6X5ukSm0ftJi4VpX.json`.
- Pruebas locales: `reports/pipeline_unit_tests.log`.

Los informes completos y originales están excluidos de Git; este resumen y su JSON pueden acompañar al código. Una nueva ejecución genera sus propios informes. El memo técnico final del curso se prepara por separado.
