# v2_6_30 Engine Voicing — Ballad SPREAD 1+4 / Lower Foundation Calibration

## Scope

This is a voicing-only listening calibration pass after `v2_6_29_engine_voicing_drop_projection_audit_counts`.

It changes only Ballad SPREAD voicing policy / grouped-SPREAD selection calibration and piano audit diagnostics. It does not change Pattern, Anticipation, Expression, Gesture, MIDI writer, Agent, API, HarmonyOS fixtures, VERSION, README, or shared integration docs.

## Goal

Restore `1+4` as a low-frequency Jazz Ballad SPREAD lane while keeping the established Ballad voicing guardrails:

```text
5-note / 6-note remains near 6:4
4-note SPREAD remains 0
7-note SPREAD remains 0 in the default Misty seed
maj7#11 remains absent unless charted or explicitly requested
upper/top register does not return to the previous sharp high ceiling
```

At the same time, expose lower foundation register/thickness diagnostics so future tuning can be based on audit data instead of patching by ear only.

## 1+4 role

`1+4` is not restored as a high-frequency default comping body. It is a low-frequency upper4 color lane inside the 5-note SPREAD lane.

Target for the current Misty / Jazz Ballad / 3-chorus seed:

```text
1+4 events: 4 to 10 per 196 piano audit events
```

The normal 5-note body remains `2+3`; `1+4` only replaces a small number of those 5-note events. It should not noticeably reduce the 6-note lane.

## Grouping policy

Current Ballad SPREAD runtime contract ids:

```text
spread_1plus4_contract
spread_2plus3_contract
spread_2plus4_contract
spread_3plus3_contract
```

Current grouping behavior target:

```text
2+3 remains the main 5-note body
1+4 enters only as a low-frequency 5-note lane
2+4 remains the main 6-note body
3+3 remains a low-frequency 6-note thickness lane
legacy 4-note 1+3 / 2+2 SPREAD remain retired
```

Zero-weight behavior remains strict: if `spread_1plus4_contract` has weight 0 in a scene, it must not leak back into the compatible neighbor pool.

## Lower foundation audit

`src/jammate_engine/generation/piano_audit.py` now exposes:

```text
lower_foundation_audit_version = v2_6_30
lower_foundation_note_min
lower_foundation_note_max
lower_foundation_note_average
lower_foundation_span_max
lower_foundation_span_average
lower_foundation_notes_by_grouping
lower_foundation_notes_by_density
lower_foundation_spans_by_grouping
lower_foundation_spans_by_density
lower_foundation_recipe_counts
lower_foundation_low_register_events
lower_foundation_low_register_events_by_grouping
lower_foundation_low_register_events_by_density
lower_foundation_span_violation_events
```

This audit reads selected voicing metadata only. It does not feed back into runtime selection.

## Lower foundation guardrail

Lower/foundation groups should remain compact:

```text
lower group max span: 12 semitones
low-register density remains guarded
below the low-register threshold, avoid multiple dense lower notes
```

The v2_6_30 pass also tightens current 3-note lower recipes so the lower group stays within one octave instead of allowing wide 15-16 semitone lower blocks.

## Expected Misty / Jazz Ballad / 3 choruses audit

Expected seed: `26912`.

```text
piano_audit_events: 196

5-note: 120
6-note: 76
4-note: 0
7-note: 0

functional_groupings:
  2+3: 110
  2+4: 72
  1+4: 10
  3+3: 4

maj7#11 events: 0
top_note_max: <= 74
low_note_min: 41
```

Drop projection audit remains active and now observes the restored 5-note `1+4` upper drop usage:

```text
spread_upper_projection_methods:
  closed_upper_stack: 114
  drop3: 72
  drop2: 10

spread_upper_drop_projection_methods_by_density:
  6:
    drop3: 62
    drop2: 10
  5:
    drop3: 10

spread_upper_drop_projection_methods_by_grouping:
  2+4:
    drop3: 62
    drop2: 10
  1+4:
    drop3: 10
```

Lower foundation audit target:

```text
lower_foundation_note_min: 41
lower_foundation_note_max: 58
lower_foundation_span_max: <= 12
lower_foundation_span_violation_events: 0
lower_foundation_low_register_events: <= 30
```

## Boundary

Allowed implementation surface:

```text
src/jammate_engine/core/voicing/
src/jammate_engine/styles/jazz_ballad/voicing_policy.py
src/jammate_engine/generation/piano_audit.py
tests/test_v2_6_30_engine_ballad_spread_1plus4_lower_foundation_calibration.py
```

Do not use this pass to retune pedal, anticipation, pattern rhythm, MIDI timing, or agent guidance.

## Validation

Recommended focused validation:

```bash
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python tools/check_development_harness.py
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_v2_6_30_engine_ballad_spread_1plus4_lower_foundation_calibration.py \
  tests/test_v2_6_29_engine_voicing_drop_projection_audit_counts.py \
  tests/test_v2_6_28_engine_ballad_spread_top_voice_register_micro_calibration.py \
  tests/test_v2_6_27_engine_ballad_spread_listening_calibration.py
```

## Recommended next task

```text
v2_6_31_engine_ballad_spread_lower_upper_gap_and_weight_balance
```

Continue by listening to lower/upper gap and lower foundation weight balance with the new audit fields, without changing density lanes again unless the audit and listening result both require it.
