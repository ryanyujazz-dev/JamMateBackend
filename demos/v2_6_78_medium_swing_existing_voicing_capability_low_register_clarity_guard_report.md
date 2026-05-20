# v2_6_78 — Medium Swing Existing Voicing Capability Low Register Clarity Guard

Acceptance Passed: **True**

## Scope
Medium Swing keeps v2_6_77 as an explicit style/event policy using existing grouped SPREAD 5/6-note capability, but v2_6_78 routes that optional support through the existing spread low-register density guard so full-band piano does not stack more than one note below C3. The task does not modify core voicing source, projection, selector, expression, pattern, API, Agent, or HarmonyOS behavior.

## Aggregate
- Piano voicing events: 438
- Grouped SPREAD events: 17
- 5-note events: 13
- 6-note events: 4
- 5/6 ratio: 0.0388
- Ordinary-body 5/6 events: 0
- Voice-leading warnings: 0
- Low-register dense events (>1 note below C3): 0
- Bar 88 low-register dense events: 0
- Max top note: 73

## Per Tune
### All the Things You Are
- MIDI: `demos/v2_6_78_all_the_things_you_are_medium_swing_existing_voicing_capability_low_register_clarity_guard_demo.mid`
- Piano voicing events: 206
- Density counts: `{'4': 198, '5': 6, '6': 2}`
- Recipe counts: `{'d4__2plus2__seventh_chord_basic__rootless_allowed': 129, 'd4__1plus3__seventh_chord_basic__rootless_allowed': 69, 'spread_2plus3_contract': 6, 'spread_2plus4_contract': 2}`
- 5-note / 6-note: 6 / 2
- Section-tail 5/6 events: 8
- Ending 5/6 events: 2
- Voice-leading warnings: 0
- Low-register dense rows: 0
- Bar 88 rows: `[{'event_id': 'c2_b15_ch0_medium_swing_piano_1_4_tail_0', 'region_id': 'c2_b15_ch0', 'chord_symbol': 'Gmaj7', 'pattern_id': 'medium_swing_piano_1_4_tail', 'density': 5, 'disposition': 'spread', 'recipe_id': 'spread_2plus3_contract', 'functional_grouping': '2+3', 'midi_notes': [43, 54, 59, 66, 69], 'notes_below_c3': 1, 'low_register_clarity_guard_violation': False, 'top_note': 69, 'region_chorus_index': 2, 'region_total_choruses': 3, 'region_is_last_bar_of_section': True, 'region_is_last_bar_of_chorus': False, 'region_performance_bar_index': 87, 'top_voice_leap_exceeds_max': False, 'top_voice_abs_motion': 3}, {'event_id': 'c2_b15_ch0_medium_swing_piano_1_4_tail_1', 'region_id': 'c2_b15_ch0', 'chord_symbol': 'Gmaj7', 'pattern_id': 'medium_swing_piano_1_4_tail', 'density': 5, 'disposition': 'spread', 'recipe_id': 'spread_2plus3_contract', 'functional_grouping': '2+3', 'midi_notes': [43, 54, 59, 66, 69], 'notes_below_c3': 1, 'low_register_clarity_guard_violation': False, 'top_note': 69, 'region_chorus_index': 2, 'region_total_choruses': 3, 'region_is_last_bar_of_section': True, 'region_is_last_bar_of_chorus': False, 'region_performance_bar_index': 87, 'top_voice_leap_exceeds_max': False, 'top_voice_abs_motion': 3}]`

### Autumn Leaves
- MIDI: `demos/v2_6_78_autumn_leaves_medium_swing_existing_voicing_capability_low_register_clarity_guard_demo.mid`
- Piano voicing events: 232
- Density counts: `{'4': 223, '5': 7, '6': 2}`
- Recipe counts: `{'d4__1plus3__seventh_chord_basic__rootless_allowed': 90, 'd4__2plus2__seventh_chord_basic__rootless_allowed': 133, 'spread_2plus3_contract': 7, 'spread_2plus4_contract': 2}`
- 5-note / 6-note: 7 / 2
- Section-tail 5/6 events: 9
- Ending 5/6 events: 2
- Voice-leading warnings: 0
- Low-register dense rows: 0
- Bar 88 rows: `[]`

## Acceptance Checks

- policy_version_declared: True
- low_register_clarity_guard_declared: True
- policy_available_but_default_opt_in: True
- no_core_voicing_change_declared: True
- ordinary_base_policy_still_open_4note: True
- patterns_still_no_expression_or_voicing_leakage: True
- patterns_still_region_first: True
- existing_5note_capability_used: True
- existing_6note_capability_used: True
- ordinary_body_not_thickened: True
- voice_leading_guard_ok: True
- low_register_clarity_guard_ok: True
- bar_88_clarity_regression_fixed: True
- top_register_ok: True
