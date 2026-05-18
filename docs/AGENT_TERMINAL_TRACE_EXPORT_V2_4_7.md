# v2_4_7 Agent Terminal Trace Export

`v2_4_7_agent_terminal_trace_export` belongs to `feature/agent-workflow`.

## Scope

This version makes the terminal Agent chat/debug loop auditable without enabling autonomous tools or changing the accompaniment engine.

It extends the existing `python -m jammate_agent.cli.terminal_chat` entrypoint with explicit trace export support:

```bash
PYTHONPATH=src python -m jammate_agent.cli.terminal_chat \
  --trace-dir tmp/terminal_traces
```

One-shot trace export is also supported:

```bash
PYTHONPATH=src python -m jammate_agent.cli.terminal_chat \
  --trace-dir tmp/terminal_traces \
  --once "解释一下 guide tones"
```

Tool-preview trace export is supported without provider calls:

```bash
PYTHONPATH=src python -m jammate_agent.cli.terminal_chat \
  --task-type immediate_practice_playback \
  --trace-dir tmp/terminal_traces \
  --once '/tool-preview agent_playback_prepare {"durationMinutes":20}'
```

## Terminal Commands

```text
/help
/tools
/tool-preview <tool_name> [json_object_arguments]
/trace
/traces
/exit
```

## Trace Boundary

Trace export reuses the existing Agent trace owner:

```text
terminal_chat.py
  -> TraceLogger
  -> JsonTraceStore
  -> AgentTrace JSON
```

Rules:

- Trace export is explicit through `--trace-dir`; no terminal traces are written by default.
- Terminal chat traces include context-packet summary, request-envelope summary, provider response summary, and final response summary.
- `/tool-preview` traces include context-packet summary and tool invocation preview result.
- Trace export does not execute tools.
- Trace export does not dispatch deterministic workflows.
- Trace export does not call engine adapters or `jammate_engine`.
- Trace export does not bypass provider/network guards.

## Cleanup Rule

Delivery packages must not include transient trace folders. Use temporary/local trace directories during debugging and remove them before packaging.
