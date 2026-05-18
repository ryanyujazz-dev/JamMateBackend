# v2_5_10 Agent / Engine Integration Merge

This is a reconciliation package that merges the latest `feature/agent-workflow` line (`v2_4_13`) into the current official engine-deepening baseline (`v2_5_9`).

## Merge Policy

- Engine generation runtime, style rules, gesture/expression/voicing behavior, and the Jazz Ballad swing-8 timing baseline are kept from `v2_5_9`.
- Agent/LLM terminal workflow, tool-call preview, trace viewer, provider boundary, and HarmonyOS contract fixture work are kept from `v2_4_13`.
- Shared documents are merged by ownership rather than blanket overwrite.
- HarmonyOS direct accompaniment generation remains stable: `POST /accompaniment/generate` returns `ok`, `asset.format`, `asset.midi_base64`, `asset.midi_path`, `asset.cache_key`, and `debug_summary`.
- Agent tool-call preview remains validation-only. It does not execute tools, dispatch workflows, call adapters, or call `jammate_engine`.

## Engine Baseline Preserved

The engine side remains based on `v2_5_9_v1_instrument_rules_deep_audit_and_v2_native_mapping`, which itself uses `v2_5_8` as the audible Jazz Ballad timing baseline. The experimental Ballad brush-drums shortcut is not included as a formal baseline.

## Agent Baseline Preserved

The Agent side includes `v2_4_0` through `v2_4_13` additions:

- LLM context runtime preview
- provider-neutral LLM boundary
- terminal chat CLI
- local LLM setup/doctor/config helpers
- read-only trace viewer CLI
- validation-only tool invocation preview
- JSON-only tool-call candidate extraction
- stable preview trace contract
- HarmonyOS contract and smoke fixture synchronization

## Next Recommended Engine Task

After this integration package is validated on `main`, resume engine work with:

`v2_5_11_jazz_ballad_bass_anchor_path_policy`

Do not reintroduce the discarded Ballad brush shortcut before the V1 instrument-rule mapping is used to design a V2-native percussion policy.
