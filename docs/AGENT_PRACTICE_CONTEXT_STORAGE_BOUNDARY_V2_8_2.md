# Agent Practice Context Storage Boundary v2_8_2

## 0. Scope

`v2_8_2_agent_practice_context_storage_boundary_contract` defines the ownership boundary for practice-context data used by the Agent route.

This version is a contract/preview surface only. It does not implement a database, sync job, local write, LLM call, tool execution, Routine start, `/accompaniment/generate`, engine adapter dispatch, MIDI asset creation, or playback.

## 1. Why this exists

The Agent context chain can now see:

- active PracticePlan context
- Routine history context
- UserPracticeProfile context
- today constraints
- assembled practice context

Before adding persistence, the project needs a stable answer to a more basic question:

```text
Which context belongs to HarmonyOS local state?
Which context belongs to backend long-term storage?
Which context is request-only?
Which context is Agent trace/debug metadata?
Which fields should never enter Agent context?
```

## 2. Ownership categories

### 2.1 HarmonyOS local-only

HarmonyOS owns live UI/runtime state:

```text
current RoutineSession timer / pause / resume state
playback position and local player state
local MIDI file path and decoded MIDI cache
Routine setup form drafts and current UI selection
score viewport / scroll position / local render state
```

These should not be treated as durable Agent context. They may be summarized into a current request when useful, but raw playback/local-cache fields must not enter ContextPacket.

### 2.2 Backend long-term context

Backend storage should eventually own durable practice objects:

```text
UserPracticeProfile
ActivePracticePlan and plan progress summary
RoutineHistory summary / PracticeHistoryContextItem
saved leadsheets, routine templates, and user-approved practice assets
sanitized Agent trace metadata when persistence exists
```

`v2_8_2` does not write these objects yet. It only documents that they are backend-owned when persistence exists.

### 2.3 Request-ephemeral context

The following are used for the current turn only:

```text
current user question
available_minutes / duration constraints for this turn
current screen/session summary
temporary Routine candidate or setup preview
```

They should not become durable storage unless they are converted into explicit saved objects.

### 2.4 Agent trace context

Trace context is for debugging and audit:

```text
trace_id and trace step names
sanitized tool preview metadata
validation summaries and blocked reasons
provider-boundary status without hidden chain-of-thought
```

Trace must not store secrets, raw API keys, raw MIDI assets, local MIDI paths, or hidden reasoning.

### 2.5 Never store or contextualize

These must not enter Agent context or backend summaries:

```text
api_key / token / password
midi_base64 and local_midi_path
precise_location / payment_info
hidden_chain_of_thought
raw playback position / timer state as durable Agent context
```

## 3. API surface

```http
GET  /agent/context/storage-boundary/spec
POST /agent/context/storage-boundary/preview
```

The preview route accepts arbitrary practice-context-like signals and returns:

```text
context_storage_boundary
ownership_matrix
context_packet_boundary
sync_boundary
retention_boundary
field_classification
validation
guard_summary
```

It does not echo raw sensitive values.

## 4. Terminal command

```text
/practice-context-storage-boundary [json_payload]
```

Example:

```text
/practice-context-storage-boundary {"availableMinutes":20,"userPracticeProfile":{"currentGoal":"comping"},"playbackState":{"localMidiPath":"/tmp/nope.mid"}}
```

Expected behavior:

```text
PracticeContextStorageBoundary>
  version: v2_8_2
  validation_status: boundary_ready_with_warnings
  storage_contract_only: true
  storage_written: false
  backend_write_enabled: false
```

## 5. ContextPacket boundary

May enter ContextPacket:

```text
active_practice_plan_context
practice_history_context
user_practice_profile_context
assembled_practice_context
today_constraints
sanitized_agent_trace_metadata
```

Must not enter ContextPacket:

```text
current playback position
local MIDI file path
midi_base64 asset payload
API keys / tokens / passwords
payment information
precise geolocation
hidden chain-of-thought
```

`ContextBuilder` may assemble normalized context sections, but it must not become a storage layer.

## 6. Completion criteria

`v2_8_2` is complete when:

```text
/practice-context-storage-boundary works
GET /agent/context/storage-boundary/spec works
POST /agent/context/storage-boundary/preview works
context/runtime manifests expose the boundary
payload classifies local/backend/request/trace/never-store contexts
sensitive/local asset fields are detected without raw value echo
all no-side-effect guards remain false
Agent targeted regression passes
```

## 7. Next recommended task

```text
v2_8_3_agent_today_practice_guidance_profile_aware_e2e
```

Goal: connect `UserPracticeProfileContext` into the today-practice guidance prompt/provider/action-card E2E so “今天该练什么” can actually use long-term user preference context, while still returning candidate-only guidance and not starting Routine automatically.
