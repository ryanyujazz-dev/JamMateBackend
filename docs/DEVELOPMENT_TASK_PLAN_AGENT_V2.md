# Agent Track Development Task Plan V2

Current baseline: `v2_6_2_agent_tool_execution_confirmation_gate`.

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

## Current Agent Task

```text
v2_6_3_agent_tool_executor_boundary
```

Scope:

- define ToolExecutor boundary contracts without real tool execution;
- add `ToolExecutionPolicy`, `ToolExecutionRequest`, and `ToolExecutionResult`;
- add dry-run/no-op executor behavior after approved confirmation;
- add terminal `/execute-dry-run` command;
- expose executor spec/dry-run API routes;
- record dry-run executor request/result in trace.

Forbidden scope:

- no direct edits to `src/jammate_engine/styles/`;
- no direct edits to `src/jammate_engine/core/`;
- no changes to MIDI realization;
- no replacement of `/accompaniment/generate` response shape;
- no real workflow dispatch;
- no engine adapter calls;
- no shared documentation updates from the Agent branch.

## Recommended Next Agent Task

```text
v2_6_4_agent_deterministic_workflow_dispatcher
```

Goal: map approved tool names to deterministic workflow descriptors while still avoiding deep engine imports and uncontrolled execution.

---

## Near-Term Agent Queue

1. `v2_6_4_agent_deterministic_workflow_dispatcher` — map tool names to deterministic workflows without engine deep imports;
2. `v2_6_5_agent_first_controlled_tool_execution_e2e` — first low-risk real controlled workflow;
3. `v2_6_6_harmonyos_agent_action_contract` — expose Agent action cards/confirmation/execution state to Routine;
4. `v2_6_7_agent_runtime_skeleton_cleanup` — cleanup before concrete Agent feature development.

Any task that changes shared API contract or frontend fixtures should be moved to an integration task.
