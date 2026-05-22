# v2_6_94 — Engine Bossa Nova Distance-Aware Expression Calibration

Engine version tag: `v2_10_28`

## Scope

Calibrate Bossa non-core piano cell expression in place. Style-owned ExpressionProfiles declare distance articulation parameters, and the shared core ExpressionResolver applies them after anticipation/timeline rewrite. No Bossa-specific resolver, new pattern vocabulary, core voicing change, MIDI writer change, API, Agent, or HarmonyOS change.

## Static expression audit

- Arrangement policy version: `v2_6_94`
- Resolver hook: `ExpressionResolver.policy_driven_distance_articulation`
- Distance threshold: `1.0`
- Distance-sensitive profiles: `['cell_close_gap_short', 'cell_soft_hold']`
- Legacy alias metadata preserved: `True`

## Runtime Blue Bossa audits

### 3 choruses / seed `22704`

- MIDI: `demos/v2_6_94_blue_bossa_3x_bossa_nova_distance_aware_expression_calibration_demo.mid`
- Notes by track: `{'piano': 404, 'bass': 102, 'drums': 102}`
- Non-core / Class A / Class B event counts: `74` / `73` / `1`
- Distance articulation events: `74`
- Distance articulation branches: `{'sustain': 64, 'short': 10}`
- Expression profiles: `{'core_short': 20, 'core_sustain': 13, 'cell_soft_hold': 69, 'cell_close_gap_short': 5}`
- Expression articulations: `{'short': 30, 'sustain': 77}`
- Expression avg velocity / duration: `48.692` / `1.507`
- Expression warnings / missing / cross-region / cross-next-event / short-overlap / sustain-chop: `0` / `0` / `0` / `0` / `0` / `0`
- Active anticipations / terminal-ending anticipations: `11` / `0`
- Pedal CC64 events: `0`

### 5 choruses / seed `22754`

- MIDI: `demos/v2_6_94_blue_bossa_5x_bossa_nova_distance_aware_expression_calibration_demo.mid`
- Notes by track: `{'piano': 620, 'bass': 170, 'drums': 170}`
- Non-core / Class A / Class B event counts: `130` / `120` / `10`
- Distance articulation events: `130`
- Distance articulation branches: `{'sustain': 115, 'short': 15}`
- Expression profiles: `{'core_short': 26, 'core_sustain': 18, 'cell_soft_hold': 121, 'cell_close_gap_short': 9}`
- Expression articulations: `{'short': 41, 'sustain': 133}`
- Expression avg velocity / duration: `48.201` / `1.521`
- Expression warnings / missing / cross-region / cross-next-event / short-overlap / sustain-chop: `0` / `0` / `0` / `0` / `0` / `0`
- Active anticipations / terminal-ending anticipations: `22` / `0`
- Pedal CC64 events: `0`

## Known next gap

Bossa non-core piano touch is now distance-aware; next pass should audit dense harmonic rhythm / short-region clarity and Bossa voicing intent without changing core voicing.

Recommended next task: `v2_6_95_engine_bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_audit`

## Acceptance

Passed: `True`

- `style_and_policy_registered`: `True`
- `in_place_boundaries_preserved`: `True`
- `expression_policy_declares_distance_profiles`: `True`
- `runtime_blue_bossa_full_band_passes`: `True`
