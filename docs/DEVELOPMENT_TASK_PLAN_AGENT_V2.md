## v2_8_18_agent_today_practice_guidance_persisted_context_terminal_memory_controls

- Added terminal-only persisted context memory controls for today-practice guidance testing.
- Added `/persisted-context-load [json_payload]`, `/persisted-context-show`, and `/persisted-context-clear`.
- Loaded memory is session-only and can inject recovered user profile / active plan / routine history context into the next ordinary `今天该练什么？` turn.
- Explicit command arguments still win over terminal memory to avoid hidden debug overrides.
- Added `today_practice_guidance_persisted_context_terminal_memory_controls_contract()` and context/runtime manifest entries.
- Preserved all no-side-effect guards: no backend/local write, no SQLite connection/table/row, no LLM call from memory commands, no tool/Engine/Routine/MIDI/playback side effects.

Next recommended task: `v2_8_19_agent_today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture`.

## v2_8_10_agent_context_persistence_real_storage_adapter_design

- Added design-only Context Persistence Storage Adapter contract.
- Added `ContextPersistenceStorageAdapterDesignPayload`, summary builder, and `context_persistence_storage_adapter_design_contract()`.
- Added API routes: `GET /agent/context/persistence-storage-adapter/spec` and `POST /agent/context/persistence-storage-adapter/design-preview`.
- Added terminal command `/context-persistence-storage-adapter [json_payload]`.
- Defined future adapter interface methods: `preview_write`, `write_confirmed_context`, `read_context_snapshot`, `check_idempotency`, and `record_trace_link`.
- Mapped durable context entities to backend-long-term ownership while keeping HarmonyOS Routine session/playback/local MIDI state client-owned.
- Preserved all no-side-effect guards: no database connection, no storage write, no LLM/tool/Engine/Routine/MIDI/playback side effects.

Next recommended task: `v2_8_11_agent_context_persistence_storage_adapter_sqlite_dev_preview`.

## v2_8_9_agent_context_persistence_executor_noop_skeleton

- Added Context Persistence Executor no-op skeleton.
- Added GET /agent/context/persistence-executor-noop/spec and POST /agent/context/persistence-executor-noop/preview.
- Added CLI /context-persistence-executor-noop.
- The executor checks confirmation approval, idempotency, trace and storage-contract boundaries, but never writes storage.
- Real persistence executor remains unimplemented; no LLM/tool/Engine/Routine/MIDI/playback side effects.

Next recommended task: `v2_8_10_agent_context_persistence_real_storage_adapter_design`.

# Agent Track Development Task Plan V2


## v2_8_7_agent_routine_history_persistence_candidate_contract

- Added RoutineHistory summary save/upload persistence candidate contract.
- Added `RoutineHistoryPersistenceCandidatePayload`, summary builder, and `routine_history_persistence_candidate_contract()`.
- Added API routes: `GET /agent/routine-history/persistence-candidate/spec` and `POST /agent/routine-history/persistence-candidate/preview`.
- Added terminal command `/routine-history-persistence-candidate [json_payload]`.
- Supports `append_new_records` and `upsert_summary_batch` as preview-only operations.
- Reuses RoutineHistory context normalization to produce sanitized `PracticeHistoryContextItem` summaries and aggregate history summary.
- Drops client-only playback/MIDI fields such as `midiBase64`, `localMidiPath`, playback position, timer/raw asset state, and sensitive fields.
- Preserved candidate-only guardrails: no LLM call, no tool execution, no backend/local write, no post-session recommendation card, no Routine start, no `/accompaniment/generate`, no engine adapter, no MIDI asset, no playback.
- Added `docs/AGENT_ROUTINE_HISTORY_PERSISTENCE_CANDIDATE_CONTRACT_V2_8_7.md` and `tests/test_v2_8_7_agent_routine_history_persistence_candidate_contract.py`.

Next recommended task: `v2_8_8_agent_context_persistence_confirmation_boundary`.

## v2_8_5_agent_terminal_guidance_json_contract_hotfix

- Fixed terminal today-practice guidance UX when a configured LLM returns plain text or partial JSON instead of strict `TodayPracticeGuidanceOutput`.
- Strengthened JSON-only prompt instructions while preserving the existing 4-message prompt contract.
- Added safe display-only provider-output coercion: successful plain text becomes `fallback_without_plan` guidance with `show_guidance` only.
- Partial JSON receives safe defaults for `guidance_mode`, `recommended_focus`, `user_confirmation_required`, and `next_client_actions`.
- Preserved no-side-effect guarantees: no Routine start, no tools, no Engine adapter, no `/accompaniment/generate`, no MIDI, no playback.
- Added `tests/test_v2_8_5_agent_terminal_guidance_json_contract_hotfix.py`.

Next recommended task: `v2_8_6_agent_practice_plan_persistence_candidate_contract`.


Current baseline: `v2_8_7_agent_routine_history_persistence_candidate_contract`.

This file is the rolling plan for `feature/agent-workflow`. It owns Agent / LLM orchestration, terminal chat, tool-preview, traces, provider boundaries, controlled low-risk Agent workflows, and HarmonyOS Routine Agent action surfaces.

---

## Ownership

Allowed owner paths:

```text
src/jammate_agent/
src/jammate_api/routes/agent_routes.py
tools/*agent*
tools/*trace*
tools/*terminal*
tests/test_*agent*.py
tests/test_*trace*.py
tests/test_*tool*.py
demos/agent_fixtures/
docs/AGENT*.md
docs/DEVELOPMENT_TASK_PLAN_AGENT_V2.md
docs/CHANGELOG_AGENT.md
```

Do not modify engine generation/style/core runtime code in an Agent task.

Do not modify shared docs from the Agent branch:

```text
README.md
agent.md
VERSION
pyproject.toml
docs/ARCHITECTURE_V2.md
docs/API_CONTRACT_V2.md
docs/DEVELOPMENT_TASK_PLAN_V2.md
docs/CHANGELOG.md
frontend_fixtures/harmonyos/
```

---

## Current Agent Baseline

Official Agent runtime skeleton preserved in the integrated package:

```text
v2_7_1_agent_practice_plan_to_routine_candidate_bridge
```

Current Agent capability status:

