# v2_3_9 — Anticipation Pedal / Release Micro-tuning

## Goal

v2_3_9 refines the expression layer after the v2_3_5 timing-grid repair. The timing contract is unchanged: anticipation still moves the next region beat-1 event to the previous written upbeat, and Medium Swing still performs that written upbeat at the swing triplet upbeat. This pass only tunes how the already-moved anticipated chord releases and pedals.

## Core rule

Anticipation has three separate responsibilities:

1. **AnticipationResolver** moves the pitchless beat-1 event to the previous upbeat.
2. **TimingPolicy** interprets that upbeat according to the style grid.
3. **ExpressionResolver** decides the tied duration, release tail, and pedal behavior.

v2_3_9 changes only item 3.

## Style-specific expression behavior

- **Bossa Nova**: anticipated chords stay dry, with a short clean release. A core-short anticipated chord sustains across beat 1 but releases shortly after it, avoiding a blurred 4& → 1 transition.
- **Jazz Ballad**: anticipated chords remain connected, but use `light` pedal metadata rather than full sustain pedal. Long 4& anticipations are softly capped so they do not ring almost the entire next bar unless the next-event clamp requires an earlier release.
- **Medium Swing**: anticipated pushes remain dry and short; their duration uses the performed swing lead-in from v2_3_5 and a short post-downbeat cap.

## New audit fields

`ExpressionResolver` now writes:

- `anticipation_pedal_release_micro_tuning_version`
- `anticipation_pedal_release_micro_tuning_applied`
- `anticipation_pedal_release_micro_tuning_reason`
- `anticipation_original_pedal`
- `anticipation_resolved_pedal`
- `anticipation_original_release_beats`
- `anticipation_resolved_release_beats`
- `duration_anticipation_micro_tuning_version`
- `duration_anticipation_micro_tuning_applied`
- `duration_anticipation_post_downbeat_sustain_cap`

`build_expression_foundation_audit()` now summarizes:

- `anticipation_tie_event_count`
- `anticipation_pedal_release_micro_tuned_count`
- `anticipation_duration_micro_tuned_count`
- `anticipation_pedal_modes`
- `anticipation_avg_release_beats`

The demo matrix validates these signals through:

- `min_anticipation_pedal_release_micro_tuned_events`
- `max_anticipation_sustain_pedal_events`
- `max_anticipation_avg_release_beats`

## Validation

```bash
python -m compileall src tools
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src python -m pytest -q tests/test_v2_3_3_anticipation_tie_sustain.py tests/test_v2_3_4_anticipation_listening_calibration.py tests/test_v2_3_5_anticipation_timing_grid_contract.py tests/test_v2_3_9_anticipation_pedal_release_micro_tuning.py
python tools/check_development_harness.py
PYTHONPATH=src python tools/demo_audit_pipeline.py --fail-on-thresholds
```

## Listening review targets

- Bossa 4& anticipation should connect into beat 1 without smearing over the next hit.
- Ballad 4& anticipation should sound connected, but less over-pedaled than a full-bar sustain.
- Swing pushes should remain rare, dry, and short, while still respecting swing upbeat timing.

## Recommended next step

v2_3_9 should audit whether expression release/pedal metadata should be rendered as actual MIDI CC/pedal events or remain expression-level metadata until a dedicated pedal realizer is introduced.
