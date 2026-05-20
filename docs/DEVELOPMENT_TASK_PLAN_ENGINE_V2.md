## v2_6_51 Completed — Engine Medium Swing Generic 4-Note Rotation Alignment Policy

Completed a voicing-only correction pass on the merged `v2_10_8` baseline plus `v2_6_50` orientation checkpoint.

Scope: Engine voicing only. No Agent/API/HarmonyOS/Pattern/Anticipation/Expression/MIDI-writer changes.

What changed:

- generalized the v2_6_50 rootless-only orientation alignment into `medium_swing_four_note_rotation_alignment_*`;
- mapped `basic_4note`, `rooted_color_4note`, and `rootless_ab` into one generic four-note rotation alignment contract;
- preserved legacy `rootless_ab_*` fields as compatibility aliases rather than deleting the content family;
- made basic/rooted 4-note follow logic use the expected `(previous_inversion + 2) % 4` motion, e.g. `1357 -> 5713`, `3571 -> 7135`, `5713 -> 1357`, `7135 -> 3571`;
- kept rootless A/B follow logic as `A <-> B` while preserving content type and rootless inversion index;
- added a smoothness guard so generic rooted/basic 4-note hard filtering only applies when a matching candidate is also voice-leading safe;
- exposed generic four-note rotation alignment audit fields in piano audit summaries and the Medium Swing audit script;
- added `tests/test_v2_6_51_engine_generic_4note_rotation_alignment_policy.py`.

Validation:

- `compileall`: passed
- `tools/check_development_harness.py`: HARNESS OK
- v2_6_44 through v2_6_51 focused regression: 29 passed
- integration today-guidance runtime smoke: 3 passed
- Medium Swing two-standard demo/audit generation: passed

Listening/audit checkpoint:

- All The Things You Are / Medium Swing / 3 choruses: voice-leading, section-boundary, phrase-scope method lock, and generic four-note rotation checkpoints passed.
- Autumn Leaves / Medium Swing / 3 choruses: voice-leading, section-boundary, phrase-scope method lock, and generic four-note rotation checkpoints passed.

Next recommended voicing-only task: `v2_6_52_engine_medium_swing_open_drop_same_chord_reattack_and_comping_reuse`.

## v2_6_50 Completed — Engine Medium Swing OPEN Drop-Family ii–V–I Orientation / Method Alignment

Completed a voicing-only Medium Swing continuity pass on the merged `v2_10_8` baseline plus `v2_6_49` phrase-scope method-lock policy.

Implemented:

- added conservative rootless A/B orientation-alignment metadata for local ii-V / V-I / ii-V-I follow regions;
- reused the existing `method_lock_seed_then_follow` runtime path instead of adding a new planner;
- requested A/B flip while preserving `rootless_ab_content_type` and `rootless_ab_inversion_index`;
- filtered candidate pools only when matching rootless A/B candidates are available;
- kept full candidate pools and audit reasons when no matching rootless candidates exist;
- explicitly avoided forcing rootless A/B when the previous seed is not rootless;
- exposed v2_6_50 orientation-alignment audit fields in piano audit summaries and the Medium Swing audit script;
- added `docs/ENGINE_VOICING_MEDIUM_SWING_OPEN_DROP_II_V_I_ORIENTATION_METHOD_ALIGNMENT_V2_6_50.md`;
- added `tests/test_v2_6_50_engine_medium_swing_open_drop_ii_v_i_orientation_method_alignment.py`;
- preserved Pattern, Anticipation, Expression, Gesture, MIDI, Agent, API, HarmonyOS fixtures, and shared integration files.

Reference three-chorus audit:

```text
All The Things You Are: method_lock_applied=88, method_lock_mismatches=0, phrase_switch_ratio=0.1429, rootless_ab_runtime_enabled=88, rootless_ab_applied=0, skip=previous_seed_not_rootless_ab=88
Autumn Leaves: method_lock_applied=100, method_lock_mismatches=0, phrase_switch_ratio=0.2308, rootless_ab_runtime_enabled=100, rootless_ab_applied=0, skip=previous_seed_not_rootless_ab=100
```

Reading note: the standard demos do not currently activate rootless A/B filtering because their selected Medium Swing seed voicings are not rootless A/B under the current default chord-symbol-only behavior. A targeted rootless candidate probe confirms the filter is active when matching candidates exist (`G13`, desired `B/with_13/index0`, 44 candidates -> 3 matching candidates).

Next recommended voicing-only task: `v2_6_51_engine_medium_swing_open_drop_same_chord_reattack_and_comping_reuse`.

## v2_6_49 Completed — Engine Medium Swing OPEN Drop-Family Phrase-Scope Method Lock Policy

Completed a voicing-only Medium Swing runtime policy pass on the merged `v2_10_8` baseline plus `v2_6_48` phrase-scope continuity audit.

Implemented:

- added conservative local ii-V / V-I / ii-V-I method-lock propagation for Medium Swing OPEN drop-family voicings;
- reused core `FunctionalMotion` labels and existing method-lock seed/follow runtime filtering rather than adding a new progression planner;
- propagated only `drop2` / `drop3` as phrase-body methods;
- kept `drop2_and_4` as recorded low-frequency phrase-internal color that is not propagated;
- exposed v2_6_49 runtime lock audit fields in piano audit summaries and the Medium Swing audit script;
- added `docs/ENGINE_VOICING_MEDIUM_SWING_OPEN_DROP_PHRASE_SCOPE_METHOD_LOCK_POLICY_V2_6_49.md`;
- added `tests/test_v2_6_49_engine_medium_swing_open_drop_phrase_scope_method_lock_policy.py`;
- preserved Pattern, Anticipation, Expression, Gesture, MIDI, Agent, API, HarmonyOS fixtures, and shared integration files.

Reference three-chorus audit:

```text
All The Things You Are: applied=88, matches=88, mismatches=0, filtering=88, phrase_switch_ratio=0.1429, drop2&4_run_max=1
Autumn Leaves: applied=100, matches=100, mismatches=0, filtering=100, phrase_switch_ratio=0.2308, drop2&4_run_max=2
```

Next recommended voicing-only task: `v2_6_50_engine_medium_swing_open_drop_ii_v_i_orientation_method_alignment`.

## v2_6_47 Completed — Engine Medium Swing OPEN Drop-Family Section Boundary Method-Lock Review

Completed a behavior-preserving Medium Swing voicing checkpoint on the merged `v2_10_8` baseline plus `v2_6_46` continuity audit.

Implemented:

- added section-boundary method-lock readability audit fields;
- confirmed section boundaries enter with readable `drop2` / `drop3` methods;
- confirmed `drop2_and_4` stays away from boundary entry and remains phrase-internal low-frequency color;
- added `docs/ENGINE_VOICING_MEDIUM_SWING_OPEN_DROP_SECTION_BOUNDARY_METHOD_LOCK_REVIEW_V2_6_47.md`;
- added `tests/test_v2_6_47_engine_medium_swing_open_drop_section_boundary_method_lock_review.py`;
- preserved selected notes, OPEN method weights, Pattern, Anticipation, Expression, Gesture, MIDI, Agent, API, and HarmonyOS behavior.

Reference three-chorus audit:

```text
All The Things You Are: boundaries=11, boundary_method_switches=8, drop2_and_4_entries=0, warnings=0, avg_motion_max=4.5
Autumn Leaves: boundaries=11, boundary_method_switches=8, drop2_and_4_entries=0, warnings=0, avg_motion_max=5.25
```

