# v2_6_101 — Engine Bossa Nova Cross-stick Phrase-local Contour Refinement

Engine version tag: `v2_10_28`

## Scope

Refine the existing Bossa cross-stick layer in place. The same shaker/cross-stick/light-kick percussion candidate remains active, but cross-stick events now carry phrase-local A/B slots and arc-aware contour-density metadata. The shared percussion realizer maps those semantic slots to small velocity-shape offsets. No piano, bass, core voicing, API, Agent, HarmonyOS, or parallel percussion selector change.

## Static audit

- policy version: `v2_6_101`
- no parallel selector: `True`
- no new pattern vocabulary: `True`
- full A cross slots: `['A_beat1_phrase_anchor', 'A_2and_syncopated_answer', 'A_beat4_phrase_tail']`
- full B cross slots: `['B_beat2_response_anchor', 'B_3and_light_answer']`
- breath A cross slots: `['A_beat1_phrase_anchor', 'A_2and_syncopated_answer']`
- release A/B cross slots: `['A_beat1_phrase_anchor', 'A_2and_syncopated_answer']` / `['B_beat2_response_anchor']`
- forbidden pattern numeric keys: `[]`

## Runtime audits

### Blue Bossa 3x

- MIDI: `demos/v2_6_101_blue_bossa_3x_bossa_nova_cross_stick_phrase_local_contour_refinement_demo.mid`
- notes piano/bass/drums: `332` / `96` / `585`
- cross-stick contour coverage: `1.0`
- cross-stick phrase patterns: `['A', 'B', 'split']`
- cross-stick slot counts: `{'A_beat1_phrase_anchor': 24, 'A_2and_syncopated_answer': 24, 'A_beat4_phrase_tail': 16, 'B_beat2_response_anchor': 21, 'B_3and_light_answer': 14, 'split_region_light_mark': 6}`
- cross-stick contour density counts: `{'identity_clear': 38, 'split_region_single_mark': 6, 'gentle_lift_clear': 38, 'settled_release_sparse': 23}`
- cross-stick slot average velocity: `{'A_2and_syncopated_answer': 34.46, 'A_beat1_phrase_anchor': 42.33, 'A_beat4_phrase_tail': 47.0, 'B_3and_light_answer': 38.57, 'B_beat2_response_anchor': 41.33, 'split_region_light_mark': 32.0}`
- breath A tail push events: `0`
- release tail push events: `0`
- drum swing/rock events: `0`

### Blue Bossa 5x

- MIDI: `demos/v2_6_101_blue_bossa_5x_bossa_nova_cross_stick_phrase_local_contour_refinement_demo.mid`
- notes piano/bass/drums: `556` / `160` / `977`
- cross-stick contour coverage: `1.0`
- cross-stick phrase patterns: `['A', 'B', 'split']`
- cross-stick slot counts: `{'A_beat1_phrase_anchor': 40, 'A_2and_syncopated_answer': 40, 'A_beat4_phrase_tail': 24, 'B_beat2_response_anchor': 35, 'B_3and_light_answer': 28, 'split_region_light_mark': 10}`
- cross-stick contour density counts: `{'identity_clear': 38, 'split_region_single_mark': 10, 'warm_flow_full': 38, 'breath_space_reduced': 30, 'gentle_lift_clear': 38, 'settled_release_sparse': 23}`
- cross-stick slot average velocity: `{'A_2and_syncopated_answer': 33.65, 'A_beat1_phrase_anchor': 41.4, 'A_beat4_phrase_tail': 45.96, 'B_3and_light_answer': 35.0, 'B_beat2_response_anchor': 40.43, 'split_region_light_mark': 31.5}`
- breath A tail push events: `0`
- release tail push events: `0`
- drum swing/rock events: `0`

## Acceptance

```json
{
  "checks": {
    "style_and_policy_registered": true,
    "boundary_preserved": true,
    "pattern_layer_stays_semantic": true,
    "full_region_A_B_slots_are_phrase_local": true,
    "breath_and_release_remove_forward_tail": true,
    "runtime_blue_bossa_cross_stick_contour_passes": true
  },
  "passed": true
}
```

Recommended next task: `v2_6_102_engine_bossa_nova_kick_bass_lock_and_low_frequency_shadow_refinement`
