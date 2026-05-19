# Engine Voicing Ballad SPREAD Phrase-State Boundary Regression Review v2.6.36

## Scope

`v2_6_36_engine_ballad_spread_phrase_state_boundary_regression_and_listening_review` is a **voicing-only audit / regression pass** on top of the merged `v2_8_24` integration baseline and the Engine `v2_6_35` Ballad SPREAD phrase-scope wide-gap candidate availability work.

This pass does **not** generalize the v2_6_35 mechanism; in plain terms, it does not generalize beyond the two known Fm7 rows. It validates the boundary created by realizing a substituted top-stable candidate while advancing `VoicingState` with the original phrase anchor.

Forbidden changes in this pass:

```text
Pattern
Anticipation
Expression
Gesture
MIDI writer
Agent
API contract
HarmonyOS fixtures
shared integration files
```

## Why this pass exists

v2_6_35 fixed two remaining `2+3 Fm7` wide-gap rows by realizing:

```text
[41, 51, 58, 63, 68]
```

while advancing phrase continuity state with the original phrase anchor:

```text
[41, 51, 63, 68, 70]
```

That avoided the earlier density-lane cascade. Before expanding or reusing this idea, the next-event boundary needs an explicit regression review: the following `Bb7` event should read the protected anchor as its previous state, not the realized substitute.

## Implementation

v2.6.36 adds observational audit fields in `piano_audit.py`:

```text
spread_phrase_state_boundary_review_version
spread_phrase_state_boundary_review_events
spread_phrase_state_boundary_review_next_events_found
spread_phrase_state_boundary_review_state_anchor_matches_override_events
spread_phrase_state_boundary_review_realized_notes_not_used_as_state_events
spread_phrase_state_boundary_review_voice_leading_previous_matches_override_events
spread_phrase_state_boundary_review_warning_events
spread_phrase_state_boundary_review_next_event_top_motion_max
spread_phrase_state_boundary_review_next_event_voice_leading_distance_max
spread_phrase_state_boundary_review_next_event_smoothness_labels
```

It also annotates the protected rows and their immediate next rows with row-level boundary review fields, including whether:

```text
next event previous state == protected override notes
next event voice-leading previous notes == protected override notes
realized substitute notes were not used as the next state
next event top motion / voice-leading distance stayed inside the review threshold
```

This is audit-only. It does not change selected candidates, scoring, density routing, state advancement behavior, expression, or MIDI rendering.

## Misty / Jazz Ballad / 3 choruses observation

```text
5-note: 124
6-note: 72
4-note: 0
7-note: 0

2+3: 114
2+4: 68
1+4: 10
3+3: 4

lower_upper_too_tight_events: 0
lower_upper_too_wide_events: 0

spread_phrase_scope_wide_gap_candidate_availability_events: 2
spread_phrase_state_boundary_review_events: 2
spread_phrase_state_boundary_review_next_events_found: 2
spread_phrase_state_boundary_review_state_anchor_matches_override_events: 2
spread_phrase_state_boundary_review_realized_notes_not_used_as_state_events: 2
spread_phrase_state_boundary_review_voice_leading_previous_matches_override_events: 2
spread_phrase_state_boundary_review_warning_events: 0
spread_phrase_state_boundary_review_next_event_top_motion_max: 0.0
spread_phrase_state_boundary_review_next_event_voice_leading_distance_max: 5.333
spread_phrase_state_boundary_review_next_event_smoothness_labels: {"moderate": 2}

top_note_max: 72
top_note_ge_75_events: 0
lower_foundation_span_violation_events: 0
```

## Interpretation

The two protected Fm7 rows now have acceptable realized lower/upper gaps, and the following Bb7 rows still see the protected phrase anchor as their previous state. The next-event boundary shows no top-line discontinuity and no large continuity warning.

This means the v2_6_35 mechanism is safe for the two known Misty rows, but it should still not be generalized automatically. The next step should be a listening review and then, only if needed, a narrow abstraction of this boundary into a named helper with the same guardrails.

## Recommended next task

```text
v2_6_37_engine_ballad_spread_phrase_state_boundary_helper_cleanup
```

Only proceed if the v2_6_36 demo sounds continuous around the two protected Fm7 → Bb7 points. If the listening review reveals a seam, keep the mechanism local and adjust only the candidate availability boundary; do not introduce a broad scorer.
