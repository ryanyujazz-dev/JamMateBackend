# v2_6_38 — Engine Ballad 1& Whisper Continuity Patch

This is a focused Jazz Ballad continuity bugfix. It is not a voicing selector change.

## Problem

The user identified sudden breaks around Misty performance bars 41, 63, and 95. The notes themselves were not wrong: the break came from the interaction between Ballad 1& whisper / soft-mark cells and expression duration clamping.

Before this patch, the 1& touch was a full simultaneous chord event. Expression treated it as the next full harmonic attack, so the beat-1 `soft_sustain` anchor could be shortened. The 1& touch was light and short, and pedal could release soon after, making the phrase feel like the whole piano suddenly stopped.

## Fix

The near-downbeat 1& touch is now a non-interrupting upper/projection-group re-touch:

- `ballad_piano_downbeat_1and_whisper`
- `ballad_phrase_two_chord_soft_marks`
- `ballad_piano_two_beat_light_retouch`

The second event keeps local beat `0.5` and `timing_intent=swing_upbeat`, but requests `inner_movement` on `projection_group` rather than a full `simultaneous_onset` chord.

## Boundary

- Pattern declares a pitchless partial re-touch intent.
- Expression no longer shortens the foundation for this non-interrupting re-touch.
- Realizer trims only the reattacked projection-group notes and keeps lower/foundation notes sustained.
- MIDI writer remains unchanged.
- Voicing selector remains unchanged.
- Agent and HarmonyOS remain unchanged.

## Timing detail

The partial reattack release now trims against the performed swing-upbeat start, not the raw logical `.5` slot. This prevents the earlier logical 0.5 release from creating a small gap before the rendered 2/3 upbeat.

## Guardrails

Misty / Jazz Ballad / 3 choruses should keep the existing voicing distribution:

```text
5-note: 124
6-note: 72
2+3: 114
2+4: 68
1+4: 10
3+3: 4
4-note: 0
7-note: 0
top_note_max <= 74
```

## Next step

After listening confirmation, continue voicing with `v2_6_39_engine_ballad_spread_post_continuity_listening_checkpoint`, rather than immediately adding new voicing behavior.
