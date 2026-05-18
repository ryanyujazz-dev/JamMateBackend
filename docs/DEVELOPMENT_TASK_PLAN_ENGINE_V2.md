# Engine Track Development Task Plan V2

Current baseline: `v2_6_1`; latest engine-track task completed in this package: `v2_6_8_engine_voicing_spread_register_guard_behavior_preserving_split` (shared VERSION intentionally unchanged).

This file is the rolling plan for `feature/engine-deepening`. It owns accompaniment generation, style rules, voicing/expression/gesture behavior, MIDI realization, and listening demos.

---

## Ownership

Allowed owner paths:

```text
src/jammate_engine/core/
src/jammate_engine/styles/
src/jammate_engine/generation/
src/jammate_engine/performance/
src/jammate_engine/harmony/
src/jammate_engine/midi/
src/jammate_engine/realization/
examples/scripts/generate_standard_tune_v2_examples_demos.py
```

Do not modify Agent workflow code in an Engine task.

---

## Current Engine Baseline

Official engine music baseline preserved in the integrated package:

```text
v2_5_9_v1_instrument_rules_deep_audit_and_v2_native_mapping
```

Important retained engine facts:

- Jazz Ballad defaults to swing-8 feel.
- Ballad anticipation keeps logical `.5` but performs on the swing/triplet upbeat.
- Ballad `beat 1 -> 1&` continuity respects performed swing-upbeat timing.
- Jazz Ballad `inner_movement` is a V2 `GestureRequest`, not a pattern hack.
- Held foundation + partial reattack remains a realization/gesture/expression boundary behavior.
- V1 is only a musical-rule reference; no V1 code migration or runtime mirror.

---

## Latest Engine Task Completed

```text
v2_6_8_engine_voicing_spread_register_guard_behavior_preserving_split
```

Goal: continue the SPREAD split by moving register/gap/span guard ownership out of `spread.py` while preserving public imports and candidate behavior signatures.

Completed scope:

- added `src/jammate_engine/core/voicing/disposition/spread_register_guards.py`;
- added `docs/ENGINE_VOICING_SPREAD_REGISTER_GUARD_SPLIT_V2_6_8.md`;
- added `tests/test_v2_6_8_engine_voicing_spread_register_guard_split.py`;
- moved `SpreadProjectionRegisterPolicy`, `basic_spread_register_policy`, lower/upper register windows, rooted bass anchor guards, low-register density guard, group gap guard, overall span guard, and register debug payload ownership out of `spread.py`;
- kept public imports compatible from `jammate_engine.core.voicing.disposition.spread` and `jammate_engine.core.voicing.disposition`;
- preserved v2_6_5 representative `project_basic_spread_candidates` signatures for `Cmaj7`, `G7b9`, and `Bm7b5`;
- did not retune voicing, change style policies, alter source weights, or touch pattern/expression/realization/MIDI/API/Agent/shared version files.

## Previous Engine Task Completed

```text
v2_6_6_engine_voicing_spread_lower_group_recipes_behavior_preserving_split
```

Goal: start the SPREAD split with the safest behavior-preserving extraction: move lower group recipe inventory and placement out of `spread.py` while preserving all public imports and v2_6_5 behavior signatures.

Completed scope:

- added `src/jammate_engine/core/voicing/disposition/spread_contracts.py`;
- added `src/jammate_engine/core/voicing/disposition/spread_lower_groups.py`;
- added `docs/ENGINE_VOICING_SPREAD_LOWER_GROUP_SPLIT_V2_6_6.md`;
- added `tests/test_v2_6_6_engine_voicing_spread_lower_group_split.py`;
- moved lower recipe ids, lower recipe dataclasses, lower recipe inventory, lower instantiation, lower placement helpers, and lower inventory debug payload out of `spread.py`;
- kept public imports compatible from `jammate_engine.core.voicing.disposition.spread` and `jammate_engine.core.voicing.disposition`;
- preserved v2_6_5 lower recipe ids and representative `project_basic_spread_candidates` signatures for `Cmaj7`, `G7b9`, and `Bm7b5`;
- did not retune voicing, change style policies, alter source weights, or touch pattern/expression/realization/MIDI/API/Agent/shared version files.

## Previous Engine Task Completed

```text
v2_6_4_engine_voicing_taxonomy_doc_and_boundary_hardening
```

Goal: make the current voicing taxonomy explicit and harden the rule that other layers must not perform voicing work.

Completed scope:

- added `docs/ENGINE_VOICING_TAXONOMY_AND_BOUNDARY_HARDENING_V2_6_4.md`;
- added `tests/test_v2_6_4_engine_voicing_taxonomy_boundary_hardening.py`;
- documented the active voicing axes: ContentFamily, RootSupportPolicy, BassRelation, Density/FunctionalGrouping, Disposition/ProjectionMethod, ColorPolicy/AlteredDominantPolicy, register guards, and selector/voice-leading;
- added import/contract tests so voicing core does not depend on style/pattern/expression/realization/MIDI owners, and style pattern files do not import concrete voicing selection internals;
- verified style voicing policies still generate taxonomy-visible candidates without retuning weights or listening behavior;
- did not change style pattern rules, expression policy, voicing weights, MIDI rendering behavior, API, Agent, or shared version files.

