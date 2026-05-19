# Agent RoutineHistory Persistence Candidate Contract — v2_8_7

## Scope

`v2_8_7_agent_routine_history_persistence_candidate_contract` defines a candidate-only contract for saving or uploading sanitized RoutineHistory summaries.

This version is deliberately **not** a database implementation. It only builds a preview payload that a client can show to the user before a future confirmation/write step exists.

## API

```text
GET  /agent/routine-history/persistence-candidate/spec
POST /agent/routine-history/persistence-candidate/preview
```

## Terminal command

```text
/routine-history-persistence-candidate [json_payload]
```

Example:

```json
{
  "operation": "upsert",
  "historyScopeId": "user_001",
  "routineHistoryRecords": [
    {
      "sessionId": "session_001",
      "routineId": "routine_blue_bossa",
      "title": "Blue Bossa comping",
      "tuneTitle": "Blue Bossa",
      "style": "bossa_nova",
      "tempo": 118,
      "actualSeconds": 1260,
      "completed": true,
      "practiceGoal": "bossa comping stability",
      "planId": "plan_001",
      "planBlockId": "block_bossa"
    }
  ]
}
```

## Supported operations

```text
append_new_records
upsert_summary_batch
```

Both are preview-only in v2_8_7.

## Ownership boundary

HarmonyOS owns:

```text
live RoutineSession state
timer / pause / resume
playback position
local MIDI path / decoded playback cache
Routine completion UI state
```

Backend long-term context should own in the future, after explicit user confirmation:

```text
sanitized RoutineHistory summaries
PracticeHistoryContextItem summaries
aggregate practice-history summary
trace metadata references
```

## Guardrails

This contract must not:

```text
write database
write local device state
call LLM
execute tools
create post-session recommendation card
start Routine
call /accompaniment/generate
call Engine adapter
create MIDI asset
start playback
```

The payload must drop:

```text
midi_base64
local_midi_path
current playback position
timer state
raw asset payloads
API keys / tokens / secrets
payment info
precise location
hidden chain-of-thought
```

## Design reason

Routine completion should remain simple on the HarmonyOS side: show what was practiced, how long it lasted, and that it was recorded.

Agent should use RoutineHistory only on the next user-initiated planning turn, such as:

```text
今天该练什么？
```

Therefore v2_8_7 only prepares a safe candidate payload for future persistence. It does not turn Routine completion into an Agent recommendation moment.

## Regression expectations

```text
compileall passes
harness passes
v2_8_7 tests pass
Agent targeted regression remains green
```
