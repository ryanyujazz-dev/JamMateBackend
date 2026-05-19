# AGENT_FIRST_CONTROLLED_TOOL_EXECUTION_E2E_V2_6_5

## Purpose

`v2_6_5_agent_first_controlled_tool_execution_e2e` adds the first real controlled Agent workflow after the preview / confirmation / dry-run / descriptor chain.

This milestone deliberately chooses the lowest-risk workflow:

```text
agent_practice_plan
→ PracticePlanner.build_plan
→ structured PracticePlan output
```

It does not execute accompaniment playback, does not call `/accompaniment/generate`, does not call engine adapters, and does not create MIDI assets.

## Required Chain

```text
ToolInvocationPreview
→ ToolExecutionConfirmationEnvelope
→ user /confirm
→ ToolExecutor dry-run
→ deterministic workflow descriptor resolution
→ controlled PracticePlanner execution
→ trace summary
```

The controlled execution command/API must not skip any earlier gate.

## Allowed Workflow

Only this tool/workflow is enabled in v2_6_5:

```text
Tool: agent_practice_plan
Workflow: PracticePlanner.build_plan
Side-effect level: none
```

All other tools, including `agent_playback_prepare`, remain blocked at the controlled-execution policy layer.

## Terminal Command

```text
/execute-controlled
```

Expected developer flow:

```text
/tool-preview agent_practice_plan {"userInput":"练 30 分钟 Blue Bossa","availableMinutes":30}
/confirm
/execute-dry-run
/dispatch-dry-run
/execute-controlled
```

## API Contract

```http
GET /agent/tools/workflows/controlled-execution/spec
POST /agent/tools/workflows/execute-controlled
```

Example request:

```json
{
  "taskType": "practice_plan_generation",
  "toolName": "agent_practice_plan",
  "arguments": {
    "userInput": "练 30 分钟 Blue Bossa",
    "availableMinutes": 30,
    "instrument": "piano"
  },
  "userApproved": true
}
```

Response contains:

```text
preview
confirmation
confirmation_result
execution_result
workflow_dispatch_result
controlled_workflow_execution_result
controlled_workflow_execution_summary
context_packet_summary
```

## Guards

Required false fields for this milestone:

```text
route_called = false
engine_adapter_called = false
side_effects_created = false
midi_asset_created = false
autonomous_execution_enabled = false
```

## Non-goals

This version does not do:

```text
agent_playback_prepare real execution
/accompaniment/generate call
engine adapter call
MIDI generation
MIDI asset caching
HarmonyOS action-card UI contract
practice feedback scoring
```

The next recommended task is `v2_6_6_harmonyos_agent_action_contract`, which should expose Routine-facing action-card state rather than adding higher-risk playback execution.