```text
ContextPacket
→ LLM Provider Boundary
→ Tool Registry
→ Tool Invocation Preview
→ Tool Execution Confirmation
→ ToolExecutor Dry-run / No-op
→ Deterministic Workflow Descriptor Resolution
→ Controlled PracticePlan Execution
→ HarmonyOS Routine AgentActionCard
→ Runtime Skeleton Status
→ Routine-facing PracticePlan ActionCard Payload
→ Routine-facing PlaybackPrepare Guarded Payload
→ Editable RoutineConfig Prepare Payload
→ PracticePlan Block to UI-flow-agnostic Routine Candidate Bridge
```

Important retained facts:

- terminal chat is available through the Agent CLI boundary;
- LLM provider configuration remains explicit and bounded;
- tool-call preview remains validation-only until user confirmation;
- real controlled execution is currently allow-listed to `agent_practice_plan` only;
- HarmonyOS Routine can receive an ActionCard, a Routine-facing practice-plan payload, and a guarded playback-prepare setup candidate;
- no playback execution, no `/accompaniment/generate` call, no engine adapter dispatch, and no MIDI asset creation are allowed from this Agent stage.

---

## Completed Agent Milestones

```text
v2_6_2_agent_tool_execution_confirmation_gate
v2_6_3_agent_tool_executor_boundary
v2_6_4_agent_deterministic_workflow_dispatcher
v2_6_5_agent_first_controlled_tool_execution_e2e
v2_6_6_harmonyos_agent_action_contract
v2_6_7_agent_runtime_skeleton_cleanup
v2_6_8_agent_practice_plan_action_card_e2e
v2_7_0_agent_routine_config_prepare_contract
v2_7_1_agent_practice_plan_to_routine_candidate_bridge
```

---

## Current Agent Task

```text
v2_8_1_agent_user_profile_context_intake
```

Scope:

- define a UI-flow-agnostic bridge payload from `routine_practice_plan_payload` / practice-plan block data to Routine candidate data;
- support selecting a specific practice block by `block_id` or `block_index`;
- keep `frontend_flow_assumption=false` and `client_decides_presentation=true`;
- expose neutral client actions such as `present_routine_candidate`, `apply_to_current_routine`, `show_confirmation_sheet`, `add_to_routine_queue`, and `save_as_template`;
- add terminal `/practice-plan-routine-candidate` command;
- add `GET /agent/actions/practice-plan/routine-candidate/spec` and `POST /agent/actions/practice-plan/routine-candidate/prepare`;
- keep Routine start, accompaniment generation, MIDI asset creation, and playback as separate future user-confirmed actions.

Forbidden scope:

- no direct edits to `src/jammate_engine/styles/`;
- no direct edits to `src/jammate_engine/core/`;
- no changes to MIDI realization;
- no direct `/accompaniment/generate` call;
- no `agent_playback_prepare` real execution;
- no engine adapter calls;
- no MIDI asset creation;
- no shared documentation updates from the Agent branch.

---

## Recommended Next Agent Task

```text
v2_7_2_agent_session_review_action_card
```

Goal: structure post-practice review / next-step suggestions into Routine-facing recommendation cards without starting playback or generating MIDI assets.

Suggested scope:

- define `SessionReviewActionCard` payload for completed Routine sessions;
- summarize completed blocks, user notes, current tempo/style/tune, and next-step recommendations;
- expose neutral client actions such as `save_review`, `create_followup_routine_candidate`, `view_trace`, and `dismiss`;
- keep playback/generation as separate future user-confirmed actions;
- do not call `/accompaniment/generate` from Agent.

---

## Near-Term Agent Queue

1. `v2_7_2_agent_session_review_action_card` — structure post-practice review into Routine-facing recommendation cards;
2. `v2_7_3_agent_playback_prepare_execution_policy_plan` — only plan the future execution policy for playback/asset generation, still without execution;
3. `v2_7_4_agent_routine_candidate_queue_contract` — optional client-owned queue/template payloads for Routine candidates, without playback execution.

Any task that changes shared API contract docs or HarmonyOS fixtures should be moved to an integration task.

## v2_7_2_agent_routine_history_context_intake

Status: completed in Agent track.

Goal:

```text
HarmonyOS RoutineHistoryRecord summary
→ Agent PracticeHistoryContext intake
→ future ContextPacket section for user-initiated “what should I practice next?” conversations
```

Boundary:

```text
No post-session recommendation card.
No `/accompaniment/generate` call.
No engine adapter call.
No MIDI asset creation.
No playback start.
No shared docs / HarmonyOS fixture edits from Agent track.
```

Next recommended task:

```text
v2_7_3_agent_active_practice_plan_context_intake
```

Purpose: define how the current/active long-term PracticePlan enters Agent Context alongside recent Routine history, so the LLM can compare planned work against actual recent practice.

## v2_7_3_agent_context_engineering_skeleton_foundation

- Added Active PracticePlan Context Intake for backend-persisted long-term practice plans.
- Added Practice Context Assembly Policy to combine active plan, Routine history, and today constraints into context-only decision inputs.
- Added Today Practice Context E2E preview for future user-initiated “今天该练什么？” turns.
- Integrated active plan / history / assembled practice context into ContextBuilder.
- Preserved guardrails: no post-session recommendation card, no LLM call, no /accompaniment/generate, no engine adapter, no MIDI asset, no playback.

## v2_7_4_agent_today_practice_guidance_prompt_contract

- Added prompt/output contract preview for future user-initiated “今天该练什么？” guidance.
- Added `TodayPracticeGuidancePromptContractPayload`, summary builder, and spec contract.
- Added terminal `/today-practice-guidance-prompt` command.
- Added API routes: `GET /agent/context/today-practice-guidance/spec` and `POST /agent/context/today-practice-guidance/prompt-preview`.
- The contract builds provider-boundary-ready prompt messages and `TodayPracticeGuidanceOutput` schema, but does not call the LLM or create a final recommendation.
- Preserved guardrails: no post-session recommendation card, no Routine start, no `/accompaniment/generate`, no engine adapter, no MIDI asset, no playback.


## v2_7_5_agent_user_capability_map_and_intent_taxonomy

Goal: define what users can ask the LLM/Agent to do before adding more output validation or execution capability.

Scope:

```text
LLM User Capability Map
Intent Taxonomy
Allowed Action Types
Side Effect Policy
Routine-specific Agent boundaries
```

Non-goals:

```text
No LLM call
No final today-practice answer generation
No Routine start
No /accompaniment/generate call
No engine adapter call
No MIDI asset creation
No playback
No shared-doc or HarmonyOS fixture changes
```

