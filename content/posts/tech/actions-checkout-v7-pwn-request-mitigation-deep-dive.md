---
title: "actions/checkout v7 拆解：GitHub 最常用的 Action 如何用 default-deny + ESM 迁移解决 pwn request 这类 fork PR 攻击面"
date: 2026-07-17T02:58:00+08:00
lastmod: 2026-07-17T02:58:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["GitHub Actions", "actions/checkout", "Security", "pwn request", "ESM"]
description: "actions/checkout v7（2026-06-18 发布）是 GitHub Actions 生态最高频使用的 action，8455 stars、MIT、TypeScript。v7 核心变化是默认拒绝 fork PR 在 pull_request_target / workflow_run 触发器下被 checkout（pwn request 攻击面），并完成 ESM 模块化迁移。"
weight: 1
slug: "actions-checkout-v7-pwn-request-mitigation-deep-dive"
author: text-matrix
---

## 一句话判断

**actions/checkout（[actions/checkout](https://github.com/actions/checkout)）是 GitHub Actions 生态里被引用次数最多的 action——几乎每一个 CI workflow 的第一行都是 `uses: actions/checkout@v4`**。它做的事情表面简单："在 runner 上把仓库克隆到 `$GITHUB_WORKSPACE`"，但 v7（2026-06-18 发布）是一次被安全事件驱动的硬性升级：**默认拒绝 fork pull request 在 `pull_request_target` / `workflow_run` 触发器下被 checkout——也就是业界常说的"pwn request"漏洞类别**。同时 v7 完成了从 CJS 到 ESM 的模块化迁移，以适配新的 `@actions/*` 包版本。8455 stars、MIT、TypeScript 实现，仓库本身**不接收外部 contribution**（README 明确写明），由 GitHub 官方 Actions 团队直接维护。

如果你在维护任何会被外部贡献者提 PR 的 GitHub 仓库，这篇 v7 的 default-deny + ESM 拆解值得读完。

---

## 系统地图

```
┌──────────────────────────────────────────────────────────────────────┐
│                    actions/checkout v7 内部                            │
│                                                                          │
│  ┌─────────────────────┐    ┌────────────────────────────────────┐    │
│  │  入口与配置          │    │  Git 操作层                          │    │
│  │  ─────────────────── │    │  ────────────────────────────────  │    │
│  │  src/main.ts         │    │  git-command-manager.ts            │    │
│  │  src/input-helper.ts │    │  git-source-provider.ts             │    │
│  │  src/state-helper.ts │    │  git-source-settings.ts             │    │
│  └──────────┬──────────┘    │  ref-helper.ts                      │    │
│             │               │  git-directory-helper.ts            │    │
│             ▼               │  fs-helper.ts                       │    │
│  ┌─────────────────────┐    └────────────────┬───────────────────┘    │
│  │  安全层（v7 新增）    │                     │                         │
│  │  ─────────────────── │                     │                         │
│  │  unsafe-pr-checkout-│                     │                         │
│  │    helper.ts         │                     │                         │
│  │  workflow-context-   │                     │                         │
│  │    helper.ts         │                     │                         │
│  │  regexp-helper.ts    │                     │                         │
│  └──────────┬──────────┘                     │                         │
│             │                                │                         │
│             ▼                                ▼                         │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  凭证与远端适配层                                             │      │
│  │  ────────────────────────────────────────────────────────── │      │
│  │  git-auth-helper.ts（PAT / SSH / OAuth App / GitHub App）    │      │
│  │  github-api-helper.ts（Git 协议 fallback，REST API）          │      │
│  │  url-helper.ts（GHES / GitHub.com URL 适配）                  │      │
│  │  git-version.ts（Git ≥ 2.18 优先，旧版 REST API 兜底）        │      │
│  └──────────┬───────────────────────────────────────────────────┘      │
│             │                                                           │
│             ▼                                                           │
│  ┌─────────────────────────────┐    ┌──────────────────────────────┐  │
│  │  杂项                        │    │  ADR（决策记录）              │  │
│  │  ──────────────────────────  │    │  ─────────────────────────── │  │
│  │  retry-helper.ts            │    │  adrs/0153-checkout-v2.md    │  │
│  │  misc/                      │    │  （决策归档）                │  │
│  └─────────────────────────────┘    └──────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
                          ▼
        ┌─────────────────────────────────────┐
        │  下游消费者                          │
        │  ────────────────────────────────  │
        │  $GITHUB_WORKSPACE/                 │
        │  ← 仓库被 checkout 到这里          │
        │  ← .git/config 里有 token（默认）  │
        │  ← post-job 时清理（默认）         │
        └─────────────────────────────────────┘
```

这张图最重要的一条路径：**入口 main.ts → 输入解析 → 安全检查（v7 新增 unsafe-pr-checkout-helper） → git command manager → 凭证 / 远端适配 → 落盘 `$GITHUB_WORKSPACE`**。v7 把"安全检查"提为独立模块，是 pwn request 缓解的物理位置。

---

## 边界与角色划分

actions/checkout v7 的设计边界可以用 5 条不变项概括：

| 维度 | 不变项 | 含义 |
|------|--------|------|
| 运行时 | ESM + Node.js 24 | v7 配合 actions/publish-immutable-action 0.0.4 升级到 ESM |
| 默认行为 | fork PR 在 `pull_request_target` / `workflow_run` 下被拒 | v7 引入 `allow-unsafe-pr-checkout` 输入，默认 `false` |
| 默认 fetch depth | 1（单 commit） | 想要全历史需 `fetch-depth: 0`；想要 tags 需 `fetch-tags: true` |
| 凭证管理 | 默认持久化 + post-job 清理 | v6 起凭证存到 `$RUNNER_TEMP` 单独文件，不再直接写 `.git/config` |
| 外部贡献 | 不接受 | README 明确写 "right now we are not taking contributions" |

不变项之外，**它明确不做的事**：

- ❌ **不**做 Git LFS push（只 fetch；`lfs: true` 是 fetch-time 行为）。
- ❌ **不**管理 GPG signing。commit signing 由用户后续自己 `git config` / `git commit -S` 完成。
- ❌ **不**做 submodules 自动递归里的 LFS / credentials 嵌套传递（`submodules: recursive` 时按每个子模块独立走同一逻辑）。
- ❌ **不**内置 GHES / 3rd-party Git server 的 token 注入；用户必须自己通过 `github-server-url` + 自定义 token。
- ❌ **不**替代 `git` CLI。它在 runner 上调用 `git`，本身不重写 Git 协议。

这 5 条"不做"恰好决定了它的设计取舍——下面拆开看。

---

## 关键机制：v7 的两件大事

### 1. Default-Deny：pwn request 缓解

**问题定义**：在 v7 之前，actions/checkout 在 `pull_request_target` 触发器下默认会 checkout fork PR 的代码。

**为什么这是安全问题**：

- `pull_request_target` workflow 跑在**base 仓库**的 context 里，能访问 `secrets`、使用 base 仓库的 `GITHUB_TOKEN`。
- fork PR 的代码默认是 untrusted。
- 如果 workflow 第一步用 `actions/checkout` 把 fork 的代码 checkout 到 runner，再 `run: npm ci && npm test` 之类的步骤执行它——攻击者在 fork 仓库里放恶意 `package.json` 的 `postinstall` 脚本，CI 跑起来就拿到了 base 仓库 secret 的访问权。
- 这就是 GitHub Security Lab 命名的 **"pwn request"** 攻击面。

**v7 的修复**：

```yaml
- uses: actions/checkout@v7
  with:
    # 不再需要手动加 if 条件
    # v7 默认就拒绝
    allow-unsafe-pr-checkout: false  # 默认值，显式标注
```

v7 新增 `unsafe-pr-checkout-helper.ts` + `workflow-context-helper.ts` 两个模块，在 checkout 流程的最早期判断：

1. 当前事件是不是 `pull_request_target` 或 `workflow_run`？
2. 当前 PR 是不是来自 fork？
3. 如果都是 → 默认拒绝；必须显式设 `allow-unsafe-pr-checkout: true` 才允许 checkout fork 代码。

**为什么用 default-deny 而不是 default-allow + 文档提示**：历史教训。v4-v6 期间这个风险被无数次安全公告和 advisories 强调，但总有人不看文档。default-deny 把"易错操作"变成"显式 opt-in"，大幅降低误配概率。

**显式 opt-in 的代价**：用户在真正需要 checkout fork 代码的场景（比如要给 fork 仓库做 lint）必须显式：

```yaml
- uses: actions/checkout@v7
  with:
    allow-unsafe-pr-checkout: true
    # 并且强烈建议：
    # 1. 不要用 GITHUB_TOKEN，直接 checkout
    # 2. 不要在后续 step 里用这个代码执行 npm ci / make 等
    # 3. 参考 README 顶部 v7 "What's new" 段官方安全指南
```

### 2. ESM 迁移

**变更动机**：v7 升级 `@actions/core` / `@actions/tool-cache` 等依赖到新版本，这些新版只发布 ESM。CJS 用户升级时会撞墙。

**v7 的具体改动**（来自 CHANGELOG）：

- `upgrade module to esm and update dependencies` (PR #2463)
- `Bump @actions/core and @actions/tool-cache and Remove uuid` (PR #2459)
- 同步升级 `flatted` / `js-yaml` 等 security updates

**对用户的影响**：

- 如果 workflow 里有自己的 JS step import `@actions/core`，那些 step 也需要切 ESM（`import` 而不是 `require`）。
- actions/checkout 本身是 ESM，但 runner 仍能正常调用——这是 action 内部的实现细节，对调用方无感。
- 这条改动本身不是安全问题，是 dependency hygiene。

### 3. 凭证存储的演化（v6 → v7）

v6.0.0 引入的 `persist-credentials` 重构，v7 沿用：

| 版本 | token 存储位置 |
|---|---|
| v4 / v5 | `.git/config` 里的 `http.extraHeader` / `url.<base>.insteadOf` |
| v6+ | `$RUNNER_TEMP/_temp/_github_home/.../credentials` 单独文件 + `includeIf "gitdir:..."` |

**为什么 v6 要改**：

- 直接把 token 写到 `.git/config` 里，任何后续 `git config` 输出都可能泄露 token 到 log。
- 拆出去后，token 文件路径独立，且 post-job 阶段被清理；workflow log 里看不到 `http.extraHeader` 这种敏感行。
- v6.0.3 额外修了 SHA-256 仓库的 init 逻辑（PR #2439），v6.0.2 修了 tag annotation 保留（PR #2356）。

### 4. 推荐权限最小化

v4.3.0 引入的"Recommended permissions"段在 v7 沿用：

```yaml
permissions:
  contents: read   # checkout 只需要读
```

**关键约束**：

- 如果 workflow 要在 checkout 后 `git push` 改动回 base 仓库，需要 `contents: write`。
- 如果 workflow 要给 fork PR 评论，需要 `pull-requests: write`。
- 推荐用 fine-grained token 或 GitHub App 而不是 `GITHUB_TOKEN`，最小化 token 权限。

---

## 任务流案例：v7 在 fork PR 上的实际表现

把上面的零件拼起来跑一次完整 flow：

**Step 1：仓库设置**

假设你维护一个公开仓库 `acme/widget`，有外部贡献者 fork。

**Step 2：CI workflow（v7 写法）**

```yaml
name: CI
on:
  pull_request:
  pull_request_target:
    # 关键：pull_request_target 用于跑在 base context

permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
        with:
          # v7 新行为：
          # 如果是 fork PR + pull_request_target 触发 → 报错退出
          # 如果是 base PR → 正常 checkout
          # 如果你想真的 checkout fork 代码（lint / spell check），必须显式 opt-in
          allow-unsafe-pr-checkout: false  # 默认值，可省略
```

**Step 3：fork PR 到来**

外部贡献者 fork `acme/widget`，提一个 PR。

**Step 4：CI 实际跑出来的结果**

- `pull_request` 触发器：v7 正常 checkout fork 代码（安全）。
- `pull_request_target` 触发器：v7 拒绝 checkout，job fail 并打印明确错误信息，提示用户"如需 checkout fork 代码，请阅读 README 顶部 v7 段官方安全指南后显式 opt-in"。

**Step 5：base 仓库维护者想 lint fork 代码**

```yaml
- uses: actions/checkout@v7
  with:
    allow-unsafe-pr-checkout: true
    # 但后续步骤不要执行 untrusted code
- name: Run lint on read-only files
  run: |
    # 只读扫描，不执行 npm ci / make
    npx eslint . --max-warnings 0
    # 不传 secrets，不写 .npmrc
```

**这是 v7 的核心工作流变化**：把"易错的安全配置"变成"必须显式 opt-in 的高风险操作"。

---

## 与同类项目的横向对照

| 维度 | actions/checkout v7 | `actions/setup-node@v4` | 自托管 checkout script | GitHub App-based checkout |
|---|---|---|---|---|
| 角色 | 官方默认 checkout | node 环境 | runner 内 bash script | 第三方细粒度 token 工具 |
| 安全 | ✅ default-deny pwn | ✅ OIDC token 支持 | ❌ 全靠自己 | ✅ 短时 token |
| 凭证存储 | `$RUNNER_TEMP` 独立文件 | 不存凭证 | 任意 | 不存凭证 |
| Runtime | ESM + Node 24 | ESM + Node 24 | bash | 不依赖 action |
| License | MIT | MIT | 用户自有 | 各异 |
| Stars | 8.5k | 1k+ | — | 各自不同 |
| 维护方 | GitHub 官方 | GitHub 官方 | 自维护 | 社区 / 商业 |

这张表想表达一件事：**v7 的 pwn request 修复不是个例，而是 GitHub Actions 生态在 2024-2026 年逐步收紧 untrusted code checkout 的趋势**——`pull_request_target` 从"默认能 checkout + 文档警告"演化到"默认拒绝 + 显式 opt-in"。

---

## 适用边界

**推荐使用 v7**：

- 任何公开仓库（fork PR 是常态）。
- 任何使用 `pull_request_target` / `workflow_run` 触发器的 workflow。
- 任何追求 Node 24 + ESM 现代依赖链的工程团队。
- 任何想要"显式声明安全姿态"的团队。

**不推荐使用 v7**：

- 强依赖 v4 / v5 旧 workflow 文件（迁移成本极低，但旧依赖若有兼容问题需要评估）。
- 在 runner 上跑老旧 Node 16 工具链（v7 要求 Node 24，actions runner 需 ≥ v2.327.1）。

**不推荐自己 fork 维护**：

- 仓库明确写 "right now we are not taking contributions"。
- 任何 fork 都会跟主线脱钩，最终在 v8 / v9 上付出大量 cherry-pick 成本。

---

## 决策建议

按升级路径选：

1. **新 workflow** → 直接用 `actions/checkout@v7`。
2. **存量 v4 workflow** → 升到 v7 是低风险操作（ESM 改动只在 action 内部，对调用方无感；主要差异是 default-deny 行为）。先在 sandbox repo 验证 fork PR 场景。
3. **存量 v5 / v6 workflow** → 同上，迁移成本极低。
4. **fork PR 真的需要 checkout** → 显式 `allow-unsafe-pr-checkout: true`，并确保后续步骤**不执行 untrusted code**（不 `npm ci` / 不 `make` / 不 `bash untrusted.sh`）。
5. **完全避免 pwn request** → 改 workflow 设计：把"需要 fork 代码"的逻辑放在 `pull_request` 触发器（runner 没有 secrets），把"需要 secrets"的逻辑放在 `pull_request_target` 触发器（runner 不 checkout fork 代码）。

---

## 阅读路径

按需读：

- **只想知道 v7 改了什么**：本文 + README 头部 "What's new" 段
- **想理解 pwn request**：阅读 README 顶部 v7 "What's new" 段引用的官方安全指南（链接见 [actions/checkout](https://github.com/actions/checkout) README）+ `unsafe-pr-checkout-helper.ts` 源码
- **想理解凭证管理**：`git-auth-helper.ts` + v6.0.0 release notes
- **想理解 ESM 迁移**：CHANGELOG.md v7.0.0 + PR #2463
- **想理解 multi-repo 工作流**：README "Scenarios" 段
- **想理解 sparse-checkout**：README "Fetch only the root files" / "Fetch only the root files and `.github` and `src` folder" 两个例子

---

## 边界声明

本文基于 [actions/checkout](https://github.com/actions/checkout) 仓库 README（2026-07-17 抓取）、`action.yml`、`src/` 目录列表、`CHANGELOG.md`、`adrs/0153-checkout-v2.md` 公开文件。

**重要事实**：

- 仓库 README 明确写 "right now we are not taking contributions"——所有外部贡献当前不被接受，bug 报告走 GitHub Community Discussions。
- v7 的具体版本：v7.0.0 发布于 2026-06-18；v7 后续小版本（如 v7.0.1 等）尚未发布（截至 2026-07-17）。
- v4 / v5 / v6 各版本的具体变更以对应 release tag 为准，本文按 README "What's new" 段归纳。
- `allow-unsafe-pr-checkout` 是 v7 新增输入；v6 / v5 / v4 没有这个输入，对应行为是默认 checkout（不安全）。
- 仓库 License 是 MIT，但分支内的 GitHub 官方 runners、GitHub Actions 服务条款与本 action 本身的 MIT license 是两层——使用 GitHub Actions 服务仍受 GitHub 服务条款约束。

如果你的 workflow 在 fork PR 触发下出错，第一时间排查的就是 `pull_request_target` + `actions/checkout` 的组合；按本文 Step 5 的方式显式 opt-in 或改 workflow 设计即可。
