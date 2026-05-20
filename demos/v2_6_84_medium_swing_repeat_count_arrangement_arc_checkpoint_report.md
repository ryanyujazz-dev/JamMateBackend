# v2_6_84 — Medium Swing Repeat-Count-Aware Arrangement Arc Checkpoint

## Scope
Repeat-count-aware Medium Swing macro-energy checkpoint. It declares and audits a style-owned semantic arc policy for arbitrary user-selected repeat counts, including 1x, 2x, 3x, 5x, 6x, 8x, 9x, 10x, and long practice loops such as 50x. Runtime MIDI demos cover 3x and 5x full-band samples only; 50x is validated by policy simulation to avoid generating very long MIDI during checkpoint work. No new patterns, core voicing changes, expression numeric changes, API, Agent, or HarmonyOS changes are made.

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
- MIDI: `demos/v2_6_84_all_the_things_you_are_3x_medium_swing_repeat_count_arrangement_arc_checkpoint_demo.mid`
- Piano/Bass/Drums notes: 786 / 462 / 864
- Piano active patterns: 195
- 2-beat anchor ratio: 0.8077
- Anticipations: 8
- 5-note / 6-note: 6 / 0 (ratio 0.0308)
- Low-register dense events: 0

### Autumn Leaves — 3x
- MIDI: `demos/v2_6_84_autumn_leaves_3x_medium_swing_repeat_count_arrangement_arc_checkpoint_demo.mid`
- Piano/Bass/Drums notes: 754 / 396 / 768
- Piano active patterns: 187
- 2-beat anchor ratio: 0.8759
- Anticipations: 13
- 5-note / 6-note: 6 / 0 (ratio 0.0321)
- Low-register dense events: 0

### All the Things You Are — 5x
- MIDI: `demos/v2_6_84_all_the_things_you_are_5x_medium_swing_repeat_count_arrangement_arc_checkpoint_demo.mid`
- Piano/Bass/Drums notes: 1314 / 756 / 1440
- Piano active patterns: 327
- 2-beat anchor ratio: 0.875
- Anticipations: 10
- 5-note / 6-note: 6 / 0 (ratio 0.0183)
- Low-register dense events: 0

### Autumn Leaves — 5x
- MIDI: `demos/v2_6_84_autumn_leaves_5x_medium_swing_repeat_count_arrangement_arc_checkpoint_demo.mid`
- Piano/Bass/Drums notes: 1285 / 661 / 1280
- Piano active patterns: 320
- 2-beat anchor ratio: 0.8405
- Anticipations: 22
- 5-note / 6-note: 5 / 0 (ratio 0.0156)
- Low-register dense events: 0

## Aggregate
- Runtime chorus counts: [3, 5]
- Total piano/bass/drums notes: 4139 / 2275 / 4352
- Total anticipations: 53
- Total 5/6 ratio: 0.0224
- Low-register dense events: 0
- Voice-leading warnings: 0

## Acceptance
- [x] v2_6_84 repeat-count arc declared
- [x] policy covers requested repeat counts
- [x] 50x loop uses reset/develop/peak/release waves
- [x] 50x loop is not monotonic ramp
- [x] 3x is not the only modeled case
- [x] runtime demos include 3x and 5x
- [x] full-band tracks present
- [x] anticipation remains active
- [x] 5/6-note remains low-intrusion
- [x] 5/6-note stays out of ordinary body
- [x] low register remains clear
- [x] voice leading remains safe
- [x] Medium Swing remains dry

Acceptance Passed: True
