# Voicing Texture State Architecture V2 — Compact

Current version: `v2_2_63`.

## Purpose

`VoicingTextureIntent` is LLM/user/arrangement-facing. `VoicingTextureState` is the engine-resolved runtime contract. Both live in `core/voicing/texture_plan.py`.

Do not place `VoicingTextureState` in `core/voicing/disposition/`: that package owns low-level Disposition Projection, not phrase/section texture language.

## Layer relationship

```text
LLM / user / arrangement intent
→ VoicingTextureIntent
→ style + ensemble + progression context
→ VoicingTextureState
→ candidate generator / selector metadata
→ Disposition Projection
→ method lock for ii-V / V-I / ii-V-I continuity
```

## Current contract

`derive_voicing_texture_intent`, `derive_voicing_texture_state`, `voicing_texture_state_engine_resolved_contract_v2_2_21` plus `voicing_texture_state_contrast_dimensions_v2_2_38`, `family`, `method lock`, `Capability Reuse Before New Construction`, `default listening behavior unchanged unless a style explicitly opts into runtime filtering`.

Contract labels: `v2_2_20 update — VoicingTextureState / LLM Intent Architecture Planning`; `v2_2_21 update — VoicingTextureIntent / VoicingTextureState Contract Planning Pass`.

## Recent Medium Swing bridge / chorus contrast planning

Medium Swing still filters runtime candidates to OPEN family. The runtime contract exposes semantic contrast dimensions in `VoicingTextureState` and can lightly shape OPEN-method weights: baseline A sections use `baseline_open_swing`, the bridge can expose `bridge_open_contrast`, and the final chorus can expose `final_chorus_open_lift`. These values live in `energy`, `density`, `width`, and `contrast_role`; v2_2_38 lightly reshapes OPEN-method selector priors for bridge/final-chorus contrast and still does not bypass MethodLock.


## Additional compact compatibility aliases

generation/bass_foundation/; Do not add more core infrastructure; No BassFoundation retune; 3-note; 5-note; 6-note; rootless_ab_content_type_with_5; rootless_ab_content_type_with_13; m7 + 13; m7b5; m11b5; b3 + b7 + b5; shell_plus_expanded_color; supersedes; replaces; directed minor-second; directed m2; runtime_filtering_enabled=True; HarmonicContext-backed Method Lock Scope Adapter; Seed-Then-Follow; Method Lock Rescue; Method Lock Rescue Runtime; OpenProjectionMethod.DROP2; ii-V; V-I; ii-V-I; progression_phrase_voicing_method_lock_planning_only; locked_method; open_projection_method; boundary_test_source; DROP2 Audit Fixture; open_drop2_parent_closed_degrees; docs/ARCHITECTURE_V2.md; docs/PIPELINE_V2.md; docs/SYSTEM_CONTRACTS_V2.md; docs/API_CONTRACT_V2.md; docs/GENERATION_RULES_SUMMARY_V2.md; docs/STYLE_RULE_BASELINE_V2.md; docs/STYLE_TUNING_ENTRY_POINT_V2.md; docs/DEVELOPMENT_TASK_PLAN_V2.md; docs/DEVELOPMENT_HARNESS_V2.md; docs/NEW_FILE_PLACEMENT_GUIDE_V2.md; docs/FUTURE_IDEAS_BACKLOG_V2.md; docs/VOICING_MODULE_FILE_AUDIT_V2.md; docs/PROJECT_DOCUMENTATION_AUDIT_V2.md; docs/CLOSED_3_4_NOTE_BASELINE_AND_PRE_DISPOSITION_PLAN_V2.md; docs/DISPOSITION_PROJECTION_ARCHITECTURE_V2.md; docs/VOICING_TEXTURE_STATE_ARCHITECTURE_V2.md; generate_closed_34note_baseline_smoke_listening.py; generate_3note_closed_listening_verification_demos.py; generate_4note_source_weight_listening_verification_demos.py; generate_4note_triad_closed_listening_verification_demos.py; generate_4note_triad_closed_listening_verification_demos; closed_34note_baseline_smoke_summary; 4-note triad-aware closed listening; closed register downshift; closed legality; avg_closed_4note_source_collapse_distance; closed_3note_closed_legality_then_nearest_motion; closed_3note_per_source_minimum_motion; closed_4note_per_source_minimum_motion; closed_4note_minimum_motion_events; closed_voicing_lowest_note_floor; min_closed_voicing_lowest_note; max_closed_voicing_span; max_density; min_density; preferred_density.



