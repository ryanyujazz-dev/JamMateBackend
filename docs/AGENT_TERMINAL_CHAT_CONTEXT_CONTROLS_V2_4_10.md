# v2_4_10 — Agent Terminal Chat Context Controls

## Scope

`v2_4_10_agent_terminal_chat_context_controls` stays inside `feature/agent-workflow` and does not deepen accompaniment generation.

It extends the existing terminal chat owner:

```text
src/jammate_agent/cli/terminal_chat.py
```

No parallel chat CLI, tracing subsystem, tool executor, or engine-facing module was added.

## New terminal commands

```text
/session
/context [full|--full|json|--json]
/profiles
/profile [task_type]
/task-type [task_type]
/instrument [instrument]
/reset
```

Existing commands remain:

```text
/help
/tools
/tool-preview <tool_name> [json_object_arguments]
/trace
/traces
/exit
```

## Behavior

- `/context` builds the current task-scoped `ContextPacket` summary only.
- `/context full` prints the full current `ContextPacket` JSON payload.
- `/profiles` lists available context profiles from `ContextBuilder.profile_manifest()`.
- `/profile` shows the current profile; `/profile <task_type>` switches task profile.
- `/task-type <task_type>` is an alias for profile switching.
- Switching task type clears terminal chat history to avoid mixing old conversation state into a new profile.
- `/instrument <instrument>` changes the instrument hint used by future `ContextPacket` builds.
- `/session` shows local terminal session state.
- `/reset` clears local chat history.

## Hard guards

These context controls are local debugging controls only:

- They do not call the LLM provider.
- They do not execute tools.
- They do not dispatch deterministic workflows.
- They do not call Agent adapters.
- They do not import or call `jammate_engine`.

The existing `/tool-preview` command remains validation-only and execution-blocked.

## Validation

Targeted regression covers:

- context preview without provider calls
- profile manifest display
- task type switching and history clearing
- invalid task type rejection
- instrument update
- session reset
- CLI help output
- full context JSON output
- import boundary checks
