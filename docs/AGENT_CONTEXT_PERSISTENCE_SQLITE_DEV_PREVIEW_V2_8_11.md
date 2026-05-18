# Agent Context Persistence SQLite Dev Preview — v2_8_11

## Purpose

`v2_8_11_agent_context_persistence_storage_adapter_sqlite_dev_preview` adds a local-development preview surface for the future Agent context persistence adapter.

It is not a real storage implementation yet. It provides:

- SQLite schema DDL preview
- idempotency-key preview
- trace-link preview
- read-snapshot query shape preview
- fixture snapshot shape preview
- no-side-effect guard report

## Surfaces

```text
GET  /agent/context/persistence-sqlite-dev-preview/spec
POST /agent/context/persistence-sqlite-dev-preview/preview
/context-persistence-sqlite-dev-preview [json_payload]
```

## Contract

The contract version is:

```text
v2_8_11
```

The terminal command is:

```text
/context-persistence-sqlite-dev-preview
```

Example:

```text
/context-persistence-sqlite-dev-preview {"userId":"user_001","entities":["user_practice_profile","active_practice_plan","routine_history_summary"]}
```

## SQLite schema preview

The preview exposes future table shapes only. It does not create a database connection and does not apply migrations.

Previewed tables:

```text
user_practice_profiles
active_practice_plans
practice_history_summaries
context_persistence_idempotency_keys
agent_trace_metadata
```

## Write gate

Default status:

```text
sqlite_dev_preview_ready_no_write
```

If a caller requests dev write through `devWriteEnabled=true`, v2_8_11 blocks the request:

```text
sqlite_dev_preview_blocked
blocked_reasons: ["dev_write_requested_but_v2_8_11_is_preview_only"]
```

This is intentional. The version only prepares the development adapter contract.

## Strict guards

This version must not:

```text
create a SQLite connection
create SQLite tables
write SQLite rows
write backend database
write HarmonyOS local device state
call LLM
execute tool
start Routine
call /accompaniment/generate
call Engine adapter
generate MIDI
start playback
create post-session recommendation card
```

## Storage ownership reminder

Backend future storage may own compact durable context:

```text
UserPracticeProfile
ActivePracticePlan / saved PracticePlan
RoutineHistory summary / PracticeHistoryContextItem
sanitized Agent trace metadata
idempotency records
```

HarmonyOS remains the owner of live local state:

```text
Routine session runtime
timer / pause / resume
playback state
local MIDI cache/path
score viewport
UI draft/setup state
```

Forbidden payload fields remain excluded:

```text
api_key
token
password
secret
midi_base64
local_midi_path
playback_position
timer_state
precise_location
payment_info
hidden_chain_of_thought
```

## Recommended next task

```text
v2_8_12_agent_context_persistence_dev_sqlite_explicit_write_gate
```

Suggested next step: introduce an explicit dev-only write gate and config-path contract, but still require confirmation, idempotency, trace-link, redaction, and storage-boundary checks before any real SQLite write is permitted.
