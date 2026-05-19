# Integration Agent / Engine Merge Audit v2_8_24

## Source packages

- Engine Track source: `v2_6_30_engine_ballad_spread_1plus4_lower_foundation_calibration`.
- Agent Track source: `v2_8_23_agent_v2_8_phase_cleanup_regression_handoff`.
- Integration output baseline: `v2_8_24`.

## Ownership decisions

- Engine-owned runtime paths were kept from the Engine Track package: `src/jammate_engine/core/`, `styles/`, `generation/`, `performance/`, `harmony/`, `midi/`, and `realization/`.
- Agent-owned paths were taken from the Agent Track package: `src/jammate_agent/`, `src/jammate_api/routes/agent_routes.py`, Agent docs, Agent tests, and Agent terminal/trace/tool/context/guidance contracts.
- Integration-owned shared files were reconciled manually instead of one-sided overwrite: `README.md`, `agent.md`, `VERSION`, `pyproject.toml`, architecture/API/task-plan/changelog docs, and HarmonyOS fixture surfaces.

## Protected contracts

- Direct accompaniment route `POST /accompaniment/generate` remains the HarmonyOS playback path.
- The direct accompaniment response keeps `ok`, `asset.format`, `asset.midi_base64`, `asset.midi_path`, `asset.cache_key`, and `debug_summary`.
- Agent preview/debug routes remain orchestration/preview surfaces and do not modify Engine generation runtime.
- Pattern, Gesture, Expression, Voicing, Realization, and MIDI boundaries remain separated.

## Non-goals honored

- No new Engine music-generation rule.
- No new Agent/LLM feature.
- No V1 code migration.
- No Agent logic inside Engine generation runtime.
- No Engine music rules inside Agent contract.

## Validation summary

Passed in this integration package:

```text
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python tools/check_development_harness.py
HarmonyOS / API contract targeted tests: 38 passed
Agent v2_8 regression tests: 163 passed
Agent contract / trace / tool-preview / guidance targeted tests: 228 passed
Engine v2_6_2–v2_6_30 targeted regression tests: 139 passed, run in smaller batches to avoid long single-command timeout
Standard tune demo generation: Autumn Leaves / Blue Bossa / Misty, 3 choruses each, ok=true
```

Integration cleanup also aligned stale historical version/string assertions and SPREAD freeze expectations in tests to the active `{version}` / Engine `v2_6_30` baseline. No Engine generation runtime rule was changed for those test updates.

## Generated standard tune demos

```text
demos/v2_8_24_autumn_leaves_medium_swing_demo.mid
demos/v2_8_24_blue_bossa_bossa_nova_demo.mid
demos/v2_8_24_misty_jazz_ballad_demo.mid
demos/v2_8_24_standard_tune_v2_examples_summary.json
```

The summary reports 3 choruses for each tune.
