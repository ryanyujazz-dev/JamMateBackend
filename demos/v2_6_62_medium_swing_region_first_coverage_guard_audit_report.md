# v2_6_62 — Medium Swing CoverageGuard Region-First Cleanup

Audit that Medium Swing CoverageGuard is ChordRegion-first and backup-only after the region-length piano comping work. The guard should stamp coverage metadata on already selected region-local piano events, insert no fallback anchors in normal standard-tune generation, and leave top-register / voice-leading checkpoints calm.

## All the Things You Are

- MIDI: `demos/v2_6_62_all_the_things_you_are_medium_swing_region_first_coverage_guard_demo.mid`
- Covered regions: `120` / `120`
- Uncovered regions / short uncovered: `0` / `0`
- Piano events: `207`
- Coverage inserted events: `0`
- Max piano events per region: `3`
- Coverage metadata: `{'coverage_version_counts': {'v2_6_62': 207}, 'coverage_checked_events': 207, 'coverage_backup_only_events': 207, 'coverage_region_first_scope_events': 207, 'coverage_region_local_time_events': 207}`
- Region length counts: `{'four_beat_region': 173, 'two_beat_region': 34}`
- Coverage outcome counts: `{'covered_by_selected_region_length_pattern': 207}`
- Top note max / >=75 / voice-leading warnings: `72` / `0` / `0`

## Autumn Leaves

- MIDI: `demos/v2_6_62_autumn_leaves_medium_swing_region_first_coverage_guard_demo.mid`
- Covered regions: `162` / `162`
- Uncovered regions / short uncovered: `0` / `0`
- Piano events: `223`
- Coverage inserted events: `0`
- Max piano events per region: `2`
- Coverage metadata: `{'coverage_version_counts': {'v2_6_62': 223}, 'coverage_checked_events': 223, 'coverage_backup_only_events': 223, 'coverage_region_first_scope_events': 223, 'coverage_region_local_time_events': 223}`
- Region length counts: `{'two_beat_region': 173, 'four_beat_region': 50}`
- Coverage outcome counts: `{'covered_by_selected_region_length_pattern': 223}`
- Top note max / >=75 / voice-leading warnings: `72` / `0` / `0`

## Acceptance

Passed: `True`

- `all_the_things_you_are: generation ok`: `True`
- `all_the_things_you_are: all ChordRegions have piano harmonic presence`: `True`
- `all_the_things_you_are: no short ChordRegion uncovered`: `True`
- `all_the_things_you_are: all piano events carry v2_6_62 coverage metadata`: `True`
- `all_the_things_you_are: normal generation does not need fallback insertion`: `True`
- `all_the_things_you_are: guard remains backup-only`: `True`
- `all_the_things_you_are: top register calm`: `True`
- `all_the_things_you_are: voice-leading warnings calm`: `True`
- `autumn_leaves: generation ok`: `True`
- `autumn_leaves: all ChordRegions have piano harmonic presence`: `True`
- `autumn_leaves: no short ChordRegion uncovered`: `True`
- `autumn_leaves: all piano events carry v2_6_62 coverage metadata`: `True`
- `autumn_leaves: normal generation does not need fallback insertion`: `True`
- `autumn_leaves: guard remains backup-only`: `True`
- `autumn_leaves: top register calm`: `True`
- `autumn_leaves: voice-leading warnings calm`: `True`
