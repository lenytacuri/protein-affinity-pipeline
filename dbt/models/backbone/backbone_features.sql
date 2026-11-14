{{ config(alias='BACKBONE_FEATURES') }}
{% set angles=['phi','psi','omega'] %}
{% set linear=['tau_deg','n_ca_length','ca_c_length','peptide_cn_length'] %}
with participants as (
 select g.geometry_id,g.pdb_id,g.geometry_status,s.column1::varchar as partner,
        case when s.column1='L' then g.n_selected_q1_ligand else g.n_selected_q1_receptor end as n_selected
 from {{ ref('silver_structure_geometry') }} g cross join (values ('L'),('R')) s
), aggregated as (
 select geometry_id,partner,count(*) as n_measured_rows,
        count_if(phi_deg is not null and psi_deg is not null) as n_phi_psi_complete,
        {% for angle in angles %}
        count({{angle}}_deg) as n_{{angle}},
        avg(round(sin(radians({{angle}}_deg)),12)::number(18,12))::number(18,12) as {{angle}}_mean_sin,
        avg(round(cos(radians({{angle}}_deg)),12)::number(18,12))::number(18,12) as {{angle}}_mean_cos,
        {% endfor %}
        {% for name in linear %}
        count({{name}}) as n_{{name}},
        avg({{name}})::number(18,8) as {{name}}_mean{% if not loop.last %},{% endif %}
        {% endfor %}
 from {{ ref('backbone_residues') }} group by geometry_id,partner
), deviations as (
 select r.geometry_id,r.partner,
        {% for name in linear %}
        round(sqrt(avg(((r.{{name}}-a.{{name}}_mean)*(r.{{name}}-a.{{name}}_mean))::number(30,16))),8)::number(18,8) as {{name}}_std_pop{% if not loop.last %},{% endif %}
        {% endfor %}
 from {{ ref('backbone_residues') }} r join aggregated a using(geometry_id,partner)
 group by r.geometry_id,r.partner
), metrics as (
 select p.*,
        iff(p.geometry_status='computed',coalesce(a.n_measured_rows,0),null) as n_measured_rows,
        iff(p.geometry_status='computed',coalesce(a.n_phi_psi_complete,0),null) as n_phi_psi_complete,
        {% for angle in angles %}
        iff(p.geometry_status='computed',coalesce(a.n_{{angle}},0),null) as n_{{angle}},
        a.{{angle}}_mean_sin,a.{{angle}}_mean_cos,
        least(1.0,sqrt(a.{{angle}}_mean_sin*a.{{angle}}_mean_sin+a.{{angle}}_mean_cos*a.{{angle}}_mean_cos))::number(18,12) as {{angle}}_resultant_length,
        {% endfor %}
        {% for name in linear %}
        iff(p.geometry_status='computed',coalesce(a.n_{{name}},0),null) as n_{{name}},
        a.{{name}}_mean,d.{{name}}_std_pop{% if not loop.last %},{% endif %}
        {% endfor %}
 from participants p left join aggregated a using(geometry_id,partner)
 left join deviations d using(geometry_id,partner)
)
select geometry_id || ':' || partner as backbone_feature_id,
       'backbone_v1'::varchar as feature_version,
       'observed_structure_q1'::varchar as feature_basis,
       metrics.*,
       case when geometry_status<>'computed' then 'geometry_unavailable'
            when n_selected=0 then 'empty_selection'
            when n_phi+n_psi+n_omega+n_tau_deg=0 then 'no_valid_angles'
            when least(n_phi,n_psi,n_omega,n_tau_deg)<n_selected then 'partial_angles'
            else 'complete' end as backbone_status,
       n_phi_psi_complete::double/nullif(n_selected,0) as fraction_phi_psi_complete,
       {% for angle in angles %}
       n_{{angle}}::double/nullif(n_selected,0) as {{angle}}_coverage,
       case when {{angle}}_resultant_length>1e-8 then round(degrees(atan2({{angle}}_mean_sin,{{angle}}_mean_cos)),8)::number(18,8) end as {{angle}}_circular_mean_deg,
       1-{{angle}}_resultant_length as {{angle}}_circular_variance,
       {% endfor %}
       {% for name in linear %}
       n_{{name}}::double/nullif(n_selected,0) as {{name}}_coverage{% if not loop.last %},{% endif %}
       {% endfor %}
from metrics
