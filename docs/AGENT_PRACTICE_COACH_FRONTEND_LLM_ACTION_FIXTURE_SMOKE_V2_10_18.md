# v2_10_18 — Practice Coach Frontend LLM Action Fixture and Smoke

## Scope

`v2_10_18` prepares HarmonyOS frontend/device integration fixtures for the unified Practice Coach Session endpoint:

```text
POST /agent/harmonyos/practice-coach-session/message/execute
```

This task is intentionally Agent / Integration scoped. It does not change Engine music generation, accompaniment generation, MIDI rendering, style logic, voicing, bass, piano, drums, or playback.

## Product boundary

HarmonyOS product requests should stay black-box and frontend-owned:

```text
userId
sessionId
deviceId
userMessage
profileFormResult (only when submitting a native sheet)
```

Product requests must not include:

```text
dbPath
sqliteDbPath
clientConfirmedRecordWrite
internal write gates
llmActionDecisionResult
providerResult
```

The backend owns DB path selection, provider configuration, LLM action validation, Practice Coach session persistence, and safety gates.

## Fixture split

### Product fixtures

These fixtures represent real frontend request shape and contain no backend internals or injected LLM output:

```text
frontend_fixtures/harmonyos/smoke/product_practice_coach_message_today_request.json
frontend_fixtures/harmonyos/smoke/product_practice_coach_profile_form_submit_request.json
```

### Smoke-only LLM action fixtures

These fixtures intentionally include `llmActionDecisionResult` to simulate the LLM provider boundary during backend/device smoke without requiring live provider setup:

```text
frontend_fixtures/harmonyos/smoke/smoke_llm_action_ask_clarifying_request.json
frontend_fixtures/harmonyos/smoke/smoke_llm_action_request_profile_sheet_request.json
frontend_fixtures/harmonyos/smoke/smoke_llm_action_plan_proposal_request.json
frontend_fixtures/harmonyos/smoke/smoke_llm_action_routine_card_ready_request.json
```

Important: `llmActionDecisionResult` is a dev/smoke injection hook only, not a HarmonyOS product field. HarmonyOS product code should never send it.

## Smoke script

The new script is:

```text
frontend_fixtures/harmonyos/smoke/curl_practice_coach_llm_action_smoke.sh
```

It validates:

1. `GET /health`.
2. Product-shaped `message/execute` request works without injected LLM output.
3. Injected LLM action `ask_clarifying_question` is accepted and persisted.
4. Injected LLM action `request_profile_sheet` returns `sheetIntent` for native HarmonyOS bindSheet rendering.
5. Product-shaped profile form submission is accepted and stored through fallback/session-state logic.
6. Injected LLM action `practice_plan_proposal` saves a draft plan awaiting confirmation.
7. Injected LLM action `routine_card_ready` rebuilds `routineCardPayload` from backend persisted draft plan rather than trusting LLM-supplied card content.

## Safety expectations

Every Practice Coach Session smoke response must preserve:

```text
startsRoutine = false
callsEngineAdapter = false
createsMidiAsset = false
startsPlayback = false
writesHarmonyOSLocalState = false
```

`routine_card_ready` may set `routineStartEnabled=true` in the returned frontend card payload, but it only means the frontend may show a start button. The backend does not start Routine.

## Frontend guidance

HarmonyOS should migrate toward the unified endpoint and render by:

```text
data.responseType
data.nextClientActions
data.sheetIntent
data.planProposal
data.routineCardPayload
```

Recommended frontend handling:

```text
ask_clarifying_question -> chat bubble + suggested replies
request_profile_sheet -> native bindSheet / bottom sheet
practice_plan_proposal -> proposal card with confirm / adjust actions
routine_card_ready -> routine card with explicit user start button
chat_message -> plain chat bubble
cannot_proceed -> plain error/empty-state message
```

## Why this step exists

`v2_10_17` made the unified Practice Coach endpoint LLM-action-decision-first. `v2_10_18` gives frontend/device integration a deterministic way to smoke that contract without requiring real provider credentials, while keeping product payloads clean and black-box.

## Recommended next task

`v2_10_19_agent_practice_coach_frontend_contract_types_and_state_mapper`:

- update HarmonyOS-facing ArkTS type fixture for the unified endpoint;
- add frontend state mapping guidance for response types;
- keep `llmActionDecisionResult` out of production types;
- document how `request_profile_sheet`, `practice_plan_proposal`, and `routine_card_ready` should render.
