# v2_6_69 — Medium Swing Piano Standard-Tune Listening Checkpoint

Contract version: `v2_10_8`

Behavior-preserving Medium Swing piano listening checkpoint after v2_6_67 history scoring and v2_6_68 ExpressionPolicy calibration. Generates three-chorus standard-tune demos and audits that pattern, expression, voicing, anticipation, and ChordRegion boundary contracts remain separated.

Acceptance Passed: `True`

## Static audit

- Arrangement checkpoint version: `v2_6_69`
- Missing prior policy versions: `0`
- Pattern candidates: `39`
- Forbidden expression candidates: `0`
- Forbidden voicing candidates: `0`
- Bar-first/two-chord-bar candidates: `0`

## Listening outputs

### All the Things You Are / `all_the_things_you_are`

- MIDI: `demos/v2_6_69_all_the_things_you_are_medium_swing_piano_standard_tune_listening_checkpoint_demo.mid`
- Choruses: `3`; regions: `120`; piano pattern events: `206`
- Pattern region lengths: `{'four_beat_region': 174, 'two_beat_region': 32}`
- Activity classes: `{'offbeat': 27, 'stable': 87, 'active': 6}`
- Candidate flags: `{'no_4and_delayed_tail': 33, 'push': 6, 'active': 6}`
- Consecutive flags: `{'no_4and_delayed_tail': 8}`
- Expression profiles: `{'comp_medium': 66, 'comp_short': 62, 'comp_accent_hold': 27, 'comp_backbeat_hold': 51}`
- Calibrated expression events: `206/206`
- Hold guard / clamped: `144` / `24`
- Expression cross-region: `0`; cross-next warning signal: `42`
- Top note max: `72`; voice-leading warnings: `0`
- Open-drop method counts: `{'drop3': 102, 'drop2': 97, 'drop2_and_4': 7}`

### Autumn Leaves / `autumn_leaves`

- MIDI: `demos/v2_6_69_autumn_leaves_medium_swing_piano_standard_tune_listening_checkpoint_demo.mid`
- Choruses: `3`; regions: `162`; piano pattern events: `234`
- Pattern region lengths: `{'two_beat_region': 179, 'four_beat_region': 55}`
- Activity classes: `{'stable': 136, 'offbeat': 25, 'active': 1}`
- Candidate flags: `{'push': 23, 'no_4and_delayed_tail': 31, 'active': 1}`
- Consecutive flags: `{'no_4and_delayed_tail': 1}`
- Expression profiles: `{'comp_medium': 108, 'comp_backbeat_hold': 44, 'comp_short': 74, 'comp_accent_hold': 8}`
- Calibrated expression events: `234/234`
- Hold guard / clamped: `160` / `29`
- Expression cross-region: `0`; cross-next warning signal: `18`
- Top note max: `73`; voice-leading warnings: `0`
- Open-drop method counts: `{'drop2': 161, 'drop2_and_4': 15, 'drop3': 58}`

## Acceptance checks

- `PASS` — static: arrangement declares v2_6_69 listening checkpoint
- `PASS` — static: all prior Medium Swing piano milestones still declared
- `PASS` — static: ExpressionPolicy remains v2_6_68 calibrated
- `PASS` — static: no pattern candidate writes final expression values
- `PASS` — static: no pattern candidate writes voicing output
- `PASS` — static: no bar-first/two-chord-bar markers remain
- `PASS` — all_the_things_you_are: generation ok
- `PASS` — all_the_things_you_are: three-chorus listening loop
- `PASS` — all_the_things_you_are: piano comping events present
- `PASS` — all_the_things_you_are: v2_6_67 history metadata covers selected piano events
- `PASS` — all_the_things_you_are: v2_6_68 calibrated expression covers piano events
- `PASS` — all_the_things_you_are: hold boundary guard still active
- `PASS` — all_the_things_you_are: no expression cross-region sustain
- `PASS` — all_the_things_you_are: no pattern events contain concrete expression values
- `PASS` — all_the_things_you_are: no pattern events contain voicing output
- `PASS` — all_the_things_you_are: no bar-first two_chord_bar runtime events
- `PASS` — all_the_things_you_are: busy does not repeat
- `PASS` — all_the_things_you_are: tail-push does not repeat
- `PASS` — all_the_things_you_are: top register calm
- `PASS` — all_the_things_you_are: voice-leading warnings calm
- `PASS` — autumn_leaves: generation ok
- `PASS` — autumn_leaves: three-chorus listening loop
- `PASS` — autumn_leaves: piano comping events present
- `PASS` — autumn_leaves: v2_6_67 history metadata covers selected piano events
- `PASS` — autumn_leaves: v2_6_68 calibrated expression covers piano events
- `PASS` — autumn_leaves: hold boundary guard still active
- `PASS` — autumn_leaves: no expression cross-region sustain
- `PASS` — autumn_leaves: no pattern events contain concrete expression values
- `PASS` — autumn_leaves: no pattern events contain voicing output
- `PASS` — autumn_leaves: no bar-first two_chord_bar runtime events
- `PASS` — autumn_leaves: busy does not repeat
- `PASS` — autumn_leaves: tail-push does not repeat
- `PASS` — autumn_leaves: top register calm
- `PASS` — autumn_leaves: voice-leading warnings calm

## Recommended next tasks

- `v2_6_70_engine_medium_swing_ending_specific_region_context_candidate_subset_policy`
- `v2_6_71_engine_medium_swing_optional_fill_variation_vocabulary_activation`
