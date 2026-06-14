# v2_6_133 — Engine Ballad Classic Brush Fill Overlays

Engine version tag: `v2_10_28`

## Scope

Add phrase-level classic Jazz Ballad brush fill overlays on top of the real brush sound-source time-feel contract: soft pickup-to-4, tap-drag-tap release, single-stroke-4 to next phrase, turnaround sweep roll, and final release. All offbeats keep shared swing-8 timing; no custom brush voices, no chord-region fill loop, and no piano/bass/voicing/API/Agent/HarmonyOS change.

## Static audit

- Arrangement policy version: `v2_6_133`
- Brush source assumed: `True`
- Scope: `bar_level_brush_time_feel_with_region_projection`
- Motion points: `['1', '1&', '2', '2&', '3', '3&', '4', '4&']`

## Misty runtime audit

- MIDI: `demos/v2_6_133_misty_jazz_ballad_classic_brush_fill_overlays_demo.mid`
- Note events by track: `{'piano': 1026, 'bass': 150, 'drums': 963}`
- Brush feel cell counts: `{'pure_legato_brush': 12, 'brush_swing_skip': 49, 'basic_brush_time': 49, 'brush_two_feel': 40}`
- Brush event drum counts: `{'snare': 636, 'kick': 154, 'hihat_pedal': 168}`
- Brush event slot counts: `{'1': 296, '2': 288, '3': 54, '4': 84, '4&': 48, '2&': 168, '3&': 20}`
- Classic fill cell counts: `{'none': 82, 'tap_drag_tap_release': 30, 'soft_pickup_to_4': 26, 'single_stroke_4_to_next': 12}`
- Classic fill event count: `64`

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
  "offbeats_use_shared_swing8_timing": true,
  "split_regions_project_same_bar_plan": true,
  "phrase_breath_articulates_3and_and_4and": true,
  "pickup_fill_uses_3and_to_4": true,
  "section_fill_uses_single_stroke_4": true,
  "final_release_contextual": true,
  "misty_runtime_has_classic_fill_events": true,
  "misty_runtime_has_drum_layer": true,
  "piano_bass_still_present": true
}
```

Recommended next task: `v2_6_134_engine_ballad_brush_fill_listening_calibration`
