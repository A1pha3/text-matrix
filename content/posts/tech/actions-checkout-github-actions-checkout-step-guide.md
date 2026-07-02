---
title: "actions/checkout 实战指南：从零开始掌握 GitHub Actions 的第一步"
date: "2026-07-02T21:02:26+08:00"
lastmod: "2026-07-02T21:02:26+08:00"
draft: false
categories: ["技术笔记"]
tags: ["GitHub Actions", "CI/CD", "DevOps", "TypeScript"]
description: "拆解 actions/checkout 的 v7 安全默认、v6 凭据持久化机制与常见场景：sparse-checkout、fetch-depth、多仓库与子模块，走向可靠 CI。"
weight: 1
author: text-matrix
---

# actions/checkout 实战指南：从零开始掌握 GitHub Actions 的第一步

几乎所有 GitHub Actions workflow 都从一行 `uses: actions/checkout@vX` 写起。它看起来像一个无脑工具：把仓库代码拉到 runner 上，让后续步骤能跑。但当 workflow 出问题（拉不到私有依赖、构建挂在新提交、PR 触发器把 fork 代码当成 base 执行）时，几乎所有根因都和这一步的输入参数有关。本文按 v7/v6/v4 的关键差异、凭据模型与典型场景，拆解这个最常用的 Action。

## 它解决了什么问题

runner 是 GitHub 提供的临时虚拟机，初始状态是干净的 Ubuntu/Windows/macOS 镜像，里面没有你的代码。`actions/checkout` 的职责就是：在 `GITHUB_WORKSPACE` 下准备一个 Git 工作区，让后续 `npm install`、`cargo build`、`pytest` 之类的步骤能直接读文件、读 commit history、读 git 元数据。

具体落点（README v7 节选）：

- 默认只 fetch 一个 commit（即触发 workflow 的 `$GITHUB_SHA`），节省时间和磁盘。
- 凭据（`GITHUB_TOKEN` 或 SSH key）默认会写入本地 `git/config`，让后续 `git fetch`/`git push` 等命令在同一个 workflow 里能继续认证。Post-job 阶段会把凭据清掉。
- 当 runner 上 Git < 2.18 时，回退到 GitHub REST API 下载文件，保留对旧 runner 的兼容。

## v7 默认行为变化：拒绝 fork PR 代码

v7 在 README "What's new" 节里写了一句话："checkout now refuses to check out fork pull request code by default when the workflow is triggered by `pull_request_target` or `workflow_run`."

这是这一代最重要的一条变更。背景是：`pull_request_target` 与 `workflow_run` 触发器运行在 base 仓库上下文里，使用 base 的 `GITHUB_TOKEN`、secrets 和 runner 资源。如果此时直接把 fork 仓库的 PR 代码 checkout 下来并执行，等于把不可信代码放进了高权限环境，攻击者可以用 fork 里的恶意脚本窃取 secret、修改 release 工件。这就是常说的 "pwn request"。

v7 之前默认会 checkout；v7 之后默认拒绝。要继续 checkout fork 代码必须显式设置：

```yaml
- uses: actions/checkout@v7
  with:
    allow-unsafe-pr-checkout: true
```

`allow-unsafe-pr-checkout` 的注释里写明"Set to `true` only after reviewing the risks at <https://gh.io/securely-using-pull_request_target>"。换句话说：这不是一个无害的兼容性开关，是一次必须自己判断风险后的显式 opt-in。

## v6 凭据持久化：从 `.git/config` 移到 `$RUNNER_TEMP`

v6 的关键改动是 `persist-credentials` 的存储位置：凭据不再写进仓库的 `.git/config`，而是写进 `$RUNNER_TEMP` 下的独立文件。

为什么这是一个值得关注的细节：

- 仓库的 `.git/config` 会被 `git config` 系列命令看到。如果某个 step 不小心执行了 `git config --list` 把 config dump 到日志，或者把 `.git/config` 拷贝到 artifact，就可能泄露 `GITHUB_TOKEN`。
- 移到 `$RUNNER_TEMP`（runner 的临时目录）之后，仓库历史与 config 不再持有明文凭据。`git fetch` / `git push` 这些命令继续能用，因为 Git 会按仓库路径找到对应 helper。