## v2_2_55 update — Ballad SPREAD 1+4 Upper DROP2/DROP3 Only Audit

- `SPREAD_UPPER_4NOTE_DROP2_DROP3_ONLY_VERSION = "v2_2_55"`: SPREAD upper 4-note blocks explicitly reuse only OPEN DROP2 / DROP3 projection resources. OPEN DROP2&4 remains available for OPEN-family listening and style policies, but it is intentionally excluded from SPREAD upper 4-note blocks because SPREAD already owns a lower+upper grouping and gap/span guard.
- The restriction is enforced at the SPREAD adapter boundary: even if a future config accidentally passes DROP2&4 into an upper 4-note reference, SPREAD filters it back to DROP2/DROP3 and emits metadata `spread_upper_4note_drop2_and_4_allowed=false`.
- Listening/audit demo: `v2_2_55_misty_jazz_ballad_spread_1plus4_upper_drop2_drop3_only_audit_demo.mid`; audit summary: `v2_2_55_misty_jazz_ballad_spread_1plus4_upper_drop2_drop3_only_audit_summary.json`.
- Next lower+upper grouping work should proceed one grouping or a small coherent group at a time, each with a standard-tune listening demo for user review before mixing into broader Ballad SPREAD defaults.

## v2_2_54 update — Global Seventh-Chord Expansion Source Integrity Gate

- `GLOBAL_SEVENTH_CHORD_EXPANSION_SOURCE_INTEGRITY_GATE_VERSION = "v2_2_54"`: global voicing source gate for CLOSED/OPEN/SPREAD/future grouped voicings. Seventh-chord expansions preserve 3+7 identity (and half-dim/dim keep b5); triad/add paths may keep `1-3-5-9`, but seventh chords use sources such as `1-3-7-9`, `1-3-7-13`, `3-5-7-9`, `3-13-7-9`. Demo: `v2_2_54_misty_jazz_ballad_global_source_integrity_demo.mid`.

## Final compact compatibility aliases

