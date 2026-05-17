# Ballad SPREAD Grouping Mix Gap Tightening — v2_2_80 (superseded)


> Superseded by `v2_2_81 — Ballad SPREAD Texture-State + Set-Based Voice Leading`.
> The `spread_lower_1note_target_low = 53` lower-lift workaround documented here is no longer the active direction. v2_2_81 keeps the lower foundation natural and solves the gap through texture-state grouping plus set-based full-candidate voice-leading.

## Version

```text
v2_2_80 — Ballad SPREAD Grouping Mix No-1+3 Gap Tightening
```

## Scope

This pass only tightens the Ballad SPREAD grouping mix dry-run / audit path. It does **not** enable the mix policy in the default Jazz Ballad runtime and does not change pattern or expression layers.

## Problem Found

In the v2_2_79 no-1+3 mix demo, measures such as Misty bar 11, bar 15, and bar 24 exposed a large audible hole between the lower/foundation group and upper/projection group.

The root cause was not the 2+3 / 2+4 / 3+3 / 3+4 contracts. Those already have stricter lower-upper gap behavior. The main source was 1+4:

```text
1+4 = one low root + upper DROP2/DROP3 4-note block
```

When the single lower root stayed too low while the upper block stayed in the mid-high register, the lower-top to upper-bottom gap could reach roughly 16–23 semitones.

## Design Decision

1+4 remains an active Ballad SPREAD grouping, but in the Ballad SPREAD mix context its single lower root should sit closer to the upper block.

This is implemented as a policy-driven 1-note lower target, not a hardcoded global root register change.

```text
spread_lower_1note_target_low = 53
spread_target_group_gap = 7
spread_comfort_group_gap_max = 12
```

The lower root can still remain the only lower/foundation note, but it is selected in a register that prevents a large empty hole.

## Code Changes

### 1. SPREAD register policy

`SpreadProjectionRegisterPolicy` now includes:

```text
lower_1note_target_low
```

For `spread_1plus4_contract`, `_lower_group_register_window()` uses this 1-note target. Other grouped SPREAD contracts continue using their own lower-register policies.

### 2. Group-gap selection cost

The selector now adds a soft current-gap cost for SPREAD candidates:

```text
spread_target_group_gap
spread_comfort_group_gap_max
spread_large_group_gap_penalty
spread_group_gap_target_penalty
```

This prevents the selector from preferring a smooth-but-hollow voicing where the lower and upper groups are too far apart.

### 3. Audit extension

The dry-run audit now reports:

```text
max_group_gap_semitones
large_group_gap_gt12_events
group_gap_distribution
```

## v2_2_81 Audit Result

Reference demo:

```text
events = 150
1+3 = 0
1+4 = 48
2+3 = 30
2+4 = 45
3+3 = 17
3+4 = 10
max_group_gap_semitones = 12
large_group_gap_gt12_events = 0
fallback_non_spread_events = 0
source_integrity_rejected_events = 0
DROP2&4 = 0
```

Expanded 60% demo:

```text
events = 150
1+3 = 0
1+4 = 48
2+3 = 30
2+4 = 45
3+3 = 17
3+4 = 10
actual_color_upper_events = 92
max_group_gap_semitones = 12
large_group_gap_gt12_events = 0
fallback_non_spread_events = 0
source_integrity_rejected_events = 0
DROP2&4 = 0
```

## Validation

```text
compileall: OK
pytest: 672 passed
harness: HARNESS OK
```

## Next Suggested Step

Listen to the new no-1+3 gap-tightened reference and expanded 60% demos. If the lower-upper spacing now feels natural, the next development step should be:

```text
v2_2_81 — Ballad SPREAD Grouping Mix Listening Tuning
```

Focus of that step:

```text
1. Fine-tune 1+4 / 2+3 / 2+4 / 3+3 / 3+4 weights.
2. Adjust scene boundaries between normal_comping / chorus_lift / ending_climax.
3. Keep 3+4 as a low-frequency climax texture.
4. Still keep default Jazz Ballad runtime unchanged until the listening pilot is approved.
```
