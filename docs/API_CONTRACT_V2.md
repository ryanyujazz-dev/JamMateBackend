# v2_10_28 Context persistence SQLite path guard hotfix

No public API contract change.

`POST /agent/harmonyos/routine-completion-record/execute` keeps the same black-box product request shape. The hotfix only aligns the backend dev/test SQLite path guard with the Practice Coach session-state guard so macOS pytest tempdirs such as `/private/var/folders/...` are accepted when they are under `tempfile.gettempdir()`.

Frontend still must not send `dbPath`, `sqliteDbPath`, or any internal write gate.

# v2_10_27 Practice Coach HarmonyOS UI integration fields

The primary Practice Coach endpoint remains:

```text
POST /agent/harmonyos/practice-coach-session/message/execute
```

In addition to canonical fields such as `data.responseType`, `data.content`, `data.sheetIntent`, `data.planProposal`, `data.routineCardPayload`, and `data.deviceFeedbackTracePack`, responses now include:

```text
data.frontendUiAction
debug.frontendUiAction
```

`frontendUiAction` is a frontend rendering hint, not a new backend execution command. HarmonyOS may render directly by `data.responseType`, or use `frontendUiAction.renderMode` for simpler UI branching.

Important mappings:

```text
practice_plan_proposal -> show_plan_proposal_card
practice_plan_revision -> replace_plan_proposal_card
routine_card_ready -> show_routine_card, user tap required
routine-completion-record success -> show_routine_summary_recorded, do not auto-open Practice Coach
```

Safety invariants remain:

```text
safeToAutostartRoutine=false
backendStartsRoutine=false
startsRoutine=false
callsEngineAdapter=false
createsMidiAsset=false
startsPlayback=false
writesHarmonyOSLocalState=false
```

Production HarmonyOS requests must not send `dbPath`, `sqliteDbPath`, `clientConfirmedRecordWrite`, `providerResult`, `llmActionDecisionResult`, or `apiKey`.


## v2_10_25 Practice Coach device feedback trace pack

Unified endpoint:

```text
POST /agent/harmonyos/practice-coach-session/message/execute
```

Every successful response now includes a compact device feedback object in both:

```text
data.deviceFeedbackTracePack
debug.deviceFeedbackTracePack
```

Frontend should copy `debug.deviceFeedbackTracePack` when reporting a true-device issue. It includes request summary, `responseType`, decision/fallback trace, state digests, artifact summary, SQLite IO status, and safety flags. It is a debug/reporting envelope only and does not grant any new client-side authority.

Product requests still must not include:

```text
dbPath / sqliteDbPath / clientConfirmedRecordWrite / providerResult / llmActionDecisionResult / apiKey
```

## v2_10_24 Practice Coach plan revision E2E smoke

The recommended product endpoint remains:

```text
POST /agent/harmonyos/practice-coach-session/message/execute
```

`v2_10_24` adds the frontend-facing plan revision E2E smoke for one-session Practice Coach adjustment:

```text
今天该练什么？ -> ask_clarifying_question
30分钟 bossa -> practice_plan_proposal
我想调整为20分钟 -> practice_plan_revision
我想多安排基本功和节拍器稳定性练习 -> practice_plan_revision
我想换成曲目练习 -> practice_plan_revision
确认这个安排 -> routine_card_ready
```

HarmonyOS production requests still must not send `dbPath`, `sqliteDbPath`, `providerResult`, `llmActionDecisionResult`, `apiKey`, or internal write-gate fields. The smoke assets are:

```text
frontend_fixtures/harmonyos/smoke/product_practice_coach_plan_revision_e2e_sequence.json
frontend_fixtures/harmonyos/smoke/curl_practice_coach_plan_revision_e2e_smoke.sh
```

## v2_10_22 Practice Coach SQLite path guard macOS tempdir hotfix

The HarmonyOS production request contract is unchanged. Frontend product requests still must not send `sqliteDbPath`, `dbPath`, `llmActionDecisionResult`, provider internals, or write-gate fields.

For backend tests and local-device smoke only, the Practice Coach SQLite state-store guard now accepts absolute SQLite paths under:

```text
/mnt/data
/tmp
Path(tempfile.gettempdir()).resolve(strict=False)
```

