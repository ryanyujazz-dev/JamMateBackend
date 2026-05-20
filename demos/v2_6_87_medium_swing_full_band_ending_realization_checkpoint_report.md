# v2_6_87 — Medium Swing Full-Band Ending Realization Checkpoint

## Scope
Medium Swing full-band ending realization checkpoint after the user-approved repeat-count-aware arrangement arc.  It audits piano ending subset stability, bass continuity, drum/piano density, explicit 5/6-note low-intrusion, low-register clarity, and dry swing behavior on 3x and 5x full-band demos.  It includes a generic terminal-ending anticipation guard so the final downbeat is not anticipated away; otherwise it does not add ending patterns, change multipliers, modify core voicing, write expression numbers, or touch API/Agent/HarmonyOS.

## Runtime full-band ending demos
### All the Things You Are — 3x
- MIDI: `demos/v2_6_87_all_the_things_you_are_3x_medium_swing_full_band_ending_realization_checkpoint_demo.mid`
- Piano/Bass/Drums notes: 786 / 460 / 864
- Piano active patterns: 195
- 2-beat anchor ratio: 0.9583
- Anticipations: 3 (ending 0)
- Ending pattern events: 2
- Ending stable settle ratio: 1.0
- Ending push/active events: 0
- Ending arc final-release ratio: 1.0
- Ending 5/6-note events: 0
- 5-note / 6-note: 6 / 0 (ratio 0.0308)
- Ending low-register dense events: 0

### Autumn Leaves — 3x
- MIDI: `demos/v2_6_87_autumn_leaves_3x_medium_swing_full_band_ending_realization_checkpoint_demo.mid`
- Piano/Bass/Drums notes: 744 / 394 / 768
- Piano active patterns: 185
- 2-beat anchor ratio: 0.8963
- Anticipations: 12 (ending 0)
- Ending pattern events: 1
- Ending stable settle ratio: 1.0
- Ending push/active events: 0
- Ending arc final-release ratio: 1.0
- Ending 5/6-note events: 0
- 5-note / 6-note: 4 / 0 (ratio 0.0216)
- Ending low-register dense events: 0

### All the Things You Are — 5x
- MIDI: `demos/v2_6_87_all_the_things_you_are_5x_medium_swing_full_band_ending_realization_checkpoint_demo.mid`
- Piano/Bass/Drums notes: 1325 / 767 / 1440
- Piano active patterns: 330
- 2-beat anchor ratio: 0.878
- Anticipations: 16 (ending 0)
- Ending pattern events: 1
- Ending stable settle ratio: 1.0
- Ending push/active events: 0
- Ending arc final-release ratio: 1.0
- Ending 5/6-note events: 0
- 5-note / 6-note: 5 / 0 (ratio 0.0152)
- Ending low-register dense events: 0

### Autumn Leaves — 5x
- MIDI: `demos/v2_6_87_autumn_leaves_5x_medium_swing_full_band_ending_realization_checkpoint_demo.mid`
- Piano/Bass/Drums notes: 1265 / 657 / 1280
- Piano active patterns: 315
- 2-beat anchor ratio: 0.9067
- Anticipations: 23 (ending 0)
- Ending pattern events: 2
- Ending stable settle ratio: 1.0
- Ending push/active events: 0
- Ending arc final-release ratio: 1.0
- Ending 5/6-note events: 0
- 5-note / 6-note: 5 / 0 (ratio 0.0159)
- Ending low-register dense events: 0

## Aggregate
- Runtime chorus counts: [3, 5]
- Total piano/bass/drums notes: 4120 / 2278 / 4352
- Total anticipations: 54
- Ending anticipations: 0
- Min ending stable settle ratio: 1.0
- Ending push/active events: 0
- Ending 5/6-note events: 0
- Total 5/6 ratio: 0.0195
- Low-register dense events: 0
- Voice-leading warnings: 0

## Acceptance
- [x] v2_6_87 ending realization checkpoint declared
- [x] v2_6_86 listening refinement remains declared
- [x] v2_6_85 runtime arc remains declared
- [x] 50x loop remains long-loop safe
- [x] runtime demos include 3x and 5x
- [x] full-band tracks present
- [x] runtime arc metadata covers piano events
- [x] listening refinement metadata covers piano events
- [x] ending checkpoint metadata covers piano events
- [x] ending checkpoint metadata is behavior-preserving
- [x] ending regions favor stable settle
- [x] ending has no active/push/fill risk
- [x] ending arc is final release
- [x] anticipation remains active
- [x] terminal ending is not anticipated away
- [x] 5/6-note remains low-intrusion
- [x] 5/6-note stays out of ordinary body
- [x] ending low register remains clear
- [x] full low register remains clear
- [x] voice leading remains safe
- [x] bass continuity remains safe
- [x] Medium Swing remains dry

Acceptance Passed: True
