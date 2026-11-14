select r.residue_id
from {{ ref('silver_interface_residues') }} r
join {{ ref('silver_interface_residues') }} n on r.nearest_residue_id=n.residue_id
where r.partner=n.partner or r.geometry_id<>n.geometry_id
or abs(sqrt(power(r.x-n.x,2)+power(r.y-n.y,2)+power(r.z-n.z,2))-r.min_distance_angstrom)>1e-7
