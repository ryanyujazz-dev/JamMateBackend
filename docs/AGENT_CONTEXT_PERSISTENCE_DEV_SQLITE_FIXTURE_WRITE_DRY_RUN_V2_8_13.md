# Agent Context Persistence Dev SQLite Fixture Write Dry-run — v2_8_13

## Status

This is an Agent-track contract surface only.

It simulates the shape of a future dev-only SQLite fixture write, but it does not open SQLite, create tables, write rows, or persist backend storage.

## Surfaces

```text
GET  /agent/context/persistence-dev-sqlite-fixture-write-dry-run/spec
POST /agent/context/persistence-dev-sqlite-fixture-write-dry-run/preview
/context-persistence-dev-sqlite-fixture-write-dry-run [json_payload]
```

## Purpose

v2_8_13 sits after:

```text
v2_8_10 storage adapter design
v2_8_11 SQLite dev preview
v2_8_12 explicit write gate
```

It previews the future writer flow:

```text
approved persistence candidate
→ idempotency check preview
→ simulated transaction begin
→ sanitized fixture row plan
→ trace-link preview
→ read-back snapshot preview
→ no-write report
```

## Required gates

The dry-run accepts only a safe dev/test fixture shape:

```text
userDecision = approved
confirmationStatus = user_approved_future_executor_required
environment = dev | local_dev | test | fixture
dryRunEnabled = true
storageBoundaryCheckPassed = true
redactionCheckPassed = true
schemaPreviewAccepted = true
```

`sqliteConfigPath` is recommended, but missing config path only produces a warning in this dry-run version because no write is performed.

## Explicit non-goals

v2_8_13 does not:

```text
create SQLite connection
create tables
write rows
commit transactions
write backend database
write HarmonyOS local state
call LLM
execute tools
start Routine
call /accompaniment/generate
call Engine adapter
generate MIDI
start playback
generate post-session recommendation card
```

## Storage boundary

Allowed future backend entities are limited to sanitized long-term context:

```text
user_practice_profile
active_practice_plan / practice_plan
routine_history_summary
agent_trace_metadata
idempotency_record
```

Client-owned HarmonyOS local state remains outside this adapter:

```text
Routine session runtime
playback state
local MIDI cache/path
score viewport
timer / pause / resume
```

## Example

```text
/context-persistence-dev-sqlite-fixture-write-dry-run {"userDecision":"approved","sqliteConfigPath":"./.jammate/dev_sqlite_context.json","traceId":"trace_fixture_dry_run"}
```

Expected outcome:

```text
validation_status: fixture_write_dry_run_ready
transaction_simulated: true
read_back_simulated: true
sqlite_connection_created: false
sqlite_rows_written: false
fixture_write_executed: false
storage_written: false
```

## Next recommended task

```text
v2_8_14_agent_context_persistence_dev_sqlite_fixture_store_explicit_opt_in
```

The next version may introduce an explicit opt-in fixture store, but it should still remain dev-only and require approval, idempotency, trace-link, redaction, and storage-boundary checks.
