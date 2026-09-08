---
title: "actions/checkout v7 拆解：GitHub 最常用的 Action 如何用 default-deny + ESM 迁移收窄 pwn request 攻击面"
date: 2026-07-17T02:58:00+08:00
lastmod: 2026-09-07T00:00:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["GitHub Actions", "Security"]
description: "actions/checkout v7（2026-06-18 发布）是 GitHub Actions 生态最高频使用的 action，8.8k+ stars、MIT、TypeScript。v7 核心变化是默认拒绝 fork PR 在 pull_request_target / workflow_run 触发器下被 checkout（pwn request 攻击面），并完成 ESM 模块化迁移；该安全加固已 backport 到 v6.1.0 / v5.1.0 / v4.4.0 / v3.7.0 / v2.8.0，自 2026-07-20 起对所有受支持 major 强制执行。"
slug: "actions-checkout-v7-pwn-request-mitigation-deep-dive"
github_repo: "actions/checkout"
author: text-matrix
---

## 一句话判断

**actions/checkout** 是 GitHub Actions 生态里被引用次数最多的 action——几乎每个 CI workflow 的第一行都是 `uses: actions/checkout@v4`。它做的事表面简单：在 runner 上把仓库克隆到 `$GITHUB_WORKSPACE`。但 v7（2026-06-18 发布）是一次被安全事件驱动的硬性升级：**默认拒绝 fork pull request（fork 即派生、PR 即拉取请求）的代码在 `pull_request_target` / `workflow_run` 触发器下被 checkout——也就是"pwn request"漏洞类别的入口**。同时完成了从 CJS 到 ESM 的模块化迁移。到 2026-07-20，这个安全加固又随 v6.1.0 / v5.1.0 / v4.4.0 / v3.7.0 / v2.8.0 backport 回全部受支持的旧版本，GitHub 在当日对所有受支持的 checkout major 强制执行新默认行为——所以即使你还在 `@v4`，行为也已经变了。

如果你维护任何会被外部贡献者提 PR 的 GitHub 仓库，这篇值得读完。

---

## 系统地图

```text
┌────────────────────────────────────────────────────────────────────────┐
│                      actions/checkout v7 内部                           │
│                                                                        │
│  ┌────────────────────┐  ┌──────────────────────────────────────┐     │
│  │ 入口与配置          │  │ Git 操作层                           │     │
│  │ src/main.ts        │  │ git-command-manager.ts               │     │
│  │ src/input-helper.ts│  │ git-source-provider.ts               │     │
│  │ src/state-helper.ts│  │ git-source-settings.ts               │     │
│  │ workflow-context-  │  │ ref-helper.ts                         │     │
│  │   helper.ts        │  │ git-directory-helper.ts               │     │
│  └────────┬───────────┘  │ fs-helper.ts                          │     │
│           │              └──────────────────┬───────────────────┘     │
│           ▼                                 │                          │
│  ┌────────────────────┐                     │                          │
│  │ 安全检查（v7 新增）│                     │                          │
│  │ unsafe-pr-checkout-│                     │                          │
│  │   helper.ts        │                     │                          │
│  └────────┬───────────┘                     │                          │
│           │                                 │                          │
│           ▼                                 ▼                          │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │ 凭证与远端适配层                                             │    │
│  │ git-auth-helper.ts（PAT / SSH / OAuth App / GitHub App）      │    │
│  │ github-api-helper.ts（Git 协议 fallback，REST API）           │    │
│  │ url-helper.ts（GHES / GitHub.com URL 适配）                   │    │
│  │ git-version.ts（Git ≥ 2.18 优先，旧版 REST API 兜底）         │    │
│  └──────────────────────┬───────────────────────────────────────┘    │
│                          │                                            │
│                          ▼                                            │
│  ┌───────────────────────────────────────────┐  ┌───────────────────┐ │
│  │ 杂项                                       │  │ ADR（决策记录）   │ │
│  │ retry-helper.ts                            │  │ adrs/0153-...    │ │
│  │ regexp-helper.ts                           │  │ （决策归档）      │ │
│  │ misc/                                      │  │                  │ │
│  └───────────────────────────────────────────┘  └───────────────────┘ │
└──────────────────────────────┬─────────────────────────────────────────┘
                               ▼
                 ┌─────────────────────────────────────────────┐
                 │ 下游消费者                                   │
                 │ $GITHUB_WORKSPACE/ ← 仓库被 checkout 到这里 │
                 │ 凭证存 $RUNNER_TEMP 独立文件（v6+）          │
                 │ post-job 时清理（默认）                     │
                 └─────────────────────────────────────────────┘
```

