---
title: "autofix.ci：让 Pull Request 自动化修复成为流水线标配"
date: 2026-05-16T03:07:35+08:00
slug: "autofix-ci-github-action-automated-pr-fixes"
description: "autofix.ci 是 GitHub App + GitHub Action 组合，在 CI 末端自动修复 PR 中的格式问题。本文解析其原理、架构与使用方法。"
draft: false
categories: ["技术笔记"]
tags: ["GitHub Actions", "自动化修复", "CI 流水线", "代码格式化", "Pull Request"]
---

# autofix.ci：让 Pull Request 自动化修复成为流水线标配

autofix.ci 把 PR 里那些"修起来 30 秒、等起来半小时"的格式问题交给 CI 末端处理：开发者在 CI 中跑已有的格式化工具，autofix.ci 收集 staged 变更并 push 回 PR 分支。它适合对代码风格有强制要求、且不想在 review 中反复纠结格式的团队；如果项目对第三方后端可见性敏感，或需要自托管修复链路，则要权衡后再采用。

## 总览：组件边界与数据流

autofix.ci 由两端组成，边界清晰：

| 组件 | 角色 | 开源情况 |
|------|------|---------|
| GitHub App（`autofix-ci`） | 安装到仓库，提供写入 PR 的权限 | 否 |
| GitHub Action（`autofix-ci/action`） | 在 CI 末端收集变更、上报任务 | 是（MIT，TypeScript） |
| 后端服务（`autofix-api.maximilianhils.com`） | 接收 artifact、生成 commit、push 回 PR | 否（Rust） |

Action 只负责"收集 + 上报"，commit 构造和 push 发生在云端后端。这种拆分让 Action 保持轻量，代价是修复链路必须经过第三方服务。

| 维度 | 数据 |
|------|------|
| GitHub App slug | `autofix-ci` |
| Action 仓库 | `autofix-ci/action` |
| Action Stars | 228（截至 2026-05，源自仓库公开数据） |
| 主要语言 | TypeScript（Action），Rust（后端服务） |
| 许可证 | MIT |
| 后端开源 | 否（API 地址：`autofix-api.maximilianhils.com`） |

## 它在解决什么问题

PR 经常因为以下原因被阻塞：

- `cargo fmt` / `gofmt` / `prettier` / `ruff format` 报出的格式问题
- import 顺序错误或未使用的 import 残留
- 文档注释与代码不同步

这些问题修复成本极低，但传统流程需要：开发者本地修复 → 推送 → CI 通过 → 再次 review，一来一回消耗不少注意力。

autofix.ci 的做法是：在 CI 里运行你已有的格式化工具，然后让 autofix.ci 自动把修复结果推回到 PR 分支。开发者接受或 review 修复即可，不必再手动处理琐碎的 style 问题。

## 工作原理：一次修复任务的完整路径

下面以一个 PR 触发场景为例，跟踪修复任务如何流过系统。理解这条路径有助于排查"为什么修复没生效"或"为什么 commit 出现在 PR head 而非当前 checkout 的 commit"。

```
开发者 push 代码
 ↓
CI 流水线运行（包含格式化工序）
 ↓
autofix-ci/action 在流水线末端被调用
 ↓
收集 staged changes，构建 artifact
 ↓
上报到 autofix.ci 后端 API
 ↓
后端处理修复，生成 commit 并 push 回 PR
```

举一个具体场景：开发者 Alice 向 PR #42 push 了一次提交，CI 跑 `prettier --write .` 修改了 3 个文件。Action 启动后，先 `git reset` 清空暂存区，再 `git add --all` 把 prettier 的改动全部暂存；接着校验这 3 个文件路径不包含 `.github`，创建一条 `autofix` commit；随后 `fetch` PR #42 的 head sha，`cherry-pick` 把修复 diff 挂到 PR head 之上；最后把变更打包成 artifact 上传，并 POST 到 `autofix-api.maximilianhils.com/fix`。后端拉取 artifact、以 autofix.ci App 身份 push commit 到 PR #42 的分支，Alice 在 PR 上看到一条新的 `autofix` commit，review 或直接合并即可。

关键约束有两条：

1. **workflow 必须命名为 `autofix.ci`**。Action 启动时校验 `GITHUB_WORKFLOW` 环境变量，名称不匹配会直接抛错。这是安全机制：防止恶意 PR 通过其他 workflow 触发 autofix.ci 写入。
2. **Action 禁止修改 `.github` 目录**。一旦 staged 文件中包含 `.github` 路径，Action 抛错退出。这条规则阻止 PR 通过 autofix.ci 改动 workflow 自身，避免权限提升。