Recommended next task:

```text
v2_7_6_agent_today_practice_guidance_output_validation
```

## v2_7_6_agent_today_practice_guidance_output_validation

Status: completed.

Goal: validate and normalize future LLM `TodayPracticeGuidanceOutput` before HarmonyOS Routine displays or acts on it.

Boundaries:

```text
No LLM call.
No tool execution.
No Routine start.
No /accompaniment/generate call.
No engine adapter call.
No MIDI asset creation.
No playback start.
No frontend UI flow assumption.
```

Next recommended task: define the actual provider-boundary E2E for today-practice guidance using the prompt contract and output validator, while still returning suggestions/candidates only.

## v2_7_7_agent_today_practice_guidance_provider_boundary_e2e

- Added TodayPracticeGuidance provider-boundary E2E contract.
- Connected prompt contract → providerResult / explicit provider call → output validation.
- Added API routes `/agent/context/today-practice-guidance/provider-boundary/spec` and `/agent/context/today-practice-guidance/provider-boundary/e2e-preview`.
- Added terminal command `/today-practice-guidance-e2e`.
- Kept all execution guards disabled: no Routine start, no `/accompaniment/generate`, no engine adapter, no MIDI asset, no playback.


## v2_7_8_agent_today_practice_guidance_action_card

Status: completed.

Goal: wrap validated today-practice guidance into a HarmonyOS Routine display ActionCard that the client can render after the user asks “今天该练什么？”.

Scope:

```text
TodayPracticeGuidance provider-boundary E2E payload
→ output validation
→ display-only ActionCard
→ recommended blocks / Routine candidates
→ client-decided presentation actions
```

Boundaries:

```text
No automatic post-session recommendation card.
No direct Routine start.
No /accompaniment/generate call.
No engine adapter call.
No MIDI asset creation.
No playback start.
No frontend UI flow assumption.
```

Recommended next task:

```text
v2_7_9_agent_today_practice_guidance_terminal_chat_e2e
```

Suggested focus: connect normal terminal user turns such as “今天该练什么？” to the context assembly + provider-boundary + validation + ActionCard flow, while still keeping all generated Routine actions as user-confirmed candidates only.

## v2_7_9_agent_today_practice_guidance_terminal_chat_e2e

Status: completed.

Goal: connect ordinary terminal user turns such as “今天该练什么？” to the existing context assembly → provider boundary → output validation → display-only ActionCard flow.

Scope:

```text
ordinary user input
→ narrow today-practice intent detection
→ TodayPracticeGuidance provider-boundary E2E
→ output validation
→ display-only Routine ActionCard
```

Boundaries:

```text
No automatic post-session recommendation card.
No direct Routine start.
No /accompaniment/generate call.
No engine adapter call.
No MIDI asset creation.
No playback start.
No frontend UI flow assumption.
```

Recommended next task:

```text
v2_8_0_agent_context_and_guidance_skeleton_cleanup
```

Suggested focus: after v2_7_3 through v2_7_9, do a small Agent context/guidance skeleton cleanup pass to remove naming duplication, align docs, inspect API route grouping, and prepare for concrete user-facing Agent features.

## v2_8_0_agent_context_and_guidance_skeleton_cleanup

Status: completed.

Goal: close the first context/guidance skeleton pass after `v2_7_3` through `v2_7_9` by exposing a single read-only stage registry and guard surface.

Scope:

```text
v2_7_3 context engineering skeleton
→ v2_7_4 prompt contract
→ v2_7_5 capability map / intent taxonomy
→ v2_7_6 output validation
→ v2_7_7 provider-boundary E2E
→ v2_7_8 display-only ActionCard
→ v2_7_9 terminal chat E2E
→ v2_8_0 cleanup/status contract
```

Boundaries:

```text
No Routine end recommendation card.
No LLM call from cleanup.
No tool execution.
No Routine start.
No /accompaniment/generate call.
No engine adapter call.
No MIDI asset creation.
No playback start.
No frontend UI flow assumption.
No shared-document or HarmonyOS fixture changes.
```

Recommended next task:

```text
v2_8_1_agent_user_profile_context_intake
```

Suggested focus: define how durable user practice preferences, current goals, comfortable tempo ranges, and focus areas enter ContextPacket without turning them into execution actions.


## v2_8_1_agent_user_profile_context_intake

Status: completed in Agent track.

Goal:

```text
UserPracticeProfile
→ UserPracticeProfileContext intake
→ ContextPacket learner_context.user_practice_profile_context
→ assembled_practice_context profile_summary / decision input
```

Added surfaces:

```text
GET  /agent/context/user-practice-profile/spec
POST /agent/context/user-practice-profile/intake
/user-practice-profile-context [json_payload]
```

Scope completed:

- Added `UserPracticeProfileContextIntakePayload`, summary builder, and spec contract.
- Normalizes durable practice-profile fields: current goal, preferred styles, focus areas, skill focus, common tunes, comfort tempo ranges, preferred session minutes, avoid list, saved routine preferences, practice-mode preference, and updated timestamp.
- Supports camelCase and snake_case payloads from HarmonyOS/backend/client callers.
- Normalizes tempo ranges to `min/max`; reversed ranges become swapped warnings, invalid ranges are skipped with warnings.
- Drops sensitive or client-only fields before Agent context: API keys, tokens, passwords, local MIDI paths, MIDI base64, precise location, payment info, playback internals, and hidden chain-of-thought.
- Injects profile context into `ContextBuilder` and `learner_context.user_practice_profile_context`.
- Extends practice context assembly so `assembled_practice_context` can carry `user_practice_profile_context`, `profile_summary`, and `llm_decision_inputs.user_practice_profile_input_available`.
- Preserves the v2_8_1 boundary: context intake only; no LLM call, no tool execution, no storage write, no Routine start, no `/accompaniment/generate`, no engine adapter, no MIDI asset, no playback.

Design judgment:

```text
UserPracticeProfile is not a recommendation rule engine.
It is durable user context for later profile-aware guidance.
```

Recommended next Agent task:

```text
v2_8_2_agent_practice_context_storage_boundary_contract
```

Goal: define which practice-context objects are owned by HarmonyOS local storage, backend long-term storage, Agent trace, and temporary request payloads, without implementing a full database yet.

## v2_8_2_agent_practice_context_storage_boundary_contract

Status: completed in Agent track.

Scope:

