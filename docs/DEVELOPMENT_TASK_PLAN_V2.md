## v2_10_28 — Context persistence SQLite path guard macOS tempdir hotfix

Status: completed.

Goal: fix the routine completion context persistence route on macOS pytest tempdirs while preserving the existing safety allowlist.

Boundary:
- Agent / Integration only.
- Do not modify Engine generation logic.

Validation:
- compileall
- v2_10_28 focused tests
- v2_10_26 / v2_10_27 regression tests that use routine completion history persistence
- v2_10 full regression
- v2_8 + v2_9 + v2_10 regression
- development harness

## v2_10_27 — Practice Coach HarmonyOS UI integration feedback fit

Agent / Integration 线完成 Practice Coach 前端 UI action hint 契约：`data.frontendUiAction` 帮助 HarmonyOS 渲染多轮对话、计划草案替换、Routine 卡片、完成记录摘要和下一次历史读取。Engine 线无改动。

## v2_10_26 — Practice Coach routine-card completion loop smoke

Integration/Agent task only. Adds the smoke and docs needed to validate the end-to-end product loop after `routine_card_ready`: HarmonyOS submits a completion record, and the next Practice Coach turn reads that completion history through the context builder.

## v2_10_25 — Practice Coach device feedback trace pack

- Added `deviceFeedbackTracePack` to unified Practice Coach responses at `data.deviceFeedbackTracePack` and `debug.deviceFeedbackTracePack`.
- The pack summarizes request, responseType, decision source/fallback, schema repair, state digests, plan/card artifacts, SQLite IO, and safety flags.
- Added HarmonyOS smoke fixture and curl script for verifying the trace pack.
- Updated frontend type fixtures with `PracticeCoachDeviceFeedbackTracePack`.
- Preserved black-box frontend contract and Agent/Engine boundaries: no Engine call, no MIDI/playback generation, no Routine auto-start, and no HarmonyOS local-state write.


## v2_10_24 — Practice Coach plan revision E2E smoke

- Validate the full one-session plan adjustment flow for HarmonyOS frontend integration.
- Keep `existing_draft_plan_waiting_for_confirmation` as a fallback only; clear revision requests must continue returning `practice_plan_revision`.
- Provide a curl smoke and product-shaped sequence fixture so frontend can retest without inventing workaround sessions or client-side plan rewriting.

Recommended next task:

```text
v2_10_25_agent_practice_coach_device_feedback_trace_pack
```

Purpose: collect real device/provider feedback fields into a compact debug trace once frontend reruns the revision E2E smoke.

## v2_10_22_agent_practice_coach_sqlite_path_guard_macos_tempdir_hotfix

Integration/Agent hotfix: allow Practice Coach SQLite state-store paths under the resolved OS tempdir root (`tempfile.gettempdir()`), fixing macOS pytest `/private/var/folders/...` failures while keeping the DB path safety guard strict.

## v2_10_21_agent_practice_coach_live_llm_response_repair_and_schema_hardening

Integration/Agent task: add response repair and schema hardening for Practice Coach LLM action decisions. This prepares the unified endpoint for real provider/device feedback while preserving deterministic fallback and safety.

## v2_10_20_agent_practice_coach_real_llm_provider_execution_guarded_smoke

Integration/Agent task: guarded real LLM provider smoke for the unified Practice Coach endpoint. The product request remains black-box HarmonyOS friendly; provider configuration lives on the FastAPI server. No Engine generation files are modified.

Recommended next task: `v2_10_21_agent_practice_coach_live_llm_response_repair_and_schema_hardening`.

## v2_10_19_agent_practice_coach_frontend_contract_types_and_state_mapper

Integration/Agent line completed: added copy-friendly HarmonyOS Practice Coach types, state mapper, and API client method for the unified `message/execute` endpoint. Engine generation logic remains untouched.

## v2_10_18 — Practice Coach Frontend LLM Action Fixture Smoke

Status: completed.

This Integration/Agent pass prepares HarmonyOS frontend/device smoke for the unified Practice Coach Session endpoint. It keeps the v2_10_17 LLM-action-decision-first architecture intact and gives frontend Claude copyable fixtures for responseType rendering.

Boundary: no Engine music generation changes. No accompaniment generation, MIDI generation, playback, style, voicing, bass, piano, or drum logic was modified.

Recommended next task: `v2_10_19_agent_practice_coach_frontend_contract_types_and_state_mapper`.

## v2_10_17 — Practice Coach LLM Action Decision Contract

