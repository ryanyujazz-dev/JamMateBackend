# Agent LLM Provider Boundary v2_4_2

## Scope

`v2_4_2_agent_llm_provider_boundary` belongs to `feature/agent-workflow`.

It establishes the optional LLM provider boundary for JamMate Agent without enabling a real provider call and without enabling autonomous tool execution.

No accompaniment engine music-generation logic is changed.

## Harness Reuse Audit

| Need | Existing owner reused / added | Decision |
|---|---|---|
| Provider-neutral config guard | `src/jammate_agent/core/llm_provider.py` | Added one clear long-term owner because provider config/protocol is a distinct boundary, not a runloop detail. |
| Task-scoped context packet | `src/jammate_agent/core/context.py` | Reused `ContextBuilder`; runtime policy now embeds provider status. |
| Bounded runloop preview | `src/jammate_agent/core/runloop.py` | Reused `BoundedAgentRunLoop`; preview now reports provider status and request-envelope summary. |
| API route | `src/jammate_api/routes/agent_routes.py` | Added `GET /agent/llm/provider/spec`; no new route package. |
| Contract/codegen | `src/jammate_agent/core/contracts.py`, `src/jammate_agent/core/contract_codegen.py` | Extended existing contract owners; no parallel contract system. |

## Runtime Shape

```text
ContextBuilder
  -> ContextPacket.runtime_policy.llm_provider_status
  -> build_request_envelope(ContextPacket)
  -> BoundedAgentRunLoop.preview()
  -> runloop_preview.llm_provider_status
  -> runloop_preview.request_envelope_summary
```

Provider boundary:

```text
LLMProviderConfig.from_env()
  -> DisabledLLMProvider.status()
  -> LLMProvider.generate(LLMRequestEnvelope) future protocol
```

## Env / Config Guard

`v2_4_2` inspects these environment variables only:

```text
JAMMATE_LLM_PROVIDER
JAMMATE_LLM_MODEL
JAMMATE_LLM_API_KEY_ENV_VAR
JAMMATE_LLM_API_KEY
JAMMATE_LLM_ENABLE_NETWORK_CALLS
JAMMATE_LLM_MAX_PROMPT_CHARS
JAMMATE_LLM_MAX_OUTPUT_TOKENS
JAMMATE_LLM_TEMPERATURE
```

A provider is considered configured only when:

1. `JAMMATE_LLM_PROVIDER` is not `none` / `disabled` / empty.
2. The configured API key env var exists.
3. `JAMMATE_LLM_ENABLE_NETWORK_CALLS` is truthy.

Even then, `v2_4_2` still does not call the provider. It only reports that the provider is configured but preview-guarded.

## API

```text
GET /agent/llm/provider/spec
```

Returns:

```json
{
  "ok": true,
  "spec": {
    "version": "v2_4_2",
    "boundary_version": "v2_4_2",
    "status": {
      "provider_name": "none",
      "provider_configured": false,
      "llm_calls_enabled": false,
      "autonomous_tool_execution_enabled": false
    },
    "guards": {
      "llm_calls_enabled": false,
      "autonomous_tool_execution_enabled": false
    }
  }
}
```

## Non-goals

- No real LLM network call.
- No autonomous tool execution.
- No provider SDK import.
- No engine generation-rule change.
- No voicing / pattern / expression / pedal change.

## Recommended Next Step

`v2_4_4_agent_terminal_chat_cli_foundation`

Suggested scope:

- Define a task-scoped Agent tool registry boundary.
- Map current deterministic workflows to tool descriptors.
- Keep execution disabled or deterministic-only.
- Do not allow arbitrary tool calls from an LLM yet.
