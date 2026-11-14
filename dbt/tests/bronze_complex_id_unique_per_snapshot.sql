-- Regla del paper. Un mismo Complex ID puede aparecer en versiones distintas del Excel.
select source_sha256,complex_id,count(*) as n
from {{ ref('bronze_affinity_observations') }}
group by source_sha256,complex_id having count(*)>1
