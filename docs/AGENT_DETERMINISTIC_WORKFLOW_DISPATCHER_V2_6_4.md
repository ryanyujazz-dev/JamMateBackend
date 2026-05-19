# Agent Deterministic Workflow Dispatcher V2_6_4

## Scope

`v2_6_4_agent_deterministic_workflow_dispatcher` adds the Agent deterministic workflow dispatcher boundary.

This version is **descriptor resolution only**. It maps an approved dry-run ToolExecutor result to the deterministic workflow descriptor declared in the Agent tool registry.

It does not invoke workflows, call API routes, call engine adapters, import `jammate_engine`, or create MIDI assets.

## Runtime Chain

```text
ToolInvocationPreview
→ ToolExecutionConfirmation
→ ToolExecutor dry-run / no-op
→ Deterministic workflow descriptor resolution
```

## Added Contract

```text
GET /agent/tools/workflows/spec
POST /agent/tools/workflows/dispatch-dry-run
```

## Added Terminal Command

```text
/dispatch-dry-run
```

Expected terminal sequence:

```text
/tool-preview agent_playback_prepare {"durationMinutes":20}
/confirm
/execute-dry-run
/dispatch-dry-run
```

## Key Guarantees

```text
workflow_descriptor_resolution_enabled = true
real_workflow_dispatch_enabled = false
deterministic_workflow_dispatched = false
workflow_invoked = false
route_called = false
engine_adapter_called = false
side_effects_created = false
```

## Current Output

A successful dispatch dry-run returns a `workflow_descriptor`, for example:

```text
tool_name = agent_playback_prepare
workflow_name = ImmediatePlaybackWorkflow.prepare
route = POST /agent/playback/prepare
adapter_boundary = jammate_agent.adapters.JamMateEngineAccompanimentAdapter
next_stage_required = ControlledWorkflowExecution
```

## Non-goals

This version does not:

```text
execute tools
invoke deterministic workflows
call /agent/playback/prepare
call /accompaniment/generate
call engine adapters
change Engine music rules
change pattern / voicing / expression / pedal
modify MIDI demos
update shared docs
```

## Next Stage

Recommended next task:

```text
v2_6_5_agent_first_controlled_tool_execution_e2e
```

That next task may run the first real low-risk controlled workflow. It should start with a safer workflow such as practice-plan preparation before any accompaniment-generation side effect.
