{% macro backbone_file() -%}
    {%- set prefix = var('backbone_prefix', 'not_built') -%}
    {%- if not modules.re.fullmatch('[a-zA-Z0-9_]+', prefix) -%}
        {{ exceptions.raise_compiler_error('Invalid backbone artifact prefix') }}
    {%- endif -%}
    @{{ env_var('SNOWFLAKE_DATABASE') }}.SILVER.BACKBONE_FILES/{{ prefix }}/
    (file_format => '{{ env_var("SNOWFLAKE_DATABASE") }}.SILVER.BACKBONE_JSON',
     pattern => '.*backbone_[0-9]+[.]jsonl[.]gz')
{%- endmacro %}
