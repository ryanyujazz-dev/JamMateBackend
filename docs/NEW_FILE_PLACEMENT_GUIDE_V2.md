# New File Placement Guide V2 — Compact

Current version: `v2_2_63`.

## Minimal File Split Principle

One logical task should usually live in one existing responsible file. Create a new file only when the responsibility is stable, testable, and naturally separate.

## Capability Reuse Before New Construction

Before a new module/planner/recognizer/resolver/selector, do a reuse audit: existing generic capability, local implementation, adjacent owner, adapter, facade, metadata, or policy extension. Reuse `core/harmony/harmonic_context.py` plus a method-lock scope adapter for progression context.

## Placement rules

- Style rhythm vocabularies → `styles/<style>/comping_patterns.py`, `bass_foundation_patterns.py`, `percussion_patterns.py`.
- Core pattern runtime → `core/pattern_runtime/`, never style-named.
- BassFoundation algorithms → `generation/bass_foundation/`.
- Voicing source/content/texture → `core/voicing/`.
- Disposition projection algorithms → `core/voicing/disposition/`.
- Realizers → `realization/`.
- MIDI writing/timing → `midi/`.
- Solo vocabulary only → `vocabulary/melodic_foreground/`.


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

## v2_2_49 update — Ballad SPREAD Pilot Selection Weight + Fallback Audit

- Added `BALLAD_SPREAD_PILOT_SELECTION_WEIGHT_FALLBACK_AUDIT_VERSION = "v2_2_49"` in the existing `core/voicing/disposition/spread.py` owner; no new parallel voicing system or new SPREAD file split was introduced.
- New audit/debug surfaces: `BalladSpreadPilotSelectionAuditStatus`, `BalladSpreadPilotSelectionWeightPlan`, `BalladSpreadPilotSelectionWeightFallbackAuditResult`, `ballad_spread_pilot_selection_weight_plan`, `audit_ballad_spread_pilot_selection_weight_and_fallback`, and `ballad_spread_pilot_selection_weight_fallback_audit_debug`.
- The audit checks explicit Ballad pilot pool safety before any real selection: `fallback_required=true`, `candidate_order_is_selection_priority=false`, `selector_scoring_still_authoritative=true`, and `candidate_selection_not_performed=true`.
- Explicit SPREAD pilot candidates remain secondary pilot candidates rather than a default replacement for the existing non-SPREAD pool. The fallback pool must be retained, SPREAD raw-score margin and candidate share are audited, and dominance risk is reported instead of silently retuning selection.
- This pass remains audit-only: `style_runtime_default_enabled=false`, `default_style_runtime_unchanged=true`, `runtime_enabled=false`, no expression/pedal/touch retune, and Medium Swing and Bossa remain unaffected.

