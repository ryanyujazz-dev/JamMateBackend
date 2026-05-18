# v2_5_4 — Jazz Ballad Held Foundation + Partial Reattack Realization

This pass is an engine-deepening realization pass. It does not migrate V1 code and does not add Agent/LLM behavior.

## Musical purpose

V1's useful musical lesson is that Ballad piano motion often keeps a warm foundation ringing while only an inner/color voice is lightly re-articulated. In V2 this must not become a low-level pattern or voicing texture bundle. The V2 ownership is:

```text
Pattern    -> places a pitchless phrase/motion slot
Gesture    -> requests INNER_MOVEMENT / projection scope
Expression -> resolves sustain, velocity, pedal, release
Voicing    -> selects the concrete vertical note stack
Realizer   -> projects the gesture onto the selected voicing and trims only reattacked motion voices
```

## Runtime behavior

- `INNER_MOVEMENT` no longer falls back to all voices.
- Inner/color gesture refs project only the requested voice/group from the already-selected `VoicingPlan`.
- Expression duration no longer treats a later inner-movement event as a full harmonic interruption.
- Harmonic realization trims only the prior voices that are re-struck by the inner movement.
- Foundation/common-tone voices from the previous anchor continue ringing.

## Boundary rules

- No V1 code migration.
- No V1 sorted-note `INNER_DYAD` slot slicing.
- No pattern-selected notes, source degrees, voicing texture, duration, velocity, or pedal.
- No MIDI repair path.
- Projection remains based on V2 `VoicingPlan.projection_map` / `voice_role` / `group_id` metadata.

## Next step

`v2_5_5_ballad_bass_anchor_path` should improve Jazz Ballad bass from single root anchors into a restrained two-feel anchor path before adding more advanced Ballad 251 color families.
