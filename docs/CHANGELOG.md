# JamMatePyEngineV2 Changelog

This file is the chronological project history. README should remain the project overview; `agent.md` should remain the development harness.

---

## v2_3_17 — Harness Hardening and Changelog Split

- Compressed `agent.md` into a short hard development harness.
- Rewrote `docs/DEVELOPMENT_HARNESS_V2.md` as the expanded harness explanation.
- Added this `docs/CHANGELOG.md` as the canonical place for chronological version history.
- Replaced the oversized historical `tools/check_development_harness.py` with a focused automated harness checker.
- Added a targeted regression test for harness/changelog/cleanup behavior.
- Runtime music generation behavior is unchanged from `v2_3_16`.

## v2_3_16 — Project Cleanup and README Consolidation

- Converted README into the project entrance document: core design principles, directory architecture, core features, startup and validation commands.
- Removed README-style rolling implementation history from the project entrance.
- Added package cleanup rules and `.gitignore`.
- Kept the package as a clean baseline for two-window Agent/Engine development.

## v2_3_15 — HarmonyOS API Smoke Test Pack

- Added HarmonyOS API smoke-pack endpoints and repository fixtures.
- Added `/health`, `/accompaniment/generate`, and `/agent/playback/prepare` minimum validation sequence.
- Added curl smoke script and LAN testing notes.

## v2_3_14 — Agent Contract Case Policy and Response Adapter

- Kept backend API responses canonical `snake_case`.
- Added HarmonyOS client-domain `camelCase` model mapping through `CaseAdapter.ets`.
- Added `/agent/contracts/case-policy` and synchronized frontend fixtures.

## v2_3_13 — Agent Contract Codegen and Frontend Fixture Pack

- Added generated ArkTS contract file pack.
- Added `AgentTypes.ets`, `PracticeTypes.ets`, `PlaybackTypes.ets`, `JamMateApiClient.ets` sketches.
- Added HarmonyOS fixture JSON for frontend mock/integration work.

## v2_3_12 — HarmonyOS Practice API Contract Sync

- Added HarmonyOS playback/cache contract details.
- Added API examples for direct accompaniment and Agent playback.
- Clarified `client_loop_until_target_duration` and local practice timer ownership.

## v2_3_11 — JamMate Agent Context and Contract Hardening

- Added Agent capability and context profile manifests.
- Added persistent Agent trace store.
- Added snake_case/camelCase request compatibility.
- Added contract endpoints for HarmonyOS integration.

## v2_3_10 — Agent / Engine / API Boundary Foundation

- Introduced sibling `jammate_agent` and `jammate_api` packages beside `jammate_engine`.
- Preserved direct engine accompaniment generation without LLM/Agent.
- Added Agent playback preparation route backed by the engine adapter.