Next recommended voicing-only task: `v2_6_48_engine_medium_swing_open_drop_phrase_scope_method_continuity_plan`.

## v2_6_46 Completed — Engine Medium Swing OPEN Drop-Family Voice-Leading Continuity Audit

Completed a behavior-preserving Medium Swing voicing checkpoint on the merged `v2_10_8` baseline plus `v2_6_45` method calibration.

Implemented:

- added cross-region OPEN drop-family voice-leading continuity audit fields;
- tracked method-switch and section-boundary transitions separately;
- added accepted motion guardrails for top, low, average motion, and span jump;
- updated the Medium Swing audit script so the two reference standard demos verify continuity in addition to method ratios;
- added `docs/ENGINE_VOICING_MEDIUM_SWING_OPEN_DROP_VOICE_LEADING_CONTINUITY_AUDIT_V2_6_46.md`;
- added `tests/test_v2_6_46_engine_medium_swing_open_drop_voice_leading_continuity_audit.py`;
- preserved selected notes, OPEN method weights, Pattern, Anticipation, Expression, Gesture, MIDI, Agent, API, and HarmonyOS behavior.

Reference three-chorus audit:

```text
All The Things You Are: transitions=119, method_switches=51, section_boundaries=11, warnings=0, top_motion_max_abs=5, low_motion_max_abs=7, avg_motion_max=5.25
Autumn Leaves: transitions=161, method_switches=68, section_boundaries=11, warnings=0, top_motion_max_abs=5, low_motion_max_abs=7, avg_motion_max=5.25
```

Next recommended voicing-only task: `v2_6_47_engine_medium_swing_open_drop_section_boundary_method_lock_review`.

## v2_6_45 Completed — Engine Medium Swing Open/Drop Method Lock Calibration

Completed a voicing-only Medium Swing OPEN drop-family calibration on the merged `v2_10_8` baseline.

Implemented:

- kept Medium Swing in OPEN family only;
- kept `generic_open` as fallback-only with normal runtime weight `0.0`;
- recalibrated baseline OPEN weights to `drop2=0.52`, `drop3=0.38`, `drop2_and_4=0.10`;
- recalibrated bridge/final-chorus contrast weights so DROP3 remains the contrast/lift method while DROP2&4 stays controlled;
- added `docs/ENGINE_VOICING_MEDIUM_SWING_OPEN_DROP_METHOD_LOCK_CALIBRATION_V2_6_45.md`;
- added `tests/test_v2_6_45_engine_medium_swing_open_drop_method_lock_calibration.py`;
- added piano audit checkpoint fields for the Medium Swing open/drop calibration profile.

Reference three-chorus audit:

```text
All the Things You Are: events=174, methods={drop2:104, drop3:69, drop2_and_4:1}
Autumn Leaves: events=223, methods={drop2:87, drop3:103, drop2_and_4:33}
```

Both pass the control rules: OPEN family only, bridge/final DROP3 share above baseline, DROP2&4 total ratio <= 0.20, no failed register guards, and no missing piano events.

Next recommended voicing-only task: `v2_6_46_engine_medium_swing_open_drop_voice_leading_continuity_audit`.

## v2_6_44 Completed — Engine Ballad SPREAD Voicing Phase Summary and Handoff

Completed behavior-preserving Ballad SPREAD voicing phase handoff.

Implemented:

- added `docs/ENGINE_VOICING_BALLAD_SPREAD_PHASE_SUMMARY_AND_HANDOFF_V2_6_44.md`;
- added `tests/test_v2_6_44_engine_ballad_spread_voicing_phase_summary_and_handoff.py`;
- added policy metadata that freezes the accepted Ballad SPREAD guardrails without changing runtime candidate selection;
- added piano audit fields for the phase summary, completed milestones, frozen guardrails, and next candidate voicing areas;
- preserved Pattern / Anticipation / Expression / Gesture / MIDI / Agent / API / HarmonyOS behavior.

Frozen Misty / Jazz Ballad / 3 choruses guardrails:

```text
5-note: 124
6-note: 72
4-note: 0
7-note: 0
2+3: 114
2+4: 68
1+4: 10
3+3: 4
lower_upper_too_tight_events: 0
lower_upper_too_wide_events: 0
top_note_max: 72
major_seventh_unnotated_sharp11_events: 0
```

Next recommended voicing area: `medium_swing_open_drop_method_lock_calibration`.

## v2_6_33 Completed — Engine Ballad SPREAD Wide Gap Deferred Outlier Strategy

Completed voicing-only deferred strategy for the remaining `2+3 Fm7` wide-gap outliers from v2_6_32.

Implemented:

- added `docs/ENGINE_VOICING_BALLAD_SPREAD_WIDE_GAP_DEFERRED_OUTLIER_STRATEGY_V2_6_33.md`;
- added `tests/test_v2_6_33_engine_ballad_spread_wide_gap_deferred_outlier_strategy.py`;
- added selector metadata that detects wide-gap same-recipe alternatives without replacing runtime notes;
- added piano audit fields for deferred wide-gap outlier strategy events;
- preserved Pattern / Anticipation / Expression / Gesture / MIDI / Agent / API / HarmonyOS behavior.

Misty / Jazz Ballad / 3 choruses observation:

```text
5-note: 124
6-note: 72
2+3: 114
2+4: 68
1+4: 10
3+3: 4
lower_upper_too_tight_events: 0
lower_upper_too_wide_events: 2
spread_gap_aware_candidate_scope_micro_calibration_events: 3
spread_wide_gap_deferred_outlier_strategy_events: 2
top_note_max: 72
```

The remaining wide gaps are intentionally still audible/auditable. Runtime replacement remains disabled because local same-recipe replacement caused density-lane cascade in experiments.

Next recommended voicing-only task: `v2_6_34_engine_ballad_spread_2plus3_wide_gap_source_inventory_plan`.

## v2_6_31 Completed — Engine Ballad SPREAD Lower/Upper Gap & Weight Balance Audit

Completed voicing-only audit/guardrail pass on the merged `v2_8_24` integration baseline:

- added explicit lower/upper group gap audit fields to `piano_audit.py`;
- tracked gap stats by grouping, density, and recipe;
- flagged tight gaps below 2 semitones and wide gaps above 7 semitones;
- deliberately preserved the existing `v2_6_30` density lane instead of applying a scorer patch that would distort the 5-note / 6-note balance;
- confirmed Misty Ballad 3-chorus output remains `5-note=120`, `6-note=76`, `1+4=10`, `4-note=0`, `7-note=0`, and `top_note_max=72`.

Next recommended voicing-only task: `v2_6_32_engine_ballad_spread_gap_aware_candidate_scope_micro_calibration`.

## v2_6_28 Completed — Engine Ballad SPREAD Top Voice / Register Micro Calibration

## Latest Engine Task Completed

```text
v2_6_30_engine_ballad_spread_1plus4_lower_foundation_calibration
```

Goal: restore Ballad SPREAD `1+4` at low frequency while adding lower foundation register/thickness audit visibility.

Completed scope:

- restored `spread_1plus4_contract` as a low-frequency Jazz Ballad SPREAD runtime lane;
- kept `2+3` as the main 5-note body and `2+4` as the main 6-note body;
- preserved 5-note / 6-note near 6:4, 4-note SPREAD disabled, and default maj7#11 absence;
- added lower foundation note/span/recipe/low-register diagnostics to the piano audit summary;
- tightened 3-note lower foundation placement to stay within one octave;
- added `docs/ENGINE_VOICING_BALLAD_SPREAD_1PLUS4_LOWER_FOUNDATION_CALIBRATION_V2_6_30.md`;
- added `tests/test_v2_6_30_engine_ballad_spread_1plus4_lower_foundation_calibration.py`.

