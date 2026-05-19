# Agent Context Persistence Dev Fixture Readback / Replay Preview v2_8_15

## Scope

`v2_8_15_agent_context_persistence_dev_fixture_readback_and_replay_preview` adds a read-only preview layer on top of the `v2_8_14` dev fixture JSONL store.

It is intended to validate the future context recovery chain:

```text
v2_8_14 explicit opt-in fixture JSONL store
→ v2_8_15 fixture read-back
→ context snapshot preview
→ replay preview without mutation
```

## API

```http
GET  /agent/context/persistence-dev-fixture-readback-replay/spec
POST /agent/context/persistence-dev-fixture-readback-replay/preview
```

## Terminal command

```text
/context-persistence-dev-fixture-readback-replay {json_payload}
```

Example:

```text
/context-persistence-dev-fixture-readback-replay {"fixtureStorePath":"./.jammate/dev_agent_fixture_store.jsonl","environment":"dev"}
```

## Input fields

```text
fixtureStorePath / fixture_store_path
environment / env
maxRecords / max_records
userId / user_id
candidateKind / candidate_kind
candidateId / candidate_id
confirmationId / confirmation_id
traceId / trace_id
filterTraceId / filter_trace_id
idempotencyKey / idempotency_key
entities / requestedEntities
```

## Behavior

This layer may read a safe development JSONL fixture file and return:

```text
fixture_read_result
replay_preview
context_snapshot_preview
trace_link_preview
validation
guard_summary
```

It can filter fixture records by:

```text
user_id
candidate_kind
candidate_id
confirmation_id
trace_id
idempotency_key
```

The replay result is only a preview shape. It does not restore live Agent state.

## Non-goals

This version does not:

```text
write files
create SQLite connections
create SQLite tables
write SQLite rows
write backend database records
write HarmonyOS local state
call LLM
execute tools
start Routine
call /accompaniment/generate
call Engine adapter
generate MIDI
start playback
create post-session recommendation cards
```

## Safety rules

Read-back is allowed only for dev/test/fixture environments and safe fixture paths.

Forbidden sensitive/runtime fields remain blocked or redacted:

```text
api_key / token / password
midi_base64
local_midi_path
payment_info
precise_location
hidden_chain_of_thought
```

HarmonyOS local Routine/playback state remains client-owned and must not be reconstructed as backend context.

## Completion criteria

```text
Contract route returns v2_8_15 spec
Preview route can read a v2_8_14 fixture JSONL file
Terminal command works
Context snapshot preview is returned
Replay is preview-only and does not mutate state
All no-side-effect guards remain false
Agent targeted regression passes
```

## Recommended next task

```text
v2_8_16_agent_context_persistence_profile_plan_history_snapshot_context_intake
```

That step can turn the read-back snapshot into a clean ContextPacket intake contract for user profile, active plan, and routine history summary, still without touching Engine generation.
