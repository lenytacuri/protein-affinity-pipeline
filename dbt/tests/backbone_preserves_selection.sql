{{ config(tags=['backbone']) }}
select coalesce(r.residue_id,b.residue_id) as residue_id
from (select * from {{ ref('silver_interface_residues') }} where selected_q1) r
full outer join {{ ref('backbone_residues') }} b using(residue_id)
where r.residue_id is null or b.residue_id is null or r.geometry_id<>b.geometry_id
 or r.partner<>b.partner or r.chain_id<>b.chain_id or r.residue_number<>b.residue_number
 or r.insertion_code<>b.insertion_code or r.altloc<>b.altloc
 or abs(r.x-b.atoms:ca:xyz[0]::double)>1e-6
 or abs(r.y-b.atoms:ca:xyz[1]::double)>1e-6
 or abs(r.z-b.atoms:ca:xyz[2]::double)>1e-6
