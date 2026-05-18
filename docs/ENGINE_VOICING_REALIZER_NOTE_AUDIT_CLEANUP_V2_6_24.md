# v2_6_24 Engine Voicing — Realizer Note/Audit Cleanup

## Scope

This is a voicing-only cleanup pass. It separates NoteEvent/audit/debug helpers from `harmonic_realizer.py` into `realizer_note_audit.py` while preserving generated MIDI behavior and the piano musical audit schema.

No Pattern, Anticipation, Expression, Gesture, MIDI writer, Agent, API, HarmonyOS fixture, VERSION, README, or shared integration document was changed.

## Why this cleanup exists

After v2_6_23, `harmonic_realizer.py` no longer owns event-scoped voicing policy/context adaptation. The remaining file still mixed request orchestration with audit/debug helpers and partial-reattack NoteEvent trimming.

The intended boundary is now clearer:

```text
harmonic_realizer.py
  PatternEvent + ExpressionPlan + VoicingPolicy
  -> policy_with_event_voicing_context
  -> VoicingRequest
  -> VoicingResolver
  -> GestureRealizer
  -> NoteEvent list + piano audit rows

realizer_note_audit.py
  selected PatternEvent / Expression / VoicingPlan / NoteEvent
  -> note/audit/debug payloads
  -> partial inner-movement reattack NoteEvent release using selected voicing metadata
```

## New owner

```text
src/jammate_engine/realization/realizer_note_audit.py
```

Public entries:

```text
piano_audit_event
sync_piano_audit_realized_notes
note_event_debug
gesture_debug
event_is_partial_reattack
release_reattacked_motion_voices
```

Boundary profile:

```text
REALIZER_NOTE_AUDIT_CLEANUP_VERSION = "v2_6_24"
RealizerNoteAuditCleanupProfile
realizer_note_audit_cleanup_profile()
```

## Owned responsibilities

`realizer_note_audit.py` owns only the realization-side note/audit/debug boundary:

- piano audit event debug payload construction;
- final NoteEvent-to-audit synchronization;
- NoteEvent debug serialization of projection metadata;
- partial inner-movement reattack release using already-selected voicing metadata.

## Forbidden responsibilities

`realizer_note_audit.py` does not build VoicingRequest, does not construct degree sources, does not route content families, does not decide color permission, does not project closed/open/spread voicings, does not score or select candidates, and does not apply expression or write MIDI.

Partial reattack release remains a realization-layer NoteEvent trim only. It may inspect selected note `voice_role`, `group_id`, `projection_ref`, and pitch identity, but it must not choose new pitch content.

## Realizer after cleanup

`harmonic_realizer.py` now stays small and orchestration-focused:

```text
- normalize style VoicingPolicy
- iterate active piano PatternEvents
- adapt event policy context
- build VoicingRequest
- call VoicingResolver
- reuse one selected voicing per chord region unless explicitly revoiced
- call GestureRealizer
- delegate note/audit/debug helpers to realizer_note_audit.py
```

The moved helpers are no longer defined inside `harmonic_realizer.py`:

```text
_event_is_partial_reattack
_release_reattacked_motion_voices
_voice_identity_key
_sync_piano_audit_realized_notes
_piano_audit_event
_gesture_debug
_note_event_debug
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
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_v2_6_24_engine_voicing_realizer_note_audit_cleanup.py
```

Regression validation should include v2_6_10 through v2_6_24 focused voicing tests, plus the current non-retired SPREAD/source behavior subset.

## Recommended next task

```text
v2_6_25_engine_voicing_request_orchestration_cache_boundary_audit
```

Goal: audit the remaining `harmonic_realizer.py` responsibilities around request orchestration, one-voicing-per-region cache reuse, and explicit revoicing escape hatches. Keep it behavior-preserving unless the user explicitly requests listening changes.
