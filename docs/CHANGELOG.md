## v2_10_28 — Context persistence SQLite path guard macOS tempdir hotfix

- Fixed `routine-completion-record/execute` context persistence SQLite path guard for macOS pytest tempdirs such as `/private/var/folders/...`.
- Aligned `tool_invocation.py` with the v2_10_22 Practice Coach session-state path policy by allowing the resolved `tempfile.gettempdir()` root.
- Added v2_10_28 regression tests for direct guard behavior and route persistence.
- No Engine generation logic changed.

## v2_10_27 — Practice Coach HarmonyOS UI integration feedback fit

- Added `frontendUiAction` to Practice Coach message responses for HarmonyOS UI rendering hints.
- Added completion-record `frontendUiAction` for RoutineSummaryPage recorded-state rendering.
- Added product fixture, curl smoke, tests, and docs for proposal/revision/card/completion/next-history UI integration.
- Agent/Integration-only; Engine generation logic unchanged.

## v2_10_26 — Practice Coach routine-card completion loop smoke

- Added HarmonyOS-facing smoke coverage for Practice Coach routine card confirmation, completion record persistence, and next-turn history readback.
- No Engine generation logic changed.

## v2_10_25 — Practice Coach device feedback trace pack

- Added `deviceFeedbackTracePack` to unified Practice Coach responses at `data.deviceFeedbackTracePack` and `debug.deviceFeedbackTracePack`.
- The pack summarizes request, responseType, decision source/fallback, schema repair, state digests, plan/card artifacts, SQLite IO, and safety flags.
- Added HarmonyOS smoke fixture and curl script for verifying the trace pack.
- Updated frontend type fixtures with `PracticeCoachDeviceFeedbackTracePack`.
- Preserved black-box frontend contract and Agent/Engine boundaries: no Engine call, no MIDI/playback generation, no Routine auto-start, and no HarmonyOS local-state write.


## v2_10_24

- Added a HarmonyOS/front-end-facing Practice Coach plan revision E2E smoke pack.
- Added `product_practice_coach_plan_revision_e2e_sequence.json` and `curl_practice_coach_plan_revision_e2e_smoke.sh`.
- Locked the original reported flow in tests: initial plan, duration revision, fundamentals/metronome revision, tune-practice revision, and final confirmation to Routine card.
- Preserved black-box frontend contract and Agent/Engine boundaries: no Engine call, no MIDI/playback generation, no Routine auto-start, and no HarmonyOS local-state write.

## v2_10_22_agent_practice_coach_sqlite_path_guard_macos_tempdir_hotfix

- Fixed a macOS local pytest compatibility issue where Practice Coach SQLite paths under `/private/var/folders/...` were blocked by a Linux-specific allowlist.
- The path guard now also allows the resolved `tempfile.gettempdir()` root while keeping unsafe-path rejection.
- No Engine generation logic changed.

## v2_10_21_agent_practice_coach_live_llm_response_repair_and_schema_hardening

- Hardened Practice Coach live LLM action decisions with response repair and schema validation.
- Added safe repair for Markdown/JSON wrapping and common action field aliases.
- Added deterministic fallback for invalid/unsafe LLM outputs.
- Preserved Agent/Integration boundary: 不启动 Routine, 不调用 Engine, 不生成 MIDI, 不播放.

## v2_10_20_agent_practice_coach_real_llm_provider_execution_guarded_smoke

- Added opt-in real LLM provider smoke for Practice Coach Session unified message execution.
- Added production-shaped live LLM request fixture and curl smoke script.
- Added tests with a local OpenAI-compatible stub provider.
- Updated HarmonyOS smoke pack and API docs.
- Preserved all Agent/Integration safety boundaries; Engine generation logic was not changed.

## v2_10_19_agent_practice_coach_frontend_contract_types_and_state_mapper

- Added frontend fixture types and state mapper for the unified Practice Coach Session endpoint.
- Updated HarmonyOS fixture README/API docs and smoke pack metadata.
- Confirmed production frontend types do not include `llmActionDecisionResult`; smoke-only LLM action fixtures remain separate.
- No Engine music generation changes.

