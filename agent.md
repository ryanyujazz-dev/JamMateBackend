# JamMatePyEngineV2 Agent Harness — v2_3_15

Current version: `v2_3_15`.

## Active v2_3_15 scope

v2_3_15 — HarmonyOS API Smoke Test Pack. Keep `jammate_engine` independent, keep direct accompaniment callable without LLM, and keep HarmonyOS smoke fixtures aligned with `/agent/contracts/smoke-pack*`. Runtime generation logic is unchanged.

# JamMatePyEngineV2 Agent Harness — v2_3_15

Current version: `v2_3_15`.

## Active v2_3_15 scope

v2_3_15 — HarmonyOS API Smoke Test Pack. HarmonyOS contract files must be generated from `jammate_agent.core.contract_codegen`, not hand-copied in multiple places. Keep `frontend_fixtures/harmonyos/` and `/agent/contracts/*` aligned. Runtime generation logic is unchanged.

New contract endpoints:

```text
GET /agent/contracts/arkts/files
GET /agent/contracts/fixtures
GET /agent/contracts/frontend-pack
```

## Agent / Engine / API boundary

JamMate Agent is a sibling system to JamMate Engine, not a submodule inside the engine. `src/jammate_engine/` is the independent accompaniment generation kernel; `src/jammate_agent/` is the intelligent orchestration layer; `src/jammate_api/` is the HTTP/API service assembly layer. `jammate_engine` must not import `jammate_agent`; `jammate_engine` must remain directly callable without LLM/Agent; `jammate_agent` may use `jammate_engine` only through provider/adapter boundaries; `jammate_api` may assemble both direct engine routes and agent routes.

LLM / Agent is an enhancement path, not a required path. HarmonyOS can run a local non-LLM practice workspace and directly call `/accompaniment/generate` when parameters are explicit.

## Mandatory reading order

Read: `agent.md`, `docs/DEVELOPMENT_HARNESS_V2.md`, `docs/ARCHITECTURE_V2.md`, `docs/PIPELINE_V2.md`, `docs/SYSTEM_CONTRACTS_V2.md`, `docs/API_CONTRACT_V2.md`, `docs/GENERATION_RULES_SUMMARY_V2.md`, `docs/STYLE_RULE_BASELINE_V2.md`, `docs/STYLE_TUNING_ENTRY_POINT_V2.md`, `docs/NEW_FILE_PLACEMENT_GUIDE_V2.md`, `docs/DEVELOPMENT_TASK_PLAN_V2.md`, `docs/FUTURE_IDEAS_BACKLOG_V2.md`, `docs/PROJECT_DOCUMENTATION_AUDIT_V2.md`, `docs/PEDAL_POLICY_EXPRESSION_BOUNDARY_V2_3_9.md`.

## Development workflow rules

- Development delivery workflow rule: Do not output a continuation development document by default; do so only when the user explicitly asks.
- Every engineering delivery should include or preserve a current standard-tune listening demo where relevant. Use All the Things You Are when a generic standard-tune reference is needed; use Misty / Blue Bossa when style context is specific.
- Runtime generation logic is unchanged in documentation/contract/codegen passes unless explicitly stated.
- Update docs with any rule/code behavior change. Do not only change code.
- Future Ideas Backlog: capture non-immediate ideas in `docs/FUTURE_IDEAS_BACKLOG_V2.md` instead of smuggling them into active implementation.

## Minimal File Split Principle

Do not create a new file/module/planner/recognizer before checking whether an existing file or domain package can naturally carry the change. New files must have a stable architectural reason, not merely aesthetic separation.

## Capability Reuse Before New Construction

Before adding a new capability, perform a reuse audit. Prefer an existing local implementation, adapter, facade, metadata extension, or shared resolver before building a new subsystem. Especially reuse `core/harmony/harmonic_context.py` and existing voicing / style / expression policies before adding parallel logic.

## Core boundaries