This fixes macOS local pytest paths such as `/private/var/folders/...` while retaining rejection for unsafe paths, parent traversal, production/secrets/api-key markers, and non-SQLite extensions.

## v2_10_21 Practice Coach LLM Response Repair / Schema Hardening

The unified Practice Coach endpoint remains:

```text
POST /agent/harmonyos/practice-coach-session/message/execute
```

`v2_10_21` adds backend response repair and schema hardening for real LLM output drift. The backend can repair Markdown-fenced JSON, embedded JSON objects, nested action objects, common field aliases, responseType aliases, missing `nextClientActions`, missing `sheetIntent`, and top-level plan proposal fields.

Production HarmonyOS requests still must not include `llmActionDecisionResult`, `providerResult`, `sqliteDbPath`, or internal write gates. Those remain backend/test concerns.

Debug additions:

```text
debug.llmResponseRepairSchemaHardeningVersion = v2_10_21
debug.llmActionDecisionRepairReport
```

Safety remains unchanged:

```text
startsRoutine=false
callsEngineAdapter=false
createsMidiAsset=false
startsPlayback=false
writesHarmonyOSLocalState=false
```

Invalid or unsafe LLM payloads use deterministic fallback. For example, payloads containing `midiBase64`, `apiKey`, or `hiddenChainOfThought` are rejected instead of repaired.

## v2_10_20 Practice Coach Real LLM Provider Guarded Smoke

The unified Practice Coach endpoint remains:

```text
POST /agent/harmonyos/practice-coach-session/message/execute
```

`v2_10_20` real LLM provider smoke adds a real LLM provider guarded smoke path. HarmonyOS production requests still only send product fields:

```json
{
  "userId": "local-dev-user",
  "sessionId": "practice-coach-live-llm-session-local",
  "deviceId": "harmonyos-device-local",
  "userMessage": "今天该练什么？",
  "clientLocalDate": "2026-05-20",
  "clientTimezone": "Asia/Singapore",
  "locale": "zh-CN"
}
```

Production requests must not send:

```text
llmActionDecisionResult
providerResult
dbPath / sqliteDbPath
clientConfirmedRecordWrite / internal write gate
```

For guarded smoke, the FastAPI server must be started with server-side provider env such as `JAMMATE_LLM_PROVIDER`, `JAMMATE_LLM_MODEL`, `JAMMATE_LLM_API_KEY`, and `JAMMATE_LLM_ENABLE_NETWORK_CALLS=true`. Then run:

```bash
cd frontend_fixtures/harmonyos/smoke
JAMMATE_ENABLE_LIVE_PRACTICE_COACH_LLM_SMOKE=1   bash curl_practice_coach_live_llm_provider_smoke.sh http://127.0.0.1:8000
```

The smoke expects `debug.llmActionDecisionSource=live_provider`, `debug.networkCallExecuted=true`, and `debug.llmActionDecisionValidation.ok=true`. Safety remains no Routine autostart, no Engine call, no MIDI, no playback, and no HarmonyOS local-state write.

## v2_10_19 Practice Coach Frontend Contract Types and State Mapper

`v2_10_19` adds copy-friendly HarmonyOS frontend contract files for the unified Practice Coach Session endpoint:

```text
POST /agent/harmonyos/practice-coach-session/message/execute
```

New frontend fixture files:

```text
frontend_fixtures/harmonyos/types/PracticeCoachTypes.ets
frontend_fixtures/harmonyos/api/PracticeCoachStateMapper.ets
```

`JamMateApiClient.ets` exposes `executePracticeCoachMessage(request)`. Production request types intentionally do not include `llmActionDecisionResult`; that field remains smoke-only and must not be copied into HarmonyOS product code. Frontend rendering should be driven by `data.responseType`, with `request_profile_sheet` opening a native bindSheet, `practice_plan_proposal` showing a confirm/adjust card, and `routine_card_ready` showing a routine card with an explicit user start button.

## v2_10_18 Practice Coach Frontend LLM Action Fixture Smoke

The primary HarmonyOS Practice Coach product endpoint remains:

```text
POST /agent/harmonyos/practice-coach-session/message/execute
```

`v2_10_18` clarifies frontend/device smoke for the LLM-action-decision-first contract introduced in `v2_10_17`. Product frontend requests must not include `dbPath`, `sqliteDbPath`, internal write gates, `llmActionDecisionResult`, or `providerResult`. Smoke-only fixtures may include `llmActionDecisionResult` to simulate the LLM provider boundary when provider credentials are unavailable.

