# AGENT_ROUTINE_CONFIG_PREPARE_CONTRACT_V2_7_0

## Purpose

`v2_7_0_agent_routine_config_prepare_contract` adds a low-risk Agent contract that prepares an editable HarmonyOS Routine setup draft. It is designed for the Routine module to open a setup screen from natural language, a practice plan, or a selected practice block.

## New Tool

```text
agent_routine_config_prepare
→ RoutineConfigPreparer.prepare_candidate
```

The tool is descriptor/draft only. It does not execute playback, call `/accompaniment/generate`, call engine adapters, or create MIDI assets.

## New Payload

```text
RoutineConfigPrepareActionPayload
```

Key fields:

```text
routine_config_candidate
routine_blocks
source_inputs
validation
next_client_actions
client_button_semantics
```

The candidate includes editable Routine setup values such as style, tempo, duration, tune/material, muted roles, output format, loop/count-in preferences, and guard flags.

## Terminal

```text
/routine-config-prepare
```

Expected sequence:

```text
/tool-preview agent_routine_config_prepare {...}
/confirm
/execute-dry-run
/dispatch-dry-run
/routine-config-prepare
```

## API

```http
GET  /agent/actions/routine-config/spec
POST /agent/actions/routine-config/prepare
```

## Guard Rules

```text
routine_start_enabled = false
accompaniment_generate_call_enabled = false
playback_execution_enabled = false
engine_adapter_dispatch_enabled = false
midi_asset_creation_enabled = false
```

Opening Routine setup is allowed. Starting a playable Routine remains a separate future user-confirmed client action.

## Non-goals

- No `/accompaniment/generate` call.
- No real `agent_playback_prepare` execution.
- No engine adapter dispatch.
- No MIDI asset creation.
- No changes to Engine pattern / voicing / expression / pedal rules.