```text
Pattern      = horizontal, pitchless rhythm / event layout
Anticipation = pitchless event movement across region boundary
Expression   = duration, release, velocity, pedal intent
Voicing      = vertical pitch realization
MIDI         = final event / CC materialization
```

Patterns live in styles; voicing and expression are core-level. Style policies may request behavior, but core modules realize shared mechanisms. Do not place Practice/JamMate Agent orchestration inside `jammate_engine/core`.

## VoicingTextureState architecture tokens

VoicingTextureIntent and VoicingTextureState are LLM-facing/runtime abstractions in `texture_plan.py`; family selection, method lock, and Disposition Projection follow Capability Reuse Before New Construction. The contract includes `derive_voicing_texture_intent`, `derive_voicing_texture_state`, `voicing_texture_state_engine_resolved_contract_v2_2_21`, default listening behavior unchanged, and the next engineering target should be selected by the user.

## BassFoundation and generation-rule tokens

Medium Swing / BassFoundation generation rules are summarized in `docs/GENERATION_RULES_SUMMARY_V2.md`: ThreeBeatSkeleton, Five-zone register model, Seventh Bias Audit, Target Continuity Audit, Region Decision Trace, code placement under `generation/bass_foundation/`, policy.py, rules.py, generator.py, audit.py, BassFoundation 规则包. Generation Rule Documentation Principle requires `GENERATION_RULES_SUMMARY_V2.md` updates for 生成规则 changes.

BassFoundation tuning aliases preserved for harness continuity: root echo density, scale_near_nextR, old-engine lane weighting, root echo same-root, logical grid, same current-root note, timing_intent, CF_TWO_BAR_TONIC_01 scene-triggered, classic fill, classic_fill_enabled, classic_fill_scene, max_region_span.

## Style / voicing documentation aliases

Style baseline tokens: Medium Swing Piano Baseline, Bossa Nova Piano Baseline, Jazz Ballad Piano Baseline, v2_1_0 — Medium Swing Piano Musicality Tuning Pass 1, piano musical audit, expression audit.

3-note closed listening verification: root-third-fifth, per-source nearest, no-seventh symbols use real triad/add/sus sources.

4-Note Triad-Aware Closed Source Sync: 1351, 3513, 5135, sus2, density=4, closed, closed register floor down by a major third, F3 / MIDI 53.

Voicing source cleanup: source_balance.py, No new subfolder, Minimal File Split Principle.

Closed/disposition aliases: generate_closed_34note_baseline_smoke_listening.py, CLOSED_3_4_NOTE_BASELINE_AND_PRE_DISPOSITION_PLAN_V2.md, closed legality filter, per-source nearest-motion realization, DispositionFamily, OpenProjectionMethod, SpreadProjectionMethod, DROP2, legacy Disposition, resolver migration is not part of v2_2_x, project_source_to_disposition(), DispositionProjectionResult.

SPREAD recipe aliases: Spread Recipe Reuse Audit + Contract Skeleton, SPREAD_RECIPE_CONTRACT_VERSION, SpreadRecipeContract, LowerGroupRecipeContract, UpperSourceRef, SpreadReuseAuditItem, spread_recipe_reuse_audit, spread_recipe_contract_skeleton, source/orientation/projection, final placed closed/open, notes-only, expression, lower/upper group-wise voice leading, Basic SPREAD Projection, BASIC_SPREAD_PROJECTION_VERSION, SpreadProjectionRegisterPolicy.

## Project documentation audit

Keep `docs/PROJECT_DOCUMENTATION_AUDIT_V2.md` as the Source-of-truth matrix, Documentation update policy, Canonical reading path, No new docs subfolder is needed, v2_1_44.


## v2_3_15 response case policy

Backend API responses are canonical `snake_case`. HarmonyOS generated types are camelCase client-domain types, and `frontend_fixtures/harmonyos/api/CaseAdapter.ets` maps raw backend payloads before UI/store use. Do not add a parallel backend camelCase response format unless a future compatibility requirement explicitly needs it. Runtime generation logic is unchanged.
