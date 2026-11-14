{{ config(tags=['backbone']) }}
with expected as (
 select geometry_id,partner,
 {% for a in ['phi','psi','omega'] %}
 avg(sin(radians({{a}}_deg))) as {{a}}_s,avg(cos(radians({{a}}_deg))) as {{a}}_c,
 {% endfor %}
 {% for n in ['tau_deg','n_ca_length','ca_c_length','peptide_cn_length'] %}
 avg({{n}}) as {{n}}_m,stddev_pop({{n}}) as {{n}}_sd{% if not loop.last %},{% endif %}
 {% endfor %}
 from {{ ref('backbone_residues') }} group by 1,2
)
select f.backbone_feature_id from {{ ref('backbone_features') }} f join expected e using(geometry_id,partner)
where
{% for a in ['phi','psi','omega'] %}
 abs(f.{{a}}_mean_sin-e.{{a}}_s)>1e-9 or abs(f.{{a}}_mean_cos-e.{{a}}_c)>1e-9 or
{% endfor %}
{% for n in ['tau_deg','n_ca_length','ca_c_length','peptide_cn_length'] %}
 abs(f.{{n}}_mean-e.{{n}}_m)>1e-6 or abs(f.{{n}}_std_pop-e.{{n}}_sd)>1e-6{% if not loop.last %} or{% endif %}
{% endfor %}
