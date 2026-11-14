{{ config(alias='AFFINITY_OBSERVATIONS') }}

-- Una fila por observacion original. Sin DISTINCT, agrupaciones ni deduplicacion.
-- NULL JSON se representa como NULL SQL. PAYLOAD conserva los valores originales.
-- Las listas de cadenas, mutaciones, temperaturas y fechas siguen como texto.
with source_rows as (
    select * from {{ source('raw', 'source_records') }}
    where input_kind = 'measurement_table'
), projected as (
    select
        record_id as observation_id,
        source_sha256,
        raw_record:source_file::varchar as source_file,
        raw_record:sheet::varchar as source_sheet,
        raw_record:source_row::integer as source_row,
        loaded_at as raw_loaded_at,
        pdb_id,
        raw_record:payload as payload,
        strip_null_value(raw_record:payload:"_unnamed_0")::varchar as source_index_raw,
        strip_null_value(raw_record:payload:"Source Data Set")::varchar as source_dataset,
        strip_null_value(raw_record:payload:"Complex ID")::varchar as complex_id,
        strip_null_value(raw_record:payload:"PDB")::varchar as pdb_id_raw,
        strip_null_value(raw_record:payload:"Mutations")::varchar as mutations_raw,
        strip_null_value(raw_record:payload:"Ligand Chains")::varchar as ligand_chains_raw,
        strip_null_value(raw_record:payload:"Receptor Chains")::varchar as receptor_chains_raw,
        strip_null_value(raw_record:payload:"Ligand Name")::varchar as ligand_name,
        strip_null_value(raw_record:payload:"Receptor Name")::varchar as receptor_name,
        strip_null_value(raw_record:payload:"KD(M)")::varchar as kd_m_raw,
        strip_null_value(raw_record:payload:"Affinity Method")::varchar as affinity_method_raw,
        strip_null_value(raw_record:payload:"Structure Method")::varchar as structure_method_raw,
        strip_null_value(raw_record:payload:"Temperature(K)")::varchar as temperature_raw,
        strip_null_value(raw_record:payload:"Resolution(Å)")::varchar as resolution_angstrom_raw,
        strip_null_value(raw_record:payload:"PDB PubMed ID")::varchar as structure_reference_raw,
        strip_null_value(raw_record:payload:"PDB Release Date")::varchar as structure_release_date_raw,
        strip_null_value(raw_record:payload:"Affinity PubMed ID")::varchar as affinity_reference_raw,
        strip_null_value(raw_record:payload:"Affinity Release Date")::varchar as affinity_release_date_raw,
        strip_null_value(raw_record:payload:"Subgroup")::varchar as subgroup_raw
    from source_rows
)
select *,
    try_to_double(kd_m_raw) as kd_m,
    try_to_double(resolution_angstrom_raw) as resolution_angstrom
from projected
