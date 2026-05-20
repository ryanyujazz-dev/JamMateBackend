# v2_6_46 — Engine Medium Swing OPEN Drop-Family Voice-Leading Continuity Audit

## Scope

Engine voicing-only checkpoint on top of the merged `v2_10_8` baseline plus `v2_6_45` Medium Swing OPEN drop-family method calibration.

This pass is behavior-preserving. It does not change selected notes, method weights, Pattern, Anticipation, Expression, Gesture, MIDI, Agent, API, HarmonyOS fixtures, or shared integration contracts.

## Why this pass exists

`v2_6_45` stabilized the OPEN method mix:

```text
DROP2      = baseline body
DROP3      = bridge / final-chorus lift
DROP2&4    = controlled low-frequency color
GENERIC    = fallback/rescue only
```

Before changing weights again, the next risk to audit is whether actual method switches and section boundaries stay smooth in rendered standard-tune output. This pass turns that listening concern into an explicit piano-audit checkpoint.

## Added audit contract

The piano audit now exposes:

```text
medium_swing_open_drop_voice_leading_continuity_version
medium_swing_open_drop_voice_leading_continuity_transition_events
medium_swing_open_drop_voice_leading_continuity_method_switch_events
medium_swing_open_drop_voice_leading_continuity_section_boundary_events
medium_swing_open_drop_voice_leading_continuity_warning_events
medium_swing_open_drop_voice_leading_continuity_method_switch_warning_events
medium_swing_open_drop_voice_leading_continuity_section_boundary_warning_events
medium_swing_open_drop_voice_leading_continuity_top_motion_max_abs
medium_swing_open_drop_voice_leading_continuity_low_motion_max_abs
medium_swing_open_drop_voice_leading_continuity_avg_motion_max
medium_swing_open_drop_voice_leading_continuity_avg_motion_average
medium_swing_open_drop_voice_leading_continuity_span_jump_max_abs
medium_swing_open_drop_voice_leading_continuity_method_switches
medium_swing_open_drop_voice_leading_continuity_checkpoint_passed
```

The audit excludes same-region reattacks because those are already covered by the cached-region same-chord reattack audit. It only checks cross-region OPEN drop-family transitions.

## Current acceptance thresholds

```text
top_motion_max_abs <= 7
low_motion_max_abs <= 8
avg_motion_max <= 6.0
span_jump_max_abs <= 8
warning_events == 0
```

These thresholds are observational guardrails, not selector scoring rules.

## Reference demo results

### All The Things You Are / Medium Swing / 3 choruses

```text
events: 174
methods: drop2=104, drop3=69, drop2_and_4=1
cross-region transitions: 119
method-switch transitions: 51
section-boundary transitions: 11
warning events: 0
method-switch warning events: 0
section-boundary warning events: 0
top_motion_max_abs: 5
low_motion_max_abs: 7
avg_motion_max: 5.25
avg_motion_average: 1.807
span_jump_max_abs: 5
checkpoint_passed: true
```

### Autumn Leaves / Medium Swing / 3 choruses

```text
events: 223
methods: drop2=87, drop3=103, drop2_and_4=33
cross-region transitions: 161
method-switch transitions: 68
section-boundary transitions: 11
warning events: 0
method-switch warning events: 0
section-boundary warning events: 0
top_motion_max_abs: 5
low_motion_max_abs: 7
avg_motion_max: 5.25
avg_motion_average: 1.582
span_jump_max_abs: 5
checkpoint_passed: true
```

## Interpretation

The current Medium Swing OPEN method mix is not causing obvious cross-region voice-leading discontinuities in the two reference standards. `DROP3` contrast and rare `DROP2&4` color remain inside the current motion guardrails.

Future Medium Swing voicing work should not solve perceived issues by broadly re-enabling `generic_open` or random family switching. If a listening issue appears, first locate it through this continuity audit and then decide whether the fix belongs to method weights, phrase-scope method lock, register rescue, or source inventory.

## Verification

```bash
PYTHONPATH=src python -m compileall -q src tests examples/scripts
PYTHONPATH=src python tools/check_development_harness.py
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_v2_6_46_engine_medium_swing_open_drop_voice_leading_continuity_audit.py
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_v2_6_45_engine_medium_swing_open_drop_method_lock_calibration.py
PYTHONPATH=src python examples/scripts/generate_medium_swing_texture_method_audit.py
```

## Recommended next task

```text
v2_6_47_engine_medium_swing_open_drop_section_boundary_method_lock_review
```

Focus only on section boundary method lock/readability if listening reveals a problem. Do not change method weights broadly unless the audit points to a specific failure mode.
