

## v2_10_5_agent_harmonyos_today_guidance_api_contract_alignment

- Added HarmonyOS-facing API contract alignment for the usable Agent loop.
- Added `GET /agent/harmonyos/today-guidance-api-contract-alignment/spec`.
- Added `POST /agent/harmonyos/today-guidance-api-contract-alignment/preview`.
- Added product wrapper route `POST /agent/harmonyos/today-practice-guidance/preview`, reusing v2_10_2 usable today-practice guidance.
- Added product wrapper route `POST /agent/harmonyos/routine-completion-record/execute`, reusing v2_10_3 Routine completion record persistence.
- Normalized HarmonyOS responses to `{ok, code, message, data, debug, safety}` with camelCase data/debug fields.
- Kept internal payloads available only under optional debug payloads; product clients should read `data` and `safety`.
- Preserved boundaries: today guidance preview is read/display-only; completion record execute may write backend SQLite only after explicit client confirmation; neither route writes HarmonyOS local state, starts Routine, calls Engine, creates MIDI, starts playback, or creates post-session recommendation cards.
- Added terminal `/harmonyos-today-guidance-api-contract [json_payload]` for contract inspection.
- Added `docs/AGENT_HARMONYOS_TODAY_GUIDANCE_API_CONTRACT_ALIGNMENT_V2_10_5.md`.
- Added `tests/test_v2_10_5_agent_harmonyos_today_guidance_api_contract_alignment.py`.

Recommended next Agent / integration task:

```text
integration_handoff_or_v2_10_6_agent_harmonyos_contract_smoke_docs
```
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

# Agent Track Changelog


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

This file records Agent-track changes to reduce conflicts in the global `docs/CHANGELOG.md`.

---


## v2_8_1_agent_user_profile_context_intake

- Added UserPracticeProfile context intake contract for durable learner goals/preferences.
- Added `UserPracticeProfileContextIntakePayload`, summary builder, and `user_practice_profile_context_intake_contract()`.
- Added API routes: `GET /agent/context/user-practice-profile/spec` and `POST /agent/context/user-practice-profile/intake`.
- Added terminal command `/user-practice-profile-context [json_payload]`.
- Integrated `user_practice_profile_context` into `ContextBuilder`, `learner_context`, practice context assembly, context/runtime manifests, and today-practice decision inputs.
- Normalizes camelCase/snake_case fields, comfort tempo ranges, preferred session minutes, and LLM-facing profile summary.
- Drops sensitive/client-only fields such as API keys, tokens, passwords, local MIDI paths, MIDI base64, precise location, payment info, playback internals, and hidden chain-of-thought.
- Preserved all guards: no LLM call, no tool execution, no storage write, no Routine start, no `/accompaniment/generate`, no engine adapter, no MIDI asset, no playback.

## v2_7_1 — Agent PracticePlan to Routine Candidate Bridge

- Added UI-flow-agnostic bridge from practice-plan block data to Routine candidate payloads.
- Added `PracticePlanToRoutineCandidateBridgePayload` and `practice_plan_to_routine_candidate_bridge_contract()`.
- Added terminal `/practice-plan-routine-candidate` command.
- Added `GET /agent/actions/practice-plan/routine-candidate/spec` and `POST /agent/actions/practice-plan/routine-candidate/prepare`.
- Payload exposes `frontend_flow_assumption=false` and `client_decides_presentation=true`; HarmonyOS can render setup page, bottom sheet, current form fill, queue item, template, or a future custom flow.
- Kept all start/generate/playback actions disabled: no `/accompaniment/generate`, no engine adapter dispatch, no MIDI asset creation, and no playback start.

## v2_7_0 — Agent RoutineConfig Prepare Contract

- Added `agent_routine_config_prepare` descriptor for low-risk Routine setup candidate generation.
- Added editable `RoutineConfigPrepareActionPayload` for HarmonyOS Routine.
- Added `routine_config_prepare_payload` under `HarmonyOSAgentActionCard.result_preview` after descriptor resolution.
- Added terminal `/routine-config-prepare` command.
- Added `GET /agent/actions/routine-config/spec` and `POST /agent/actions/routine-config/prepare`.
- Payload can derive draft RoutineConfig from user intent, a practice plan, or a practice block.
- Opening Routine setup remains separate from playback; no `/accompaniment/generate` call, no engine adapter dispatch, no MIDI asset creation, and no playback start.

## v2_6_9 — Agent Playback Prepare Guarded Design

- Added guarded Routine-facing design payload for `agent_playback_prepare`.
- Added `playback_prepare_guarded_payload` under `HarmonyOSAgentActionCard.result_preview` after descriptor-only workflow resolution.
- Payload includes playback request candidate, RoutineConfig candidate, high-risk guard summary, confirmation ladder, next client actions, and client button semantics.
- Added terminal `/playback-prepare-guarded` command.
- Added `GET /agent/actions/playback-prepare/spec` and `POST /agent/actions/playback-prepare/guarded-preview`.
- `agent_playback_prepare` remains preview/confirmation/dry-run/descriptor-only: no `/accompaniment/generate`, no engine adapter dispatch, no MIDI asset creation, and no playback start.

## v2_6_8 — Agent Practice Plan ActionCard E2E

- Added Routine-facing practice-plan payload for controlled `agent_practice_plan` outputs.
- Added `routine_practice_plan_payload` under `HarmonyOSAgentActionCard.result_preview`.
- Payload includes compact plan metadata, Routine blocks, RoutineConfig candidate, next client actions, and client button semantics.
- Added terminal `/practice-plan-action-card` command.
- Added `GET /agent/actions/practice-plan/spec` and `POST /agent/actions/practice-plan/execute-controlled`.
- Opening Routine setup is explicitly separated from playback; no `/accompaniment/generate` call, no engine adapter dispatch, and no MIDI asset creation.

## v2_6_7 — Agent Runtime Skeleton Cleanup

- Added consolidated read-only Agent runtime skeleton contract.
- Added terminal `/runtime-skeleton` command.
- Added `GET /agent/runtime/skeleton` API route.
- Added trace spec entry for runtime skeleton inspection.
- Kept controlled execution limited to `agent_practice_plan`.
- No playback execution, no `/accompaniment/generate` call, no engine adapter dispatch, and no MIDI asset creation.

## v2_6_6 — HarmonyOS Agent Action Contract

