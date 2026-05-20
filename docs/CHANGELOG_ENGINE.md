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

## v2_6_31 Engine Ballad SPREAD — lower/upper gap and weight balance audit

- Added lower/upper group gap audit fields to `generation/piano_audit.py` without changing runtime density selection.
- Preserved the `v2_6_30` Misty guardrails: 5-note / 6-note remains `120 / 76`, `1+4` remains low-frequency at `10`, 4-note and 7-note remain `0`, and `top_note_max` remains `72`.
- Exposed sparse outliers for the next micro-calibration: 3 tight `2+4` gap events below 2 semitones, and 2 wide `2+3` gap events above 7 semitones.
- Added `docs/ENGINE_VOICING_BALLAD_SPREAD_LOWER_UPPER_GAP_WEIGHT_BALANCE_V2_6_31.md` and `tests/test_v2_6_31_engine_ballad_spread_lower_upper_gap_weight_balance.py`.

Next recommended voicing-only task: `v2_6_32_engine_ballad_spread_gap_aware_candidate_scope_micro_calibration`.

## v2_6_28 Engine Ballad SPREAD — top voice/register micro calibration

## v2_6_30 Engine Ballad SPREAD — 1+4 / lower foundation calibration

- Restored Ballad SPREAD `1+4` as a low-frequency 5-note upper4 color lane instead of a high-frequency default body.
- Preserved the current Jazz Ballad voicing guardrails: 5-note / 6-note remains near 6:4, 4-note SPREAD remains 0, 7-note remains 0 in the default Misty seed, and unnotated maj7#11 remains 0.
- Added lower foundation audit fields to `generation/piano_audit.py` for lower note min/max/average, lower span, grouping/density buckets, recipe counts, low-register events, and span violations.
- Tightened 3-note lower foundation placement so lower group spans stay within one octave.
- Updated the v2_6_27-v2_6_29 focused regression expectations to reflect the new v2_6_30 low-frequency `1+4` baseline.

Next recommended voicing-only task: `v2_6_31_engine_ballad_spread_lower_upper_gap_and_weight_balance`.


- Listening calibration pass: added a narrow grouped-SPREAD top-register micro bias for Jazz Ballad.
- The bias only shapes already-legal SPREAD candidates during selector/groupwise realization collapse; it does not construct sources, change color permission, alter density lanes, project notes, or touch MIDI/expression.
- Opening Misty Ebmaj7 now avoids selecting the highest legal top at 77; the three-chorus audit caps top voice at 74.
- Preserved current guardrails: 4-note SPREAD remains 0, `1+4` ordinary runtime remains 0, 5-note:6-note remains near 6:4, and unnotated maj7#11 remains 0.
- Added `docs/ENGINE_VOICING_BALLAD_SPREAD_TOP_VOICE_REGISTER_MICRO_CALIBRATION_V2_6_28.md` and `tests/test_v2_6_28_engine_ballad_spread_top_voice_register_micro_calibration.py`.

## v2_6_26_engine_voicing_realization_surface_final_cleanup

- Cleanup pass: finalized the thin `harmonic_realizer.py` realization surface after the policy/context, note/audit, and request/cache splits.
- Added `HarmonicRealizerSurfaceFinalCleanupProfile` and explicit owned/forbidden responsibility constants in `harmonic_realizer.py`.
- Piano audit rows now carry `harmonic_realizer_surface_final_cleanup_version = v2_6_26` for boundary traceability.
- Corrected `realizer_note_audit.py` and `voicing_policy_context_adapter.py` debug ownership so request/context flow points through `realizer_voicing_request_orchestration.py`, not the top-level realizer.
- Preserved Jazz Ballad guardrails: 4-note SPREAD remains 0, 5-note / 6-note remains near 6:4, and maj7#11 remains off by default.
- Added `docs/ENGINE_VOICING_REALIZATION_SURFACE_FINAL_CLEANUP_V2_6_26.md` and `tests/test_v2_6_26_engine_voicing_realization_surface_final_cleanup.py`.

## v2_6_25_engine_voicing_request_orchestration_cache_boundary_audit

- Cleanup pass: moved VoicingRequest construction, one-voicing-per-region cache reuse, and explicit fresh revoicing escape hatch out of `harmonic_realizer.py` into `src/jammate_engine/realization/realizer_voicing_request_orchestration.py`.
- `harmonic_realizer.py` now asks `RealizerVoicingRequestOrchestrator` for a `VoicingPlan` and remains focused on PatternEvent iteration, GestureRealizer, NoteEvent list ownership, and audit delegation.
- Added `RealizerVoicingRequestOrchestrationProfile` and explicit owned/forbidden responsibility constants.
- Preserved Jazz Ballad guardrails: 4-note SPREAD remains 0, 5-note / 6-note remains near 6:4, and maj7#11 remains off by default.
- Added `docs/ENGINE_VOICING_REQUEST_ORCHESTRATION_CACHE_BOUNDARY_AUDIT_V2_6_25.md` and `tests/test_v2_6_25_engine_voicing_request_orchestration_cache_boundary_audit.py`.

## v2_6_24_engine_voicing_realizer_note_audit_cleanup

