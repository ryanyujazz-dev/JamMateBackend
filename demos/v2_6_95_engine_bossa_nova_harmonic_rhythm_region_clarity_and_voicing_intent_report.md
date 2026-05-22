# v2_6_95 — Engine Bossa Nova Harmonic-Rhythm Region Clarity + Voicing Intent Audit

Engine version tag: `v2_10_28`

## Scope

Audit and refine Bossa dense harmonic-rhythm / short ChordRegion clarity in-place. Short regions keep ChordRegion-first pattern handling and request lighter existing voicing capabilities through style-level policy intent. No core voicing source/projection/selector changes, no new pattern vocabulary, no expression numeric changes, API, Agent, or HarmonyOS changes.

## Static audit

- Arrangement policy version: `v2_6_95`
- Voicing policy metadata version: `v2_6_95`
- Dense short-region threshold: `2.25`
- Dense config preferred content/root support: `guide_tone` / `rootless_preferred`
- Half-region candidate function: `dense_harmonic_rhythm_light_clarity_adaptation`

## Runtime Blue Bossa audits

### 3 choruses / seed `22705`

- MIDI: `demos/v2_6_95_blue_bossa_3x_bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_demo.mid`
- Notes by track: `{'piano': 352, 'bass': 102, 'drums': 102}`
- Non-core / Class A / Class B event counts: `77` / `68` / `9`
- Short-region piano events: `12`
- Short-region content families: `{'guide_tone': 12}`
- Short-region densities: `{'2': 12}`
- Short-region root-included / span violations: `0` / `0`
- Ordinary-region content families: `{'seventh_chord_basic': 65, 'rooted_color': 7, 'guide_tone': 20}`
- Expression warnings/missing/cross-region: `0` / `0` / `0`
- Active anticipations: `14`

### 5 choruses / seed `22755`

- MIDI: `demos/v2_6_95_blue_bossa_5x_bossa_nova_harmonic_rhythm_region_clarity_and_voicing_intent_demo.mid`
- Notes by track: `{'piano': 580, 'bass': 170, 'drums': 170}`
- Non-core / Class A / Class B event counts: `116` / `104` / `12`
- Short-region piano events: `20`
- Short-region content families: `{'guide_tone': 20}`
- Short-region densities: `{'2': 20}`
- Short-region root-included / span violations: `0` / `0`
- Ordinary-region content families: `{'seventh_chord_basic': 106, 'rooted_color': 12, 'guide_tone': 34}`
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

`v2_6_96_engine_bossa_nova_bass_and_drums_identity_audit`
