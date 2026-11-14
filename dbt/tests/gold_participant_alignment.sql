{{ config(tags=['gold']) }}
select f.observation_id
from {{ ref('fact_affinity') }} f
left join {{ ref('dim_geometry') }} g on f.geometry_id=g.geometry_id
left join {{ ref('dim_participant_features') }} l on f.ligand_participant_key=l.participant_key
left join {{ ref('dim_participant_features') }} r on f.receptor_participant_key=r.participant_key
where (f.geometry_id is null and (f.ligand_participant_key is not null or f.receptor_participant_key is not null))
 or (f.geometry_id is not null and (
  l.partner is distinct from 'L' or r.partner is distinct from 'R'
  or l.geometry_id is distinct from f.geometry_id or r.geometry_id is distinct from f.geometry_id
  or g.pdb_id is distinct from f.pdb_id or l.pdb_id is distinct from f.pdb_id or r.pdb_id is distinct from f.pdb_id
  or l.n_selected is distinct from g.n_selected_q1_ligand or r.n_selected is distinct from g.n_selected_q1_receptor))