- Cleanup pass: moved piano NoteEvent/audit/debug helpers out of `harmonic_realizer.py` into `src/jammate_engine/realization/realizer_note_audit.py`.
- `harmonic_realizer.py` now remains focused on voicing request orchestration, one-voicing-per-region cache reuse, `VoicingResolver`, `GestureRealizer`, and final NoteEvent list ownership.
- `realizer_note_audit.py` owns `piano_audit_event`, `sync_piano_audit_realized_notes`, note/gesture debug serialization, and partial inner-movement reattack release using already-selected voicing metadata.
- Preserved Jazz Ballad guardrails: 4-note SPREAD remains 0, 5-note / 6-note remains near 6:4, and maj7#11 remains off by default.
- Added `docs/ENGINE_VOICING_REALIZER_NOTE_AUDIT_CLEANUP_V2_6_24.md` and `tests/test_v2_6_24_engine_voicing_realizer_note_audit_cleanup.py`.

## v2_6_23_engine_voicing_harmonic_realizer_policy_context_adapter_cleanup

- Cleanup pass: moved event-scoped voicing policy/context adaptation out of `harmonic_realizer.py` into `src/jammate_engine/realization/voicing_policy_context_adapter.py`.
- Added `HarmonicRealizerPolicyContextAdapterProfile` and explicit owned/forbidden responsibility constants.
- `harmonic_realizer.py` now calls `policy_with_event_voicing_context(policy, event)` and no longer directly owns harmonic-context, texture-scope, Ballad SPREAD grouping-mix, or SPREAD ratio-slot helpers.
- Preserved current Jazz Ballad guardrails: 4-note SPREAD default remains 0, 5-note / 6-note remains near 6:4, and maj7#11 remains absent by default.
- Added `docs/ENGINE_VOICING_HARMONIC_REALIZER_POLICY_CONTEXT_ADAPTER_CLEANUP_V2_6_23.md` and `tests/test_v2_6_23_engine_voicing_harmonic_realizer_policy_context_adapter_cleanup.py`.

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

## v2_6_27 — Engine Ballad SPREAD Listening Calibration

- Voicing-only listening calibration pass; no Pattern / Anticipation / Expression / Gesture / MIDI / Agent / API / shared version changes.
- Demoted `spread_1plus4_contract` from ordinary Jazz Ballad SPREAD runtime to an explicit upper4-color/listening-isolation lane.
- Kept `spread_1plus4_contract` as a valid SPREAD contract; only removed it from the default compatible runtime pool when its scene weight is zero.
- Added zero-weight compatible filtering in the Ballad grouping-mix texture state so disabled contracts cannot re-enter through voice-leading neighbor pools.
- Tuned the deterministic extra 6-note support slot and selected-contract bias so Misty remains near 5-note:6-note = 6:4 after 1+4 is removed from ordinary runtime.
- Preserved zero default 4-note SPREAD and zero default unnotated maj7#11.
- Added `docs/ENGINE_VOICING_BALLAD_SPREAD_LISTENING_CALIBRATION_V2_6_27.md` and `tests/test_v2_6_27_engine_ballad_spread_listening_calibration.py`.

## v2_6_29 — Engine Voicing Drop Projection Audit Counts

- Voicing-only audit/diagnostics pass; no Pattern / Anticipation / Expression / Gesture / MIDI / Agent / API / shared version changes.
- Added `PIANO_DROP_PROJECTION_AUDIT_VERSION = v2_6_29` to `src/jammate_engine/generation/piano_audit.py`.
- Added audit counters for total drop projection methods and scope-specific counts:
  - `main_voicing`
  - `spread_upper_group`
- Added SPREAD upper-group drop counters by density, grouping, and recipe so 5-note / 6-note / 7-note grouped SPREAD can expose internal DROP2 / DROP3 usage.
- Preserved v2_6_28 Misty Ballad output: 5-note:6-note remains near 6:4, 4-note SPREAD remains zero, 1+4 remains zero by default, top note remains capped at 74, and default maj7#11 remains zero.
- Added `docs/ENGINE_VOICING_DROP_PROJECTION_AUDIT_COUNTS_V2_6_29.md` and `tests/test_v2_6_29_engine_voicing_drop_projection_audit_counts.py`.

## v2_6_32 Completed — Engine Ballad SPREAD Gap-Aware Candidate-Scope Micro Calibration

Completed voicing-only selector micro-calibration:

- added `docs/ENGINE_VOICING_BALLAD_SPREAD_GAP_AWARE_CANDIDATE_SCOPE_MICRO_CALIBRATION_V2_6_32.md`;
- added `tests/test_v2_6_32_engine_ballad_spread_gap_aware_candidate_scope_micro_calibration.py`;
- added same-recipe-only gap-aware candidate replacement in the SPREAD groupwise selector;
- fixed the three `2+4` tight-gap outliers from the v2_6_31 audit without changing Pattern / Anticipation / Expression / Gesture / MIDI / Agent / API / HarmonyOS behavior;
- preserved low-frequency `1+4`, zero 4-note/7-note SPREAD defaults, zero unnotated maj7#11, and top register guardrails;
- kept the two `2+3` wide-gap events visible but deferred because broad fixes changed downstream density balance in experiments.

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
top_note_max: 72
```

Next recommended voicing-only task: `v2_6_33_engine_ballad_spread_wide_gap_deferred_outlier_strategy`.

## v2_6_34 — Engine Ballad SPREAD 2+3 Wide Gap Source Inventory Plan

- Voicing-only source-inventory/audit pass on top of the merged `v2_8_24` integration baseline; no Pattern / Anticipation / Expression / Gesture / MIDI / Agent / API / HarmonyOS/shared integration changes.
- Kept runtime replacement disabled for the two remaining `2+3 Fm7` wide-gap rows because direct replacement fixes the local gap but cascades the accepted Ballad SPREAD density lane.
- Added `spread_wide_gap_source_inventory_plan_*` metadata to the deferred rows so same-recipe inventory alternatives are visible without changing selected notes.
- Added piano audit summary fields for source-inventory plan counts, replacement gap ranges, runtime-replacement enabled count, and recommended next boundary.
- Preserved Misty three-chorus guardrails: `5-note:124`, `6-note:72`, `1+4:10`, `4-note:0`, `7-note:0`, `top_note_max:72`, and two wide-gap rows still auditable.
- Added `docs/ENGINE_VOICING_BALLAD_SPREAD_2PLUS3_WIDE_GAP_SOURCE_INVENTORY_PLAN_V2_6_34.md` and `tests/test_v2_6_34_engine_ballad_spread_2plus3_wide_gap_source_inventory_plan.py`.

## v2_6_35 — Engine Ballad SPREAD Phrase-Scope Wide Gap Candidate Availability

- Voicing-only phrase-scope availability pass on top of the merged `v2_8_24` integration baseline; no Pattern / Anticipation / Expression / Gesture / MIDI / Agent / API / HarmonyOS/shared integration changes.
- Fixed the two remaining `2+3 Fm7` lower/upper wide-gap rows by realizing the top-stable same-recipe candidate while advancing voicing continuity state with the original phrase anchor.
- Preserved accepted Ballad SPREAD density and register guardrails: `5-note:124`, `6-note:72`, `1+4:10`, `4-note:0`, `7-note:0`, `top_note_max:72`.
- Reduced `lower_upper_group_gap_too_wide_events` from `2` to `0` without broad scorer changes or density-lane cascade.
- Added `spread_phrase_scope_wide_gap_*` metadata and piano audit summary fields.
- Added `docs/ENGINE_VOICING_BALLAD_SPREAD_PHRASE_SCOPE_WIDE_GAP_CANDIDATE_AVAILABILITY_V2_6_35.md` and `tests/test_v2_6_35_engine_ballad_spread_phrase_scope_wide_gap_candidate_availability.py`.

## v2_6_36 — Engine Ballad SPREAD Phrase-State Boundary Regression Review

- Voicing-only audit/regression pass on top of the merged `v2_8_24` integration baseline; no Pattern / Anticipation / Expression / Gesture / MIDI / Agent / API / HarmonyOS/shared integration changes.
- Added phrase-state boundary review audit fields to verify that v2_6_35 state-protected Fm7 rows advance the following Bb7 event from the protected phrase anchor, not from the substituted realized notes.
- Confirmed the two protected rows have immediate next-event state anchor matches, realized notes are not used as state, and boundary warnings remain zero.
- Preserved accepted Misty three-chorus guardrails: `5-note:124`, `6-note:72`, `1+4:10`, `4-note:0`, `7-note:0`, `top_note_max:72`, and zero lower/upper gap outliers.
- Added `docs/ENGINE_VOICING_BALLAD_SPREAD_PHRASE_STATE_BOUNDARY_REGRESSION_REVIEW_V2_6_36.md` and `tests/test_v2_6_36_engine_ballad_spread_phrase_state_boundary_regression_review.py`.

## v2_6_37 — Engine Ballad SPREAD Phrase-State Boundary Helper Cleanup

- Behavior-preserving voicing-only helper cleanup on top of the merged `v2_8_24` integration baseline; no Pattern / Anticipation / Expression / Gesture / MIDI / Agent / API / HarmonyOS/shared integration changes.
- Added `VoicingStateAdvanceAnchor` in `src/jammate_engine/core/voicing/runtime/state.py` as the owner for separating current realized notes from the state anchor used by later voice-leading.
- Updated the Ballad SPREAD phrase-scope wide-gap path so the selector declares the state anchor through the helper instead of scattering raw resolver metadata keys.
- Updated the voicing resolver so state advancement consumes the helper through one runtime surface while retaining legacy audit aliases for v2_6_35/v2_6_36 compatibility.
- Added helper cleanup audit fields showing two protected events, two direct state anchors, three rows observing the protected previous-state anchor, and legacy alias compatibility.
- Preserved accepted Misty three-chorus guardrails: `5-note:124`, `6-note:72`, `1+4:10`, `4-note:0`, `7-note:0`, `top_note_max:72`, and zero lower/upper gap outliers.
- Added `docs/ENGINE_VOICING_BALLAD_SPREAD_PHRASE_STATE_BOUNDARY_HELPER_CLEANUP_V2_6_37.md` and `tests/test_v2_6_37_engine_ballad_spread_phrase_state_boundary_helper_cleanup.py`.

## v2_6_38 — Engine Ballad 1& Whisper Continuity Patch

- Focused Jazz Ballad continuity bugfix requested before continuing voicing work; this is not a voicing selector change and does not touch Agent / API / HarmonyOS/shared integration surfaces.
- Changed near-downbeat Ballad 1& whisper / soft-mark cells from full `simultaneous_onset` chord reattacks to pitchless `inner_movement` requests on `projection_group`.
- Affected patterns: `ballad_piano_downbeat_1and_whisper`, `ballad_phrase_two_chord_soft_marks`, and `ballad_piano_two_beat_light_retouch`.
- Kept beat-1 foundation sustained while trimming and reattacking only the upper/projection-group notes; this fixes the sudden break reported around Misty performance bars 41, 63, and 95.
- Updated partial-reattack release timing to trim against the performed swing-upbeat start rather than the raw logical `.5` slot, avoiding a tiny gap before the rendered 2/3 upbeat.
- Preserved accepted Misty three-chorus voicing guardrails: `5-note:124`, `6-note:72`, `1+4:10`, `4-note:0`, `7-note:0`, `top_note_max:72`, and zero lower/upper gap outliers.
- Added `docs/ENGINE_BALLAD_1AND_WHISPER_CONTINUITY_PATCH_V2_6_38.md` and `tests/test_v2_6_38_engine_ballad_1and_whisper_continuity_patch.py`.

## v2_6_39 — Engine Ballad SPREAD Post-Continuity Listening Checkpoint

- Observational voicing-track checkpoint on top of `v2_6_38`; no runtime music behavior change and no Agent / API / HarmonyOS/shared integration changes.
- Added post-continuity audit fields to confirm Misty bars 41, 63, and 95 keep the accepted 1& projection re-touch behavior: projection-only retouch, foundation sustain through retouch, and projection notes trimmed at the performed swing-upbeat start.
- Confirmed the accepted Ballad SPREAD guardrails remain stable after the continuity bugfix: `5-note:124`, `6-note:72`, `1+4:10`, `4-note:0`, `7-note:0`, zero lower/upper gap outliers, and `top_note_max:72`.
- Confirmed the v2_6_35/v2_6_37 phrase-state anchor boundary remains valid: two protected events, two next events found, zero boundary warnings.
- Added `docs/ENGINE_VOICING_BALLAD_SPREAD_POST_CONTINUITY_LISTENING_CHECKPOINT_V2_6_39.md` and `tests/test_v2_6_39_engine_ballad_spread_post_continuity_listening_checkpoint.py`.

## v2_6_40 — Engine Ballad SPREAD Phrase-State Anchor Policy Boundary

- Behavior-preserving voicing policy-boundary pass on top of `v2_6_39`; no selected voicing, Pattern, Anticipation, Expression, Gesture/realizer, MIDI, Agent, API, or HarmonyOS behavior change.
- Kept `VoicingStateAdvanceAnchor` as a core helper but made resolver consumption explicitly policy-gated in production runtime.
- Added Jazz Ballad policy gate keys: `voicing_state_advance_anchor_policy_gate_enabled`, `voicing_state_advance_anchor_policy_gate_version`, and `voicing_state_advance_anchor_allowed_scopes`.
- Limited the currently allowed scope to `ballad_spread_phrase_scope_wide_gap_candidate_availability`; other styles/scopes do not consume state anchors unless they opt in through policy.
- Added audit fields for phrase-state anchor policy boundary events, required-gate events, scopes, and previous-state gate consumption.
- Preserved accepted Misty three-chorus guardrails: `5-note:124`, `6-note:72`, `1+4:10`, `4-note:0`, `7-note:0`, `top_note_max:72`, and zero lower/upper gap outliers.
- Added `docs/ENGINE_VOICING_BALLAD_SPREAD_PHRASE_STATE_ANCHOR_POLICY_BOUNDARY_V2_6_40.md` and `tests/test_v2_6_40_engine_ballad_spread_phrase_state_anchor_policy_boundary.py`.

## v2_6_41 — Engine Ballad SPREAD Same-Chord Reattack Continuity Calibration

- Behavior-preserving voicing-only audit/calibration pass on top of `v2_6_40`; no selected voicing, Pattern, Anticipation, Expression, Gesture/realizer note behavior, MIDI, Agent, API, or HarmonyOS behavior change.
- Formalized the accepted same-chord region behavior: repeated touches in one chord region reuse the cached voicing unless an event explicitly requests fresh revoicing.
- Added `same_chord_reattack_continuity_*` metadata on reused region voicings and audit rows.
- Added piano audit summary fields for same-chord regions reviewed, reattack events, cached voicing reuse, exact voicing reuse, foundation stability, fresh revoicing events, changed-voicing warnings, and checkpoint pass/fail.
- Confirmed Misty / Jazz Ballad / 3 choruses has 46 same-chord reattack events, all 46 reuse the cached voicing, all 46 keep exact voicing/foundation stable, and warning events remain zero.
- Preserved accepted Misty guardrails: `5-note:124`, `6-note:72`, `1+4:10`, `4-note:0`, `7-note:0`, `top_note_max:72`, zero lower/upper gap outliers, post-continuity checkpoint passed, and phrase-state boundary warnings zero.
- Added `docs/ENGINE_VOICING_BALLAD_SPREAD_SAME_CHORD_REATTACK_CONTINUITY_CALIBRATION_V2_6_41.md` and `tests/test_v2_6_41_engine_ballad_spread_same_chord_reattack_continuity_calibration.py`.


## v2_6_42 — Engine Ballad SPREAD Safe Extension Frequency Calibration

- Behavior-preserving voicing-only safe-extension frequency checkpoint on top of `v2_6_41`; no selected voicing, Pattern, Anticipation, Expression, Gesture/realizer note behavior, MIDI, Agent, API, or HarmonyOS behavior change.
- Formalized the accepted Ballad major-seventh color rule: default warm SPREAD uses `9` / `13`; unnotated `#11` remains disabled unless the chart explicitly writes it or a future policy declares harmonic-color intent.
- Added Jazz Ballad policy metadata for `ballad_spread_safe_extension_frequency_calibration` and explicit major-seventh default color flags.
- Added piano audit summary fields for major-seventh safe-extension event count, color counts, by-chord color counts, unnotated #11 events, explicit #11 events, preferred colors, and checkpoint pass/fail.
- Confirmed Misty / Jazz Ballad / 3 choruses has major-seventh color counts `{"9": 14, "13": 7}` and `major_seventh_unnotated_sharp11_events: 0`.
- Preserved accepted Misty guardrails: `5-note:124`, `6-note:72`, `1+4:10`, `4-note:0`, `7-note:0`, `top_note_max:72`, zero lower/upper gap outliers, same-chord continuity passed, and post-continuity checkpoint passed.
- Added `docs/ENGINE_VOICING_BALLAD_SPREAD_SAFE_EXTENSION_FREQUENCY_CALIBRATION_V2_6_42.md` and `tests/test_v2_6_42_engine_ballad_spread_safe_extension_frequency_calibration.py`.

