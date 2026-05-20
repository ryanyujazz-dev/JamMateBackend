# v2_6_62 — Engine Medium Swing CoverageGuard Region-First Cleanup

## Scope

Engine-only Medium Swing piano pattern/coverage checkpoint.

This pass does **not** add piano rhythm cells, voicing behavior, expression realization parameters, deliberate revoice gestures, MIDI writer behavior, Agent/API/HarmonyOS logic, or a parallel pattern selector.

## Design intent

V2 is ChordRegion-first. Coverage must therefore be checked at the ChordRegion level, not by a bar-first or two-chord-bar assumption.

The v2_6_62 contract is:

```text
ChordRegion-length pattern policy chooses the piano comping candidate first.
CoverageGuard then checks the selected PatternPlan.
If the selected region already has piano harmonic presence, only audit metadata is stamped.
If a ChordRegion would otherwise be uncovered, insert one pitchless region-start fallback anchor.
CoverageGuard never chooses voicing, duration, velocity, pedal, or a bar-level pattern.
```

## Runtime placement

The guard is intentionally placed in the existing `StyleProfile.plan_region()` path:

```text
ChordRegion-length candidate pool
→ repeat/category guard
→ harmonic-function multiplier
→ history-continuity scorer
→ weighted sampling
→ PatternPlan.combine()
→ v2_6_62 region-first CoverageGuard
→ AnticipationResolver
→ ExpressionResolver
→ Voicing/realization
```

This avoids a shadow planner or parallel pattern path.

## Implementation notes

Changed files:

```text
src/jammate_engine/styles/base.py
src/jammate_engine/styles/medium_swing/arrangement_policy.py
tests/test_v2_6_62_engine_medium_swing_coverage_guard_region_first_cleanup.py
examples/scripts/generate_medium_swing_region_first_coverage_guard_audit.py
docs/ENGINE_MEDIUM_SWING_COVERAGE_GUARD_REGION_FIRST_CLEANUP_V2_6_62.md
```

Key metadata stamped on piano events:

```text
piano_region_first_coverage_guard_version = v2_6_62
piano_region_first_coverage_guard_checked = true
piano_region_first_coverage_guard_outcome
piano_region_first_coverage_guard_inserted
coverage_time_reference = region_local_beats
coverage_region_duration_beats
coverage_region_length_family
coverage_guard_is_backup_only = true
```

## Standard-tune audit

### All The Things You Are / Medium Swing / 3 choruses

```text
expected_region_count: 120
covered_region_count: 120
uncovered_region_count: 0
short_uncovered_region_count: 0
piano_events: 207
coverage_inserted_events: 0
max_piano_events_per_region: 3
top_note_max: 72
top_note_ge_75_events: 0
voice_leading_warning_events: 0
```

### Autumn Leaves / Medium Swing / 3 choruses

```text
expected_region_count: 162
covered_region_count: 162
uncovered_region_count: 0
short_uncovered_region_count: 0
piano_events: 223
coverage_inserted_events: 0
max_piano_events_per_region: 2
top_note_max: 72
top_note_ge_75_events: 0
voice_leading_warning_events: 0
```

## Validation

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
  tests/test_v2_6_62_engine_medium_swing_coverage_guard_region_first_cleanup.py
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_v2_10_7_integration_harmonyos_agent_today_guidance_runtime_smoke.py
PYTHONPATH=src python examples/scripts/generate_medium_swing_region_first_coverage_guard_audit.py
```

Observed results:

```text
compileall: passed
harness: HARNESS OK
v2_6_44 ~ v2_6_49: 21 passed
v2_6_50 ~ v2_6_62: 54 passed
integration smoke: 3 passed
demo/audit generation: ok
```

## Recommended next task

```text
v2_6_63_engine_medium_swing_piano_expression_hint_handoff_checkpoint
```

The next task should confirm that Medium Swing piano pattern events only carry semantic expression hints (`soft_hold`, `light_stab`, `accent_stab`, `backbeat_hold`, `final_hold`) and that final velocity/duration/pedal decisions remain owned by ExpressionPolicy.
