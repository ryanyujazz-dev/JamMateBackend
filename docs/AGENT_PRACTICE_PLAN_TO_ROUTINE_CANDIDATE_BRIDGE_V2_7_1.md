# AGENT PracticePlan to Routine Candidate Bridge V2.7.1

## Purpose

`v2_7_1_agent_practice_plan_to_routine_candidate_bridge` connects a practice-plan block to HarmonyOS Routine candidate data without assuming a specific frontend flow.

The important design correction is:

```text
Agent backend returns candidate data.
HarmonyOS decides presentation and navigation.
```

The backend must not hard-code that the client opens a Routine setup page. A setup page is only one possible presentation mode.

## New Contract

```text
PracticePlanToRoutineCandidateBridgePayload
practice_plan_to_routine_candidate_bridge_contract()
build_practice_plan_to_routine_candidate_bridge_payload(...)
build_practice_plan_to_routine_candidate_bridge_summary(...)
```

Version:

```text
v2_7_1
```

## New Surfaces

Terminal:

```text
/practice-plan-routine-candidate
/practice-plan-routine-candidate {"blockId":"..."}
/practice-plan-routine-candidate {"blockIndex":1}
```

API:

```http
GET  /agent/actions/practice-plan/routine-candidate/spec
POST /agent/actions/practice-plan/routine-candidate/prepare
```

## Input Sources

The bridge can consume:

```text
routine_practice_plan_payload
practicePlanPayload
practice_plan_payload
HarmonyOSAgentActionCard.result_preview.routine_practice_plan_payload
raw practicePlan
single practiceBlock
```

It can select a block using:

```text
block_id / blockId
block_index / blockIndex
```

If no block is specified, it selects the first playable/accompaniment-capable block, then falls back to the first block.

## Output Semantics

The payload exposes:

```text
frontend_flow_assumption = false
client_decides_presentation = true
backend_does_not_require_open_routine_setup = true
backend_does_not_start_playback = true
```

Available client actions are deliberately neutral:

```text
present_routine_candidate
apply_to_current_routine
show_confirmation_sheet
add_to_routine_queue
save_as_template
dismiss
view_trace
```

These are not commands to the backend. They are UI/action semantics for HarmonyOS Routine.

## Allowed Frontend Presentations

HarmonyOS may render the same candidate as:

```text
Routine setup page
Bottom sheet confirmation
Current Routine form fill
Routine queue item
Template library item
Custom future client flow
```

The backend does not care which one is used.

## Guardrails

This version must not:

```text
call /accompaniment/generate
call engine adapters
create MIDI assets
start playback
execute agent_playback_prepare
hard-code a frontend flow
modify Engine music generation rules
modify shared docs or HarmonyOS fixtures
```

All start/generate/playback actions remain future user-confirmed client actions.

## Trace

Trace summary field:

```text
final_response_summary.practice_plan_to_routine_candidate_bridge_summary
```

Trace step names:

```text
terminal_practice_plan_routine_candidate_payload_built
terminal_practice_plan_routine_candidate_summary_recorded
api_practice_plan_routine_candidate_payload_built
```

## Completion Criteria

A valid delivery should satisfy:

```text
Practice-plan block can become Routine candidate data.
Candidate can be selected by block_id or block_index.
Payload states client_decides_presentation=true.
No playback/generation flags are enabled.
Terminal and API surfaces return the same contract family.
Agent targeted regression remains green.
```
