# v2_6_135 — Engine Ballad Section Transition Hint Fills

Engine version tag: `v2_10_28`

## Scope

Replace overly explicit foreground Ballad brush fills with shorter phrase/section transition hints: section-tail 4& cue, section-entry bloom, cadence 3&→4 hint, and soft turnaround 2&/4& cue. Dynamics remain available, but the automatic planner avoids long tap-drag/single-stroke displays. Offbeats keep shared swing-8 timing; no piano/bass/voicing/API/Agent/HarmonyOS change.

## Static audit

- Arrangement policy version: `v2_6_135`
- Brush source assumed: `True`
- Scope: `bar_level_brush_time_feel_with_region_projection`
- Motion points: `['1', '1&', '2', '2&', '3', '3&', '4', '4&']`

## Misty runtime audit

- MIDI: `demos/v2_6_135_misty_jazz_ballad_section_transition_hint_fills_demo.mid`
- Note events by track: `{'piano': 1026, 'bass': 150, 'drums': 856}`
- Brush feel cell counts: `{'pure_legato_brush': 12, 'brush_swing_skip': 49, 'basic_brush_time': 49, 'brush_two_feel': 40}`
- Brush event drum counts: `{'snare': 554, 'kick': 154, 'hihat_pedal': 168}`
- Brush event slot counts: `{'1': 296, '2': 288, '3': 44, '4': 66, '4&': 42, '2&': 138, '3&': 2}`
- Classic fill cell counts: `{'section_entry_brush_bloom': 12, 'none': 70, 'cadence_3and_4_hint': 24, 'section_tail_4and_hint': 18, 'turnaround_soft_2and_4and_hint': 26}`
- Classic fill event count: `0`
- Section transition hint event count: `50`

## Section-hint focus demo

- MIDI: `demos/v2_6_135_jazz_ballad_section_transition_hint_focus_demo.mid`
- Bars: `[{'label': 'basic_time', 'bar_start': 0.0, 'brush_classic_fill_cell': 'none', 'event_slot_counts': {'1': 2, '2': 2, '2&': 1, '3': 1, '4': 2, '4&': 1}, 'foreground_fill_event_count': 0}, {'label': 'cadence_3and_4_hint', 'bar_start': 4.0, 'brush_classic_fill_cell': 'cadence_3and_4_hint', 'event_slot_counts': {'1': 1, '2': 1, '3': 1, '3&': 1, '4': 2}, 'foreground_fill_event_count': 2}, {'label': 'turnaround_soft_2and_4and_hint', 'bar_start': 8.0, 'brush_classic_fill_cell': 'turnaround_soft_2and_4and_hint', 'event_slot_counts': {'1': 2, '2': 2, '2&': 1, '3': 1, '4': 1, '4&': 1}, 'foreground_fill_event_count': 2}, {'label': 'section_tail_4and_hint', 'bar_start': 12.0, 'brush_classic_fill_cell': 'section_tail_4and_hint', 'event_slot_counts': {'1': 1, '2': 1, '3': 1, '4': 2, '4&': 1}, 'foreground_fill_event_count': 1}, {'label': 'section_entry_brush_bloom', 'bar_start': 16.0, 'brush_classic_fill_cell': 'section_entry_brush_bloom', 'event_slot_counts': {'1': 2, '2': 1, '3': 1, '4': 2, '4&': 1}, 'foreground_fill_event_count': 1}, {'label': 'final_release', 'bar_start': 20.0, 'brush_classic_fill_cell': 'final_brush_release', 'event_slot_counts': {'1': 1, '2&': 1}, 'foreground_fill_event_count': 2}]`

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
  "section_hints_use_foreground_lane": true,
  "section_hints_keep_existing_fill_dynamic_profiles": true,
  "pickup_uses_soft_2and_4and_hint": true,
  "section_tail_uses_single_4and_hint": true,
  "cadence_uses_3and_4_hint": true,
  "no_default_long_explicit_fill_cells": true,
  "final_release_contextual": true,
  "misty_runtime_has_section_hint_events": true,
  "misty_runtime_has_drum_layer": true,
  "piano_bass_still_present": true
}
```

Recommended next task: `v2_6_136_engine_ballad_section_hint_listening_calibration`
