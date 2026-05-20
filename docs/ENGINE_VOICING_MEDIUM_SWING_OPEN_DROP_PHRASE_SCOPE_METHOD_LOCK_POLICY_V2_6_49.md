# ENGINE v2_6_49 — Medium Swing OPEN / DROP Phrase-Scope Method Lock Policy

## Scope

Engine voicing-only runtime policy pass on top of the merged `v2_10_8` integration baseline plus Engine v2_6_48.

This pass keeps Pattern, Anticipation, Expression, Gesture/MIDI realization, Agent, API, HarmonyOS fixtures, and shared integration files unchanged.

## Why this pass exists

v2_6_48 made the Medium Swing phrase-scope continuity problem visible: global OPEN method ratios were acceptable, DROP2&4 was controlled, and voice-leading was smooth, but ii–V / V–I / ii–V–I local progressions could still switch DROP methods too freely.

v2_6_49 therefore adds a narrow runtime method-lock policy for local functional progressions instead of changing broad DROP2 / DROP3 / DROP2&4 weights.

## Policy behavior

The policy is enabled by Medium Swing voicing metadata:

```text
medium_swing_phrase_scope_method_lock_policy_version = v2_6_49
medium_swing_phrase_scope_method_lock_policy_enabled = true
```

Runtime behavior:

```text
1. The realizer records the selected OPEN drop-family method for each distinct chord region.
2. On the next distinct region, it asks core harmony's FunctionalMotion classifier whether the previous-current pair is local ii-V, minor ii-V, V-I major, V-I minor, or dominant-to-tonic.
3. If the previous method was DROP2 or DROP3, the follow region receives the existing strict method-lock metadata.
4. Candidate generation then uses the existing method-lock runtime filtering path.
5. DROP2&4 is recorded for audit and skip reasons, but is not propagated as phrase-body method.
```

This means v2_6_49 does not introduce a new progression recognizer, planner, source selector, projection implementation, or scorer. It reuses:

```text
core/harmony/harmonic_context.py
core/voicing/disposition/method_lock.py
core/voicing/selection/candidate_generator.py
```

## Runtime guardrails

Accepted guardrails:

```text
DROP2 / DROP3 may propagate across local ii-V / V-I motion.
DROP2&4 must not propagate as phrase body.
generic_open remains fallback-only.
section boundary texture-scope changes break the local lock.
locked follow candidates must match the locked method.
method-lock runtime filtering must be visible in audit metadata.
```

## Implementation summary

Touched files:

```text
src/jammate_engine/realization/realizer_voicing_request_orchestration.py
src/jammate_engine/core/voicing/selection/candidate_generator.py
src/jammate_engine/styles/medium_swing/voicing_policy.py
src/jammate_engine/generation/piano_audit.py
examples/scripts/generate_medium_swing_texture_method_audit.py
tests/test_v2_6_49_engine_medium_swing_open_drop_phrase_scope_method_lock_policy.py
docs/ENGINE_VOICING_MEDIUM_SWING_OPEN_DROP_PHRASE_SCOPE_METHOD_LOCK_POLICY_V2_6_49.md
docs/CHANGELOG_ENGINE.md
docs/DEVELOPMENT_TASK_PLAN_ENGINE_V2.md
docs/GENERATION_RULES_SUMMARY_V2.md
```

Key additions:

```text
MEDIUM_SWING_PHRASE_SCOPE_METHOD_LOCK_POLICY_VERSION = v2_6_49
medium_swing_phrase_scope_method_lock_policy_runtime_enabled_events
medium_swing_phrase_scope_method_lock_policy_applied_events
medium_swing_phrase_scope_method_lock_policy_candidate_match_events
medium_swing_phrase_scope_method_lock_policy_candidate_mismatch_events
medium_swing_phrase_scope_method_lock_policy_runtime_filtering_events
medium_swing_phrase_scope_method_lock_policy_pair_types
medium_swing_phrase_scope_method_lock_policy_locked_methods
medium_swing_phrase_scope_method_lock_policy_skip_reasons
medium_swing_phrase_scope_method_lock_policy_checkpoint_passed
```

## Reference three-chorus audit

### All The Things You Are / Medium Swing / 3 choruses

