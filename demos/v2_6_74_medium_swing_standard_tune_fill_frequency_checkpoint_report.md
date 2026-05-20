# v2_6_74 — Medium Swing Standard-Tune Fill Frequency Checkpoint

Contract version: `v2_10_8`

Behavior-preserving Medium Swing standard-tune fill frequency checkpoint. v2_6_74 measures how often the v2_6_71 optional variation/fill vocabulary is actually selected after v2_6_72 listening refinement and v2_6_73 phrase-end precision, while checking continuity, pattern/expression/voicing boundaries, and standard-tune 3-chorus demo safety. No candidate weight, vocabulary, fill selector, voicing, expression numeric, API, Agent, or HarmonyOS behavior is changed.

Acceptance Passed: **True**

## Static Audit
- Checkpoint policy: `v2_6_74` enabled=True
- Optional vocabulary/refinement/precision: `v2_6_71` / `v2_6_72` / `v2_6_73`
- Optional candidate count: `3`
- Optional roles: `{'variation': 1, 'transition_fill': 1, 'busy_fill': 1}`
- Optional weights: `{'medium_swing_piano_optional_variation_1_2and_3and': 0.075, 'medium_swing_piano_optional_fill_2and_4_4and': 0.018, 'medium_swing_piano_optional_busy_1and_2and_3and_4': 0.004}`
- Policy mismatches: `{}`
- Pattern expression leakage candidates: `0`
- Pattern voicing leakage candidates: `0`
- Bar-first/two_chord_bar markers: `0`

## Aggregate Fill Frequency
- Selected region patterns total: `282`
- Optional selected total: `3`
- Optional selected ratio: `0.0106`
- Frequency band: `very_low_intrusion`
- Transition fill selected total: `0`
- Macro density gate needed now: `False`

## Demo Outputs
### All the Things You Are
- MIDI: `demos/v2_6_74_all_the_things_you_are_medium_swing_standard_tune_fill_frequency_checkpoint_demo.mid`
- Piano pattern events: `206`
- Selected region patterns: `120`
- Optional selected region patterns: `3`
- Optional selected ratio: `0.025`
- Optional role counts: `{'variation': 3}`
- Optional status counts: `{'optional_context_allowed': 3}`
- Phrase precision status counts: `{'harmonic_transition_without_phrase_tail': 3}`
- History summary: `{'activity_class_counts': {'stable': 89, 'offbeat': 26, 'active': 5}, 'consecutive_active_count': 0, 'consecutive_busy_count': 0, 'consecutive_fill_count': 0, 'consecutive_tail_push_count': 0}`
- Voicing summary: `{'top_note_max': 72, 'top_note_ge_75_events': 0, 'voice_leading_warning_events': 0, 'register_guard_failed_events': 0, 'method_counts': {'drop2': 99, 'drop3': 99, 'drop2_and_4': 8}}`

### Autumn Leaves
- MIDI: `demos/v2_6_74_autumn_leaves_medium_swing_standard_tune_fill_frequency_checkpoint_demo.mid`
- Piano pattern events: `232`
- Selected region patterns: `162`
- Optional selected region patterns: `0`
- Optional selected ratio: `0.0`
- Optional role counts: `{}`
- Optional status counts: `{}`
- Phrase precision status counts: `{}`
- History summary: `{'activity_class_counts': {'stable': 131, 'offbeat': 30, 'active': 1}, 'consecutive_active_count': 0, 'consecutive_busy_count': 0, 'consecutive_fill_count': 0, 'consecutive_tail_push_count': 0}`
- Voicing summary: `{'top_note_max': 73, 'top_note_ge_75_events': 0, 'voice_leading_warning_events': 0, 'register_guard_failed_events': 0, 'method_counts': {'drop2': 90, 'drop2_and_4': 36, 'drop3': 106}}`

## Recommended Next Tasks
- v2_6_75_engine_medium_swing_optional_fill_density_macro_gate_only_if_frequency_rises
- v2_6_76_engine_medium_swing_piano_comping_checkpoint_or_return_to_voicing_line
