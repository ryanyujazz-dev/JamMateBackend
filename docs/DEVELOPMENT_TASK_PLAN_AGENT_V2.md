# Agent Track Development Task Plan V2

Current baseline: `v2_6_8_agent_practice_plan_action_card_e2e`.

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
v2_6_7_agent_runtime_skeleton_cleanup
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
```

Important retained facts:

- terminal chat is available through the Agent CLI boundary;
- LLM provider configuration remains explicit and bounded;
- tool-call preview remains validation-only until user confirmation;
- real controlled execution is currently allow-listed to `agent_practice_plan` only;
- HarmonyOS Routine can receive an ActionCard and a Routine-facing practice-plan payload;
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
```

---

## Current Agent Task

```text
v2_6_8_agent_practice_plan_action_card_e2e
```

Scope:

- refine Routine-facing payloads for controlled `agent_practice_plan` results;
- add `routine_practice_plan_payload` under `HarmonyOSAgentActionCard.result_preview`;
- expose plan title, duration, focus, block count, Routine blocks, RoutineConfig candidate, and next client actions;
- add terminal `/practice-plan-action-card` command;
- add `GET /agent/actions/practice-plan/spec` and `POST /agent/actions/practice-plan/execute-controlled`;
- keep all playback and accompaniment generation as separate future user-confirmed Routine actions.

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
v2_6_9_agent_playback_prepare_guarded_design
```

Goal: design the higher-risk `agent_playback_prepare` path as a guarded, multi-stage workflow without enabling real playback execution yet.

Suggested scope:

- define playback preparation risk policy;
- specify confirmation requirements for asset-generating actions;
- define Routine-side preview fields for chart/style/tempo/duration;
- keep real execution disabled;
- do not call `/accompaniment/generate` from Agent.

---

## Near-Term Agent Queue

1. `v2_6_9_agent_playback_prepare_guarded_design` — design higher-risk playback/asset workflow guards without execution;
2. `v2_7_0_agent_routine_config_prepare_contract` — prepare RoutineConfig candidate actions without starting playback;
3. `v2_7_1_agent_practice_plan_to_routine_setup_bridge` — let Routine open setup from an ActionCard payload;
4. `v2_7_2_agent_session_review_action_card` — structure post-practice review into Routine-facing recommendation cards.

Any task that changes shared API contract docs or HarmonyOS fixtures should be moved to an integration task.