- Added Routine-facing `HarmonyOSAgentActionCard` contract.
- Added Agent action spec, preview, and controlled execution API routes.
- Added terminal `/action-card` command for composing the latest action-card state.
- Action cards aggregate preview, confirmation, executor dry-run, workflow descriptor, controlled practice-plan output, and `trace_id`.
- The contract does not call `/accompaniment/generate`, does not call engine adapters, and does not create MIDI assets.

## v2_6_5 — Agent First Controlled Tool Execution E2E

- Added first guarded controlled workflow execution path.
- Enabled only `agent_practice_plan` / `PracticePlanner.build_plan` for real controlled execution.
- Added `ControlledWorkflowExecutionPolicy` and `ControlledWorkflowExecutionResult` shapes.
- Added terminal `/execute-controlled` command after preview, confirmation, executor dry-run, and workflow descriptor resolution.
- Added Agent controlled execution spec/API route.
- Controlled execution remains low-risk: no route call, no engine adapter call, no accompaniment generation, and no MIDI asset creation.

## v2_6_4 — Agent Deterministic Workflow Dispatcher

- Added descriptor-only deterministic workflow dispatcher boundary.
- Added `ToolWorkflowDispatcherPolicy`, `DeterministicWorkflowDescriptor`, and `ToolWorkflowDispatchResult` shapes.
- Added terminal `/dispatch-dry-run` command after ToolExecutor dry-run.
- Added Agent workflow dispatcher spec/dry-run API routes.
- Dispatch remains descriptor-only: no workflow invocation, no route call, no engine adapter call, no MIDI asset creation.

## v2_6_3 — Agent Tool Executor Boundary

- Added dry-run/no-op ToolExecutor boundary contracts.
- Added `ToolExecutionPolicy`, `ToolExecutionRequest`, and `ToolExecutionResult` shapes.
- Added terminal `/execute-dry-run` command after explicit confirmation.
- Added Agent executor spec/dry-run API routes.
- Execution remains no-op: no deterministic workflow dispatch, no route call, no engine adapter call, no MIDI asset creation.

## v2_6_2 — Agent Tool Execution Confirmation Gate

- Added a preview-after confirmation envelope for Agent tool proposals.
- Added terminal chat `/pending`, `/confirm`, and `/reject` commands.
- Added trace summaries for confirmation envelope creation and user approve/reject decisions.
- Added Agent confirmation spec/preview API routes.
- Execution remains disabled: no ToolExecutor, no workflow dispatch, no engine adapter call.

## v2_4_13 — Agent Tool Call Preview Trace Contract

- Preserved as the current Agent baseline inside the integrated package.
- Tool-call preview remains validation-only and non-autonomous.
- Preview trace contract remains available for inspection and HarmonyOS integration.

## v2_4_12 — Agent Terminal LLM Config Wizard

- Added bounded provider-configuration guidance for terminal chat.

## v2_4_11 — Agent Terminal Tool-Call Candidate Extraction

- Added JSON candidate extraction for tool-call preview.

## v2_4_9 — Agent Trace Viewer CLI

- Added read-only trace inspection surface.

## v2_7_2_agent_routine_history_context_intake

- Added Routine history context intake contract for HarmonyOS Routine completion summaries.
- Added `RoutineHistoryContextIntakePayload`, summary builder, and spec contract.
- Added terminal `/routine-history-context` command.
- Added API routes: `GET /agent/context/routine-history/spec` and `POST /agent/context/routine-history/intake`.
- Added ContextBuilder support for injecting `routine_history_context` into `learner_context` for future user-initiated planning turns.
- Explicitly avoids post-session Agent recommendation cards, `/accompaniment/generate`, engine adapters, MIDI assets, playback, and local playback internals.

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

- Added user-facing LLM capability map and intent taxonomy contract.
- Added `GET /agent/capabilities/user-intents/spec` and `POST /agent/capabilities/user-intents/preview`.
- Added terminal `/user-capability-map [json_payload]` command.
- Clarified Routine end remains HarmonyOS-client-owned; Agent does not create automatic post-session recommendation cards.
- Clarified candidate-only, confirmation-required, and forbidden direct action layers.
- Maintained no-LLM, no-tool-execution, no-engine, no-MIDI, no-playback guards.

## v2_7_6_agent_today_practice_guidance_output_validation

- Added `TodayPracticeGuidanceOutput` validation/normalization contract.
- Added API routes:
  - `GET /agent/context/today-practice-guidance/output-validation/spec`
  - `POST /agent/context/today-practice-guidance/output-validation/validate`
- Added terminal command `/today-practice-guidance-validate [json_payload]`.
- Blocks unsafe future LLM output that attempts to start Routine, call `/accompaniment/generate`, generate MIDI, invoke engine adapters, execute tools, expose local MIDI paths/API keys, or bypass user confirmation.
- Keeps HarmonyOS Routine presentation UI-flow-neutral.

## v2_7_7_agent_today_practice_guidance_provider_boundary_e2e

- Added TodayPracticeGuidance provider-boundary E2E contract.
- Connected prompt contract → providerResult / explicit provider call → output validation.
- Added API routes `/agent/context/today-practice-guidance/provider-boundary/spec` and `/agent/context/today-practice-guidance/provider-boundary/e2e-preview`.
- Added terminal command `/today-practice-guidance-e2e`.
- Kept all execution guards disabled: no Routine start, no `/accompaniment/generate`, no engine adapter, no MIDI asset, no playback.


## v2_7_8_agent_today_practice_guidance_action_card

- Added HarmonyOS Routine display ActionCard wrapper for validated today-practice guidance.
- Added `TodayPracticeGuidanceActionCardPayload`, summary builder, and contract spec.
- Added API routes:
  - `GET /agent/context/today-practice-guidance/action-card/spec`
  - `POST /agent/context/today-practice-guidance/action-card/preview`
- Added terminal command `/today-practice-guidance-action-card`.
- The card is display-only: it may show guidance, reasons, recommended blocks, and editable Routine candidates, but it never starts Routine, calls `/accompaniment/generate`, invokes engine adapters, creates MIDI assets, or starts playback.
- Preserved UI-flow neutrality: HarmonyOS decides whether to render the result as a card, bottom sheet, setup page, queue item, or another Routine surface.

## v2_7_9_agent_today_practice_guidance_terminal_chat_e2e

