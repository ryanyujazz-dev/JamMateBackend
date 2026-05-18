# JamMate HarmonyOS API Smoke Pack v2_6_1

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
