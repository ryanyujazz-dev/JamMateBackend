# v2_6_120 — Engine Bossa Nova Two-beat Phrase Pair Local 1& Hold

Engine version tag: `v2_10_28`

## Scope

Add the user-requested Bossa two-beat phrase as style-owned, pitchless, ChordRegion-local piano comping vocabulary: one 2-beat region states local 1+2, and the following 2-beat region may answer on local 1& with a hold. The shared phrase-pair weighting now reads style metadata rather than hard-coding a Medium Swing cell name.

## Static audit

- Policy version: `v2_6_120`
- Call pattern: `bossa_piano_half_region_1_2` beats `[0.0, 1.0]` role `call`
- Response pattern: `bossa_piano_half_region_1and_hold` beats `[0.5]` role `response`
- Response expression hint: `cell_soft_hold` / semantic `soft_hold`
- Shared policy no Medium Swing cell hard-code: `True`

## Runtime demos

### Bossa Two-Beat Phrase Focus

- MIDI: `demos/v2_6_120_bossa_nova_two_beat_phrase_focus_demo.mid`
- Pattern counts: `{'bossa_piano_half_region_1_2': 24, 'bossa_piano_half_region_1and_hold': 12}`
- Phrase policy status counts: `{'phrase_call_preferred': 24, 'phrase_response_preferred_after_call': 12}`
- Response local beats: `[0.5]`

### Blue Bossa

- MIDI: `demos/v2_6_120_blue_bossa_bossa_nova_two_beat_phrase_pair_demo.mid`
- Pattern counts: `{'bossa_piano_core_batida_1_2_3and': 15, 'bossa_piano_cell_A_1_3and': 20, 'bossa_piano_cell_A_1_3': 10, 'bossa_piano_cell_A_1': 9, 'bossa_piano_cell_A_1_2_3and': 15, 'bossa_piano_cell_A_1_2and': 16, 'bossa_piano_half_region_1_2': 6, 'bossa_piano_half_region_1and_hold': 3, 'bossa_piano_cell_B_1and_3': 2, 'bossa_piano_cell_B_1and_3and': 2, 'bossa_piano_cell_A_1_4and': 2}`
- Phrase policy status counts: `{'phrase_call_preferred': 6, 'phrase_response_preferred_after_call': 3}`
- Response local beats: `[0.5]`

## Acceptance

Passed: `True`

```json
{
  "style_policy_and_candidates_present": true,
  "phrase_shape_is_region_local": true,
  "boundaries_preserved": true,
  "shared_policy_is_not_medium_swing_cell_hardcoded": true,
  "focus_demo_contains_phrase_response": true,
  "blue_bossa_demo_still_generates": true,
  "expression_boundary_clean": true
}
```

Recommended next task: `v2_6_121_engine_bossa_nova_two_beat_phrase_pair_listening_calibration`