- Added ordinary terminal chat routing for high-confidence “今天该练什么？” / “what should I practice today?” turns.
- Added `TodayPracticeGuidanceTerminalChatE2EPayload`, summary builder, intent detector, and contract spec.
- Added API routes:
  - `GET /agent/context/today-practice-guidance/terminal-chat/spec`
  - `POST /agent/context/today-practice-guidance/terminal-chat/e2e-preview`
- Added optional terminal command `/today-practice-guidance-chat-e2e [json_payload]`.
- Normal terminal responses can now include a compact display-only TodayPracticeGuidance ActionCard summary.
- Preserved all guards: no Routine start, no `/accompaniment/generate`, no engine adapter, no MIDI asset, no playback, no frontend UI-flow assumption.

## v2_8_0_agent_context_and_guidance_skeleton_cleanup

- Added read-only context/guidance skeleton cleanup status for the v2_7_3 → v2_7_9 today-practice guidance chain.
- Added `ContextAndGuidanceSkeletonCleanupPayload`, summary builder, and contract spec.
- Added API route: `GET /agent/context/guidance-skeleton-cleanup`.
- Added terminal command `/context-guidance-skeleton [json_payload]`.
- Centralized the ordered stage registry, canonical route map, terminal commands, no-side-effect guard flags, and next-task hint.
- Preserved all guards: no Routine end recommendation card, no LLM call from cleanup, no tool execution, no Routine start, no `/accompaniment/generate`, no engine adapter, no MIDI asset, no playback, no frontend UI-flow assumption.

## v2_8_2_agent_practice_context_storage_boundary_contract

- Added practice-context storage/source-of-truth boundary contract.
- Added `PracticeContextStorageBoundaryPayload`, summary builder, and contract spec.
- Added API routes:
  - `GET /agent/context/storage-boundary/spec`
  - `POST /agent/context/storage-boundary/preview`
- Added terminal command `/practice-context-storage-boundary [json_payload]`.
- Classified practice context into HarmonyOS local-only, backend long-term, request-ephemeral, Agent trace, and never-store categories.
- Clarified that HarmonyOS owns live RoutineSession/timer/playback/local MIDI/UI draft state.
- Clarified that backend should eventually own durable compact summaries such as UserPracticeProfile, ActivePracticePlan, RoutineHistory summary, saved leadsheets/templates, and sanitized trace metadata.
- Added ContextPacket boundary guidance: normalized plan/history/profile/assembled/today-constraints may enter context; local MIDI paths, MIDI base64, secrets, precise location, payment info, playback internals, and hidden chain-of-thought must not.
- Preserved all guards: no database write, no local-device write, no LLM call, no tool execution, no Routine start, no `/accompaniment/generate`, no engine adapter, no MIDI asset, no playback.

Recommended next Agent task:

```text
v2_8_3_agent_today_practice_guidance_profile_aware_e2e
```


## v2_8_3_agent_today_practice_guidance_profile_aware_e2e

- Added profile-aware today-practice guidance E2E contract.
- Added `TodayPracticeGuidanceProfileAwareE2EPayload`, summary builder, and contract spec.
- Added API routes:
  - `GET /agent/context/today-practice-guidance/profile-aware/spec`
  - `POST /agent/context/today-practice-guidance/profile-aware/e2e-preview`
- Added terminal command `/today-practice-guidance-profile-aware [json_payload]`.
- Extended the TodayPracticeGuidance prompt policy with `profile_aware_policy`, including current goal, preferred styles, focus areas, comfort tempo ranges, avoid list, and practice-mode preference as soft context.
- Extended normalized guidance output/display sections with optional `profile_considerations`.
- Added profile-alignment preview counters for preferred-style and comfort-tempo matches; mismatches are warnings only and do not block safe candidate guidance.
- Preserved all guards: no storage write, no LLM call by default, no tool execution, no Routine start, no `/accompaniment/generate`, no engine adapter, no MIDI asset, no playback, no frontend-flow assumption.

Recommended next Agent task:

```text
v2_8_4_agent_practice_plan_persistence_candidate_contract
```

## v2_8_4_agent_terminal_llm_provider_compatibility_hotfix

- Fixed terminal module entrypoint argument forwarding so `python -m jammate_agent.cli.terminal_chat setup/doctor/config-path` reaches `run_interactive_chat(sys.argv[1:])`.
- Added OpenAI-compatible Chat Completions message normalization before network calls.
- Merged internal `system` / `developer` / `context` prompt sections into one outgoing `system` message.
- Preserved `user` / `assistant` history turns and converted unknown/tool preview roles into user-visible context instead of sending provider-rejected roles.
- Added regression coverage for role normalization, provider payload compatibility, and `python -m` setup command behavior.
- Preserved all Agent guards: no tool execution, no Routine start, no `/accompaniment/generate`, no engine adapter, no MIDI asset, no playback, no Engine music-generation change.

Recommended next Agent task:

```text
v2_8_5_agent_practice_plan_persistence_candidate_contract
```

## v2_8_11_agent_context_persistence_storage_adapter_sqlite_dev_preview

- Added dev-only SQLite/fixture adapter preview for Agent context persistence.
- Added `ContextPersistenceSqliteDevPreviewPayload`, summary builder, and contract spec.
- Added API routes:
  - `GET /agent/context/persistence-sqlite-dev-preview/spec`
  - `POST /agent/context/persistence-sqlite-dev-preview/preview`
- Added terminal command `/context-persistence-sqlite-dev-preview [json_payload]`.
- Added schema DDL preview for `user_practice_profiles`, `active_practice_plans`, `practice_history_summaries`, `context_persistence_idempotency_keys`, and `agent_trace_metadata`.
- Added idempotency-key, trace-link, read-snapshot, and fixture-snapshot preview sections.
- Kept default behavior no-write: no SQLite connection, no tables, no rows, no backend database write, no HarmonyOS local write.
- Explicitly blocks `devWriteEnabled=true` in this version because v2_8_11 is preview-only.
- Preserved all Agent guards: no LLM call, no tool execution, no Routine start, no `/accompaniment/generate`, no engine adapter, no MIDI asset, no playback, no post-session recommendation card.

Recommended next Agent task:

```text
v2_8_12_agent_context_persistence_dev_sqlite_explicit_write_gate
```

