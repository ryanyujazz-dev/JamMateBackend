# Engine MIDI Output Pipeline Boundary Audit V2.6.3

**Track:** `feature/engine-deepening`  
**Task:** `v2_6_3_engine_midi_pipeline_boundary_audit_doc_and_light_tests`  
**Change type:** documentation + light boundary tests; no generation-rule or listening-behavior change  
**Shared version files:** intentionally unchanged

---

## 1. Purpose

This document records the important runtime boundaries in the current MIDI output chain. It is meant to prevent future development from accidentally mixing responsibilities across pattern, anticipation, expression, voicing, realization, timing, pedal, and MIDI writing.

The current healthy shape is:

```text
GenerationRequest / API request
↓
Leadsheet validation and parsing
↓
ChordRegionTimeline
↓
Style-owned pitchless pattern planning
↓
Bass foundation target-to-target generation
↓
Anticipation pitchless timeline rewrite
↓
Expression resolution
↓
Voicing resolution
↓
Gesture projection / instrument realization
↓
NoteEvent list
↓
Timing / humanization policy
↓
Pedal CC64 realization
↓
MIDI writer
↓
.mid / midi_base64 asset
```

---

## 2. API Boundary

### Owner

```text
src/jammate_api/routes/accompaniment_routes.py
src/jammate_api/schemas.py
```

### Input

The HarmonyOS-facing request is `DirectAccompanimentGenerateRequest`, usually carrying:

```text
leadsheet | tune
style
tempo
choruses
seed
output_path
ensemble
voicing_override
output_format = midi_base64
```

### Output

The active route converts camelCase client fields into engine snake_case data and calls `generate_accompaniment(...)` with a plain generation request dictionary.

Successful API response is an asset envelope:

```json
{
  "ok": true,
  "asset": {
    "format": "midi_base64",
    "midi_base64": "...",
    "midi_path": "...",
    "cache_key": "...",
    "debug_summary": {}
  }
}
```

### Boundary rule

The API layer may normalize request field naming and choose a chart source. It must not make musical pattern, expression, voicing, pedal, or MIDI timing decisions.

---

## 3. Runtime Facade Boundary

### Owner

```text
src/jammate_engine/runtime/generate.py
src/jammate_engine/runtime/generation_request.py
src/jammate_engine/runtime/generation_result.py
src/jammate_engine/runtime/engine_runtime.py
```

### Input

```text
GenerationRequest | dict
```

### Output

```text
GenerationResult(ok, midi_path, version, style, tempo, debug)
```

### Boundary rule

The runtime facade is a public entrypoint and result wrapper. It should not own generation rules, voicing rules, or MIDI repair logic.

---

## 4. Engine Orchestration Boundary

### Owner

```text
src/jammate_engine/core/engine.py
```

### Input

```text
GenerationRequest
output_path
```

### Main runtime data it gathers

```text
random seed / rng
EnsembleContext
Leadsheet
ChordRegionTimeline
StyleProfile
effective VoicingPolicy
```

### Output

```text
midi_path
debug dictionary
```

### Boundary rule

`JamMateEngine.generate()` is the pipeline orchestrator. It may sequence modules and collect debug data. It should not become the owner of style pattern vocabulary, voicing recipe logic, expression profile selection, pedal CC64 mechanics, or MIDI serialization details.

---

## 5. Leadsheet / Form / Chord Region Boundary

### Owner

```text
src/jammate_engine/core/leadsheet/
src/jammate_engine/core/form/form_expander.py
src/jammate_engine/core/timeline/chord_region_timeline.py
```

### Input

```text
jammate_leadsheet_v2 document
```

### Output

```text
Leadsheet
ChordRegionTimeline
HarmonicRegion[]
```

A `HarmonicRegion` is the main generation unit and carries facts such as:

```text
region_id
chord_symbol
next_chord_symbol
chorus_index
bar_index / performance_bar_index
chord_index
start_beat
duration_beats
section / phrase metadata
```

