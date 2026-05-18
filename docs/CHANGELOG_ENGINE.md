# Engine Track Changelog

Current baseline: `v2_6_1`; latest engine-track task: `v2_6_8_engine_voicing_spread_register_guard_behavior_preserving_split` (shared VERSION intentionally unchanged).

This file records engine-track changes to reduce conflicts in the global `docs/CHANGELOG.md`.

---


## v2_6_8 — Engine Voicing SPREAD Register Guard Split

- Behavior-preserving implementation split; no voicing retune, source-weight change, style-policy change, listening-behavior change, API, Agent, or shared version change.
- Added `src/jammate_engine/core/voicing/disposition/spread_register_guards.py` as the owner for SPREAD register policy, lower/upper register windows, rooted bass anchor guards, low-register density guard, group gap guard, and overall span guard.
- Kept public import compatibility through `jammate_engine.core.voicing.disposition.spread` and `jammate_engine.core.voicing.disposition`.
- Added `docs/ENGINE_VOICING_SPREAD_REGISTER_GUARD_SPLIT_V2_6_8.md` and `tests/test_v2_6_8_engine_voicing_spread_register_guard_split.py`.
- Verified the v2_6_5 representative SPREAD candidate signatures for `Cmaj7`, `G7b9`, and `Bm7b5` remain unchanged.


## v2_6_7 — Engine Voicing SPREAD Upper Source Split

- Behavior-preserving implementation split; no voicing retune, source-weight change, style-policy change, listening-behavior change, API, Agent, or shared version change.
- Added `src/jammate_engine/core/voicing/disposition/spread_upper_sources.py` as the owner for upper source refs, upper source options, adapter results, source-oriented adapter policy, upper-structure source gate, and DROP2/DROP3-only upper 4-note projection method normalization.
- Kept public import compatibility through `jammate_engine.core.voicing.disposition.spread` and `jammate_engine.core.voicing.disposition`.
- Added `docs/ENGINE_VOICING_SPREAD_UPPER_SOURCE_SPLIT_V2_6_7.md` and `tests/test_v2_6_7_engine_voicing_spread_upper_source_split.py`.
- Verified representative upper adapter signatures and representative SPREAD candidate signatures for `Cmaj7`, `G7b9`, and `Bm7b5` remain unchanged.

## v2_6_6 — Engine Voicing SPREAD Lower Group Split

- Behavior-preserving implementation split; no voicing retune, source-weight change, style-policy change, listening-behavior change, API, Agent, or shared version change.
- Added `src/jammate_engine/core/voicing/disposition/spread_contracts.py` for shared SPREAD contract constants/enums used before a full package conversion.
- Added `src/jammate_engine/core/voicing/disposition/spread_lower_groups.py` as the owner for lower/foundation recipe ids, dataclasses, inventory, instantiation, placement, and lower inventory debug payloads.
- Kept public import compatibility through `jammate_engine.core.voicing.disposition.spread` and `jammate_engine.core.voicing.disposition`.
- Added `docs/ENGINE_VOICING_SPREAD_LOWER_GROUP_SPLIT_V2_6_6.md` and `tests/test_v2_6_6_engine_voicing_spread_lower_group_split.py`.
- Verified the v2_6_5 representative SPREAD candidate signatures for `Cmaj7`, `G7b9`, and `Bm7b5` remain unchanged.

## v2_6_5 — Engine Voicing SPREAD Boundary Split Plan

- Documentation + pre-split behavior-signature test pass; no implementation split, voicing retune, source-weight change, style-policy change, listening-behavior change, API, Agent, or shared version change.
- Added `docs/ENGINE_VOICING_SPREAD_BOUNDARY_SPLIT_PLAN_V2_6_5.md` to inventory the current responsibilities inside `core/voicing/disposition/spread.py` and define a future behavior-preserving package split.
- Added `tests/test_v2_6_5_engine_voicing_spread_boundary_split_plan.py` to freeze lower recipe inventory, SPREAD contract skeletons, and representative `project_basic_spread_candidates` signatures before implementation code is moved.
- Planned the future minimal split order: lower groups, upper source adapter, register guards, projection orchestration, and Ballad runtime pilot isolation.

