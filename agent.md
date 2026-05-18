# JamMatePyEngineV2 Development Harness

Current version: `v2_4_13`.

This file is the active development harness for ChatGPT and Claude Code. It is intentionally short and hard. README is the project overview. Historical implementation notes belong in `docs/CHANGELOG.md` or focused docs.

---

## 0. Required Reading Order

Before any new development window changes code, read:

1. `README.md`
2. `agent.md`
3. `docs/ARCHITECTURE_V2.md`
4. `docs/API_CONTRACT_V2.md`
5. `docs/DEVELOPMENT_TASK_PLAN_V2.md`
6. For engine work: `docs/PIPELINE_V2.md`, `docs/GENERATION_RULES_SUMMARY_V2.md`, `docs/STYLE_RULE_BASELINE_V2.md`, `docs/STYLE_TUNING_ENTRY_POINT_V2.md`
7. For placement decisions: `docs/NEW_FILE_PLACEMENT_GUIDE_V2.md`
8. For historical context only: `docs/CHANGELOG.md`

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

## 3. Two-Window Development Split

```text
feature/agent-workflow
  Agent / Practice Agent / LLM context / tool loop / HarmonyOS API / contracts

feature/engine-deepening
  Engine / voicing / pattern / expression / style tuning / listening demos
```

If a task changes both Agent/API and engine generation deeply, stop and ask whether to split the work or which branch should own it.

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
- `docs/CHANGELOG.md` = chronological version history.
- Focused architecture/API/rule docs remain in `docs/`.
- Do not put rolling version logs back into README.
- Do not output continuation development documents unless explicitly requested.
- Capture non-immediate ideas in the Future Ideas Backlog: `docs/FUTURE_IDEAS_BACKLOG_V2.md`.
- If generation rules change, update `docs/GENERATION_RULES_SUMMARY_V2.md`.

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

`v2_4_13_agent_tool_call_preview_trace_contract` is the active `feature/agent-workflow` baseline. It keeps terminal chat, local LLM setup/doctor/config-path, explicit `--trace-dir` JSON trace export, validation-only `/tool-preview`, versioned Trace API list/detail contracts, read-only trace viewer CLI, terminal context/profile/session controls, and JSON-only extraction of candidate tool calls from successful terminal LLM replies. It adds a stable tool-call preview trace contract so the LLM response -> candidate extraction -> preview validation -> execution guard chain is replayable. Extracted candidates are sent through the same preview contract and never execute tools, dispatch workflows, call adapters, or call `jammate_engine`. API keys must remain local secrets and must not appear in status, trace, docs, git, or zip packages. HarmonyOS `/accompaniment/generate` inline leadsheet behavior remains the direct playback contract. Runtime music generation behavior is unchanged from `v2_3_17`.
