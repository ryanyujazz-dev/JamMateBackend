# Agent Practice Plan ActionCard E2E v2_6_8

## Purpose

`v2_6_8_agent_practice_plan_action_card_e2e` converts the first controlled Agent workflow result, `agent_practice_plan`, into a HarmonyOS Routine-facing ActionCard payload.

This version does **not** add playback execution. It only makes the controlled practice plan easier for the Routine module to render and use as a setup starting point.

---

## Chain

```text
Tool Preview
→ Confirmation
→ ToolExecutor Dry-run
→ Workflow Descriptor
→ Controlled PracticePlanner Execution
→ HarmonyOSAgentActionCard
→ routine_practice_plan_payload
```

---

## New payload

The ActionCard result preview now includes:

```text
result_preview.routine_practice_plan_payload
```

Payload fields:

```text
payload_contract_version
plan
routine_config_candidate
routine_blocks
next_client_actions
client_button_semantics
trace_id
route_called
engine_adapter_called
midi_asset_created
playback_started
accompaniment_generate_call_enabled
start_requires_separate_routine_confirmation
```

Important rule:

```text
open_routine_setup does not start playback.
```

Routine may use this payload to open a setup screen, but starting playback remains a separate user-confirmed client action.

---

## Terminal command

```text
/practice-plan-action-card
```

Required prior chain:

```text
/tool-preview agent_practice_plan {"userInput":"练 30 分钟 Blue Bossa", "availableMinutes":30}
/confirm
/execute-dry-run
/dispatch-dry-run
/execute-controlled
/practice-plan-action-card
```

---

## API routes

```http
GET /agent/actions/practice-plan/spec
POST /agent/actions/practice-plan/execute-controlled
```

The route follows the existing guarded chain and then returns a Routine-facing ActionCard payload.

---

## Guardrails

This version must not:

```text
call /accompaniment/generate
execute agent_playback_prepare
call engine adapters
create MIDI assets
start playback
modify pattern / voicing / expression / pedal
modify shared docs or HarmonyOS fixtures
```

---

## Completion standard

`v2_6_8` is complete when:

```text
controlled agent_practice_plan produces an ActionCard
ActionCard contains routine_practice_plan_payload
Routine payload includes plan blocks and RoutineConfig candidate
next client action can be open_routine_setup
all playback/asset flags remain false
Agent targeted regression passes
```
