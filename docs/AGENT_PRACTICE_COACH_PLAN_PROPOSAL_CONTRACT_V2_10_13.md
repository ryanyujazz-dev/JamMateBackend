# v2_10_13 — Practice Coach Session Plan Proposal Contract

## 目标

`v2_10_13_agent_practice_coach_plan_proposal_contract` 在 v2_10_12 的 Practice Coach Session conversation state 基础上，补齐从“信息已收集”到“练习计划草案”的产品契约。

这一步仍然不是完整 LLM 执行，也不是 Routine 启动。它只负责：

```text
读取同一个 userId/sessionId 的 Practice Coach Session 状态
合并当前 userMessage 中可抽取的 available_minutes / practice_focus
如果信息不足，返回 ask_clarifying_question
如果信息齐备，返回结构化 practice_plan_proposal
把 draft_plan 写回后端 SQLite session state
等待用户确认或调整
```

## 新增接口

```text
POST /agent/harmonyos/practice-coach-session/plan-proposal/execute
```

请求仍然是 HarmonyOS 黑盒产品请求体：

```json
{
  "userId": "local-dev-user",
  "sessionId": "practice-coach-session-001",
  "deviceId": "harmonyos-device-local",
  "userMessage": "生成练习计划草案"
}
```

前端仍然不传：

```text
dbPath / sqliteDbPath
internal write gate
providerResult
LLM raw prompt
```

后端 wrapper 自己补本地 dev SQLite path。

## 输出：信息不足

当缺少 `available_minutes` 或 `practice_focus` 时：

```json
{
  "responseType": "ask_clarifying_question",
  "missingFields": ["available_minutes", "practice_focus"],
  "requiresUserConfirmation": false,
  "planProposal": null,
  "nextClientActions": ["show_chat_message", "show_suggested_replies"]
}
```

## 输出：信息齐备

当上下文已有或当前 turn 抽取到 `available_minutes` 与 `practice_focus` 时：

```json
{
  "responseType": "practice_plan_proposal",
  "message": "我建议先按这个 20 分钟方案练...",
  "requiresUserConfirmation": true,
  "planProposal": {
    "title": "今日 Bossa 练习安排",
    "totalDurationMinutes": 20,
    "practiceFocus": "bossa",
    "blocks": [
      {"title": "Bossa 核心节奏热身", "durationMinutes": 5},
      {"title": "Bossa 曲式循环练习", "durationMinutes": 11},
      {"title": "回听与记录", "durationMinutes": 4}
    ],
    "confirmationStatus": "awaiting_user_confirmation",
    "requiresUserConfirmation": true,
    "routineCardCreated": false,
    "routineStartEnabled": false
  },
  "nextClientActions": ["show_practice_plan_proposal", "ask_user_to_confirm_or_adjust"]
}
```

## 安全边界

本接口：

```text
不会调用大模型
不会发 provider 网络请求
不启动 Routine
不生成 Routine card
不调用 Engine
不生成 MIDI
不播放
不写 HarmonyOS 本地状态
只会写后端 SQLite Practice Coach Session 状态
```

## 前端理解方式

前端不需要知道后端 SQLite 表结构。只需要：

```text
responseType=ask_clarifying_question：展示追问与 suggestedReplies
responseType=practice_plan_proposal：展示练习计划草案卡片，提供确认/调整入口
requiresUserConfirmation=true：确认之前不能开始 Routine
routineCardPayload=null：此阶段还没有正式 Routine 卡片
```

## 下一步

推荐下一步：

```text
v2_10_14_agent_practice_coach_plan_confirmation_to_routine_card_contract
```

目标：用户说“确认”后，把已保存的 `draft_plan` 转成 HarmonyOS `routineCardPayload`，但仍由前端决定何时展示与何时开始。
