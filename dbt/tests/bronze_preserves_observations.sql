-- Debe conservar cada observacion y su contenido original, incluso con campos nulos.
select coalesce(r.record_id,b.observation_id) as mismatched_id
from (select * from {{ source('raw','source_records') }} where input_kind='measurement_table') r
full outer join {{ ref('bronze_affinity_observations') }} b on r.record_id=b.observation_id
where r.record_id is null or b.observation_id is null
   or not equal_null(r.raw_record:payload,b.payload)
   or not equal_null(r.source_sha256,b.source_sha256)
   or not equal_null(r.raw_record:source_row::integer,b.source_row)
   or not equal_null(r.loaded_at,b.raw_loaded_at)
