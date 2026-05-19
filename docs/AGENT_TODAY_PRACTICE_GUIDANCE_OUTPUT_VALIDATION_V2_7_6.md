# AGENT Today Practice Guidance Output Validation V2_7_6

## Scope

`v2_7_6_agent_today_practice_guidance_output_validation` adds the validation and normalization gate for a future LLM-generated `TodayPracticeGuidanceOutput`.

This version does **not** call the LLM. It assumes a future provider boundary has returned a structured output and validates whether that output is safe for HarmonyOS Routine display.

## What this version does

```text
TodayPracticeGuidanceOutput
→ validation policy
→ normalized candidate-only guidance payload
→ accepted / blocked summary
```

Allowed output:

```text
practice guidance summary
recommended focus
recommended practice blocks
editable Routine candidate drafts
client-side next actions such as show_guidance / present_routine_candidate
```

Blocked output:

```text
start Routine now
start playback now
call /accompaniment/generate
generate MIDI
execute tool / dispatch workflow / invoke engine adapter
midi_base64 / local_midi_path / api_key / hidden_chain_of_thought
user_confirmation_required=false
```

## Contract routes

```http
GET  /agent/context/today-practice-guidance/output-validation/spec
POST /agent/context/today-practice-guidance/output-validation/validate
```

## Terminal command

```text
/today-practice-guidance-validate [json_payload]
```

## Key boundaries

```text
llm_called = false
tool_executed = false
routine_start_enabled = false
accompaniment_generate_call_enabled = false
engine_adapter_called = false
midi_asset_created = false
playback_started = false
```

## HarmonyOS Routine relationship

The validator returns UI-flow-neutral candidate data. HarmonyOS still decides whether to show guidance as a normal answer, ActionCard, Bottom Sheet, Setup prefill, queue item, or another future presentation.

The validator never assumes a specific frontend flow.

## Why this exists

The previous v2_7_4 contract defined what the LLM should output. v2_7_6 defines what must be true before any LLM output can be treated as safe client-facing guidance.

This keeps the next-practice guidance flow aligned with the Agent capability map:

```text
LLM may answer and propose candidates.
LLM may not directly execute Routine, playback, accompaniment generation, or engine internals.
```
