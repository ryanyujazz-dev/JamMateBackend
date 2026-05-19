# v2_6_15 Engine Voicing — SPREAD Runtime Gate / Adapter Cleanup

## Scope

`v2_6_15_engine_voicing_spread_runtime_gate_and_adapter_cleanup` is a voicing-only boundary cleanup pass.

It is behavior-preserving relative to `v2_6_14_engine_voicing_ballad_spread_5_to_6_ratio_calibration`:

```text
Do not change Pattern / Anticipation / Expression / Gesture / MIDI
Do not change API / Agent / HarmonyOS fixtures
Do not change Ballad 5-note:6-note target ratio
Do not re-enable 4-note 1+3 / 2+2 SPREAD defaults
Do not allow default maj7#11 safe extension
```

## What changed

Two dedicated SPREAD runtime-boundary owners were introduced:

```text
src/jammate_engine/core/voicing/disposition/spread_runtime_gate.py
src/jammate_engine/core/voicing/disposition/spread_runtime_adapter.py
```

`spread.py` remains a public compatibility facade, but no longer directly defines:

```text
SpreadRuntimeGateDecision
SpreadCandidateSelectorRequest
SpreadCandidateSelectorResult
spread_runtime_gate_from_policy
select_spread_candidate_with_runtime_gate
SpreadRuntimeAdapterStatus
SpreadRuntimeAdapterFieldMapping
SpreadRuntimeAdapterResult
adapter field-mapping helper implementation
```

## Runtime gate owner

`spread_runtime_gate.py` owns the question:

```text
May notes-only SPREAD projection be queried for candidate selection?
```

It still does not own:

```text
conversion into runtime VoicingCandidate
candidate-generator pool merge
style retuning
expression / pedal / duration
pattern / anticipation / gesture / MIDI
```

The default gate remains closed unless both conditions are true:

```text
explicit spread runtime/selector request
spread texture family requested
```

## Runtime adapter owner

`spread_runtime_adapter.py` owns the explicit field mapping between:

```text
SpreadProjectionCandidate -> VoicingCandidate
```

It keeps conversion explicitly gated and preserves the existing safety flags:

```text
candidate_generator_wiring_allowed = false by default
style_runtime_wiring_enabled = false by default
runtime_enabled = false by default
adapter_skeleton_only = true
notes_only_source = true
no_expression_or_pedal = true
```

## Behavior preserved

The `v2_6_14` Ballad/SPREAD density calibration is preserved:

```text
5-note:6-note target ~= 6:4
4-note SPREAD default remains 0
7-note remains low-frequency
maj7#11 default remains 0
```

## Tests

Added:

```text
tests/test_v2_6_15_engine_voicing_spread_runtime_gate_adapter_cleanup.py
```

Primary assertions:

```text
1. dedicated runtime gate owner exists
2. dedicated runtime adapter owner exists
3. spread.py re-exports compatibility names but does not define the moved classes/functions
4. runtime gate remains closed by default
5. adapter conversion preserves notes/degrees and does not imply style runtime wiring
6. Misty Ballad 3-chorus density remains near 5-note:6-note = 6:4
7. maj7#11 remains absent by default
```

## Recommended next step

`v2_6_16_engine_voicing_content_planner_boundary_split_plan`

Rationale: after SPREAD lower/upper/register/projection/voice-leading/runtime boundaries are clearer, the next architecture pressure is content planning. The next step should be a planning/audit pass, not a destructive split, to decide how `sources/content_planner.py`, source weighting, color permission, and style policy inputs should be separated without breaking current voicing behavior.
