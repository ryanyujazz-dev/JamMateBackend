# Medium Swing OPEN Drop-Family Section Boundary Method-Lock Review

- Contract version: `v2_10_8`
- Milestone: `v2_6_47 — Medium Swing OPEN Drop-Family Section Boundary Method-Lock Review`
- Acceptance passed: `True`

## All the Things You Are

- MIDI: `demos/v2_10_8_all_the_things_you_are_medium_swing_demo.mid`
- Events: `174`
- Families: `{'open': 174}`
- Methods: `{'drop2': 104, 'drop3': 69, 'drop2_and_4': 1}`
- Contrast roles: `{'baseline_open_swing': 92, 'bridge_open_contrast': 36, 'final_chorus_open_lift': 46}`
- Methods by contrast role: `{'baseline_open_swing': {'drop2': 75, 'drop3': 17}, 'bridge_open_contrast': {'drop3': 25, 'drop2': 11}, 'final_chorus_open_lift': {'drop3': 27, 'drop2': 18, 'drop2_and_4': 1}}`
- Percentages by contrast role: `{'baseline_open_swing': {'drop2': 0.8152, 'drop3': 0.1848}, 'bridge_open_contrast': {'drop3': 0.6944, 'drop2': 0.3056}, 'final_chorus_open_lift': {'drop3': 0.587, 'drop2': 0.3913, 'drop2_and_4': 0.0217}}`
- OPEN method weight plans: `{'baseline_open_swing': {'generic_open': 0.0, 'drop2': 0.52, 'drop3': 0.38, 'drop2_and_4': 0.1}, 'bridge_open_contrast': {'generic_open': 0.0, 'drop2': 0.35, 'drop3': 0.53, 'drop2_and_4': 0.1}, 'final_chorus_open_lift': {'generic_open': 0.0, 'drop2': 0.43, 'drop3': 0.48, 'drop2_and_4': 0.08}}`
- Voice-leading transitions: `119`
- Voice-leading warnings: `0`
- Method-switch / section-boundary warnings: `0` / `0`
- Top / low / avg-motion max: `5` / `7` / `5.25`
- Section-boundary review events / warnings: `11` / `0`
- Section-boundary entry methods by role: `{'baseline_open_swing': {'drop2': 4, 'drop3': 1}, 'bridge_open_contrast': {'drop3': 3}, 'final_chorus_open_lift': {'drop3': 2, 'drop2': 1}}`
- Section-boundary method pairs: `{'drop2->drop2': 2, 'drop2->drop3': 5, 'drop3->drop2': 3, 'drop3->drop3': 1}`

## Autumn Leaves

- MIDI: `demos/v2_10_8_autumn_leaves_medium_swing_demo.mid`
- Events: `223`
- Families: `{'open': 223}`
- Methods: `{'drop2': 87, 'drop3': 103, 'drop2_and_4': 33}`
- Contrast roles: `{'baseline_open_swing': 116, 'bridge_open_contrast': 50, 'final_chorus_open_lift': 57}`
- Methods by contrast role: `{'baseline_open_swing': {'drop2': 66, 'drop3': 34, 'drop2_and_4': 16}, 'bridge_open_contrast': {'drop3': 42, 'drop2_and_4': 6, 'drop2': 2}, 'final_chorus_open_lift': {'drop3': 27, 'drop2_and_4': 11, 'drop2': 19}}`
- Percentages by contrast role: `{'baseline_open_swing': {'drop2': 0.569, 'drop3': 0.2931, 'drop2_and_4': 0.1379}, 'bridge_open_contrast': {'drop3': 0.84, 'drop2_and_4': 0.12, 'drop2': 0.04}, 'final_chorus_open_lift': {'drop3': 0.4737, 'drop2_and_4': 0.193, 'drop2': 0.3333}}`
- OPEN method weight plans: `{'baseline_open_swing': {'generic_open': 0.0, 'drop2': 0.52, 'drop3': 0.38, 'drop2_and_4': 0.1}, 'bridge_open_contrast': {'generic_open': 0.0, 'drop2': 0.35, 'drop3': 0.53, 'drop2_and_4': 0.1}, 'final_chorus_open_lift': {'generic_open': 0.0, 'drop2': 0.43, 'drop3': 0.48, 'drop2_and_4': 0.08}}`
- Voice-leading transitions: `161`
- Voice-leading warnings: `0`
- Method-switch / section-boundary warnings: `0` / `0`
- Top / low / avg-motion max: `5` / `7` / `5.25`
- Section-boundary review events / warnings: `11` / `0`
- Section-boundary entry methods by role: `{'baseline_open_swing': {'drop2': 3, 'drop3': 2}, 'bridge_open_contrast': {'drop3': 1, 'drop2': 2}, 'final_chorus_open_lift': {'drop3': 3}}`
- Section-boundary method pairs: `{'drop3->drop2': 5, 'drop2_and_4->drop3': 2, 'drop3->drop3': 3, 'drop2->drop3': 1}`

## Acceptance checks

