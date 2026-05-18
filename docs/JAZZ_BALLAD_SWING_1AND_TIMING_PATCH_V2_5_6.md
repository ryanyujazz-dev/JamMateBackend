# v2_5_6 — Jazz Ballad Swing 1& Timing Patch

This pass corrects the narrow v2_5_5 Ballad `1&` patch.

## Problem

v2_5_5 changed the affected Jazz Ballad two-beat soft-mark candidates from `beat 1 + beat 2` to logical `beat 1 + beat 1&` by using local beats `0.0, 0.5`. That fixed the written rhythmic cell, but because the Jazz Ballad profile currently has `timing_policy.feel = straight`, the second touch performed as a straight eighth.

## V2 timing contract

V2 already has a timing contract for this case:

- pattern/generation writes the written upbeat as logical `.5`;
- render timing owns performed grid placement;
- `timing_intent=swing_upbeat` forces `.5` to perform at the swing/triplet upbeat (`2/3`) without writing `0.666...` into the pattern.

## Patch

For the affected Jazz Ballad `1&` piano soft-mark / retouch events, keep `beat=0.5` and add event metadata:

```python
"timing_intent": "swing_upbeat"
```

This applies to:

- `ballad_piano_downbeat_1and_whisper` second event;
- `ballad_phrase_two_chord_soft_marks` second event;
- `ballad_piano_two_beat_light_retouch` second event.

## Boundary

This is not a global Jazz Ballad feel change. Jazz Ballad profile remains globally `feel=straight` until a broader Ballad timing-feel policy is designed.

No notes, voicing texture, expression values, pedal behavior, gesture logic, API behavior, or Agent/LLM code changed.
