# v2_4_5 Agent Tool Invocation Preview Contract

`v2_4_5_agent_tool_invocation_preview_contract` belongs to `feature/agent-workflow`.

## Scope

This version defines the validation envelope for future LLM-proposed tool calls without executing any tool.

It does not change accompaniment engine generation, voicing, patterns, expression, pedal, or MIDI realization rules.

## Runtime boundary

```text
LLM / terminal / API proposal
  -> ToolInvocationProposal
  -> task-scoped ContextPacket.allowed_tools
  -> AgentToolRegistry descriptor lookup
  -> ToolInvocationPreviewResult
  -> blocked by execution guard
```

## Routes

```text
GET  /agent/tools/invocation/spec
POST /agent/tools/invocation/preview
```

`POST /agent/tools/invocation/preview` accepts camelCase or snake_case request fields through the normal API schema policy.

Example:

```json
{
  "userInput": "我想练 Blue Bossa 20分钟",
  "taskType": "immediate_practice_playback",
  "toolName": "agent_playback_prepare",
  "arguments": {
    "userInput": "练 Blue Bossa 20分钟",
    "durationMinutes": 20
  },
  "clientContext": {
    "currentScreen": "practice_home",
    "availableMinutes": 20,
    "locale": "zh-CN"
  }
}
```

## Hard guards

- Tool must exist in `jammate_agent/core/tool_registry.py`.
- Tool must be present in the task-specific `ContextPacket.allowed_tools`.
- Arguments are normalized and shape-checked only.
- No deterministic route dispatch.
- No Agent adapter dispatch.
- No engine adapter dispatch.
- No autonomous tool execution.

## Result semantics

A known and allowed tool returns:

```json
{
  "ok": true,
  "preview": {
    "status": "preview_only_blocked_by_execution_guard",
    "would_execute": false,
    "execution_enabled": false,
    "autonomous_execution_enabled": false
  }
}
```

Unknown or not-allowed tools return `ok=false` at the preview level and explain the blocking reason.

## Next step

Recommended next step:

```text
v2_4_7_agent_terminal_trace_export
```

That step can make the terminal chat CLI accept explicit `/tool-preview` commands while still keeping tool execution disabled.