New frontend fixture files:

```text
frontend_fixtures/harmonyos/smoke/product_practice_coach_message_today_request.json
frontend_fixtures/harmonyos/smoke/product_practice_coach_profile_form_submit_request.json
frontend_fixtures/harmonyos/smoke/smoke_llm_action_ask_clarifying_request.json
frontend_fixtures/harmonyos/smoke/smoke_llm_action_request_profile_sheet_request.json
frontend_fixtures/harmonyos/smoke/smoke_llm_action_plan_proposal_request.json
frontend_fixtures/harmonyos/smoke/smoke_llm_action_routine_card_ready_request.json
frontend_fixtures/harmonyos/smoke/curl_practice_coach_llm_action_smoke.sh
```

Safety remains unchanged: Practice Coach chat may persist backend session state, but must not start Routine, call Engine, create MIDI, start playback, or write HarmonyOS local state.

## v2_10_17 Practice Coach LLM Action Decision Contract

`POST /agent/harmonyos/practice-coach-session/message/execute` is now LLM-action-decision-first. The backend builds the Practice Coach context, asks the LLM/provider to choose a structured `responseType`, validates the action contract, persists Practice Coach session state, and falls back to the deterministic v2_10_16 router only when provider output is unavailable or invalid. HarmonyOS should render by `responseType`, `nextClientActions`, `sheetIntent`, `planProposal`, and `routineCardPayload`; the LLM never renders UI code and the backend never starts Routine/Engine/MIDI/playback from this route.

## v2_10_16 Practice Coach Unified Message/Action Router

新增统一入口：`POST /agent/harmonyos/practice-coach-session/message/execute`。前端可以用一个 Practice Coach message 入口驱动追问、profile sheet、plan proposal 与 routine card ready 四类下一步动作。响应继续使用 `{ok, code, message, data, debug, safety}`，核心字段为 `data.responseType`、`data.nextClientActions`、`data.agentActionPreview`、`data.sheetIntent`、`data.planProposal`、`data.routineCardPayload`。本接口不调用大模型、不启动 Routine、不调用 Engine。

## v2_10_15 Practice Coach Profile Sheet Intent Contract

Endpoint:

```text
POST /agent/harmonyos/practice-coach-session/profile-sheet/execute
```

Purpose: let Practice Coach Session ask HarmonyOS for structured baseline practice information through a native bindSheet-style UI, or record a submitted `profileFormResult` into backend session state. The LLM does not render UI; it only produces/uses structured action intent. This endpoint does not call an LLM, does not start Routine, does not call Engine, does not create MIDI, and does not write HarmonyOS local state. It may write backend SQLite Practice Coach session state.

HarmonyOS still sends only black-box product fields plus optional `profileFormResult`: `userId`, `sessionId`, `deviceId`, `userMessage`, and when submitting the sheet, `profileFormResult`. The frontend must not send `dbPath`, `sqliteDbPath`, or internal write gate fields.

Key response fields:

```text
data.agentActionPreview.responseType = request_profile_sheet | chat_message
data.sheetIntent
data.profileSheetIntentReady
data.profileFormResultRecorded
data.stateAfter.collected_fields.practice_profile
data.llmRequestPreview
```

`responseType=request_profile_sheet` means the frontend may open a native HarmonyOS bindSheet using `data.sheetIntent`. `responseType=chat_message` with `profileFormResultRecorded=true` means the profile form result has been saved and the user can continue the Practice Coach conversation.


## v2_10_14 Practice Coach Plan Confirmation to Routine Card Contract

Endpoint:

```text
POST /agent/harmonyos/practice-coach-session/routine-card/execute
```

Purpose: convert a previously persisted Practice Coach Session `draft_plan` into a HarmonyOS-presentable `routineCardPayload` only after the user explicitly confirms the proposal. The endpoint does not call an LLM, does not start Routine, does not call Engine, does not create MIDI, and does not write HarmonyOS local state. It may write backend SQLite session state so the confirmed card state survives the next turn.

HarmonyOS still sends only black-box product fields: `userId`, `sessionId`, `deviceId`, and `userMessage`. The frontend must not send `dbPath`, `sqliteDbPath`, or internal write gate fields.

