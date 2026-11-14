select batch_id,pdb_id,resource
from {{ ref('bronze_resource_receipts') }}
where download_status in ('cached','downloaded')
  and (content_sha256 is null or stage_path is null or byte_count is null or byte_count<=0)
