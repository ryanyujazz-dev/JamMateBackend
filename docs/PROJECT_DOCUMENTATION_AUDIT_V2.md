# Project Documentation Audit V2 — Compact

Current version: `v2_2_88`.

## Canonical reading path

`agent.md` → `DEVELOPMENT_HARNESS_V2.md` → `ARCHITECTURE_V2.md` → `PIPELINE_V2.md` → `SYSTEM_CONTRACTS_V2.md` → voicing docs → generation/style docs.

## Source-of-truth matrix

- Architecture tree: `ARCHITECTURE_V2.md`, mirrored in `DEVELOPMENT_HARNESS_V2.md`.
- Pipeline: `PIPELINE_V2.md`.
- Cross-layer rules: `SYSTEM_CONTRACTS_V2.md`.
- Voicing design: `VOICING_SYSTEM_V2_DESIGN.md` and `DISPOSITION_PROJECTION_ARCHITECTURE_V2.md`.
- Texture state: `VOICING_TEXTURE_STATE_ARCHITECTURE_V2.md`.
- Generation rules: `GENERATION_RULES_SUMMARY_V2.md`.
- Style baselines: `STYLE_RULE_BASELINE_V2.md`.
- Future ideas: `FUTURE_IDEAS_BACKLOG_V2.md`.

## Documentation update policy

Keep docs concise. Replace rolling history with current truth plus shipped-contract aliases only when tests need stable names. No new docs subfolder is needed at this stage. `v2_1_44` introduced this audit map; this pass compresses it.

## SPREAD documentation ownership

SPREAD notes design lives primarily in `VOICING_SYSTEM_V2_DESIGN.md` and `DISPOSITION_PROJECTION_ARCHITECTURE_V2.md`. `VOICING_MODULE_CORE_LOGIC_V2.md` records runtime/core boundaries. `DEVELOPMENT_TASK_PLAN_V2.md` owns the implementation sequence. Do not create a new continuation document unless explicitly requested.

## Compact shipped-contract alias index

