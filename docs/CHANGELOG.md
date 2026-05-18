# JamMatePyEngineV2 Changelog

## v2_4_13 — Agent Tool Call Preview Trace Contract

- Added a stable terminal tool-call preview trace contract for the chain: LLM response -> explicit JSON candidate extraction -> preview validation -> execution guard.
- Focused doc: `docs/AGENT_TOOL_CALL_PREVIEW_TRACE_CONTRACT_V2_4_13.md`.
- Added `build_tool_call_preview_trace_summary(...)` and `tool_call_preview_trace_contract()` in `jammate_agent.core.tool_invocation`, reusing the existing tool invocation owner.
- Terminal chat trace export now records `terminal_tool_call_preview_trace_summary_recorded` and places `tool_call_preview_trace_summary` in `final_response_summary`.
- Trace API/runtime specs expose the tool-call preview trace boundary for HarmonyOS and terminal debugging.
- The contract is trace-only: no tool execution, no deterministic workflow dispatch, no API route dispatch, no adapter call, and no engine call.
- Runtime music generation behavior is unchanged.

## v2_4_12 — Agent Terminal LLM Config Wizard

- Added `jammate-agent-chat setup`, `jammate-agent-chat doctor`, and `jammate-agent-chat config-path` for local terminal LLM configuration.
- Added `.env`-style config loading with precedence: explicit env vars, `JAMMATE_AGENT_LLM_CONFIG_FILE`, repo-local `.jammate_agent.env`, then `~/.jammate/agent_config.env`.
- API key values are masked from setup output, doctor output, provider status, config summaries, and traces.
- Terminal chat can use `--config-file <path>` instead of requiring repeated shell `export` commands.
- Tool execution, deterministic workflow dispatch, adapter calls, API route dispatch, and engine calls remain disabled from terminal LLM flows.
- Runtime music generation behavior is unchanged.

## v2_4_11 — Agent Terminal Tool Call Candidate Extraction

- Added explicit JSON-only tool-call candidate extraction from successful terminal LLM replies.
- Reused `core/tool_invocation.py` as the owner for candidate extraction and validation-only preview; no second parser/tool subsystem was added.
- Terminal chat now sends extracted candidates through `preview_tool_invocation(...)` using the current task-scoped `ContextPacket.allowed_tools`.
- Supported candidate shapes include `tool_name`/`toolName`, `tool_call`, `function_call`, and `tool_calls` JSON objects/lists, either as full assistant messages or fenced JSON blocks.
- Extracted candidates never execute tools, dispatch workflows, call adapters, call API routes, or call the engine.
- Runtime music generation behavior is unchanged.

## v2_4_10 — Agent Terminal Chat Context Controls

- Added explicit terminal chat context/profile/session controls: `/context`, `/profiles`, `/profile`, `/task-type`, `/instrument`, `/session`, and `/reset`.
- Reused the existing `terminal_chat.py` owner and `ContextBuilder`; no parallel chat CLI or context subsystem was added.
- `/context` and `/context full` build ContextPacket previews only; they do not call the provider, execute tools, dispatch workflows, or call the engine.
- `/profile` and `/task-type` switch the active task profile and clear local terminal history to avoid cross-profile conversation leakage.
- `/instrument` updates the instrument hint used by future ContextPacket builds; `/reset` clears local chat history.
- Existing `/tool-preview`, trace export, read-only trace viewer, and HarmonyOS `/accompaniment/generate` contracts remain intact.
- Runtime music generation behavior is unchanged.

## v2_4_9 — Agent Trace Viewer CLI

- Added a read-only local terminal trace viewer: `python -m jammate_agent.cli.trace_viewer`.
- Added console script `jammate-agent-traces`.
- Viewer supports `list`, `show <trace_id>`, and `spec`, with optional `--json` output.
- Viewer reuses `JsonTraceStore` and `AgentTrace` summary/detail contracts; no second tracing subsystem was added.
- Viewer is inspection-only: no tool execution, no deterministic workflow dispatch, no provider call, no adapter/engine call.
- Updated README, agent harness, architecture/API/task-plan docs, and focused regression tests.


## v2_4_8 — Agent Trace API Contract Hardening

