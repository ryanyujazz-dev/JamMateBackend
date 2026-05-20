# v2_10_19 — Practice Coach Frontend Contract Types and State Mapper

## Scope

`v2_10_19` prepares HarmonyOS-facing contract files for the unified Practice Coach Session endpoint:

```text
POST /agent/harmonyos/practice-coach-session/message/execute
```

This is an Agent / Integration task. It does not change Engine music generation, accompaniment generation, MIDI rendering, style logic, voicing, bass, piano, drums, or playback.

## Files added

```text
frontend_fixtures/harmonyos/types/PracticeCoachTypes.ets
frontend_fixtures/harmonyos/api/PracticeCoachStateMapper.ets
```

## API client update

`frontend_fixtures/harmonyos/api/JamMateApiClient.ets` now exposes:

```text
executePracticeCoachMessage(request)
```

The method calls:

```text
POST /agent/harmonyos/practice-coach-session/message/execute
```

## Production request boundary

Production HarmonyOS requests should contain only product fields:

```text
userId
sessionId
deviceId
userMessage
profileFormResult
clientLocalDate / clientTimezone / locale when needed
```

Production HarmonyOS requests must not include:

```text
dbPath
sqliteDbPath
clientConfirmedRecordWrite
internal write gates
providerResult
llmActionDecisionResult
```

`llmActionDecisionResult` remains a backend/device smoke-only provider-boundary injection hook. It should never appear in production ArkTS request interfaces or ViewModels.

## Response rendering contract

HarmonyOS should render by:

```text
data.responseType
data.nextClientActions
data.sheetIntent
data.planProposal
data.routineCardPayload
```

Mapping:

```text
ask_clarifying_question -> chat bubble + suggested replies
request_profile_sheet -> native bindSheet / bottom sheet
practice_plan_proposal -> plan proposal card with confirm / adjust actions
practice_plan_revision -> updated plan proposal card
routine_card_ready -> routine card with explicit user start button
chat_message -> plain chat bubble
cannot_proceed -> plain error or empty-state message
```

## State mapper contract

`PracticeCoachStateMapper.ets` maps backend envelopes into frontend UI states:

```text
loading
chat_message
clarifying
profile_sheet
plan_proposal
routine_card
cannot_proceed
backend_error
network_error
```

It always sets:

```text
safeToAutostartRoutine = false
```

Even when `routine_card_ready` is returned, the frontend may only show a start button. The backend does not start Routine, call Engine, create MIDI, or start playback.

## Safety boundary

The frontend should trust these backend safety fields for assertions and logs:

```text
safety.startsRoutine = false
safety.callsEngineAdapter = false
safety.createsMidiAsset = false
safety.startsPlayback = false
safety.writesHarmonyOSLocalState = false
```

`routineCardPayload.startEnabled=true` means the frontend may enable an explicit user-start button, not that the backend has started anything.

## Recommended next task

`v2_10_20_agent_practice_coach_real_llm_provider_execution_guarded_smoke`:

- keep the same unified frontend contract;
- run the LLM action decision through the configured provider when explicitly enabled;
- preserve deterministic fallback when provider is absent or returns invalid JSON;
- keep all Routine / Engine / MIDI / playback safety gates intact.
