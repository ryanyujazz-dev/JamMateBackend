# JamMatePyEngineV2 Architecture

Current baseline: `v2_10_8`.

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
  -> Gesture requests / projection intent
  -> Expression policy
  -> Voicing policy / selector
  -> Realization
  -> MIDI writer / base64 asset
```

Responsibilities:

```text
Pattern       = horizontal pitchless rhythm / event layout
Anticipation  = pitchless event movement across chord-region boundaries
Gesture       = pitchless projection / inner movement / rolled onset / partial reattack intent
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


### Agent Trace Viewer CLI

The Agent trace viewer is a read-only developer/HarmonyOS debugging surface. It reads `JsonTraceStore` output through `jammate_agent.cli.trace_viewer` / `jammate-agent-traces` and must not call the LLM provider, execute tools, dispatch deterministic workflows, or invoke the accompaniment engine.

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


## V1 Rule Absorption Boundary

V1 source may be reviewed for musical facts, but V2 implementation must remain native to this architecture. In particular, inner movement, rolled comping, cadence roll, and partial reattack are Gesture/Expression/Voicing cooperation points. They must not be reintroduced as V1-style pattern+voicing+MIDI bundles.


## v2_5_2 Jazz Ballad Gesture Contract Boundary

Jazz Ballad may now request `inner_movement` and `rolled_onset` through its style `gesture_policy.py`, but these requests remain pitchless projection/motion contracts. Gesture metadata may describe abstract motion shape, attack scope, held-foundation policy, and functional projection refs. It must not carry concrete MIDI notes, final expression values, pedal decisions, voicing texture names, source-degree choices, or V1 slot-slicing assumptions.

Default audible comping is intentionally unchanged in this pass. Phrase intent and partial-reattack realization remain later stages in the engine-deepening roadmap.


## v2_5_3 Jazz Ballad Phrase Intent Boundary

Jazz Ballad phrase intent is now expressed inside the existing style comping vocabulary, not through a migrated V1 phrase engine. `styles/jazz_ballad/comping_patterns.py` may label pitchless candidates with `phrase_family`, `phrase_function`, `phrase_slot`, `context_gate`, and approved `gesture_intent`, and may request approved pitchless `GestureRequest` values through `gesture_policy.py`.

Phrase candidates must not choose concrete notes, source degrees, voicing textures, final duration/velocity/touch/pedal, or MIDI repair behavior. Inner movement remains a Gesture request; held-foundation partial reattack is deferred to the realization/expression pass.


## v2_5_4 Held Foundation Partial Reattack Boundary

Jazz Ballad partial reattack is realized at the boundary between `core/gestures`, `core/expression`, `core/voicing`, and `realization`. Pattern candidates may request `INNER_MOVEMENT`, but they remain pitchless. `GestureRealizer` projects only requested motion voices from the `VoicingPlan`; `ExpressionResolver` does not cut a warm anchor merely because a later inner movement occurs; `HarmonicRealizer` trims only the re-struck motion voices so foundation/common tones continue ringing.


## v2_5_6 Jazz Ballad Swing 1& Timing Intent Patch Boundary


## v2_5_9 V1 instrument-rule absorption boundary

`v2_5_9` formalizes how V1 style/instrument rules may influence V2: V1 source can be used only as musical-rule evidence, not as code structure to migrate. The concrete mapping is maintained in `docs/V1_INSTRUMENT_RULES_DEEP_AUDIT_AND_V2_NATIVE_MAPPING_V2_5_9.md`.

Important architectural consequences:

- Ballad `inner movement` remains a V2 gesture/projection concern, not a comping pattern cell.
- Ballad brush/drums must be modeled as semantic percussion policy dimensions before adding audible loops.
- Ballad bass should evolve through an anchor-path policy before walking or generic ornaments.
- Swing and Bossa style work must preserve each style's own instrument grammar rather than sharing generic MIDI patterns.

