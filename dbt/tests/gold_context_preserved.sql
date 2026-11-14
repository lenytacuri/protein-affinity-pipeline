{{ config(tags=['gold']) }}
select f.observation_id
from {{ ref('fact_affinity') }} f
join {{ ref('silver_affinity_observations') }} a using(observation_id)
left join {{ ref('dim_source') }} s using(source_key)
left join {{ ref('dim_experiment') }} e using(experiment_key)
where s.source_key is null or e.experiment_key is null
{% for c in gold_source_columns() %} or a.{{c}} is distinct from s.{{c}}{% endfor %}
{% for c in gold_experiment_columns() %} or a.{{c}} is distinct from e.{{c}}{% endfor %}
