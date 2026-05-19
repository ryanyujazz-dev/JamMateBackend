# AGENT_HARMONYOS_AGENT_ACTION_CONTRACT_V2_6_6

## Purpose

`v2_6_6_harmonyos_agent_action_contract` exposes a Routine-facing Agent action-card contract for HarmonyOS.

The goal is to let the Routine UI display one stable card that contains:

```text
LLM reply / candidate action context
→ tool invocation preview
→ confirmation state
→ executor dry-run state
→ workflow descriptor state
→ optional controlled practice-plan execution result
→ trace_id
```

This version is a contract/presentation layer. It does not introduce new playback execution.

---

## New contract

```text
GET  /agent/actions/spec
POST /agent/actions/preview
POST /agent/actions/execute-controlled
```

The primary client object is the Routine-facing AgentActionCard:

```text
HarmonyOSAgentActionCard
```

Important fields:

```text
action_contract_version
action_id
proposal_id
tool_name
title
description
arguments_preview
side_effect_level
risk_summary
requires_user_confirmation
confirmation_status
preview_status
execution_status
workflow_name
result_preview
trace_id
available_client_actions
route_called
engine_adapter_called
midi_asset_created
```

---

## Allowed controlled execution

This milestone continues the `v2_6_5` safety boundary.

Only this low-risk controlled workflow is allowed:

```text
agent_practice_plan
→ PracticePlanner.build_plan
```

This action can return a structured practice plan for Routine display.

---

## Explicit non-goals

This version does not call /accompaniment/generate.

This version does not execute:

```text
agent_playback_prepare
```

This version does not:

```text
call engine adapters
create MIDI assets
change playback state
modify pattern / voicing / expression / pedal
change HarmonyOS playback main route
```

---

## Routine UI usage

HarmonyOS Routine should treat the action card as the UI state source for Agent suggestions:

```text
confirmation_status=pending
→ show Confirm / Reject

execution_status=controlled_execution_succeeded
→ show result_preview and trace_id

side_effect_level=creates_midi_asset
→ never auto-execute; require stronger guarded flow in a later milestone
```

---

## Guard summary

```text
Action card enabled: yes
Practice plan controlled execution: yes
Playback execution: no
/accompaniment/generate from Agent action: no
Engine adapter dispatch: no
MIDI asset creation: no
Autonomous execution: no
```
