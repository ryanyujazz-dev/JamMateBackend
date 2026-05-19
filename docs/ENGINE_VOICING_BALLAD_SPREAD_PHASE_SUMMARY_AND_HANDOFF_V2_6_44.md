# v2_6_44 — Engine Ballad SPREAD Voicing Phase Summary and Handoff

## Scope

This is an Engine voicing-only phase summary and handoff on top of `v2_6_43_engine_ballad_spread_lower_foundation_weight_and_register_final_pass`.

It does not change Pattern, Anticipation, Expression, Gesture realization, MIDI writing, Agent, API, HarmonyOS fixtures, or shared integration contracts.

## Why this pass exists

The recent Ballad SPREAD voicing phase has stabilized the default Jazz Ballad SPREAD runtime around a musically accepted Misty three-chorus reference. Before moving to another voicing area, this pass freezes the accepted guardrails, records the phase milestones, and creates a clean handoff point.

This pass is behavior-preserving. It adds policy metadata, audit summary fields, documentation, and regression tests only.

## Accepted reference

Reference output:

```text
Tune: Misty
Style: Jazz Ballad
Choruses: 3
Seed: 26912
Bass present: true
```

Accepted guardrails:

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
top_note_ge_75_events: 0
major_seventh_unnotated_sharp11_events: 0
lower_foundation_span_violation_events: 0
post_continuity_checkpoint_passed: true
same_chord_reattack_continuity_checkpoint_passed: true
phrase_state_boundary_warning_events: 0
```

## Frozen musical decisions

The accepted Ballad SPREAD default should remain:

```text
2+3  main stable 5-note body
2+4  main fuller 6-note support
1+4  low-frequency 5-note color lane
3+3  very low-frequency 6-note thickness lane
```

Still disabled in the default Ballad SPREAD body:

```text
4-note SPREAD
7-note SPREAD
unnotated maj7#11 as default warm color
```

Safe extension rule remains:

```text
maj7 default color prefers 9 / 13
#11 requires explicit chord symbol or explicit harmonic-color intent
```

State-anchor rule remains:

```text
realized_notes may differ from state_anchor_notes only when a style policy gate explicitly allows the scope.
Current allowed scope: ballad_spread_phrase_scope_wide_gap_candidate_availability.
```

## Phase milestones summarized

```text
v2_6_30  restored low-frequency 1+4 and lower foundation audit
v2_6_31  added lower/upper gap audit
v2_6_32  fixed 2+4 tight-gap outliers
v2_6_35  fixed 2+3 wide-gap output with phrase-scope state protection
v2_6_37  cleaned state-anchor helper boundary
v2_6_40  added explicit policy gate for state-anchor consumption
v2_6_41  confirmed same-chord reattack voicing reuse
v2_6_42  froze maj7 safe-extension frequency
v2_6_43  froze lower foundation weight/register profile
v2_6_44  freezes the phase summary and handoff guardrails
```

## Audit contract

`build_piano_musical_audit()` now reports:

```text
ballad_spread_voicing_phase_summary_version
ballad_spread_voicing_phase_summary_behavior_preserving
ballad_spread_voicing_phase_summary_handoff_ready
ballad_spread_voicing_phase_summary_frozen_guardrails
ballad_spread_voicing_phase_summary_completed_milestones
ballad_spread_voicing_phase_summary_next_candidate_areas
```

The audit is observational only. It reads already-realized voicing, gap, density, continuity, and color results.

## Next handoff options

Recommended next voicing areas, in practical order:

```text
1. Medium Swing open/drop method-lock calibration
2. Bossa voicing-policy boundary and default texture pass
3. Upper Structure policy-gated runtime expansion
4. Minor dominant / altered light-gate plan
```

Do not continue adding Ballad SPREAD micro-patches unless listening reveals a specific regression. The current Ballad SPREAD reference should be treated as accepted until a new user listening note identifies a concrete issue.
