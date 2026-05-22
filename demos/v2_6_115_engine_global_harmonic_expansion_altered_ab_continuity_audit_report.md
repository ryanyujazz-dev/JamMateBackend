# v2_6_115 — Engine Global Harmonic Expansion / Altered / AB Continuity Audit

Engine tag: `v2_10_28`

## Acceptance
- `all_expected_styles_audited`: `True`
- `all_runtime_ok`: `True`
- `all_harmonic_expansion_enabled`: `True`
- `all_altered_mode_requested`: `True`
- `local_functional_pairs_detected`: `True`
- `ab_metadata_detected`: `True`
- `altered_sources_detected`: `True`
- `audit_exposes_non_global_method_lock_wiring`: `True`
- `audit_exposes_non_global_ab_filtering`: `True`
- `no_generic_open_regression_in_audit`: `True`

## Global findings
- Styles audited: `['bossa_nova', 'medium_swing', 'jazz_ballad']`
- Styles with method-lock runtime wiring pairs: `['bossa_nova', 'medium_swing']`
- Styles missing method-lock wiring pairs: `['jazz_ballad']`
- Styles with AB rotation filter pairs: `[]`
- Styles missing AB rotation filter pairs: `['bossa_nova', 'medium_swing']`
- Altered sources without AB metadata by style: `{'bossa_nova': 0, 'medium_swing': 0, 'jazz_ballad': 0}`
- Next recommended step: `v2_6_116_engine_style_neutral_progression_method_lock_wiring`

## bossa_nova

- MIDI: `demos/v2_6_115_bossa_nova_expansion_altered_ab_continuity_audit_demo.mid`
- piano / bass / drums: `412 / 108 / 593`
- color mode: `altered_dominant`
- local functional pairs: `23` `{'minor_ii_v': 9, 'v_i_minor': 8, 'ii_v': 3, 'v_i_major': 3}`
- method continuity: `23 / 23` ratio `1.0`
- AB follow: `23 / 23` ratio `1.0`
- method-lock runtime wiring pairs: `23`
- AB rotation filter-applied pairs: `0`
- altered source events / AB-missing: `21 / 0`
- method counts: `{'drop2': 89, 'drop3': 14}`
- source family counts: `{'third_fifth_seventh_ninth': 65, 'third_seventh_ninth_eleventh': 12, 'altered_dominant_rootless': 18, 'third_eleventh_fifth_seventh': 8}`

## medium_swing

- MIDI: `demos/v2_6_115_medium_swing_expansion_altered_ab_continuity_audit_demo.mid`
- piano / bass / drums: `260 / 155 / 288`
- color mode: `altered_dominant`
- local functional pairs: `20` `{'ii_v': 9, 'v_i_major': 9, 'minor_ii_v': 1, 'v_i_minor': 1}`
- method continuity: `20 / 20` ratio `1.0`
- AB follow: `20 / 20` ratio `1.0`
- method-lock runtime wiring pairs: `20`
- AB rotation filter-applied pairs: `0`
- altered source events / AB-missing: `14 / 0`
- method counts: `{'drop3': 36, 'drop2': 27, 'drop2_and_4': 2}`
- source family counts: `{'third_fifth_seventh_ninth': 49, 'altered_dominant_rootless': 14, 'third_thirteenth_seventh_ninth': 2}`

## jazz_ballad

- MIDI: `demos/v2_6_115_jazz_ballad_expansion_altered_ab_continuity_audit_demo.mid`
- piano / bass / drums: `360 / 50 / 0`
- color mode: `altered_dominant`
- local functional pairs: `26` `{'ii_v': 16, 'v_i_major': 8, 'v_i_minor': 2}`
- method continuity: `0 / 0` ratio `0.0`
- AB follow: `0 / 0` ratio `0.0`
- method-lock runtime wiring pairs: `0`
- AB rotation filter-applied pairs: `0`
- altered source events / AB-missing: `0 / 0`
- method counts: `{'unknown': 73}`
- source family counts: `{}`