## v2_6_43 — Engine Ballad SPREAD Lower Foundation Weight / Register Final Pass

- Behavior-preserving voicing-only lower foundation checkpoint on top of `v2_6_42`; no selected voicing, Pattern, Anticipation, Expression, Gesture/realizer note behavior, MIDI, Agent, API, or HarmonyOS behavior change.
- Formalized the accepted lower/foundation group profile for Ballad SPREAD: `2+3` stays stable/not too thin, `2+4` carries accepted heavier low-register pressure, `1+4` remains a low-frequency color lane, and `3+3` remains very low frequency without low-register mud.
- Added Jazz Ballad policy metadata for `ballad_spread_lower_foundation_weight_register_final_pass`.
- Added piano audit summary fields for lower-foundation final pass profile, recipe profile, density/grouping preservation, low-register threshold, grouping role checks, and checkpoint pass/fail.
- Confirmed Misty / Jazz Ballad / 3 choruses keeps `lower_foundation_span_violation_events:0`, `lower_foundation_span_max:11`, `lower_foundation_low_register_events_by_grouping:{"2+4":26,"2+3":2}`, and final checkpoint passed.
- Preserved accepted Misty guardrails: `5-note:124`, `6-note:72`, `1+4:10`, `4-note:0`, `7-note:0`, `top_note_max:72`, zero lower/upper gap outliers, and zero unnotated maj7 #11 events.
- Added `docs/ENGINE_VOICING_BALLAD_SPREAD_LOWER_FOUNDATION_WEIGHT_REGISTER_FINAL_PASS_V2_6_43.md` and `tests/test_v2_6_43_engine_ballad_spread_lower_foundation_weight_register_final_pass.py`.