## v2_8_12_agent_context_persistence_dev_sqlite_explicit_write_gate

- Added explicit dev-only SQLite write gate and config-path contract for future Agent context persistence.
- Added `ContextPersistenceDevSqliteWriteGatePayload`, summary builder, and contract spec.
- Added API routes:
  - `GET /agent/context/persistence-dev-sqlite-write-gate/spec`
  - `POST /agent/context/persistence-dev-sqlite-write-gate/preview`
- Added terminal command `/context-persistence-dev-sqlite-write-gate [json_payload]`.
- Added required future-write checks: approved confirmation, idempotency key, trace link, dev config path, storage-boundary check, redaction check, and schema-preview acceptance.
- Kept the version no-write: no SQLite connection, no tables, no rows, no backend database write, no HarmonyOS local write.
- Preserved all Agent guards: no LLM call, no tool execution, no Routine start, no `/accompaniment/generate`, no engine adapter, no MIDI asset, no playback, no post-session recommendation card.

Recommended next Agent task:

```text
v2_8_13_agent_context_persistence_dev_sqlite_fixture_write_dry_run
```

## v2_8_13_agent_context_persistence_dev_sqlite_fixture_write_dry_run

- Added dev SQLite fixture writer dry-run contract for Agent context persistence.
- Added `ContextPersistenceDevSqliteFixtureWriteDryRunPayload`, summary builder, and contract spec.
- Added API routes:
  - `GET /agent/context/persistence-dev-sqlite-fixture-write-dry-run/spec`
  - `POST /agent/context/persistence-dev-sqlite-fixture-write-dry-run/preview`
- Added terminal command `/context-persistence-dev-sqlite-fixture-write-dry-run [json_payload]`.
- Added transaction, idempotency, trace-link, fixture row plan, and read-back snapshot preview sections.
- Kept the version dry-run only: no SQLite connection, no tables, no rows, no backend database write, no HarmonyOS local write, no committed transaction.
- Preserved all Agent guards: no LLM call, no tool execution, no Routine start, no `/accompaniment/generate`, no engine adapter, no MIDI asset, no playback, no post-session recommendation card.

Recommended next Agent task:

```text
v2_8_14_agent_context_persistence_dev_sqlite_fixture_store_explicit_opt_in
```

## v2_8_14_agent_context_persistence_dev_sqlite_fixture_store_explicit_opt_in

- Added dev-only explicit opt-in fixture JSONL store contract.
- Added `GET /agent/context/persistence-dev-sqlite-fixture-store/spec`.
- Added `POST /agent/context/persistence-dev-sqlite-fixture-store/preview`.
- Added terminal command `/context-persistence-dev-sqlite-fixture-store [json_payload]`.
- Added tests for explicit opt-in gates, redaction, idempotency, API, CLI, and manifest exposure.
- The fixture store can append a local development JSONL record only after explicit opt-in and all gates pass.
- Still does not open SQLite, create tables, write SQLite rows, write backend database, write HarmonyOS local state, call LLM, execute tools, start Routine, call Engine, create MIDI, or start playback.

## v2_8_15_agent_context_persistence_dev_fixture_readback_and_replay_preview

- Added dev fixture JSONL read-back / replay preview contract.
- Added `GET /agent/context/persistence-dev-fixture-readback-replay/spec`.
- Added `POST /agent/context/persistence-dev-fixture-readback-replay/preview`.
- Added terminal command `/context-persistence-dev-fixture-readback-replay`.
- Added `docs/AGENT_CONTEXT_PERSISTENCE_DEV_FIXTURE_READBACK_REPLAY_V2_8_15.md`.
- Read-only preview only: no SQLite connection, no SQLite rows, no backend write, no HarmonyOS local write, no LLM/tool/Engine call.

## v2_8_16_agent_context_persistence_profile_plan_history_snapshot_context_intake

- Added profile / active-plan / routine-history snapshot context intake contract.
- Added `ContextPersistenceProfilePlanHistorySnapshotContextIntakePayload`, summary builder, and contract spec.
- Added API routes:
  - `GET /agent/context/persistence-snapshot-context-intake/spec`
  - `POST /agent/context/persistence-snapshot-context-intake/preview`
- Added terminal command `/context-persistence-snapshot-context-intake [json_payload]`.
- Added `docs/AGENT_CONTEXT_PERSISTENCE_SNAPSHOT_CONTEXT_INTAKE_V2_8_16.md`.
- Added ContextBuilder support for injecting `context_persistence_snapshot_context_intake` into `learner_context`.
- Converts v2_8_15 dev fixture read-back snapshots into ContextPacket-ready user profile, active plan, routine history, and assembled practice context sections.
- Preserves strict no-side-effect guards: no database write, no HarmonyOS local write, no LLM/tool execution, no Routine start, no Engine call, no MIDI, no playback, no post-session recommendation card.

Recommended next Agent task:

```text
v2_8_17_agent_today_practice_guidance_persisted_context_recovery_e2e
```

## v2_8_17_agent_today_practice_guidance_persisted_context_recovery_e2e

- Added persisted-context recovery E2E for today-practice guidance.
- Added `GET /agent/context/today-practice-guidance/persisted-context-recovery/spec`.
- Added `POST /agent/context/today-practice-guidance/persisted-context-recovery/e2e-preview`.
- Added CLI `/today-practice-guidance-persisted-context-recovery`.
- Added `docs/AGENT_TODAY_PRACTICE_GUIDANCE_PERSISTED_CONTEXT_RECOVERY_E2E_V2_8_17.md`.
- Guardrails remain: no storage writes, no Routine start, no `/accompaniment/generate`, no engine adapter, no MIDI asset, no playback.

## v2_8_19_agent_today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture

- Added terminal persisted-context memory → HarmonyOS debug fixture preview contract.
- Added `GET /agent/context/today-practice-guidance/terminal-memory-harmonyos-debug-fixture/spec`.
- Added `POST /agent/context/today-practice-guidance/terminal-memory-harmonyos-debug-fixture/preview`.
- Added terminal command `/persisted-context-harmonyos-debug-fixture [json_payload]`.
- Added `docs/AGENT_TODAY_PRACTICE_GUIDANCE_TERMINAL_MEMORY_TO_HARMONYOS_DEBUG_FIXTURE_V2_8_19.md`.
- Added tests for contract, payload, API route, terminal command, manifest exposure, and Agent/Engine boundary.
- The fixture preview serializes recovered profile / active plan / routine history context into a HarmonyOS debug payload and Agent request preview.
- Still does not write backend database, write HarmonyOS local state, call LLM, execute tools, start Routine, call `/accompaniment/generate`, call Engine, create MIDI, or start playback.

