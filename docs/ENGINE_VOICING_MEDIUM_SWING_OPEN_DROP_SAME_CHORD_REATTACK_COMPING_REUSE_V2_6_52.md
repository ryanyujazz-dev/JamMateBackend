# v2_6_52 — Engine Medium Swing OPEN / DROP Same-Chord Reattack / Comping Reuse

## Scope

This is an Engine voicing-only checkpoint on top of `v2_6_51_engine_medium_swing_generic_4note_rotation_alignment_policy`.

It does not change Pattern, Anticipation, Expression, Gesture note realization, MIDI writer, Agent, API, HarmonyOS fixtures, shared VERSION, or shared integration docs.

## Goal

Medium Swing OPEN / DROP comping often has more than one piano touch inside the same chord region. Those repeated hits should not accidentally re-run the selector and jump to a different voicing. The default behavior should be:

```text
one-default-voicing-per-chord-region
reuse cached region voicing on repeated same-chord comping hits
fresh revoicing only when explicitly requested
```

The explicit fresh-revoicing escape hatches remain:

```text
force_fresh_voicing
revoice_within_region
```

## Implementation decision

No new selector, scorer, source router, projection method, or pattern rule was added.

The project already has the correct boundary in `RealizerVoicingRequestOrchestrator`:

```text
region_voicing_cache_key = (region_id, chord_symbol, track)
event_requests_fresh_voicing(event) gates fresh revoicing
reuse_region_voicing(...) attaches reuse metadata
```

v2_6_52 therefore formalizes Medium Swing consumption of this existing cache boundary and adds a Medium Swing audit alias over the generic same-chord continuity fields.

## Runtime contract

```text
same chord region + same track + no explicit fresh-revoicing flag
↓
reuse cached region voicing exactly
```

This means repeated Medium Swing comping hits keep:

```text
same midi note set
same lower/foundation notes
same OPEN/DROP projection method
same density lane
same selected voicing source
```

Future deliberate same-chord movement should use an explicit gesture or fresh-revoicing flag, not accidental selector churn.

## Audit fields

The existing generic same-chord fields remain:

```text
same_chord_reattack_regions_reviewed
same_chord_reattack_events
same_chord_reattack_region_voicing_reused_events
same_chord_reattack_exact_voicing_reuse_events
same_chord_reattack_foundation_stable_events
same_chord_reattack_fresh_revoicing_events
same_chord_reattack_changed_voicing_warning_events
same_chord_reattack_continuity_warning_events
same_chord_reattack_continuity_checkpoint_passed
```

v2_6_52 adds Medium Swing naming aliases:

```text
medium_swing_same_chord_reattack_comping_reuse_version
medium_swing_same_chord_reattack_comping_reuse_events
medium_swing_same_chord_reattack_comping_reuse_region_voicing_reused_events
medium_swing_same_chord_reattack_comping_reuse_exact_voicing_reuse_events
medium_swing_same_chord_reattack_comping_reuse_foundation_stable_events
medium_swing_same_chord_reattack_comping_reuse_fresh_revoicing_events
medium_swing_same_chord_reattack_comping_reuse_warning_events
medium_swing_same_chord_reattack_comping_reuse_checkpoint_passed
```

## Accepted demo checkpoints

### All The Things You Are / Medium Swing / 3 choruses

```text
same_chord_reattack_comping_reuse_events: 54
region_voicing_reused_events: 54
exact_voicing_reuse_events: 54
foundation_stable_events: 54
fresh_revoicing_events: 0
warning_events: 0
checkpoint_passed: true
```

### Autumn Leaves / Medium Swing / 3 choruses

```text
same_chord_reattack_comping_reuse_events: 61
region_voicing_reused_events: 61
exact_voicing_reuse_events: 61
foundation_stable_events: 61
fresh_revoicing_events: 0
warning_events: 0
checkpoint_passed: true
```

## Relationship to v2_6_49 / v2_6_51

v2_6_49 and v2_6_51 operate across adjacent chord regions:

```text
ii–V / V–I method lock
4-note rotation alignment
```

v2_6_52 operates inside one chord region:

```text
same-chord repeated comping hits reuse the already selected region voicing
```

These are complementary scopes:

```text
local progression scope: choose a coherent next voicing
same region scope: do not rechoose unless explicitly requested
```

## Guardrails

Do not use this checkpoint to suppress musical fills or inner movement. If a future style needs deliberate same-chord movement, it should declare a clear gesture/fresh-revoicing policy and remain auditable.

This checkpoint does not modify:

```text
Pattern
Anticipation
Expression
MIDI
Agent
HarmonyOS
```

## Recommended next task

```text
v2_6_53_engine_medium_swing_open_drop_safe_extension_and_top_register_checkpoint
```

Focus: keep Medium Swing OPEN / DROP voicings in the accepted top-register band while checking that harmonic expansion / chart color does not make the comping too sharp or high.
