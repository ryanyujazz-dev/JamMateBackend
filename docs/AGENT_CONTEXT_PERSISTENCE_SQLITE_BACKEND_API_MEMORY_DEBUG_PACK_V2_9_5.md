# Agent Context Persistence SQLite Backend API Memory Debug Pack V2.9.5

## Milestone

```text
v2_9_5_agent_context_persistence_sqlite_backend_api_memory_debug_pack
```

This milestone packages the v2.9 SQLite backend persistence / readback / memory / today-practice guidance surfaces into a concise API debug pack for backend-HarmonyOS alignment.

The pack is intentionally preview-only. It does not call the underlying v2.9 routes, does not open SQLite, does not write/read the database, and does not mutate API server memory.

## New surfaces

```text
GET  /agent/context/persistence-sqlite-backend-api-memory-debug-pack/spec
POST /agent/context/persistence-sqlite-backend-api-memory-debug-pack/preview
CLI  /sqlite-api-memory-debug-pack [json_payload]
CLI  /context-persistence-sqlite-backend-api-memory-debug-pack [json_payload]
```

## Packaged route sequence

```text
1. POST /agent/context/persistence-sqlite-backend-store/execute
2. POST /agent/context/persistence-sqlite-backend-readback-context-recovery/preview
3. POST /agent/context/persistence-sqlite-backend-today-guidance-recovery-e2e/preview
4. POST /agent/context/persistence-sqlite-backend-terminal-memory-autoload-preview/preview
5. POST /agent/context/persistence-sqlite-backend-terminal-memory-to-guidance-smoke/preview
```

## Included debug data

The payload includes:

- `route_catalog`: route keys, methods, route paths, purpose, version, and side-effect notes.
- `request_examples`: example request bodies for store, readback, today-guidance recovery, API autoload preview, and smoke preview.
- `response_path_catalog`: frontend-useful response paths to inspect during debugging.
- `terminal_debug_commands`: matching terminal command examples.
- `frontend_safe_contract_notes`: HarmonyOS-facing notes about display-only guidance, CLI-local memory, and forbidden local playback/MIDI/API-key payload fields.

## Side-effect boundary

Always false for this debug pack:

```text
SQLite connection created
SQLite tables created
SQLite rows written
SQLite rows read
backend database written/read
API server memory mutation
HarmonyOS local state write
LLM call
Tool execution
Routine start
/accompaniment/generate
Engine adapter dispatch
MIDI asset creation
Playback start
Post-session recommendation card creation
```

The debug pack may include sample requests that, when sent separately to their own endpoints, could write SQLite through the v2_9_0 explicit opt-in gate. The debug pack itself never executes those requests.

## API memory note

`/agent/context/persistence-sqlite-backend-terminal-memory-autoload-preview/preview` is API preview-only. It returns the TerminalChatSession memory object shape, but it does not mutate server-side memory. Actual terminal memory loading remains CLI-local through `/persisted-context-autoload-sqlite`.

## Tests

```text
tests/test_v2_9_5_agent_context_persistence_sqlite_backend_api_memory_debug_pack.py
```

Coverage includes:

- contract/spec metadata;
- core payload route catalog, request examples, response paths, and redaction;
- API preview no-side-effect behavior;
- terminal command compact status output;
- TerminalChatSession no memory mutation;
- runtime/context manifest exposure;
- no Engine import / no shared-doc dependency.

## Verification commands

```bash
PYTHONPATH=src python -m compileall -q src tests tools
PYTHONPATH=src python -m pytest -q tests/test_v2_9_5_agent_context_persistence_sqlite_backend_api_memory_debug_pack.py
PYTHONPATH=src python -m pytest -q tests/test_v2_9_*.py
PYTHONPATH=src python tools/check_development_harness.py
```

## Next recommended task

```text
v2_9_6_agent_context_persistence_sqlite_backend_harmonyos_api_fixture_pack
```

Goal: create an Agent-owned API fixture pack for HarmonyOS integration testing of the v2_9 SQLite persistence/readback/guidance path. Keep it outside `frontend_fixtures/harmonyos/` from the Agent branch unless the integration branch explicitly owns the shared fixture update.