## v2_10_18 — Practice Coach Frontend LLM Action Fixture Smoke

- Added unified Practice Coach frontend/device smoke pack for `POST /agent/harmonyos/practice-coach-session/message/execute`.
- Added product fixtures that intentionally omit backend internals and LLM injection fields.
- Added smoke-only LLM action injection fixtures for responseType coverage.
- Added curl smoke script and regression tests for the new fixture pack.
- Updated Agent/API docs and version metadata to `v2_10_18`.
- Preserved Engine boundary: no music generation logic changed.

## v2_10_17 — Practice Coach LLM Action Decision Contract

- Upgraded the Practice Coach unified HarmonyOS route to prefer LLM-selected structured action intent.
- Preserved deterministic router as fallback when provider output is unavailable, disabled, unsafe, or invalid.
- Added LLM action request preview / validation / fallback debug fields.
- Added tests and Agent documentation for the new contract.
- No Engine generation, MIDI, playback, voicing, style, or accompaniment logic changed.

## v2_10_16 — Practice Coach Unified Message/Action Router

- Added HarmonyOS Practice Coach unified message/action router endpoint.
- Added deterministic auto-routing from chat message to clarification, profile sheet, plan proposal, or routine card ready.
- No Engine music-generation changes.

## v2_10_15 — Practice Coach Profile Sheet Intent Contract

- Added HarmonyOS-facing `profile-sheet/execute` contract for Practice Coach Session.
- Added structured `sheetIntent` with required profile fields and submit action.
- Added profile form result persistence into backend Practice Coach session state.
- Added focused tests and development documentation.
- Preserved no-LLM/no-Routine/no-Engine/no-MIDI/no-HarmonyOS-local-write safety boundary.

## v2_10_14 — Practice Coach Plan Confirmation to Routine Card Contract

- Added Practice Coach Session confirmation-to-card contract.
- New route: `POST /agent/harmonyos/practice-coach-session/routine-card/execute`.
- Converts explicit confirmation of a saved `draft_plan` into HarmonyOS `routineCardPayload`.
- Preserved boundaries: no LLM/provider call, no Routine start, no Engine call, no MIDI, no playback, no HarmonyOS local-state write.
- Added focused development doc and tests for v2_10_14.

## v2_10_13 — Practice Coach Session Plan Proposal Contract

- Added Practice Coach plan proposal endpoint and deterministic proposal contract.
- The endpoint returns either `ask_clarifying_question` or `practice_plan_proposal`.
- Proposal remains a draft requiring user confirmation; `routineCardPayload` remains null in this step.
- Engine/music generation code was not changed.

## v2_10_12 — Practice Coach Session Conversation State Store

- Added `POST /agent/harmonyos/practice-coach-session/message-state/execute`.
- Added backend SQLite state continuity for Practice Coach Session turns via `practice_coach_session_states` and `practice_coach_session_turns`.
- The first `今天该练什么？` turn can persist missing fields; a later same-session reply such as `20 分钟，想练 Bossa` can restore the prior pending question and collect the answer.
- The route returns updated `llmRequestPreview` for cache/debug inspection but does not call an LLM/provider.
- No Engine music-generation logic was changed.

## v2_10_11 — Practice Coach Session Context Builder

- Added the Practice Coach Session context-builder preview route: `POST /agent/harmonyos/practice-coach-session/context-builder-preview`.
- Established cache-friendly LLM context block ordering and digests for product/action contract, user profile, active plan, recent practice memory, session state, and current user turn.
- Projected Routine completion `items` and `notes` into compact practice memory summaries for future Practice Coach Session decisions.
- Preserved boundaries: preview only, no LLM call, no Routine start, no Engine call, no MIDI/playback, no HarmonyOS local-state write.

# JamMatePyEngineV2 Changelog

## v2_10_10 — HarmonyOS Agent Today Guidance LLM Payload Trace

