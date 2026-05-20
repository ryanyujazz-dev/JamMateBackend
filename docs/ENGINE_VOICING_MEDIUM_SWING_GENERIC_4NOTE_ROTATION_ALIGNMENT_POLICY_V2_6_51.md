# v2_6_51 Engine Voicing — Medium Swing Generic 4-Note Rotation Alignment Policy

## Goal

Generalize the previous rootless-only A/B orientation alignment into a generic four-note rotation alignment mechanism for Medium Swing local functional progressions.

## Boundary

This is Engine voicing-only work. It does not modify Agent, API, HarmonyOS fixtures, pattern selection, anticipation, expression, pedal, or MIDI writer logic.

## Main correction

v2_6_50 correctly introduced local follow-region orientation alignment, but it only recognized `rootless_ab_*` metadata. v2_6_51 corrects that scope so rooted/basic four-note closed rotations also participate.

```text
basic_4note:        1357 / 3571 / 5713 / 7135
rooted_color_4note: rooted color rotations
rootless_ab:        existing A/B rootless vocabulary
```

## Runtime rule

Within the existing v2_6_49 local method-lock scope, the selected seed voicing carries generic `four_note_rotation_*` metadata forward to the follow region.

For rooted/basic four-note sources:

```text
1357 -> 5713
3571 -> 7135
5713 -> 1357
7135 -> 3571
```

For rootless A/B sources:

```text
A -> B
B -> A
```

## Smoothness guard

The generic rooted/basic hard filter only applies when a matching candidate is also voice-leading safe. If every matching candidate would create a large register jump, the full candidate pool is preserved and audit records:

```text
matching_four_note_rotation_candidates_fail_smoothness_guard
```

This keeps ABA as an idiomatic preference without sacrificing voice-leading continuity.

## Validation

- compileall: passed
- harness: HARNESS OK
- focused v2_6_44 through v2_6_51 regression: 29 passed
- integration today-guidance smoke: 3 passed
- Medium Swing All The Things You Are and Autumn Leaves demo/audit: passed

## Next recommended task

`v2_6_52_engine_medium_swing_open_drop_same_chord_reattack_and_comping_reuse`
