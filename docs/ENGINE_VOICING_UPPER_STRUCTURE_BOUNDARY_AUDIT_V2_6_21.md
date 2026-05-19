# v2_6_21 — Engine Voicing Upper Structure Boundary Audit

Task: `v2_6_21_engine_voicing_upper_structure_boundary_audit`

This is a voicing-only boundary audit pass. It does not change Pattern, Anticipation, Expression, Gesture, MIDI, Agent, API, shared version files, or HarmonyOS fixtures.

## Goal

`upper_structure.py` is now explicitly documented and tested as a **source-only** owner.

It may:

```text
provide source-level upper-structure degree recipes
gate Upper Structure entry by policy metadata
gate Upper Structure density to 3-note and 4-note source recipes
provide dominant safe / altered source recipe catalogs
provide maj7 / minor7 safe source recipe catalogs
attach source metadata so downstream layers can reuse existing projection systems
```

It must not:

```text
does not project closed/open/spread voicings
does not choose register or octave placement
does not score or select candidates
does not rank voice-leading
does not adapt runtime spread candidates
does not write MIDI or touch expression
```

## Code changes

Updated:

```text
src/jammate_engine/core/voicing/sources/upper_structure.py
src/jammate_engine/core/voicing/sources/__init__.py
```

Added source-boundary audit markers:

```text
UPPER_STRUCTURE_BOUNDARY_AUDIT_VERSION = "v2_6_21"
UpperStructureBoundaryProfile
upper_structure_boundary_profile
UPPER_STRUCTURE_OWNED_RESPONSIBILITIES
UPPER_STRUCTURE_FORBIDDEN_RESPONSIBILITIES
```

`UpperStructureBoundaryProfile` is descriptive only. It exposes static responsibility metadata and does not contain concrete MIDI notes, projection decisions, register choices, selector scores, or runtime adapter data.

## Preserved behavior

The existing Upper Structure source contract remains:

```text
UPPER_STRUCTURE_SOURCE_VERSION = v2_2_88
```

No source recipe weights or density mix were changed.

Upper Structure remains a source family:

```text
3-note upper structures reuse existing closed / inversion placement
4-note upper structures reuse existing closed / inversion / DROP2 / DROP3 projection paths
```

It is not a new projection system.

## Guardrails preserved

Misty / Jazz Ballad / 3 choruses remains aligned with the current voicing calibration:

```text
5-note:6-note ~= 6:4
4-note SPREAD remains 0
7-note remains low-frequency
maj7#11 remains off by default unless explicitly requested or written in the chart
```

## Validation

Recommended focused validation:

```bash
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python tools/check_development_harness.py
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_v2_6_21_engine_voicing_upper_structure_boundary_audit.py
```

Recommended regression subset:

```bash
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/test_v2_6_10_engine_voicing_spread_density_system_reset.py \
  tests/test_v2_6_11_engine_voicing_ballad_safe_extension_color_gate.py \
  tests/test_v2_6_12_engine_voicing_spread_groupwise_voice_leading_split.py \
  tests/test_v2_6_13_engine_voicing_ballad_six_note_ratio_lift.py \
  tests/test_v2_6_14_engine_voicing_ballad_spread_5_to_6_ratio_calibration.py \
  tests/test_v2_6_15_engine_voicing_spread_runtime_gate_adapter_cleanup.py \
  tests/test_v2_6_16_engine_voicing_content_planner_boundary_split_plan.py \
  tests/test_v2_6_17_engine_voicing_content_family_router_split.py \
  tests/test_v2_6_18_engine_voicing_content_source_inventory_split.py \
  tests/test_v2_6_19_engine_voicing_color_permission_adapter_cleanup.py \
  tests/test_v2_6_20_engine_voicing_source_balance_boundary_cleanup.py \
  tests/test_v2_6_21_engine_voicing_upper_structure_boundary_audit.py
```

## Recommended next task

`v2_6_22_engine_voicing_harmonic_realizer_policy_context_adapter_cleanup`

Purpose: audit the adapter boundary between style voicing policy, harmonic realizer, and core voicing sources/disposition. The next step should ensure the harmonic realizer passes policy/context cleanly into voicing, without constructing sources, choosing color permission, implementing projection, or doing selector work itself.
