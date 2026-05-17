# v2_3_11 — JamMate Agent Context and Contract Hardening

## 目标

本版本不改变 `jammate_engine` 的音乐生成主链路，而是把 v2_3_10 建立的 Agent / Engine / API 边界继续收口成更适合 HarmonyOS 联调的契约层。

核心原则保持不变：

```text
LLM / Agent 是增强入口，不是必经入口。
JamMate Engine 可被客户端直接调用。
JamMate Agent 是同级智能编排层，通过 provider/adapter 使用 Engine。
HarmonyOS 本地练习模块应能无 LLM 跑通基础 practice workspace。
```

---

## 1. 本版本新增内容

### 1.1 Agent Capability Manifest

新增：

```text
GET /agent/capabilities
```

用于让 HarmonyOS / 未来 LLM context 明确知道当前 Agent 能力边界：

```text
direct_accompaniment_generate     # 直接伴奏路径，不需要 LLM
agent_playback_prepare            # 自然语言立即播放准备
agent_practice_plan               # 练习计划生成，P0 rule-based
session_review_recommendation     # 复盘推荐，P0 rule-based
```

这一步把“伴奏引擎是 Agent 可用工具之一，但不是 Agent 必经入口”的原则机器可读化。

---

### 1.2 Context Profile Manifest

新增：

```text
GET /agent/context/profiles
```

用于公开当前 Agent 任务类型与上下文组装策略：

```text
practice_plan_generation
immediate_practice_playback
session_review
coach_qa
```

P0 仍未接真实 LLM，但 `ContextPacket` / `ContextBuilder` / `ContextProfile` 的契约已经明确。

---

### 1.3 ArkTS Contract Sketch

新增：

```text
GET /agent/contracts/arkts
```

返回 HarmonyOS 可参考的接口草图，包括：

```text
ClientContext
AgentPlanRequest
AgentPlaybackPrepareRequest
PracticePlan
PlaybackInstruction
AccompanimentAsset
AgentResponse
```

注意：该 endpoint 是 contract sketch，不替代正式 ArkTS 源码；鸿蒙端应在 `PracticeTypes.ets` / `AgentTypes.ets` 中实现等价 interface。

---

### 1.4 API 请求支持 snake_case 与 camelCase

`jammate_api.schemas.ApiModel` 现在支持：

```text
snake_case:  user_input / available_minutes / duration_minutes
camelCase:   userInput / availableMinutes / durationMinutes
```

这让 Python 端保持 snake_case，同时方便 HarmonyOS 使用 ArkTS 风格字段。

---

### 1.5 Agent Trace 持久化

`TraceLogger` 新增 `JsonTraceStore`，默认 API 进程持久化到：

```text
demos/agent_traces/
```

新增：

```text
GET /agent/traces
GET /agent/traces/{trace_id}
```

每次 `/agent/practice/plan` 或 `/agent/playback/prepare` 返回的 `trace_id` 都可被查询，用于排查：

```text
Agent 为什么这样分类？
用了什么 context summary？
workflow 走到哪一步？
plan / playback 是否通过 guardrail？
```

---

## 2. 当前边界确认

### 2.1 直接伴奏路径

```text
HarmonyOS
↓
POST /accompaniment/generate
↓
jammate_api.routes.accompaniment_routes
↓
jammate_engine.runtime.generate
↓
midi_base64
```

不需要 Agent，不需要 LLM。

### 2.2 Agent 编排路径

```text
HarmonyOS
↓
POST /agent/playback/prepare 或 /agent/practice/plan
↓
jammate_api.routes.agent_routes
↓
jammate_agent.core.JamMateAgent
↓
capability / provider / adapter
↓
jammate_engine 或其他未来 provider
```

### 2.3 HarmonyOS 本地 practice workspace

仍然应能无 LLM 跑通：

```text
PracticeTask
Routine
PracticeSession
Timer
ExerciseBlock status
SessionReview
Local history
Pending sync
```

Python Agent 是智能增强层，不是本地练习模块的唯一实现。

---

## 3. 测试覆盖

新增测试：

```text
tests/test_v2_3_11_agent_context_contract_hardening.py
```

覆盖：

```text
/agent/capabilities
/agent/context/profiles
/agent/contracts/arkts
/agent/traces/{trace_id}
camelCase HarmonyOS payload compatibility
```

---

## 4. 下一步建议

推荐下一步：

```text
v2_3_12_harmonyos_practice_api_contract_sync
```

目标：

```text
1. 输出正式 ArkTS interface 文件草案。
2. 固化 HarmonyOS 调用样例。
3. 增加 /accompaniment/generate 与 /agent/playback/prepare 的端到端 JSON 示例。
4. 明确 midi_base64 播放与 client_loop_until_target_duration 的前端处理规则。
5. 为直接伴奏与 Agent 伴奏准备统一的 PlaybackAsset 缓存字段。
```