A-B-A; B-A-B; Dorian; modal; 3-5-7-9; 7-9-3-5; 5-7-9-3; 9-3-5-7; Content Recipe; ContentRecipe; Register Center; register center; b9; b13; 1357; 1-3-5-7; color_permission.py; four_note_sources.py; SEVENTH_BASIC altered-dominant compatibility path has been removed; 4-Note Source Weight Implementation / Listening Prep Pass; 4-Note Source Weight Listening Verification Pass; 3-note functional closed; no partial fallback; 2-note Guide-Tone Shell; Rule Change Documentation Sync Standard; 不能只改代码、不改规则文档; root/1; root / 1; shell+1/root; 1251; 2512; 5125; docs/VOICING_SYSTEM_V2_DESIGN.md; docs/VOICING_MODULE_CORE_LOGIC_V2.md; docs/VOICING_TUNING_WORKFLOW_V2.md; Voicing Source Module Boundary Cleanup; _four_note_color_permission_notes; from .color_permission import; from .four_note_sources import; source_family_weights; mode-aware gate buckets; four_note_source_balance_gate_modes; four_note_source_balance_keys; source_family; source_type; source weight; altered dominant; compatibility path; root_third_fifth_seventh; root_third_fifth_sixth; root_fourth_fifth_seventh; root_third_fifth_ninth; root_third_ninth; root_third_seventh_altered_color; root-third-fifth-sixth; root-third-seventh-altered-color; rooted_color_4note; rooted_color_4note_source_family; rooted_color_4note_functional_content_type_; rootless_ab_content_type_with_5; rootless_ab_content_type_with_13; rootless_ab_inversion_index; rootless_ab_inversion_prior_score; rootless_ab_degree_order; basic_4note_legacy_source_family_alias; basic_4note_altered_dominant_compatibility_source; basic_4note_dim7_source_family; basic_4note_1357; 4_note_basic_1357; hard binding concept; not a new progression recognizer; OpenProjectionMethod.DROP3; OpenProjectionMethod.DROP2_AND_4; same DispositionFamily + ProjectionMethod; method lock rescue; same-family fallback; generic open fallback; closed compact fallback; nearest motion; source-order compact stack; parent-closed; parent_closed; closed_parent_placement_callback.
Compact consistency index (historical shipped contract aliases, not active roadmap): ABA; BAB; 8:2; 52-74; 60-74; 3-b7-X-Y; Harmonic expansion does not replace the chord; functional degree source; 4-Note Source Gating Audit; Mode-Aware Source Weight; Unified Color Permission + Chart Fidelity; Eleventh / #11 / Explicit Extension Source Completion; Color Source Gating Regression; four_mode_aware; v2_1_37; v2_1_40; v2_1_43; B3-F4; Rule Change Documentation Sync Standard; 规则变化就必须同步文档; 1451; 1351; 1251; core/harmony/harmonic_context.py; OpenProjectionMethod.GENERIC_OPEN; planning-only.
Compact contract token index B (historical shipped docs preserved as aliases, not active roadmap): rootless_ab_register_center_score; generated demo artifacts are not packaged; third-fifth-seventh-ninth; source_family_weights_by_gate; AllowedColorSet; root-third-seventh-eleventh; alt palette; G9 / G7#9 / G7b13 / Bm11b5; Top-k nearest realizations; common-tone; 3-note closed; 4-note closed; 3513; 5135; Progression / phrase-level voicing method lock.
Compact contract token index C: Gesture-driven revoicing; 2_note_guide_tone_shell; per-source nearest.
Compact contract token index D: Do not generalize v2_1_37 immediately; All the Things You Are.
Compact harness contract index: classic_fill_min_gap_regions; classic fill; logical grid; same current-root note; timing_intent; BassFoundation Musicality Audit; Region Decision Trace; target-to-target; target_nextR_note; Seventh lower-lane; Target Continuity Audit; Pattern rules; Voicing rules; Expression rules; Timing rules; generate_closed_34note_baseline_smoke_listening.py; CLOSED_3_4_NOTE_BASELINE_AND_PRE_DISPOSITION_PLAN_V2.md; legacy Disposition; resolver migration is not part of v2_2_x; project_source_to_disposition(); DispositionProjectionResult; v2_2_2 — Closed Projection Migration / No Behavior Change; src/jammate_engine/core/voicing/disposition/closed.py; place_compact_closed_seed_layout; strict_closed_register_variants; closed_projection_migrated; v2_2_3 — Legacy Disposition Cleanup Pass; src/jammate_engine/core/voicing/disposition/open.py; src/jammate_engine/core/voicing/disposition/spread.py; src/jammate_engine/core/voicing/disposition/placement_utils.py; disposition/facade.py is now only a placement facade; v2_2_4 — Open Projection Skeleton / DROP2 4-note Only; v2_2_5 update — DROP2 Parent-Closed Projection Correction Pass; place_drop2_projection_from_closed_parent; open_drop2_parent_closed_notes; not from a direct source-order compact stack; v2_2_7 update — OPEN Method Candidate Pool / DROP3-DROP2&4 Skeleton Pass; open_projection_method_pool; DROP3; DROP2_AND_4.
Compact package organization token: BassFoundation 规则包; generation/bass_foundation/.

## v2_2_28 runtime pilot

`VoicingTextureState` has its first small runtime consumer in Medium Swing. When style metadata opts in, `candidate_generator` filters the policy's legacy `allowed_dispositions` to the state `allowed_families` before disposition projection. Medium Swing currently resolves to OPEN-only family continuity, while DROP2 / DROP3 / GENERIC_OPEN / low-weight DROP2&4 remain method-level choices inside OPEN. Bossa and Ballad remain opt-in false.


## v2_2_29 — Texture-State Rescue / Nearest-Motion

