# Jazz Ballad 1& Sustain Continuity Bugfix — v2_5_7

## Problem

The v2_5_6 Ballad patch correctly marked logical `1&` events as `timing_intent=swing_upbeat`, so the renderer performed them at the triplet/swing upbeat (`2/3`). However, expression duration clamping still measured the next same-track event at the logical `0.5` grid point.

That created an audible gap:

```text
beat 1 anchor releases at 0.5
1& event performs at 0.666...
=> short hiccup / disconnected sound
```

This was especially obvious around the reported measure-15 passage in the Misty Ballad demo.

## Fix

Expression duration resolution now consumes the event's declared timing intent when calculating the next same-track performed gap. Pattern still writes logical `0.5`; timing still owns the performed location; expression only sustains the previous event to the already-declared performed onset.

```text
logical second event: 0.5
timing_intent: swing_upbeat
performed second event: 0.666...
anchor duration clamp: 0.666...
```

`soft_whisper` is also changed from `SHORT` to `SUSTAIN` because Jazz Ballad near-downbeat re-touch should feel connected and light, not clipped.

## Boundary

- No V1 code migration.
- No Agent/LLM changes.
- No voicing texture binding.
- No pattern-layer concrete timing math; pattern still uses logical `0.5`.
- No MIDI post-repair.

## Verification

The focused regression test checks that `ballad_piano_downbeat_1and_whisper` keeps the written logical `0.5`, requests `swing_upbeat`, and gives the beat-1 anchor a duration of `2/3` beats.
