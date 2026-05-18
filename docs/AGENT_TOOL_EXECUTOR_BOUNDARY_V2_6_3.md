# Agent Tool Executor Boundary v2_6_3

## Scope

`v2_6_3_agent_tool_executor_boundary` adds the first ToolExecutor boundary shape for Agent Workflow.

This version is **dry-run / no-op only**.

It proves that an approved tool confirmation can be converted into a stable execution request/result contract, but it still does not execute a real tool.

## Pipeline

```text
ToolInvocationPreviewResult
→ ToolExecutionConfirmationEnvelope
→ user approved / rejected
→ ToolExecutionRequest
→ ToolExecutionResult
→ trace summary
```

## What this version adds

- `ToolExecutionPolicy`
- `ToolExecutionRequest`
- `ToolExecutionResult`
- `build_tool_execution_request(...)`
- `execute_tool_dry_run(...)`
- `build_tool_executor_summary(...)`
- `tool_executor_boundary_contract()`
- terminal command `/execute-dry-run`
- API routes:
  - `GET /agent/tools/executor/spec`
  - `POST /agent/tools/executor/dry-run`

## Hard guards

`v2_6_3` must keep all of the following false:

```text
real_tool_execution_enabled=false
autonomous_execution_enabled=false
deterministic_workflow_dispatch_enabled=false
engine_adapter_dispatch_enabled=false
route_call_enabled=false
side_effects_enabled=false
```

A successful dry-run means only:

```text
approved confirmation exists
→ dry-run executor request/result shape is valid
→ no-op result returned
```

It does **not** mean:

```text
tool executed
workflow dispatched
engine adapter called
/accompaniment/generate called
MIDI asset created
```

## Terminal behavior

Expected development flow:

```text
/tool-preview agent_playback_prepare {"durationMinutes":20}
/confirm
/execute-dry-run
```

Before `/confirm`, `/execute-dry-run` must be blocked.

After `/confirm`, `/execute-dry-run` may return:

```text
status=dry_run_noop_completed
real_tool_executed=false
deterministic_workflow_dispatched=false
engine_adapter_called=false
next_stage_required=DeterministicWorkflowDispatcher
```

## API behavior

`POST /agent/tools/executor/dry-run` accepts a tool proposal plus `userApproved`.

If `userApproved=false`, the route returns a blocked dry-run result.

If `userApproved=true` and preview/confirmation are valid, the route returns a dry-run no-op execution result.

The route still does not call workflows, routes, adapters, LLM providers, or engine modules.

## Trace contract

Trace step names:

```text
terminal_tool_executor_dry_run_requested
terminal_tool_executor_dry_run_completed
terminal_tool_executor_dry_run_blocked
terminal_tool_executor_summary_recorded
```

Final summary field:

```text
final_response_summary.tool_executor_summary
```

## Next stage

Next recommended version:

```text
v2_6_4_agent_deterministic_workflow_dispatcher
```

That stage should map approved tool names to deterministic workflow descriptors, but should still avoid deep engine imports and should start from low-risk workflows.
