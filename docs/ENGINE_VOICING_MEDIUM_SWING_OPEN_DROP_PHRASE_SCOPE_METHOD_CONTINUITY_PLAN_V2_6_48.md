# ENGINE v2_6_48 — Medium Swing OPEN / DROP Phrase-Scope Method Continuity Plan

## Scope

Engine voicing-only, behavior-preserving audit pass on top of the merged `v2_10_8` integration baseline plus Engine v2_6_47.

This pass does **not** change selected notes, OPEN method weights, Pattern, Anticipation, Expression, Gesture/realizer behavior, MIDI writer, Agent, API, HarmonyOS fixtures, or shared integration files.

## Why this pass exists

v2_6_45 to v2_6_47 already confirmed the broad Medium Swing OPEN / DROP-family state:

```text
DROP2 / DROP3 are the main OPEN methods
DROP2&4 remains controlled color
section-boundary entries avoid DROP2&4
cross-region voice-leading remains smooth
```

The next useful question is not another global weight tweak. The missing visibility is whether **inside a section**, local phrase windows feel method-continuous enough, especially around ii–V, V–I, and ii–V–I progressions.

## v2_6_48 implementation

Added an observational audit layer in `generation/piano_audit.py`:

```text
medium_swing_phrase_scope_method_continuity_version = v2_6_48
```

The audit derives phrase windows from actual runtime piano output:

```text
source rows: realized piano audit events
family:      OPEN only
methods:     drop2 / drop3 / drop2_and_4
scope:       section-local windows
window size: 4 chord-region entries
```

The audit reports:

```text
medium_swing_phrase_scope_events
medium_swing_phrase_scope_count
medium_swing_phrase_scope_method_switch_events
medium_swing_phrase_scope_method_switch_ratio
medium_swing_phrase_scope_drop2_and_4_run_events
medium_swing_phrase_scope_drop2_and_4_run_max
medium_swing_phrase_scope_ii_v_events
medium_swing_phrase_scope_v_i_events
medium_swing_phrase_scope_ii_v_i_events
medium_swing_phrase_scope_ii_v_i_method_consistent_events
medium_swing_phrase_scope_ii_v_i_method_switch_events
medium_swing_phrase_scope_progression_method_consistent_events
medium_swing_phrase_scope_progression_method_switch_events
medium_swing_phrase_scope_high_motion_switch_events
medium_swing_phrase_scope_warning_events
medium_swing_phrase_scope_checkpoint_passed
```

Checkpoint thresholds are intentionally conservative but not policy-forcing:

```text
phrase_scope_events_min: 20
method_switch_ratio_max: 0.70
drop2_and_4_run_max: 2
high_motion_switch_events: 0
avg_motion_max: 6.0
```

These thresholds are not a future musical law. They only determine whether the current runtime is safe enough to proceed without immediate selector intervention.

## Runtime audit results

### All The Things You Are / Medium Swing / 3 choruses

```text
events: 174
methods: drop2=104, drop3=69, drop2_and_4=1
voice_leading_warning_events: 0
section_boundary_review_warning_events: 0

phrase_scope_events: 84
phrase_scope_count: 36
phrase_scope_method_switch_events: 34
phrase_scope_method_switch_ratio: 0.4048
phrase_scope_drop2_and_4_run_events: 1
phrase_scope_drop2_and_4_run_max: 1
phrase_scope_ii_v_events: 30
phrase_scope_v_i_events: 27
phrase_scope_ii_v_i_events: 27
phrase_scope_ii_v_i_method_consistent_events: 10
phrase_scope_ii_v_i_method_switch_events: 17
phrase_scope_high_motion_switch_events: 0
phrase_scope_warning_events: 0
phrase_scope_checkpoint_passed: true
```

Interpretation:

```text
DROP2&4 is isolated and not acting as phrase body.
Method switches are common but smooth.
ii–V–I method consistency is mixed, which is now visible for future policy work.
No immediate runtime correction is needed.
```

### Autumn Leaves / Medium Swing / 3 choruses

