# v2_10_10 Integration — HarmonyOS Agent Today Guidance LLM Payload Trace

Status: completed.

## Purpose

This pass adds a product/debug endpoint that answers one concrete integration question:

```text
When the user taps “今天该练什么？”, what would JamMate send to the LLM?
```

The endpoint is preview-only. It does not call the LLM, does not execute tools, does not start Routine, does not call the accompaniment engine, does not create MIDI, and does not start playback.

## Endpoint

```text
POST /agent/harmonyos/today-practice-guidance/llm-payload-trace
```

Request body is the same HarmonyOS black-box product request used by the normal guidance route:

```json
{
  "userId": "local-dev-user",
  "sessionId": "agent-session-1779200000000",
  "deviceId": "harmonyos-device-local",
  "userMessage": "今天该练什么？"
}
```

Frontend product UI still must not send backend internals:

```text
dbPath
sqliteDbPath
clientConfirmedRecordWrite
internal write gate
migration guard fields
```

## Response focus

The response keeps the standard HarmonyOS envelope:

```json
{
  "ok": true,
  "code": "today_guidance_llm_payload_trace_ready",
  "message": "已生成今日练习建议的 LLM 请求预览；本接口不会调用大模型。",
  "data": {
    "llmPayloadTraceReady": true,
    "userMessage": "今天该练什么？",
    "contextSource": "sqlite_backend",
    "llmRequestPreview": {}
  },
  "debug": {},
  "safety": {}
}
```

Important fields inside `data.llmRequestPreview`:

```text
internalPromptMessages
providerEnvelopeMessages
chatCompletionsMessagesIfCalled
chatCompletionsRequestBodyPreview
assembledPracticeContext
outputSchema
promptPolicy
contextSummary
roleNormalization
safety
```

## Role normalization

Internal preview messages may include:

```text
system
developer
user
context
```

The actual OpenAI-compatible network payload preview uses compatible roles only:

```text
system
user
assistant
```

`developer` and `context` content is merged into the leading `system` message in `chatCompletionsMessagesIfCalled`. This prevents OpenAI-compatible providers that do not support `developer` or custom `context` roles from rejecting the request.

## Safety

The trace route is explicitly preview-only:

```text
llmCalledByThisTraceRoute=false
networkCallExecuted=false
toolExecutionEnabled=false
routineStartEnabled=false
accompanimentGenerateCallEnabled=false
engineAdapterCalled=false
midiAssetCreated=false
playbackStarted=false
rawApiKeyIncluded=false
```

`chatCompletionsRequestBodyPreview` includes `model`, `messages`, `temperature`, and `max_tokens`, but never includes Authorization headers or raw API keys.

## Product meaning

Use this route when debugging or reviewing the Agent prompt payload. Use the normal route for production UI display:

```text
POST /agent/harmonyos/today-practice-guidance/preview
```

The normal route remains lightweight and does not return the full prompt/context payload unless separate debug surfaces are requested.

## Current known limitation

Routine completion records are compacted before entering `assembledPracticeContext.practice_history_context.recent_practice_history`. The compact item currently preserves fields such as title, routine id, duration, completion status, style, tempo, plan id, and block id. Full completion `items` and freeform `notes` are stored in SQLite context records, but they are not yet preserved in the compact LLM history item.

Future Agent work can decide whether `items` and `notes` should be summarized into the LLM context with privacy/length controls.
