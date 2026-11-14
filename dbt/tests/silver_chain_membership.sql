select r.residue_id
from {{ ref('silver_interface_residues') }} r join {{ ref('silver_structure_geometry') }} g using(geometry_id)
where not array_contains(r.chain_id::variant,case when r.partner='L' then g.ligand_chains else g.receptor_chains end)
