# v2_3_10 — JamMate Agent / Engine / API Boundary Foundation
## 核心结论
本版本将 JamMate 从单一伴奏引擎工程，升级为更清晰的三层系统：
```text
src/
  jammate_engine/   # 独立伴奏生成内核
  jammate_agent/    # 同级智能编排层
  jammate_api/      # 面向客户端的服务装配层
```
最重要的架构原则：
```text
LLM / Agent 是增强入口，不是必经入口。
JamMate Engine 必须不依赖 Agent，仍可被客户端直接调用。
JamMate Agent 可以把 Engine 当作一个工具 / capability / provider 使用。
JamMate API 同时暴露直接伴奏路径和 Agent 编排路径。
```
---
## 1. 角色边界
### 1.1 `jammate_engine`
`jammate_engine` 是独立音乐生成内核。它只关心：
```text
leadsheet
style
tempo
choruses
ensemble
voicing_override
output_path
```
它不应该知道：
```text
用户为什么练这首歌
用户是否使用 LLM
用户最近练习历史
练习计划 / session / review
```
### 1.2 `jammate_agent`
`jammate_agent` 是 JamMate 的智能编排层。它当前 P0 能力包括：
```text
1. Practice plan generation
2. Immediate practice playback
3. Chart resolution
4. Accompaniment capability orchestration
5. Session review recommendation
6. Context packet / trace / guardrail skeleton
```
它不直接生成 MIDI；它通过 `AccompanimentProvider` 调用具体 provider。
### 1.3 `jammate_api`
`jammate_api` 是服务装配层，面向 HarmonyOS 暴露两条路径：
```text
/accompaniment/*  # 直接伴奏，不需要 Agent / LLM
/agent/*         # JamMate Agent 自然语言/智能编排入口
/practice/*      # 练习模板与轻量 practice API
```
---
## 2. 两条调用路径
### 路径 A：直接伴奏路径
当用户已经在 UI 中明确选择曲谱、风格、速度、choruses、声部等参数时，应直接调用：
```text
POST /accompaniment/generate
```
链路：
```text
HarmonyOS
↓
jammate_api.routes.accompaniment_routes
↓
jammate_engine.runtime.generate
↓
MIDI / midi_base64
```
这条路径不需要 LLM。
### 路径 B：Agent 编排路径
当用户用自然语言表达目标时，例如：
```text
我想练 Autumn Leaves 30 分钟，钢琴和声色彩丰富一点。
```
调用：
```text
POST /agent/playback/prepare
```
链路：
```text
HarmonyOS
↓
jammate_api.routes.agent_routes
↓
jammate_agent.core.JamMateAgent
↓
ChartResolver
↓
ImmediatePlaybackWorkflow
↓
AccompanimentProvider
↓
JamMateEngineAccompanimentAdapter
↓
jammate_engine.runtime.generate
```
---
## 3. Provider / Adapter 解耦
`jammate_agent` 不直接依赖 `jammate_engine` 内部细节。当前只有一个 adapter 允许 import engine：
```text
src/jammate_agent/adapters/jammate_engine_accompaniment_adapter.py
```
其余 agent/capability 逻辑依赖抽象：
```text
AccompanimentProvider
```
这保证未来可以替换成：
```text
RemoteAccompanimentApiAdapter
CachedAccompanimentAdapter
CloudAccompanimentAdapter
SimpleMetronomeAdapter
```
---
## 4. API 列表
### Health
```text
GET /health
```
### Direct Engine API
```text
GET  /accompaniment/styles
GET  /accompaniment/capabilities
POST /accompaniment/generate
```
### Agent API
```text
POST /agent/message
POST /agent/practice/plan
POST /agent/playback/prepare
POST /agent/session/review
```
### Practice API
```text
GET /practice/routines/templates
```
---
## 5. 与 HarmonyOS 的关系
HarmonyOS 应有自己的本地练习模块，可无 LLM 跑通：
```text
PracticeTask
Routine
PracticeSession
Timer
ExerciseBlock 状态
SessionReview
Local history
Pending sync
```
Python 端新增的 `jammate_agent` 主要用于智能增强：
```text
自然语言理解
练习计划编排
曲谱检索
伴奏生成调度
复盘推荐
上下文工程
```
直接伴奏也不需要 Agent；HarmonyOS 可以调用 `/accompaniment/generate`。
---
## 6. 当前 P0 实现说明
本版本实现了：
```text
1. 新增 sibling package: jammate_agent
2. 新增 sibling package: jammate_api
3. 保留 jammate_engine 作为独立内核
4. 直接伴奏 API: /accompaniment/generate
5. Agent 计划 API: /agent/practice/plan
6. Agent 立即播放 API: /agent/playback/prepare
7. ChartResolver 读取 examples/leadsheets
8. JamMateEngineAccompanimentAdapter 返回真实 midi_base64
9. Practice routine template API
10. 基础 smoke tests
```
P0 不做：
```text
1. 真正 LLM 调用
2. 开放式无限 tool loop
3. 云端存储
4. 网络曲谱搜索
5. 音频/MIDI 分析
```
这些属于后续能力。
---
## 7. 下一步建议
推荐下一步：
```text
v2_3_11_jammate_agent_context_and_contract_hardening
```
目标：
```text
1. 补齐 Agent API contract 文档与 HarmonyOS ArkTS interface 对照
2. 增加 direct accompaniment request/response 测试
3. 增加 /agent/playback/prepare 的 richer harmony fixture 测试
4. 为 AgentTrace 增加可查询 API 或 JSONL 存储
5. 明确 LLMProvider 抽象，但仍不接真实 LLM
```
## 8. Playback duration policy
`/agent/playback/prepare` treats `duration_minutes` as a session/playback target, not as a requirement to render one huge MIDI file. P0 generates a bounded backing asset of up to 3 choruses and returns:
```json
{
  "playback_instruction": {
    "auto_start": true,
    "target_duration_minutes": 30,
    "client_loop_until_target_duration": true
  }
}
```
HarmonyOS should loop the asset until the target practice duration is reached. Direct `/accompaniment/generate` still honors explicit `choruses` for manual engine calls.
