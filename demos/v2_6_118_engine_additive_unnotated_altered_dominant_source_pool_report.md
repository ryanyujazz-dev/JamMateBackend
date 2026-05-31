# v2_6_118 — Engine Additive Unnotated Altered Dominant Source Pool

Engine tag: `v2_10_28`

## Acceptance
- `all_expected_styles_audited`: `True`
- `all_runtime_ok`: `True`
- `plain_g7_keeps_ordinary_source_in_all_styles`: `True`
- `plain_g7_adds_altered_source_in_all_styles`: `True`
- `bossa_and_swing_plain_g7_keep_rootless_9_13_sources`: `True`
- `explicit_g7b9b13_stays_altered_only_in_all_styles`: `True`
- `altered_rootless_omits_natural_five`: `True`
- `demos_written`: `True`

## Principle
Altered dominant augments source candidates for unnotated/plain dominants; explicit altered symbols remain altered-only; AB/method/projection consume the chosen source without post-voicing note mutation.

## bossa_nova

- MIDI: `demos/v2_6_118_bossa_nova_additive_unnotated_altered_dominant_source_pool_demo.mid`
- piano / bass / drums: `420 / 101 / 593`
- plain G7 candidate pool: `{'ordinary_with_5': 8, 'ordinary_with_13': 8, 'altered_dominant_rootless': 8, 'ordinary_rooted_harmonic_expansion': 4, 'altered_dominant_rooted': 4}`
- explicit G7b9b13 candidate pool: `{'altered_dominant_rootless': 8, 'altered_dominant_rooted': 4}`
- selected source families: `{'third_fifth_seventh_ninth': 65, 'third_seventh_ninth_eleventh': 13, 'altered_dominant_rootless': 18, 'third_eleventh_fifth_seventh': 9}`
- selected altered / safe-rootless events: `18 / 65`

## medium_swing

- MIDI: `demos/v2_6_118_medium_swing_additive_unnotated_altered_dominant_source_pool_demo.mid`
- piano / bass / drums: `792 / 460 / 864`
- plain G7 candidate pool: `{'ordinary_with_5': 8, 'ordinary_with_13': 8, 'altered_dominant_rootless': 8, 'ordinary_rooted_harmonic_expansion': 4, 'altered_dominant_rooted': 4}`
- explicit G7b9b13 candidate pool: `{'altered_dominant_rootless': 8, 'altered_dominant_rooted': 4}`
- selected source families: `{'third_fifth_seventh_ninth': 198}`
- selected altered / safe-rootless events: `0 / 198`

## jazz_ballad

- MIDI: `demos/v2_6_118_jazz_ballad_additive_unnotated_altered_dominant_source_pool_demo.mid`
- piano / bass / drums: `990 / 150 / 0`
- plain G7 candidate pool: `{'ordinary_rooted_harmonic_expansion': 4, 'altered_dominant_rooted': 4}`
- explicit G7b9b13 candidate pool: `{'altered_dominant_rootless': 8, 'altered_dominant_rooted': 4}`
- selected source families: `{}`
- selected altered / safe-rootless events: `0 / 0`

Recommended next step: `v2_6_119_engine_style_level_expansion_alter_weight_calibration_by_functional_context`