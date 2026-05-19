# AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_TODAY_GUIDANCE_RECOVERY_E2E_V2_9_2

Status: completed in Agent track.

## Goal

Continue the v2_9_x Agent Persistence Implementation phase after the v2_9_1 SQLite backend readback bridge:

```text
v2_9_2_agent_context_persistence_sqlite_backend_today_guidance_recovery_e2e
```

This milestone composes the real backend SQLite readback path with the existing today-practice guidance persisted-context recovery path.

## Implemented surfaces

```text
GET  /agent/context/persistence-sqlite-backend-today-guidance-recovery-e2e/spec
POST /agent/context/persistence-sqlite-backend-today-guidance-recovery-e2e/preview
CLI  /context-persistence-sqlite-backend-today-guidance-recovery-e2e [json_payload]
```

Core builder:

```text
build_context_persistence_sqlite_backend_today_guidance_recovery_e2e_payload(...)
build_context_persistence_sqlite_backend_today_guidance_recovery_e2e_summary(...)
context_persistence_sqlite_backend_today_guidance_recovery_e2e_contract()
```

Test coverage:

```text
tests/test_v2_9_2_agent_context_persistence_sqlite_backend_today_guidance_recovery_e2e.py
```

## E2E flow

```text
v2_9_0 SQLite backend store
        ↓ existing persisted records
v2_9_1 read-only SQLite backend context recovery
        ↓ ContextBuilder-ready contextPersistenceSnapshotContextIntake
v2_8_17 persisted-context today-practice guidance recovery
        ↓
display-only today-practice guidance / Routine candidate preview
```

## Required readback gates

The first stage reuses the same readback gates as v2_9_1:

```text
backendReadbackEnabled=true
executeBackendReadback=true
environment in dev/local_dev/test
sqliteDbPath is relative or /tmp or /mnt/data and ends with .db/.sqlite/.sqlite3
optional idempotencyKey / traceId / userId / candidate filters
no forbidden client-local/MIDI/API-key fields
```

The SQLite connection remains read-only. Missing databases are blocked without creating a file.

## Boundary

Allowed by this milestone:

```text
Read existing backend SQLite context records after explicit readback gates.
Convert recovered profile / active plan / routine history into today-practice guidance context.
Return display-only guidance and Routine candidate preview.
```

Still forbidden:

```text
No backend SQLite write.
No SQLite table creation.
No HarmonyOS local write by Agent.
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
Default callProvider=false.
A bounded provider preview path can still be explicitly requested by the caller, following the existing v2_8_17 / v2_8_3 guidance boundary.
```

## Agent/Engine boundary

This milestone stays inside the Agent track:

```text
src/jammate_agent/core/tool_invocation.py
src/jammate_agent/core/context.py
src/jammate_agent/core/contracts.py
src/jammate_agent/cli/terminal_chat.py
src/jammate_api/routes/agent_routes.py
tests/test_v2_9_2_agent_context_persistence_sqlite_backend_today_guidance_recovery_e2e.py
docs/AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_TODAY_GUIDANCE_RECOVERY_E2E_V2_9_2.md
docs/DEVELOPMENT_TASK_PLAN_AGENT_V2.md
docs/CHANGELOG_AGENT.md
```

No `src/jammate_engine/*` file is modified.

## Regression commands

```bash
PYTHONPATH=src python -m compileall -q src tests tools
PYTHONPATH=src python -m pytest -q tests/test_v2_9_2_agent_context_persistence_sqlite_backend_today_guidance_recovery_e2e.py
PYTHONPATH=src python -m pytest -q \
  tests/test_v2_8_17_agent_today_practice_guidance_persisted_context_recovery_e2e.py \
  tests/test_v2_9_0_agent_context_persistence_sqlite_backend_store.py \
  tests/test_v2_9_1_agent_context_persistence_sqlite_backend_readback_context_recovery.py \
  tests/test_v2_9_2_agent_context_persistence_sqlite_backend_today_guidance_recovery_e2e.py
PYTHONPATH=src python tools/check_development_harness.py
```

## Next recommended Agent task

```text
v2_9_3_agent_context_persistence_sqlite_backend_terminal_memory_autoload_preview
```

Suggested scope:

```text
Let terminal chat optionally load the v2_9_2 recovered SQLite guidance context into its session memory preview path, so a following ordinary “今天该练什么” turn can reuse recovered backend context without manually pasting the recovery packet. Keep it explicit, read-only, display-only, and side-effect-free.
```
