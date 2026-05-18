# AGENT_ROUTINE_HISTORY_CONTEXT_INTAKE_V2_7_2

## 版本目标

`v2_7_2_agent_routine_history_context_intake` 定义鸿蒙 Routine 练习历史进入 Agent Context 的 intake 契约。

本版本解决的问题不是“练习结束后让 Agent 推荐下一步”，而是：

```text
HarmonyOS Routine 完成记录
→ 结构化 RoutineHistoryRecord 摘要
→ Agent PracticeHistoryContext
→ 下一次用户主动询问“今天该练什么”时进入 ContextPacket
```

## 核心原则

Routine 结束页由鸿蒙客户端自己负责：

```text
本次练习已完成
练习内容
练习时长
状态：已记录
```

Agent 不在练习结束后自动弹推荐卡片。下一次用户主动发起 LLM 对话时，系统再把原计划、最近几次 Routine 记录、用户偏好等整合进 ContextPacket，供 LLM 判断是按原计划继续，还是灵活调整。

## 新增契约

```text
RoutineHistoryContextIntakePayload
build_routine_history_context_intake_payload(...)
build_routine_history_context_intake_summary(...)
routine_history_context_intake_contract()
```

## 新增 API

```http
GET  /agent/context/routine-history/spec
POST /agent/context/routine-history/intake
```

## 新增 Terminal 命令

```text
/routine-history-context [json_payload]
```

示例：

```bash
/routine-history-context {"routineHistoryRecords":[{"sessionId":"s1","tuneTitle":"Blue Bossa","style":"bossa_nova","tempo":120,"actualSeconds":1180,"completed":true}]}
```

## 输入字段建议

鸿蒙端可以提交一个或多个 Routine 历史摘要：

```json
{
  "routineHistoryRecords": [
    {
      "sessionId": "session_blue_bossa_001",
      "routineId": "routine_blue_bossa_001",
      "title": "Blue Bossa Bossa Comping",
      "tuneTitle": "Blue Bossa",
      "style": "bossa_nova",
      "tempo": 120,
      "plannedDurationMinutes": 20,
      "actualSeconds": 1180,
      "completed": true,
      "practiceGoal": "Bossa comping stability",
      "planId": "plan_week_1",
      "planBlockId": "day1_bossa",
      "finishedAt": "2026-05-18T20:30:00"
    }
  ]
}
```

## 输出内容

输出包含：

```text
routine_history_records
practice_history_context_items
context_packet_section
aggregate_summary
storage_boundary
validation
client_action_semantics
```

其中 `context_packet_section` 可作为未来 `ContextBuilder` 的 `practice_history_context`：

```json
{
  "section_name": "practice_history_context",
  "recent_practice_history": [],
  "aggregate_summary": {},
  "context_usage_policy": {
    "use_when_user_asks_what_to_practice_next": true,
    "do_not_create_post_session_recommendation_card": true,
    "do_not_start_routine": true,
    "do_not_call_accompaniment_generate": true
  }
}
```

## 本地与后端边界

鸿蒙本地负责：

```text
当前 RoutineSession 状态
timer / pause / resume / playback position
local MIDI file path / local playback cache
临时 Routine 设置草稿
Routine 结束页展示状态
```

后端应保存或未来可保存给 Agent 使用的摘要：

```text
PracticePlan
RoutineHistory summary
PracticeHistoryContextItem
UserPracticeProfile
用户保存的 leadsheets / routine templates
Agent trace metadata
```

本版本只定义 intake/context 契约，不实现数据库持久化。

## 明确禁止

本版本不做：

```text
不创建练习结束后的 Agent 推荐卡片
不调用 `POST /accompaniment/generate`，也就是不调用 `/accompaniment/generate`
不调用 engine adapter
不生成 MIDI asset
不启动 playback
不保存当前播放秒级状态
不保存 localMidiPath / midiBase64 / currentPositionMs 到 Agent context
```

## 验收标准

```text
RoutineHistoryRecord 可以归一化为 PracticeHistoryContextItem
client-only playback fields 会被丢弃并记录在 validation.dropped_client_only_fields
ContextBuilder 可以接收 routine_history_context 并写入 learner_context
API route 返回 context-only payload
Terminal 命令可 trace
所有 no-side-effect guard 均为 false/disabled
```
