# Agent HarmonyOS Debug Fixture Roundtrip Terminal E2E v2_8_20

## Purpose

`v2_8_20_agent_harmonyos_debug_fixture_roundtrip_terminal_e2e` verifies that the HarmonyOS debug fixture produced by `v2_8_19` can roundtrip back into the Agent persisted-context recovery guidance preview.

The target chain is:

```text
terminal persisted-context memory / direct profile-plan-history JSON
→ v2_8_19 HarmonyOS debug fixture preview
→ fixture.agentRequestPreview.body
→ v2_8_17 persisted-context recovery E2E
→ display-only TodayPracticeGuidance ActionCard / Routine candidate
```

This is a frontend/debug interoperability check only. It proves that the fixture payload shape HarmonyOS sees can be fed back into the Agent preview endpoint without losing recovered profile, active plan, or RoutineHistory context.

## Surfaces

```text
GET  /agent/context/today-practice-guidance/harmonyos-debug-fixture-roundtrip/spec
POST /agent/context/today-practice-guidance/harmonyos-debug-fixture-roundtrip/e2e-preview
CLI  /harmonyos-debug-fixture-roundtrip [json_payload]
```

## Accepted input forms

The roundtrip preview accepts:

```text
1. harmonyosDebugFixture / harmonyos_debug_fixture
2. a v2_8_19 debug fixture payload containing harmonyos_debug_fixture
3. direct profile / active plan / routine history JSON
4. terminal persisted-context memory when the CLI has already run /persisted-context-load
```

If direct JSON or terminal memory is used, the builder first creates the same v2_8_19 HarmonyOS debug fixture preview, then extracts its `agentRequestPreview.body`.

## Output

The response includes:

```text
fixture_payload
agent_request_body
recovery_payload
recovery_summary
roundtrip_validation
guard_summary
```

The roundtrip is accepted only when:

```text
agent preview route matches /agent/context/today-practice-guidance/persisted-context-recovery/e2e-preview
profile / active plan / routine history context can be recovered
TodayPracticeGuidance ActionCard validates
```

## CLI example

```text
/persisted-context-load { ...profile / practicePlan / routineHistoryRecords... }
/harmonyos-debug-fixture-roundtrip
```

Or directly:

```text
/harmonyos-debug-fixture-roundtrip { ...profile / practicePlan / routineHistoryRecords / providerResult... }
```

## Boundary

This version does **not**:

```text
write backend database
write HarmonyOS local state
create SQLite connection / tables / rows
call LLM
execute tool
start Routine
call /accompaniment/generate
call Engine adapter
generate MIDI
start playback
create post-session recommendation card
change frontend_fixtures/harmonyos
```

HarmonyOS still owns presentation and local debug state. Agent only returns preview/candidate data.

## Recommended next task

```text
v2_8_21_agent_harmonyos_debug_fixture_api_request_pack
```

That version can package the debug fixture roundtrip into a clearer API request pack for frontend developers, still without changing `frontend_fixtures/harmonyos` from the Agent line.
