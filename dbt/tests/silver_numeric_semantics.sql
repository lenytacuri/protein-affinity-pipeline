select observation_id
from {{ ref('silver_affinity_observations') }}
where (kd_status='valid' and (pkd is null or abs(power(10,-pkd)/kd_m-1)>1e-10))
   or (kd_status<>'valid' and pkd is not null)
   or (temperature_status='assumed' and (not temperature_assumed or temperature_k is null))
   or (temperature_raw is null and (temperature_k is not null or temperature_status<>'missing'))
