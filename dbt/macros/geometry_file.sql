{% macro geometry_file(kind) -%}
    {%- set prefix = var('geometry_prefix', 'not_built') -%}
    {%- if not modules.re.fullmatch('[a-zA-Z0-9_]+', prefix) or kind not in ['jobs','observations','residues','pairs'] -%}
        {{ exceptions.raise_compiler_error('Ruta de artefactos geometria invalida') }}
    {%- endif -%}
    @{{ env_var('SNOWFLAKE_DATABASE') }}.SILVER.GEOMETRY_FILES/{{ prefix }}/
    (file_format => '{{ env_var("SNOWFLAKE_DATABASE") }}.SILVER.GEOMETRY_JSON',
     pattern => '.*{{ kind }}_[0-9]+[.]jsonl[.]gz')
{%- endmacro %}