v7 最重要的路径：**入口 main.ts → 输入解析（`input-helper.ts`，安全检查挂在这里）→ git command manager → 凭证/远端适配 → 落盘 `$GITHUB_WORKSPACE`**。安全检查被提为独立模块 `unsafe-pr-checkout-helper.ts`，是 pwn request 缓解的物理位置；`workflow-context-helper.ts` 只负责从事件 payload 里读组织 ID，给凭证层用，不参与 fork 判定。

---

## 边界与角色划分

### 5 条不变项

| 维度 | 不变项 | 含义 |
|------|--------|------|
| 运行时 | ESM + Node.js 24 | v7 起 action 本体编译为 ESM，运行在 node24 runtime；v4–v6 仍是 CJS |
| 默认行为 | fork PR 代码在 `pull_request_target` / `workflow_run` 下被拒 | v7 引入 `allow-unsafe-pr-checkout` 输入，默认 `false`；v6.1.0 / v5.1.0 / v4.4.0 已 backport 同一行为 |
| 默认 fetch depth | 1（commit，即单次提交） | 全历史需 `fetch-depth: 0`；tags 需 `fetch-tags: true` |
| 凭证管理 | 默认持久化 + post-job 清理 | v6 起凭证存到 `$RUNNER_TEMP` 单独文件，不再直接写 `.git/config` |
| 外部贡献 | 不接受 | README 明确写 "right now we are not taking contributions" |

### 它明确不做的事

- **不**做 Git LFS push（推送），只 fetch；`lfs: true` 是拉取时行为。
- **不**管理 GPG signing。commit signing 由用户后续自己完成。
- **不**做 submodules 自动递归里的 LFS / credentials 嵌套传递。
- **不**内置 GHES / 第三方 Git 服务器的 token（令牌）注入；用户必须自己通过 `github-server-url` + 自定义 token。
- **不**替代 `git` 命令行工具（CLI）。它在 runner 上调用 `git`，本身不重写 Git 协议。

这些边界把 checkout 的职责收得很窄：它只负责把代码取下来、落好凭证，签名、推送、构建这些后续动作都留给用户自己的 step。

---

## 关键机制：v7 的实际变化

v7 最核心的变化有两处：default-deny 拒绝 fork PR checkout，以及 ESM 模块化迁移。下面两小节展开它们；凭证存储与权限最小化并非 v7 新引入，但它们是决定安全是否真正奏效的持续设计，单独列出。

### 1. Default-Deny：pwn request 缓解

**问题定义**：v7 之前，actions/checkout 允许 workflow 在 `pull_request_target` 触发器下把 fork PR 的代码 checkout 到 runner。

**为什么这是安全问题**：

- `pull_request_target` workflow 跑在 **base 仓库**的 context 里，能访问 `secrets`、使用 base 仓库的 `GITHUB_TOKEN`。
- fork PR 的代码默认是 untrusted。
- 经典踩坑写法是第一步 `actions/checkout` 时显式传 `ref: ${{ github.event.pull_request.head.sha }}` 或 `ref: refs/pull/N/merge`，把 fork 代码落盘后紧接着 `run: npm ci && npm test` 执行它——攻击者在 fork 仓库里放恶意 `package.json` 的 `postinstall` 脚本，CI 跑起来就拿到了 base 仓库 secret 的访问权。
- 这就是 GitHub Security Lab 命名的 **"pwn request"** 攻击面。GitHub 官方公告称 `pull_request_target` 是 "one of the most commonly misused triggers in GitHub Actions"。

