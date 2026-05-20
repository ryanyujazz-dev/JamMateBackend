# v2_6_82 — Medium Swing Bass–Piano Interaction Audit

Acceptance Passed: **True**

## Scope
Full-band bass–piano interaction audit after v2_6_80/v2_6_81. It checks piano/bass low-register overlap, exact low unisons, two-beat region density sharing, bass continuity, optional 5/6-note SPREAD intrusion, and dry Medium Swing pedal behavior. For explicitly enabled optional 5/6-note grouped SPREAD demos, v2_6_82 requests stricter C3+ foundation-register metadata through the existing style/event policy adapter so piano does not duplicate the bass walking foundation in the low register. Core voicing internals, pattern rhythm, expression numbers, API, Agent, and HarmonyOS are unchanged.

## Aggregate Bass–Piano Interaction Audit
- Tracks present in all tunes: True
- Note events by track: piano=1538, bass=854, drums=1632
- Piano active pattern events / voicing events: 382 / 382
- Piano 2-beat active / start anchors / anchor ratio: 158 / 142 / 0.8987
- Active anticipations / 2-beat previous-tail anticipations: 19 / 14
- 5-note / 6-note events / ratio: 10 / 0 / 0.0262
- 5/6 low below C3 / low unison with bass: 0 / 0
- Bass–piano joined events: 378
- Bass–piano exact low unisons / close low spacing: 1 / 3
- Bass–piano foundation gap too tight events: 3
- Bar 88 bass–piano exact low unisons: 0
- Piano low/top note range: 48–73
- Voice-leading warnings / low-register dense events: 0 / 0
- Bass span / continuity / repeated-root violations: 0 / 0 / 0
- Bass root-echo bad same/timing: 0 / 0
- Pedal CC64 / warnings: 0 / 0

## Per Tune
### All the Things You Are
- MIDI: `demos/v2_6_82_all_the_things_you_are_medium_swing_bass_piano_interaction_audit_demo.mid`
- Performance: 3 choruses, 108 bars
- Note events by track: `{'piano': 773, 'bass': 456, 'drums': 864}`
- Piano active / 2-beat active / 2-beat anchor ratio: 192 / 24 / 0.875
- Active anticipations / 2-beat previous-tail: 5 / 1
- Piano density counts: `{'4': 187, '5': 5}`
- Piano recipe counts: `{'d4__2plus2__seventh_chord_basic__rootless_allowed': 122, 'd4__1plus3__seventh_chord_basic__rootless_allowed': 65, 'spread_2plus3_contract': 5}`
- 5-note / 6-note: 5 / 0
- 5/6 low below C3 / low unison with bass: 0 / 0
- Bass–piano exact low unisons / close low spacing / tight foundation gap: 1 / 3 / 3
- Bar 88 rows: `[{'event_id': 'c2_b15_ch0_medium_swing_piano_charleston_1_2and_0', 'region_id': 'c2_b15_ch0', 'chord_symbol': 'Gmaj7', 'pattern_id': 'medium_swing_piano_charleston_1_2and', 'density': 5, 'recipe_id': 'spread_2plus3_contract', 'midi_notes': [55, 59, 66, 69, 71], 'notes_below_c3': 0, 'low_note': 55, 'top_note': 71, 'region_performance_bar_index': 87, 'region_length_family': 'four_beat_region', 'authorized_5_6_scene': True, 'top_voice_leap_exceeds_max': False}, {'event_id': 'c2_b15_ch0_medium_swing_piano_charleston_1_2and_1', 'region_id': 'c2_b15_ch0', 'chord_symbol': 'Gmaj7', 'pattern_id': 'medium_swing_piano_charleston_1_2and', 'density': 5, 'recipe_id': 'spread_2plus3_contract', 'midi_notes': [55, 59, 66, 69, 71], 'notes_below_c3': 0, 'low_note': 55, 'top_note': 71, 'region_performance_bar_index': 87, 'region_length_family': 'four_beat_region', 'authorized_5_6_scene': True, 'top_voice_leap_exceeds_max': False}]`

### Autumn Leaves
- MIDI: `demos/v2_6_82_autumn_leaves_medium_swing_bass_piano_interaction_audit_demo.mid`
- Performance: 3 choruses, 96 bars
- Note events by track: `{'piano': 765, 'bass': 398, 'drums': 768}`
- Piano active / 2-beat active / 2-beat anchor ratio: 190 / 134 / 0.903
- Active anticipations / 2-beat previous-tail: 14 / 13
- Piano density counts: `{'4': 185, '5': 5}`
- Piano recipe counts: `{'d4__1plus3__seventh_chord_basic__rootless_allowed': 73, 'd4__2plus2__seventh_chord_basic__rootless_allowed': 112, 'spread_2plus3_contract': 5}`
- 5-note / 6-note: 5 / 0
- 5/6 low below C3 / low unison with bass: 0 / 0
- Bass–piano exact low unisons / close low spacing / tight foundation gap: 0 / 0 / 0
- Bar 88 rows: `[]`

## Acceptance Checks

- ✅ v2_6_82 bass-piano interaction audit declared
- ✅ post-density full-band checkpoint retained
- ✅ two-beat density relief retained
- ✅ existing 5/6-note capability remains explicit opt-in
- ✅ low-register clarity guard retained
- ✅ bass-piano interaction guard declared
- ✅ no core voicing change declared
- ✅ all full-band tracks present
- ✅ 2-beat piano remains relieved
- ✅ All The Things not over-thinned
- ✅ generic anticipation still active
- ✅ explicit 5/6-note usage remains low intrusion
- ✅ optional 5/6-note no longer lives below C3
- ✅ optional 5/6-note avoids low bass unison
- ✅ low-register dense piano guard ok
- ✅ bar 88 bass-piano low unison cleared
- ✅ close low spacing stays rare
- ✅ voice-leading and top register ok
- ✅ bass foundation audit ok
- ✅ root echo and dry pedal ok
