# v2_6_83 — Medium Swing Drum–Piano Interaction Audit

Acceptance Passed: **True**

## Scope
Full-band drum–piano interaction checkpoint after v2_6_82. This audit reconstructs the existing Medium Swing region-local ride/hi-hat time grid for analysis only, then checks whether piano comping is overlapping too aggressively with ride accents, hi-hat 2/4, ride-skip ghosts, optional fill/variation cells, and dense 2-beat ChordRegions. No drum fills, drum patterns, piano patterns, voicing internals, expression numbers, API, Agent, or HarmonyOS behavior are changed.

## Aggregate Drum–Piano Interaction Audit
- Tracks present in all tunes: True
- Note events by track: piano=1538, bass=854, drums=1632
- Piano active pattern events / voicing events: 382 / 382
- Piano 2-beat active / start anchors / anchor ratio: 158 / 142 / 0.8987
- Active anticipations / 2-beat previous-tail anticipations: 19 / 14
- 5-note / 6-note events / ratio: 10 / 0 / 0.0262
- Piano–drum joined events: 358
- Piano on ride medium / hi-hat / ride-skip ghost: 257 / 40 / 61
- 2-beat non-anchor with drums / optional with drums / accented hi-hat: 16 / 0 / 0
- Drum–piano risk events: 16
- Voice-leading warnings / low-register dense events: 0 / 0
- Bass span / continuity / repeated-root violations: 0 / 0 / 0
- Pedal CC64 / warnings: 0 / 0

## Per Tune
### All the Things You Are
- MIDI: `demos/v2_6_83_all_the_things_you_are_medium_swing_drum_piano_interaction_audit_demo.mid`
- Performance: 3 choruses, 108 bars
- Note events by track: `{'piano': 773, 'bass': 456, 'drums': 864}`
- Piano active / 2-beat active / 2-beat anchor ratio: 192 / 24 / 0.875
- Active anticipations / 2-beat previous-tail: 5 / 1
- Piano–drum roles: `{'ride_medium': 116, 'ride_skip_ghost': 36, 'ride_soft': 21, 'hihat_pedal': 21}`
- 2-beat non-anchor with drums / optional with drums / accented hi-hat: 3 / 0 / 0
- Samples: `[{'event_id': 'c0_b0_ch0_medium_swing_piano_anchor_1_0', 'region_id': 'c0_b0_ch0', 'bar': 0, 'pattern_id': 'medium_swing_piano_anchor_1', 'local_beat': 0.0, 'swing_local_beat': 0.0, 'expression_hint': 'comp_medium', 'region_length_family': 'four_beat_region', 'drum_roles': ['ride_medium'], 'optional_selected': False}, {'event_id': 'c0_b1_ch0_medium_swing_piano_reverse_charleston_1and_3_1', 'region_id': 'c0_b1_ch0', 'bar': 1, 'pattern_id': 'medium_swing_piano_reverse_charleston_1and_3', 'local_beat': 2.0, 'swing_local_beat': 2.0, 'expression_hint': 'comp_medium', 'region_length_family': 'four_beat_region', 'drum_roles': ['ride_medium'], 'optional_selected': False}, {'event_id': 'c0_b2_ch0_medium_swing_piano_charleston_1_2and_0', 'region_id': 'c0_b2_ch0', 'bar': 2, 'pattern_id': 'medium_swing_piano_charleston_1_2and', 'local_beat': 0.0, 'swing_local_beat': 0.0, 'expression_hint': 'comp_accent_hold', 'region_length_family': 'four_beat_region', 'drum_roles': ['ride_medium'], 'optional_selected': False}]`

### Autumn Leaves
- MIDI: `demos/v2_6_83_autumn_leaves_medium_swing_drum_piano_interaction_audit_demo.mid`
- Performance: 3 choruses, 96 bars
- Note events by track: `{'piano': 765, 'bass': 398, 'drums': 768}`
- Piano active / 2-beat active / 2-beat anchor ratio: 190 / 134 / 0.903
- Active anticipations / 2-beat previous-tail: 14 / 13
- Piano–drum roles: `{'ride_medium': 141, 'ride_soft': 19, 'hihat_pedal': 19, 'ride_skip_ghost': 25}`
- 2-beat non-anchor with drums / optional with drums / accented hi-hat: 13 / 0 / 0
- Samples: `[{'event_id': 'c0_b0_ch0_medium_swing_piano_two_beat_region_start_anchor_0', 'region_id': 'c0_b0_ch0', 'bar': 0, 'pattern_id': 'medium_swing_piano_two_beat_region_start_anchor', 'local_beat': 0.0, 'swing_local_beat': 0.0, 'expression_hint': 'comp_medium', 'region_length_family': 'two_beat_region', 'drum_roles': ['ride_medium'], 'optional_selected': False}, {'event_id': 'c0_b0_ch1_medium_swing_piano_two_beat_region_start_anchor_0', 'region_id': 'c0_b0_ch1', 'bar': 0, 'pattern_id': 'medium_swing_piano_two_beat_region_start_anchor', 'local_beat': 0.0, 'swing_local_beat': 0.0, 'expression_hint': 'comp_medium', 'region_length_family': 'two_beat_region', 'drum_roles': ['ride_medium'], 'optional_selected': False}, {'event_id': 'c0_b1_ch0_medium_swing_piano_two_beat_region_start_anchor_0', 'region_id': 'c0_b1_ch0', 'bar': 1, 'pattern_id': 'medium_swing_piano_two_beat_region_start_anchor', 'local_beat': 0.0, 'swing_local_beat': 0.0, 'expression_hint': 'comp_medium', 'region_length_family': 'two_beat_region', 'drum_roles': ['ride_medium'], 'optional_selected': False}]`

## Acceptance Checks

- ✅ v2_6_83 drum-piano audit declared
- ✅ previous bass-piano checkpoint retained
- ✅ no music behavior change declared
- ✅ existing drum ride candidates retained
- ✅ drum grid remains ride-time only and not anticipation receiver
- ✅ all full-band tracks present
- ✅ 2-beat piano remains relieved
- ✅ All The Things not over-thinned
- ✅ anticipation remains active
- ✅ piano does not accent hi-hat 2/4
- ✅ 2-beat piano non-anchor with drums stays controlled
- ✅ optional fill/variation does not collide with drums
- ✅ drum-piano risk events stay low
- ✅ explicit 5/6-note usage remains low intrusion
- ✅ low register, voice-leading, and dry pedal remain safe
- ✅ bass foundation remains safe