When a strict method lock or texture-state path enters explicit rescue, fallback candidates must not be selected only because they are legal. The selector reuses existing voice-leading continuity cost and applies `texture_state_rescue_nearest_motion` to collapse rescue pools to the nearest previous voicing before weighted selection. This is core voicing behavior, not a style pattern rule.

## Recent Medium Swing phrase/section texture scope

Medium Swing now opts into `voicing_texture_scope_runtime_enabled` with `voicing_texture_runtime_scope_type = section`. `PatternEvent.metadata` carries section/phrase/chorus context from `HarmonicRegion`; `HarmonicRealizer` attaches a concrete `texture_scope_id` such as `chorus:0|section:A1` to the event-scoped `VoicingPolicy` before `derive_voicing_texture_state()` runs.

This is not a new planner and not a disposition algorithm. It is the runtime wiring that makes `VoicingTextureState` scoped to phrase/section context while `Disposition Projection` still generates notes and MethodLock still handles local progression method continuity.

## Relationship to SPREAD notes

VoicingTextureState decides whether a phrase/section/chorus is SPREAD. It must not contain the SPREAD notes algorithm. The notes algorithm belongs to `core/voicing/disposition` and consumes the resolved family/method context.

The planned SPREAD implementation is lower/upper grouped and notes-only. Expression remains decoupled; style expression policies may later interpret lower and upper groups differently through metadata.

## v2_2_43 — SPREAD Candidate Selector Contract / Runtime Gate Skeleton

SPREAD Candidate Selector Contract / Runtime Gate Skeleton adds a safety-gated selector surface in the existing `core/voicing/disposition/spread.py` owner. It introduces `SPREAD_SELECTOR_RUNTIME_GATE_VERSION = "v2_2_42"`, `SpreadRuntimeGateDecision`, `SpreadCandidateSelectorRequest`, `SpreadCandidateSelectorResult`, `spread_runtime_gate_from_policy`, `select_spread_candidate_with_runtime_gate`, and `spread_candidate_selector_contract_debug`.

The gate is closed by default. To open it, policy metadata must explicitly request the SPREAD selector gate, for example `spread_selector_enabled=true` / `spread_runtime_gate_enabled=true`, and the resolved texture family must request `spread` through `primary_family`, `allowed_families`, or `VoicingTextureState`. Even when open, the result remains a notes-only `SpreadProjectionCandidate`: `candidate_conversion_allowed=false`, `style_runtime_wiring_enabled=false`, `runtime_enabled=false`, and no expression or pedal behavior is introduced. This is a selector contract / runtime gate skeleton only; it does not retune Ballad, Bossa, or Medium Swing runtime behavior.

## v2_2_43 — SPREAD Runtime Pilot Planning / Ballad Entry Contract

SPREAD Runtime Pilot Planning / Ballad Entry Contract adds a guarded Jazz Ballad pilot entry contract in the existing `core/voicing/disposition/spread.py` owner. It introduces `BALLAD_SPREAD_RUNTIME_ENTRY_CONTRACT_VERSION = "v2_2_43"`, `BalladSpreadEntryScene`, `BalladSpreadRuntimeEntryContract`, `BalladSpreadRuntimeEntryDecision`, `BalladSpreadRuntimePilotResult`, `ballad_spread_runtime_entry_contract`, `resolve_ballad_spread_runtime_entry`, `select_ballad_spread_pilot_candidate`, and `ballad_spread_runtime_entry_debug`.

The contract is planning/debug only: Jazz Ballad must explicitly set `ballad_spread_runtime_pilot.enabled=true` and still pass the existing SPREAD selector gate before notes-only pilot selection can return a `SpreadProjectionCandidate`. It keeps `style_runtime_wiring_enabled=false`, `candidate_conversion_allowed=false`, `runtime_enabled=false`, `notes-only`, and `no_expression_or_pedal=true`; Medium Swing and Bossa remain unaffected. Ballad pilot grouping is limited to `1+4`, `2+3`, `2+4`, and `3+3`, with `3+4` / 7-note thick ending left for a later explicit ending/climax pass.


## v2_2_44 update — Ballad SPREAD Runtime Pilot Wiring Plan + Safe Dry Run

