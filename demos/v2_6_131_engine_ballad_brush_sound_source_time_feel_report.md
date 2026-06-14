# v2_6_131 — Engine Ballad Brush Sound Source Time Feel

Engine version tag: `v2_10_28`

## Scope

Reset Jazz Ballad drums around a real brush sound source: bar-level brush time feel, continuous eighth sweep path, contextual 1&/2&/3&/4& offbeat policy, soft 2/4 foot anchors, felt-not-heard feather kick, phrase breath, and final release. No custom internal brush drum voices, no chord-region dense drum loop, and no piano/bass/voicing/API/Agent/HarmonyOS change.

## Static audit

- Arrangement policy version: `v2_6_131`
- Brush source assumed: `True`
- Scope: `bar_level_brush_time_feel_with_region_projection`
- Motion points: `['1', '1&', '2', '2&', '3', '3&', '4', '4&']`

## Misty runtime audit

- MIDI: `demos/v2_6_131_misty_jazz_ballad_brush_sound_source_time_feel_demo.mid`
- Note events by track: `{'piano': 1026, 'bass': 150, 'drums': 885}`
- Brush feel cell counts: `{'pure_legato_brush': 12, 'brush_swing_skip': 49, 'basic_brush_time': 49, 'brush_two_feel': 40}`
- Brush event drum counts: `{'snare': 572, 'kick': 154, 'hihat_pedal': 168}`
- Brush event slot counts: `{'1': 296, '2': 288, '3': 50, '4': 72, '4&': 42, '2&': 138, '3&': 8}`

## Acceptance

Passed: `True`

```json
{
  "version_declared": true,
  "brush_source_assumed": true,
  "bar_level_not_chord_loop": true,
  "motion_grid_includes_offbeats": true,
  "no_custom_internal_brush_drums": true,
  "standard_drum_entries_only": true,
  "basic_bar_has_brush_pressure_hat_and_feather": true,
  "skip_bar_articulates_2and_4and": true,
  "split_regions_project_same_bar_plan": true,
  "phrase_breath_articulates_3and_and_4and": true,
  "final_release_contextual": true,
  "misty_runtime_has_drum_layer": true,
  "piano_bass_still_present": true
}
```

Recommended next task: `v2_6_132_engine_ballad_brush_sound_source_listening_calibration`
