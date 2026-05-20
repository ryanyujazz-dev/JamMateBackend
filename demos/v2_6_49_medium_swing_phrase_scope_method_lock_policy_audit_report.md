# Medium Swing OPEN Drop-Family Phrase-Scope Method Lock Policy Audit

- Contract version: `v2_10_8`
- Milestone: `v2_6_49 — Medium Swing OPEN Drop-Family Phrase-Scope Method Lock Policy`
- Acceptance passed: `True`

## All the Things You Are

- MIDI: `demos/v2_6_49_all_the_things_you_are_medium_swing_phrase_scope_method_lock_policy_demo.mid`
- Events: `174`
- Families: `{'open': 174}`
- Methods: `{'drop2': 98, 'drop2_and_4': 2, 'drop3': 74}`
- Contrast roles: `{'baseline_open_swing': 92, 'bridge_open_contrast': 36, 'final_chorus_open_lift': 46}`
- Methods by contrast role: `{'baseline_open_swing': {'drop2': 71, 'drop2_and_4': 1, 'drop3': 20}, 'bridge_open_contrast': {'drop3': 29, 'drop2': 7}, 'final_chorus_open_lift': {'drop3': 25, 'drop2': 20, 'drop2_and_4': 1}}`
- Percentages by contrast role: `{'baseline_open_swing': {'drop2': 0.7717, 'drop2_and_4': 0.0109, 'drop3': 0.2174}, 'bridge_open_contrast': {'drop3': 0.8056, 'drop2': 0.1944}, 'final_chorus_open_lift': {'drop3': 0.5435, 'drop2': 0.4348, 'drop2_and_4': 0.0217}}`
- OPEN method weight plans: `{'baseline_open_swing': {'generic_open': 0.0, 'drop2': 0.52, 'drop3': 0.38, 'drop2_and_4': 0.1}, 'bridge_open_contrast': {'generic_open': 0.0, 'drop2': 0.35, 'drop3': 0.53, 'drop2_and_4': 0.1}, 'final_chorus_open_lift': {'generic_open': 0.0, 'drop2': 0.43, 'drop3': 0.48, 'drop2_and_4': 0.08}}`
- Voice-leading transitions: `119`
- Voice-leading warnings: `0`
- Method-switch / section-boundary warnings: `0` / `0`
- Top / low / avg-motion max: `5` / `7` / `4.25`
- Section-boundary review events / warnings: `11` / `0`
- Section-boundary entry methods by role: `{'baseline_open_swing': {'drop2': 4, 'drop3': 1}, 'bridge_open_contrast': {'drop3': 2, 'drop2': 1}, 'final_chorus_open_lift': {'drop3': 2, 'drop2': 1}}`
- Section-boundary method pairs: `{'drop2->drop2': 2, 'drop2_and_4->drop3': 1, 'drop3->drop2': 4, 'drop3->drop3': 2, 'drop2->drop3': 2}`
- Phrase-scope events / switches / ratio: `84` / `12` / `0.1429`
- Phrase-scope DROP2&4 run events / max: `2` / `1`
- Phrase-scope ii-V / V-I / ii-V-I events: `30` / `27` / `27`
- Phrase-scope ii-V-I method consistent / switch: `27` / `0`
- Phrase-scope high-motion switches / warnings / checkpoint: `0` / `0` / `True`

## Autumn Leaves

