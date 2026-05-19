# JamMatePyEngineV2 Development Harness

Current version: `v2_8_24`.

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

`v2_8_24_integration_agent_engine_merge` is the active integration baseline for `integration/agent-engine-merge`. It merges Engine Track `v2_6_30_engine_ballad_spread_1plus4_lower_foundation_calibration` and Agent Track `v2_8_23_agent_v2_8_phase_cleanup_regression_handoff`.

Strict boundaries remain active:

- Engine runtime/style/pattern/gesture/expression/voicing/realization behavior stays owned by the Engine Track.
- Agent terminal, LLM/provider boundary, trace, tool-preview, context, and guidance contracts stay owned by the Agent Track; the `v2_4_13_agent_tool_call_preview_trace_contract` tool-call preview trace contract remains preserved.
- Shared files, frontend fixtures, version surfaces, and public API docs are integration-task territory.
- Do not migrate V1 code, create V1-style runtime mirrors, bind patterns to voicing textures, or place Agent practice orchestration inside engine generation runtime.
- Do not let `jammate_engine` import `jammate_agent`; do not let `jammate_agent` import `jammate_engine` except through adapters.

The direct HarmonyOS accompaniment response shape remains protected: `{ ok, asset: { format, midi_base64, midi_path, cache_key }, debug_summary }`.
