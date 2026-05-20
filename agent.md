Current version: `v2_10_28`.

# JamMatePyEngineV2 Development Harness

This file is the active development harness for ChatGPT and Claude Code. It is intentionally compact. Long design notes, version history, and continuation details belong in `docs/`.

## Current Boundary Update

`v2_10_28` is an Agent / Integration hotfix: routine completion context persistence SQLite path validation now accepts the current resolved OS tempdir (`tempfile.gettempdir()`), matching the Practice Coach session-state guard and fixing macOS `/private/var/folders/...` pytest failures. No Engine generation logic changed.

## Required Reading Order

Before changing code, read:

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

## Mandatory Architecture Boundary

```text
src/jammate_engine/   # Independent accompaniment generation kernel
src/jammate_agent/    # Sibling Agent / practice orchestration layer
src/jammate_api/      # HTTP/API facade and integration boundary
```

Rules:

- Engine code must not import Agent code.
- Agent code may use Engine only through explicit adapter boundaries.
- HarmonyOS-facing APIs must remain black-box product contracts.
- Frontend must not receive or send SQLite paths, provider internals, or internal write gates.
- Practice Coach must not auto-start Routine, call Engine, create MIDI, start playback, or write HarmonyOS local state.

## Track Ownership and Branch Split

Shared integration files should be changed only when the task is explicitly integration-facing:

```text
README.md
agent.md
VERSION
pyproject.toml
docs/ARCHITECTURE_V2.md
docs/API_CONTRACT_V2.md
docs/DEVELOPMENT_TASK_PLAN_V2.md
docs/CHANGELOG.md
frontend_fixtures/harmonyos/
```

Engine-only work should stay in Engine-owned docs/code. Agent-only work should stay in Agent-owned docs/code. Avoid cross-track edits unless the task requires them.

## Minimal File Split Principle

Do not create a new file/module/planner unless there is a clear long-term boundary. First inspect existing code for reusable capability. Prefer extending the closest responsible file when the responsibility is already clear. Do not split tiny features across many files to look architectural.

## Cleanup Before Every Delivery

Before delivering:

1. Remove dead or superseded code.
2. Avoid duplicate logic paths.
3. Keep docs aligned with actual behavior.
4. Run focused tests plus relevant regression tests.
5. Run `PYTHONPATH=src python tools/check_development_harness.py`.
6. State what changed, what was tested, and the next recommended task.

## Artifact / Demo Discipline

- For Engine music work, provide standard-tune listening demos when relevant.
- For Agent / Integration work, provide fixtures, curl smoke, API contract notes, and true-device feedback expectations.
- Do not output continuation documents unless explicitly requested.