Next recommended Engine/Voicing task:

```text
v2_6_31_engine_ballad_spread_lower_upper_gap_and_weight_balance
```

Goal: use the new lower foundation audit fields plus listening demo to balance lower/upper gap and lower foundation weight without changing Pattern, Anticipation, Expression, MIDI, Agent, API, or shared integration docs.

---


Completed voicing-only listening calibration:

- added a narrow grouped-SPREAD top-register micro bias in `selection/selector.py`;
- enabled the bias from `styles/jazz_ballad/voicing_policy.py` metadata only;
- kept ordinary runtime groupings as `2+3`, `2+4`, and `3+3`;
- kept `1+4` out of ordinary runtime;
- preserved 5-note:6-note near 6:4, zero 4-note SPREAD, zero 7-note SPREAD in the Misty seed, and zero unnotated maj7#11;
- lowered the opening/top ceiling behavior from max top 77 to max top 74 in the Misty three-chorus audit.

Next recommended voicing-only task: `v2_6_29_engine_ballad_spread_lower_foundation_register_micro_calibration`.

## v2_6_26 Voicing cleanup — realization surface final cleanup

Completed `v2_6_26_engine_voicing_realization_surface_final_cleanup`.

Scope completed:

- kept `harmonic_realizer.py` as the final thin realization surface rather than a voicing decision owner;
- added `HarmonicRealizerSurfaceFinalCleanupProfile` with explicit owned/forbidden responsibilities;
- added per-audit-row `harmonic_realizer_surface_final_cleanup_version = v2_6_26`;
- corrected `realizer_note_audit.py` and `voicing_policy_context_adapter.py` debug metadata so request/context ownership points through `realizer_voicing_request_orchestration.py`;
- preserved Ballad/SPREAD guardrails: zero default 4-note SPREAD, 5-note:6-note near 6:4, and zero unnotated maj7#11.

Next recommended voicing-only task: `v2_6_27_engine_ballad_spread_listening_calibration_pass`.

## v2_6_25 Voicing cleanup — request orchestration/cache boundary audit

Completed `v2_6_25_engine_voicing_request_orchestration_cache_boundary_audit`.

Scope:

```text
harmonic_realizer.py
  no longer owns VoicingRequest construction
  no longer owns one-voicing-per-region cache implementation
  no longer owns explicit fresh revoicing escape hatch helper

realizer_voicing_request_orchestration.py
  owns request/cache orchestration only
  delegates event policy context to voicing_policy_context_adapter.py
  delegates musical resolution to core VoicingResolver
  does not construct sources / choose colors / project / select / write MIDI / build audit payloads
```

Next recommended task:

```text
v2_6_26_engine_voicing_realization_surface_final_cleanup
```

Goal: audit the now-small `harmonic_realizer.py` realization surface, remove remaining misleading old comments/imports/tests, and decide whether the realizer is sufficiently thin.

---

## v2_6_24 Voicing cleanup — realizer NoteEvent/audit split

- NoteEvent/audit/debug helpers have moved from `harmonic_realizer.py` to `realization/realizer_note_audit.py`.
- `harmonic_realizer.py` should remain an orchestration boundary: normalize policy, adapt event context, build `VoicingRequest`, call `VoicingResolver`, reuse/copy region voicings, pass selected plans into `GestureRealizer`, and return final `NoteEvent` output.
- `realizer_note_audit.py` may serialize PatternEvent / Expression / VoicingPlan / NoteEvent debug payloads and trim partial inner-movement reattacks using already-selected voicing metadata, but it must not build requests, construct sources, decide color permission, project voicings, score/select candidates, apply expression, or write MIDI.
- Current Ballad guardrails remain: 4-note SPREAD disabled, 5-note / 6-note near 6:4, maj7#11 absent unless written/intent-enabled.

Recommended next task:

```text
v2_6_25_engine_voicing_request_orchestration_cache_boundary_audit
```

Goal: audit the remaining `harmonic_realizer.py` request orchestration/cache responsibilities and ensure one-voicing-per-region reuse remains explicit, behavior-preserving.

## v2_6_23 Voicing cleanup — harmonic realizer policy/context adapter

- Event-scoped voicing policy/context adaptation has moved from `harmonic_realizer.py` to `realization/voicing_policy_context_adapter.py`.
- `harmonic_realizer.py` should remain a request-orchestration and NoteEvent realization boundary: build `VoicingRequest`, call `VoicingResolver`, reuse/copy region voicings, pass selected plans into `GestureRealizer`, and maintain final piano audit output.
- `voicing_policy_context_adapter.py` may translate PatternEvent metadata into `VoicingPolicy.metadata`, but it must not construct sources, decide color permission, project voicings, score/select candidates, apply expression, or write MIDI.
- Current Ballad guardrails remain: 4-note SPREAD disabled, 5-note / 6-note near 6:4, maj7#11 absent unless written/intent-enabled.

Recommended next task:

```text
v2_6_24_engine_voicing_realizer_note_audit_cleanup
```

Goal: continue cleanup inside `harmonic_realizer.py` by separating NoteEvent/audit/debug helpers from voicing request orchestration, behavior-preserving.

## v2_6_22 Engine Voicing Cleanup — retired SPREAD pilot logic

Completed cleanup scope:

- removed retired Ballad SPREAD pilot / dry-run / safe-dry-run / runtime-guard / selection-audit public workflow;
- kept current grouped SPREAD runtime candidate pool as the only Ballad SPREAD runtime route;
- kept `spread_runtime_adapter.py` as the projection-candidate adapter owner;
- kept `spread.py` as current compatibility facade only, not a home for old pilot code;
- deleted stale v2_2 pilot tests that were asserting removed behavior;
- verified Misty three-chorus density/color guardrails remain stable.

Next recommended Engine/Voicing task:

```text
v2_6_23_engine_voicing_harmonic_realizer_policy_context_adapter_cleanup
```

Goal: continue cleanup at the harmonic-realizer adapter boundary so realizer metadata remains policy/context adaptation only, not source construction, color permission, projection, selector, expression, or MIDI behavior.

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

## v2_6_18 Completed — Engine Voicing Content Source Inventory Behavior-Preserving Split

Completed voicing-only source-boundary split:

- added `content_source_inventory.py` as the owner for family-to-degree source inventory;
- kept `content_planner.py` as public compatibility facade and recipe orchestration layer;
- preserved historical imports for `trim_content_degrees`, `source_preserves_seventh_chord_identity`, and `seventh_chord_source_integrity_notes` through `content_planner.py`;
- did not move content-family routing, color permission ownership, source balance, upper structure, disposition, register, projection, pattern, expression, gesture, MIDI, API, or Agent behavior;
- preserved Jazz Ballad `5-note:6-note ~= 6:4`, zero default 4-note SPREAD, low-frequency 7-note, and zero unnotated maj7#11.

Next recommended voicing-only task: `v2_6_19_engine_voicing_color_permission_adapter_cleanup`.
## v2_6_19 Completed — Engine Voicing Color Permission Adapter Cleanup

Goal: clean up color-permission glue after the content source inventory split without moving voicing source construction into the color-permission layer.

Completed scope:

- added `docs/ENGINE_VOICING_COLOR_PERMISSION_ADAPTER_CLEANUP_V2_6_19.md`;
- added `tests/test_v2_6_19_engine_voicing_color_permission_adapter_cleanup.py`;
- moved explicit chart color helpers and expansion color candidate helpers into `color_permission.py`;
- added `build_voicing_color_permission_context` as the single adapter for explicit + expansion color admission;
- updated `content_source_inventory.py` to consume color-permission helpers while retaining source-construction ownership;
- updated `content_family_router.py` to reuse explicit-color helpers from `color_permission.py`;
- preserved v2_6_14/v2_6_15 Misty density/color guardrails.

Next recommended voicing-only task: `v2_6_20_engine_voicing_source_balance_boundary_cleanup`.

## v2_6_20 Completed — Engine Voicing Source Balance Boundary Cleanup

Goal: clean up the source-balance scoring boundary after the content-family, source-inventory, and color-permission splits.

Completed scope:

- kept `source_balance.py` as the owner for source-family scoring / bias only;
- added `SourceBalanceProfile` and `source_balance_profile(...)` for inspectable scoring metadata;
- added explicit owned/forbidden responsibility constants to prevent future boundary drift;
- preserved `SOURCE_BALANCE_CONTRACT_VERSION = v2_1_43` and altered-dominant intensity scoring `v2_2_88`;
- hardened source-key extraction from current `content_recipe.validity_notes` metadata without moving source inventory ownership into source balance;
- preserved v2_6_14/v2_6_15 Misty density/color guardrails.

Next recommended voicing-only task: `v2_6_21_engine_voicing_upper_structure_boundary_audit`.

## v2_6_21 Completed — Engine Voicing Upper Structure Boundary Audit

Goal: audit the Upper Structure source boundary after the source-balance cleanup and ensure it remains source-only.

Completed scope:

- kept `upper_structure.py` as the owner for source-level upper-structure degree recipes only;
- added `UpperStructureBoundaryProfile` and `upper_structure_boundary_profile(...)` for inspectable responsibility metadata;
- added explicit owned/forbidden responsibility constants to prevent future boundary drift;
- preserved `UPPER_STRUCTURE_SOURCE_VERSION = v2_2_88` and existing harmonic-expansion / altered-dominant policy gates;
- confirmed Upper Structure does not import projection, register, selector, voice-leading, runtime adapter, or MIDI owners;
- preserved v2_6_14/v2_6_15 Misty density/color guardrails.

Next recommended voicing-only task: `v2_6_22_engine_voicing_harmonic_realizer_policy_context_adapter_cleanup`.

## v2_6_27 Completed — Engine Ballad SPREAD Listening Calibration

Completed voicing-only listening calibration:

- kept Ballad SPREAD focused on ordinary runtime groupings `2+3`, `2+4`, and `3+3`;
- demoted `1+4` to an explicit upper4-color/listening-isolation lane instead of default comping body;
- filtered zero-weight compatible contracts out of the runtime candidate pool;
- kept the 5-note:6-note balance near 6:4 after removing 1+4 from ordinary runtime;
- preserved zero default 4-note SPREAD and zero default unnotated maj7#11.

Next recommended voicing-only task: `v2_6_28_engine_ballad_spread_top_voice_and_register_micro_calibration`.

## v2_6_29 Completed — Engine Voicing Drop Projection Audit Counts

Completed voicing-only audit visibility pass:

- kept all runtime musical behavior unchanged from v2_6_28;
- added drop projection audit counters to `piano_audit.py`;
- counted ordinary top-level OPEN drop usage separately from SPREAD upper-group drop usage;
- added density/grouping/recipe breakdowns so upper group DROP2 / DROP3 inside 5-note, 6-note, and 7-note SPREAD voicings is visible;
- confirmed current Misty Ballad runtime has 76 upper-drop events inside 6-note `2+4` SPREAD: `drop2=12`, `drop3=64`;
- preserved zero default 4-note SPREAD, zero default `1+4`, and zero unnotated maj7#11.

Next recommended voicing-only task: `v2_6_30_engine_ballad_spread_lower_foundation_register_micro_calibration`.

## v2_6_32 Completed — Engine Ballad SPREAD Gap-Aware Candidate-Scope Micro Calibration

Status: completed on top of the merged `v2_8_24` integration baseline.

Scope:

```text
Engine voicing-only
No Pattern / Anticipation / Expression / Gesture / MIDI changes
No Agent / API / HarmonyOS/shared integration changes
```

Implemented:

- same-recipe-only gap-aware candidate replacement for Jazz Ballad SPREAD groupwise selector;
- audit fields for v2_6_32 micro-calibration applications;
- regression tests for policy metadata, Misty guardrails, gap audit, and event-row metadata;
- documentation of why broad gap scoring was avoided.

Current Misty / Jazz Ballad / 3-chorus guardrails:

```text
5-note: 124
6-note: 72
4-note: 0
7-note: 0
1+4: 10
maj7#11 default events: 0
top_note_max: 72
lower_foundation_span_violation_events: 0
lower_upper_too_tight_events: 0
lower_upper_too_wide_events: 2
```

Recommended next task:

```text
v2_6_33_engine_ballad_spread_wide_gap_deferred_outlier_strategy
```

Next task should target only the two remaining `2+3` wide-gap Fm7 outliers and must not use a broad scorer patch that changes the density lane.

## v2_6_34 Completed — Engine Ballad SPREAD 2+3 Wide Gap Source Inventory Plan

Status: completed on top of the merged `v2_8_24` integration baseline.

Scope:

```text
Engine voicing-only
No Pattern / Anticipation / Expression / Gesture / MIDI changes
No Agent / API / HarmonyOS/shared integration changes
```

Implemented:

- kept the two remaining `2+3 Fm7` wide-gap rows deferred rather than locally replacing them;
- added source-inventory plan metadata for the deferred rows;
- exposed source-inventory plan summary fields in `piano_audit.py`;
- documented why direct runtime replacement is unsafe for this case;
- preserved the accepted Ballad SPREAD density and register guardrails.

Current Misty / Jazz Ballad / 3-chorus guardrails:

```text
5-note: 124
6-note: 72
4-note: 0
7-note: 0
1+4: 10
top_note_max: 72
lower_upper_too_tight_events: 0
lower_upper_too_wide_events: 2
spread_wide_gap_source_inventory_plan_events: 2
spread_wide_gap_source_inventory_runtime_replacement_enabled_events: 0
```

Recommended next task:

```text
v2_6_35_engine_ballad_spread_phrase_scope_wide_gap_candidate_availability
```

Next task should test phrase-scope or source-inventory candidate availability before state advancement, not broad scorer or local runtime replacement.

## v2_6_35 Completed — Engine Ballad SPREAD Phrase-Scope Wide Gap Candidate Availability

Status: completed on top of the merged `v2_8_24` integration baseline.

Scope:

```text
Engine voicing-only
No Pattern / Anticipation / Expression / Gesture / MIDI changes
No Agent / API / HarmonyOS/shared integration changes
```

Implemented:

- realized the top-stable same-recipe candidate for the two remaining `2+3 Fm7` wide-gap rows;
- protected phrase-level density by advancing `VoicingState` with the original phrase anchor for those two rows;
- exposed phrase-scope wide-gap metadata and summary audit fields;
- preserved the accepted Ballad SPREAD density, 1+4 frequency, register, and default no-4/no-7 guardrails.

Current Misty / Jazz Ballad / 3-chorus guardrails:

```text
5-note: 124
6-note: 72
4-note: 0
7-note: 0
1+4: 10
top_note_max: 72
lower_upper_too_tight_events: 0
lower_upper_too_wide_events: 0
spread_phrase_scope_wide_gap_candidate_availability_events: 2
spread_phrase_scope_wide_gap_state_advance_protected_events: 2
spread_phrase_scope_wide_gap_runtime_realization_enabled_events: 2
```