## v2_6_48 — Engine Medium Swing OPEN / DROP Phrase-Scope Method Continuity Plan

- Behavior-preserving voicing-only audit pass on top of the merged `v2_10_8` integration baseline plus Engine v2_6_47.
- Added `medium_swing_phrase_scope_method_continuity_*` audit fields to derive section-local four-region phrase windows from realized OPEN drop-family chord-region events.
- Added visibility for phrase-internal method switches, DROP2&4 run length, ii–V / V–I / ii–V–I method consistency, high-motion method switches, warnings, and checkpoint pass/fail.
- Confirmed All The Things You Are / Medium Swing / 3 choruses: `phrase_scope_method_switch_ratio=0.4048`, `drop2_and_4_run_max=1`, `high_motion_switch_events=0`, checkpoint passed.
- Confirmed Autumn Leaves / Medium Swing / 3 choruses: `phrase_scope_method_switch_ratio=0.4274`, `drop2_and_4_run_max=2`, `high_motion_switch_events=0`, checkpoint passed.
- Updated the Medium Swing voicing policy metadata and the existing Medium Swing texture audit script to emit v2_6_48 demo/audit artifacts.
- Added `tests/test_v2_6_48_engine_medium_swing_open_drop_phrase_scope_method_continuity_plan.py` and `docs/ENGINE_VOICING_MEDIUM_SWING_OPEN_DROP_PHRASE_SCOPE_METHOD_CONTINUITY_PLAN_V2_6_48.md`.

Recommended next task: `v2_6_49_engine_medium_swing_open_drop_phrase_scope_method_lock_policy`.

## v2_6_52 — Engine Medium Swing OPEN / DROP Same-Chord Reattack / Comping Reuse

- Behavior-preserving Engine voicing-only checkpoint on top of `v2_6_51`; no Pattern, Anticipation, Expression, Gesture realization, MIDI, Agent, API, HarmonyOS, or shared integration docs changed.
- Formalized Medium Swing repeated-hit behavior: same-chord comping hits inside one chord region reuse the cached region voicing unless an explicit fresh-revoicing escape hatch is present.
- Added Medium Swing policy metadata for `medium_swing_same_chord_reattack_comping_reuse_*`.
- Added Medium Swing audit aliases over the existing same-chord region cache audit fields.
- Confirmed All The Things You Are / Medium Swing / 3 choruses has 54 same-chord reattack/comping reuse events, all 54 exact voicing reuse, zero fresh revoicing, and zero warnings.
- Confirmed Autumn Leaves / Medium Swing / 3 choruses has 61 same-chord reattack/comping reuse events, all 61 exact voicing reuse, zero fresh revoicing, and zero warnings.
- Updated `examples/scripts/generate_medium_swing_texture_method_audit.py` to emit v2_6_52 demo/audit artifacts and same-chord reuse acceptance checks.
- Added `docs/ENGINE_VOICING_MEDIUM_SWING_OPEN_DROP_SAME_CHORD_REATTACK_COMPING_REUSE_V2_6_52.md` and `tests/test_v2_6_52_engine_medium_swing_open_drop_same_chord_reattack_comping_reuse.py`.

