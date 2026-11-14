{{ config(tags=['chemistry']) }}
with expected as (
 select geometry_id,s.column1::varchar as partner,
 case when s.column1='L' then n_selected_q1_ligand else n_selected_q1_receptor end as n
 from {{ ref('silver_structure_geometry') }} cross join (values ('L'),('R')) s
)
select coalesce(e.geometry_id,c.geometry_id) as geometry_id
from expected e full outer join {{ ref('silver_interface_chemistry') }} c using(geometry_id,partner)
where e.geometry_id is null or c.geometry_id is null or not equal_null(e.n,c.n_selected)
