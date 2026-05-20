# v2_6_81 — Medium Swing Full-Band Post-Density-Relief Checkpoint

Acceptance Passed: **True**

## Scope
Behavior-preserving full-band checkpoint after v2_6_80. It checks that the two-beat density relief works in a piano+bass+drums setting: Autumn Leaves should no longer be over-dense in consecutive 2-beat ChordRegions, All The Things You Are should not be over-thinned, generic region-first anticipation must remain active, and the v2_6_78 low-register clarity guard plus explicit-only 5/6-note grouped SPREAD usage stay intact. No pattern, voicing internals, expression numbers, API, Agent, or HarmonyOS behavior are changed.

## Aggregate Full-Band Audit
- Tracks present in all tunes: True
- Note events by track: piano=1546, bass=854, drums=1632
- Piano active pattern events: 382
- Piano 2-beat active / multi-touch / anchor: 158 / 4 / 142
- 2-beat anchor ratio / multi-touch ratio: 0.8987 / 0.0253
- Active anticipations / 2-beat previous-tail anticipations: 19 / 14
- Piano voicing events: 382
- Grouped SPREAD events: 14
- 5-note / 6-note events: 10 / 4
- 5/6 ratio: 0.0366
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
- MIDI: `demos/v2_6_81_all_the_things_you_are_medium_swing_full_band_post_density_relief_checkpoint_demo.mid`
- Performance: 3 choruses, 108 bars
- Note events by track: `{'piano': 777, 'bass': 456, 'drums': 864}`
- Piano active / 2-beat active: 192 / 24
- 2-beat start anchors / multi-touch: 21 / 0
- 2-beat pattern counts: `{'medium_swing_piano_two_beat_region_start_anchor': 21, 'medium_swing_piano_two_beat_region_local2_only': 3}`
- 2-beat relief status counts: `{'simple_anchor_preferred': 21, 'delayed_only_short_region_downweighted': 3}`
- Active anticipations / 2-beat previous-tail: 5 / 1
- Piano density counts: `{'4': 185, '5': 5, '6': 2}`
- Piano recipe counts: `{'d4__2plus2__seventh_chord_basic__rootless_allowed': 118, 'd4__1plus3__seventh_chord_basic__rootless_allowed': 67, 'spread_2plus3_contract': 5, 'spread_2plus4_contract': 2}`
- 5-note / 6-note: 5 / 2
- Optional selected events / ratio: 0 / 0.0
- Low-register dense events: 0
- Bar 88 rows: `[{'event_id': 'c2_b15_ch0_medium_swing_piano_charleston_1_2and_0', 'region_id': 'c2_b15_ch0', 'chord_symbol': 'Gmaj7', 'pattern_id': 'medium_swing_piano_charleston_1_2and', 'density': 5, 'disposition': 'spread', 'recipe_id': 'spread_2plus3_contract', 'functional_grouping': '2+3', 'midi_notes': [43, 54, 59, 66, 69], 'notes_below_c3': 1, 'low_note': 43, 'top_note': 69, 'region_chorus_index': 2, 'region_total_choruses': 3, 'region_is_last_bar_of_section': True, 'region_is_last_bar_of_chorus': False, 'region_performance_bar_index': 87, 'authorized_5_6_scene': True, 'top_voice_leap_exceeds_max': False, 'top_voice_abs_motion': 3}, {'event_id': 'c2_b15_ch0_medium_swing_piano_charleston_1_2and_1', 'region_id': 'c2_b15_ch0', 'chord_symbol': 'Gmaj7', 'pattern_id': 'medium_swing_piano_charleston_1_2and', 'density': 5, 'disposition': 'spread', 'recipe_id': 'spread_2plus3_contract', 'functional_grouping': '2+3', 'midi_notes': [43, 54, 59, 66, 69], 'notes_below_c3': 1, 'low_note': 43, 'top_note': 69, 'region_chorus_index': 2, 'region_total_choruses': 3, 'region_is_last_bar_of_section': True, 'region_is_last_bar_of_chorus': False, 'region_performance_bar_index': 87, 'authorized_5_6_scene': True, 'top_voice_leap_exceeds_max': False, 'top_voice_abs_motion': 3}]`

### Autumn Leaves
- MIDI: `demos/v2_6_81_autumn_leaves_medium_swing_full_band_post_density_relief_checkpoint_demo.mid`
- Performance: 3 choruses, 96 bars
- Note events by track: `{'piano': 769, 'bass': 398, 'drums': 768}`
- Piano active / 2-beat active: 190 / 134
- 2-beat start anchors / multi-touch: 121 / 4
- 2-beat pattern counts: `{'medium_swing_piano_two_beat_region_start_anchor': 121, 'medium_swing_piano_two_beat_region_local2_only': 9, 'medium_swing_piano_two_beat_region_start_local2': 4}`
- 2-beat relief status counts: `{'simple_anchor_preferred': 121, 'delayed_only_short_region_downweighted': 9, 'multi_touch_short_region_downweighted': 4}`
- Active anticipations / 2-beat previous-tail: 14 / 13
- Piano density counts: `{'4': 183, '5': 5, '6': 2}`
- Piano recipe counts: `{'d4__1plus3__seventh_chord_basic__rootless_allowed': 67, 'd4__2plus2__seventh_chord_basic__rootless_allowed': 116, 'spread_2plus3_contract': 5, 'spread_2plus4_contract': 2}`
- 5-note / 6-note: 5 / 2
- Optional selected events / ratio: 0 / 0.0
- Low-register dense events: 0
- Bar 88 rows: `[]`

## Acceptance Checks

- ✅ v2_6_81 checkpoint declared
- ✅ v2_6_80 density relief still declared
- ✅ generic region-first anticipation checkpoint retained
- ✅ low-register clarity guard retained
- ✅ existing 5/6-note capability remains explicit opt-in
- ✅ no core voicing change declared
- ✅ base policy still open/drop 4-note
- ✅ patterns still no expression/voicing leakage
- ✅ patterns remain ChordRegion-first
- ✅ all tracks present
- ✅ All The Things not over-thinned
- ✅ Autumn Leaves relieved but not sparse
- ✅ Autumn Leaves two-beat multi-touch remains rare
- ✅ Autumn Leaves simple anchors dominate two-beat regions
- ✅ All The Things two-beat remains relaxed
- ✅ generic anticipation active on both tunes
- ✅ 2-beat previous-tail anticipation observed
- ✅ no invalid region-first anticipations
- ✅ explicit 5/6-note usage remains low intrusion
- ✅ ordinary body not thickened
- ✅ optional fill/variation remains low intrusion
- ✅ no consecutive optional events
- ✅ voice-leading guard ok
- ✅ low-register clarity guard ok
- ✅ top register ok
- ✅ bass foundation audit ok
- ✅ root echo audit ok
- ✅ dry Medium Swing pedal
