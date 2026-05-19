# v2_6_43 — Engine Ballad SPREAD Lower Foundation Weight / Register Final Pass

## Scope

This is an Engine voicing-only lower-foundation checkpoint on top of `v2_6_42_engine_ballad_spread_safe_extension_frequency_calibration`.

It does not change Pattern, Anticipation, Expression, Gesture realization, MIDI writing, Agent, API, HarmonyOS fixtures, or shared integration contracts.

## Musical intent

Jazz Ballad SPREAD has now stabilized around a 5-note / 6-note body with low-frequency `1+4` color. Before moving on to broader voicing work, the lower/foundation group needs one final weight and register review:

```text
2+3  should not become thin or overly high
2+4  may be heavier, but must not become muddy or too tight
1+4  should remain a low-frequency color lane, not a main body
3+3  should remain very low frequency and avoid low-register mud
```

This pass is behavior-preserving. The current Misty checkpoint already passes the musical guardrails, so v2_6_43 formalizes the accepted lower foundation profile as audit data and regression tests rather than changing candidate selection.

## Accepted lower foundation profile

For Misty / Jazz Ballad / 3 choruses with seed `26912`:

```text
lower_foundation_note_min: 41
lower_foundation_note_max: 58
lower_foundation_note_average: 49.93
lower_foundation_span_max: 11
lower_foundation_span_average: 6.138
lower_foundation_span_violation_events: 0
lower_foundation_low_register_events: 28
```

Grouping profile:

```text
2+3:
  events: 114
  note_average: 51.855
  low_register_events: 2
  gap range: 5..7

2+4:
  events: 68
  note_average: 46.603
  low_register_events: 26
  gap range: 2..7

1+4:
  events: 10
  note_average: 48.4
  low_register_events: 0
  gap: 4

3+3:
  events: 4
  note_average: 52.333
  low_register_events: 0
  span: 10
```

The `2+4` low-register pressure is accepted because it is part of the heavier 6-note lane and still passes span/gap guards. It should remain audited, but this pass does not globally raise the lower group or thin the 6-note body.

## Audit contract

`build_piano_musical_audit()` now reports:

```text
ballad_spread_lower_foundation_weight_register_final_pass_version
lower_foundation_weight_register_final_pass_behavior_preserving
lower_foundation_weight_register_final_pass_density_lane_unchanged
lower_foundation_weight_register_final_pass_grouping_mix_unchanged
lower_foundation_weight_register_final_pass_low_register_threshold
lower_foundation_weight_register_final_pass_profile_by_grouping
lower_foundation_weight_register_final_pass_recipe_profile
lower_foundation_weight_register_final_pass_2plus3_not_too_thin
lower_foundation_weight_register_final_pass_2plus4_pressure_accepted
lower_foundation_weight_register_final_pass_3plus3_no_low_mud
lower_foundation_weight_register_final_pass_1plus4_low_frequency_role_preserved
lower_foundation_weight_register_final_pass_checkpoint_passed
```

The audit is observational only. It reads realized lower group notes, spans, gaps, recipes, density, and grouping counts.

## Guardrails retained

The previous accepted Ballad SPREAD guardrails stay unchanged:

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
major_seventh_unnotated_sharp11_events: 0
same_chord_reattack_continuity_checkpoint_passed: true
post_continuity_checkpoint_passed: true
```

## Next recommendation

Proceed to `v2_6_44_engine_ballad_spread_voicing_phase_summary_and_handoff`. That task should summarize the Ballad SPREAD voicing phase, freeze the accepted guardrails, and prepare a clean handoff before moving to a new voicing area.
