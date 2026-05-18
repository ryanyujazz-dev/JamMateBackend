# v2_6_19 Engine Voicing — Color Permission Adapter Cleanup

## Scope

`v2_6_19_engine_voicing_color_permission_adapter_cleanup` is a voicing-only boundary cleanup pass.

It is behavior-preserving relative to `v2_6_18_engine_voicing_content_source_inventory_behavior_preserving_split`:

```text
Do not change Pattern / Anticipation / Expression / Gesture / MIDI
Do not change API / Agent / HarmonyOS fixtures
Do not retune Ballad SPREAD density or color behavior
Do not re-enable 4-note SPREAD 1+3 / 2+2 defaults
Do not allow default unnotated maj7#11
Do not move source construction into color_permission.py
```

## What changed

`color_permission.py` is now the owner for color-admission adapter helpers:

```text
src/jammate_engine/core/voicing/sources/color_permission.py
```

It owns:

```text
ColorPermissionContext
build_color_permission_context
build_voicing_color_permission_context
explicit_symbol_color_degrees
rootless_ab_explicit_color_degrees
ordered_explicit_colors
expansion_color_candidates
major_seventh_safe_extension_preference
major_seventh_sharp11_harmonic_color_intent_enabled
COLOR_PERMISSION_ADAPTER_VERSION = v2_6_19
```

`content_source_inventory.py remains the source-construction owner`.

It may ask `color_permission.py` which explicit / expanded colors are allowed, but it still decides which functional-degree source family to emit:

```text
rooted-color 4-note sources
rootless A/B sources
altered-dominant source options
shell+color 3-note options
triad-aware source options
seventh-source integrity notes
```

## Boundary after this cleanup

```text
content_family_router.py      family-choice / chord-quality-valid routing
content_source_inventory.py   family -> degree source options and source metadata
content_planner.py            public facade + recipe orchestration only
color_permission.py           color admission, explicit-symbol fidelity, expansion palette adapter
source_balance.py             source-family scoring only
upper_structure.py            source-only upper-structure recipes
```

Important: `color_permission.py` does not construct voicing sources. It returns color sets, permission context, and audit notes. Source construction remains in `content_source_inventory.py`.

## Preserved color rules

Default Ballad/safe major-seventh color remains warm and conservative:

```text
Cmaj7 + safe extension -> 9 / 13, not unnotated #11
Cmaj7#11 -> #11 is explicit chart color and remains allowed
Cmaj7 + explicit Lydian/bright/modern intent -> #11 may be allowed
```

Half-diminished / diminished identity tones are still not treated as optional colors:

```text
Bm7b5 -> b5 does not by itself open rootless color gate
Bm9b5 -> 9 is explicit chart color
```

Altered dominant color admission is still policy-gated and source construction remains in inventory:

```text
G7alt / altered-dominant policy may admit altered colors
rooted/rootless altered source construction stays in content_source_inventory.py
```

## Behavior guardrails preserved

Reference Misty / Jazz Ballad / 3-chorus behavior remains the same target:

```text
5-note:6-note ~= 6:4
4-note SPREAD remains 0
1+3 / 2+2 SPREAD defaults remain retired
7-note remains rare
maj7#11 remains off by default unless explicitly requested by chart or harmonic-color intent
```

## Validation expectations

Required checks:

```bash
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python tools/check_development_harness.py
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_v2_6_19_engine_voicing_color_permission_adapter_cleanup.py \
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

Legacy source-routing checks may still have historical `ENGINE_VERSION_TAG == v2_3_9` and old shared-doc assertions. Exclude only those legacy version/doc assertions when using them as behavior regression tests.

## Recommended next task

```text
v2_6_20_engine_voicing_source_balance_boundary_cleanup
```

Next pass should audit `source_balance.py` and ensure it only scores / biases already-constructed source families. It should not construct source degrees, route content families, or decide color permission.