Recommended next Agent task:

```text
v2_8_20_agent_harmonyos_debug_fixture_roundtrip_terminal_e2e
```

## v2_8_20_agent_harmonyos_debug_fixture_roundtrip_terminal_e2e

- Added HarmonyOS debug fixture roundtrip terminal/API E2E preview.
- Added `GET /agent/context/today-practice-guidance/harmonyos-debug-fixture-roundtrip/spec`.
- Added `POST /agent/context/today-practice-guidance/harmonyos-debug-fixture-roundtrip/e2e-preview`.
- Added terminal command `/harmonyos-debug-fixture-roundtrip [json_payload]`.
- Added `docs/AGENT_HARMONYOS_DEBUG_FIXTURE_ROUNDTRIP_TERMINAL_E2E_V2_8_20.md`.
- Added tests for contract, payload roundtrip, API route, CLI command, manifest exposure, and Agent/Engine boundary.
- The roundtrip consumes a v2_8_19 HarmonyOS debug fixture or builds one from terminal memory/direct context, extracts `agentRequestPreview.body`, and feeds it into v2_8_17 persisted-context recovery guidance.
- Still does not write backend database, write HarmonyOS local state, call LLM, execute tools, start Routine, call `/accompaniment/generate`, call Engine, create MIDI, or start playback.

Recommended next Agent task:

```text
v2_8_21_agent_harmonyos_debug_fixture_api_request_pack
```

## v2_8_21_agent_harmonyos_debug_fixture_api_request_pack

- 新增 HarmonyOS debug fixture API request pack。
- 新增 `/agent/context/today-practice-guidance/harmonyos-debug-fixture-api-request-pack/spec`。
- 新增 `/agent/context/today-practice-guidance/harmonyos-debug-fixture-api-request-pack/preview`。
- 新增终端命令 `/harmonyos-debug-fixture-api-request-pack [json_payload]`。
- 只生成 endpoint / request body / response path / curl example / terminal command preview，不调用 route、不写库、不调用 LLM、不启动 Routine、不调用 Engine。


## v2_8_22_agent_terminal_chat_product_smoke_polish

- 新增终端真实对话体验 smoke polish contract。
- 新增 `GET /agent/context/today-practice-guidance/terminal-product-smoke/spec`。
- 新增 `POST /agent/context/today-practice-guidance/terminal-product-smoke/preview`。
- 新增终端命令 `/terminal-product-smoke [json_payload]`。
- 增强普通“今天该练什么”终端输出：当 ActionCard validation guarded 时，额外提示 `doctor` 与 `/terminal-product-smoke`，避免只显示内部字段。
- 覆盖 provider setup / doctor、普通中文 guidance、persisted-context memory、JSON fallback、guarded error hint 等真实终端测试路径。
- 保持边界：smoke preview 不调用 LLM、不执行 tool、不写存储、不启动 Routine、不调用 `/accompaniment/generate`、不调用 Engine。

Recommended next Agent task:

```text
v2_8_23_agent_v2_8_phase_cleanup_regression_handoff
```

## v2_8_23_agent_v2_8_phase_cleanup_regression_handoff

- Added Agent v2_8 phase cleanup/regression/handoff report.
- Added `GET /agent/context/today-practice-guidance/v2-8-phase-handoff/spec`.
- Added `POST /agent/context/today-practice-guidance/v2-8-phase-handoff/preview`.
- Added terminal command `/v2-8-phase-handoff [json_payload]`.
- Added `docs/AGENT_V2_8_PHASE_CLEANUP_REGRESSION_HANDOFF_V2_8_23.md`.
- Added tests for contract, payload, API route, CLI command, manifest exposure, and Agent/Engine boundary.
- Captures the v2_8_1 → v2_8_22 completed milestone list, terminal smoke handoff, HarmonyOS debug fixture handoff, persistence boundary, regression commands, and next-phase recommendation.
- No new runtime product capability: the preview does not call LLM, execute tools, write storage, start Routine, call `/accompaniment/generate`, call Engine, create MIDI, or play audio.

Recommended next phase:

```text
Stop expanding v2_8. Move to integration handoff or v2_9_x Agent Persistence Implementation planning.
```

## v2_9_0_agent_context_persistence_sqlite_backend_store

- Added the first real Agent backend persistence implementation surface for dev/test/local SQLite context snapshots.
- Added `GET /agent/context/persistence-sqlite-backend-store/spec`.
- Added `POST /agent/context/persistence-sqlite-backend-store/execute`.
- Added terminal command `/context-persistence-sqlite-backend-store [json_payload]`.
- Added `docs/AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_STORE_V2_9_0.md`.
- Added tests for contract, explicit gate blocking, approved SQLite write, idempotency replay, sensitive/prod blocking, manifest exposure, API route, terminal command, and Agent/Engine boundary.
- The SQLite backend store writes only after explicit gates: `backendPersistenceEnabled=true`, `executeBackendPersistence=true`, user approval, dev/local/test environment, safe `.db/.sqlite/.sqlite3` path, trace ID, idempotency key, schema preview acceptance, storage-boundary check, and redaction check.
- Created backend tables: `context_persistence_records`, `context_persistence_idempotency_keys`, and `context_persistence_trace_links`.
- Repeated calls with the same idempotency key return an idempotent replay and do not duplicate rows.
- Still does not write HarmonyOS local state, call LLM, execute tools, start Routine, call `/accompaniment/generate`, call Engine, create MIDI, start playback, or create a post-session recommendation card.

Recommended next Agent task:

```text
v2_9_1_agent_context_persistence_sqlite_backend_readback_context_recovery
```

## v2_9_1_agent_context_persistence_sqlite_backend_readback_context_recovery

