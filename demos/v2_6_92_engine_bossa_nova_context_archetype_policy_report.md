# v2_6_92 — Engine Bossa Nova Context Archetype Policy + History Scorer Refinement

Engine version tag: `v2_10_28`

## Scope

Overwrite the previous simple v2_6_91 Bossa weighting in place with context archetype multipliers and rolling history metadata inside the existing ChordRegion-first comping pattern path. No new selector, no new rhythm vocabulary, no bar-first route, no expression numeric change, and no core voicing change.

## Static Bossa policy audit

- Arrangement policy version: `v2_6_92`
- Candidate count: `13` full-region / `1` half-region
- Class A / Class B / Core counts: `6` / `6` / `1`
- Archetypes: `['core_batida_anchor', 'steady_batida_flow', 'breath_space', 'response_comping', 'transition_lift', 'release', 'dense_harmonic_marks']`
- Legacy bar-first tags: `[]`

## Context probes

- `opening`: archetypes=`['core_batida_anchor']`, candidate_count=`1`, has_only_core=`True`, max_class_B_multiplier=`None`
- `steady`: archetypes=`['steady_batida_flow']`, candidate_count=`12`, has_only_core=`False`, max_class_B_multiplier=`0.42`
- `bridge_breath`: archetypes=`['breath_space']`, candidate_count=`12`, has_only_core=`False`, max_class_B_multiplier=`2.0925`
- `transition_lift`: archetypes=`['transition_lift']`, candidate_count=`12`, has_only_core=`False`, max_class_B_multiplier=`0.45`
- `release`: archetypes=`['release']`, candidate_count=`12`, has_only_core=`False`, max_class_B_multiplier=`0.432`
- `short_region`: archetypes=`['dense_harmonic_marks']`, candidate_count=`1`, has_only_core=`False`, max_class_B_multiplier=`None`
- `recent_class_B_guard`: archetypes=`['breath_space']`, candidate_count=`12`, has_only_core=`False`, max_class_B_multiplier=`0.0201`

## Runtime Blue Bossa audits

### 3 choruses / seed `22702`

- MIDI: `demos/v2_6_92_blue_bossa_3x_bossa_nova_context_archetype_policy_demo.mid`
- Notes by track: `{'piano': 382, 'bass': 102, 'drums': 102}`
- Piano pattern counts: `{'bossa_piano_core_batida_1_2_3and': 12, 'bossa_piano_cell_A_1': 7, 'bossa_piano_cell_A_1_2and': 18, 'bossa_piano_cell_A_1_3and': 18, 'bossa_piano_cell_A_1_2_3and': 18, 'bossa_piano_cell_B_1and': 3, 'bossa_piano_half_region_1_2': 12, 'bossa_piano_cell_A_1_3': 12, 'bossa_piano_cell_B_1and_3and': 2}`
- Piano archetype counts: `{'core_batida_anchor': 24, 'breath_space': 25, 'steady_batida_flow': 7, 'transition_lift': 26, 'response_comping': 8, 'dense_harmonic_marks': 12}`
- Weighting status counts: `{'opening_first_two_bars_core_only': 6, 'breath_space_weighted': 25, 'steady_batida_flow_weighted': 7, 'transition_lift_weighted': 26, 'core_batida_anchor_weighted': 18, 'response_comping_weighted': 7, 'dense_harmonic_short_region': 12, 'class_B_recent_history_guard_downweight': 1}`
- Non-core / Class A / Class B event counts: `78` / `73` / `5`
- Class B ratio: `0.0641`
- Opening first two bars patterns: `['bossa_piano_core_batida_1_2_3and']`
- Active anticipations: `10`
- Terminal-ending anticipations: `0`
- Expression warnings / missing / cross-region / cross-next-event: `0` / `0` / `0` / `0`
- Pedal CC64 events: `0`

### 5 choruses / seed `22752`

- MIDI: `demos/v2_6_92_blue_bossa_5x_bossa_nova_context_archetype_policy_demo.mid`
- Notes by track: `{'piano': 596, 'bass': 170, 'drums': 170}`
- Piano pattern counts: `{'bossa_piano_core_batida_1_2_3and': 33, 'bossa_piano_cell_A_1_2and': 38, 'bossa_piano_cell_A_1': 10, 'bossa_piano_cell_A_1_3and': 34, 'bossa_piano_cell_A_1_2_3and': 18, 'bossa_piano_cell_A_1_3': 12, 'bossa_piano_half_region_1_2': 20, 'bossa_piano_cell_B_1and_3': 4, 'bossa_piano_cell_B_1and': 2, 'bossa_piano_cell_B_1and_4': 4}`
- Piano archetype counts: `{'core_batida_anchor': 41, 'breath_space': 47, 'steady_batida_flow': 12, 'transition_lift': 39, 'dense_harmonic_marks': 20, 'response_comping': 16}`
- Weighting status counts: `{'opening_first_two_bars_core_only': 6, 'breath_space_weighted': 47, 'steady_batida_flow_weighted': 12, 'transition_lift_weighted': 39, 'core_batida_anchor_weighted': 35, 'dense_harmonic_short_region': 20, 'response_comping_weighted': 14, 'class_B_recent_history_guard_downweight': 2}`
- Non-core / Class A / Class B event counts: `122` / `112` / `10`
- Class B ratio: `0.082`
- Opening first two bars patterns: `['bossa_piano_core_batida_1_2_3and']`
- Active anticipations: `20`
- Terminal-ending anticipations: `0`
- Expression warnings / missing / cross-region / cross-next-event: `0` / `0` / `0` / `0`
- Pedal CC64 events: `0`

## Known next gap

Context/history weighting is active; next pass should specifically audit Bossa anticipation tail rules and native 4& separation before doing distance-aware expression calibration.

Recommended next task: `v2_6_93_engine_bossa_nova_anticipation_tail_policy_and_native_4and_audit`

## Acceptance

Passed: `True`

- `style_and_policy_registered`: `True`
- `in_place_replacement_boundaries`: `True`
- `same_vocabulary_preserved`: `True`
- `archetype_context_probes_work`: `True`
- `history_guard_probe_downweights_class_B`: `True`
- `boundaries_preserved`: `True`
- `runtime_blue_bossa_full_band_passes`: `True`
