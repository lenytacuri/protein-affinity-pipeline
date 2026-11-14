{{ config(tags=['backbone']) }}
select residue_id from {{ ref('backbone_residues') }} where
{% for angle in ['phi','psi','omega','tau'] %}
 ({{angle}}_deg is not null and ({{angle}}_status<>'ok' or {{angle}}_deg not between {% if angle=='tau' %}0{% else %}-180{% endif %} and 180))
 or ({{angle}}_deg is null and {{angle}}_status='ok') or
{% endfor %}
 (phi_deg is not null and previous_link_status not in ('connected','connected_author_inferred'))
 or ((psi_deg is not null or omega_deg is not null or peptide_cn_length is not null) and next_link_status not in ('connected','connected_author_inferred'))
 or (peptide_cn_length is not null and peptide_cn_length not between 0.8 and 1.8)
 or n_ca_length<=0 or ca_c_length<=0