Key response fields:

```text
data.agentActionPreview.responseType = routine_card_ready
data.routineCardReady
data.routineCardPayload
data.routineStartEnabled
data.requiresUserTapToStart
data.backendStartsRoutine = false
```

`responseType=routine_card_ready` means the frontend should show the routine card and wait for the user to tap Start locally. Backend confirmation-to-card is not backend Routine execution.

## v2_10_13 Practice Coach Session Plan Proposal Contract

Endpoint:

```text
POST /agent/harmonyos/practice-coach-session/plan-proposal/execute
```

Purpose: convert an already-collected Practice Coach Session state into a structured `practice_plan_proposal`, or return `ask_clarifying_question` when `available_minutes` / `practice_focus` is still missing. The endpoint does not call an LLM, does not start Routine, does not call Engine, and does not create MIDI. It may write backend SQLite session state so the `draft_plan` and `awaiting_confirmation` state survive the next turn.

HarmonyOS still sends only black-box product fields: `userId`, `sessionId`, `deviceId`, and `userMessage`. The frontend must not send `dbPath`, `sqliteDbPath`, or internal write gate fields.

Key response fields:

```text
data.agentActionPreview.responseType
data.planProposal
data.requiresUserConfirmationBeforeRoutineCard
data.routineCardPayload = null
data.routineStartEnabled = false
```

`responseType=practice_plan_proposal` means the frontend should show a proposal card and let the user confirm or adjust. Confirmation-to-routine-card is intentionally deferred to a later contract.

# JamMate API Contract V2

Current baseline: `v2_10_15`.

This document records the stable API contract shape. Detailed version-specific API delivery notes live in separate `docs/*V2_x_x*.md` files.

---

## Track Ownership for API Changes

- Direct accompaniment route `/accompaniment/generate` is Engine/HarmonyOS playback contract territory.
- Agent routes `/agent/*` are Agent workflow territory.
- Shared response envelopes, frontend fixture packs, and version surfaces are integration-task territory.
- Agent changes must not replace the direct accompaniment asset response shape.

---

## Case Policy

Backend canonical response case:

```text
snake_case
```

HarmonyOS client-domain case:

```text
camelCase
```

Rules:

- Python/FastAPI routes return canonical snake_case.
- Request schemas may accept both snake_case and camelCase where supported.
- HarmonyOS generated files include `CaseAdapter.ets` to map raw backend snake_case payloads into camelCase UI/store objects.
- Do not add a second backend camelCase response mode unless a future compatibility requirement explicitly demands it.

---

## Core Endpoints

### Health

```text
GET /health
```

Expected response:

```json
{
  "ok": true,
  "service": "jammate-api",
  "engine_version": "v2_10_8",
  "agent_version": "v0_1"
}
```

---

### Direct accompaniment generation

```text
POST /accompaniment/generate
```

Use this when the client has explicit tune/style/tempo/chorus parameters.

Example request:

```json
{
  "tune": "Blue Bossa",
  "style": "bossa_nova",
  "tempo": 120,
  "choruses": 1,
  "outputFormat": "midi_base64"
}
```

Expected response shape:

```json
{
  "ok": true,
  "asset": {
    "format": "midi_base64",
    "midi_base64": "...",
    "midi_path": "demos/...mid",
    "cache_key": "direct_accomp:...",
    "debug_summary": {}
  }
}
```

---

### Agent immediate playback

```text
POST /agent/playback/prepare
```

Use this when the user expresses a practice/playback goal.

Example request:

```json
{
  "userInput": "我想练 Blue Bossa 20分钟，帮我生成 Bossa Nova 伴奏",
  "durationMinutes": 20,
  "clientContext": {
    "currentScreen": "practice_home",
    "availableMinutes": 20,
    "timezone": "America/Los_Angeles",
    "locale": "zh-CN"
  }
}
```

Expected response shape:

```json
{
  "ok": true,
  "intent_type": "immediate_practice_playback",
  "practice_session": {},
  "asset": {
    "asset_id": "...",
    "format": "midi_base64",
    "midi_base64": "...",
    "midi_path": "demos/...mid",
    "cache_key": "agent_playback:..."
  },
  "playback_instruction": {
    "auto_start": true,
    "target_duration_minutes": 20,
    "client_loop_until_target_duration": true,
    "asset_loop_mode": "loop_until_target_duration",
    "requires_local_timer": true
  },
  "trace_id": "trace_..."
}
```

