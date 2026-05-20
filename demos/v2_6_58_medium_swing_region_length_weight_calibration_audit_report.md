# v2_6_58 — Medium Swing Piano Region-Length Weight Calibration

Calibrate existing ChordRegion-length-aware Medium Swing piano comping vocabulary weights; keep stable cells primary, offbeat conversation secondary, active controlled, native tail-push rare; no new pattern source or bar-first path.

## Candidate weight ratios

- `four_beat_region`: `{'active': 0.0341, 'offbeat': 0.2263, 'stable': 0.7363, 'tail_push': 0.0033}`
- `two_beat_region`: `{'offbeat': 0.1223, 'stable': 0.8777}`
- `one_beat_region`: `{'inactive': 0.0, 'offbeat': 0.0099, 'stable': 0.9901}`

## Runtime outputs

### All the Things You Are

- Piano events: `204`
- Class ratios: `{'active': 0.0441, 'offbeat': 0.2696, 'stable': 0.6863}`
- Top patterns: `[('medium_swing_piano_anchor_1_3', 28), ('medium_swing_piano_charleston_1_2and', 24), ('medium_swing_piano_1_3and_answer', 22), ('medium_swing_piano_backbeat_2_4', 18), ('medium_swing_piano_reverse_charleston_1and_3', 18), ('medium_swing_piano_anchor_1', 17), ('medium_swing_piano_2and_4_answer', 16), ('medium_swing_piano_two_beat_region_start_local2', 12), ('medium_swing_piano_two_beat_region_start_anchor', 10), ('medium_swing_piano_2_3and_answer', 10), ('medium_swing_piano_1_2and_4', 9), ('medium_swing_piano_two_beat_region_start_local2and', 6), ('medium_swing_piano_two_beat_region_local2_only', 5), ('medium_swing_piano_light_2and_only', 5), ('medium_swing_piano_anchor_3', 2), ('medium_swing_piano_1_4_tail', 2)]`
- Region length counts: `{'four_beat_region': 171, 'two_beat_region': 33}`
- Top note max: `72`
- Voice-leading warnings: `0`

### Autumn Leaves

- Piano events: `224`
- Class ratios: `{'offbeat': 0.2277, 'stable': 0.7723}`
- Top patterns: `[('medium_swing_piano_two_beat_region_start_anchor', 55), ('medium_swing_piano_two_beat_region_start_local2', 48), ('medium_swing_piano_two_beat_region_start_local2and', 36), ('medium_swing_piano_two_beat_region_local2_only', 33), ('medium_swing_piano_1_3and_answer', 10), ('medium_swing_piano_charleston_1_2and', 10), ('medium_swing_piano_anchor_1_3', 8), ('medium_swing_piano_anchor_1', 6), ('medium_swing_piano_2and_4_answer', 4), ('medium_swing_piano_reverse_charleston_1and_3', 4), ('medium_swing_piano_light_2and_only', 3), ('medium_swing_piano_2_3and_answer', 2), ('medium_swing_piano_1_4_tail', 2), ('medium_swing_piano_two_beat_region_local1and_only', 2), ('medium_swing_piano_anchor_3', 1)]`
- Region length counts: `{'two_beat_region': 174, 'four_beat_region': 50}`
- Top note max: `72`
- Voice-leading warnings: `0`
