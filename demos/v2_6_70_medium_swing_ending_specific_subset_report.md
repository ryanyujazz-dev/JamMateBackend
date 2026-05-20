# v2_6_70 — Medium Swing Ending-Specific Region Context Candidate Subset Policy

Contract version: `v2_10_8`

Medium Swing piano ending-specific candidate subset policy. Final-bar ChordRegions are reweighted inside the existing region-length pool toward stable region-start settling and away from active/4& push. This does not add an ending selector, new vocabulary, voicing logic, or final expression values.

Acceptance Passed: `True`

## Static audit

- Ending policy version: `v2_6_70`
- Missing prior policy versions: `0`
- Pattern candidates: `39`
- Forbidden expression candidates: `0`
- Forbidden voicing candidates: `0`
- Bar-first/two-chord-bar candidates: `0`

## Listening outputs

### All the Things You Are / `all_the_things_you_are`

- MIDI: `demos/v2_6_70_all_the_things_you_are_medium_swing_ending_specific_subset_demo.mid`
- Choruses: `3`; regions: `120`; piano pattern events: `205`
- Pattern region lengths: `{'four_beat_region': 175, 'two_beat_region': 30}`
- Ending selected region patterns: `3`
- Ending status counts: `{'ending_settle_anchor_preferred': 3}`
- Ending cell counts: `{'1_4': 1, '1': 1, '1_3and': 1}`
- Ending push / active / region-start counts: `0` / `0` / `3`
- Calibrated expression events: `205/205`
- Expression cross-region: `0`; cross-next warning signal: `38`
- Top note max: `72`; voice-leading warnings: `0`
- Open-drop method counts: `{'drop2': 100, 'drop3': 101, 'drop2_and_4': 4}`

### Autumn Leaves / `autumn_leaves`

- MIDI: `demos/v2_6_70_autumn_leaves_medium_swing_ending_specific_subset_demo.mid`
- Choruses: `3`; regions: `162`; piano pattern events: `237`
- Pattern region lengths: `{'two_beat_region': 182, 'four_beat_region': 55}`
- Ending selected region patterns: `3`
- Ending status counts: `{'ending_settle_anchor_preferred': 3}`
- Ending cell counts: `{'1_3': 2, '1_2and': 1}`
- Ending push / active / region-start counts: `0` / `0` / `3`
- Calibrated expression events: `237/237`
- Expression cross-region: `0`; cross-next warning signal: `17`
- Top note max: `72`; voice-leading warnings: `0`
- Open-drop method counts: `{'drop3': 97, 'drop2': 117, 'drop2_and_4': 23}`

## Acceptance checks

- `PASS` — static: arrangement declares v2_6_70 ending-specific subset policy
- `PASS` — static: all prior Medium Swing piano milestones still declared
- `PASS` — static: ExpressionPolicy remains v2_6_68 calibrated
- `PASS` — static: no pattern candidate writes final expression values
- `PASS` — static: no pattern candidate writes voicing output
- `PASS` — static: no bar-first/two-chord-bar markers remain
- `PASS` — all_the_things_you_are: generation ok
- `PASS` — all_the_things_you_are: three-chorus listening loop
- `PASS` — all_the_things_you_are: piano comping events present
- `PASS` — all_the_things_you_are: v2_6_70 metadata reaches runtime piano events
- `PASS` — all_the_things_you_are: ending policy applies to at least final regions
- `PASS` — all_the_things_you_are: ending push selected count remains controlled
- `PASS` — all_the_things_you_are: v2_6_67 history metadata still covers piano events
- `PASS` — all_the_things_you_are: v2_6_68 calibrated expression covers piano events
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
- `PASS` — autumn_leaves: v2_6_70 metadata reaches runtime piano events
- `PASS` — autumn_leaves: ending policy applies to at least final regions
- `PASS` — autumn_leaves: ending push selected count remains controlled
- `PASS` — autumn_leaves: v2_6_67 history metadata still covers piano events
- `PASS` — autumn_leaves: v2_6_68 calibrated expression covers piano events
- `PASS` — autumn_leaves: no expression cross-region sustain
- `PASS` — autumn_leaves: no pattern events contain concrete expression values
- `PASS` — autumn_leaves: no pattern events contain voicing output
- `PASS` — autumn_leaves: no bar-first two_chord_bar runtime events
- `PASS` — autumn_leaves: busy does not repeat
- `PASS` — autumn_leaves: tail-push does not repeat
- `PASS` — autumn_leaves: top register calm
- `PASS` — autumn_leaves: voice-leading warnings calm

## Recommended next tasks

- `v2_6_71_engine_medium_swing_optional_fill_variation_vocabulary_activation`
- `v2_6_72_engine_medium_swing_ending_listening_refinement_after_user_review`
