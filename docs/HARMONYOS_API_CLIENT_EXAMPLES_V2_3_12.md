# v2_3_12 — HarmonyOS API Client Examples

## 1. 健康检查

```ts
await httpGet('/health')
```

## 2. 无 LLM 直接生成伴奏

```ts
const response = await httpPost('/accompaniment/generate', {
  tune: 'Blue Bossa',
  style: 'bossa_nova',
  tempo: 120,
  choruses: 3,
  seed: 42,
})

if (response.ok) {
  const asset = response.asset
  await playbackAssetCache.save(asset.cache_key, asset.midi_base64)
}
```

## 3. Agent 立即陪练

```ts
const response = await httpPost('/agent/playback/prepare', {
  userInput: '我想练 Blue Bossa 20分钟，钢琴和声色彩丰富一些',
  durationMinutes: 20,
})

if (response.ok) {
  const asset = response.asset
  const instruction = response.playback_instruction
  await playbackAssetCache.save(asset.cache_key, asset.midi_base64)
  if (instruction.auto_start) {
    practicePlaybackController.startLoopingAssetUntilTimerDone(asset, instruction)
  }
}
```

## 4. Agent 生成练习计划

```ts
const response = await httpPost('/agent/practice/plan', {
  userInput: '我今天有45分钟，想练Misty的ballad comping',
  availableMinutes: 45,
  instrument: 'piano',
})

if (response.ok) {
  localPracticeStore.savePlan(response.plan)
}
```

## 5. Trace 查询

```ts
const trace = await httpGet(`/agent/traces/${response.trace_id}`)
```

Trace 只用于 debug / 开发，不应成为普通用户 UI 的必需数据。
