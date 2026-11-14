select p.pair_id
from {{ ref('silver_residue_pairs') }} p
join {{ ref('silver_interface_residues') }} l on p.ligand_residue_id=l.residue_id
join {{ ref('silver_interface_residues') }} r on p.receptor_residue_id=r.residue_id
where l.partner<>'L' or r.partner<>'R' or l.geometry_id<>p.geometry_id or r.geometry_id<>p.geometry_id
   or p.distance_angstrom<0 or not p.both_selected_q1
   or abs(sqrt(power(l.x-r.x,2)+power(l.y-r.y,2)+power(l.z-r.z,2))-p.distance_angstrom)>1e-7
   or p.both_selected_q1<>(l.selected_q1 and r.selected_q1)
