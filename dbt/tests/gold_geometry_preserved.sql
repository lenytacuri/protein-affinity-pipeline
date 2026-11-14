{{ config(tags=['gold']) }}
select coalesce(s.geometry_id,g.geometry_id) as geometry_id
from {{ ref('silver_structure_geometry') }} s
full outer join {{ ref('dim_geometry') }} g using(geometry_id)
where s.geometry_id is null or g.geometry_id is null
{% for c in ['pdb_id','structure_sha256','code_sha256','geometry_status','n_ligand','n_receptor','min_distance_angstrom','q1_ligand_angstrom','q1_receptor_angstrom','n_selected_q1_ligand','n_selected_q1_receptor','selected_pairs_lt10','selected_pair_count','has_ca_contacts_10','biological_assembly_validated'] %}
 or s.{{c}} is distinct from g.{{c}}
{% endfor %}
 or s.issue is distinct from g.geometry_issue
 or to_json(s.ligand_chains) is distinct from g.ligand_chains_json
 or to_json(s.receptor_chains) is distinct from g.receptor_chains_json
