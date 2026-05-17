# JamMate Agent Context Engineering v0.1

## 原则

JamMate Agent 的上下文不是普通聊天上下文，而是音乐任务决策上下文。

```text
HarmonyOS 只发送当前用户输入 + 客户端状态 + object ids。
Python Agent 根据任务类型组装 ContextPacket。
LLM 只接收当前任务需要的信息。
```

P0 当前没有接真实 LLM，但已保留：

```text
ContextBuilder
ContextPacket
TraceLogger
Guardrails
IntentClassifier
```

## Context Profiles

后续按任务类型扩展：

```text
PRACTICE_PLAN_GENERATION
IMMEDIATE_PRACTICE_PLAYBACK
SESSION_REVIEW
NEXT_RECOMMENDATION
COACH_QA
FUTURE_SOLO_GENERATION
FUTURE_RECORDING_ANALYSIS
```

## 与 Engine 的边界

Agent context 只描述练习/任务意图，不进入 engine 内部 voicing/pattern 细节。Engine 只接收结构化 generation request。
