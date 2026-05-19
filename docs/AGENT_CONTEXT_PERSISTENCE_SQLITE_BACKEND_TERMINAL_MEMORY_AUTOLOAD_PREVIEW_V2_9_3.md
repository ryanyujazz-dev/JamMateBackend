# AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_TERMINAL_MEMORY_AUTOLOAD_PREVIEW_V2_9_3

Status: completed in Agent track.

## Goal

Continue the v2_9_x Agent Persistence Implementation phase after the v2_9_2 SQLite backend to today-practice guidance E2E preview:

```text
v2_9_3_agent_context_persistence_sqlite_backend_terminal_memory_autoload_preview
```

This milestone lets terminal chat explicitly read persisted Agent context from the real SQLite backend and load it into the current `TerminalChatSession.persisted_context_memory`, so the following ordinary “今天该练什么” turn can reuse recovered profile / active plan / routine history without manually pasting a recovery packet.

## Implemented surfaces

```text
GET  /agent/context/persistence-sqlite-backend-terminal-memory-autoload-preview/spec
POST /agent/context/persistence-sqlite-backend-terminal-memory-autoload-preview/preview
CLI  /persisted-context-autoload-sqlite [json_payload]
CLI  /context-persistence-sqlite-backend-terminal-memory-autoload-preview [json_payload]
```

Core builder:

```text
build_context_persistence_sqlite_backend_terminal_memory_autoload_preview_payload(...)
build_context_persistence_sqlite_backend_terminal_memory_autoload_preview_summary(...)
context_persistence_sqlite_backend_terminal_memory_autoload_preview_contract()
```

Test coverage:

```text
tests/test_v2_9_3_agent_context_persistence_sqlite_backend_terminal_memory_autoload_preview.py
```

## Flow

```text
v2_9_0 SQLite backend store
        ↓ existing persisted records
v2_9_1 read-only SQLite backend context recovery
        ↓ ContextBuilder-ready contextPersistenceSnapshotContextIntake
v2_9_3 terminal memory autoload preview
        ↓ CLI-only in-process TerminalChatSession.persisted_context_memory
ordinary terminal chat: “今天该练什么”
        ↓
v2_8_17 persisted-context today-practice guidance recovery
```

## Required readback gates

The SQLite stage reuses the same readback gates as v2_9_1:

```text
backendReadbackEnabled=true
executeBackendReadback=true
environment in dev/local_dev/test
sqliteDbPath is relative or /tmp or /mnt/data and ends with .db/.sqlite/.sqlite3
optional idempotencyKey / traceId / userId / candidate filters
no forbidden client-local/MIDI/API-key fields
```

The API route only returns the preview payload. It does not own a terminal session and therefore does not load server-side memory.

## Boundary

Allowed by this milestone:

```text
Read existing backend SQLite context records after explicit readback gates.
Prepare a terminal session-memory object compatible with v2_8_18 memory controls.
CLI may load only current in-process TerminalChatSession.persisted_context_memory.
Allow the next ordinary terminal “今天该练什么” turn to reuse loaded memory.
```

Still forbidden:

```text
No backend SQLite write.
No SQLite table creation.
No HarmonyOS local write by Agent.
No API-side session memory mutation.
No Routine start.
No post-session recommendation card.
No /accompaniment/generate.
No Engine adapter call.
No MIDI asset creation.
No playback.
No tool execution.
No production persistence environment enablement.
No Engine music-generation change.
No frontend_fixtures/harmonyos change.
```

LLM/provider behavior:

```text
The autoload step does not call LLM.
If the loaded memory contains an explicit providerResult, the next guidance turn can remain deterministic/display-only.
If no providerResult is supplied, the existing today-practice guidance provider boundary decides whether a provider preview is allowed.
```

## Agent/Engine boundary

This milestone stays inside the Agent track:

```text
src/jammate_agent/core/tool_invocation.py
src/jammate_agent/core/context.py
src/jammate_agent/core/contracts.py
src/jammate_agent/cli/terminal_chat.py
src/jammate_api/routes/agent_routes.py
tests/test_v2_9_3_agent_context_persistence_sqlite_backend_terminal_memory_autoload_preview.py
docs/AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_TERMINAL_MEMORY_AUTOLOAD_PREVIEW_V2_9_3.md
docs/DEVELOPMENT_TASK_PLAN_AGENT_V2.md
docs/CHANGELOG_AGENT.md
```

No `src/jammate_engine/*` file is modified.

## Regression commands

```bash
PYTHONPATH=src python -m compileall -q src tests tools
PYTHONPATH=src python -m pytest -q tests/test_v2_9_3_agent_context_persistence_sqlite_backend_terminal_memory_autoload_preview.py
PYTHONPATH=src python -m pytest -q \
  tests/test_v2_8_18_agent_today_practice_guidance_persisted_context_terminal_memory_controls.py \
  tests/test_v2_9_0_agent_context_persistence_sqlite_backend_store.py \
  tests/test_v2_9_1_agent_context_persistence_sqlite_backend_readback_context_recovery.py \
  tests/test_v2_9_2_agent_context_persistence_sqlite_backend_today_guidance_recovery_e2e.py \
  tests/test_v2_9_3_agent_context_persistence_sqlite_backend_terminal_memory_autoload_preview.py
PYTHONPATH=src python tools/check_development_harness.py
```

## Next recommended Agent task

```text
v2_9_4_agent_context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke
```

Suggested scope:

```text
Add a compact terminal smoke command that demonstrates the full dev flow: write approved context to SQLite, autoload it into terminal session memory, then preview the next ordinary “今天该练什么” guidance turn. Keep it deterministic/display-only by using providerResult fixtures and maintain all Routine/Engine/playback guards.
```
