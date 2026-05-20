# v2_6_77 — Medium Swing Existing Voicing Capability Usage Policy

Acceptance Passed: **True**

## Scope
Medium Swing can request already-existing grouped SPREAD 5/6-note capability from style/event policy when explicitly enabled. Ordinary runtime comping remains OPEN/DROP 4-note by default. The task does not modify core voicing source, projection, selector, expression, pattern, API, Agent, or HarmonyOS behavior.

## Aggregate
- Piano voicing events: 438
- Grouped SPREAD events: 17
- 5-note events: 13
- 6-note events: 4
- 5/6 ratio: 0.0388
- Ordinary-body 5/6 events: 0
- Voice-leading warnings: 0
- Max top note: 73

## Per Tune
### All the Things You Are
- MIDI: `demos/v2_6_77_all_the_things_you_are_medium_swing_existing_voicing_capability_usage_demo.mid`
- Piano voicing events: 206
- Density counts: `{'4': 198, '5': 6, '6': 2}`
- Recipe counts: `{'d4__2plus2__seventh_chord_basic__rootless_allowed': 130, 'd4__1plus3__seventh_chord_basic__rootless_allowed': 68, 'spread_2plus3_contract': 6, 'spread_3plus3_contract': 2}`
- 5-note / 6-note: 6 / 2
- Section-tail 5/6 events: 8
- Ending 5/6 events: 2
- Voice-leading warnings: 0

### Autumn Leaves
- MIDI: `demos/v2_6_77_autumn_leaves_medium_swing_existing_voicing_capability_usage_demo.mid`
- Piano voicing events: 232
- Density counts: `{'4': 223, '5': 7, '6': 2}`
- Recipe counts: `{'d4__1plus3__seventh_chord_basic__rootless_allowed': 90, 'd4__2plus2__seventh_chord_basic__rootless_allowed': 133, 'spread_2plus3_contract': 7, 'spread_2plus4_contract': 2}`
- 5-note / 6-note: 7 / 2
- Section-tail 5/6 events: 9
- Ending 5/6 events: 2
- Voice-leading warnings: 0

## Acceptance Checks

- policy_version_declared: True
- policy_available_but_default_opt_in: True
- no_core_voicing_change_declared: True
- ordinary_base_policy_still_open_4note: True
- patterns_still_no_expression_or_voicing_leakage: True
- patterns_still_region_first: True
- existing_5note_capability_used: True
- existing_6note_capability_used: True
- ordinary_body_not_thickened: True
- voice_leading_guard_ok: True
- top_register_ok: True
