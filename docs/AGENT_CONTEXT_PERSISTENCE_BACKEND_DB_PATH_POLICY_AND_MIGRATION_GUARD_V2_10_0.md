# AGENT_CONTEXT_PERSISTENCE_BACKEND_DB_PATH_POLICY_AND_MIGRATION_GUARD_V2_10_0

## Status

Completed in Agent track.

## Goal

Start the `v2_10_x` backend persistence hardening phase after the `v2_9_x` SQLite persistence handoff.

This milestone adds a preview-only guard that evaluates:

- proposed SQLite backend DB path policy;
- declared Agent context SQLite schema version;
- migration mode / schema creation intent;
- operational observability requirements for future real backend persistence.

The guard is intended to be used by integration/backend联调 before any production-like SQLite persistence path is enabled.

## New surfaces

```text
GET  /agent/context/persistence-backend-db-path-policy-migration-guard/spec
POST /agent/context/persistence-backend-db-path-policy-migration-guard/preview
CLI  /sqlite-db-policy-guard [json_payload]
CLI  /context-persistence-backend-db-path-policy-migration-guard [json_payload]
```

## Current schema policy

```text
current_schema_version = agent_context_sqlite_schema_v1
```

Required v1 tables:

```text
context_persistence_records
context_persistence_idempotency_keys
context_persistence_trace_links
```

This milestone does not create or inspect those tables. It only previews whether the declared schema/migration intent is acceptable.

## DB path policy

Allowed in Agent `v2_10_0`:

```text
relative project/dev path
/tmp/*.db|*.sqlite|*.sqlite3
/mnt/data/*.db|*.sqlite|*.sqlite3
```

Blocked:

```text
missing sqliteDbPath
parent traversal such as ../
production/staging env
paths containing production/prod/secrets/private_key/api_key/token
absolute paths outside /tmp/ and /mnt/data/
non-SQLite extensions
```

Production DB path policy remains explicitly disabled in Agent track until integration/backend ownership is defined.

## Migration policy

Allowed preview modes:

```text
disabled_preview
read_only_existing
create_if_missing_dev_only
```

Forbidden:

```text
force/drop/truncate/reset/destructive/auto_migrate_prod style modes
automatic production migration
legacy schema upgrade without a future migration registry
```

`create_if_missing_dev_only` is only an intent preview. This surface does not create a database or schema.

## No-side-effect boundary

This guard is preview-only:

```text
No SQLite connection.
No SQLite read.
No SQLite write.
No SQLite table creation.
No migration execution.
No API/server memory mutation.
No TerminalChatSession memory mutation.
No frontend_fixtures/harmonyos write.
No HarmonyOS local state write.
No LLM call.
No tool execution.
No Routine start.
No post-session recommendation card.
No /accompaniment/generate call.
No Engine adapter call.
No MIDI asset creation.
No playback.
No Engine music-generation change.
No shared README/agent.md/VERSION/pyproject/shared-doc change in Agent track.
```

## Recommended request

```json
{
  "traceId": "trace_backend_policy_guard_dev",
  "environment": "integration_dev",
  "sqliteDbPath": "/mnt/data/jammate_agent_context.sqlite",
  "declaredSchemaVersion": "agent_context_sqlite_schema_v1",
  "migrationMode": "create_if_missing_dev_only",
  "migrationPlanId": "migration_plan_v2_10_0_dev_create_if_missing"
}
```

## Expected ready response fields

```text
context_persistence_backend_db_path_policy_and_migration_guard_summary.validation_status
  = backend_db_path_policy_and_migration_guard_ready

context_persistence_backend_db_path_policy_and_migration_guard_summary.db_path_policy_passed
  = true

context_persistence_backend_db_path_policy_and_migration_guard_summary.schema_guard_passed
  = true

context_persistence_backend_db_path_policy_and_migration_guard_summary.migration_guard_passed
  = true

sqlite_connection_created = false
sqlite_tables_created = false
sqlite_rows_written = false
migration_execution_performed = false
storage_written = false
backend_database_written = false
backend_database_read = false
```

## Next recommended task

```text
v2_10_1_agent_context_persistence_backend_schema_metadata_table_preview
```

That should define the future metadata table / schema registry preview before any real migration execution is introduced.
