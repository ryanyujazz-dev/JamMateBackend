# Agent Context Persistence Dev SQLite Explicit Write Gate — v2_8_12

## Scope

`v2_8_12_agent_context_persistence_dev_sqlite_explicit_write_gate` defines the explicit dev-only SQLite write gate and config-path contract for future Agent context persistence.

This version is still side-effect free:

```text
No SQLite connection
No table creation
No row write
No backend database write
No HarmonyOS local write
No LLM call
No tool execution
No Routine start
No /accompaniment/generate
No Engine adapter dispatch
No MIDI asset creation
No playback
No post-session recommendation card
```

## Surfaces

```text
GET  /agent/context/persistence-dev-sqlite-write-gate/spec
POST /agent/context/persistence-dev-sqlite-write-gate/preview
/context-persistence-dev-sqlite-write-gate [json_payload]
```

## Why this step exists

`v2_8_11` exposed the SQLite dev schema/idempotency/trace/snapshot preview. `v2_8_12` adds the explicit switch that a future local dev writer must pass before writing anything.

Even when the gate is accepted, the current version returns:

```text
future_executor_implemented = false
sqlite_write_enabled = false
storage_written = false
```

An accepted gate only means the future executor has enough checked information to proceed in a later version.

## Required future write checks

Future dev writes must require all of the following:

```text
devWriteEnabled = true
userDecision = approved
confirmationStatus = user_approved_future_executor_required
idempotencyKey present
traceId present
sqliteConfigPath present
environment is dev/test/fixture only
storageBoundaryCheckPassed = true
redactionCheckPassed = true
schemaPreviewAccepted = true
```

## Config-path contract

The gate accepts a dev config path, for example:

```json
{
  "devWriteEnabled": true,
  "userDecision": "approved",
  "sqliteConfigPath": "./.jammate/dev_sqlite_context.json",
  "sqliteDbPath": "./.jammate/dev_context.sqlite3",
  "environment": "dev"
}
```

The config is previewed only. No config file is written.

## Redaction and boundary rules

The gate blocks forbidden persistence payload fields, including:

```text
api_key
token
password
midi_base64
local_midi_path
precise_location
payment_info
hidden_chain_of_thought
```

HarmonyOS-local runtime state remains client-owned:

```text
Routine session runtime
playback state
local MIDI cache/path
score viewport
timer / pause / resume
```

## Terminal example

```text
/context-persistence-dev-sqlite-write-gate {"devWriteEnabled":true,"userDecision":"approved","sqliteConfigPath":"./.jammate/dev_sqlite_context.json","traceId":"trace_dev_gate"}
```

Expected summary:

```text
ContextPersistenceDevSqliteWriteGate>
  version: v2_8_12
  validation_status: dev_sqlite_write_gate_ready_future_executor_required
  sqlite_connection_created: false
  sqlite_rows_written: false
  storage_written: false
```

## Next task hint

```text
v2_8_13_agent_context_persistence_dev_sqlite_fixture_write_dry_run
```

The next version can implement a dry-run/fixture write path, but should still keep real durable writes behind explicit test/dev config and confirmation gates.
