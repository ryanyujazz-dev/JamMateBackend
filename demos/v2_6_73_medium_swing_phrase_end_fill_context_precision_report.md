# v2_6_73 — Medium Swing Phrase-End Fill Context Precision

Contract version: `v2_10_8`

Medium Swing phrase-end fill context precision. v2_6_73 keeps the v2_6_71/v2_6_72 optional fill vocabulary and listening-refinement layers unchanged, then narrows the existing transition-fill bonus toward explicit phrase ends, section tails, and 4/8-bar phrase tails while downweighting harmonic-transition-only regions. No phrase engine, fill selector, new vocabulary, voicing logic, or final expression values are introduced.

Acceptance Passed: **True**

## Static Audit
- Optional vocabulary policy: `v2_6_71` enabled=True
- Optional refinement policy: `v2_6_72` enabled=True
- Phrase-end precision policy: `v2_6_73` enabled=True
- Optional candidate count: `3`
- Optional roles: `{'variation': 1, 'transition_fill': 1, 'busy_fill': 1}`
- Prior policy mismatches: `{}`
- Pattern expression leakage candidates: `0`
- Pattern voicing leakage candidates: `0`
- Bar-first/two_chord_bar markers: `0`

## Demo Outputs
### All the Things You Are
- MIDI: `demos/v2_6_73_all_the_things_you_are_medium_swing_phrase_end_fill_context_precision_demo.mid`
- Piano pattern events: `206`
- Optional selected region patterns: `3`
- Optional status counts: `{'optional_context_allowed': 3}`
- Optional role counts: `{'variation': 3}`
- Phrase precision status counts: `{'harmonic_transition_without_phrase_tail': 3}`
- History summary: `{'activity_class_counts': {'stable': 89, 'offbeat': 26, 'active': 5}, 'consecutive_busy_count': 0, 'consecutive_fill_count': 0, 'consecutive_tail_push_count': 0}`
- Voicing summary: `{'top_note_max': 72, 'top_note_ge_75_events': 0, 'voice_leading_warning_events': 0, 'register_guard_failed_events': 0, 'method_counts': {'drop2': 99, 'drop3': 99, 'drop2_and_4': 8}}`

### Autumn Leaves
- MIDI: `demos/v2_6_73_autumn_leaves_medium_swing_phrase_end_fill_context_precision_demo.mid`
- Piano pattern events: `232`
- Optional selected region patterns: `0`
- Optional status counts: `{}`
- Optional role counts: `{}`
- Phrase precision status counts: `{}`
- History summary: `{'activity_class_counts': {'stable': 131, 'offbeat': 30, 'active': 1}, 'consecutive_busy_count': 0, 'consecutive_fill_count': 0, 'consecutive_tail_push_count': 0}`
- Voicing summary: `{'top_note_max': 73, 'top_note_ge_75_events': 0, 'voice_leading_warning_events': 0, 'register_guard_failed_events': 0, 'method_counts': {'drop2': 90, 'drop2_and_4': 36, 'drop3': 106}}`

## Recommended Next Tasks
- v2_6_74_engine_medium_swing_standard_tune_fill_frequency_checkpoint_if_needed
- v2_6_75_engine_medium_swing_optional_fill_density_macro_gate_if_needed