Integration / Agent line update: the unified Practice Coach endpoint is now LLM-action-decision-first, with deterministic fallback. This keeps the frontend contract stable while moving the product logic toward the intended Agent behavior: the LLM decides whether to ask a clarifying question, request a profile sheet, propose/revise a plan, or return a routine card after confirmation. No Engine music generation logic was changed.

## v2_10_16 — Practice Coach Unified Message/Action Router

Integration/Agent update: added unified `practice-coach-session/message/execute` route so HarmonyOS can send one user message and render by `responseType` / `nextClientActions`.

Recommended next task: `v2_10_17_agent_practice_coach_unified_frontend_fixture_and_smoke`.

## v2_10_15 — Practice Coach Profile Sheet Intent Contract

Integration/Agent milestone for structured profile capture in the Practice Coach Session flow. Added `/agent/harmonyos/practice-coach-session/profile-sheet/execute`, which returns `request_profile_sheet` / `sheetIntent` for HarmonyOS native bindSheet rendering or records submitted `profileFormResult` into backend session state. This preserves black-box product boundaries and does not touch Engine generation.

## v2_10_14 — Practice Coach Plan Confirmation to Routine Card Contract

- Agent / Integration boundary update only.
- Added `POST /agent/harmonyos/practice-coach-session/routine-card/execute`.
- Converts a confirmed Practice Coach `draft_plan` into frontend-presentable `routineCardPayload`.
- Keeps Routine start client-owned: backend returns card data but does not start Routine, call Engine, create MIDI, start playback, write HarmonyOS local state, or call an LLM.
- Recommended next task: `v2_10_15_agent_practice_coach_profile_sheet_intent_contract`.

## v2_10_13 — Practice Coach Session Plan Proposal Contract

Integration/Agent step for the Practice Coach Session product loop. After missing info is collected, the backend can now return a structured `practice_plan_proposal` and persist it as `draft_plan`, while still requiring explicit user confirmation before any Routine card is created.

Endpoint:

```text
POST /agent/harmonyos/practice-coach-session/plan-proposal/execute
```

Boundary: no Engine changes; no LLM call; no Routine start.

## v2_10_12 — Practice Coach Session Conversation State Store

- Agent/Integration milestone for user-facing Practice Coach Session continuity.
- New route: `POST /agent/harmonyos/practice-coach-session/message-state/execute`.
- Stores and restores same-session missing-info state so `今日练什么` does not end after one preview response.
- Boundary: backend SQLite session-state write only; no LLM call, no Routine start, no Engine call, no MIDI/playback, no HarmonyOS local write.

# JamMate Development Task Plan V2

Current baseline: `v2_10_11`.

This file is now the stable integration index. To reduce Agent/Engine merge conflicts, rolling task plans are split:

```text
docs/DEVELOPMENT_TASK_PLAN_ENGINE_V2.md
docs/DEVELOPMENT_TASK_PLAN_AGENT_V2.md
```

Rules:

- Engine feature branches update only `DEVELOPMENT_TASK_PLAN_ENGINE_V2.md`.
- Agent feature branches update only `DEVELOPMENT_TASK_PLAN_AGENT_V2.md`.
- This main file is updated only by integration tasks or explicit user request.
- Track ownership is defined in `docs/BRANCH_AND_TRACK_OWNERSHIP_V2.md`.

## Current Recommended Next Tasks

```text
Engine: continue ballad SPREAD lower/upper gap and weight balance from v2_6_44
Agent: continue persistence implementation planning only after explicit approval
Integration: use v2_10_10 LLM payload trace to verify prompt/context, then fit UI state mapping from frontend feedback
```



## v2_10_10 Integration HarmonyOS Agent Today Guidance LLM Payload Trace

Status: completed.

Scope:

- Added `POST /agent/harmonyos/today-practice-guidance/llm-payload-trace` as a read-only debug endpoint.
- The endpoint accepts the same black-box `userMessage` product body as the normal HarmonyOS today-guidance route.
- It returns `data.llmRequestPreview` with `internalPromptMessages`, `chatCompletionsMessagesIfCalled`, `chatCompletionsRequestBodyPreview`, `assembledPracticeContext`, `outputSchema`, and `promptPolicy`.
- It explicitly performs no LLM/network call, no tool execution, no Routine start, no Engine adapter call, no MIDI creation, and no playback.
- It documents the role normalization from internal `system/developer/user/context` messages to OpenAI-compatible `system/user/assistant` messages.

Recommended next task:

