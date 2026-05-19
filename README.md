# JamMatePyEngineV2

JamMatePyEngineV2 is the Python backend foundation for JamMate. It currently contains three sibling systems:

```text
src/
  jammate_engine/   # Independent accompaniment generation kernel
  jammate_agent/    # Agent / practice orchestration layer
  jammate_api/      # FastAPI service assembly layer
```

Current package version: `v2_10_8`.

This repository is intentionally designed so the accompaniment engine can run without LLM/Agent. Agent and LLM workflows are enhancement paths, not required paths.

---

## Core Design Principles

### 1. Engine independence

`jammate_engine` is the independent music-generation kernel. It owns leadsheet expansion, style policies, pattern planning, anticipation, expression, voicing, realization, and MIDI export. It must not import `jammate_agent`.

HarmonyOS or any other client can directly call the engine through `/accompaniment/generate` when tune/style/tempo/chorus parameters are explicit.

### 2. Agent as orchestration, not engine internals

`jammate_agent` is a sibling orchestration layer. It can interpret practice intent, prepare immediate playback, resolve chart/material context, build practice plans, record session reviews, and call the engine through provider/adapters.

The Agent may use the engine only through an adapter boundary, not by embedding practice logic inside the engine.

### 3. API as assembly boundary

`jammate_api` exposes both routes:

```text
Direct path:
HarmonyOS -> /accompaniment/generate -> jammate_engine -> MIDI asset

Agent path:
HarmonyOS -> /agent/playback/prepare -> jammate_agent -> engine adapter -> jammate_engine -> MIDI asset
```

### 4. Local-first HarmonyOS practice module

The HarmonyOS practice UI should be able to run local practice tasks, routines, timers, reviews, history, and pending sync without LLM. Python backend services provide accompaniment generation, Agent orchestration, future LLM planning, and deeper analysis.

### 5. Pattern / anticipation / expression / voicing separation

The engine pipeline keeps musical responsibilities separate:

```text
Pattern       = horizontal pitchless rhythm / event layout
Anticipation  = pitchless event movement across chord-region boundaries
Expression    = duration, release, velocity, articulation, pedal intent
Voicing       = vertical pitch realization
MIDI          = final note / CC materialization
```

Patterns live in styles. Voicing and expression are core-level shared systems.

### 6. Branch / track ownership

Parallel development is split into Engine, Agent, and Integration tracks. Engine work owns musical generation behavior. Agent work owns orchestration, terminal chat, tool-preview, traces, and LLM/provider boundaries. Integration work owns shared version surfaces, public docs, frontend fixture refresh, and cross-track API reconciliation. See `docs/BRANCH_AND_TRACK_OWNERSHIP_V2.md`.

---

## Current Main Capabilities

### Accompaniment engine

- Reads V2 leadsheet-style examples from `examples/leadsheets/`.
- Generates accompaniment MIDI for standard-tune practice demos.
- Supports current core styles:
  - `medium_swing`
  - `bossa_nova`
  - `jazz_ballad`
- Exports MIDI assets and optional base64 payloads for API clients.
- Maintains voicing, expression, anticipation, style pattern, and pedal boundaries.

### JamMate Agent foundation

- Provides rule/workflow-based Agent routes before full LLM integration.
- Prepares immediate practice playback from natural-language-like user input.
- Creates practice plan and session review responses.
- Maintains trace logging for Agent steps.
- Exposes capability and contract manifests for HarmonyOS integration.

### HarmonyOS API / contract support

- Exposes direct accompaniment and Agent routes.
- Provides generated ArkTS contract files and frontend fixture packs.
- Keeps backend responses canonical `snake_case`.
- Provides HarmonyOS client-domain `camelCase` types and `CaseAdapter.ets` mapping.
- Provides smoke-test JSON/curl files for LAN testing from a phone to the Mac backend.

---

## Directory Architecture

```text
JamMatePyEngineV2/
  VERSION
  pyproject.toml
  README.md
  agent.md

  src/
    jammate_engine/
      api/                 # Engine-facing version/API helpers
      core/                # Shared harmony, performance, voicing, expression concepts
      generation/          # Runtime generation planning and musical generation packages
      midi/                # MIDI writing / rendering boundaries
      realization/         # Final event realization helpers
      runtime/             # Public engine runtime entry point
      styles/              # Style-specific pattern/policy packages
      utils/
      vocabulary/

    jammate_agent/
      core/                # Agent workflow, context, contracts, trace, guardrails
      capabilities/        # Practice/accompaniment/chart capabilities
      adapters/            # Boundaries to engine/chart providers

    jammate_api/
      app.py               # FastAPI app assembly
      schemas.py           # API request schema compatibility
      routes/              # Health, accompaniment, agent, practice routes

  examples/
    leadsheets/            # V2 leadsheet examples: standards and smoke fixtures
    scripts/               # Demo generation scripts

  frontend_fixtures/
    harmonyos/             # ArkTS types, API client sketch, fixtures, smoke pack

  docs/                    # Architecture, contracts, style rules, development harness
  tests/                   # Targeted regression and contract tests
  tools/                   # Demo/audit utilities
  demos/                   # Small generated MIDI listening/demo artifacts
```

