# v2_3_12 — Playback Asset Cache Policy

## 背景

Practice duration 由 HarmonyOS 本地 timer 负责，返回的 MIDI asset 应作为可循环材料，不应为了 30 分钟练习生成超长 MIDI。

## 缓存 key

优先级：

```text
1. asset.cache_key
2. asset.asset_id
3. request signature hash（客户端 fallback）
```

## 推荐缓存对象

```ts
interface CachedPlaybackAsset {
  cacheKey: string
  midiBase64: string
  durationSeconds?: number
  createdAt: number
  debugSummary?: Record<string, Object>
}
```

## 复用规则

```text
- 同一 cache_key 可复用。
- 用户要求“重新生成”时应绕过缓存。
- Agent 侧返回 cache_policy.reuse_when_request_signature_matches=true 时可直接复用。
- Session 结束后可保留 recent_practice_asset 缓存，便于重复练习。
```

## 不要缓存的情况

```text
1. response.ok=false
2. asset.midi_base64 为空
3. 用户明确要求 regenerate
4. 本地播放解码失败
```
