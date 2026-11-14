{{ config(alias='AFFINITY_OBSERVATIONS') }}
-- Conserva todas las observaciones y los originales heredados de Bronze.
with interpreted as (
    select b.*,
        case when kd_m>0 and kd_m<'inf'::double then -log(10,kd_m) end as pkd,
        case when kd_m is null then 'missing_or_unparsed'
             when kd_m>0 and kd_m<'inf'::double then 'valid' else 'invalid' end as kd_status,
        case when regexp_like(lower(trim(temperature_raw)), '[0-9]+([.][0-9]+)?([ ]*[(]assumed[)])?')
             then try_to_double(regexp_substr(temperature_raw,'[0-9]+([.][0-9]+)?')) end as temperature_k,
        coalesce(temperature_raw ilike '%assumed%',false) as temperature_assumed,
        case when lower(trim(affinity_method_raw)) in ('unknown','n/a','na','none','null','') then null
             else trim(affinity_method_raw) end as affinity_method,
        case when affinity_reference_raw is null or trim(affinity_reference_raw)='' then 'missing'
             when upper(trim(affinity_reference_raw))='TBD' then 'placeholder'
             when regexp_like(trim(affinity_reference_raw),'[0-9]+') then 'pmid' else 'text_reference' end as affinity_reference_status,
        case when regexp_like(trim(affinity_reference_raw),'[0-9]+') then try_to_number(trim(affinity_reference_raw)) end as affinity_pmid
    from {{ ref('bronze_affinity_observations') }} b
)
select i.*,
    case when temperature_raw is null then 'missing'
         when temperature_k is null then 'unparsed'
         when temperature_k<=0 then 'invalid'
         when temperature_assumed then 'assumed' else 'reported' end as temperature_status,
    g.geometry_id,
    g.structure_versions,
    g.mutation_structure_status,
    coalesce(s.geometry_status,g.mapping_status,'mapping_missing') as geometry_status,
    s.issue as geometry_issue,
    s.has_ca_contacts_10,
    s.biological_assembly_validated,
    case when g.mutation_structure_status='reference_geometry_only' then true
         when g.mutation_structure_status='target_residues_present' then false end as uses_reference_for_mutation
from interpreted i
left join {{ ref('silver_observation_geometry') }} g on i.observation_id=g.observation_id
left join {{ ref('silver_structure_geometry') }} s on g.geometry_id=s.geometry_id
