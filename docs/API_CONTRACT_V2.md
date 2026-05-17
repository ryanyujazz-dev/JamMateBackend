## v2_3_15 HarmonyOS API Smoke Test Pack

New endpoints: `GET /agent/contracts/smoke-pack` and `GET /agent/contracts/smoke-pack/files`. The smoke pack defines the minimum HarmonyOS integration sequence: `/health`, `/accompaniment/generate`, and `/agent/playback/prepare`. Smoke payloads are also written under `frontend_fixtures/harmonyos/smoke/`.

## v2_3_15 Response Case Policy / HarmonyOS Adapter Addendum

Backend responses are canonical `snake_case`; requests accept `snake_case` and `camelCase`. HarmonyOS client-domain objects are camelCase after `CaseAdapter.ets` mapping. New endpoint: `GET /agent/contracts/case-policy`. Generated frontend pack now includes `api/CaseAdapter.ets`, and `JamMateApiClient.ets` maps `/agent/*` and `/accompaniment/generate` responses into camelCase domain objects.


## v2_3_15 Agent Contract Codegen / Fixture Pack

New endpoints:

```text
GET /agent/contracts/arkts/files
GET /agent/contracts/fixtures
GET /agent/contracts/frontend-pack
```

These endpoints expose copyable ArkTS interfaces and stable frontend fixtures. They do not replace `/accompaniment/generate` or `/agent/playback/prepare`; they only support HarmonyOS development and mock UI/state testing.

# v2_3_15 API Contract Addendum — HarmonyOS API Smoke Test Pack

New contract endpoints: `GET /agent/contracts/arkts/source`, `GET /agent/contracts/examples`, and `GET /agent/playback/spec`. Responses remain canonical snake_case; requests accept snake_case or camelCase. Playback assets now expose `asset.cache_key`, and agent playback instructions expose local-loop and cache policy metadata.

# v2_3_11 API Contract Addendum — Agent Context / Contract Hardening

New Agent contract/debug endpoints:

```text
GET /agent/capabilities
GET /agent/context/profiles
GET /agent/contracts/arkts
GET /agent/traces
GET /agent/traces/{trace_id}
```

API input models now accept both snake_case and camelCase. HarmonyOS may send `userInput`, `availableMinutes`, `durationMinutes`, and `clientContext`; Python examples may continue to use `user_input`, `available_minutes`, `duration_minutes`, and `client_context`.

`/agent/playback/prepare` response keeps `playback_instruction.client_loop_until_target_duration = true`; clients should loop the returned MIDI asset until the practice timer reaches `target_duration_minutes`.

# API Contract V2 — Compact

Current version: `v2_2_63`.

`generate_accompaniment(request)` accepts a score/leadsheet document or path, style, tempo, choruses, seed, output path, and ensemble/options. The runtime response uses centralized `ENGINE_VERSION_TAG` and must not hardcode version strings elsewhere.

Server API files live in `src/jammate_engine/api/`: `schemas.py`, `routes.py`, `app.py`, `version.py`.

Runtime package note: callers should pass `leadsheet` / `score_document` or a valid external score path; the runtime package is not required to ship a full `scores/` library.


## Compact shipped-contract alias index

