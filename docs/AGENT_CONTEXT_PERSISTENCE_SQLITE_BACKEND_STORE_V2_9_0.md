# AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_STORE_V2_9_0

Status: completed in Agent track.

## Goal

Start the v2_9_x Agent Persistence Implementation phase with the first real backend persistence surface:

```text
v2_9_0_agent_context_persistence_sqlite_backend_store
```

This milestone turns the v2_8 persistence design / confirmation / fixture-store chain into an explicit opt-in SQLite backend store for Agent long-term context snapshots.

## Implemented surfaces

```text
GET  /agent/context/persistence-sqlite-backend-store/spec
POST /agent/context/persistence-sqlite-backend-store/execute
CLI  /context-persistence-sqlite-backend-store [json_payload]
```

Core builder:

```text
build_context_persistence_sqlite_backend_store_payload(...)
build_context_persistence_sqlite_backend_store_summary(...)
context_persistence_sqlite_backend_store_contract()
```

Test coverage:

```text
tests/test_v2_9_0_agent_context_persistence_sqlite_backend_store.py
```

## Required gates

A real SQLite write is allowed only when all gates pass:

```text
backendPersistenceEnabled=true
executeBackendPersistence=true
userDecision=approved
confirmationStatus=user_approved_future_executor_required
environment in dev/local_dev/test
sqliteDbPath is relative or /tmp or /mnt/data and ends with .db/.sqlite/.sqlite3
traceId present
idempotencyKey present or derived
storageBoundaryCheckPassed=true
redactionCheckPassed=true
schemaPreviewAccepted=true
```

If any gate fails, the builder returns a blocked payload and does not open/create the SQLite database.

## SQLite schema

The store creates three backend tables after the gates pass:

```text
context_persistence_records
context_persistence_idempotency_keys
context_persistence_trace_links
```

`context_persistence_records` stores the redacted Agent context snapshot JSON.
`context_persistence_idempotency_keys` prevents duplicate writes for repeated requests.
`context_persistence_trace_links` links stored records back to Agent trace IDs.

## Idempotency behavior

The first approved request with a new idempotency key inserts one record, one idempotency row, and one trace-link row.

A repeated request with the same idempotency key returns:

```text
validation.status = sqlite_backend_store_idempotent_replay
idempotent_replay = true
sqlite_rows_written = false
sqlite_row_count_written = 0
readback_record_found = true
```

No duplicate context record is inserted.

## Boundary

Allowed by this milestone:

```text
Backend SQLite context persistence write after explicit gates.
Backend SQLite readback verification after write or idempotent replay.
```

Still forbidden:

```text
No HarmonyOS local write by Agent.
No Routine start.
No post-session recommendation card.
No /accompaniment/generate.
No Engine adapter call.
No MIDI asset creation.
No playback.
No LLM call by the persistence route/CLI.
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
tests/test_v2_9_0_agent_context_persistence_sqlite_backend_store.py
docs/AGENT_CONTEXT_PERSISTENCE_SQLITE_BACKEND_STORE_V2_9_0.md
docs/DEVELOPMENT_TASK_PLAN_AGENT_V2.md
docs/CHANGELOG_AGENT.md
```

No `src/jammate_engine/*` file is modified.

## Regression commands

```bash
PYTHONPATH=src python -m compileall -q src tests tools
PYTHONPATH=src python -m pytest -q tests/test_v2_9_0_agent_context_persistence_sqlite_backend_store.py
PYTHONPATH=src python -m pytest -q \
  tests/test_v2_8_23_agent_v2_8_phase_cleanup_regression_handoff.py \
  tests/test_v2_8_14_agent_context_persistence_dev_sqlite_fixture_store_explicit_opt_in.py \
  tests/test_v2_9_0_agent_context_persistence_sqlite_backend_store.py
PYTHONPATH=src python tools/check_development_harness.py
```

## Next recommended Agent task

```text
v2_9_1_agent_context_persistence_sqlite_backend_readback_context_recovery
```

Suggested scope:

```text
Read persisted records from the v2_9_0 backend SQLite store and transform them into the same persisted-context recovery packet shape used by today-practice guidance, still without LLM/tool/Engine/Routine/playback side effects.
```
