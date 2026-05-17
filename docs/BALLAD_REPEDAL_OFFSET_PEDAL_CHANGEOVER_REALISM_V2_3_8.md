# v2_3_9 — Ballad Re-pedal Offset / Pedal Changeover Realism

## Goal

v2_3_7 connected expression pedal intent to MIDI CC64, but its spans could still behave too mechanically: pedal-down at the same tick as a note attack, then pedal-up exactly at span end. For Jazz Ballad this does not feel like a pianist changing pedal at harmony changes.

v2_3_9 keeps the same boundary principle: pattern, anticipation, expression, voicing, and MIDI realization remain separated. The new behavior is only a MIDI controller realization detail.

## Rule

For Jazz Ballad piano CC64 spans:

```text
previous harmony pedal down
↓
pedal lift before the next harmony
↓
next chord note attack
↓
pedal down shortly after the new attack
```

Default offsets:

- `on_after_attack_beats = 0.02`
- `lift_before_next_onset_beats = 0.035`
- `minimum_gap_beats = 0.02`
- `minimum_span_beats = 0.05`

This models a human-like re-pedal: the new chord is first articulated dry/clear, then the pedal catches it immediately after the attack. The previous harmony is cleared before the next harmony arrives.

## Style boundary

- Jazz Ballad: CC64 `light` / `sustain` may materialize and uses re-pedal offsets.
- Bossa Nova: no CC64 by default.
- Medium Swing: no CC64 by default.

Dry styles must stay dry even if expression metadata carries `light` or `sustain` pedal intent.

## Audit fields

`pedal_realization_audit` now includes:

- `repedal_policy_version`
- `repedal_offset_enabled`
- `repedal_adjusted_span_count`
- `repedal_gap_count`
- `repedal_gap_beats_min`
- `repedal_gap_beats_max`
- `repedal_gap_beats_avg`
- `repedal_warning_count`
- `spans_sample[].raw_start_beat`
- `spans_sample[].cc64_on_beat`
- `spans_sample[].cc64_off_beat`
- `spans_sample[].repedal_gap_before_next`

## Validation

The demo matrix now requires the Ballad job to have realized CC64 spans and re-pedal gaps, while Bossa/Swing must have zero CC64 and zero re-pedal offsets.

Recommended commands:

```bash
python -m compileall src tools
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src python -m pytest -q
python tools/check_development_harness.py
PYTHONPATH=src python tools/demo_audit_pipeline.py --fail-on-thresholds
```

## Next step

Next recommended step: `v2_3_9 — Ballad Pedal Density / Phrase-level Pedal Policy Calibration`, focused on listening to whether Ballad CC64 is too frequent and whether light vs sustain spans need phrase-level thinning.
