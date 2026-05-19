# v2_6_29 Engine Voicing — Drop Projection Audit Counts

## Scope

This is a voicing-only audit/diagnostics pass after `v2_6_28_engine_ballad_spread_top_voice_and_register_micro_calibration`.

It does not change Ballad SPREAD density, source selection, color permission, projection, register, Pattern, Anticipation, Expression, Gesture, MIDI writer, Agent, API, HarmonyOS fixtures, VERSION, README, or shared integration docs.

The goal is to make drop usage auditable in both ordinary OPEN voicings and grouped SPREAD voicings.

## Why this pass is needed

A normal top-level OPEN voicing can expose its method through the main voicing projection metadata, for example `drop2`, `drop3`, or `drop2_and_4`.

Grouped SPREAD is different:

```text
SPREAD whole voicing
  lower/foundation group
  upper/projection group
```

For 5-note / 6-note / 7-note SPREAD contracts, the whole voicing is still `disposition = spread`, but the upper group may internally reuse a drop-family projection resource.

Therefore audit must count both:

```text
main_voicing drop methods
spread_upper_group drop methods
```

Otherwise `2+4`, `3+4`, and future `1+4` upper blocks can hide DROP2 / DROP3 usage inside the upper group.

## New audit fields

`src/jammate_engine/generation/piano_audit.py` now exposes:

```text
drop_projection_audit_version = v2_6_29

drop_projection_methods_total
  total drop methods across all counted scopes

drop_projection_methods_by_scope
  main_voicing
  spread_upper_group

spread_upper_projection_methods
  all SPREAD upper projection methods, including closed_upper_stack

spread_upper_drop_projection_methods
  only SPREAD upper methods that are actual drop-family resources

spread_upper_drop_projection_events
  sum of SPREAD upper drop events

spread_upper_drop_projection_methods_by_density
  includes 5-note / 6-note / 7-note buckets when their upper group uses drop

spread_upper_drop_projection_methods_by_grouping
  e.g. 1+4, 2+4, 3+4

spread_upper_drop_projection_methods_by_recipe
  e.g. spread_2plus4_contract

spread_upper_drop_projection_events_by_density
  compact event counts per density bucket
```

## Boundary

This pass only reads existing debug metadata:

```text
voicing.metadata.upper_projection_method
voicing.metadata.upper_projection_metadata.open_named_projection_method
voicing.metadata.upper_projection_metadata.open_drop2_projection
voicing.metadata.upper_projection_metadata.open_drop3_projection
voicing.metadata.upper_projection_metadata.open_drop2_and_4_projection
```

It does not feed audit results back into runtime selection.

## Expected Misty / Jazz Ballad / 3 choruses audit

The v2_6_28 musical output should stay unchanged:

```text
5-note: 115
6-note: 81
4-note: 0
7-note: 0
1+4: 0
maj7#11 events: 0
top_note_max: 74
```

The new drop audit should show the current upper-group usage:

```text
spread_upper_projection_methods:
  closed_upper_stack: 120
  drop2: 12
  drop3: 64

spread_upper_drop_projection_methods:
  drop2: 12
  drop3: 64

spread_upper_drop_projection_methods_by_density:
  6:
    drop2: 12
    drop3: 64

spread_upper_drop_projection_methods_by_grouping:
  2+4:
    drop2: 12
    drop3: 64
```

There are no 5-note upper-drop events in the current ordinary Ballad runtime because `1+4` remains disabled by default. The audit still supports 5-note upper-drop counting for explicit `1+4` / future upper4 lanes.

## Validation

Recommended focused validation:

```bash
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python tools/check_development_harness.py
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_v2_6_29_engine_voicing_drop_projection_audit_counts.py \
  tests/test_v2_6_28_engine_ballad_spread_top_voice_register_micro_calibration.py \
  tests/test_v2_6_27_engine_ballad_spread_listening_calibration.py
```

## Recommended next task

```text
v2_6_30_engine_ballad_spread_lower_foundation_register_micro_calibration
```

After audit visibility is complete, continue with lower foundation register listening calibration without mixing it with density, top register, or drop-projection diagnostics.
