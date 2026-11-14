# Plan de entrega en 12 horas

Estado actualizado: inventario ejecutado, Snowflake conectado y primer flujo
de Kestra exitoso. Extraccion finalizada: 3 032 mmCIF, 3 026 JSON y seis 404 de
metadatos; 12 062 registros conservados. RAW cargado y repeticion sin duplicados verificada. Bronze creada con dbt: tres tablas y 28 pruebas aprobadas. Silver inicial: cinco tablas y 35 pruebas aprobadas. Ampliacion quimica: sexta tabla y 12 pruebas adicionales aprobadas. Ampliacion de geometria interna: dos tablas adicionales (ocho tablas Silver en total); mediciones por residuo y resumenes por participante. Evidencia: reports/backbone.md. Gold validada: cinco tablas en estrella y 29 pruebas aprobadas. OBT construida con Spark local[8]: 12 062 filas y 280 columnas; evidencia en reports/obt.md.
Los tiempos de esta tabla son el plan original, no evidencia de ejecucion.

## Prioridad y presupuesto orientativo

| Tiempo | Hito verificable |
|---|---|
| 0-1 h | Conexion automatizable a Snowflake; Compose con Kestra y PostgreSQL. |
| 1-4 h | Ingesta completa desde Kestra a Raw; perfiles de calidad y validacion estructural. |
| 4-7 h | dbt Bronze/Silver/Gold, esquema estrella y tests. |
| 7-9 h | Spark construye la OBT; verifica cardinalidad y escribe en Snowflake. |
| 9-12 h | Reejecucion, evidencia de retries/backfill, README y memo de hasta seis paginas. |

Los tiempos son una reserva de trabajo, no una garantia. Adelantar la prueba
de conexion y una ejecucion pequena permite descubrir problemas de acceso pronto.
La entrega final debe procesar todo el universo de registros definido abajo.

## Universo y grano

- Snapshot principal: 12 062 filas de PPB-Affinity, Zenodo 14271435.
- Coleccion AF excluida por decision del usuario. Los archivos antiguos se
  conservan como antecedente, pero no ingresan al pipeline ni a la OBT.
- Clave de observacion: version de fuente + tabla + fila de origen. Un PDB ID
  no es una clave unica de observacion ni prueba de independencia experimental.
- Otros archivos locales se inventarian, pero no se convierten automaticamente
  en ejemplos etiquetados de afinidad.
- Raw y la OBT conservaran trazabilidad y estados. Separar elegibilidad para
  entrenamiento de presencia en la tabla; ausencia de feature no equivale a cero.

## Primera version de caracteristicas

Validar archivo, modelo, grupos de cadenas, residuos observados y compatibilidad
con variante. Documentar si se usa estructura de referencia para una mutacion.
Calcular numero de residuos observados, distancias minimas CA, seleccion Q1 por
participante y composicion de residuos seleccionados. Los 10 A se conservan como
referencia comparativa; no se usa un corte fijo de 25 A. Guardar todos los pares
entre los residuos seleccionados de ambos participantes.
No etiquetar contactos geometricos como evidencia experimental de union.
Los puentes de hidrogeno y energias requieren preparacion adicional y quedan
para una ampliacion despues de conseguir el pipeline obligatorio completo.

## Infraestructura prevista

Kestra coordina la ingesta y tareas Python. PostgreSQL almacena exclusivamente
el estado interno de Kestra. dbt Core ejecuta limpieza y modelado en Snowflake.
Spark ejecuta los joins de Gold para producir ANALYTICS.OBT_AFFINITY.
Docker Compose define los servicios locales; Snowflake permanece en la nube.

## Paso actual

Conexion, extraccion, carga RAW, perfil de calidad y Bronze verificados.
Evidencia Bronze: `reports/bronze.md`; ejecucion Kestra `9U1zjvzV0p7em1QpPFVbI`.
Silver ejecutada con seleccion Q1 por participante sobre distancias minimas CA; 8 procesos locales.
Evidencia: `reports/silver.md`; Kestra `4UxuWoB0gjC1afe0JtZZZe`.
135 observaciones quedan marcadas por problemas de geometria/cadenas, sin eliminarlas.
Gold creada: 12 062 hechos y cuatro dimensiones; 29 pruebas, reconstruccion identica y conservacion de todas las capas previas. Evidencia: `reports/gold.md`; Kestra `7E048eN7rrZRaKPIQg7S9T`.
OBT construida y validada en ANALYTICS.OBT_AFFINITY con Spark. Siguiente etapa de la entrega: consolidar las evidencias y el memo tecnico. La elegibilidad final y la particion train/test siguen pendientes; se conservan los estados de validacion.
La carga y su repeticion estan en `reports/raw_load.md`. El diagnostico previo a
limpieza y acciones propuestas estan en `reports/raw_profile.md`.

## Evidencia minima que debe conservarse

- IDs y resultados de ejecuciones de Kestra, incluyendo reejecucion y fallo controlado.
- Cantidades por fuente antes y despues, y motivo de cada caso no procesable.
- Tabla Problema / Evidencia / Accion / Justificacion con cifras reales.
- Resultado de dbt build, pruebas de claves y relaciones, y reglas del dominio.
- Conteo de hechos Gold frente a OBT y unicidad de observation_id.
- Comprobacion de que reprocesar el mismo lote no duplica observaciones.
- Versiones, parametros, huellas de archivos y procedencia de cada resultado.

Referencia de la tarea: Downloads/CD_PSet_2 (1).pdf.
Documentacion de inicio: https://docs.snowflake.com/en/sql-reference/sql/create-warehouse
Autenticacion: https://docs.snowflake.com/en/user-guide/key-pair-auth
