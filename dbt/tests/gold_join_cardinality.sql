{{ config(tags=['gold']) }}
-- Same five joins planned for Spark. Each observation must yield exactly one row.
select f.observation_id
from {{ ref('fact_affinity') }} f
left join {{ ref('dim_source') }} s using(source_key)
left join {{ ref('dim_experiment') }} e using(experiment_key)
left join {{ ref('dim_geometry') }} g on f.geometry_id=g.geometry_id
left join {{ ref('dim_participant_features') }} l on f.ligand_participant_key=l.participant_key
left join {{ ref('dim_participant_features') }} r on f.receptor_participant_key=r.participant_key
group by f.observation_id having count(*)<>1
