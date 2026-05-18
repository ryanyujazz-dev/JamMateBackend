# v2_5_5 — Jazz Ballad Two-Beat 1& Pattern Patch

This is a narrow engine-deepening listening patch based on direct audition feedback.

## Problem

A Jazz Ballad two-beat piano candidate was perceived as a `beat 1 + beat 2` soft-mark pattern. In local region coordinates this was represented as:

```text
0.0, 1.0
```

For this Ballad use case, the more idiomatic light re-touch is closer to:

```text
beat 1 + beat 1&
0.0, 0.5
```

## V2 boundary

This pass only adjusts pitchless pattern timing metadata inside the existing Jazz Ballad comping vocabulary.

It does **not**:

- migrate V1 code;
- create a V1-style phrase engine;
- select concrete MIDI notes;
- bind a voicing texture/source;
- change duration, velocity, touch, pedal, or re-pedal policy;
- change Agent/LLM behavior.

## Code change

Updated candidates:

- `ballad_phrase_two_chord_soft_marks`
- `ballad_piano_two_beat_light_retouch`

Both now use local beats:

```text
(0.0, 0.5)
```

Their `rhythmic_cell` metadata is now:

```text
region_start_1and
```

## Development note

This is intentionally a small listening correction before continuing into larger Ballad bass / phrase-family work. The next larger musical task should resume as `v2_5_6_ballad_bass_anchor_path` unless listening feedback identifies another blocking piano issue first.
