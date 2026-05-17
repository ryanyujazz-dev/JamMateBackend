# v2_3_15 — HarmonyOS Response Case Policy

## Decision

Python/FastAPI backend responses remain canonical `snake_case`. HarmonyOS requests may be sent as `camelCase` or `snake_case`, but HarmonyOS UI and local store code should consume camelCase client-domain objects after applying `CaseAdapter.ets`.

```text
Backend raw response: trace_id / playback_instruction / midi_base64 / cache_key
HarmonyOS domain object: traceId / playbackInstruction / midiBase64 / cacheKey
```

## Why

1. Python/Pydantic/FastAPI remain stable and simple with snake_case.
2. HarmonyOS ArkTS code remains idiomatic with camelCase.
3. We avoid maintaining two backend response formats.
4. The adapter boundary is explicit, testable, and copyable.

## Endpoints

```text
GET /agent/contracts/case-policy
GET /agent/contracts/arkts/files
GET /agent/contracts/frontend-pack
```

## Generated files

```text
frontend_fixtures/harmonyos/api/CaseAdapter.ets
frontend_fixtures/harmonyos/api/JamMateApiClient.ets
frontend_fixtures/harmonyos/types/AgentTypes.ets
frontend_fixtures/harmonyos/types/PracticeTypes.ets
frontend_fixtures/harmonyos/types/PlaybackTypes.ets
```

## Client rule

Use `JamMateApiClient.ets` or equivalent logic to call backend endpoints, then map raw responses with:

```text
mapAgentResponse(raw)
mapDirectAccompanimentResponse(raw)
```

The backend still returns snake_case when inspected directly. This is intentional.