### Action 源码关键路径

Action 源码托管于 [autofix-ci/action](https://github.com/autofix-ci/action)，核心逻辑在 `index.ts`。

**1. 安全校验**

```typescript
// 出于安全考虑，工作流必须命名为 "autofix.ci"
if (process.env.GITHUB_WORKFLOW !== "autofix.ci") {
  throw `For security reasons, the workflow in which the autofix.ci action is used must be named "autofix.ci".`;
}
```

**2. 收集变更文件**

```typescript
// 重置并暂存所有变更
await exec("git", ["reset"]);
await exec("git", ["-c", "core.fileMode=false", "add", "--all"]);

// 提取文件列表（禁用路径转义，支持中文路径）
let { stdout } = await getExecOutput("git", [
  "-c", "core.quotepath=false",
  "diff", "--name-only", "--staged", "--no-renames",
]);

// 安全检查：禁止修改 .github 目录
if (changes.some((path) => path.includes(".github"))) {
  throw "The autofix.ci action is not allowed to modify the .github directory.";
}
```

`core.fileMode=false` 忽略文件权限位变化（CI 环境中常见噪声），`core.quotepath=false` 让中文路径不被转义，`--no-renames` 防止重命名被识别为删除+新增，简化 diff 处理。

**3. PR 场景下的 rebase 处理**

当触发源是 Pull Request 时，Action 需要先将修复 commit rebased 到 PR head 上：

```typescript
if (event.pull_request) {
  // 创建修复 commit
  await exec("git", ["config", "user.name", "autofix.ci"]);
  await exec("git", ["config", "user.email", "noreply@autofix.ci"]);
  await exec("git", ["commit", "--no-verify", "-m", "autofix"]);

  // 拉取并 checkout PR head
  await exec("git", ["fetch", "--depth=1", "origin", event.pull_request.head.sha]);
  await exec("git", ["checkout", "--force", "FETCH_HEAD"]);

  // 将修复以 cherry-pick 方式应用到 PR head
  await exec("git", ["cherry-pick", "--no-commit", commit_hash]);
}
```

为什么需要这一步？CI runner checkout 的 commit 可能是 merge commit，`github.event.pull_request.head.sha` 与 `actions/checkout` 拉到的 ref 不一定一致。直接 push 修复会污染 PR head 历史。Action 通过 fetch PR head → cherry-pick 修复 diff 的方式，保证最终 push 的 commit 直接挂在 PR head 之上。

**4. 上报后端**

```typescript
// 构建修复请求 payload
const fileChanges = { additions: [], deletions: [] };
// ... 收集文件内容 ...

// 上传 artifact
await client.uploadArtifact("autofix.ci", [filename], ".", { retentionDays: 1 });

// 通知后端处理
const url =
  "https://autofix-api.maximilianhils.com/fix" +
  "?owner=" + encodeURIComponent(event.repository.owner.login) +
  "&repo=" + encodeURIComponent(event.repository.name);
```

修复 artifact 通过 GitHub Actions artifact 机制上传（保留 1 天），后端收到通知后拉取 artifact 并执行修复。Action 本身不接触修复逻辑，只完成"打包 + 通知"。

## 接入：从零到第一次自动修复

### 第一步：安装 GitHub App

访问 [autofix.ci](https://autofix.ci) 并安装应用到目标仓库。安装时会提示授权以下权限：

- `actions: write`——更新 workflow 状态
- `checks: write`——写入 check 结果
- `contents: write`——写入 commit
- `pull_requests: write`——更新 PR

### 第二步：创建 workflow 文件

在仓库根目录创建 `.github/workflows/autofix.yml`：

```yaml
name: autofix.ci

on:
  push:
    branches: [main, master]
  pull_request:

jobs:
  autofix:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}

      # ↓ 这里放你自己的格式化工序 ↓
      - run: cargo fmt

      # ↓ Action 必须在格式化工序之后调用 ↓
      - uses: autofix-ci/action@v1
        with:
          fail-fast: false
```

> **安全加固建议**：将 Action 固定到特定 commit hash 而非 tag，例如 `autofix-ci/action@8bc06253bec489732e5f9c52884c7cace15c0160`，以降低供应链攻击风险。

### 第三步：配置参数（可选）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `fail-fast` | `true` | 当某个 commit 触发修复时，取消其他并行 workflow |
| `commit-message` | `autofix` | 自定义修复 commit 的提交信息 |
| `comment` | 无 | 在 PR 中添加自定义评论 |

示例：

```yaml
- uses: autofix-ci/action@v1
  with:
    fail-fast: false
    commit-message: "style: auto-format code"
    comment: "autofix.ci 已自动修复格式问题"
```

### 多语言场景示例

官方 setup 页面（[autofix.ci/setup](https://autofix.ci/setup)）提供了大量开箱即用的 YAML 片段，以下是几个典型语言生态的示例：

**Python + ruff**

```yaml
- uses: actions/checkout@v4
- run: pip install ruff
- run: ruff format .
- uses: autofix-ci/action@v1
```

**TypeScript / JavaScript + Prettier**

```yaml
- uses: actions/checkout@v4
- run: npx prettier --write .
- uses: autofix-ci/action@v1
```

**Rust + rustfmt**

```yaml
- uses: actions/checkout@v4
- run: rustfmt
- uses: autofix-ci/action@v1
```

**Go + gofmt**

```yaml
- uses: actions/checkout@v4
- run: gofmt -w .
- uses: autofix-ci/action@v1
```

所有示例的关键逻辑一致：先运行本地格式化工具，再调用 autofix.ci。autofix.ci 本身不内置任何 linter 或 formatter，它只收集上一阶段产生的 staged 变更。

## 适用边界与采用建议

### 适合的场景

- **格式强制统一**：团队对 code style 有明确要求，不想在 review 中纠结格式化问题
- **减少 PR 轮次**：避免"CI 失败→修复→再 review"的琐碎等待
- **多语言项目**：同一个 workflow 可以串联多种格式化工具（如 Python 用 ruff、JS 用 prettier、Rust 用 rustfmt）
- **PR 贡献引导**：开源项目可以用 autofix.ci 降低外部贡献者的格式门槛

### 优势

- **零侵入**：不需要改代码，不需要 pre-commit hook，不需要额外的本地配置
- **安全边界清晰**：Action 明确禁止修改 `.github` 目录，防止误操作 workflow 配置
- **PR 专用**：对 Push 到分支和 PR 两种触发场景做了不同处理（rebase onto PR head）
- **隐私友好**：官方声明不收集、不传输、不出售任何个人数据（见[隐私政策](https://autofix.ci/privacy)）

### 局限与注意事项

- **后端非开源**：修复逻辑运行在 `autofix-api.maximilianhils.com`，无法自托管
- **不修改 `.github`**：workflow 配置文件本身不会被 autofix.ci 修复（安全限制）
- **对敏感代码库**：如果 CI 涉及私有密钥或高度敏感逻辑，上报 artifact 到第三方需要自行评估风险
- **职责单一**：autofix.ci 不做代码质量检查，只负责修复你 CI 中已经运行的工具所发现的问题
- **依赖 CI 顺序**：Action 必须放在所有格式化工序之后调用

### 采用建议

引入前建议按以下顺序评估：

1. **先确认格式工具链稳定**：autofix.ci 放大已有工具的效果，工具链本身有问题会被同步放大。先在本地或 pre-commit hook 中跑通 `ruff format` / `prettier` / `rustfmt` 等基础工具。
2. **评估第三方后端可见性**：artifact 上传到 `autofix-api.maximilianhils.com`，敏感仓库考虑用 GitHub 自带的 `pre-commit` action 或自建方案。
3. **小范围试点**：先在一个仓库跑两周，观察 commit 噪声和 review 流程变化，再推广到组织级别。
4. **配合分支保护**：把 autofix.ci workflow 加入必需检查，避免 PR 在修复完成前被合并。

## 常见问题

**Q: 修复 commit 会不会和我的原始 commit 混在一起造成历史污染？**

不会。autofix.ci 的修复以独立 commit 形式 push 到 PR 分支，消息默认为 `autofix`（可自定义）。最终合并时可以 squash 或 rebase，保持干净的 master 历史。

**Q: 可以指定只对特定文件类型自动修复吗？**

这是 CI 层面的设计选择。你可以在 workflow 中只对特定目录或文件类型运行格式化工具，autofix.ci 会自动收集该步骤产生的 staged changes。

**Q: 如何禁用 autofix.ci 对某个 PR 的自动修复？**

暂时没有 per-PR 的开关。如果需要临时禁用，可以将对应 workflow 的 `autofix-ci/action` step 注释掉，或在 workflow 中加入条件判断。

**Q: 修复失败怎么办？**

后端处理失败时，Action 会输出错误信息并将 workflow 标为失败，同时打印需要手动修复的内容。

## 延伸链接

- autofix.ci 官网：https://autofix.ci
- GitHub Action 仓库：https://github.com/autofix-ci/action
- Action 源码（TypeScript）：https://github.com/autofix-ci/action/blob/main/index.ts
- 官方 Setup 指南：https://autofix.ci/setup
- 隐私政策：https://autofix.ci/privacy
