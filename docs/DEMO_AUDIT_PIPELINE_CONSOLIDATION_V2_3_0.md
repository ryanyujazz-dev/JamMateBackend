# v2_3_9 — Anticipation Timing Grid Contract Repair

## Purpose

Consolidate the project's growing listening-demo and audit workflow into one stable entrypoint without changing runtime musical generation.

## Canonical tool

`tools/demo_audit_pipeline.py`

Responsibilities:

- Load a V2 leadsheet fixture.
- Build a public `generate_accompaniment()` request.
- Enforce three-chorus standard-tune demos by default.
- Write a MIDI file.
- Write a paired `_audit_summary.json`.
- Write a run manifest.
- Summarize runtime, piano, expression, bass, altered-dominant, upper-structure, and register-guard signals in one shared JSON shape.

Non-responsibilities:

- No style pattern ownership.
- No voicing algorithm ownership.
- No expression or realization ownership.
- No hidden retuning of runtime behavior.

## Standard jobs

- `minimal_swing`
- `misty_ballad_upper_structure_altered`
- `blue_bossa_minor_altered`
- `minor_turnaround_fixture`

## Commands

```bash
PYTHONPATH=src python tools/demo_audit_pipeline.py --list
PYTHONPATH=src python tools/demo_audit_pipeline.py --job minimal_swing
PYTHONPATH=src python tools/demo_audit_pipeline.py
```

## Validation

```bash
python -m compileall src tools
PYTHONPATH=src python -m pytest -q
python tools/check_development_harness.py
PYTHONPATH=src python tools/demo_audit_pipeline.py --job minimal_swing
```

## Next recommended step

`v2_3_9 — Demo Matrix / Listening Regression Thresholds` should add a small manifest-driven matrix and numeric threshold checks over generated audit summaries, without converting subjective listening into over-rigid tests.