---

## Public API Overview

### Health

```text
GET /health
```

### Direct accompaniment path

```text
POST /accompaniment/generate
```

Use this when the client already knows the tune/style/tempo/chorus settings.

Typical request:

```json
{
  "tune": "Blue Bossa",
  "style": "bossa_nova",
  "tempo": 120,
  "choruses": 1,
  "outputFormat": "midi_base64"
}
```

### Agent immediate playback path

```text
POST /agent/playback/prepare
```

Use this when the user asks in practice language, for example: “I want to practice Blue Bossa for 20 minutes.”

The backend prepares a MIDI asset and a playback instruction. Practice duration remains a HarmonyOS local timer responsibility; the returned asset may be looped until the target duration.

### Agent and contract helper routes

```text
POST /agent/practice/plan
POST /agent/session/review
GET  /agent/capabilities
GET  /agent/context/profiles
GET  /agent/contracts/arkts
GET  /agent/contracts/arkts/files
GET  /agent/contracts/frontend-pack
GET  /agent/contracts/smoke-pack
GET  /agent/traces
GET  /agent/traces/{trace_id}
```


### Agent terminal tooling

Terminal Agent chat:

```bash
PYTHONPATH=src python -m jammate_agent.cli.terminal_chat
jammate-agent-chat
```

Agent Trace Viewer CLI:

```bash
PYTHONPATH=src python -m jammate_agent.cli.trace_viewer --trace-dir demos/agent_traces list
PYTHONPATH=src python -m jammate_agent.cli.trace_viewer --trace-dir demos/agent_traces show <trace_id>
PYTHONPATH=src python -m jammate_agent.cli.trace_viewer spec
jammate-agent-traces --trace-dir demos/agent_traces list
jammate-agent-traces --trace-dir demos/agent_traces show <trace_id>
```

The trace viewer is read-only. It does not call the LLM provider, execute tools, dispatch workflows, or invoke the accompaniment engine.

---

## Running the Backend Locally

From the project root:

```bash
PYTHONPATH=src uv run uvicorn jammate_api.app:app --host 0.0.0.0 --port 8000
```

Mac local test:

```text
http://127.0.0.1:8000/health
```

Phone-to-Mac LAN test:

```text
http://<MAC_LAN_IP>:8000/health
```

The phone must use the Mac LAN IP, not `127.0.0.1`.

---

## Basic Validation Commands

```bash
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python examples/scripts/generate_minimal_demo.py
```

For HarmonyOS smoke testing:

```bash
cd frontend_fixtures/harmonyos/smoke
bash curl_smoke.sh http://127.0.0.1:8000
```

---

## Development Workflow

Current recommended Git branches:

```text
main                       # Stable only; do not commit directly
feature/engine-deepening    # Engine / voicing / pattern / expression / style tuning
feature/agent-workflow      # Agent / API / HarmonyOS / LLM workflow development
integration/agent-engine-merge # Shared files, versions, API/docs reconciliation
```

Each ChatGPT engineering delivery should be treated as a full project package. Before packaging and handing off, remove cache/temp artifacts, keep README focused on project identity and architecture, and keep version surfaces aligned.

See:

```text
docs/DEVELOPMENT_HARNESS_V2.md
docs/BRANCH_AND_TRACK_OWNERSHIP_V2.md
docs/DEVELOPMENT_TASK_PLAN_ENGINE_V2.md
docs/DEVELOPMENT_TASK_PLAN_AGENT_V2.md
docs/ARCHITECTURE_V2.md
docs/API_CONTRACT_V2.md
docs/STYLE_TUNING_ENTRY_POINT_V2.md
docs/GENERATION_RULES_SUMMARY_V2.md
docs/AGENT_TOOL_CALL_PREVIEW_TRACE_CONTRACT_V2_4_13.md
docs/V1_MUSICAL_RULES_TO_V2_NATIVE_MAPPING_V2_5_1.md
docs/JAZZ_BALLAD_GESTURE_CONTRACT_FOUNDATION_V2_5_2.md
docs/JAZZ_BALLAD_PHRASE_INTENT_FOUNDATION_V2_5_3.md
docs/JAZZ_BALLAD_HELD_FOUNDATION_PARTIAL_REATTACK_V2_5_4.md
docs/JAZZ_BALLAD_TWO_BEAT_1AND_PATTERN_PATCH_V2_5_5.md
```