`core/voicing/disposition/spread.py` now exposes `BALLAD_SPREAD_RUNTIME_SAFE_DRY_RUN_VERSION`, `BalladSpreadRuntimePilotWiringPlan`, `BalladSpreadRuntimeDryRunChordTrace`, `BalladSpreadRuntimeSafeDryRunResult`, `ballad_spread_runtime_pilot_wiring_plan`, `run_ballad_spread_runtime_safe_dry_run`, and `ballad_spread_runtime_safe_dry_run_debug`. This pass validates the safe chain `entry_contract_to_selector_gate_to_notes_only_candidate_to_future_conversion_boundary` for an explicitly enabled Ballad SPREAD pilot. The result remains a notes-only `SpreadProjectionCandidate`; `candidate_conversion_allowed=false`, `style_runtime_wiring_enabled=false`, and `runtime_enabled=false`. It is safe dry run only, with no expression/pedal changes and no default Ballad runtime retune. Medium Swing and Bossa remain unaffected.


## v2_2_45 update — Ballad SPREAD Runtime Conversion Boundary Audit

- Added `SPREAD_RUNTIME_CONVERSION_BOUNDARY_AUDIT_VERSION` in the existing `core.voicing.disposition.spread` owner.
- Added `SpreadRuntimeConversionBoundaryStatus`, `SpreadRuntimeConversionFieldAudit`, `SpreadRuntimeConversionBoundaryAudit`, and `BalladSpreadRuntimeConversionBoundaryAuditResult`.
- Added `spread_runtime_conversion_boundary_audit`, `audit_ballad_spread_runtime_conversion_boundaries`, `spread_runtime_conversion_boundary_debug`, and `ballad_spread_runtime_conversion_boundary_debug`.
- This stage audits the future `SpreadProjectionCandidate_to_VoicingCandidate_boundary_audit_only` path and explicitly does not create a runtime `VoicingCandidate`.
- The audit records mappable fields such as notes/degrees, adapter-required fields such as `content_family/root_support/bass_relation/interval_structure`, and the v2_2_46 `runtime_functional_grouping_value_exists` alignment for `1+4` before any SPREAD runtime conversion.
- `candidate_conversion_allowed=false`, `candidate_generator_wiring_allowed=false`, `style_runtime_wiring_enabled=false`, and `runtime_enabled=false`; no expression/pedal/touch behavior is changed.
- Medium Swing and Bossa remain unaffected. This is boundary audit only, not Ballad runtime retune.


## v2_2_46 update — FunctionalGrouping 1+4 Contract Alignment

Tokens: `FUNCTIONAL_GROUPING_1PLUS4_CONTRACT_ALIGNMENT_VERSION`, `FunctionalGrouping.ONE_PLUS_FOUR`, `SpreadFunctionalGroupingContractAlignment`, `align_spread_functional_grouping_contract`, `functional_grouping_1plus4_contract_alignment_debug`, `runtime_functional_grouping_value_exists`, `foundation_group`, `projection_group`, `candidate_conversion_allowed=false`, `candidate_generator_wiring_allowed=false`, `style_runtime_wiring_enabled=false`, `runtime_enabled=false`; Medium Swing and Bossa remain unaffected.

Meaning: SPREAD `1+4` is now aligned with the core abstract grouping taxonomy as lower/foundation root plus upper/projection 4-note block. The projection map can partition a five-note candidate as `foundation_group=[0]` and `projection_group=[1,2,3,4]`. This is contract alignment only: it does not convert `SpreadProjectionCandidate` into `VoicingCandidate`, does not wire candidate_generator, and does not touch expression or pedal.

## v2_2_47 update — SPREAD Runtime Adapter Skeleton

