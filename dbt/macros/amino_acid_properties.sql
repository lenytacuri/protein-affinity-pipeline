{% macro amino_acid_properties() -%}
-- chemistry_v1: categories are explicit conventions, not measured charge states.
-- Hydropathy: Kyte & Doolittle (1982), https://web.expasy.org/protscale/pscale/Hydropath.Doolittle.html
select column1::varchar as aa, column2::varchar as residue_name,
       column3::varchar as side_chain_class, column4::number(4,1) as kd_hydropathy
from values
 ('A','ALA','nonpolar',1.8), ('C','CYS','polar_uncharged',2.5),
 ('D','ASP','acidic',-3.5), ('E','GLU','acidic',-3.5),
 ('F','PHE','nonpolar',2.8), ('G','GLY','nonpolar',-0.4),
 ('H','HIS','basic',-3.2), ('I','ILE','nonpolar',4.5),
 ('K','LYS','basic',-3.9), ('L','LEU','nonpolar',3.8),
 ('M','MET','nonpolar',1.9), ('N','ASN','polar_uncharged',-3.5),
 ('P','PRO','nonpolar',-1.6), ('Q','GLN','polar_uncharged',-3.5),
 ('R','ARG','basic',-4.5), ('S','SER','polar_uncharged',-0.8),
 ('T','THR','polar_uncharged',-0.7), ('V','VAL','nonpolar',4.2),
 ('W','TRP','nonpolar',-0.9), ('Y','TYR','polar_uncharged',-1.3)
{%- endmacro %}
