select batch_id,pdb_id,resource,count(*) as n
from {{ ref('bronze_resource_receipts') }}
group by batch_id,pdb_id,resource having count(*)>1
