# v2_3_12 — HarmonyOS Practice API Contract Sync

## 目标

本版本不改变 JamMate Engine 的音乐生成主链路，而是把 HarmonyOS 侧接入 JamMate Agent / Practice / Accompaniment API 所需的合同进一步收口。

核心原则：

```text
HarmonyOS 本地练习模块可以无 LLM 跑通：task / routine / timer / session / review / local history。
直接伴奏生成可以无 LLM 跑通：POST /accompaniment/generate。
JamMate Agent 是增强入口：自然语言练习编排、立即陪练、复盘推荐、后续 LLM 上下文工程。
```

## 新增/强化 API

```text
GET /agent/contracts/arkts/source
GET /agent/contracts/examples
GET /agent/playback/spec
```

继续保留：

```text
GET  /agent/contracts/arkts
GET  /agent/capabilities
GET  /agent/context/profiles
POST /agent/practice/plan
POST /agent/playback/prepare
POST /accompaniment/generate
```

## 请求/响应大小写规则

- Request：继续支持 `camelCase` 与 `snake_case`。
- Response：当前后端 canonical 仍为 `snake_case`。
- HarmonyOS 建议在 `PracticeApiClient` 层做统一映射，不要让 UI 页面直接关心后端字段命名。

## 播放循环规范

`/agent/playback/prepare` 返回的 MIDI asset 不是为了覆盖完整 30 分钟/45 分钟而生成超长文件。Practice duration 是本地 timer 的目标，MIDI asset 是可循环播放的伴奏材料。

HarmonyOS 应读取：

```json
{
  "playback_instruction": {
    "auto_start": true,
    "target_duration_minutes": 30,
    "client_loop_until_target_duration": true,
    "asset_loop_mode": "loop_until_target_duration",
    "stop_condition": "practice_timer_reaches_target_duration_or_user_stops",
    "requires_local_timer": true
  }
}
```

客户端行为：

```text
1. decode/cache midi_base64
2. start local practice timer
3. play returned asset
4. if asset ends before timer target, loop locally
5. stop when timer reaches target or user stops
6. save SessionReview locally, then sync when available
```

## 缓存规则

新增/强化字段：

```text
asset.cache_key
playback_instruction.cache_policy.cache_key
```

HarmonyOS 建议：

```text
1. 优先用 asset.cache_key 作为本地缓存 key。
2. 没有 cache_key 时 fallback 到 asset.asset_id。
3. cache payload 至少包含 midi_base64 / duration_seconds / debug_summary。
4. 当 cache_key 与当前请求签名匹配且用户没有要求重新生成时，可复用缓存。
```

## 直接伴奏路径仍不经过 Agent

用户手动选择明确参数时：

```text
POST /accompaniment/generate
```

这条路径不需要 LLM，不需要 JamMate Agent 参与。

## Agent 路径

用户自然语言输入时：

```text
POST /agent/practice/plan
POST /agent/playback/prepare
POST /agent/message
```

Agent 可能调用 Chart / Practice / Accompaniment capabilities；其中伴奏引擎只是可调用工具之一。

## HarmonyOS 文件建议

```text
features/practice/model/AgentTypes.ets
features/practice/model/PracticeTypes.ets
features/practice/api/PracticeApiClient.ets
features/practice/service/PlaybackAssetCache.ets
features/practice/service/PracticePlaybackController.ets
```

`GET /agent/contracts/arkts/source` 已提供可复制的 `AgentTypes.ets` 草案。
