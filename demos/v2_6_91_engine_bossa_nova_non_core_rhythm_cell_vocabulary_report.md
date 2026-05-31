# v2_6_91 — Engine Bossa Nova Non-Core Rhythm Cell Vocabulary

Engine version tag: `v2_10_28`

## Scope

Activate Bossa Nova non-core piano rhythm cells directly in the existing V2 ChordRegion-first pattern library. This replaces the old core-only runtime path without adding a parallel selector or moving expression/voicing/API/Agent/HarmonyOS boundaries.

## Static Bossa policy audit

- Arrangement policy version: `v2_6_91`
- Candidate count: `13` full-region / `1` half-region
- Class A / Class B / Core counts: `6` / `6` / `1`
- Core batida beats: `[0.0, 1.0, 2.5]`
- Non-core expression hints: `['cell_close_gap_short', 'cell_soft_hold']`
- Native 4& candidates: `['bossa_piano_cell_A_1_4and', 'bossa_piano_cell_B_1and_4and', 'bossa_piano_cell_B_1and_3_4and']`
- Legacy bar-first tags: `[]`

## Runtime Blue Bossa audits

### 3 choruses / seed `22702`

- MIDI: `demos/v2_6_91_blue_bossa_3x_bossa_nova_non_core_rhythm_cell_vocabulary_demo.mid`
- Notes by track: `{'piano': 386, 'bass': 102, 'drums': 102}`
- Piano pattern counts: `{'bossa_piano_core_batida_1_2_3and': 6, 'bossa_piano_cell_A_1': 5, 'bossa_piano_cell_A_1_2and': 20, 'bossa_piano_cell_A_1_3': 8, 'bossa_piano_cell_A_1_2_3and': 33, 'bossa_piano_cell_B_1and_4': 4, 'bossa_piano_half_region_1_2': 12, 'bossa_piano_cell_A_1_3and': 16, 'bossa_piano_cell_B_1and': 2, 'bossa_piano_cell_B_1and_3and': 2}`
- Non-core / Class A / Class B event counts: `90` / `82` / `8`
- Class B ratio: `0.0889`
- Opening first two bars patterns: `['bossa_piano_core_batida_1_2_3and']`
- Active anticipations: `10`
- Terminal-ending anticipations: `0`
- Expression warnings / missing / cross-region / cross-next-event: `0` / `0` / `0` / `0`
- Pedal CC64 events: `0`

### 5 choruses / seed `22752`

- MIDI: `demos/v2_6_91_blue_bossa_5x_bossa_nova_non_core_rhythm_cell_vocabulary_demo.mid`
- Notes by track: `{'piano': 648, 'bass': 170, 'drums': 170}`
- Piano pattern counts: `{'bossa_piano_core_batida_1_2_3and': 12, 'bossa_piano_cell_A_1_2and': 30, 'bossa_piano_cell_A_1': 10, 'bossa_piano_cell_A_1_3and': 30, 'bossa_piano_cell_A_1_3': 20, 'bossa_piano_cell_A_1_2_3and': 48, 'bossa_piano_half_region_1_2': 20, 'bossa_piano_cell_B_1and': 1, 'bossa_piano_cell_A_1_4and': 2, 'bossa_piano_cell_B_1and_4': 2, 'bossa_piano_cell_B_1and_3and': 2, 'bossa_piano_cell_B_1and_4and': 2}`
- Non-core / Class A / Class B event counts: `147` / `140` / `7`
- Class B ratio: `0.0476`
- Opening first two bars patterns: `['bossa_piano_core_batida_1_2_3and']`
- Active anticipations: `20`
- Terminal-ending anticipations: `0`
- Expression warnings / missing / cross-region / cross-next-event: `0` / `0` / `0` / `0`
- Pedal CC64 events: `0`

## Known next gap

Non-core rhythm cells are now active, but articulation remains profile-alias based rather than true distance-sensitive Bossa articulation; next pass should refine groove archetype/context weighting and then add distance-aware expression.

Recommended next task: `v2_6_92_engine_bossa_nova_context_archetype_policy_and_history_scorer_refinement`

## Acceptance

Passed: `True`

- `style_and_policy_registered`: `True`
- `direct_replacement_not_parallel_path`: `True`
- `pattern_library_has_core_A_B_vocabulary`: `True`
- `core_batida_identity_preserved`: `True`
- `boundaries_preserved`: `True`
- `expression_aliases_exist_without_new_numeric_calibration`: `True`
- `runtime_blue_bossa_full_band_passes`: `True`
