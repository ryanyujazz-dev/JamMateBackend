# Agent Track Changelog

Current baseline: `v2_7_1_agent_practice_plan_to_routine_candidate_bridge`.

This file records Agent-track changes to reduce conflicts in the global `docs/CHANGELOG.md`.

---

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
