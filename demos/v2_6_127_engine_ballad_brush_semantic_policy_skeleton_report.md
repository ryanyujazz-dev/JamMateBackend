# v2_6_127 — Engine Ballad Brush Semantic Policy Skeleton

Engine version tag: `v2_10_28`

## Scope

Introduce a Jazz Ballad brush semantic policy skeleton in the existing jazz_ballad percussion owner. The milestone exposes per-region brush texture/time-anchor/kick/phrase-breath/density intent for audit, but intentionally keeps default Ballad drums silent and emits no MIDI drum notes.

## Static brush semantic policy

- Policy version: `v2_6_127`
- Arrangement policy active: `True` / `v2_6_127`
- Default candidate count: `0`
- Boundary: `metadata_only_no_audible_drum_events_no_midi_notes_no_expression_values`
- Texture intents: `['none', 'circular_sparse', 'circular_standard', 'half_bar_breath_sweep', 'release_sweep']`
- Time anchor intents: `['none', '4_only', '2_4_soft']`
- Kick policy intents: `['none', 'beat1_only', 'one_three', 'all_four_feather']`
- Phrase breath intents: `['none', 'brush_drag_to_4', 'soft_swish_4and', 'section_breath', 'final_release']`
- Density bands: `['silent', 'very_low', 'low', 'medium']`

## Misty runtime audit

- MIDI: `demos/v2_6_127_misty_jazz_ballad_brush_semantic_policy_skeleton_demo.mid`
- Note events by track: `{'piano': 994, 'bass': 150}`
- Audited region count: `150`
- Brush texture counts: `{'circular_sparse': 36, 'none': 108, 'half_bar_breath_sweep': 5, 'release_sweep': 1}`
- Brush time anchor counts: `{'none': 121, '4_only': 29}`
- Brush kick policy counts: `{'none': 150}`
- Brush phrase breath counts: `{'none': 144, 'section_breath': 5, 'final_release': 1}`
- Brush density counts: `{'very_low': 42, 'silent': 108}`

## Acceptance

Passed: `True`

```json
{
  "version_declared": true,
  "default_runtime_still_silent": true,
  "misty_still_generates_piano_and_bass": true,
  "semantic_dimensions_present": true,
  "ordinary_and_boundary_decisions_present": true,
  "runtime_region_decisions_exposed": true,
  "no_generic_loop_contract": true
}
```

Recommended next task: `v2_6_128_engine_ballad_first_audible_sparse_brush_foundation`