注意 v6 文档里有一条硬约束："Running authenticated git commands from a Docker container action requires Actions Runner v2.329.0 or later"。如果你的 step 在 `container:` 字段里跑，runner 版本必须够新。

## v4/v5：基础输入契约

v4 README 是一份完整参数表，下面这些是日常高频用到的：

| 参数 | 默认值 | 作用 |
| --- | --- | --- |
| `repository` | `${{ github.repository }}` | 要拉取的 owner/repo，默认就是当前触发 workflow 的仓库 |
| `ref` | 触发事件对应的 ref/SHA | 要切到哪个分支、tag 或 SHA |
| `token` | `${{ github.token }}` | 拉取仓库用的 PAT |
| `ssh-key` | 空 | 走 SSH 协议时的私钥 |
| `path` | `${{ github.workspace }}` | 工作区下的相对路径 |
| `fetch-depth` | 1 | fetch 的 commit 数，`0` 表示全历史 |
| `fetch-tags` | false | 即使 `fetch-depth > 0` 也拉 tags |
| `clean` | true | fetch 前执行 `git clean -ffdx && git reset --hard HEAD` |
| `submodules` | false | 是否拉子模块；`true` 浅拉，`recursive` 递归拉 |
| `lfs` | false | 是否下载 Git LFS 文件 |
| `sparse-checkout` | 空 | sparse 模式拉取指定模式 |
| `sparse-checkout-cone-mode` | true | cone 模式（祖先目录包含） |
| `filter` | 空 | 部分克隆 `git clone --filter` |
| `set-safe-directory` | true | 把仓库路径加入 git `safe.directory` 全局配置 |
| `github-server-url` | 自动 | 用于 GHES 私有部署 |
| `persist-credentials` | true | 是否把 token/SSH key 写到 git config |
| `ssh-strict` | true | SSH 严格主机密钥检查 |
| `allow-unsafe-pr-checkout` | false | v7 新增，见上节 |

`runs` 字段从 v5 起切换到 node24，对应 runner 需要 v2.327.1+。如果团队还在用比较老的 self-hosted runner，升 v5 之前要核对 runner 版本。

## 常见场景与最小配置

README 的 "Scenarios" 节给出了十几种典型写法。下面挑出最常用的几条，并补一些实践上的坑点。

### 只拉根目录文件

适合文档型项目，只读 README、CI 配置、`.github/` 而不需要源码：

```yaml
- uses: actions/checkout@v7
  with:
    sparse-checkout: .
```

### 只拉单个文件

拉一个特定文件，省得下载整个仓库：

```yaml
- uses: actions/checkout@v7
  with:
    sparse-checkout: |
      README.md
    sparse-checkout-cone-mode: false
```

注意第二个输入：cone 模式（默认 true）会把模式解析为"包含祖先目录"，对单个文件的精准匹配必须关掉。

### 拉全历史

构建 changelog、跑 blame、`git log --all` 之类的工具需要全历史：

```yaml
- uses: actions/checkout@v7
  with:
    fetch-depth: 0
```

`fetch-tags` 默认为 false，在浅克隆场景下不会拉 tag；如果你的 release 流程依赖 tag，把 `fetch-tags: true` 加上。

### checkout 父提交

```yaml
- uses: actions/checkout@v7
  with:
    fetch-depth: 2
- run: git checkout HEAD^
```

注意这里的写法：`fetch-depth: 1`（默认）只能拿到触发 commit 本身，没法 `HEAD^`。要做 diff 类对比时，必须把 fetch-depth 拉到 2 或更大。

### checkout PR HEAD

PR 触发器下默认 checkout 的是 merge commit，不是 PR 自己的 head commit。要拿到 PR 的源分支：

```yaml
- uses: actions/checkout@v7
  with:
    ref: ${{ github.event.pull_request.head.sha }}
```

或者用 `${{ github.head_ref }}` 拿到源分支名。

### 多个仓库

平铺在 workspace 下：

```yaml
- name: Checkout main
  uses: actions/checkout@v7
  with:
    path: main

- name: Checkout tools
  uses: actions/checkout@v7
  with:
    repository: my-org/my-tools
    path: my-tools
```

如果是私有仓库，副仓库拉不到时记得提供 token：

```yaml
- uses: actions/checkout@v7
  with:
    repository: my-org/my-private-tools
    token: ${{ secrets.GH_PAT }}
    path: my-tools
```