Recommended next task:

```text
v2_6_36_engine_ballad_spread_phrase_state_boundary_regression_and_listening_review
```

Next task should validate/listen for any discontinuity caused by the state-advance protection boundary before generalizing the mechanism beyond the two known Fm7 rows.

## v2_6_36_engine_ballad_spread_phrase_state_boundary_regression_and_listening_review

Status: completed on top of the merged `v2_8_24` integration baseline.

Scope:

```text
Engine voicing-only
No Pattern / Anticipation / Expression / Gesture / MIDI changes
No Agent / API / HarmonyOS/shared integration changes
```

Implemented:

- Added phrase-state boundary review audit fields for the v2_6_35 state-protected events.
- Verified that the immediate next Bb7 events use the protected Fm7 phrase anchor as previous `VoicingState` notes.
- Verified that the substituted realized Fm7 notes are not used as the following event state.
- Kept v2_6_35 behavior unchanged and did not generalize the mechanism.

Misty / Jazz Ballad / 3 choruses observation:

```text
5-note: 124
6-note: 72
4-note: 0
7-note: 0
1+4: 10
lower_upper_too_tight_events: 0
lower_upper_too_wide_events: 0
spread_phrase_state_boundary_review_events: 2
spread_phrase_state_boundary_review_warning_events: 0
spread_phrase_state_boundary_review_next_event_top_motion_max: 0.0
spread_phrase_state_boundary_review_next_event_voice_leading_distance_max: 5.333
```

Recommended next task:

```text
v2_6_37_engine_ballad_spread_phrase_state_boundary_helper_cleanup
```

Only continue if the v2_6_36 listening demo sounds continuous around the two protected Fm7 → Bb7 boundaries. Do not introduce a broad scorer.

## v2_6_37_engine_ballad_spread_phrase_state_boundary_helper_cleanup

Status: completed on top of the merged `v2_8_24` integration baseline.

Scope:

```text
Engine voicing-only
No Pattern / Anticipation / Expression / Gesture / MIDI changes
No Agent / API / HarmonyOS/shared integration changes
```

Implemented:

- Added `VoicingStateAdvanceAnchor` as the named runtime helper for separating realized notes from the notes used to advance `VoicingState`.
- Replaced the ad-hoc selector/resolver metadata handoff with a helper-owned contract while preserving legacy override aliases for current audits.
- Kept v2_6_35/v2_6_36 audible behavior unchanged.
- Added audit fields for helper cleanup events and previous-state anchor visibility.

Current Misty / Jazz Ballad / 3-chorus guardrails:

```text
5-note: 124
6-note: 72
4-note: 0
7-note: 0
1+4: 10
lower_upper_too_tight_events: 0
lower_upper_too_wide_events: 0
spread_phrase_state_boundary_helper_cleanup_events: 2
spread_phrase_state_boundary_helper_state_anchor_events: 2
spread_phrase_state_boundary_helper_previous_state_anchor_events: 3
top_note_max: 72
```

Recommended next task:

```text
v2_6_38_engine_ballad_spread_phrase_state_anchor_generalization_boundary_plan
```

Next task should decide whether the helper remains a narrow Ballad SPREAD boundary or becomes a more general core voicing mechanism. Do not generalize without explicit policy gates and regression tests.

## v2_6_38_engine_ballad_1and_whisper_continuity_patch

Status: completed on top of the merged `v2_8_24` integration baseline plus Engine v2_6_37.

Scope:

```text
Engine Jazz Ballad continuity bugfix
Pattern / Expression / Realizer boundary interaction only
No voicing selector/source/density changes
No Anticipation changes
No MIDI writer changes
No Agent / API / HarmonyOS/shared integration changes
```

Implemented:

- Converted the near-downbeat 1& Ballad whisper / soft-mark second touch from a full chord hit into a non-interrupting `inner_movement` on `projection_group`.
- Kept the beat-1 foundation sustained through the 1& re-touch, while only the upper/projection group is trimmed and reattacked.
- Updated partial-reattack release timing to use performed swing-upbeat timing, so the old logical `.5` trim does not create a small gap before the 2/3 rendered upbeat.
- Confirmed Misty bars 41, 63, and 95 keep at least two foundation notes sustained through the 1& upper re-touch.

Current Misty / Jazz Ballad / 3-chorus guardrails:

```text
5-note: 124
6-note: 72
4-note: 0
7-note: 0
2+3: 114
2+4: 68
1+4: 10
3+3: 4
top_note_max: 72
lower_upper_too_tight_events: 0
lower_upper_too_wide_events: 0
```

Recommended next task:

```text
v2_6_39_engine_ballad_spread_post_continuity_listening_checkpoint
```

First listen around Misty bars 41, 63, and 95. If the continuity is accepted, resume voicing work from the stable v2_6_37/v2_6_38 baseline rather than adding more Ballad pattern behavior.

## v2_6_39_engine_ballad_spread_post_continuity_listening_checkpoint

Status: completed on top of the merged `v2_8_24` integration baseline plus Engine v2_6_38.

Scope:

```text
Engine voicing-track checkpoint after Ballad continuity bugfix
Observational audit/test only
No runtime candidate/source/density change
No new Pattern / Anticipation / Expression / Realizer / MIDI behavior
No Agent / API / HarmonyOS/shared integration changes
```

Implemented:

- Added `ballad_spread_post_continuity_listening_checkpoint` policy metadata.
- Added compact post-continuity audit fields in `build_piano_musical_audit()`.
- Confirmed Misty bars 41, 63, and 95 have projection-only 1& re-touch with lower/foundation notes sustaining through the re-touch.
- Confirmed v2_6_35/v2_6_37 phrase-state protected Fm7 → Bb7 boundaries still have zero warnings after the continuity patch.
- Preserved accepted Ballad SPREAD voicing guardrails.

Current Misty / Jazz Ballad / 3-chorus guardrails:

```text
5-note: 124
6-note: 72
4-note: 0
7-note: 0
2+3: 114
2+4: 68
1+4: 10
3+3: 4
lower_upper_too_tight_events: 0
lower_upper_too_wide_events: 0
top_note_max: 72
post_continuity_checkpoint_passed: true
post_continuity_warning_events: 0
phrase_state_boundary_warning_events: 0
```

Recommended next task:

```text
v2_6_40_engine_ballad_spread_phrase_state_anchor_policy_boundary
```

Next task should decide the policy boundary for `realized_notes` versus `state_anchor_notes`: keep it as a narrow Ballad SPREAD mechanism, or expose it as a policy-gated core voicing capability. Do not generalize it globally without an explicit gate and regression tests.

## v2_6_40_engine_ballad_spread_phrase_state_anchor_policy_boundary

Status: completed on top of the merged `v2_8_24` integration baseline plus Engine v2_6_39.

Scope:

```text
Engine voicing policy-boundary pass
Behavior-preserving
No runtime candidate/source/density change
No new Pattern / Anticipation / Expression / Realizer / MIDI behavior
No Agent / API / HarmonyOS/shared integration changes
```

Implemented:

- Added a policy gate around production consumption of `VoicingStateAdvanceAnchor`.
- Kept the helper in core voicing runtime, but required explicit style `VoicingPolicy.metadata` permission before resolver state advancement may use anchor notes instead of realized notes.
- Enabled the gate only for the accepted Jazz Ballad SPREAD scope: `ballad_spread_phrase_scope_wide_gap_candidate_availability`.
- Added audit fields to confirm two current Ballad SPREAD anchor events require the gate and three subsequent rows observe the consumed previous-state gate.
- Preserved the accepted Ballad SPREAD voicing and post-continuity guardrails.

