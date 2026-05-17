# JamMate HarmonyOS Frontend Fixture Pack v2_3_15

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
