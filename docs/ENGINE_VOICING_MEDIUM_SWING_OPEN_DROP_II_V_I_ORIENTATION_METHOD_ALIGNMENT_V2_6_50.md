# ENGINE v2_6_50 — Medium Swing OPEN / DROP ii–V–I Orientation / Method Alignment

## Scope

This is an Engine voicing-only pass on top of the merged `v2_10_8` baseline plus `v2_6_49` Medium Swing phrase-scope method-lock policy.

It does not change:

```text
Pattern
Anticipation
Expression / pedal
Gesture
MIDI writer
Agent / LLM route
API contract
HarmonyOS fixtures
shared integration docs / version files
```

## Goal

`v2_6_49` already made local functional progressions keep the same OPEN projection method when appropriate:

```text
Dm7  -> G7  -> Cmaj7
DROP2   DROP2   DROP2
```

`v2_6_50` adds the next voicing-level continuity hook: when the seed region already selected a rootless A/B voicing, the follow region should prefer the corresponding A/B flip while preserving the same rootless content type and inversion index.

Example target behavior:

```text
ii    -> V     -> I
A        B        A
```

or the inverse:

```text
ii    -> V     -> I
B        A        B
```

This aligns rootless orientation with the same local progression scope used by the Medium Swing DROP method lock.

## Runtime contract

The policy is intentionally conservative:

```text
scope: same_texture_scope_local_functional_pair
mode: strict_when_matching_candidate_available
desired_motion: flip_A_B_while_preserving_content_type_and_inversion_index
```

Accepted behavior:

```text
1. v2_6_49 method-lock still decides the follow method first.
2. If the previous seed has rootless_ab_orientation_family = A, follow requests B.
3. If the previous seed has rootless_ab_orientation_family = B, follow requests A.
4. The requested follow candidate should preserve rootless_ab_content_type.
5. The requested follow candidate should preserve rootless_ab_inversion_index.
6. If matching candidates exist, the candidate pool is filtered to those candidates.
7. If no matching candidates exist, the full pool is preserved and an audit reason is recorded.
8. If the previous seed is not rootless A/B, the policy does not force rootless voicing.
```

This avoids turning Medium Swing into a forced rootless texture while still making explicit rootless passages behave like coherent ii–V–I vocabulary.

## Implementation notes

Implemented through existing surfaces:

```text
realization/realizer_voicing_request_orchestration.py
core/voicing/selection/candidate_generator.py
styles/medium_swing/voicing_policy.py
generation/piano_audit.py
examples/scripts/generate_medium_swing_texture_method_audit.py
```

No new planner or progression recognizer was introduced. The orientation request rides on the same follow-region metadata path used by `method_lock_seed_then_follow`.

## Standard-tune audit result

The two reference standard-tune demos still pass all Medium Swing OPEN / DROP checks.

Important reading note: with the current default Medium Swing `chord_symbol_only` behavior and the current reference charts, the selected seed voicings in these two demos are not rootless A/B. Therefore the v2_6_50 runtime wiring is enabled, but the orientation policy does not actively filter real demo events yet. This is correct: the policy must not force rootless A/B when the seed is not rootless.

```text
All The Things You Are / Medium Swing / 3 choruses
method_lock_applied_events: 88
method_lock_candidate_mismatch_events: 0
phrase_scope_method_switch_ratio: 0.1429
rootless_ab_orientation_runtime_enabled_events: 88
rootless_ab_orientation_policy_applied_events: 0
rootless_ab_orientation_skip_reasons: previous_seed_not_rootless_ab=88
rootless_ab_orientation_checkpoint_passed: true
```

```text
Autumn Leaves / Medium Swing / 3 choruses
method_lock_applied_events: 100
method_lock_candidate_mismatch_events: 0
phrase_scope_method_switch_ratio: 0.2308
rootless_ab_orientation_runtime_enabled_events: 100
rootless_ab_orientation_policy_applied_events: 0
rootless_ab_orientation_skip_reasons: previous_seed_not_rootless_ab=100
rootless_ab_orientation_checkpoint_passed: true
```

## Targeted rootless probe

A targeted candidate-generator test confirms the policy is live when matching rootless candidates exist:

```text
symbol: G13
desired_orientation: B
desired_content_type: with_13
desired_inversion_index: 0
original_candidate_count: 44
kept_candidate_count: 3
kept_orientations: B only
checkpoint_passed: true
```

This verifies that v2_6_50 is not merely audit metadata: candidate filtering activates for explicit rootless A/B material.

## Tests

Focused test:

```bash
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_v2_6_50_engine_medium_swing_open_drop_ii_v_i_orientation_method_alignment.py
```

Recent Engine voicing regression:

```bash
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_v2_6_44_engine_ballad_spread_voicing_phase_summary_and_handoff.py \
  tests/test_v2_6_45_engine_medium_swing_open_drop_method_lock_calibration.py \
  tests/test_v2_6_46_engine_medium_swing_open_drop_voice_leading_continuity_audit.py \
  tests/test_v2_6_47_engine_medium_swing_open_drop_section_boundary_method_lock_review.py \
  tests/test_v2_6_48_engine_medium_swing_open_drop_phrase_scope_method_continuity_plan.py \
  tests/test_v2_6_49_engine_medium_swing_open_drop_phrase_scope_method_lock_policy.py \
  tests/test_v2_6_50_engine_medium_swing_open_drop_ii_v_i_orientation_method_alignment.py
```

## Demo / audit artifacts

```text
demos/v2_6_50_all_the_things_you_are_medium_swing_ii_v_i_orientation_method_alignment_demo.mid
demos/v2_6_50_autumn_leaves_medium_swing_ii_v_i_orientation_method_alignment_demo.mid
demos/v2_6_50_medium_swing_ii_v_i_orientation_method_alignment_audit_summary.json
demos/v2_6_50_medium_swing_ii_v_i_orientation_method_alignment_audit_report.md
```

## Next recommended task

Recommended next voicing-only task:

```text
v2_6_51_engine_medium_swing_open_drop_same_chord_reattack_and_comping_reuse
```

If the goal is to make rootless A/B orientation audible in plain Medium Swing standard-tune demos, insert a smaller policy task before that to decide when Medium Swing may open rootless/color lanes under `harmonic_expansion_enabled`, explicit chord-symbol colors, or LLM harmonic-color intent. Do not force rootless A/B through the orientation alignment policy itself.
