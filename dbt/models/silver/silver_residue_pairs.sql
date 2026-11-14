{{ config(alias='RESIDUE_PAIRS') }}
-- Todos los pares L-R entre residuos seleccionados por Q1, sin limite fijo de distancia.
select
    $1:geometry_id::varchar || ':' || $1:ligand_residue_index::varchar || ':' || $1:receptor_residue_index::varchar as pair_id,
    $1:geometry_id::varchar as geometry_id,
    $1:geometry_id::varchar || ':' || $1:ligand_residue_index::varchar as ligand_residue_id,
    $1:geometry_id::varchar || ':' || $1:receptor_residue_index::varchar as receptor_residue_id,
    $1:distance::double as distance_angstrom,
    $1:both_selected_q1::boolean as both_selected_q1
from {{ geometry_file('pairs') }}
