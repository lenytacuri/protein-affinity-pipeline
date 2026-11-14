{{ config(alias='RESOURCE_RECEIPTS') }}

-- Un resultado por lote + PDB + recurso. LEFT JOIN mantiene tambien los 404.
select
    r.batch_id,
    b.source_sha256,
    r.pdb_id,
    r.resource,
    r.receipt:status::varchar as download_status,
    try_to_number(r.receipt:http_status::varchar) as http_status,
    strip_null_value(r.receipt:sha256)::varchar as content_sha256,
    strip_null_value(r.receipt:source_url)::varchar as source_url,
    strip_null_value(r.receipt:retrieved_at)::varchar as retrieved_at_raw,
    strip_null_value(r.receipt:checked_at)::varchar as checked_at_raw,
    f.stage_path,
    f.byte_count,
    r.receipt,
    r.loaded_at as raw_loaded_at
from {{ source('raw', 'batch_resources') }} r
left join {{ source('raw', 'ingestion_batches') }} b on r.batch_id = b.batch_id
left join {{ source('raw', 'resource_files') }} f on r.receipt:sha256::varchar = f.content_sha256
