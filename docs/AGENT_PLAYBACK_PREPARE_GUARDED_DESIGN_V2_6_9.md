# Agent Playback Prepare Guarded Design — v2_6_9

## Purpose

`v2_6_9_agent_playback_prepare_guarded_design` defines the guarded Routine-facing contract for `agent_playback_prepare`.

This version is intentionally **not** playback execution. It only turns a confirmed, dry-run, descriptor-resolved `agent_playback_prepare` candidate into a HarmonyOS Routine setup payload.

## Chain

```text
Tool Invocation Preview
→ Tool Execution Confirmation
→ ToolExecutor Dry-run / No-op
→ Deterministic Workflow Descriptor Resolution
→ HarmonyOSAgentActionCard
→ playback_prepare_guarded_payload
```

## New surfaces

```text
Terminal:
/playback-prepare-guarded

API:
GET  /agent/actions/playback-prepare/spec
POST /agent/actions/playback-prepare/guarded-preview
```

## Payload

`HarmonyOSAgentActionCard.result_preview.playback_prepare_guarded_payload` contains:

```text
playback_request_candidate
routine_config_candidate
risk_gate
confirmation_ladder
next_client_actions
client_button_semantics
```

The payload is designed for HarmonyOS Routine to render a parameter review/setup screen. It does not start a playable Routine.

## Current enabled behavior

```text
preview enabled: true
user confirmation record enabled: true
executor dry-run enabled: true
workflow descriptor resolution enabled: true
guarded Routine setup candidate enabled: true
```

## Current disabled behavior

```text
agent_playback_prepare real execution: false
/accompaniment/generate call: false
engine adapter dispatch: false
MIDI asset creation: false
playback start: false
autonomous LLM execution: false
```

## HarmonyOS Routine semantics

The primary client action is:

```text
open_routine_setup
```

This may show the user a Routine setup page populated from the candidate fields. It must not call `/accompaniment/generate` by itself.

The future high-risk action is:

```text
routine_start_after_confirmation
```

This action is listed as disabled in v2_6_9 and requires a later dedicated milestone.

## Guard rule

`agent_playback_prepare` is asset-generating in the future, so it must always remain behind visible user confirmation and parameter review. LLM output alone is never sufficient to generate accompaniment or start playback.
