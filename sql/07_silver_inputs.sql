-- Una estructura disponible por version de fuente y PDB. No multiplica observaciones.
-- Si en el futuro hay varias versiones estructurales, se elige la ultima y se informa.
with structures as (
    select source_sha256, pdb_id, content_sha256, stage_path,
        count(distinct content_sha256) over (partition by source_sha256,pdb_id) as structure_versions,
        row_number() over (partition by source_sha256,pdb_id order by raw_loaded_at desc,batch_id desc) as rn
    from PROTEIN_AFFINITY.BRONZE.RESOURCE_RECEIPTS
    where resource='structure' and download_status in ('downloaded','cached')
)
select o.observation_id,o.pdb_id,o.source_sha256,o.ligand_chains_raw,o.receptor_chains_raw,
       o.mutations_raw,s.content_sha256 as structure_sha256,s.stage_path,s.structure_versions
from PROTEIN_AFFINITY.BRONZE.AFFINITY_OBSERVATIONS o
left join structures s on o.source_sha256=s.source_sha256 and o.pdb_id=s.pdb_id and s.rn=1
order by o.observation_id
