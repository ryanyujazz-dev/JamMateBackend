# v2_10_21 Agent Practice Coach LLM Response Repair / Schema Hardening

## Goal

`v2_10_21` hardens the unified Practice Coach endpoint against realistic LLM output drift.

The endpoint remains:

```text
POST /agent/harmonyos/practice-coach-session/message/execute
```

This task does **response repair** and schema validation only. It does not start Routine, call Engine, create MIDI, start playback, or write HarmonyOS local state.

## Why

Real LLM providers may return:

- Markdown fenced JSON.
- Preamble/epilogue text around JSON.
- Nested action objects such as `{ "action": { ... } }`.
- Field aliases such as `type`, `content`, `actions`, `plan`, `sheet`.
- Response type aliases such as `plan_proposal`, `bindSheet`, `routine_card`.
- Missing optional fields such as `nextClientActions`.
- Over-aggressive or unsafe payloads.

The backend must repair safe shape drift, validate the final contract, and use deterministic fallback when the action is invalid or unsafe.

## Implemented

- Added `PRACTICE_COACH_LLM_RESPONSE_REPAIR_SCHEMA_HARDENING_VERSION = "v2_10_21"`.
- Added robust parsing for Markdown fences and embedded JSON objects.
- Added nested action unwrapping.
- Added responseType alias repair.
- Added message / nextClientActions / sheetIntent / planProposal alias repair.
- Added plan proposal hardening for top-level `blocks`, `durationMinutes`, and `focus`.
- Added profile sheet intent defaulting and hardening.
- Kept forbidden-key rejection for payloads such as `midiBase64`, `apiKey`, and `hiddenChainOfThought`.
- Kept deterministic fallback when LLM action validation fails.
- Exposed `debug.llmActionDecisionRepairReport`.
- Exposed `debug.llmResponseRepairSchemaHardeningVersion`.

## Contract boundary

The LLM may choose an action intent, but it does not control UI directly.

The backend still owns:

- JSON extraction and repair.
- Schema validation.
- Safety filtering.
- Session state persistence.
- Routine card rebuilding from backend draft plan.
- Deterministic fallback.

HarmonyOS still owns:

- Native rendering.
- bindSheet UI.
- User confirmation.
- Starting a routine only after explicit user tap.

## Safety

The endpoint remains safe:

```text
startsRoutine=false
callsEngineAdapter=false
createsMidiAsset=false
startsPlayback=false
writesHarmonyOSLocalState=false
```

`routine_card_ready` is accepted only when a backend draft plan exists and the user confirmation context is valid. Even then, the backend rebuilds the routine card from stored draft plan data instead of trusting an LLM-supplied card.

## Tests

Added:

```text
tests/test_v2_10_21_agent_practice_coach_live_llm_response_repair_schema_hardening.py
```

Coverage:

- Markdown-prefaced fenced JSON is parsed.
- Nested action objects are unwrapped.
- `plan_proposal` alias is repaired to `practice_plan_proposal`.
- Plan proposal top-level fields are projected into `planProposal`.
- `bindSheet` alias is repaired to `request_profile_sheet`.
- Missing sheet intent is defaulted by backend.
- Forbidden LLM payload keys trigger deterministic fallback.
- Docs record the response repair/schema hardening policy.

## Next recommended step

`v2_10_22_agent_practice_coach_llm_action_e2e_device_feedback_fit`

Use real device/provider feedback to tune the repair map, action schema, and frontend rendering assumptions without changing Engine generation logic.
