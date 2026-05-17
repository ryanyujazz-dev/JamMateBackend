# v2_3_9 — Anticipation Tie Sustain Repair

## 背景

v2_3_2 修复了 Ballad demo 的 voicing density 与 register continuity，但真实试听暴露出另一个更基础的问题：当 AnticipationResolver 把下一 chord region 的 beat-1 piano event 提前到前一 region 的 4& 时，ExpressionResolver 仍把这个 anticipated event 当成普通 region 内事件处理，并被 v2_2_51 的 `duration_region_clamp` 截断在 region 边界附近。

结果是：听起来有提前的 4& 和弦，但没有自然延续到原 beat 1 之后，缺少真正的 cross-bar tie / anticipation sustain。

## 修复原则

- Pattern 仍然只负责 pitchless onset，不决定 duration。
- Anticipation 仍然发生在 Expression / Voicing 之前。
- 普通 event 继续遵守 region-duration clamp，避免 Ballad 长 sustain 模糊 dense harmony。
- 只有 `anticipation.kind == next_beat1_to_previous_tail` 且 `tie_from_previous == true` 的 event 走特殊 duration 规则。

## 新规则

对于被提前的下一和弦 beat-1 event：

```text
anticipated_duration = lead_in_beats + original_event_duration_inside_source_region
```

例如：

- Ballad `soft_sustain=3.5`，从 beat 1 提前到前一小节 4&：`0.5 + 3.5 = 4.0`
- 如果 source chord region 只有 2 beats：`0.5 + 2.0 = 2.5`
- Bossa `core_short=0.45`，提前到 4&：`0.5 + 0.45 = 0.95`，保证至少跨过原 beat 1，而不是只响在 4& 上。

## 实现落点

- `core/anticipation/anticipation_resolver.py`
  - anticipated event metadata 记录：
    - `original_onset_beat`
    - `original_local_beat_in_source`
    - `source_region_duration_beats`
    - `lead_in_beats`
- `core/expression/expression_resolver.py`
  - 新增 `EXPRESSION_ANTICIPATION_TIE_DURATION_VERSION = v2_3_9`
  - 新增 anticipated tie duration path
  - 普通 event 仍走 v2_2_51 region clamp
- `core/expression/audit.py`
  - anticipated tie 跨 region 不再被误报为 ordinary `crosses_region_end`

## 验收

新增测试覆盖：

- Ballad anticipated sustain 从 4& 延续到原 beat 1 后。
- Dense two-beat region 中仍尊重 source region remaining duration。
- Bossa short beat-1 被 anticipation 后也会跨过原 beat 1。
- Expression audit 不把 anticipated tie 的 cross-region sustain 当作错误。
- AnticipationResolver metadata 能被 ExpressionResolver 正确读取。

## 后续建议

下一步应继续做 `v2_3_9 — Anticipation Timing Grid Contract Repair`：

- 专门输出 Bossa opening/core_batida anticipation demo。
- 专门输出 Ballad gentle 4& anticipation demo。
- 检查 anticipation 概率、持续时值、pedal 和 next-event overlap 是否自然。