This index preserves stable contract names for regression tests while avoiding old rolling task prose. Tokens: 生成规则梳理总结; Medium Swing / BassFoundation; ThreeBeatSkeleton; Five-zone register model; Seventh Bias Audit; Target Continuity Audit; 代码落位; 规则包组织方式; Pattern rules; Voicing rules; Expression rules; Timing rules; Current known; Style rule baseline docs and formal tuning entry point through `v2_0_46`; v2_0_46 Style Rule Baseline Docs + Tuning Entry Point; STYLE_RULE_BASELINE_V2.md; STYLE_TUNING_ENTRY_POINT_V2.md; Medium Swing Piano baseline; Bossa Piano baseline; Jazz Ballad Piano baseline; v2_1_0 — Medium Swing Piano Musicality Tuning Pass 1; piano musical audit; expression audit; v2_1_4 rooted foundation component; root; foundation component; rooted foundation component; standalone; 2-note standalone voicings; Do **not** treat `root + 3 / 10` as an independent 2-note tuning class; Rooted dyad component pool, not standalone review targets; foundation/support component for 4/5/6-note recipes; v2_1_5; shell_plus_5; shell_plus_1or5; 3rd + 7th + 5th; 3 + 7 + 5; not a triad; v2_1_6; specified color; shell_plus_specified_color; v2_1_7; expanded shell color; harmonic expansion; v2_1_8; superseded; v2_1_9; _color_minor_second_direction_adjustment; move color toward the other shell; v2_1_10; rootless_ab_safe; chord_symbol_has_explicit_color; rootless_ab_explicit_chord_symbol_color_used; rootless_ab_harmonic_expansion_enabled; rootless_ab_content_type_halfdim_with_9; v2_1_11; HarmonicExpansionPolicy; VoicingColorPolicy; harmonic_expansion_enabled; color_policy_mode; chord_symbol_only; explicit_chord_symbol_color; v2_1_12; rootless A/B orientation; canonical source; canonical_closed_position_source; rootless_A; rootless_B; rootless_ab_inversion_weight; 3579; 7935; with_5; with_13; v2_1_13; minor 13 modal gate; Locrian; Half-diminished is not a separate rootless source; v2_1_15; canonical inversions; v2_1_16; Voicing Source Module Boundary Cleanup; source_balance.py; No new subfolder; Minimal File Split Principle; v2_1_17; rootless_ab_average_pitch_target_low; rootless_ab_average_pitch_target_high; v2_1_18; halfdim Locrian rootless A/B; v2_1_19; basic_4note_root_third_fifth_seventh; root-third-fifth-seventh; v2_1_20; altered_dominant_rootless; rooted/rootless altered color families; v2_1_21; harmonic expansion cleanup; v2_1_22; functional source degree naming; v2_1_23; basic_4note_source_family; basic_4note_source_role_order; v2_1_24; four_note_color_gate; v2_1_27; four_note_allowed_color_set_contract_v2_1_27; chart_color_fidelity; explicit_chart_color; explicit_chart_color_plus_harmonic_expansion; v2_1_37; Do not generalize v2_1_37 immediately; v2_1_40; 3-note closed listening verification; root-third-fifth; per-source nearest; no-seventh symbols use real triad/add/sus sources; v2_1_42; 4-Note Triad-Aware Closed Source Sync; 1351; 3513; 5135; sus2, density=4, closed; closed register floor down by a major third; F3 / MIDI 53; v2_1_43; source_balance.py; Current audit version: `v2_2_10`; Source-of-truth matrix; Documentation update policy; Canonical reading path; No new docs subfolder is needed; v2_1_44; Current plan version: `v2_2_5`; closed legality filter; per-source nearest-motion realization; 1351 / 3513 / 5135; v2_2_0; v2_2_1 — Disposition Projection Entry Pass; v2_2_5; v2_2_8; OPEN method candidate pool rule; v2_2_8 Progression / Phrase-level Voicing Method Lock Contract; VoicingMethodLockSpec; auto_method_lock_scope_enabled; open_projection_method_pool; active_open_projection_method; method_lock_follow_metadata_from_seed_candidate; v2_2_10; method_lock_rescue_runtime_enabled; v2_2_12; harmonic_context_adapter; metadata_harmonic_context_adapter; harmonic_context_backed_method_lock_scope_adapter_v2_2_14; v2_2_14; method_lock_seed_then_follow_runtime_wiring_v2_2_14; method_lock_rescue_planning_v2_2_14; method_lock_filtered_all_candidates; v2_2_20; v2_2_21; VoicingTextureIntent; VoicingTextureState; VoicingTexturePlan; VoicingTexturePlan -> ContentRecipe -> CanonicalClosedSource -> DispositionGenerator -> VoiceLeadingScorer; derive_voicing_texture_intent; derive_voicing_texture_state; voicing_texture_state_engine_resolved_contract_v2_2_21; default listening behavior unchanged; the next engineering target should be selected by the user.


## Additional compact compatibility aliases

generation/bass_foundation/; Do not add more core infrastructure; No BassFoundation retune; 3-note; 5-note; 6-note; rootless_ab_content_type_with_5; rootless_ab_content_type_with_13; m7 + 13; m7b5; m11b5; b3 + b7 + b5; shell_plus_expanded_color; supersedes; replaces; directed minor-second; directed m2; runtime_filtering_enabled=True; HarmonicContext-backed Method Lock Scope Adapter; Seed-Then-Follow; Method Lock Rescue; Method Lock Rescue Runtime; OpenProjectionMethod.DROP2; ii-V; V-I; ii-V-I; progression_phrase_voicing_method_lock_planning_only; locked_method; open_projection_method; boundary_test_source; DROP2 Audit Fixture; open_drop2_parent_closed_degrees; docs/ARCHITECTURE_V2.md; docs/PIPELINE_V2.md; docs/SYSTEM_CONTRACTS_V2.md; docs/API_CONTRACT_V2.md; docs/GENERATION_RULES_SUMMARY_V2.md; docs/STYLE_RULE_BASELINE_V2.md; docs/STYLE_TUNING_ENTRY_POINT_V2.md; docs/DEVELOPMENT_TASK_PLAN_V2.md; docs/DEVELOPMENT_HARNESS_V2.md; docs/NEW_FILE_PLACEMENT_GUIDE_V2.md; docs/FUTURE_IDEAS_BACKLOG_V2.md; docs/VOICING_MODULE_FILE_AUDIT_V2.md; docs/PROJECT_DOCUMENTATION_AUDIT_V2.md; docs/CLOSED_3_4_NOTE_BASELINE_AND_PRE_DISPOSITION_PLAN_V2.md; docs/DISPOSITION_PROJECTION_ARCHITECTURE_V2.md; docs/VOICING_TEXTURE_STATE_ARCHITECTURE_V2.md; generate_closed_34note_baseline_smoke_listening.py; generate_3note_closed_listening_verification_demos.py; generate_4note_source_weight_listening_verification_demos.py; generate_4note_triad_closed_listening_verification_demos.py; generate_4note_triad_closed_listening_verification_demos; closed_34note_baseline_smoke_summary; 4-note triad-aware closed listening; closed register downshift; closed legality; avg_closed_4note_source_collapse_distance; closed_3note_closed_legality_then_nearest_motion; closed_3note_per_source_minimum_motion; closed_4note_per_source_minimum_motion; closed_4note_minimum_motion_events; closed_voicing_lowest_note_floor; min_closed_voicing_lowest_note; max_closed_voicing_span; max_density; min_density; preferred_density.


