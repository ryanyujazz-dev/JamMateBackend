# v2_10_27 — Practice Coach HarmonyOS UI Integration Feedback Fit

## Scope

This version is an Agent / Integration-only update. It does not modify Engine generation, MIDI generation, style logic, voicing logic, playback, or accompaniment generation.

The goal is to help the HarmonyOS frontend wire the real Practice Coach multi-turn UI without re-inferring backend state transitions from many scattered response fields.

## Main addition

The unified Practice Coach product endpoint remains:

```text
POST /agent/harmonyos/practice-coach-session/message/execute
```

The endpoint now includes a compact frontend rendering hint:

```text
data.frontendUiAction
debug.frontendUiAction
```

This is not a replacement for canonical fields. The canonical fields remain:

```text
data.responseType
data.content
data.sheetIntent
data.planProposal
data.routineCardPayload
data.deviceFeedbackTracePack
```

`frontendUiAction` is a stable HarmonyOS integration helper so the frontend can quickly decide whether to append a chat bubble, open a profile sheet, show or replace a plan proposal card, or show a routine card.

## Practice Coach frontendUiAction shape

```json
{
  "version": "v2_10_27",
  "responseType": "practice_plan_revision",
  "status": "plan_proposal",
  "renderMode": "replace_plan_proposal_card",
  "visibleContent": "...",
  "shouldAppendAssistantMessage": false,
  "shouldOpenProfileSheet": false,
  "shouldRenderPlanProposalCard": true,
  "shouldReplaceCurrentProposal": true,
  "shouldRenderRoutineCard": false,
  "canStartRoutineByUserTap": false,
  "safeToAutostartRoutine": false,
  "backendStartsRoutine": false,
  "requiresUserTapToStart": false,
  "conversationStatePersisted": true
}
```

## Rendering rules

| responseType | status | renderMode | frontend rule |
|---|---|---|---|
| `ask_clarifying_question` | `clarifying` | `append_assistant_message` | Show assistant text and optional quick replies. |
| `request_profile_sheet` | `profile_sheet` | `open_or_show_profile_sheet_prompt` | Frontend owns native bindSheet rendering. |
| `practice_plan_proposal` | `plan_proposal` | `show_plan_proposal_card` | Show the first proposal card. |
| `practice_plan_revision` | `plan_proposal` | `replace_plan_proposal_card` | Replace the current proposal card instead of stacking a new one. |
| `routine_card_ready` | `routine_card` | `show_routine_card` | Show routine card and start button. User must tap start. |
| `chat_message` | `chat_message` | `append_assistant_message` | Show ordinary assistant text. |
| `cannot_proceed` | `cannot_proceed` | `show_blocking_message` | Show failure/blocked state. |

## Routine completion frontendUiAction

The existing completion endpoint remains:

```text
POST /agent/harmonyos/routine-completion-record/execute
```

It now also returns:

```text
data.frontendUiAction
debug.frontendUiAction
```

When persistence succeeds, the action is:

```json
{
  "version": "v2_10_27",
  "responseType": "routine_completion_recorded",
  "status": "completion_recorded",
  "renderMode": "show_routine_summary_recorded",
  "shouldShowRecordedSummary": true,
  "shouldOpenPracticeCoach": false,
  "shouldShowPostSessionRecommendationCard": false,
  "safeToAutostartRoutine": false,
  "backendStartsRoutine": false
}
```

This preserves the product rule: RoutineSummaryPage should show that the practice was recorded. It must not auto-open Practice Coach or show a forced post-session recommendation card. The next guidance happens only when the user asks again.

## New smoke fixture and script

Added:

```text
frontend_fixtures/harmonyos/smoke/product_practice_coach_harmonyos_ui_integration_sequence.json
frontend_fixtures/harmonyos/smoke/curl_practice_coach_harmonyos_ui_integration_smoke.sh
tests/test_v2_10_27_agent_practice_coach_harmonyos_ui_integration_feedback_fit.py
```

The smoke covers:

```text
practice_plan_proposal -> show_plan_proposal_card
practice_plan_revision -> replace_plan_proposal_card
routine_card_ready -> show_routine_card
routine-completion-record/execute -> show_routine_summary_recorded
next Practice Coach request -> recent_practice_memory_summary readback
```

## Safety invariants

The update continues to assert:

```text
startsRoutine=false
callsEngineAdapter=false
createsMidiAsset=false
startsPlayback=false
writesHarmonyOSLocalState=false
safeToAutostartRoutine=false
```

`routine_card_ready` only means HarmonyOS may display a card and a start button. The backend does not start the routine.

## Frontend guidance

For the HarmonyOS branch, the recommended integration target is:

```text
1. Call /agent/harmonyos/practice-coach-session/message/execute for Practice Coach chat turns.
2. Render by data.responseType or data.frontendUiAction.renderMode.
3. For practice_plan_revision, replace the current proposal card.
4. For routine_card_ready, display the card and wait for user tap.
5. After the user finishes practice, call /agent/harmonyos/routine-completion-record/execute.
6. On completion success, show "已记录" only; do not auto-open Practice Coach.
7. The next Practice Coach guidance should read completion history when the user asks again.
```