### Boundary rule

The leadsheet/form layer compiles score structure into harmonic regions. It must not choose style patterns, expression, voicing content, or final notes.

---

## 6. Style Pattern Planning Boundary

### Owner

```text
src/jammate_engine/styles/<style>/profile.py
src/jammate_engine/styles/<style>/comping_patterns.py
src/jammate_engine/core/pattern_runtime/
```

### Input

```text
HarmonicRegion
style context: tempo, ensemble, rng, pattern history
```

### Output

```text
PatternPlan(events=PatternEvent[])
```

A `PatternEvent` is pitchless and may contain:

```text
event_id
track
region_id
chord_symbol
onset_beat / local_beat
role
gesture_type / GestureRequest
expression_hint
status
pattern_id
metadata
```

### Boundary rule

Pattern events describe horizontal placement, roles, eligibility, and pitchless gesture requests. They must not contain final MIDI note, final duration, final velocity, concrete voicing notes, or pedal CC64 events.

---

## 7. Bass Foundation Boundary

### Owner

```text
src/jammate_engine/generation/bass_foundation/
src/jammate_engine/realization/bass_foundation_realizer.py
```

### Input

```text
HarmonicRegion[]
style.bass_foundation_source
BassFoundationPolicy
rng / context
```

### Output

```text
BassFoundationPlan(events=PatternEvent[], metadata=...)
```

### Current note

Bass foundation is intentionally more pitch-continuity-aware than piano comping because target-to-target bass motion depends on register continuity and next-target resolution. Some bass `PatternEvent.metadata` may therefore carry resolved pitch facts used by `BassFoundationRealizer`.

### Boundary rule

This special bass behavior should not be generalized back into piano style patterns. Future bass work should avoid expanding generator/realizer coupling unless it is necessary for bass-line continuity.

---

## 8. Anticipation Boundary

### Owner

```text
src/jammate_engine/core/anticipation/
```

### Input

```text
PatternEvent[]
AnticipationPolicy
regions / region_plans
rng
```

### Output

```text
PatternEvent[]
```

Anticipation may:

```text
insert an anticipated pitchless event on the previous region tail
mark the original beat-1 event as suppressed
add anticipation/timing metadata
```

### Boundary rule

Anticipation rewrites the pitchless timeline only. It must not select voicing notes, final durations, velocities, or MIDI CC64 pedal events.

---

## 9. Expression Boundary

### Owner

```text
src/jammate_engine/core/expression/
src/jammate_engine/styles/<style>/expression_policy.py
```

### Input

```text
PatternEvent[]
style.expression_policy
style.timing_policy
```

### Output

```text
ExpressionPlan(events: event_id -> EventExpression)
```

An `EventExpression` may contain:

```text
duration_beats
velocity
articulation
pedal intent
touch
release_beats
accent
profile_name
metadata
```

### Boundary rule

Expression decides duration, release, velocity, articulation, touch, and pedal intent. It must not select voicing content, concrete pitch, source degrees, or MIDI serialization.

---

## 10. Harmonic Realization / Voicing Request Boundary

### Owner

```text
src/jammate_engine/realization/harmonic_realizer.py
src/jammate_engine/core/voicing/runtime/
```

### Input

```text
active piano PatternEvent
EventExpression
VoicingPolicy
EnsembleContext
```

### Output

```text
VoicingRequest
VoicingPlan
NoteEvent[] after gesture projection
```

### Boundary rule

`HarmonicRealizer` adapts a pattern event plus expression into a voicing request, then projects the returned voicing through gesture realization. It should not absorb long-term style-policy logic, source-selection algorithms, or MIDI writer behavior.

---

## 11. Voicing Boundary

### Owner

```text
src/jammate_engine/core/voicing/
```

### Input

```text
VoicingRequest
```

A `VoicingRequest` carries:

```text
event_id
chord_symbol
track
gesture_type / pitchless GestureRequest
expression_articulation
ensemble_context
VoicingPolicy
onset_beat
rng
```

### Output

```text
VoicingPlan
```

A `VoicingPlan` carries:

```text
VoicedNote[]
projection_map
groups
content_family
disposition
root_support
bass_relation
interval_structure
root_included
density
functional_grouping
recipe_id
voice-leading / selector / guard metadata
```

### Boundary rule

Voicing selects concrete vertical pitch content, disposition, density, grouping, register, and voice-leading. It should not decide final duration, final velocity, pedal span, MIDI track layout, or pattern rhythm.

---

## 12. Gesture Projection / NoteEvent Boundary

### Owner

```text
src/jammate_engine/realization/gesture_realizer.py
src/jammate_engine/realization/note_event_builder.py
```

### Input

```text
PatternEvent
VoicingPlan
EventExpression
```

### Output

```text
NoteEvent[]
```

A `NoteEvent` is the first normal object in the chain that should contain final renderable note facts:

```text
track
channel
note
velocity
start_beat
duration_beats
timing_intent
voice/projection audit metadata
expression/pedal audit metadata
```

### Boundary rule

Gesture projection may distribute already-selected voiced notes over time according to a pitchless gesture. It must not reselect voicing source degrees or perform MIDI timing/humanization.

---

## 13. Timing / Humanization Boundary

### Owner

```text
src/jammate_engine/midi/render_pipeline.py
```

### Input

```text
NoteEvent[] with logical beats
TimingPolicy
```

### Output

```text
NoteEvent[] with performed beat positions
```

### Boundary rule

Timing policy owns performance placement such as swing-upbeat interpretation and optional humanization. Pattern libraries should keep written grid values like `.5`; timing policy performs them as swing/triplet upbeats when the style requests it.

---

## 14. Pedal CC64 Boundary

### Owner

```text
src/jammate_engine/midi/render_pipeline.py
```

### Input

```text
performed NoteEvent[]
expression pedal intent carried on NoteEvent.pedal
style timing metadata
```

### Output

```text
PedalEvent[]
```

### Boundary rule

Expression chooses pedal intent. The MIDI boundary materializes approved CC64 spans and style-specific re-pedal offsets. Pattern and voicing must not emit CC64 events directly.

---

## 15. MIDI Writer Boundary

### Owner

```text
src/jammate_engine/midi/midi_writer.py
```

### Input

```text
performed NoteEvent[]
PedalEvent[]
tempo_bpm
output_path
```

### Output

```text
.mid file
```

### Boundary rule

The MIDI writer serializes already-resolved note and controller events. It must not repair musical rhythm, select notes, change voicing, or reinterpret style patterns.

---

## 16. Current Watchlist

These are not blockers for the current MIDI output chain, but they should guide future cleanup:

1. `realization/harmonic_realizer.py` carries more event-scoped voicing-policy adapter logic than ideal.
2. Bass foundation currently crosses further into pitch resolution than piano pattern planning; keep that behavior bass-specific and auditable.
3. `core/voicing/disposition/spread.py` and `core/voicing/sources/content_planner.py` remain large maintenance hotspots.
4. `jammate_engine.api.routes` is legacy compatibility; active HarmonyOS route ownership is under `jammate_api.routes`.
5. The MIDI writer is currently track-layout-specific enough for piano/bass/drums; future instruments may require dynamic track-count handling.

---

## 17. Boundary Test Intent

The focused tests for this pass should verify:

```text
PatternEvent stays pitchless.
EventExpression stays expression-only.
VoicingRequest does not carry final duration/velocity/pedal/note fields.
VoicingPlan is the concrete vertical pitch boundary.
NoteEvent is the final renderable note boundary.
Engine debug exposes the correct macro pipeline order.
Timing policy and pedal realization debug preserve their boundary strings.
This document exists and names the runtime contracts.
```

These tests are intentionally light. They are not listening tests and do not change musical output.
