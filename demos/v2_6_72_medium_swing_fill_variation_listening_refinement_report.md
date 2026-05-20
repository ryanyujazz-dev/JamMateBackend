# v2_6_72 — Medium Swing Fill/Variation Listening Refinement After User Review

Contract version: `v2_10_8`

Medium Swing piano fill/variation listening refinement after user review. v2_6_72 keeps the v2_6_71 three-candidate optional vocabulary unchanged and only refines context/history multipliers: variation remains low-intrusion, transition fill prefers phrase/section/turnaround contexts, and busy fill stays heavily guarded. No fill selector, bar-first phrase route, voicing logic, or final expression values are introduced.

Acceptance Passed: **True**

## Static Audit
- Optional vocabulary policy: `v2_6_71` enabled=True
- Optional refinement policy: `v2_6_72` enabled=True
- Optional candidate count: `3`
- Optional roles: `{'variation': 1, 'transition_fill': 1, 'busy_fill': 1}`
- Prior policy mismatches: `{}`
- Pattern expression leakage candidates: `0`
- Pattern voicing leakage candidates: `0`
- Bar-first/two_chord_bar markers: `0`

## Demo Outputs
### All the Things You Are
- MIDI: `demos/v2_6_72_all_the_things_you_are_medium_swing_fill_variation_listening_refinement_demo.mid`
- Piano pattern events: `206`
- Optional selected region patterns: `3`
- Optional status counts: `{'optional_context_allowed': 3}`
- Optional role counts: `{'variation': 3}`
- History summary: `{'activity_class_counts': {'stable': 89, 'offbeat': 26, 'active': 5}, 'consecutive_busy_count': 0, 'consecutive_fill_count': 0, 'consecutive_tail_push_count': 0}`
- Voicing summary: `{'top_note_max': 72, 'top_note_ge_75_events': 0, 'voice_leading_warning_events': 0, 'register_guard_failed_events': 0, 'method_counts': {'drop2': 99, 'drop3': 99, 'drop2_and_4': 8}}`

### Autumn Leaves
- MIDI: `demos/v2_6_72_autumn_leaves_medium_swing_fill_variation_listening_refinement_demo.mid`
- Piano pattern events: `232`
- Optional selected region patterns: `0`
- Optional status counts: `{}`
- Optional role counts: `{}`
- History summary: `{'activity_class_counts': {'stable': 131, 'offbeat': 30, 'active': 1}, 'consecutive_busy_count': 0, 'consecutive_fill_count': 0, 'consecutive_tail_push_count': 0}`
- Voicing summary: `{'top_note_max': 73, 'top_note_ge_75_events': 0, 'voice_leading_warning_events': 0, 'register_guard_failed_events': 0, 'method_counts': {'drop2': 90, 'drop2_and_4': 36, 'drop3': 106}}`

## Recommended Next Tasks
- v2_6_73_engine_medium_swing_phrase_end_fill_context_precision_if_needed
- v2_6_74_engine_medium_swing_standard_tune_fill_frequency_checkpoint_if_needed
