# v2_10_8 — HarmonyOS Agent Black-Box Contract Fit

This integration pass aligns the merged backend with the updated HarmonyOS Agent API integration report.

## Frontend contract now honored

HarmonyOS product requests do not need backend internals:

- no `dbPath` / `sqliteDbPath`
- no `clientConfirmedRecordWrite`
- no migration or storage gate fields

The backend wrappers own those details.

## Product requests

### Completion record

```json
{
  "userId": "local-dev-user",
  "sessionId": "practice-session-1779200000000",
  "deviceId": "harmonyos-device-local",
  "routineCompletionRecord": {
    "routineId": "routine-xxx",
    "routineTitle": "今日基础练习",
    "completedAt": "2026-05-20T20:30:00-07:00",
    "durationSeconds": 1800,
    "status": "completed",
    "items": [
      {
        "itemId": "item-1",
        "title": "Blue Bossa comping practice",
        "type": "tune_practice",
        "durationSeconds": 900,
        "status": "completed"
      }
    ],
    "notes": "optional user note"
  }
}
```

### Today guidance

```json
{
  "userId": "local-dev-user",
  "sessionId": "agent-session-1779200000000",
  "deviceId": "harmonyos-device-local",
  "userMessage": "今天该练什么？"
}
```

## Backend-owned DB path

The backend resolves the context database path from:

1. explicit debug override fields, when present in tests/smoke only;
2. `JAMMATE_AGENT_CONTEXT_DB_PATH`;
3. local-dev fallback `/tmp/jammate_agent_harmonyos_context.sqlite3`.

## Safety remains unchanged

The wrappers still do not write HarmonyOS local state, start Routine, call `/accompaniment/generate`, call the Engine adapter, create MIDI, or start playback.
