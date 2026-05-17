# JamMatePyEngineV2 Development Harness

Current version: `v2_3_16`.

This file is the compact instruction index for future development windows. README is the user-facing project overview; detailed implementation history belongs in `docs/`.

---

## Mandatory Architecture Boundary

```text
src/jammate_engine/   # Independent accompaniment generation kernel
src/jammate_agent/    # Sibling Agent / practice orchestration layer
src/jammate_api/      # FastAPI service assembly layer
```

Rules:

- `jammate_engine` must not import `jammate_agent`.
- `jammate_engine` must remain directly callable without LLM/Agent.
- `jammate_agent` may use `jammate_engine` only through provider/adapter boundaries.
- `jammate_api` may assemble direct engine routes and Agent routes.
- HarmonyOS local practice workflows must not require LLM.

---

## Core Pipeline Boundary

```text
Pattern       = horizontal pitchless rhythm / event layout
Anticipation  = pitchless event movement across chord-region boundaries
Expression    = duration, release, velocity, articulation, pedal intent
Voicing       = vertical pitch realization
MIDI          = final note / CC materialization
```

Patterns live in styles. Voicing and expression are core-level shared systems. Do not place Agent/practice orchestration inside `jammate_engine/core`.

---

## Two-Window Development Split

Use two branches/windows after this baseline:

```text
feature/agent-workflow
  Agent / Practice Agent / LLM context / tool loop / HarmonyOS API / contracts

feature/engine-deepening
  Engine / voicing / pattern / expression / style tuning / listening demos
```

If a task changes both Agent/API and engine generation deeply, stop and ask whether to split or which branch should own it.

---

## Required Reading Order

1. `README.md`
2. `agent.md`
3. `docs/DEVELOPMENT_HARNESS_V2.md`
4. `docs/ARCHITECTURE_V2.md`
5. `docs/API_CONTRACT_V2.md`
6. `docs/PIPELINE_V2.md`
7. `docs/SYSTEM_CONTRACTS_V2.md`
8. `docs/GENERATION_RULES_SUMMARY_V2.md`
9. `docs/STYLE_RULE_BASELINE_V2.md`
10. `docs/STYLE_TUNING_ENTRY_POINT_V2.md`
11. `docs/NEW_FILE_PLACEMENT_GUIDE_V2.md`
12. `docs/DEVELOPMENT_TASK_PLAN_V2.md`
13. `docs/FUTURE_IDEAS_BACKLOG_V2.md`

---

## Cleanup Before Every Delivery

Before packaging any engineering handoff:

- Remove `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `.DS_Store`, transient trace files, and temporary unpack/build folders.
- Do not package `.env`, `.venv`, API keys, local secrets, or Git metadata.
- Keep README focused on project identity, architecture, core functionality, and startup instructions.
- Put version-specific implementation notes in `docs/`, not as repeated README changelog blocks.
- Run at least `PYTHONPATH=src python -m compileall -q src tests tools examples/scripts`.
- Run targeted pytest or full pytest when dependencies are available.
- Preserve relevant small listening demos when the delivery changes music generation.

---

## Development Rules

- Do not output continuation development documents unless explicitly requested.
- Each engineering delivery should include or preserve a current standard-tune listening demo where relevant.
- Update docs with any rule/code behavior change; do not only change code.
- Capture non-immediate ideas in `docs/FUTURE_IDEAS_BACKLOG_V2.md`.
- Prefer existing modules/facades/resolvers before creating new files.

---

## Minimal File Split Principle

Do not create a new file/module/planner/recognizer before checking whether an existing file or domain package can naturally carry the change. New files must have a stable architectural reason, not merely aesthetic separation.

---

## Capability Reuse Before New Construction

Before adding a new capability, perform a reuse audit. Prefer an existing local implementation, adapter, facade, metadata extension, or shared resolver before building a new subsystem.

---

## Current Active Baseline

`v2_3_16_project_cleanup_and_readme_consolidation` is a cleanup baseline for starting parallel Agent and Engine development windows. Runtime music generation behavior is unchanged from `v2_3_15`.
