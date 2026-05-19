# v2_8_10 Agent Context Persistence Real Storage Adapter Design

## Goal

Define the future real storage adapter boundary for Agent context persistence without implementing a database write.

This version sits after:

```text
PracticePlan / RoutineHistory persistence candidate
→ ContextPersistenceConfirmationBoundary
→ ContextPersistenceExecutorNoop
→ ContextPersistenceStorageAdapterDesign
```

## New surfaces

```text
GET  /agent/context/persistence-storage-adapter/spec
POST /agent/context/persistence-storage-adapter/design-preview
CLI  /context-persistence-storage-adapter [json_payload]
```

## What this version defines

- `ContextPersistenceStorageAdapter` future interface
- future method contracts:
  - `preview_write`
  - `write_confirmed_context`
  - `read_context_snapshot`
  - `check_idempotency`
  - `record_trace_link`
- supported backend-long-term context entities:
  - `user_practice_profile`
  - `active_practice_plan`
  - `routine_history_summary`
  - `agent_trace_metadata`
  - `idempotency_record`
- future operation contracts:
  - `upsert_active_practice_plan`
  - `append_or_upsert_routine_history_summary`
  - `upsert_user_practice_profile`
- storage ownership alignment with v2_8_2
- idempotency / retry / migration requirements
- forbidden payload fields and redaction boundary

## What this version explicitly does not do

```text
No database connection
No database schema migration
No backend write
No HarmonyOS local write
No LLM call
No tool execution
No Routine start
No /accompaniment/generate call
No Engine adapter dispatch
No MIDI asset creation
No playback
No post-session recommendation card
```

## Future implementation rule

A real storage adapter must re-check:

```text
candidate preview accepted
user confirmation approved
executor readiness
idempotency key
trace link
storage-boundary ownership
sensitive-field redaction
retry/duplicate policy
```

before any backend write is allowed.

## Next recommended task

`v2_8_11_agent_context_persistence_storage_adapter_sqlite_dev_preview`

Suggested scope: still avoid production database. Implement a local dev-only storage adapter preview or fixture-backed contract if needed, with writes disabled by default.