## Final compact compatibility aliases

A-B-A; B-A-B; Dorian; modal; 3-5-7-9; 7-9-3-5; 5-7-9-3; 9-3-5-7; Content Recipe; ContentRecipe; Register Center; register center; b9; b13; 1357; 1-3-5-7; color_permission.py; four_note_sources.py; SEVENTH_BASIC altered-dominant compatibility path has been removed; 4-Note Source Weight Implementation / Listening Prep Pass; 4-Note Source Weight Listening Verification Pass; 3-note functional closed; no partial fallback; 2-note Guide-Tone Shell; Rule Change Documentation Sync Standard; 不能只改代码、不改规则文档; root/1; root / 1; shell+1/root; 1251; 2512; 5125; docs/VOICING_SYSTEM_V2_DESIGN.md; docs/VOICING_MODULE_CORE_LOGIC_V2.md; docs/VOICING_TUNING_WORKFLOW_V2.md; Voicing Source Module Boundary Cleanup; _four_note_color_permission_notes; from .color_permission import; from .four_note_sources import; source_family_weights; mode-aware gate buckets; four_note_source_balance_gate_modes; four_note_source_balance_keys; source_family; source_type; source weight; altered dominant; compatibility path; root_third_fifth_seventh; root_third_fifth_sixth; root_fourth_fifth_seventh; root_third_fifth_ninth; root_third_ninth; root_third_seventh_altered_color; root-third-fifth-sixth; root-third-seventh-altered-color; rooted_color_4note; rooted_color_4note_source_family; rooted_color_4note_functional_content_type_; rootless_ab_content_type_with_5; rootless_ab_content_type_with_13; rootless_ab_inversion_index; rootless_ab_inversion_prior_score; rootless_ab_degree_order; basic_4note_legacy_source_family_alias; basic_4note_altered_dominant_compatibility_source; basic_4note_dim7_source_family; basic_4note_1357; 4_note_basic_1357; hard binding concept; not a new progression recognizer; OpenProjectionMethod.DROP3; OpenProjectionMethod.DROP2_AND_4; same DispositionFamily + ProjectionMethod; method lock rescue; same-family fallback; generic open fallback; closed compact fallback; nearest motion; source-order compact stack; parent-closed; parent_closed; closed_parent_placement_callback.
Compact consistency index (historical shipped contract aliases, not active roadmap): ABA; BAB; 8:2; 52-74; 60-74; 3-b7-X-Y; Harmonic expansion does not replace the chord; functional degree source; 4-Note Source Gating Audit; Mode-Aware Source Weight; Unified Color Permission + Chart Fidelity; Eleventh / #11 / Explicit Extension Source Completion; Color Source Gating Regression; four_mode_aware; v2_1_37; v2_1_40; v2_1_43; B3-F4; Rule Change Documentation Sync Standard; 规则变化就必须同步文档; 1451; 1351; 1251; core/harmony/harmonic_context.py; OpenProjectionMethod.GENERIC_OPEN; planning-only.
Compact contract token index B (historical shipped docs preserved as aliases, not active roadmap): rootless_ab_register_center_score; generated demo artifacts are not packaged; third-fifth-seventh-ninth; source_family_weights_by_gate; AllowedColorSet; root-third-seventh-eleventh; alt palette; G9 / G7#9 / G7b13 / Bm11b5; Top-k nearest realizations; common-tone; 3-note closed; 4-note closed; 3513; 5135; Progression / phrase-level voicing method lock.
Compact contract token index C: Gesture-driven revoicing; 2_note_guide_tone_shell; per-source nearest.
Compact contract token index D: Do not generalize v2_1_37 immediately; All the Things You Are.
Compact harness contract index: classic_fill_min_gap_regions; classic fill; logical grid; same current-root note; timing_intent; BassFoundation Musicality Audit; Region Decision Trace; target-to-target; target_nextR_note; Seventh lower-lane; Target Continuity Audit; Pattern rules; Voicing rules; Expression rules; Timing rules; generate_closed_34note_baseline_smoke_listening.py; CLOSED_3_4_NOTE_BASELINE_AND_PRE_DISPOSITION_PLAN_V2.md; legacy Disposition; resolver migration is not part of v2_2_x; project_source_to_disposition(); DispositionProjectionResult; v2_2_2 — Closed Projection Migration / No Behavior Change; src/jammate_engine/core/voicing/disposition/closed.py; place_compact_closed_seed_layout; strict_closed_register_variants; closed_projection_migrated; v2_2_3 — Legacy Disposition Cleanup Pass; src/jammate_engine/core/voicing/disposition/open.py; src/jammate_engine/core/voicing/disposition/spread.py; src/jammate_engine/core/voicing/disposition/placement_utils.py; disposition/facade.py is now only a placement facade; v2_2_4 — Open Projection Skeleton / DROP2 4-note Only; v2_2_5 update — DROP2 Parent-Closed Projection Correction Pass; place_drop2_projection_from_closed_parent; open_drop2_parent_closed_notes; not from a direct source-order compact stack; v2_2_7 update — OPEN Method Candidate Pool / DROP3-DROP2&4 Skeleton Pass; open_projection_method_pool; DROP3; DROP2_AND_4.
Compact package organization token: BassFoundation 规则包; generation/bass_foundation/.

