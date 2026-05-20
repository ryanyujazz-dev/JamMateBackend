# v2_10_15 — Practice Coach Profile Sheet Intent Contract

`v2_10_15_agent_practice_coach_profile_sheet_intent_contract` 在 Practice Coach Session 链路中补齐基础信息补全能力：当用户资料缺失较多时，后端可以返回 `request_profile_sheet` / `sheetIntent`，由鸿蒙前端用原生 bindSheet 或 bottom sheet 渲染；用户提交后，后端把 `profileFormResult` 写入 Practice Coach session state。

## Endpoint

```text
POST /agent/harmonyos/practice-coach-session/profile-sheet/execute
```

## 产品边界

- LLM 不直接渲染 UI，只输出结构化 action intent。
- 鸿蒙前端负责原生 bindSheet 展示、字段交互和提交。
- 后端只保存提交后的基础练习信息，并把它投影进后续 `llmRequestPreview.user_profile_summary`。
- 该接口不会调用大模型。
- 该接口不调用大模型。
- 该接口不启动 Routine。
- 该接口不调用 Engine。
- 该接口不生成 MIDI、不播放、不写 HarmonyOS 本地状态。

## 请求体

前端产品请求体仍是黑盒字段：

```json
{
  "userId": "local-dev-user",
  "sessionId": "practice-coach-session-xxx",
  "deviceId": "harmonyos-device-local",
  "userMessage": "今天该练什么？"
}
```

提交表单时额外带：

```json
{
  "userId": "local-dev-user",
  "sessionId": "practice-coach-session-xxx",
  "deviceId": "harmonyos-device-local",
  "userMessage": "提交基础信息",
  "profileFormResult": {
    "primaryInstrument": "piano",
    "skillLevel": "intermediate",
    "dailyAvailableMinutes": 30,
    "mainGoal": "提升伴奏稳定性",
    "preferredStyles": ["bossa", "swing"]
  }
}
```

前端不要传 `dbPath`、`sqliteDbPath`、内部 write gate 或 Python/SQLite 内部字段。

## `request_profile_sheet` 响应

```json
{
  "responseType": "request_profile_sheet",
  "message": "为了后续更准确地安排练习，我需要先了解你的基础练习信息。",
  "missingFields": [
    "practice_profile.primary_instrument",
    "practice_profile.skill_level",
    "practice_profile.daily_available_minutes",
    "practice_profile.main_goal",
    "practice_profile.preferred_styles"
  ],
  "sheetIntent": {
    "sheetType": "practice_profile_setup",
    "presentation": "harmonyos_bind_sheet",
    "requiredFields": [],
    "submitAction": {
      "method": "POST",
      "endpoint": "/agent/harmonyos/practice-coach-session/profile-sheet/execute",
      "payloadField": "profileFormResult"
    }
  },
  "nextClientActions": ["open_profile_sheet", "submit_profile_form_result"]
}
```

## 已提交资料后的响应

```json
{
  "responseType": "chat_message",
  "message": "好的，我已记录你的基础练习信息。接下来可以继续帮你安排今天练什么。",
  "sheetIntent": null,
  "nextClientActions": ["continue_practice_coach_conversation"]
}
```

## Context projection

提交后的资料会进入两个地方：

```text
stateAfter.collected_fields.practice_profile
llmRequestPreview.contextBlocks[name=user_profile_summary].payload
```

这样下一轮 Practice Coach LLM context 能使用基础画像，同时保持缓存友好的上下文分层。

## 下一步建议

```text
v2_10_16_agent_practice_coach_unified_message_action_router
```

目标：把 `message-state`、`profile-sheet`、`plan-proposal`、`routine-card` 这些分步 endpoint 之上的用户旅程整理成一个统一 Practice Coach message/action router，前端可以少理解后端内部步骤，只根据 `responseType` / `nextClientActions` 渲染下一步。
