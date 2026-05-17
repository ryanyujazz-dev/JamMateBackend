# v2_2_89 — Upper Structure / Voicing Guard Listening Refinement

## Purpose

This pass refines the existing voicing guard and selector path after Upper Structure and altered-dominant color were introduced. It does **not** create a new Upper Structure projection system. Upper Structure remains a source family that reuses existing closed, inversion, DROP2, and DROP3 projection resources.

The goal is musical: altered Upper Structure should add color without making the piano voicing sound尖锐 in the top register or muddy in the low foundation.

## Runtime changes

- Added a generic `low_register_single_note` guard to `evaluate_register_guard()`.
- Default low threshold: MIDI `40` / E2.
- Default maximum notes below threshold: `1`.
- Added audit fields:
  - `low_register_single_note_guard_version`
  - `low_register_single_note_threshold`
  - `max_notes_below_low_register_single_note_threshold`
  - `low_register_single_note_count`
  - `low_register_single_note_ok`
- Added Upper Structure register score shaping in the existing selector scorer:
  - `UPPER_STRUCTURE_REGISTER_REFINEMENT_VERSION = v2_2_89`
  - `upper_structure_register_score`
  - `upper_structure_top_note_soft_high`

## Style policy tuning

Each style now publishes Upper Structure register refinement metadata:

- Medium Swing: keeps Upper Structure color in a normal comping band.
- Jazz Ballad: keeps altered Upper Structure warmer and less sharp.
- Bossa Nova: keeps Upper Structure lighter and lower in brightness.

Shared style metadata:

```python
"upper_structure_register_refinement_enabled": True,
"low_register_single_note_threshold": 40,
"max_notes_below_low_register_single_note_threshold": 1,
```

## Design constraints

- Pattern and Voicing remain decoupled.
- Upper Structure remains source-level material; projection reuse stays in the existing disposition layer.
- The low-register single-low-note rule is a core voicing/register guard, not a style-specific hack.
- Scoring refines comparable candidates; it does not override source authorization, harmonic expansion policy, or altered-dominant functional scope.

## Verification

Canonical validation:

```bash
python -m compileall src
PYTHONPATH=src python -m pytest -q
python tools/check_development_harness.py
```

Targeted tests:

```bash
PYTHONPATH=src python -m pytest -q tests/test_v2_2_89_upper_structure_voicing_guard_refinement.py
```

## Next recommended task

`v2_3_3 — Demo / Audit Pipeline Consolidation`: unify the growing demo/audit scripts so each milestone can consistently produce three-chorus standard-tune demos plus machine-readable summaries.
