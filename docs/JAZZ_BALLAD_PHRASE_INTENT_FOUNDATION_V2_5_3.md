# Jazz Ballad Phrase Intent Foundation — v2_5_3

This pass starts the Jazz Ballad phrase-intent layer without creating a V1-style phrase engine and without migrating V1 code.

## Scope

Implemented owner:

```text
src/jammate_engine/styles/jazz_ballad/comping_patterns.py
```

Reused existing owners:

```text
src/jammate_engine/styles/jazz_ballad/gesture_policy.py
src/jammate_engine/core/harmony/harmonic_context.py
src/jammate_engine/core/pattern_runtime/
```

No Agent/LLM workflow was changed. No new runtime mirror, MIDI repair layer, voicing subsystem, or V1 phrase-engine file was introduced.

## What changed

Jazz Ballad comping candidates now carry phrase-intent metadata in addition to pitchless timing:

```text
phrase_family
phrase_function
phrase_slot
context_gate
gesture_intent
```

Initial V2-native phrase families:

```text
warm_pad
breath_answer
two_chord_soft_marks
major_251_stable_cadence
temporary_low_level_fallback
```

`temporary_low_level_fallback` keeps the earlier v2_5_0 retouch cells available while marking them as fallback rather than the long-term Ballad direction.

## Phrase / Gesture boundary

Pattern candidates may now request an approved pitchless gesture slot:

```text
GestureKind.INNER_MOVEMENT
GestureKind.ROLLED_ONSET
GestureKind.SIMULTANEOUS_ONSET
```

They still must not choose:

```text
MIDI notes
source degrees
voicing texture / rootless texture
final duration
velocity
touch
pedal
MIDI repair behavior
```

The phrase layer only says, for example:

```text
phrase_family = breath_answer
phrase_slot = inner_motion_answer
gesture_intent = inner_movement
motion_shape = inner_voice_breath
projection_ref = inner
```

Concrete notes still come from the V2 voicing system. Duration, velocity, touch, and pedal still come from core expression.

## Harmonic-context reuse

The `major_251_stable_cadence` candidate is context-gated through the existing style-neutral `core/harmony/harmonic_context.py` classifier. It appears only for a conservative current-dominant window such as:

```text
Dm7 -> G7 -> Cmaj7
```

where the current region is the dominant region and the local window is `major_ii_v_i`.

This avoids adding a new progression recognizer inside the style package.

## Why partial reattack is not implemented here

`v2_5_3` only makes phrase candidates request gestures. It does not yet make inner movement sound like held foundation plus partial rearticulation. In the current realizer, inner movement is still safely projected through the existing gesture boundary.

The next pass should implement:

```text
held foundation/common tones
partial reattack of inner/color/projection group
no repeated full-voicing re-strike for inner movement
light pedal refresh owned by Expression/MIDI pedal boundary
```

## Tests

Focused regression file:

```text
tests/test_v2_5_3_jazz_ballad_phrase_intent_foundation.py
```

It checks:

- phrase families are exposed by the Jazz Ballad comping library;
- `breath_answer` requests `inner_movement` without concrete notes or texture metadata;
- two-beat regions expose `two_chord_soft_marks` inside the harmonic region only;
- `major_251_stable_cadence` is context-gated by the existing harmonic classifier;
- deterministic no-rng runtime selection still uses the warm-pad anchor.

## Next task

```text
v2_5_4_held_foundation_partial_reattack_realization
```

That pass should make `inner_movement` musically audible as held foundation plus light inner/color motion, while still respecting V2 Pattern / Gesture / Expression / Voicing boundaries.
