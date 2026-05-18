# Agent Track Development Task Plan V2

Current baseline: `v2_6_4_agent_deterministic_workflow_dispatcher`.

This file is the rolling plan for `feature/agent-workflow`. It owns Agent / LLM orchestration, terminal chat, tool-preview, traces, provider boundaries, and HarmonyOS Agent contract surfaces.

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
```

Do not modify engine generation/style/core runtime code in an Agent task.

---

## Current Agent Baseline

Official Agent baseline preserved in the integrated package:

```text
v2_4_13_agent_tool_call_preview_trace_contract
```

Important retained Agent facts:

- terminal chat is available through the Agent CLI boundary;
- LLM provider configuration remains explicit and bounded;
- tool-call preview is validation-only and does not execute tools autonomously;
- trace viewer is read-only;
- HarmonyOS fixtures and contracts remain copy-friendly;
- Agent may call engine behavior only through `src/jammate_agent/adapters/`.

---


## Completed Agent Milestones

```text
v2_6_2_agent_tool_execution_confirmation_gate
v2_6_3_agent_tool_executor_boundary
v2_6_4_agent_deterministic_workflow_dispatcher
v2_6_5_agent_first_controlled_tool_execution_e2e
```

---

## Current Agent Task

```text
v2_6_5_agent_first_controlled_tool_execution_e2e
```

Scope:

- run the first low-risk controlled Agent workflow end-to-end;
- allow only `agent_practice_plan` / `PracticePlanner.build_plan`;
- require preview, user confirmation, ToolExecutor dry-run, and workflow descriptor resolution before controlled execution;
- add terminal `/execute-controlled` command;
- expose controlled workflow execution spec/API route;
- record controlled execution request/result/summary in trace.

Forbidden scope:

- no direct edits to `src/jammate_engine/styles/`;
- no direct edits to `src/jammate_engine/core/`;
- no changes to MIDI realization;
- no direct `/accompaniment/generate` call;
- no `agent_playback_prepare` real execution in this milestone;
- no engine adapter calls;
- no route calls from the controlled workflow runner;
- no MIDI asset creation;
- no shared documentation updates from the Agent branch.

## Recommended Next Agent Task

```text
v2_6_6_harmonyos_agent_action_contract
```

Goal: expose Agent action-card state for HarmonyOS Routine: LLM reply, candidate action, preview, confirmation, execution state, result, and trace id.

---

## Near-Term Agent Queue

1. `v2_6_6_harmonyos_agent_action_contract` — expose Agent action cards/confirmation/execution state to Routine;
2. `v2_6_7_agent_runtime_skeleton_cleanup` — cleanup before concrete Agent feature development;
3. `v2_6_8_agent_practice_plan_action_card_e2e` — connect controlled practice plan output to Routine-facing action payloads;
4. `v2_6_9_agent_playback_prepare_guarded_design` — design, but not yet rush, the higher-risk playback/asset workflow.

Any task that changes shared API contract or frontend fixtures should be moved to an integration task.
