# v2_6_93 — Engine Bossa Nova Anticipation Tail Policy + Native 4& Audit

Engine version tag: `v2_10_28`

## Scope

Refine the existing Bossa style anticipation policy in place. The shared core AnticipationResolver now supports a style-configurable minimum previous-region duration, and Bossa requires a full-region tail with beat 4 and 4& empty. Native 4& cells remain current-chord events that occupy the 4& slot and block anticipation. No parallel anticipation engine, pattern-embedded anticipation, expression numeric change, or core voicing change.

## Static Bossa anticipation audit

- Arrangement policy version: `v2_6_93`
- Anticipation policy debug name: `bossa_next_bar_beat1_to_previous_4and_when_tail_free`
- Min previous region duration: `3.75`
- Requires previous beat 4 empty: `True`
- Requires previous 4& empty: `True`
- Native 4& candidates marked: `True`
- Legacy bar-first tags: `[]`

## Resolver probes

- Native 4& probe: `{'previous_candidate': 'bossa_piano_cell_A_1_4and', 'current_candidate': 'bossa_piano_cell_A_1', 'previous_duration_beats': 4.0, 'allowed': False, 'blocked': True, 'anticipated_onsets': [], 'anticipated_local_beats': [], 'tail_checked_local_beats': []}`
- Tail-free probe: `{'previous_candidate': 'bossa_piano_cell_A_1_3and', 'current_candidate': 'bossa_piano_cell_A_1', 'previous_duration_beats': 4.0, 'allowed': True, 'blocked': False, 'anticipated_onsets': [3.5], 'anticipated_local_beats': [3.5], 'tail_checked_local_beats': [[3.0, 3.5]]}`
- Short-region probe: `{'previous_candidate': 'bossa_piano_half_region_1_2', 'current_candidate': 'bossa_piano_cell_A_1', 'previous_duration_beats': 2.0, 'allowed': False, 'blocked': True, 'anticipated_onsets': [], 'anticipated_local_beats': [], 'tail_checked_local_beats': []}`

## Runtime Blue Bossa audits

### 3 choruses / seed `22703`

- MIDI: `demos/v2_6_93_blue_bossa_3x_bossa_nova_anticipation_tail_policy_demo.mid`
- Notes by track: `{'piano': 400, 'bass': 102, 'drums': 102}`
- Piano pattern counts: `{'bossa_piano_core_batida_1_2_3and': 18, 'bossa_piano_cell_B_1and': 1, 'bossa_piano_cell_A_1_3and': 18, 'bossa_piano_cell_A_1': 6, 'bossa_piano_cell_A_1_4and': 6, 'bossa_piano_cell_A_1_2and': 16, 'bossa_piano_cell_A_1_3': 6, 'bossa_piano_cell_B_1and_3': 4, 'bossa_piano_half_region_1_2': 12, 'bossa_piano_cell_A_1_2_3and': 21}`
- Non-core / Class A / Class B event counts: `78` / `73` / `5`
- Class B ratio: `0.0641`
- Native 4& events / native anticipated events: `3` / `0`
- Active anticipations: `12`
- Anticipations from short previous regions: `0`
- Anticipation policy versions: `['v2_6_93']`
- Anticipation min previous duration values: `['3.75']`
- Tail checked local beats: `[(3.0, 3.5)]`
- Terminal-ending anticipations: `0`
- Expression warnings / missing / cross-region / cross-next-event: `0` / `0` / `0` / `0`
- Pedal CC64 events: `0`

### 5 choruses / seed `22753`

- MIDI: `demos/v2_6_93_blue_bossa_5x_bossa_nova_anticipation_tail_policy_demo.mid`
- Notes by track: `{'piano': 590, 'bass': 170, 'drums': 170}`
- Piano pattern counts: `{'bossa_piano_core_batida_1_2_3and': 33, 'bossa_piano_cell_A_1_2_3and': 21, 'bossa_piano_cell_B_1and_3': 2, 'bossa_piano_cell_A_1_3': 16, 'bossa_piano_cell_A_1_2and': 28, 'bossa_piano_cell_A_1_3and': 36, 'bossa_piano_cell_A_1': 15, 'bossa_piano_half_region_1_2': 20, 'bossa_piano_cell_B_1and': 1}`
- Non-core / Class A / Class B event counts: `119` / `116` / `3`
- Class B ratio: `0.0252`
- Native 4& events / native anticipated events: `0` / `0`
- Active anticipations: `29`
- Anticipations from short previous regions: `0`
- Anticipation policy versions: `['v2_6_93']`
- Anticipation min previous duration values: `['3.75']`
- Tail checked local beats: `[(3.0, 3.5)]`
- Terminal-ending anticipations: `0`
- Expression warnings / missing / cross-region / cross-next-event: `0` / `0` / `0` / `0`
- Pedal CC64 events: `0`

## Known next gap

Anticipation tail/native-4& separation is audited; next pass should calibrate Bossa distance-aware expression and sustain release without adding new rhythm cells.

Recommended next task: `v2_6_94_engine_bossa_nova_distance_aware_expression_calibration`

## Acceptance

Passed: `True`

- `style_and_policy_registered`: `True`
- `in_place_boundaries_preserved`: `True`
- `tail_policy_declared`: `True`
- `native_4and_marked_and_blocks_tail`: `True`
- `tail_free_full_region_allows_anticipation`: `True`
- `short_region_blocks_bossa_anticipation`: `True`
- `boundaries_preserved`: `True`
- `runtime_blue_bossa_full_band_passes`: `True`
