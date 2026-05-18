# JamMatePyEngineV2

JamMatePyEngineV2 is the Python backend foundation for JamMate. It currently contains three sibling systems:

```text
src/
  jammate_engine/   # Independent accompaniment generation kernel
  jammate_agent/    # Agent / practice orchestration layer
  jammate_api/      # FastAPI service assembly layer
```

Current package version: `v2_4_12`.

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
- Builds task-scoped LLM context runtime preview packets without calling a real LLM provider.
- Exposes a provider-neutral LLM config/status boundary without provider SDK imports or network calls.
- Exposes a descriptor-only Agent tool registry for future bounded LLM tool planning.
- Exposes a terminal chat CLI for optional provider-backed LLM conversation during backend debugging.
- Provides terminal LLM setup/doctor/config-path helpers so local provider settings can be reused without repeated shell exports.
- Scans successful terminal LLM replies for explicit JSON tool-call candidates and previews them without execution.
- Exposes a bounded runloop preview contract for future tool workflows.
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

Typical HarmonyOS request prefers inline `jammate_leadsheet_v2` and keeps `tune` only as a fallback hint:

```json
{
  "leadsheet": {
    "schema_version": "jammate_leadsheet_v2",
    "title": "User Custom Chart",
    "key": "C",
    "sections": {
      "A": {
        "label": "A",
        "bars": [
          { "chords": [{ "beat": 1.0, "symbol": "Cmaj7" }] }
        ]
      }
    },
    "written_form": ["A"]
  },
  "tune": "optional fallback only",
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
GET  /agent/context/runtime/spec
POST /agent/context/runtime/preview
GET  /agent/llm/provider/spec
GET  /agent/tools/registry
GET  /agent/contracts/arkts
GET  /agent/contracts/arkts/files
GET  /agent/contracts/frontend-pack
GET  /agent/contracts/smoke-pack
GET  /agent/traces
GET  /agent/traces/{trace_id}
```

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
feature/agent-workflow      # Agent / API / HarmonyOS / LLM workflow development
feature/engine-deepening    # Engine / voicing / pattern / expression / style tuning
```

Each ChatGPT engineering delivery should be treated as a full project package. Before packaging and handing off, remove cache/temp artifacts, keep README focused on project identity and architecture, and keep version surfaces aligned.

See:

```text
docs/DEVELOPMENT_HARNESS_V2.md
docs/ARCHITECTURE_V2.md
docs/API_CONTRACT_V2.md
docs/STYLE_TUNING_ENTRY_POINT_V2.md
docs/GENERATION_RULES_SUMMARY_V2.md
```

---

## Terminal Agent Chat

The terminal-first LLM chat entry point remains available for backend debugging:

```bash
PYTHONPATH=src python -m jammate_agent.cli.terminal_chat
```

The CLI no longer requires manual shell exports every time. You can create a local provider config once:

```bash
jammate-agent-chat setup
jammate-agent-chat doctor
```

Then start chat directly, or point at a specific config file:

```bash
jammate-agent-chat --config-file ~/.jammate/agent_config.env
```

Config precedence is explicit env vars, `JAMMATE_AGENT_LLM_CONFIG_FILE`, repo-local `.jammate_agent.env`, then `~/.jammate/agent_config.env`. API key values are masked from setup/doctor/status/trace output. The CLI can call a configured provider for terminal debugging only; it does not execute Agent tools. The API runloop preview remains preview-only.

Terminal tool-call validation is also available without execution:

```bash
PYTHONPATH=src python -m jammate_agent.cli.terminal_chat --task-type immediate_practice_playback --once '/tool-preview agent_playback_prepare {"durationMinutes":20}'
```

Interactive commands:

```text
/help
/session
/context [full|--full|json|--json]
/profiles
/profile [task_type]
/task-type [task_type]
/instrument [instrument]
/reset
/tools
/tool-preview <tool_name> [json_object_arguments]
/trace
/traces
/exit
```

Read-only trace viewing is available separately from chat:

```bash
PYTHONPATH=src python -m jammate_agent.cli.trace_viewer --trace-dir tmp/terminal_traces list
PYTHONPATH=src python -m jammate_agent.cli.trace_viewer --trace-dir tmp/terminal_traces show <trace_id>
PYTHONPATH=src python -m jammate_agent.cli.trace_viewer spec
```

The trace viewer never executes tools, calls an LLM provider, dispatches workflows, or imports the engine. Terminal context controls rebuild ContextPacket previews only; they do not call the provider or execute tools.

## Current Development Status

`v2_4_12` is the Agent terminal LLM config wizard baseline for `feature/agent-workflow`. It preserves terminal chat, optional provider-backed conversation, validation-only `/tool-preview`, explicit `--trace-dir` export, read-only trace viewer, context/profile/session controls, and JSON-only tool-call candidate extraction, then adds `setup` / `doctor` / `config-path` plus local `.env`-style config loading. Extracted candidates are previewed against the current ContextPacket allow-list and never executed. Autonomous tool execution, runloop-driven tool execution, deterministic workflow dispatch, provider guard bypass, and engine adapter dispatch remain disabled. HarmonyOS `/accompaniment/generate` inline leadsheet behavior from `v2_4_1` remains intact. Runtime music generation behavior is unchanged from `v2_3_17`.

```text
Current active window -> feature/agent-workflow
Engine-deepening work -> not touched in this delivery
```