```text
v2_10_11_agent_today_guidance_compact_history_enrichment_or_frontend_trace_review
```

Goal: decide whether stored Routine completion `items` and `notes` should be summarized into the compact LLM history context, after reviewing real trace payloads.

## v2_10_9 Integration HarmonyOS Agent Black-Box Runtime and Device Smoke

Status: completed.

Scope:

- Added product-contract smoke fixtures that match the frontend report body and do not expose backend DB paths or internal write gates.
- Added `frontend_fixtures/harmonyos/smoke/curl_agent_black_box_product_contract_smoke.sh` for local Mac and phone-to-Mac LAN smoke.
- Updated API contract, smoke README, smoke pack, changelog, and targeted tests.
- Kept Engine music generation unchanged.

Next recommended integration task:

```text
v2_10_10_integration_harmonyos_agent_guidance_ui_state_mapping_feedback_fit
```

Goal: use real HarmonyOS device feedback to tune UI-state mapping around `loading`, `success`, `empty-context`, `backend-error`, `network-error`, and `user-confirmation-required` without changing Engine behavior.


## v2_10_8 Integration Agent / Engine Merge

Current integrated baseline: `v2_10_8`.

Merged sources:

```text
Engine Track: v2_6_44_engine_ballad_spread_voicing_phase_summary_handoff
Agent Track:  v2_10_7_agent_harmonyos_today_guidance_runtime_smoke
```

Integration scope:

- Engine generation chain uses the Engine Track package through v2.6.44 (frozen Ballad SPREAD guardrails, lower-foundation calibration, safe extension frequency, phrase-state anchor policy).
- Agent / LLM / trace / tool-preview / context-guidance / persistence / HarmonyOS product routes use the Agent Track package through v2.10.7.
- Shared files reconciled here: `README.md`, `agent.md`, `VERSION`, `pyproject.toml`, `docs/ARCHITECTURE_V2.md`, `docs/API_CONTRACT_V2.md`, `docs/DEVELOPMENT_TASK_PLAN_V2.md`, `docs/CHANGELOG.md`, and `frontend_fixtures/harmonyos/`.
- No new Engine music rule or V1 code migration was added by this integration pass.

Next split after this integration package:

```text
Engine: continue ballad SPREAD lower/upper gap and weight balance from v2_6_44.
Agent: continue persistence implementation planning only after explicit approval.
Integration: only reconcile shared docs/API/fixtures/version when one track changes public contracts.
```


## v2_8_24 Integration Agent / Engine Merge

Integration scope:

- Added `frontend_fixtures/harmonyos/smoke/curl_agent_today_guidance_runtime_smoke.sh` for real FastAPI runtime validation of the two HarmonyOS Agent product routes.
- Updated HarmonyOS smoke README and smoke pack metadata with the strict runtime sequence.
- The strict smoke validates backend SQLite context write/readback without calling Engine generation or playback routes.
- Next recommended integration task: run the same strict smoke from a real HarmonyOS device against the Mac LAN IP and then wire the two calls into the app-side routine-end / today-guidance screens.

---


## v2_8_24 Integration Agent / Engine Merge

Current integrated baseline: `v2_8_24`.

Merged sources:

```text
Engine Track: v2_6_30_engine_ballad_spread_1plus4_lower_foundation_calibration
Agent Track:  v2_8_23_agent_v2_8_phase_cleanup_regression_handoff
```

Integration scope:

- Engine generation chain uses the Engine Track package.
- Agent / LLM / trace / tool-preview / context-guidance contract surfaces use the Agent Track package.
- Shared files reconciled here: `README.md`, `agent.md`, `VERSION`, `pyproject.toml`, `docs/ARCHITECTURE_V2.md`, `docs/API_CONTRACT_V2.md`, `docs/DEVELOPMENT_TASK_PLAN_V2.md`, `docs/CHANGELOG.md`, and `frontend_fixtures/harmonyos/`.
- No new Engine music rule, no new Agent feature, and no V1 code migration is part of this merge.

Next split after this integration package:

```text
Engine: continue voicing/listening work from v2_6_31 on feature/engine-deepening.
Agent: continue persistence implementation planning on feature/agent-workflow only after explicit approval.
Integration: only reconcile shared docs/API/fixtures/version when one track changes public contracts.
```


## v2_5_10 Agent / Engine Integration Merge

