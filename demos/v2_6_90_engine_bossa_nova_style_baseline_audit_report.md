# v2_6_90 — Engine Bossa Nova Style Baseline Audit

Engine version tag: `v2_10_28`

## Scope

Bossa Nova baseline audit from the latest v2_10_28/v2_6_89 handoff baseline. This pass cleans misleading legacy Bossa metadata and audits the current Blue Bossa full-band runtime without adding rhythm vocabulary, changing expression numeric values, modifying core voicing, or touching API/Agent/HarmonyOS.

## Static Bossa policy audit

- Arrangement policy version: `v2_6_90`
- Core batida beats: `[0.0, 1.0, 2.5]`
- Core batida expression hints: `['core_short', 'core_short', 'core_sustain']`
- Half-region beats: `[0.0, 1.0]`
- Legacy bar-first tags: `[]`
- Behavior change: `False`

## Runtime Blue Bossa audits

### 3 choruses / seed `22702`

- MIDI: `demos/v2_6_90_blue_bossa_3x_bossa_nova_style_baseline_audit_demo.mid`
- Notes by track: `{'piano': 536, 'bass': 102, 'drums': 102}`
- Piano pattern counts: `{'bossa_piano_core_batida_1_2_3and': 135, 'bossa_piano_half_region_1_2': 12}`
- Opening first two bars patterns: `['bossa_piano_core_batida_1_2_3and']`
- Active anticipations: `11`
- Terminal-ending anticipations: `0`
- Expression warnings / missing / cross-region / cross-next-event: `0` / `0` / `0` / `0`
- Pedal CC64 events: `0`
- Piano content families: `{'seventh_chord_basic': 102, 'rooted_color': 19, 'guide_tone': 26}`

### 5 choruses / seed `22752`

- MIDI: `demos/v2_6_90_blue_bossa_5x_bossa_nova_style_baseline_audit_demo.mid`
- Notes by track: `{'piano': 922, 'bass': 170, 'drums': 170}`
- Piano pattern counts: `{'bossa_piano_core_batida_1_2_3and': 225, 'bossa_piano_half_region_1_2': 20}`
- Opening first two bars patterns: `['bossa_piano_core_batida_1_2_3and']`
- Active anticipations: `22`
- Terminal-ending anticipations: `0`
- Expression warnings / missing / cross-region / cross-next-event: `0` / `0` / `0` / `0`
- Pedal CC64 events: `0`
- Piano content families: `{'seventh_chord_basic': 181, 'rooted_color': 35, 'guide_tone': 29}`

## Known next gap

Only core_batida and its two-beat ChordRegion adaptation are active; non-core Bossa rhythm-cell vocabulary should be planned next without coupling articulation or voicing.

Recommended next task: `v2_6_91_engine_bossa_nova_non_core_rhythm_cell_vocabulary_planning`

## Acceptance

Passed: `True`

- `style_and_policy_registered`: `True`
- `baseline_audit_is_behavior_preserving`: `True`
- `core_batida_identity_matches_user_rule`: `True`
- `half_region_is_chord_region_first`: `True`
- `runtime_blue_bossa_full_band_passes`: `True`
