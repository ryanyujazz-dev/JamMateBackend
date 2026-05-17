# v2_3_15 — HarmonyOS API Smoke Test Pack

This pass turns the HarmonyOS-facing Agent/API contract into copy-friendly generated artifacts and stable UI fixtures.

## Scope

Runtime music generation is unchanged. `jammate_engine` remains an independent accompaniment engine, and direct accompaniment remains available without LLM/Agent.

This pass adds:

```text
GET /agent/contracts/arkts/files
GET /agent/contracts/fixtures
GET /agent/contracts/frontend-pack
```

It also adds a repository fixture pack under:

```text
frontend_fixtures/harmonyos/
  README.md
  types/AgentTypes.ets
  types/PracticeTypes.ets
  types/PlaybackTypes.ets
  api/JamMateApiClient.ets
  fixtures/PracticeFixtures.json
```

## Design rule

The generated ArkTS files are a frontend integration starting point, not a new source of backend truth. The canonical contract remains the Python API + JSON response shape. The generated files are intentionally simple so HarmonyOS can copy them into its own feature modules and adapt naming/import paths.

## Contract paths

### `GET /agent/contracts/arkts/files`

Returns multiple copyable ArkTS source files:

```json
{
  "ok": true,
  "version": "v2_3_15",
  "response_case": "snake_case",
  "request_case": "camelCase_or_snake_case",
  "files": [
    {
      "filename": "AgentTypes.ets",
      "relative_path": "entry/src/main/ets/features/jammateAgent/model/AgentTypes.ets",
      "purpose": "...",
      "source": "..."
    }
  ]
}
```

### `GET /agent/contracts/fixtures`

Returns stable mock payloads for frontend development. Fixture MIDI is placeholder base64 and should not be treated as musical output.

Main fixtures:

```text
agentPracticePlanResponse
agentPlaybackPrepareResponse
directAccompanimentGenerateResponse
sessionReviewRequest
```

### `GET /agent/contracts/frontend-pack`

Returns a filesystem-style pack combining ArkTS types, client sketch, fixture JSON, and README.

## HarmonyOS integration rule

HarmonyOS local practice workspace should still work without LLM:

```text
local tasks / routines / timer / review / history
```

Direct accompaniment should call:

```text
POST /accompaniment/generate
```

Natural-language planning/playback should call:

```text
POST /agent/practice/plan
POST /agent/playback/prepare
```

## Playback rule

Practice duration remains a local timer target. If:

```json
"client_loop_until_target_duration": true
```

HarmonyOS should loop the returned MIDI asset locally until the local practice timer reaches `target_duration_minutes` or the user stops.

## Recommended next task

`v2_3_15_harmonyos_api_smoke_test_pack` — decide whether API responses should remain canonical snake_case or expose an optional camelCase response mode for HarmonyOS.
