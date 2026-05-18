## v2_6_22_engine_voicing_cleanup_retired_spread_pilot_logic

- Cleanup pass: deleted retired Jazz Ballad SPREAD pilot / dry-run / safe-dry-run / selection-audit workflow from the active voicing surface.
- `candidate_generator.py` now uses the current grouped SPREAD runtime candidate pool directly instead of calling `guard_ballad_spread_pilot_runtime_enablement`.
- `spread_runtime_adapter.py` is the owner of `SpreadProjectionCandidate -> VoicingCandidate` adaptation.
- Removed old v2_2 pilot tests whose assertions targeted the deleted workflow.
- Preserved Ballad SPREAD density guardrails: 4-note SPREAD remains 0 in default Misty audit, and 5-note / 6-note remains near 6:4.
- Preserved default maj7#11 safe-extension gate.
- Added `docs/ENGINE_VOICING_CLEANUP_RETIRED_SPREAD_PILOT_LOGIC_V2_6_22.md` and `tests/test_v2_6_22_engine_voicing_cleanup_retired_spread_pilot_logic.py`.


## v2_6_15_engine_voicing_spread_runtime_gate_and_adapter_cleanup

- Added dedicated SPREAD runtime-boundary owners:
  - `src/jammate_engine/core/voicing/disposition/spread_runtime_gate.py`
  - `src/jammate_engine/core/voicing/disposition/spread_runtime_adapter.py`
- Kept `spread.py` as public compatibility facade while moving runtime gate/adapter definitions out of the facade body.
- Preserved v2_6_14 Ballad/SPREAD 5-note:6-note ~= 6:4 density calibration.
- Preserved 4-note SPREAD default exclusion and default maj7#11 safe-extension gate.
- Added `tests/test_v2_6_15_engine_voicing_spread_runtime_gate_adapter_cleanup.py`.

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

## v2_6_9 — Engine Voicing SPREAD Projection Core Split

- Behavior-preserving voicing/SPREAD cleanup; no style voicing policy, source-weight, expression, pattern, API, Agent, or shared version change.
- Added `src/jammate_engine/core/voicing/disposition/spread_projection_core.py` as the notes-only lower+upper SPREAD projection orchestration owner.
- Re-exported `project_basic_spread_contract`, `project_basic_spread_candidates`, and `basic_spread_projection_debug` through the existing `spread.py` and package-level compatibility surfaces.
- Preserved v2_6_5 frozen SPREAD candidate signatures for `Cmaj7`, `G7b9`, and `Bm7b5`.
- Added a three-chorus Misty Jazz Ballad listening demo for a full-runtime smoke check after the split.

## v2_6_10_engine_voicing_spread_density_system_reset

- Retired default 4-note SPREAD groupings `1+3` and `2+2`; they remain explicit audit/compatibility references only.
- Added `core.voicing.density_policy` as the density/disposition compatibility gate so this is a taxonomy/routing fix rather than a scorer bonus.
- Promoted Jazz Ballad grouped SPREAD runtime to active 5+/6-note contracts, centered on `spread_2plus3_contract` for normal comping and reserving `2+4`/`3+3`/`3+4` for lift and climax contexts.
- Added `docs/ENGINE_VOICING_SPREAD_DENSITY_SYSTEM_RESET_V2_6_10.md` and `tests/test_v2_6_10_engine_voicing_spread_density_system_reset.py`.
- No Pattern / Anticipation / Expression / Gesture / MIDI behavior was moved into voicing or vice versa.

## v2_6_11 — Engine Voicing Ballad Safe Extension Color Gate

- Voicing-only color-gate adjustment; no pattern, anticipation, expression, gesture, MIDI, API, Agent, or shared version change.
- Updated major-seventh style-safe expansion so Jazz Ballad defaults prefer `9` / `13` and do not treat unnotated `#11` as ordinary warm Ballad color.
- Preserved explicit chart fidelity: `maj7#11` still produces #11 voicing sources.
- Added policy/LLM intent hooks for unnotated maj7#11 via Lydian/bright/modern harmonic-color metadata.
- Added `docs/ENGINE_VOICING_BALLAD_SAFE_EXTENSION_COLOR_GATE_V2_6_11.md` and `tests/test_v2_6_11_engine_voicing_ballad_safe_extension_color_gate.py`.

## v2_6_12 — Engine Voicing SPREAD Groupwise Voice-Leading Split

- Voicing-only behavior-preserving split; no listening retune and no pattern, anticipation, expression, gesture, MIDI, API, Agent, or shared-version change.
- Added `src/jammate_engine/core/voicing/disposition/spread_voice_leading.py` as the owner of SPREAD groupwise voice-leading / ranking / continuity.
- Kept public compatibility by re-exporting the existing v2_2_41 scorer API through `spread.py` and the package-level disposition facade.
- Preserved `Cmaj7`, `G7b9`, and `Bm7b5` `spread_2plus3_contract` signatures.
- Added `docs/ENGINE_VOICING_SPREAD_GROUPWISE_VOICE_LEADING_SPLIT_V2_6_12.md` and `tests/test_v2_6_12_engine_voicing_spread_groupwise_voice_leading_split.py`.


