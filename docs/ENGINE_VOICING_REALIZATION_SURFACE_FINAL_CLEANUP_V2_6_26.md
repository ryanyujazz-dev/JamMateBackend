# v2_6_26 Engine Voicing — Realization Surface Final Cleanup

## Scope

This is a voicing-only cleanup pass. It finalizes the `harmonic_realizer.py` surface after the v2_6_23 policy/context adapter split, the v2_6_24 note/audit split, and the v2_6_25 request/cache orchestration split.

No Pattern, Anticipation, Expression, Gesture, MIDI writer, Agent, API, HarmonyOS fixture, VERSION, README, or shared integration document was changed.

## Why this cleanup exists

After v2_6_25, most heavy realization-side helper logic had already moved out of `harmonic_realizer.py`. The remaining risk was conceptual drift: future work might again place source construction, color permission, projection, selector, request construction, cache logic, or audit payload ownership into the top-level realizer.

v2_6_26 makes the remaining surface explicit and auditable.

## Current owner map

```text
harmonic_realizer.py
  active piano PatternEvent iteration
  realization pass cache reset
  voicing plan request delegation
  GestureRealizer invocation
  NoteEvent list ownership
  piano audit surface version attachment

realizer_voicing_request_orchestration.py
  style input -> base VoicingPolicy
  PatternEvent + Expression -> VoicingRequest
  VoicingResolver call
  one-default-voicing-per-region cache
  explicit fresh revoicing escape hatch

voicing_policy_context_adapter.py
  PatternEvent metadata -> event-scoped VoicingPolicy metadata

realizer_note_audit.py
  piano audit rows
  note debug payloads
  partial inner-movement reattack NoteEvent trims

gesture_realizer.py
  selected VoicingPlan -> NoteEvent projection for gesture refs
```

## HarmonicRealizer after final cleanup

`harmonic_realizer.py` is now treated as a thin realization surface:

```text
PatternEvent + ExpressionPlan + style policy
-> base_voicing_policy_from_style_input(...)
-> RealizerVoicingRequestOrchestrator.resolve_event_voicing(...)
-> GestureRealizer.realize_harmonic_event(...)
-> realizer_note_audit.py helpers
-> list[NoteEvent]
```

It may call `RealizerVoicingRequestOrchestrator`, `GestureRealizer`, and `realizer_note_audit.py` helpers, but it must not bypass them.

## Explicit boundary profile

`harmonic_realizer.py` now exposes:

```text
HARMONIC_REALIZER_SURFACE_FINAL_CLEANUP_VERSION = "v2_6_26"
HarmonicRealizerSurfaceFinalCleanupProfile
harmonic_realizer_surface_final_cleanup_profile()
```

Owned responsibilities:

- active piano PatternEvent iteration;
- realization pass cache reset;
- voicing plan request delegation;
- GestureRealizer invocation;
- NoteEvent list ownership;
- piano audit surface version attachment.

Forbidden responsibilities:

- does not construct degree sources;
- does not route content families;
- does not decide color permission;
- does not project closed/open/spread voicings;
- does not score or select voicing candidates directly;
- does not build VoicingRequest directly;
- does not own region voicing cache logic;
- does not build piano audit payloads directly;
- does not write MIDI or apply expression.

## Profile owner corrections

`realizer_note_audit.py` already owned the note/audit/debug payload boundary, but its debug profile still named `harmonic_realizer.py` as the request orchestration owner. After v2_6_25 that owner is now:

```text
jammate_engine.realization.realizer_voicing_request_orchestration
```

`voicing_policy_context_adapter.py` is likewise consumed through `realizer_voicing_request_orchestration.py`, not called directly by the top-level realizer surface. v2_6_26 updates these debug metadata fields so the surface audit matches the actual runtime boundary.

## Behavior guardrails

This pass is intended to be behavior-preserving.

Misty / Jazz Ballad / 3 choruses should retain:

```text
5-note:6-note ~= 6:4
4-note SPREAD default remains 0
retired 1+3 / 2+2 SPREAD default paths remain absent
maj7#11 remains off by default unless chart-explicit or harmonic-color intent enables it
```

The piano audit rows now include:

```text
harmonic_realizer_surface_final_cleanup_version = v2_6_26
```

## Validation

Recommended focused validation:

```bash
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python tools/check_development_harness.py
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_v2_6_26_engine_voicing_realization_surface_final_cleanup.py \
  tests/test_v2_6_25_engine_voicing_request_orchestration_cache_boundary_audit.py \
  tests/test_v2_6_24_engine_voicing_realizer_note_audit_cleanup.py \
  tests/test_v2_6_23_engine_voicing_harmonic_realizer_policy_context_adapter_cleanup.py \
  tests/test_v2_6_22_engine_voicing_cleanup_retired_spread_pilot_logic.py
```

## Recommended next task

```text
v2_6_27_engine_ballad_spread_listening_calibration_pass
```

After the realization surface is now clean enough, the next step can finally return from boundary cleanup to Ballad SPREAD listening calibration: upper register harshness, lower foundation clarity, same-chord reattack naturalness, and 5-note / 6-note voicing motion.
