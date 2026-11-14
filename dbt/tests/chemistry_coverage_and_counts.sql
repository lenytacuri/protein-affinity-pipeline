{{ config(tags=['chemistry']) }}
{% set aas='ACDEFGHIKLMNPQRSTVWY' %}
select chemistry_id from {{ ref('silver_interface_chemistry') }}
where (geometry_status<>'computed' and (n_selected is not null or n_supported is not null or chemistry_status<>'geometry_unavailable'))
   or (geometry_status='computed' and (n_selected is null or n_selected<0 or n_supported<0
       or n_supported+n_unsupported<>n_selected or n_nonstandard>n_unsupported))
   or (n_supported>0 and (abs(({% for aa in aas %}fraction_aa_{{aa|lower}}{% if not loop.last %}+{% endif %}{% endfor %})-1)>1e-10
       or mean_kd_hydropathy not between -4.5 and 4.5 or aa_entropy_bits not between -1e-10 and 4.321928094887363))
   or (n_supported=0 and (mean_kd_hydropathy is not null or aa_entropy_bits is not null or fraction_aa_a is not null))
   or (n_selected=0 and (property_coverage is not null or chemistry_status<>'empty_selection'))
   or abs(n_supported::double/nullif(n_selected,0)-property_coverage)>1e-10
   or n_supported<>({% for aa in aas %}n_aa_{{aa|lower}}{% if not loop.last %}+{% endif %}{% endfor %})
   or n_supported<>n_nonpolar+n_polar_uncharged+n_acidic+n_basic