Current Misty / Jazz Ballad / 3-chorus guardrails:

```text
5-note: 124
6-note: 72
4-note: 0
7-note: 0
2+3: 114
2+4: 68
1+4: 10
3+3: 4
lower_upper_too_tight_events: 0
lower_upper_too_wide_events: 0
top_note_max: 72
policy_boundary_events: 2
policy_boundary_previous_gate_consumed_events: 3
phrase_state_boundary_warning_events: 0
```

Recommended next task:

```text
v2_6_41_engine_ballad_spread_same_chord_reattack_continuity_calibration
```

Next task should review same-chord reattack continuity. Do not change density lanes; focus on whether repeated touches in the same chord region should reuse the previous foundation/voicing or only move upper/projection notes when explicitly marked as movement/fill.

## v2_6_41_engine_ballad_spread_same_chord_reattack_continuity_calibration

Status: completed on top of the merged `v2_8_24` integration baseline plus Engine v2_6_40.

Scope:

```text
Engine voicing-only same-chord reattack continuity audit
Behavior-preserving
No runtime candidate/source/density change
No new Pattern / Anticipation / Expression / MIDI behavior
No Agent / API / HarmonyOS/shared integration changes
```

Implemented:

- Kept the existing one-default-voicing-per-chord-region cache as the correct boundary for same-chord reattacks.
- Added explicit metadata and audit fields confirming later events in the same chord region reuse the cached voicing unless a future event opts into fresh revoicing.
- Confirmed repeated re-touch / answer / whisper events keep exact voicing and lower/foundation stability while expression/realization handles any projection-group partial reattack.
- Preserved the accepted Ballad SPREAD density, gap, top-register, post-continuity, and phrase-state boundary guardrails.

Current Misty / Jazz Ballad / 3-chorus guardrails:

```text
5-note: 124
6-note: 72
4-note: 0
7-note: 0
2+3: 114
2+4: 68
1+4: 10
3+3: 4
same_chord_reattack_events: 46
same_chord_reattack_region_voicing_reused_events: 46
same_chord_reattack_exact_voicing_reuse_events: 46
same_chord_reattack_foundation_stable_events: 46
same_chord_reattack_continuity_warning_events: 0
lower_upper_too_tight_events: 0
lower_upper_too_wide_events: 0
top_note_max: 72
```

Recommended next task:

```text
v2_6_42_engine_ballad_spread_safe_extension_frequency_calibration
```

Next task should tune Ballad SPREAD harmonic color frequency, especially safe extensions and maj7 color behavior, without changing density lanes or same-chord reattack continuity.


## v2_6_42_engine_ballad_spread_safe_extension_frequency_calibration — Completed

Scope: Engine voicing-only safe-extension frequency checkpoint.

Accepted Misty / Jazz Ballad / 3-chorus checkpoint:

```text
major_seventh_safe_extension_degree_counts: {"9": 14, "13": 7}
major_seventh_unnotated_sharp11_events: 0
major_seventh_safe_extension_checkpoint_passed: true
5-note: 124
6-note: 72
1+4: 10
4-note: 0
7-note: 0
lower_upper_too_tight_events: 0
lower_upper_too_wide_events: 0
top_note_max: 72
```

Recommended next task:

```text
v2_6_43_engine_ballad_spread_lower_foundation_weight_and_register_final_pass
```

## v2_6_43_engine_ballad_spread_lower_foundation_weight_and_register_final_pass — Completed

Scope: Engine voicing-only lower foundation weight/register checkpoint.

Accepted Misty / Jazz Ballad / 3-chorus checkpoint:

```text
lower_foundation_note_min: 41
lower_foundation_note_max: 58
lower_foundation_note_average: 49.93
lower_foundation_span_max: 11
lower_foundation_span_average: 6.138
lower_foundation_span_violation_events: 0
lower_foundation_low_register_events: 28
lower_foundation_low_register_events_by_grouping: {"2+4": 26, "2+3": 2}
lower_foundation_weight_register_final_pass_checkpoint_passed: true
```

Accepted grouping interpretation:

```text
2+3: stable two-note foundation; not too thin
2+4: heavier six-note foundation; low-register pressure accepted because gap/span guards pass
1+4: low-frequency color lane; one-note root foundation preserved
3+3: very low-frequency thick foundation; no low-register mud
```

Guardrails preserved:

```text
5-note: 124
6-note: 72
1+4: 10
4-note: 0
7-note: 0
lower_upper_too_tight_events: 0
lower_upper_too_wide_events: 0
top_note_max: 72
major_seventh_unnotated_sharp11_events: 0
```

Recommended next task:

```text
v2_6_44_engine_ballad_spread_voicing_phase_summary_and_handoff
```

## v2_6_48_engine_medium_swing_open_drop_phrase_scope_method_continuity_plan — Completed

Scope: Engine voicing-only, behavior-preserving audit pass.

Implemented:

```text
medium_swing_phrase_scope_method_continuity_version = v2_6_48
```

The audit derives section-local four-region phrase windows from actual OPEN DROP-family chord-region events and reports:

```text
phrase-scope method switches
DROP2&4 run length
ii–V / V–I / ii–V–I local method consistency
high-motion method switches
warnings
checkpoint pass/fail
```

Current 3-chorus Medium Swing checkpoints:

```text
All The Things You Are:
phrase_scope_events: 84
phrase_scope_method_switch_ratio: 0.4048
drop2_and_4_run_max: 1
ii_v_i_events: 27
ii_v_i_method_consistent_events: 10
ii_v_i_method_switch_events: 17
high_motion_switch_events: 0
checkpoint_passed: true

Autumn Leaves:
phrase_scope_events: 117
phrase_scope_method_switch_ratio: 0.4274
drop2_and_4_run_max: 2
ii_v_i_events: 21
ii_v_i_method_consistent_events: 8
ii_v_i_method_switch_events: 13
high_motion_switch_events: 0
checkpoint_passed: true
```

Conclusion:

```text
Do not tune global OPEN weights yet.
DROP2&4 is still phrase-internal color, not phrase body.
Method switches are smooth.
The next useful issue is local ii–V / V–I / ii–V–I method alignment, not global ratio tuning.
```

Recommended next task:

```text
v2_6_49_engine_medium_swing_open_drop_phrase_scope_method_lock_policy
```

## v2_6_52_engine_medium_swing_open_drop_same_chord_reattack_comping_reuse — Completed

Scope: Engine voicing-only, behavior-preserving checkpoint.

Implemented:

```text
medium_swing_same_chord_reattack_comping_reuse_version = v2_6_52
```

The runtime already owned the correct same-region cache boundary through `RealizerVoicingRequestOrchestrator`. v2_6_52 formalizes that Medium Swing OPEN / DROP comping consumes this boundary:

```text
same chord region + same track + no explicit fresh-revoicing flag
→ reuse cached region voicing exactly
```

Current 3-chorus Medium Swing checkpoints:

```text
All The Things You Are:
same_chord_reattack_comping_reuse_events: 54
region_voicing_reused_events: 54
exact_voicing_reuse_events: 54
foundation_stable_events: 54
fresh_revoicing_events: 0
warning_events: 0
checkpoint_passed: true

Autumn Leaves:
same_chord_reattack_comping_reuse_events: 61
region_voicing_reused_events: 61
exact_voicing_reuse_events: 61
foundation_stable_events: 61
fresh_revoicing_events: 0
warning_events: 0
checkpoint_passed: true
```

