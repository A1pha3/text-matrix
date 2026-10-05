---
title: "autofix.ci：让 Pull Request 自动化修复成为流水线标配"
date: 2026-05-16T03:07:35+08:00
slug: "autofix-ci-github-action-automated-pr-fixes"
github_repo: "autofix-ci/action"
source_key: "gh:autofix-ci/action"
description: "autofix.ci 是 GitHub App + GitHub Action 组合，在 CI 末端自动修复 PR 中的格式问题。本文解析其原理、安全模型、接入方法与采用边界。"
draft: false
categories: ["技术笔记"]
tags: ["GitHub Actions", "CI/CD", "代码格式化", "Pull Request"]
---

# autofix.ci：让 Pull Request 自动化修复成为流水线标配

autofix.ci 把 PR 里那些"修起来 30 秒、等起来半小时"的格式问题交给 CI 末端处理：开发者在 CI 中跑已有的格式化工具，autofix.ci 收集改动并 push 回 PR 分支。它适合对代码风格有强制要求、且不想在 review 中反复纠结格式的团队。它把仓库写权限交给一个闭源后端，所以采用前必须弄清它的安全模型和数据流向——这两件事正是本文的重点。

## 目录

- [先说结论](#先说结论)
- [前置知识](#前置知识)
- [学习目标](#学习目标)
- [总览：组件边界与数据流](#总览组件边界与数据流)
- [它在解决什么问题](#它在解决什么问题)
- [工作原理：一次修复任务的完整路径](#工作原理一次修复任务的完整路径)
- [安全模型：写权限如何被约束](#安全模型写权限如何被约束)
- [接入：从零到第一次自动修复](#接入从零到第一次自动修复)
- [实战故障排查](#实战故障排查)
- [适用边界与采用建议](#适用边界与采用建议)
- [常见问题](#常见问题)
- [自测题](#自测题)
- [练习](#练习)
- [进阶阅读路径](#进阶阅读路径)

## 先说结论

autofix.ci 解决的核心问题：**CI 里已经跑通的格式化工具，自动把修复结果 push 回 PR，不用开发者手动修完再推一次**。

三个判断：

1. **它是"格式化工具链的最后一环"**。你得先在 CI 里跑 `cargo fmt` / `prettier` / `ruff format`，autofix.ci 才收集得到改动。它不替代 linter，只替代"手动修格式 → 再 push"这一步。
2. **后端闭源是主要采用门槛，但安全设计在水准之上**。被改动文件的内容会经 autofix.ci 的服务器中转，私有仓库要评估这一点。缓解因素是它有一套明确的威胁模型：把 GitHub Actions runner 视为完全不可信，App 凭证不接触你的 workflow（详见"安全模型"一节）。
3. **适合"格式强制统一 + CI 已经配好"的团队**。如果你的项目还没在 CI 里跑格式化，先去把 `pre-commit` hook 或 CI lint 步骤配好，再回来装 autofix.ci。

## 前置知识

阅读本文前，先确认你已经用过以下工具/概念：

- **GitHub Actions 基础**：能在 `.github/workflows/` 里创建 YAML 文件并触发运行。一句话理解：autofix.ci 是以 GitHub Action 的形式接入你的 CI 流水线的。
- **代码格式化工具**：`cargo fmt`（Rust）、`prettier`（JS/TS）、`ruff format`（Python）至少用过一种。一句话理解：autofix.ci 不内置格式化能力，它只收集你已有工具的产出。
- **Git 基本操作**：理解 `staged changes`、`commit`、`push`、`PR branch` 之间的关系。抓住本质：autofix.ci 帮你自动 commit 并 push 格式化后的变更。

如果这三条任一条不满足，先花 20 分钟跑通一个最小的 GitHub Actions workflow（比如 `actions/checkout@v7` + `cargo fmt`），再回来读。

## 学习目标

读完本文后，你应当能够：

1. 在 15 分钟内为一个已有 CI 格式化工序的仓库接入 autofix.ci，并解释为什么 workflow 必须命名为 `autofix.ci`。
2. 区分 autofix.ci 的"GitHub App"和"GitHub Action"两个组件的职责边界，并画出一个修复任务从"开发者 push"到"修复 commit 出现在 PR 上"的完整数据流。
3. 向安全团队解释 autofix.ci 的威胁模型：App 凭证放在哪里、为什么 workflow 只拿只读权限、`.github` 目录为什么改不了。
4. 当修复没生效时，利用 Action 源码里的关键路径（`git reset` → `git add --all` → 安全检查 → artifact 上传 → 通知后端）定位是"格式化工具没跑出改动"还是"Action 上报失败"。

## 总览：组件边界与数据流

autofix.ci 由两端组成，边界清晰：

| 组件 | 角色 | 开源情况 |
|------|------|---------|
| GitHub App（`autofix-ci`） | 安装到仓库，持有唯一一套写凭证 | 否 |
| GitHub Action（`autofix-ci/action`） | 在 CI 末端收集改动、打包上报 | 是（MIT，TypeScript） |
| 后端服务（`autofix-api.maximilianhils.com`） | 拉取 artifact、校验内容、push 回 PR | 否（官方称用 Rust 编写） |

Action 只负责"收集 + 上报"，commit 构造和 push 发生在云端后端。这种拆分让 Action 保持极小——核心逻辑集中在一个 `index.ts` 文件里，经编译产出 `index.dist.js`，跑在 node24 运行时上。代价是修复链路必须经过第三方服务。

| 维度 | 数据 |
|------|------|
| GitHub App slug | `autofix-ci` |
| Action 仓库 | [autofix-ci/action](https://github.com/autofix-ci/action) |
| 最新 tag | v1.3.4（README 推荐用法是滚动的 `@v1` 大版本标签） |
| Action 体量 | 单个 `index.ts`，main 分支 24 次提交，最近一次推送 2026-04-19（GitHub API 2026-09-28 读数） |
| 主要语言 | TypeScript（Action）；后端为 Rust（[官方安全页](https://autofix.ci/security)原话："written in a memory-safe language that emphasizes correctness (Rust)"） |
| 许可证 | MIT（Action 仓库） |
| 平台支持 | 仅 GitHub Actions（官方 FAQ） |
| 作者 | Max Hils（官网 FAQ；安全页注明其有安全方向 CS PhD 背景） |

## 它在解决什么问题

PR 经常因为以下原因被阻塞：

- `cargo fmt` / `gofmt` / `prettier` / `ruff format` 报出的格式问题
- import 顺序错误或未使用的 import 残留
- 文档注释与代码不同步

这些问题修复成本极低，但传统流程需要：开发者本地修复 → 推送 → CI 通过 → 再次 review，一来一回消耗不少注意力。

autofix.ci 的做法是：在 CI 里运行你已有的格式化工具，然后自动把修复结果推回到 PR 分支。开发者接受或 review 修复即可，不必再手动处理琐碎的 style 问题。

## 工作原理：一次修复任务的完整路径

下面以一个 PR 触发场景为例，跟踪修复任务如何流过系统。理解这条路径有助于排查"为什么修复没生效"或"为什么 commit 出现在 PR head 而非当前 checkout 的 commit"。

```
开发者 push 代码
 ↓
CI 流水线运行（包含格式化工序）
 ↓
autofix-ci/action 在流水线末端被调用
 ↓
收集改动文件，打包成 autofix.json，上传为 artifact
 ↓
通知 autofix.ci 后端 API
 ↓
后端从 GitHub 拉取 artifact，校验内容，以 App 凭证 push 回 PR
```

举一个具体场景：开发者 Alice 向 PR #42 push 了一次提交，CI 跑 `prettier --write .` 修改了 3 个文件。Action 启动后，先 `git reset` 清空暂存区，再 `git add --all` 把 prettier 的改动全部暂存；接着校验这 3 个文件路径不包含 `.github`；PR 场景下还要先把修复 commit 挂到 PR head 之上；随后把改动打包成 `autofix.json`、上传为 GitHub Actions artifact，并 POST 通知 `autofix-api.maximilianhils.com`。后端从 GitHub 拉取这个 artifact、校验内容、以 autofix.ci App 的凭证把 commit push 到 PR #42 的分支——官方 FAQ 对这一步的原话是"fetches autofix.json from GitHub, validates its contents, and pushes a new commit to the pull request branch using its GitHub App credentials"。Alice 在 PR 上看到一条新的 `autofix` commit，review 或直接合并即可。

有一个容易误读的细节：**上报的不是 diff，而是被改动文件的完整内容**。源码里，每个变更文件被 `readFile` 读入后整体 base64 编码塞进 `fileChanges.additions`；被删除的文件只上报路径。所以 artifact 里携带的是"本次被格式化工具改过的那些文件的全文"，既不是差异片段，也不是整个仓库。

关键约束有两条：

1. **workflow 必须命名为 `autofix.ci`**。Action 启动时校验 `GITHUB_WORKFLOW` 环境变量，名称不匹配会直接抛错。这是安全机制，具体防的是什么攻击，见"安全模型"一节。
2. **Action 禁止修改 `.github` 目录**。一旦 staged 文件路径包含 `.github`，Action 会抛错退出。源码注释写明了分层逻辑："This is truly enforced on the server"——真正的强制校验在后端，Action 侧先检查只是为了让报错更即时、更好懂。

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

`core.fileMode=false` 忽略文件权限位变化（CI 环境中常见噪声），`core.quotepath=false` 让中文路径不被转义，`--no-renames` 防止重命名被识别为删除+新增，简化处理逻辑。若没有 staged 变更，Action 直接输出 `Nothing to do! ✨` 后正常退出——这也是排查"修复没生效"时要检查的第一种情况。

**3. PR 场景下的 rebase 处理**

当触发源是 Pull Request 时，Action 需要先将修复 commit 挂到 PR head 上（源码注释指向 [issue #12](https://github.com/autofix-ci/action/issues/12)）：

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

为什么需要这一步？CI runner checkout 的 commit 可能是 merge commit，`github.event.pull_request.head.sha` 与 `actions/checkout` 拉到的 ref 不一定一致。直接 push 修复会把 commit 挂错位置、污染 PR head 历史。Action 通过 fetch PR head → cherry-pick 修复的方式，保证最终 push 的 commit 直接落在 PR head 之上。

**4. 上报后端**

```typescript
// 构建修复请求：每个变更文件读入后整体 base64 编码
const fileChanges = { additions: [], deletions: [] };

// 打包为 autofix.json 并上传 artifact（保留 1 天）
await client.uploadArtifact("autofix.ci", [filename], ".", { retentionDays: 1 });

// 通知后端处理
const url =
 "https://autofix-api.maximilianhils.com/fix" +
 "?owner=" + encodeURIComponent(event.repository.owner.login) +
 "&repo=" + encodeURIComponent(event.repository.name);
```

URL 会按触发类型附加参数：PR 场景带 `&pull=<PR 编号>`，push 场景带 `&branch=<分支名>`。artifact 上传用的是 `@actions/artifact` 库（与 `actions/upload-artifact` 同一套 GitHub artifact API），并在代码里显式设置保留 1 天。Action 本身不接触修复逻辑，只完成"打包 + 通知"。

**一个反直觉的细节：修复成功启动时，workflow 会被标成失败**。源码里，Action 收到后端 `200` 响应后调用的是 `setFailed("✅ Autofix task started.")`——也就是说，修复任务正常提交后，当前这次运行反而会变红。这是有意为之的：红，意味着"修复正在路上"，提醒你别急着 review。等 autofix.ci App 把 `autofix` commit 推回 PR 后，新触发的那轮 CI 才会真正通过。所以看到 `✅ Autofix task started.` 时不用慌，那不是出错。

## 安全模型：写权限如何被约束

给一个第三方服务仓库写权限，决定权在你，但决策依据应该来自它的设计文档而非营销话术。autofix.ci 的[安全页](https://autofix.ci/security)给出了完整的威胁模型，要点如下。

**威胁模型的出发点：runner 完全不可信**。官方原话是把 GitHub Actions runner "treated as completely untrusted and potentially compromised"——也就是说，设计者假设你的 workflow 运行环境可能已经被攻破，再考虑如何不让攻击者借道拿到写权限。

**App 凭证不接触你的 workflow**。写 PR 的 token 只存在于 autofix.ci 后端，Action 自始至终拿不到它。官方 FAQ 的表述是"we keep autofix.ci's GitHub authentication token away from potentially untrusted actions"。这也是为什么接入时 workflow 自己只需要 `contents: read`（见"接入"一节）——push 这一步根本不经过你的 runner。

**API 只开一次写窗口**。安全页明确："The autofix.ci API only enables the workflow to update the current pull request once." 一次调用最多换来一次对当前 PR 的写入，不存在反复写的口子。

**workflow 名称校验防的是提权**。安全页给了具体攻击场景：假设仓库里有两个 workflow——正常的 `autofix.ci` 和一个被攻破的 `compromised_workflow`（权限锁死为 `contents: read`）。如果任意名称的 workflow 都能调用修复流程，攻击者就可以在 `compromised_workflow` 里伪造上传一个名为 `autofix.ci` 的 artifact，再手动调用 autofix API，借 App 的写权限改写 PR。要求"artifact 必须来自名为 `autofix.ci` 的 workflow"堵死了这条提权路径。该校验在服务端强制执行，Action 侧再查一遍只是为了立即报错。

**`.github` 目录整体拒改**。服务端规则：只要任何变更文件的路径包含 `.github`，整个修复直接拒绝——不是跳过那个文件，是全部不修。这条规则防止 PR 借 autofix.ci 之手改动 workflow 自身（比如注入新 workflow、放宽权限），消除一条权限提升通道。

**用 GraphQL API 而不是 git push**。后端不执行 `git checkout/apply/push`，而是调用 GitHub 的 GraphQL API 写入 commit。安全页解释：这样后端只需要处理一个 JSON 数据结构，不必对不可信仓库执行 git 命令（并举了 CVE-2021-21300 这类 git 相关漏洞作为背景）。这同时解释了后端为何无法自托管——修复逻辑、凭证、写入通道都在它的服务器上。

**权限清单**（官方安全页逐项给出用途）：

| 权限 | 用途 |
|------|------|
| `contents: write` | push 修复 commit |
| `actions: write` | 修复时取消同一 commit 关联的其他 workflow（对应 `fail-fast` 选项） |
| `pull-requests: write` | 给 PR 添加评论：外部贡献者未开启 "allow edits by maintainers" 时，用评论告知 PR 需要修复 |
| `checks: write` | 添加 commit status：修复失败时（例如被分支保护规则拦截）用 status 说明原因 |
| `metadata: read` | 所有 GitHub App 的强制要求 |

**防机器人死循环**。官方 FAQ：如果 PR 分支最后 4 个 commit 都是 bot 写的，autofix.ci 不再应用修复——避免两个自动修复机器人互相纠正、无限循环。

**兜底机制**。安全页承诺对"危及用户仓库完整性或机密性"的关键漏洞支付 bug bounty，金额最高为 autofix.ci 一个月的总收入。

这套设计不改变"后端闭源"这个事实，但它把"给不给权限"从一个笼统的信任问题，拆成了可以逐项评估的具体声明——这是阅读它的安全页比读十篇评测更有用的地方。

## 接入：从零到第一次自动修复

### 第一步：安装 GitHub App

访问 [autofix.ci](https://autofix.ci) 并安装应用到目标仓库。应用申请的权限是上一节那张表的 5 项，用途都写在[安全页](https://autofix.ci/security)里，安装前可以逐项核对。

### 第二步：创建 workflow 文件

在仓库根目录创建 `.github/workflows/autofix.yml`：

```yaml
name: autofix.ci  # needed to securely identify the workflow

on:
 push:
 branches: [main, master]
 pull_request:

jobs:
 autofix:
 runs-on: ubuntu-latest
 permissions:
 contents: read
 steps:
 - uses: actions/checkout@v7

 # ↓ 这里放你自己的格式化工序 ↓
 - run: cargo fmt

 # ↓ Action 必须在格式化工序之后调用 ↓
 - uses: autofix-ci/action@v1
 with:
 fail-fast: false
```

注意 `permissions: contents: read` 就够了：workflow 自己不做任何写操作，push 由后端以 App 凭证完成。把 workflow 权限收窄到只读，正是官方建议的加固手段之一。

> **安全加固建议**：官方建议同时做两件事——限制 runner 权限（如上），并把 Action 固定到特定 commit hash 而非 tag，以增强对供应链攻击的抵御。截至 2026-09-28，官方 setup 页给出的固定写法是 `autofix-ci/action@c5b2d67aa2274e7b5a18224e8171550871fc7e4a`。hash 会随版本滚动，接入时去官方 [setup 页](https://autofix.ci/setup)复制当前给出的值，别沿用本文或其他旧文里的例子。

### 第三步：配置参数（可选）

`action.yml` 声明了 3 个输入和 1 个输出：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `fail-fast` | `true` | 官方描述原话："Cancel all other workflows associated with a commit when fixing it."——修复某个 commit 时，取消它关联的其他 workflow |
| `commit-message` | 空 | 自定义修复 commit 的提交信息；为空时使用内置的 `autofix` |
| `comment` | 无 | 在 PR 中添加自定义评论 |
| 输出 `autofix_started` | `false` | 布尔值，表示修复任务是否已送达服务端、修复 commit 是否在路上 |

示例：

```yaml
- uses: autofix-ci/action@v1
 with:
 fail-fast: false
 commit-message: "style: auto-format code"
 comment: "autofix.ci 已自动修复格式问题"
```

### 多语言场景示例

官方 setup 页面（[autofix.ci/setup](https://autofix.ci/setup)）提供了大量开箱即用的 YAML 片段，以下是与官方一致、可直接粘贴的典型写法：

**Python + ruff**

```yaml
- uses: actions/checkout@v7
- run: pip install ruff
- run: ruff format .
- uses: autofix-ci/action@v1
```

**TypeScript / JavaScript + Prettier**

```yaml
- uses: actions/checkout@v7
- run: npx prettier --write .
- uses: autofix-ci/action@v1
```

**Rust + rustfmt**

```yaml
- uses: actions/checkout@v7
- run: cargo fmt --all
- uses: autofix-ci/action@v1
```

**Go + goimports**

```yaml
- uses: actions/checkout@v7
- run: go install golang.org/x/tools/cmd/goimports@latest
- run: goimports -w .
- uses: autofix-ci/action@v1
```

官方页面还有更多玩法：Rust 可以加 `cargo clippy --fix --workspace`，图片资产可以用 pngquant 压缩，甚至直接 `pre-commit run --all-files` 把整套 pre-commit hooks 的产出交给 autofix.ci 收集。所有示例的关键逻辑一致：先运行本地修复工具，再调用 autofix.ci。autofix.ci 本身不内置任何 linter 或 formatter，它只收集上一步产生的 staged 变更。

## 实战故障排查

### 场景 1：修复没生效

**症状**：push 代码后，CI 运行成功，但没有 `autofix` commit 出现。

**排查步骤**：

1. **检查 workflow 名称**：确认 `.github/workflows/autofix.yml` 的 `name:` 字段是 `autofix.ci`（不是文件名，是 YAML 里的 `name:` 字段）
2. **检查 Action 顺序**：确认 `autofix-ci/action` 在所有格式化工序**之后**，比如：
 ```yaml
 steps:
 - run: ruff format . # 先格式化
 - uses: autofix-ci/action@v1 # 后调用 autofix.ci
 ```
3. **检查是否真的产生了变更**：在本地手动运行格式化命令，看是否有文件被修改。没有的话，说明代码已经符合格式规范，autofix.ci 无事可做——源码对这种情况的处理就是直接退出（`Nothing to do! ✨`）
4. **检查 Action 日志**：在 GitHub Actions 页面查看 autofix.ci 的运行日志，看是否有错误信息

### 场景 2：报错"not allowed to modify the .github directory"

**症状**：autofix.ci 报错 `The autofix.ci action is not allowed to modify the .github directory.`

**原因**：你的格式化工具修改了 `.github/` 目录下的文件（比如 `.github/workflows/autofix.yml` 本身，或 `.github` 下的 Markdown 文档）。

**解决**：在格式化工具的忽略配置里排除 `.github/`。以 Prettier 为例，在仓库根目录建一个 `.prettierignore`（语法与 `.gitignore` 相同）：

```
.github/
```

注意别用 `ignorePatterns` 之类的配置键——那是 ESLint 的字段，Prettier 的忽略只能通过 `.prettierignore` 文件（外加 `// prettier-ignore` 行内注释）控制。其他工具同理：ruff 用 `extend-exclude`，思路都一样——别让格式化工具碰 `.github`。

### 场景 3：私有仓库的安全顾虑

**症状**：安全团队阻止使用 autofix.ci，理由是"代码会上传到第三方"。

**评估要点**（数据流以源码和官方 FAQ 为准）：

1. **上传的内容**：被格式化工具改动的文件的完整内容（base64 打包进 `autofix.json`），不是 diff，也不是整个仓库；被删除的文件只上报路径
2. **存放位置**：artifact 存在 GitHub 侧，保留 1 天后自动删除（源码 `retentionDays: 1`）
3. **处理位置**：autofix.ci 后端从 GitHub 拉取这个文件并处理——也就是说，变更内容确实会经过 autofix.ci 的服务器，而非全程留在 GitHub 基础设施内
4. **官方声明**：隐私政策原话是 "We do not collect, transmit, distribute, or sell your personal data."（注意它声明的是个人数据；代码数据的保留策略页面没有单独说明）

**替代方案**：

- **pre-commit.ci**：同样是第三方托管服务，跑你 `.pre-commit-config.yaml` 里的 hooks，开源仓库免费、私有仓库收费——代码同样要离开 GitHub 基础设施，安全评估的维度类似
- **pre-commit.ci lite**：同一家的轻量版，hooks 跑在你自己的 GitHub Actions runner 上，自动修复不经过第三方服务器
- **自建方案**：写一个 Action，格式化后直接用凭证 commit 并 push 回 PR。注意一个平台特性：用仓库自带的 `GITHUB_TOKEN` 做的 push 不会再触发新的 workflow 运行（GitHub 防递归的固定行为），要么接受"修复 commit 不触发 CI"，要么走 GitHub App 或个人访问令牌——而后者恰恰是 autofix.ci 安全页点名批评的高危做法（"passing around personal access tokens are highly dangerous"）

## 适用边界与采用建议

### 适合的场景

- **格式强制统一**：团队对 code style 有明确要求，不想在 review 中纠结格式化问题
- **减少 PR 轮次**：避免"CI 失败→修复→再 review"的琐碎等待
- **多语言项目**：同一个 workflow 可以串联多种修复工具（Python 用 ruff、JS 用 prettier、Rust 用 rustfmt）
- **PR 贡献引导**：开源项目可以用 autofix.ci 降低外部贡献者的格式门槛——贡献者没开 "allow edits by maintainers" 时，App 还会用 PR 评论提醒
- **fork PR 场景**：fork 来的 PR 天然没有写权限，官方的设计动机之一就是"给 fork PR 提供严格限死的自我更新能力"，这比在 `pull_request_target` 里传个人访问令牌安全得多（官方 FAQ 原话称后者 "highly dangerous to outright insecure"）

### 优势

- **零侵入**：不需要改代码，不需要 pre-commit hook，不需要额外的本地配置
- **威胁模型完整且公开**：runner 不可信假设、一次性写窗口、凭证隔离、`.github` 禁改，全部成文于官方安全页，可逐项审计
- **PR 与 push 双场景**：对两种触发做了不同处理（PR 场景 rebase onto PR head）
- **隐私声明明确**："We do not collect, transmit, distribute, or sell your personal data."（[隐私政策](https://autofix.ci/privacy)）

### 局限与注意事项

- **后端闭源且无法自托管**：修复的校验与写入都发生在 `autofix-api.maximilianhils.com`，不支持其他 git 平台（官方 FAQ：仅支持 GitHub Actions）
- **不修改 `.github`**：workflow 配置文件本身永远不会被 autofix.ci 修复（服务端强制）
- **上传的是文件全文**：被改动的文件会以完整内容形式经过第三方服务器，含密钥或敏感逻辑的仓库需自行评估
- **职责单一**：不做代码质量判断，只负责修复你 CI 中已经运行的工具所产生的变更
- **依赖 CI 顺序**：Action 必须放在所有格式化工序之后调用

### 采用建议

引入前建议按以下顺序评估：

1. **先确认格式工具链稳定**：autofix.ci 放大已有工具的效果，工具链本身有问题会被同步放大。先在本地或 pre-commit hook 中跑通 `ruff format` / `prettier` / `rustfmt` 等基础工具。
2. **按安全模型逐项过审**：拿"安全模型"一节的清单（上传内容、存放位置、处理位置、权限清单）和安全团队对表，比笼统讨论"可不可信"高效得多。合规上不允许代码离开 GitHub 基础设施的团队，直接看替代方案。
3. **小范围试点**：先在一个仓库跑两周，观察 commit 噪声和 review 流程变化，再推广到组织级别。
4. **配合分支保护**：把 autofix.ci workflow 加入必需检查，避免 PR 在修复完成前被合并。

## 常见问题

**Q: 修复 commit 会不会和我的原始 commit 混在一起造成历史污染？**

不会。autofix.ci 的修复以独立 commit 形式 push 到 PR 分支，消息默认为 `autofix`（可自定义）。最终合并时可以 squash 或 rebase，保持干净的 master 历史。

**Q: 可以指定只对特定文件类型自动修复吗？**

这是 CI 层面的设计选择。你可以在 workflow 中只对特定目录或文件类型运行格式化工具，autofix.ci 会自动收集该步骤产生的 staged 变更。

**Q: 仓库里有 dependabot、renovate 这类机器人，会互相打架吗？**

不会死循环。官方 FAQ 的规则：如果分支最后 4 个 commit 都是 bot 写的，autofix.ci 不再应用修复，从机制上避免两个自动修复机器人互相纠正。

**Q: 如何禁用 autofix.ci 对某个 PR 的自动修复？**

暂时没有 per-PR 的开关。如果需要临时禁用，可以将对应 workflow 的 `autofix-ci/action` step 注释掉，或在 workflow 中加入条件判断。

**Q: 修复"失败"了怎么办？**

先区分两种情况。如果日志显示 `✅ Autofix task started.`，那是**成功信号**，workflow 变红是设计使然（见"工作原理"一节），等 `autofix` commit 到达即可。如果后端真的返回错误，Action 会输出错误信息并把这次运行标为失败，同时用 `git diff --staged` 打印需要手动处理的改动。

## 自测题

检验理解程度，可以回答下面 5 个问题：

1. autofix.ci 的"GitHub App"和"GitHub Action"两个组件，职责边界是什么？App 申请的 5 项权限各自用来做什么？
2. 为什么 workflow 必须命名为 `autofix.ci`？官方描述的攻击场景是什么样的？
3. 为什么后端要用 GitHub 的 GraphQL API 写入 commit，而不是 `git push`？这个选择带来什么副作用？
4. 如果你要在私有仓库里用 autofix.ci，需要向安全团队讲清哪些数据流事实？
5. autofix.ci、"pre-commit hook"、"自建 Action 直接 push" 三者相比，各自的适用场景是什么？

3 题以上答不稳的话，建议重看"总览""工作原理""安全模型"三节。

<details>
<summary>参考答案</summary>

**题 1**：GitHub App（`autofix-ci`）持有唯一一套写凭证，负责最终 push 修复 commit；GitHub Action（`autofix-ci/action`）负责在 CI 末端收集变更、打包上报，自身不持有写权限。5 项权限（官方安全页）：`contents: write` push 修复 commit；`actions: write` 修复时取消同一 commit 关联的其他 workflow；`pull-requests: write` 给 PR 加评论提醒贡献者；`checks: write` 添加 commit status 说明修复失败原因；`metadata: read` 是所有 GitHub App 的强制要求。

**题 2**：Action 启动时校验 `process.env.GITHUB_WORKFLOW` 是否等于 `"autofix.ci"`，不匹配直接抛错；服务端也做同样校验。官方攻击场景：仓库里有个权限锁死为 `contents: read` 的 `compromised_workflow` 被攻击者执行了代码，若任意 workflow 都能触发修复，攻击者就能从这个 workflow 伪造上传名为 `autofix.ci` 的 artifact 并手动调用 autofix API，借 App 凭证获得仓库写权限。命名要求把"artifact 必须来自 autofix.ci workflow"变成了服务端强制条件，堵死这条提权路径。

**题 3**：安全页的解释：处理 git 数据意味着对不可信仓库执行 `git checkout/apply/push`，这类命令历史上有过漏洞（页面举了 CVE-2021-21300）；改用 GraphQL API 后，后端只需要处理一个 JSON 数据结构。副作用是修复链路深度绑定 GitHub、且核心逻辑在后端闭源实现里，第三方无法自托管或移植到其他平台。

**题 4**：至少四点：(1) 上传内容——被格式化工具改动的文件的完整内容（base64），不是 diff，不是全仓库；(2) 存放——artifact 存 GitHub，保留 1 天自动删除；(3) 处理——autofix.ci 后端从 GitHub 拉取并处理，变更内容会经过第三方服务器；(4) 声明边界——隐私政策承诺不收集、传输、出售个人数据，但代码数据没有单独的保留说明。合规红线：要求代码完全不出 GitHub 基础设施的团队不可用。

**题 5**：`pre-commit` hook 是"本地拦截"——`git commit` 时就挡下来，适合"人人都配了 hook"且工具结果确定的团队；autofix.ci 是"CI 末端兜底"——随便推，CI 自动修，适合开源项目和外部贡献者多的仓库，且它的安全设计（凭证隔离、一次性写窗口）比在 `pull_request_target` 里发个人访问令牌安全得多；自建 push 最可控、无第三方参与，但要自己处理 `GITHUB_TOKEN` 不触发新 CI 的问题，用 PAT/App 又引入新的凭证管理负担。三者不互斥：hook 拦大头，autofix.ci 兜底，是常见组合。

</details>

## 练习

### 练习一：为一个已有 CI 格式化工序的仓库接入 autofix.ci

**目标**：从安装 GitHub App 到看到第一条 `autofix` commit，完整走一遍。

**步骤**：

1. 找一个你有权限的 GitHub 仓库（测试仓库即可），确认它已经有 CI 格式化工序（比如 `ruff format` 或 `prettier --write`）。
2. 访问 [https://autofix.ci](https://autofix.ci)，安装 GitHub App 到这个仓库。
3. 创建 `.github/workflows/autofix.yml`。关键在于把 YAML 里的 `name:` 字段写成 `autofix.ci`（文件名无关紧要），再填入官方示例内容，并把格式化工序放在 `autofix-ci/action` 之前。
4. 故意在代码里加几个格式问题（比如把 import 顺序搞乱），push 到分支并开 PR。
5. 等待 CI 运行，观察第一次运行变红、`autofix` commit 到达、第二轮 CI 变绿的完整过程。

**通过标准**：PR 上出现 `autofix` commit，且 commit 内容确实是格式修复（不是代码逻辑变更）；你能说出为什么第一轮 CI 是红的。

### 练习二：读 Action 源码，标注关键路径

**目标**：把 `index.ts` 里的 4 个关键步骤（安全校验 → 收集变更 → PR 场景 rebase → 上报后端）在源码里标注出来，建立"出问题知道去哪查"的直觉。

**步骤**：

1. 打开 [index.ts](https://github.com/autofix-ci/action/blob/main/index.ts)。
2. 找到 `GITHUB_WORKFLOW` 校验那一段，标注"这是安全要求"。
3. 找到 `git reset` → `git add --all` → 提取文件列表那一段，标注"这是收集变更"。
4. 找到 `event.pull_request` 分支（fetch PR head → checkout → cherry-pick），标注"这是 PR 场景 rebase 处理"。
5. 找到 `uploadArtifact` + `fetch` 到后端那一段，标注"这是上报后端"，并确认 `additions` 里放的是文件全文还是 diff。

**通过标准**：你能对着源码说出"如果修复没生效，先查这 4 步里的哪一步"，而不用凭记忆猜。

### 练习三：为你的团队写一份"是否采用 autofix.ci"评估清单

**目标**：把"安全模型"和"适用边界"两节的内容，变成一张可以发给团队 tech lead 的评估表。

**步骤**：

1. 列出你团队当前的情况：开源/私有、是否已跑通 CI 格式化、是否有强合规要求、开发者对 `pre-commit` 的接受度。
2. 对照安全模型的逐项声明（上传内容、存放位置、处理位置、权限清单、威胁模型）和"局限与注意事项"，逐条打勾/打叉。
3. 如果"变更内容经过第三方服务器"是 blocker，调研替代方案：pre-commit.ci、pre-commit.ci lite（跑在自己的 runner 上）、自建 Action。
4. 输出一份 1 页的评估结论："采用" / "不采用" / "试点 2 周后再决定"。

**通过标准**：评估结论有具体理由（不是"感觉不错"），且覆盖了"数据流向""workflow 权限收敛""自建与第三方对比"三个维度。

## 进阶阅读路径

下面给出阅读顺序与每篇为什么放在这个位置的理由：

1. **[autofix.ci 官网 Setup 指南](https://autofix.ci/setup)**（先读）。这是最快能让你"跑起来"的页面，包含多语言的 YAML 片段和当前的 commit hash 固定值。先读到看到第一个 `autofix` commit，再往下读原理。
2. **[Action 源码（index.ts）](https://github.com/autofix-ci/action/blob/main/index.ts)**（第二读）。当你想知道"为什么修复没生效"或"为什么 commit 出现在 PR head 而非当前 checkout 的 commit"时，直接读源码比猜日志快。重点关注 `GITHUB_WORKFLOW` 校验、`git reset` → `git add --all` 的逻辑、PR 场景的 `cherry-pick` 处理，以及 `additions` 的文件内容编码方式。
3. **[autofix.ci 安全页](https://autofix.ci/security)**（第三读）。本文"安全模型"一节的原始出处：威胁模型、workflow 命名校验的攻击场景、权限清单、GraphQL 设计理由、bug bounty 政策都在这里。给安全团队做评估时，直接引用这一页。
4. **[GitHub Actions 官方文档：Store and share data with workflow artifacts](https://docs.github.com/en/actions/tutorials/store-and-share-data)**（第四读，可选）。如果你好奇"artifact 是怎么上传的、保留多久"，官方教程比博客文章准确。autofix.ci 经 `@actions/artifact` 库上传，保留 1 天。
5. **[pre-commit.ci 官网](https://pre-commit.ci)**（最后读，可选）。当"后端闭源"是团队 blocker 时的替代品之一：它跑 `.pre-commit-config.yaml` 里的 hooks，开源仓库免费；另有 lite 版把 hooks 放到你自己的 runner 上跑。读这个帮你拓宽选项。

这个顺序的好处是：

- 先"跑起来看到效果"（Setup 指南）
- 再"理解它为什么这么做"（读源码）
- 然后"搞清楚写权限给了谁、数据流向哪"（安全页）
- 最后"如果不用它，有什么替代方案"（pre-commit.ci 对比）

## 延伸链接

- autofix.ci 官网：https://autofix.ci
- GitHub Action 仓库：https://github.com/autofix-ci/action
- Action 源码（TypeScript）：https://github.com/autofix-ci/action/blob/main/index.ts
- 官方 Setup 指南：https://autofix.ci/setup
- 官方安全页（威胁模型与权限清单）：https://autofix.ci/security
- 隐私政策：https://autofix.ci/privacy