This index preserves stable contract names for regression tests while avoiding old rolling task prose. Tokens: 生成规则梳理总结; Medium Swing / BassFoundation; ThreeBeatSkeleton; Five-zone register model; Seventh Bias Audit; Target Continuity Audit; 代码落位; 规则包组织方式; Pattern rules; Voicing rules; Expression rules; Timing rules; Current known; Style rule baseline docs and formal tuning entry point through `v2_0_46`; v2_0_46 Style Rule Baseline Docs + Tuning Entry Point; STYLE_RULE_BASELINE_V2.md; STYLE_TUNING_ENTRY_POINT_V2.md; Medium Swing Piano baseline; Bossa Piano baseline; Jazz Ballad Piano baseline; v2_1_0 — Medium Swing Piano Musicality Tuning Pass 1; piano musical audit; expression audit; v2_1_4 rooted foundation component; root; foundation component; rooted foundation component; standalone; 2-note standalone voicings; Do **not** treat `root + 3 / 10` as an independent 2-note tuning class; Rooted dyad component pool, not standalone review targets; foundation/support component for 4/5/6-note recipes; v2_1_5; shell_plus_5; shell_plus_1or5; 3rd + 7th + 5th; 3 + 7 + 5; not a triad; v2_1_6; specified color; shell_plus_specified_color; v2_1_7; expanded shell color; harmonic expansion; v2_1_8; superseded; v2_1_9; _color_minor_second_direction_adjustment; move color toward the other shell; v2_1_10; rootless_ab_safe; chord_symbol_has_explicit_color; rootless_ab_explicit_chord_symbol_color_used; rootless_ab_harmonic_expansion_enabled; rootless_ab_content_type_halfdim_with_9; v2_1_11; HarmonicExpansionPolicy; VoicingColorPolicy; harmonic_expansion_enabled; color_policy_mode; chord_symbol_only; explicit_chord_symbol_color; v2_1_12; rootless A/B orientation; canonical source; canonical_closed_position_source; rootless_A; rootless_B; rootless_ab_inversion_weight; 3579; 7935; with_5; with_13; v2_1_13; minor 13 modal gate; Locrian; Half-diminished is not a separate rootless source; v2_1_15; canonical inversions; v2_1_16; Voicing Source Module Boundary Cleanup; source_balance.py; No new subfolder; Minimal File Split Principle; v2_1_17; rootless_ab_average_pitch_target_low; rootless_ab_average_pitch_target_high; v2_1_18; halfdim Locrian rootless A/B; v2_1_19; basic_4note_root_third_fifth_seventh; root-third-fifth-seventh; v2_1_20; altered_dominant_rootless; rooted/rootless altered color families; v2_1_21; harmonic expansion cleanup; v2_1_22; functional source degree naming; v2_1_23; basic_4note_source_family; basic_4note_source_role_order; v2_1_24; four_note_color_gate; v2_1_27; four_note_allowed_color_set_contract_v2_1_27; chart_color_fidelity; explicit_chart_color; explicit_chart_color_plus_harmonic_expansion; v2_1_37; Do not generalize v2_1_37 immediately; v2_1_40; 3-note closed listening verification; root-third-fifth; per-source nearest; no-seventh symbols use real triad/add/sus sources; v2_1_42; 4-Note Triad-Aware Closed Source Sync; 1351; 3513; 5135; sus2, density=4, closed; closed register floor down by a major third; F3 / MIDI 53; v2_1_43; source_balance.py; Current audit version: `v2_2_10`; Source-of-truth matrix; Documentation update policy; Canonical reading path; No new docs subfolder is needed; v2_1_44; Current plan version: `v2_2_5`; closed legality filter; per-source nearest-motion realization; 1351 / 3513 / 5135; v2_2_0; v2_2_1 — Disposition Projection Entry Pass; v2_2_5; v2_2_8; OPEN method candidate pool rule; v2_2_8 Progression / Phrase-level Voicing Method Lock Contract; VoicingMethodLockSpec; auto_method_lock_scope_enabled; open_projection_method_pool; active_open_projection_method; method_lock_follow_metadata_from_seed_candidate; v2_2_10; method_lock_rescue_runtime_enabled; v2_2_12; harmonic_context_adapter; metadata_harmonic_context_adapter; harmonic_context_backed_method_lock_scope_adapter_v2_2_14; v2_2_14; method_lock_seed_then_follow_runtime_wiring_v2_2_14; method_lock_rescue_planning_v2_2_14; method_lock_filtered_all_candidates; v2_2_20; v2_2_21; VoicingTextureIntent; VoicingTextureState; VoicingTexturePlan; VoicingTexturePlan -> ContentRecipe -> CanonicalClosedSource -> DispositionGenerator -> VoiceLeadingScorer; derive_voicing_texture_intent; derive_voicing_texture_state; voicing_texture_state_engine_resolved_contract_v2_2_21; default listening behavior unchanged; the next engineering target should be selected by the user.


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


## v2_2_38 documentation sync

Lower Group Recipe Inventory documentation is synchronized across README, agent.md, VOICING_SYSTEM_V2_DESIGN, VOICING_MODULE_CORE_LOGIC, DISPOSITION_PROJECTION_ARCHITECTURE, DEVELOPMENT_TASK_PLAN, DEVELOPMENT_HARNESS, and GENERATION_RULES_SUMMARY. No continuation document is generated by default.

## v2_2_43 — SPREAD Candidate Selector Contract / Runtime Gate Skeleton

SPREAD Candidate Selector Contract / Runtime Gate Skeleton adds a safety-gated selector surface in the existing `core/voicing/disposition/spread.py` owner. It introduces `SPREAD_SELECTOR_RUNTIME_GATE_VERSION = "v2_2_42"`, `SpreadRuntimeGateDecision`, `SpreadCandidateSelectorRequest`, `SpreadCandidateSelectorResult`, `spread_runtime_gate_from_policy`, `select_spread_candidate_with_runtime_gate`, and `spread_candidate_selector_contract_debug`.

