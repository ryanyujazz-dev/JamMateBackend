# v2_6_23 Engine Voicing — Harmonic Realizer Policy Context Adapter Cleanup

## Scope

This is a voicing-only cleanup and boundary split pass. It moves event-scoped voicing policy/context adaptation out of `harmonic_realizer.py` into `voicing_policy_context_adapter.py`.

No Pattern, Anticipation, Expression, Gesture, MIDI, Agent, API, HarmonyOS fixture, VERSION, README, or shared integration document was changed.

## Why this cleanup exists

`harmonic_realizer.py` should remain the realization boundary that:

```text
PatternEvent + ExpressionPlan + VoicingPolicy
  -> VoicingRequest
  -> VoicingResolver
  -> GestureRealizer
  -> NoteEvent audit/output
```

It should not also own the detailed event-to-policy metadata bridge for harmonic context, texture scope, SPREAD grouping-mix contracts, spread upper/lower ratio slots, or Ballad density calibration metadata.

## New owner

```text
src/jammate_engine/realization/voicing_policy_context_adapter.py
```

Public entry:

```text
policy_with_event_voicing_context(policy, event)
```

Boundary profile:

```text
HarmonicRealizerPolicyContextAdapterProfile
harmonic_realizer_policy_context_adapter_profile()
HARMONIC_REALIZER_POLICY_CONTEXT_ADAPTER_VERSION = "v2_6_23"
```

## Owned responsibilities

`voicing_policy_context_adapter.py` owns only event-scoped policy/context translation:

- harmonic-region context attachment for voicing source-level policy gates;
- texture-scope metadata attachment;
- Ballad SPREAD grouping-mix context attachment;
- SPREAD lower/upper ratio metadata attachment;
- deterministic metadata slots used by existing grouped-SPREAD candidate routing.

## Forbidden responsibilities

The adapter explicitly does not construct degree sources, does not choose content family, does not decide color permission, does not project closed/open/spread voicings, does not score or select candidates, and does not realize MIDI notes or expression.

The adapter may attach policy metadata consumed later by core voicing owners, but those owners remain separate:

```text
content_family_router.py       # family routing
content_source_inventory.py    # source construction
color_permission.py            # color admission
source_balance.py              # source-family scoring/bias
spread_projection_core.py      # notes-only grouped spread projection
spread_runtime_adapter.py      # SpreadProjectionCandidate -> VoicingCandidate mapping
selector / scorer              # final candidate selection
```

## Realizer after cleanup

`harmonic_realizer.py` now calls:

```text
policy_with_event_voicing_context(policy, event)
```

It no longer directly defines the private helpers for:

```text
_policy_with_event_harmonic_context
_policy_with_ballad_spread_grouping_mix_policy
_policy_with_spread_upper_3note_expansion_ratio
_policy_with_spread_upper_4note_expansion_ratio
_policy_with_spread_lower_2note_rooted_equal_cycle
_spread_expansion_ratio_slot
_texture_contrast_plan_metadata
```

`harmonic_realizer.py` remains responsible for building `VoicingRequest`, caching/reusing one voicing per chord region, calling `VoicingResolver`, invoking `GestureRealizer`, trimming partial inner-movement reattacks, and emitting piano audit events.

## Density / color guardrails

This cleanup preserves the current Jazz Ballad SPREAD guardrails:

- 4-note SPREAD default remains disabled.
- 5-note:6-note ~= 6:4 remains the Misty three-chorus target.
- 7-note remains low-frequency / exceptional.
- maj7#11 remains off by default unless written in the chart or explicitly enabled by harmonic-color intent.

## Validation

Focused validation should include:

```text
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python tools/check_development_harness.py
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_v2_6_23_engine_voicing_harmonic_realizer_policy_context_adapter_cleanup.py
```

Regression validation should include the v2_6_10 through v2_6_22 voicing subsets and remaining SPREAD/source legacy behavior subsets, excluding old version/doc assertions where necessary.

## Recommended next task

```text
v2_6_24_engine_voicing_realizer_note_audit_cleanup
```

Goal: continue cleanup inside `harmonic_realizer.py` after the policy-context adapter split by separating NoteEvent audit/debug helpers from voicing request orchestration, while preserving the same generated MIDI and audit summary.
