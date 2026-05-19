# Agent Today Practice Guidance Persisted Context Terminal Memory Controls v2_8_18

## Goal

`v2_8_18_agent_today_practice_guidance_persisted_context_terminal_memory_controls` adds terminal-only temporary memory controls for recovered persisted context.

The goal is developer usability: when testing `今天该练什么？` in the terminal, a developer can load profile / active plan / routine history context once, then ask ordinary natural-language turns without pasting the full JSON payload each time.

## Terminal commands

```text
/persisted-context-load [json_payload]
/persisted-context-show
/persisted-context-clear
```

`/persisted-context-load` accepts the same high-level inputs used by persisted context recovery previews:

```json
{
  "availableMinutes": 25,
  "userPracticeProfile": {
    "currentGoal": "提高 jazz comping 稳定性",
    "preferredStyles": ["medium_swing", "bossa_nova"],
    "focusAreas": ["ii-V-I", "comping"],
    "comfortableTempoRanges": {
      "medium_swing": [90, 120],
      "bossa_nova": [100, 145]
    }
  },
  "practicePlan": {
    "title": "Persisted Medium Swing Comping Plan",
    "status": "active",
    "planBlocks": [
      {"title": "ii-V-I guide tones", "style": "medium_swing", "tempo": 104, "durationMinutes": 15}
    ]
  },
  "routineHistoryRecords": [
    {"sessionId": "session_001", "title": "Blue Bossa comping", "style": "bossa_nova", "tempo": 118, "actualSeconds": 900, "completed": true}
  ]
}
```

After loading, an ordinary terminal turn such as:

```text
今天该练什么？
```

will automatically route through the persisted-context recovery E2E path and inject the loaded terminal memory into the guidance context.

## Boundary

This feature is terminal session memory only.

It does not:

```text
write backend database
write HarmonyOS local state
create SQLite connections / tables / rows
call LLM from the load/show/clear commands
execute tools
start Routine
call /accompaniment/generate
call Engine adapter
create MIDI assets
start playback
create post-session recommendation cards
```

## Explicit context wins

If a specific today-practice command already includes explicit profile / plan / history / snapshot context arguments, that explicit payload wins and terminal memory is not injected. This avoids hidden overrides during debugging.

## Intended next step

`v2_8_19_agent_today_practice_guidance_terminal_memory_to_harmonyos_debug_fixture` can add a HarmonyOS-facing debug fixture preview that mirrors these terminal memory controls for front-end integration testing, still without touching Engine generation.