---

## Current Development Status

### v2_10_8 integration merge baseline

`v2_10_8` is the current integration/agent-engine-merge baseline. It merges Engine Track `v2_6_44_engine_ballad_spread_voicing_phase_summary_handoff` with Agent Track `v2_10_7_agent_harmonyos_today_guidance_runtime_smoke`.

Integration handling:

- Engine generation/runtime/voicing/style code remains from the Engine Track through v2.6.44, including frozen Ballad SPREAD guardrails, lower-foundation calibration, safe extension frequency calibration, and phrase-state anchor policy.
- Agent orchestration, contracts, trace, terminal, tool-preview, context/guidance, persistence, and HarmonyOS product routes remain from the Agent Track through v2.10.7, including routine-completion-record persistence and today-practice-guidance runtime smoke.
- Shared docs, version surfaces, and HarmonyOS fixture surfaces are reconciled in this integration package.
- No new Engine music-generation rule and no new Agent/LLM product feature is introduced by this integration pass beyond what each track already delivered.
- `POST /accompaniment/generate` preserves the HarmonyOS playback-critical response shape: `ok`, `asset.format`, `asset.midi_base64`, `asset.midi_path`, `asset.cache_key`, and `debug_summary`.

### v2_8_24 integration merge baseline

`v2_8_24` was the previous integration baseline. It merged Engine Track `v2_6_30_engine_ballad_spread_1plus4_lower_foundation_calibration` with Agent Track `v2_8_23_agent_v2_8_phase_cleanup_regression_handoff`.

### v2_6_1 branch / track ownership status

`v2_6_1` is a governance hardening pass on top of the integrated `v2_5_10` package. It adds explicit Engine / Agent / Integration track ownership, splits rolling task plans and changelogs to reduce merge conflicts, and hardens the harness so shared files are integration-owned by default. No engine music-generation logic, Agent execution behavior, or API response shape changed.

### v2_5_10 integration merge status

`v2_5_10` merges the latest Agent workflow line (`v2_4_13`) into the official engine-deepening baseline (`v2_5_9`). Engine runtime behavior, Jazz Ballad swing-8 timing, gesture/expression/voicing boundaries, and V1-instrument-rule planning remain from the engine branch. Agent terminal chat, provider-boundary, trace-viewer, validation-only tool-preview, and HarmonyOS contract fixture work remain from the Agent branch. See `docs/AGENT_ENGINE_INTEGRATION_MERGE_V2_5_10.md`.

### v2_5_9 engine-deepening audit status

`v2_5_9` is a documentation-only engine planning pass based on the `v2_5_8` listening baseline. It rejects the earlier experimental Ballad brush-drums shortcut and records a deeper V1 instrument-rule audit for Jazz Ballad, Medium Swing, and Bossa Nova. The new formal reference is `docs/V1_INSTRUMENT_RULES_DEEP_AUDIT_AND_V2_NATIVE_MAPPING_V2_5_9.md`. No generation code, Agent/LLM logic, API behavior, voicing realization, or MIDI output behavior changed in this pass.

`v2_5_8` corrects Jazz Ballad timing-feel ownership. Ballad now defaults to swing-8 timing, so written `.5` upbeats perform at the triplet/swing `2/3` point by default. Ballad anticipation also keeps the pitchless logical `4&` location while carrying `timing_intent=swing_upbeat`, so anticipated chords perform on the swing `4&` rather than a straight eighth. Pattern remains pitchless; voicing, expression, pedal, and Agent/LLM behavior are otherwise unchanged.

`v2_5_5` is a narrow Jazz Ballad listening patch. Two-beat piano soft-mark candidates now use `beat 1 + beat 1&` (`0.0, 0.5`) instead of `beat 1 + beat 2` (`0.0, 1.0`). Pattern remains pitchless; voicing still chooses concrete notes; expression still owns duration, velocity, touch, and pedal. Agent/LLM behavior remains unchanged:

```text
Agent window  -> feature/agent-workflow
Engine window -> feature/engine-deepening
```


---

## Development Track Governance

- `docs/BRANCH_AND_TRACK_OWNERSHIP_V2.md`: owner paths, shared-file rules, and merge conflict policy.
- `docs/DEVELOPMENT_TASK_PLAN_ENGINE_V2.md`: Engine-track rolling plan.
- `docs/DEVELOPMENT_TASK_PLAN_AGENT_V2.md`: Agent-track rolling plan.
- `docs/CHANGELOG_ENGINE.md` / `docs/CHANGELOG_AGENT.md`: track-specific history to reduce conflicts in the global changelog.
