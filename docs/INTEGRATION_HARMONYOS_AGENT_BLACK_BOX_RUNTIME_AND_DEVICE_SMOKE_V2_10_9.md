# v2_10_9 — Integration HarmonyOS Agent Black-Box Runtime and Device Smoke

## Purpose

This pass turns the v2_10_8 black-box API contract into a runtime/device smoke pack that HarmonyOS and backend developers can run without exposing backend internals to the frontend.

The smoke validates the actual product contract:

```text
POST /agent/harmonyos/routine-completion-record/execute
POST /agent/harmonyos/today-practice-guidance/preview
```

HarmonyOS product requests do not send:

```text
dbPath
sqliteDbPath
clientConfirmedRecordWrite
internal write gate
migration guard fields
```

The backend wrapper owns the SQLite path and internal write gate. The frontend owns only user/session/device fields, `routineCompletionRecord`, and `userMessage`.

## Added files

```text
frontend_fixtures/harmonyos/smoke/product_contract_routine_completion_request.json
frontend_fixtures/harmonyos/smoke/product_contract_today_guidance_request.json
frontend_fixtures/harmonyos/smoke/curl_agent_black_box_product_contract_smoke.sh
tests/test_v2_10_9_integration_harmonyos_agent_black_box_runtime_and_device_smoke.py
docs/INTEGRATION_HARMONYOS_AGENT_BLACK_BOX_RUNTIME_AND_DEVICE_SMOKE_V2_10_9.md
```

## Runtime smoke sequence

```text
1. GET /health
2. POST /agent/harmonyos/routine-completion-record/execute
3. POST /agent/harmonyos/today-practice-guidance/preview
```

The script asserts:

```text
routine completion:
  ok=true
  code=routine_completion_record_persisted
  data.completionRecordPersisted=true
  data.nextTodayGuidanceCanReadHistory=true
  debug.backendDatabaseWritten=true

today guidance:
  ok=true
  code=today_guidance_ready or today_guidance_needs_context_or_provider
  data.content is non-empty
  data.contextSource=sqlite_backend
  debug.backendDatabaseRead=true
  debug.sqliteRowsRead>=1

safety:
  writesHarmonyOSLocalState=false
  startsRoutine=false
  callsEngineAdapter=false
  createsMidiAsset=false
  startsPlayback=false
  createsPostSessionRecommendationCard=false
```

`today_guidance_needs_context_or_provider` is accepted in local smoke when no real LLM/provider is configured. The important black-box contract assertion is that the product request reaches the backend, the backend reads persisted context, and the response remains display-only and safe.

## Local Mac smoke

From the project root:

```bash
export JAMMATE_AGENT_CONTEXT_DB_PATH=/tmp/jammate_agent_black_box_product_contract_smoke.sqlite3
PYTHONPATH=src uvicorn jammate_api.app:app --host 0.0.0.0 --port 8000
```

From another terminal:

```bash
cd frontend_fixtures/harmonyos/smoke
bash curl_agent_black_box_product_contract_smoke.sh http://127.0.0.1:8000
```

## HarmonyOS phone-to-Mac LAN smoke

1. Put the phone and Mac on the same Wi-Fi.
2. Start FastAPI on Mac with `--host 0.0.0.0 --port 8000`.
3. Open Mac firewall for port `8000` if needed.
4. Find Mac LAN IP, for example `ipconfig getifaddr en0`.
5. Set HarmonyOS baseUrl to `http://<MAC_LAN_IP>:8000`, for example `http://192.168.1.16:8000`.
6. Do not use `127.0.0.1` on the phone; that points to the phone itself.
7. First open `http://<MAC_LAN_IP>:8000/health` in the phone browser.
8. Then test the two Agent product routes.

## Frontend Claude minimum summary

```text
You only need the HarmonyOS product API contract.

Backend product APIs:
POST /agent/harmonyos/routine-completion-record/execute
POST /agent/harmonyos/today-practice-guidance/preview

Do not send dbPath/sqliteDbPath.
Do not send clientConfirmedRecordWrite/internal gate.
For practice completion, send routineCompletionRecord after the real Routine end event.
For today guidance, send userMessage when the user asks “今天该练什么？”.
Read ok/code/message/data for product UI. debug/safety are for diagnostics and safety assertions.
Routine completion should be bound to RoutineFocusPage / Player Practice Mode / RoutineSummaryPage, not to a fake button.
Do not show a backend-generated recommendation card immediately after practice ends; just record completion. The next user guidance request can use the history.
```

## Boundary

No Engine music generation, MIDI, style, voicing, bass, piano, or expression behavior changed in this pass.
