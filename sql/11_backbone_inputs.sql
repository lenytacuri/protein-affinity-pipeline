-- Only selected Q1 residues, identified exactly as in existing Silver.
with selected as (
 select geometry_id,array_agg(object_construct_keep_null(
   'residue_id',residue_id,'geometry_id',geometry_id,'partner',partner,'chain_id',chain_id,
   'residue_number',residue_number,'insertion_code',insertion_code,'residue_name',residue_name,
   'altloc',altloc,'x',x,'y',y,'z',z)) within group(order by residue_index) as residues
 from PROTEIN_AFFINITY.SILVER.INTERFACE_RESIDUES where selected_q1 group by geometry_id
)
select g.geometry_id,g.pdb_id,g.structure_sha256,s.residues
from PROTEIN_AFFINITY.SILVER.STRUCTURE_GEOMETRY g join selected s using(geometry_id)
where g.geometry_status='computed' order by g.geometry_id
