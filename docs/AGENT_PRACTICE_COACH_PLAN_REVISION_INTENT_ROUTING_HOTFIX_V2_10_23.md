# Agent Practice Coach Plan Revision Intent Routing Hotfix — v2_10_23

## 目标

修复 Practice Coach Session 在已有 `draft_plan` 且 `awaiting_confirmation=true` 时，把用户明确调整请求误路由到 `existing_draft_plan_waiting_for_confirmation` 的问题。

前端已能把调整文本继续发送到统一入口：

```text
POST /agent/harmonyos/practice-coach-session/message/execute
```

后端现在必须在待确认草案状态下先判断用户意图：

```text
确认 / 就这个 / 开始
  -> routine_card_ready

调整 / 改成 / 换成 / 多安排 / 少一点 / 延长 / 缩短
  -> practice_plan_revision

换曲子 / 曲目 / standard
  -> practice_plan_revision
```

`existing_draft_plan_waiting_for_confirmation` 只作为兜底提示，不再拦截明确调整请求。

## 覆盖表达

本次 hotfix 覆盖以下中文表达：

```text
我想调整为20分钟
改成20分钟
多安排基本功
加强节拍器稳定性
换成曲目练习
换一首 standard
```

这些表达会命中：

```text
routerDecisionReason = existing_draft_plan_revision_requested
selectedActionExecutor = plan_proposal
responseType = practice_plan_revision
```

## 行为边界

`practice_plan_revision` 会更新后端保存的 `draft_plan`，并保持：

```text
awaiting_confirmation = true
routineCardPayload = null
routineStartEnabled = false
```

用户明确确认后，才会进入：

```text
responseType = routine_card_ready
routerDecisionReason = existing_draft_plan_explicit_confirmation
```

安全边界保持：

```text
不启动 Routine
不调用 Engine
不生成 MIDI
不播放
不写 HarmonyOS 本地状态
```

Routine card 仍然只是前端可展示卡片，用户必须在鸿蒙前端主动点击开始练习。

## 前端影响

前端无需新开 session，也不要拼接旧草案摘要绕行。继续把用户调整文本发到同一个 Practice Coach session 即可。

前端需要处理：

```text
practice_plan_revision -> 继续使用 plan_proposal 卡片 UI 展示新草案
```

