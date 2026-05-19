# Agent Context Persistence SQLite Backend Terminal Memory To Guidance Smoke V2.9.4

## Milestone

```text
v2_9_4_agent_context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke
```

This milestone adds a compact terminal smoke chain for the Agent persistence path:

```text
v2_9_0 SQLite backend store
        ↓ explicit opt-in write gate
v2_9_3 terminal memory autoload preview
        ↓ CLI-only TerminalChatSession memory
ordinary today-practice guidance turn
        ↓
v2_8_17 persisted-context guidance recovery
```

The purpose is developer verification: one command can prove that the real backend store, backend readback, terminal session memory, and display-only “今天该练什么” guidance recovery work together.

## New surfaces

```text
GET  /agent/context/persistence-sqlite-backend-terminal-memory-to-guidance-smoke/spec
POST /agent/context/persistence-sqlite-backend-terminal-memory-to-guidance-smoke/preview
CLI  /sqlite-memory-guidance-smoke [json_payload]
CLI  /context-persistence-sqlite-backend-terminal-memory-to-guidance-smoke [json_payload]
```

## Core functions

```text
build_context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_payload(...)
build_context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_summary(...)
context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke_contract()
```

## Required gates

The smoke chain does not bypass earlier safety gates. SQLite writes only happen through the v2_9_0 explicit backend store gate:

```text
backendPersistenceEnabled=true
executeBackendPersistence=true
userDecision=approved
confirmationStatus=user_approved_future_executor_required
sqliteDbPath=<safe dev/test .sqlite/.db path>
idempotencyKey=<stable idempotency key>
traceId=<trace id>
```

Readback/autoload still requires:

```text
backendReadbackEnabled=true
executeBackendReadback=true
```

For deterministic guidance smoke tests, callers should pass `providerResult` instead of enabling a network provider call.

## Side-effect boundary

Allowed only after explicit gates:

```text
SQLite backend write through v2_9_0
SQLite backend read through v2_9_3
TerminalChatSession.persisted_context_memory update in CLI process only
```

Still forbidden:

```text
HarmonyOS local state write
LLM network call by default
Tool execution
Routine start
/accompaniment/generate
Engine adapter dispatch
MIDI asset creation
Playback start
Post-session recommendation card
```

## Tests

```text
tests/test_v2_9_4_agent_context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke.py
```

Coverage includes:

- contract/spec route metadata;
- blocked smoke without write/readback gates and no DB creation;
- core payload write → read → guidance preview;
- terminal CLI smoke command loading session memory;
- API preview summary without server session-memory mutation;
- runtime/context manifest advertising;
- no Engine import / no shared-doc dependency.

## Verification commands

```bash
PYTHONPATH=src python -m compileall -q src tests tools
PYTHONPATH=src python -m pytest -q tests/test_v2_9_4_agent_context_persistence_sqlite_backend_terminal_memory_to_guidance_smoke.py
PYTHONPATH=src python -m pytest -q tests/test_v2_9_*.py
PYTHONPATH=src python tools/check_development_harness.py
```

## Next recommended task

```text
v2_9_5_agent_context_persistence_sqlite_backend_api_memory_debug_pack
```

Goal: package the v2_9_0 → v2_9_4 backend persistence and recovery routes into a concise API debug pack with request examples, response paths, and frontend-safe contract notes for later HarmonyOS integration testing. Keep it Agent/API-only and avoid editing HarmonyOS fixtures from the Agent branch.
