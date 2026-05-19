# AGENT_RUNTIME_SKELETON_CLEANUP_V2_6_7

## Purpose

`v2_6_7_agent_runtime_skeleton_cleanup` is a cleanup and inspection milestone for the Agent runtime skeleton.

It adds a **read-only runtime skeleton status** contract so terminal, API, trace, and HarmonyOS Routine developers can inspect the whole Agent action lifecycle before concrete Agent feature development starts.

This milestone does not add a new high-risk tool. It does not call /accompaniment/generate, does not call engine adapters, does not create MIDI assets, and does not change Engine music-generation rules.

---

## Consolidated lifecycle

The runtime skeleton now exposes this stage map:

```text
ContextPacket
→ LLM Provider Boundary
→ Tool Registry
→ Tool Invocation Preview
→ Tool Execution Confirmation
→ ToolExecutor Dry-run / No-op
→ Deterministic Workflow Descriptor Resolution
→ Controlled PracticePlan Execution
→ HarmonyOS Routine AgentActionCard
```

Only one controlled tool remains enabled:

```text
agent_practice_plan
```

The following remain forbidden until a future explicitly scoped milestone:

```text
agent_playback_prepare real execution
direct Agent-triggered /accompaniment/generate
engine adapter dispatch from the Agent action card
MIDI asset creation from Agent action card
autonomous LLM tool execution
```

---

## New contract surfaces

Core:

```text
agent_runtime_no_side_effect_flags()
build_agent_runtime_skeleton_snapshot()
agent_runtime_skeleton_contract()
```

Terminal:

```text
/runtime-skeleton
```

API:

```http
GET /agent/runtime/skeleton
```

Trace spec:

```text
agent_runtime_skeleton_cleanup_trace_contract
```

---

## Cleanup decisions

This milestone intentionally keeps the Agent tool lifecycle in the existing owner:

```text
src/jammate_agent/core/tool_invocation.py
```

Reason:

```text
Preview, confirmation, executor dry-run, workflow descriptor resolution, controlled execution, and action-card composition are one readable lifecycle.
Splitting a new module at this point would add indirection without improving ownership.
```

Terminal state remains owned by:

```text
src/jammate_agent/cli/terminal_chat.py
```

Agent API route surfaces remain owned by:

```text
src/jammate_api/routes/agent_routes.py
```

No shared docs are changed in this Agent milestone.

---

## Non-goals

This milestone is not:

```text
a new ToolExecutor implementation
a playback workflow milestone
an accompaniment generation milestone
a HarmonyOS fixture update
an Engine music rule update
a pattern / voicing / expression / pedal update
```

---

## Completion standard

`v2_6_7` is complete when:

```text
GET /agent/runtime/skeleton returns the consolidated skeleton map
/runtime-skeleton prints the same lifecycle status in terminal chat
trace spec exposes agent_runtime_skeleton_cleanup_trace_contract
all no-side-effect guard flags remain false for playback/generation/engine/MIDI
Agent targeted regression remains green
```
