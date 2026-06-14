# v2_6_128 — Engine Ballad First Audible Sparse Brush Foundation

Engine version tag: `v2_10_28`

## Scope

Consume the v2_6_127 Jazz Ballad brush semantic policy and add the first very sparse audible brush texture. The change stays inside the existing Jazz Ballad percussion owner plus shared percussion voice mapping; it does not add a fixed loop, swing ride, rock backbeat, new drum engine, piano/bass/voicing change, API, Agent, or HarmonyOS change.

## Static audit

- Semantic policy version: `v2_6_127`
- Audible foundation version: `v2_6_128`
- Arrangement policy active/version: `True` / `v2_6_128`
- Ordinary candidate: `{'candidate_count': 1, 'name': 'jazz_ballad_sparse_brush_circular_sparse_none', 'category': 'jazz_ballad_sparse_brush_foundation', 'events': [{'beat': 0.0, 'role': 'ballad_brush_circular_sparse', 'drum': 'brush_swirl', 'dynamic_profile': 'ballad_brush_whisper', 'stroke_profile': 'brush_texture_sweep', 'slot': 'circular_sparse_entry'}, {'beat': 3.0, 'role': 'ballad_brush_beat4_soft_anchor', 'drum': 'brush_tap', 'dynamic_profile': 'ballad_brush_soft_anchor', 'stroke_profile': 'brush_texture_short', 'slot': 'beat4_soft_anchor'}], 'metadata': {'style_id': 'jazz_ballad', 'pattern_domain': 'percussion_foundation', 'pattern_library_id': 'jazz_ballad.brush_semantic_policy', 'pattern_library_version': 'v2_6_128', 'jazz_ballad_brush_semantic_policy_active': True, 'jazz_ballad_brush_semantic_policy_version': 'v2_6_127', 'jazz_ballad_first_audible_sparse_brush_foundation_active': True, 'jazz_ballad_first_audible_sparse_brush_foundation_version': 'v2_6_128', 'jazz_ballad_first_audible_sparse_brush_foundation_scope': 'consume existing brush semantic policy decisions and emit only sparse, region-local brush texture events', 'jazz_ballad_first_audible_sparse_brush_foundation_boundary': 'style percussion pattern metadata only; no piano, bass, voicing, fixed loop, swing ride, rock backbeat, API, Agent, or HarmonyOS change', 'brush_texture_intent': 'circular_sparse', 'brush_time_anchor_intent': '4_only', 'brush_kick_policy_intent': 'none', 'brush_phrase_breath_intent': 'none', 'brush_density_band': 'very_low', 'brush_runtime_audible': True, 'brush_runtime_note_event_count': 2, 'brush_no_fixed_loop': True, 'brush_no_swing_ride': True, 'brush_no_rock_backbeat': True, 'brush_no_piano_bass_voicing_change': True, 'chord_region_first': True, 'bar_first': False}}`
- Phrase-tail candidate: `{'candidate_count': 1, 'name': 'jazz_ballad_sparse_brush_half_bar_breath_sweep_soft_swish_4and', 'category': 'jazz_ballad_sparse_brush_foundation', 'events': [{'beat': 2.5, 'role': 'ballad_brush_phrase_breath_sweep', 'drum': 'brush_sweep', 'dynamic_profile': 'ballad_brush_phrase_breath', 'stroke_profile': 'brush_texture_sweep', 'slot': 'phrase_breath_sweep'}, {'beat': 3.5, 'role': 'ballad_brush_soft_swish_4and', 'drum': 'brush_tap', 'dynamic_profile': 'ballad_brush_whisper', 'stroke_profile': 'brush_texture_short', 'slot': 'phrase_breath_4and'}], 'metadata': {'style_id': 'jazz_ballad', 'pattern_domain': 'percussion_foundation', 'pattern_library_id': 'jazz_ballad.brush_semantic_policy', 'pattern_library_version': 'v2_6_128', 'jazz_ballad_brush_semantic_policy_active': True, 'jazz_ballad_brush_semantic_policy_version': 'v2_6_127', 'jazz_ballad_first_audible_sparse_brush_foundation_active': True, 'jazz_ballad_first_audible_sparse_brush_foundation_version': 'v2_6_128', 'jazz_ballad_first_audible_sparse_brush_foundation_scope': 'consume existing brush semantic policy decisions and emit only sparse, region-local brush texture events', 'jazz_ballad_first_audible_sparse_brush_foundation_boundary': 'style percussion pattern metadata only; no piano, bass, voicing, fixed loop, swing ride, rock backbeat, API, Agent, or HarmonyOS change', 'brush_texture_intent': 'half_bar_breath_sweep', 'brush_time_anchor_intent': '4_only', 'brush_kick_policy_intent': 'none', 'brush_phrase_breath_intent': 'soft_swish_4and', 'brush_density_band': 'very_low', 'brush_runtime_audible': True, 'brush_runtime_note_event_count': 2, 'brush_no_fixed_loop': True, 'brush_no_swing_ride': True, 'brush_no_rock_backbeat': True, 'brush_no_piano_bass_voicing_change': True, 'chord_region_first': True, 'bar_first': False}}`
- Final-release candidate: `{'candidate_count': 1, 'name': 'jazz_ballad_sparse_brush_release_sweep_final_release', 'category': 'jazz_ballad_sparse_brush_foundation', 'events': [{'beat': 0.0, 'role': 'ballad_brush_final_release', 'drum': 'brush_release', 'dynamic_profile': 'ballad_brush_release', 'stroke_profile': 'brush_texture_release', 'slot': 'final_release_start'}], 'metadata': {'style_id': 'jazz_ballad', 'pattern_domain': 'percussion_foundation', 'pattern_library_id': 'jazz_ballad.brush_semantic_policy', 'pattern_library_version': 'v2_6_128', 'jazz_ballad_brush_semantic_policy_active': True, 'jazz_ballad_brush_semantic_policy_version': 'v2_6_127', 'jazz_ballad_first_audible_sparse_brush_foundation_active': True, 'jazz_ballad_first_audible_sparse_brush_foundation_version': 'v2_6_128', 'jazz_ballad_first_audible_sparse_brush_foundation_scope': 'consume existing brush semantic policy decisions and emit only sparse, region-local brush texture events', 'jazz_ballad_first_audible_sparse_brush_foundation_boundary': 'style percussion pattern metadata only; no piano, bass, voicing, fixed loop, swing ride, rock backbeat, API, Agent, or HarmonyOS change', 'brush_texture_intent': 'release_sweep', 'brush_time_anchor_intent': 'none', 'brush_kick_policy_intent': 'none', 'brush_phrase_breath_intent': 'final_release', 'brush_density_band': 'very_low', 'brush_runtime_audible': True, 'brush_runtime_note_event_count': 1, 'brush_no_fixed_loop': True, 'brush_no_swing_ride': True, 'brush_no_rock_backbeat': True, 'brush_no_piano_bass_voicing_change': True, 'chord_region_first': True, 'bar_first': False}}`