- MIDI: `demos/v2_6_49_autumn_leaves_medium_swing_phrase_scope_method_lock_policy_demo.mid`
- Events: `223`
- Families: `{'open': 223}`
- Methods: `{'drop2': 79, 'drop3': 119, 'drop2_and_4': 25}`
- Contrast roles: `{'baseline_open_swing': 116, 'bridge_open_contrast': 50, 'final_chorus_open_lift': 57}`
- Methods by contrast role: `{'baseline_open_swing': {'drop2': 68, 'drop3': 35, 'drop2_and_4': 13}, 'bridge_open_contrast': {'drop3': 37, 'drop2': 8, 'drop2_and_4': 5}, 'final_chorus_open_lift': {'drop2': 3, 'drop3': 47, 'drop2_and_4': 7}}`
- Percentages by contrast role: `{'baseline_open_swing': {'drop2': 0.5862, 'drop3': 0.3017, 'drop2_and_4': 0.1121}, 'bridge_open_contrast': {'drop3': 0.74, 'drop2': 0.16, 'drop2_and_4': 0.1}, 'final_chorus_open_lift': {'drop2': 0.0526, 'drop3': 0.8246, 'drop2_and_4': 0.1228}}`
- OPEN method weight plans: `{'baseline_open_swing': {'generic_open': 0.0, 'drop2': 0.52, 'drop3': 0.38, 'drop2_and_4': 0.1}, 'bridge_open_contrast': {'generic_open': 0.0, 'drop2': 0.35, 'drop3': 0.53, 'drop2_and_4': 0.1}, 'final_chorus_open_lift': {'generic_open': 0.0, 'drop2': 0.43, 'drop3': 0.48, 'drop2_and_4': 0.08}}`
- Voice-leading transitions: `161`
- Voice-leading warnings: `0`
- Method-switch / section-boundary warnings: `0` / `0`
- Top / low / avg-motion max: `5` / `7` / `5.5`
- Section-boundary review events / warnings: `11` / `0`
- Section-boundary entry methods by role: `{'baseline_open_swing': {'drop2': 3, 'drop3': 2}, 'bridge_open_contrast': {'drop3': 2, 'drop2': 1}, 'final_chorus_open_lift': {'drop2': 1, 'drop3': 2}}`
- Section-boundary method pairs: `{'drop2->drop2': 2, 'drop2->drop3': 2, 'drop3->drop2': 3, 'drop3->drop3': 4}`
- Phrase-scope events / switches / ratio: `117` / `27` / `0.2308`
- Phrase-scope DROP2&4 run events / max: `19` / `2`
- Phrase-scope ii-V / V-I / ii-V-I events: `45` / `21` / `21`
- Phrase-scope ii-V-I method consistent / switch: `20` / `1`
- Phrase-scope high-motion switches / warnings / checkpoint: `0` / `0` / `True`

## Acceptance checks

