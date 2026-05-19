# Engine Voicing v2_6_31 — Ballad SPREAD Lower/Upper Gap & Weight Balance

## Scope

This is a voicing-only pass on top of the merged `v2_8_24` integration baseline.

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

`v2_6_30` restored low-frequency `1+4` and added lower foundation register audit.  
`v2_6_31` adds an explicit lower/upper gap and weight balance audit so the next listening pass can distinguish:

```text
2+4 occasionally too tight / too pasted to the upper block
2+3 occasional wide split
1+4 remaining a low-frequency color lane
5-note / 6-note still near 6:4
```

## Runtime decision

This pass intentionally keeps the `v2_6_30` density lane unchanged.

```text
5-note / 6-note target: preserve ~6:4
4-note SPREAD: still retired
7-note SPREAD: still off by default
1+4: still low-frequency only
maj7#11: still not part of default warm Ballad safe extension
```

The pass adds audit and guardrail metadata instead of applying a scorer patch that would accidentally erase the current density balance.

## New audit fields

```text
lower_upper_gap_audit_version
lower_upper_gap_comfort_min
lower_upper_gap_comfort_max
lower_upper_group_gap_min
lower_upper_group_gap_max
lower_upper_group_gap_average
lower_upper_group_gap_by_grouping
lower_upper_group_gap_by_density
lower_upper_group_gap_by_recipe
lower_upper_group_gap_too_tight_events
lower_upper_group_gap_too_tight_events_by_grouping
lower_upper_group_gap_too_wide_events
lower_upper_group_gap_too_wide_events_by_grouping
```

Comfort band for this audit:

```text
2 <= lower/upper gap <= 7 semitones
```

This is observational. It does not reselect notes.

## Misty / Jazz Ballad / 3 choruses observation

```text
piano events: 196
5-note: 120
6-note: 76
4-note: 0
7-note: 0

functional grouping:
2+3: 110
2+4: 72
1+4: 10
3+3: 4

top_note_max: 72
top_note_ge_75_events: 0
lower_foundation_span_violation_events: 0
```

Lower/upper gap:

```text
min: 1
max: 12
average: 5.061

gap by grouping:
2+3: count 110, min 5, max 12, avg 6.164
2+4: count 72, min 1, max 7,  avg 3.528
1+4: count 10, min 4, max 4,  avg 4.000
3+3: count 4,  min 5, max 5,  avg 5.000

too tight events (< 2): 3, all in 2+4
too wide events (> 7): 2, all in 2+3
```

## Why this is not a behavior retune yet

A naive gap scorer can fix the two wide `2+3` events or the three tight `2+4` events, but it can also collapse the intended `5-note:6-note ~= 6:4` balance by making `2+3` dominate the candidate pool.

So `v2_6_31` deliberately makes the issue measurable first and keeps the existing musical lane stable.

## Next recommended task

```text
v2_6_32_engine_ballad_spread_gap_aware_candidate_scope_micro_calibration
```

Recommended focus:

```text
1. fix only the sparse 2+3 wide-gap outliers
2. fix only the sparse 2+4 tight-gap outliers
3. preserve 5/6-note ≈ 6:4
4. preserve 1+4 ≈ 4-10 events
5. preserve top_note_max <= 74
6. do not change Pattern / Anticipation / Expression / MIDI
```
