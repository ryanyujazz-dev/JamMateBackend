# v2_6_47 — Engine Medium Swing OPEN Drop-Family Section Boundary Method-Lock Review

## Scope

Behavior-preserving Medium Swing voicing checkpoint on the merged `v2_10_8` baseline plus Engine `v2_6_46`.

This pass does **not** change notes, OPEN method weights, Pattern, Anticipation, Expression, Gesture, MIDI, Agent, API, or HarmonyOS behavior.

The goal is to make section-boundary method-lock readability inspectable before any future Medium Swing voicing tuning.

## Accepted boundary behavior

Medium Swing remains locked to the OPEN family. Section-boundary entries should stay readable:

```text
generic_open = fallback only
drop2        = baseline/body method
drop3        = bridge/final lift and contrast method
drop2&4      = low-frequency phrase-internal color, not boundary entry
```

v2_6_47 therefore audits:

```text
section boundary count
method switches at boundaries
entry methods by contrast role
role-pair transitions
method-pair transitions
DROP2&4 boundary-entry count
boundary top/low/average motion
warning count
checkpoint pass/fail
```

## Reference audit

### All The Things You Are / Medium Swing / 3 choruses

```text
events: 174
methods: drop2=104, drop3=69, drop2_and_4=1
section_boundary_review_events: 11
section_boundary_review_method_switch_events: 8
section_boundary_review_drop2_and_4_entry_events: 0
section_boundary_review_warning_events: 0
section_boundary_review_avg_motion_max: 4.5
section_boundary_review_top_motion_max_abs: 5
section_boundary_review_low_motion_max_abs: 4
section_boundary_review_checkpoint_passed: true
```

Boundary entry methods:

```text
baseline_open_swing: drop2=4, drop3=1
bridge_open_contrast: drop3=3
final_chorus_open_lift: drop3=2, drop2=1
```

### Autumn Leaves / Medium Swing / 3 choruses

```text
events: 223
methods: drop2=87, drop3=103, drop2_and_4=33
section_boundary_review_events: 11
section_boundary_review_method_switch_events: 8
section_boundary_review_drop2_and_4_entry_events: 0
section_boundary_review_warning_events: 0
section_boundary_review_avg_motion_max: 5.25
section_boundary_review_top_motion_max_abs: 2
section_boundary_review_low_motion_max_abs: 5
section_boundary_review_checkpoint_passed: true
```

Boundary entry methods:

```text
baseline_open_swing: drop2=3, drop3=2
bridge_open_contrast: drop3=1, drop2=2
final_chorus_open_lift: drop3=3
```

## Guardrails

```text
boundary_events >= 6
drop2_and_4_entry_events == 0
warning_events == 0
top_motion_max_abs <= 7
low_motion_max_abs <= 8
avg_motion_max <= 6.0
```

This is an audit/checkpoint, not a scorer patch. If a future section-boundary issue appears, first inspect the v2_6_47 boundary fields. Do not solve it by globally changing Medium Swing OPEN weights, re-enabling broad `generic_open`, or switching to CLOSED/SPREAD.

## Validation

```bash
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python tools/check_development_harness.py
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_v2_6_47_engine_medium_swing_open_drop_section_boundary_method_lock_review.py
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_v2_6_46_engine_medium_swing_open_drop_voice_leading_continuity_audit.py tests/test_v2_6_45_engine_medium_swing_open_drop_method_lock_calibration.py
PYTHONPATH=src python examples/scripts/generate_medium_swing_texture_method_audit.py
```

## Recommended next task

```text
v2_6_48_engine_medium_swing_open_drop_phrase_scope_method_continuity_plan
```

Next, inspect phrase-scope method continuity inside sections. Do not adjust global weights unless a concrete phrase-scope readability issue is demonstrated by audit and listening.
