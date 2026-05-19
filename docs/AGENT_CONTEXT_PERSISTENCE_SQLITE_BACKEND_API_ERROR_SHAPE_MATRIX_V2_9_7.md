# v2_9_7 Agent Context Persistence SQLite Backend API Error Shape Matrix

## Purpose

`v2_9_7_agent_context_persistence_sqlite_backend_api_error_shape_matrix` stabilizes the blocked/error response shapes for the v2_9 SQLite persistence API family so HarmonyOS and backend联调 can distinguish expected development states from real runtime defects.

This is a preview-only matrix. It does not execute packaged routes, open SQLite, create tables, read/write database rows, mutate API server memory, write terminal session memory, write HarmonyOS local state, call LLM/tools/Engine, start Routine, create MIDI, start playback, or create a post-session recommendation card.

## Surfaces

```text
GET  /agent/context/persistence-sqlite-backend-api-error-shape-matrix/spec
POST /agent/context/persistence-sqlite-backend-api-error-shape-matrix/preview
CLI  /sqlite-api-error-shape-matrix [json_payload]
CLI  /context-persistence-sqlite-backend-api-error-shape-matrix [json_payload]
```

## Covered Scenarios

```text
missing_write_gate
invalid_sqlite_db_path
empty_readback
idempotent_replay
malformed_payload
```

### missing_write_gate

Route:

```text
POST /agent/context/persistence-sqlite-backend-store/execute
```

Expected shape:

```text
validation.status = sqlite_backend_store_blocked
validation.accepted = false
validation.blocked_reasons includes backend_persistence_enabled_must_be_true
validation.blocked_reasons includes execute_backend_persistence_must_be_true
sqlite_connection_created = false
storage_written = false
backend_database_written = false
```

### invalid_sqlite_db_path

Route:

```text
POST /agent/context/persistence-sqlite-backend-store/execute
```

Expected shape:

```text
validation.status = sqlite_backend_store_blocked
validation.accepted = false
validation.blocked_reasons includes sqlite_db_path_must_be_relative_tmp_or_mnt_data_sqlite_file
sqlite_connection_created = false
storage_written = false
backend_database_written = false
```

### empty_readback

Route:

```text
POST /agent/context/persistence-sqlite-backend-readback-context-recovery/preview
```

Expected shape:

```text
validation.status = sqlite_backend_readback_context_recovery_blocked
validation.accepted = false
validation.blocked_reasons includes sqlite_backend_readback_failed:<reason>
backend_database_read = false
sqlite_connection_created = false when the file is missing before open
```

HarmonyOS should display “暂无可恢复练习上下文” and fall back to ordinary today-practice guidance, or ask the user to sync/save context first.

### idempotent_replay

Route:

```text
POST /agent/context/persistence-sqlite-backend-store/execute
```

Expected shape:

```text
validation.status = sqlite_backend_store_idempotent_replay
validation.accepted = true
validation.blocked_reasons = []
idempotent_replay = true
storage_written = false
backend_database_written = false
```

HarmonyOS should treat this as success and continue with readback/guidance; it means the same confirmed write was already stored.

### malformed_payload

Route:

```text
any v2_9 SQLite API route
```

Expected shape:

```text
validation.status = request_body_must_be_json_object
validation.accepted = false
http_status_hint = 422
validation.blocked_reasons includes request_body_must_be_json_object
```

HarmonyOS should fix the client request body before retrying. Request fields may be camelCase; backend response fields remain canonical snake_case.

## Response Case Policy

```text
HarmonyOS request fields: camelCase allowed
Backend response fields: canonical snake_case
```

Important paths to inspect:

```text
*.validation.status
*.validation.accepted
*.validation.blocked_reasons
*.validation.warnings
*.storage_written
*.backend_database_written
*.backend_database_read
*.sqlite_connection_created
*.sqlite_rows_written
*.sqlite_rows_read
*.idempotent_replay
```

## Guardrails

```text
matrix_executes_existing_routes = false
matrix_opens_sqlite = false
matrix_writes_sqlite = false
matrix_reads_sqlite = false
matrix_writes_frontend_fixtures = false
api_surface_mutates_server_memory = false
payload_calls_llm_by_default = false
payload_executes_tool = false
payload_calls_accompaniment_generate = false
payload_calls_engine_adapter = false
payload_creates_midi_asset = false
payload_starts_playback = false
payload_creates_post_session_recommendation_card = false
client_decides_presentation = true
frontend_flow_assumption = false
```

## Tests

```text
PYTHONPATH=src python -m pytest -q tests/test_v2_9_7_agent_context_persistence_sqlite_backend_api_error_shape_matrix.py
```

## Next Recommended Task

```text
v2_9_8_agent_context_persistence_sqlite_backend_harmonyos_error_fixture_pack
```
