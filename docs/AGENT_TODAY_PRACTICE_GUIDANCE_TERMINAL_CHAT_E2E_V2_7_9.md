# AGENT_TODAY_PRACTICE_GUIDANCE_TERMINAL_CHAT_E2E_V2_7_9

## Purpose

`v2_7_9_agent_today_practice_guidance_terminal_chat_e2e` connects an ordinary terminal chat turn such as:

```text
今天该练什么？
```

to the existing guarded today-practice guidance chain:

```text
ordinary terminal user turn
→ narrow today-practice intent detection
→ context assembly / prompt contract
→ LLM provider boundary or supplied providerResult
→ output validation
→ display-only HarmonyOS Routine ActionCard
```

This version does not add a new Routine workflow and does not execute playback.

## Contract

```text
version: v2_7_9
spec:    GET  /agent/context/today-practice-guidance/terminal-chat/spec
preview: POST /agent/context/today-practice-guidance/terminal-chat/e2e-preview
terminal: ordinary chat turn, e.g. “今天该练什么？”
optional explicit command: /today-practice-guidance-chat-e2e [json_payload]
```

## Guarantees

The terminal E2E result is display-only. It may return:

```text
guidance summary
recommended focus
recommended practice blocks
editable Routine candidates
available client actions
trace_id
```

It must not:

```text
start Routine
start playback
call /accompaniment/generate
call engine adapters
create MIDI assets
execute tools
decide HarmonyOS UI presentation
create automatic post-session recommendation cards
```

Routine start and accompaniment generation remain separate user-confirmed client actions.

## Why this exists

Previous versions already built the pieces:

```text
v2_7_4 prompt contract
v2_7_6 output validation
v2_7_7 provider boundary E2E
v2_7_8 display-only ActionCard
```

`v2_7_9` makes the normal terminal chat path use those pieces when the user directly asks what to practice today.

## Frontend boundary

HarmonyOS may render the resulting ActionCard as a card, bottom sheet, setup page, queue item, or another UI surface. The Agent payload intentionally sets:

```text
client_decides_presentation = true
frontend_flow_assumption = false
```

## Development boundary

This is Agent-line only. It does not modify Engine generation rules, pattern, voicing, expression, pedal, MIDI demos, shared docs, or HarmonyOS fixtures.
