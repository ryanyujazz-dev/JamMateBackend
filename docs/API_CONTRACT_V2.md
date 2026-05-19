# JamMate API Contract V2

Current baseline: `v2_8_24`.

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
  "engine_version": "v2_8_24",
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
