select coalesce(r.content_sha256,b.metadata_sha256) as mismatched_hash
from {{ source('raw','rcsb_entries') }} r
full outer join {{ ref('bronze_structure_metadata') }} b on r.content_sha256=b.metadata_sha256
where r.content_sha256 is null or b.metadata_sha256 is null
   or not equal_null(r.payload,b.payload)
