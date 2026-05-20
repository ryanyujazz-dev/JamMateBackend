# AGENT_ROUTINE_COMPLETION_RECORD_TO_BACKEND_CONTEXT_WRITE_MVP_V2_10_3

## Purpose

`v2_10_3_agent_routine_completion_record_to_backend_context_write_mvp` closes the first usable Agent context loop:

```text
Routine completed on client
  -> client submits one routineCompletionRecord
  -> backend persists it as routine_history_records in SQLite context
  -> next ordinary “今天该练什么？” can read the actual completed practice history
```

This milestone intentionally moves away from pure preview/guard packaging. It adds a product-facing write entry for completed practice records while preserving the Agent/Engine boundary.

## New API surface

```text
GET  /agent/context/routine-completion-record-to-backend-context-write-mvp/spec
POST /agent/context/routine-completion-record-to-backend-context-write-mvp/execute
```

The execute route accepts either a direct JSON body or `{ "arguments": { ... } }`.

Minimum useful request:

```json
{
  "sqliteDbPath": "/tmp/jammate_agent_context.sqlite",
  "environment": "test",
  "userId": "user_001",
  "clientConfirmedRecordWrite": true,
  "routineCompletionRecord": {
    "sessionId": "session_001",
    "title": "Medium Swing guide-tone comping",
    "style": "medium_swing",
    "tempo": 104,
    "actualSeconds": 900,
    "completed": true,
    "completedAtUtc": "2026-05-19T20:00:00+00:00",
    "practiceGoal": "稳定 3/7 声部连接"
  }
}
```

## New terminal surface

```text
/routine-completion-record-write [json_payload]
/routine-completion-to-backend-context [json_payload]
```

If `TerminalChatSession` was created with `context_db_path`, the command can omit `sqliteDbPath`.

## Implementation notes

The write MVP does not create a second persistence system. It narrows and composes the existing `v2_9_0` SQLite backend store:

```text
routineCompletionRecord
  -> normalized Routine history record
  -> build_context_persistence_sqlite_backend_store_payload(...)
  -> candidateKind = routine_history_persistence_candidate
  -> entities = [routine_history_records]
```

It also performs a readback verification with the existing `v2_9_1` SQLite backend readback recovery when the write or idempotent replay succeeds.

## Storage semantics

The persisted context entity is:

```text
routine_history_records
```

The normalized record includes:

```text
sessionId
userId
title
style
tempo
actualSeconds
durationMinutes
completed
completedAtUtc
practiceGoal
source
traceId
```

Idempotency defaults to:

```text
routine_completion:{userId}:{sessionId}:{completedAtUtc}
```

Callers may override it with `idempotencyKey`.

## Safety boundary

Allowed side effect:

```text
SQLite backend context write, only after clientConfirmedRecordWrite=true or equivalent explicit v2_9_0 backend persistence gates.
```

Still forbidden:

```text
No HarmonyOS local-state write.
No LLM call.
No tool execution.
No Routine start.
No /accompaniment/generate call.
No Engine adapter call.
No MIDI asset creation.
No playback.
No post-session recommendation card.
```

HarmonyOS should still own the local practice-completion UI and local record display. This backend write only persists Agent context for future guidance.

## Tests

Added:

```text
tests/test_v2_10_3_agent_routine_completion_record_to_backend_context_write_mvp.py
```

Coverage includes:

```text
contract route/spec advertisement
blocked write without confirmation/no DB creation
successful completion record persistence
idempotent replay for same completion record
completion write -> ordinary today guidance reads real history
terminal command with context_db_path
API execute route
context/runtime manifest advertisement
```

## Recommended next task

```text
v2_10_4_agent_routine_completion_to_today_guidance_product_smoke
```

Purpose: package the product smoke path as one developer-facing verification: seed plan/profile context, submit completion record, then ask ordinary “今天该练什么？” and verify the recommendation can adjust based on the completed routine history.
