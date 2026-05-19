# Integration Runtime Smoke: HarmonyOS Agent Today Guidance v2_10_7

This pass adds a strict runtime smoke for the two HarmonyOS-facing Agent practice-coach routes introduced in `v2_10_6`.

## Product routes under test

```text
POST /agent/harmonyos/routine-completion-record/execute
POST /agent/harmonyos/today-practice-guidance/preview
```

## Start the backend

From the project root:

```bash
PYTHONPATH=src uvicorn jammate_api.app:app --host 0.0.0.0 --port 8000
```

## Run the strict runtime smoke

From `frontend_fixtures/harmonyos/smoke`:

```bash
bash curl_agent_today_guidance_runtime_smoke.sh \
  http://127.0.0.1:8000 \
  /tmp/jammate_agent_harmonyos_today_guidance_runtime_smoke.sqlite
```

For a phone-to-Mac run, replace `127.0.0.1` with the Mac LAN IP while keeping the Python service on `--host 0.0.0.0`.

## What the script verifies

1. `GET /health` succeeds.
2. `POST /agent/harmonyos/routine-completion-record/execute` returns:
   - `ok=true`
   - `code=routine_completion_record_persisted`
   - `data.completionRecordPersisted=true`
   - `data.nextTodayGuidanceCanReadHistory=true`
   - `debug.backendDatabaseWritten=true`
   - HarmonyOS/Engine/playback safety flags remain false.
3. `POST /agent/harmonyos/today-practice-guidance/preview` returns:
   - `ok=true`
   - `code=today_guidance_ready`
   - `data.guidancePreviewReady=true`
   - `data.contextSource=sqlite_backend`
   - `debug.backendDatabaseRead=true`
   - `debug.sqliteRowsRead>=1`
   - `data.requiresUserConfirmationBeforeRoutineStart=true`
   - write/playback/Engine safety flags remain false.

## Boundary

The strict runtime smoke intentionally does not call:

```text
/accompaniment/generate
/agent/playback/prepare
```

The only allowed backend side effect is the explicit SQLite context write in the completion-record step. HarmonyOS local state, Routine start, Engine adapter calls, MIDI generation, playback start, and practice-end recommendation cards remain outside this smoke.

## Validation

```bash
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python -m pytest -q tests/test_v2_10_7_integration_harmonyos_agent_today_guidance_runtime_smoke.py
PYTHONPATH=src python -m pytest -q tests/test_v2_10_*.py
PYTHONPATH=src python -m pytest -q tests/test_v2_8_*.py tests/test_v2_9_*.py tests/test_v2_10_*.py
PYTHONPATH=src python tools/check_development_harness.py
```
