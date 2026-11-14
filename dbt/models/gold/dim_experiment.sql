{{ config(alias='DIM_EXPERIMENT') }}
-- DISTINCT groups context values; it never removes experimental observations.
select distinct {{ gold_key(gold_experiment_columns()) }} as experiment_key,
       affinity_method, affinity_method_raw, temperature_k, temperature_raw, temperature_status, temperature_assumed, affinity_reference_raw, affinity_reference_status, affinity_pmid, affinity_release_date_raw
from {{ ref('silver_affinity_observations') }}
