# Primera práctica: un contenedor que conoce nuestros datos

## Objetivo

Poder explicar qué ejecutamos, dónde están los datos y por qué el resultado
permanece disponible después de terminar el contenedor.

## Cuatro conceptos

- **Imagen:** paquete con Python, sus bibliotecas y el programa. Es la plantilla.
- **Contenedor:** una ejecución de esa imagen. En esta práctica termina al acabar el informe.
- **Dockerfile:** receta para construir la imagen.
- **Docker Compose:** archivo que describe cómo ejecutar uno o varios servicios.

## Qué ve el contenedor

| En tu Mac | Dentro del contenedor | Permiso |
|---|---|---|
| Carpeta `protein affinity` | `/data` | Lectura |
| `pset_2/data/reference` | `/reference` | Lectura |
| `pset_2/reports` | `/reports` | Lectura y escritura |

Compartir estas carpetas se llama bind mount. No estamos metiendo 19 GB de
estructuras en una imagen. El contenedor de auditoría tampoco necesita red.

## Qué hace el programa

1. Verifica la huella de la tabla oficial de Zenodo.
2. Lee **todos** sus registros.
3. Usa la fuente y el PDB para determinar el archivo esperado.
4. Comprueba si ese archivo existe y no está vacío.
5. Repite la comprobación para la tabla AF local, si existe.
6. Compara las celdas de la copia antigua con la oficial.
7. Guarda el resumen y los detalles sin alterar las estructuras.

El conteo de archivos no equivale al de observaciones. Un PDB puede ser
reutilizado por muchas mediciones y variantes. Una ruta presente no garantiza
que las cadenas, residuos o coordenadas sean correctos: esa validación viene después.

## Tu práctica

Ejecuta los tres comandos del README, en orden. Después vuelve a ejecutar
`docker compose run --rm audit` y comprueba que los conteos son iguales.
La fecha del reporte sí cambia. El programa vuelve a escribir los informes,
pero no añade copias de las observaciones ni modifica las fuentes.

Antes de pasar a Kestra, intenta explicar:

1. ¿Por qué hay más registros que estructuras necesarias?
2. ¿Por qué el reporte sigue en tu Mac si usamos `--rm`?
3. ¿Qué hace `read_only: true`?
4. ¿Qué garantiza esta auditoría y qué todavía no garantiza?

En la próxima etapa Kestra ejecutará tareas y guardará su historial.
PostgreSQL será la base interna de Kestra. Más adelante sumaremos dbt y Spark,
cada uno con su función. Todo se coordinará desde un mismo Compose.

Referencias: https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-docker-compose/
https://zenodo.org/records/14271435
