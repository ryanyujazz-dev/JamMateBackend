# v2_9_6 Agent Context Persistence SQLite Backend HarmonyOS API Fixture Pack

Status: completed in Agent track.

## Goal

Provide a HarmonyOS-facing API fixture pack for the v2_9 SQLite backend context persistence route family, without touching shared integration files.

This pack is meant for frontend/backend联调. It converts the existing v2_9_0 → v2_9_5 SQLite persistence/readback/memory/guidance route catalog into:

- copyable API request examples
- expected response key/assertion catalog
- curl examples
- ArkTS fetch sketch
- manual debug order
- frontend-safe boundary notes

## New surfaces

```text
GET  /agent/context/persistence-sqlite-backend-harmonyos-api-fixture-pack/spec
POST /agent/context/persistence-sqlite-backend-harmonyos-api-fixture-pack/preview
CLI  /sqlite-harmonyos-api-fixture-pack [json_payload]
CLI  /context-persistence-sqlite-backend-harmonyos-api-fixture-pack [json_payload]
```

## Packaged routes

```text
POST /agent/context/persistence-sqlite-backend-store/execute
POST /agent/context/persistence-sqlite-backend-readback-context-recovery/preview
POST /agent/context/persistence-sqlite-backend-today-guidance-recovery-e2e/preview
POST /agent/context/persistence-sqlite-backend-terminal-memory-autoload-preview/preview
POST /agent/context/persistence-sqlite-backend-terminal-memory-to-guidance-smoke/preview
POST /agent/context/persistence-sqlite-backend-api-memory-debug-pack/preview
```

## Boundary

The fixture pack itself is preview-only.

It does **not**:

```text
open SQLite
create SQLite tables
write SQLite
read SQLite
call packaged routes
mutate API/server memory
write TerminalChatSession memory
write HarmonyOS local state
write frontend_fixtures/harmonyos/
write fixture files
call LLM
execute tools
start Routine
call /accompaniment/generate
call Engine adapter
generate MIDI
start playback
create post-session recommendation card
```

The generated store/smoke request examples are copyable, but if a developer executes them manually they still must pass the existing v2_9_0 explicit opt-in persistence gates.

## HarmonyOS contract notes

- HarmonyOS may send camelCase fields; Agent routes accept camelCase/snake_case aliases where needed.
- Backend responses remain canonical snake_case.
- HarmonyOS should map response fields to camelCase client-side if desired.
- Preview responses are display-only and must not start Routine/playback by themselves.
- Do not persist or send `midiBase64`, local MIDI paths, raw API keys, hidden reasoning, or local playback state in context persistence payloads.

## Files changed

```text
src/jammate_agent/core/tool_invocation.py
src/jammate_agent/core/context.py
src/jammate_agent/core/contracts.py
src/jammate_agent/cli/terminal_chat.py
src/jammate_api/routes/agent_routes.py
tests/test_v2_9_6_agent_context_persistence_sqlite_backend_harmonyos_api_fixture_pack.py
docs/AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_HARMONYOS_API_FIXTURE_PACK_V2_9_6.md
docs/DEVELOPMENT_TASK_PLAN_AGENT_V2.md
docs/CHANGELOG_AGENT.md
```

## Tests

```text
PYTHONPATH=src python -m compileall -q src tests
PYTHONPATH=src python -m pytest -q tests/test_v2_9_6_agent_context_persistence_sqlite_backend_harmonyos_api_fixture_pack.py
PYTHONPATH=src python -m pytest -q tests/test_v2_9_*.py
PYTHONPATH=src python -m pytest -q tests/test_v2_8_*.py tests/test_v2_9_*.py
PYTHONPATH=src python tools/check_development_harness.py
```

## Next recommended Agent task

```text
v2_9_7_agent_context_persistence_sqlite_backend_api_error_shape_matrix
```

Rationale: after request fixture alignment, the next useful frontend/API step is to document and test blocked/error response shapes for missing gates, missing DB path, empty readback, idempotent replay, and malformed payloads so HarmonyOS can render precise debug messages.
