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

## Recommended Next Engine Task

```text
v2_6_9_engine_voicing_spread_projection_core_behavior_preserving_split
```

Goal: continue the SPREAD split by extracting the remaining core lower+upper projection orchestration while preserving lower-group, upper-source, and register-guard owners plus all v2_6_5/v2_6_6/v2_6_7/v2_6_8 behavior signatures.

Expected scope:

- keep lower groups in `spread_lower_groups.py`;
- keep upper source adaptation in `spread_upper_sources.py`;
- keep register/gap/span legality in `spread_register_guards.py`;
- move only notes-only projection orchestration helpers if behavior signatures remain stable;
- keep groupwise voice-leading, runtime gate, Ballad runtime pilot, and candidate adapter logic in place for later passes;
- preserve `jammate_engine.core.voicing.disposition.spread` import compatibility.

Forbidden scope:

- no listening-behavior retune;
- no source-weight changes;
- no harmonic-expansion or altered-dominant policy changes;
- no pattern/expression/gesture ownership drift;
- no Agent/shared docs/version edits.

---

## Near-Term Engine Queue

1. `v2_6_9_engine_voicing_spread_projection_core_behavior_preserving_split`
2. `v2_6_10_engine_voicing_spread_runtime_gate_and_adapter_cleanup`
3. `v2_6_11_engine_voicing_spread_ballad_runtime_pilot_isolation_cleanup`
4. `v2_6_12_engine_jazz_ballad_bass_anchor_path_policy`

Each task should produce either a focused audit summary or a three-chorus standard-tune listening demo when music output changes.