```text
Practice context storage/source-of-truth boundary contract only.
No database implementation.
No backend write.
No HarmonyOS local write.
No LLM call.
No tool execution.
No Routine start.
No /accompaniment/generate.
No engine adapter.
No MIDI asset.
No playback.
```

Implemented surfaces:

```text
GET  /agent/context/storage-boundary/spec
POST /agent/context/storage-boundary/preview
/practice-context-storage-boundary [json_payload]
docs/AGENT_PRACTICE_CONTEXT_STORAGE_BOUNDARY_V2_8_2.md
```

Boundary categories:

```text
harmonyos_local_only
backend_long_term_context
request_ephemeral_context
agent_trace_context
never_store_or_contextualize
```

Key judgment:

```text
ContextBuilder can assemble normalized context sections, but it must not become a storage layer.
HarmonyOS owns live Routine/playback/UI state.
Backend should eventually own durable compact practice-context summaries.
This version only defines the contract and writes nothing.
```

Recommended next task:

```text
v2_8_3_agent_today_practice_guidance_profile_aware_e2e
```


## v2_8_3_agent_today_practice_guidance_profile_aware_e2e

Status: completed in Agent track.

Scope:

```text
Profile-aware TodayPracticeGuidance E2E only.
UserPracticeProfileContext is soft personalization context.
No recommendation rule engine.
No database write.
No LLM call by default.
No tool execution.
No Routine start.
No /accompaniment/generate.
No engine adapter.
No MIDI asset.
No playback.
```

Implemented surfaces:

```text
GET  /agent/context/today-practice-guidance/profile-aware/spec
POST /agent/context/today-practice-guidance/profile-aware/e2e-preview
/today-practice-guidance-profile-aware [json_payload]
docs/AGENT_TODAY_PRACTICE_GUIDANCE_PROFILE_AWARE_E2E_V2_8_3.md
```

Key judgment:

```text
UserPracticeProfileContext can affect focus/style/tempo/avoid/practice-mode wording as soft context,
but active PracticePlan and recent RoutineHistory remain primary decision inputs.
```

Recommended next task:

```text
v2_8_4_agent_practice_plan_persistence_candidate_contract
```

Goal: design save/update PracticePlan as a previewable, user-confirmed candidate action, still without implementing full database persistence unless explicitly requested.

## v2_8_4_agent_terminal_llm_provider_compatibility_hotfix

Status: completed in Agent track.

Reason:

```text
Real terminal LLM testing exposed two usability/compatibility bugs:
1. python -m terminal_chat setup/doctor ignored argv because main() did not forward sys.argv[1:].
2. Some OpenAI-compatible providers rejected role="developer" in Chat Completions payloads.
```

Implemented:

```text
src/jammate_agent/cli/terminal_chat.py
src/jammate_agent/core/llm_provider.py
tests/test_v2_8_4_agent_terminal_llm_provider_compatibility_hotfix.py
docs/AGENT_TERMINAL_LLM_PROVIDER_COMPATIBILITY_HOTFIX_V2_8_4.md
```

Boundary:

```text
Terminal hotfix only.
No recommendation logic expansion.
No storage implementation.
No Engine music-generation changes.
No pattern / voicing / expression / pedal changes.
No demo MIDI changes.
```

Recommended next task:

```text
v2_8_5_agent_practice_plan_persistence_candidate_contract
```

Goal: design save/update PracticePlan as a previewable, user-confirmed candidate action, still without implementing full database persistence unless explicitly requested.

## v2_8_11_agent_context_persistence_storage_adapter_sqlite_dev_preview

Status: completed in Agent track.

Scope:

```text
Dev-only SQLite/fixture adapter preview.
No real SQLite write.
No database connection.
No schema migration applied.
No HarmonyOS local write.
No LLM call.
No tool execution.
No Routine start.
No /accompaniment/generate.
No engine adapter.
No MIDI asset.
No playback.
```

Implemented surfaces:

```text
GET  /agent/context/persistence-sqlite-dev-preview/spec
POST /agent/context/persistence-sqlite-dev-preview/preview
/context-persistence-sqlite-dev-preview [json_payload]
docs/AGENT_CONTEXT_PERSISTENCE_SQLITE_DEV_PREVIEW_V2_8_11.md
```

Key judgment:

```text
v2_8_11 should expose the concrete dev storage shape and roundtrip boundaries
(schema/idempotency/trace/snapshot) before enabling even local SQLite writes.
This keeps persistence work inspectable and prevents accidentally introducing
backend storage side effects into the Agent route.
```

Recommended next task:

```text
v2_8_12_agent_context_persistence_dev_sqlite_explicit_write_gate
```

Goal: define an explicit dev-only write gate and config-path contract for a future SQLite adapter, still requiring confirmation, idempotency, trace-link, redaction, and storage-boundary checks.

## v2_8_12_agent_context_persistence_dev_sqlite_explicit_write_gate

Status: completed in Agent track.

Scope:

```text
Explicit dev-only SQLite write gate and config-path contract.
No real SQLite write.
No database connection.
No schema migration applied.
No HarmonyOS local write.
No LLM call.
No tool execution.
No Routine start.
No /accompaniment/generate.
No engine adapter.
No MIDI asset.
No playback.
```

Implemented surfaces:

```text
GET  /agent/context/persistence-dev-sqlite-write-gate/spec
POST /agent/context/persistence-dev-sqlite-write-gate/preview
/context-persistence-dev-sqlite-write-gate [json_payload]
docs/AGENT_CONTEXT_PERSISTENCE_DEV_SQLITE_WRITE_GATE_V2_8_12.md
```

Key judgment:

```text
v2_8_12 does not implement SQLite writes. It defines the explicit switch and
checks a future dev writer must pass: user approval, confirmation status,
idempotency key, trace link, dev config path, redaction, storage-boundary, and
schema-preview acceptance.
```

Recommended next task:

```text
v2_8_13_agent_context_persistence_dev_sqlite_fixture_write_dry_run
```

Goal: add a fixture/dry-run writer shape that simulates the transaction and read-back contract while still avoiding durable backend writes by default.

## v2_8_13_agent_context_persistence_dev_sqlite_fixture_write_dry_run

Status: completed in Agent track.

Scope:

```text
Dev SQLite fixture writer dry-run.
No real SQLite write.
No database connection.
No schema migration applied.
No transaction commit.
No HarmonyOS local write.
No LLM call.
No tool execution.
No Routine start.
No /accompaniment/generate.
No engine adapter.
No MIDI asset.
No playback.
```

