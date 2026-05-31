# v2_6_119 Medium Swing Two-beat Phrase Pair Local 1& Hold

This checkpoint adds one pitchless 2-beat piano comping candidate and a history-aware phrase-pair weighting policy. It keeps the vocabulary ChordRegion-local: first 2-beat region local 1+2 can be followed by the next 2-beat region local 1& hold, corresponding to full-bar beat 3&.

## Demo / audit outputs

### two_beat_phrase_focus

- MIDI: `/mnt/data/jammate_v26119/JamMateBackend/demos/v2_6_119_two_beat_phrase_focus_medium_swing_two_beat_phrase_pair_demo.mid`
- Piano events: 32
- Call `start_local2` count: 16
- Response `local1and_hold` count: 4

### autumn_leaves

- MIDI: `/mnt/data/jammate_v26119/JamMateBackend/demos/v2_6_119_autumn_leaves_medium_swing_two_beat_phrase_pair_demo.mid`
- Piano events: 214
- Call `start_local2` count: 60
- Response `local1and_hold` count: 23

### all_the_things_you_are

- MIDI: `/mnt/data/jammate_v26119/JamMateBackend/demos/v2_6_119_all_the_things_you_are_medium_swing_two_beat_phrase_pair_demo.mid`
- Piano events: 198
- Call `start_local2` count: 10
- Response `local1and_hold` count: 5

## Boundary

- Pattern remains pitchless and region-local.
- `local1and_hold` carries `soft_hold` semantic hint only; ExpressionResolver maps it to `comp_medium` hold and clamps it inside the current ChordRegion.
- Phrase pair is weighted from recent selected candidate metadata; no bar-first/two-chord-bar selector was restored.
- No voicing, altered dominant, API, Agent, or HarmonyOS behavior changed.
