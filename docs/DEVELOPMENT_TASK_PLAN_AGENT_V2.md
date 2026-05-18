# Agent Track Development Task Plan V2

Current baseline: `v2_6_1`.

This file is the rolling plan for `feature/agent-workflow`. It owns Agent / LLM orchestration, terminal chat, tool-preview, traces, provider boundaries, and HarmonyOS Agent contract surfaces.

---

## Ownership

Allowed owner paths:

```text
src/jammate_agent/
src/jammate_api/routes/agent_routes.py
tools/*agent*
tools/*trace*
tools/*terminal*
tests/test_*agent*.py
tests/test_*trace*.py
tests/test_*tool*.py
demos/agent_fixtures/
docs/AGENT*.md
```

Do not modify engine generation/style/core runtime code in an Agent task.

---

## Current Agent Baseline

Official Agent baseline preserved in the integrated package:

```text
v2_4_13_agent_tool_call_preview_trace_contract
```

Important retained Agent facts:

- terminal chat is available through the Agent CLI boundary;
- LLM provider configuration remains explicit and bounded;
- tool-call preview is validation-only and does not execute tools autonomously;
- trace viewer is read-only;
- HarmonyOS fixtures and contracts remain copy-friendly;
- Agent may call engine behavior only through `src/jammate_agent/adapters/`.

---

## Recommended Next Agent Task

No Agent implementation task is currently required before the next Engine pass.

When resumed, the next Agent task should stay within Agent-owned surfaces, for example:

```text
v2_6_agent_terminal_chat_usage_polish_or_harmonyos_agent_fixture_review
```

Forbidden scope:

- no direct edits to `src/jammate_engine/styles/`;
- no direct edits to `src/jammate_engine/core/`;
- no changes to MIDI realization;
- no replacement of `/accompaniment/generate` response shape.

---

## Near-Term Agent Queue

1. terminal chat UX polish after engine baseline stabilizes;
2. HarmonyOS fixture review after frontend asks for concrete fields;
3. provider-boundary LLM config validation hardening;
4. trace viewer filtering/export polish.

Any task that changes shared API contract or frontend fixtures should be moved to an integration task.