- Added `POST /agent/harmonyos/today-practice-guidance/llm-payload-trace`, a read-only debug endpoint that shows the LLM request preview for the user action “今天该练什么？”.
- The trace response exposes `data.llmRequestPreview.internalPromptMessages`, `chatCompletionsMessagesIfCalled`, `chatCompletionsRequestBodyPreview`, `assembledPracticeContext`, `outputSchema`, and `promptPolicy`.
- Documented internal role handling: JamMate may build `system` / `developer` / `user` / `context` messages, while OpenAI-compatible network payloads merge `developer` and `context` into a leading `system` message.
- Preserved black-box HarmonyOS product inputs: frontend still sends `userId`, `sessionId`, `deviceId`, and `userMessage`, not backend DB paths or write gates.
- Preserved safety boundaries: the trace route makes no LLM/network call, executes no tools, starts no Routine, calls no Engine adapter, creates no MIDI, and starts no playback.
- Runtime music generation behavior is unchanged; no Engine generation logic was modified.

## v2_10_9 — HarmonyOS Agent Black-Box Runtime and Device Smoke

- Added exact HarmonyOS product-contract fixtures for `routine-completion-record/execute` and `today-practice-guidance/preview` that omit `dbPath` / `sqliteDbPath` and `clientConfirmedRecordWrite`.
- Added `curl_agent_black_box_product_contract_smoke.sh`, a runtime/device smoke script that calls `GET /health`, persists a Routine completion record, then previews today guidance using only black-box product payloads.
- Updated HarmonyOS smoke README, smoke-pack metadata, API contract notes, and integration task plan with LAN/device instructions: Mac FastAPI must listen on `0.0.0.0`, phone baseUrl must use the Mac LAN IP, and `/health` should be verified first.
- Preserved safety boundaries: no HarmonyOS local-state write, no Routine start, no Engine adapter call, no MIDI creation, no playback, and no post-session recommendation card.
- Runtime music generation behavior is unchanged; no Engine generation logic was modified.

## v2_10_8 — HarmonyOS Agent Black-Box Contract Fit

- Aligned the backend HarmonyOS Agent product wrappers with the actual frontend contract report: HarmonyOS sends only user/session/device fields plus `routineCompletionRecord` or `userMessage`.
- Product wrappers now inject backend-owned SQLite context path and internal write confirmation when the frontend omits `dbPath` / `clientConfirmedRecordWrite`.
- Preserved safety boundaries: no HarmonyOS local-state write, no Routine start, no Engine adapter call, no MIDI creation, no playback.


## v2_10_8 — Integration Agent / Engine Merge

- Merged Engine Track through `v2_6_44_engine_ballad_spread_voicing_phase_summary_handoff`.
- Merged Agent Track through `v2_10_7_agent_harmonyos_today_guidance_runtime_smoke`.
- Reconciled integration-owned shared files: `README.md`, `agent.md`, `VERSION`, `pyproject.toml`, `docs/ARCHITECTURE_V2.md`, `docs/API_CONTRACT_V2.md`, `docs/DEVELOPMENT_TASK_PLAN_V2.md`, `docs/CHANGELOG.md`, and `frontend_fixtures/harmonyos/`.
- Preserved the direct HarmonyOS `/accompaniment/generate` response shape with top-level `ok`, `asset.format`, `asset.midi_base64`, `asset.midi_path`, `asset.cache_key`, and top-level `debug_summary`.
- Preserved Agent contract / trace / tool-preview / context-guidance / persistence-preview / HarmonyOS product route boundaries without moving Agent logic into Engine runtime.
- Preserved V2 Pattern / Gesture / Expression / Voicing / Realization boundaries; no new music-generation rule or V1 code migration was added by this integration pass.
- Engine-side changes since v2_8_24 include frozen Ballad SPREAD guardrails, lower-foundation calibration, safe extension frequency calibration, and phrase-state anchor policy.
- Agent-side changes since v2_8_24 include routine-completion-record persistence, today-practice-guidance with SQLite backend readback, and HarmonyOS runtime smoke.

## v2_8_24 — Integration Agent / Engine Merge