```text
events: 174
methods: drop2=98, drop3=74, drop2_and_4=2
voice_leading_warning_events: 0
section_boundary_review_warning_events: 0
phrase_scope_method_switch_ratio: 0.1429
phrase_scope_drop2_and_4_run_max: 1
phrase_scope_ii_v_i_method_switch_events: 0
phrase_scope_progression_method_switch_events: 0

method_lock_runtime_enabled_events: 174
method_lock_applied_events: 88
method_lock_candidate_match_events: 88
method_lock_candidate_mismatch_events: 0
method_lock_runtime_filtering_events: 88
method_lock_pair_types: ii_v=39, v_i_major=41, minor_ii_v=5, v_i_minor=3
method_lock_locked_methods: drop2=53, drop3=35
method_lock_checkpoint_passed: true
```

Interpretation:

```text
Local progression method consistency is now enforced without broad weight retuning.
DROP2&4 remains isolated color.
No locked follow candidate breaks the selected method lock.
```

### Autumn Leaves / Medium Swing / 3 choruses

```text
events: 223
methods: drop2=79, drop3=119, drop2_and_4=25
voice_leading_warning_events: 0
section_boundary_review_warning_events: 0
phrase_scope_method_switch_ratio: 0.2308
phrase_scope_drop2_and_4_run_max: 2
phrase_scope_ii_v_i_method_switch_events: 1
phrase_scope_progression_method_switch_events: 1

method_lock_runtime_enabled_events: 223
method_lock_applied_events: 100
method_lock_candidate_match_events: 100
method_lock_candidate_mismatch_events: 0
method_lock_runtime_filtering_events: 100
method_lock_pair_types: ii_v=31, v_i_major=26, minor_ii_v=22, v_i_minor=21
method_lock_locked_methods: drop2=48, drop3=52
method_lock_checkpoint_passed: true
```

Interpretation:

```text
DROP2/DROP3 continuity improves while DROP2&4 remains available as controlled color.
The remaining single progression switch is accepted because no high-motion warning appears and the runtime lock itself has zero mismatches.
```

## Validation

```bash
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python tools/check_development_harness.py
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_v2_6_49_engine_medium_swing_open_drop_phrase_scope_method_lock_policy.py \
  tests/test_v2_6_48_engine_medium_swing_open_drop_phrase_scope_method_continuity_plan.py \
  tests/test_v2_6_47_engine_medium_swing_open_drop_section_boundary_method_lock_review.py \
  tests/test_v2_6_46_engine_medium_swing_open_drop_voice_leading_continuity_audit.py \
  tests/test_v2_6_45_engine_medium_swing_open_drop_method_lock_calibration.py \
  tests/test_v2_6_44_engine_ballad_spread_voicing_phase_summary_and_handoff.py \
  tests/test_v2_10_7_integration_harmonyos_agent_today_guidance_runtime_smoke.py
```

Result:

```text
HARNESS OK
24 passed
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
demos/v2_6_49_all_the_things_you_are_medium_swing_phrase_scope_method_lock_policy_demo.mid
demos/v2_6_49_autumn_leaves_medium_swing_phrase_scope_method_lock_policy_demo.mid
demos/v2_6_49_medium_swing_phrase_scope_method_lock_policy_audit_summary.json
demos/v2_6_49_medium_swing_phrase_scope_method_lock_policy_audit_report.md
```

## Known unrelated old-test issue

Some old `v2_2_*` tests still assert historical `ENGINE_VERSION_TAG == v2_3_9`, old shared-doc text, or old Medium Swing OPEN weights such as `drop2=0.50`. Current merged baseline is `v2_10_8` and Medium Swing has accepted v2_6_45 weights, so those old assertions remain unrelated to v2_6_49.

## Recommended next task

```text
v2_6_50_engine_medium_swing_open_drop_ii_v_i_orientation_method_alignment
```

Recommended focus:

```text
1. Keep v2_6_49 method-lock policy active.
2. Audit whether rootless AB / ABA orientation remains aligned with the locked DROP method across ii-V-I.
3. Do not change global OPEN method weights.
4. Do not let DROP2&4 become a phrase default.
5. Continue validating with All The Things You Are and Autumn Leaves, both 3 choruses.
```