Implemented surfaces:

```text
GET  /agent/context/persistence-dev-sqlite-fixture-write-dry-run/spec
POST /agent/context/persistence-dev-sqlite-fixture-write-dry-run/preview
/context-persistence-dev-sqlite-fixture-write-dry-run [json_payload]
docs/AGENT_CONTEXT_PERSISTENCE_DEV_SQLITE_FIXTURE_WRITE_DRY_RUN_V2_8_13.md
```

Key judgment:

```text
v2_8_13 should still not write SQLite. It previews the future writer shape:
transaction begin/commit/rollback, idempotency lookup/insert, sanitized row plan,
trace metadata link, and read-back snapshot. This allows the persistence chain to
be reviewed end-to-end before any durable backend write is enabled.
```

Recommended next task:

```text
v2_8_14_agent_context_persistence_dev_sqlite_fixture_store_explicit_opt_in
```

Goal: if desired, introduce a dev-only explicit opt-in fixture store while preserving confirmation, idempotency, trace-link, redaction, storage-boundary, and no Engine side effects.

## v2_8_14_agent_context_persistence_dev_sqlite_fixture_store_explicit_opt_in

目标：在 v2_8_13 dry-run writer shape 之后，新增 dev-only 显式 opt-in fixture store。

完成内容：

```text
GET  /agent/context/persistence-dev-sqlite-fixture-store/spec
POST /agent/context/persistence-dev-sqlite-fixture-store/preview
CLI  /context-persistence-dev-sqlite-fixture-store [json_payload]
docs/AGENT_CONTEXT_PERSISTENCE_DEV_SQLITE_FIXTURE_STORE_V2_8_14.md
tests/test_v2_8_14_agent_context_persistence_dev_sqlite_fixture_store_explicit_opt_in.py
```

边界：

```text
只允许显式 opt-in 后写 dev fixture JSONL
不写 SQLite / backend database
不写 HarmonyOS local state
不调用 LLM
不执行 tool
不启动 Routine
不调用 /accompaniment/generate
不调用 Engine adapter
不生成 MIDI
不播放
```

下一步建议：

```text
v2_8_15_agent_context_persistence_dev_fixture_readback_and_replay_preview
```

## v2_8_16_agent_context_persistence_profile_plan_history_snapshot_context_intake

Status: completed in Agent track.

Implemented surfaces:

```text
GET  /agent/context/persistence-snapshot-context-intake/spec
POST /agent/context/persistence-snapshot-context-intake/preview
CLI  /context-persistence-snapshot-context-intake [json_payload]
docs/AGENT_CONTEXT_PERSISTENCE_SNAPSHOT_CONTEXT_INTAKE_V2_8_16.md
tests/test_v2_8_16_agent_context_persistence_profile_plan_history_snapshot_context_intake.py
```

ContextBuilder now accepts:

```text
context_persistence_snapshot_context_intake=<context_packet_section>
```

and can inject recovered sections into:

```text
learner_context.user_practice_profile_context
learner_context.active_practice_plan_context
learner_context.routine_history_context
learner_context.assembled_practice_context
learner_context.context_persistence_snapshot_context_intake
```

Boundary:

```text
No backend database write.
No HarmonyOS local write.
No SQLite connection/table/row.
No LLM call.
No tool execution.
No Routine start.
No /accompaniment/generate.
No Engine adapter call.
No MIDI asset.
No playback.
No post-session recommendation card.
```

Next recommended task:

```text
v2_8_17_agent_today_practice_guidance_persisted_context_recovery_e2e
```

## v2_8_17_agent_today_practice_guidance_persisted_context_recovery_e2e

Status: completed in this package.

Goal: bridge recovered persisted snapshot context into the profile-aware TodayPracticeGuidance E2E chain.

Scope:
- read-only snapshot/context recovery preview
- ContextBuilder-ready profile / active plan / routine history sections
- display-only guidance/action-card output
- terminal and API preview surfaces

Out of scope:
- real database persistence
- HarmonyOS local writes
- Routine start
- accompaniment generation
- engine adapter dispatch
- MIDI asset creation
- playback

Recommended next task: `v2_8_18_agent_today_practice_guidance_persisted_context_terminal_memory_controls`.

## v2_8_19_agent_today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture

Status: completed in Agent track.

Goal: map terminal persisted-context memory into a HarmonyOS-facing debug fixture preview so frontend debug screens can test recovered-context today-practice guidance without repeatedly pasting large JSON payloads.

Implemented surfaces:

```text
GET  /agent/context/today-practice-guidance/terminal-memory-harmonyos-debug-fixture/spec
POST /agent/context/today-practice-guidance/terminal-memory-harmonyos-debug-fixture/preview
CLI  /persisted-context-harmonyos-debug-fixture [json_payload]
docs/AGENT_TODAY_PRACTICE_GUIDANCE_TERMINAL_MEMORY_TO_HARMONYOS_DEBUG_FIXTURE_V2_8_19.md
tests/test_v2_8_19_agent_today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture.py
```

Boundary:

```text
No backend database write.
No HarmonyOS local write by Agent.
No SQLite connection/table/row.
No LLM call by fixture builder.
No tool execution.
No Routine start.
No /accompaniment/generate.
No Engine adapter call.
No MIDI asset.
No playback.
No post-session recommendation card.
No change to frontend_fixtures/harmonyos.
```

Next recommended task:

```text
v2_8_20_agent_harmonyos_debug_fixture_roundtrip_terminal_e2e
```

## v2_8_20_agent_harmonyos_debug_fixture_roundtrip_terminal_e2e

Status: completed in Agent track.

Goal: verify that a HarmonyOS debug fixture preview can roundtrip back into the Agent persisted-context recovery guidance preview.

Implemented surfaces:

```text
GET  /agent/context/today-practice-guidance/harmonyos-debug-fixture-roundtrip/spec
POST /agent/context/today-practice-guidance/harmonyos-debug-fixture-roundtrip/e2e-preview
CLI  /harmonyos-debug-fixture-roundtrip [json_payload]
docs/AGENT_HARMONYOS_DEBUG_FIXTURE_ROUNDTRIP_TERMINAL_E2E_V2_8_20.md
tests/test_v2_8_20_agent_harmonyos_debug_fixture_roundtrip_terminal_e2e.py
```

Boundary:

