# Agent Terminal LLM Provider Compatibility Hotfix v2_8_4

## Scope

This hotfix improves real terminal-chat usability after profile-aware guidance work.

It fixes two terminal-facing issues only:

```text
1. python -m jammate_agent.cli.terminal_chat setup/doctor/config-path ignored argv.
2. Some OpenAI-compatible providers reject Chat Completions messages with role="developer".
```

## What changed

### CLI argv forwarding

`main()` now forwards command-line arguments into `run_interactive_chat(sys.argv[1:])`.

This makes the documented shell commands work when launched as a module:

```bash
PYTHONPATH=src python -m jammate_agent.cli.terminal_chat setup
PYTHONPATH=src python -m jammate_agent.cli.terminal_chat doctor
PYTHONPATH=src python -m jammate_agent.cli.terminal_chat config-path
PYTHONPATH=src python -m jammate_agent.cli.terminal_chat --show-provider-status
```

### Provider role compatibility

JamMate can still use provider-neutral internal envelopes, but the actual OpenAI-compatible network payload is normalized before sending:

```text
system/developer/context -> merged leading system message
user/assistant          -> preserved
tool/unknown            -> converted into user-visible context
```

The outgoing Chat Completions payload no longer sends `developer` or `context` roles, avoiding HTTP 400 errors from providers that only accept conservative roles.

## Non-goals

```text
No new recommendation logic.
No database write.
No LLM provider SDK dependency.
No requests/httpx dependency.
No tool execution.
No Routine start.
No /accompaniment/generate.
No engine adapter call.
No MIDI asset generation.
No playback.
No Engine music-generation change.
```

## Validation

Added:

```text
tests/test_v2_8_4_agent_terminal_llm_provider_compatibility_hotfix.py
```

Covers:

```text
1. developer/context roles are not sent to OpenAI-compatible Chat Completions payloads.
2. provider generate() uses normalized message roles.
3. module entrypoint forwards sys.argv so setup works through python -m.
```

## Recommended next Agent task

```text
v2_8_5_agent_practice_plan_persistence_candidate_contract
```

The originally planned persistence-candidate contract can continue next, now that real terminal LLM testing is unblocked.