## Request / leadsheet boundary

Runtime requests accept `leadsheet` plus `choruses`. The leadsheet describes written form; the request describes this performance. This prevents score-level repeat counts from multiplying with runtime chorus counts.



V2 does not maintain a V1 `blocks/form` compatibility shape; mature V1 chart ideas were re-expressed as native `sections + written_form` documents.

## v2_2_49 update — Ballad SPREAD Pilot Selection Weight + Fallback Audit

- Added `BALLAD_SPREAD_PILOT_SELECTION_WEIGHT_FALLBACK_AUDIT_VERSION = "v2_2_49"` in the existing `core/voicing/disposition/spread.py` owner; no new parallel voicing system or new SPREAD file split was introduced.
- New audit/debug surfaces: `BalladSpreadPilotSelectionAuditStatus`, `BalladSpreadPilotSelectionWeightPlan`, `BalladSpreadPilotSelectionWeightFallbackAuditResult`, `ballad_spread_pilot_selection_weight_plan`, `audit_ballad_spread_pilot_selection_weight_and_fallback`, and `ballad_spread_pilot_selection_weight_fallback_audit_debug`.
- The audit checks explicit Ballad pilot pool safety before any real selection: `fallback_required=true`, `candidate_order_is_selection_priority=false`, `selector_scoring_still_authoritative=true`, and `candidate_selection_not_performed=true`.
- Explicit SPREAD pilot candidates remain secondary pilot candidates rather than a default replacement for the existing non-SPREAD pool. The fallback pool must be retained, SPREAD raw-score margin and candidate share are audited, and dominance risk is reported instead of silently retuning selection.
- This pass remains audit-only: `style_runtime_default_enabled=false`, `default_style_runtime_unchanged=true`, `runtime_enabled=false`, no expression/pedal/touch retune, and Medium Swing and Bossa remain unaffected.


- v2_2_85 — Altered Dominant Functional Scope / LLM Semantic Control Tuning: unnotated altered color is gated by resolving V7, secondary, static/blues, backdoor, explicit-symbol, or LLM-selected altered dominant region metadata; rooted color/rootless A-B/Upper Structure share one decision.

- v2_2_88 — Project Audit / Documentation Plan Sync: runtime generation logic is unchanged; docs/version/test expectations now point to the audited v2_2_85 altered-dominant implementation and the next task is altered intensity/source-weight calibration.

## v2_3_10 update — Direct Engine API and JamMate Agent API

New active service app:

```text
jammate_api.app:app
```

Run locally:

```bash
uvicorn jammate_api.app:app --host 0.0.0.0 --port 8000
```

Direct accompaniment path, no LLM required:

```text
GET  /accompaniment/styles
GET  /accompaniment/capabilities
POST /accompaniment/generate
```

Agent orchestration path:

```text
POST /agent/message
POST /agent/practice/plan
POST /agent/playback/prepare
POST /agent/session/review
```

Practice support path:

```text
GET /practice/routines/templates
```

`/agent/playback/prepare` returns a bounded MIDI asset and a playback instruction for the client to loop until the target practice duration. Direct `/accompaniment/generate` honors explicit `choruses`.