**攻击面从哪来**：关键不在 checkout 本身，而在 job 运行的 context。`pull_request` 触发器始终以 PR 属主（fork 仓库）的 context 运行，README 明确声明它不向 fork 提供 secrets，`GITHUB_TOKEN` 也是只读；而 `pull_request_target` 以 base 仓库的 context 运行，能拿到 base 仓库的 `GITHUB_TOKEN` 与 secrets，head 却可以指向不可信的 fork 代码。checkout 一旦把 fork 代码落盘，就给了攻击者一个"在拥有 secrets 的 runner 上执行任意代码"的入口。

**v7 的修复**：

```yaml
- uses: actions/checkout@v7
  with:
    allow-unsafe-pr-checkout: false  # 默认值，显式写出来便于 code review
```

`action.yml` 里这个输入的官方描述直说了它防什么："fetching and executing a fork's code in that trusted context commonly leads to 'pwn request' vulnerabilities"，并要求 opt-in 前先阅读 [gh.io/securely-using-pull_request_target](https://gh.io/securely-using-pull_request_target)。GitHub 公告还解释了命名意图：这个名字故意起得刺眼，方便在 code review 和静态分析里一眼扫出来。

**判定逻辑（读自 v7.0.1 源码）**：检查挂在 `input-helper.ts` 的输入解析末尾，分两层。

第一层是短路：如果 checkout 的就是触发 workflow 的同一个仓库、且没有显式传 `ref`，源码注释写明这种"默认自 checkout"解析出的 ref/commit 由 GitHub 按当前事件设定，属于可信范围——**直接跳过检查，行为与 v6 完全一致**。所以 `pull_request_target` 下无参数的 `actions/checkout`（拿到的是 base 分支的 commit）不受任何影响。

第二层只对自定义了 `repository` / `ref` / `commit` 的调用生效，`unsafe-pr-checkout-helper.ts` 的 `assertSafePrCheckout` 依次判断：

1. `allow-unsafe-pr-checkout: true` → 直接放行。
2. 当前事件不是 `pull_request_target` / `workflow_run`（`workflow_run` 还要求内层事件以 `pull_request` 开头）→ 放行。
3. PR head 仓库与 base 仓库同属主（不是 fork）→ 放行。
4. checkout 的输入指向 fork PR 代码，三个模式命中任意一个即拒绝：
   - `repository` 解析后指向 fork 仓库（不区分大小写比较 full name）；
   - `ref` 匹配 `^refs/pull/[0-9]+/(?:head|merge)$`；
   - 解析出的 commit 是 PR 的 head SHA 或 merge commit SHA。

拒绝时抛出的错误信息把原因和出路一次讲完：

```text
Refusing to check out fork pull request code from a 'pull_request_target' workflow.
This workflow runs with the base repository's GITHUB_TOKEN, secrets, default-branch
cache scope, and runner access. Fetching and executing a fork's code in that trusted
context commonly leads to "pwn request" vulnerabilities. To opt in, review the risks
at https://gh.io/securely-using-pull_request_target and set 'allow-unsafe-pr-checkout: true'
on the actions/checkout step.
```

**为什么是 default-deny 而不是 default-allow + 文档提示**：历史教训。v4–v6 期间这个风险被无数次安全公告强调，但总有人不看文档。default-deny 把"易错操作"变成"显式 opt-in"，大幅降低误配概率。

**2026-07-20 起，这个默认对所有受支持版本生效**。GitHub 官方公告（[Safer pull_request_target defaults for GitHub Actions checkout](https://github.blog/changelog/2026-06-18-safer-pull_request_target-defaults-for-github-actions-checkout/)）把 default-deny 行为 backport 到所有受支持的 checkout major，并在 2026-07-20 强制执行（原定 07-16，公告在 07-15 的编辑注记里宣布推迟）；同日发布 v6.1.0、v5.1.0、v4.4.0、v3.7.0、v2.8.0，正式带上 `allow-unsafe-pr-checkout` 输入（v4.4.0 的 `action.yml` 已核实含该输入）。v1 是唯一明确不收此变更的版本。这对存量用户意味着：

- 固定到浮动 major tag（`actions/checkout@v2` 到 `@v6`）的 workflow 自动拿到新行为——checkout 输入指向 fork PR 代码时直接 fail。
- 固定到具体 SHA / minor / patch（如 `@v6.0.3`）的 workflow 不受影响，需 Dependabot 或手动升级到含修复的版本。

**显式 opt-in 的代价**：在真正需要 checkout fork 代码的场景（比如给 fork 仓库做 lint）必须显式声明：

```yaml
- uses: actions/checkout@v7
  with:
    allow-unsafe-pr-checkout: true
    # 强烈建议：
    # 1. 不要用 GITHUB_TOKEN，直接 checkout
    # 2. 不要在后续 step 里用这个代码执行 npm ci / make 等
    # 3. 参考 README 顶部 v7 "What's new" 段官方安全指南
```

### 2. ESM 迁移

**变更动机**：README What's new 一句话讲清——"Migrated `actions/checkout` to ESM to support new versions of the `@actions/*` packages"。新版 `@actions/core`（v3.x）、`@actions/tool-cache`（v4.x）只发布 ESM，旧模块体系接不上。

**v7 的具体改动**：`package.json` 顶层 `"type": "module"`，`engines` 要求 Node.js ≥ 24；CHANGELOG 里 v7.0.0 只有两条——核心安全变更 "Block checking out fork PR for pull_request_target and workflow_run"（PR [#2454](https://github.com/actions/checkout/pull/2454)）和 "Various dependency updates"。ESM 迁移与依赖升级打包在后一条里，没有独立 PR 条目。

**对用户的影响**：

- 对 workflow 作者基本无感。runner 按 `node24` 加载 action 打包好的 `dist/index.js`，ESM 是 action 内部实现细节；你自己仓库里的 JS step、依赖版本都不受影响。
- 真正需要关心的是 fork checkout 源码做二次开发的人：v7 起要用 ESM 写法（`import` 而非 `require`），且本地环境需要 Node.js 24。
- 这条改动本身不是安全问题，是 dependency hygiene；同批依赖更新含已知漏洞的安全修复。

**v7.0.1（2026-07-20 发布）的后续修正**：

- 默认 checkout 跳过安全检查（[#2518](https://github.com/actions/checkout/pull/2518)），把默认路径的开销降到最低——也就是上文判定逻辑的第一层短路。
- `branch`（分支）参数只裁剪 ASCII 空白（[#2521](https://github.com/actions/checkout/pull/2521)）、`git config --unset` 传值做转义（[#2530](https://github.com/actions/checkout/pull/2530)），属于边界加固。
- 该版本与 v6.1.0 / v5.1.0 / v4.4.0 同日发布，各 major 的安全行为保持一致。

### 3. 凭证存储的演化（v6 → v7）

v6.0.0 引入的 `persist-credentials` 重构（PR [#2286](https://github.com/actions/checkout/pull/2286) "Persist creds to a separate file"），v7 沿用：

| 版本 | token 存储位置 |
|---|---|
| v4 / v5 | `.git/config` 里的 `http.extraHeader` / `url.<base>.insteadOf` |
| v6+ | `$RUNNER_TEMP` 下单独凭证文件 + `includeIf "gitdir:..."` |

**为什么 v6 要改**：

- 直接把 token 写到 `.git/config` 里，任何后续 `git config` 输出都可能泄露 token 到 log。
- 拆出去后，token 文件路径独立，post-job 阶段被清理；workflow log 里看不到 `http.extraHeader` 这种敏感行。

**`includeIf` 的作用**：凭证写进独立文件后，再靠 `includeIf "gitdir:..."` 让 Git 只在匹配该目录（本次 checkout 的工作区）时才加载那个文件。这样 token 不会污染 runner 上其它仓库的 Git 配置，其它 git 操作读不到它；用后即焚的清理因此也干净，不会留下持久凭证。

**对容器 action 的兼容性影响**：Docker container action 默认只挂载 `$GITHUB_WORKSPACE`，看不到 `$RUNNER_TEMP` 里的凭证文件。要让容器内跑认证 git 命令，runner 需要 ≥ [v2.329.0](https://github.com/actions/runner/releases/tag/v2.329.0)，这个版本会把凭证上下文透传给容器；旧 runner 会静默失败或退回未认证操作。

### 4. 推荐权限最小化

v4.3.0 引入的"Recommended permissions"文档段在 v7 沿用：

```yaml
permissions:
  contents: read   # checkout 只需要读
```

**关键约束**：

- 如果 workflow 要在 checkout 后 `git push` 改动回 base 仓库，需要 `contents: write`。
- 如果 workflow 要给 fork PR 评论，需要 `pull-requests: write`。
- 推荐用 fine-grained token 或 GitHub App 而不是 `GITHUB_TOKEN`，最小化 token 权限。

---

## 任务流案例：v7 在三种真实场景下的表现

**场景 A：无参数 checkout + `pull_request_target`（最常见）**

```yaml
on: pull_request_target
steps:
  - uses: actions/checkout@v7   # 无任何 with
```

外部贡献者提来 fork PR，checkout 正常执行，拿到的是 base 分支的 commit——这是 `pull_request_target` 事件的默认行为，属于源码里"默认自 checkout"的可信路径，检查被跳过。**升级后行为不变，不需要任何改动。**

**场景 B：显式 checkout fork PR 代码（经典 pwn request 写法）**

```yaml
on: pull_request_target
steps:
  - uses: actions/checkout@v7
    with:
      ref: ${{ github.event.pull_request.head.sha }}   # 指向 fork PR 代码
```

fork PR 到来，`ref` 解析出的 commit 命中 PR head SHA，三个拒绝模式之一命中，job 立刻 fail，报错信息即上文引用的那段——原因、风险链接、opt-in 方法都在里面。这类 workflow 是这次强制升级真正针对的对象：它们以前能跑通，不代表安全，只代表风险还没爆发。

**场景 C：确实要 lint fork 代码**

```yaml
- uses: actions/checkout@v7
  with:
    allow-unsafe-pr-checkout: true
- name: Run lint on read-only files
  run: |
    # 只读扫描，不执行 npm ci / make
    npx eslint . --max-warnings 0
```

opt-in 后 checkout 放行，但后续步骤必须只做只读扫描——不 `npm ci`、不 `make`、不执行任何来自 fork 的脚本。更稳的做法是把这类逻辑挪到 `pull_request` 触发器：那里没有 base 仓库 secrets，fork 代码本来就可以随便 checkout。

三个场景合起来看：v7 没有禁止 checkout fork 代码，它把"我要在可信 context 里拉不可信代码"这个动作从隐式默认变成了必须手写、review 时一眼可见的一行声明。

**快速自查**：在自己的仓库里搜三类模式，命中任意一条且触发器含 `pull_request_target` / `workflow_run`，升级后就会 fail——`ref:` 里带 `pull_request.head.sha` / `refs/pull`、`repository:` 指向 `github.event.pull_request.head.repo`、或任何解析后等于 fork PR commit 的 SHA。

---

## 与同类方案的横向对照

| 维度 | checkout v7 | checkout v2–v6（backport 后） | 自托管 checkout script | GitHub App-based checkout |
|---|---|---|---|---|
| 角色 | 官方默认 checkout | 官方旧版 + 安全 backport | runner 内 bash script | 第三方细粒度 token 工具 |
| fork PR 默认行为 | ✅ default-deny | ✅ 同 v7（各 major 的 backport 版起） | ❌ 全靠自己 | ✅ 短时 token |
| 凭证存储 | `$RUNNER_TEMP` 独立文件（v6+） | v6+ 同 v7；v4 / v5 在 `.git/config` | 任意 | 不存凭证 |
| Runtime | ESM + Node.js 24 | CJS（v3 起 node16、v4 起 node20、v5 起 node24） | bash | 不依赖 action |
| License | MIT | MIT | 用户自有 | 各异 |
| Stars | 8.8k | 共用同一仓库 | — | 各自不同 |
| 维护方 | GitHub 官方 | GitHub 官方 | 自维护 | 社区/商业 |

v7 的 pwn request 修复不是个例，而是 GitHub Actions 生态在 2024–2026 年逐步收紧 untrusted code checkout 的趋势——`pull_request_target` 从"默认能 checkout + 文档警告"演化到"默认拒绝 + 显式 opt-in"，并且这个默认被强制推到了所有仍在维护的版本。

---

## 适用边界

**推荐使用 v7**：

- 任何公开仓库（fork PR 是常态）。
- 任何使用 `pull_request_target` / `workflow_run` 触发器的 workflow。
- 任何追求 Node.js 24 + ESM 现代依赖链的工程团队。
- 任何想要"显式声明安全姿态"的团队。

**升级前需要评估的**：

- v7 没有输入层面的破坏性变更，`action.yml` 的输入与 v6 兼容，迁移本身只是改一个 tag。
- 真正要评估的是行为变化：仓库里所有显式 checkout fork PR 代码的 step 都会开始 fail，需要逐个决定是删除、改造还是 opt-in（见上文自查清单）。
- 自托管 runner 版本低于 v2.327.1 的环境跑不了 node24 runtime，先升 runner。

**不推荐自己 fork 维护**：

- 仓库明确写 "right now we are not taking contributions"，bug 报告走 GitHub Community Discussions，但仍提供安全更新。
- 任何 fork 都会跟主线脱钩，最终在 v8 / v9 上付出大量 cherry-pick 成本。

---

## 决策建议

1. **新 workflow** → 直接用 `actions/checkout@v7`。
2. **存量 v2–v6 workflow** → 若 pinned 到浮动 major tag，2026-07-20 起已自动拿到 default-deny 加固；若 pinned 到具体版本（如 `@v6.0.3`），先升到所在 major 的 backport 版（v5.1.0 / v6.1.0 / v4.4.0），或直接升 v7。v7 是省心的终点：安全默认与旧版一致，另获 ESM 迁移与依赖修复。
3. **只想补安全、不动 major** → 升到所在 major 的 backport 版即可拿到同一 default-deny，但拿不到 v7 的 ESM 迁移与新依赖。
4. **fork PR 真的需要 checkout** → 显式 `allow-unsafe-pr-checkout: true`，并确保后续步骤**不执行 untrusted code**（不 `npm ci` / 不 `make` / 不 `bash untrusted.sh`）。
5. **完全避免 pwn request** → 改 workflow 设计：把"需要 fork 代码"的逻辑放在 `pull_request` 触发器（runner 没有 secrets），把"需要 secrets"的逻辑放在 `pull_request_target` 触发器（保持无参数 checkout，拿到 base commit）。

---

## 常见问题与排查

**Q1：升级后 `pull_request_target` workflow 的 checkout 突然 fail，为什么？**

先看 checkout step 是不是显式指向了 fork PR 代码——`ref` 传了 `github.event.pull_request.head.sha`、`refs/pull/N/merge` 这类值，或 `repository` 指向 fork 仓库。这是预期行为：fork PR 代码默认不再被 checkout。如果不需要那份代码，把自定义 ref 删掉、退回无参数 checkout（拿 base commit）即可；确实需要，见 Q3。无参数 checkout 的 workflow 不受影响。

**Q2：我 pinned 到 `@v4`，为什么行为也变了？**

因为 GitHub 把 default-deny 强制推到了所有受支持的 major——2026-07-20 同日发布的 backport 版本覆盖 v4.4.0 / v5.1.0 / v6.1.0（以及更老的 v2.8.0 / v3.7.0），v1 除外。浮动 major tag（`@v4` 等）在当日之后自动指向含加固的版本；固定到具体 SHA / minor / patch 的 workflow 行为不变，但需要主动升级才能拿到防护。

**Q3：我确实要 checkout fork 代码做 lint / spell check，怎么配？**

显式 `allow-unsafe-pr-checkout: true`，且后续步骤只做只读扫描，不执行 untrusted code（不 `npm ci` / 不 `make`）。更稳妥的做法是把这类逻辑放到 `pull_request` 触发器——那里没有 base 仓库 secrets。

**Q4：Docker container action 里 git 认证失败或静默退回未认证？**

v6 起凭证在 `$RUNNER_TEMP`，容器默认看不到。升级 runner 到 ≥ v2.329.0，让它把凭证上下文透传给容器。

**Q5：怎么确认我的 workflow 拿到了加固？**

在沙箱仓库里用 fork 账号提一个带自定义 `ref`（指向 PR head）的 `pull_request_target` workflow，观察 checkout 是否报 "Refusing to check out fork pull request code"；只验证无参数 checkout 是测不出来的，因为它本来就不在检查范围内。

---

## 边界声明

本文基于 [actions/checkout](https://github.com/actions/checkout) 仓库 README、`action.yml`、`src/` 源码（重点复核 `unsafe-pr-checkout-helper.ts` 与 `input-helper.ts`）、`CHANGELOG.md`、releases 列表（2026-09-07 复核），以及 [GitHub 官方 changelog 公告](https://github.blog/changelog/2026-06-18-safer-pull_request_target-defaults-for-github-actions-checkout/)。

**关键事实与出处**：

- 仓库 README 明确写 "right now we are not taking contributions"——外部贡献不被接受，问题走 GitHub Community Discussions，安全更新仍会提供。
- 版本线：v7.0.0 发布于 2026-06-18；v7.0.1、v6.1.0、v5.1.0、v4.4.0、v3.7.0、v2.8.0 均发布于 2026-07-20。
- 安全 backport：`allow-unsafe-pr-checkout` 在 v7 / v6.1.0 / v5.1.0 / v4.4.0 的 `action.yml` 中均存在（默认 `false`）；GitHub 于 2026-07-20 对所有受支持 major 强制执行 default-deny（v1 除外）。更早版本（如 v6.0.x、v5.0.x、v4.3.x）没有该输入，对应行为是允许 checkout fork PR 代码。
- 判定逻辑引用自 `unsafe-pr-checkout-helper.ts` 的 `assertSafePrCheckout` 与 `input-helper.ts` 的调用点（"默认自 checkout"短路、fork 判定、三个拒绝模式），非官方文档转述；后续版本若改动源码，以仓库为准。
- 仓库 stars 为 8.8k+（8848，2026-09-07 查询），License 是 MIT；使用 GitHub Actions 服务本身仍受 GitHub 服务条款约束，与代码的 MIT license 是两层。

如果你的 workflow 在 fork PR 触发下出错，第一时间排查的就是 `pull_request_target` + "checkout 输入指向 fork PR 代码"的组合；按场景 C 显式 opt-in，或按决策建议第 5 条改 workflow 设计。
