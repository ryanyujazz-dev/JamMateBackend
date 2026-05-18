# AGENT_TODAY_PRACTICE_GUIDANCE_PROVIDER_BOUNDARY_E2E_V2_7_7

## 版本

```text
v2_7_7_agent_today_practice_guidance_provider_boundary_e2e
```

## 目标

本版本把 `v2_7_4` 的 Today Practice Guidance prompt contract 与 `v2_7_6` 的 output validation 串成一条 provider-boundary E2E：

```text
assembled_practice_context
→ TodayPracticeGuidance prompt messages
→ LLM Provider boundary / supplied providerResult
→ TodayPracticeGuidanceOutput validation
→ candidate-only guidance payload
```

这一步允许未来在用户主动询问“今天该练什么？”时，通过 LLM Provider boundary 生成结构化建议；但无论 LLM 返回什么，都必须先经过 validator，最终只输出建议和可编辑 Routine 候选。

## 明确非目标

本版本不做：

```text
不自动启动 Routine
不调用 /accompaniment/generate
不调用 engine adapter
不生成 MIDI asset
不启动 playback
不执行 tool
不绕过用户确认
不假设鸿蒙前端 UI 流程
不创建 Routine 结束后的推荐卡片
不改 Engine 音乐生成
不改共享文档
不改 HarmonyOS fixture
```

## 新增核心契约

```python
TodayPracticeGuidanceProviderBoundaryE2EPayload
build_today_practice_guidance_provider_boundary_e2e_payload(...)
build_today_practice_guidance_provider_boundary_e2e_summary(...)
today_practice_guidance_provider_boundary_e2e_contract()
```

## 新增 API

```http
GET  /agent/context/today-practice-guidance/provider-boundary/spec
POST /agent/context/today-practice-guidance/provider-boundary/e2e-preview
```

## 新增 CLI

```text
/today-practice-guidance-e2e [json_payload]
```

## Provider 行为

默认情况下，本版本不会自动发起 LLM 网络调用。

支持两种方式进入 E2E：

```text
1. 传入 providerResult / llmOutput fixture
   用于测试、预览、鸿蒙端调试、未来 provider adapter 测试。

2. 显式 callProvider=true 且传入/配置 provider
   通过 LLM Provider boundary 调用，但返回结果仍必须进入 v2_7_6 validator。
```

## 安全边界

所有结果必须保持：

```text
tool_executed = false
routine_start_enabled = false
route_called = false
engine_adapter_called = false
midi_asset_created = false
playback_started = false
accompaniment_generate_call_enabled = false
```

如果 provider 返回以下内容，validator 必须阻断：

```text
start_routine
start_playback
call_accompaniment_generate
generate_midi
execute_tool
dispatch_workflow
invoke_engine_adapter
midi_base64
local_midi_path
api_key
hidden_chain_of_thought
user_confirmation_required=false
```

## 与 Routine 的关系

本版本仍然不规定鸿蒙端展示流程。

Agent 只输出：

```text
guidance summary
recommended focus
recommended blocks
editable Routine candidates
next client actions
```

鸿蒙端自行决定展示为：

```text
聊天回复
ActionCard
Routine Setup
Bottom Sheet
练习队列
其他未来 UI
```

## 完成标准

完成后应当可以说：

```text
用户主动问“今天该练什么？”的 provider-boundary 技术链路已经闭合：
上下文 → prompt → provider output → validator → candidate-only guidance。
但 Agent 仍不会自动启动 Routine 或生成伴奏。
```