Recommended next task:

```text
v2_6_53_engine_medium_swing_open_drop_safe_extension_and_top_register_checkpoint
```

## v2_6_53 — Medium Swing OPEN/DROP Safe Extension + Top Register Checkpoint

Status: completed.

Scope: Engine voicing-only, behavior-preserving checkpoint after the Medium Swing OPEN/DROP method-lock, generic 4-note rotation alignment, and same-chord reattack reuse passes.

Accepted guardrails:

```text
All The Things You Are / Medium Swing / 3 choruses / seed 3300
- top_note_max: 72
- top_note_ge_75_events: 0
- major_seventh_unnotated_sharp11_events: 0
- register_guard_failed_events: 0
- voice_leading_warning_events: 0

Autumn Leaves / Medium Swing / 3 choruses / seed 3301
- top_note_max: 72
- top_note_ge_75_events: 0
- major_seventh_unnotated_sharp11_events: 0
- register_guard_failed_events: 0
- voice_leading_warning_events: 0
```

Do not use this checkpoint to force more harmonic color. In chord-symbol-only Medium Swing, basic 4-note seventh voicings are acceptable. Safe extension means that when color is allowed, major-seventh defaults prefer `9 / 13` and do not introduce unnotated `#11` unless the chart or harmonic-color intent explicitly asks for it.

Next recommended task: `v2_6_54_engine_medium_swing_open_drop_deliberate_revoice_gesture_boundary_plan`.

## v2_6_54 — Medium Swing OPEN/DROP Deliberate Revoice Gesture Boundary Plan

Status: completed.

Scope: Engine voicing-only, behavior-preserving boundary checkpoint after same-chord reattack reuse and safe-extension/top-register checks.

Runtime boundary:

```text
same chord region + same track + no explicit revoice intent
→ reuse_cached_region_voicing_exactly

same chord region + explicit pitchless revoice intent
→ bypass cache, resolve fresh VoicingPlan, annotate deliberate boundary
```

Allowed escape hatches:

```text
force_fresh_voicing
revoice_within_region
```

Allowed intent sources:

```text
event_metadata
gesture_metadata
```

Current 3-chorus Medium Swing checkpoints:

```text
All The Things You Are:
default_reuse_events: 54
explicit_revoice_events: 0
implicit_revoice_events: 0
warning_events: 0
checkpoint_passed: true

Autumn Leaves:
default_reuse_events: 61
explicit_revoice_events: 0
implicit_revoice_events: 0
warning_events: 0
checkpoint_passed: true
```

Next recommended task: `v2_6_55_engine_medium_swing_open_drop_deliberate_revoice_micro_motion_policy_probe`.

## v2_6_55 — Medium Swing OPEN/DROP Deliberate Revoice Micro-Motion Policy Probe

Status: completed.

Scope: Engine voicing-only. This task does not create any new revoice gestures and does not change Pattern, Anticipation, Expression, MIDI, Agent, API, HarmonyOS, or shared integration files.

Runtime boundary:

```text
same chord region + no explicit fresh-revoice intent
→ reuse_cached_region_voicing_exactly

same chord region + explicit fresh-revoice intent + micro_motion policy
→ filter candidate pool to safe micro-motion candidates when available
```

Default micro-motion thresholds:

```text
foundation stable: required
max_low_motion:    0 semitones
max_top_motion:    2 semitones
max_avg_motion:    2.5 semitones
```

Allowed explicit motion policies:

```text
micro_motion
inner_motion
top_voice_answer
```

Current 3-chorus Medium Swing checkpoints:

```text
All The Things You Are:
micro_motion_runtime_enabled_events: 0
filter_applied_events: 0
warning_events: 0
checkpoint_passed: true

Autumn Leaves:
micro_motion_runtime_enabled_events: 0
filter_applied_events: 0
warning_events: 0
checkpoint_passed: true
```

Targeted probe confirms that explicit micro-motion revoice keeps only safe candidates with stable foundation, `top_motion_abs <= 2`, and `avg_motion_abs <= 2.5`.

Next recommended task: `v2_6_56_engine_medium_swing_deliberate_revoice_gesture_inventory_plan`.

## v2_6_56 — Engine Medium Swing Piano Region-Length Pattern Vocabulary Baseline

- Started the Medium Swing piano pattern track in the existing `styles/medium_swing/comping_patterns.py` source; no parallel pattern line or shadow selector was introduced.
- Replaced old bar-first / `two_chord_bar` terminology with ChordRegion-first `one_beat_region`, `two_beat_region`, `four_beat_region`, and future-safe `three_beat_region` / `five_beat_region` vocabulary metadata.
- Added region-local metadata for rhythm family, phrase role, semantic expression hint, tail-push risk, and pattern/expression/voicing boundaries.
- Preserved the current runtime-active v2_6_55 behavior by keeping newly added vocabulary zero-weight until the next lookup/weight-calibration task.
- Added `tests/test_v2_6_56_engine_medium_swing_piano_region_length_pattern_vocabulary.py` and `docs/ENGINE_MEDIUM_SWING_PIANO_REGION_LENGTH_PATTERN_VOCABULARY_BASELINE_V2_6_56.md`.

Recommended next task: `v2_6_57_engine_medium_swing_piano_region_length_candidate_lookup_policy`.

## v2_6_57 — Engine Medium Swing Piano Region-Length Candidate Lookup Policy

- Continued the Medium Swing piano pattern track in the existing `styles/medium_swing/comping_patterns.py` source; no parallel pattern source or bar-first `two_chord_bar` route was added.
- Kept `PATTERN_LIBRARY_VERSION=v2_6_56` as the vocabulary baseline and added `candidate_lookup_policy_version=v2_6_57` metadata for ChordRegion-length-aware candidate routing.
- Conservatively activated selected 4-beat, 2-beat, and 1-beat region-local vocabulary candidates with low positive weights inside their matching region-length family.
- Added arrangement policy metadata for `piano_region_length_candidate_lookup_policy_version`.
- Updated older Medium Swing exact-count voicing tests to assert reuse/top-register invariants instead of frozen event counts, because pattern activation can legitimately increase same-region reattack events while preserving exact cached-voicing reuse.
- Confirmed All The Things You Are / Medium Swing / 3 choruses: active region-length lookup candidates appear, `top_note_max=72`, `top_note_ge_75_events=0`, `voice_leading_warning_events=0`.
- Confirmed Autumn Leaves / Medium Swing / 3 choruses: active region-length lookup candidates appear, `top_note_max=72`, `top_note_ge_75_events=0`, `voice_leading_warning_events=0`.
- Added `tests/test_v2_6_57_engine_medium_swing_piano_region_length_candidate_lookup_policy.py` and `docs/ENGINE_MEDIUM_SWING_PIANO_REGION_LENGTH_CANDIDATE_LOOKUP_POLICY_V2_6_57.md`.

Recommended next task: `v2_6_58_engine_medium_swing_piano_region_length_weight_calibration`.

## v2_6_58 — Engine Medium Swing Piano Region-Length Weight Calibration

