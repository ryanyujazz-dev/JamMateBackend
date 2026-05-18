# Development Harness V2

Current version: `v2_6_1`.

This document expands the root `agent.md` harness. The root file is the active short checklist; this file explains the same rules for future maintainers.

---

## Purpose

The harness exists to constrain development behavior, not runtime behavior. It should be short, hard, and checkable.

It must help ChatGPT / Claude Code avoid:

- mixing Agent logic into the engine;
- creating unnecessary files or mini-frameworks;
- leaving cache/traces/secrets in delivery packages;
- turning README into a version changelog;
- changing code without updating rule/API/architecture docs.

---

## Mandatory Architecture Boundary

```text
src/jammate_engine/   # 独立伴奏生成内核，不依赖 Agent / LLM
src/jammate_agent/    # Agent / Practice orchestration，同级层
src/jammate_api/      # FastAPI 装配层，连接直接引擎路径与 Agent 路径
```

Hard rules:

- `jammate_engine` must not import `jammate_agent`.
- `jammate_agent` may use `jammate_engine` only through `src/jammate_agent/adapters/`.
- `jammate_api` may assemble both systems.
- Direct accompaniment generation remains available without LLM.
- HarmonyOS local practice tasks/timers/reviews must not require LLM.

---

## Current Project Architecture Tree

```text
CURRENT_PROJECT_ARCHITECTURE_TREE
src/jammate_engine/
  api/                         # API 边界：version / schemas helpers
  core/                        # 通用音乐核心，不放 Agent，不放风格库
    anticipation/              # pitchless timeline anticipation
    expression/                # duration / velocity / articulation / pedal intent
    form/                      # 曲式展开
    gestures/                  # gesture contracts
    harmony/                   # chord parser/material/scale/harmonic_context
    leadsheet/                 # leadsheet models/parser/normalization
    pattern_runtime/           # pitchless pattern runtime
    roles/                     # ensemble/domain role context
    timeline/                  # chord-region timeline
    voicing/                   # source/orientation/texture/projection/selection
  generation/                  # domain generators，例如 bass_foundation/
  realization/                 # plans/gestures -> NoteEvent
  midi/                        # MIDI writer / render_pipeline / timing policy
  runtime/                     # generate_accompaniment public runtime entry
  styles/                      # style policies + pitchless vocabularies
    medium_swing/
    bossa_nova/
    jazz_ballad/
  vocabulary/                  # melodic foreground / future solo vocabulary

src/jammate_agent/
  core/                        # workflow, context, runloop, trace, contracts
  capabilities/                # practice / accompaniment / charts
  adapters/                    # engine/chart provider boundaries

src/jammate_api/
  routes/                      # health / accompaniment / agent / practice
  schemas.py                   # API request compatibility layer
  app.py                       # service assembly
```

---

## Core Pipeline Boundary

```text
Pattern       = horizontal pitchless rhythm / event layout
Anticipation  = pitchless event movement across chord-region boundaries
Expression    = duration, release, velocity, articulation, pedal intent
Voicing       = vertical pitch realization
MIDI          = final note / CC materialization
```

Patterns live in `styles/`. Voicing and expression are core-level shared systems. Agent/practice orchestration stays out of `jammate_engine/core`.

---

## Track Ownership and Branch Split

```text
feature/engine-deepening
  Engine / voicing / pattern / expression / style tuning / demos

feature/agent-workflow
  Agent / LLM context / tool loop / terminal chat / traces / contracts

integration/agent-engine-merge
  shared files / version surfaces / API-doc reconciliation / fixture refresh
```

Engine tasks must not edit Agent-owned runtime. Agent tasks must not edit engine generation/style/core runtime. Shared files are integration-owned by default. The authoritative owner-path list is `docs/BRANCH_AND_TRACK_OWNERSHIP_V2.md`.

---

## Capability Reuse Before New Construction

Before building a new capability, perform a reuse audit. Check:

- existing local implementation;
- adapter boundary;
- facade boundary;
- metadata extension;
- policy extension;
- adjacent owner file;
- existing core owner such as `core/harmony/harmonic_context.py`.

Do not create a new subsystem when a small extension to an existing owner is clearer.

---

## Minimal File Split Principle

Do not split one logical task into many files unless there is a stable architecture reason. Prefer existing owners or one new file with a clear responsibility.

---

## Generation Rule Documentation Principle

When generation behavior changes, update `docs/GENERATION_RULES_SUMMARY_V2.md` and relevant style docs. Important categories include:

- Pattern rules;
- Voicing rules;
- Expression rules;
- Timing rules;
- BassFoundation / Medium Swing rules;
- Bossa and Ballad style rules.

---

## Changelog Split Rule

- README is not a changelog.
- `agent.md` is not a changelog.
- Track rolling history belongs in `docs/CHANGELOG_ENGINE.md` and `docs/CHANGELOG_AGENT.md`.
- Integration-level chronological version history belongs in `docs/CHANGELOG.md`.
- Focused implementation docs can remain in `docs/` when they are still useful.

---

## Split Task Plan Rule

`docs/DEVELOPMENT_TASK_PLAN_V2.md` is the stable index. Engine rolling tasks go in `docs/DEVELOPMENT_TASK_PLAN_ENGINE_V2.md`; Agent rolling tasks go in `docs/DEVELOPMENT_TASK_PLAN_AGENT_V2.md`. Do not update the main plan file from ordinary feature branches.

## Delivery Checklist

Before any zip delivery:

```bash
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python tools/check_development_harness.py
```

Then run targeted pytest for the changed area.

Remove:

```text
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.DS_Store
demos/agent_traces/
.env
.venv
.git
temporary unpack/build folders
```

Do not claim full test success if only targeted tests were run. State exactly what passed.

## Future Ideas Backlog

Non-immediate ideas belong in `docs/FUTURE_IDEAS_BACKLOG_V2.md`; do not expand active scope during a focused delivery.


## v2_6_1 Track Ownership Rule

Engine-deepening and Agent-workflow changes must be merged by owner boundary. Engine code owns `jammate_engine`, style rules, gestures, expression, voicing, and generation behavior. Agent code owns `jammate_agent`, terminal chat, provider-boundary, tool-preview, and trace contracts. Shared API, frontend fixtures, versions, and public docs require integration-task reconciliation; do not blanket overwrite shared files. See `docs/BRANCH_AND_TRACK_OWNERSHIP_V2.md`.

## Agent Trace API / Viewer Rule

Agent trace APIs and the read-only trace viewer CLI are Agent-workflow owned debugging surfaces. They may read `JsonTraceStore` summaries/details, but must not call the LLM provider, execute tools, dispatch deterministic workflows, or invoke the accompaniment engine. Keep `jammate_agent.cli.trace_viewer` / `jammate-agent-traces` documented whenever shared README or architecture docs are consolidated during integration merges.
