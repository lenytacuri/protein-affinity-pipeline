{{ config(alias='FACT_AFFINITY') }}
-- Grain: one original experimental observation, including repeated complexes.
select o.observation_id,
       s.source_key,
       e.experiment_key,
       o.geometry_id,
       o.geometry_id || ':L' as ligand_participant_key,
       o.geometry_id || ':R' as receptor_participant_key,
       o.pdb_id,o.complex_id,o.source_row,o.source_index_raw,
       o.ligand_name,o.receptor_name,o.ligand_chains_raw,o.receptor_chains_raw,
       o.mutations_raw,o.subgroup_raw,
       o.kd_m,o.pkd,o.kd_status,
       o.kd_m_raw,o.structure_method_raw,o.resolution_angstrom,o.resolution_angstrom_raw,
       o.structure_reference_raw,o.structure_release_date_raw,
       o.geometry_status,o.geometry_issue,o.structure_versions,
       o.mutation_structure_status,o.uses_reference_for_mutation,
       o.has_ca_contacts_10,o.biological_assembly_validated,
       o.kd_status='valid' as has_valid_label,
       o.geometry_status='computed' as has_computed_geometry,
       coalesce(g.n_selected_q1_ligand>0 and g.n_selected_q1_receptor>0,false) as has_q1_both_partners,
       coalesce(o.mutation_structure_status not in ('not_annotated','target_residues_present'),true) as needs_variant_review
from {{ ref('silver_affinity_observations') }} o
left join {{ ref('dim_geometry') }} g on o.geometry_id=g.geometry_id

left join {{ ref('dim_source') }} s on s.source_key={{ gold_key(gold_source_columns(), 'o.') }}
left join {{ ref('dim_experiment') }} e on e.experiment_key={{ gold_key(gold_experiment_columns(), 'o.') }}
