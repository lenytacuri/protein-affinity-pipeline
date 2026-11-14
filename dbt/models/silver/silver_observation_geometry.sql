{{ config(alias='OBSERVATION_GEOMETRY') }}
-- Una fila por observacion, incluso si no pudo asignarse una estructura.
select
    $1:observation_id::varchar as observation_id,
    $1:pdb_id::varchar as pdb_id,
    strip_null_value($1:geometry_id)::varchar as geometry_id,
    $1:mapping_status::varchar as mapping_status,
    $1:structure_versions::integer as structure_versions,
    $1:mutation_check:status::varchar as mutation_structure_status,
    $1:mutation_check:items::array as mutation_details
from {{ geometry_file('observations') }}
