# v2_6_96 — Engine Bossa Nova Bass + Drums Identity Audit

Engine version tag: `v2_10_28`

## Scope

Replace the old Bossa bass one-size root/fifth pattern and drums hihat placeholder in place. Bass now declares root/fifth support for full regions and root-only support for split/short ChordRegions; drums now declare region-local shaker/cross-stick/light-kick identity. No piano vocabulary change, no parallel selector, no core voicing, API, Agent, or HarmonyOS change.

## Static audit

- Arrangement policy version: `v2_6_96`
- Bass identity: `root_fifth_support_not_walking`
- Drums identity: `shaker_cross_stick_light_kick`
- Full-region bass candidate: `bossa_bass_root_fifth_2bar_A`
- Split-region bass candidate: `bossa_bass_split_region_root_only`
- Full-region drums candidate: `bossa_drums_shaker_cross_stick_kick_full_region_A`

## Runtime Blue Bossa audits

### 3 choruses / seed `22706`

- MIDI: `demos/v2_6_96_blue_bossa_3x_bossa_nova_bass_and_drums_identity_demo.mid`
- Notes by track: `{'piano': 362, 'bass': 96, 'drums': 600}`
- Planned bass degrees: `{'root': 51, 'fifth': 45}`
- Planned bass length profiles: `{'bossa_root': 45, 'bossa_fifth': 45, 'bossa_split_root': 6}`
- Bass walking-like / short-region non-root events: `0` / `0`
- Planned drum voices: `{'shaker_time': 384, 'cross_stick_A_1': 24, 'cross_stick_A_2and': 24, 'cross_stick_A_4': 24, 'soft_kick_root_shadow': 51, 'soft_kick_fifth_shadow': 45, 'cross_stick_B_2': 21, 'cross_stick_B_3and': 21, 'cross_stick_split_mark': 6}`
- Planned drum kinds: `{'shaker': 384, 'cross_stick': 120, 'kick': 96}`
- Drum swing/rock placeholder events: `0`

### 5 choruses / seed `22756`

- MIDI: `demos/v2_6_96_blue_bossa_5x_bossa_nova_bass_and_drums_identity_demo.mid`
- Notes by track: `{'piano': 588, 'bass': 160, 'drums': 1000}`
- Planned bass degrees: `{'root': 85, 'fifth': 75}`
- Planned bass length profiles: `{'bossa_root': 75, 'bossa_fifth': 75, 'bossa_split_root': 10}`
- Bass walking-like / short-region non-root events: `0` / `0`
- Planned drum voices: `{'shaker_time': 640, 'cross_stick_A_1': 40, 'cross_stick_A_2and': 40, 'cross_stick_A_4': 40, 'soft_kick_root_shadow': 85, 'soft_kick_fifth_shadow': 75, 'cross_stick_B_2': 35, 'cross_stick_B_3and': 35, 'cross_stick_split_mark': 10}`
- Planned drum kinds: `{'shaker': 640, 'cross_stick': 200, 'kick': 160}`
- Drum swing/rock placeholder events: `0`

## Acceptance

Passed: `True`

```json
{
  "style_and_policy_registered": true,
  "in_place_boundaries_preserved": true,
  "bass_static_identity_declared": true,
  "drums_static_identity_declared": true,
  "runtime_blue_bossa_full_band_identity_passes": true
}
```

## Recommended next task

`v2_6_97_engine_bossa_nova_repeat_count_arrangement_arc_policy`
