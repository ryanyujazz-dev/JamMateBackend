# Ballad SPREAD Grouping Mix Policy Draft + 1+3 Removal — v2_2_79

## Scope

This pass updates the explicit, default-off Ballad SPREAD grouping mix policy after listening review: `1+3` is no longer an active Ballad SPREAD grouping option.

The change is intentionally policy-level and runtime-safe:

- no new voicing system;
- no pattern / expression / pedal changes;
- no default Jazz Ballad runtime activation;
- no change to Medium Swing or Bossa;
- no change to the already accepted `3+4` color/rootless/register contract.

## Active Ballad SPREAD grouping set

Active grouping mix options are now:

```text
1+4
2+3
2+4
3+3
3+4
```

Deprecated from active Ballad SPREAD entry/mix:

```text
1+3
```

The old `spread_1plus3_contract` remains in the low-level historical isolation contract so old regression/audit tests can still inspect it, but it is not part of active Ballad SPREAD entry or grouping mix selection.

## Architecture boundary

The policy still only decides which existing SPREAD contract should be requested for a given chord-region event:

- `spread_1plus4_contract`
- `spread_2plus3_contract`
- `spread_2plus4_contract`
- `spread_3plus3_contract`
- `spread_3plus4_contract`

It does not create notes directly, does not own rhythm, and does not own expression. Runtime activation still requires explicit override metadata:

```text
ballad_spread_grouping_mix_policy.enabled = true
style_runtime_default_enabled = false
runtime_enabled = false
```

## Scene policy

The draft keeps three scenes:

```text
normal_comping
chorus_lift
ending_climax
```

Default weights after removing `1+3`:

```text
normal_comping:
  1+4: 40
  2+3: 25
  2+4: 30
  3+3: 5
  3+4: 0

chorus_lift:
  1+4: 30
  2+3: 20
  2+4: 30
  3+3: 15
  3+4: 5

ending_climax:
  1+4: 10
  2+3: 5
  2+4: 25
  3+3: 25
  3+4: 35
```

The final weighted choice uses a stable deterministic slot based on chorus/bar/chord index rather than Python's process-dependent hash. This keeps demos repeatable and gives the dry-run a representative spread across small scene samples.

## Guard preservation

`1+4` remains the lightest active SPREAD option after removing `1+3`. The P5 lower-to-upper gap guard remains reserved for the rooted lower `2+3` / `2+4` / `3+3` / `3+4` style of grouping; `1+4` uses the wider default SPREAD gap.

## 3+4 contract preservation

The mix policy preserves the 3+4 constraints:

```text
whole register: A1–G5
root anchor: A1–C3
root target: Eb2 / MIDI39
upper 4-note: color-only
seventh-family upper: rootless color
DROP2 / DROP3 only
DROP2&4 forbidden
source integrity gate preserved
```

## Expected audit invariants

All mix demos must satisfy:

```text
1+3 selected events: 0
fallback_non_spread_events: 0
source_integrity_rejected_events: 0
drop2_and_4_events: 0
whole_register_violations: 0
3+4 upper root degree events: 0
```


## Actual v2_2_81 demo audit summary

Reference demo:

```text
events: 150
1+3: 0
1+4: 48
2+3: 30
2+4: 45
3+3: 17
3+4: 10
fallback_non_spread_events: 0
source_integrity_rejected_events: 0
drop2_and_4_events: 0
whole_register_violations: 0
3+4 upper root degree events: 0
```

Expanded-60% demo:

```text
events: 150
1+3: 0
1+4: 48
2+3: 30
2+4: 45
3+3: 17
3+4: 10
actual_color_upper_events: 92
fallback_non_spread_events: 0
source_integrity_rejected_events: 0
drop2_and_4_events: 0
whole_register_violations: 0
3+4 upper root degree events: 0
```

## Next recommended task

Listen to the two mix demos. If the distribution feels reasonable without `1+3`, the next step should be `v2_2_81 — Ballad SPREAD Grouping Mix Listening Tuning`, focused on musical weights and scene boundaries rather than architecture.
