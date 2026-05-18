# v2_4_6 Agent Terminal Tool Preview CLI

`v2_4_6_agent_terminal_tool_preview_cli` belongs to `feature/agent-workflow`.

This delivery exposes the existing validation-only Agent tool invocation preview contract directly inside the terminal chat CLI. It is a backend debugging surface for checking future LLM tool-call proposals before enabling any real tool execution.

## Scope

In scope:

- Add explicit slash command support to `src/jammate_agent/cli/terminal_chat.py`.
- Reuse `ContextBuilder`, task-scoped `ContextPacket.allowed_tools`, `tool_registry.py`, and `tool_invocation.py`.
- Support terminal preview of a proposed tool call.
- Keep normal provider-backed terminal chat behavior unchanged.

Out of scope:

- No autonomous tool execution.
- No deterministic workflow dispatch from the terminal.
- No API route dispatch from the terminal command.
- No engine adapter call from terminal preview.
- No accompaniment engine generation-rule changes.

## Commands

Interactive terminal chat:

```bash
PYTHONPATH=src python -m jammate_agent.cli.terminal_chat
```

One-shot LLM chat, guarded by provider env vars:

```bash
PYTHONPATH=src python -m jammate_agent.cli.terminal_chat --once "解释一下 altered dominant"
```

One-shot tool preview, no provider call required:

```bash
PYTHONPATH=src python -m jammate_agent.cli.terminal_chat \
  --task-type immediate_practice_playback \
  --once '/tool-preview agent_playback_prepare {"durationMinutes":20}'
```

Interactive commands:

```text
/help
/tools
/tool-preview <tool_name> [json_object_arguments]
/trace
/traces
/exit
```

## Runtime path

```text
TerminalChatSession.preview_tool_call(...)
  -> ContextBuilder.build(task_type, user_input, client_context={entry_point: terminal_chat_cli})
  -> ContextPacket.allowed_tools
  -> ToolInvocationProposal
  -> preview_tool_invocation(proposal, allowed_tools=context.allowed_tools)
  -> ToolInvocationPreviewResult
```

## Safety guarantees

- `tool_execution_enabled = false`
- `autonomous_tool_execution_enabled = false`
- `would_execute = false`
- terminal preview does not call the LLM provider
- terminal preview does not dispatch routes
- terminal preview does not dispatch deterministic workflows
- terminal preview does not call engine adapters

## Example output semantics

A valid allowed tool call returns `preview_only_blocked_by_execution_guard`. This means the tool exists and is allowed in the current task context, but execution is intentionally blocked by the v2_4_x guard.

A known but disallowed tool returns `rejected_not_allowed_for_context`. This means the tool exists in the registry but is not present in the current task profile's `ContextPacket.allowed_tools`.

Invalid JSON returns a terminal command error before any context or preview call is built.