README 明确写了 `${{ github.token }}` 只对当前仓库生效，跨私有仓库需要自带 PAT。

### 拉子模块

```yaml
- uses: actions/checkout@v7
  with:
    submodules: recursive
```

如果子模块用了 SSH URL 而没有提供 `ssh-key`，checkout 会把 `git@github.com:` 开头的 URL 转换成 HTTPS。

### 用内置 token 推送 commit

```yaml
- uses: actions/checkout@v7
- run: |
    date > generated.txt
    git config user.name "github-actions[bot]"
    git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
    git add .
    git commit -m "generated"
    git push
```

注意 `github-actions[bot]` 的邮箱是 `{user.id}+{user.login}@users.noreply.github.com`，README 注释里特别提示这在 GHES 上不会生效。

## 推荐权限

不管是用默认 `GITHUB_TOKEN` 还是自带 PAT，README 的 "Recommended permissions" 都建议把 workflow 的权限收窄到最小：

```yaml
permissions:
  contents: read
```

如果某个 job 必须 push，记得把它单独放到一个 step 或 job，并把对应 job 的 permissions 显式写成 `contents: write`。这与 GitHub 的 least-privilege 原则一致，能在 token 意外泄露时限制爆炸半径。

## 实战中的几条注意事项

- v4/v5/v6/v7 不互通：使用 `<major>` 引用的是 GitHub 推荐的 major version tag，但仓库默认分支上的代码可能是更新的预发布版本。生产里通常固定到具体 major（`@v7`）而不是 `@main`。
- 不要相信 PR 来自 fork 时 `pull_request` 触发的 `GITHUB_TOKEN` 是只读的：fork 来的 PR 在 `pull_request` 触发器里，token 是只读的、secret 不可访问。但 `pull_request_target` 切换到了 base 仓库的 token 与 secret——这时是否 checkout fork 代码，就是 v7 那条 `allow-unsafe-pr-checkout` 在管的事情。
- `persist-credentials: false` 适合不需要在 workflow 后续步骤里执行 `git push` 的场景，能减少凭据在文件系统上的存在时间。
- sparse-checkout + Docker 构建：在 docker build context 里如果用 sparse 拉到的代码做 build，要确保 Dockerfile 里的 COPY 路径仍然存在，否则会构建失败。
- runner 镜像里如果 git 太老，README 说会自动回退到 REST API。这种路径下 `fetch-tags`、`submodules` 这类需要 server-side 计算的功能可能不可用。

## 认证方式的选择

`token` 与 `ssh-key` 是 `actions/checkout` 提供的两条认证路径，分别对应 HTTPS 和 SSH 协议。它们的取舍主要看下游 step 的需求：

- **只用 `GITHUB_TOKEN`**：默认 `token: ${{ github.token }}` 已经够用。Post-job 会自动清掉 git config 里的凭据，适合 CI 流水线本身不做 push 的场景。
- **必须 push 回同一仓库**（例如 release 流程里修改 tag、生成 changelog commit）：仍然用 `GITHUB_TOKEN`，但 workflow 顶层需要把 permissions 调到 `contents: write`。
- **跨私有仓库 checkout**：默认 token 只对当前仓库有效，必须自带 PAT（`token: ${{ secrets.GH_PAT }}`）。README 明确建议 PAT 用服务账号、并按最小权限 scope 生成。
- **必须 SSH**：用 `ssh-key` 私钥 + `ssh-known-hosts` 注入 known_hosts，必要时关闭严格检查 `ssh-strict: 'false'`。SSH 模式下要注意：未提供 `ssh-key` 时，`git@github.com:` 开头的子模块 URL 会被自动转成 HTTPS；如果不想转，单独提供 ssh-key。

GitHub Enterprise Server 上还要设 `github-server-url`，否则 checkout 会试图连公共 `github.com`。

## 浅克隆与历史相关的边界情况

`fetch-depth: 1` 是大多数 workflow 的最佳选择：足够算 commit 元数据（短 SHA、作者、tree hash）、够 checkout 文件、不浪费带宽。但以下场景需要拉更多：

