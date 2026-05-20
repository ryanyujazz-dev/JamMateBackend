# v2_6_45 Engine Medium Swing Open/Drop Method Lock Calibration

Scope: Engine voicing-only pass on the merged `v2_10_8` baseline.

This pass moves the voicing track from the completed Jazz Ballad SPREAD phase into Medium Swing OPEN drop-family calibration. It does not change Pattern, Anticipation, Expression, Gesture, MIDI writer, Agent, API, or HarmonyOS fixtures.

## Goal

Medium Swing should remain in the OPEN family while using named drop-family methods as the normal comping language:

```text
generic_open     fallback / explicit rescue only
drop2            primary baseline OPEN sound
drop3            bridge / final-chorus contrast and lift
drop2_and_4      controlled low-frequency color, not default body
```

The previous merged baseline already had the correct architecture, but the actual Autumn Leaves three-chorus audit let `drop2_and_4` drift slightly above the 20% control line.

## Calibration

Baseline Medium Swing OPEN-method weights are now:

```text
generic_open: 0.00
drop2:        0.52
drop3:        0.38
drop2_and_4: 0.10
```

Bridge contrast keeps DROP3 as the primary contrast method while also controlling DROP2&4:

```text
generic_open: 0.00
drop2:        0.35
drop3:        0.53
drop2_and_4: 0.10
```

Final chorus lift keeps DROP3 above baseline and DROP2&4 lower than baseline:

```text
generic_open: 0.00
drop2:        0.43
drop3:        0.48
drop2_and_4: 0.08
```

## Reference audit

The reference script is still `examples/scripts/generate_medium_swing_texture_method_audit.py`, using:

```text
All the Things You Are / Medium Swing / 3 choruses
Autumn Leaves / Medium Swing / 3 choruses
```

After v2_6_45:

```text
All the Things You Are:
  events: 174
  methods: drop2=104, drop3=69, drop2_and_4=1
  drop2_and_4 ratio: 0.006

Autumn Leaves:
  events: 223
  methods: drop2=87, drop3=103, drop2_and_4=33
  drop2_and_4 ratio: 0.148
```

Both examples preserve:

```text
OPEN family only
all contrast roles present
bridge DROP3 share > baseline DROP3 share
final chorus DROP3 share > baseline DROP3 share
drop2_and_4 total ratio <= 0.20
no failed register guards
no missing piano note events
```

## Boundary

This is a policy/audit calibration pass. It does not add a new selector, does not broaden method switching, and does not reintroduce `generic_open` as ordinary runtime material.

The existing `v2_2_38` texture contract remains the compatibility surface; v2_6_45 adds a narrower accepted calibration profile on top of it.

## Next recommended task

```text
v2_6_46_engine_medium_swing_open_drop_voice_leading_continuity_audit
```

Next, audit the actual voice-leading continuity of the selected DROP2 / DROP3 / DROP2&4 methods, especially at ii–V–I and section boundaries, before changing any more weights.
