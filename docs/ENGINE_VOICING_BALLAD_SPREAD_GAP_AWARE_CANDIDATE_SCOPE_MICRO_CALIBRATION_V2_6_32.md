# Engine Voicing v2_6_32 — Ballad SPREAD Gap-Aware Candidate-Scope Micro Calibration

## Scope

This is a voicing-only selector micro-calibration on top of the merged `v2_8_24` integration baseline and the `v2_6_31` lower/upper gap audit.

It does not change:

```text
Pattern
Anticipation
Expression
Gesture
MIDI writer
Agent runtime
HarmonyOS API contract
```

## Goal

`v2_6_31` made lower/upper gap outliers visible without changing behavior. The Misty / Jazz Ballad / 3-chorus audit exposed:

```text
2+4 tight gap outliers: 3 events, gap = 1
2+3 wide gap outliers: 2 events, gap = 12
```

`v2_6_32` fixes only the safe, local `2+4` tight-gap outliers by choosing a same-recipe alternative candidate inside the already selected candidate scope.

The pass deliberately avoids a global gap scorer because early experiments showed that a broad gap penalty can collapse the intended `5-note / 6-note ~= 6:4` balance.

## Runtime decision

The micro-calibration is allowed only when all conditions are true:

```text
style policy enables spread_gap_aware_candidate_scope_micro_calibration
selected SPREAD candidate has lower/upper group gap outside 2..7 semitones
replacement candidate uses the same recipe_id
replacement candidate gap is inside 2..7 semitones
replacement top note stays <= 74
replacement primary realization cost is within +3.3 of the original selected candidate
```

This means the pass:

```text
keeps density lane unchanged
keeps recipe scope unchanged
keeps 1+4 as low-frequency color lane
keeps 4-note SPREAD retired
keeps 7-note SPREAD off by default
keeps default unnotated maj7#11 off
```

## Why only the 2+4 tight outliers are fixed here

The three tight `2+4 Abmaj7` events had safe same-recipe replacements:

```text
original gap: 1
replacement gap: 3
same recipe: spread_2plus4_contract
top guard: <= 74
```

The two wide `2+3 Fm7` events remain visible in the audit, but are intentionally deferred. Forcing them in this pass required higher-cost or state-changing replacements and caused downstream density drift in experiments. They should be handled later with a narrower continuity-aware strategy instead of a global gap patch.

## New audit fields

```text
spread_gap_aware_candidate_scope_micro_calibration_version
spread_gap_aware_candidate_scope_micro_calibration_events
spread_gap_aware_candidate_scope_micro_calibration_events_by_recipe
spread_gap_aware_candidate_scope_micro_calibration_events_by_grouping
spread_gap_aware_original_gap_min
spread_gap_aware_original_gap_max
spread_gap_aware_replacement_gap_min
spread_gap_aware_replacement_gap_max
```

Event rows also expose:

```text
spread_gap_aware_candidate_scope_micro_calibration_applied
spread_gap_aware_candidate_scope_micro_calibration_version
spread_gap_aware_original_gap
spread_gap_aware_replacement_gap
spread_gap_aware_original_primary_cost
spread_gap_aware_replacement_primary_cost
spread_gap_aware_same_recipe_only
spread_gap_aware_density_lane_unchanged
```

## Misty / Jazz Ballad / 3 choruses observation

```text
piano events: 196
5-note: 124
6-note: 72
4-note: 0
7-note: 0

functional grouping:
2+3: 114
2+4: 68
1+4: 10
3+3: 4

top_note_max: 72
top_note_ge_75_events: 0
low_note_min: 41
lower_foundation_span_violation_events: 0
```

Lower/upper gap after the micro-calibration:

```text
min: 2
max: 12
average: 5.153

gap by grouping:
2+3: count 114, min 5, max 12, avg 6.123
2+4: count 68,  min 2, max 7,  avg 3.706
1+4: count 10,  min 4, max 4,  avg 4.000
3+3: count 4,   min 5, max 5,  avg 5.000

too tight events (< 2): 0
too wide events (> 7): 2, all in 2+3
```

Micro-calibration applications:

```text
events: 3
by recipe: spread_2plus4_contract = 3
by grouping: 2+4 = 3
original gap: 1
replacement gap: 3
```

## Next recommended task

```text
v2_6_33_engine_ballad_spread_wide_gap_deferred_outlier_strategy
```

Recommended focus:

```text
1. target only the two remaining 2+3 wide-gap Fm7 events
2. avoid broad gap scoring that changes density balance
3. preserve 5-note / 6-note near 6:4
4. preserve 1+4 low frequency
5. preserve top_note_max <= 74
6. do not change Pattern / Anticipation / Expression / Gesture / MIDI
```