HarmonyOS should loop the returned asset until its local practice timer reaches `target_duration_minutes` or the user stops.

---

### Practice planning

```text
POST /agent/practice/plan
```

Returns a rule/workflow-based practice plan today; future LLM support should preserve the same response contract as much as possible.

---

### Session review

```text
POST /agent/session/review
```

Returns a next-step recommendation based on submitted review data.



### HarmonyOS Agent today practice guidance

```text
POST /agent/harmonyos/today-practice-guidance/preview
```

Use this when the user asks “今天该练什么？” from HarmonyOS. The route may read backend SQLite context but must not start a Routine, call `/accompaniment/generate`, call the Engine adapter, create MIDI, or start playback.

HarmonyOS product clients should treat the backend as a black-box HTTP API. Do **not** send internal `sqliteDbPath`, migration, or persistence gate fields from product UI; the backend owns the context DB path through `JAMMATE_AGENT_CONTEXT_DB_PATH` or its local-dev default.

Example request matching the current HarmonyOS frontend report:

```json
{
  "userId": "local-dev-user",
  "sessionId": "agent-session-1779200000000",
  "deviceId": "harmonyos-device-local",
  "userMessage": "今天该练什么？"
}
```

Expected response shape:

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
  "debug": {},
  "safety": {
    "backendSQLiteWriteMayOccur": false,
    "writesHarmonyOSLocalState": false,
    "startsRoutine": false,
    "callsAccompanimentGenerate": false,
    "callsEngineAdapter": false,
    "createsMidiAsset": false,
    "startsPlayback": false
  }
}
```


Runtime smoke:

```bash
cd frontend_fixtures/harmonyos/smoke
bash curl_agent_today_guidance_runtime_smoke.sh \
  http://127.0.0.1:8000 \
  /tmp/jammate_agent_harmonyos_today_guidance_runtime_smoke.sqlite
```

The strict runtime smoke asserts both HarmonyOS Agent product routes and intentionally skips `/accompaniment/generate` and `/agent/playback/prepare`; it is for backend context persistence/readback validation, not playback validation.

---

### HarmonyOS routine completion record persistence

```text
POST /agent/harmonyos/routine-completion-record/execute
```

Use this after HarmonyOS has already finished and recorded a practice session locally. The client remains owner of timer/playback/local state; the backend stores only an Agent context record. Product clients do **not** send `sqliteDbPath` or `clientConfirmedRecordWrite`; the route itself is the explicit completed-record submission and the backend injects its internal persistence confirmation.

Example request matching the current HarmonyOS frontend report:

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

Expected response shape:

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
  "debug": {},
  "safety": {
    "backendSQLiteWriteMayOccur": true,
    "writesHarmonyOSLocalState": false,
    "startsRoutine": false,
    "callsAccompanimentGenerate": false,
    "callsEngineAdapter": false,
    "createsMidiAsset": false,
    "startsPlayback": false
  }
}
```

---

## Contract / Fixture Endpoints

```text
GET /agent/capabilities
GET /agent/context/profiles
GET /agent/contracts/arkts
GET /agent/contracts/arkts/files
GET /agent/contracts/frontend-pack
GET /agent/contracts/case-policy
GET /agent/contracts/smoke-pack
GET /agent/contracts/smoke-pack/files
GET /agent/contracts/fixtures
GET /agent/traces
GET /agent/traces/{trace_id}
```

These endpoints support HarmonyOS development, frontend fixtures, local mocking, and trace inspection.

---

## Playback Asset Cache Policy

Every returned accompaniment asset should include a `cache_key` when possible.

HarmonyOS should:

1. Use `cache_key` to store/reuse decoded MIDI assets.
2. Treat practice duration as local timer state.
3. Loop the asset when `client_loop_until_target_duration=true`.
4. Stop when local timer reaches target duration or the user stops.


v2_5_6 note: API behavior is unchanged. This patch only corrects Jazz Ballad `1&` piano timing intent: logical `0.5` stays in the pitchless pattern layer, while `timing_intent=swing_upbeat` lets the render timing policy perform it at the swing/triplet upbeat.

