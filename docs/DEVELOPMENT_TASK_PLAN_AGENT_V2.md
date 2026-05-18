# Agent Track Development Task Plan V2

Current baseline: `v2_7_1_agent_practice_plan_to_routine_candidate_bridge`.

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
v2_7_1_agent_practice_plan_to_routine_candidate_bridge
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

