# v2_3_9 — Demo Matrix / Listening Regression Thresholds

## 1. 目标

v2_3_9 在 v2_3_0 统一 demo/audit pipeline 的基础上，增加一个轻量、稳定、manifest-driven 的 demo matrix 与基础 listening regression thresholds。

这一步不是替代人工试听，而是避免每次工程迭代后出现以下低级回归：

- demo 没有真正生成三遍循环；
- MIDI 里没有 note events；
- piano track 没有事件；
- piano audit 没有可检查事件；
- register guard 出现违规但没有被发现；
- altered / upper-structure 目标 demo 没有产出对应 audit signal。

## 2. 新增/更新文件

- `tools/demo_audit_pipeline.py`
  - 新增 `AuditThresholds`
  - 新增 `DemoMatrixEntry`
  - 新增 `standard_demo_matrix()`
  - 新增 `validate_audit_summary()`
  - 新增 `validate_job_audit()`
  - 新增 `validate_pipeline_outputs()`
  - `run_jobs()` 默认写入 manifest validation block
  - CLI 新增：
    - `--list-matrix`
    - `--no-validate`
    - `--fail-on-thresholds`
- `tests/test_v2_3_0_demo_audit_pipeline_consolidation.py`
  - 增加 v2_3_9 demo matrix / threshold validator / manifest validation 测试。
- `docs/DEMO_MATRIX_LISTENING_REGRESSION_THRESHOLDS_V2_3_1.md`
  - 本文档。

## 3. 标准 Demo Matrix

当前 matrix 保持小而稳定，不做风格全集扩张。

| matrix id | job id | 目的 |
|---|---|---|
| `minimal_swing_smoke` | `minimal_swing` | 普通 ii–V–I smoke demo，确认最小生成链路可听。 |
| `misty_ballad_upper_structure_altered` | `misty_ballad_upper_structure_altered` | Ballad / spread / upper structure / altered dominant 综合试听与审计。 |
| `blue_bossa_minor_altered` | `blue_bossa_minor_altered` | Bossa minor V / light altered 行为审计。 |
| `minor_turnaround_fixture` | `minor_turnaround_fixture` | minor V、local minor secondary、turnaround VI7、final V7 的紧凑 fixture。 |

## 4. 阈值设计

所有标准 job 默认检查：

- `performance_choruses == 3`
- `note_events >= 1`
- `note_events_by_track.piano >= 1`
- `piano_event_summary.event_count >= 1`
- `register_guard_violations <= 0`

Altered / upper-structure 定向 job 额外检查：

- `altered_degree_events >= 1`
- `altered_source_events >= 1`
- upper-structure job additionally requires `upper_structure_register_refinement_events >= 1`

这些阈值只负责捕获结构性回归，不负责判断“听感好坏”。真正的音乐判断仍然需要标准曲三遍循环试听。

## 5. 使用方式

列出标准 jobs：

```bash
PYTHONPATH=src python tools/demo_audit_pipeline.py --list
```

列出 demo matrix 与阈值：

```bash
PYTHONPATH=src python tools/demo_audit_pipeline.py --list-matrix
```

运行完整标准 demo matrix，并在阈值失败时退出非零：

```bash
PYTHONPATH=src python tools/demo_audit_pipeline.py --fail-on-thresholds
```

默认输出：

- `demos/v2_3_9_*_demo.mid`
- `demos/v2_3_9_*_audit_summary.json`
- `demos/v2_3_9_demo_audit_pipeline_manifest.json`

manifest 中包含：

```json
{
  "validation": {
    "status": "passed",
    "required_job_ids": [...],
    "missing_jobs": [],
    "failed_jobs": [],
    "job_results": {...}
  }
}
```

## 6. 架构边界

- Demo matrix 位于 `tools/demo_audit_pipeline.py`，属于开发/试听验证工具，不进入 runtime generation path。
- 阈值检查只读取公开 audit summary，不反向依赖 style 内部实现。
- 不新增独立 listening-regression 系统，不拆出额外模块，符合 Minimal File Split Principle。
- 旧 `examples/scripts/generate_*` 继续保留兼容；后续新试听优先走统一 pipeline。

## 7. 验证命令

```bash
python -m compileall src tools
PYTHONPATH=src python -m pytest -q
python tools/check_development_harness.py
PYTHONPATH=src python tools/demo_audit_pipeline.py --fail-on-thresholds
```

## 8. 下一步建议

v2_3_9 可以进入 **Style-specific Demo Matrix Expansion / Regression Coverage**：

- medium swing：标准曲 + drop-family/open method coverage；
- jazz ballad：Misty spread / upper structure / non-expanded comparison；
- bossa nova：Blue Bossa core rhythm + anticipation coverage；
- 每个风格只加入少量稳定 job，避免 demo matrix 膨胀成慢速全集测试。
