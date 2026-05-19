# JamMate HarmonyOS API Smoke Pack v2_8_24

This folder contains the minimal payloads and commands for testing the Python API from HarmonyOS or from a Mac terminal.

## Start Python service on Mac

```bash
PYTHONPATH=src uvicorn jammate_api.app:app --host 0.0.0.0 --port 8000
```

## Local Mac test

```bash
cd frontend_fixtures/harmonyos/smoke
bash curl_smoke.sh http://127.0.0.1:8000
```

## Phone / HarmonyOS to Mac LAN test

1. Make sure phone and Mac are on the same Wi-Fi.
2. Find Mac LAN IP, for example `ipconfig getifaddr en0`.
3. Start API with `--host 0.0.0.0 --port 8000`.
4. Open Mac firewall for port 8000 if needed.
5. Use base URL `http://<MAC_LAN_IP>:8000` in HarmonyOS.
6. First verify `GET /health`.

## Minimum smoke sequence

1. `GET /health`
2. `POST /accompaniment/generate` using `smoke_direct_accompaniment_blue_bossa.json`
3. `POST /agent/playback/prepare` using `smoke_agent_playback_blue_bossa.json`

## Playback rule

Practice duration is owned by HarmonyOS local timer. The returned MIDI asset should be looped when `playbackInstruction.clientLoopUntilTargetDuration === true`.


## HarmonyOS Agent today guidance integration smoke

`v2_10_6` adds two product-facing Agent routes for the practice-coach loop:

```text
POST /agent/harmonyos/routine-completion-record/execute
POST /agent/harmonyos/today-practice-guidance/preview
```

Recommended integration sequence:

1. Practice ends in HarmonyOS.
2. HarmonyOS keeps its local completion UI/timer state locally.
3. HarmonyOS calls `routine-completion-record/execute` with `clientConfirmedRecordWrite=true` to persist a backend context record.
4. When the user later asks “今天该练什么？”, HarmonyOS calls `today-practice-guidance/preview`.
5. HarmonyOS displays `data.content` and routine candidates, but must still ask for user confirmation before starting any Routine/playback.

The provided smoke payloads use `/tmp/jammate_agent_harmonyos_today_guidance_smoke.sqlite` and may write a local SQLite file on the Python backend machine. They do not write HarmonyOS local state, start a Routine, call `/accompaniment/generate`, create MIDI, or start playback.

```bash
bash curl_smoke.sh http://127.0.0.1:8000
```

For a strict runtime smoke that only hits the two HarmonyOS Agent routes and asserts the returned JSON fields, run:

```bash
bash curl_agent_today_guidance_runtime_smoke.sh \
  http://127.0.0.1:8000 \
  /tmp/jammate_agent_harmonyos_today_guidance_runtime_smoke.sqlite
```

This strict script intentionally does not call `/accompaniment/generate` or any playback route. It writes only the backend SQLite context record when the fixture includes `clientConfirmedRecordWrite=true`, then verifies the next today-guidance preview reads that record back from SQLite.

## v2_10_8 product payload alignment

The actual HarmonyOS frontend treats the Agent backend as a black-box HTTP API.
Product UI requests should omit backend internals:

- no `dbPath` / `sqliteDbPath`
- no `clientConfirmedRecordWrite`
- no migration or storage gate fields

Use these copyable product fixtures for frontend contract checks:

```text
smoke_agent_harmonyos_routine_completion_record_execute_product.json
smoke_agent_harmonyos_today_practice_guidance_preview_product.json
```

The backend resolves the context database path from `JAMMATE_AGENT_CONTEXT_DB_PATH`, or falls back to `/tmp/jammate_agent_harmonyos_context.sqlite3` in local development.
