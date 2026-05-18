# Agent Context Persistence Snapshot Context Intake v2_8_16

`v2_8_16_agent_context_persistence_profile_plan_history_snapshot_context_intake` converts a dev persistence read-back snapshot into `ContextPacket`-ready practice context sections:

```text
UserPracticeProfileContext
ActivePracticePlanContext
RoutineHistoryContext
AssembledPracticeContext
```

It does not implement recommendation logic. It only restores context shape for a later user-initiated Agent turn such as “今天该练什么？”.

## API surfaces

```text
GET  /agent/context/persistence-snapshot-context-intake/spec
POST /agent/context/persistence-snapshot-context-intake/preview
```

## Terminal surface

```text
/context-persistence-snapshot-context-intake [json_payload]
```

Example:

```text
/context-persistence-snapshot-context-intake {"fixtureStorePath":"./.jammate/dev_agent_fixture_store.jsonl","environment":"dev","filterTraceId":"trace_fixture_store"}
```

## Output shape

```text
normalized_context_sections
context_packet_section
context_packet_kwargs
context_builder_injection_preview
validation
guard_summary
```

`context_packet_kwargs` can be passed to `ContextBuilder` through:

```text
context_persistence_snapshot_context_intake=<context_packet_section>
```

The builder injects available sections into `learner_context` while preserving the existing no-side-effect boundary.

## Metadata-only fallback

The current dev fixture store records often contain persistence metadata rather than full profile / plan / history payloads. In that case v2_8_16 builds metadata-only placeholder sections, for example:

```text
profile_status = restored_snapshot_preview_metadata_only
plan_status = restored_snapshot_preview_metadata_only
```

This is intentional. The purpose is to verify the future context recovery chain without pretending metadata is full learner data.

## Non-goals

```text
No backend database write
No HarmonyOS local write
No SQLite connection/table/row
No LLM call
No tool execution
No Routine start
No /accompaniment/generate
No Engine adapter call
No MIDI asset creation
No playback
No post-session recommendation card
```

## Next recommended task

```text
v2_8_17_agent_today_practice_guidance_persisted_context_recovery_e2e
```
