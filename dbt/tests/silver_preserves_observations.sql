select coalesce(b.observation_id,s.observation_id) as id
from {{ ref('bronze_affinity_observations') }} b
full outer join {{ ref('silver_affinity_observations') }} s on b.observation_id=s.observation_id
where b.observation_id is null or s.observation_id is null
or not equal_null(b.payload,s.payload) or not equal_null(b.source_sha256,s.source_sha256)
