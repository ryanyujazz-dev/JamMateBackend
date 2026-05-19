# v2_6_40 — Engine Ballad SPREAD Phrase-State Anchor Policy Boundary

This is a behavior-preserving voicing boundary pass after the accepted `v2_6_39` checkpoint.

## Purpose

`v2_6_35` introduced a musically useful separation:

```text
realized_notes      # the notes actually played for the current event
state_anchor_notes  # the notes used to advance later voice-leading state
```

`v2_6_37` centralized that contract in `VoicingStateAdvanceAnchor`.  `v2_6_40` defines its policy boundary: the helper is a core voicing runtime capability, but production runtime consumption is disabled unless a style voicing policy explicitly opens a gate.

## Boundary

This pass does not change selected voicings for the current accepted Ballad SPREAD baseline.

```text
Pattern: unchanged
Anticipation: unchanged
Expression: unchanged
Gesture/realizer: unchanged
MIDI writer: unchanged
Agent / API / HarmonyOS: unchanged
```

## Policy-gated contract

The resolver now consumes `VoicingStateAdvanceAnchor` only when both are true:

```text
candidate metadata declares a state anchor
style voicing policy enables voicing_state_advance_anchor_policy_gate_enabled
```

For Ballad SPREAD, the only opened scope is:

```text
ballad_spread_phrase_scope_wide_gap_candidate_availability
```

This keeps the mechanism narrow and auditable:

```text
Core helper exists: yes
Default global behavior: disabled without style policy gate
Enabled for other styles: no
Enabled for arbitrary candidates: no
Audit required: yes
```

## Added audit surface

`build_piano_musical_audit()` now exposes:

```text
spread_phrase_state_anchor_policy_boundary_version: v2_6_40
spread_phrase_state_anchor_policy_boundary_events
spread_phrase_state_anchor_policy_boundary_gate_required_events
spread_phrase_state_anchor_policy_boundary_scopes
spread_phrase_state_anchor_policy_boundary_previous_gate_consumed_events
```

The event rows also expose:

```text
voicing_state_advance_anchor_policy_gate_version
voicing_state_advance_anchor_policy_gate_required
voicing_state_advance_anchor_policy_gate_scope
spread_phrase_state_anchor_policy_boundary_applied
spread_phrase_state_anchor_policy_boundary_contract
spread_phrase_state_anchor_policy_boundary_scope
previous_voicing_state_state_advance_anchor_policy_gate_consumed
```

## Accepted Misty / Jazz Ballad / 3-chorus guardrails

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
state anchor boundary warnings: 0
```

## Next step

If this policy boundary remains accepted, continue with:

```text
v2_6_41_engine_ballad_spread_same_chord_reattack_continuity_calibration
```

The next task should review same-chord reattack continuity: repeated touches inside one chord region should generally reuse the foundation/voicing unless a deliberate movement or fill is requested.
