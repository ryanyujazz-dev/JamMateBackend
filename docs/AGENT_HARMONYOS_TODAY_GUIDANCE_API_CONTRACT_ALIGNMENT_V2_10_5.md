# Agent HarmonyOS Today Guidance API Contract Alignment — v2_10_5

## Goal

`v2_10_5_agent_harmonyos_today_guidance_api_contract_alignment` turns the usable Agent loop from internal MVP/smoke routes into HarmonyOS-facing API wrappers.

The product loop is now expressed as two stable frontend routes:

```text
POST /agent/harmonyos/routine-completion-record/execute
POST /agent/harmonyos/today-practice-guidance/preview
```

These wrappers reuse the already tested v2_10_2 and v2_10_3 builders instead of creating another Agent recommendation or persistence system.

## Routes

### Contract alignment

```text
GET  /agent/harmonyos/today-guidance-api-contract-alignment/spec
POST /agent/harmonyos/today-guidance-api-contract-alignment/preview
```

The preview route returns the route catalog, request examples, response fields, safety contract, and frontend/backend state ownership notes.

### Routine completion write

```text
POST /agent/harmonyos/routine-completion-record/execute
```

Minimum request:

```json
{
  "userId": "dev_user",
  "sqliteDbPath": "/tmp/jammate_agent_context.sqlite",
  "environment": "test",
  "clientConfirmedRecordWrite": true,
  "idempotencyKey": "completion:dev_user:session_001",
  "routineCompletionRecord": {
    "sessionId": "session_001",
    "title": "Medium Swing guide-tone comping",
    "actualSeconds": 900,
    "completed": true
  }
}
```

Stable response shape:

```json
{
  "ok": true,
  "code": "routine_completion_record_persisted",
  "message": "...",
  "data": {
    "completionRecordPersisted": true,
    "nextTodayGuidanceCanReadHistory": true,
    "idempotentReplay": false,
    "routineCompletionRecord": {}
  },
  "debug": {
    "underlyingVersion": "v2_10_3",
    "backendDatabaseWritten": true,
    "sqliteRowsWritten": true
  },
  "safety": {
    "backendSQLiteWriteMayOccur": true,
    "writesHarmonyOSLocalState": false,
    "startsRoutine": false,
    "callsEngineAdapter": false,
    "createsMidiAsset": false,
    "startsPlayback": false
  }
}
```

### Today guidance preview

```text
POST /agent/harmonyos/today-practice-guidance/preview
```

Minimum request:

```json
{
  "userId": "dev_user",
  "sqliteDbPath": "/tmp/jammate_agent_context.sqlite",
  "environment": "test",
  "userInput": "今天该练什么？",
  "availableMinutes": 25
}
```

Stable response shape:

```json
{
  "ok": true,
  "code": "today_guidance_ready",
  "message": "...",
  "data": {
    "content": "...",
    "guidancePreviewReady": true,
    "contextSource": "sqlite_backend",
    "actionCardPayload": {},
    "routineCandidateCount": 1,
    "requiresUserConfirmationBeforeRoutineStart": true
  },
  "debug": {
    "underlyingVersion": "v2_10_2",
    "sqliteReadbackAttempted": true,
    "backendDatabaseRead": true,
    "sqliteRowsRead": 2
  },
  "safety": {
    "backendSQLiteWriteMayOccur": false,
    "writesHarmonyOSLocalState": false,
    "startsRoutine": false,
    "callsEngineAdapter": false,
    "createsMidiAsset": false,
    "startsPlayback": false
  }
}
```

## Frontend ownership boundary

HarmonyOS keeps ownership of:

```text
Routine timer
Playback state
Local MIDI/player state
End-of-practice local display
```

The backend Agent owns only backend context persistence when a safe SQLite path and explicit write confirmation are supplied.

## Safety boundary

`/agent/harmonyos/today-practice-guidance/preview`:

```text
may read SQLite context
must not write SQLite
must not start Routine
must not call /accompaniment/generate
must not call Engine adapter
must not create MIDI
must not play
```

`/agent/harmonyos/routine-completion-record/execute`:

```text
may write backend SQLite only after clientConfirmedRecordWrite=true or equivalent explicit write gates
must not write HarmonyOS local state
must not start Routine
must not call /accompaniment/generate
must not call Engine adapter
must not create MIDI
must not play
```

## Tests

```text
PYTHONPATH=src python -m pytest -q tests/test_v2_10_5_agent_harmonyos_today_guidance_api_contract_alignment.py
```

The tests verify:

```text
contract route catalog
camelCase HarmonyOS response shape
completion write wrapper
completion -> guidance readback wrapper
no-context guidance state
manifest/runtime advertisement
no Engine/Routine/MIDI/playback side effects
```

## Next recommended task

```text
integration_handoff_or_v2_10_6_agent_harmonyos_contract_smoke_docs
```

Recommended product direction: move this into an integration task so HarmonyOS can call these two wrapper routes directly instead of the internal v2_10_2/v2_10_3/v2_10_4 routes.
