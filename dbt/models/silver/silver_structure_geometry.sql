{{ config(alias='STRUCTURE_GEOMETRY') }}
-- Una geometria por archivo + grupos de cadenas + version de codigo/parametros.
select
    $1:geometry_id::varchar as geometry_id,
    $1:pdb_id::varchar as pdb_id,
    $1:structure_sha256::varchar as structure_sha256,
    $1:code_sha256::varchar as code_sha256,
    $1:ligand_chains::array as ligand_chains,
    $1:receptor_chains::array as receptor_chains,
    $1:status::varchar as geometry_status,
    strip_null_value($1:reason)::varchar as issue,
    $1:n_ligand::integer as n_ligand,
    $1:n_receptor::integer as n_receptor,
    $1:min_distance::double as min_distance_angstrom,
    $1:q1_ligand::double as q1_ligand_angstrom,
    $1:q1_receptor::double as q1_receptor_angstrom,
    $1:n_selected_q1_ligand::integer as n_selected_q1_ligand,
    $1:n_selected_q1_receptor::integer as n_selected_q1_receptor,
    $1:selected_pairs_lt10::integer as selected_pairs_lt10,
    $1:selected_pair_count::integer as selected_pair_count,
    $1:has_ca_contacts_10::boolean as has_ca_contacts_10,
    coalesce($1:biological_assembly_validated::boolean,false) as biological_assembly_validated,
    $1:composition_ligand_q1 as composition_ligand_q1,
    $1:composition_receptor_q1 as composition_receptor_q1,
    $1:parameters as parameters,
    $1:stats as structure_stats
from {{ geometry_file('jobs') }}
