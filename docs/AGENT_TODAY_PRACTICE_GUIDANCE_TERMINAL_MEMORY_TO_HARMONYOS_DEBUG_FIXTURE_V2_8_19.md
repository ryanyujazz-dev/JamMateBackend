# Agent Today Practice Guidance Terminal Memory → HarmonyOS Debug Fixture v2_8_19

## Purpose

`v2_8_19_agent_today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture` converts the terminal-only persisted context memory from `v2_8_18` into a HarmonyOS-facing debug fixture preview.

This lets HarmonyOS developers test the chain:

```text
recovered user profile / active practice plan / routine history
→ HarmonyOS debug fixture state
→ Agent persisted-context recovery preview
→ display-only TodayPracticeGuidance ActionCard / Routine candidate
```

without pasting a large profile / plan / history JSON block every time.

## Surfaces

```text
GET  /agent/context/today-practice-guidance/terminal-memory-harmonyos-debug-fixture/spec
POST /agent/context/today-practice-guidance/terminal-memory-harmonyos-debug-fixture/preview
CLI  /persisted-context-harmonyos-debug-fixture [json_payload]
```

## Inputs

The preview accepts either:

```text
1. a terminal persisted context memory object
2. a snapshotContextIntakePayload
3. direct userPracticeProfile / practicePlan / routineHistoryRecords JSON
```

The terminal command can also use the currently loaded session memory when no JSON payload is supplied:

```text
/persisted-context-load { ...profile/plan/history... }
/persisted-context-harmonyos-debug-fixture
```

## Output

The response includes:

```text
harmonyos_debug_fixture
agent_request_preview
terminal_command_preview
snapshot_context_intake_payload
recovered_context_summary
validation
guard_summary
```

The `agent_request_preview` points to:

```text
POST /agent/context/today-practice-guidance/persisted-context-recovery/e2e-preview
```

HarmonyOS can use the fixture payload to populate a debug screen and call the persisted-context recovery preview endpoint.

## Boundary

This version is a debug-fixture preview only.

It does **not**:

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
```

HarmonyOS remains responsible for presentation. Agent returns candidate/display data only.

## Recommended next task

```text
v2_8_20_agent_harmonyos_debug_fixture_roundtrip_terminal_e2e
```

That version should test a roundtrip from fixture preview back into persisted-context recovery guidance, still without starting Routine or touching Engine.