Current integrated baseline: `v2_5_10`. Agent workflow is merged through `v2_4_13_agent_tool_call_preview_trace_contract`; engine-deepening is merged through `v2_5_9_v1_instrument_rules_deep_audit_and_v2_native_mapping`. Resume engine work only after this package passes harness and smoke tests. Recommended next engine task: `v2_5_11_jazz_ballad_bass_anchor_path_policy`. Recommended Agent continuation should remain in Agent-owned modules and must not alter engine generation runtime.


Current baseline: `v2_5_9`.

`v2_5_9_v1_instrument_rules_deep_audit_and_v2_native_mapping` is a documentation-only engine planning baseline based on the audible `v2_5_8` Ballad swing-8 timing patch. It explicitly discards the earlier experimental Ballad brush-drums shortcut and records the required V1-to-V2 musical-rule mapping in `docs/V1_INSTRUMENT_RULES_DEEP_AUDIT_AND_V2_NATIVE_MAPPING_V2_5_9.md`.

---

## Immediate Branch Split

### Agent branch

```text
feature/agent-workflow
```

Scope:

- JamMate Agent workflow
- Practice Agent
- LLM context engineering
- bounded tool loop
- HarmonyOS API / contracts / fixtures
- trace/debug inspection

Suggested next task:

```text
v2_4_0_agent_llm_context_runtime_foundation
```

### Engine branch

```text
feature/engine-deepening
```

Scope:

- JamMatePyEngine music generation
- voicing
- pattern selection
- expression / touch / dynamics / pedal
- style tuning
- listening demos

Suggested next task:

```text
v2_5_10_jazz_ballad_bass_anchor_path_policy
```

---

## Engine Deepening Roadmap after v2_5_9

```text
v2_5_9_v1_instrument_rules_deep_audit_and_v2_native_mapping — completed, docs only
v2_5_10_jazz_ballad_bass_anchor_path_policy — next audible pass
v2_5_11_jazz_ballad_brush_semantic_policy — after bass, policy dimensions before hits
v2_5_12_jazz_ballad_251_color_families_gated — gated phrase/color families
v2_5_13_medium_swing_piano_phrase_feel_restoration — statement/answer and 4& rarity
v2_5_14_medium_swing_bass_classic_fill_branch_review — scene-gated classic fills
v2_5_15_bossa_identity_anticipation_articulation_review — core batida, A/B ratio, anticipation separation
v2_5_16_bossa_percussion_groove_identity_review — shaker/cross-stick/kick layers
```

Rule: V1 is a musical-rule reference only. Do not migrate V1 code, file structure, runtime mirrors, pattern-texture binding, or MIDI repair paths. Inner movement belongs to V2 gesture semantics, not ordinary pattern cells.

---

## v2_5_9 delivery result: V1 Instrument Rules Deep Audit and V2-Native Mapping

- Rebased official planning baseline on `v2_5_8`; the previous experimental Ballad brush-drums shortcut is not carried forward.
- Added `docs/V1_INSTRUMENT_RULES_DEEP_AUDIT_AND_V2_NATIVE_MAPPING_V2_5_9.md`.
- Audited V1 Jazz Ballad, Medium Swing, and Bossa Nova piano/bass/drums behavior.
- Mapped each absorbed musical rule to V2 owners: pattern, gesture, expression, voicing, bass foundation, percussion policy, fill policy, or harmony context.
- No generation code changed. No Agent/LLM logic changed.

Recommended next task:

```text
v2_5_10_jazz_ballad_bass_anchor_path_policy
```

---

## v2_5_2 delivery result: Jazz Ballad Gesture Contract Foundation

- Extended existing `styles/jazz_ballad/gesture_policy.py`; no new gesture subsystem was created.
- Opened only pitchless `inner_movement` and `rolled_onset` style-approved requests.
- Added helper constructors and validation that reject V1-style voicing texture metadata, concrete MIDI/pitch data, final duration/velocity/pedal data, and unknown legacy slot keys.
- Kept default Jazz Ballad runtime comping selection unchanged. The next pass should add phrase-intent candidates that may request these gestures without choosing notes or voicing textures.

## v2_5_3 delivery result: Jazz Ballad Phrase Intent Foundation

- Extended existing `styles/jazz_ballad/comping_patterns.py`; no V1-style phrase engine or new runtime path was created.
- Added phrase-intent metadata for `warm_pad`, `breath_answer`, `two_chord_soft_marks`, and context-gated `major_251_stable_cadence`.
- Phrase candidates may request approved pitchless gestures but still cannot choose notes, voicing textures, expression values, pedal, source degrees, or MIDI repair behavior.
- Reused `core/harmony/harmonic_context.py` for the conservative `major_ii_v_i` context gate instead of adding a new recognizer.
- Kept deterministic no-rng Ballad selection anchored on the warm pad until partial-reattack realization is implemented.

