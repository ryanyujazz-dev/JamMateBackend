# v2_6_68 — Medium Swing ExpressionPolicy V1 Numeric Calibration

v2_6_68 calibrates Medium Swing piano comping ExpressionProfile defaults against V1 soft_hold/light_stab/accent_stab/backbeat_hold/final_hold numeric ranges. It changes expression policy only; pattern candidates remain semantic-only and ChordRegion-first.

## Static expression policy audit

- Arrangement / expression versions: `v2_6_68` / `v2_6_68`
- V1 ticks per beat: `120`
- Profiles outside V1 ranges: `0`
- Forbidden pattern expression candidates: `0`
- Bar-first two_chord_bar candidates: `0`

### Calibrated profiles

| profile | semantic hint | velocity | velocity range | duration | duration range | articulation | touch |
|---|---:|---:|---:|---:|---:|---|---|
| `comp_medium` | `soft_hold` | `54` | `(48, 59)` | `0.95` | `(0.7, 1.166667)` | `sustain` | `clear` |
| `comp_short` | `light_stab` | `56` | `(48, 65)` | `0.62` | `(0.516667, 0.733333)` | `short` | `clear` |
| `comp_accent` | `accent_stab` | `66` | `(60, 70)` | `0.54` | `(0.483333, 0.6)` | `accent` | `accented` |
| `comp_backbeat_hold` | `backbeat_hold` | `58` | `(51, 64)` | `0.78` | `(0.633333, 0.9)` | `sustain` | `clear` |
| `comp_accent_hold` | `accent_hold_from_accent_stab_plus_hold_semantics` | `64` | `(60, 70)` | `0.78` | `(0.633333, 0.9)` | `accent` | `accented` |
| `comp_final_hold` | `final_hold` | `45` | `(44, 45)` | `1.92` | `(1.833333, 2.0)` | `sustain` | `warm` |

## Runtime standard-tune audit

### All the Things You Are

- MIDI: `demos/v2_6_68_all_the_things_you_are_medium_swing_expression_policy_v1_numeric_calibration_demo.mid`
- Piano expression events / calibrated metadata events: `200` / `200`
- Profile counts: `{'comp_accent_hold': 18, 'comp_short': 52, 'comp_backbeat_hold': 55, 'comp_medium': 75}`
- Realized velocity ranges by profile: `{'comp_accent_hold': [64, 64], 'comp_short': [56, 56], 'comp_backbeat_hold': [58, 58], 'comp_medium': [54, 54]}`
- Realized duration ranges by profile: `{'comp_accent_hold': [1.053333, 1.666667], 'comp_short': [0.333333, 0.62], 'comp_backbeat_hold': [1.0, 2.0], 'comp_medium': [1.0, 4.0]}`
- Hold boundary guard / clamped-to-region events: `148` / `21`
- Forbidden expression / bar-first events: `0` / `0`
- Top note max / >=75 / voice-leading warnings: `72` / `0` / `0`

### Autumn Leaves

- MIDI: `demos/v2_6_68_autumn_leaves_medium_swing_expression_policy_v1_numeric_calibration_demo.mid`
- Piano expression events / calibrated metadata events: `230` / `230`
- Profile counts: `{'comp_medium': 114, 'comp_short': 69, 'comp_backbeat_hold': 38, 'comp_accent_hold': 9}`
- Realized velocity ranges by profile: `{'comp_medium': [54, 54], 'comp_short': [56, 56], 'comp_backbeat_hold': [58, 58], 'comp_accent_hold': [64, 64]}`
- Realized duration ranges by profile: `{'comp_medium': [0.666667, 4.0], 'comp_short': [0.333333, 0.62], 'comp_backbeat_hold': [1.0, 2.0], 'comp_accent_hold': [1.666667, 1.666667]}`
- Hold boundary guard / clamped-to-region events: `161` / `29`
- Forbidden expression / bar-first events: `0` / `0`
- Top note max / >=75 / voice-leading warnings: `72` / `0` / `0`

## Acceptance

Passed: `True`

- `static: arrangement declares v2_6_68 expression calibration`: `True`
- `static: expression policy declares v2_6_68 calibration`: `True`
- `static: all calibrated profiles inside V1 reference ranges`: `True`
- `static: no pattern candidate writes final expression values`: `True`
- `static: no bar-first/two-chord-bar markers remain`: `True`
- `all_the_things_you_are: generation ok`: `True`
- `all_the_things_you_are: calibrated expression metadata present`: `True`
- `all_the_things_you_are: hold boundary guard still active`: `True`
- `all_the_things_you_are: no pattern events contain concrete expression values`: `True`
- `all_the_things_you_are: no bar-first two_chord_bar runtime events`: `True`
- `all_the_things_you_are: top register calm`: `True`
- `all_the_things_you_are: voice-leading warnings calm`: `True`
- `autumn_leaves: generation ok`: `True`
- `autumn_leaves: calibrated expression metadata present`: `True`
- `autumn_leaves: hold boundary guard still active`: `True`
- `autumn_leaves: no pattern events contain concrete expression values`: `True`
- `autumn_leaves: no bar-first two_chord_bar runtime events`: `True`
- `autumn_leaves: top register calm`: `True`
- `autumn_leaves: voice-leading warnings calm`: `True`

## Recommended next tasks

- `v2_6_69_engine_medium_swing_piano_standard_tune_listening_checkpoint`
- `v2_6_70_engine_medium_swing_ending_specific_region_context_candidate_subset_policy`
