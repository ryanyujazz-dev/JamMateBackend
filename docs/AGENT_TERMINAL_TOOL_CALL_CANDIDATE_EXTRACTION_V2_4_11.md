# v2_4_11 — Agent Terminal Tool Call Candidate Extraction

`v2_4_11_agent_terminal_tool_call_candidate_extraction` stays inside `feature/agent-workflow` and does not deepen accompaniment generation.

## Goal

Let backend developers use terminal chat with an LLM provider and see whether the assistant reply contains explicit JSON tool-call candidates. Extracted candidates are sent through the existing validation-only preview contract, so the terminal can show whether a future tool call would be known and allowed by the current ContextPacket.

## Owner Placement

No new parser subsystem was created.

```text
src/jammate_agent/core/tool_invocation.py
  -> ToolCallCandidate
  -> ToolCallCandidateExtractionResult
  -> extract_tool_call_candidates(text)

src/jammate_agent/cli/terminal_chat.py
  -> TerminalChatSession.respond(...)
  -> extract candidates from provider content
  -> preview each candidate with preview_tool_invocation(...)
```

`tool_registry.py` remains the descriptor owner. `tool_invocation.py` owns tool proposal, preview validation, and now candidate extraction because the extracted object is still only a tool invocation proposal.

## Supported Candidate Shapes

Extraction is intentionally explicit and JSON-only. Plain natural language is ignored.

```json
{ "tool_name": "agent_playback_prepare", "arguments": { "durationMinutes": 20 } }
```

```json
{ "toolName": "agent_playback_prepare", "args": { "durationMinutes": 20 } }
```

```json
{ "tool_call": { "name": "agent_playback_prepare", "arguments": { "durationMinutes": 20 } } }
```

```json
{ "tool_calls": [ { "name": "chart_resolve", "arguments": { "tune": "Blue Bossa" } } ] }
```

JSON may be the entire assistant message or appear inside fenced code blocks such as ` ```json ... ``` `.

## Safety Boundary

- Candidate extraction does not execute tools.
- Candidate preview does not dispatch deterministic workflows.
- Candidate preview does not call API routes.
- Candidate preview does not call adapters or `jammate_engine`.
- Unknown tools are rejected.
- Known tools outside the current ContextPacket allow-list are rejected.
- Allowed tools are still blocked by `tool_execution_disabled_in_v2_4_11`.

## Terminal Behavior

Normal terminal chat output remains unchanged, with an added preview summary when candidates are found:

```text
JamMate> ...assistant response...
ToolCandidateExtraction> 1 candidate(s); execution disabled
  - agent_playback_prepare: preview_only_blocked_by_execution_guard would_execute=False
```

The explicit `/tool-preview` command remains unchanged and still works without calling the provider.

## Runtime Music Impact

None. This delivery does not modify voicing, pattern, expression, pedal, MIDI generation, leadsheet parsing, or accompaniment output behavior.
