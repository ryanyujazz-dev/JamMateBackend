# v2_6_41 — Engine Ballad SPREAD Same-Chord Reattack Continuity Calibration

## Scope

This is an Engine voicing-only checkpoint on top of `v2_6_40_engine_ballad_spread_phrase_state_anchor_policy_boundary`.

It does not change Pattern, Anticipation, Expression, Gesture realization, MIDI writing, Agent, API, HarmonyOS fixtures, or shared integration contracts.

## Musical intent

Jazz Ballad SPREAD repeated touches inside the same chord region should normally reuse the same selected voicing. The repeated touch may be a light retouch, answer, whisper, or projection-group reattack, but the lower/foundation group should remain stable unless the event explicitly requests fresh revoicing for a fill or deliberate movement.

This keeps the piano part from sounding like every retouch is a new chord choice while still allowing higher-level movement/fill gestures later.

## Runtime boundary

The existing realizer boundary already owns the correct behavior:

```text
one default voicing selection per chord region
reuse cached voicing for later events in the same region
fresh revoicing only through explicit escape hatch
```

v2_6_41 does not add a new selector or scorer. It formalizes and audits this boundary.

## Audit contract

`build_piano_musical_audit()` now reports:

```text
ballad_spread_same_chord_reattack_continuity_version
same_chord_reattack_regions_reviewed
same_chord_reattack_events
same_chord_reattack_region_voicing_reused_events
same_chord_reattack_exact_voicing_reuse_events
same_chord_reattack_foundation_stable_events
same_chord_reattack_projection_or_retouch_events
same_chord_reattack_fresh_revoicing_events
same_chord_reattack_changed_voicing_warning_events
same_chord_reattack_continuity_warning_events
same_chord_reattack_continuity_checkpoint_passed
```

Each repeated row also records its anchor event, whether the cached voicing was reused, whether the full voicing and lower/foundation group remained stable, and whether any warning was raised.

## Accepted Misty checkpoint

For Misty / Jazz Ballad / 3 choruses with seed `26912`:

```text
same_chord_reattack_regions_reviewed: 46
same_chord_reattack_events: 46
same_chord_reattack_region_voicing_reused_events: 46
same_chord_reattack_exact_voicing_reuse_events: 46
same_chord_reattack_foundation_stable_events: 46
same_chord_reattack_projection_or_retouch_events: 46
same_chord_reattack_fresh_revoicing_events: 0
same_chord_reattack_changed_voicing_warning_events: 0
same_chord_reattack_continuity_warning_events: 0
same_chord_reattack_continuity_checkpoint_passed: true
```

The previous Ballad SPREAD guardrails stay unchanged:

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
top_note_max: 72
```

## Next recommendation

Proceed to `v2_6_42_engine_ballad_spread_safe_extension_frequency_calibration` after listening confirms the same-chord retouch behavior feels stable. That next task should tune harmonic color frequency, not density lanes.
