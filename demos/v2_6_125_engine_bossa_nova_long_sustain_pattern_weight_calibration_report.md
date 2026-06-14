# v2_6_125 — Engine Bossa Nova Long-Sustain Pattern Weight Calibration

## Scope

Reduce slightly excessive Bossa long-sustain feeling through style-owned piano comping pattern weights only. No voicing, source inventory, OPEN/SPREAD routing, generic_open fallback, expression numeric profile, bass/drums, API, Agent, or HarmonyOS logic is changed.

## Pattern weight calibration

| Pattern | Weight |
|---|---:|
| A_1 sparse hold | 108.0 |
| A_1_3& long-gap hold | 198.0 |
| A_1_3 square hold | 56.0 |
| A_1_2& split cell | 216.0 |
| A_1_2_3& split/core-like ordinary cell | 236.0 |

## Blue Bossa runtime audit

- MIDI: `demos/v2_6_125_blue_bossa_bossa_nova_long_sustain_pattern_weight_demo.mid`
- Piano harmonic events: 98
- `A_1_3&` count delta vs v2_6_124: -6
- `A_1` count delta vs v2_6_124: -3
- `A_1_2&` count delta vs v2_6_124: 10
- Extreme long duration events (>= 3 beats): 12
- 5-note SPREAD 1+4 selected: 4
- OPEN 5-note selected: 0
- generic_open selected: 0
- Core batida front velocities: [48, 48, 48, 48]

## Pattern counts

```json
{
  "bossa_piano_core_batida_1_2_3and": 21,
  "bossa_piano_cell_A_1_3and": 22,
  "bossa_piano_cell_A_1_3": 8,
  "bossa_piano_cell_A_1_2and": 20,
  "bossa_piano_cell_A_1": 10,
  "bossa_piano_cell_B_1and_3and": 2,
  "bossa_piano_half_region_1_2": 6,
  "bossa_piano_half_region_1and_hold": 3,
  "bossa_piano_cell_A_1_2_3and": 6
}
```

## Acceptance

```json
{
  "passed": true,
  "checks": {
    "pattern_weight_only_boundary_declared": true,
    "long_hold_base_weights_reduced": true,
    "shorter_split_cells_lifted": true,
    "runtime_reduces_sparse_long_hold_cells": true,
    "runtime_lifts_shorter_split_cell": true,
    "runtime_reduces_extreme_long_duration_events": true,
    "voicing_route_unchanged": true,
    "core_batida_velocity_48_retained": true
  }
}
```