## v2_6_13 — Engine Voicing Ballad Six-Note Ratio Lift

- Voicing-only listening calibration; no pattern, anticipation, expression, gesture, MIDI, API, Agent, or shared-version change.
- Added a small notes-only selected 6-note contract bias owned by `core.voicing.disposition.spread_voice_leading`.
- Raised the Misty Jazz Ballad three-chorus 6-note SPREAD count from the v2_6_12 audit baseline of 8 to 12, while keeping 5-note `2+3` as the dominant body.
- Preserved v2_6_10 guardrails: 4-note SPREAD `1+3` / `2+2` remain retired from default Ballad runtime.
- Preserved v2_6_11 color gate: unnotated Ballad maj7#11 remains off by default.
- Added `docs/ENGINE_VOICING_BALLAD_SIX_NOTE_RATIO_LIFT_V2_6_13.md` and `tests/test_v2_6_13_engine_voicing_ballad_six_note_ratio_lift.py`.

## v2_6_14 — Engine Voicing Ballad SPREAD 5-to-6 Ratio Calibration

- Voicing-only listening calibration; no pattern, anticipation, expression, gesture, MIDI, API, Agent, or shared-version change.
- Raised the existing selected 6-note SPREAD contract bias from `0.20` to `5.0` so Jazz Ballad grouped SPREAD approaches the requested `5-note:6-note ~= 6:4` mix.
- Reference Misty three-chorus audit now reports `5-note: 118`, `6-note: 76`, `7-note: 2`, `4-note: 0`.
- Preserved v2_6_10 guardrails: retired 4-note SPREAD `1+3` / `2+2` do not return.
- Preserved v2_6_11 color gate: unnotated Ballad maj7#11 remains off by default.
- Added `docs/ENGINE_VOICING_BALLAD_SPREAD_5_TO_6_RATIO_CALIBRATION_V2_6_14.md` and `tests/test_v2_6_14_engine_voicing_ballad_spread_5_to_6_ratio_calibration.py`.

## v2_6_15 — Engine Voicing SPREAD Runtime Gate / Adapter Cleanup

- Voicing-only behavior-preserving boundary cleanup; no pattern, anticipation, expression, gesture, MIDI, API, Agent, or shared-version change.
- Added `spread_runtime_gate.py` as the owner for SPREAD notes-only runtime enablement / selector gate decisions.
- Added `spread_runtime_adapter.py` as the owner for explicit `SpreadProjectionCandidate -> VoicingCandidate` adapter field mapping.
- Kept `spread.py` as the public compatibility facade while removing the major runtime gate / adapter implementation owners from it.
- Preserved v2_6_14 Jazz Ballad 5-note:6-note ratio calibration and v2_6_11 unnotated maj7#11 gate.
- Added `docs/ENGINE_VOICING_SPREAD_RUNTIME_GATE_ADAPTER_CLEANUP_V2_6_15.md` and `tests/test_v2_6_15_engine_voicing_spread_runtime_gate_adapter_cleanup.py`.

## v2_6_16 — Engine Voicing Content Planner Boundary Split Plan

- Documentation/test planning pass; no generation behavior changed.
- Audited `core.voicing.sources.content_planner` and clarified future owners for content family routing, source inventory, color permission, source balance, and upper-structure source planning.
- Established that the next code split should move family-choice / normalization first into `content_family_router.py`, while leaving source inventory in place for a later pass.
- Reaffirmed that Upper Structure remains source-only and must reuse existing closed / inversion / DROP projection capabilities instead of reimplementing disposition projection.
- Preserved v2_6_14 / v2_6_15 Jazz Ballad density and color guardrails: 4-note SPREAD remains zero, 5-note:6-note remains near 6:4, and unnotated maj7#11 remains off by default.
- Added `docs/ENGINE_VOICING_CONTENT_PLANNER_BOUNDARY_SPLIT_PLAN_V2_6_16.md` and `tests/test_v2_6_16_engine_voicing_content_planner_boundary_split_plan.py`.

## v2_6_17 — Engine Voicing Content Family Router Split

- Behavior-preserving voicing source boundary cleanup; no pattern, anticipation, expression, gesture, MIDI, API, Agent, or shared-version change.
- Added `src/jammate_engine/core/voicing/sources/content_family_router.py` as the owner for content-family routing and chord-quality normalization.
- Kept `content_planner.py` as the public compatibility facade and source-inventory orchestration surface for this pass.
- Preserved historical `content_planner.choose_content_families(...)` imports through a thin wrapper.
- Preserved v2_6_14/v2_6_15 Jazz Ballad `5-note:6-note ~= 6:4`, retired 4-note SPREAD defaults, and default maj7#11 gate.
- Added `docs/ENGINE_VOICING_CONTENT_FAMILY_ROUTER_SPLIT_V2_6_17.md` and `tests/test_v2_6_17_engine_voicing_content_family_router_split.py`.

