# AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_READBACK_CONTEXT_RECOVERY_V2_9_1

Status: completed in Agent track.

## Goal

Continue the v2_9_x Agent Persistence Implementation phase after the v2_9_0 SQLite backend store:

```text
v2_9_1_agent_context_persistence_sqlite_backend_readback_context_recovery
```

This milestone adds a read-only recovery bridge from the real backend SQLite store into the same snapshot-context-intake packet shape already used by today-practice guidance persisted-context recovery.

## Implemented surfaces

```text
GET  /agent/context/persistence-sqlite-backend-readback-context-recovery/spec
POST /agent/context/persistence-sqlite-backend-readback-context-recovery/preview
CLI  /context-persistence-sqlite-backend-readback-context-recovery [json_payload]
```

Core builder:

```text
build_context_persistence_sqlite_backend_readback_context_recovery_payload(...)
build_context_persistence_sqlite_backend_readback_context_recovery_summary(...)
context_persistence_sqlite_backend_readback_context_recovery_contract()
```

Test coverage:

```text
tests/test_v2_9_1_agent_context_persistence_sqlite_backend_readback_context_recovery.py
```

## Required readback gates

Readback is allowed only when all gates pass:

```text
backendReadbackEnabled=true
executeBackendReadback=true
environment in dev/local_dev/test
sqliteDbPath is relative or /tmp or /mnt/data and ends with .db/.sqlite/.sqlite3
optional idempotencyKey / traceId / userId / candidate filters
no forbidden client-local/MIDI/API-key fields
```

The route opens the existing database in SQLite read-only mode. Missing databases are blocked without creating a file.

## Recovery flow

```text
v2_9_0 context_persistence_records
        ↓ read-only query
redacted persisted record JSON
        ↓ extract profile / active plan / routine history sections
v2_8_16 snapshot context intake
        ↓
ContextBuilder-ready context_persistence_snapshot_context_intake section
        ↓
ready to pass into v2_8_17 today-practice guidance persisted-context recovery
```

The recovery payload includes `recovery_packet_preview.context_persistence_snapshot_context_intake`, which can be passed as `contextPersistenceSnapshotContextIntake` into the existing today-practice guidance recovery preview.

## Boundary

Allowed by this milestone:

```text
Read existing backend SQLite context persistence records.
Build a ContextBuilder-ready recovery packet from recovered profile / plan / history data.
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
No LLM call by the readback route/CLI.
No tool execution.
No production persistence environment enablement.
No Engine music-generation change.
No frontend_fixtures/harmonyos change.
```

## Agent/Engine boundary

This milestone stays inside the Agent track:

```text
src/jammate_agent/core/tool_invocation.py
src/jammate_agent/core/context.py
src/jammate_agent/core/contracts.py
src/jammate_agent/cli/terminal_chat.py
src/jammate_api/routes/agent_routes.py
tests/test_v2_9_1_agent_context_persistence_sqlite_backend_readback_context_recovery.py
docs/AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_READBACK_CONTEXT_RECOVERY_V2_9_1.md
docs/DEVELOPMENT_TASK_PLAN_AGENT_V2.md
docs/CHANGELOG_AGENT.md
```

No `src/jammate_engine/*` file is modified.

## Regression commands

```bash
PYTHONPATH=src python -m compileall -q src tests tools
PYTHONPATH=src python -m pytest -q tests/test_v2_9_1_agent_context_persistence_sqlite_backend_readback_context_recovery.py
PYTHONPATH=src python -m pytest -q \
  tests/test_v2_9_0_agent_context_persistence_sqlite_backend_store.py \
  tests/test_v2_9_1_agent_context_persistence_sqlite_backend_readback_context_recovery.py
PYTHONPATH=src python tools/check_development_harness.py
```

## Next recommended Agent task

```text
v2_9_2_agent_context_persistence_sqlite_backend_today_guidance_recovery_e2e
```

Suggested scope:

```text
Compose v2_9_1 SQLite backend readback recovery with the existing v2_8_17 today-practice guidance persisted-context recovery preview, still without LLM/tool/Engine/Routine/playback side effects unless explicitly requested through the already bounded provider preview path.
```
