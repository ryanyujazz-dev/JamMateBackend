# JamMate API Contract V2

Current baseline: `v2_4_0`.

This document records the stable API contract shape. Detailed version-specific API delivery notes live in separate `docs/*V2_x_x*.md` files.

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
  "engine_version": "v2_4_0",
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

### Agent LLM context runtime preview

```text
GET  /agent/context/runtime/spec
POST /agent/context/runtime/preview
```

Use this on `feature/agent-workflow` to inspect the task-scoped context packet and bounded runloop envelope that a future LLM provider would receive. `v2_4_0` does not call an LLM and does not execute autonomous tools.

Example request:

```json
{
  "requestId": "ctx_preview_001",
  "userInput": "我想练 Blue Bossa 20分钟，帮我安排一下",
  "taskType": "immediate_practice_playback",
  "durationMinutes": 20,
  "instrument": "piano",
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
  "task_type": "immediate_practice_playback",
  "context_packet": {
    "context_runtime_version": "v2_4_0",
    "task_type": "immediate_practice_playback",
    "allowed_tools": ["chart_resolve", "agent_playback_prepare"],
    "runtime_policy": {
      "tool_loop_mode": "bounded_preview",
      "llm_provider_configured": false
    }
  },
  "runloop_preview": {
    "runtime_mode": "preview_only",
    "tool_execution_enabled": false,
    "next_action": "deterministic_workflow_fallback"
  },
  "trace_id": "trace_..."
}
```

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
GET /agent/context/runtime/spec
POST /agent/context/runtime/preview
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
