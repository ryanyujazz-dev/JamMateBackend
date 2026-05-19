# v2_6_20 — Engine Voicing Source Balance Boundary Cleanup

Task: `v2_6_20_engine_voicing_source_balance_boundary_cleanup`

This is a voicing-only boundary cleanup pass. It does not change Pattern, Anticipation, Expression, Gesture, MIDI, Agent, API, shared version files, or HarmonyOS fixtures.

## Goal

`source_balance.py` is now explicitly documented and tested as the owner of source-family scoring / bias only.

It may:

```text
read existing candidate metadata
extract source_balance_key
extract source_balance_gate_mode
apply source_family_weights / source_family_weights_by_gate
apply altered-dominant source intensity bias
return inspectable scoring/debug profile data
```

It must not:

```text
does not construct sources
does not route ContentFamily
does not decide color permission
does not plan Upper Structure recipes
does not choose disposition / projection / register
does not touch Pattern / Anticipation / Expression / Gesture / MIDI
```

## Code changes

Updated:

```text
src/jammate_engine/core/voicing/sources/source_balance.py
src/jammate_engine/core/voicing/__init__.py
```

Added:

```text
SourceBalanceProfile
source_balance_profile
SOURCE_BALANCE_BOUNDARY_CLEANUP_VERSION = "v2_6_20"
SOURCE_BALANCE_OWNED_RESPONSIBILITIES
SOURCE_BALANCE_FORBIDDEN_RESPONSIBILITIES
```

`SourceBalanceProfile` is a scoring/debug profile only. It exposes the already-resolved key, gate, lookup keys, content family, and altered-dominant source kind. It does not create degree recipes or authorize color.

## Behavior preservation

The existing source scoring contract remains:

```text
SOURCE_BALANCE_CONTRACT_VERSION = v2_1_43
ALTERED_DOMINANT_INTENSITY_BALANCE_VERSION = v2_2_88
```

The pass also keeps legacy behavior for:

```text
3-note shell/color gate scoring
4-note triad/rootless/rooted/basic source-key extraction
altered-dominant source intensity score
selector score details
```

A small metadata-read hardening was added so 4-note functional keys can be read from the current `content_recipe.validity_notes` markers when older top-level metadata aliases are absent. This keeps source-balance behavior aligned with the existing inventory/facade split without moving inventory ownership into source balance.

## Runtime guardrails

Reference Jazz Ballad guardrails remain unchanged:

```text
5-note:6-note ~= 6:4
4-note SPREAD default remains retired
7-note remains low-frequency
maj7#11 remains off by default unless chart-explicit or harmonic-color intent enables it
```

## Validation

Focused validation should include:

```bash
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python tools/check_development_harness.py
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_v2_6_20_engine_voicing_source_balance_boundary_cleanup.py
```

Regression scope should include the recent voicing boundary tests from `v2_6_10` through `v2_6_20`, plus legacy source-balance and altered-dominant scoring subsets.

## Next recommended task

`v2_6_21_engine_voicing_upper_structure_boundary_audit`

Next pass should audit Upper Structure as a source-only layer. It should verify that Upper Structure constructs source recipes but reuses existing closed / inversion / DROP projection and does not implement its own voicing projection, register, or selector logic.
