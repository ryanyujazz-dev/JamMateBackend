# Agent v2_8 Phase Cleanup / Regression / Handoff v2_8_23

## Goal

`v2_8_23_agent_v2_8_phase_cleanup_regression_handoff` closes the Agent v2_8 context/guidance/persistence/debug-fixture phase.

This version does not add a new product capability. It packages the phase handoff report, regression checklist, terminal smoke path, HarmonyOS debug fixture联调 path, persistence boundary, and next-phase recommendation.

## New surfaces

```text
GET  /agent/context/today-practice-guidance/v2-8-phase-handoff/spec
POST /agent/context/today-practice-guidance/v2-8-phase-handoff/preview
CLI  /v2-8-phase-handoff [json_payload]
```

## Phase scope closed by this handoff

```text
v2_8_1  UserPracticeProfileContext intake
v2_8_2  practice context storage boundary contract
v2_8_3  profile-aware today-practice guidance E2E
v2_8_4  terminal LLM provider compatibility hotfix
v2_8_5  terminal guidance JSON/fallback hotfix
v2_8_6  PracticePlan persistence candidate contract
v2_8_7  RoutineHistory persistence candidate contract
v2_8_8  context persistence confirmation boundary
v2_8_9  context persistence executor no-op skeleton
v2_8_10 storage adapter design contract
v2_8_11 SQLite dev preview
v2_8_12 dev SQLite explicit write gate contract
v2_8_13 fixture writer dry-run
v2_8_14 explicit opt-in dev fixture JSONL store
v2_8_15 fixture read-back / replay preview
v2_8_16 persisted snapshot → profile/plan/history context intake
v2_8_17 persisted-context recovery today-practice guidance E2E
v2_8_18 terminal persisted-context memory controls
v2_8_19 terminal memory → HarmonyOS debug fixture preview
v2_8_20 HarmonyOS debug fixture roundtrip E2E
v2_8_21 HarmonyOS debug fixture API request pack
v2_8_22 terminal chat product smoke polish
```

## Terminal handoff

```bash
PYTHONPATH=src python -m jammate_agent.cli.terminal_chat setup
PYTHONPATH=src python -m jammate_agent.cli.terminal_chat doctor
PYTHONPATH=src python -m jammate_agent.cli.terminal_chat --show-provider-status
```

Inside terminal chat:

```text
/terminal-product-smoke
/persisted-context-load { ...profile / practicePlan / routineHistoryRecords... }
今天该练什么？
/v2-8-phase-handoff
```

Expected behavior:

```text
Display-only guidance/action-card preview.
No Routine start.
No Engine call.
No MIDI generation.
```

## HarmonyOS debug fixture handoff

Primary request-pack route:

```text
POST /agent/context/today-practice-guidance/harmonyos-debug-fixture-api-request-pack/preview
```

Roundtrip validation route:

```text
POST /agent/context/today-practice-guidance/harmonyos-debug-fixture-roundtrip/e2e-preview
```

Important boundary:

```text
Agent line only generates debug payload previews.
It does not modify frontend_fixtures/harmonyos.
Actual frontend fixture changes belong to the integration track.
```

## Persistence handoff

v2_8 has prepared the persistence chain up to dev fixture read-back/recovery preview:

```text
candidate
→ confirmation
→ executor no-op
→ storage adapter design
→ dev SQLite/fixture preview
→ explicit write gate
→ fixture dry-run
→ explicit opt-in JSONL fixture store
→ read-back/replay preview
→ ContextPacket recovery
→ today-practice guidance recovery E2E
```

Real backend database persistence is intentionally not part of v2_8.

Recommended future phase:

```text
v2_9_x_agent_persistence_implementation
```

Before real writes, keep these mandatory:

```text
user confirmation
idempotency key
trace-link
redaction
storage-boundary check
backend/local ownership separation
```

## Regression handoff

Recommended commands:

```bash
PYTHONPATH=src python -m compileall -q src tests tools examples/scripts
PYTHONPATH=src python tools/check_development_harness.py
PYTHONPATH=src python -m pytest -q tests/test_v2_8_*.py
PYTHONPATH=src python -m pytest -q tests/test_v2_4_*agent*.py tests/test_v2_6_*agent*.py tests/test_v2_7_*agent*.py tests/test_v2_8_*.py
```

Full historical `pytest -q` may still include older shared-doc/version assertions outside this Agent-line scope. For this handoff, use the targeted Agent regression as the acceptance surface.

## Boundaries

```text
No backend database write.
No HarmonyOS local write by Agent.
No SQLite connection/table/row by handoff preview.
No LLM call by handoff preview.
No tool execution.
No Routine start.
No /accompaniment/generate.
No Engine adapter call.
No MIDI asset.
No playback.
No post-session recommendation card.
No change to frontend_fixtures/harmonyos.
No change to Engine music generation rules.
No change to shared docs in Agent track.
```

## Next recommendation

Do not keep expanding v2_8 with new capabilities.

Recommended next tracks:

```text
1. Integration track: merge Agent v2_8 handoff into shared docs/API contract if needed.
2. v2_9_x Agent Persistence Implementation: real storage adapter/migration behind explicit config and tests.
3. Engine track can resume independently without Agent persistence touching music generation boundaries.
```
