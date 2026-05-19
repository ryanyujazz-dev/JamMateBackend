# v2_6_18 Engine Voicing — Content Source Inventory Behavior-Preserving Split

## Scope

`v2_6_18_engine_voicing_content_source_inventory_behavior_preserving_split` is a voicing-only boundary cleanup pass.

It is behavior-preserving relative to `v2_6_17_engine_voicing_content_family_router_behavior_preserving_split`:

```text
Do not change Pattern / Anticipation / Expression / Gesture / MIDI
Do not change API / Agent / HarmonyOS fixtures
Do not retune Ballad SPREAD density or color behavior
Do not re-enable 4-note SPREAD 1+3 / 2+2 defaults
Do not allow default unnotated maj7#11
Do not move family routing back into source inventory
```

## What changed

A new owner now handles family -> degree source options:

```text
src/jammate_engine/core/voicing/sources/content_source_inventory.py
```

It owns:

```text
content_degree_options
trim_content_degrees
content_validity_notes
source_preserves_seventh_chord_identity
seventh_chord_source_integrity_notes
shell+5 / shell+color source options
seventh-basic 4-note source options
rooted-color 4-note source options
rootless A/B source options
triad-aware 3-note and 4-note source options
altered-dominant source inventory
explicit-symbol color source inventory
CONTENT_SOURCE_INVENTORY_VERSION = v2_6_18
```

`content_planner.py remains the compatibility facade` for historical imports and orchestration:

```text
VoicingContentRecipe
choose_content_families  # thin wrapper to content_family_router
plan_content_recipes     # orchestrates router + inventory + density metadata
choose_degrees
```

The public helpers below remain importable through `content_planner.py`, but their implementation owner is now `content_source_inventory.py`:

```text
trim_content_degrees
source_preserves_seventh_chord_identity
seventh_chord_source_integrity_notes
```

## Boundary after this split

```text
content_family_router.py      family-choice / chord-quality-valid routing
content_source_inventory.py   family -> degree source options
content_planner.py            public facade + recipe orchestration only
color_permission.py           color admission and explicit-symbol fidelity helpers
source_balance.py             source-family scoring only
upper_structure.py            source-only upper-structure recipes
```

Important: `content_source_inventory.py` does not own family routing / chord-quality normalization.  It receives a valid `ContentFamily` and returns legal source options for that family.

## Non-goals

`content_source_inventory.py` must not own:

```text
family routing / chord-quality normalization
source-family scoring / weighting
density ratio calibration
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

The v2_6_14 / v2_6_15 / v2_6_16 / v2_6_17 density and color guardrails remain the baseline for this pass.

## Validation expectations

Required checks:

```bash
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python tools/check_development_harness.py
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_v2_6_18_engine_voicing_content_source_inventory_split.py \
  tests/test_v2_6_17_engine_voicing_content_family_router_split.py \
  tests/test_v2_6_16_engine_voicing_content_planner_boundary_split_plan.py \
  tests/test_v2_6_15_engine_voicing_spread_runtime_gate_adapter_cleanup.py \
  tests/test_v2_6_14_engine_voicing_ballad_spread_5_to_6_ratio_calibration.py \
  tests/test_v2_6_13_engine_voicing_ballad_six_note_ratio_lift.py \
  tests/test_v2_6_12_engine_voicing_spread_groupwise_voice_leading_split.py \
  tests/test_v2_6_11_engine_voicing_ballad_safe_extension_color_gate.py \
  tests/test_v2_6_10_engine_voicing_spread_density_system_reset.py
```

Legacy source-routing checks may still have historical `ENGINE_VERSION_TAG == v2_3_9` and old shared-doc assertions.  Exclude only those legacy version/doc assertions when using them as behavior regression tests.

## Recommended next task

```text
v2_6_19_engine_voicing_color_permission_adapter_cleanup
```

Next pass should audit whether `content_source_inventory.py` still has too much direct color-permission glue.  The likely cleanup is a small adapter layer that prepares `ColorPermissionContext` and explicit/expanded color sets for source inventory without moving source construction into `color_permission.py`.
