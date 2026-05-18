# JamMatePyEngineV2 Architecture

Current baseline: `v2_4_7`.

This document records the canonical architecture. Version-specific delivery notes belong in separate `docs/*V2_x_x*.md` files.

---

## Top-Level Package Boundary

```text
src/
  jammate_engine/   # Independent accompaniment generation kernel
  jammate_agent/    # Sibling Agent / practice orchestration layer
  jammate_api/      # FastAPI service assembly layer
```

### Boundary rules

- `jammate_engine` must not import `jammate_agent`.
- `jammate_engine` must remain directly callable without LLM/Agent.
- `jammate_agent` may use the engine only through provider/adapter boundaries.
- `jammate_api` may assemble both direct engine routes and Agent routes.
- HarmonyOS local practice state must be able to run without LLM.

---

## Runtime Paths

### Direct accompaniment path

```text
HarmonyOS / client
  -> POST /accompaniment/generate
  -> jammate_api.routes.accompaniment_routes
  -> jammate_engine.runtime.generate.generate_accompaniment
  -> MIDI asset / midi_base64
```

Use this when the client already has explicit accompaniment parameters.

### Agent playback path

```text
HarmonyOS / client
  -> POST /agent/playback/prepare
  -> jammate_api.routes.agent_routes
  -> JamMateAgent workflow
  -> ChartResolver / ImmediatePlaybackWorkflow
  -> JamMateEngineAccompanimentAdapter
  -> jammate_engine.runtime.generate.generate_accompaniment
  -> MIDI asset / playback instruction / trace_id
```

Use this when the user expresses a practice goal or natural-language playback request.

---

## Engine Musical Pipeline

```text
LeadSheet / Score Input
  -> ChordRegionTimeline / performance regions
  -> Style pattern policy
  -> Pitchless event timeline
  -> Anticipation resolver
  -> Expression policy
  -> Voicing policy / selector
  -> Realization
  -> MIDI writer / base64 asset
```

Responsibilities:

```text
Pattern       = horizontal pitchless rhythm / event layout
Anticipation  = pitchless event movement across chord-region boundaries
Expression    = duration, release, velocity, articulation, pedal intent
Voicing       = vertical pitch realization
MIDI          = final note / CC materialization
```

Patterns are style-owned. Voicing and expression are core-level shared systems.

---

## Agent Architecture

```text
jammate_agent/core/
  jammate_agent.py       # high-level Agent facade
  context.py             # context packet structures
  intent_classifier.py   # workflow intent classification
  runloop.py             # bounded workflow loop foundation
  guardrails.py          # validation / safety / constraints
  trace.py               # trace logging and persistence
  contracts.py           # capability/context/contract manifests
  contract_codegen.py    # ArkTS + fixture generation source

jammate_agent/capabilities/
  practice/              # practice plan/session/review capabilities
  accompaniment/         # playback request / provider contracts
  charts/                # chart resolving contracts

jammate_agent/adapters/
  jammate_engine_accompaniment_adapter.py
  local_chart_library_adapter.py
  placeholder_accompaniment_adapter.py
```

The Agent is currently workflow/rule based. Full LLM integration is a future enhancement and should preserve deterministic tool/workflow boundaries.


### LLM Context Runtime Foundation

`v2_4_7` keeps the existing Agent context/trace/contract owners as a previewable LLM runtime envelope and adds a provider-neutral boundary without enabling real LLM calls:

```text
ContextBuilder
  -> ContextPacket
  -> BoundedAgentRunLoop.preview()
  -> AgentContextRuntimePreviewResponse
  -> TraceLogger
```

Rules:

- Context packets are task-scoped and should include only current request, client context, relevant learner/session/material summaries, capability manifest, constraints, allowed tools, output contract, and routing hints.
- `BoundedAgentRunLoop` is preview-only in `v2_4_7`: no API-runloop LLM call and no autonomous tool execution.
- `LLMProviderConfig`, `DisabledLLMProvider`, and the small stdlib OpenAI-compatible chat provider live in `jammate_agent/core/llm_provider.py`.
- `python -m jammate_agent.cli.terminal_chat` may call a configured provider for terminal debugging only; it still does not execute tools.
- Future LLM providers must obey the task-specific allowed tool list, request envelope, and bounded step policy.
- This layer belongs to `jammate_agent/core/` and must not import engine internals.
- Engine access remains adapter-only through `jammate_agent/adapters/`.

