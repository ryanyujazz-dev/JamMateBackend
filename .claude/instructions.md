# JamMateBackend 项目工作流

## 开发模式

用户通过 ChatGPT 进行开发，每次对话产出一个完整的 zip 工程包。我的任务是接收 zip 并更新到 GitHub 对应分支。

## 仓库分支

- `main` — 稳定版本，禁止直接提交，只通过 PR 更新
- `integration` — 集成分支，处理共享文档冲突，feature 分支的 PR 先到这里
- `feature/agent-workflow` — Agent 工作流相关开发
- `feature/engine-deepening` — 引擎深度优化相关开发

main 和 integration 分支已在 GitHub 设为保护分支，禁止直接 push。

### 分支流转方向

```
feature/agent-workflow ──→ integration ──→ main
feature/engine-deepening ──→ integration ──→ main
```

feature 分支的代码通过 PR 合入 integration，在 integration 上统一处理共享文档（README、VERSION 等），确认无误后再通过 PR 合入 main。

---

## 收到 zip 时的操作流程

用户只需给我 zip 路径，严格按以下顺序执行：

### 第一步：解压到临时目录（不碰工作区）

```
unzip -o <zip文件> -d /tmp/jammate_update
```

### 第二步：分析 zip 内容，判断目标分支

浏览 `/tmp/jammate_update/<包内目录>/` 的文件结构和变更内容：
- 变更集中在 agent/workflow 相关文件 → `feature/agent-workflow`
- 变更集中在 engine/音频处理相关文件 → `feature/engine-deepening`
- 两者都有 → 询问用户
- 不涉及两边（cleanup、文档治理等）→ 合到当时更活跃的分支（最近有 commit 的那个）

同时生成 commit message。

### 第三步：切换到目标分支并拉取最新

```
git checkout <目标分支>
git pull origin <目标分支>
```

### 第四步：rsync 覆盖到工作区

因为每次是完整工程 zip，使用 `--delete` 防止旧文件残留：

```
rsync -av --delete \
  --exclude='.git' \
  --exclude='.claude' \
  --exclude='.env' \
  --exclude='.venv' \
  --exclude='__pycache__' \
  --exclude='.pytest_cache' \
  /tmp/jammate_update/<包内目录>/ .
```

**不删除 zip 原文件**，仅清理临时目录：
```
rm -rf /tmp/jammate_update
```

**警告：`--delete` 会删除目标目录中源目录没有的文件。必须确保已 checkout 到正确分支再执行 rsync，否则会破坏 main 工作区。**

### 第五步：跑基础测试 / 编译检查

根据项目类型执行对应的检查命令（如 `pytest`、`python -m py_compile` 等），确认无报错。

如果测试失败，不能直接提交。必须告诉用户：
```
测试失败：
<失败命令>
<失败摘要>

是否仍然提交？
```

### 第六步：展示变更，等待用户确认

按标准汇报格式展示：

```
判断目标分支：feature/agent-workflow

判断依据：
- src/jammate_agent 有变更
- src/jammate_api 有变更
- frontend_fixtures 有变更
- jammate_engine 核心生成链路无明显变更

版本：v2_4_0

变更摘要：
<git diff --stat>

拟定 commit message：
feat(agent): add LLM workflow foundation

是否确认同步到 feature/agent-workflow 并提交？
```

### 第七步：确认后提交推送

```
git add -A
git commit -m "<commit message>"
git push
```

提交前检查是否有敏感信息（API key 等）。

提交后按标准格式汇报：

```
已完成提交并推送。

分支：feature/agent-workflow
commit：abc1234 feat(agent): add LLM workflow foundation

检查结果：
- compileall passed
- pytest passed

下一步建议：创建 PR 或继续当前分支下一阶段开发。
```

---

## PR 合并流程

### 合并路径

```
feature/agent-workflow ──→ integration ──→ main
feature/engine-deepening ──→ integration ──→ main
```

### 第一步：feature 分支 → integration

1. 按文档归属规则，检查 feature 分支是否只改了自己专属的文档
2. 创建 PR 到 integration：
   ```
   gh pr create --base integration --head <feature分支> --title "<标题>" --body "<摘要>"
   ```
3. 用户确认后 merge：
   ```
   gh pr merge <PR编号> --merge
   ```
4. 在 integration 上统一更新共享文档（README、VERSION、ARCHITECTURE 等）
5. 提交共享文档更新并推送 integration

### 第二步：integration → main

integration 上的共享文档对齐完成后：

1. 创建 PR：
   ```
   gh pr create --base main --head integration --title "<标题>" --body "<摘要>"
   ```
2. 用户确认后 merge：
   ```
   gh pr merge <PR编号> --merge
   ```

### 第三步：同步 feature 分支

main 更新后，将两个 feature 分支 reset 到最新 main：
```
git checkout <feature分支>
git fetch origin main
git reset --hard origin/main
git push origin <feature分支> --force
```

### 对齐策略（替代方案）

如果不想 reset feature 分支，也可以让 ChatGPT 基于最新 main 重新出 zip，再按正常流程覆盖。
   ```
   gh pr merge <PR编号> --merge
   ```

---

## 注意事项

### 1. main 不直接提交

任何情况下都不要：
```
git checkout main
git add .
git commit -m "..."
git push
```
main 只通过 PR 更新。GitHub 保护分支已开启作为硬约束。

### 2. 切换分支时文件会自动切换

本地文件反映的是当前分支内容：
- `git checkout feature/agent-workflow` → 工作区显示 Agent 分支内容
- `git checkout feature/engine-deepening` → 工作区显示 Engine 分支内容

这是正常的。

### 3. 文档归属规则（防止并行开发冲突）

各分支只能修改自己归属的文档，共享文档只在合入 main 时统一更新。

**共享文档（仅 main / integration 分支改）：**
- `README.md`
- `agent.md`
- `VERSION`
- `pyproject.toml`
- `docs/ARCHITECTURE_V2.md`
- `docs/API_CONTRACT_V2.md`
- `docs/DEVELOPMENT_TASK_PLAN_V2.md`
- `docs/CHANGELOG.md`
- `frontend_fixtures/harmonyos/`

**Engine 线专属文档（仅 feature/engine-deepening 改）：**
- `docs/DEVELOPMENT_TASK_PLAN_ENGINE_V2.md`
- `docs/CHANGELOG_ENGINE.md`
- `docs/GENERATION_RULES_SUMMARY_V2.md`
- `docs/STYLE_RULE_BASELINE_V2.md`

**Agent 线专属文档（仅 feature/agent-workflow 改）：**
- `docs/DEVELOPMENT_TASK_PLAN_AGENT_V2.md`
- `docs/CHANGELOG_AGENT.md`
- `docs/AGENT*.md`

收到 zip 后，如果 ChatGPT 的全量包修改了不属于当前分支的共享文档，rsync 覆盖后要在 commit 前检查：属于另一分支归属的文档改动应被忽略或备注。合入 main 时再统一同步共享文档。

### 4. 不要提交无关本地文件

不要提交：
- `.venv/`
- `.env`
- `__pycache__/`
- `.pytest_cache/`
- `.DS_Store`
- 临时 zip 解压目录

### 5. demos 文件处理

如果 demos 是本次开发交付的一部分，可以提交。
如果 demos 很大，先询问用户是否需要提交到 GitHub。

### 6. commit message 格式

遵循 conventional commits：
```
feat: 新功能
fix: 修复问题
refactor: 重构
test: 测试相关
docs: 文档更新
chore: 杂项
```
