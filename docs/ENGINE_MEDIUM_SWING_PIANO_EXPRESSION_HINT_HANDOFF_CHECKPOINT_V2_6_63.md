# v2_6_63 Engine — Medium Swing Piano Expression-Hint Handoff Checkpoint

## Scope

This checkpoint keeps the current ChordRegion-first Medium Swing piano pattern line intact and only tightens the Pattern → Expression boundary.

It does not modify voicing, MIDI writing, anticipation placement, gesture generation, Agent, API, or HarmonyOS fixtures.

## Core decision

Patterns still do not write final performance values. They only carry semantic hints such as:

```text
soft_hold
light_stab
accent_stab
accent_hold
backbeat_hold
final_hold
```

`accent_hold` is added as a distinct semantic hint for an accented harmonic support event that should sustain like a hold, rather than behave like a short accent stab.

## Hold semantics

User correction accepted for this checkpoint:

```text
hold should sustain until the next piano touch
```

Therefore v2_6_63 introduces explicit expression-layer metadata:

```text
duration_semantics = hold_until_next_touch
duration_semantics_version = v2_6_63
```

The ExpressionResolver now resolves hold-style hints by looking at the next active same-track event. If a next same-track touch exists, the hold duration is the gap to that touch. If not, the duration falls back to the remaining ChordRegion duration when available, otherwise the profile duration is preserved.

This is expression-layer behavior. Pattern candidates still do not contain `duration`, `duration_beats`, `velocity`, or `pedal` values.

## Medium Swing profile mapping

```text
soft_hold     -> comp_medium         -> hold_until_next_touch
backbeat_hold -> comp_backbeat_hold  -> hold_until_next_touch
accent_hold   -> comp_accent_hold    -> hold_until_next_touch + accented touch
final_hold    -> comp_final_hold     -> hold_until_next_touch
light_stab    -> comp_short          -> short non-hold
accent_stab   -> comp_accent         -> accent short/stab
```

`accent_hold` is used for selected Charleston-style strong anchors. Tail-push events remain `accent_stab` so a rare 4& push does not smear.

## Audit result

```text
All The Things You Are:
  piano_events: 207
  hold_hint_events: 149
  hold_until_next_touch_applied_events: 149
  accent_hold_events: 17
  top_note_max: 72
  voice_leading_warning_events: 0

Autumn Leaves:
  piano_events: 223
  hold_hint_events: 140
  hold_until_next_touch_applied_events: 140
  accent_hold_events: 6
  top_note_max: 72
  voice_leading_warning_events: 0
```

## Verification

```bash
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python tools/check_development_harness.py
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_v2_6_44_engine_ballad_spread_voicing_phase_summary_and_handoff.py \
  tests/test_v2_6_45_engine_medium_swing_open_drop_method_lock_calibration.py \
  tests/test_v2_6_46_engine_medium_swing_open_drop_voice_leading_continuity_audit.py \
  tests/test_v2_6_47_engine_medium_swing_open_drop_section_boundary_method_lock_review.py \
  tests/test_v2_6_48_engine_medium_swing_open_drop_phrase_scope_method_continuity_plan.py \
  tests/test_v2_6_49_engine_medium_swing_open_drop_phrase_scope_method_lock_policy.py
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_v2_6_50_engine_medium_swing_open_drop_ii_v_i_orientation_method_alignment.py \
  tests/test_v2_6_51_engine_generic_4note_rotation_alignment_policy.py \
  tests/test_v2_6_52_engine_medium_swing_open_drop_same_chord_reattack_comping_reuse.py \
  tests/test_v2_6_53_engine_medium_swing_open_drop_safe_extension_top_register_checkpoint.py \
  tests/test_v2_6_54_engine_medium_swing_open_drop_deliberate_revoice_gesture_boundary_plan.py \
  tests/test_v2_6_55_engine_medium_swing_open_drop_deliberate_revoice_micro_motion_policy_probe.py \
  tests/test_v2_6_56_engine_medium_swing_piano_region_length_pattern_vocabulary.py \
  tests/test_v2_6_57_engine_medium_swing_piano_region_length_candidate_lookup_policy.py \
  tests/test_v2_6_58_engine_medium_swing_piano_region_length_weight_calibration.py \
  tests/test_v2_6_59_engine_medium_swing_piano_comping_history_continuity_scorer.py \
  tests/test_v2_6_60_engine_medium_swing_harmonic_function_aware_piano_comping_policy.py \
  tests/test_v2_6_61_engine_medium_swing_region_first_anticipation_compatibility_checkpoint.py \
  tests/test_v2_6_62_engine_medium_swing_coverage_guard_region_first_cleanup.py \
  tests/test_v2_6_63_engine_medium_swing_piano_expression_hint_handoff_checkpoint.py
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_v2_10_7_integration_harmonyos_agent_today_guidance_runtime_smoke.py
PYTHONPATH=src python examples/scripts/generate_medium_swing_piano_expression_hint_handoff_audit.py
```

## Recommended next task

`v2_6_64_engine_medium_swing_piano_standard_tune_listening_checkpoint`

Do not add more pattern cells yet. The next step should be a listening checkpoint over the accumulated region-length pattern, weighting, history, harmonic-function, anticipation, coverage, and expression-hint handoff work.
