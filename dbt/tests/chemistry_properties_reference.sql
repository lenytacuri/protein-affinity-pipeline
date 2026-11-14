{{ config(tags=['chemistry']) }}
-- depends_on: {{ ref('silver_interface_chemistry') }}
-- Known scale anchors and cardinality protect the property lookup.
with p as ({{ amino_acid_properties() }})
select 'invalid_reference' as issue from p
having count(*)<>20 or count(distinct aa)<>20 or count(distinct residue_name)<>20
or max(iff(aa='I',kd_hydropathy,null))<>4.5
or max(iff(aa='R',kd_hydropathy,null))<>-4.5
or max(iff(aa='Y',kd_hydropathy,null))<>-1.3
or max(iff(aa='C',kd_hydropathy,null))<>2.5
or max(iff(aa='H',kd_hydropathy,null))<>-3.2
