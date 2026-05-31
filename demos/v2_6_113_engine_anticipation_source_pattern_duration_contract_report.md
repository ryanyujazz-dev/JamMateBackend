# v2_6_113 — Anticipation Source-Pattern Duration Contract

Engine version: `v2_10_28`

## Scope

First-principles anticipation duration fix: a next-region beat-1 event moved to the previous tail keeps the suppressed source event's original continuation target, such as source beat 1 -> source 3&, instead of being shortened to a generic post-downbeat cap. This is a shared AnticipationResolver / ExpressionResolver contract, not a Bossa-specific patch.

## Static probes

```json
{
  "checkpoint_version": "v2_6_113",
  "engine_version_tag": "v2_10_28",
  "hold_probe": {
    "first_hint": "soft_hold",
    "anticipated_onset": 3.5,
    "original_onset": 4.0,
    "source_continuation_contract_version": "v2_6_113",
    "source_continuation_target_kind": "next_same_track_touch",
    "source_next_same_track_gap_beats": 3.5,
    "lead_in_beats": 0.5,
    "duration_beats": 4.0,
    "duration_anticipation_original_sustain_beats": 3.5,
    "duration_anticipation_source_continuation_applied": true,
    "duration_anticipation_source_continuation_reason": "hold_until_source_next_same_track_touch",
    "duration_anticipation_micro_tuning_reason": "source_pattern_continuation_target_preserved"
  },
  "short_probe": {
    "first_hint": "short",
    "anticipated_onset": 3.5,
    "original_onset": 4.0,
    "source_continuation_contract_version": "v2_6_113",
    "source_continuation_target_kind": "next_same_track_touch",
    "source_next_same_track_gap_beats": 3.5,
    "lead_in_beats": 0.5,
    "duration_beats": 0.95,
    "duration_anticipation_original_sustain_beats": 0.45,
    "duration_anticipation_source_continuation_applied": false,
    "duration_anticipation_source_continuation_reason": "profile_requested_duration_clamped_to_source_region_remaining",
    "duration_anticipation_micro_tuning_reason": "no_style_specific_duration_micro_tuning"
  },
  "hold_expected_duration_beats": 4.0,
  "short_expected_duration_beats": 0.95,
  "first_principles_contract": "Anticipation moves the logical event onset, not its source-pattern continuation endpoint. Hold-style source beat-1 events use lead-in + source next-touch/source-region-end gap; fixed short events keep fixed short duration."
}
```

## Runtime audits

### Blue Bossa 3x

- MIDI: `demos/v2_6_113_blue_bossa_3x_bossa_nova_anticipation_source_pattern_duration_contract_demo.mid`
- Piano/bass/drums notes: 420 / 104 / 593
- Anticipated piano events: 15
- Source-continuation applied: 12
- Next-touch continuation mismatches: 0
- Continuation micro-cap count: 0

### Blue Bossa 5x

- MIDI: `demos/v2_6_113_blue_bossa_5x_bossa_nova_anticipation_source_pattern_duration_contract_demo.mid`
- Piano/bass/drums notes: 672 / 173 / 989
- Anticipated piano events: 26
- Source-continuation applied: 20
- Next-touch continuation mismatches: 0
- Continuation micro-cap count: 0

## Acceptance

```json
{
  "checks": {
    "static_hold_probe_preserves_source_3and_target": true,
    "static_short_probe_remains_short": true,
    "static_contract_metadata_present": true,
    "runtime_blue_bossa_generated": true,
    "runtime_has_anticipations": true,
    "runtime_has_source_continuation_rows": true,
    "runtime_next_touch_continuation_matches_expected_duration": true,
    "runtime_source_continuation_not_micro_capped": true
  },
  "passed": true
}
```
