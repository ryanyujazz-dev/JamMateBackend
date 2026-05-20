# v2_6_68 — Engine Medium Swing ExpressionPolicy V1 Numeric Calibration

## Scope

This pass calibrates Medium Swing piano comping expression numbers from the V1 reference ranges recorded in the v2_6_64 idiom audit.
It is an ExpressionPolicy-only change.

```text
Pattern semantic hint
→ style-owned ExpressionProfile default values
→ core ExpressionResolver duration/next-touch/region-boundary guards
→ voicing/realization later
```

No pattern candidate, voicing policy, MIDI writer, Agent, API, or HarmonyOS behavior was moved or rewritten.

## V1 reference ranges absorbed

The V1 audit provided these touch ranges:

```text
soft_hold     velocity 48-59, duration ticks 84-140
light_stab    velocity 48-65, duration ticks 62-88
accent_stab   velocity 60-70, duration ticks 58-72
backbeat_hold velocity 51-64, duration ticks 76-108
final_hold    velocity 44-45, duration ticks 220-240
```

v2_6_68 records `v1_reference_ticks_per_beat = 120` in the style expression policy metadata and stores each profile's reference velocity/duration ranges in profile metadata.

## Calibrated profile defaults

```text
comp_medium       soft_hold      velocity 54, duration 0.95
comp_short        light_stab     velocity 56, duration 0.62
comp_accent       accent_stab    velocity 66, duration 0.54
comp_backbeat_hold backbeat_hold velocity 58, duration 0.78
comp_accent_hold  accent+hold    velocity 64, duration 0.78
comp_final_hold   final_hold     velocity 45, duration 1.92
```

Hold-style profiles still declare:

```text
duration_semantics = hold_until_next_touch
```

Therefore their fixed profile durations are fallback/default expression values, not permission to ring through a later ChordRegion.
The v2_6_66 boundary guard remains the hard rule:

```text
hold_until_next_touch = min(next same-track touch, current ChordRegion end)
```

## Boundary

Patterns still carry only semantic hints such as:

```text
soft_hold
light_stab
accent_stab
accent_hold
backbeat_hold
final_hold
```

Patterns still do not write:

```text
velocity
duration
duration_beats
release_beats
pedal
accent
midi_note
```

## Files changed

```text
src/jammate_engine/styles/medium_swing/expression_policy.py
src/jammate_engine/styles/medium_swing/arrangement_policy.py
tests/test_v2_6_68_engine_medium_swing_expression_policy_v1_numeric_calibration.py
examples/scripts/generate_medium_swing_expression_policy_v1_numeric_calibration_audit.py
docs/ENGINE_MEDIUM_SWING_EXPRESSION_POLICY_V1_NUMERIC_CALIBRATION_V2_6_68.md
docs/CHANGELOG_ENGINE.md
```

## Validation

Focused tests:

```bash
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_v2_6_68_engine_medium_swing_expression_policy_v1_numeric_calibration.py
```

Regression slice:

```bash
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_v2_6_63_engine_medium_swing_piano_expression_hint_handoff_checkpoint.py \
  tests/test_v2_6_66_engine_medium_swing_no_4and_delayed_tail_idiom_reinforcement.py \
  tests/test_v2_6_67_engine_medium_swing_active_fill_busy_multi_region_history_scorer.py \
  tests/test_v2_6_68_engine_medium_swing_expression_policy_v1_numeric_calibration.py
```

Demo/audit:

```bash
PYTHONPATH=src python examples/scripts/generate_medium_swing_expression_policy_v1_numeric_calibration_audit.py
```

## Recommended next task

`v2_6_69_engine_medium_swing_piano_standard_tune_listening_checkpoint`

This should be a listening/audit checkpoint over the current Medium Swing piano line before adding ending-specific subsets or more fill vocabulary.