Recommended next task: `v2_6_53_engine_medium_swing_open_drop_safe_extension_and_top_register_checkpoint`.

## v2_6_53 — Engine Medium Swing OPEN/DROP Safe Extension + Top Register Checkpoint

- Behavior-preserving Engine voicing-only checkpoint on top of `v2_6_52`; no Pattern, Anticipation, Expression, Gesture realization, MIDI, Agent, API, HarmonyOS, or shared integration docs changed.
- Added Medium Swing policy metadata for `medium_swing_open_drop_safe_extension_top_register_checkpoint_*`.
- Added piano audit fields for Medium Swing OPEN/DROP top register, major-seventh safe-extension counts, unnotated `#11` events, register guard failures, voice-leading warnings, and checkpoint pass/fail.
- Confirmed All The Things You Are / Medium Swing / 3 choruses keeps `top_note_max:72`, `top_note_ge_75_events:0`, `major_seventh_unnotated_sharp11_events:0`, `register_guard_failed_events:0`, and checkpoint passed.
- Confirmed Autumn Leaves / Medium Swing / 3 choruses keeps `top_note_max:72`, `top_note_ge_75_events:0`, `major_seventh_unnotated_sharp11_events:0`, `register_guard_failed_events:0`, and checkpoint passed.
- Updated `examples/scripts/generate_medium_swing_texture_method_audit.py` to emit v2_6_53 demo/audit artifacts and safe-extension/top-register acceptance checks.
- Added `docs/ENGINE_VOICING_MEDIUM_SWING_OPEN_DROP_SAFE_EXTENSION_TOP_REGISTER_CHECKPOINT_V2_6_53.md` and `tests/test_v2_6_53_engine_medium_swing_open_drop_safe_extension_top_register_checkpoint.py`.

Recommended next task: `v2_6_54_engine_medium_swing_open_drop_deliberate_revoice_gesture_boundary_plan`.

## v2_6_54 — Engine Medium Swing OPEN/DROP Deliberate Revoice Gesture Boundary Plan

- Behavior-preserving Engine voicing-only boundary pass on top of `v2_6_53`; no Pattern, Anticipation, Expression, MIDI, Agent, API, HarmonyOS, or shared integration docs changed.
- Formalized that Medium Swing same-chord fresh voicing inside one chord region is allowed only through explicit pitchless event/gesture intent, not selector randomness.
- Added `deliberate_revoice_request_from_event()` and v2_6_54 metadata annotation for explicit `force_fresh_voicing` / `revoice_within_region` cache bypasses.
- Preserved default same-chord comping reuse for current standard demos: All The Things You Are has 54 default reuse events and zero explicit/implicit revoices; Autumn Leaves has 61 default reuse events and zero explicit/implicit revoices.
- Added `medium_swing_deliberate_revoice_gesture_boundary_*` audit summary fields and focused tests for both default runtime and targeted explicit gesture bypass.
- Added `docs/ENGINE_VOICING_MEDIUM_SWING_OPEN_DROP_DELIBERATE_REVOICE_GESTURE_BOUNDARY_PLAN_V2_6_54.md` and `tests/test_v2_6_54_engine_medium_swing_open_drop_deliberate_revoice_gesture_boundary_plan.py`.

Recommended next task: `v2_6_55_engine_medium_swing_open_drop_deliberate_revoice_micro_motion_policy_probe`.

## v2_6_55 — Engine Medium Swing OPEN/DROP Deliberate Revoice Micro-Motion Policy Probe

- Added a narrow Engine voicing-only micro-motion policy for explicit same-chord fresh revoicing on top of `v2_6_54`; default same-chord comping still reuses cached region voicing exactly.
- Added `policy_with_deliberate_revoice_micro_motion_context()` to pass the cached region voicing into `VoicingPolicy` metadata only when `force_fresh_voicing` or `revoice_within_region` is explicitly requested.
- Added a candidate-pool filter for explicit micro-motion revoice requests: stable foundation, `max_low_motion=0`, `max_top_motion=2`, `max_avg_motion=2.5`, same density, and same OPEN/DROP method when available.
- Added `medium_swing_deliberate_revoice_micro_motion_policy_*` audit summary fields and default-demo acceptance checks.
- Confirmed All The Things You Are / Medium Swing / 3 choruses keeps micro-motion runtime inactive by default: zero runtime-enabled events, zero filter-applied events, zero warnings, checkpoint passed.
- Confirmed Autumn Leaves / Medium Swing / 3 choruses keeps micro-motion runtime inactive by default: zero runtime-enabled events, zero filter-applied events, zero warnings, checkpoint passed.
- Added `docs/ENGINE_VOICING_MEDIUM_SWING_OPEN_DROP_DELIBERATE_REVOICE_MICRO_MOTION_POLICY_PROBE_V2_6_55.md` and `tests/test_v2_6_55_engine_medium_swing_open_drop_deliberate_revoice_micro_motion_policy_probe.py`.

Recommended next task: `v2_6_56_engine_medium_swing_deliberate_revoice_gesture_inventory_plan`.

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

