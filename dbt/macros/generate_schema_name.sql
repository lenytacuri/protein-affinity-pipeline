{% macro generate_schema_name(custom_schema_name, node) -%}
    {# Proyecto de un solo usuario: usa los esquemas que ya creamos en Snowflake. #}
    {%- set requested = custom_schema_name | trim | upper if custom_schema_name else target.schema | upper -%}
    {%- if requested not in ['BRONZE', 'SILVER', 'GOLD', 'ANALYTICS'] -%}
        {{ exceptions.raise_compiler_error('Esquema de destino no autorizado: ' ~ requested) }}
    {%- endif -%}
    {{ requested }}
{%- endmacro %}
