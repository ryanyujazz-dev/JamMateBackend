# v2_10_20 Practice Coach real LLM provider guarded smoke

`curl_practice_coach_live_llm_provider_smoke.sh` validates a real LLM provider call through the unified Practice Coach endpoint:

```text
POST /agent/harmonyos/practice-coach-session/message/execute
```

This smoke is opt-in and requires:

```bash
JAMMATE_ENABLE_LIVE_PRACTICE_COACH_LLM_SMOKE=1
```

The running FastAPI server must already have provider env configured server-side, for example:

```bash
export JAMMATE_AGENT_CONTEXT_DB_PATH=/tmp/jammate_practice_coach_live_llm.sqlite3
export JAMMATE_LLM_PROVIDER=openai_compatible
export JAMMATE_LLM_MODEL=<model>
export JAMMATE_LLM_API_KEY=<key>
export JAMMATE_LLM_ENABLE_NETWORK_CALLS=true
export JAMMATE_LLM_BASE_URL=<openai-compatible-base-url>
PYTHONPATH=src uvicorn jammate_api.app:app --host 0.0.0.0 --port 8000
```

Run:

```bash
JAMMATE_ENABLE_LIVE_PRACTICE_COACH_LLM_SMOKE=1 \
  bash curl_practice_coach_live_llm_provider_smoke.sh http://127.0.0.1:8000
```

The product fixture is `product_practice_coach_live_llm_message_request.json`. It must not contain `llmActionDecisionResult`, `providerResult`, `dbPath`, `sqliteDbPath`, or internal write gates. Those injection fields are reserved only for smoke-only fixtures from v2_10_18.

The smoke expects `debug.llmActionDecisionSource=live_provider`, `debug.networkCallExecuted=true`, and `debug.llmActionDecisionValidation.ok=true`, while keeping `startsRoutine=false`, `callsEngineAdapter=false`, `createsMidiAsset=false`, `startsPlayback=false`, and `writesHarmonyOSLocalState=false`.

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

## v2_10_9 black-box product-contract runtime/device smoke

`v2_10_9` adds a product-contract smoke that uses the same black-box request shape the HarmonyOS frontend report described:

- no `dbPath` / `sqliteDbPath`
- no `clientConfirmedRecordWrite` or internal write gate
- `today-practice-guidance` uses `userMessage`
- response remains `{ ok, code, message, data, debug, safety }`

Copyable product-contract fixtures:

```text
product_contract_routine_completion_request.json
product_contract_today_guidance_request.json
```

Run locally on the Mac:

```bash
# Optional but recommended for isolated smoke data:
export JAMMATE_AGENT_CONTEXT_DB_PATH=/tmp/jammate_agent_black_box_product_contract_smoke.sqlite3
PYTHONPATH=src uvicorn jammate_api.app:app --host 0.0.0.0 --port 8000

cd frontend_fixtures/harmonyos/smoke
bash curl_agent_black_box_product_contract_smoke.sh http://127.0.0.1:8000
```

Run from HarmonyOS phone to Mac LAN:

```bash
# On Mac, from project root:
export JAMMATE_AGENT_CONTEXT_DB_PATH=/tmp/jammate_agent_black_box_product_contract_device_smoke.sqlite3
PYTHONPATH=src uvicorn jammate_api.app:app --host 0.0.0.0 --port 8000

# On phone / HarmonyOS config:
# baseUrl = http://<MAC_LAN_IP>:8000, for example http://192.168.1.16:8000
```

Device checklist:

1. Mac and phone are on the same Wi-Fi.
2. Mac FastAPI listens on `0.0.0.0`, not only `127.0.0.1`.
3. HarmonyOS baseUrl uses `http://<MAC_LAN_IP>:8000`; do not use `127.0.0.1` on the phone.
4. Mac firewall allows port `8000`.
5. Open `http://<MAC_LAN_IP>:8000/health` in the phone browser before testing Agent routes.
6. Then call `routine-completion-record/execute` after the real Routine end event, and call `today-practice-guidance/preview` when the user later asks “今天该练什么？”.

The script asserts both product routes and safety fields. With no live LLM/provider configured, `today-practice-guidance` may return `code=today_guidance_needs_context_or_provider`, but it must still be HTTP-ok, read SQLite context, return non-empty `data.content`, and avoid Routine start, Engine calls, MIDI creation, playback, or HarmonyOS local-state writes.

## v2_10_18 Practice Coach unified LLM action fixture smoke

`v2_10_18` adds fixtures for the unified Practice Coach Session endpoint:

```text
POST /agent/harmonyos/practice-coach-session/message/execute
```

Product frontend fixtures:

```text
product_practice_coach_message_today_request.json
product_practice_coach_profile_form_submit_request.json
```

These product fixtures intentionally omit:

```text
dbPath / sqliteDbPath
clientConfirmedRecordWrite / internal write gates
llmActionDecisionResult / providerResult
```

Smoke-only LLM action fixtures:

```text
smoke_llm_action_ask_clarifying_request.json
smoke_llm_action_request_profile_sheet_request.json
smoke_llm_action_plan_proposal_request.json
smoke_llm_action_routine_card_ready_request.json
```

These `smoke_llm_action_*` fixtures intentionally include `llmActionDecisionResult` to simulate the LLM provider boundary without live provider credentials. Do not copy that field into HarmonyOS product code.

Run locally:

```bash
# Optional but recommended for isolated backend session state:
export JAMMATE_AGENT_CONTEXT_DB_PATH=/tmp/jammate_practice_coach_llm_action_smoke.sqlite3
PYTHONPATH=src uvicorn jammate_api.app:app --host 0.0.0.0 --port 8000

cd frontend_fixtures/harmonyos/smoke
bash curl_practice_coach_llm_action_smoke.sh http://127.0.0.1:8000
```

Phone / HarmonyOS device:

```text
baseUrl = http://<MAC_LAN_IP>:8000
```

The script validates `ask_clarifying_question`, `request_profile_sheet`, `practice_plan_proposal`, and `routine_card_ready`. It also verifies that the backend does not start Routine, call Engine, create MIDI, start playback, or write HarmonyOS local state.

## v2_10_19 Practice Coach frontend types and state mapper

`v2_10_19` adds copy-friendly HarmonyOS frontend contract files for the unified Practice Coach endpoint:

```text
../types/PracticeCoachTypes.ets
../api/PracticeCoachStateMapper.ets
```

The production API client method is:

```text
executePracticeCoachMessage(request)
```

It calls:

```text
POST /agent/harmonyos/practice-coach-session/message/execute
```

Important boundary:

```text
llmActionDecisionResult is not a HarmonyOS product field.
```

It is smoke-only and intentionally present only in `smoke_llm_action_*` fixtures so backend/device smoke can simulate LLM action outputs without live provider credentials. Do not copy that field into ArkTS request types, ViewModels, or production API calls.

Frontend state mapping rule:

```text
data.responseType -> PracticeCoachUiState.kind
```

The mapper covers:

```text
ask_clarifying_question
request_profile_sheet
practice_plan_proposal
practice_plan_revision
routine_card_ready
chat_message
cannot_proceed
```

Every mapped UI state keeps `safeToAutostartRoutine=false`. Showing a routine card is allowed only as a user-confirmable UI state; backend never starts Routine automatically.
