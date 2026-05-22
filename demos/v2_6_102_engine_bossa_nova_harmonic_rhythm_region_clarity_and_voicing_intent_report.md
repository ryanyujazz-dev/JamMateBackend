# v2_6_102 — Engine Bossa Nova No Forced 2/3-Note Voicing Policy Audit

Engine version tag: `v2_10_28`

## Scope

Audit and refine Bossa dense harmonic-rhythm / short ChordRegion voicing policy in-place. Short regions keep ChordRegion-first pattern handling but no longer force 2-note guide-tone or 3-note low-density voicings; they use the normal Bossa 4-to-5-note voicing policy. No core voicing source/projection/selector changes, no new pattern vocabulary, no expression numeric changes, API, Agent, or HarmonyOS changes.

## Static audit

- Arrangement policy version: `v2_6_102`
- Voicing policy metadata version: `v2_6_102`
- Dense short-region threshold: `2.25`
- Dense config preferred content/root support: `rootless_A` / `rootless_allowed`
- Avoid forced 2-note / 3-note: `True` / `True`
- Half-region candidate function: `dense_harmonic_rhythm_normal_voicing_adaptation`

## Runtime Blue Bossa audits

### 3 choruses / seed `22705`

- MIDI: `demos/v2_6_102_blue_bossa_3x_bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_demo.mid`
- Notes by track: `{'piano': 412, 'bass': 96, 'drums': 585}`
- Non-core / Class A / Class B event counts: `76` / `68` / `8`
- Short-region piano events: `12`
- Short-region content families: `{'seventh_chord_basic': 6, 'rooted_color': 6}`
- Short-region densities: `{'4': 12}`
- Short-region root-included / span violations: `12` / `0`
- Ordinary-region content families: `{'seventh_chord_basic': 80, 'rooted_color': 11}`
- Expression warnings/missing/cross-region: `0` / `0` / `0`
- Active anticipations: `14`

### 5 choruses / seed `22755`

- MIDI: `demos/v2_6_102_blue_bossa_5x_bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_demo.mid`
- Notes by track: `{'piano': 672, 'bass': 160, 'drums': 977}`
- Non-core / Class A / Class B event counts: `124` / `118` / `6`
- Short-region piano events: `20`
- Short-region content families: `{'seventh_chord_basic': 10, 'rooted_color': 10}`
- Short-region densities: `{'4': 20}`
- Short-region root-included / span violations: `20` / `0`
- Ordinary-region content families: `{'seventh_chord_basic': 128, 'rooted_color': 20}`
- Expression warnings/missing/cross-region: `0` / `0` / `0`
- Active anticipations: `23`

## Acceptance

Passed: `True`

```json
{
  "style_and_policy_registered": true,
  "in_place_boundaries_preserved": true,
  "voicing_policy_declares_dense_short_region_intent": true,
  "runtime_blue_bossa_full_band_passes": true
}
```

## Recommended next task

`v2_6_103_engine_bossa_nova_kick_bass_lock_and_low_frequency_shadow_refinement`