```text
No backend database write.
No HarmonyOS local write by Agent.
No SQLite connection/table/row.
No LLM call by roundtrip preview.
No tool execution.
No Routine start.
No /accompaniment/generate.
No Engine adapter call.
No MIDI asset.
No playback.
No post-session recommendation card.
No change to frontend_fixtures/harmonyos.
```

Next recommended task:

```text
v2_8_21_agent_harmonyos_debug_fixture_api_request_pack
```

## v2_8_21_agent_harmonyos_debug_fixture_api_request_pack

目标：把 persisted-context guidance debug fixture 链路整理成鸿蒙前端可直接联调的 API request pack。

范围：

```text
GET  /agent/context/today-practice-guidance/harmonyos-debug-fixture-api-request-pack/spec
POST /agent/context/today-practice-guidance/harmonyos-debug-fixture-api-request-pack/preview
CLI  /harmonyos-debug-fixture-api-request-pack [json_payload]
```

非目标：不写数据库、不改 HarmonyOS fixture、不调用 LLM、不执行 tool、不启动 Routine、不调用 Engine。

下一步建议：`v2_8_22_agent_terminal_chat_product_smoke_polish`。


## v2_8_22_agent_terminal_chat_product_smoke_polish

Status: completed in Agent track.

Goal: polish the real terminal-chat smoke-test experience before v2_8 phase handoff.

Implemented surfaces:

```text
GET  /agent/context/today-practice-guidance/terminal-product-smoke/spec
POST /agent/context/today-practice-guidance/terminal-product-smoke/preview
CLI  /terminal-product-smoke [json_payload]
docs/AGENT_TERMINAL_CHAT_PRODUCT_SMOKE_POLISH_V2_8_22.md
tests/test_v2_8_22_agent_terminal_chat_product_smoke_polish.py
```

Boundary:

```text
No backend database write.
No HarmonyOS local write by Agent.
No SQLite connection/table/row.
No LLM call by smoke preview.
No tool execution.
No Routine start.
No /accompaniment/generate.
No Engine adapter call.
No MIDI asset.
No playback.
No post-session recommendation card.
No change to frontend_fixtures/harmonyos.
```

Next recommended task:

```text
v2_8_23_agent_v2_8_phase_cleanup_regression_handoff
```

## v2_8_23_agent_v2_8_phase_cleanup_regression_handoff

Status: completed in Agent track.

Goal: close the Agent v2_8 context/guidance/persistence/HarmonyOS-debug-fixture phase with a handoff report, regression checklist, and next-phase boundary.

Implemented surfaces:

```text
GET  /agent/context/today-practice-guidance/v2-8-phase-handoff/spec
POST /agent/context/today-practice-guidance/v2-8-phase-handoff/preview
CLI  /v2-8-phase-handoff [json_payload]
docs/AGENT_V2_8_PHASE_CLEANUP_REGRESSION_HANDOFF_V2_8_23.md
tests/test_v2_8_23_agent_v2_8_phase_cleanup_regression_handoff.py
```

Boundary:

```text
No backend database write.
No HarmonyOS local write by Agent.
No SQLite connection/table/row by handoff preview.
No LLM call by handoff preview.
No tool execution.
No Routine start.
No /accompaniment/generate.
No Engine adapter call.
No MIDI asset.
No playback.
No post-session recommendation card.
No change to frontend_fixtures/harmonyos.
No Engine music generation change.
No shared document change in Agent track.
```

Next phase recommendation:

```text
Stop expanding v2_8. Move to integration handoff or v2_9_x Agent Persistence Implementation planning.
```

## v2_9_0_agent_context_persistence_sqlite_backend_store

Status: completed in Agent track.

Goal: start the v2_9_x Agent Persistence Implementation phase by adding an explicit opt-in backend SQLite store for Agent long-term context snapshots.

Implemented surfaces:

```text
GET  /agent/context/persistence-sqlite-backend-store/spec
POST /agent/context/persistence-sqlite-backend-store/execute
CLI  /context-persistence-sqlite-backend-store [json_payload]
docs/AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_STORE_V2_9_0.md
tests/test_v2_9_0_agent_context_persistence_sqlite_backend_store.py
```

Required write gates:

```text
backendPersistenceEnabled=true
executeBackendPersistence=true
userDecision=approved
confirmationStatus=user_approved_future_executor_required
environment in dev/local_dev/test
safe sqliteDbPath ending .db/.sqlite/.sqlite3
traceId present
idempotencyKey present or derived
storageBoundaryCheckPassed=true
redactionCheckPassed=true
schemaPreviewAccepted=true
```

Boundary:

```text
Allows real backend SQLite context snapshot write only after explicit gates.
No HarmonyOS local write by Agent.
No Routine start.
No post-session recommendation card.
No /accompaniment/generate.
No Engine adapter call.
No MIDI asset.
No playback.
No LLM call by persistence route/CLI.
No tool execution.
No production persistence enablement.
No Engine music generation change.
No frontend_fixtures/harmonyos change.
No shared documentation/version file change in Agent track.
```

Next recommended Agent task:

```text
v2_9_1_agent_context_persistence_sqlite_backend_readback_context_recovery
```

## v2_9_1_agent_context_persistence_sqlite_backend_readback_context_recovery

Status: completed in Agent track.

Goal: read records written by the v2_9_0 SQLite backend store and convert them into the same persisted-context recovery packet shape used by today-practice guidance.

Implemented surfaces:

```text
GET  /agent/context/persistence-sqlite-backend-readback-context-recovery/spec
POST /agent/context/persistence-sqlite-backend-readback-context-recovery/preview
CLI  /context-persistence-sqlite-backend-readback-context-recovery [json_payload]
docs/AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_READBACK_CONTEXT_RECOVERY_V2_9_1.md
tests/test_v2_9_1_agent_context_persistence_sqlite_backend_readback_context_recovery.py
```

Required readback gates:

```text
backendReadbackEnabled=true
executeBackendReadback=true
environment in dev/local_dev/test
safe sqliteDbPath ending .db/.sqlite/.sqlite3
optional idempotencyKey / traceId / userId / candidate filters
no forbidden client-local/MIDI/API-key fields
```

Boundary:

```text
Allows read-only backend SQLite context recovery from existing persistence records.
No backend SQLite write.
No SQLite table creation.
No HarmonyOS local write by Agent.
No Routine start.
No post-session recommendation card.
No /accompaniment/generate.
No Engine adapter call.
No MIDI asset.
No playback.
No LLM call by readback route/CLI.
No tool execution.
No production persistence enablement.
No Engine music generation change.
No frontend_fixtures/harmonyos change.
No shared documentation/version file change in Agent track.
```

