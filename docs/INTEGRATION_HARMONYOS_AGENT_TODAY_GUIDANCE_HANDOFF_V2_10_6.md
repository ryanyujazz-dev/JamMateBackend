# Integration Handoff: HarmonyOS Agent Today Guidance v2_10_6

This handoff exposes the usable Agent practice-coach loop to HarmonyOS through two stable wrapper routes.

## Product routes

```text
POST /agent/harmonyos/routine-completion-record/execute
POST /agent/harmonyos/today-practice-guidance/preview
```

## Client flow

1. HarmonyOS completes a local practice session and keeps local timer/playback/session UI state locally.
2. HarmonyOS calls `/agent/harmonyos/routine-completion-record/execute` with `clientConfirmedRecordWrite=true` and an idempotency key.
3. The backend writes only the Agent context record to SQLite.
4. Later, when the user asks “今天该练什么？”, HarmonyOS calls `/agent/harmonyos/today-practice-guidance/preview`.
5. HarmonyOS displays `data.content` and optional routine candidates. Starting a Routine still requires user confirmation.

## Fixture files

```text
frontend_fixtures/harmonyos/api/JamMateApiClient.ets
frontend_fixtures/harmonyos/types/AgentTypes.ets
frontend_fixtures/harmonyos/smoke/smoke_agent_harmonyos_routine_completion_record_execute.json
frontend_fixtures/harmonyos/smoke/smoke_agent_harmonyos_today_practice_guidance_preview.json
frontend_fixtures/harmonyos/smoke/curl_smoke.sh
```

## Safety boundaries

The today-guidance preview route does not write storage. The routine-completion route may write backend SQLite only when explicitly confirmed. Neither route writes HarmonyOS local state, starts a Routine, calls `/accompaniment/generate`, calls the Engine adapter, creates MIDI, starts playback, or creates a practice-end recommendation card.

## Validation

```bash
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python -m pytest -q tests/test_v2_10_6_integration_harmonyos_agent_today_guidance_handoff.py
PYTHONPATH=src python -m pytest -q tests/test_v2_10_*.py
PYTHONPATH=src python -m pytest -q tests/test_v2_8_*.py tests/test_v2_9_*.py tests/test_v2_10_*.py
PYTHONPATH=src python tools/check_development_harness.py
```
