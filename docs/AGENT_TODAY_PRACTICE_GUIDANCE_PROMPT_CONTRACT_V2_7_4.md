# AGENT_TODAY_PRACTICE_GUIDANCE_PROMPT_CONTRACT_V2_7_4

## Scope

`v2_7_4_agent_today_practice_guidance_prompt_contract` defines the prompt and output contract for the future user-initiated question:

```text
今天该练什么？
```

This version is still a contract/preview layer. It does not call the LLM, does not create the final guidance answer, does not start Routine, and does not generate accompaniment assets.

## Pipeline

```text
Active PracticePlan Context
+ RoutineHistory Context
+ Today constraints / available minutes
→ assembled_practice_context
→ TodayPracticeGuidance prompt messages
→ TodayPracticeGuidanceOutput schema
```

## New surfaces

```text
GET  /agent/context/today-practice-guidance/spec
POST /agent/context/today-practice-guidance/prompt-preview

/today-practice-guidance-prompt [json_payload]
```

## Output contract

Future LLM responses should follow `TodayPracticeGuidanceOutput`:

```text
guidance_mode
summary
recommended_focus
recommended_blocks
routine_candidates
user_confirmation_required
next_client_actions
```

The response should answer the user's current planning question only. It must not create a post-session recommendation card automatically.

## Guardrails

```text
llm_called = false
guidance_response_created = false
recommendation_created = false
routine_start_enabled = false
accompaniment_generate_call_enabled = false
engine_adapter_called = false
midi_asset_created = false
playback_started = false
```

## Product rule

Routine end remains HarmonyOS-owned. The client may show normal completion details such as practice content, duration, and saved status. Agent guidance is only used when the user later initiates a conversation asking what to practice next.