- Added read-only SQLite backend context recovery bridge for records written by v2_9_0.
- Added `GET /agent/context/persistence-sqlite-backend-readback-context-recovery/spec`.
- Added `POST /agent/context/persistence-sqlite-backend-readback-context-recovery/preview`.
- Added terminal command `/context-persistence-sqlite-backend-readback-context-recovery [json_payload]`.
- Added `docs/AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_READBACK_CONTEXT_RECOVERY_V2_9_1.md`.
- Added tests for contract, explicit readback gates, missing DB no-create behavior, read-only SQLite recovery, latest/user-filter readback, manifest exposure, API route, terminal command, and Agent/Engine boundary.
- The readback bridge opens an existing SQLite backend store in read-only mode, reads `context_persistence_records`, extracts redacted profile / active plan / routine history sections, and reuses v2_8_16 snapshot context intake to produce a ContextBuilder-ready recovery packet.
- Still does not write backend database, create SQLite tables, write HarmonyOS local state, call LLM, execute tools, start Routine, call `/accompaniment/generate`, call Engine, create MIDI, start playback, or create a post-session recommendation card.

Recommended next Agent task:

```text
v2_9_2_agent_context_persistence_sqlite_backend_today_guidance_recovery_e2e
```

## v2_9_2_agent_context_persistence_sqlite_backend_today_guidance_recovery_e2e

- Added SQLite backend persisted-context to today-practice guidance E2E preview.
- Added `GET /agent/context/persistence-sqlite-backend-today-guidance-recovery-e2e/spec`.
- Added `POST /agent/context/persistence-sqlite-backend-today-guidance-recovery-e2e/preview`.
- Added terminal command `/context-persistence-sqlite-backend-today-guidance-recovery-e2e [json_payload]`.
- Added `docs/AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_TODAY_GUIDANCE_RECOVERY_E2E_V2_9_2.md`.
- Added tests for contract, gate blocking/no DB creation, SQLite readback-to-guidance E2E, manifest exposure, API route, terminal command, and Agent/Engine boundary.
- The E2E reuses v2_9_1 read-only SQLite backend context recovery, then passes the recovered ContextBuilder-ready `contextPersistenceSnapshotContextIntake` section into v2_8_17 persisted-context today-practice guidance recovery.
- Still does not write backend database, create SQLite tables, write HarmonyOS local state, execute tools, start Routine, call `/accompaniment/generate`, call Engine, create MIDI, start playback, or create a post-session recommendation card.

Recommended next Agent task:

```text
v2_9_3_agent_context_persistence_sqlite_backend_terminal_memory_autoload_preview
```

## v2_9_3_agent_context_persistence_sqlite_backend_terminal_memory_autoload_preview

- Added terminal SQLite backend context autoload preview for Agent session memory.
- Added `GET /agent/context/persistence-sqlite-backend-terminal-memory-autoload-preview/spec`.
- Added `POST /agent/context/persistence-sqlite-backend-terminal-memory-autoload-preview/preview`.
- Added terminal command `/persisted-context-autoload-sqlite [json_payload]` plus the long-form `/context-persistence-sqlite-backend-terminal-memory-autoload-preview [json_payload]` alias.
- Added `docs/AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_TERMINAL_MEMORY_AUTOLOAD_PREVIEW_V2_9_3.md`.
- Added tests for contract, gate blocking/no DB creation, SQLite readback-to-terminal-memory preview, CLI session-memory load, next ordinary today-practice guidance turn memory reuse, API preview-only behavior, manifest exposure, terminal command output, and Agent/Engine boundary.
- The CLI reads SQLite through the v2_9_1 read-only bridge, prepares the same `guidance_arguments` shape used by v2_8_18 terminal memory controls, and writes only current in-process `TerminalChatSession.persisted_context_memory`.
- The API route is preview-only and does not load server-side session memory.
- Still does not write backend database, create SQLite tables, write HarmonyOS local state, execute tools, start Routine, call `/accompaniment/generate`, call Engine, create MIDI, start playback, or create a post-session recommendation card.

Recommended next Agent task:

```text
v2_9_4_agent_context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke
```

## v2_9_4_agent_context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke

- Added compact terminal smoke chain for the SQLite backend persistence path.
- Added `GET /agent/context/persistence-sqlite-backend-terminal-memory-to-guidance-smoke/spec`.
- Added `POST /agent/context/persistence-sqlite-backend-terminal-memory-to-guidance-smoke/preview`.
- Added terminal command `/sqlite-memory-guidance-smoke [json_payload]` plus the long-form `/context-persistence-sqlite-backend-terminal-memory-to-guidance-smoke [json_payload]` alias.
- Added `docs/AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_TERMINAL_MEMORY_TO_GUIDANCE_SMOKE_V2_9_4.md`.
- Added tests for contract/spec metadata, blocked no-gate behavior/no DB creation, SQLite write→read→guidance payload composition, terminal session-memory loading, API preview-only behavior, CLI output, manifest exposure, and Agent/Engine boundary.
- The smoke chain reuses the existing v2_9_0 explicit SQLite backend store gate, the v2_9_3 terminal-memory autoload preview, and the v2_8_17 persisted-context today-practice guidance recovery flow.
- Allowed side effects remain deliberately narrow: SQLite backend write only through explicit opt-in gates, SQLite readback, and current-process `TerminalChatSession.persisted_context_memory` update in CLI mode.
- Still does not write HarmonyOS local state, execute tools, start Routine, call `/accompaniment/generate`, call Engine, create MIDI, start playback, or create a post-session recommendation card.

Recommended next Agent task:

```text
v2_9_5_agent_context_persistence_sqlite_backend_api_memory_debug_pack
```


## v2_9_5_agent_context_persistence_sqlite_backend_api_memory_debug_pack

- Added SQLite backend API memory debug pack for v2_9_0 → v2_9_4 persistence/readback/guidance route alignment.
- Added `GET /agent/context/persistence-sqlite-backend-api-memory-debug-pack/spec` and `POST /agent/context/persistence-sqlite-backend-api-memory-debug-pack/preview`.
- Added terminal commands `/sqlite-api-memory-debug-pack` and `/context-persistence-sqlite-backend-api-memory-debug-pack`.
- Added route catalog, request examples, response path catalog, terminal command hints, and HarmonyOS/frontend-safe contract notes.
- Preserved strict no-side-effect behavior for the debug pack itself: no SQLite connection/read/write, no API server memory mutation, no HarmonyOS local write, no LLM/tool/Engine/Routine/MIDI/playback side effects.
- Added `tests/test_v2_9_5_agent_context_persistence_sqlite_backend_api_memory_debug_pack.py`.

