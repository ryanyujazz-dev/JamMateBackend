# Jazz Ballad Default Swing-8 Anticipation Timing Patch — v2_5_8

## Scope

This pass fixes Jazz Ballad timing-feel ownership. Jazz Ballad should feel like swing eighths by default, not only for a few manually tagged `1&` events.

## Musical rule

- Written upbeats remain logical `.5` grid positions in pattern candidates.
- Jazz Ballad timing policy performs `.5` as swing/triplet `2/3` by default.
- Anticipation uses the same rule: the pitchless timeline moves the next-chord beat-1 event to the previous logical `4&`, but the performed attack lands on the swing `4&`.

## V2 boundary

```text
Pattern       owns written logical grid only
Anticipation  owns pitchless beat-1-to-previous-4& movement
Timing        owns performed swing placement
Expression    consumes performed lead-in for tied duration
Voicing       owns concrete notes
MIDI          materializes already-resolved timing; no repair path
```

## Contract

Jazz Ballad anticipation now uses:

```text
target_offset_beats = -0.5
timing_grid = swing_triplet_upbeat
target_timing_intent = swing_upbeat
performed_lead_in_beats = 1/3
expected_upbeat_fraction = 2/3
```

Jazz Ballad timing profile now uses:

```text
feel = swing
swing_ratio = 2/3
half_beat_grid = 0.5
```

## Explicit non-goals

- Do not write literal `0.666...` into pattern candidates.
- Do not migrate V1 code.
- Do not bind pattern to voicing texture.
- Do not change concrete voicing, expression values, pedal policy, Agent, or LLM behavior.