## Previous Engine Task Completed

```text
v2_6_3_engine_midi_pipeline_boundary_audit_doc_and_light_tests
```

Goal: document the current end-to-end MIDI output chain and add light tests that protect pattern / anticipation / expression / voicing / realization / timing / pedal / MIDI boundaries from future cross-layer drift.

Completed scope:

- added `docs/ENGINE_MIDI_OUTPUT_PIPELINE_BOUNDARY_AUDIT_V2_6_3.md`;
- added `tests/test_v2_6_3_engine_midi_pipeline_boundary_audit.py`;
- verified PatternEvent, EventExpression, VoicingRequest, VoicingPlan, NoteEvent, and PedalEvent boundary fields;
- verified a small Jazz Ballad runtime generation exposes the expected macro pipeline order and timing/pedal boundary debug strings;
- did not change style pattern rules, expression policy, voicing weights, MIDI rendering behavior, API, Agent, or shared version files.

## Previous Engine Task Completed

```text
v2_6_2_engine_voicing_projection_cleanup
```

Goal: behavior-preserving cleanup of the voicing candidate/projection internals so candidate generation stays an orchestration layer instead of owning source placement, source-rotation audit metadata, and register-variant mechanics.

Completed scope:

- extracted content/source-order placement helpers into `selection/content_placement.py`;
- extracted source-rotation/audit metadata helpers into `selection/source_rotation_metadata.py`;
- extracted register guard/variant helpers into `selection/register_variants.py`;
- kept voicing candidate output contract and projection metadata intact;
- did not change style voicing policies, source weights, expression, pattern, API, Agent, or shared version files.

## v2_6_9 Completed — Engine Voicing SPREAD Projection Core Split

Completed behavior-preserving split:

- added `src/jammate_engine/core/voicing/disposition/spread_projection_core.py`;
- moved notes-only lower+upper SPREAD projection orchestration behind this owner;
- kept lower groups, upper source adaptation, and register/gap/span legality in their existing v2_6_6/v2_6_7/v2_6_8 owners;
- preserved public import compatibility through `spread.py` and `jammate_engine.core.voicing.disposition`;
- preserved v2_6_5 frozen SPREAD behavior signatures;
- generated a three-chorus Misty Jazz Ballad demo for full-runtime listening smoke verification.

## Recommended Next Engine Task

```text
v2_6_10_engine_voicing_spread_groupwise_voice_leading_behavior_preserving_split
```

Goal: extract SPREAD groupwise voice-leading scoring/ranking from `spread.py` while preserving notes-only SPREAD projection behavior and public import compatibility.

Forbidden scope:

- no listening-behavior retune;
- no source-weight changes;
- no harmonic-expansion or altered-dominant policy changes;
- no pattern/expression/gesture ownership drift;
- no Agent/shared docs/version edits.

---

## Near-Term Engine Queue

1. `v2_6_10_engine_voicing_spread_groupwise_voice_leading_behavior_preserving_split`
2. `v2_6_11_engine_voicing_spread_runtime_gate_and_adapter_cleanup`
3. `v2_6_12_engine_voicing_spread_ballad_runtime_pilot_isolation_cleanup`
4. `v2_6_13_engine_jazz_ballad_bass_anchor_path_policy`

Each task should produce either a focused audit summary or a three-chorus standard-tune listening demo when music output changes.

## Completed: v2_6_10_engine_voicing_spread_density_system_reset

This pass is a voicing-only density/disposition routing reset.

### Result

- Default SPREAD no longer emits 4-note `1+3` / `2+2` groupings.
- Jazz Ballad grouped SPREAD now uses active 5+ density contracts instead of falling back to ordinary 4-note SPREAD projection.
- Normal Ballad comping is centered on `spread_2plus3_contract`; fuller 6/7-note contracts remain available for chorus lift and ending/climax contexts.
- The fix is expressed through `core.voicing.density_policy` and Ballad grouped-spread runtime routing, not through selector score patching.

### Next recommended voicing-only task

`v2_6_11_engine_voicing_spread_groupwise_voice_leading_behavior_preserving_split`

Split SPREAD groupwise voice-leading / ranking ownership while keeping the v2_6_10 density reset behavior stable.

## v2_6_11 Completed — Engine Voicing Ballad Safe Extension Color Gate

Completed voicing-only color-gate pass:

- Jazz Ballad default `style_safe_extensions` for plain maj7 now prefers `9` and `13`;
- unnotated maj7 `#11` is gated behind explicit chart notation or harmonic-color intent metadata;
- explicit `maj7#11` chart symbols remain faithful;
- v2_6_10 grouped SPREAD density behavior remains the baseline;
- no Pattern / Anticipation / Expression / Gesture / MIDI behavior was moved into voicing or vice versa.

Next recommended voicing-only task: `v2_6_12_engine_voicing_spread_groupwise_voice_leading_behavior_preserving_split`.

## v2_6_12 Completed — Engine Voicing SPREAD Groupwise Voice-Leading Split