- Added `SPREAD_RUNTIME_ADAPTER_SKELETON_VERSION = "v2_2_47"` in the existing `core/voicing/disposition/spread.py` module; no new parallel voicing system or new file split was introduced.
- New contract/debug surfaces: `SpreadRuntimeAdapterStatus`, `SpreadRuntimeAdapterFieldMapping`, `SpreadRuntimeAdapterResult`, `BalladSpreadRuntimeAdapterSkeletonResult`, `spread_projection_candidate_to_voicing_candidate_adapter`, `run_ballad_spread_runtime_adapter_skeleton`, `spread_runtime_adapter_skeleton_debug`, and `ballad_spread_runtime_adapter_skeleton_debug`.
- The adapter maps a legal `SpreadProjectionCandidate` to a `VoicingCandidate` only when explicitly requested for dry-run/debug verification; default behavior remains blocked.
- Field mapping preserves notes, degrees, `FunctionalGrouping.ONE_PLUS_FOUR`, foundation/projection group roles, projection map metadata, register/span/gap guards, and SPREAD source metadata.
- `candidate_generator_wiring_allowed=false`, `style_runtime_wiring_enabled=false`, and `runtime_enabled=false` remain hard boundaries; this is adapter skeleton only, not Ballad runtime retune.
- Jazz Ballad metadata now declares `SpreadProjectionCandidate_to_VoicingCandidate_adapter_skeleton_only`; Medium Swing and Bossa remain unaffected.

## v2_2_48 update — Ballad SPREAD Runtime Pilot Candidate Pool Integration

- Added `BALLAD_SPREAD_RUNTIME_CANDIDATE_POOL_INTEGRATION_VERSION = "v2_2_48"` in the existing `core/voicing/disposition/spread.py` owner; no new parallel voicing system or new SPREAD file split was introduced.
- New contract/debug surfaces: `BalladSpreadRuntimeCandidatePoolStatus`, `BalladSpreadRuntimeCandidatePoolPlan`, `BalladSpreadRuntimeCandidatePoolResult`, `ballad_spread_runtime_candidate_pool_plan`, `build_ballad_spread_runtime_pilot_candidate_pool`, and `ballad_spread_runtime_candidate_pool_debug`.
- The candidate pool is closed by default: `candidate_pool_enabled=false`, `adapter_conversion_allowed=false`, `candidate_pool_merge_allowed=false`, and `candidate_generator_wiring_allowed=false` in the default Jazz Ballad policy metadata.
- When explicitly enabled for `jazz_ballad`, the pilot may prepend adapted SPREAD `VoicingCandidate` skeletons to the runtime candidate pool while preserving the existing non-SPREAD pool as fallback: `fallback_to_existing_pool=true` and `default_style_runtime_unchanged=true`.
- The integration is still a controlled pilot candidate source: no expression/pedal/touch behavior is changed, no Ballad default retune is enabled, and Medium Swing and Bossa remain unaffected.

## v2_2_49 update — Ballad SPREAD Pilot Selection Weight + Fallback Audit

- Added `BALLAD_SPREAD_PILOT_SELECTION_WEIGHT_FALLBACK_AUDIT_VERSION = "v2_2_49"` in the existing `core/voicing/disposition/spread.py` owner; no new parallel voicing system or new SPREAD file split was introduced.
- New audit/debug surfaces: `BalladSpreadPilotSelectionAuditStatus`, `BalladSpreadPilotSelectionWeightPlan`, `BalladSpreadPilotSelectionWeightFallbackAuditResult`, `ballad_spread_pilot_selection_weight_plan`, `audit_ballad_spread_pilot_selection_weight_and_fallback`, and `ballad_spread_pilot_selection_weight_fallback_audit_debug`.
- The audit checks explicit Ballad pilot pool safety before any real selection: `fallback_required=true`, `candidate_order_is_selection_priority=false`, `selector_scoring_still_authoritative=true`, and `candidate_selection_not_performed=true`.
- Explicit SPREAD pilot candidates remain secondary pilot candidates rather than a default replacement for the existing non-SPREAD pool. The fallback pool must be retained, SPREAD raw-score margin and candidate share are audited, and dominance risk is reported instead of silently retuning selection.
- This pass remains audit-only: `style_runtime_default_enabled=false`, `default_style_runtime_unchanged=true`, `runtime_enabled=false`, no expression/pedal/touch retune, and Medium Swing and Bossa remain unaffected.

### v2_2_50 — Ballad SPREAD Pilot Runtime Enablement Guard + First Listening Isolation

