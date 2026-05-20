Current version: `v2_10_25`.

## v2_10_25 Agent / Integration Boundary Update

Practice Coach unified endpoint now returns a compact `deviceFeedbackTracePack` for HarmonyOS true-device feedback. The pack is a debugging/reporting envelope only; it does not change user-facing behavior. Product requests remain black-box and must not include `dbPath`, `sqliteDbPath`, `providerResult`, or `llmActionDecisionResult`.


## v2_10_24 Agent / Integration Boundary Update

Practice Coach adds a plan-revision E2E smoke pack for the one-session proposal → revision → confirmation flow. Production requests remain black-box; no Engine generation logic changed.

Practice Coach SQLite state-store path guard now accepts the resolved OS tempdir root (`tempfile.gettempdir()`), fixing macOS `/private/var/folders/...` pytest failures while preserving unsafe-path rejection. No Engine generation logic changed.

Current version: `v2_10_21`.

## v2_10_21 Agent / Integration Boundary Update

Practice Coach now includes LLM response repair and schema hardening for `POST /agent/harmonyos/practice-coach-session/message/execute`.

The backend may repair Markdown-fenced JSON, nested action wrappers, responseType aliases, and common field aliases. It must reject unsafe payload keys and use deterministic fallback when validation fails. This does not change Engine generation logic and still does not start Routine, call Engine, generate MIDI, or play anything.

Current version: `v2_10_21`.

## v2_10_21 Agent / Integration Boundary Update

Practice Coach now has an opt-in guarded smoke for real LLM provider execution through `POST /agent/harmonyos/practice-coach-session/message/execute`. The frontend request remains product-shaped and must not include `llmActionDecisionResult`, `providerResult`, `dbPath`, or internal write gates. Provider configuration belongs to the FastAPI server environment. The route still never starts Routine, calls Engine, creates MIDI, starts playback, or writes HarmonyOS local state.

# JamMatePyEngineV2 Development Harness

Current version: `v2_10_19`.


## v2_10_19 Agent / Integration Boundary Update

Practice Coach frontend integration now has copy-friendly ArkTS contract fixtures for the unified endpoint `POST /agent/harmonyos/practice-coach-session/message/execute`: `PracticeCoachTypes.ets`, `PracticeCoachStateMapper.ets`, and `JamMateApiClient.executePracticeCoachMessage(request)`. Production ArkTS request types must not include backend DB path fields, internal write gates, provider test hooks, or `llmActionDecisionResult`. The latter remains smoke-only in `smoke_llm_action_*` fixtures.

Frontend rendering should be driven by `data.responseType` and `nextClientActions`; `safeToAutostartRoutine` must remain false. Even when a routine card is ready, the user must explicitly tap the frontend start button.

This file is the active development harness for ChatGPT and Claude Code. It is intentionally short and hard. README is the project overview. Historical implementation notes belong in `docs/CHANGELOG.md` or focused docs.

---

## 0. Required Reading Order

Before any new development window changes code, read:

1. `README.md`
2. `agent.md`
3. `docs/ARCHITECTURE_V2.md`
4. `docs/API_CONTRACT_V2.md`
5. `docs/DEVELOPMENT_TASK_PLAN_V2.md`
6. `docs/BRANCH_AND_TRACK_OWNERSHIP_V2.md`
7. For engine work: `docs/DEVELOPMENT_TASK_PLAN_ENGINE_V2.md`, `docs/PIPELINE_V2.md`, `docs/GENERATION_RULES_SUMMARY_V2.md`, `docs/STYLE_RULE_BASELINE_V2.md`, `docs/STYLE_TUNING_ENTRY_POINT_V2.md`
8. For agent work: `docs/DEVELOPMENT_TASK_PLAN_AGENT_V2.md`
9. For placement decisions: `docs/NEW_FILE_PLACEMENT_GUIDE_V2.md`
10. For historical context only: `docs/CHANGELOG.md`

---

## 1. Mandatory Architecture Boundary

```text
src/jammate_engine/   # Independent accompaniment generation kernel
src/jammate_agent/    # Sibling Agent / practice orchestration layer
src/jammate_api/      # FastAPI service assembly layer
```

Rules:

- `jammate_engine` must not import `jammate_agent`.
- `jammate_engine` must remain directly callable without LLM/Agent.
- `jammate_agent` may import/use `jammate_engine` only inside `src/jammate_agent/adapters/`.
- `jammate_api` may assemble direct engine routes and Agent routes.
- HarmonyOS local practice workflows must not require LLM.

---

## 2. Core Music Pipeline Boundary

```text
Pattern       = horizontal pitchless rhythm / event layout
Anticipation  = pitchless event movement across chord-region boundaries
Expression    = duration, release, velocity, articulation, pedal intent
Voicing       = vertical pitch realization
MIDI          = final note / CC materialization
```

Patterns live in styles. Voicing and expression are core-level shared systems. Do not place Agent/practice orchestration inside `jammate_engine/core`.

---

## 3. Track Ownership and Branch Split

```text
feature/engine-deepening  # musical engine only
feature/agent-workflow    # Agent / LLM / terminal / trace only
integration/agent-engine-merge  # shared files, versions, API/docs reconciliation
```

Hard owner rule: Engine tasks must not edit `src/jammate_agent/`; Agent tasks must not edit `src/jammate_engine/core/`, `src/jammate_engine/styles/`, generation, MIDI, or realization logic. Shared files such as `VERSION`, `pyproject.toml`, `README.md`, `agent.md`, `docs/ARCHITECTURE_V2.md`, `docs/API_CONTRACT_V2.md`, `docs/DEVELOPMENT_TASK_PLAN_V2.md`, `docs/CHANGELOG.md`, and `frontend_fixtures/harmonyos/` belong to integration tasks unless explicitly requested. See `docs/BRANCH_AND_TRACK_OWNERSHIP_V2.md`.

---

## 4. Capability Reuse Before New Construction

Before building a new capability, perform a reuse audit. Prefer an existing local implementation, adapter, facade, metadata extension, shared resolver, or adjacent owner file before creating a new subsystem.

Minimum reuse-audit checklist:

- Is there an existing local implementation that can be generalized?
- Is there an adapter/facade boundary that should own this?
- Can metadata or policy extension solve it without a new module?
- Is there an existing core owner, for example `core/harmony/harmonic_context.py`, that should be extended instead of creating a new recognizer?

---

## 5. Minimal File Split Principle

Do not create a new file/module/planner/recognizer before checking whether an existing file or domain package can naturally carry the change. New files must have a stable architectural reason, not merely aesthetic separation.

---

## 6. Documentation and Changelog Rules

- README = project identity, core design理念, directory architecture, core functionality, startup / validation commands.
- `agent.md` = hard development harness only.
- `docs/CHANGELOG.md` = integration-level chronological version history; track rolling history goes to `docs/CHANGELOG_ENGINE.md` and `docs/CHANGELOG_AGENT.md`.
- Focused architecture/API/rule docs remain in `docs/`.
- Do not put rolling version logs back into README.
- Do not output continuation development documents unless explicitly requested.
- Capture non-immediate ideas in the Future Ideas Backlog: `docs/FUTURE_IDEAS_BACKLOG_V2.md`.
- If generation rules change, update `docs/GENERATION_RULES_SUMMARY_V2.md`. Engine/Agent rolling plans live in their split task-plan docs, not the main index.

---

## 7. Cleanup Before Every Delivery

Before packaging any engineering handoff:

```bash
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python tools/check_development_harness.py
```

Also run targeted pytest or full pytest when dependencies are available.

Remove before zip:

```text
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.DS_Store
demos/agent_traces/
temporary unpack/build folders
.env
.venv
local secrets
.git
```

Preserve relevant small listening demos when the delivery changes music generation or when the package is used as a current baseline.

---

## 8. Current Active Baseline

Current integration baseline: `v2_10_25`. Practice Coach unified endpoint returns `deviceFeedbackTracePack` for HarmonyOS device feedback. This is diagnostic only; product requests remain black-box and must not include internal DB/provider fields.

Strict boundaries remain active: Engine generation stays Engine-owned; Agent practice orchestration stays Agent-owned; Shared files are integration tasks per `BRANCH_AND_TRACK_OWNERSHIP_V2.md`.