- Merged Engine Track through `v2_6_30_engine_ballad_spread_1plus4_lower_foundation_calibration`.
- Merged Agent Track through `v2_8_23_agent_v2_8_phase_cleanup_regression_handoff`.
- Reconciled integration-owned shared files: `README.md`, `agent.md`, `VERSION`, `pyproject.toml`, `docs/ARCHITECTURE_V2.md`, `docs/API_CONTRACT_V2.md`, `docs/DEVELOPMENT_TASK_PLAN_V2.md`, `docs/CHANGELOG.md`, and `frontend_fixtures/harmonyos/`.
- Preserved and explicitly restored the direct HarmonyOS `/accompaniment/generate` response shape with top-level `ok`, `asset.format`, `asset.midi_base64`, `asset.midi_path`, `asset.cache_key`, and top-level `debug_summary` while retaining the existing `asset.debug_summary` compatibility field.
- Preserved Agent contract / trace / tool-preview / context-guidance preview boundaries without moving Agent logic into Engine runtime.
- Preserved V2 Pattern / Gesture / Expression / Voicing / Realization boundaries; no new music-generation rule, Agent/LLM feature, or V1 code migration was added by this integration pass.
- Aligned stale version/string assertions and historical SPREAD freeze expectations in tests to the active integration/Engine baseline without changing Engine generation runtime behavior.

## v2_6_1 — Branch Boundary and Track Ownership Hardening

- Added `docs/BRANCH_AND_TRACK_OWNERSHIP_V2.md` as the authoritative owner-path and merge-conflict policy for parallel Engine and Agent development.
- Split rolling task plans into `docs/DEVELOPMENT_TASK_PLAN_ENGINE_V2.md` and `docs/DEVELOPMENT_TASK_PLAN_AGENT_V2.md`; the main `DEVELOPMENT_TASK_PLAN_V2.md` is now an integration index.
- Split track history into `docs/CHANGELOG_ENGINE.md` and `docs/CHANGELOG_AGENT.md`; the main changelog remains integration-level chronology.
- Hardened `agent.md`, `docs/DEVELOPMENT_HARNESS_V2.md`, and `tools/check_development_harness.py` so shared-file edits are treated as integration-owned by default.
- Bumped package/version surfaces and HarmonyOS contract fixtures to `v2_6_1`.
- No engine music-generation logic, Agent execution behavior, or API response shape changed.

## v2_5_10 — Agent / Engine Integration Merge

- Merged Agent workflow line through `v2_4_13` into the official engine-deepening line through `v2_5_9`.
- Preserved engine runtime behavior, Jazz Ballad swing-8 timing, V2 gesture/expression/voicing boundaries, and the V1 instrument-rule mapping baseline.
- Preserved Agent terminal chat, provider boundary, local config wizard, validation-only tool preview, read-only trace viewer, JSON tool-call candidate extraction, and preview trace contract.
- Kept HarmonyOS `/accompaniment/generate` direct playback contract stable.
- Added focused integration doc: `docs/AGENT_ENGINE_INTEGRATION_MERGE_V2_5_10.md`.
- No new music-generation feature was added in this merge pass.

## v2_5_9 — V1 Instrument Rules Deep Audit and V2-Native Mapping

- Documentation-only engine planning pass based on `v2_5_8`; no generation code changed.
- Explicitly discards the prior experimental Ballad brush-drums shortcut as an abandoned trial, not an official baseline.
- Added `docs/V1_INSTRUMENT_RULES_DEEP_AUDIT_AND_V2_NATIVE_MAPPING_V2_5_9.md`.
- Deep-audited V1 Jazz Ballad, Medium Swing, and Bossa Nova piano/bass/drums rules and mapped them to V2-native owners.
- Reaffirmed that V1 is a musical-rule reference only: no code migration, no V1 phrase-engine/runtime mirror, no pattern-to-texture binding, and no MIDI repair paths.
- Recommended next engine task: `v2_5_10_jazz_ballad_bass_anchor_path_policy`.


## v2_5_8 — Jazz Ballad Default Swing-8 Anticipation Timing Patch

