# v2_6_137 — Engine Ballad Hint Timbre Variation and Offbeat Density Calibration

Engine version tag: `v2_10_28`

## Scope

Vary Ballad transition-hint timbre across standard brush-kit entries (snare, cross-stick, hat, ride/cymbal, tom-brush lanes) while reducing articulated offbeat density. The logical brush path still includes swing-8 offbeats, but many offbeats remain motion-only; explicit tap-drag/single-stroke fills remain vocabulary only. No piano/bass/voicing/API/Agent/HarmonyOS change.

## Static audit

- Arrangement policy version: `v2_6_137`
- Brush source assumed: `True`
- Scope: `bar_level_brush_time_feel_with_region_projection`
- Motion points: `['1', '1&', '2', '2&', '3', '3&', '4', '4&']`

## Misty runtime audit

- MIDI: `demos/v2_6_137_misty_jazz_ballad_hint_timbre_and_offbeat_density_demo.mid`
- Note events by track: `{'piano': 1026, 'bass': 150, 'drums': 807}`
- Brush feel cell counts: `{'pure_legato_brush': 12, 'brush_swing_skip': 49, 'basic_brush_time': 49, 'brush_two_feel': 40}`
- Brush event drum counts: `{'snare': 447, 'low_tom': 26, 'kick': 154, 'hihat_pedal': 178, 'cross_stick': 10, 'ride': 4}`
- Brush event slot counts: `{'1': 322, '2': 288, '3': 50, '4': 82, '2&': 42, '4&': 29, '3&': 6}`
- Classic fill cell counts: `{'section_entry_brush_bloom': 4, 'none': 56, 'v1_drag_to_4_hint': 8, 'v1_soft_swish_4and_hint': 6, 'bridge_entry_low_tom_bloom_hint': 22, 'cadence_3_to_4_tom_hat_hint': 16, 'turnaround_cross_stick_4_hint': 16, 'turnaround_2and_4_hat_hint': 10, 'section_tail_4_hat_cymbal_hint': 12}`
- Classic fill event count: `0`
- Section transition hint event count: `52`

## Hint timbre/offbeat-density focus demo

- MIDI: `demos/v2_6_137_jazz_ballad_hint_timbre_and_offbeat_density_focus_demo.mid`
- Bars: `[{'label': 'basic_time', 'bar_start': 0.0, 'brush_classic_fill_cell': 'none', 'event_slot_counts': {'1': 2, '2': 2, '3': 1, '4': 2}, 'foreground_fill_event_count': 0}, {'label': 'v1_drag_to_4_hint', 'bar_start': 4.0, 'brush_classic_fill_cell': 'v1_drag_to_4_hint', 'event_slot_counts': {'1': 1, '2': 1, '3': 1, '3&': 1, '4': 3}, 'foreground_fill_event_count': 0}, {'label': 'turnaround_cross_stick_4_hint', 'bar_start': 8.0, 'brush_classic_fill_cell': 'turnaround_cross_stick_4_hint', 'event_slot_counts': {'1': 2, '2': 2, '3': 2, '3&': 1, '4': 3}, 'foreground_fill_event_count': 0}, {'label': 'v1_section_breath_4_to_4and_hint', 'bar_start': 12.0, 'brush_classic_fill_cell': 'section_tail_4_hat_cymbal_hint', 'event_slot_counts': {'1': 1, '2': 1, '3': 1, '4': 3, '4&': 1}, 'foreground_fill_event_count': 0}, {'label': 'bridge_entry_low_tom_bloom_hint', 'bar_start': 16.0, 'brush_classic_fill_cell': 'bridge_entry_low_tom_bloom_hint', 'event_slot_counts': {'1': 3, '2': 1, '3': 1, '4': 2}, 'foreground_fill_event_count': 0}, {'label': 'final_release', 'bar_start': 20.0, 'brush_classic_fill_cell': 'final_brush_release', 'event_slot_counts': {'1': 1, '2&': 1}, 'foreground_fill_event_count': 2}]`

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
  "skip_bar_uses_reduced_offbeat_articulation": true,
  "offbeats_use_shared_swing8_timing": true,
  "split_regions_project_same_bar_plan_with_reduced_offbeats": true,
  "phrase_tail_keeps_4and_transition_hint": true,
  "section_hints_are_not_foreground_lane": true,
  "section_hints_use_subtle_hint_dynamic_profiles": true,
  "pickup_uses_timbre_varied_turnaround_hint": true,
  "section_tail_uses_hat_cymbal_timbre_hint": true,
  "cadence_uses_timbre_varied_hint_or_v1_drag": true,
  "v1_reference_primitives_declared": true,
  "no_default_long_explicit_fill_cells": true,
  "final_release_contextual": true,
  "misty_runtime_has_section_hint_events": true,
  "misty_runtime_hint_timbre_varies": true,
  "misty_runtime_offbeats_reduced": true,
  "misty_runtime_has_drum_layer": true,
  "piano_bass_still_present": true
}
```

Recommended next task: `v2_6_138_engine_ballad_hint_timbre_and_offbeat_density_listening_calibration`