v2_5_5 note: API behavior is unchanged. This engine-deepening patch only corrects Jazz Ballad two-beat piano soft-mark timing from beat 2 to 1& and synchronizes package version labels.


## v2_5_9 note

This pass changes only version metadata and engine-planning documentation. Direct accompaniment API request/response shape is unchanged from `v2_5_8`; Agent/LLM behavior is unchanged.


## v2_5_10 Integration Contract Note

This integrated package preserves both current public surfaces: HarmonyOS direct accompaniment generation and Agent preview/trace APIs. `POST /accompaniment/generate` remains the playback-critical route and must continue returning canonical snake_case backend fields, including `asset.midi_base64` and `asset.cache_key`. Agent tool-preview and trace APIs remain preview/inspection-only and must not execute tools or dispatch engine adapters.


## v2_10_8 Integration Contract Note

This integration pass preserves the two public route families:

- Direct playback: `POST /accompaniment/generate`.
- Agent/debug/preview: `GET/POST /agent/*`.

Engine Track merged through v2.6.44 (frozen Ballad SPREAD guardrails). Agent Track merged through v2.10.7 (routine-completion-record persistence, today-practice-guidance with SQLite readback, HarmonyOS runtime smoke).

The direct accompaniment response remains playback-critical for HarmonyOS and must keep the canonical backend shape unchanged. Agent contract, trace, context, guidance, persistence-preview, and tool-preview routes remain preview/orchestration surfaces and must not mutate Engine generation behavior.


## v2_8_24 Integration Contract Note

This integration pass preserves the two public route families:

- Direct playback: `POST /accompaniment/generate`.
- Agent/debug/preview: `GET/POST /agent/*`.

The direct accompaniment response remains playback-critical for HarmonyOS and must keep this canonical backend shape:

```json
{
  "ok": true,
  "asset": {
    "format": "midi_base64",
    "midi_base64": "...",
    "midi_path": "...",
    "cache_key": "..."
  },
  "debug_summary": {}
}
```

Agent contract, trace, context, guidance, persistence-preview, and tool-preview routes must remain preview/orchestration surfaces and must not mutate Engine generation behavior.

## v2_10_9 HarmonyOS Agent Black-Box Product-Contract Smoke

The current HarmonyOS Agent product smoke validates the frontend-facing black-box contract, not Python internals.

Product endpoints:

```text
POST /agent/harmonyos/routine-completion-record/execute
POST /agent/harmonyos/today-practice-guidance/preview
```

Product clients must not send backend-owned internals:

```text
dbPath
sqliteDbPath
clientConfirmedRecordWrite
internal write gate / migration guard fields
```

`routine-completion-record/execute` accepts the real Routine completion payload:

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

`today-practice-guidance/preview` accepts `userMessage`:

```json
{
  "userId": "local-dev-user",
  "sessionId": "agent-session-1779200000000",
  "deviceId": "harmonyos-device-local",
  "userMessage": "今天该练什么？"
}
```

The backend wrapper owns the SQLite context path through `JAMMATE_AGENT_CONTEXT_DB_PATH` or the local-dev default, and owns the internal confirmation/gate injection needed by the persistence executor. The response envelope remains:

```json
{
  "ok": true,
  "code": "...",
  "message": "...",
  "data": {},
  "debug": {},
  "safety": {}
}
```

Runtime/device smoke script:

```bash
cd frontend_fixtures/harmonyos/smoke
bash curl_agent_black_box_product_contract_smoke.sh http://127.0.0.1:8000
```

For phone-to-Mac LAN testing, start the service with `--host 0.0.0.0 --port 8000`, set HarmonyOS baseUrl to `http://<MAC_LAN_IP>:8000`, verify `/health` in the phone browser first, and never use `127.0.0.1` as the phone baseUrl.
## v2_10_10 HarmonyOS Agent Today Guidance LLM Payload Trace

Use this debug endpoint when you need to inspect exactly what the backend would prepare for the model after the user taps “今天该练什么？”:

```text
POST /agent/harmonyos/today-practice-guidance/llm-payload-trace
```

It accepts the same black-box product body as `today-practice-guidance/preview`:

