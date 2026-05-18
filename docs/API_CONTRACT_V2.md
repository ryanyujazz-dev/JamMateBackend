# JamMate API Contract V2

Current baseline: `v2_4_7`.

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
  "engine_version": "v2_4_7",
  "agent_version": "v0_1"
}
```

---

### Direct accompaniment generation

```text
POST /accompaniment/generate
```

This is the current HarmonyOS direct playback route. Prefer inline `jammate_leadsheet_v2` so user-custom charts do not depend on the server tune resolver. `tune` may still be sent as a fallback hint, but inline `leadsheet` takes priority when both are present.

Request rules:

- Preferred score body: `leadsheet.schema_version = "jammate_leadsheet_v2"`.
- Preferred V2 score fields: `sections` + `written_form`.
- Do not use old Harmony bridge `blocks` + `playback_form` as the direct-generation contract.
- Requests may use camelCase or snake_case for API fields, for example `outputFormat` / `output_format` and `voicingOverride` / `voicing_override`.
- Backend responses remain canonical snake_case.
- Practice duration is owned by the HarmonyOS local timer; the backend should not generate 20/30/45-minute long MIDI files.

Example request:

```json
{
  "leadsheet": {
    "schema_version": "jammate_leadsheet_v2",
    "title": "HarmonyOS Inline Smoke",
    "key": "C",
    "sections": {
      "A": {
        "label": "A",
        "bars": [
          {
            "chords": [
              { "beat": 1.0, "symbol": "Cmaj7" },
              { "beat": 3.0, "symbol": "Dm7" }
            ]
          },
          {
            "chords": [
              { "beat": 1.0, "symbol": "G7" },
              { "beat": 3.0, "symbol": "Cmaj7" }
            ]
          }
        ]
      }
    },
    "written_form": ["A"]
  },
  "tune": "Blue Bossa",
  "style": "bossa_nova",
  "tempo": 120,
  "choruses": 1,
  "voicingOverride": { "harmonicExpansionEnabled": false },
  "outputFormat": "midi_base64"
}
```

Minimum HarmonyOS playback response shape:

```json
{
  "ok": true,
  "asset": {
    "format": "midi_base64",
    "midi_base64": "...",
    "midi_path": "demos/...mid",
    "cache_key": "direct_accomp:..."
  }
}
```

The backend may include `asset.debug_summary` for diagnostics; HarmonyOS should map snake_case to camelCase on the client side when needed.

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
GET  /agent/llm/provider/spec
GET  /agent/tools/registry
```

