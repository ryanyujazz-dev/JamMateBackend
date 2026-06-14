# v2_6_136 — Engine Ballad Subtle Transition Hint Vocabulary

Engine version tag: `v2_10_28`

## Scope

Lower automatic Ballad transition hints so they no longer read as foreground fills, and expand the vocabulary using V1-derived primitives: brush_drag_to_4, section_breath, soft_swish_4and, and final_release. Hints ride inside the brush texture with no background ducking; explicit tap-drag/single-stroke fills remain vocabulary only. Offbeats keep shared swing-8 timing; no piano/bass/voicing/API/Agent/HarmonyOS change.

## Static audit

- Arrangement policy version: `v2_6_136`
- Brush source assumed: `True`
- Scope: `bar_level_brush_time_feel_with_region_projection`
- Motion points: `['1', '1&', '2', '2&', '3', '3&', '4', '4&']`

## Misty runtime audit

- MIDI: `demos/v2_6_136_misty_jazz_ballad_subtle_transition_hint_vocabulary_demo.mid`
- Note events by track: `{'piano': 1026, 'bass': 150, 'drums': 957}`
- Brush feel cell counts: `{'pure_legato_brush': 12, 'brush_swing_skip': 49, 'basic_brush_time': 49, 'brush_two_feel': 40}`
- Brush event drum counts: `{'snare': 662, 'kick': 154, 'hihat_pedal': 168}`
- Brush event slot counts: `{'1': 318, '1&': 12, '2': 288, '3': 50, '4': 82, '4&': 48, '2&': 178, '3&': 8}`
- Classic fill cell counts: `{'section_entry_1and_bloom_hint': 4, 'none': 56, 'v1_drag_to_4_hint': 8, 'v1_soft_swish_4and_hint': 6, 'section_entry_soft_1_to_1and_hint': 8, 'cadence_3and_4and_whisper': 16, 'bridge_entry_soft_1_2and_hint': 14, 'turnaround_2and_3and_4and_whisper': 16, 'turnaround_2and_4_hat_hint': 10, 'v1_section_breath_4_to_4and_hint': 12}`
- Classic fill event count: `0`
- Section transition hint event count: `90`

## Subtle transition-hint focus demo

- MIDI: `demos/v2_6_136_jazz_ballad_subtle_transition_hint_focus_demo.mid`
- Bars: `[{'label': 'basic_time', 'bar_start': 0.0, 'brush_classic_fill_cell': 'none', 'event_slot_counts': {'1': 2, '2': 2, '2&': 1, '3': 1, '4': 2, '4&': 1}, 'foreground_fill_event_count': 0}, {'label': 'v1_drag_to_4_hint', 'bar_start': 4.0, 'brush_classic_fill_cell': 'v1_drag_to_4_hint', 'event_slot_counts': {'1': 1, '2': 1, '3': 1, '3&': 1, '4': 3}, 'foreground_fill_event_count': 0}, {'label': 'turnaround_2and_3and_4and_whisper', 'bar_start': 8.0, 'brush_classic_fill_cell': 'turnaround_2and_3and_4and_whisper', 'event_slot_counts': {'1': 2, '2': 2, '2&': 2, '3': 2, '3&': 2, '4': 2, '4&': 2}, 'foreground_fill_event_count': 0}, {'label': 'v1_section_breath_4_to_4and_hint', 'bar_start': 12.0, 'brush_classic_fill_cell': 'v1_section_breath_4_to_4and_hint', 'event_slot_counts': {'1': 1, '2': 1, '3': 1, '4': 3, '4&': 1}, 'foreground_fill_event_count': 0}, {'label': 'section_entry_1and_bloom_hint', 'bar_start': 16.0, 'brush_classic_fill_cell': 'section_entry_soft_1_to_1and_hint', 'event_slot_counts': {'1': 3, '1&': 1, '2': 1, '3': 1, '4': 2, '4&': 1}, 'foreground_fill_event_count': 0}, {'label': 'final_release', 'bar_start': 20.0, 'brush_classic_fill_cell': 'final_brush_release', 'event_slot_counts': {'1': 1, '2&': 1}, 'foreground_fill_event_count': 2}]`

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
  "phrase_tail_keeps_4and_transition_hint": true,
  "section_hints_are_not_foreground_lane": true,
  "section_hints_use_subtle_hint_dynamic_profiles": true,
  "pickup_uses_turnaround_whisper_hint": true,
  "section_tail_uses_v1_section_breath_hint": true,
  "cadence_uses_v1_drag_to_4_hint": true,
  "v1_reference_primitives_declared": true,
  "no_default_long_explicit_fill_cells": true,
  "final_release_contextual": true,
  "misty_runtime_has_section_hint_events": true,
  "misty_runtime_has_drum_layer": true,
  "piano_bass_still_present": true
}
```

Recommended next task: `v2_6_137_engine_ballad_transition_hint_listening_calibration`