## v2_6_4 — Engine Voicing Taxonomy and Boundary Hardening

- Documentation + light boundary-test pass; no voicing retune, style-weight change, listening-behavior change, API, Agent, or shared version change.
- Added `docs/ENGINE_VOICING_TAXONOMY_AND_BOUNDARY_HARDENING_V2_6_4.md` to document the active voicing taxonomy axes: content family, root support, bass relation, density/functional grouping, disposition/projection method, color/altered-dominant policy, register guards, and selector/voice-leading.
- Added `tests/test_v2_6_4_engine_voicing_taxonomy_boundary_hardening.py` to keep taxonomy documentation synchronized with enum values and protect the boundary that pattern, anticipation, expression, style pattern vocabulary, realization, and MIDI layers must not perform voicing selection.
- Verified style voicing policies remain policy-only surfaces that can bias VoicingPolicy and generate taxonomy-visible candidates without moving concrete note selection into style pattern files.

## v2_6_3 — Engine MIDI Output Pipeline Boundary Audit

- Documentation + light test pass; no generation-rule, listening-behavior, API, Agent, or shared version change.
- Added `docs/ENGINE_MIDI_OUTPUT_PIPELINE_BOUNDARY_AUDIT_V2_6_3.md` to document the runtime chain from request/leadsheet through chord regions, pitchless patterns, anticipation, expression, voicing, gesture projection, NoteEvent, timing, pedal CC64, MIDI writing, and base64 asset response.
- Added `tests/test_v2_6_3_engine_midi_pipeline_boundary_audit.py` to protect key object boundaries and macro pipeline order.
- Verified PatternEvent stays pitchless, EventExpression remains expression-only, VoicingRequest does not carry final render facts, VoicingPlan is the concrete vertical pitch boundary, and NoteEvent/PedalEvent are realization/MIDI boundary objects.

## v2_6_2 — Engine Voicing Projection Cleanup

- Behavior-preserving voicing cleanup; no style voicing policy, weight, expression, pattern, API, Agent, or shared version change.
- Moved source-order/content placement helpers out of `selection/candidate_generator.py` into `selection/content_placement.py`.
- Moved source-rotation and source-family audit metadata helpers into `selection/source_rotation_metadata.py`.
- Moved register-variant and disposition-register helper logic into `selection/register_variants.py`.
- Reduced `selection/candidate_generator.py` from a detail-heavy placement/scoring catch-all toward candidate orchestration while preserving existing candidate metadata contracts.

## v2_5_9 — V1 Instrument Rules Deep Audit and V2-Native Mapping

- Documentation-only engine planning pass based on `v2_5_8`; no generation code changed.
- Explicitly discarded the experimental Ballad brush-drums shortcut as an abandoned trial, not an official baseline.
- Added deep V1 instrument-rule audit and V2-native mapping for Jazz Ballad, Medium Swing, and Bossa Nova piano/bass/drums.
- Reaffirmed no V1 code migration, no V1 phrase-engine/runtime mirror, no pattern-to-texture binding, and no MIDI repair paths.

## v2_5_8 — Jazz Ballad Default Swing-8 Anticipation Timing Patch

- Jazz Ballad timing profile defaults to swing-8 feel.
- Anticipation uses logical `.5` but performs as swing/triplet upbeat.

## v2_5_7 — Jazz Ballad 1& Sustain Continuity Bugfix

- Expression duration clamp respects performed swing-upbeat timing for Ballad `beat 1 -> 1&` continuity.

## v2_5_4 — Held Foundation Partial Reattack Realization

- `INNER_MOVEMENT` projects only requested inner/color voices.
- Foundation/common tones remain held through partial reattack.
