# v2_6_100 — Engine Bossa Nova Drum Shaker Microdynamics + Pulse Shape

Engine version tag: `v2_10_28`

## Scope

Refine the existing Bossa shaker/hi-hat proxy in place. Pattern candidates keep the same shaker/cross-stick/light-kick identity shape and only annotate semantic straight-8th pulse slots; the shared percussion realizer maps those slots to microdynamic velocity shape. No piano, bass, voicing, API, Agent, or HarmonyOS change.

## Static audit

- policy version: `v2_6_100`
- no parallel selector: `True`
- no new pattern vocabulary: `True`
- full shaker pulse slots: `['primary_clear', 'offbeat_light', 'secondary_mid', 'offbeat_feather', 'primary_clear', 'offbeat_light', 'secondary_mid', 'offbeat_feather']`
- forbidden pattern numeric keys: `[]`

## Runtime audits

### Blue Bossa 3x

- MIDI: `demos/v2_6_100_blue_bossa_3x_bossa_nova_drum_shaker_microdynamics_and_pulse_shape_demo.mid`
- notes piano/bass/drums: `328` / `96` / `600`
- shaker microdynamic coverage: `1.0`
- shaker unique velocities: `21`
- shaker slot average velocity: `{'offbeat_feather': 28.67, 'offbeat_light': 30.67, 'primary_clear': 36.67, 'secondary_mid': 33.67}`
- shaker profile min/max: `{'shaker_lift': [32, 42], 'shaker_light': [29, 39], 'shaker_release': [22, 32]}`
- drum swing/rock events: `0`

### Blue Bossa 5x

- MIDI: `demos/v2_6_100_blue_bossa_5x_bossa_nova_drum_shaker_microdynamics_and_pulse_shape_demo.mid`
- notes piano/bass/drums: `568` / `160` / `1000`
- shaker microdynamic coverage: `1.0`
- shaker unique velocities: `21`
- shaker slot average velocity: `{'offbeat_feather': 28.19, 'offbeat_light': 30.2, 'primary_clear': 36.19, 'secondary_mid': 33.21}`
- shaker profile min/max: `{'shaker_breath': [24, 34], 'shaker_lift': [32, 42], 'shaker_light': [29, 39], 'shaker_release': [22, 32]}`
- drum swing/rock events: `0`

## Acceptance

```json
{
  "checks": {
    "style_and_policy_registered": true,
    "boundary_preserved": true,
    "pattern_layer_stays_semantic": true,
    "full_region_has_shaker_pulse_slots": true,
    "split_region_stays_region_local": true,
    "runtime_blue_bossa_shaker_microdynamics_passes": true
  },
  "passed": true
}
```

Recommended next task: `v2_6_101_engine_bossa_nova_cross_stick_phrase_local_contour_refinement`
