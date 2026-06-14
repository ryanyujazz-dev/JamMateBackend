# v2_6_134 — Engine Ballad Audible Classic Brush Fill Rework

Engine version tag: `v2_10_28`

## Scope

Rework Jazz Ballad classic brush fills from metadata-only overlays into an audible foreground fill lane: background snare sweep is ducked inside the fill window, fill dynamics use a clear pickup→drag→release contour, and all offbeats keep shared swing-8 timing. No custom brush voices, no chord-region fill loop, and no piano/bass/voicing/API/Agent/HarmonyOS change.

## Static audit

- Arrangement policy version: `v2_6_134`
- Brush source assumed: `True`
- Scope: `bar_level_brush_time_feel_with_region_projection`
- Motion points: `['1', '1&', '2', '2&', '3', '3&', '4', '4&']`

## Misty runtime audit

- MIDI: `demos/v2_6_134_misty_jazz_ballad_audible_classic_brush_fill_rework_demo.mid`
- Note events by track: `{'piano': 1026, 'bass': 150, 'drums': 921}`
- Brush feel cell counts: `{'pure_legato_brush': 12, 'brush_swing_skip': 49, 'basic_brush_time': 49, 'brush_two_feel': 40}`
- Brush event drum counts: `{'snare': 570, 'kick': 154, 'hihat_pedal': 168}`
- Brush event slot counts: `{'1': 296, '2': 288, '3': 48, '4': 72, '4&': 36, '2&': 138, '3&': 14}`
- Classic fill cell counts: `{'none': 82, 'tap_drag_tap_release': 14, 'turnaround_sweep_roll': 16, 'soft_pickup_to_4': 26, 'single_stroke_4_to_next': 12}`
- Classic fill event count: `64`

## Fill-focus demo

- MIDI: `demos/v2_6_134_jazz_ballad_audible_classic_brush_fill_focus_demo.mid`
- Bars: `[{'label': 'basic_time', 'bar_start': 0.0, 'brush_classic_fill_cell': 'none', 'event_slot_counts': {'1': 2, '2': 2, '2&': 1, '3': 1, '4': 2, '4&': 1}, 'foreground_fill_event_count': 0}, {'label': 'tap_drag_tap_release', 'bar_start': 4.0, 'brush_classic_fill_cell': 'tap_drag_tap_release', 'event_slot_counts': {'1': 1, '2': 1, '2&': 1, '3&': 1, '4': 2, '4&': 1}, 'foreground_fill_event_count': 4}, {'label': 'soft_pickup_to_4', 'bar_start': 8.0, 'brush_classic_fill_cell': 'soft_pickup_to_4', 'event_slot_counts': {'1': 2, '2': 2, '2&': 1, '3': 2, '3&': 1, '4': 2}, 'foreground_fill_event_count': 2}, {'label': 'single_stroke_4_to_next', 'bar_start': 12.0, 'brush_classic_fill_cell': 'single_stroke_4_to_next', 'event_slot_counts': {'1': 1, '2': 1, '3': 1, '3&': 1, '4': 2, '4&': 1}, 'foreground_fill_event_count': 4}, {'label': 'turnaround_sweep_roll', 'bar_start': 16.0, 'brush_classic_fill_cell': 'turnaround_sweep_roll', 'event_slot_counts': {'1': 1, '2': 1, '2&': 1, '3': 1, '3&': 1, '4': 1, '4&': 1}, 'foreground_fill_event_count': 4}, {'label': 'final_release', 'bar_start': 20.0, 'brush_classic_fill_cell': 'final_brush_release', 'event_slot_counts': {'1': 1, '2&': 1}, 'foreground_fill_event_count': 2}]`

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
  "classic_fill_uses_foreground_lane": true,
  "classic_fill_uses_audible_dynamic_profiles": true,
  "classic_fill_ducks_overlapping_background_snare": true,
  "pickup_fill_uses_3and_to_4": true,
  "section_fill_uses_single_stroke_4": true,
  "final_release_contextual": true,
  "misty_runtime_has_classic_fill_events": true,
  "misty_runtime_has_drum_layer": true,
  "piano_bass_still_present": true
}
```

Recommended next task: `v2_6_135_engine_ballad_brush_fill_listening_calibration`
