# v2_5_0 Engine Deepening Audit and Next Music Pass

## Scope

Branch scope: `feature/engine-deepening`.

This pass only touches engine-side generation, style vocabulary, expression policy, documentation, tests, and listening demos. Agent/LLM workflow behavior is not developed in this pass.

## Pre-development audit

Required entry documents reviewed before code changes:

- `README.md`
- `agent.md`
- `docs/ARCHITECTURE_V2.md`
- `docs/API_CONTRACT_V2.md`
- `docs/DEVELOPMENT_TASK_PLAN_V2.md`
- Engine-required harness references: `docs/PIPELINE_V2.md`, `docs/GENERATION_RULES_SUMMARY_V2.md`, `docs/STYLE_RULE_BASELINE_V2.md`, `docs/STYLE_TUNING_ENTRY_POINT_V2.md`, `docs/NEW_FILE_PLACEMENT_GUIDE_V2.md`, and `docs/CHANGELOG.md`

Audit conclusion:

- The post-split package boundary is clean: `jammate_engine` remains independent and does not import `jammate_agent`.
- The harness already has a clear engine-vs-agent branch split, so no new subsystem or new file split was needed for this music pass.
- The most obvious next music issue was Jazz Ballad comping motion: the pre-pass standard-tune demo selected only `ballad_piano_soft_downbeat_sustain` for Ballad piano events.

## Implemented music change

Owner files reused:

- `src/jammate_engine/styles/jazz_ballad/comping_patterns.py`
- `src/jammate_engine/styles/jazz_ballad/expression_policy.py`

Changes:

- Kept `ballad_piano_soft_downbeat_sustain` as the highest-weight default anchor.
- Added low-weight, pitchless anchored light-retouch cells:
  - `ballad_piano_downbeat_midbar_retouch`
  - `ballad_piano_downbeat_3and_answer`
  - `ballad_piano_downbeat_1and_whisper`
- Added short-region Ballad candidates so two-beat chord regions remain locally anchored and do not spill four-beat gestures across harmonic boundaries.
- Added semantic expression profiles:
  - `soft_retouch`
  - `soft_answer`
  - `soft_whisper`

The style layer still emits pitchless pattern events only. Voicing and final expression realization remain core responsibilities.

## Validation

Targeted validation commands:

```bash
PYTHONPATH=src pytest -q tests/test_v2_5_0_engine_deepening_ballad_music_pass.py tests/test_v2_0_42_comping_pattern_organization.py tests/test_expression_policy.py
PYTHONPATH=src python examples/scripts/generate_standard_tune_v2_examples_demos.py
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python tools/check_development_harness.py
```

Expected result: targeted tests pass, standard-tune demos generate, compileall passes, and harness check reports `HARNESS OK`.

## Recommended next engine task

Recommended next task: `v2_5_1_ballad_spread_or_expression_followup`.

Reason: after this pass, Ballad has more rhythm motion but still needs a focused listening decision on whether the next improvement should be SPREAD voicing selection, richer Ballad expression/pedal nuance, or a targeted motion-density gate for busier harmonic regions.
