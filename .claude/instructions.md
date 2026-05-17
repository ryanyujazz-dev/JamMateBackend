# JamMateBackend 项目工作流

## 开发模式

用户通过 ChatGPT 进行开发，每次对话产出一个完整的 zip 工程包。我的任务是接收 zip 并更新到 GitHub 对应分支。

## 仓库分支

- `main` — 稳定版本，禁止直接提交，只通过 PR 更新
- `feature/agent-workflow` — Agent 工作流相关开发
- `feature/engine-deepening` — 引擎深度优化相关开发

main 分支已在 GitHub 设为保护分支，禁止直接 push。

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

### 并行开发的核心约束

两个分支并行开发时，ChatGPT 给的全量 zip 会让共有文件（VERSION、README、docs 等）在两边各自不同。如果直接 merge，会产生大量冲突且难以解决。

**解决方案：合并前需要对齐一次。** 先合并第一个分支，然后让 ChatGPT 基于最新 main 重新出一个第二个分支的 zip，再用新 zip 覆盖第二个分支，最后合并。

### 合并顺序：先 Agent → 对齐 → 再 Engine

#### 第一步：合并 feature/agent-workflow → main

1. 执行：
   ```
   git checkout feature/agent-workflow
   git pull origin feature/agent-workflow
   git diff main...feature/agent-workflow --stat
   ```
2. 分析差异，生成 PR 标题和摘要，展示给用户确认
3. 用户确认后：
   ```
   gh pr create --base main --head feature/agent-workflow --title "<标题>" --body "<摘要>"
   ```
4. 询问用户是否 merge，确认后：
   ```
   gh pr merge <PR编号> --merge
   ```

#### 第二步：对齐 Engine 分支

Agent 合入 main 后，**不要直接 git merge main 到 engine 分支**（会大量冲突）。

正确的做法：
1. 提醒用户把合并后的 main 状态告诉 ChatGPT 窗口 B（复制 VERSION、README、关键 docs 过去）
2. ChatGPT 基于最新 main 重新出一个 engine zip
3. 用户把新 zip 给我，按正常 zip 更新流程（解压 → checkout engine-deepening → rsync 覆盖 → 提交推送）

#### 第三步：合并 feature/engine-deepening → main

对齐完成后，合并应该是干净的：

1. 执行：
   ```
   git checkout feature/engine-deepening
   git pull origin feature/engine-deepening
   git diff main...feature/engine-deepening --stat
   ```
2. 分析差异，生成 PR 标题和摘要，展示给用户确认
3. 用户确认后：
   ```
   gh pr create --base main --head feature/engine-deepening --title "<标题>" --body "<摘要>"
   ```
4. 询问用户是否 merge，确认后：
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

### 3. 两个分支都可能改版本文件

容易冲突的文件：
- `VERSION`
- `pyproject.toml`
- `README.md`
- `agent.md`
- `docs/API_CONTRACT_V2.md`
- `docs/ARCHITECTURE_V2.md`
- `docs/DEVELOPMENT_TASK_PLAN_V2.md`

遇到冲突时，不要简单覆盖。需要根据 main 和当前分支内容合并保留双方有效信息。

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
