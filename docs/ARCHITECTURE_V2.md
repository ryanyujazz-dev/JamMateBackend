# JamMatePyEngineV2 Architecture

Current baseline: `v2_3_17`.

This document records the canonical architecture. Version-specific delivery notes belong in separate `docs/*V2_x_x*.md` files.

---

## Top-Level Package Boundary

```text
src/
  jammate_engine/   # Independent accompaniment generation kernel
  jammate_agent/    # Sibling Agent / practice orchestration layer
  jammate_api/      # FastAPI service assembly layer
```

### Boundary rules

- `jammate_engine` must not import `jammate_agent`.
- `jammate_engine` must remain directly callable without LLM/Agent.
- `jammate_agent` may use the engine only through provider/adapter boundaries.
- `jammate_api` may assemble both direct engine routes and Agent routes.
- HarmonyOS local practice state must be able to run without LLM.

---

## Runtime Paths

### Direct accompaniment path

```text
HarmonyOS / client
  -> POST /accompaniment/generate
  -> jammate_api.routes.accompaniment_routes
  -> jammate_engine.runtime.generate.generate_accompaniment
  -> MIDI asset / midi_base64
```

Use this when the client already has explicit accompaniment parameters.

### Agent playback path

```text
HarmonyOS / client
  -> POST /agent/playback/prepare
  -> jammate_api.routes.agent_routes
  -> JamMateAgent workflow
  -> ChartResolver / ImmediatePlaybackWorkflow
  -> JamMateEngineAccompanimentAdapter
  -> jammate_engine.runtime.generate.generate_accompaniment
  -> MIDI asset / playback instruction / trace_id
```

Use this when the user expresses a practice goal or natural-language playback request.

---

## Engine Musical Pipeline

```text
LeadSheet / Score Input
  -> ChordRegionTimeline / performance regions
  -> Style pattern policy
  -> Pitchless event timeline
  -> Anticipation resolver
  -> Expression policy
  -> Voicing policy / selector
  -> Realization
  -> MIDI writer / base64 asset
```

Responsibilities:

```text
Pattern       = horizontal pitchless rhythm / event layout
Anticipation  = pitchless event movement across chord-region boundaries
Expression    = duration, release, velocity, articulation, pedal intent
Voicing       = vertical pitch realization
MIDI          = final note / CC materialization
```

Patterns are style-owned. Voicing and expression are core-level shared systems.

---

## Agent Architecture

```text
jammate_agent/core/
  jammate_agent.py       # high-level Agent facade
  context.py             # context packet structures
  intent_classifier.py   # workflow intent classification
  runloop.py             # bounded workflow loop foundation
  guardrails.py          # validation / safety / constraints
  trace.py               # trace logging and persistence
  contracts.py           # capability/context/contract manifests
  contract_codegen.py    # ArkTS + fixture generation source

jammate_agent/capabilities/
  practice/              # practice plan/session/review capabilities
  accompaniment/         # playback request / provider contracts
  charts/                # chart resolving contracts

jammate_agent/adapters/
  jammate_engine_accompaniment_adapter.py
  local_chart_library_adapter.py
  placeholder_accompaniment_adapter.py
```

The Agent is currently workflow/rule based. Full LLM integration is a future enhancement and should preserve deterministic tool/workflow boundaries.

---

## API Architecture

```text
jammate_api/
  app.py
  schemas.py
  routes/
    health_routes.py
    accompaniment_routes.py
    agent_routes.py
    practice_routes.py
```

API contracts:

- Requests accept snake_case and camelCase where useful.
- Backend responses are canonical snake_case.
- HarmonyOS frontend types are camelCase and should use generated `CaseAdapter.ets` for mapping.
- Long practice duration is a client timer concern. The backend returns a playable asset and loop instruction.

---

## HarmonyOS Integration Boundary

HarmonyOS should own:

- local practice tasks/routines/session state
- timers
- playback state
- local asset cache
- UI/store camelCase domain objects
- pending sync

Python backend should own:

- accompaniment generation
- Agent orchestration
- future LLM context/tool workflows
- chart/material resolving that is not local-only
- future MIDI/audio analysis

---

## Delivery Hygiene

Every package handoff must remove transient caches and keep project entry docs clean. See `docs/DEVELOPMENT_HARNESS_V2.md` and `docs/PROJECT_CLEANUP_AND_README_CONSOLIDATION_V2_3_16.md`.
