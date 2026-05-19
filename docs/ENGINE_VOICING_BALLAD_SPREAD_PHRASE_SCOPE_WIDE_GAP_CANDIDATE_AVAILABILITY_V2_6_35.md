# Engine Voicing Ballad SPREAD Phrase-Scope Wide Gap Candidate Availability — v2_6_35

## Scope

`v2_6_35_engine_ballad_spread_phrase_scope_wide_gap_candidate_availability` is a **voicing-only phrase-scope candidate availability pass** on top of the merged `v2_8_24` integration baseline and the Engine `v2_6_34` Ballad SPREAD source-inventory plan.

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

`v2_6_34` showed that the two remaining `2+3 Fm7` wide-gap rows have viable same-recipe alternatives, but direct local replacement caused a density-lane cascade:

```text
accepted baseline: 5-note:124 / 6-note:72
unsafe replacement experiment: 5-note:183 / 6-note:13
```

The root cause is not lack of notes. It is state advancement: if the local replacement becomes the next `VoicingState` anchor, later groupwise selection gets pulled toward the same 2+3 texture and the Ballad SPREAD density balance collapses.

## Decision

`v2_6_35` uses a narrow phrase-scope availability boundary:

```text
realize the top-stable same-recipe candidate for the current wide-gap event
advance voicing continuity state with the original phrase anchor
keep density lane guarded
avoid broad scorer changes
avoid pattern / expression / MIDI changes
```

This is intentionally narrower than a general scorer. It applies only to the existing `spread_2plus3_contract` wide-gap case that already had v2_6_34 source-inventory evidence.

## Runtime behavior

For each of the two Fm7 rows:

```text
original realized notes: 41, 51, 63, 68, 70
original gap: 12

v2_6_35 realized notes: 41, 51, 58, 63, 68
realized gap: 7

state-advance override notes: 41, 51, 63, 68, 70
```

The realized voicing fixes the audible wide gap while the state-advance override preserves the phrase-level density route.

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
lower_upper_too_wide_events: 0
spread_phrase_scope_wide_gap_candidate_availability_events: 2
spread_phrase_scope_wide_gap_state_advance_protected_events: 2
spread_phrase_scope_wide_gap_runtime_realization_enabled_events: 2
```

## Audit metadata

The selected rows expose:

```text
spread_phrase_scope_wide_gap_candidate_availability_version: v2_6_35
spread_phrase_scope_wide_gap_candidate_availability_applied: true
spread_phrase_scope_wide_gap_candidate_availability_scope
spread_phrase_scope_wide_gap_original_gap
spread_phrase_scope_wide_gap_realized_gap
spread_phrase_scope_wide_gap_original_notes
spread_phrase_scope_wide_gap_realized_notes
spread_phrase_scope_wide_gap_state_advance_protected: true
spread_phrase_scope_wide_gap_state_advance_override_enabled: true
spread_phrase_scope_wide_gap_state_advance_override_notes
spread_phrase_scope_wide_gap_not_broad_scorer: true
spread_phrase_scope_wide_gap_same_recipe_only: true
spread_phrase_scope_wide_gap_density_lane_guarded: true
spread_phrase_scope_wide_gap_runtime_realization_enabled: true
```

## Next recommended task

```text
v2_6_36_engine_ballad_spread_phrase_state_boundary_regression_and_listening_review
```

Next pass should be mostly validation/listening: confirm the state-advance protected realization does not create audible discontinuity at the following event, before generalizing this mechanism beyond the two known Fm7 rows.
