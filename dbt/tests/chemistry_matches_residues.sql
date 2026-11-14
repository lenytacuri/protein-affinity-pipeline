{{ config(tags=['chemistry']) }}
-- Independent recount directly from canonical residue names (no property macro).
with actual as (
 select geometry_id,partner,count(*) as n_selected,
 sum(iff(is_standard and residue_name in ('ALA','CYS','ASP','GLU','PHE','GLY','HIS','ILE','LYS','LEU','MET','ASN','PRO','GLN','ARG','SER','THR','VAL','TRP','TYR'),1,0)) as n_supported,
 sum(iff(is_standard and residue_name in ('ASP','GLU'),1,0)) as n_acidic,
 sum(iff(is_standard and residue_name in ('LYS','ARG','HIS'),1,0)) as n_basic,
 sum(iff(is_standard and residue_name in ('CYS','MET'),1,0)) as n_sulfur
 from {{ ref('silver_interface_residues') }} where selected_q1 group by 1,2
)
select c.chemistry_id from {{ ref('silver_interface_chemistry') }} c
join actual a using(geometry_id,partner)
where c.n_selected<>a.n_selected or c.n_supported<>a.n_supported
or c.n_acidic<>a.n_acidic or c.n_basic<>a.n_basic or c.n_sulfur_containing<>a.n_sulfur