```text
events: 223
methods: drop2=87, drop3=103, drop2_and_4=33
voice_leading_warning_events: 0
section_boundary_review_warning_events: 0

phrase_scope_events: 117
phrase_scope_count: 45
phrase_scope_method_switch_events: 50
phrase_scope_method_switch_ratio: 0.4274
phrase_scope_drop2_and_4_run_events: 24
phrase_scope_drop2_and_4_run_max: 2
phrase_scope_ii_v_events: 45
phrase_scope_v_i_events: 21
phrase_scope_ii_v_i_events: 21
phrase_scope_ii_v_i_method_consistent_events: 8
phrase_scope_ii_v_i_method_switch_events: 13
phrase_scope_high_motion_switch_events: 0
phrase_scope_warning_events: 0
phrase_scope_checkpoint_passed: true
```

Interpretation:

```text
DROP2&4 appears more often than in All The Things You Are, but max run stays 2.
Method switches are smooth and do not create high-motion jumps.
ii–V–I method consistency is mixed, suggesting the next policy should target local progression alignment rather than global weights.
```

## Design conclusion

v2_6_48 confirms the current Medium Swing OPEN / DROP-family runtime is safe to keep as-is for now:

```text
Do not change global OPEN weights yet.
Do not make DROP2&4 a phrase default.
Do not solve local progression method consistency through Pattern or Expression.
```

The next step should move from audit to a narrow voicing policy rule only if needed:

```text
v2_6_49_engine_medium_swing_open_drop_phrase_scope_method_lock_policy
```

That next policy should focus on local ii–V / V–I / ii–V–I alignment, not broad section-level weight tuning.

## Files touched

```text
src/jammate_engine/generation/piano_audit.py
src/jammate_engine/styles/medium_swing/voicing_policy.py
examples/scripts/generate_medium_swing_texture_method_audit.py
tests/test_v2_6_48_engine_medium_swing_open_drop_phrase_scope_method_continuity_plan.py
docs/ENGINE_VOICING_MEDIUM_SWING_OPEN_DROP_PHRASE_SCOPE_METHOD_CONTINUITY_PLAN_V2_6_48.md
docs/DEVELOPMENT_TASK_PLAN_ENGINE_V2.md
docs/CHANGELOG_ENGINE.md
docs/GENERATION_RULES_SUMMARY_V2.md
```

## Validation

```bash
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_v2_2_33_medium_swing_texture_method_audit.py \
  tests/test_v2_6_45_engine_medium_swing_open_drop_method_lock_calibration.py \
  tests/test_v2_6_46_engine_medium_swing_open_drop_voice_leading_continuity_audit.py \
  tests/test_v2_6_47_engine_medium_swing_open_drop_section_boundary_method_lock_review.py \
  tests/test_v2_6_48_engine_medium_swing_open_drop_phrase_scope_method_continuity_plan.py
```

Result:

```text
15 passed
```

Audit/demo generation:

```bash
PYTHONPATH=src python examples/scripts/generate_medium_swing_texture_method_audit.py
```

Result:

```text
ok: true
```

Generated artifacts:

```text
demos/v2_6_48_all_the_things_you_are_medium_swing_phrase_scope_method_continuity_demo.mid
demos/v2_6_48_autumn_leaves_medium_swing_phrase_scope_method_continuity_demo.mid
demos/v2_6_48_medium_swing_phrase_scope_method_continuity_audit_summary.json
demos/v2_6_48_medium_swing_phrase_scope_method_continuity_audit_report.md
```

## Recommended next task

```text
v2_6_49_engine_medium_swing_open_drop_phrase_scope_method_lock_policy
```

Recommended focus:

```text
1. Keep global OPEN method weights unchanged.
2. Use v2_6_48 phrase audit to decide if ii–V / V–I / ii–V–I should share a local method anchor.
3. If policy is added, scope it to voicing only and avoid Pattern / Expression / Anticipation changes.
4. Preserve DROP2&4 as phrase-internal color with max-run guard.
5. Continue validating with All The Things You Are and Autumn Leaves, both 3 choruses.
```
