# v2_6_112 — Engine Bossa Nova Voicing Listening Checkpoint

- Engine version tag: `v2_10_28`
- Acceptance passed: `True`

## Scope

Checkpoint the Bossa OPEN-main voicing baseline after v2_6_102 through v2_6_111. This verifies ordinary runtime uses normal 4-to-5-note drop-family OPEN voicing, excludes generic_open, does not revive 2/3-note forced density or retired 1+3/2+2 grouped metadata, and has no low-cluster/top-gap artifact.

## Static audit

- Policy disposition: `open`
- Policy density range: `[4, 5]`
- Policy open methods: `['drop2', 'drop3', 'drop2_and_4']`
- Candidate count: `72`
- Method counts: `{'drop2': 24, 'drop3': 24, 'drop2_and_4': 24}`
- Density counts: `{'4': 72}`
- Generic-open candidates: `0`
- Low-density candidates: `0`
- Fallback/wrong-parent candidates: `0` / `0`
- Low-cluster/top-gap candidates: `0`
- Retired grouping candidates: `0`

## Runtime audits

### 3x — seed 23112

- MIDI: `demos/v2_6_112_blue_bossa_3x_bossa_nova_voicing_listening_checkpoint_demo.mid`
- Notes piano/bass/drums: `396` / `100` / `593`
- Piano harmonic events: `99`
- Dispositions: `{'open': 99}`
- Open methods: `{'drop2': 87, 'drop3': 12}`
- Densities: `{'4': 99}`
- Content families: `{'seventh_chord_basic': 83, 'rooted_color': 16}`
- Generic-open events: `0`
- Low-density events: `0`
- Retired grouping events: `0`
- Fallback/wrong-parent events: `0` / `0`
- Low-cluster/top-gap events: `0`
- Inspected bars bad events: `0`

### 5x — seed 23113

- MIDI: `demos/v2_6_112_blue_bossa_5x_bossa_nova_voicing_listening_checkpoint_demo.mid`
- Notes piano/bass/drums: `668` / `172` / `989`
- Piano harmonic events: `167`
- Dispositions: `{'open': 167}`
- Open methods: `{'drop2': 144, 'drop3': 23}`
- Densities: `{'4': 167}`
- Content families: `{'seventh_chord_basic': 135, 'rooted_color': 32}`
- Generic-open events: `0`
- Low-density events: `0`
- Retired grouping events: `0`
- Fallback/wrong-parent events: `0` / `0`
- Low-cluster/top-gap events: `0`
- Inspected bars bad events: `0`

## Acceptance

```json
{
  "passed": true,
  "checks": {
    "policy_declares_checkpoint": true,
    "checkpoint_is_metadata_only": true,
    "policy_open_main_drop_family_only": true,
    "policy_density_4_to_5": true,
    "static_no_generic_open": true,
    "static_no_low_density_candidates": true,
    "static_no_fallback_or_wrong_parent": true,
    "static_no_silent_fallback": true,
    "static_parent_spans_compact": true,
    "static_no_low_cluster_artifact": true,
    "static_no_retired_grouping": true,
    "runtime_demos_ok": true,
    "runtime_open_only": true,
    "runtime_no_generic_open": true,
    "runtime_no_low_density": true,
    "runtime_no_retired_grouping": true,
    "runtime_no_fallback_or_wrong_parent": true,
    "runtime_parent_spans_compact": true,
    "runtime_no_low_cluster_artifact": true
  }
}
```
