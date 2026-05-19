# AGENT_TODAY_PRACTICE_GUIDANCE_ACTION_CARD_V2_7_8

## Purpose

`v2_7_8_agent_today_practice_guidance_action_card` wraps validated `TodayPracticeGuidanceOutput` into a HarmonyOS Routine-facing display ActionCard.

This is the first user-visible container for the “今天该练什么？” flow:

```text
assembled_practice_context
→ prompt contract
→ provider boundary / supplied provider result
→ output validation
→ display-only Routine ActionCard
```

## What this version does

- Builds `TodayPracticeGuidanceActionCardPayload`.
- Converts accepted guidance into:
  - summary section
  - recommended focus
  - adjustment reason
  - recommended blocks
  - Routine candidate cards
  - client button semantics
- Adds CLI command:

```text
/today-practice-guidance-action-card [json_payload]
```

- Adds API routes:

```http
GET  /agent/context/today-practice-guidance/action-card/spec
POST /agent/context/today-practice-guidance/action-card/preview
```

## What this version does not do

```text
No automatic post-session recommendation card.
No Routine start.
No playback start.
No /accompaniment/generate call.
No engine adapter call.
No MIDI asset creation.
No tool execution.
No frontend UI flow assumption.
```

## HarmonyOS boundary

The returned ActionCard is a display payload. HarmonyOS may render it as:

```text
card
bottom sheet
Routine setup draft
inline guidance panel
queue item
other client-defined surface
```

The backend Agent contract does not require any specific UI flow.

## User confirmation rule

The ActionCard itself has no side effects and does not require confirmation merely to display.

Any future Routine start, playback, or accompaniment generation remains a separate user-confirmed client action.

## Safety guards

The payload always keeps these false:

```text
tool_executed = false
routine_start_enabled = false
route_called = false
engine_adapter_called = false
midi_asset_created = false
playback_started = false
accompaniment_generate_call_enabled = false
```
