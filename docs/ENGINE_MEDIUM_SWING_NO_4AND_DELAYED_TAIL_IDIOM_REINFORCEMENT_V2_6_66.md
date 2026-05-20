# v2_6_66 — Engine Medium Swing No-4& Delayed-Tail Idiom + Hold Boundary Guard

## Scope

This milestone continues the Medium Swing piano pattern line without creating a parallel selector or restoring V1 bar-first templates.

It does two things:

1. Fixes the `hold_until_next_touch` duration semantics so hold-style piano events never sustain current-region harmony into a later ChordRegion.
2. Reinforces the V1-derived no-4& / delayed-tail idiom as conservative ChordRegion-first candidate reweighting.

No voicing, gesture, MIDI writer, Agent, API, HarmonyOS, or final pattern-level expression values are changed.

## Hold boundary guard

Previous v2_6_63 semantics made hold-style events last until the next same-track piano touch. That was musically wrong when the next piano touch happened inside a later ChordRegion: the current chord could sustain across a harmony change.

v2_6_66 changes the core expression rule to:

```text
hold_until_next_touch = min(next same-track touch, current ChordRegion end)
```

If there is no later touch inside the same region, the event releases at the current region end. This keeps the user's intended hold feel while preserving harmonic boundaries.

Audit metadata now includes:

```text
duration_next_touch_hold_version = v2_6_66
duration_next_touch_hold_reason
  - held_until_next_same_track_touch_within_region
  - next_same_track_touch_beyond_region_clamped_to_region_end
  - no_next_same_track_touch_held_to_region_end
```

## No-4& / delayed-tail policy

V1's Medium Swing piano comping did not delete 4& pickup/tail-push material; it kept those as rare lifts and gave delayed/tail/no-4& shapes a small idiomatic preference.

v2_6_66 translates that into the existing V2 region-first pipeline:

```text
ChordRegion-length candidate pool
→ progression-specific preferred subset
→ no-4& / delayed-tail reweighting
→ harmonic-function multiplier
→ history scorer
→ weighted sampling
```

The policy:

- modestly boosts region-local delayed/tail/backbeat candidates;
- downweights native 4& tail-push candidates;
- keeps 4& available as rare lift;
- never introduces a bar-level template route;
- never selects voicing or final expression values.

## Files changed

```text
src/jammate_engine/core/expression/expression_resolver.py
src/jammate_engine/styles/base.py
src/jammate_engine/styles/medium_swing/arrangement_policy.py
src/jammate_engine/styles/medium_swing/comping_patterns.py
tests/test_v2_6_63_engine_medium_swing_piano_expression_hint_handoff_checkpoint.py
tests/test_v2_6_66_engine_medium_swing_no_4and_delayed_tail_idiom_reinforcement.py
examples/scripts/generate_medium_swing_piano_no_4and_delayed_tail_audit.py
docs/ENGINE_MEDIUM_SWING_NO_4AND_DELAYED_TAIL_IDIOM_REINFORCEMENT_V2_6_66.md
```

## Runtime audit summary

All The Things You Are / Medium Swing / 3 choruses:

```text
piano_events: 210
no_4and_policy_applied_events: 210
no_4and_preferred_events: 49
tail_push_rare_downweighted_events: 3
hold_until_next_touch_applied_events: 145
hold_cross_region_boundary_guard_events: 23
top_note_max: 72
voice_leading_warning_events: 0
```

Autumn Leaves / Medium Swing / 3 choruses:

```text
piano_events: 227
no_4and_policy_applied_events: 227
no_4and_preferred_events: 54
tail_push_rare_downweighted_events: 0
hold_until_next_touch_applied_events: 147
hold_cross_region_boundary_guard_events: 35
top_note_max: 73
voice_leading_warning_events: 0
```

## Verification

```text
compileall: passed
harness: HARNESS OK
v2_6_44 ~ v2_6_49: 21 passed
v2_6_50 ~ v2_6_66: 71 passed
integration smoke: 3 passed
demo/audit generation: ok
```

## Recommended next task

```text
v2_6_67_engine_medium_swing_active_fill_busy_multi_region_history_scorer
```

Focus next on V1-derived active/fill/busy memory, but keep it as multi-region history scoring rather than a bar-first phrase system.
