# Engine Voicing Ballad SPREAD 2+3 Wide Gap Source Inventory Plan — v2_6_34

## Scope

`v2_6_34_engine_ballad_spread_2plus3_wide_gap_source_inventory_plan` is a **voicing-only source-inventory/audit pass** on top of the merged `v2_8_24` integration baseline and the Engine `v2_6_33` Ballad SPREAD deferred wide-gap strategy.

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

`v2_6_33` proved that the two remaining `2+3 Fm7` wide-gap rows have same-recipe alternatives:

```text
recipe: spread_2plus3_contract
grouping: 2+3
original gap: 12 semitones
best replacement gap: 5 semitones
top-stable replacement gap: 7 semitones
same-recipe candidate count: 13
```

However, direct runtime replacement is still not safe. A controlled experiment that replaced these two rows locally fixed the wide gaps, but caused a density-lane cascade in Misty:

```text
accepted baseline: 5-note:124 / 6-note:72
replacement experiment: 5-note:183 / 6-note:13
```

That violates the accepted Ballad SPREAD density balance, so this version does not turn replacement on.

## Decision

`v2_6_34` keeps the current runtime notes unchanged and formalizes the next solution boundary as:

```text
phrase-scope or source-inventory-level candidate availability,
not selector-level broad scoring,
not local runtime replacement.
```

The selector now records a source-inventory plan for the deferred rows, including:

```text
spread_wide_gap_source_inventory_plan_version: v2_6_34
spread_wide_gap_source_inventory_plan_active: true
spread_wide_gap_source_inventory_plan_scope: 2plus3_same_recipe_upper_source_inventory_audit_only
spread_wide_gap_source_inventory_candidate_count
spread_wide_gap_source_inventory_comfort_candidate_count
spread_wide_gap_source_inventory_best_replacement_gap
spread_wide_gap_source_inventory_top_stable_replacement_gap
spread_wide_gap_source_inventory_original_upper_source_degrees
spread_wide_gap_source_inventory_best_replacement_upper_source_degrees
spread_wide_gap_source_inventory_top_stable_upper_source_degrees
spread_wide_gap_source_inventory_runtime_replacement_enabled: false
spread_wide_gap_source_inventory_recommended_next_boundary
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
spread_wide_gap_source_inventory_plan_events: 2
spread_wide_gap_source_inventory_runtime_replacement_enabled_events: 0
```

## Why this is still useful

This pass turns the remaining problem from a vague gap defect into a precise inventory decision:

```text
Original selected row:
  lower: root + b7
  upper source: b3 + b7 + 11
  realized upper placement: b7 / b3 / 11
  gap: 12

Best same-recipe replacement:
  upper source: b3 + b7 + 9
  gap: 5

Top-stable same-recipe replacement:
  upper source: b3 + b7 + 11
  gap: 7
```

The next implementation should therefore happen before the selected note becomes the current state for later events. It should be phrase-scope or inventory-level, so the whole local passage can remain density-stable instead of letting a single replacement cascade through later choices.

## Next recommended task

```text
v2_6_35_engine_ballad_spread_phrase_scope_wide_gap_candidate_availability
```

The next pass should test a phrase-scope or source-inventory availability rule for these `2+3 Fm7` rows while explicitly preserving:

```text
5-note / 6-note ~= 6:4
1+4 low frequency
4-note = 0
7-note = 0
maj7#11 default = 0
top_note_max <= 74
```
