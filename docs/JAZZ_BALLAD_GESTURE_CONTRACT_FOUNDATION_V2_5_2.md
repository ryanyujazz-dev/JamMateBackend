# Jazz Ballad Gesture Contract Foundation — v2_5_2

This pass opens the Jazz Ballad style to V2-native gesture requests without changing default audible comping behavior.

## Scope

Implemented owner:

```text
src/jammate_engine/styles/jazz_ballad/gesture_policy.py
```

No V1 code was migrated. No Agent/LLM workflow was changed. No new phrase engine, runtime mirror, MIDI repair layer, or voicing subsystem was introduced.

## Contract

Jazz Ballad style-approved gesture kinds are now:

```text
simultaneous_onset
inner_movement
rolled_onset
```

`arpeggiated_onset`, `broken_chord`, and `fill` remain closed for default Ballad comping until a later style-specific pass explicitly opens them.

## Ownership boundary

```text
Pattern
  owns pitchless timing, event role, phrase slot, tail facts

Gesture
  owns pitchless projection / motion request:
  - inner movement
  - rolled onset
  - attack scope
  - abstract projection refs
  - held-foundation intent

Expression
  owns duration, velocity, articulation, touch, release, pedal

Voicing
  owns concrete notes, density, source, disposition, projection map

MIDI
  owns final note and CC64 materialization only
```

## Inner movement rule

Ballad `inner_movement` is not a pattern cell and not a voicing hack. It is a `GestureRequest` such as:

```text
kind = inner_movement
projection_refs = (inner / color_group / motion_group)
metadata.motion_shape = inner_resolution / inner_voice_breath / color_glide
metadata.held_voice_policy = hold_foundation_common_tones
metadata.rearticulation_scope = inner_or_color_group_only
```

The request must not name MIDI notes, final duration, final velocity, pedal, voicing texture, rootless texture, or V1 slot names such as `INNER_DYAD`.

## Rolled onset rule

Ballad `rolled_onset` is a projection gesture over an already-selected voicing. It may state abstract order such as:

```text
foundation_group -> projection_group
top -> inner -> lowest
```

It must not imply a specific cadence color, source degrees, rootless texture, or altered dominant choice. Those remain Voicing / HarmonicExpansion / AlteredPolicy responsibilities.

## Why default runtime remains unchanged

This pass only establishes the contract. The existing v2_5_0 retouch candidates remain temporary fallback and default deterministic selection still chooses the soft downbeat sustain anchor. This avoids pretending that contract-level gesture permission alone creates good Ballad phrasing.

Next passes should use the contract in this order:

```text
v2_5_3_jazz_ballad_phrase_intent_foundation
v2_5_4_held_foundation_partial_reattack_realization
```

## Tests

Targeted regression file:

```text
tests/test_v2_5_2_jazz_ballad_gesture_contract_foundation.py
```

It checks:

- Jazz Ballad opens only `simultaneous_onset`, `inner_movement`, and `rolled_onset`.
- Inner movement requests are pitchless and projection-scoped.
- Rolled cadence requests use functional projection refs.
- V1-style voicing texture metadata and concrete MIDI/expression metadata are rejected.
- Pattern events can carry a future Ballad gesture request without selecting notes.
- Default Ballad runtime selection remains unchanged until phrase-intent work.
