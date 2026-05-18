# Agent User Practice Profile Context Intake V2.8.1

## Purpose

`v2_8_1_agent_user_profile_context_intake` adds a context-only intake contract for durable learner profile information:

```text
UserPracticeProfile
→ UserPracticeProfileContext
→ ContextPacket.learner_context.user_practice_profile_context
→ assembled_practice_context.profile_summary
```

This layer gives future “今天该练什么？” guidance access to stable user facts such as current goal, preferred styles, comfort tempo ranges, focus areas, common tunes, and avoidances.

## Important boundary

UserPracticeProfile is context, not a recommendation rule engine.

The v2.8.1 layer does not decide what the user should practice. It only normalizes safe, durable context for later prompt/provider/validation layers.

## New surfaces

```text
GET  /agent/context/user-practice-profile/spec
POST /agent/context/user-practice-profile/intake
/user-practice-profile-context [json_payload]
```

## Accepted profile fields

```text
user_id / userId
current_goal / currentGoal
preferred_styles / preferredStyles
focus_areas / focusAreas
skill_focus / skillFocus
common_tunes / commonTunes / frequent_tunes / frequentTunes
comfortable_tempo_ranges / comfortableTempoRanges
preferred_session_minutes / preferredSessionMinutes
practice_mode_preference / practiceModePreference
avoid
saved_routine_preferences / savedRoutinePreferences
updated_at / updatedAt
```

## Sanitization

The intake layer drops sensitive, local-only, or unsafe fields before they enter Agent context:

```text
api_key / apiKey
token / access_token / refresh_token
password / secret
local_midi_path / localMidiPath
midi_base64 / midiBase64
precise_location / preciseLocation
payment_info / paymentInfo
hidden_chain_of_thought / hiddenChainOfThought
playback position / current position / remaining seconds / raw asset
```

Unknown fields are also discarded and reported through validation warnings.

## Tempo normalization

Comfort tempo ranges accept either array or object forms:

```json
{
  "comfortableTempoRanges": {
    "medium_swing": [130, 90],
    "bossa_nova": { "min": 100, "max": 145 }
  }
}
```

Reversed ranges are normalized to `min/max` with a warning:

```json
{
  "medium_swing": { "min": 90, "max": 130 }
}
```

Invalid ranges are skipped with warnings instead of crashing the request.

## ContextBuilder integration

`ContextBuilder` now supports profile input through either a normalized context section or raw profile payload:

```text
user_practice_profile_context / userPracticeProfileContext
user_practice_profile / userPracticeProfile
input_profile / inputProfile
```

When supplied, it injects:

```text
learner_context.user_practice_profile_context
routing_hints.user_practice_profile_context_present = true
```

## Practice context assembly integration

Practice context assembly now accepts profile context alongside active plan and history:

```text
active_practice_plan_context
routine_history_context
user_practice_profile_context
today_constraints
```

The assembled context includes:

```text
assembled_practice_context.user_practice_profile_context
assembled_practice_context.profile_summary
assembled_practice_context.llm_decision_inputs.user_practice_profile_input_available
```

## Side-effect guards

This version preserves all Agent safety boundaries:

```text
llm_called = false
tool_executed = false
storage_written = false
route_called = false
engine_adapter_called = false
midi_asset_created = false
playback_started = false
accompaniment_generate_call_enabled = false
routine_start_enabled = false
```

## Regression coverage

Main test file:

```text
tests/test_v2_8_1_agent_user_profile_context_intake.py
```

Covers:

- contract/spec route;
- camelCase and snake_case profile fields;
- tempo-range normalization;
- sensitive/local field dropping;
- ContextBuilder learner_context injection;
- assembled_practice_context profile summary;
- terminal `/user-practice-profile-context` command;
- no LLM/tool/storage/engine/MIDI/playback side effects.

## Recommended next task

```text
v2_8_2_agent_practice_context_storage_boundary_contract
```

Define which practice-context objects are owned by HarmonyOS local storage, backend long-term storage, Agent trace, or temporary requests. Still avoid implementing full database persistence in the next step.
