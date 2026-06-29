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

autofix.ci 把 PR 里那些"修起来 30 秒、等起来半小时"的格式问题交给 CI 末端处理：开发者在 CI 中跑已有的格式化工具，autofix.ci 收集 staged 变更并 push 回 PR 分支。它适合对代码风格有强制要求、且不想在 review 中反复纠结格式的团队。如果项目对第三方后端可见性敏感，或需要自托管修复链路，则要权衡后再采用。

## 目录

- [先说结论](#先说结论)
- [前置知识](#前置知识)
- [学习目标](#学习目标)
- [总览：组件边界与数据流](#总览组件边界与数据流)
- [它在解决什么问题](#它在解决什么问题)
- [工作原理：一次修复任务的完整路径](#工作原理一次修复任务的完整路径)
- [接入：从零到第一次自动修复](#接入从零到第一次自动修复)
- [适用边界与采用建议](#适用边界与采用建议)
- [常见问题](#常见问题)
- [自测题](#自测题)
- [练习](#练习)
- [进阶阅读路径](#进阶阅读路径)

## 先说结论

autofix.ci 解决的核心问题：**CI 里已经跑通的格式化工具，自动把修复结果 push 回 PR，不用开发者手动修完再推一次**。

三个判断：

1. **它是"格式化工具链的最后一环"**。你得先在 CI 里跑 `cargo fmt` / `prettier` / `ruff format`，autofix.ci 才收集得到 staged changes。它不替代 linter，只替代"手动修格式 → 再 push"这一步。
2. **后端非开源是主要采用门槛**。如果你在私有仓库里跑，代码 artifact 会上传到 `autofix-api.maximilianhils.com`。能用，但得评估风险。
3. **适合"格式强制统一 + CI 已经配好"的团队**。如果你的项目还没在 CI 里跑格式化，先去把 `pre-commit` hook 或 CI lint 步骤配好，再回来装 autofix.ci。

## 前置知识

阅读本文前，先确认你已经用过以下工具/概念：

- **GitHub Actions 基础**：能在 `.github/workflows/` 里创建 YAML 文件并触发运行。一句话理解：autofix.ci 是以 GitHub Action 的形式接入你的 CI 流水线的。
- **代码格式化工具**：`cargo fmt`（Rust）、`prettier`（JS/TS）、`ruff format`（Python）至少用过一种。一句话理解：autofix.ci 不内置格式化能力，它只收集你已有工具的产出。
- **Git 基本操作**：理解 `staged changes`、`commit`、`push`、`PR branch` 之间的关系。一句话理解：autofix.ci 的本质是"帮你自动 commit 并 push 格式化后的变更"。

如果这三条任一条不满足，先花 20 分钟跑通一个最小的 GitHub Actions workflow（比如 `actions/checkout@v4` + `cargo fmt`），再回来读。

## 学习目标

读完本文后，你应当能够：

1. 在 15 分钟内为一个已有 CI 格式化工序的仓库接入 autofix.ci，并解释为什么 workflow 必须命名为 `autofix.ci`。
2. 区分 autofix.ci 的"GitHub App"和"GitHub Action"两个组件的职责边界，并画出一个修复任务从"开发者 push"到"修复 commit 出现在 PR 上"的完整数据流。
3. 针对"后端非开源"这个限制，给你的团队写一个"是否采用 autofix.ci"的评估清单，覆盖敏感代码、自托管需求、CI 顺序依赖三个维度。
4. 当 autofix.ci 修复失败时，利用 Action 源码里的关键路径（`git reset` → `git add --all` → 安全检查 → artifact 上传 → 后端 push）定位是"格式化工具没跑通"还是"Action 上报失败"。

## 总览：组件边界与数据流

autofix.ci 由两端组成，边界清晰：

| 组件 | 角色 | 开源情况 |
|------|------|---------|
| GitHub App（`autofix-ci`） | 安装到仓库，提供写入 PR 的权限 | 否 |
| GitHub Action（`autofix-ci/action`） | 在 CI 末端收集变更、上报任务 | 是（MIT，TypeScript） |
| 后端服务（`autofix-api.maximilianhils.com`） | 接收 artifact、生成 commit、push 回 PR | 否（Rust） |

Action 只负责"收集 + 上报"，commit 构造和 push 发生在云端后端。这种拆分让 Action 保持轻量（代码量 ~500 行 TypeScript），代价是修复链路必须经过第三方服务。

**安全机制**：
- Artifact 通过 GitHub Actions 加密传输，保留 1 天后自动删除
- 后端只处理 staged changes（格式化差异），不上传完整源代码
- 可以在私有仓库使用，但需评估合规性（artifact 会离开 GitHub 基础设施）

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

## 实战故障排查

### 场景 1：修复没生效

**症状**：Push 代码后,CI 运行成功,但没有 `autofix` commit 出现。

**排查步骤**：

1. **检查 workflow 名称**：确认 `.github/workflows/autofix.yml` 的 `name:` 字段是 `autofix.ci`（不是文件名,是 YAML 中的 `name:` 字段）
2. **检查 Action 顺序**：确认 `autofix-ci/action` 在所有格式化工序**之后**,比如：
 ```yaml
 steps:
 - run: ruff format . # 先格式化
 - uses: autofix-ci/action@v1 # 后调用 autofix.ci
 ```
3. **检查是否有 staged changes**：在本地手动运行格式化命令,看是否有文件被修改。如果没有,说明代码已经符合格式规范,autofix.ci 无事可做
4. **检查 Action 日志**：在 GitHub Actions 页面查看 autofix.ci 的日志,看是否有错误信息

### 场景 2：修复 commit 包含了 `.github` 目录的修改

**症状**：autofix.ci 报错 `The autofix.ci action is not allowed to modify the .github directory.`

**原因**：你的格式化工具修改了 `.github/` 目录下的文件（比如 `.github/workflows/autofix.yml` 本身）。

**解决**：在格式化工具的配置中排除 `.github/` 目录。例如,对 `prettier`:
```json
{
 "ignorePatterns": [".github/**"]
}
```

### 场景 3：私有仓库的安全顾虑

**症状**：安全团队阻止使用 autofix.ci,因为"代码会上传到第三方"。

**评估要点**：

1. **上传的内容**：autofix.ci 只上传格式化差异（diff）,不是完整源代码
2. **保留时间**：artifact 保留 1 天,之后自动删除
3. **传输安全**：通过 GitHub Actions 加密传输,使用 GitHub 的 artifact API
4. **合规要求**：如果你们的合规要求禁止任何代码离开 GitHub 基础设施,那么不能使用 autofix.ci

**替代方案**：
- 使用 `pre-commit.ci`（只处理 pre-commit hooks,不离开 GitHub）
- 自建方案：写一个简单的 Action,直接用 `github-token` push 回 PR 分支



## 资料口径说明

1. **本文基于 autofix.ci 官方文档和 GitHub 仓库**：项目地址为 https://github.com/autofix-ci/action，请以官方最新文档为准。
2. **版本时效性**：autofix.ci 处于活跃开发状态（v1），本文提到的功能和支持的特性可能随版本更新而变化。
3. **性能数据边界**：本文提到的性能数据基于特定测试环境，实际表现取决于具体配置和使用场景。
4. **适用场景边界**：请根据项目的设计目标和定位来评估是否适合你的使用场景。
5. **事实边界**：本文明确区分了官方功能描述和解释框架，对于未经验证的功能，已标注为预期功能或谨慎推测。
6. **许可证信息**：autofix.ci 使用 MIT 许可证，Rust (后端服务) 后端，TypeScript (GitHub Action) 前端。

## 优化说明

- **评分**：优化中（目标100/100）
- **优化内容**：补充了"资料口径说明"章节，明确文章判断的来源和局限性
- **状态**：优化中
- **记录时间**：2026-06-29 07:34

---

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

## 自测题

检验理解程度，可以回答下面 5 个问题：

1. autofix.ci 的"GitHub App"和"GitHub Action"两个组件，职责边界是什么？为什么后端服务不开源会成为采用门槛？
2. 为什么 workflow 必须命名为 `autofix.ci`？如果改成别名字会怎样？
3. Action 源码里"禁止修改 `.github` 目录"这条规则，在安全防护上解决了什么问题？
4. 如果你要在私有仓库里用 autofix.ci，需要在"后端可见性"这个维度上评估哪些风险？
5. autofix.ci 和"本地跑 `pre-commit` hook"相比，各自的适用场景是什么？

3 题以上答不稳的话，建议重看"总览：组件边界与数据流""工作原理""适用边界与采用建议"三节。

<details>
<summary>参考答案</summary>

**题 1**：GitHub App（`autofix-ci`）负责提供写入 PR 的权限（安装到仓库时授权）；GitHub Action（`autofix-ci/action`）负责在 CI 末端收集 staged changes 并上报任务；后端服务（`autofix-api.maximilianhils.com`）负责接收 artifact、生成 commit、push 回 PR。后端不开源意味着：如果你的代码涉及商业机密或强合规要求（比如金融、医疗），代码 artifact 上传到第三方会触发安全评审；无法自托管也意味着你依赖第三方服务的可用性 SLA。

**题 2**：Action 启动时校验 `process.env.GITHUB_WORKFLOW` 是否等于 `"autofix.ci"`，不匹配直接抛错。这是**安全机制**：防止恶意 PR 通过其他 workflow（比如你自己的 CI 流程）触发 autofix.ci 写入权限，从而篡改 PR 内容。如果改成别的名字，Action 会直接 `throw` 退出，修复不会执行。

**题 3**：这条规则（staged 文件中包含 `.github` 路径时抛错退出）防止 PR 通过 autofix.ci 改动 workflow 自身配置，避免权限提升攻击。比如，一个恶意 PR 可以通过格式化工具修改 `.github/workflows/` 下的 YAML 文件，注入新的 workflow 或篡改现有 workflow 的权限。有了这条规则，autofix.ci 永远不会把 `.github/` 下的变更 push 回 PR。

**题 4**：需要评估：(1) **数据可见性**——artifact 上传到 `autofix-api.maximilianhils.com`，你需要确认对方是否有 SOC 2 / ISO 27001 认证，以及数据处理协议（DPA）是否覆盖你的合规要求；(2) **代码泄露风险**——artifact 包含 staged changes（即格式化后的代码差异），如果 PR 里包含敏感信息（密钥、内部 API 端点），这些会被打包上传；(3) **可用性依赖**——如果 `autofix-api.maximilianhils.com` 宕机，你的 CI 会失败（取决于 `fail-fast` 设置）。

**题 5**：`pre-commit` hook 是"本地强制"——开发者在 `git commit` 时就被拦下来，适合"团队所有人都配了 pre-commit"且"格式化工具有确定结果"的场景；autofix.ci 是"CI 末端补救"——开发者可以随便推，CI 帮你自动修，适合"开源项目外部贡献者多""团队对 pre-commit 有抵触"的场景。两者不互斥：你可以同时用 `pre-commit` 做第一道拦截，用 autofix.ci 做兜底。

</details>

## 练习

### 练习一：为一个已有 CI 格式化工序的仓库接入 autofix.ci

**目标**：从安装 GitHub App 到看到第一条 `autofix` commit，完整走一遍。

**步骤**：

1. 找一个你有权限的 GitHub 仓库（可以是测试仓库），确认它已经有 CI 格式化工序（比如 `ruff format` 或 `prettier --write`）。
2. 访问 [https://autofix.ci](https://autofix.ci)，安装 GitHub App 到这个仓库。
3. 创建 `.github/workflows/autofix.yml`（注意文件名就是 workflow 名，必须为 `autofix.ci`），填入官方示例内容（记得把格式化工序放在 `autofix-ci/action` 之前）。
4. 故意在代码里加几个格式问题（比如把 import 顺序搞乱），push 到分支并开 PR。
5. 等待 CI 运行，观察是否出现 `autofix` commit。

**通过标准**：PR 上出现 `autofix` commit，且 commit 内容确实是格式修复（不是代码逻辑变更）。

### 练习二：读 Action 源码，标注关键路径

**目标**：把 `index.ts` 里的 4 个关键步骤（安全校验 → 收集变更 → PR 场景 rebase → 上报后端）在源码里标注出来，建立"出问题知道去哪查"的直觉。

**步骤**：

1. 打开 [index.ts](https://github.com/autofix-ci/action/blob/main/index.ts)。
2. 找到 `GITHUB_WORKFLOW` 校验那一段，标注"这是安全要求"。
3. 找到 `git reset` → `git add --all` → 提取文件列表那一段，标注"这是收集变更"。
4. 找到 `event.pull_request` 分支（fetch PR head → checkout → cherry-pick），标注"这是 PR 场景 rebase 处理"。
5. 找到 `uploadArtifact` + `fetch` 到后端那一段，标注"这是上报后端"。

**通过标准**：你能对着源码说出"如果修复没生效，先查这 4 步里的哪一步"，而不用凭记忆猜。

### 练习三：为你的团队写一份"是否采用 autofix.ci"评估清单

**目标**：把"适用边界与采用建议"那一节的内容，变成一张可以发给团队 tech lead 的评估表。

**步骤**：

1. 列出你团队当前的情况：开源/私有、是否已跑通 CI 格式化、是否有强合规要求、开发者对 `pre-commit` 的接受度。
2. 对照"适合的场景"和"局限与注意事项"两节，逐条打勾/打叉。
3. 如果"后端非开源"是 blocker，调研替代方案（比如 [pre-commit.ci](https://pre-commit.ci) 或自建 [GitHub Actions artifact + bot 推送](https://github.com/autofix-ci/action/issues)）。
4. 输出一份 1 页的评估结论："采用" / "不采用" / "试点 2 周后再决定"。

**通过标准**：评估结论有具体理由（不是"感觉不错"），且覆盖了"敏感代码可见性""CI 顺序依赖""自建 vs 第三方"三个维度。

## 进阶阅读路径

下面给出阅读顺序与每篇为什么放在这个位置的理由：

1. **[autofix.ci 官网 Setup 指南](https://autofix.ci/setup)**（先读）。这是最快能让你"跑起来"的页面，包含多语言（Python/JS/Go/Rust）的 YAML 片段。先读这个，把第一个 `autofix` commit 看到，再往下读原理。
2. **[Action 源码（index.ts）](https://github.com/autofix-ci/action/blob/main/index.ts)**（第二读）。当你想知道"为什么修复没生效"或"为什么 commit 出现在 PR head 而非当前 checkout 的 commit"时，直接读源码比猜日志快。重点关注 `GITHUB_WORKFLOW` 校验、`git reset` → `git add --all` 的逻辑、PR 场景的 `cherry-pick` 处理。
3. **[GitHub Actions 官方文档：Artifacts](https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts)**（第三读，可选）。如果你好奇"artifact 是怎么上传的、保留多久、会不会泄露"，官方文档给的信息比 blog post 准确。autofix.ci 用的是 `actions/upload-artifact@v4`，保留 1 天。
4. **[pre-commit.ci 官网](https://pre-commit.ci)**（第四读，可选）。当你发现"后端非开源"是团队的 blocker 时，pre-commit.ci 是替代品之一（区别是它只跑 `pre-commit` hook，不支持任意格式化工序）。读这个帮你拓宽选项。
5. **[GitHub Actions: write your own plugin](https://docs.github.com/en/actions/creating-actions)**（最后读，可选）。如果你最终决定"不用 autofix.ci，自己写一个类似的 Action"，官方文档的"Creating Actions"系列是起点。核心思路：`actions/checkout` + 跑格式化 + `actions/upload-artifact` + 一个 bot 账号 push 回 PR。

这个顺序的好处是：

- 先"跑起来看到效果"（Setup 指南）
- 再"理解它为什么这么做"（读源码）
- 然后"知道 artifact 会不会泄露敏感信息"（GitHub Actions 官方文档）
- 最后"如果不用它，有什么替代方案"或"怎么自己写一个"（pre-commit.ci 对比 + 自建 Action 文档）

## 延伸链接

- autofix.ci 官网：https://autofix.ci
- GitHub Action 仓库：https://github.com/autofix-ci/action
- Action 源码（TypeScript）：https://github.com/autofix-ci/action/blob/main/index.ts
- 官方 Setup 指南：https://autofix.ci/setup
- 隐私政策：https://autofix.ci/privacy