- Added `GET /agent/traces/spec` as the machine-readable Trace API contract route.
- Hardened `GET /agent/traces` responses with `trace_contract_version`, stable summary fields, `step_count`, and context/final-summary flags.
- Hardened `GET /agent/traces/{trace_id}` responses with versioned detail payloads and a stable `TRACE_NOT_FOUND` shape.
- Reused the existing `TraceLogger` / `JsonTraceStore` / `AgentTrace` owner; no second tracing subsystem was introduced.
- Updated ArkTS types, API client sketch, smoke pack, README, API contract, architecture, task plan, and harness references.
- Trace APIs remain inspection-only: no autonomous tools, no deterministic workflow dispatch, no adapter dispatch, no engine call, and no provider call.
- Runtime music generation behavior is unchanged.

## v2_4_7 — Agent Terminal Trace Export

- Added explicit terminal trace export through `--trace-dir <dir>` on `python -m jammate_agent.cli.terminal_chat` and the `jammate-agent-chat` console script.
- Reused the existing `TraceLogger` / `JsonTraceStore` / `AgentTrace` owner instead of creating a second tracing subsystem.
- Terminal chat traces now capture context packet summaries, request-envelope summaries, provider response summaries, and final response summaries.
- Terminal `/tool-preview` traces now capture context packet summaries and validation-only tool invocation preview results.
- Added `/trace` and `/traces` terminal commands for inspecting the most recent local trace export.
- Trace export remains explicit, local, and debug-only: no autonomous tools, no deterministic workflow dispatch, no adapter dispatch, no engine call, and no provider guard bypass.
- Runtime music generation behavior is unchanged.

## v2_4_6 — Agent Terminal Tool Preview CLI

- Added explicit `/tool-preview <tool_name> [json_object_arguments]` command inside `python -m jammate_agent.cli.terminal_chat` and the `jammate-agent-chat` console script.
- Reused `ContextBuilder`, task-scoped `ContextPacket.allowed_tools`, `tool_registry.py`, and `tool_invocation.py` instead of creating a second terminal tool stack.
- Added `/tools` and `/help` terminal commands for local debugging of allowed tool names and CLI usage.
- Tool preview from the terminal remains validation-only: no deterministic workflow dispatch, no API route dispatch, no adapter dispatch, no engine call, and no autonomous tool execution.
- Normal terminal chat provider behavior remains unchanged: provider calls require explicit env guards and never execute tools.
- Runtime music generation behavior is unchanged.

This file is the chronological project history. README should remain the project overview; `agent.md` should remain the development harness.

---

## v2_4_5 — Agent Tool Invocation Preview Contract

- Added `jammate_agent/core/tool_invocation.py` as the validation-only owner for future LLM-proposed tool calls.
- Added `GET /agent/tools/invocation/spec` and `POST /agent/tools/invocation/preview`.
- Tool-call proposals validate against the task-scoped `ContextPacket.allowed_tools` and registry descriptors, but never dispatch deterministic workflows, adapters, routes, or engine code.
- Context/runtime policies expose `tool_invocation_preview_version` and preview-only execution guards.
- HarmonyOS contract/codegen/smoke fixtures include the preview endpoint.
- Runtime music generation behavior is unchanged.

## v2_4_4 — Agent Terminal Chat CLI Foundation

- Added `src/jammate_agent/cli/terminal_chat.py` and console script `jammate-agent-chat` for terminal-first LLM conversation debugging.
- Reused ContextBuilder, ContextPacket, provider boundary, and tool registry descriptors instead of creating a separate prompt stack.
- Added stdlib-only OpenAI-compatible chat-completions provider support behind explicit env guards: provider, model, API key, and `JAMMATE_LLM_ENABLE_NETWORK_CALLS=true`.
- Kept API runloop preview-only and kept autonomous/tool execution disabled; terminal chat can see tool descriptors as context but cannot execute tools.
- Preserved HarmonyOS `/accompaniment/generate` inline leadsheet contract and left runtime music generation unchanged.

## v2_4_2 — Agent LLM Provider Boundary

- Added provider-neutral `src/jammate_agent/core/llm_provider.py` with `LLMProviderConfig`, `DisabledLLMProvider`, `LLMRequestEnvelope`, and provider protocol shape.
- Added `GET /agent/llm/provider/spec` to inspect provider config/status without making network calls.
- Extended context runtime packets and runloop preview with provider status, request-envelope summary, and explicit `llm_call_mode = provider_boundary_preview_only`.
- Kept `llm_calls_enabled = false` and `autonomous_tool_execution_enabled = false` even when future provider config env vars are present.
- Synchronized Agent capability manifest, API docs, ArkTS contract codegen, fixtures, smoke pack, and harness docs.
- Runtime music generation behavior is unchanged from `v2_3_17`; no voicing/pattern/expression/pedal deepening in this delivery.

