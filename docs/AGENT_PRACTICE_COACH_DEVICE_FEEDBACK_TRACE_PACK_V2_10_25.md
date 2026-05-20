# v2_10_25 — Practice Coach device feedback trace pack

## Goal

`v2_10_25` adds a compact, frontend-copyable `deviceFeedbackTracePack` to the unified HarmonyOS Practice Coach endpoint:

```text
POST /agent/harmonyos/practice-coach-session/message/execute
```

This is not a new product behavior. It is a debugging/联调 aid for device feedback reports. The frontend can copy this single object when a response renders incorrectly, when a session state transition looks wrong, or when a plan revision does not match user intent.

## Response location

The same trace pack is returned in both places:

```text
data.deviceFeedbackTracePack
debug.deviceFeedbackTracePack
```

The canonical version marker is:

```text
debug.deviceFeedbackTracePackVersion = v2_10_25
```

## What the pack contains

```text
requestSummary
  userId / sessionId / deviceId
  clientLocalDate / clientTimezone / locale
  userMessagePreview + userMessageDigest
  hasProfileFormResult
  productRequestMustNotContainInternalFields

responseSummary
  ok / code / responseType
  nextClientActions
  conversationStatePersisted
  profileSheetIntentReady
  planProposalReady
  routineCardReady
  routineStartEnabled
  requiresUserTapToStart

decisionTrace
  decisionMode
  selectedActionExecutor
  routerDecisionReason
  llmCalled / networkCallExecuted
  llmActionDecisionSource
  deterministicFallbackUsed / deterministicFallbackReason
  llmActionDecisionValidationOk / reason
  repairAnyApplied / repairWarnings

stateTrace
  stateFoundBeforeTurn
  stateDigestBefore / stateDigestAfter
  turnCountBefore / turnCountAfter
  awaitingConfirmationBefore / After
  pendingMissingFieldsAfter
  collectedFieldKeysAfter
  draftPlanDigestBefore / After
  draftPlanSummaryAfter

artifactTrace
  sheetType
  planProposalId / totalDurationMinutes / practiceFocus
  routineCardId / routineId

ioTrace
  sqlite read/write blocked reasons
  sqliteConnectionCreated
  sqliteTablesCreated
  sqliteRowsWritten
  sqliteRowCountWritten
  transactionCommitted
  readError / writeError

safetyTrace
  startsRoutine=false
  callsEngineAdapter=false
  createsMidiAsset=false
  startsPlayback=false
  writesHarmonyOSLocalState=false
  backendValidatesLlmActionContract=true
  clientMustStartRoutineExplicitly when routine_card_ready
```

## Frontend reporting rule

When a real device issue happens, frontend should return:

```text
1. request URL and baseUrl
2. request JSON
3. HTTP status
4. response JSON
5. mapped UI state
6. debug.deviceFeedbackTracePack
7. screenshot/logs if available
```

Frontend must not include internal fields in product requests:

```text
dbPath
sqliteDbPath
clientConfirmedRecordWrite
providerResult
llmActionDecisionResult
apiKey
```

## Smoke

Fixture:

```text
frontend_fixtures/harmonyos/smoke/product_practice_coach_device_feedback_trace_request.json
```

Script:

```bash
cd frontend_fixtures/harmonyos/smoke
bash curl_practice_coach_device_feedback_trace_smoke.sh http://127.0.0.1:8000
```

The smoke validates that `deviceFeedbackTracePack` exists and preserves the Practice Coach safety boundary.

## Boundary

Unchanged:

```text
不启动 Routine
不调用 Engine
不生成 MIDI
不播放
不写 HarmonyOS 本地状态
```
