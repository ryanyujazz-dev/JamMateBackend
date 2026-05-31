# v2_6_97 — Engine Bossa Nova Repeat-Count Arrangement Arc Policy

Engine version tag: `v2_10_28`

## Scope

Add a Bossa-owned repeat-count-aware arrangement arc in place. The arc shapes existing piano comping candidates for arbitrary repeat counts without creating a selector, adding vocabulary, cloning Medium Swing, changing expression numbers, or touching core voicing/API/Agent/HarmonyOS.

## Static audit

- Arrangement policy version: `v2_6_97`
- Repeat counts audited: `[1, 2, 3, 5, 10, 50]`
- Long-loop 50x has reset / breath / final release: `True` / `True` / `final_soft_release`
- Three-chorus hardcoded: `False`
- Medium Swing clone: `False`

## Runtime Blue Bossa audits

### 3 choruses / seed `22807`

- MIDI: `demos/v2_6_97_blue_bossa_3x_bossa_nova_repeat_count_arrangement_arc_policy_demo.mid`
- Notes by track: `{'piano': 368, 'bass': 96, 'drums': 600}`
- Piano arc coverage: `104` / `104` = `1.0`
- Piano arc phases: `{'head_in_core_identity': 35, 'gentle_lift': 35, 'final_soft_release': 34}`
- Piano runtime intents: `{'core_identity_reset': 35, 'gentle_transition_lift': 35, 'settled_release': 34}`
- Piano arc status counts: `{'bossa_arc_core_identity_bonus': 9, 'bossa_arc_neutral': 51, 'bossa_arc_reset_color_guard': 2, 'bossa_arc_dense_region_passthrough': 12, 'bossa_arc_gentle_lift': 23, 'bossa_arc_lift_color_guard': 3, 'bossa_arc_release_activity_guard': 3, 'bossa_arc_release_settle': 1}`
- Arc multiplier min/max: `0.2736` / `1.28`

### 5 choruses / seed `22857`

- MIDI: `demos/v2_6_97_blue_bossa_5x_bossa_nova_repeat_count_arrangement_arc_policy_demo.mid`
- Notes by track: `{'piano': 584, 'bass': 160, 'drums': 1000}`
- Piano arc coverage: `165` / `165` = `1.0`
- Piano arc phases: `{'head_in_core_identity': 34, 'loop_wave_warm_flow': 33, 'loop_wave_breath_space': 34, 'loop_wave_gentle_lift': 33, 'final_soft_release': 31}`
- Piano runtime intents: `{'core_identity_reset': 34, 'warm_batida_flow': 33, 'breath_space': 34, 'gentle_transition_lift': 33, 'settled_release': 31}`
- Piano arc status counts: `{'bossa_arc_core_identity_bonus': 9, 'bossa_arc_neutral': 48, 'bossa_arc_dense_region_passthrough': 20, 'bossa_arc_warm_flow_A': 25, 'bossa_arc_warm_flow_color': 4, 'bossa_arc_breath_density_guard': 6, 'bossa_arc_breath_space': 20, 'bossa_arc_gentle_lift': 19, 'bossa_arc_lift_color_guard': 1, 'bossa_arc_release_activity_guard': 8, 'bossa_arc_release_settle': 5}`
- Arc multiplier min/max: `0.2736` / `1.28`

## Acceptance

Passed: `True`

```json
{
  "style_and_policy_registered": true,
  "in_place_boundaries_preserved": true,
  "repeat_count_policy_is_bossa_specific": true,
  "runtime_blue_bossa_arc_metadata_passes": true
}
```

## Recommended next task

`v2_6_98_engine_bossa_nova_full_band_arrangement_arc_listening_refinement`