### LLM Provider Boundary

`v2_4_7` introduces a thin provider boundary instead of wiring a provider SDK directly into the runloop:

```text
LLMProviderConfig.from_env()
  -> DisabledLLMProvider or OpenAICompatibleChatProvider
  -> build_request_envelope(ContextPacket)
  -> BoundedAgentRunLoop.preview() or terminal_chat CLI
```

Rules:

- `JAMMATE_LLM_PROVIDER`, `JAMMATE_LLM_MODEL`, `JAMMATE_LLM_API_KEY_ENV_VAR`, `JAMMATE_LLM_BASE_URL`, and `JAMMATE_LLM_ENABLE_NETWORK_CALLS` are the provider/config guard surface.
- API runloop preview never executes a provider call.
- Terminal chat may call a provider only when provider, model, API key, and network gate are explicitly configured.
- Provider boundary code must not import provider SDKs or `jammate_engine`.
- Concrete providers must implement `LLMProvider.status()` and `LLMProvider.generate(LLMRequestEnvelope)`.

---

## API Architecture

```text
jammate_api/
  app.py
  schemas.py
  routes/
    health_routes.py
    accompaniment_routes.py
    agent_routes.py
    practice_routes.py
```

API contracts:

- HarmonyOS direct accompaniment uses `POST /accompaniment/generate`, not legacy `/v1/generate-midi-base64`.
- Direct accompaniment should prefer inline `jammate_leadsheet_v2` using `sections + written_form`; `tune` is fallback only.
- Requests accept snake_case and camelCase where useful.
- Backend responses are canonical snake_case.
- HarmonyOS frontend types are camelCase and should use generated `CaseAdapter.ets` for mapping.
- Long practice duration is a client timer concern. The backend returns a playable asset and loop instruction.

---

## HarmonyOS Integration Boundary

HarmonyOS should own:

- local practice tasks/routines/session state
- timers
- playback state
- local asset cache
- UI/store camelCase domain objects
- pending sync

Python backend should own:

- accompaniment generation
- Agent orchestration
- future LLM context/tool workflows
- chart/material resolving that is not local-only
- future MIDI/audio analysis

---

## Delivery Hygiene

Every package handoff must remove transient caches and keep project entry docs clean. See `docs/DEVELOPMENT_HARNESS_V2.md` and `docs/PROJECT_CLEANUP_AND_README_CONSOLIDATION_V2_3_16.md`.

### Agent Terminal Trace Export CLI

`v2_4_7` keeps the validation-only tool invocation preview contract inside terminal chat and adds explicit local trace export:

```text
terminal_chat.py
  -> --trace-dir <dir>
  -> normal chat or /tool-preview <tool_name> [json_args]
  -> ContextBuilder.build(task_type, ...)
  -> ContextPacket.allowed_tools
  -> ToolInvocationProposal
  -> preview_tool_invocation(...)
  -> ToolInvocationPreviewResult
```

The API preview path remains available and shares the same core owner:

```text
POST /agent/tools/invocation/preview
  -> ContextBuilder.build(task_type, ...)
  -> ToolInvocationProposal
  -> preview_tool_invocation(...)
```

Rules:

- The registry is descriptor-only in `v2_4_7`; it does not execute tools.
- `tool_execution_enabled=false` and `autonomous_tool_execution_enabled=false` remain hard runtime guards.
- A future LLM provider may only see tools from the task-specific `ContextPacket.allowed_tools` allow-list.
- Registry and invocation-preview code belong in `jammate_agent/core/` and must not import `jammate_engine` or provider SDKs.
- `terminal_chat.py` may import Agent core context/provider/preview utilities, but must not import `jammate_engine` or provider SDKs.
- Actual engine access remains direct API or Agent adapter workflow, never arbitrary runloop or terminal command execution.
- Terminal `/tool-preview` and API `POST /agent/tools/invocation/preview` validate proposed tool calls against `ContextPacket.allowed_tools` and argument shape only; they never dispatch routes, adapters, or engine workflows.
- Terminal trace export is explicit through `--trace-dir`; it reuses `TraceLogger` / `JsonTraceStore` / `AgentTrace` and must not create a second tracing subsystem.
