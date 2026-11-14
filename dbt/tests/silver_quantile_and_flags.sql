with thresholds as (
    select geometry_id,partner,percentile_cont(0.25) within group(order by min_distance_angstrom) as q
    from {{ ref('silver_interface_residues') }} group by 1,2
)
select r.residue_id
from {{ ref('silver_interface_residues') }} r join thresholds t using(geometry_id,partner)
where abs(r.q1_threshold_angstrom-t.q)>1e-8
   or r.selected_q1<>(r.min_distance_angstrom<r.q1_threshold_angstrom)
   or r.within_10<>(r.min_distance_angstrom<10)
   or r.min_distance_angstrom<0 or r.occupancy<=0
