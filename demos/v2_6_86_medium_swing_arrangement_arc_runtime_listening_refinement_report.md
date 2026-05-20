# v2_6_86 — Medium Swing Arrangement Arc Runtime Listening Refinement Checkpoint

## Scope
Repeat-count-aware Medium Swing macro-energy checkpoint. It declares and audits a style-owned semantic arc policy for arbitrary user-selected repeat counts, including 1x, 2x, 3x, 5x, 6x, 8x, 9x, 10x, and long practice loops such as 50x. Runtime MIDI demos cover 3x and 5x full-band samples only after user listening approval; 50x is validated by policy simulation to avoid generating very long MIDI during checkpoint work. No multiplier changes, new patterns, core voicing changes, expression numeric changes, API, Agent, or HarmonyOS changes are made.

## Repeat-count policy simulation
- 1x: ['single_pass_balanced']
- 2x: ['head_in_clear', 'final_head_out_release']
- 3x: ['head_in_clear', 'late_build', 'final_head_out_release']
- 5x: ['head_in_clear', 'loop_wave_develop', 'loop_wave_peak', 'loop_wave_release', 'final_head_out_release']
- 6x: ['head_in_clear', 'loop_wave_develop', 'loop_wave_peak', 'loop_wave_release', 'loop_wave_reset', 'final_head_out_release']
- 8x: ['head_in_clear', 'loop_wave_develop', 'loop_wave_peak', 'loop_wave_release', 'loop_wave_reset', 'loop_wave_develop', 'loop_wave_peak', 'final_head_out_release']
- 9x: ['head_in_clear', 'loop_wave_develop', 'loop_wave_peak', 'loop_wave_release', 'loop_wave_reset', 'loop_wave_develop', 'loop_wave_peak', 'loop_wave_release', 'final_head_out_release']
- 10x: ['head_in_clear', 'loop_wave_develop', 'loop_wave_peak', 'loop_wave_release', 'loop_wave_reset', 'loop_wave_develop', 'loop_wave_peak', 'loop_wave_release', 'loop_wave_reset', 'final_head_out_release']
- 50x: ['head_in_clear', 'loop_wave_develop', 'loop_wave_peak', 'loop_wave_release', 'loop_wave_reset', 'loop_wave_develop', 'loop_wave_peak', 'loop_wave_release', 'loop_wave_reset', 'loop_wave_develop', 'loop_wave_peak', 'loop_wave_release', '…', 'final_head_out_release']

## Runtime full-band demos
### All the Things You Are — 3x
- MIDI: `demos/v2_6_86_all_the_things_you_are_3x_medium_swing_arrangement_arc_runtime_listening_refinement_demo.mid`
- Piano/Bass/Drums notes: 776 / 457 / 864
- Piano active patterns: 193
- 2-beat anchor ratio: 0.9167
- Anticipations: 10
- Runtime arc intent events: 193 (coverage 1.0)
- Runtime arc listening refinement events: 193 (coverage 1.0)
- Runtime arc phases: ['final_head_out_release', 'head_in_clear', 'late_build']
- 5-note / 6-note: 4 / 0 (ratio 0.0207)
- Low-register dense events: 0

### Autumn Leaves — 3x
- MIDI: `demos/v2_6_86_autumn_leaves_3x_medium_swing_arrangement_arc_runtime_listening_refinement_demo.mid`
- Piano/Bass/Drums notes: 777 / 391 / 768
- Piano active patterns: 193
- 2-beat anchor ratio: 0.854
- Anticipations: 16
- Runtime arc intent events: 193 (coverage 1.0)
- Runtime arc listening refinement events: 193 (coverage 1.0)
- Runtime arc phases: ['final_head_out_release', 'head_in_clear', 'late_build']
- 5-note / 6-note: 5 / 0 (ratio 0.0259)
- Low-register dense events: 0

### All the Things You Are — 5x
- MIDI: `demos/v2_6_86_all_the_things_you_are_5x_medium_swing_arrangement_arc_runtime_listening_refinement_demo.mid`
- Piano/Bass/Drums notes: 1309 / 776 / 1440
- Piano active patterns: 326
- 2-beat anchor ratio: 0.925
- Anticipations: 18
- Runtime arc intent events: 326 (coverage 1.0)
- Runtime arc listening refinement events: 326 (coverage 1.0)
- Runtime arc phases: ['final_head_out_release', 'head_in_clear', 'loop_wave_develop', 'loop_wave_peak', 'loop_wave_release']
- 5-note / 6-note: 5 / 0 (ratio 0.0153)
- Low-register dense events: 0

### Autumn Leaves — 5x
- MIDI: `demos/v2_6_86_autumn_leaves_5x_medium_swing_arrangement_arc_runtime_listening_refinement_demo.mid`
- Piano/Bass/Drums notes: 1265 / 669 / 1280
- Piano active patterns: 315
- 2-beat anchor ratio: 0.864
- Anticipations: 24
- Runtime arc intent events: 315 (coverage 1.0)
- Runtime arc listening refinement events: 315 (coverage 1.0)
- Runtime arc phases: ['final_head_out_release', 'head_in_clear', 'loop_wave_develop', 'loop_wave_peak', 'loop_wave_release']
- 5-note / 6-note: 5 / 0 (ratio 0.0159)
- Low-register dense events: 0

## Aggregate
- Runtime chorus counts: [3, 5]
- Total piano/bass/drums notes: 4127 / 2293 / 4352
- Total anticipations: 68
- Total runtime arc intent events: 1027
- Min runtime arc intent coverage ratio: 1.0
- Min runtime listening refinement coverage ratio: 1.0
- Total 5/6 ratio: 0.0185
- Low-register dense events: 0
- Voice-leading warnings: 0

## Acceptance
- [x] v2_6_84 repeat-count arc remains declared
- [x] v2_6_85 runtime intent usage remains declared
- [x] v2_6_86 listening refinement declared
- [x] policy covers requested repeat counts
- [x] 50x loop uses reset/develop/peak/release waves
- [x] 50x loop is not monotonic ramp
- [x] 3x is not the only modeled case
- [x] runtime demos include 3x and 5x
- [x] runtime arc intent metadata covers piano events
- [x] listening refinement metadata covers piano events
- [x] listening refinement is behavior-preserving
- [x] full-band tracks present
- [x] anticipation remains active
- [x] 5/6-note remains low-intrusion
- [x] 5/6-note stays out of ordinary body
- [x] low register remains clear
- [x] voice leading remains safe
- [x] Medium Swing remains dry

Acceptance Passed: True
