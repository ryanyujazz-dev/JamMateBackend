# Engine Voicing v2_6_55 — Medium Swing OPEN/DROP Deliberate Revoice Micro-Motion Policy Probe

## Scope

`v2_6_55` stays inside the Engine voicing track. It does not change Pattern, Anticipation, Expression, MIDI writer, Agent, API, HarmonyOS fixtures, shared VERSION, README, or shared architecture/API docs.

This checkpoint follows `v2_6_54`, where same-chord comping reattack was made explicit-intent only:

```text
same chord region + same track + no explicit fresh-revoicing flag
→ reuse cached region voicing exactly
```

`v2_6_55` adds a narrow probe for what happens **after** a gesture explicitly requests fresh same-region voicing. It does not create such gestures by itself.

## New policy boundary

The new policy is named:

```text
medium_swing_deliberate_revoice_micro_motion_policy_version = v2_6_55
```

Runtime scope:

```text
same_chord_region_explicit_revoice_micro_motion
```

Allowed explicit motion policies:

```text
micro_motion
inner_motion
top_voice_answer
```

Default thresholds:

```text
foundation stable: required
max_low_motion:    0 semitones
max_top_motion:    2 semitones
max_avg_motion:    2.5 semitones
```

The policy is only activated when the pitchless event or gesture already contains an explicit fresh-revoicing escape hatch, such as:

```text
revoice_within_region: true
force_fresh_voicing: true
```

and may optionally provide:

```text
revoice_motion_policy: micro_motion
```

## Behavior

Default Medium Swing comping remains unchanged; this preserves default same-chord reuse:

```text
default repeated same-chord hit
→ reuse cached region voicing exactly
```

Explicit same-region fresh revoicing now gains a safe micro-motion filter:

```text
explicit revoice request
→ pass cached region notes into VoicingPolicy metadata
→ generate normal candidates
→ keep only candidates with stable foundation and small top/average motion
→ if none are safe, keep full pool and record fallback reason
```

The fallback is intentional. This policy must not force a bad voicing just to satisfy a gesture label.

## Why this is not a broad revoice system

This checkpoint does not decide when to revoice. It only defines the safe candidate boundary if a future FillGesture / OrnamentGesture / CompingGesture explicitly asks for same-chord revoice.

It remains separate from:

```text
Pattern       # does not create revoice timing here
Anticipation  # does not move or suppress events here
Expression    # does not decide touch/duration/pedal here
MIDI writer   # does not repair voicing here
Agent/API     # no contract change here
```

## Audit expectations

For default standard-tune demos, the micro-motion policy should remain inactive:

```text
runtime_enabled_events: 0
filter_applied_events: 0
warning_events: 0
```

Targeted unit probes verify that when explicit revoice is requested, the candidate filter keeps only safe micro-motion candidates.

## Validation songs

```text
All The Things You Are / Medium Swing / 3 choruses
Autumn Leaves / Medium Swing / 3 choruses
```

## Recommended next task

`v2_6_56_engine_medium_swing_deliberate_revoice_gesture_inventory_plan`

Recommended focus: design a very small inventory of explicit same-chord revoice gestures, such as top-voice answer or inner-motion answer, without allowing random selector revoicing and without mixing gesture timing into voicing selection.