Next recommended Agent task:

```text
v2_9_2_agent_context_persistence_sqlite_backend_today_guidance_recovery_e2e
```

## v2_9_2_agent_context_persistence_sqlite_backend_today_guidance_recovery_e2e

Status: completed in Agent track.

Goal: compose the v2_9_1 read-only SQLite backend context recovery with the existing v2_8_17 today-practice guidance persisted-context recovery, producing a display-only guidance preview from real backend persistence records.

Implemented surfaces:

```text
GET  /agent/context/persistence-sqlite-backend-today-guidance-recovery-e2e/spec
POST /agent/context/persistence-sqlite-backend-today-guidance-recovery-e2e/preview
CLI  /context-persistence-sqlite-backend-today-guidance-recovery-e2e [json_payload]
docs/AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_TODAY_GUIDANCE_RECOVERY_E2E_V2_9_2.md
tests/test_v2_9_2_agent_context_persistence_sqlite_backend_today_guidance_recovery_e2e.py
```

Composition flow:

```text
v2_9_0 SQLite backend store
        ↓
v2_9_1 read-only SQLite backend context recovery
        ↓
ContextBuilder-ready contextPersistenceSnapshotContextIntake
        ↓
v2_8_17 persisted-context today-practice guidance recovery
        ↓
display-only guidance / Routine candidate preview
```

Boundary:

```text
Allows read-only backend SQLite context recovery after explicit gates.
Allows display-only today-practice guidance preview from recovered context.
No backend SQLite write.
No SQLite table creation.
No HarmonyOS local write by Agent.
No Routine start.
No post-session recommendation card.
No /accompaniment/generate.
No Engine adapter call.
No MIDI asset.
No playback.
No tool execution.
No Engine music generation change.
No frontend_fixtures/harmonyos change.
No shared documentation/version file change in Agent track.
```

Next recommended Agent task:

```text
v2_9_3_agent_context_persistence_sqlite_backend_terminal_memory_autoload_preview
```

## v2_9_3_agent_context_persistence_sqlite_backend_terminal_memory_autoload_preview

Status: completed in Agent track.

Goal: let terminal chat explicitly read SQLite backend context records into current session memory so a following ordinary “今天该练什么” turn can reuse recovered persisted context without manually pasting the recovery packet.

Implemented surfaces:

```text
GET  /agent/context/persistence-sqlite-backend-terminal-memory-autoload-preview/spec
POST /agent/context/persistence-sqlite-backend-terminal-memory-autoload-preview/preview
CLI  /persisted-context-autoload-sqlite [json_payload]
CLI  /context-persistence-sqlite-backend-terminal-memory-autoload-preview [json_payload]
docs/AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_TERMINAL_MEMORY_AUTOLOAD_PREVIEW_V2_9_3.md
tests/test_v2_9_3_agent_context_persistence_sqlite_backend_terminal_memory_autoload_preview.py
```

Composition flow:

```text
v2_9_0 SQLite backend store
        ↓
v2_9_1 read-only SQLite backend context recovery
        ↓
terminal session-memory preview compatible with v2_8_18
        ↓
CLI-local TerminalChatSession.persisted_context_memory
        ↓
ordinary “今天该练什么” terminal turn reuses loaded memory
```

Boundary:

```text
Allows read-only backend SQLite context recovery after explicit gates.
Allows CLI-only in-process session memory loading.
API surface remains preview-only and does not mutate server-side memory.
No backend SQLite write.
No SQLite table creation.
No HarmonyOS local write by Agent.
No Routine start.
No post-session recommendation card.
No /accompaniment/generate.
No Engine adapter call.
No MIDI asset.
No playback.
No tool execution.
No Engine music generation change.
No frontend_fixtures/harmonyos change.
No shared documentation/version file change in Agent track.
```

Next recommended Agent task:

```text
v2_9_4_agent_context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke
```

## v2_9_4_agent_context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke

Status: completed in Agent track.

Goal: provide a compact terminal smoke chain that verifies real backend persistence can write a context snapshot into SQLite, autoload it into current terminal session memory, and immediately preview a normal “今天该练什么” response from that recovered memory.

Implemented surfaces:

```text
GET  /agent/context/persistence-sqlite-backend-terminal-memory-to-guidance-smoke/spec
POST /agent/context/persistence-sqlite-backend-terminal-memory-to-guidance-smoke/preview
CLI  /sqlite-memory-guidance-smoke [json_payload]
CLI  /context-persistence-sqlite-backend-terminal-memory-to-guidance-smoke [json_payload]
docs/AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_TERMINAL_MEMORY_TO_GUIDANCE_SMOKE_V2_9_4.md
tests/test_v2_9_4_agent_context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke.py
```

Composition flow:

```text
v2_9_0 SQLite backend store
        ↓ explicit backendPersistenceEnabled / executeBackendPersistence / user approval gates
v2_9_3 terminal memory autoload preview
        ↓ CLI-local TerminalChatSession.persisted_context_memory
ordinary “今天该练什么” terminal guidance turn
        ↓
display-only persisted-context guidance preview
```

Boundary:

```text
Allows SQLite backend write only through v2_9_0 explicit opt-in gates.
Allows read-only backend SQLite context recovery after explicit readback gates.
Allows CLI-only in-process session memory loading.
Allows display-only today-practice guidance preview from loaded terminal memory.
API surface remains preview-oriented and does not mutate server-side memory.
No HarmonyOS local write by Agent.
No Routine start.
No post-session recommendation card.
No /accompaniment/generate.
No Engine adapter call.
No MIDI asset.
No playback.
No tool execution.
No Engine music generation change.
No frontend_fixtures/harmonyos change.
No shared documentation/version file change in Agent track.
```

Next recommended Agent task:

```text
v2_9_5_agent_context_persistence_sqlite_backend_api_memory_debug_pack
```


## v2_9_5_agent_context_persistence_sqlite_backend_api_memory_debug_pack

