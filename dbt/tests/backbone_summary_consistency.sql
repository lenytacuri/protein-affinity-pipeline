{{ config(tags=['backbone']) }}
with r as (
 select geometry_id,partner,count(*) as n,count(phi_deg) as np,count(psi_deg) as nq,count(omega_deg) as no,
 count_if(phi_deg is not null and psi_deg is not null) as nb
 from {{ ref('backbone_residues') }} group by 1,2
)
select f.backbone_feature_id from {{ ref('backbone_features') }} f left join r using(geometry_id,partner)
where (geometry_status='computed' and (n_selected<>coalesce(r.n,0) or n_measured_rows<>n_selected
 or n_phi<>coalesce(r.np,0) or n_psi<>coalesce(r.nq,0) or n_omega<>coalesce(r.no,0) or n_phi_psi_complete<>coalesce(r.nb,0)))
 or (geometry_status<>'computed' and (n_selected is not null or n_phi is not null or backbone_status<>'geometry_unavailable'))
{% for a in ['phi','psi','omega'] %}
 or {{a}}_coverage not between 0 and 1 or {{a}}_resultant_length not between 0 and 1
 or {{a}}_circular_variance not between 0 and 1
 or (n_{{a}}=0 and ({{a}}_mean_sin is not null or {{a}}_mean_cos is not null))
 or ({{a}}_resultant_length<=1e-8 and {{a}}_circular_mean_deg is not null)
{% endfor %}