The gate is closed by default. To open it, policy metadata must explicitly request the SPREAD selector gate, for example `spread_selector_enabled=true` / `spread_runtime_gate_enabled=true`, and the resolved texture family must request `spread` through `primary_family`, `allowed_families`, or `VoicingTextureState`. Even when open, the result remains a notes-only `SpreadProjectionCandidate`: `candidate_conversion_allowed=false`, `style_runtime_wiring_enabled=false`, `runtime_enabled=false`, and no expression or pedal behavior is introduced. This is a selector contract / runtime gate skeleton only; it does not retune Ballad, Bossa, or Medium Swing runtime behavior.

## v2_2_43 — SPREAD Runtime Pilot Planning / Ballad Entry Contract

SPREAD Runtime Pilot Planning / Ballad Entry Contract adds a guarded Jazz Ballad pilot entry contract in the existing `core/voicing/disposition/spread.py` owner. It introduces `BALLAD_SPREAD_RUNTIME_ENTRY_CONTRACT_VERSION = "v2_2_43"`, `BalladSpreadEntryScene`, `BalladSpreadRuntimeEntryContract`, `BalladSpreadRuntimeEntryDecision`, `BalladSpreadRuntimePilotResult`, `ballad_spread_runtime_entry_contract`, `resolve_ballad_spread_runtime_entry`, `select_ballad_spread_pilot_candidate`, and `ballad_spread_runtime_entry_debug`.

The contract is planning/debug only: Jazz Ballad must explicitly set `ballad_spread_runtime_pilot.enabled=true` and still pass the existing SPREAD selector gate before notes-only pilot selection can return a `SpreadProjectionCandidate`. It keeps `style_runtime_wiring_enabled=false`, `candidate_conversion_allowed=false`, `runtime_enabled=false`, `notes-only`, and `no_expression_or_pedal=true`; Medium Swing and Bossa remain unaffected. Ballad pilot grouping is limited to `1+4`, `2+3`, `2+4`, and `3+3`, with `3+4` / 7-note thick ending left for a later explicit ending/climax pass.


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

## v2_2_49 update — Ballad SPREAD Pilot Selection Weight + Fallback Audit

- Added `BALLAD_SPREAD_PILOT_SELECTION_WEIGHT_FALLBACK_AUDIT_VERSION = "v2_2_49"` in the existing `core/voicing/disposition/spread.py` owner; no new parallel voicing system or new SPREAD file split was introduced.
- New audit/debug surfaces: `BalladSpreadPilotSelectionAuditStatus`, `BalladSpreadPilotSelectionWeightPlan`, `BalladSpreadPilotSelectionWeightFallbackAuditResult`, `ballad_spread_pilot_selection_weight_plan`, `audit_ballad_spread_pilot_selection_weight_and_fallback`, and `ballad_spread_pilot_selection_weight_fallback_audit_debug`.
- The audit checks explicit Ballad pilot pool safety before any real selection: `fallback_required=true`, `candidate_order_is_selection_priority=false`, `selector_scoring_still_authoritative=true`, and `candidate_selection_not_performed=true`.
- Explicit SPREAD pilot candidates remain secondary pilot candidates rather than a default replacement for the existing non-SPREAD pool. The fallback pool must be retained, SPREAD raw-score margin and candidate share are audited, and dominance risk is reported instead of silently retuning selection.
- This pass remains audit-only: `style_runtime_default_enabled=false`, `default_style_runtime_unchanged=true`, `runtime_enabled=false`, no expression/pedal/touch retune, and Medium Swing and Bossa remain unaffected.

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


## v2_2_88 audit note

`PROJECT_AUDIT_DEVELOPMENT_TASK_PLAN_V2_2_86.md` is the current project-audit and roadmap sync document. It records that runtime generation logic is unchanged, that v2_2_85 altered dominant functional scoping is stable, and that the next true musical implementation task is `v2_2_88 — Altered Dominant Intensity / Source Weight Calibration`.

Canonical validation is now documented as:

```bash
python -m compileall src
PYTHONPATH=src python -m pytest -q
python tools/check_development_harness.py
```
