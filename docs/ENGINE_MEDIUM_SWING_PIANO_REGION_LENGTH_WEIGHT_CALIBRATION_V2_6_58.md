# v2_6_58 — Engine Medium Swing Piano Region-Length Weight Calibration

## Scope

This task calibrates the existing Medium Swing piano `ChordRegion`-first, region-length-aware comping vocabulary.

It does **not** add a parallel pattern source, a bar-first selector, a two-chord-bar path, voicing logic, expression parameter realization, MIDI duration/velocity values, or gesture/revoice behavior.

Implementation remains in:

```text
src/jammate_engine/styles/medium_swing/comping_patterns.py
src/jammate_engine/styles/medium_swing/arrangement_policy.py
tests/test_v2_6_58_engine_medium_swing_piano_region_length_weight_calibration.py
```

## Versions

```text
PATTERN_LIBRARY_VERSION = v2_6_56
CANDIDATE_LOOKUP_POLICY_VERSION = v2_6_57
WEIGHT_CALIBRATION_POLICY_VERSION = v2_6_58
```

The library version remains `v2_6_56` because this task does not replace the vocabulary baseline. The lookup policy remains `v2_6_57` because routing is still region-length-aware. v2_6_58 only calibrates the weights inside that existing source.

## Musical intent

Medium Swing piano comping should be sparse and interactive:

```text
stable cells primary
offbeat conversation secondary
active cells controlled
native tail-push / 4& cells rare
short regions conservative and anchor-led
```

## Calibrated candidate-weight ratios

```text
4-beat region:
  stable:    ~73.6%
  offbeat:   ~22.6%
  active:    ~3.4%
  tail_push: ~0.3%

2-beat region:
  stable:    ~87.8%
  offbeat:   ~12.2%

1-beat region:
  stable:    ~99.0%
  offbeat:   ~1.0%
  rest_if_covered: 0.0% inactive
```

## Key changes

- Reduced Charleston dominance so `1,2&` remains a core cell but no longer overwhelms the pool.
- Raised `1,3` and other stable support cells so stable comping is not only downbeat-plus-answer.
- Activated offbeat conversation at a controlled secondary level (`1&,3`, `2&,4`, `2,3&`).
- Kept `1,2&,4` as a low active color rather than a frequent busy pattern.
- Kept native `4&` tail-push cells extremely rare.
- Made 2-beat region selection more anchor-led so dense harmonic rhythm does not overproduce short-region offbeats.

## Runtime audit

Generated and audited:

```text
All The Things You Are / Medium Swing / 3 choruses
Autumn Leaves / Medium Swing / 3 choruses
```

Key results:

```text
All The Things You Are:
  piano_events: 204
  stable/offbeat/active: 68.6% / 27.0% / 4.4%
  tail_push_events: 0
  top_note_max: 72
  voice_leading_warning_events: 0

Autumn Leaves:
  piano_events: 224
  stable/offbeat/active: 77.2% / 22.8% / 0.0%
  tail_push_events: 0
  top_note_max: 72
  voice_leading_warning_events: 0
```

## Validation

```bash
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python tools/check_development_harness.py
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_v2_6_58_engine_medium_swing_piano_region_length_weight_calibration.py
```

Focused regression was also run across v2_6_44 through v2_6_58 plus Medium Swing pattern organization tests and the current integration smoke.

## Next recommended task

```text
v2_6_59_engine_medium_swing_piano_comping_history_continuity_scorer
```

The next step should not add more rhythm cells. It should add a lightweight history/continuity scorer so Medium Swing piano avoids exact repeat, repeated family, consecutive offbeat, consecutive active, and repeated tail-push behavior over a short region history window.
