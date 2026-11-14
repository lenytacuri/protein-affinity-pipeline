# Primer flujo de Kestra

Snowflake ya responde desde el contenedor con PPA_SERVICE y PPA_PIPELINE.
Esta etapa comprueba el mismo acceso desde Kestra; aun no carga datos.

## Servicios

- postgres: guarda el historial y configuracion interna de Kestra.
- kestra: interfaz y coordinacion en http://localhost:8080.
- audit, snowflake-check y pipeline: trabajos temporales, activados por perfiles.

El usuario y la contrasena locales de Kestra estan en .env, en KESTRA_USER y
KESTRA_PASSWORD. No se versionan. PostgreSQL no publica un puerto en el Mac.
Kestra publica su interfaz solo en 127.0.0.1 y accede al motor Docker para
crear contenedores de trabajo. Es una configuracion de desarrollo local.

## Ejecutar

```sh
docker compose build pipeline
docker compose up -d postgres kestra
docker compose run --rm pipeline python scripts/kestra_flow.py kestra/check_connection.yml --run --wait
```

El flujo debe terminar en SUCCESS. El informe se guarda en reports/.
Las credenciales de Snowflake se leen dentro del contenedor desde .env y
.secrets, montados desde el proyecto. La clave privada no se copia a la imagen
ni a la definicion YAML ni se imprime en los logs.

La tarea check tiene hasta tres intentos separados por 15 segundos. Si falla,
revisar sus logs en Kestra. Este flujo de diagnostico no tiene programacion;
el flujo principal bajo demanda y el reprocesamiento de lotes estan en
`docs/14_pipeline_reproducible.md`. No se configura cron: los lotes requieren curacion cientifica.

Referencias:
- https://kestra.io/docs/installation/docker-compose
- https://kestra.io/plugins/plugin-script-shell/io.kestra.plugin.scripts.shell.commands
- https://kestra.io/docs/how-to-guides/api

## Resultado verificado

Ejecucion `SCDZl1ORrf6M5iWWAVdAV`: SUCCESS.
Flujo `protein.affinity/check_snowflake_connection`.
Comprobacion HTTP de Kestra: 200, pong. PostgreSQL: healthy.
Esta es evidencia de conexion y orquestacion, no de ingesta de los datasets.