## Misty runtime audit

- MIDI: `demos/v2_6_128_misty_jazz_ballad_first_audible_sparse_brush_foundation_demo.mid`
- Note events by track: `{'piano': 981, 'bass': 150, 'drums': 71}`
- Audible candidate count: `42`
- Expected brush pattern events: `71`
- Brush candidate texture counts: `{'circular_sparse': 36, 'half_bar_breath_sweep': 5, 'release_sweep': 1}`
- Brush event drum counts: `{'brush_swirl': 36, 'brush_tap': 29, 'brush_sweep': 5, 'brush_release': 1}`
- Brush event dynamic counts: `{'ballad_brush_whisper': 41, 'ballad_brush_soft_anchor': 24, 'ballad_brush_phrase_breath': 5, 'ballad_brush_release': 1}`

## Acceptance

Passed: `True`

```json
{
  "versions_declared": true,
  "ordinary_sparse_brush_audible": true,
  "short_regions_still_silent": true,
  "phrase_and_release_are_contextual": true,
  "misty_generates_sparse_drums": true,
  "piano_and_bass_unchanged_present": true,
  "expected_and_runtime_drum_counts_match": true,
  "no_generic_loop_contract": true
}
```

Recommended next task: `v2_6_129_engine_ballad_phrase_breath_brush_markers`
