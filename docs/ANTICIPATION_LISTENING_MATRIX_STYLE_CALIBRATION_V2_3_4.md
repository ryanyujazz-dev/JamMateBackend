# v2_3_9 — Anticipation Timing Grid Contract Repair

## Purpose

v2_3_9 closes the first listening-calibration pass after the v2_3_3 anticipation tie repair. The goal is not to create a new anticipation system. The pass keeps the existing pipeline order:

```text
Pattern → Anticipation → Expression → Voicing → Realization
```

and tightens the expression/audit boundary so anticipated 4& pushes sound connected without blurring into the next harmonic attack.

## What changed

### 1. Expression next-event clamp

`ExpressionResolver` now computes the next active event on the same track and applies a final duration clamp after the ordinary region clamp / anticipated-tie duration logic.

This fixes the Bossa case where the current bar's 3& sustain was allowed to keep ringing after a new next-chord anticipation was inserted at 4&.

New metadata:

- `duration_next_event_clamp_version = v2_3_9`
- `duration_next_event_clamp_applied`
- `duration_next_event_clamp_reason`
- `duration_next_event_gap_beats`
- `duration_before_next_event_clamp_beats`

Design rule:

- Ordinary events may sustain up to the next same-track event, but not past it.
- Anticipated events still keep the v2_3_3 tie repair behavior, then are also checked against the next same-track event if one exists.
- This is an expression-layer guard, not a pattern or voicing rewrite.

### 2. Bossa two-beat-region adaptation

The Bossa core batida remains the identity anchor for normal four-beat regions:

```text
1, 2, 3&  short-short-sustain
```

For two-beat harmonic regions, the style now uses a duration-aware adaptation:

```text
half-region: 1, 2
```

This prevents the original `3&` event from being emitted outside a two-beat chord region, which previously produced a near-zero clipped sustain at dense harmonic-rhythm points.

### 3. Anticipation matrix thresholds

`tools/demo_audit_pipeline.py` now validates anticipation as part of the demo matrix:

- expected minimum/maximum anticipation counts per style job
- every inserted anticipation must have expression-layer tie handling
- cross-next-event expression overlap must be zero for calibrated jobs
- expression warning count must be zero for calibrated jobs

Canonical jobs remain small:

- `minimal_swing`
- `misty_ballad_upper_structure_altered`
- `blue_bossa_minor_altered`
- `minor_turnaround_fixture`

## Current calibrated results

From the v2_3_9 demo matrix:

| job | anticipation events | tie expression events | cross-next warnings | expression warnings |
|---|---:|---:|---:|---:|
| minimal_swing | 1 | 1 | 0 | 0 |
| misty_ballad_upper_structure_altered | 18 | 18 | 0 | 0 |
| blue_bossa_minor_altered | 11 | 11 | 0 | 0 |
| minor_turnaround_fixture | 2 | 2 | 0 | 0 |

## Validation

```bash
python -m compileall src tools
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src python -m pytest -q
python tools/check_development_harness.py
PYTHONPATH=src python tools/demo_audit_pipeline.py --fail-on-thresholds
```

Because the full test suite contains many generated-demo tests, it may be run in grouped batches when the execution environment has a hard timeout. The grouped validation used for this pass covered all 731 collected tests.

## Next recommended task

v2_3_9 should focus on **Anticipation Pedal / Release Micro-tuning**:

- Bossa: confirm 4& anticipation release feels clean against the following beat-2 event.
- Ballad: tune pedal/release so 4& approaches feel connected but not smeared.
- Medium Swing: keep 4& push rare and short enough to avoid heavy comping clutter.
