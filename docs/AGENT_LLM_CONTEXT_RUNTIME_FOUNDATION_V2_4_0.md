# v2_4_0 — Agent LLM Context Runtime Foundation

## Scope

This delivery is limited to `feature/agent-workflow`:

- Agent context runtime preview
- bounded future LLM/tool loop contract
- HarmonyOS API / contract / fixture synchronization
- trace/debug inspection

It intentionally does **not** deepen accompaniment engine generation, voicing, pattern, expression, pedal, or listening-demo behavior.

---

## Harness Reuse Audit

Before implementation, the existing Agent/API owners were audited and reused:

| Need | Existing owner reused | Decision |
|---|---|---|
| Task-scoped context packet | `src/jammate_agent/core/context.py` | Expanded `ContextBuilder`, `ContextPacket`, and profile metadata instead of creating a new context subsystem. |
| Future workflow loop envelope | `src/jammate_agent/core/runloop.py` | Upgraded the existing runloop placeholder into preview-only `BoundedAgentRunLoop`. |
| Agent facade | `src/jammate_agent/core/jammate_agent.py` | Added `build_llm_context_runtime()` as a facade method beside existing deterministic workflows. |
| Trace/debug inspection | `src/jammate_agent/core/trace.py` | Reused existing trace logger/store; no new trace backend. |
| API surface | `src/jammate_api/routes/agent_routes.py`, `src/jammate_api/schemas.py` | Added two Agent routes and one schema without touching engine routes. |
| HarmonyOS contracts | `src/jammate_agent/core/contracts.py`, `src/jammate_agent/core/contract_codegen.py` | Extended current manifest/codegen/fixture pack instead of adding parallel contract files. |

No new engine owner was introduced, and `jammate_engine` remains independent from `jammate_agent`.

---

## Runtime Contract

### Spec

```text
GET /agent/context/runtime/spec
```

Returns the context runtime contract, request/response schema outline, context packet layers, runloop policy, and explicit non-goals.

### Preview

```text
POST /agent/context/runtime/preview
```

Builds a task-scoped `ContextPacket`, runs `BoundedAgentRunLoop.preview()`, writes an Agent trace, and returns:

```text
AgentContextRuntimePreviewResponse
  ok
  task_type
  context_packet
  runloop_preview
  trace_id
```

In `v2_4_0`:

- `runtime_mode = preview_only`
- `llm_provider_configured = false`
- `tool_execution_enabled = false`
- `autonomous_tool_execution_enabled = false`

---

## Context Profiles

The runtime preview currently exposes these profiles:

- `practice_plan_generation`
- `immediate_practice_playback`
- `session_review`
- `coach_qa`

Each profile declares:

- required context layers
- optional context layers
- allowed tools
- expected output schema
- whether a future LLM is required
- deterministic fallback, when available

---

## Boundary Guarantees

- Engine does not import Agent.
- Agent imports engine only through `src/jammate_agent/adapters/`.
- HarmonyOS may continue using direct `/accompaniment/generate` without LLM.
- HarmonyOS local timer remains responsible for long practice duration.
- Backend responses remain canonical `snake_case`; generated HarmonyOS client-domain types remain `camelCase`.

---

## Recommended Next Step

`v2_4_1_agent_llm_provider_boundary`

Recommended scope:

- Add an interface/protocol for an optional LLM provider.
- Keep provider disabled by default.
- Add config/env guardrails and deterministic fallback behavior.
- Do not enable autonomous tool execution yet.
