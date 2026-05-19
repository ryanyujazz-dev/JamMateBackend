# Agent PracticePlan Persistence Candidate Contract v2_8_6

## 1. Scope

`v2_8_6_agent_practice_plan_persistence_candidate_contract` defines a candidate-only contract for saving or updating a `PracticePlan`.

This is not a database implementation. It only shapes a reviewable candidate payload so HarmonyOS or a future backend persistence executor can later ask for explicit user confirmation before writing anything.

## 2. Surfaces

```text
GET  /agent/practice-plan/persistence-candidate/spec
POST /agent/practice-plan/persistence-candidate/preview
```

Terminal command:

```text
/practice-plan-persistence-candidate [json_payload]
```

## 3. Input examples

Save new plan candidate:

```json
{
  "practicePlan": {
    "title": "Medium Swing Comping Plan",
    "mainFocus": "ii-V-I comping 稳定性",
    "durationMinutes": 30,
    "planBlocks": [
      {"title": "Guide-tone warmup", "style": "medium_swing", "tempo": 96, "durationMinutes": 10},
      {"title": "Blue Bossa comping", "style": "bossa_nova", "tempo": 120, "durationMinutes": 20}
    ]
  }
}
```

Update existing plan candidate:

```json
{
  "operation": "update_existing",
  "targetPlanId": "plan_001",
  "existingPracticePlan": {"planId": "plan_001", "title": "Old Plan"},
  "practicePlan": {"planId": "plan_001", "title": "Updated Plan", "planBlocks": []}
}
```

## 4. Output shape

The preview returns:

```text
practice_plan_persistence_candidate_payload
practice_plan_persistence_candidate_summary
```

Important sections:

```text
operation
candidate_id
target_plan_ref
normalized_practice_plan
candidate_action
diff_preview
confirmation_policy
storage_boundary
validation
guard_summary
```

## 5. Confirmation boundary

The required ladder is:

```text
preview_candidate
→ user_reviews_or_edits
→ user_confirms_save_or_update
→ future_persistence_executor_writes_backend
→ client_refreshes_cached_plan
```

Only the first two are represented in this version. The future executor is intentionally not implemented.

## 6. No-side-effect guarantees

`v2_8_6` must always keep these false:

```text
llm_called
tool_executed
storage_written
backend_database_written
local_device_written
engine_adapter_called
midi_asset_created
playback_started
routine_start_enabled
accompaniment_generate_call_enabled
```

## 7. Security / sanitation

The normalized candidate must discard or avoid echoing:

```text
api_key / token / password / secret
midi_base64
local_midi_path
payment_info
precise_location
hidden_chain_of_thought
```

## 8. Design principle

Do not turn this into an automatic persistence system.

The Agent can propose:

```text
“Here is a plan worth saving or updating.”
```

But the write path must remain:

```text
candidate preview
→ explicit user confirmation
→ future controlled persistence executor
```

The LLM must not directly write `PracticePlan` storage.
