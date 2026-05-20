# v2_6_61 — Engine Medium Swing Region-First Anticipation Compatibility Checkpoint

## Scope

This is a behavior-preserving Engine checkpoint after the v2_6_56~v2_6_60 Medium Swing piano region-length pattern work.

It does **not** add new patterns, voicings, gestures, expression realization parameters, MIDI writer behavior, Agent behavior, API behavior, or HarmonyOS fixtures.

The goal is to prove and annotate that Medium Swing anticipation remains **ChordRegion-first**:

```text
previous ChordRegion tail slot
= previous_region.start_beat + previous_region.duration_beats - 0.5
```

Therefore:

```text
4-beat previous region → local 3.5  (written 4& in a 4/4 full-bar region)
2-beat previous region → local 1.5  (local 2& inside that region)
1-beat previous region → local 0.5, but ordinary anchor occupancy will usually block it
```

This avoids reverting to a bar-first assumption where every anticipation is treated as a literal bar 4&.

## Implementation notes

Updated existing runtime/policy surfaces only:

```text
src/jammate_engine/core/anticipation/anticipation_resolver.py
src/jammate_engine/styles/medium_swing/anticipation_policy.py
src/jammate_engine/styles/medium_swing/arrangement_policy.py
examples/scripts/generate_medium_swing_region_first_anticipation_audit.py
tests/test_v2_6_61_engine_medium_swing_region_first_anticipation_compatibility_checkpoint.py
```

The AnticipationResolver already used the real `HarmonicRegion.duration_beats` for placement through `is_tail_slot_available()`. v2_6_61 adds explicit audit metadata to anticipated events:

```text
region_first_anticipation_compatibility_checkpoint_version = v2_6_61
previous_region_duration_beats
current_region_duration_beats
previous_region_last_beat_local
previous_region_last_upbeat_local
tail_checked_local_beats
tail_availability_reason
bar_first_4and_assumption = false
```

Medium Swing policy metadata now documents the region-first contract:

```text
medium_swing_light_region_tail_push
no_bar_first_4and_assumption = true
```

## Standard-tune audit

Generated three-chorus Medium Swing demos:

```text
All The Things You Are
Autumn Leaves
```

Summary:

```text
All The Things You Are:
active_anticipation_count: 8
target_local_counts: {3.5: 7, 1.5: 1}
previous_region_duration_counts: {4.0: 7, 2.0: 1}
invalid_region_first_rows: 0
top_note_max: 72
top_note_ge_75_events: 0
voice_leading_warning_events: 0

Autumn Leaves:
active_anticipation_count: 3
target_local_counts: {1.5: 2, 3.5: 1}
previous_region_duration_counts: {2.0: 2, 4.0: 1}
invalid_region_first_rows: 0
top_note_max: 72
top_note_ge_75_events: 0
voice_leading_warning_events: 0
```

The audit confirms that both 4-beat and 2-beat previous regions are handled through the same region-first rule.

## Validation

```bash
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src:. python tools/check_development_harness.py

PYTHONPATH=src:. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_v2_6_44_engine_ballad_spread_voicing_phase_summary_and_handoff.py \
  tests/test_v2_6_45_engine_medium_swing_open_drop_method_lock_calibration.py \
  tests/test_v2_6_46_engine_medium_swing_open_drop_voice_leading_continuity_audit.py \
  tests/test_v2_6_47_engine_medium_swing_open_drop_section_boundary_method_lock_review.py \
  tests/test_v2_6_48_engine_medium_swing_open_drop_phrase_scope_method_continuity_plan.py \
  tests/test_v2_6_49_engine_medium_swing_open_drop_phrase_scope_method_lock_policy.py

PYTHONPATH=src:. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
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
  tests/test_v2_6_61_engine_medium_swing_region_first_anticipation_compatibility_checkpoint.py

PYTHONPATH=src:. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_anticipation_resolver.py \
  tests/test_v2_3_5_anticipation_timing_grid_contract.py \
  tests/test_v2_5_8_ballad_swing8_anticipation_timing_patch.py

PYTHONPATH=src:. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_v2_10_7_integration_harmonyos_agent_today_guidance_runtime_smoke.py

PYTHONPATH=src:. python examples/scripts/generate_medium_swing_region_first_anticipation_audit.py
```

Observed:

```text
compileall: passed
harness: HARNESS OK
v2_6_44~49 regression: 21 passed
v2_6_50~61 regression: 50 passed
anticipation regression: 10 passed
integration smoke: 3 passed
demo/audit generation: ok
```

## Recommended next task

```text
v2_6_62_engine_medium_swing_coverage_guard_region_first_cleanup
```

Focus: ensure CoverageGuard remains a safety net after region-length pattern activation. It should protect short ChordRegions from silence without replacing the region-length pattern policy or making piano comping too dense.
