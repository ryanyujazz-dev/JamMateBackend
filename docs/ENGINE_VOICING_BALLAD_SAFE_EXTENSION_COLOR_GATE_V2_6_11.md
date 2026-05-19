# Engine Voicing Ballad Safe Extension Color Gate — v2_6_11

## Purpose

This pass tightens Jazz Ballad's default safe-extension color behavior after the v2_6_10 SPREAD density reset made 5/6-note grouped voicings the normal Ballad texture.

The musical rule is:

```text
Plain maj7 + Ballad style-safe expansion:
  prefer 9 / 13
  do not automatically add unnotated #11

maj7#11 written in the chart:
  preserve #11 faithfully

Unnotated maj7#11:
  allowed only when policy / LLM / arrangement metadata expresses harmonic-color intent,
  such as Lydian, bright, modern, or explicit allow_unnotated_maj7_sharp11.
```

## Why this is not a scorer patch

The previous behavior came from the source/color candidate pool: ordinary `style_safe_extensions` for major-seventh chords exposed `9`, `13`, and `#11`. Because SPREAD upper groups reuse the core content planner, #11 became a normal upper source option and could appear repeatedly in the full Ballad demo.

This pass changes the source-level permission/routing:

```text
core.voicing.sources.content_planner
  _expansion_color_candidates
    major seventh default safe colors -> 9 / 13 only
    #11 -> explicit chart symbol or harmonic-color intent gate
```

Selection/scoring still consumes the candidate pool normally. Pattern, Anticipation, Expression, Gesture, Pedal, MIDI, and style pattern vocabulary do not choose or suppress #11.

## Explicit chart fidelity

The rule does not block chart-written #11:

```text
Ebmaj7#11 -> explicit #11 source remains available
```

Explicit chart color remains higher priority than the style-safe default.

## Harmonic-color intent hooks

Unnotated maj7#11 may be enabled by policy metadata such as:

```text
harmonic_color_intent = lydian / bright / modern / #11
allow_unnotated_maj7_sharp11 = true
lydian_major_color_enabled = true
safe_extension_color_gate.major_seventh_sharp11 = allow / enabled / low_frequency / occasional
```

The default Jazz Ballad policy documents the gate as:

```text
safe_extension_color_gate.version = v2_6_11
major_seventh_default_colors = [9, 13]
major_seventh_sharp11 = explicit_symbol_or_harmonic_color_intent_only
```

## Boundary

This is voicing-only:

- no Pattern ownership change;
- no Anticipation ownership change;
- no Expression / duration / velocity / pedal change;
- no Gesture projection change;
- no MIDI writer repair;
- no Agent/API/shared version change.

## Validation target

The Misty Jazz Ballad default expansion demo should keep the v2_6_10 grouped SPREAD density behavior, but maj7 events should no longer contain unnotated #11 unless the chart or policy explicitly asks for it.
