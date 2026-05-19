# Engine Voicing Ballad SPREAD Wide Gap Deferred Outlier Strategy — v2_6_33

## Scope

`v2_6_33_engine_ballad_spread_wide_gap_deferred_outlier_strategy` is a **voicing-only** pass on top of the merged `v2_8_24` integration baseline and the Engine `v2_6_32` Ballad SPREAD gap-aware calibration.

This pass does **not** modify:

```text
Pattern
Anticipation
Expression
Gesture
MIDI writer
Agent
API
HarmonyOS fixtures
shared integration docs
```

## Problem

After `v2_6_32`, the three `2+4` tight lower/upper gaps were fixed with same-recipe candidate replacement, but two `2+3 Fm7` wide gap outliers remained visible:

```text
notes: 41 51 63 68 70
recipe: spread_2plus3_contract
grouping: 2+3
gap: 12 semitones
```

A same-recipe comfort-band replacement exists, for example:

```text
best replacement gap: 5
top-stable replacement gap: 7
same-recipe candidate count: 13
```

However, enabling runtime replacement for these wide-gap rows causes a downstream density-lane cascade in Misty, moving the Ballad SPREAD balance away from the accepted `5-note / 6-note ~= 6:4` baseline.

## Decision

`v2_6_33` therefore implements a **deferred outlier strategy**, not a broad scorer patch.

The selector now does the following for wide-gap `2+3` candidates:

```text
1. detect the selected wide-gap candidate;
2. search only same-recipe comfort-band alternatives;
3. record the best replacement gap and top-stable replacement gap;
4. keep runtime replacement disabled;
5. preserve the selected notes and keep the density lane unchanged;
6. expose the deferred decision in piano audit rows.
```

This keeps the musical baseline stable while making the remaining problem precise enough for a future source-inventory or phrase-scope solution.

## Why runtime replacement remains disabled

A broad scorer or unrestricted replacement can make the local gap look better while changing later voicing choices. In the current Misty three-chorus run, that experiment collapses the accepted density distribution.

Therefore this version explicitly records:

```text
spread_wide_gap_deferred_runtime_replacement_enabled: false
spread_wide_gap_deferred_not_broad_scorer: true
spread_wide_gap_deferred_reason: runtime_replacement_deferred_to_avoid_density_lane_cascade
```

## Expected Misty / Jazz Ballad / 3-chorus observation

```text
5-note: 124
6-note: 72
4-note: 0
7-note: 0

2+3: 114
2+4: 68
1+4: 10
3+3: 4

top_note_max: 72
top_note_ge_75_events: 0
lower_foundation_span_violation_events: 0

lower_upper_too_tight_events: 0
lower_upper_too_wide_events: 2
```

New audit fields:

```text
spread_wide_gap_deferred_outlier_strategy_version: v2_6_33
spread_wide_gap_deferred_outlier_strategy_events: 2
spread_wide_gap_deferred_outlier_strategy_deferred_events: 2
spread_wide_gap_deferred_outlier_strategy_events_by_recipe: {spread_2plus3_contract: 2}
spread_wide_gap_deferred_outlier_strategy_events_by_grouping: {2+3: 2}
spread_wide_gap_deferred_original_gap_min/max: 12 / 12
spread_wide_gap_deferred_replacement_gap_min/max: 5 / 5
```

## Next recommended task

```text
v2_6_34_engine_ballad_spread_2plus3_wide_gap_source_inventory_plan
```

The next pass should solve the remaining `2+3 Fm7` wide gap at the source inventory / projection option level or phrase-scope continuity level, not by a broad scorer or local runtime swap.