- Added API debug pack for the v2_9_0 → v2_9_4 SQLite backend persistence/readback/memory/guidance surfaces.
- Added `GET /agent/context/persistence-sqlite-backend-api-memory-debug-pack/spec`.
- Added `POST /agent/context/persistence-sqlite-backend-api-memory-debug-pack/preview`.
- Added terminal commands `/sqlite-api-memory-debug-pack [json_payload]` and `/context-persistence-sqlite-backend-api-memory-debug-pack [json_payload]`.
- Added `docs/AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_API_MEMORY_DEBUG_PACK_V2_9_5.md`.
- Added tests for contract/spec metadata, core route catalog/request examples/response paths, redaction, API preview no-side-effect behavior, terminal command output, TerminalChatSession no memory mutation, manifest exposure, and Agent/Engine boundary.
- The debug pack is preview-only: it does not call packaged routes, open SQLite, write/read SQLite, mutate server memory, call LLM, execute tools, start Routine, call `/accompaniment/generate`, call Engine, create MIDI, start playback, or create a post-session recommendation card.
- The pack includes frontend-safe notes clarifying that API autoload is preview-only and TerminalChatSession memory loading remains CLI-local.

Recommended next Agent task:

```text
v2_9_6_agent_context_persistence_sqlite_backend_harmonyos_api_fixture_pack
```

## v2_9_6_agent_context_persistence_sqlite_backend_harmonyos_api_fixture_pack

Status: completed in Agent track.

Goal: package v2_9 SQLite backend persistence/readback/guidance API fixtures for HarmonyOS联调 while avoiding shared integration-file conflicts.

Implemented surfaces:

```text
GET  /agent/context/persistence-sqlite-backend-harmonyos-api-fixture-pack/spec
POST /agent/context/persistence-sqlite-backend-harmonyos-api-fixture-pack/preview
CLI  /sqlite-harmonyos-api-fixture-pack [json_payload]
CLI  /context-persistence-sqlite-backend-harmonyos-api-fixture-pack [json_payload]
docs/AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_HARMONYOS_API_FIXTURE_PACK_V2_9_6.md
tests/test_v2_9_6_agent_context_persistence_sqlite_backend_harmonyos_api_fixture_pack.py
```

Composition flow:

```text
v2_9_5 API memory debug pack
        ↓ reuse route catalog / request examples
HarmonyOS API fixture pack
        ↓ copyable request examples + response assertions + ArkTS fetch sketch
frontend/backend manual联调
```

Boundary:

```text
Preview-only pack generation.
No SQLite connection/read/write by the fixture pack itself.
No packaged route execution.
No API/server memory mutation.
No TerminalChatSession memory write.
No frontend_fixtures/harmonyos write.
No HarmonyOS local write.
No LLM call.
No tool execution.
No Routine start.
No post-session recommendation card.
No /accompaniment/generate.
No Engine adapter call.
No MIDI asset.
No playback.
No Engine music generation change.
No shared documentation/version file change in Agent track.
```

Next recommended Agent task:

```text
v2_9_7_agent_context_persistence_sqlite_backend_api_error_shape_matrix
```

## v2_9_7_agent_context_persistence_sqlite_backend_api_error_shape_matrix

Status: completed in Agent track.

Goal: stabilize the SQLite backend persistence API error/blocked response shapes so HarmonyOS and backend联调 can show clear debug states instead of treating expected gate blocks as unknown failures.

Implemented surfaces:

```text
GET  /agent/context/persistence-sqlite-backend-api-error-shape-matrix/spec
POST /agent/context/persistence-sqlite-backend-api-error-shape-matrix/preview
CLI  /sqlite-api-error-shape-matrix [json_payload]
CLI  /context-persistence-sqlite-backend-api-error-shape-matrix [json_payload]
docs/AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_API_ERROR_SHAPE_MATRIX_V2_9_7.md
tests/test_v2_9_7_agent_context_persistence_sqlite_backend_api_error_shape_matrix.py
```

Covered scenarios:

```text
missing_write_gate
invalid_sqlite_db_path
empty_readback
idempotent_replay
malformed_payload
```

Boundary:

```text
Preview-only matrix generation.
No packaged route execution.
No SQLite connection/read/write by the matrix itself.
No API/server memory mutation.
No TerminalChatSession memory write.
No frontend_fixtures/harmonyos write.
No HarmonyOS local write.
No LLM call.
No tool execution.
No Routine start.
No post-session recommendation card.
No /accompaniment/generate.
No Engine adapter call.
No MIDI asset.
No playback.
No Engine music generation change.
No shared documentation/version file change in Agent track.
```

Next recommended Agent task:

```text
v2_9_8_agent_context_persistence_sqlite_backend_harmonyos_error_fixture_pack
```

## v2_9_8_agent_context_persistence_sqlite_backend_harmonyos_error_fixture_pack

Status: completed in Agent track.

Goal: translate the v2_9_7 SQLite backend API error/blocked shape matrix into HarmonyOS-facing bad-request fixtures, UI/debug messages, retry policies, and response-field assertions for frontend/backend联调.

Implemented surfaces:

```text
GET  /agent/context/persistence-sqlite-backend-harmonyos-error-fixture-pack/spec
POST /agent/context/persistence-sqlite-backend-harmonyos-error-fixture-pack/preview
CLI  /sqlite-harmonyos-error-fixture-pack [json_payload]
CLI  /context-persistence-sqlite-backend-harmonyos-error-fixture-pack [json_payload]
docs/AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_HARMONYOS_ERROR_FIXTURE_PACK_V2_9_8.md
tests/test_v2_9_8_agent_context_persistence_sqlite_backend_harmonyos_error_fixture_pack.py
```

Pack content:

```text
bad_request_examples
expected_ui_debug_messages
retry_policy_catalog
response_field_assertion_catalog
curlBadRequestExamples
ArkTS handling sketch
frontend-safe contract notes
```

Covered scenarios:

```text
missing_write_gate
invalid_sqlite_db_path
empty_readback
idempotent_replay
malformed_payload
```

Boundary:

```text
Preview-only fixture generation.
No packaged route execution.
No SQLite connection/read/write by the pack itself.
No API/server memory mutation.
No TerminalChatSession memory write.
No frontend_fixtures/harmonyos write.
No HarmonyOS local write.
No LLM call.
No tool execution.
No Routine start.
No post-session recommendation card.
No /accompaniment/generate.
No Engine adapter call.
No MIDI asset.
No playback.
No Engine music generation change.
No shared documentation/version file change in Agent track.
```

Next recommended Agent task:

```text
v2_9_9_agent_context_persistence_sqlite_backend_handoff_completion_pack
```
