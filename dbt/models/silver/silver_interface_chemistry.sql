{{ config(alias='INTERFACE_CHEMISTRY', tags=['chemistry']) }}
{% set amino_acids = 'ACDEFGHIKLMNPQRSTVWY' %}
{% set groups = {
 'nonpolar': "p.side_chain_class='nonpolar'",
 'polar_uncharged': "p.side_chain_class='polar_uncharged'",
 'acidic': "p.side_chain_class='acidic'",
 'basic': "p.side_chain_class='basic'",
 'aromatic_ring': "p.aa in ('F','W','Y','H')",
 'sulfur_containing': "p.aa in ('C','M')",
 'aliphatic_avil': "p.aa in ('A','V','I','L')"
} %}
-- One row for each geometry/participant, including failed and empty selections.
with properties as (
    {{ amino_acid_properties() }}
), participants as (
    select g.geometry_id,g.pdb_id,g.geometry_status,s.column1::varchar as partner,
           case when s.column1='L' then g.q1_ligand_angstrom else g.q1_receptor_angstrom end as q1_threshold_angstrom
    from {{ ref('silver_structure_geometry') }} g cross join (values ('L'),('R')) s
), aggregate_features as (
    select r.geometry_id,r.partner,count(*) as n_selected,
           count(p.aa) as n_supported,
           sum(iff(not r.is_standard,1,0)) as n_nonstandard,
           sum(iff(p.aa is null,1,0)) as n_unsupported,
           avg(p.kd_hydropathy)::number(12,6) as mean_kd_hydropathy,
           {% for aa in amino_acids %}
           sum(iff(p.aa='{{ aa }}',1,0)) as n_aa_{{ aa|lower }},
           {% endfor %}
           {% for label,condition in groups.items() %}
           sum(iff({{ condition }},1,0)) as n_{{ label }}{% if not loop.last %},{% endif %}
           {% endfor %}
    from {{ ref('silver_interface_residues') }} r
    left join properties p on r.is_standard and r.residue_name=p.residue_name and r.amino_acid=p.aa
    where r.selected_q1
    group by r.geometry_id,r.partner
), aa_distribution as (
    select r.geometry_id,r.partner,p.aa,count(*) as n
    from {{ ref('silver_interface_residues') }} r
    join properties p on r.is_standard and r.residue_name=p.residue_name and r.amino_acid=p.aa
    where r.selected_q1 group by 1,2,3
), entropy as (
    select d.geometry_id,d.partner,
           -sum(round((d.n::double/a.n_supported)*log(2,d.n::double/a.n_supported),12)::number(20,12)) as aa_entropy_bits
    from aa_distribution d join aggregate_features a using(geometry_id,partner)
    group by 1,2
), filled as (
    select t.*,
           case when t.geometry_status<>'computed' then 'geometry_unavailable'
                when coalesce(a.n_selected,0)=0 then 'empty_selection'
                when a.n_supported=0 then 'no_supported_residues'
                when a.n_supported<a.n_selected then 'partial_coverage' else 'complete' end as chemistry_status,
           {% for name in ['selected','supported','nonstandard','unsupported'] %}
           iff(t.geometry_status='computed',coalesce(a.n_{{ name }},0),null) as n_{{ name }},
           {% endfor %}
           a.mean_kd_hydropathy,e.aa_entropy_bits,
           {% for aa in amino_acids %}
           iff(t.geometry_status='computed',coalesce(a.n_aa_{{ aa|lower }},0),null) as n_aa_{{ aa|lower }},
           {% endfor %}
           {% for label in groups %}
           iff(t.geometry_status='computed',coalesce(a.n_{{ label }},0),null) as n_{{ label }}{% if not loop.last %},{% endif %}
           {% endfor %}
    from participants t left join aggregate_features a using(geometry_id,partner)
    left join entropy e using(geometry_id,partner)
)
select geometry_id || ':' || partner as chemistry_id,
       'chemistry_v1'::varchar as feature_version,
       'observed_structure_q1'::varchar as feature_basis,
       filled.*,
       n_supported::double/nullif(n_selected,0) as property_coverage,
       {% for aa in amino_acids %}
       n_aa_{{ aa|lower }}::double/nullif(n_supported,0) as fraction_aa_{{ aa|lower }},
       {% endfor %}
       {% for label in groups %}
       n_{{ label }}::double/nullif(n_supported,0) as fraction_{{ label }}{% if not loop.last %},{% endif %}
       {% endfor %}
from filled