Jazz Ballad upbeats keep the V2 timing contract: the pattern layer stores written upbeats as logical `.5`, and the render timing stage owns performed placement. As of v2_5_8 the Jazz Ballad timing profile defaults to `feel=swing`, so ordinary `.5` events with `timing_intent=auto` and explicit `timing_intent=swing_upbeat` events both perform at the swing/triplet upbeat (`2/3`). Ballad anticipation likewise keeps the pitchless logical `4&` target but carries `timing_intent=swing_upbeat` and `timing_grid=swing_triplet_upbeat`; expression tie duration uses the performed lead-in (`1/3`) rather than a straight half-beat.

This remains a timing-intent correction only. It does not move the event to literal `0.666...` in the pattern, does not change notes, voicing texture, expression duration/velocity, pedal behavior, gesture semantics, or Agent/LLM logic.

## v2_5_5 Jazz Ballad Two-Beat 1& Pattern Patch Boundary

Jazz Ballad two-beat piano soft-mark candidates now use local beats `0.0, 0.5`, corresponding to beat 1 plus beat 1&. This remains a pitchless pattern-layer timing correction only. Gesture, expression, voicing, pedal, and Agent/LLM boundaries are unchanged.


## v2_5_10 Integrated Two-Track Boundary

The integrated package keeps the engine and Agent as separate architectural tracks. `jammate_engine` remains the accompaniment generation owner; it must not import `jammate_agent`. `jammate_agent` may call engine behavior only through explicit adapters. Agent/LLM context, terminal chat, tool-preview, and traces are high-level workflow surfaces and must not choose pattern notes, voicing textures, expression values, or MIDI repair behavior.


## v2_6_1 Branch / Track Ownership Hardening

Parallel development now uses explicit Engine / Agent / Integration ownership. Engine work owns musical runtime behavior under `jammate_engine`; Agent work owns orchestration under `jammate_agent`; Integration work owns shared version surfaces, public docs, API reconciliation, and frontend fixtures. See `docs/BRANCH_AND_TRACK_OWNERSHIP_V2.md`.

This is a governance/architecture boundary change only. It does not change accompaniment generation behavior, Agent tool execution behavior, or HarmonyOS response shapes.


## v2_10_8 Integration Merge Boundary

This baseline merges Engine Track `v2_6_44_engine_ballad_spread_voicing_phase_summary_handoff` and Agent Track `v2_10_7_agent_harmonyos_today_guidance_runtime_smoke`.

The merge is boundary-preserving:

- Engine generation code remains the source of truth for Pattern, Gesture, Expression, Voicing, Realization, MIDI, and style behavior, including frozen Ballad SPREAD guardrails, lower-foundation calibration, safe extension frequency, and phrase-state anchor policy.
- Agent code remains the source of truth for practice orchestration, terminal chat, LLM/provider boundary, trace, tool-preview, context/guidance contracts, persistence preview contracts, and HarmonyOS product routes (routine-completion-record and today-practice-guidance).
- `jammate_api` assembles the direct accompaniment route and Agent routes without moving Agent logic into engine runtime.
- HarmonyOS direct accompaniment output remains backend snake_case with `asset.midi_base64`, `asset.midi_path`, `asset.cache_key`, and top-level `debug_summary`.


## v2_8_24 Integration Merge Boundary

This baseline merges Engine Track `v2_6_30_engine_ballad_spread_1plus4_lower_foundation_calibration` and Agent Track `v2_8_23_agent_v2_8_phase_cleanup_regression_handoff`.

The merge is boundary-preserving:

- Engine generation code remains the source of truth for Pattern, Gesture, Expression, Voicing, Realization, MIDI, and style behavior.
- Agent code remains the source of truth for practice orchestration, terminal chat, LLM/provider boundary, trace, tool-preview, context/guidance contracts, and persistence preview contracts.
- `jammate_api` assembles the direct accompaniment route and Agent routes without moving Agent logic into engine runtime.
- HarmonyOS direct accompaniment output remains backend snake_case with `asset.midi_base64`, `asset.midi_path`, `asset.cache_key`, and top-level `debug_summary`.
