{{ config(alias='INTERFACE_RESIDUES') }}
-- Todos los CA utilizables; SELECTED_Q1 distingue la seleccion adaptativa.
select
    $1:geometry_id::varchar || ':' || $1:residue_index::varchar as residue_id,
    $1:geometry_id::varchar as geometry_id,
    $1:residue_index::integer as residue_index,
    $1:partner::varchar as partner,
    $1:chain_id::varchar as chain_id,
    $1:residue_number::integer as residue_number,
    $1:insertion_code::varchar as insertion_code,
    $1:residue_name::varchar as residue_name,
    $1:amino_acid::varchar as amino_acid,
    $1:is_standard::boolean as is_standard,
    $1:altloc::varchar as altloc,
    $1:occupancy::double as occupancy,
    $1:x::double as x,
    $1:y::double as y,
    $1:z::double as z,
    $1:min_distance::double as min_distance_angstrom,
    $1:geometry_id::varchar || ':' || $1:nearest_residue_index::varchar as nearest_residue_id,
    $1:q1_threshold::double as q1_threshold_angstrom,
    $1:selected_q1::boolean as selected_q1,
    $1:within_10::boolean as within_10
from {{ geometry_file('residues') }}