- `all_the_things_you_are: generated`: `True` — `{'ok': True}`
- `all_the_things_you_are: enough three-chorus piano events`: `True` — `{'events': 174}`
- `all_the_things_you_are: open family only`: `True` — `{'families': {'open': 174}}`
- `all_the_things_you_are: all texture contrast roles present`: `True` — `{'roles': {'baseline_open_swing': 92, 'bridge_open_contrast': 36, 'final_chorus_open_lift': 46}}`
- `all_the_things_you_are: multiple open methods realized`: `True` — `{'methods': {'drop2': 104, 'drop3': 69, 'drop2_and_4': 1}}`
- `all_the_things_you_are: bridge increases drop3 share over baseline`: `True` — `{'baseline_drop3': 0.1848, 'bridge_drop3': 0.6944}`
- `all_the_things_you_are: final chorus increases drop3 share over baseline after generic-open removal`: `True` — `{'baseline_drop3': 0.1848, 'final_drop3': 0.587}`
- `all_the_things_you_are: drop2_and_4 remains controlled`: `True` — `{'methods': {'drop2': 104, 'drop3': 69, 'drop2_and_4': 1}, 'drop2_and_4_total_ratio': 0.005747126436781609}`
- `all_the_things_you_are: no failed register guards`: `True` — `{'failed': 0}`
- `all_the_things_you_are: no missing piano note events`: `True` — `{'missing': 0}`
- `all_the_things_you_are: open/drop cross-region voice-leading checkpoint passes`: `True` — `{'transitions': 119, 'warnings': 0, 'top_motion_max_abs': 5, 'avg_motion_max': 5.25, 'legacy_output_without_v2_6_46_fields': False}`
- `all_the_things_you_are: method switches remain smooth`: `True` — `{'method_switch_events': 51, 'method_switch_warnings': 0}`
- `all_the_things_you_are: section boundaries remain smooth`: `True` — `{'section_boundary_events': 11, 'section_boundary_warnings': 0}`
- `all_the_things_you_are: section-boundary method-lock readability passes`: `True` — `{'boundary_events': 11, 'warnings': 0, 'drop2_and_4_entry_events': 0, 'entry_methods_by_role': {'baseline_open_swing': {'drop2': 4, 'drop3': 1}, 'bridge_open_contrast': {'drop3': 3}, 'final_chorus_open_lift': {'drop3': 2, 'drop2': 1}}, 'legacy_output_without_v2_6_47_fields': False}`
- `autumn_leaves: generated`: `True` — `{'ok': True}`
- `autumn_leaves: enough three-chorus piano events`: `True` — `{'events': 223}`
- `autumn_leaves: open family only`: `True` — `{'families': {'open': 223}}`
- `autumn_leaves: all texture contrast roles present`: `True` — `{'roles': {'baseline_open_swing': 116, 'bridge_open_contrast': 50, 'final_chorus_open_lift': 57}}`
- `autumn_leaves: multiple open methods realized`: `True` — `{'methods': {'drop2': 87, 'drop3': 103, 'drop2_and_4': 33}}`
- `autumn_leaves: bridge increases drop3 share over baseline`: `True` — `{'baseline_drop3': 0.2931, 'bridge_drop3': 0.84}`
- `autumn_leaves: final chorus increases drop3 share over baseline after generic-open removal`: `True` — `{'baseline_drop3': 0.2931, 'final_drop3': 0.4737}`
- `autumn_leaves: drop2_and_4 remains controlled`: `True` — `{'methods': {'drop2': 87, 'drop3': 103, 'drop2_and_4': 33}, 'drop2_and_4_total_ratio': 0.14798206278026907}`
- `autumn_leaves: no failed register guards`: `True` — `{'failed': 0}`
- `autumn_leaves: no missing piano note events`: `True` — `{'missing': 0}`
- `autumn_leaves: open/drop cross-region voice-leading checkpoint passes`: `True` — `{'transitions': 161, 'warnings': 0, 'top_motion_max_abs': 5, 'avg_motion_max': 5.25, 'legacy_output_without_v2_6_46_fields': False}`
- `autumn_leaves: method switches remain smooth`: `True` — `{'method_switch_events': 68, 'method_switch_warnings': 0}`
- `autumn_leaves: section boundaries remain smooth`: `True` — `{'section_boundary_events': 11, 'section_boundary_warnings': 0}`
- `autumn_leaves: section-boundary method-lock readability passes`: `True` — `{'boundary_events': 11, 'warnings': 0, 'drop2_and_4_entry_events': 0, 'entry_methods_by_role': {'baseline_open_swing': {'drop2': 3, 'drop3': 2}, 'bridge_open_contrast': {'drop3': 1, 'drop2': 2}, 'final_chorus_open_lift': {'drop3': 3}}, 'legacy_output_without_v2_6_47_fields': False}`

## Reading note

This is an observational audit: it verifies actual selected projection methods and cross-region voice-leading from runtime debug, not just policy metadata. Medium Swing still stays in OPEN family; generic_open has zero normal runtime weight and remains available only for explicit rescue/fallback. DROP2 is the baseline body, DROP3 is bridge/final lift, and DROP2&4 is controlled low-frequency color. The v2_6_47 checkpoint confirms section-boundary entries stay readable: DROP2/DROP3 carry the boundary transitions, DROP2&4 does not enter boundaries, and cross-boundary motion remains smooth before any further weighting changes.
