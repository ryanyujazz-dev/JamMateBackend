# v2_6_25 Engine Voicing — Request Orchestration / Cache Boundary Audit

## Scope

This is a voicing-only cleanup pass. It separates VoicingRequest construction, one-voicing-per-region cache reuse, and the explicit fresh revoicing escape hatch from `harmonic_realizer.py` into `realizer_voicing_request_orchestration.py` while preserving generated MIDI behavior and the piano musical audit schema.

No Pattern, Anticipation, Expression, Gesture, MIDI writer, Agent, API, HarmonyOS fixture, VERSION, README, or shared integration document was changed.

## Why this cleanup exists

After v2_6_23 and v2_6_24, `harmonic_realizer.py` no longer owns event-scoped policy/context adaptation or NoteEvent/audit/debug helpers. The remaining file still owned request construction and region voicing cache logic directly.

That was still too much for the top-level realizer because it mixed two responsibilities:

```text
harmonic_realizer.py
  PatternEvent + ExpressionPlan iteration
  -> request/cache orchestration
  -> VoicingResolver
  -> GestureRealizer
  -> NoteEvent list
```

The intended boundary after v2_6_25 is:

```text
harmonic_realizer.py
  PatternEvent + ExpressionPlan iteration
  -> ask RealizerVoicingRequestOrchestrator for a VoicingPlan
  -> call GestureRealizer
  -> call realizer_note_audit.py helpers
  -> return NoteEvent list

realizer_voicing_request_orchestration.py
  style voicing policy input
  -> base VoicingPolicy
  -> event-scoped policy_with_event_voicing_context
  -> VoicingRequest
  -> VoicingResolver
  -> one_default_voicing_selection_per_chord_region_until_explicit_gesture_revoices cache
  -> VoicingPlan
```

## New owner

```text
src/jammate_engine/realization/realizer_voicing_request_orchestration.py
```

Public entries:

```text
RealizerVoicingRequestOrchestrator
base_voicing_policy_from_style_input
region_voicing_cache_key
event_requests_fresh_voicing
reuse_region_voicing
realizer_voicing_request_orchestration_profile
```

Boundary profile:

```text
REALIZER_VOICING_REQUEST_ORCHESTRATION_VERSION = "v2_6_25"
RealizerVoicingRequestOrchestrationProfile
```

## Owned responsibilities

`realizer_voicing_request_orchestration.py` owns only request/cache orchestration:

- style voicing policy input coercion;
- event-scoped VoicingRequest construction;
- one default voicing selection per chord region cache;
- explicit fresh revoicing escape hatch via event / gesture metadata;
- region voicing reuse metadata attachment.

## Forbidden responsibilities

`realizer_voicing_request_orchestration.py` does not construct degree sources, does not route content families, does not decide color permission, does not project closed/open/spread voicings, does not directly score or select voicing candidates, does not build piano audit payloads, and does not apply expression or write MIDI.

The file may call `VoicingResolver.resolve(...)`, but it must not import or bypass the lower-level source inventory, color permission, projection, scorer, selector, gesture realizer, NoteEvent builder, or MIDI writer.

## Realizer after cleanup

`harmonic_realizer.py` is now a small realization surface:

```text
- normalize style VoicingPolicy through base_voicing_policy_from_style_input
- reset request orchestrator cache per realization pass
- iterate active piano PatternEvents
- request VoicingPlan from RealizerVoicingRequestOrchestrator
- call GestureRealizer
- delegate partial reattack and audit/debug helpers to realizer_note_audit.py
- return NoteEvent list
```

The following request/cache helpers are no longer defined inside `harmonic_realizer.py`:

```text
_event_requests_fresh_voicing
_reuse_region_voicing
region_voicing_cache
VoicingRequest construction
VoicingResolver construction
policy_with_event_voicing_context call site
```

## Cache contract

The cache remains behavior-preserving:

```text
one_default_voicing_selection_per_chord_region_until_explicit_gesture_revoices
```

Default behavior:

```text
same region_id + chord_symbol + track
  -> reuse selected VoicingPlan
```

Explicit fresh revoicing escape hatch:

```text
event.metadata.force_fresh_voicing
event.metadata.revoice_within_region
event.gesture.metadata.force_fresh_voicing
event.gesture.metadata.revoice_within_region
```

A reused plan receives metadata:

```text
region_voicing_reused = True
region_voicing_source_event_id = <original event id>
region_voicing_contract = one_default_voicing_selection_per_chord_region_until_explicit_gesture_revoices
realizer_voicing_request_orchestration_version = v2_6_25
```

## Density / color guardrails

This cleanup preserves the current Jazz Ballad SPREAD guardrails:

- 4-note SPREAD default remains disabled.
- 5-note:6-note ~= 6:4 remains the Misty three-chorus target.
- 7-note remains low-frequency / exceptional.
- maj7#11 remains off by default unless written in the chart or explicitly enabled by harmonic-color intent.

## Validation

Focused validation:

```text
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python tools/check_development_harness.py
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_v2_6_25_engine_voicing_request_orchestration_cache_boundary_audit.py
```

Regression validation should include v2_6_10 through v2_6_25 focused voicing tests, plus the current non-retired SPREAD/source behavior subset.

## Recommended next task

```text
v2_6_26_engine_voicing_realization_surface_final_cleanup
```

Goal: audit the now-small `harmonic_realizer.py` realization surface, remove any remaining misleading old comments/imports/tests, and decide whether the realizer is now sufficiently thin or whether a final naming/docs cleanup is still useful. Keep it behavior-preserving unless the user explicitly requests listening changes.