Next recommended task: `v2_9_6_agent_context_persistence_sqlite_backend_harmonyos_api_fixture_pack`.

## v2_9_6_agent_context_persistence_sqlite_backend_harmonyos_api_fixture_pack

- Added HarmonyOS API fixture pack for the v2_9_0 → v2_9_5 SQLite backend persistence/readback/memory/guidance route family.
- Added `GET /agent/context/persistence-sqlite-backend-harmonyos-api-fixture-pack/spec`.
- Added `POST /agent/context/persistence-sqlite-backend-harmonyos-api-fixture-pack/preview`.
- Added terminal commands `/sqlite-harmonyos-api-fixture-pack [json_payload]` and `/context-persistence-sqlite-backend-harmonyos-api-fixture-pack [json_payload]`.
- Added copyable HarmonyOS request examples, expected response assertion catalog, curl examples, ArkTS fetch sketch, manual debug order, and integration boundary notes.
- Kept the pack preview-only: it does not call packaged routes, open/read/write SQLite, mutate server memory, write TerminalChatSession memory, write `frontend_fixtures/harmonyos/`, call LLM/tools/Engine, start Routine, generate MIDI, or start playback.
- Added `docs/AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_HARMONYOS_API_FIXTURE_PACK_V2_9_6.md`.
- Added `tests/test_v2_9_6_agent_context_persistence_sqlite_backend_harmonyos_api_fixture_pack.py`.

Recommended next Agent task:

```text
v2_9_7_agent_context_persistence_sqlite_backend_api_error_shape_matrix
```

## v2_9_7_agent_context_persistence_sqlite_backend_api_error_shape_matrix

- Added SQLite backend API error/blocked response shape matrix for v2_9 persistence/readback surfaces.
- Added `GET /agent/context/persistence-sqlite-backend-api-error-shape-matrix/spec`.
- Added `POST /agent/context/persistence-sqlite-backend-api-error-shape-matrix/preview`.
- Added terminal commands `/sqlite-api-error-shape-matrix [json_payload]` and `/context-persistence-sqlite-backend-api-error-shape-matrix [json_payload]`.
- Covered stable client-facing shapes for `missing_write_gate`, `invalid_sqlite_db_path`, `empty_readback`, `idempotent_replay`, and `malformed_payload`.
- Clarified HarmonyOS handling: idempotent replay is success, empty readback falls back to ordinary guidance/no persisted context, malformed payload requires client schema fix, and response fields stay canonical snake_case.
- Kept the matrix preview-only: no packaged route execution, no SQLite connection/read/write, no API/server memory mutation, no TerminalChatSession memory write, no frontend fixture write, no LLM/tool/Engine/Routine/MIDI/playback side effects.
- Added `docs/AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_API_ERROR_SHAPE_MATRIX_V2_9_7.md`.
- Added `tests/test_v2_9_7_agent_context_persistence_sqlite_backend_api_error_shape_matrix.py`.

Recommended next Agent task:

```text
v2_9_8_agent_context_persistence_sqlite_backend_harmonyos_error_fixture_pack
```

## v2_9_8_agent_context_persistence_sqlite_backend_harmonyos_error_fixture_pack

- Added HarmonyOS error fixture pack for SQLite backend persistence/readback API联调.
- Added `GET /agent/context/persistence-sqlite-backend-harmonyos-error-fixture-pack/spec`.
- Added `POST /agent/context/persistence-sqlite-backend-harmonyos-error-fixture-pack/preview`.
- Added terminal commands `/sqlite-harmonyos-error-fixture-pack [json_payload]` and `/context-persistence-sqlite-backend-harmonyos-error-fixture-pack [json_payload]`.
- Packaged copyable bad-request examples, expected UI/debug messages, retry policies, response-field assertions, curl examples, and ArkTS handling notes.
- Covered `missing_write_gate`, `invalid_sqlite_db_path`, `empty_readback`, `idempotent_replay`, and `malformed_payload`.
- Clarified client behavior: idempotent replay is success-like, empty readback falls back to ordinary guidance/no persisted context, malformed payload requires client schema fix, and response fields remain canonical snake_case.
- Kept the fixture pack preview-only: no packaged route execution, no SQLite connection/read/write, no API/server memory mutation, no TerminalChatSession memory write, no frontend fixture write, no LLM/tool/Engine/Routine/MIDI/playback side effects.
- Added `docs/AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_HARMONYOS_ERROR_FIXTURE_PACK_V2_9_8.md`.
- Added `tests/test_v2_9_8_agent_context_persistence_sqlite_backend_harmonyos_error_fixture_pack.py`.

Recommended next Agent task:

```text
v2_9_9_agent_context_persistence_sqlite_backend_handoff_completion_pack
```

## v2_9_9_agent_context_persistence_sqlite_backend_handoff_completion_pack

- Added Agent-track handoff completion pack for the `v2_9_0 → v2_9_8` SQLite backend persistence route.
- Added `GET /agent/context/persistence-sqlite-backend-handoff-completion-pack/spec`.
- Added `POST /agent/context/persistence-sqlite-backend-handoff-completion-pack/preview`.
- Added terminal commands `/sqlite-handoff-completion-pack [json_payload]` and `/context-persistence-sqlite-backend-handoff-completion-pack [json_payload]`.
- Packaged completed milestones, API route handoff pack, terminal command pack, HarmonyOS handoff pack, error fixture handoff pack, integration checklist, regression commands, boundary audit, and next-phase recommendation.
- Kept the handoff pack preview-only: no packaged route execution, no SQLite connection/read/write/table/row creation, no API/server memory mutation, no TerminalChatSession memory write, no frontend fixture write, no LLM/tool/Engine/Routine/MIDI/playback side effects.
- Added `docs/AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_HANDOFF_COMPLETION_PACK_V2_9_9.md`.
- Added `tests/test_v2_9_9_agent_context_persistence_sqlite_backend_handoff_completion_pack.py`.

Recommended next Agent / integration task:

```text
integration handoff or v2_10_0_agent_context_persistence_backend_db_path_policy_and_migration_guard
```

## v2_10_0_agent_context_persistence_backend_db_path_policy_and_migration_guard

