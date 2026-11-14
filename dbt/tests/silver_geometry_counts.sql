with r as (
    select geometry_id,count_if(partner='L') as nl,count_if(partner='R') as nr,
        count_if(partner='L' and selected_q1) as ql,count_if(partner='R' and selected_q1) as qr,
        min(min_distance_angstrom) as minimum
    from {{ ref('silver_interface_residues') }} group by 1
), p as (
    select geometry_id,count(*) as n,count_if(distance_angstrom<10) as n10
    from {{ ref('silver_residue_pairs') }} group by 1
)
select g.geometry_id
from {{ ref('silver_structure_geometry') }} g left join r using(geometry_id) left join p using(geometry_id)
where g.geometry_status='computed' and (
    g.n_ligand<>coalesce(r.nl,0) or g.n_receptor<>coalesce(r.nr,0)
    or g.n_selected_q1_ligand<>coalesce(r.ql,0) or g.n_selected_q1_receptor<>coalesce(r.qr,0)
    or g.selected_pair_count<>coalesce(p.n,0) or g.selected_pairs_lt10<>coalesce(p.n10,0)
    or g.selected_pair_count<>r.ql*r.qr
    or g.has_ca_contacts_10<>(r.minimum<10))