- `actions/setup-node` 之类的依赖缓存按 `package-lock.json` 哈希计算命中。浅克隆本身不影响 lock 文件，但如果你在 workflow 里跑 `npm version` 或 `lerna version`，这些命令会读 git tag，这时要 `fetch-depth: 0` 或者 `fetch-tags: true`。
- 跑 `git diff --stat HEAD~1` 做增量检查，需要 `fetch-depth: 2`。
- `git tag --list` 在浅克隆下默认只返回 fetch 到的 tag，`fetch-tags: true` 才能看到全部。
- 子模块如果是显式 gitlink hash 提交，浅克隆也能正常 update；但要把子模块历史用于 blame 时需要 `submodules: recursive` + `fetch-depth: 0`。

## `clean` 与 `set-safe-directory` 的角色

这两个参数容易被忽略，但都会影响 workflow 的稳定性。

`clean` 默认为 true，会在 fetch 前执行 `git clean -ffdx && git reset --hard HEAD`。这意味着前一次 workflow 运行遗留的任何未跟踪文件、修改过的 tracked 文件都会被冲掉。在 self-hosted runner 复用缓存目录、或者用 matrix 跑多语言构建时，这个默认通常是正确的——但如果你的 workflow 在 checkout 之后写了一些临时文件并希望保留到下一步，就要把 `clean: false`。

`set-safe-directory` 默认为 true，会执行 `git config --global --add safe.directory <path>`。这是为了应对 Git 2.35.2 之后引入的"目录所有权保护"：当 Git 检测到当前用户对仓库目录的所有权与系统记录不一致时，会拒绝执行 `git status` 等操作。在 runner 镜像里，因为挂载点和文件权限的缘故几乎一定会触发这条保护，所以默认开启是合理的。团队如果用了根目录运行的 self-hosted 镜像，可以保留默认；用 rootless 容器跑 runner 且没有权限问题，可以关闭它减少全局 config 污染。

## 升级路径与回退

升级 major 版本前建议这样测：

1. 在测试 workflow 的 pin 上改成 `@v7`，把 `pull_request_target` 与 `workflow_run` 触发场景单测一遍，确认 `allow-unsafe-pr-checkout` 没被遗漏。
2. 内部 docker 镜像如果 `RUN` 步骤里用 git 凭据，确认 runner ≥ v2.329.0（v6 引入 `$RUNNER_TEMP` 凭据存储的最低版本）。
3. self-hosted runner 用 node24 跑 v5 之前要确认 ≥ v2.327.1。
4. 在私有 fork 流程里，刻意构造一个 fork PR，验证新默认是否真的拒绝了 fork 代码——避免"以为安全实则绕开"。

如果需要紧急回退到上一个 major，把 pin 改回 `@v6` 或 `@v5` 即可；运行时差异在 README 的 "What's new" 里都列了。

## 它不是什么

`actions/checkout` 只负责把仓库代码准备好。它不做：

- 安装依赖（用 `actions/setup-node`、`actions/setup-python` 等）。
- 缓存依赖（用 `actions/cache` 或 `actions/setup-X` 自带缓存）。
- 测试、构建、发布（后面的 step）。

把它当成一个"获取代码"原语，而不是一个完整 CI 工具，理解了这一点就不会在它身上找不该有的功能。

## 适用边界

适合：

- 任何 GitHub Actions workflow 的第一步。
- 拉取当前仓库、跨仓库拉取、PR head 拉取。
- 文档项目用 sparse-checkout 做轻量克隆。

不适合：

- 不是 Git 仓库的产物下载（比如要拉 release artifact，用 `gh release download` 或 `actions/download-artifact`）。
- 需要 GitHub API 写操作时（应该用 `gh` CLI 或专门的 octokit Action，`actions/checkout` 只管代码）。
- 对 fork PR 做代码执行（在 v7 之后这正是它的默认拒绝行为）。

## 一句话总结

`actions/checkout` 是 GitHub Actions 的入口原语。v7 把"fork PR 在高权限上下文中执行"这条已知风险修成了默认拒绝；v6 把凭据持久化从 `.git/config` 搬到了 runner 临时目录；其他输入（`fetch-depth`、`sparse-checkout`、`submodules`、`path`、`ref`）只是把"按什么形态取代码"这件事讲得更细。日常用时，把版本钉到具体 major、配合 `permissions: contents: read` 收窄权限，就能避开绝大多数 CI 凭据与拉取相关的坑。