- Continued the Medium Swing piano pattern track on the existing ChordRegion-first `styles/medium_swing/comping_patterns.py` line; no parallel pattern source, shadow selector, voicing rule, expression realization, gesture, Agent, API, or HarmonyOS change was introduced.
- Added `piano_comping_history_continuity_scorer=True` and `piano_comping_history_continuity_scorer_version=v2_6_59` to the Medium Swing arrangement policy.
- Extended the existing `StyleProfile.plan_region()` selection path with a lightweight piano-comping history reweighting stage after region-length candidate lookup and existing repeat/category guards.
- The scorer penalizes exact repeats, non-stable family repeats, consecutive offbeat/active/tail-push choices, and rewards stable resets after offbeat/active/tail-push contexts.
- Selected piano pattern events now carry v2_6_59 audit metadata such as `history_continuity_multiplier`, `history_continuity_reasons`, and `history_continuity_class` while remaining pitchless and free of concrete expression values.
- Generated All The Things You Are and Autumn Leaves three-chorus Medium Swing demos plus history-continuity audit summary/report.
- Added `tests/test_v2_6_59_engine_medium_swing_piano_comping_history_continuity_scorer.py` and `docs/ENGINE_MEDIUM_SWING_PIANO_COMPING_HISTORY_CONTINUITY_SCORER_V2_6_59.md`.

Recommended next task: `v2_6_60_engine_medium_swing_harmonic_function_aware_piano_comping_policy`.

## v2_6_60 — Engine Medium Swing Harmonic-Function-Aware Piano Comping Policy

- Continued directly on the existing Medium Swing piano region-length pattern line; no parallel selector, shadow pattern source, bar-first/two-chord-bar route, voicing rule, expression realization, gesture, Agent, API, or HarmonyOS change was introduced.
- Added `piano_comping_harmonic_function_policy=True` and `piano_comping_harmonic_function_policy_version=v2_6_60` to the Medium Swing arrangement policy.
- Extended the existing `StyleProfile.plan_region()` selection path with a harmonic-function reweighting stage after ChordRegion-length candidate lookup/repeat guards and before the v2_6_59 history scorer.
- The policy reuses the existing harmony `classify_functional_motion()` metadata to label contexts such as `predominant_to_dominant`, `dominant_resolution`, `tonic_resolution`, `section_start`, `section_end`, `ending`, `tonic_prolongation`, and `turnaround_like`.
- Candidate multipliers remain conservative: stable anchors are supported at section starts and tonic resolutions, answer/tail cells are modestly supported over dominant resolutions, and native tail-push remains controlled.
- Selected piano events now carry v2_6_60 audit metadata such as `harmonic_function_context_label`, `harmonic_function_multiplier`, and harmonic motion tags while remaining pitchless and free of concrete expression values.
- Generated All The Things You Are and Autumn Leaves three-chorus Medium Swing demos plus harmonic-function audit summary/report.
- Added `tests/test_v2_6_60_engine_medium_swing_harmonic_function_aware_piano_comping_policy.py` and `docs/ENGINE_MEDIUM_SWING_HARMONIC_FUNCTION_AWARE_PIANO_COMPING_POLICY_V2_6_60.md`.

Recommended next task: `v2_6_61_engine_medium_swing_region_first_anticipation_compatibility_checkpoint`.

## v2_6_61 — Engine Medium Swing Region-First Anticipation Compatibility Checkpoint

- Added a behavior-preserving Medium Swing anticipation checkpoint after the ChordRegion-first piano pattern work; no new patterns, voicings, gestures, expression realization parameters, MIDI writer behavior, Agent, API, or HarmonyOS changes were introduced.
- Documented and audited the region-first anticipation contract: previous tail slot is computed from `previous_region.duration_beats - 0.5`, so 4-beat regions use local `3.5`, 2-beat regions use local `1.5`, and short regions are not forced through a bar-first 4& assumption.
- Added v2_6_61 anticipation metadata to anticipated events, including previous/current region duration, last-beat/upbeat local slots, checked tail slots, tail availability reason, and `bar_first_4and_assumption=False`.
- Updated Medium Swing anticipation and arrangement policy metadata with `piano_region_first_anticipation_compatibility_checkpoint_version=v2_6_61`.
- Generated All The Things You Are and Autumn Leaves three-chorus Medium Swing demos plus region-first anticipation audit summary/report.
- Added `tests/test_v2_6_61_engine_medium_swing_region_first_anticipation_compatibility_checkpoint.py`, `examples/scripts/generate_medium_swing_region_first_anticipation_audit.py`, and `docs/ENGINE_MEDIUM_SWING_REGION_FIRST_ANTICIPATION_COMPATIBILITY_CHECKPOINT_V2_6_61.md`.

Recommended next task: `v2_6_62_engine_medium_swing_coverage_guard_region_first_cleanup`.

## v2_6_62 — Engine Medium Swing CoverageGuard Region-First Cleanup

- Added a backup-only Medium Swing piano CoverageGuard in the existing `StyleProfile.plan_region()` path; no parallel selector, shadow pattern source, voicing rule, expression realization, gesture, Agent, API, or HarmonyOS change was introduced.
- The guard runs after ChordRegion-length candidate lookup, harmonic-function multiplier, history scorer, and weighted sampling; it stamps coverage metadata when a region is already covered and inserts a single pitchless region-start fallback anchor only if a ChordRegion would otherwise have no piano harmonic presence.
- Added Medium Swing arrangement policy metadata: `piano_region_first_coverage_guard=True`, `piano_region_first_coverage_guard_version=v2_6_62`, and a region-first/no-two-chord-bar backup-only contract.
- Selected piano events now carry v2_6_62 coverage metadata such as `coverage_region_duration_beats`, `coverage_region_length_family`, and `coverage_guard_is_backup_only` while remaining pitchless and free of final velocity/duration/pedal or voicing fields.
- Generated All The Things You Are and Autumn Leaves three-chorus demos plus v2_6_62 coverage-guard audit summary/report.
- Added `tests/test_v2_6_62_engine_medium_swing_coverage_guard_region_first_cleanup.py`, `examples/scripts/generate_medium_swing_region_first_coverage_guard_audit.py`, and `docs/ENGINE_MEDIUM_SWING_COVERAGE_GUARD_REGION_FIRST_CLEANUP_V2_6_62.md`.

