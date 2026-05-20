# v2_6_67 — Medium Swing Active/Fill/Busy Multi-Region History Scorer

v2_6_67 upgrades the existing Medium Swing piano history scorer in-place with multi-region active/fill/busy/push/tail-push memory. It remains ChordRegion-first and does not write voicing, final expression values, MIDI pitch, duration, velocity, or pedal into the pattern layer.

## Static V2 policy audit

- Pattern / lookup / weight versions: `v2_6_56` / `v2_6_57` / `v2_6_58`
- History scorer compatibility/new version: `v2_6_59` / `v2_6_67`
- Candidate counts total/active: `39` / `37`
- Active by region length: `{'one_beat_region': 2, 'two_beat_region': 6, 'three_beat_region': 1, 'four_beat_region': 28}`
- Active by weight class: `{'stable': 19, 'offbeat': 12, 'active': 2, 'tail_push': 4}`
- Forbidden expression candidates: `0`
- Bar-first two_chord_bar candidates: `0`

## Runtime standard-tune audit

### All the Things You Are

- MIDI: `demos/v2_6_67_all_the_things_you_are_medium_swing_active_fill_busy_history_demo.mid`
- Piano events: `210`
- v2_6_67 metadata events: `210`
- History class counts: `{'stable': 149, 'offbeat': 46, 'active': 15}`
- Active/fill/busy/push/tail-push events: `15` / `0` / `0` / `5` / `0`
- History penalty/bonus events: `12` / `56`
- Active-after-active / busy-near-block / tail-push-cluster penalties: `0` / `0` / `0`
- Stable reset after active/fill/busy: `6` / `0` / `0`
- No-4& recovery after push bonuses: `14`
- Forbidden expression / bar-first events: `0` / `0`
- Top note max / >=75 / voice-leading warnings: `72` / `0` / `0`

### Autumn Leaves

- MIDI: `demos/v2_6_67_autumn_leaves_medium_swing_active_fill_busy_history_demo.mid`
- Piano events: `229`
- v2_6_67 metadata events: `229`
- History class counts: `{'stable': 178, 'offbeat': 51}`
- Active/fill/busy/push/tail-push events: `0` / `0` / `0` / `23` / `0`
- History penalty/bonus events: `17` / `37`
- Active-after-active / busy-near-block / tail-push-cluster penalties: `0` / `0` / `0`
- Stable reset after active/fill/busy: `0` / `0` / `0`
- No-4& recovery after push bonuses: `19`
- Forbidden expression / bar-first events: `0` / `0`
- Top note max / >=75 / voice-leading warnings: `73` / `0` / `0`

## Acceptance

Passed: `True`

- `static: active/fill/busy history policy enabled`: `True`
- `static: active/fill/busy history policy version`: `True`
- `static: no pattern candidate writes final expression values`: `True`
- `static: no bar-first/two-chord-bar markers remain`: `True`
- `all_the_things_you_are: generation ok`: `True`
- `all_the_things_you_are: v2_6_67 metadata present`: `True`
- `all_the_things_you_are: history penalties present`: `True`
- `all_the_things_you_are: no pattern events contain concrete expression values`: `True`
- `all_the_things_you_are: no bar-first two_chord_bar runtime events`: `True`
- `all_the_things_you_are: top register calm`: `True`
- `all_the_things_you_are: voice-leading warnings calm`: `True`
- `autumn_leaves: generation ok`: `True`
- `autumn_leaves: v2_6_67 metadata present`: `True`
- `autumn_leaves: history penalties present`: `True`
- `autumn_leaves: no pattern events contain concrete expression values`: `True`
- `autumn_leaves: no bar-first two_chord_bar runtime events`: `True`
- `autumn_leaves: top register calm`: `True`
- `autumn_leaves: voice-leading warnings calm`: `True`

## Recommended next tasks

- `v2_6_68_engine_medium_swing_expression_policy_v1_numeric_calibration`
- `v2_6_69_engine_medium_swing_piano_standard_tune_listening_checkpoint`
