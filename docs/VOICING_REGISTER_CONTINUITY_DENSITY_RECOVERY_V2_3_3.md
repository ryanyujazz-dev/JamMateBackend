# v2_3_3 — Voicing Register Continuity / Density Recovery

## 背景

v2_3_1 的 `tools/demo_audit_pipeline.py` 成功统一了 Demo Matrix 与 audit thresholds，但 Misty Ballad listening demo 暴露出两个听感问题：

1. Ballad upper-structure job 仍偏向 voicing isolation / audit mode，使用 `global_voicing_override_region_start_anchor`，导致真实 comping feel 丢失。
2. Voicing selector 在局部 voice-leading 上奖励小步移动，但缺少段落级 register center / top ceiling / density distribution 检查，容易让音高一段时间慢慢爬到很高，再被 guard 或候选池突然拉低。

v2_3_3 的目标不是继续扩张新 voicing source，而是恢复之前 Ballad SPREAD / functional grouping 的厚度与自然音区连续性。

## 核心改动

### 1. Listening demo 退出 isolation mode

`tools/demo_audit_pipeline.py` 中的 Misty Ballad job 不再强制：

- `pattern_mode = region_start_anchor_only`
- `disable_anticipation = True`
- `global_voicing_override_region_start_anchor`

Misty job 现在回到自然 Ballad comping pattern，并保留三遍循环。

### 2. Register continuity recovery

在 `core/voicing/selection/scorer.py` 中加入 `REGISTER_CONTINUITY_RECOVERY_VERSION = v2_3_3`，并把 register continuity 作为 candidate scoring 的一个独立分量：

- register center target
- center tolerance
- top soft / hard high
- low soft / hard low
- average pitch motion soft limit
- top motion soft limit
- continued upward drift above center penalty
- continued downward drift below center penalty

该逻辑仍然属于 selector/scorer，不新建另一套 voicing 系统。

### 3. Candidate filtering guard

`core/voicing/selection/selector.py` 新增 metadata-gated candidate filter：

- 如果候选池中存在满足 top motion、average motion、hard top ceiling 的候选，则优先只在这些候选内选择。
- 如果全部被过滤，则回退完整候选池，避免生成失败。

### 4. Ballad SPREAD grouping mix 恢复

Misty Ballad pipeline job 重新启用 `ballad_spread_grouping_mix_policy`，让 5/6/7-note functional grouping 真正进入 listening demo：

- `2+3`
- `2+4`
- `3+3`
- 少量 `3+4`

同时降低 SPREAD / Upper Structure 的 top high 和 whole-register high，避免过亮或尖锐。

## Demo Matrix 阈值增强

v2_3_3 继续使用 `tools/demo_audit_pipeline.py` 作为统一入口，并增强 Demo Matrix listening regression thresholds：

```bash
PYTHONPATH=src python tools/demo_audit_pipeline.py --fail-on-thresholds
```

Misty Ballad job 新增验证：

- 非 4-note density events 至少 50 个
- `top_note_max <= 74`
- `average_pitch_mean <= 62.0`
- upper-structure / altered-dominant audit signal 仍必须存在

这避免后续再次出现“全是 4-note”或“音区一路爬高再突然下降”的回归。

## 审计目标

Misty Ballad v2_3_3 demo 的目标状态：

- 主要密度回到 5/6-note functional grouping
- piano top note 不超过 MIDI 74
- average pitch 维持在温暖 register center 附近
- 不再使用 `global_voicing_override_region_start_anchor`
- register guard violations 为 0

## 后续建议

下一步不应继续扩大 Demo Matrix，而应先做 v2_3_3：

**Ballad SPREAD Density / Register Listening Calibration**

重点根据人工试听微调：

- 2+3 / 2+4 / 3+3 / 3+4 比例
- top note ceiling 是否需要进一步降低到 72/73
- 5-note 与 6-note 的 balance
- Upper Structure altered 的出现比例与亮度
