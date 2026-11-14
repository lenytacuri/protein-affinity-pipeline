{% macro gold_key(columns, prefix='') -%}
sha2(to_json(array_construct({% for col in columns %}{{ prefix }}{{ col }}{% if not loop.last %}, {% endif %}{% endfor %})),256)
{%- endmacro %}
{% macro gold_source_columns() %}
{{ return(['source_sha256','source_file','source_sheet','source_dataset']) }}
{% endmacro %}
{% macro gold_experiment_columns() %}
{{ return(['affinity_method','affinity_method_raw','temperature_k','temperature_raw','temperature_status','temperature_assumed','affinity_reference_raw','affinity_reference_status','affinity_pmid','affinity_release_date_raw']) }}
{% endmacro %}
