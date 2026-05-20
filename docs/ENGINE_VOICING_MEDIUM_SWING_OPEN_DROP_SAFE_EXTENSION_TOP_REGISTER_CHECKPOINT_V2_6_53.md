# Engine Voicing — Medium Swing OPEN/DROP Safe Extension + Top Register Checkpoint v2_6_53

## Scope

`v2_6_53` is an Engine voicing-only, behavior-preserving checkpoint on top of `v2_6_52`.

It does not change:

- Pattern
- Anticipation
- Expression
- Gesture realization
- MIDI writer
- Agent
- API
- HarmonyOS fixtures
- shared integration docs

The goal is to freeze the current Medium Swing OPEN/DROP voicing guardrails after:

- `v2_6_49` local ii–V / V–I method-lock policy
- `v2_6_51` generic 4-note rotation alignment
- `v2_6_52` same-chord reattack / comping reuse

## Why this checkpoint exists

After DROP2 / DROP3 method lock and generic 4-note ABA/BAB rotation alignment, the main risk is not phrase method continuity anymore. The risk is that OPEN/DROP voicings might drift too high or that safe extension logic might introduce too much brightness, especially unnotated major-seventh `#11`.

This checkpoint confirms that the current default Medium Swing runtime remains calm:

```text
projection family: OPEN only
top_note_max_allowed: 72
top_note_ge_75_events: 0
unnotated major-seventh #11 events: 0
register guard failed events: 0
voice-leading warning events: 0
```

## Safe-extension rule

Medium Swing inherits the same global harmonic-expansion principle:

```text
chord-symbol-only mode:
  stay faithful to the written chord symbol
  do not add gratuitous unnotated #11

major-seventh safe colors when expansion is allowed:
  prefer 9 / 13
  keep #11 disabled unless the chart explicitly writes it or a harmonic-color intent requests it
```

In the current default standard-tune demos, major-seventh events are mostly basic 4-note seventh voicings. That is acceptable: this checkpoint is not trying to force more color. It only confirms that the current OPEN/DROP + rotation alignment chain does not accidentally create bright or unnotated major-seventh colors.

## Accepted audit references

### All The Things You Are / Medium Swing / 3 choruses / seed 3300

```text
events: 174
projection family: open only
methods: drop2=94, drop2_and_4=2, drop3=78
top_note_max: 72
low_note_min: 48
top_note_ge_75_events: 0
major_seventh_events: 71
major_seventh_color_events: 0
major_seventh_unnotated_sharp11_events: 0
register_guard_failed_events: 0
voice_leading_warning_events: 0
checkpoint_passed: true
```

### Autumn Leaves / Medium Swing / 3 choruses / seed 3301

```text
events: 223
projection family: open only
methods: drop2=122, drop3=83, drop2_and_4=18
top_note_max: 72
low_note_min: 48
top_note_ge_75_events: 0
major_seventh_events: 56
major_seventh_color_events: 0
major_seventh_unnotated_sharp11_events: 0
register_guard_failed_events: 0
voice_leading_warning_events: 0
checkpoint_passed: true
```

## Policy metadata

Medium Swing declares:

```text
medium_swing_open_drop_safe_extension_top_register_checkpoint_version = v2_6_53
medium_swing_open_drop_safe_extension_top_register_checkpoint_enabled = true
```

The target explicitly records:

```text
scope = medium_swing_open_drop_actual_runtime
projection_family = open
top_note_max_allowed = 72
top_note_ge_75_events = 0
major_seventh_default_preferred_colors = [9, 13]
major_seventh_sharp11_default = disabled_unless_explicit_symbol_or_harmonic_color_intent
register_guard_failed_events = 0
voice_leading_warning_events = 0
behavior_preserving = true
no_runtime_candidate_change = true
```

## Next recommended task

Recommended next task:

```text
v2_6_54_engine_medium_swing_open_drop_deliberate_revoice_gesture_boundary_plan
```

Rationale: `v2_6_52` freezes same-chord reattack reuse by default. The next useful voicing question is not accidental re-selection, but how to represent deliberate same-chord movement as an explicit gesture or `fresh-revoicing` intent without breaking the cached-region default.