Recommended next task:

```text
v2_5_9_ballad_bass_anchor_path
```


## v2_5_4 delivery result: Held Foundation Partial Reattack Realization

- Updated Jazz Ballad inner-movement realization without migrating V1 code or adding a V1-style phrase engine.
- `INNER_MOVEMENT` now projects only the requested inner/color voice or group instead of appending all unselected voices.
- Expression next-event duration clamping ignores non-interrupting partial reattack gestures so warm anchors can hold through inner motion.
- Harmonic realization trims only the voices re-struck by the inner movement; foundation/common-tone notes remain sustained.
- Pattern, gesture, expression, voicing, and realization boundaries remain separate.

Recommended next task:

```text
v2_5_8_ballad_bass_anchor_path
```



## v2_5_8 delivery result: Jazz Ballad Default Swing-8 Anticipation Timing Patch

Corrected Jazz Ballad timing-feel ownership. The style timing profile now uses `feel=swing`, and Ballad anticipation now mirrors the swing-upbeat contract: logical `4&` remains at `.5` in the pitchless timeline, but the event carries `timing_intent=swing_upbeat`, `timing_grid=swing_triplet_upbeat`, and a performed lead-in of `1/3`. This does not move pattern events to literal `0.666...`, does not migrate V1 code, and does not change notes, voicing texture, expression values, pedal behavior, API behavior, or Agent/LLM logic. Recommended next task: `v2_5_9_ballad_bass_anchor_path`.

## v2_5_6 delivery result: Jazz Ballad Swing 1& Timing Patch

Corrected the previous Ballad `1&` patch so logical `0.5` is interpreted through the existing V2 swing-upbeat timing contract. The pattern layer still writes logical `.5`; the second `1&` touch now carries `timing_intent=swing_upbeat`, so render timing performs it at `2/3`. No notes, voicing texture, expression values, pedal behavior, gesture logic, API behavior, or Agent/LLM code changed. Recommended next task: `v2_5_7_ballad_bass_anchor_path`.

## v2_5_5 delivery result: Jazz Ballad Two-Beat 1& Pattern Patch

Corrected the Jazz Ballad two-beat piano soft-mark timing from local beat `1.0` to `0.5`, so the feel is beat 1 + beat 1& rather than beat 1 + beat 2. This did not change notes, voicing texture, expression values, pedal behavior, or Agent/LLM logic. Recommended next task: `v2_5_7_ballad_bass_anchor_path`.


## v2_10_8 Integration — HarmonyOS Agent Black-Box Contract Fit

Status: completed.

The merged backend now matches the HarmonyOS frontend report contract:

- `POST /agent/harmonyos/routine-completion-record/execute` accepts frontend product payloads without `dbPath` or `clientConfirmedRecordWrite`.
- `POST /agent/harmonyos/today-practice-guidance/preview` accepts `userMessage` and does not require frontend-supplied SQLite fields.
- Backend-owned context DB path comes from `JAMMATE_AGENT_CONTEXT_DB_PATH` or the local-dev default `/tmp/jammate_agent_harmonyos_context.sqlite3`.

Next: run real device LAN smoke against `http://192.168.1.16:8000` or the current Mac LAN IP, then map UI states from `{ok, code, message, data, debug, safety}`.


## v2_10_7 Integration HarmonyOS Agent Today Guidance Runtime Smoke

Status: completed. Runtime smoke script is available at `frontend_fixtures/harmonyos/smoke/curl_agent_today_guidance_runtime_smoke.sh`.


## v2_10_11 Integration / Agent Practice Coach Session Context Builder

- Current integration baseline adds the Practice Coach Session context-builder preview.
- New route: `POST /agent/harmonyos/practice-coach-session/context-builder-preview`.
- Purpose: inspect cache-friendly LLM messages and block digests before implementing full multi-turn Practice Coach conversation execution.
- Boundaries: no Engine change, no MIDI/playback, no Routine start, no HarmonyOS local-state write, no LLM/provider call.

Next integration/agent step:

```text
v2_10_12_agent_practice_coach_conversation_state_store
```


## v2_10_23 — Agent hotfix

Practice Coach 统一入口新增待确认草案下的调整意图路由修复。此任务属于 Agent / Integration 边界，不改 Engine 音乐生成逻辑。
