# AGENT_CONTEXT_PERSISTENCE_BACKEND_SCHEMA_METADATA_TABLE_PREVIEW_V2_10_1

## Status

Completed in Agent track.

## Goal

Define the future SQLite backend schema metadata / migration registry tables before any real schema creation or migration execution is introduced.

This milestone follows `v2_10_0_agent_context_persistence_backend_db_path_policy_and_migration_guard` and composes that guard as a prerequisite. It remains preview-only.

## New surfaces

```text
GET  /agent/context/persistence-backend-schema-metadata-table-preview/spec
POST /agent/context/persistence-backend-schema-metadata-table-preview/preview
CLI  /sqlite-schema-metadata-preview [json_payload]
CLI  /context-persistence-backend-schema-metadata-table-preview [json_payload]
```

## Metadata schema version

```text
agent_context_sqlite_schema_metadata_v1
```

Current core context schema remains:

```text
agent_context_sqlite_schema_v1
```

## Previewed metadata tables

```text
context_persistence_schema_metadata
context_persistence_migration_registry
context_persistence_schema_validation_events
```

These tables are returned as schema/DDL previews only. This milestone does not create them.

### context_persistence_schema_metadata

Purpose: record current backend schema state.

Required columns:

```text
schema_key
schema_version
metadata_schema_version
applied_migration_id
schema_status
created_at_utc
updated_at_utc
last_validated_at_utc
schema_checksum
notes_json
```

### context_persistence_migration_registry

Purpose: append-only registry for future migration plan/results.

Required columns:

```text
migration_id
from_schema_version
to_schema_version
metadata_schema_version
migration_mode
migration_status
planned_at_utc
applied_at_utc
rollback_supported
destructive_migration
migration_checksum
notes_json
```

### context_persistence_schema_validation_events

Purpose: append-only validation observations for integration/backend diagnostics.

Required columns:

```text
validation_event_id
schema_version
metadata_schema_version
validation_status
validated_at_utc
table_count
missing_tables_json
warning_count
trace_id
notes_json
```

## Request example

```json
{
  "previewId": "ctx_backend_schema_metadata_preview_dev",
  "traceId": "trace_backend_schema_metadata_preview_dev",
  "environment": "integration_dev",
  "sqliteDbPath": "/mnt/data/jammate_agent_context.sqlite",
  "declaredSchemaVersion": "agent_context_sqlite_schema_v1",
  "metadataSchemaVersion": "agent_context_sqlite_schema_metadata_v1",
  "migrationMode": "create_if_missing_dev_only",
  "migrationPlanId": "migration_plan_v2_10_1_metadata_preview",
  "metadataTablePreviewAccepted": true,
  "migrationRegistryPreviewAccepted": true,
  "schemaValidationEventPreviewAccepted": true
}
```

## Expected ready response fields

```text
context_persistence_backend_schema_metadata_table_preview_summary.validation_status
  = backend_schema_metadata_table_preview_ready

context_persistence_backend_schema_metadata_table_preview_summary.metadata_schema_version
  = agent_context_sqlite_schema_metadata_v1

context_persistence_backend_schema_metadata_table_preview_summary.required_metadata_tables
  includes context_persistence_schema_metadata
  includes context_persistence_migration_registry
  includes context_persistence_schema_validation_events

sqlite_connection_created = false
sqlite_tables_created = false
sqlite_rows_written = false
migration_execution_performed = false
schema_creation_performed = false
storage_written = false
backend_database_written = false
backend_database_read = false
```

## No-side-effect boundary

```text
No SQLite connection.
No SQLite read.
No SQLite write.
No SQLite table creation.
No migration execution.
No schema creation.
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

## Next recommended task

```text
v2_10_2_agent_context_persistence_backend_schema_metadata_migration_dry_run_plan
```

That should turn this table preview into a deterministic migration dry-run plan while still avoiding real schema creation.
