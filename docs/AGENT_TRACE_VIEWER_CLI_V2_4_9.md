# v2_4_9 Agent Trace Viewer CLI

## Purpose

`v2_4_9_agent_trace_viewer_cli` adds a read-only terminal viewer for local AgentTrace JSON files. It is meant for backend/HarmonyOS integration debugging after terminal chat or API trace export has already produced traces.

This delivery does not deepen accompaniment generation logic.

## Entry Points

```bash
PYTHONPATH=src python -m jammate_agent.cli.trace_viewer --trace-dir demos/agent_traces list
PYTHONPATH=src python -m jammate_agent.cli.trace_viewer --trace-dir demos/agent_traces show <trace_id>
PYTHONPATH=src python -m jammate_agent.cli.trace_viewer spec
```

Console script:

```bash
jammate-agent-traces --trace-dir demos/agent_traces list
```

## Commands

```text
list [--limit N] [--json]
show <trace_id> [--json]
spec [--json]
```

## Boundary Rules

The trace viewer:

- only reads local JSON traces through `JsonTraceStore`;
- reuses the `AgentTrace` summary/detail contract;
- does not execute tools;
- does not call the LLM provider;
- does not dispatch deterministic workflows;
- does not call routes, adapters, or engine code;
- does not import `jammate_engine` or provider SDKs.

## Relationship to Existing Trace Surfaces

`v2_4_7` terminal chat can export traces with `--trace-dir`.
`v2_4_8` hardened Trace API list/detail/spec responses.
`v2_4_9` adds a local terminal viewer over the same trace files and schema so terminal debugging and HarmonyOS trace inspection remain aligned.
