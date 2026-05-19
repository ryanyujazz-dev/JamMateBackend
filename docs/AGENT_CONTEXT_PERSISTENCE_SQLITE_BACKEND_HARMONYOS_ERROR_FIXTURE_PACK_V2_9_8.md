# Agent Context Persistence SQLite Backend HarmonyOS Error Fixture Pack v2_9_8

Status: completed in Agent track.

This pass turns the v2_9_7 SQLite backend API error/blocked response matrix into a HarmonyOS-facing error fixture pack. The pack is intended for frontend/backend联调: developers can copy bad-request examples, expected UI/debug messages, retry policies, and response field assertions without executing any route from the pack builder itself.

## Surfaces

```text
GET  /agent/context/persistence-sqlite-backend-harmonyos-error-fixture-pack/spec
POST /agent/context/persistence-sqlite-backend-harmonyos-error-fixture-pack/preview
CLI  /sqlite-harmonyos-error-fixture-pack [json_payload]
CLI  /context-persistence-sqlite-backend-harmonyos-error-fixture-pack [json_payload]
```

## Purpose

v2_9_7 defines the canonical backend error shapes. v2_9_8 packages those shapes for HarmonyOS API integration work:

```text
missing_write_gate
invalid_sqlite_db_path
empty_readback
idempotent_replay
malformed_payload
```

The pack contains:

```text
bad_request_examples
expected_ui_debug_messages
retry_policy_catalog
response_field_assertion_catalog
harmonyos_error_fixture_pack.curlBadRequestExamples
harmonyos_error_fixture_pack.arktsHandlingSketch
harmonyos_error_fixture_pack.frontendSafeContractNotes
```

## Client handling policy

- `missing_write_gate`: show a gate/confirmation debug message; do not retry automatically until the user/developer enables the explicit backend persistence gates.
- `invalid_sqlite_db_path`: show a developer-path debug message; use a relative path, `/tmp`, or `/mnt/data` SQLite file for development.
- `empty_readback`: show “暂无可恢复练习上下文” and fall back to ordinary “今天该练什么” or request a context save/sync first.
- `idempotent_replay`: treat as success-like; do not show as fatal failure; continue to readback/guidance.
- `malformed_payload`: fix the client request body; it must be a JSON object with `Content-Type: application/json`.

## Boundary

This fixture pack is preview-only:

```text
No packaged route execution.
No SQLite connection/read/write.
No API/server memory mutation.
No TerminalChatSession memory write.
No frontend_fixtures/harmonyos write.
No HarmonyOS local write.
No LLM call.
No tool execution.
No Routine start.
No post-session recommendation card.
No /accompaniment/generate.
No Engine adapter call.
No MIDI asset.
No playback.
No Engine music generation change.
No shared documentation/version file change in Agent track.
```

## Response case policy

HarmonyOS may continue sending camelCase request fields. Backend responses remain canonical snake_case, including fields such as:

```text
validation.status
validation.accepted
validation.blocked_reasons
validation.warnings
storage_written
backend_database_written
backend_database_read
sqlite_connection_created
sqlite_rows_written
sqlite_rows_read
routine_start_enabled
engine_adapter_called
midi_asset_created
playback_started
```

## Implementation files

```text
src/jammate_agent/core/tool_invocation.py
src/jammate_agent/core/context.py
src/jammate_agent/core/contracts.py
src/jammate_agent/cli/terminal_chat.py
src/jammate_api/routes/agent_routes.py
tests/test_v2_9_8_agent_context_persistence_sqlite_backend_harmonyos_error_fixture_pack.py
```

## Verification

```text
PYTHONPATH=src python -m compileall -q src tests tools
PYTHONPATH=src python -m pytest -q tests/test_v2_9_8_agent_context_persistence_sqlite_backend_harmonyos_error_fixture_pack.py
PYTHONPATH=src python -m pytest -q tests/test_v2_9_*.py
PYTHONPATH=src python -m pytest -q tests/test_v2_8_*.py tests/test_v2_9_*.py
PYTHONPATH=src python tools/check_development_harness.py
```

## Next recommended Agent task

```text
v2_9_9_agent_context_persistence_sqlite_backend_handoff_completion_pack
```

Suggested goal: summarize the v2_9_0 → v2_9_8 SQLite backend persistence route family into a compact Agent-track handoff completion pack for integration branch and HarmonyOS联调, without modifying shared frontend fixtures or Engine code.