Recommended next task: `v2_6_63_engine_medium_swing_piano_expression_hint_handoff_checkpoint`.

## v2_6_64 — Engine Medium Swing Piano V1 Idiom Delta Audit Checkpoint

- Added a behavior-preserving V1→V2 Medium Swing piano idiom delta audit; no runtime selection logic, voicing, expression realization, gesture, MIDI writer, Agent, API, or HarmonyOS behavior was changed.
- Compared the V1 Medium Swing piano report against the current V2 ChordRegion-first pattern line and recorded a translation matrix for base/offbeat vocabulary, short-region translation of V1 `two_chord_bar`, progression-specific vocabulary, fill/variation, ending, rare 4& lift policy, history guard, expression touch calibration, and texture expansion.
- Confirmed that V2 candidates remain pitchless, region-local, free of concrete `velocity` / `duration` / `pedal` values, and contain no bar-first `two_chord_bar` markers.
- Confirmed V2 currently covers generic stable/offbeat vocabulary and V1 split-bar ideas as 1/2-beat ChordRegion patterns, but V1-style `major_251` / `minor_251` / `two_five` / `ii_setup` candidate priority is still only partial via harmonic-function multipliers.
- Explicitly rejected V1 pattern-layer texture expansion (`shell2` / `shell4` / `rootless4`) for V2; texture/voicing remains in the voicing policy layer.
- Generated All The Things You Are and Autumn Leaves three-chorus Medium Swing demos plus v2_6_64 V1 idiom delta audit summary/report.
- Added `tests/test_v2_6_64_engine_medium_swing_piano_v1_idiom_delta_audit_checkpoint.py`, `examples/scripts/generate_medium_swing_piano_v1_idiom_delta_audit.py`, and `docs/ENGINE_MEDIUM_SWING_PIANO_V1_IDIOM_DELTA_AUDIT_CHECKPOINT_V2_6_64.md`.

Recommended next task: `v2_6_65_engine_medium_swing_progression_specific_candidate_subset_policy`.

## v2_6_65 — Engine Medium Swing Progression-Specific Candidate Subset Policy

- Added a V1-derived, V2-native Medium Swing piano progression-specific preferred subset policy in the existing `StyleProfile.plan_region()` path.
- Translated V1 `major_251` / `minor_251` / `two_five` / `ii_setup` candidate priority into ChordRegion-first labels such as `dominant_resolution`, `predominant_to_dominant`, and `tonic_resolution` without restoring bar-first templates.
- The policy runs inside the existing region-length candidate pool before the v2_6_60 harmonic-function multiplier and v2_6_59 history scorer; it does not create a parallel selector, choose voicings, or write final expression values.
- Added runtime audit metadata including `progression_specific_subset_key`, `progression_specific_subset_status`, and `progression_specific_subset_multiplier`.
- Generated All The Things You Are and Autumn Leaves three-chorus Medium Swing demos plus v2_6_65 progression subset audit summary/report.
- Added `tests/test_v2_6_65_engine_medium_swing_progression_specific_candidate_subset_policy.py`, `examples/scripts/generate_medium_swing_piano_progression_subset_audit.py`, and `docs/ENGINE_MEDIUM_SWING_PROGRESSION_SPECIFIC_CANDIDATE_SUBSET_POLICY_V2_6_65.md`.

Recommended next task: `v2_6_66_engine_medium_swing_no_4and_delayed_tail_idiom_reinforcement`.

## v2_6_66 — Engine Medium Swing No-4& Delayed-Tail Idiom + Hold Boundary Guard

- Fixed `hold_until_next_touch` semantics in the core ExpressionResolver: hold-style events now sustain to the next same-track touch only when that touch is still inside the current ChordRegion; otherwise they release at the current ChordRegion end.
- Added v2_6_66 audit metadata for hold boundary outcomes, including `next_same_track_touch_beyond_region_clamped_to_region_end`.
- Added a V1-derived no-4& / delayed-tail reinforcement policy in the existing Medium Swing piano selection pipeline; it modestly boosts delayed/tail/backbeat cells and downweights native 4& tail-push candidates while keeping 4& available as rare lift.
- Kept routing ChordRegion-first and region-local; no bar-level template path, voicing selection, final pattern-level velocity/duration/pedal, gesture, Agent, API, or HarmonyOS changes were introduced.
- Generated All The Things You Are and Autumn Leaves three-chorus Medium Swing demos plus v2_6_66 no-4& / hold-boundary audit summary/report.
- Added `tests/test_v2_6_66_engine_medium_swing_no_4and_delayed_tail_idiom_reinforcement.py`, `examples/scripts/generate_medium_swing_piano_no_4and_delayed_tail_audit.py`, and `docs/ENGINE_MEDIUM_SWING_NO_4AND_DELAYED_TAIL_IDIOM_REINFORCEMENT_V2_6_66.md`.

Recommended next task: `v2_6_67_engine_medium_swing_active_fill_busy_multi_region_history_scorer`.
