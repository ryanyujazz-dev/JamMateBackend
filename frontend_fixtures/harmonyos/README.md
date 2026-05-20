
## v2_10_25 Practice Coach device feedback trace pack

`POST /agent/harmonyos/practice-coach-session/message/execute` responses include `data.deviceFeedbackTracePack` and `debug.deviceFeedbackTracePack`. For device feedback, return this object together with request URL, request JSON, HTTP status, response JSON, mapped UI state, and screenshot/logs if available. The pack is diagnostic only; frontend still must not send internal fields such as `sqliteDbPath`, `providerResult`, or `llmActionDecisionResult`.

# JamMate HarmonyOS Frontend Fixture Pack v2_10_6

This folder is a copy-friendly frontend contract pack for HarmonyOS development.

## Files

- `types/AgentTypes.ets`: Agent request/response and trace types.
- `types/PracticeTypes.ets`: Local-first practice plan/session/review types.
- `types/PlaybackTypes.ets`: Playback asset, cache, direct accompaniment types.
- `api/CaseAdapter.ets`: snake_case -> camelCase response adapter.
- `api/JamMateApiClient.ets`: Minimal API client sketch. Replace HTTP internals.
- `fixtures/PracticeFixtures.json`: Stable UI/store mock payloads.

## Rules

- HarmonyOS local practice workspace must run without LLM.
- Direct accompaniment uses `/accompaniment/generate` and does not require Agent.
- Natural-language planning/playback uses `/agent/*`.
- Backend responses are canonical `snake_case`.
- Client-domain objects should be camelCase after `CaseAdapter.ets` mapping.
- Requests may be sent as camelCase or snake_case.
- Practice duration is a local timer target; returned MIDI asset can be looped until target duration.

## v2_10_6 Agent Today-Guidance Handoff

HarmonyOS can now use two product-facing Agent wrapper routes for the practice-context loop:

```text
POST /agent/harmonyos/routine-completion-record/execute
POST /agent/harmonyos/today-practice-guidance/preview
```

Recommended product flow:

1. At routine end, HarmonyOS keeps its normal local completion UI and may call `routine-completion-record/execute` to persist the completion record into backend Agent context. Do not show a backend recommendation card on the routine-end page.
2. Later, when the user asks “今天该练什么？”, call `today-practice-guidance/preview`. The response is display-only and any routine start must require a separate user confirmation.

Useful smoke payloads:

```text
smoke/smoke_agent_harmonyos_routine_completion_record_execute.json
smoke/smoke_agent_harmonyos_today_practice_guidance_preview.json
```

The API client sketch exposes:

```text
executeHarmonyOSRoutineCompletionRecord(request)
previewHarmonyOSTodayPracticeGuidance(request)
```

## v2_10_19 Practice Coach unified frontend contract types

HarmonyOS can now use a single Practice Coach Session product endpoint:

```text
POST /agent/harmonyos/practice-coach-session/message/execute
```

Copy-friendly frontend files:

```text
types/PracticeCoachTypes.ets
api/PracticeCoachStateMapper.ets
```

Recommended frontend call:

```text
JamMateApiClient.executePracticeCoachMessage(request)
```

Production requests contain only product fields such as:

```text
userId
sessionId
deviceId
userMessage
profileFormResult
```

Production requests must not include `llmActionDecisionResult`. That name is smoke-only and appears only in backend smoke fixtures as a provider-boundary simulation hook.

Frontend rendering should be driven by `data.responseType`:

```text
ask_clarifying_question -> chat bubble + suggested replies
request_profile_sheet -> native bindSheet / bottom sheet
practice_plan_proposal -> proposal card with confirm / adjust actions
practice_plan_revision -> updated proposal card
routine_card_ready -> routine card with explicit user start button
chat_message -> plain chat bubble
cannot_proceed -> plain error/empty-state message
```

The state mapper keeps `safeToAutostartRoutine=false` for every response. Even when a routine card is ready, the user must explicitly tap the frontend start button.

## v2_10_27 Practice Coach UI integration

Use `POST /agent/harmonyos/practice-coach-session/message/execute` as the main Practice Coach product endpoint. Responses include `data.frontendUiAction` as a rendering helper:

- `show_plan_proposal_card` for `practice_plan_proposal`
- `replace_plan_proposal_card` for `practice_plan_revision`
- `show_routine_card` for `routine_card_ready`
- `show_routine_summary_recorded` for successful `routine-completion-record/execute`

The frontend must never auto-start Routine from these responses. Completion summary should show “已记录” and should not auto-open Practice Coach.
