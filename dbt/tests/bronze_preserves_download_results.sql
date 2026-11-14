-- Los seis 404 son filas validas del manifiesto y deben llegar a Bronze.
select coalesce(r.batch_id,b.batch_id) as batch_id, coalesce(r.pdb_id,b.pdb_id) as pdb_id
from {{ source('raw','batch_resources') }} r
full outer join {{ ref('bronze_resource_receipts') }} b
    on r.batch_id=b.batch_id and r.pdb_id=b.pdb_id and r.resource=b.resource
where r.batch_id is null or b.batch_id is null or not equal_null(r.receipt,b.receipt)
