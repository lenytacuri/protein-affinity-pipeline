{{ config(tags=['backbone']) }}
with p as (
 select geometry_id,s.column1::varchar as partner from {{ ref('silver_structure_geometry') }} cross join (values ('L'),('R')) s
)
select coalesce(p.geometry_id,f.geometry_id) as geometry_id from p
full outer join {{ ref('backbone_features') }} f using(geometry_id,partner)
where p.geometry_id is null or f.geometry_id is null
