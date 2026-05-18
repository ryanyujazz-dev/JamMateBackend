# Agent Tool Registry Boundary v2_4_3

`v2_4_3_agent_tool_registry_boundary` belongs to `feature/agent-workflow`.

## Goal

Create a stable descriptor-only registry for Agent deterministic workflows and future bounded LLM tool planning.

This delivery does **not** execute tools from the runloop and does **not** deepen accompaniment generation.

## Owner

```text
src/jammate_agent/core/tool_registry.py
```

The registry owns:

- deterministic workflow/tool names
- route or internal workflow references
- task type applicability
- input/output contract summaries
- adapter boundary notes
- side-effect level
- execution guard status

## Runtime Flow

```text
ContextProfile.allowed_tools
  -> summarize_tools_for_names(...)
  -> ContextPacket.tool_descriptors
  -> BoundedAgentRunLoop.preview(...)
  -> runloop_preview.tool_registry_summary
  -> GET /agent/tools/registry
```

## Hard Guards

```text
tool_execution_enabled = false
autonomous_tool_execution_enabled = false
llm_tool_calls_enabled = false
```

`v2_4_3` is still preview-only:

- no LLM network call
- no provider SDK import
- no autonomous tool execution
- no runloop-driven tool execution
- no engine generation-rule change

## API

```text
GET /agent/tools/registry
```

Response shape:

```json
{
  "ok": true,
  "registry": {
    "version": "v2_4_3",
    "execution_status": {
      "tool_execution_enabled": false,
      "autonomous_tool_execution_enabled": false,
      "llm_tool_calls_enabled": false
    },
    "tools": [],
    "tool_names": [],
    "task_allow_lists": {}
  }
}
```

## Tools Currently Described

- `direct_accompaniment_generate`
- `chart_resolve`
- `agent_playback_prepare`
- `agent_practice_plan`
- `session_review_recommendation`
- `agent_llm_context_runtime_preview`
- `agent_llm_provider_boundary_spec`
- `agent_tool_registry_spec`

## Design Notes

- `direct_accompaniment_generate` remains a direct HarmonyOS/API route, not an Agent runloop tool.
- `chart_resolve` is internal chart-context preparation for Agent playback.
- `agent_playback_prepare`, `agent_practice_plan`, and `session_review_recommendation` remain deterministic workflows.
- Diagnostic routes are exposed to HarmonyOS and developers, but are not part of task allow-lists unless explicitly added later.

## Recommended Next Task

```text
v2_4_4_agent_terminal_chat_cli_foundation
```

Recommended scope: define a non-executing tool invocation preview/result envelope so a future LLM loop can propose tool calls, validate allow-list/arguments/side effects, and still stop before execution.
