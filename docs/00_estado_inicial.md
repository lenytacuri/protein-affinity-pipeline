# Estado inicial — 10 de noviembre de 2026

Docker Desktop funciona en este Mac ARM64. Hay un contenedor de otro curso;
no se ha modificado. El proyecto usa el nombre Compose `protein-affinity-pset2`.

## Fuentes locales

- `PDB/`: 11.370 archivos PDB, de cinco colecciones de origen.
- `PPB-Affinity-AF/`: 95 observaciones en la tabla local y 70 PDB.
- `sabdab_search_structures_20260911T200227/`: descarga adicional de SAbDab2.
- `splits_final/`: estructuras SAbDab2 procesadas para ML; no son automáticamente
  observaciones con afinidad de PPB-Affinity.
- Tabla principal encontrada en Downloads; se conserva el original.

Se descargó una copia de la tabla oficial del registro Zenodo 14271435 (v5)
y los dos paquetes pequeños AF y samples_deleted, verificando sus MD5 publicados.
No fue necesario descargar otra vez el archivo PDB.zip de 3,1 GB.
`samples_deleted` contiene anotaciones de exclusiones; no debe mezclarse con
los registros elegibles como si fueran mediciones adicionales para entrenamiento.

## Resultados

- La tabla oficial tiene 12.062 registros y 3.032 PDB distintos.
- Todos los registros principales tienen una ruta esperada existente y no vacía.
- Esto NO demuestra que todos los átomos o cadenas sean correctos, ni verifica
  bit a bit las estructuras principales contra el archivo oficial PDB.zip.
- La tabla antigua y la oficial difieren en ocho celdas: tres diferencias de
  representación numérica diminutas y cinco diferencias de escapes de texto.
  Los datos se conservan sin limpiar; la limpieza documentada será parte de dbt.
- El paquete AF oficial contiene exactamente 70 PDB, todos presentes en local
  y coincidentes con el CRC del archivo oficial. Los 25 IDs HER2 mutantes no
  tienen PDB individual en la publicación. Existe HER2-data-wt.pdb y anotaciones
  de mutación. Hay que validar ese mapeo antes de generar features; no inventar
  coordenadas ni descartar esas observaciones silenciosamente.

## Límite de esta etapa

La auditoría prepara el inventario. No es todavía una ingesta Kestra ni Raw en
Snowflake. Se conservarán las observaciones y las decisiones de elegibilidad
en las siguientes capas. El script será una pieza reutilizable, no un reemplazo
del pipeline exigido por el profesor.

## Lo que sigue

Explicar y ejecutar Compose con el usuario; añadir Kestra y PostgreSQL, crear
un primer flujo y después conectar Snowflake. Aún no se han creado recursos
en Snowflake ni se han configurado credenciales.
