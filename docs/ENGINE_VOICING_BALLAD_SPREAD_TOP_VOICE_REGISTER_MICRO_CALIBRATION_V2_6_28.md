# v2_6_28 Engine Voicing — Ballad SPREAD Top Voice / Register Micro Calibration

## Scope

This is a voicing-only listening calibration pass after `v2_6_27_engine_ballad_spread_listening_calibration_pass`.

It does not change density lane, does not change Pattern, Anticipation, Expression, Gesture, MIDI writer, Agent, API, HarmonyOS fixtures, VERSION, README, or shared integration docs.

The goal is intentionally narrow: keep the current Ballad SPREAD density lane stable while preventing the opening / isolated no-previous-state SPREAD selection from choosing the highest legal upper projection too easily.

## Starting audit

`v2_6_27` was already structurally stable:

```text
5-note:6-note ~= 58.7:41.3
4-note SPREAD = 0
1+4 ordinary runtime events = 0
maj7#11 = 0
max top note = 77, only at the opening Ebmaj7 events
large top jumps = 0
```

The issue was not a global register drift. The only audible risk was the first Ballad SPREAD voicing starting at the top ceiling before top-line continuity had any previous state to compare against.

## Calibration decision

v2_6_28 adds a narrow SPREAD top-register micro bias inside grouped SPREAD realization collapse:

```text
spread_top_register_micro_calibration_enabled = true
spread_top_register_micro_soft_high = 74
spread_top_register_micro_hard_high = 76
spread_top_register_micro_average_soft_high = 66
```

This is a selector-side notes-only cost among already-legal SPREAD candidates. It does not construct source degrees, does not route content family, does not decide color permission, does not project closed/open/spread notes, and does not write MIDI.

## What remains unchanged

```text
ordinary runtime groupings:
  2+3  stable 5-note body
  2+4  fuller 6-note support
  3+3  fuller 6-note support / lift

still not ordinary default:
  1+4  explicit upper4 color lane only

unchanged guardrails:
  4-note SPREAD remains 0
  5-note:6-note remains near 6:4
  maj7#11 remains 0 by default
```

## Expected Misty / Jazz Ballad / 3 choruses audit

```text
5-note: 115
6-note: 81
4-note: 0
7-note: 0
1+4: 0
max top note: 74
top >= 75 events: 0
max average pitch: <= 62
maj7#11 events: 0
```

## Code boundaries

Changed owners:

```text
core/voicing/selection/selector.py
  adds SPREAD_TOP_REGISTER_MICRO_CALIBRATION_VERSION
  adds a narrow grouped-SPREAD top-register micro cost/profile

styles/jazz_ballad/voicing_policy.py
  enables the v2_6_28 micro calibration through metadata only
```

Still forbidden:

```text
no source construction in selector
no color permission change
no density-lane change
no projection rewrite
no Pattern / Anticipation / Expression / Gesture / MIDI changes
```

## Validation

Recommended focused validation:

```bash
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python tools/check_development_harness.py
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_v2_6_28_engine_ballad_spread_top_voice_register_micro_calibration.py \
  tests/test_v2_6_27_engine_ballad_spread_listening_calibration.py \
  tests/test_v2_6_26_engine_voicing_realization_surface_final_cleanup.py
```

## Recommended next task

```text
v2_6_29_engine_ballad_spread_lower_foundation_register_micro_calibration
```

After top voice is controlled, the next listening pass can inspect lower foundation placement: whether the repeated low-note range around C#2–F2 feels warm or occasionally too heavy, without mixing that decision with top-register or density-lane tuning.
