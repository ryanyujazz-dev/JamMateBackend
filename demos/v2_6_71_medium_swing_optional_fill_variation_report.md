# v2_6_71 — Medium Swing Optional Fill/Variation Vocabulary Activation

Contract version: `v2_10_8`

Medium Swing piano optional fill/variation vocabulary activation. v2_6_71 adds only three pitchless, low-weight 4-beat ChordRegion candidates and reweights them by region context/history inside the existing StyleProfile path. It does not add a fill selector, bar-first phrase route, voicing logic, or final expression values.

Acceptance Passed: **True**

## Static Audit
- Optional policy: `v2_6_71` enabled=True
- Optional candidate count: `3`
- Optional roles: `{'variation': 1, 'transition_fill': 1, 'busy_fill': 1}`
- Prior policy mismatches: `{}`
- Pattern expression leakage candidates: `0`
- Pattern voicing leakage candidates: `0`
- Bar-first/two_chord_bar markers: `0`

## Demo Outputs
### All the Things You Are
- MIDI: `demos/v2_6_71_all_the_things_you_are_medium_swing_optional_fill_variation_demo.mid`
- Piano pattern events: `206`
- Optional selected region patterns: `3`
- Optional status counts: `{'optional_context_allowed': 3}`
- Optional role counts: `{'variation': 3}`
- History summary: `{'activity_class_counts': {'stable': 89, 'offbeat': 26, 'active': 5}, 'consecutive_busy_count': 0, 'consecutive_fill_count': 0, 'consecutive_tail_push_count': 0}`
- Voicing summary: `{'top_note_max': 72, 'top_note_ge_75_events': 0, 'voice_leading_warning_events': 0, 'register_guard_failed_events': 0, 'method_counts': {'drop2': 99, 'drop3': 99, 'drop2_and_4': 8}}`

### Autumn Leaves
- MIDI: `demos/v2_6_71_autumn_leaves_medium_swing_optional_fill_variation_demo.mid`
- Piano pattern events: `232`
- Optional selected region patterns: `0`
- Optional status counts: `{}`
- Optional role counts: `{}`
- History summary: `{'activity_class_counts': {'stable': 131, 'offbeat': 30, 'active': 1}, 'consecutive_busy_count': 0, 'consecutive_fill_count': 0, 'consecutive_tail_push_count': 0}`
- Voicing summary: `{'top_note_max': 73, 'top_note_ge_75_events': 0, 'voice_leading_warning_events': 0, 'register_guard_failed_events': 0, 'method_counts': {'drop2': 90, 'drop2_and_4': 36, 'drop3': 106}}`

## Recommended Next Tasks
- v2_6_72_engine_medium_swing_fill_variation_listening_refinement_after_user_review
- v2_6_73_engine_medium_swing_phrase_end_fill_context_precision_if_needed
