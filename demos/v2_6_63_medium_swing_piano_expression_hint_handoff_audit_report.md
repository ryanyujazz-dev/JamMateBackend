# v2_6_63 — Medium Swing Piano Expression-Hint Handoff Checkpoint

Audit that Medium Swing piano patterns carry semantic expression hints only, include accent_hold, and that hold-style hints are resolved by ExpressionResolver as hold-until-next-touch durations rather than fixed pattern durations.

## All the Things You Are

- MIDI: `demos/v2_6_63_all_the_things_you_are_medium_swing_piano_expression_hint_handoff_demo.mid`
- Piano events: `207`
- Semantic hint counts: `{'soft_hold': 73, 'light_stab': 58, 'backbeat_hold': 59, 'accent_hold': 17}`
- Profile counts: `{'comp_medium': 73, 'comp_short': 58, 'comp_backbeat_hold': 59, 'comp_accent_hold': 17}`
- Hold events / next-touch applied / missing: `149` / `149` / `0`
- Hold reasons: `{'held_until_next_same_track_touch': 148, 'no_next_same_track_touch_held_to_region_end': 1}`
- Accent-hold events/profile events/duration range: `17` / `17` / `1.6666666666666572`–`2.0`
- Missing handoff / invalid hints / forbidden pattern keys: `0` / `0` / `0`
- Duration min/max: `0.3333333333333144` / `6.0`
- Top note max / >=75 / voice-leading warnings: `72` / `0` / `0`

## Autumn Leaves

- MIDI: `demos/v2_6_63_autumn_leaves_medium_swing_piano_expression_hint_handoff_demo.mid`
- Piano events: `223`
- Semantic hint counts: `{'soft_hold': 99, 'light_stab': 83, 'backbeat_hold': 35, 'accent_hold': 6}`
- Profile counts: `{'comp_medium': 99, 'comp_short': 83, 'comp_backbeat_hold': 35, 'comp_accent_hold': 6}`
- Hold events / next-touch applied / missing: `140` / `140` / `0`
- Hold reasons: `{'held_until_next_same_track_touch': 139, 'no_next_same_track_touch_held_to_region_end': 1}`
- Accent-hold events/profile events/duration range: `6` / `6` / `1.6666666666666572`–`1.6666666666666856`
- Missing handoff / invalid hints / forbidden pattern keys: `0` / `0` / `0`
- Duration min/max: `0.3333333333333144` / `4.0`
- Top note max / >=75 / voice-leading warnings: `72` / `0` / `0`

## Acceptance

Passed: `True`

- `all_the_things_you_are: generation ok`: `True`
- `all_the_things_you_are: all piano events carry v2_6_63 handoff metadata`: `True`
- `all_the_things_you_are: semantic hints stay in approved set`: `True`
- `all_the_things_you_are: patterns still contain no final expression values`: `True`
- `all_the_things_you_are: hold hints use next-touch duration semantics`: `True`
- `all_the_things_you_are: non-hold hints do not accidentally use hold semantics`: `True`
- `all_the_things_you_are: accent_hold is available and routed`: `True`
- `all_the_things_you_are: top register calm`: `True`
- `all_the_things_you_are: voice-leading warnings calm`: `True`
- `autumn_leaves: generation ok`: `True`
- `autumn_leaves: all piano events carry v2_6_63 handoff metadata`: `True`
- `autumn_leaves: semantic hints stay in approved set`: `True`
- `autumn_leaves: patterns still contain no final expression values`: `True`
- `autumn_leaves: hold hints use next-touch duration semantics`: `True`
- `autumn_leaves: non-hold hints do not accidentally use hold semantics`: `True`
- `autumn_leaves: accent_hold is available and routed`: `True`
- `autumn_leaves: top register calm`: `True`
- `autumn_leaves: voice-leading warnings calm`: `True`
