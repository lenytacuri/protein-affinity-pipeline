{{ config(alias='BACKBONE_RESIDUES') }}
select
 {% for name in ['residue_id','geometry_id','partner','chain_id','insertion_code','residue_name','altloc','structure_sha256','backbone_version','backbone_code_sha256','previous_link_status','next_link_status','phi_status','psi_status','omega_status','tau_status'] %}
 $1:{{name}}::varchar as {{name}},
 {% endfor %}
 $1:residue_number::integer as residue_number,
 {% for name in ['phi_deg','psi_deg','omega_deg','tau_deg','n_ca_length','ca_c_length','peptide_cn_length'] %}
 strip_null_value($1:{{name}})::number(18,8) as {{name}},
 {% endfor %}
 $1:previous_residue as previous_residue,
 $1:next_residue as next_residue,
 $1:atoms as atoms
from {{ backbone_file() }}