- Adds `BALLAD_SPREAD_PILOT_RUNTIME_ENABLEMENT_GUARD_VERSION = "v2_2_50"` in the existing SPREAD disposition module.
- Adds `BalladSpreadPilotRuntimeEnablementGuardStatus`, `BalladSpreadPilotRuntimeEnablementGuardPlan`, and `BalladSpreadPilotRuntimeEnablementGuardResult`.
- Adds `ballad_spread_pilot_runtime_enablement_guard_plan`, `guard_ballad_spread_pilot_runtime_enablement`, and `ballad_spread_pilot_runtime_enablement_guard_debug`.
- Candidate generation now requires the v2_2_50 guard before consuming explicit Ballad SPREAD pilot candidates: `runtime_guard_enabled=false` and `listening_isolation_enabled=false` are the default style-policy values.
- First listening isolation is generated by `examples/scripts/generate_ballad_spread_first_listening_isolation_demo.py` and writes `v2_2_50_misty_jazz_ballad_spread_first_listening_isolation_demo.mid`.
- The pilot remains `first_listening_isolation_only=true`: fallback is retained, expression/pedal are not changed, and Medium Swing and Bossa remain unaffected.

### v2_2_51 — Expression Region Duration Clamp for Ballad SPREAD Listening Clarity

- Adds `EXPRESSION_REGION_DURATION_CLAMP_VERSION = "v2_2_51"` in the existing core expression resolver.
- Concrete expression durations are clamped to the remaining length of their own harmonic/chord region when region metadata is available. Pattern remains pitchless; style expression profiles still describe desired touch/sustain.
- This directly addresses Ballad SPREAD first-listening clarity: warm sustain can no longer spill over dense two-chord bars and blur into the next chord region.
- The expression audit exposes clamp metadata and does not treat intentionally region-clamped Ballad soft sustain as a soft-sustain error.
- No SPREAD voicing retune, no pedal retune, no new voicing system, and no Medium Swing/Bossa behavior change by policy.
- Listening demo: `v2_2_51_misty_jazz_ballad_spread_region_clamped_listening_demo.mid`.

## v2_2_52 update — Ballad SPREAD 1+4 True Isolation Fix

- Adds `BALLAD_SPREAD_1PLUS4_TRUE_ISOLATION_FIX_VERSION = "v2_2_52"` in the existing `core/voicing/disposition/spread.py` owner; no new parallel voicing system or new file split was introduced.
- Adds explicit listening-isolation metadata: `ballad_spread_1plus4_true_isolation.enabled=true`, `required_recipe_id="spread_1plus4_contract"`, and `fallback_only_when_missing=true`.
- In first-listening isolation mode, candidate generation now filters the guarded pool to the matching SPREAD pilot candidate when available, so the selector cannot choose the normal 4-note fallback pool during a requested 1+4 isolation demo.
- Fallback remains available only when the requested SPREAD contract cannot be built at all; Medium Swing and Bossa remain blocked by the existing Ballad style gate.
- This pass does not change expression, pedal, pattern, or default Jazz Ballad runtime policy. It only fixes the isolation demo contract so `1+4 = lower root + upper 4-note block` can actually be heard as a 5-note piano voicing.
- Listening demo: `v2_2_52_misty_jazz_ballad_spread_1plus4_true_isolation_demo.mid`.

## v2_2_53 update — SPREAD 1+4 Upper Compact Closed Parent Alignment

- Adds `SPREAD_1PLUS4_UPPER_COMPACT_CLOSED_PARENT_ALIGNMENT_VERSION = "v2_2_53"`.
- Adds `compact_closed_parent_candidates_for_projection()` to existing `core/voicing/disposition/closed.py` as a shared compact parent construction boundary.
- SPREAD 1+4 upper 4-note blocks now use compact closed parent candidates before delegating to OPEN-owned DROP2/DROP3 projection resources.
- This prevents extension/alteration offsets such as 9/b9 from being treated as wide oriented-stack parents before drop projection.
- No new parallel voicing system; no Ballad expression/pedal/pattern retune; no Medium Swing/Bossa runtime change.
- Listening demo: `v2_2_53_misty_jazz_ballad_spread_1plus4_compact_parent_alignment_demo.mid`.
