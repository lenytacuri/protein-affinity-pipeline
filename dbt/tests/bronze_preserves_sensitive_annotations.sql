-- Evita perder temperatura supuesta, referencia pendiente o la anotacion de mutacion.
select b.observation_id
from {{ ref('bronze_affinity_observations') }} b
join {{ source('raw','source_records') }} r on b.observation_id=r.record_id
where not equal_null(b.temperature_raw,strip_null_value(r.raw_record:payload:"Temperature(K)")::varchar)
   or not equal_null(b.affinity_reference_raw,strip_null_value(r.raw_record:payload:"Affinity PubMed ID")::varchar)
   or not equal_null(b.mutations_raw,strip_null_value(r.raw_record:payload:"Mutations")::varchar)
   or not equal_null(b.ligand_chains_raw,strip_null_value(r.raw_record:payload:"Ligand Chains")::varchar)
   or not equal_null(b.receptor_chains_raw,strip_null_value(r.raw_record:payload:"Receptor Chains")::varchar)
