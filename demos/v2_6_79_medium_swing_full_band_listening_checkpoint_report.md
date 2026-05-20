# v2_6_79 — Medium Swing Full-Band Listening Checkpoint after Low-Register Clarity Guard

Acceptance Passed: **True**

## Scope
Behavior-preserving full-band checkpoint after v2_6_78. It generates 3-chorus Medium Swing demos with bass, drums, and piano enabled, using the explicit existing-voicing-capability override only to audit optional 5/6-note grouped SPREAD scenes. The checkpoint does not add rhythm vocabulary, change core voicing internals, change expression numbers, or touch API/Agent/HarmonyOS.

## Aggregate Full-Band Audit
- Tracks present in all tunes: True
- Note events by track: piano=1779, bass=854, drums=1632
- Piano voicing events: 440
- Grouped SPREAD events: 15
- 5-note / 6-note events: 11 / 4
- 5/6 ratio: 0.0341
- Ordinary-body 5/6 events: 0
- Optional selected events / ratio: 0 / 0.0
- Consecutive optional events: 0
- Voice-leading warnings: 0
- Low-register dense events (>1 piano note below C3): 0
- Bar 88 low-register dense events: 0
- Piano low/top note range: 41–73
- Bass span / continuity / repeated-root violations: 0 / 0 / 0
- Bass root-echo bad same/timing: 0 / 0
- Pedal CC64 / warnings: 0 / 0

## Per Tune
### All the Things You Are
- MIDI: `demos/v2_6_79_all_the_things_you_are_medium_swing_full_band_listening_checkpoint_demo.mid`
- Performance: 3 choruses, 108 bars
- Note events by track: `{'piano': 813, 'bass': 456, 'drums': 864}`
- Piano density counts: `{'4': 194, '5': 5, '6': 2}`
- Piano recipe counts: `{'d4__2plus2__seventh_chord_basic__rootless_allowed': 122, 'd4__1plus3__seventh_chord_basic__rootless_allowed': 72, 'spread_2plus3_contract': 5, 'spread_2plus4_contract': 2}`
- 5-note / 6-note: 5 / 2
- Optional selected events / ratio: 0 / 0.0
- Bass classic fill count: 2
- Low-register dense events: 0
- Bar 88 rows: `[{'event_id': 'c2_b15_ch0_medium_swing_piano_charleston_1_2and_0', 'region_id': 'c2_b15_ch0', 'chord_symbol': 'Gmaj7', 'pattern_id': 'medium_swing_piano_charleston_1_2and', 'density': 5, 'disposition': 'spread', 'recipe_id': 'spread_2plus3_contract', 'functional_grouping': '2+3', 'midi_notes': [43, 54, 59, 66, 69], 'notes_below_c3': 1, 'low_note': 43, 'top_note': 69, 'region_chorus_index': 2, 'region_total_choruses': 3, 'region_is_last_bar_of_section': True, 'region_is_last_bar_of_chorus': False, 'region_performance_bar_index': 87, 'top_voice_leap_exceeds_max': False, 'top_voice_abs_motion': 3}, {'event_id': 'c2_b15_ch0_medium_swing_piano_charleston_1_2and_1', 'region_id': 'c2_b15_ch0', 'chord_symbol': 'Gmaj7', 'pattern_id': 'medium_swing_piano_charleston_1_2and', 'density': 5, 'disposition': 'spread', 'recipe_id': 'spread_2plus3_contract', 'functional_grouping': '2+3', 'midi_notes': [43, 54, 59, 66, 69], 'notes_below_c3': 1, 'low_note': 43, 'top_note': 69, 'region_chorus_index': 2, 'region_total_choruses': 3, 'region_is_last_bar_of_section': True, 'region_is_last_bar_of_chorus': False, 'region_performance_bar_index': 87, 'top_voice_leap_exceeds_max': False, 'top_voice_abs_motion': 3}]`

### Autumn Leaves
- MIDI: `demos/v2_6_79_autumn_leaves_medium_swing_full_band_listening_checkpoint_demo.mid`
- Performance: 3 choruses, 96 bars
- Note events by track: `{'piano': 966, 'bass': 398, 'drums': 768}`
- Piano density counts: `{'4': 231, '5': 6, '6': 2}`
- Piano recipe counts: `{'d4__2plus2__seventh_chord_basic__rootless_allowed': 147, 'd4__1plus3__seventh_chord_basic__rootless_allowed': 84, 'spread_2plus3_contract': 6, 'spread_2plus4_contract': 2}`
- 5-note / 6-note: 6 / 2
- Optional selected events / ratio: 0 / 0.0
- Bass classic fill count: 0
- Low-register dense events: 0
- Bar 88 rows: `[]`

## Acceptance Checks

- checkpoint_declared: True
- keeps_v2_6_78_low_register_guard: True
- existing_voicing_capability_still_opt_in: True
- no_core_voicing_change_declared: True
- base_policy_still_open_drop_4note: True
- patterns_still_no_expression_or_voicing_leakage: True
- patterns_still_region_first: True
- all_tracks_present: True
- existing_5_6_usage_remains_low_intrusion: True
- ordinary_body_not_thickened: True
- optional_fill_variation_remains_low_intrusion: True
- no_consecutive_optional_events: True
- voice_leading_guard_ok: True
- low_register_clarity_guard_ok: True
- top_register_ok: True
- bass_foundation_audit_ok: True
- root_echo_audit_ok: True
- pedal_no_medium_swing_cc64_spill: True
