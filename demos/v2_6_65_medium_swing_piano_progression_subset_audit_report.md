# v2_6_65 — Medium Swing Progression-Specific Candidate Subset Policy

V1-derived progression-specific Medium Swing piano candidate priority translated into V2 ChordRegion-first preferred-subset reweighting. No bar-first templates, voicing selection, final expression values, gesture, API, Agent, or HarmonyOS behavior is introduced.

## V1 idioms translated

- **major_251 / minor_251 dominant-resolution vocabulary** → dominant-resolution ChordRegion preferred subset inside the existing region-length pool (`implemented_as_preferred_subset_v2_6_65`)
- **two_five / ii_setup vocabulary** → predominant-to-dominant ChordRegion preferred subset; short regions remain anchor-led (`implemented_as_preferred_subset_v2_6_65`)
- **two_chord_bar split vocabulary** → already translated as 2-beat / 1-beat ChordRegion vocabulary, not restored as bar-first templates (`kept_region_first`)
- **texture expansion shell2/shell4/rootless4** → explicitly excluded from pattern selection; remains voicing policy territory (`rejected_for_pattern_layer`)

## Static V2 policy audit

- Pattern / lookup / weight / expression-hint versions: `v2_6_56` / `v2_6_57` / `v2_6_58` / `v2_6_63`
- Progression subset policy enabled/version: `True` / `v2_6_65`
- Active by region length: `{'one_beat_region': 2, 'two_beat_region': 6, 'three_beat_region': 1, 'four_beat_region': 28}`
- Active by weight class: `{'stable': 19, 'offbeat': 12, 'active': 2, 'tail_push': 4}`
- Forbidden expression candidates: `0`
- Bar-first two_chord_bar candidates: `0`

## Runtime standard-tune audit

### All the Things You Are

- MIDI: `demos/v2_6_65_all_the_things_you_are_medium_swing_piano_progression_subset_demo.mid`
- Piano events: `209`
- Progression subset applied / preferred / fallback: `191` / `181` / `10`
- Progression context counts: `{'section_start': 21, 'predominant_to_dominant': 42, 'dominant_resolution': 54, 'tonic_resolution': 47, 'generic': 18, 'section_end': 16, 'tonic_prolongation': 5, 'ending': 6}`
- Progression subset key counts: `{'section_start_region': 21, 'ii_setup_region': 39, 'major_251_dominant_region': 49, 'tonic_resolution_region': 47, 'generic_region': 18, 'section_end_region': 16, 'tonic_prolongation_region': 5, 'minor_ii_setup_region': 3, 'minor_251_dominant_region': 5, 'ending_region': 6}`
- Progression status counts: `{'preferred_subset_candidate': 149, 'generic_context_no_subset': 18, 'preferred_short_region_subset_candidate': 32, 'fallback_candidate_downweighted': 10}`
- Harmonic / history penalty / history bonus: `209` / `20` / `53`
- Hold-until-next-touch events: `142`
- Forbidden expression / bar-first events: `0` / `0`
- Top note max / >=75 / voice-leading warnings: `72` / `0` / `0`

### Autumn Leaves

- MIDI: `demos/v2_6_65_autumn_leaves_medium_swing_piano_progression_subset_demo.mid`
- Piano events: `228`
- Progression subset applied / preferred / fallback: `188` / `169` / `19`
- Progression context counts: `{'section_start': 34, 'tonic_resolution': 49, 'generic': 40, 'predominant_to_dominant': 37, 'dominant_resolution': 47, 'section_end': 15, 'ending': 6}`
- Progression subset key counts: `{'section_start_region': 34, 'tonic_resolution_region': 49, 'generic_region': 40, 'minor_ii_setup_region': 23, 'minor_251_dominant_region': 30, 'ii_setup_region': 14, 'major_251_dominant_region': 17, 'section_end_region': 15, 'ending_region': 6}`
- Progression status counts: `{'preferred_short_region_subset_candidate': 131, 'fallback_candidate_downweighted': 19, 'generic_context_no_subset': 40, 'preferred_subset_candidate': 38}`
- Harmonic / history penalty / history bonus: `228` / `4` / `37`
- Hold-until-next-touch events: `148`
- Forbidden expression / bar-first events: `0` / `0`
- Top note max / >=75 / voice-leading warnings: `73` / `0` / `0`

## Acceptance

Passed: `True`

- `static: progression subset policy enabled`: `True`
- `static: progression subset policy version`: `True`
- `static: no pattern candidate writes final expression values`: `True`
- `static: no bar-first/two-chord-bar markers remain`: `True`
- `all_the_things_you_are: generation ok`: `True`
- `all_the_things_you_are: progression subset metadata present`: `True`
- `all_the_things_you_are: preferred subset events present`: `True`
- `all_the_things_you_are: harmonic policy remains active`: `True`
- `all_the_things_you_are: no pattern events contain concrete expression values`: `True`
- `all_the_things_you_are: no bar-first two_chord_bar runtime events`: `True`
- `all_the_things_you_are: top register calm`: `True`
- `all_the_things_you_are: voice-leading warnings calm`: `True`
- `autumn_leaves: generation ok`: `True`
- `autumn_leaves: progression subset metadata present`: `True`
- `autumn_leaves: preferred subset events present`: `True`
- `autumn_leaves: harmonic policy remains active`: `True`
- `autumn_leaves: no pattern events contain concrete expression values`: `True`
- `autumn_leaves: no bar-first two_chord_bar runtime events`: `True`
- `autumn_leaves: top register calm`: `True`
- `autumn_leaves: voice-leading warnings calm`: `True`

## Recommended next tasks

- `v2_6_66_engine_medium_swing_no_4and_delayed_tail_idiom_reinforcement`
- `v2_6_67_engine_medium_swing_active_fill_busy_multi_region_history_scorer`
- `v2_6_68_engine_medium_swing_expression_policy_v1_numeric_calibration`
- `v2_6_69_engine_medium_swing_piano_standard_tune_listening_checkpoint`