```json
{
  "userId": "local-dev-user",
  "sessionId": "agent-session-1779200000000",
  "deviceId": "harmonyos-device-local",
  "userMessage": "今天该练什么？"
}
```

The route is for debug/audit only and **不会调用大模型**. It also does not start Routine, call `/accompaniment/generate`, call the Engine adapter, create MIDI, start playback, or write HarmonyOS local state.

The main response field is:

```text
data.llmRequestPreview
```

Important nested fields:

```text
internalPromptMessages              # internal prompt roles: system/developer/user/context
providerEnvelopeMessages            # provider-neutral envelope messages before network normalization
chatCompletionsMessagesIfCalled     # OpenAI-compatible messages if a provider call were enabled
chatCompletionsRequestBodyPreview   # model/messages/temperature/max_tokens only; no Authorization/api key
assembledPracticeContext            # recovered plan/history/profile/today constraints used as context
outputSchema                        # TodayPracticeGuidanceOutput schema
promptPolicy                        # answer and safety rules
contextSummary                      # context source, sqlite readback, rows read, candidate count
roleNormalization                   # explains developer/context -> system merge
```

`chatCompletionsMessagesIfCalled` uses compatible roles only: `system`, `user`, and `assistant`. Internal `developer` and `context` messages are merged into the leading `system` message before a real OpenAI-compatible network request would be made.



## v2_10_11 Practice Coach Session Context Builder Preview

Use this debug/audit endpoint to inspect the cache-friendly Practice Coach Session LLM context shape before introducing full conversation execution:

```text
POST /agent/harmonyos/practice-coach-session/context-builder-preview
```

It accepts the same black-box product fields as today guidance, including `userId`, `sessionId`, `deviceId`, and `userMessage`. The route may read backend SQLite context through the backend-owned `JAMMATE_AGENT_CONTEXT_DB_PATH`, but it does **not** call an LLM/provider and does not start Routine, call Engine, create MIDI, start playback, or write HarmonyOS local state.

Main response field:

```text
data.llmRequestPreview
```

Important nested fields:

```text
messages
chatCompletionsMessagesIfCalled
contextBlocks
blockDigests
debugMetadata.stable_prefix_digest
debugMetadata.context_packet_digest
debugMetadata.current_turn_digest
cacheDesign
sourceProjection
```

The context block order is stable and cache-aware:

```text
stable_product_contract
stable_action_contract
user_profile_summary
active_practice_plan_summary
recent_practice_memory_summary
practice_coach_session_state
current_user_turn
```

Routine completion `items` and `notes` are projected into compact `recent_practice_memory_summary` fields (`item_summaries` and `user_note_summary`) rather than raw blobs. This keeps the prompt useful for the model while preserving token and cache discipline.

本接口不会调用大模型。

## v2_10_12 Practice Coach Session Conversation State Store

```text
POST /agent/harmonyos/practice-coach-session/message-state/execute
```

Purpose: persist and restore Practice Coach Session conversation state so a user can continue after a clarifying question.

Request:

```json
{
  "userId": "local-dev-user",
  "sessionId": "coach-session-1",
  "deviceId": "harmonyos-device-local",
  "userMessage": "今天该练什么？"
}
```

The HarmonyOS client still does not send `dbPath`, `sqliteDbPath`, `clientConfirmedRecordWrite`, or internal write gates.

Response fields:

```text
ok
code
message
data.conversationStatePersisted
data.stateFoundBeforeTurn
data.stateBefore
data.stateAfter
data.extractedFieldsFromCurrentTurn
data.agentActionPreview
data.llmRequestPreview
debug
safety
```

This route may write backend SQLite tables `practice_coach_session_states` and `practice_coach_session_turns`. It does not call an LLM/provider, start Routine, call Engine, generate MIDI, start playback, or write HarmonyOS local state.


## v2_10_23 Practice Coach plan revision routing

统一入口 `POST /agent/harmonyos/practice-coach-session/message/execute` 在已有待确认 `draft_plan` 时会先判断用户意图。`确认/就这个/开始` 生成 `routine_card_ready`；`我想调整为20分钟`、`改成20分钟`、`多安排基本功`、`加强节拍器稳定性`、`换成曲目练习`、`换一首 standard` 等明确调整请求返回 `responseType=practice_plan_revision`，并更新 `planProposal` / `stateAfter.draft_plan`，继续要求用户确认。
