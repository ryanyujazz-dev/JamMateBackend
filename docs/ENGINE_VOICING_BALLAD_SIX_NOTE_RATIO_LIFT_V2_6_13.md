# Engine Voicing Ballad Six-Note Ratio Lift — v2_6_13

## Scope

`v2_6_13_engine_voicing_ballad_six_note_ratio_lift` is a voicing-only listening calibration pass.

The user requested that Ballad/SPREAD 6-note voicings be raised by roughly two-tenths of the previous ratio.  The goal is not to make 6-note voicings the new body of the texture; the body remains 5-note `2+3` SPREAD, with 6-note `2+4` / `3+3` appearing a little more often as fuller support.

This pass does not touch:

```text
Pattern
Anticipation
Expression
Pedal
Gesture
MIDI writer
Agent
API contract
HarmonyOS fixtures
shared VERSION / README / architecture docs
```

## Implementation

The adjustment is owned by `core.voicing.disposition.spread_voice_leading`, not by pattern, expression, or MIDI.

A small metadata-controlled notes-only cost adjustment was added:

```text
spread_grouping_mix_selected_6note_contract_bias = 0.20
```

When the Ballad grouping-mix policy selects a 6-note SPREAD contract such as:

```text
spread_2plus4_contract
spread_3plus3_contract
```

the groupwise voice-leading collapse gives that selected 6-note contract a gentle preference, while still allowing the compatible 5-note neighbor to win when it is clearly smoother.

This means the density mix is adjusted through the voicing selector's existing SPREAD grouping-mix intent, not by forcing note counts after the fact.

## Expected runtime behavior

The expected Misty / Jazz Ballad / 3-chorus audit shape after this pass:

```text
5-note remains dominant
6-note increases modestly from the v2_6_12 baseline
7-note remains rare
4-note SPREAD remains zero
unnotated maj7#11 remains zero by default
```

Reference audit from this pass:

```text
piano_audit_events: 196
5-note: 182
6-note: 12
7-note: 2
4-note: 0

2+3: 182
2+4: 7
3+3: 5
3+4: 2

maj7 #11 events: 0
```

## Boundary statement

This is a voicing density/selection calibration only.  It does not change chord rhythm, anticipation placement, articulation, sustain, pedal, or generated MIDI semantics.  If later Ballad voicing feels too thick or too thin, the next adjustment should continue through grouped SPREAD density policy / voice-leading selection, not through pattern or MIDI-side fixes.
