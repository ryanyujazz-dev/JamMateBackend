# v2_10_17 — Practice Coach LLM Action Decision Contract

## Summary

`v2_10_17` upgrades the unified Practice Coach route from a deterministic router to an LLM-action-decision-first contract.

The HarmonyOS-facing entry remains:

```text
POST /agent/harmonyos/practice-coach-session/message/execute
```

The intended product flow is now:

```text
HarmonyOS user message
→ backend builds cache-friendly Practice Coach context
→ LLM chooses a structured action intent
→ backend validates the action contract and safety rules
→ backend persists Practice Coach session state
→ HarmonyOS renders by responseType / nextClientActions
```

The deterministic v2_10_16 router remains available as fallback only.

## Why this matters

The previous v2_10_16 router could prove the product skeleton, but it still hard-coded decisions such as when to ask a question, when to request a profile sheet, and when to generate a plan proposal. That is not the desired final Agent behavior.

The correct Practice Coach product behavior is that the LLM decides whether the next turn should be:

```text
chat_message
ask_clarifying_question
request_profile_sheet
practice_plan_proposal
practice_plan_revision
routine_card_ready
cannot_proceed
```

The frontend should not guess this logic, and the backend should not overfit a deterministic rule tree as the primary decision engine.

## Backend responsibilities

Even when the LLM chooses the action, the backend still owns:

```text
schema validation
responseType allow-list enforcement
forbidden payload rejection
Practice Coach session state persistence
routine card safety rebuild from backend draft_plan
fallback when provider is disabled or invalid
no autonomous Routine start
no Engine / MIDI / playback side effects
```

The LLM does not directly render UI. It only emits structured action intent. HarmonyOS renders native UI such as chat bubbles, proposal cards, routine cards, or bindSheet.

## Provider behavior

`v2_10_17` supports three decision modes:

```text
llm_action_decision
  A valid LLM/provider or injected provider-like result selected the action.

deterministic_fallback
  Provider is unavailable, disabled, invalid, or returned unsafe/invalid JSON.

live_provider
  Possible only when existing explicit LLM env guards are configured.
```

For tests and development, `llmActionDecisionResult` / `providerResult` can inject a provider-like JSON result without a network call.

## Safety notes

The backend rejects forbidden LLM action payload keys including:

```text
midiBase64
localMidiPath
apiKey
rawToolExecutionResult
hiddenChainOfThought
```

If the LLM returns `routine_card_ready`, the backend does not trust an LLM-supplied routine card. It rebuilds the `routineCardPayload` from the persisted backend `draft_plan` after confirmation context is present.

## Current endpoint result fields

The unified route now includes debug fields such as:

```text
decisionMode
llmActionDecisionSource
llmActionDecisionValidation
llmActionRequestPreview
deterministicFallbackUsed
deterministicFallbackReason
```

HarmonyOS product UI should still mainly render from:

```text
responseType
content
nextClientActions
sheetIntent
planProposal
routineCardPayload
```

## Tests

Added:

```text
tests/test_v2_10_17_agent_practice_coach_llm_action_decision_contract.py
```

Coverage includes:

```text
LLM-selected request_profile_sheet persists state and creates sheetIntent
LLM-selected practice_plan_proposal persists draft_plan
LLM-selected routine_card_ready rebuilds card from backend draft_plan
forbidden LLM payload falls back to deterministic router
LLM action request preview exposes messages and output contract
```

## Next recommended task

`v2_10_18_agent_practice_coach_frontend_llm_action_fixture_and_smoke`

Goal: provide HarmonyOS frontend fixtures and curl smoke for the LLM-driven unified endpoint, including examples for `ask_clarifying_question`, `request_profile_sheet`, `practice_plan_proposal`, and `routine_card_ready`.
