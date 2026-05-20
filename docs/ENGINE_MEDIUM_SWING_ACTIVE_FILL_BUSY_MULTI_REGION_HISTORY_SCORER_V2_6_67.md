# v2_6_67 — Engine Medium Swing Active/Fill/Busy Multi-Region History Scorer

## Scope

This pass upgrades the existing Medium Swing piano comping history scorer in place.
It does not add a parallel selector, restore bar-first/two-chord-bar templates, or move voicing/expression work into the pattern layer.

```text
ChordRegion-length candidate pool
→ progression-specific preferred subset
→ no-4& / delayed-tail reweighting
→ harmonic-function multiplier
→ v2_6_67 multi-region history scorer
→ weighted sampling
```

## What changed

`src/jammate_engine/styles/base.py` now keeps the existing v2_6_59 compatibility metadata and adds:

```text
medium_swing_active_fill_busy_history_policy_version = v2_6_67
active_fill_busy_multi_region_history_policy_version = v2_6_67
```

The scorer now records and scores a six-region recent comping window:

```text
recent_active_count
recent_fill_count
recent_busy_count
recent_push_count
recent_tail_push_count
recent_offbeat_count
```

The selected candidate history now stores semantic flags:

```text
activity_class
is_active
is_fill
is_busy
is_push
is_tail_push
is_offbeat
is_no_4and_delayed_tail
```

## Musical policy

The policy translates the V1 idiom lesson into V2-native metadata scoring:

```text
active after active                  → medium penalty
recent active cluster                → additional multi-region penalty
fill after fill                      → strong penalty
fill outside phrase/section context  → downweight
busy after busy                      → near block
recent busy                          → near block
busy after active/fill               → strong penalty
busy outside high-energy/phrase end  → near block
push after push                      → strong penalty
tail-push after recent tail-push     → very strong penalty
stable after active/fill/busy        → reset bonus
no-4& delayed-tail after recent push → recovery bonus
```

## Boundary

The scorer only rewrites candidate weights and audit metadata before normal weighted sampling.
It does not write:

```text
midi_note
velocity
duration
pedal
voicing method
```

Pattern remains pitchless and ChordRegion-local.

## Files changed

```text
src/jammate_engine/styles/base.py
src/jammate_engine/styles/medium_swing/arrangement_policy.py
tests/test_v2_6_67_engine_medium_swing_active_fill_busy_multi_region_history_scorer.py
examples/scripts/generate_medium_swing_piano_active_fill_busy_history_audit.py
docs/ENGINE_MEDIUM_SWING_ACTIVE_FILL_BUSY_MULTI_REGION_HISTORY_SCORER_V2_6_67.md
docs/CHANGELOG_ENGINE.md
```

## Validation

Focused tests:

```bash
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_v2_6_67_engine_medium_swing_active_fill_busy_multi_region_history_scorer.py
```

Regression slice:

```bash
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_v2_6_59_engine_medium_swing_piano_comping_history_continuity_scorer.py \
  tests/test_v2_6_66_engine_medium_swing_no_4and_delayed_tail_idiom_reinforcement.py \
  tests/test_v2_6_67_engine_medium_swing_active_fill_busy_multi_region_history_scorer.py
```

Demo/audit:

```bash
PYTHONPATH=src python examples/scripts/generate_medium_swing_piano_active_fill_busy_history_audit.py
```

## Recommended next task

`v2_6_68_engine_medium_swing_expression_policy_v1_numeric_calibration`

This should calibrate ExpressionPolicy numeric ranges from the V1 report, while keeping pattern files semantic-only.