## v2_4_1 — HarmonyOS Generate Contract Sync

- Hardened `POST /accompaniment/generate` as the current HarmonyOS direct accompaniment route.
- Promoted inline `jammate_leadsheet_v2` with `sections + written_form` as the preferred direct-generation chart input; `tune` remains fallback only.
- Added leadsheet content signatures to direct output paths and `asset.cache_key` to avoid user-custom chart cache collisions.
- Added graceful `INVALID_LEADSHEET` response handling for malformed inline leadsheets.
- Synchronized HarmonyOS ArkTS contract types, fixture pack, smoke pack, API docs, and capability manifests around the inline leadsheet contract.
- Runtime music generation behavior is unchanged from `v2_3_17`; no voicing/pattern/expression/pedal deepening in this delivery.

## v2_4_0 — Agent LLM Context Runtime Foundation

- Promoted the existing Agent `ContextBuilder` / `ContextPacket` into a task-scoped LLM context runtime preview envelope.
- Added preview-only `BoundedAgentRunLoop` contract with bounded steps, task-specific allowed tools, and no real LLM/tool execution in this version.
- Added `GET /agent/context/runtime/spec` and `POST /agent/context/runtime/preview` for HarmonyOS/backend inspection.
- Synchronized Agent capability/context manifests, ArkTS contract generation, frontend fixtures, and smoke-pack files around the new runtime preview contract.
- Kept `feature/agent-workflow` scoped to Agent/API/HarmonyOS contracts; accompaniment engine generation behavior is unchanged from `v2_3_17`.

## v2_3_17 — Harness Hardening and Changelog Split

- Compressed `agent.md` into a short hard development harness.
- Rewrote `docs/DEVELOPMENT_HARNESS_V2.md` as the expanded harness explanation.
- Added this `docs/CHANGELOG.md` as the canonical place for chronological version history.
- Replaced the oversized historical `tools/check_development_harness.py` with a focused automated harness checker.
- Added a targeted regression test for harness/changelog/cleanup behavior.
- Runtime music generation behavior is unchanged from `v2_3_16`.

## v2_3_16 — Project Cleanup and README Consolidation

- Converted README into the project entrance document: core design principles, directory architecture, core features, startup and validation commands.
- Removed README-style rolling implementation history from the project entrance.
- Added package cleanup rules and `.gitignore`.
- Kept the package as a clean baseline for two-window Agent/Engine development.

## v2_3_15 — HarmonyOS API Smoke Test Pack

- Added HarmonyOS API smoke-pack endpoints and repository fixtures.
- Added `/health`, `/accompaniment/generate`, and `/agent/playback/prepare` minimum validation sequence.
- Added curl smoke script and LAN testing notes.

## v2_3_14 — Agent Contract Case Policy and Response Adapter

- Kept backend API responses canonical `snake_case`.
- Added HarmonyOS client-domain `camelCase` model mapping through `CaseAdapter.ets`.
- Added `/agent/contracts/case-policy` and synchronized frontend fixtures.

## v2_3_13 — Agent Contract Codegen and Frontend Fixture Pack

- Added generated ArkTS contract file pack.
- Added `AgentTypes.ets`, `PracticeTypes.ets`, `PlaybackTypes.ets`, `JamMateApiClient.ets` sketches.
- Added HarmonyOS fixture JSON for frontend mock/integration work.

## v2_3_12 — HarmonyOS Practice API Contract Sync

- Added HarmonyOS playback/cache contract details.
- Added API examples for direct accompaniment and Agent playback.
- Clarified `client_loop_until_target_duration` and local practice timer ownership.

## v2_3_11 — JamMate Agent Context and Contract Hardening

- Added Agent capability and context profile manifests.
- Added persistent Agent trace store.
- Added snake_case/camelCase request compatibility.
- Added contract endpoints for HarmonyOS integration.

## v2_3_10 — Agent / Engine / API Boundary Foundation

- Introduced sibling `jammate_agent` and `jammate_api` packages beside `jammate_engine`.
- Preserved direct engine accompaniment generation without LLM/Agent.
- Added Agent playback preparation route backed by the engine adapter.
