# HarmonyOS / JamMate Agent API Integration v2_3_11

## 1. 三条调用路径

### A. 本地无 LLM 练习模块

HarmonyOS 本地完成：

```text
PracticeTask / Routine / Session / Timer / Review / History
```

不依赖 Python Agent。

### B. 直接伴奏生成

用户已经明确参数时调用：

```text
POST /accompaniment/generate
```

示例：

```json
{
  "tune": "Blue Bossa",
  "style": "bossa_nova",
  "tempo": 120,
  "choruses": 1
}
```

### C. Agent 编排

用户使用自然语言时调用：

```text
POST /agent/message
POST /agent/practice/plan
POST /agent/playback/prepare
```

---

## 2. camelCase 支持

Python API 同时支持：

```json
{
  "user_input": "我想练 Blue Bossa 20分钟",
  "duration_minutes": 20
}
```

和：

```json
{
  "userInput": "我想练 Blue Bossa 20分钟",
  "durationMinutes": 20
}
```

鸿蒙端建议使用 camelCase，Python 文档内部继续使用 snake_case。

---

## 3. Agent Playback Prepare

Request:

```json
{
  "userInput": "我想练 Blue Bossa 20分钟，钢琴和声色彩丰富一点",
  "durationMinutes": 20
}
```

Response 关键字段：

```json
{
  "ok": true,
  "intent_type": "immediate_practice_playback",
  "asset": {
    "format": "midi_base64",
    "midi_base64": "...",
    "midi_path": "demos/...mid"
  },
  "playback_instruction": {
    "auto_start": true,
    "target_duration_minutes": 20,
    "client_loop_until_target_duration": true
  },
  "trace_id": "trace_xxx"
}
```

前端处理规则：

```text
1. 解码 midi_base64。
2. 播放返回的 MIDI asset。
3. 如果 client_loop_until_target_duration = true，则循环播放该 asset 直到练习 timer 达到 target_duration_minutes。
4. 保存 trace_id，调试时可 GET /agent/traces/{trace_id}。
```

---

## 4. Contract / Debug Endpoints

```text
GET /agent/capabilities
GET /agent/context/profiles
GET /agent/contracts/arkts
GET /agent/traces
GET /agent/traces/{trace_id}
```

这些 endpoint 主要服务联调和未来 LLM context engineering。
