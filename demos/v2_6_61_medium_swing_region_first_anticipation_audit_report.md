# v2_6_61 — Medium Swing Region-First Anticipation Compatibility Checkpoint

Audit that Medium Swing anticipation remains ChordRegion-first after the region-length piano comping work: anticipated next-region starts are placed at previous_region.duration_beats - 0.5, so 4-beat regions use local 3.5 and 2-beat regions use local 1.5. This checkpoint does not add new patterns, voicings, gestures, expression parameters, or bar-first/two-chord-bar routing.

## All the Things You Are

- MIDI: `demos/v2_6_61_all_the_things_you_are_medium_swing_region_first_anticipation_demo.mid`
- Anticipation events / active / suppressed: `8` / `8` / `0`
- Target local counts: `{'3.5': 7, '1.5': 1}`
- Previous-region duration counts: `{'4.0': 7, '2.0': 1}`
- 2-beat previous-tail anticipations: `1`
- 4-beat previous-tail anticipations: `7`
- Region-first version counts: `{'v2_6_61': 8}`
- Invalid rows: `[]`
- Top note max / >=75 / voice-leading warnings: `72` / `0` / `0`

## Autumn Leaves

- MIDI: `demos/v2_6_61_autumn_leaves_medium_swing_region_first_anticipation_demo.mid`
- Anticipation events / active / suppressed: `3` / `3` / `0`
- Target local counts: `{'1.5': 2, '3.5': 1}`
- Previous-region duration counts: `{'2.0': 2, '4.0': 1}`
- 2-beat previous-tail anticipations: `2`
- 4-beat previous-tail anticipations: `1`
- Region-first version counts: `{'v2_6_61': 3}`
- Invalid rows: `[]`
- Top note max / >=75 / voice-leading warnings: `72` / `0` / `0`

## Acceptance

Passed: `True`

- `all_the_things_you_are: generation ok`: `True`
- `all_the_things_you_are: active anticipations have region-first metadata`: `True`
- `all_the_things_you_are: no invalid region-first anticipation rows`: `True`
- `all_the_things_you_are: top register calm`: `True`
- `all_the_things_you_are: voice-leading warnings calm`: `True`
- `autumn_leaves: generation ok`: `True`
- `autumn_leaves: active anticipations have region-first metadata`: `True`
- `autumn_leaves: no invalid region-first anticipation rows`: `True`
- `autumn_leaves: top register calm`: `True`
- `autumn_leaves: voice-leading warnings calm`: `True`
- `combined: observed at least one 2-beat previous-region local 2& anticipation`: `True`