Completed behavior-preserving voicing/SPREAD split:

- added `src/jammate_engine/core/voicing/disposition/spread_voice_leading.py` as the groupwise voice-leading / ranking / continuity owner;
- moved `SpreadGroupwiseVoiceLeadingWeights`, `SpreadGroupwiseVoiceLeadingScore`, scoring, ranking, selection, and debug-path ownership out of `spread.py`;
- preserved public compatibility through `spread.py` and `jammate_engine.core.voicing.disposition` re-exports;
- preserved `Cmaj7`, `G7b9`, and `Bm7b5` `spread_2plus3_contract` candidate signatures;
- preserved v2_6_10 Jazz Ballad 5/6-note SPREAD density reset;
- preserved v2_6_11 maj7 safe-extension gate where default Ballad maj7 favors 9/13 and does not auto-enable unnotated #11;
- did not change Pattern / Anticipation / Expression / Gesture / MIDI / Agent / API / shared docs.

Next recommended voicing-only task: `v2_6_13_engine_voicing_spread_runtime_gate_and_adapter_cleanup`.


## v2_6_13 Completed — Engine Voicing Ballad Six-Note Ratio Lift

Completed voicing-only listening calibration:

- added a gentle selected-6-note contract intent bias in the SPREAD groupwise voice-leading owner;
- kept the 5-note `2+3` lane as the Jazz Ballad SPREAD body;
- raised 6-note grouped SPREAD appearances in the three-chorus Misty audit from 8 to 12;
- kept 4-note SPREAD at zero;
- kept unnotated maj7#11 at zero;
- did not touch Pattern / Anticipation / Expression / Gesture / MIDI / Agent / API / shared docs.

Next recommended voicing-only task: `v2_6_14_engine_voicing_spread_runtime_gate_and_adapter_cleanup`.

## v2_6_14 Completed — Engine Voicing Ballad SPREAD 5-to-6 Ratio Calibration

Completed voicing-only listening calibration:

- adjusted the existing selected-6-note contract intent bias from `0.20` to `5.0`;
- moved the Misty three-chorus Jazz Ballad audit toward `5-note:6-note ~= 6:4`;
- kept 4-note SPREAD retired at zero;
- kept 7-note as rare ending/climax thickness;
- kept unnotated maj7#11 at zero;
- did not touch Pattern / Anticipation / Expression / Gesture / MIDI / Agent / API / shared docs.

Reference audit:

```text
5-note: 118
6-note: 76
7-note: 2
4-note: 0
```

Next recommended voicing-only task: `v2_6_15_engine_voicing_spread_runtime_gate_and_adapter_cleanup`.

## v2_6_15 Completed — Engine Voicing SPREAD Runtime Gate / Adapter Cleanup

Completed behavior-preserving voicing/SPREAD boundary cleanup:

- added `spread_runtime_gate.py` as the SPREAD notes-only runtime enablement / selector gate owner;
- added `spread_runtime_adapter.py` as the `SpreadProjectionCandidate -> VoicingCandidate` field-mapping owner;
- kept `spread.py` as a compatibility facade, not a growing implementation file;
- preserved Jazz Ballad `5-note:6-note ~= 6:4` behavior;
- preserved retired 4-note SPREAD defaults and default maj7#11 gate;
- did not touch Pattern / Anticipation / Expression / Gesture / MIDI / Agent / API / shared docs.

Next recommended voicing-only task: `v2_6_16_engine_voicing_content_planner_boundary_split_plan`.

## v2_6_16 Completed — Engine Voicing Content Planner Boundary Split Plan

Completed documentation/test planning pass:

- audited the current `core.voicing.sources` boundary;
- kept `content_planner.py` behavior unchanged in this pass;
- documented future split owners:
  - `content_family_router.py` for family-choice / chord-quality normalization;
  - `content_source_inventory.py` for family-to-degree source option inventory;
  - existing `color_permission.py` for color admission gates;
  - existing `source_balance.py` for source-family scoring only;
  - existing `upper_structure.py` for source-only upper-structure recipes;
- froze the principle that Upper Structure reuses existing closed / inversion / DROP projection and must not reimplement projection;
- preserved v2_6_14/v2_6_15 Misty density/color guardrails.

Next recommended voicing-only task: `v2_6_17_engine_voicing_content_family_router_behavior_preserving_split`.

## v2_6_17 Completed — Engine Voicing Content Family Router Behavior-Preserving Split

Completed voicing-only source-boundary split:

- added `content_family_router.py` as the owner of content-family routing / chord-quality normalization;
- kept `content_planner.py` as public compatibility facade and source inventory orchestration for now;
- preserved `content_planner.choose_content_families(...)` as a wrapper to avoid breaking historical imports;
- did not move source inventory, color permission, source balance, upper structure, disposition, register, projection, pattern, expression, gesture, MIDI, API, or Agent behavior;
- preserved Jazz Ballad `5-note:6-note ~= 6:4`, zero default 4-note SPREAD, low-frequency 7-note, and zero unnotated maj7#11.

Next recommended voicing-only task: `v2_6_18_engine_voicing_content_source_inventory_behavior_preserving_split`.
