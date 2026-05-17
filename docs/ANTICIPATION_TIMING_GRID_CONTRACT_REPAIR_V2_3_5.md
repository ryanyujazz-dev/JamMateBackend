# v2_3_9 — Anticipation Timing Grid Contract Repair

## Problem

v2_3_3/v2_3_4 correctly repaired anticipation tie sustain and next-event overlap, but the repair still treated the anticipation lead-in too much like a universal straight eighth. That is musically wrong for Medium Swing:

- The pitchless timeline may still represent the written upbeat as `.5`.
- But Medium Swing must perform that written upbeat through the swing timing grid, i.e. beat + `2/3`.
- Therefore a beat-1 anticipation moved to the previous written 4& has:
  - logical lead-in: `0.5` beat
  - performed lead-in: `1/3` beat

The engine must keep these two ideas separate.

## Repair

### 1. AnticipationPolicy now carries timing-grid contract fields

`AnticipationPolicy` keeps `target_offset_beats=-0.5` as the logical written-upbeat move, and adds:

- `timing_grid`
- `target_timing_intent`
- `performed_lead_in_beats`
- `expected_upbeat_fraction`

Style defaults:

| Style | Logical target | Timing intent | Performed upbeat | Performed lead-in |
|---|---:|---|---:|---:|
| Medium Swing | `-0.5` | `swing_upbeat` | `2/3` | `1/3` |
| Bossa Nova | `-0.5` | `straight_even` | `1/2` | `1/2` |
| Jazz Ballad | `-0.5` | `straight_even` | `1/2` | `1/2` |

### 2. AnticipationResolver writes explicit timing metadata

Every inserted anticipation now stores:

- `timing_intent`
- `anticipation.timing_grid_contract_version = v2_3_9`
- `anticipation.logical_lead_in_beats`
- `anticipation.performed_lead_in_beats`
- `anticipation.expected_performed_onset_beat`
- `anticipation.expected_upbeat_fraction`

For Medium Swing this means the event remains logically at written `4&` (`.5`) but realizes through `timing_intent=swing_upbeat`.

### 3. Expression tie duration uses performed lead-in

`ExpressionResolver` now prefers `anticipation.performed_lead_in_beats` when computing tie sustain:

```text
realized_duration = performed_lead_in + original_source_duration_inside_source_region
```

That prevents a Medium Swing anticipation from sustaining as though the lead-in were a straight half beat.

### 4. Demo/audit matrix validates timing-grid placement

`tools/demo_audit_pipeline.py` now records and validates anticipation timing placement:

- `anticipation_timing_grid_events`
- `anticipation_timing_grid_failures`
- `anticipation_timing_grid_error_max`
- `anticipation_timing_grid_samples`

Medium Swing matrix jobs now fail if written 4& does not perform at the swing 2/3 upbeat.

## Validation

```bash
python -m compileall src tools
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src python -m pytest -q tests/test_v2_3_9_anticipation_timing_grid_contract.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src python -m pytest -q tests/test_anticipation_resolver.py tests/test_v2_3_3_anticipation_tie_sustain.py tests/test_v2_3_4_anticipation_listening_calibration.py tests/test_v2_3_9_anticipation_timing_grid_contract.py
PYTHONPATH=src python tools/demo_audit_pipeline.py --fail-on-thresholds
python tools/check_development_harness.py
```

Additional segmented full-suite verification used in this delivery:

```bash
# Group 1
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src python -m pytest -q <all tests except the late voicing/demo group>
# 656 passed

# Group 2
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src python -m pytest -q <late voicing/demo group>
# 78 passed
```

Combined segmented coverage: `734 passed`.

## Next recommended task

`v2_3_9 — Anticipation Pedal / Release Micro-tuning` can now safely tune release and pedal, because the timing-grid contract is restored first.
