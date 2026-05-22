# v2_6_98 — Engine Bossa Nova Full-Band Arrangement Arc Listening Refinement

Engine version tag: `v2_10_28`

## Scope

Refine the Bossa repeat-count arrangement arc at full-band level. Piano already uses the v2_6_97 arc; v2_6_98 lets bass and drums read the same arc to become softer in breath/release and gently lifted in transition phases, without adding vocabulary, creating a selector, changing core voicing, or touching API/Agent/HarmonyOS.

## Static audit

- policy version: `v2_6_98`
- boundaries: no parallel selector=True, no bar-first restore=True, no new vocabulary=True, no core voicing change=True
- tracks: `['piano', 'bass', 'drums']`
- breath band: `breath_space`
- lift band: `gentle_lift`
- release band: `soft_release`

## Runtime audits

### Blue Bossa 3x

- MIDI: `demos/v2_6_98_blue_bossa_3x_bossa_nova_full_band_arrangement_arc_listening_refinement_demo.mid`
- piano/bass/drums notes: `368 / 96 / 600`
- full-band arc coverage piano/bass/drums: `1.0 / 1.0 / 1.0`
- bass dynamic profiles: `{'bossa_root': 15, 'bossa_fifth': 15, 'bossa_split_root': 2, 'bossa_root_lift': 15, 'bossa_fifth_lift': 15, 'bossa_split_root_lift': 2, 'bossa_root_release': 15, 'bossa_fifth_release': 15, 'bossa_split_root_release': 2}`
- drum dynamic profiles: `{'shaker_light': 128, 'bossa_cross_main': 23, 'bossa_cross_light': 17, 'bossa_kick_root': 17, 'bossa_kick_fifth': 15, 'shaker_lift': 128, 'bossa_cross_lift': 23, 'bossa_cross_lift_light': 17, 'bossa_kick_root_lift': 17, 'bossa_kick_fifth_lift': 15, 'shaker_release': 128, 'bossa_cross_release': 23, 'bossa_cross_release_light': 17, 'bossa_kick_root_release': 17, 'bossa_kick_fifth_release': 15}`
- bass walking-like events: `0`
- drum swing/rock events: `0`

### Blue Bossa 5x

- MIDI: `demos/v2_6_98_blue_bossa_5x_bossa_nova_full_band_arrangement_arc_listening_refinement_demo.mid`
- piano/bass/drums notes: `568 / 160 / 1000`
- full-band arc coverage piano/bass/drums: `1.0 / 1.0 / 1.0`
- bass dynamic profiles: `{'bossa_root': 30, 'bossa_fifth': 30, 'bossa_split_root': 4, 'bossa_root_soft': 15, 'bossa_fifth_soft': 15, 'bossa_split_root_soft': 2, 'bossa_root_lift': 15, 'bossa_fifth_lift': 15, 'bossa_split_root_lift': 2, 'bossa_root_release': 15, 'bossa_fifth_release': 15, 'bossa_split_root_release': 2}`
- drum dynamic profiles: `{'shaker_light': 256, 'bossa_cross_main': 46, 'bossa_cross_light': 34, 'bossa_kick_root': 34, 'bossa_kick_fifth': 30, 'shaker_breath': 128, 'bossa_cross_breath': 23, 'bossa_cross_breath_light': 17, 'bossa_kick_root_breath': 17, 'bossa_kick_fifth_breath': 15, 'shaker_lift': 128, 'bossa_cross_lift': 23, 'bossa_cross_lift_light': 17, 'bossa_kick_root_lift': 17, 'bossa_kick_fifth_lift': 15, 'shaker_release': 128, 'bossa_cross_release': 23, 'bossa_cross_release_light': 17, 'bossa_kick_root_release': 17, 'bossa_kick_fifth_release': 15}`
- bass walking-like events: `0`
- drum swing/rock events: `0`

## Acceptance

- passed: `True`
- checks: `{'style_and_policy_registered': True, 'in_place_boundaries_preserved': True, 'track_scope_is_full_band': True, 'refinement_profiles_are_distinct': True, 'runtime_blue_bossa_full_band_arc_passes': True}`

## Recommended next task

`v2_6_99_engine_bossa_nova_style_baseline_phase_completion_checkpoint`
