{{ config(tags=['backbone']) }}
select residue_id from {{ ref('backbone_residues') }} where
{% for field,a,b in [('n_ca_length','n','ca'),('ca_c_length','ca','c'),('peptide_cn_length','c','next_n')] %}
 ({{field}} is not null and abs({{field}}-sqrt(
 power(atoms:{{a}}:xyz[0]::double-atoms:{{b}}:xyz[0]::double,2)+
 power(atoms:{{a}}:xyz[1]::double-atoms:{{b}}:xyz[1]::double,2)+
 power(atoms:{{a}}:xyz[2]::double-atoms:{{b}}:xyz[2]::double,2)))>1e-6){% if not loop.last %} or{% endif %}
{% endfor %}
