{{ config(alias='DIM_GEOMETRY') }}
select geometry_id, pdb_id, structure_sha256, code_sha256,
       to_json(ligand_chains) as ligand_chains_json,
       to_json(receptor_chains) as receptor_chains_json,
       geometry_status, issue as geometry_issue,
       n_ligand, n_receptor, min_distance_angstrom,
       q1_ligand_angstrom, q1_receptor_angstrom,
       n_selected_q1_ligand, n_selected_q1_receptor,
       selected_pairs_lt10, selected_pair_count, has_ca_contacts_10,
       biological_assembly_validated,
       to_json(parameters) as geometry_parameters_json
from {{ ref('silver_structure_geometry') }}
