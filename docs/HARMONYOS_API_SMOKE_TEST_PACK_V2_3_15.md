# v2_3_15 — HarmonyOS API Smoke Test Pack

This pass adds a copy-friendly smoke-test pack for HarmonyOS and LAN integration. It does not change JamMateEngine music generation behavior.

## Goal

Make it easy to verify the three minimum backend links before deeper UI work:

1. `GET /health`
2. `POST /accompaniment/generate` — direct engine path, no Agent/LLM
3. `POST /agent/playback/prepare` — Agent immediate playback path, loops asset on client until practice timer completes

## New endpoints

```text
GET /agent/contracts/smoke-pack
GET /agent/contracts/smoke-pack/files
```

## Files generated for HarmonyOS

```text
frontend_fixtures/harmonyos/smoke/
  README.md
  curl_smoke.sh
  smoke_pack.json
  smoke_direct_accompaniment_blue_bossa.json
  smoke_agent_playback_blue_bossa.json
  smoke_agent_practice_plan_misty.json
  smoke_session_review.json
```

## Start Python service on Mac

```bash
PYTHONPATH=src uvicorn jammate_api.app:app --host 0.0.0.0 --port 8000
```

## Local terminal smoke

```bash
cd frontend_fixtures/harmonyos/smoke
bash curl_smoke.sh http://127.0.0.1:8000
```

## HarmonyOS phone to Mac LAN

1. Ensure phone and Mac are on the same Wi-Fi.
2. Find Mac LAN IP, for example `ipconfig getifaddr en0`.
3. Start API using `--host 0.0.0.0 --port 8000`.
4. Open Mac firewall for port 8000 if needed.
5. Set HarmonyOS base URL to `http://<MAC_LAN_IP>:8000`.
6. First verify `GET /health`.
7. Then verify direct accompaniment and Agent playback prepare.

## Playback rule

Practice duration is owned by HarmonyOS local timer. The backend returns a playable MIDI asset. If `playback_instruction.client_loop_until_target_duration` is true, HarmonyOS should loop that asset until the local practice timer reaches `targetDurationMinutes` or the user stops playback.

## Architecture reminder

- Direct accompaniment generation remains available without LLM: `/accompaniment/generate`.
- Agent is an enhancement and orchestration path: `/agent/*`.
- Backend canonical responses remain `snake_case`.
- HarmonyOS business models should use camelCase via `CaseAdapter.ets`.
