{{ config(alias='STRUCTURE_METADATA') }}

-- Una version de JSON por hash. No elegimos ni fusionamos versiones aqui.
select
    content_sha256 as metadata_sha256,
    pdb_id,
    strip_null_value(payload:struct:title)::varchar as structure_title,
    strip_null_value(payload:exptl[0]:method)::varchar as experimental_method,
    try_to_double(strip_null_value(payload:rcsb_entry_info:resolution_combined[0])::varchar) as resolution_angstrom,
    try_to_number(strip_null_value(payload:rcsb_entry_info:polymer_entity_count_protein)::varchar) as protein_entity_count,
    try_to_number(strip_null_value(payload:rcsb_entry_info:deposited_polymer_entity_instance_count)::varchar) as polymer_chain_count,
    strip_null_value(payload:rcsb_accession_info:initial_release_date)::varchar as initial_release_date_raw,
    strip_null_value(payload:rcsb_accession_info:revision_date)::varchar as revision_date_raw,
    strip_null_value(payload:rcsb_primary_citation:pdbx_database_id_PubMed)::varchar as structure_reference_raw,
    payload,
    loaded_at as raw_loaded_at
from {{ source('raw', 'rcsb_entries') }}
