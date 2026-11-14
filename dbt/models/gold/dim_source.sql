{{ config(alias='DIM_SOURCE') }}
-- DISTINCT groups context values; it never removes experimental observations.
select distinct {{ gold_key(gold_source_columns()) }} as source_key,
       source_sha256, source_file, source_sheet, source_dataset
from {{ ref('silver_affinity_observations') }}
