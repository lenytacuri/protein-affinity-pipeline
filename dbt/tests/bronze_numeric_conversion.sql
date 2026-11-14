-- Una afinidad o resolucion numerica de origen no debe perderse al tiparla.
-- Los valores de texto no numericos se conservan en *_RAW para decidir en Silver.
select observation_id
from {{ ref('bronze_affinity_observations') }}
where (typeof(payload:"KD(M)") in ('INTEGER','DECIMAL','DOUBLE') and kd_m is null)
   or (typeof(payload:"Resolution(Å)") in ('INTEGER','DECIMAL','DOUBLE') and resolution_angstrom is null)
