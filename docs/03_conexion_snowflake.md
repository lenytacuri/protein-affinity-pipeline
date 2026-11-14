# Conexion con Snowflake

El bootstrap sql/01_bootstrap.sql se ejecuto y verifico en la cuenta del proyecto.
Existen PROTEIN_AFFINITY, RAW, BRONZE, SILVER, GOLD, ANALYTICS y PPA_WH.
El warehouse es XSMALL, inicialmente suspendido y con AUTO_SUSPEND=60.
Esta es la preparacion inicial; el proyecto ya tiene datos hasta la OBT.
Para otra cuenta seguir `docs/14_pipeline_reproducible.md`.

## Acceso automatico verificado

En esta maquina ya se ejecuto:

```sh
python3 scripts/prepare_snowflake_auth.py
```

La clave privada esta en .secrets/snowflake_key.p8 (permisos 600, fuera de Git).
El SQL publico esta en sql/02_service_user.local.sql. El titular ya copio su
contenido a una nueva hoja SQL de Snowflake y ejecuto Run all. Crea PPA_SERVICE
con TYPE=SERVICE, clave publica y rol PPA_PIPELINE, limitado a la base del proyecto.
No enviarlo al chat ni modificar el usuario personal. Si PPA_SERVICE ya existe,
CREATE USER falla deliberadamente: no reemplazar sus credenciales a ciegas.

En otra maquina, copiar .env.example a .env, ajustar SNOWFLAKE_ACCOUNT y generar
la clave local. Registrar esa clave en Snowflake requiere administrar el usuario
correspondiente; no copiar claves privadas al repositorio.

## Comprobacion

```sh
docker compose build snowflake-check
docker compose run --rm snowflake-check
```

El segundo comando debe mostrar connection=ok y las cinco capas. Esta prueba
lee el contexto de sesion y la lista de esquemas; no carga ni modifica datos.
La imagen esta construida y la comprobacion termino con connection=ok.
Se verificaron usuario PPA_SERVICE, rol PPA_PIPELINE y visibilidad de las cinco capas.

Documentacion: https://docs.snowflake.com/en/user-guide/key-pair-auth
