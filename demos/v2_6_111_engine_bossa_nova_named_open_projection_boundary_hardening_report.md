# v2_6_111 — Engine Bossa Nova Drop-Family Closed-Parent Projection Fix

- Engine version tag: `v2_10_28`
- Acceptance passed: `True`

## Scope

Fix named OPEN drop-family projection wiring so DROP2/DROP3/DROP2&4 project from true compact CLOSED parents, not from already-open runtime closed variants. This retires the low-cluster/top-gap artifact heard in Bossa bars such as 14/19/29 without adding a new voicing ability.

## Static audit

- Candidate count: `48`
- Method counts: `{'drop2': 16, 'drop3': 16, 'drop2_and_4': 16}`
- Bad parent span count: `0`
- Bad low-cluster candidate count: `0`
- Fallback parent count: `0`
- Wrong parent-source count: `0`

## Runtime audits

### Blue Bossa 3x

- MIDI: `demos/v2_6_111_blue_bossa_3x_bossa_nova_named_open_projection_boundary_hardening_demo.mid`
- Piano / bass / drums notes: `412 / 103 / 593`
- Open methods: `{'drop2': 98, 'drop3': 5}`
- Generic open events: `0`
- Low-cluster/top-gap events: `0`
- Inspected bar bad events: `0`
- Max parent closed span: `11`
- Fallback parent events: `0`
- Wrong parent-source events: `0`

### Blue Bossa 5x

- MIDI: `demos/v2_6_111_blue_bossa_5x_bossa_nova_named_open_projection_boundary_hardening_demo.mid`
- Piano / bass / drums notes: `688 / 172 / 989`
- Open methods: `{'drop3': 12, 'drop2': 160}`
- Generic open events: `0`
- Low-cluster/top-gap events: `0`
- Inspected bar bad events: `0`
- Max parent closed span: `11`
- Fallback parent events: `0`
- Wrong parent-source events: `0`

## Acceptance checks

```json
{
  "passed": true,
  "checks": {
    "static_drop_parents_are_compact": true,
    "static_no_low_cluster_candidates": true,
    "runtime_demos_ok": true,
    "runtime_no_low_cluster_top_gap": true,
    "runtime_inspected_bars_clean": true,
    "runtime_no_generic_open": true,
    "runtime_parent_spans_compact": true,
    "static_no_fallback_parent_candidates": true,
    "static_parent_sources_are_compact_helper": true,
    "static_no_silent_fallback_allowed": true,
    "runtime_no_fallback_parent_candidates": true,
    "runtime_parent_sources_are_compact_helper": true,
    "runtime_no_silent_fallback_allowed": true
  }
}
```

Recommended next task: `v2_6_112_engine_bossa_nova_voicing_listening_checkpoint_or_continue_bass_drums`.
