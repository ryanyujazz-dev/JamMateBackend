# v2_6_42 — Engine Ballad SPREAD Safe Extension Frequency Calibration

## Scope

This is an Engine voicing-only safe-extension frequency checkpoint on top of `v2_6_41_engine_ballad_spread_same_chord_reattack_continuity_calibration`.

It does not change Pattern, Anticipation, Expression, Gesture realization, MIDI writing, Agent, API, HarmonyOS fixtures, or shared integration contracts.

## Musical intent

Jazz Ballad SPREAD should keep major-seventh color warm by default. For ordinary, unnotated `maj7` chords, the safe extension palette should prefer `9` and `13`. Unnotated `#11` is a brighter Lydian color and should not appear in the default warm Ballad runtime unless the chart explicitly writes `#11` or a future local policy declares harmonic-color intent.

This keeps the Ballad sound from drifting into a modern/bright color profile while still allowing explicit chart color fidelity.

## Runtime boundary

v2_6_42 does not add a new scorer and does not change candidate selection. The existing v2_6_11 color gate already keeps unnotated major-seventh `#11` out of the default Ballad candidate pool.

This pass formalizes the current accepted runtime as an auditable frequency contract:

```text
major-seventh default safe colors: 9 / 13
unnotated major-seventh #11: 0 events in default Misty checkpoint
explicit chart #11: still allowed
harmonic-color intent #11: reserved for explicit future policy
```

## Audit contract

`build_piano_musical_audit()` now reports:

```text
ballad_spread_safe_extension_frequency_calibration_version
major_seventh_safe_extension_events
major_seventh_safe_extension_color_events
major_seventh_safe_extension_warm_color_events
major_seventh_safe_extension_degree_counts
major_seventh_safe_extension_degree_counts_by_chord
major_seventh_safe_extension_non_safe_color_events_by_chord
major_seventh_unnotated_sharp11_events
major_seventh_explicit_sharp11_events
major_seventh_safe_extension_preferred_colors
major_seventh_safe_extension_checkpoint_passed
```

The audit is observational only. It reads realized voicing degrees and does not re-plan source material.

## Accepted Misty checkpoint

For Misty / Jazz Ballad / 3 choruses with seed `26912`:

```text
major_seventh_safe_extension_events: 60
major_seventh_safe_extension_color_events: 21
major_seventh_safe_extension_degree_counts: {"13": 7, "9": 14}
major_seventh_unnotated_sharp11_events: 0
major_seventh_explicit_sharp11_events: 0
major_seventh_safe_extension_checkpoint_passed: true
```

The previous Ballad SPREAD guardrails stay unchanged:

```text
5-note: 124
6-note: 72
4-note: 0
7-note: 0
2+3: 114
2+4: 68
1+4: 10
3+3: 4
lower_upper_too_tight_events: 0
lower_upper_too_wide_events: 0
top_note_max: 72
same_chord_reattack_continuity_checkpoint_passed: true
post_continuity_checkpoint_passed: true
```

## Next recommendation

Proceed to `v2_6_43_engine_ballad_spread_lower_foundation_weight_and_register_final_pass`. That task should review lower foundation weight/register one more time using the already-stable density, gap, same-chord continuity, state-anchor, and safe-extension checkpoints.
