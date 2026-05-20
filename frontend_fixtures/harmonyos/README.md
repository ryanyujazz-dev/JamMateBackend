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