- Added Agent backend persistence DB path policy and migration guard preview.
- Added `GET /agent/context/persistence-backend-db-path-policy-migration-guard/spec` and `POST /agent/context/persistence-backend-db-path-policy-migration-guard/preview`.
- Added terminal commands `/sqlite-db-policy-guard [json_payload]` and `/context-persistence-backend-db-path-policy-migration-guard [json_payload]`.
- Defined `agent_context_sqlite_schema_v1` as the current backend context SQLite schema version for guard purposes.
- Added path, environment, schema, migration mode, and observability validation without opening or creating SQLite databases.
- Blocked production-like paths/envs and destructive/force migration modes in Agent track.
- Preserved all Agent no-side-effect guards: no SQLite connection/read/write/table creation, no migration execution, no frontend fixture write, no server/terminal memory mutation, no LLM/tool/Engine/Routine/MIDI/playback side effects.
- Added docs and tests for `v2_10_0`.

Recommended next Agent task:

```text
v2_10_1_agent_context_persistence_backend_schema_metadata_table_preview
```

## v2_10_1_agent_context_persistence_backend_schema_metadata_table_preview

- Added preview-only backend schema metadata / migration registry table contract.
- Added `GET /agent/context/persistence-backend-schema-metadata-table-preview/spec`.
- Added `POST /agent/context/persistence-backend-schema-metadata-table-preview/preview`.
- Added terminal commands `/sqlite-schema-metadata-preview [json_payload]` and `/context-persistence-backend-schema-metadata-table-preview [json_payload]`.
- Defined metadata schema version `agent_context_sqlite_schema_metadata_v1`.
- Previewed future metadata tables: `context_persistence_schema_metadata`, `context_persistence_migration_registry`, and `context_persistence_schema_validation_events`.
- Composed the `v2_10_0` DB path / schema / migration guard as a prerequisite without opening SQLite.
- Kept the milestone preview-only: no SQLite connection/read/write/table creation, no schema creation, no migration execution, no API/server or terminal memory mutation, no frontend fixture write, no LLM/tool/Engine/Routine/MIDI/playback side effects.
- Added `docs/AGENT_CONTEXT_PERSISTENCE_BACKEND_SCHEMA_METADATA_TABLE_PREVIEW_V2_10_1.md`.
- Added `tests/test_v2_10_1_agent_context_persistence_backend_schema_metadata_table_preview.py`.

Recommended next Agent task:

```text
v2_10_2_agent_context_persistence_backend_schema_metadata_migration_dry_run_plan
```

## v2_10_2_agent_usable_today_practice_guidance_mvp

- Shifted the Agent track from preview/guard packaging back toward a user-facing today-practice guidance MVP.
- Added `GET /agent/context/usable-today-practice-guidance-mvp/spec`.
- Added `POST /agent/context/usable-today-practice-guidance-mvp/preview`.
- Added terminal command `/usable-today-practice-guidance [json_payload]`.
- Added terminal `--context-db-path <path>` and `JAMMATE_AGENT_CONTEXT_DB_PATH` support so ordinary `今天该练什么？` turns can auto-read persisted SQLite context.
- Implemented a natural fallback for fresh installs/no context DB: return a clear no-context setup message instead of exposing internal recovery/gate commands.
- Reused existing v2_9 SQLite readback + v2_8/v2_7 today-guidance chains instead of creating another recommendation system.
- Preserved display-only guidance boundaries: no Routine start, no `/accompaniment/generate`, no Engine adapter, no MIDI, no playback, no HarmonyOS local write, and no schema migration.
- Added `docs/AGENT_USABLE_TODAY_PRACTICE_GUIDANCE_MVP_V2_10_2.md`.
- Added `tests/test_v2_10_2_agent_usable_today_practice_guidance_mvp.py`.

Recommended next Agent task:

```text
v2_10_3_agent_routine_completion_record_to_backend_context_write_mvp
```

## v2_10_3_agent_routine_completion_record_to_backend_context_write_mvp

- Added the first product-facing write MVP for completed Routine/practice records.
- Added `GET /agent/context/routine-completion-record-to-backend-context-write-mvp/spec`.
- Added `POST /agent/context/routine-completion-record-to-backend-context-write-mvp/execute`.
- Added terminal commands `/routine-completion-record-write [json_payload]` and `/routine-completion-to-backend-context [json_payload]`.
- Reused the existing `v2_9_0` SQLite backend store instead of creating another persistence system.
- Normalized client-submitted `routineCompletionRecord` into `routine_history_records` backend context.
- Added idempotency for repeated completion-record writes.
- Added readback verification through the existing SQLite backend readback recovery.
- Preserved boundaries: no HarmonyOS local state write, no LLM/tool/Engine/Routine/MIDI/playback side effects, and no post-session recommendation card.
- Added `docs/AGENT_ROUTINE_COMPLETION_RECORD_TO_BACKEND_CONTEXT_WRITE_MVP_V2_10_3.md`.
- Added `tests/test_v2_10_3_agent_routine_completion_record_to_backend_context_write_mvp.py`.

Recommended next Agent task:

```text
v2_10_4_agent_routine_completion_to_today_guidance_product_smoke
```

## v2_10_4_agent_routine_completion_to_today_guidance_product_smoke

- Added the first compact product smoke for the usable Agent loop.
- Added `GET /agent/context/routine-completion-to-today-guidance-product-smoke/spec`.
- Added `POST /agent/context/routine-completion-to-today-guidance-product-smoke/execute`.
- Added terminal commands `/routine-completion-to-today-guidance-smoke [json_payload]` and `/completion-guidance-smoke [json_payload]`.
- Composed existing `v2_10_3` Routine completion write with existing `v2_10_2` ordinary today-practice guidance MVP.
- Added optional confirmed one-call profile/plan seed for deterministic local product smoke testing.
- Verified that a completed Routine record can be persisted and then read by the next ordinary `今天该练什么？` guidance turn.
- Preserved strict boundaries: no HarmonyOS local write, no tool execution, no Routine start, no `/accompaniment/generate`, no Engine adapter call, no MIDI asset, no playback, and no post-session recommendation card.
- Added `docs/AGENT_ROUTINE_COMPLETION_TO_TODAY_GUIDANCE_PRODUCT_SMOKE_V2_10_4.md`.
- Added `tests/test_v2_10_4_agent_routine_completion_to_today_guidance_product_smoke.py`.

Recommended next Agent / integration task:

```text
integration handoff or v2_10_5_agent_harmonyos_today_guidance_api_contract_alignment
```
