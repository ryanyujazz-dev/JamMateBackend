# v2_6_56 — Engine Medium Swing Piano Region-Length Pattern Vocabulary Baseline

## Scope

This milestone starts the Medium Swing piano pattern track without creating a parallel pattern system.
The existing style-owned source remains:

```text
src/jammate_engine/styles/medium_swing/comping_patterns.py
```

The old bar-first / `two_chord_bar` terminology is replaced by a ChordRegion-first contract:

```text
ChordRegion duration -> region-local pattern vocabulary
```

No Agent, API, HarmonyOS, MIDI writer, voicing selector, anticipation runtime, or final expression parameters are changed.

## Core changes

- Upgraded `medium_swing.piano_comping` pattern library metadata to `v2_6_56`.
- Added `region_length_beats`, `region_length_family`, `time_reference=region_local_beats`, `rhythm_family`, `phrase_role`, `tail_push_risk`, `requires_region_start_anchor`, and expression-boundary metadata.
- Kept existing runtime-active Medium Swing piano cells behavior-compatible with v2_6_55 so recent voicing checkpoints remain stable.
- Replaced old `two_chord_bar_*` naming/tags/categories with `two_beat_region_*` naming and metadata.
- Added inactive zero-weight vocabulary candidates for future activation:
  - 4-beat region: `1,3`, `3`, `1,4`, `1,2&,4`, reverse Charleston, `2&,4`, delayed answer, rare 4& push variants.
  - 2-beat region: `start,local2`, `start,local1&`, `local1&`.
  - 1-beat region: `start`, `local&`, `rest_if_covered`.
  - Safe placeholders for 3-beat and 5-beat regions.

## Pattern / expression boundary

Patterns still do not contain final expression values. Existing concrete expression profile ids such as `comp_short` and `comp_medium` remain for behavior compatibility, while V1-style touch semantics are carried as metadata:

```text
semantic_expression_hint = soft_hold | light_stab | accent_stab | backbeat_hold | final_hold
```

A later Expression handoff milestone can map these semantic hints into style-specific duration / velocity / release / pedal behavior.

## Acceptance

- 1/2/4-beat region candidates are pitchless and region-local.
- No `two_chord_bar` label remains in the normal Medium Swing piano pattern names, categories, or tags.
- New vocabulary is present but inactive until the next candidate-lookup / weight-calibration milestones.
- v2_6_44 through v2_6_56 focused regression passes.
- Current standard-tune demos remain behavior-compatible with the v2_6_55 voicing checkpoints.

## Recommended next task

```text
v2_6_57_engine_medium_swing_piano_region_length_candidate_lookup_policy
```

Activate the region-length lookup policy explicitly and start deciding when inactive 1/2/4-beat vocabulary candidates become available, instead of relying on a single flat weighted pool.
