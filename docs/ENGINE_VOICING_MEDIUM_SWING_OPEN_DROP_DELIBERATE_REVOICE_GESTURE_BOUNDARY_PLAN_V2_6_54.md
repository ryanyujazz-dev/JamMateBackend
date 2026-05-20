# v2_6_54 — Medium Swing OPEN/DROP Deliberate Revoice Gesture Boundary Plan

## Scope

Engine voicing-only checkpoint on top of `v2_6_53`.

This task does **not** change Pattern, Anticipation, Expression, MIDI, Agent, API, or HarmonyOS behavior. It formalizes the boundary for same-chord fresh voicing inside Medium Swing OPEN/DROP comping.

## Problem

`v2_6_52` correctly established the default contract:

```text
same chord region + same track + no explicit fresh-revoicing flag
→ reuse_cached_region_voicing_exactly
```

The next design question is when a repeated hit inside the same chord region may intentionally revoice. The answer should not be selector randomness. It must be explicit musical intent from a pitchless event or gesture.

## Contract

Default behavior remains:

```text
same_chord_region
→ reuse cached region voicing exactly
```

Fresh same-region voicing is allowed only through:

```text
force_fresh_voicing
revoice_within_region
```

Allowed intent sources:

```text
event_metadata
gesture_metadata
```

Runtime boundary name:

```text
same_chord_region_explicit_gesture_intent
```

## Runtime behavior

When an event requests fresh voicing and there is already a cached voicing for the same region/track/chord, the realizer bypasses the cache and asks the normal core `VoicingResolver` for a new `VoicingPlan`.

The realizer does not construct sources, decide chord tones, project DROP methods, score candidates, change expression, or write MIDI. It only annotates that the cache bypass was intentional.

Metadata attached to the fresh `VoicingPlan` includes:

```text
medium_swing_deliberate_revoice_gesture_boundary_version = v2_6_54
medium_swing_deliberate_revoice_gesture_boundary_applied = true
medium_swing_deliberate_revoice_gesture_boundary_scope = same_chord_region_explicit_gesture_intent
medium_swing_deliberate_revoice_gesture_boundary_escape_hatch
medium_swing_deliberate_revoice_gesture_boundary_source
medium_swing_deliberate_revoice_gesture_boundary_previous_event_id
medium_swing_deliberate_revoice_gesture_boundary_changed_notes
same_chord_reattack_explicit_fresh_revoicing = true
same_chord_reattack_continuity_region_cache_reuse = false
```

## Default demo checkpoint

The current Medium Swing standard-tune demos do not include deliberate revoice gestures, so they should continue to show exact same-region cache reuse.

```text
All The Things You Are / Medium Swing / 3 choruses / seed 3300
- default reuse events: 54
- explicit revoice events: 0
- implicit revoice events: 0
- warning events: 0
- checkpoint passed: true

Autumn Leaves / Medium Swing / 3 choruses / seed 3301
- default reuse events: 61
- explicit revoice events: 0
- implicit revoice events: 0
- warning events: 0
- checkpoint passed: true
```

Accepted phrase for tests and audit:

```text
implicit revoicing events: 0
```

## Targeted probe

A focused unit probe confirms that a `gesture_metadata` request with `revoice_within_region: true` bypasses the cache and marks the selected voicing with the v2_6_54 boundary metadata.

This confirms the boundary is available without changing the default Medium Swing demos.

## Guardrails

Do not use this pass to introduce random same-chord revoicing.

Do not let style patterns decide concrete voicing notes.

Do not move this into Pattern, Anticipation, Expression, MIDI, Agent, API, or HarmonyOS.

Do not rename `force_fresh_voicing` / `revoice_within_region` without compatibility handling.

## Next recommended task

```text
v2_6_55_engine_medium_swing_open_drop_deliberate_revoice_micro_motion_policy_probe
```

That next task should only design a small, explicit musical gesture lane for same-chord revoice, such as inner-motion or top-voice-answer, and should keep default comping reuse unchanged.
