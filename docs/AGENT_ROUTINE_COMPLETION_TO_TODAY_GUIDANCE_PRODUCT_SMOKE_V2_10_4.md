# Agent Routine Completion → Today Guidance Product Smoke v2.10.4

## Purpose

`v2_10_4_agent_routine_completion_to_today_guidance_product_smoke` closes the first usable Agent product-loop smoke:

```text
existing profile / active plan context
        ↓ optional confirmed one-call seed for smoke testing
client-submitted Routine completion record
        ↓ confirmed backend SQLite context write
ordinary user input: 今天该练什么？
        ↓ SQLite readback through usable guidance MVP
display-only today-practice guidance
```

This is not another preview/debug pack. It is a compact product smoke proving that a completed practice record can affect the next ordinary today-practice guidance turn.

## Routes

```text
GET  /agent/context/routine-completion-to-today-guidance-product-smoke/spec
POST /agent/context/routine-completion-to-today-guidance-product-smoke/execute
```

## Terminal commands

```text
/routine-completion-to-today-guidance-smoke [json_payload]
/completion-guidance-smoke [json_payload]
```

## Minimum request

```json
{
  "sqliteDbPath": "/mnt/data/jammate_agent_context.sqlite",
  "environment": "test",
  "userId": "user_001",
  "clientConfirmedRecordWrite": true,
  "routineCompletionRecord": {
    "sessionId": "session_001",
    "title": "Medium Swing guide-tone comping",
    "style": "medium_swing",
    "actualSeconds": 900,
    "completed": true,
    "completedAtUtc": "2026-05-19T21:00:00+00:00"
  },
  "userInput": "今天该练什么？",
  "providerResult": {
    "ok": true,
    "provider_name": "fixture",
    "model": "fixture-model",
    "content": "{...validated TodayPracticeGuidanceOutput JSON...}"
  }
}
```

## Optional one-call seed

For deterministic local smoke tests, the request may also seed profile/plan context before the completion write:

```json
{
  "seedInitialContext": true,
  "clientConfirmedInitialContextSeed": true,
  "userPracticeProfile": { "userId": "user_001" },
  "practicePlan": { "planId": "plan_001", "status": "active", "planBlocks": [] }
}
```

The seed uses the existing `v2_9_0` SQLite backend store and is guarded by explicit confirmation.

## Acceptance conditions

The smoke is accepted only when:

```text
initial context seed is skipped or accepted
completion record is persisted or idempotently replayed
guidance preview is built
guidance action card is valid
guidance context source is sqlite_backend
recent completion history is read by guidance
```

## Boundaries

Allowed side effects:

```text
confirmed SQLite backend context write for optional seed
confirmed SQLite backend context write for routine completion record
SQLite readback for guidance
```

Still forbidden:

```text
no HarmonyOS local-state write
no tool execution
no Routine start
no /accompaniment/generate
no Engine adapter call
no MIDI asset creation
no playback
no post-session recommendation card
```

## Tests

```text
PYTHONPATH=src python -m pytest -q tests/test_v2_10_4_agent_routine_completion_to_today_guidance_product_smoke.py
PYTHONPATH=src python -m pytest -q tests/test_v2_10_*.py
PYTHONPATH=src python -m pytest -q tests/test_v2_9_*.py tests/test_v2_10_*.py
```

## Next recommended task

```text
integration handoff or v2_10_5_agent_harmonyos_today_guidance_api_contract_alignment
```
