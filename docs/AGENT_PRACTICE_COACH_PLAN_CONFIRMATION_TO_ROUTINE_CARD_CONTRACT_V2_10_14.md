# v2_10_14 — Practice Coach Plan Confirmation to Routine Card Contract

`v2_10_14_agent_practice_coach_plan_confirmation_to_routine_card_contract` 在 v2_10_13 的 `practice_plan_proposal` 基础上，补齐“用户确认计划草案 → 生成 HarmonyOS 前端可展示练习安排卡片”的产品契约。

## Endpoint

```text
POST /agent/harmonyos/practice-coach-session/routine-card/execute
```

## Product Flow

```text
Practice Coach Session 已保存 draft_plan
→ 用户明确说“确认这个安排”
→ 后端把 draft_plan 投影成 routineCardPayload
→ 前端展示 Routine card
→ 用户在前端点击开始
```

## Request Shape

HarmonyOS 仍只传黑盒产品字段：

```json
{
  "userId": "local-dev-user",
  "sessionId": "practice-coach-session-xxx",
  "deviceId": "harmonyos-device-local",
  "userMessage": "确认这个安排"
}
```

前端不要传：

```text
dbPath
sqliteDbPath
clientConfirmedRecordWrite
internal write gate
Python/SQLite 内部字段
```

## Response Highlights

成功确认后：

```text
data.agentActionPreview.responseType = routine_card_ready
data.routineCardReady = true
data.routineCardPayload = {...}
data.routineStartEnabled = true
data.requiresUserTapToStart = true
data.backendStartsRoutine = false
```

`routineCardPayload` 是前端展示契约，不代表后端自动启动 Routine。

## Safety Boundary

本接口可以写后端 SQLite 的 Practice Coach Session state，但必须保持：

```text
不会调用大模型
不会发 provider 网络请求
不启动 Routine
不调用 Engine
不生成 MIDI
不播放
不写 HarmonyOS 本地状态
```

## Frontend Responsibility

HarmonyOS 负责：

```text
渲染 routineCardPayload
让用户点击开始
管理本地练习计时
在练习结束后调用 routine-completion-record/execute
```

后端只负责把已确认的 `draft_plan` 转成结构化 `routineCardPayload`。

## Non-confirmation Behavior

如果没有 `draft_plan`：返回 `ask_clarifying_question`，提示先生成练习计划草案。

如果有 `draft_plan` 但用户没有明确确认：继续返回 `practice_plan_proposal`，让前端展示确认/调整入口，不生成 card。

## Next Recommended Task

```text
v2_10_15_agent_practice_coach_profile_sheet_intent_contract
```

目标：当 Practice Coach Session 缺少长期画像字段时，输出 `request_profile_sheet` / `sheetIntent`，让 HarmonyOS 用原生 bindSheet 补齐基础信息，而不是在聊天里反复追问。
