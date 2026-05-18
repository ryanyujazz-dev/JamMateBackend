# v2_4_13 — Agent Tool Call Preview Trace Contract

`v2_4_13_agent_tool_call_preview_trace_contract` stays inside `feature/agent-workflow` and does not deepen accompaniment generation.

## Goal

Make the terminal LLM debugging chain replayable as a stable trace contract:

```text
LLM response
-> explicit JSON tool-call candidate extraction
-> ContextPacket.allowed_tools validation
-> preview_tool_invocation result
-> execution guard result
-> AgentTrace JSON
```

## Owner Files

```text
src/jammate_agent/core/tool_invocation.py
src/jammate_agent/cli/terminal_chat.py
src/jammate_agent/core/trace.py
```

No second tracing subsystem was added. The implementation reuses `TraceLogger`, `JsonTraceStore`, and `AgentTrace`.

## Stable Trace Step

Terminal chat traces now record:

```text
terminal_tool_call_preview_trace_summary_recorded
```

The same summary is also included in:

```text
final_response_summary.tool_call_preview_trace_summary
```

## Summary Contract

```json
{
  "tool_call_preview_trace_contract_version": "v2_4_13",
  "candidate_extraction_version": "v2_4_13",
  "tool_invocation_preview_version": "v2_4_13",
  "tool_registry_version": "v2_4_13",
  "source": "terminal_chat_cli",
  "task_type": "immediate_practice_playback",
  "candidate_count": 1,
  "rejected_candidate_count": 0,
  "preview_count": 1,
  "previewed_tool_names": ["agent_playback_prepare"],
  "preview_statuses": ["preview_only_blocked_by_execution_guard"],
  "all_previews_execution_blocked": true,
  "execution_enabled": false,
  "autonomous_tool_execution_enabled": false,
  "dispatch_enabled": false,
  "engine_adapter_dispatch_enabled": false,
  "preview_summaries": [],
  "warnings": []
}
```

## Safety Boundary

This is a trace/debug contract only. It does not:

- execute tools
- dispatch deterministic workflows
- call API routes
- call adapters
- call `jammate_engine`
- bypass provider/network guards
- expose API keys

## Recommended Use

For local debugging:

```bash
PYTHONPATH=src python -m jammate_agent.cli.terminal_chat \
  --trace-dir tmp/terminal_traces \
  --task-type immediate_practice_playback \
  --once '练 Blue Bossa 20分钟'
```

Then inspect:

```bash
PYTHONPATH=src python -m jammate_agent.cli.trace_viewer \
  --trace-dir tmp/terminal_traces show <trace_id> --json
```