## v2_6_18 — Engine Voicing Content Source Inventory Split

- Behavior-preserving voicing source boundary cleanup; no pattern, anticipation, expression, gesture, MIDI, API, Agent, or shared-version change.
- Added `src/jammate_engine/core/voicing/sources/content_source_inventory.py` as the owner for family-to-degree source options.
- Kept `content_planner.py` as the public compatibility facade and recipe orchestration layer.
- Moved source inventory implementation blocks out of `content_planner.py`, including shell+color, seventh-basic, rooted-color, rootless A/B, triad-aware 3-note/4-note, altered-dominant, and explicit-symbol source construction.
- Preserved historical public imports for `trim_content_degrees`, `source_preserves_seventh_chord_identity`, and `seventh_chord_source_integrity_notes` through `content_planner.py`.
- Preserved v2_6_14/v2_6_15 Jazz Ballad `5-note:6-note ~= 6:4`, retired 4-note SPREAD defaults, and default maj7#11 gate.
- Added `docs/ENGINE_VOICING_CONTENT_SOURCE_INVENTORY_SPLIT_V2_6_18.md` and `tests/test_v2_6_18_engine_voicing_content_source_inventory_split.py`.
## v2_6_19 — Engine Voicing Color Permission Adapter Cleanup

- Behavior-preserving voicing-only boundary cleanup; no Pattern / Anticipation / Expression / Gesture / MIDI / Agent / API / shared version changes.
- Moved color-admission adapter helpers into `src/jammate_engine/core/voicing/sources/color_permission.py`: explicit chart color extraction, rootless explicit-color extraction, ordered explicit colors, expansion-color candidate ordering, major-seventh #11 intent gate, and `build_voicing_color_permission_context`.
- Kept `content_source_inventory.py` as the source-construction owner; it now consumes color-permission helpers instead of carrying local color-permission glue.
- Updated `content_family_router.py` to reuse the same explicit-color helpers from `color_permission.py`, removing duplicated color parsing logic from the router.
- Preserved v2_6_14/v2_6_15 Jazz Ballad `5-note:6-note ~= 6:4`, retired 4-note SPREAD defaults, and default maj7#11 gate.
- Added `docs/ENGINE_VOICING_COLOR_PERMISSION_ADAPTER_CLEANUP_V2_6_19.md` and `tests/test_v2_6_19_engine_voicing_color_permission_adapter_cleanup.py`.

## v2_6_20 — Engine Voicing Source Balance Boundary Cleanup

- Behavior-preserving voicing-only source-balance boundary cleanup; no Pattern / Anticipation / Expression / Gesture / MIDI / Agent / API / shared version changes.
- Clarified `src/jammate_engine/core/voicing/sources/source_balance.py` as source-family scoring / bias only.
- Added `SourceBalanceProfile`, `source_balance_profile(...)`, `SOURCE_BALANCE_BOUNDARY_CLEANUP_VERSION`, and explicit owned/forbidden responsibility markers.
- Hardened 4-note source-key extraction so source balance can read current `content_recipe.validity_notes` markers when older top-level metadata aliases are absent, without moving source construction into source balance.
- Preserved v2_6_14/v2_6_15 Jazz Ballad `5-note:6-note ~= 6:4`, retired 4-note SPREAD defaults, and default maj7#11 gate.
- Added `docs/ENGINE_VOICING_SOURCE_BALANCE_BOUNDARY_CLEANUP_V2_6_20.md` and `tests/test_v2_6_20_engine_voicing_source_balance_boundary_cleanup.py`.

## v2_6_21 — Engine Voicing Upper Structure Boundary Audit

- Behavior-preserving voicing-only boundary audit; no Pattern / Anticipation / Expression / Gesture / MIDI / Agent / API / shared version changes.
- Clarified `src/jammate_engine/core/voicing/sources/upper_structure.py` as source-only upper-structure recipe planning.
- Added `UpperStructureBoundaryProfile`, `upper_structure_boundary_profile(...)`, `UPPER_STRUCTURE_BOUNDARY_AUDIT_VERSION`, and explicit owned/forbidden responsibility markers.
- Confirmed Upper Structure does not import projection, register, selector, voice-leading, runtime adapter, or MIDI owners.
- Preserved `UPPER_STRUCTURE_SOURCE_VERSION = v2_2_88` and existing harmonic-expansion / altered-dominant source gates.
- Preserved v2_6_14/v2_6_15 Jazz Ballad `5-note:6-note ~= 6:4`, retired 4-note SPREAD defaults, and default maj7#11 gate.
- Added `docs/ENGINE_VOICING_UPPER_STRUCTURE_BOUNDARY_AUDIT_V2_6_21.md` and `tests/test_v2_6_21_engine_voicing_upper_structure_boundary_audit.py`.