- `all_the_things_you_are: generated`: `True` — `{'ok': True}`
- `all_the_things_you_are: enough three-chorus piano events`: `True` — `{'events': 174}`
- `all_the_things_you_are: open family only`: `True` — `{'families': {'open': 174}}`
- `all_the_things_you_are: all texture contrast roles present`: `True` — `{'roles': {'baseline_open_swing': 92, 'bridge_open_contrast': 36, 'final_chorus_open_lift': 46}}`
- `all_the_things_you_are: multiple open methods realized`: `True` — `{'methods': {'drop2': 98, 'drop2_and_4': 2, 'drop3': 74}}`
- `all_the_things_you_are: bridge increases drop3 share over baseline`: `True` — `{'baseline_drop3': 0.2174, 'bridge_drop3': 0.8056}`
- `all_the_things_you_are: final chorus increases drop3 share over baseline after generic-open removal`: `True` — `{'baseline_drop3': 0.2174, 'final_drop3': 0.5435}`
- `all_the_things_you_are: drop2_and_4 remains controlled`: `True` — `{'methods': {'drop2': 98, 'drop2_and_4': 2, 'drop3': 74}, 'drop2_and_4_total_ratio': 0.011494252873563218}`
- `all_the_things_you_are: no failed register guards`: `True` — `{'failed': 0}`
- `all_the_things_you_are: no missing piano note events`: `True` — `{'missing': 0}`
- `all_the_things_you_are: open/drop cross-region voice-leading checkpoint passes`: `True` — `{'transitions': 119, 'warnings': 0, 'top_motion_max_abs': 5, 'avg_motion_max': 4.25, 'legacy_output_without_v2_6_46_fields': False}`
- `all_the_things_you_are: method switches remain smooth`: `True` — `{'method_switch_events': 30, 'method_switch_warnings': 0}`
- `all_the_things_you_are: section boundaries remain smooth`: `True` — `{'section_boundary_events': 11, 'section_boundary_warnings': 0}`
- `all_the_things_you_are: section-boundary method-lock readability passes`: `True` — `{'boundary_events': 11, 'warnings': 0, 'drop2_and_4_entry_events': 0, 'entry_methods_by_role': {'baseline_open_swing': {'drop2': 4, 'drop3': 1}, 'bridge_open_contrast': {'drop3': 2, 'drop2': 1}, 'final_chorus_open_lift': {'drop3': 2, 'drop2': 1}}, 'legacy_output_without_v2_6_47_fields': False}`
- `all_the_things_you_are: phrase-scope method continuity checkpoint passes`: `True` — `{'phrase_scope_events': 84, 'method_switch_ratio': 0.1429, 'drop2_and_4_run_max': 1, 'high_motion_switch_events': 0, 'warnings': 0, 'legacy_output_without_v2_6_48_fields': False}`
- `all_the_things_you_are: DROP2&4 stays phrase-internal color`: `True` — `{'drop2_and_4_run_events': 2, 'drop2_and_4_run_max': 1}`
- `all_the_things_you_are: phrase-scope method lock policy applies to local progressions`: `True` — `{'applied_events': 88, 'pair_types': {'ii_v': 39, 'v_i_major': 41, 'minor_ii_v': 5, 'v_i_minor': 3}}`
- `all_the_things_you_are: all locked follow candidates match their method lock`: `True` — `{'candidate_match_events': 88, 'candidate_mismatch_events': 0, 'runtime_filtering_events': 88}`
- `all_the_things_you_are: rootless A/B orientation alignment checkpoint passes`: `True` — `{'policy_applied_events': 0, 'filter_applied_events': 0, 'candidate_match_events': 0, 'candidate_mismatch_events': 0, 'skip_reasons': {'previous_seed_not_rootless_ab': 88}}`
- `autumn_leaves: generated`: `True` — `{'ok': True}`
- `autumn_leaves: enough three-chorus piano events`: `True` — `{'events': 223}`
- `autumn_leaves: open family only`: `True` — `{'families': {'open': 223}}`
- `autumn_leaves: all texture contrast roles present`: `True` — `{'roles': {'baseline_open_swing': 116, 'bridge_open_contrast': 50, 'final_chorus_open_lift': 57}}`
- `autumn_leaves: multiple open methods realized`: `True` — `{'methods': {'drop2': 79, 'drop3': 119, 'drop2_and_4': 25}}`
- `autumn_leaves: bridge increases drop3 share over baseline`: `True` — `{'baseline_drop3': 0.3017, 'bridge_drop3': 0.74}`
- `autumn_leaves: final chorus increases drop3 share over baseline after generic-open removal`: `True` — `{'baseline_drop3': 0.3017, 'final_drop3': 0.8246}`
- `autumn_leaves: drop2_and_4 remains controlled`: `True` — `{'methods': {'drop2': 79, 'drop3': 119, 'drop2_and_4': 25}, 'drop2_and_4_total_ratio': 0.11210762331838565}`
- `autumn_leaves: no failed register guards`: `True` — `{'failed': 0}`
- `autumn_leaves: no missing piano note events`: `True` — `{'missing': 0}`
- `autumn_leaves: open/drop cross-region voice-leading checkpoint passes`: `True` — `{'transitions': 161, 'warnings': 0, 'top_motion_max_abs': 5, 'avg_motion_max': 5.5, 'legacy_output_without_v2_6_46_fields': False}`
- `autumn_leaves: method switches remain smooth`: `True` — `{'method_switch_events': 37, 'method_switch_warnings': 0}`
- `autumn_leaves: section boundaries remain smooth`: `True` — `{'section_boundary_events': 11, 'section_boundary_warnings': 0}`
- `autumn_leaves: section-boundary method-lock readability passes`: `True` — `{'boundary_events': 11, 'warnings': 0, 'drop2_and_4_entry_events': 0, 'entry_methods_by_role': {'baseline_open_swing': {'drop2': 3, 'drop3': 2}, 'bridge_open_contrast': {'drop3': 2, 'drop2': 1}, 'final_chorus_open_lift': {'drop2': 1, 'drop3': 2}}, 'legacy_output_without_v2_6_47_fields': False}`
- `autumn_leaves: phrase-scope method continuity checkpoint passes`: `True` — `{'phrase_scope_events': 117, 'method_switch_ratio': 0.2308, 'drop2_and_4_run_max': 2, 'high_motion_switch_events': 0, 'warnings': 0, 'legacy_output_without_v2_6_48_fields': False}`
- `autumn_leaves: DROP2&4 stays phrase-internal color`: `True` — `{'drop2_and_4_run_events': 19, 'drop2_and_4_run_max': 2}`
- `autumn_leaves: phrase-scope method lock policy applies to local progressions`: `True` — `{'applied_events': 100, 'pair_types': {'ii_v': 31, 'v_i_major': 26, 'minor_ii_v': 22, 'v_i_minor': 21}}`
- `autumn_leaves: all locked follow candidates match their method lock`: `True` — `{'candidate_match_events': 100, 'candidate_mismatch_events': 0, 'runtime_filtering_events': 100}`
- `autumn_leaves: rootless A/B orientation alignment checkpoint passes`: `True` — `{'policy_applied_events': 0, 'filter_applied_events': 0, 'candidate_match_events': 0, 'candidate_mismatch_events': 0, 'skip_reasons': {'previous_seed_not_rootless_ab': 100}}`

## Reading note

This is an observational audit: it verifies actual selected projection methods and cross-region voice-leading from runtime debug, not just policy metadata. Medium Swing still stays in OPEN family; generic_open has zero normal runtime weight and remains available only for explicit rescue/fallback. DROP2 is the baseline body, DROP3 is bridge/final lift, and DROP2&4 is controlled low-frequency color. The v2_6_48 checkpoint adds phrase-scope visibility before any runtime lock: section-local four-region windows expose method switches, ii-V/V-I/ii-V-I consistency, DROP2&4 run length, and whether method switches coincide with high voice-leading motion.
