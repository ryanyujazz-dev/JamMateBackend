# v2_6_103 — Engine Bossa Nova OPEN Voicing + Retired 4-Note Grouping Metadata

Engine version tag: `v2_10_28`

## Scope

Make Bossa piano voicing OPEN-main while keeping normal 4-to-5-note voicing density. Retire the old ordinary 4-note 1+3 / 2+2 functional-grouping metadata from core taxonomy so grouped voicing reports refer only to genuine SPREAD lower/upper contracts. No Bossa parallel selector, no pattern vocabulary change, no expression numeric change, no API/Agent/HarmonyOS change.

## Static audit

- Arrangement policy version: `v2_6_103`
- Preferred disposition: `open`
- Allowed dispositions: `['open', 'closed']`
- Texture runtime family: `open` / `['open']`
- Open methods: `['generic_open', 'drop2', 'drop3']`
- Density range: `4` / `4` / `5`
- Ordinary 4-note recipe: `d4__unGrouped__seventh_chord_basic__rootless_allowed`, grouping=`None`
- Rootless 4-note recipe: `d4__unGrouped__rootless_A__rootless_allowed`, grouping=`None`

## Runtime Blue Bossa audits

### 3 choruses / seed `22803`

- MIDI: `demos/v2_6_103_blue_bossa_3x_bossa_nova_open_voicing_taxonomy_cleanup_demo.mid`
- Notes by track: `{'piano': 404, 'bass': 96, 'drums': 585}`
- Piano active events: `101`
- Dispositions: `{'open': 101}`
- Open methods: `{'generic_open': 83, 'drop2': 18}`
- Densities: `{'4': 101}`
- Content families: `{'seventh_chord_basic': 84, 'rooted_color': 17}`
- Functional groupings: `{'none': 101}`
- Retired 1+3/2+2 grouping events: `0`
- Spread grouping events: `0`
- Expression warnings/missing/cross-region: `0` / `0` / `0`

### 5 choruses / seed `22855`

- MIDI: `demos/v2_6_103_blue_bossa_5x_bossa_nova_open_voicing_taxonomy_cleanup_demo.mid`
- Notes by track: `{'piano': 676, 'bass': 160, 'drums': 977}`
- Piano active events: `169`
- Dispositions: `{'open': 169}`
- Open methods: `{'generic_open': 121, 'drop3': 3, 'drop2': 45}`
- Densities: `{'4': 169}`
- Content families: `{'seventh_chord_basic': 138, 'rooted_color': 31}`
- Functional groupings: `{'none': 169}`
- Retired 1+3/2+2 grouping events: `0`
- Spread grouping events: `0`
- Expression warnings/missing/cross-region: `0` / `0` / `0`

## Acceptance

Passed: `True`

```json
{
  "style_and_arrangement_registered": true,
  "bossa_policy_is_open_main": true,
  "density_stays_normal_4_to_5": true,
  "ordinary_4note_grouping_metadata_retired": true,
  "runtime_blue_bossa_full_band_passes": true
}
```

## Recommended next task

`v2_6_104_engine_bossa_nova_kick_bass_lock_and_low_frequency_shadow_refinement`