- Changed Jazz Ballad timing policy from a temporary straight profile with local `1&` swing tags to a default swing-8 feel (`feel=swing`). Written `.5` upbeats remain logical pattern positions and render at the triplet/swing `2/3` point.
- Corrected Ballad anticipation to use the same swing-upbeat timing contract: logical previous `4&` stays at `.5`, but anticipated events carry `timing_intent=swing_upbeat`, `timing_grid=swing_triplet_upbeat`, `performed_lead_in_beats=1/3`, and `expected_upbeat_fraction=2/3`.
- Kept V2 ownership boundaries: no literal `0.666...` in pattern candidates, no V1 code migration, no voicing texture binding, no Agent/LLM behavior change, and no MIDI repair path.

## v2_5_7 — Jazz Ballad 1& Sustain Continuity Bugfix

- Fixed the Ballad `beat 1 → swing 1&` continuity bug: the expression next-event clamp now respects event-level timing intent, so an anchor before a `timing_intent=swing_upbeat` event sustains to the performed `2/3` upbeat instead of stopping at the logical `0.5` grid point.
- Changed `soft_whisper` from a short articulation to a light sustained articulation; Ballad near-downbeat re-touch should not sound like a clipped/stuttering hit.
- Kept the fix inside V2 boundaries: pattern still stores logical `0.5`; timing remains owned by the timing policy/render contract; expression only uses the already-declared timing intent to choose a connected duration.
- No V1 code migration, no Agent/LLM changes, no voicing texture binding, and no MIDI repair path were added.

## v2_5_6 — Jazz Ballad Swing 1& Timing Patch

- Corrected the v2_5_5 Ballad `1&` timing interpretation: logical beat `0.5` remains the pattern-layer written upbeat, but the second `1&` piano touch now carries `timing_intent=swing_upbeat`.
- Reused the existing V2 render timing contract instead of writing literal `0.666...` into pattern candidates.
- Kept Jazz Ballad global timing profile unchanged (`feel=straight`) and scoped the swing-upbeat intent only to the affected Ballad `1&` soft-mark / retouch events.
- No notes, voicing texture, expression values, pedal behavior, gesture logic, API behavior, or Agent/LLM code changed.


## v2_5_5 — Jazz Ballad Two-Beat 1& Pattern Patch

- Corrected Jazz Ballad two-beat piano soft-mark candidates from region-start + beat 2 to region-start + 1&.
- Updated both `ballad_phrase_two_chord_soft_marks` and the temporary two-beat fallback retouch so the second touch is local beat `0.5`, not `1.0`.
- Kept the change inside the existing pitchless pattern/phrase metadata boundary: no V1 code migration, no concrete notes, no voicing texture binding, no expression/pedal ownership changes, and no Agent/LLM logic changes.
- Added a focused regression test to guard the two-beat `1 + 1&` Ballad cell.


## v2_5_4 — Held Foundation Partial Reattack Realization

- Implemented V2-native Jazz Ballad partial reattack realization without migrating V1 code.
- `INNER_MOVEMENT` now projects only requested inner/color voices instead of falling back to a full voicing hit.
- Expression duration clamp treats inner movement as non-interrupting so the warm anchor can sustain through motion.
- Harmonic realization trims only re-struck motion voices from the previous anchor; foundation/common tones remain held.
- Added focused regression tests and docs for the boundary.
- Agent/LLM workflow logic remains unchanged; only version/contract labels were synchronized for package consistency.

## v2_5_3 — Jazz Ballad Phrase Intent Foundation

- Extended existing `styles/jazz_ballad/comping_patterns.py` instead of creating or migrating a V1-style phrase engine.
- Added V2-native Jazz Ballad phrase metadata for `warm_pad`, `breath_answer`, `two_chord_soft_marks`, and context-gated `major_251_stable_cadence`.
- Allowed phrase candidates to request approved pitchless `inner_movement` gestures while preserving boundaries: no notes, source degrees, voicing textures, final expression values, pedal decisions, or MIDI repair behavior in the pattern layer.
- Reused the existing `core/harmony/harmonic_context.py` classifier for the conservative `major_ii_v_i` gate.
- Kept deterministic no-rng Ballad selection anchored on warm pad until held-foundation partial reattack is implemented.
- Agent/LLM workflow logic remains unchanged; only version/contract labels were synchronized for package consistency.

