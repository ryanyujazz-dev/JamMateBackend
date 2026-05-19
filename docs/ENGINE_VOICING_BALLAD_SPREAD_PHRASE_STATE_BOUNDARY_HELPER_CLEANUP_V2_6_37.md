# v2_6_37 — Engine Ballad SPREAD Phrase-State Boundary Helper Cleanup

## Scope

This is a voicing-only helper cleanup pass on top of the merged `v2_8_24` integration baseline.

It does not change:

- Pattern
- Anticipation
- Expression
- Gesture
- MIDI writer
- Agent
- API
- HarmonyOS fixtures
- shared integration docs / version files

## Reason

v2_6_35 fixed two Jazz Ballad SPREAD `2+3 Fm7` wide-gap rows by realizing a top-stable same-recipe candidate while advancing later voice-leading from the original phrase anchor. v2_6_36 verified that the immediate `Fm7 → Bb7` boundary stayed continuous.

The mechanism was musically accepted, but the state-advance contract lived as raw metadata keys in both selector and resolver code. v2_6_37 keeps the same audible output and moves the contract into a named helper.

## New helper boundary

Owner:

```text
src/jammate_engine/core/voicing/runtime/state.py
```

Helper:

```text
VoicingStateAdvanceAnchor
```

Responsibility:

```text
realized_notes      = notes used for this event's actual voicing output
state_anchor_notes  = notes used to advance the next event's VoicingState
```

The selector now declares the anchor through the helper. The resolver consumes the helper via a single runtime surface instead of manually checking scattered `voicing_state_advance_override_*` keys.

## Compatibility

v2_6_37 keeps legacy aliases such as:

```text
voicing_state_advance_override_notes
spread_phrase_scope_wide_gap_state_advance_override_notes
```

This preserves existing v2_6_35 / v2_6_36 audit rows and tests while introducing the cleaner helper fields:

```text
voicing_state_advance_anchor_helper_version
voicing_state_advance_anchor_enabled
voicing_state_advance_anchor_notes
voicing_state_advance_anchor_degrees
voicing_state_advance_anchor_reason
```

## Expected Misty guardrails

Misty / Jazz Ballad / 3 choruses should remain behavior-preserving:

```text
5-note: 124
6-note: 72
4-note: 0
7-note: 0
1+4: 10
lower_upper_too_tight_events: 0
lower_upper_too_wide_events: 0
top_note_max: 72
top_note_ge_75_events: 0
```

Helper audit should show:

```text
spread_phrase_state_boundary_helper_cleanup_events: 2
spread_phrase_state_boundary_helper_state_anchor_events: 2
spread_phrase_state_boundary_helper_legacy_alias_match_events: 2
spread_phrase_state_boundary_helper_previous_state_anchor_events: 3
```

## Forbidden follow-up in this pass

Do not generalize the phrase-state mechanism to other styles yet. Do not add a broad gap scorer. Do not change density lanes. Do not change Ballad SPREAD source inventory.

## Recommended next task

```text
v2_6_38_engine_ballad_spread_phrase_state_anchor_generalization_boundary_plan
```

Only after v2_6_37 is stable, decide whether this helper remains a narrow Ballad SPREAD boundary or becomes a general core voicing mechanism with explicit policy gates.
