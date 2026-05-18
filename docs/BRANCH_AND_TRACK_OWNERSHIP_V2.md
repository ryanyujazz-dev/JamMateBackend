# Branch and Track Ownership V2

Current baseline: `v2_6_1`.

This document is the ownership contract for parallel Agent and Engine development. Its purpose is to prevent the two tracks from repeatedly editing the same files and creating avoidable merge conflicts.

---

## Core Rule

```text
Engine track makes the engine play better.
Agent track makes LLM / practice orchestration control and explain better.
Integration track reconciles shared contracts, versions, and public docs.
```

Feature branches must not perform integration work opportunistically. If a task needs deep changes on both tracks, split it or move it to an integration task.

---

## Branch Model

```text
main
├── feature/engine-deepening
├── feature/agent-workflow
└── integration/agent-engine-merge
```

### `feature/engine-deepening`

Owns accompaniment generation behavior, musical rules, style tuning, and listening demos.

### `feature/agent-workflow`

Owns Agent / LLM workflow surfaces, terminal chat, tool-preview, trace contracts, and HarmonyOS Agent fixtures.

### `integration/agent-engine-merge`

Owns shared files, version surfaces, cross-track API reconciliation, contract pack refresh, and final validation before merging to `main`.

---

## Engine-Owned Paths

Engine tasks may modify:

```text
src/jammate_engine/core/
src/jammate_engine/styles/
src/jammate_engine/generation/
src/jammate_engine/performance/
src/jammate_engine/harmony/
src/jammate_engine/midi/
src/jammate_engine/realization/
examples/scripts/generate_standard_tune_v2_examples_demos.py
tests/test_v2_5_*.py
tests/test_*engine*.py
```

Engine tasks may also update engine-only docs:

```text
docs/DEVELOPMENT_TASK_PLAN_ENGINE_V2.md
docs/CHANGELOG_ENGINE.md
docs/GENERATION_RULES_SUMMARY_V2.md
docs/STYLE_RULE_BASELINE_V2.md
docs/STYLE_TUNING_ENTRY_POINT_V2.md
```

Engine tasks must not modify:

```text
src/jammate_agent/
src/jammate_api/routes/agent_routes.py
tools/*agent*
tools/*trace*
tools/*terminal*
frontend_fixtures/harmonyos/          # except integration tasks
docs/AGENT*.md                        # except integration tasks
```

---

## Agent-Owned Paths

Agent tasks may modify:

```text
src/jammate_agent/
src/jammate_api/routes/agent_routes.py
tools/*agent*
tools/*trace*
tools/*terminal*
tests/test_*agent*.py
tests/test_*trace*.py
tests/test_*tool*.py
demos/agent_fixtures/
```

Agent tasks may also update agent-only docs:

```text
docs/DEVELOPMENT_TASK_PLAN_AGENT_V2.md
docs/CHANGELOG_AGENT.md
docs/AGENT*.md
```

Agent tasks must not modify:

```text
src/jammate_engine/core/
src/jammate_engine/styles/
src/jammate_engine/generation/
src/jammate_engine/midi/
src/jammate_engine/realization/
docs/GENERATION_RULES_SUMMARY_V2.md
docs/STYLE_RULE_BASELINE_V2.md
examples/scripts/generate_standard_tune_v2_examples_demos.py
```

The Agent may use engine behavior only through `src/jammate_agent/adapters/`.

---

## Shared Files: Integration-Owned Only

These files are high-conflict and should normally be changed only in integration tasks:

```text
VERSION
pyproject.toml
README.md
agent.md
docs/ARCHITECTURE_V2.md
docs/API_CONTRACT_V2.md
docs/DEVELOPMENT_TASK_PLAN_V2.md
docs/CHANGELOG.md
frontend_fixtures/harmonyos/
```

Exception: a feature branch may edit a shared file only when the user explicitly asks for that branch to update the shared contract. The change must be called out in the delivery summary.

---

## API Contract Ownership

`/accompaniment/generate` belongs to the direct engine/HarmonyOS playback contract.

`/agent/*` belongs to the Agent workflow contract.

The shared envelope must stay compatible:

```json
{
  "ok": true,
  "asset": {
    "format": "midi_base64",
    "midi_base64": "...",
    "midi_path": "...",
    "cache_key": "..."
  },
  "debug_summary": {}
}
```

Agent routes may add Agent-specific preview/trace/tool fields, but must not replace the direct accompaniment response shape.

---

## Documentation Split

The stable index files should change rarely:

```text
docs/DEVELOPMENT_TASK_PLAN_V2.md     # index only
docs/CHANGELOG.md                    # integration-level chronological summary
```

Track-specific rolling history belongs here:

```text
docs/DEVELOPMENT_TASK_PLAN_ENGINE_V2.md
docs/DEVELOPMENT_TASK_PLAN_AGENT_V2.md
docs/CHANGELOG_ENGINE.md
docs/CHANGELOG_AGENT.md
```

---

## Conflict Resolution Policy

When conflicts happen:

1. Create or use `integration/agent-engine-merge`.
2. Classify every conflict as Engine-owned, Agent-owned, or shared.
3. Resolve Engine-owned code in favor of the Engine branch unless the Agent branch contains a required adapter compatibility fix.
4. Resolve Agent-owned code in favor of the Agent branch unless it violates engine independence.
5. Manually merge shared files; do not blindly use ours/theirs.
6. Run harness, targeted tests, and standard-tune demos before merging back to `main`.

---

## Required Validation for Integration Tasks

```bash
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python tools/check_development_harness.py
```

Then run targeted tests for both tracks and generate standard-tune demos if engine behavior may have changed.
