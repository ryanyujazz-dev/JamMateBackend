# v2_3_16 — Project Cleanup and README Consolidation

This pass prepares the repository as a clean baseline for two-window development.

## Scope

Runtime music generation behavior is unchanged from `v2_3_15`.

The pass focuses on:

- README consolidation into a project-facing overview.
- Agent harness cleanup and two-window branch guidance.
- Delivery hygiene rule: cleanup caches/temp artifacts before every package handoff.
- Version surface alignment to `v2_3_16`.
- Removal of transient cache/trace artifacts from the packaged project.

## README Policy

README should describe:

- Project identity.
- Core design理念.
- Directory architecture.
- Main capabilities.
- Public API overview.
- Startup and validation commands.
- Current development workflow.

README should not become a version-by-version changelog. Detailed implementation notes belong in `docs/`.

## Cleanup Policy

Before every future package handoff, remove:

```text
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.DS_Store
transient demos/agent_traces/
local temp unpack/build folders
.env / .venv / local secrets
```

Preserve small relevant MIDI listening demos when they are part of the engineering delivery.

## Next Development Split

```text
feature/agent-workflow
  Agent / Practice Agent / LLM Context / Tool Loop / HarmonyOS API / Contracts

feature/engine-deepening
  Engine / Voicing / Pattern / Expression / Style Tuning / Listening Demos
```
