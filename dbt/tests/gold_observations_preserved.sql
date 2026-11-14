{{ config(tags=['gold']) }}
select coalesce(s.observation_id,f.observation_id) as observation_id
from {{ ref('silver_affinity_observations') }} s
full outer join {{ ref('fact_affinity') }} f using(observation_id)
where s.observation_id is null or f.observation_id is null
{% for c in ['kd_m','pkd','kd_status','pdb_id','geometry_id','source_row','mutations_raw','mutation_structure_status','geometry_status','uses_reference_for_mutation'] %}
 or s.{{c}} is distinct from f.{{c}}
{% endfor %}
