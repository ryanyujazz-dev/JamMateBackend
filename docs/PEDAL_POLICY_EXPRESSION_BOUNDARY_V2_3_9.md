# Pedal Policy / Expression Boundary — v2_3_9

This pass is documentation-only. Runtime music generation, voicing selection, pattern selection, anticipation timing, and MIDI CC64 behavior remain unchanged from v2_3_9.

## Core contract

Pedal is an expression-level musical decision, not a pattern or voicing decision.

```text
Style Pattern
→ exposes rhythmic facts: onset spacing, tail availability, density, anticipation eligibility
→ Expression Policy
→ decides pedal intent: none / light / sustain / lush
→ MIDI Pedal Realizer
→ materializes approved intent as CC64 with re-pedal offset
```

Pattern must not directly emit CC64 or hard-code “use pedal”. A pattern may imply useful facts: long sustain tail, sparse texture, dense rhythm, syncopation, anticipation, phrase start, ending, or harmonic rhythm. Expression policy interprets those facts with the style and ensemble context.

## Decision inputs

Expression policy should consider:

- style: jazz_ballad, bossa_nova, medium_swing, future pop/solo-piano styles
- role: piano comping, solo piano foundation, pad-like support, exposed intro/ending
- harmonic rhythm: slow change favors pedal; dense changes require cleaner release
- voicing density and register: thick low-register voicings need less pedal
- pattern density: sparse sustained patterns may accept pedal; active short patterns usually stay dry
- anticipation: anticipated chords must connect without blurring the previous harmony
- phrase context: openings, endings, rubato-like ballad moments can be more connected
- LLM semantic intent: dry, clean, balanced, lush, solo_piano_lush

## Style defaults

### Jazz Ballad

Default target is balanced, connected, and clear. Ballad may use light or sustain pedal, but every harmony change should use re-pedal behavior:

```text
lift shortly before next chord
→ next chord attack
→ press shortly after attack
```

This simulates a human pianist changing harmony under pedal. A lush or solo-piano intent may increase pedal, but must still preserve harmonic clarity.

### Bossa Nova

Default is dry. Core batida identity comes from articulation and rhythmic placement, not pedal. Bossa anticipations should normally use no CC64; release should be clean enough that the next chord does not smear into the previous one.

### Medium Swing

Default is dry. Swing comping and push anticipations should remain rhythmically clear. Do not add pedal unless an explicit future style/LLM policy requests a special texture.

## Pattern-authoring guidance

When designing future patterns, document pedal-relevant facts, not pedal commands:

- `tail_available`
- `last_event_can_sustain`
- `dense_harmonic_rhythm`
- `short_comping_cell`
- `long_ballad_sustain`
- `anticipation_candidate`
- `phrase_ending`
- `exposed_solo_piano_context`

Expression policy can later translate these into `pedal=none/light/sustain/lush` according to the style.

## Expression-authoring guidance

Expression owns duration, release, velocity, articulation, touch, and pedal. It may choose pedal based on pattern facts and voicing facts. It should not choose new notes, voicings, or rhythm cells.

Recommended semantic mapping:

| Semantic intent | Meaning |
|---|---|
| dry | no pedal except explicit special cases |
| clean | mostly no pedal; short releases |
| balanced | natural ballad pedal with re-pedal |
| lush | more connected pedal, still re-pedaled |
| solo_piano_lush | broadest pedal use, still guarded by register and harmony |

## MIDI realizer boundary

MIDI realizer must not invent musical pedal intent. It only receives expression pedal intent and converts approved piano events into CC64. It is allowed to enforce physical realism such as re-pedal offsets, minimum gaps, and style allow-lists.

Current boundary:

- Jazz Ballad may use light or sustain pedal and materialize `light` / `sustain` as CC64.
- Bossa and Medium Swing remain dry by default.
- `pedal=none` must never create CC64.
- Re-pedal offset belongs at MIDI boundary because it is a performance-realization detail.

## Future work

Future pattern/expression development should update this document when a new style or role needs pedal semantics. Do not add ad-hoc pedal logic inside pattern libraries, voicing selectors, or chord resolvers.