Use this on `feature/agent-workflow` to inspect the task-scoped context packet, provider-neutral request envelope summary, and bounded runloop envelope that a future LLM provider would receive. `v2_4_7` does not call an LLM and does not execute autonomous tools.

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
    "context_runtime_version": "v2_4_7",
    "task_type": "immediate_practice_playback",
    "allowed_tools": ["chart_resolve", "agent_playback_prepare"],
    "runtime_policy": {
      "tool_loop_mode": "bounded_preview",
      "llm_call_mode": "provider_boundary_preview_only",
      "llm_provider_configured": false,
      "llm_provider_boundary_version": "v2_4_7"
    }
  },
  "runloop_preview": {
    "runtime_mode": "preview_only",
    "tool_execution_enabled": false,
    "next_action": "deterministic_workflow_fallback",
    "llm_provider_status": { "provider_configured": false },
    "request_envelope_summary": { "message_count": 3 }
  },
  "trace_id": "trace_..."
}
```




### Agent tool invocation preview

```text
GET  /agent/tools/invocation/spec
POST /agent/tools/invocation/preview
```

Use this to validate a future LLM-proposed tool call against the task-specific `ContextPacket.allowed_tools` and tool registry descriptor before any execution capability exists.

Example request:

```json
{
  "userInput": "我想练 Blue Bossa 20分钟",
  "taskType": "immediate_practice_playback",
  "toolName": "agent_playback_prepare",
  "arguments": {
    "userInput": "练 Blue Bossa 20分钟",
    "durationMinutes": 20
  },
  "clientContext": {
    "currentScreen": "practice_home",
    "availableMinutes": 20,
    "locale": "zh-CN"
  }
}
```

Expected response shape:

```json
{
  "ok": true,
  "preview": {
    "preview_version": "v2_4_7",
    "status": "preview_only_blocked_by_execution_guard",
    "known_tool": true,
    "allowed_by_context": true,
    "execution_enabled": false,
    "autonomous_execution_enabled": false,
    "would_execute": false,
    "blocking_reasons": ["tool_execution_disabled_in_v2_4_7"]
  },
  "context_packet_summary": {}
}
```

Rules:

- Unknown tools are rejected.
- Tools not present in the task-scoped allow-list are rejected.
- Arguments are normalized and shape-checked only.
- The preview endpoint never dispatches deterministic workflows, adapters, API routes, or engine code.


### Agent tool registry boundary spec

```text
GET /agent/tools/registry
```

Returns descriptor-only Agent tool/workflow contracts for HarmonyOS diagnostics and future bounded LLM tool planning. `v2_4_7` does not execute tools from the runloop. Deterministic API routes remain the only execution path.

Minimum response shape:

```json
{
  "ok": true,
  "registry": {
    "version": "v2_4_7",
    "execution_status": {
      "tool_execution_enabled": false,
      "autonomous_tool_execution_enabled": false,
      "llm_tool_calls_enabled": false
    },
    "tool_names": ["direct_accompaniment_generate", "chart_resolve", "agent_playback_prepare"],
    "task_allow_lists": {
      "immediate_practice_playback": ["direct_accompaniment_generate", "chart_resolve", "agent_playback_prepare"]
    }
  }
}
```

### Agent LLM provider boundary spec

```text
GET /agent/llm/provider/spec
```

Returns provider-neutral configuration/status information. This endpoint is diagnostic only; the API route does not call an LLM and does not enable autonomous tools. Terminal chat can call a configured provider through `python -m jammate_agent.cli.terminal_chat`.

Expected response shape:

```json
{
  "ok": true,
  "spec": {
    "version": "v2_4_7",
    "boundary_version": "v2_4_7",
    "route": "GET /agent/llm/provider/spec",
    "status": {
      "provider_name": "none",
      "provider_configured": false,
      "llm_calls_enabled": false,
      "autonomous_tool_execution_enabled": false
    },
    "guards": {
      "api_runloop_llm_calls_enabled": false,
      "terminal_chat_llm_calls_enabled_when_configured": true,
      "autonomous_tool_execution_enabled": false
    }
  }
}
```

Provider env/config keys currently inspected only:

```text
JAMMATE_LLM_PROVIDER
JAMMATE_LLM_MODEL
JAMMATE_LLM_API_KEY_ENV_VAR
JAMMATE_LLM_API_KEY
JAMMATE_LLM_ENABLE_NETWORK_CALLS
JAMMATE_LLM_BASE_URL
JAMMATE_LLM_CHAT_COMPLETIONS_PATH
JAMMATE_LLM_MAX_PROMPT_CHARS
JAMMATE_LLM_MAX_OUTPUT_TOKENS
JAMMATE_LLM_TEMPERATURE
```


### Terminal Agent chat CLI

```text
PYTHONPATH=src python -m jammate_agent.cli.terminal_chat
```

The CLI is a developer/operator debugging surface, not a HarmonyOS API contract. It uses the same context packet and provider boundary as the Agent runtime preview. It may call an OpenAI-compatible chat-completions provider only when provider, model, API key, and `JAMMATE_LLM_ENABLE_NETWORK_CALLS=true` are explicitly configured. It does not execute tools.

One-shot example:

```bash
PYTHONPATH=src python -m jammate_agent.cli.terminal_chat --once "解释一下 altered dominant"
```

Trace-export one-shot example:

```bash
PYTHONPATH=src python -m jammate_agent.cli.terminal_chat --trace-dir tmp/terminal_traces --once "解释一下 altered dominant"
```

Terminal tool preview example:

```bash
PYTHONPATH=src python -m jammate_agent.cli.terminal_chat --task-type immediate_practice_playback --once '/tool-preview agent_playback_prepare {"durationMinutes":20}'
```

Interactive slash commands:

```text
/help
/tools
/tool-preview <tool_name> [json_object_arguments]
/trace
/traces
/exit
```

`/tool-preview` returns terminal text for the same validation-only preview contract as `POST /agent/tools/invocation/preview`; it does not execute tools, routes, adapters, or engine workflows. `--trace-dir <dir>` explicitly exports normal chat and tool-preview turns as `AgentTrace` JSON via the existing `TraceLogger` / `JsonTraceStore` owner; no traces are written by default.

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
