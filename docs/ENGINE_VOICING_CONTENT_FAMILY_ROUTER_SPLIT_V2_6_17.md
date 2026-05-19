# v2_6_17 Engine Voicing — Content Family Router Behavior-Preserving Split

## Scope

`v2_6_17_engine_voicing_content_family_router_behavior_preserving_split` is a voicing-only boundary cleanup pass.

It is behavior-preserving relative to `v2_6_16_engine_voicing_content_planner_boundary_split_plan`:

```text
Do not change Pattern / Anticipation / Expression / Gesture / MIDI
Do not change API / Agent / HarmonyOS fixtures
Do not retune Ballad SPREAD density or color behavior
Do not re-enable 4-note SPREAD 1+3 / 2+2 defaults
Do not allow default unnotated maj7#11
Do not split source inventory in this pass
```

## What changed

A new owner now handles content-family routing and chord-quality normalization:

```text
src/jammate_engine/core/voicing/sources/content_family_router.py
```

It owns:

```text
choose_content_families
normalize_content_families_for_chord
is_three_note_closed_request
four_note_color_gate_open
family_expansion_target_allowed
ROOTLESS_FAMILIES / ROOTED_FAMILIES / TRIAD_FAMILIES
CONTENT_FAMILY_ROUTER_VERSION = v2_6_17
```

`content_planner.py remains the compatibility facade` for historical imports and orchestration:

```text
VoicingContentRecipe
choose_content_families  # thin wrapper to content_family_router
plan_content_recipes
choose_degrees
trim_content_degrees
source_preserves_seventh_chord_identity
seventh_chord_source_integrity_notes
```

## Boundary after this split

```text
content_family_router.py    family-choice / chord-quality-valid routing
content_planner.py          public facade + current source inventory orchestration
color_permission.py         color admission and explicit-symbol fidelity helpers
source_balance.py           source-family scoring only
upper_structure.py          source-only upper-structure recipes
```

Important: `source inventory stays in content_planner.py` for this pass.  The next split should move family-to-degree option inventory separately, after this router behavior is proven stable.

## Non-goals

`content_family_router.py` must not own:

```text
family -> degree source inventory
rootless A/B source rotations
seventh-basic / rooted-color / triad-4note source construction
upper-structure source recipes
source-family scoring
register placement
closed / open / spread projection
runtime candidate selection
Pattern / Anticipation / Expression / Gesture / MIDI behavior
```

It also `does not own disposition / register / projection`.

## Behavior guardrails preserved

Reference Misty / Jazz Ballad / 3-chorus behavior remains the same target:

```text
5-note:6-note ~= 6:4
4-note SPREAD remains 0
1+3 / 2+2 SPREAD defaults remain retired
7-note remains rare
maj7#11 remains off by default unless explicitly requested by chart or harmonic-color intent
```

The v2_6_14 / v2_6_15 / v2_6_16 density and color guardrails remain the baseline for this pass.

## Validation expectations

Required checks:

```bash
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python tools/check_development_harness.py
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_v2_6_17_engine_voicing_content_family_router_split.py \
  tests/test_v2_6_16_engine_voicing_content_planner_boundary_split_plan.py \
  tests/test_v2_6_15_engine_voicing_spread_runtime_gate_adapter_cleanup.py \
  tests/test_v2_6_14_engine_voicing_ballad_spread_5_to_6_ratio_calibration.py \
  tests/test_v2_6_13_engine_voicing_ballad_six_note_ratio_lift.py \
  tests/test_v2_6_12_engine_voicing_spread_groupwise_voice_leading_split.py \
  tests/test_v2_6_11_engine_voicing_ballad_safe_extension_color_gate.py \
  tests/test_v2_6_10_engine_voicing_spread_density_system_reset.py
```

Legacy source-routing checks may still have historical `ENGINE_VERSION_TAG == v2_3_9` assertions.  Exclude only those version assertions when using them as behavior regression tests.

## Recommended next task

```text
v2_6_18_engine_voicing_content_source_inventory_behavior_preserving_split
```

Next pass should move only family-to-degree source inventory out of `content_planner.py` into `content_source_inventory.py`, while keeping `content_planner.py` as the public facade and preserving all current density/color guardrails.