## v2_5_2 — Jazz Ballad Gesture Contract Foundation

- Extended existing `styles/jazz_ballad/gesture_policy.py` instead of creating a new V1-style phrase/runtime subsystem.
- Opened Jazz Ballad style-approved pitchless gesture kinds to `simultaneous_onset`, `inner_movement`, and `rolled_onset`.
- Added V2-native helper constructors and validation for Ballad inner movement / rolled cadence requests. Validation rejects V1 texture metadata, concrete MIDI/pitch data, expression values, pedal decisions, and legacy slot keys.
- Kept default Jazz Ballad audible runtime comping selection unchanged until phrase-intent and partial-reattack passes.
- Added targeted regression tests and a focused architecture note for the gesture contract.
- Agent/LLM workflow logic remains unchanged; only version/contract labels were synchronized for package consistency.


## v2_5_1 — V1 Musical Rules Absorption and V2-Native Mapping

- Performed a no-runtime-change engine-deepening audit of the V1 source as musical-rule reference material.
- Added `docs/V1_MUSICAL_RULES_TO_V2_NATIVE_MAPPING_V2_5_1.md` to translate V1 Ballad/Swing/Bossa instrument behavior into V2 Pattern / Gesture / Expression / Voicing / BassFoundation ownership.
- Clarified that V1 code, runtime mirrors, pattern-texture binding, MIDI repair paths, and sorted-note slot slicing must not be migrated.
- Reframed Jazz Ballad next steps around gesture and phrase semantics rather than more low-level `soft_retouch` cells.
- Updated engine development roadmap toward `v2_5_2_jazz_ballad_gesture_contract_foundation`.
- Agent/LLM behavior remains unchanged; only version metadata/contract labels were synchronized for package consistency.

## v2_5_0 — Engine Deepening Audit and Ballad Music Pass

- Performed the post-split engine audit before development and kept `jammate_engine` independent from `jammate_agent`.
- Deepened Jazz Ballad piano comping with weighted pitchless anchored light-retouch cells: downbeat + beat 3, downbeat + beat 3&, and downbeat + beat 1&.
- Added short-region Ballad adaptation for two-beat chord regions so multi-chord bars remain anchored without spilling events across the region boundary.
- Added `soft_retouch`, `soft_answer`, and `soft_whisper` expression profiles; final duration, velocity, touch, and pedal remain resolved by the core expression layer.
- Added targeted regression tests and regenerated standard-tune listening demos for the engine branch.
- Agent/LLM workflow logic is intentionally unchanged in this engine-deepening pass.

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

## v2_10_6 — HarmonyOS Agent Today Guidance Integration Handoff

- Integrated the `v2_10_5` HarmonyOS-facing Agent wrappers into repository frontend fixtures.
- Added ArkTS client methods and types for:
  - `POST /agent/harmonyos/routine-completion-record/execute`
  - `POST /agent/harmonyos/today-practice-guidance/preview`
- Added copyable smoke payloads and curl smoke steps for the completion-record → today-guidance loop.
- Updated the shared API contract with the product-facing response envelopes and safety boundaries.
- Runtime music generation behavior is unchanged; no Engine files were modified.

## v2_10_7 — HarmonyOS Agent Today Guidance Runtime Smoke

- Added a strict runtime smoke script for the two HarmonyOS-facing Agent practice-coach routes.
- The script starts from copyable smoke fixtures, injects a caller-provided SQLite DB path and unique idempotency key, calls the running FastAPI service with curl, and asserts the returned JSON fields.
- The strict runtime smoke validates completion-record persistence followed by today-guidance SQLite readback while intentionally skipping `/accompaniment/generate` and `/agent/playback/prepare`.
- Added `docs/INTEGRATION_HARMONYOS_AGENT_TODAY_GUIDANCE_RUNTIME_SMOKE_V2_10_7.md` and updated HarmonyOS smoke README / smoke pack metadata.
- Runtime music generation behavior is unchanged; no Engine files were modified.



## v2_10_23

- Agent: hotfixed Practice Coach plan revision intent routing for pending draft plans.
- No Engine generation changes.