- Calibrated the existing `styles/medium_swing/comping_patterns.py` region-length-aware piano vocabulary without adding a parallel selector or bar-first path.
- Kept `PATTERN_LIBRARY_VERSION=v2_6_56` and `CANDIDATE_LOOKUP_POLICY_VERSION=v2_6_57`; added `WEIGHT_CALIBRATION_POLICY_VERSION=v2_6_58`.
- Adjusted 4-beat candidate weights toward stable primary / offbeat secondary / active controlled / tail-push rare.
- Made 2-beat and 1-beat short-region candidates more anchor-led so dense harmonic rhythm stays supported without overproducing offbeats.
- Updated Medium Swing pattern organization tests and added `tests/test_v2_6_58_engine_medium_swing_piano_region_length_weight_calibration.py`.
- Generated All The Things You Are and Autumn Leaves three-chorus Medium Swing demos plus audit summary/report.

Recommended next task: `v2_6_59_engine_medium_swing_piano_comping_history_continuity_scorer`.

## v2_6_59 — Engine Medium Swing Piano Comping History Continuity Scorer

- Continued directly on the existing Medium Swing piano region-length pattern line; no parallel selector or shadow pattern source was added.
- Added a lightweight history scorer to `StyleProfile.plan_region()` that reweights the existing region-length candidate pool before normal weighted sampling.
- Added Medium Swing arrangement policy metadata: `piano_comping_history_continuity_scorer=True`, `piano_comping_history_continuity_scorer_version=v2_6_59`, and a no-parallel-selector contract.
- The scorer penalizes exact repeats, non-stable family repeat, consecutive offbeat, recent offbeat clusters, recent active, and recent tail-push; it gives small stable-reset bonuses after active/offbeat contexts.
- Selected piano events expose v2_6_59 history metadata for audit while remaining pitchless and free of final velocity/duration/pedal or voicing fields.
- Generated All The Things You Are and Autumn Leaves three-chorus demos plus v2_6_59 audit summary/report.

Recommended next task: `v2_6_60_engine_medium_swing_harmonic_function_aware_piano_comping_policy`.

## v2_6_60 — Engine Medium Swing Harmonic-Function-Aware Piano Comping Policy

- Continued directly on the existing ChordRegion-first Medium Swing piano pattern system; no new parallel selector or bar-level two-chord-bar logic was added.
- Added a conservative harmonic-function multiplier stage in `StyleProfile.plan_region()` before the v2_6_59 history scorer.
- Added Medium Swing arrangement policy metadata: `piano_comping_harmonic_function_policy=True`, `piano_comping_harmonic_function_policy_version=v2_6_60`, and a no-parallel-selector/no-two-chord-bar contract.
- The policy uses `classify_functional_motion()` and ChordRegion section/ending flags to label `predominant_to_dominant`, `dominant_resolution`, `tonic_resolution`, `section_start`, `section_end`, `ending`, `tonic_prolongation`, and `turnaround_like` contexts.
- Selected piano events expose v2_6_60 harmonic metadata for audit while remaining pitchless and free of final velocity/duration/pedal or voicing fields.
- Generated All The Things You Are and Autumn Leaves three-chorus demos plus v2_6_60 audit summary/report.

Recommended next task: `v2_6_61_engine_medium_swing_region_first_anticipation_compatibility_checkpoint`.

## v2_6_61 — Engine Medium Swing Region-First Anticipation Compatibility Checkpoint

Status: completed.

Scope: Engine pattern/anticipation compatibility checkpoint. This does not add new piano rhythm cells, voicing behavior, expression realization, gesture behavior, MIDI writer behavior, Agent/API/HarmonyOS changes, or a parallel pattern path.

Runtime contract:

```text
previous ChordRegion tail slot = previous_region.duration_beats - 0.5
4-beat previous region → local 3.5
2-beat previous region → local 1.5
1-beat previous region → local 0.5, usually blocked by existing anchor occupancy
```

Current standard-tune checkpoints:

```text
All The Things You Are:
active_anticipation_count: 8
target_local_counts: {3.5: 7, 1.5: 1}
invalid_region_first_rows: 0
top_note_max: 72
voice_leading_warning_events: 0

Autumn Leaves:
active_anticipation_count: 3
target_local_counts: {1.5: 2, 3.5: 1}
invalid_region_first_rows: 0
top_note_max: 72
voice_leading_warning_events: 0
```

Next recommended task: `v2_6_62_engine_medium_swing_coverage_guard_region_first_cleanup`.

## v2_6_62 — Engine Medium Swing CoverageGuard Region-First Cleanup

Status: completed.

Scope: Engine Medium Swing piano region-first coverage checkpoint. This does not add new rhythm cells, voicing behavior, expression realization, gesture behavior, MIDI writer behavior, Agent/API/HarmonyOS changes, or a parallel pattern path.

Runtime contract:

```text
CoverageGuard is backup-only.
It checks the selected ChordRegion-local piano PatternPlan after normal candidate lookup/scoring.
If the region already has piano harmonic presence, it only stamps audit metadata.
If a ChordRegion would otherwise be uncovered, it inserts one pitchless region-start fallback anchor.
It never routes through bar-first/two-chord-bar logic.
```

Current standard-tune checkpoints:

```text
All The Things You Are:
expected_region_count: 120
covered_region_count: 120
uncovered_region_count: 0
short_uncovered_region_count: 0
coverage_inserted_events: 0
top_note_max: 72
voice_leading_warning_events: 0

Autumn Leaves:
expected_region_count: 162
covered_region_count: 162
uncovered_region_count: 0
short_uncovered_region_count: 0
coverage_inserted_events: 0
top_note_max: 72
voice_leading_warning_events: 0
```

Next recommended task: `v2_6_63_engine_medium_swing_piano_expression_hint_handoff_checkpoint`.

## v2_6_64 — Engine Medium Swing Piano V1 Idiom Delta Audit Checkpoint

Status: completed.

Scope: behavior-preserving audit/checkpoint. This step studies the uploaded V1 Medium Swing piano report and maps V1's useful idioms into V2's ChordRegion-first, pattern/voicing/expression-decoupled architecture. It does not change runtime selection logic, voicing, expression realization, gesture behavior, MIDI writing, Agent/API/HarmonyOS code, or any shared integration-track files.

Key result:

```text
V1 base stable/offbeat vocabulary      -> covered by 4-beat ChordRegion pitchless cells
V1 two_chord_bar split vocabulary      -> covered as 2-beat / 1-beat ChordRegion vocabulary
V1 251 / two_five / ii_setup priority  -> partial; current V2 only has harmonic-function multipliers
V1 fill / variation vocabulary         -> partial; active/fill/busy memory should come before enabling more
V1 ending vocabulary                   -> partial; final_hold hint exists but ending subset is pending
V1 4& policy                           -> covered but needs V1-ratio no-4& / delayed-tail reinforcement
V1 history guard                       -> partial; busy/fill/multi-region memory pending
V1 touch numeric ranges                -> reference only; ExpressionPolicy calibration pending
V1 shell2/shell4/rootless4 expansion   -> rejected from pattern layer; remains voicing policy concern
```

Current standard-tune checkpoints:

```text
All The Things You Are:
piano_events: 205
region_length_counts: {four_beat_region: 175, two_beat_region: 30}
tail_push_events: 0
active_or_tail_push_events: 9
no_4and_delayed_tail_events: 67
forbidden_expression_events: 0
bar_first_two_chord_bar_events: 0
top_note_max: 72
voice_leading_warning_events: 0

Autumn Leaves:
piano_events: 234
region_length_counts: {two_beat_region: 179, four_beat_region: 55}
tail_push_events: 0
active_or_tail_push_events: 0
no_4and_delayed_tail_events: 47
forbidden_expression_events: 0
bar_first_two_chord_bar_events: 0
top_note_max: 72
voice_leading_warning_events: 0
```

Next recommended task: `v2_6_65_engine_medium_swing_progression_specific_candidate_subset_policy`.
