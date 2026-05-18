# v2_4_8 Agent Trace API Contract Hardening

Branch scope: `feature/agent-workflow`.

## Purpose

`v2_4_8` turns Agent trace inspection from a loose debug dump into a stable API/contract surface for HarmonyOS and terminal debugging.

This version does not change accompaniment generation, voicing, pattern selection, expression, pedal, MIDI realization, or style tuning.

## Routes

```text
GET /agent/traces/spec
GET /agent/traces?limit=20
GET /agent/traces/{trace_id}
```

## Owner

Trace ownership remains in:

```text
src/jammate_agent/core/trace.py
```

The implementation reuses:

- `AgentTrace`
- `JsonTraceStore`
- `TraceLogger`

No second tracing subsystem is introduced.

## Contract changes

### List response

`GET /agent/traces` now returns:

- `ok`
- `trace_contract_version`
- `traces[]`

Each trace summary includes:

- `trace_contract_version`
- `trace_schema_version`
- `trace_id`
- `task_type`
- `request_id`
- `user_input_preview`
- `validation_result`
- `created_at`
- `updated_at`
- `step_count`
- `has_context_packet_summary`
- `has_final_response_summary`

A backward-compatible `steps` count alias is preserved for older diagnostics.

### Detail response

`GET /agent/traces/{trace_id}` now returns:

- `ok`
- `trace_contract_version`
- `trace`

The detail payload includes:

- `trace_contract_version`
- `trace_schema_version`
- `trace_id`
- `task_type`
- `request_id`
- `user_input`
- `context_packet_summary`
- `steps`
- `validation_result`
- `final_response_summary`
- `created_at`
- `updated_at`

### Not found

Missing traces return a stable shape:

```json
{
  "ok": false,
  "trace_contract_version": "v2_4_8",
  "error_code": "TRACE_NOT_FOUND",
  "message": "Trace not found: trace_missing",
  "trace": null
}
```

## Guards

Trace API hardening is inspection-only:

- no tool execution
- no autonomous tool execution
- no deterministic workflow dispatch
- no LLM provider call
- no engine adapter call

## HarmonyOS sync

Updated generated/frontend files include:

- `AgentTraceSummary`
- `AgentTraceDetail`
- `AgentTraceListResponse`
- `AgentTraceDetailResponse`
- `AgentTraceApiSpecResponse`
- `getAgentTraceSpec()`
- `listAgentTraces()`
- `getAgentTrace()`

The smoke pack now includes optional `GET /agent/traces/spec` and `GET /agent/traces` checks.

## Recommended next task

`v2_4_9_agent_trace_viewer_cli`: add a terminal-side read-only trace viewer command for local trace directories and/or API trace responses. It should remain inspection-only and must not execute tools or call the engine.
