---
title: "actions/checkout 实战指南：从零开始掌握 GitHub Actions 的第一步"
date: "2026-07-02T21:02:26+08:00"
lastmod: "2026-09-07T00:00:00+08:00"
draft: false
categories: ["技术笔记"]
tags: ["GitHub Actions", "CI/CD", "DevOps", "TypeScript"]
description: "拆解 actions/checkout 的 v7 安全默认（含 2026-07-20 对 v2–v6 的回移植）、v6 凭据持久化机制与常见场景：sparse-checkout、fetch-depth、多仓库与子模块。"
author: text-matrix
slug: actions-checkout-github-actions-checkout-step-guide
github_repo: "actions/checkout"
source_key: "gh:actions/checkout"

---

# actions/checkout 实战指南：从零开始掌握 GitHub Actions 的第一步

几乎所有 GitHub Actions workflow 都从一行 `uses: actions/checkout@vX` 写起。它看起来像一个无脑工具：把仓库代码拉到 runner 上，让后续步骤能跑。但当 workflow 出问题（拉不到私有依赖、构建挂在新提交、PR 触发器把 fork 代码当成 base 执行）时，几乎所有根因都和这一步的输入参数有关。本文按 v7/v6/v4 的关键差异、凭据模型与典型场景，拆解这个最常用的 Action。文中事实对照官方 README、release 记录与 GitHub Changelog，核对截至 2026-09-07。

## 目录

- [学习目标](#学习目标)
- [解决的问题](#解决的问题)
- [v7 默认行为变化：拒绝 fork PR 代码](#v7-默认行为变化拒绝-fork-pr-代码)
- [v6 凭据持久化：从 .git/config 移到 $RUNNER_TEMP](#v6-凭据持久化从-gitconfig-移到-runner_temp)
- [输入参数速查](#输入参数速查)
- [常见场景与最小配置](#常见场景与最小配置)
- [认证方式的选择](#认证方式的选择)
- [推荐权限](#推荐权限)
- [浅克隆与历史相关的边界情况](#浅克隆与历史相关的边界情况)
- [clean 与 set-safe-directory 的角色](#clean-与-set-safe-directory-的角色)
- [升级路径与回退](#升级路径与回退)
- [适用边界](#适用边界)
- [小结](#小结)
- [常见问题 FAQ](#常见问题-faq)
- [自测题](#自测题)
- [练习](#练习)
- [进阶路径](#进阶路径)
- [参考资料](#参考资料)

## 学习目标

读完本文后，你应该能够：

1. 解释 `actions/checkout` 在 GitHub Actions workflow 中的角色——它只负责准备代码，不做构建、测试、发布
2. 对比 v4/v6/v7 的关键差异——尤其是 v7 的 fork PR 安全默认和 v6 的凭据持久化位置变化
3. 写出常见场景的 checkout 配置（sparse-checkout、多仓库、子模块、PR head checkout）
4. 根据自己的场景选择合适的认证方式（GITHUB_TOKEN vs PAT vs SSH）
5. 规划从 v4/v5 升级到 v7 的测试路径

---

## 解决的问题

runner 是 GitHub 提供的临时虚拟机，初始状态是干净的 Ubuntu/Windows/macOS 镜像，里面没有你的代码。`actions/checkout` 的职责就是：在 `GITHUB_WORKSPACE` 下准备一个 Git 工作区，让后续 `npm install`、`cargo build`、`pytest` 之类的步骤能直接读文件、读 commit history、读 git 元数据。

它的核心行为有三条（对照 README 各节）：

- 默认只 fetch 一个 commit（即触发 workflow 的 `$GITHUB_SHA`），节省时间和磁盘。
- 认证凭据（`GITHUB_TOKEN` 或 SSH key）默认持久化，让后续 `git fetch`/`git push` 等命令在同一个 workflow 里能继续认证；存储位置在 v6 有变化（v4 直接写仓库的 `.git/config`，v6 起改存 `$RUNNER_TEMP` 下的独立文件，见下文）。post-job 阶段会清除凭据。
- 当 runner 上没有 Git 2.18 或更高版本时，回退到 GitHub REST API 下载文件。

## v7 默认行为变化：拒绝 fork PR 代码

v7 于 2026-06-18 发布。README "What's new" 共三条，主干是第一条："checkout now refuses to check out fork pull request code by default when the workflow is triggered by `pull_request_target` or `workflow_run`." 另外两条是迁移到 ESM（以支持新版 `@actions/*` 包）和常规依赖安全更新，对 workflow 写法没有影响。

背景是：`pull_request_target` 与 `workflow_run` 触发器运行在 base 仓库上下文里，使用 base 的 `GITHUB_TOKEN`、secrets 和 runner 资源。如果此时直接把 fork 仓库的 PR 代码 checkout 下来并执行，等于把不可信代码放进了高权限环境——攻击者可以用 fork 里的恶意脚本窃取 secret、污染构建产物。这就是常说的 "pwn request"，也是 2025 年 tj-actions/changed-files（CVE-2025-30066）和 2026 年 7 月 AsyncAPI 等真实供应链事件的根因套路。

两条边界需要先看清。其一，`workflow_run` 的限定比 `pull_request_target` 更窄——只有在 `workflow_run` 的触发事件本身是某个 `pull_request*` 事件时（即 `workflow_run.event` 是 `pull_request` / `pull_request_target` 等）才拦截，其他类型的 `workflow_run` 不受影响。其二，同一仓库内部的 PR 不在此列，`pull_request` 触发器的行为也完全不变——这份保护针对的只有"来自 fork 的 PR 代码在高权限上下文里执行"这一个模式。

v7 的默认拒绝并不是一刀切，只在以下条件同时成立时才会拦：

- PR 来自 fork（而非同一仓库）；
- 在 `pull_request_target` 或 `workflow_run` 上下文里，本次 checkout 的目标命中二者之一：`repository` 输入解析到 fork 仓库，或 `ref` 匹配 `refs/pull/<N>/head`、`refs/pull/<N>/merge`（含改写后落到 fork PR 的 head / merge commit SHA）。

要继续 checkout fork 代码，必须显式设置：

```yaml
- uses: actions/checkout@v7
  with:
    allow-unsafe-pr-checkout: true
```

`allow-unsafe-pr-checkout` 的注释写明 "Set to `true` only after reviewing the risks at <https://gh.io/securely-using-pull_request_target>"。这不是一个无害的兼容性开关，是要自己判断风险后的一次显式 opt-in。

误判高发的是回移植这条时间线。官方在 2026-07-15 的编辑注中把执行日期从 7 月 16 日推迟到 7 月 20 日，并明确 v1 不接收此变更；7 月 20 日当天 v2.8.0、v3.7.0、v4.4.0、v5.1.0、v6.1.0、v7.0.1 一并发布，fork PR 保护落地到除 v1 外所有受支持的 major 版本。这意味着只要 workflow 用的是 `@v4` 这类浮动 major tag（floating major tag，即 `@v主版本号` 形式、由维护者随 release 移动的标签），就会自动继承新行为；pin 到具体 SHA 或 minor/patch 的版本不会自动获得，需要按正常升级流程升上来。所以哪怕多年没动过 checkout 这一行，行为也可能已经变了。

另一点值得提醒：大多数 `pull_request_target` 用例（打 label、发评论、跑只读检查）本来就不需要 checkout fork 代码。遇到拦截时先问自己"我是不是真的要在高权限上下文里执行某人的 fork 代码"，而不是急着打开开关。

还要说明一层：这份保护只拦 checkout 这一步。它不识别 `run:` 块里手写的 `git fetch`、`gh pr checkout`、其他第三方拉取行为，也不会拦 `issue_comment` 等事件的 fork 代码执行——这些仍属于 pwn request 攻击面，需要靠工作流设计本身（低权限 job 处理不可信代码、高权限 job 只信任元数据）来兜底。

## v6 凭据持久化：从 `.git/config` 移到 `$RUNNER_TEMP`

v6 的关键改动是 `persist-credentials` 的存储位置：凭据不再写进仓库的 `.git/config`，而是写进 `$RUNNER_TEMP` 下的独立文件。workflow 写法不用改，`git fetch`、`git push` 等命令继续可用。

变化之前的风险点在泄密面：仓库的 `.git/config` 会被 `git config` 系列命令看到。如果某个 step 不小心执行了 `git config --list` 把 config dump 到日志，或者把 `.git/config` 拷贝到 artifact，就可能泄露 `GITHUB_TOKEN`。移到 runner 的临时目录之后，仓库 config 不再持有明文凭据。

如果 workflow 后续步骤根本不需要执行 `git push`，可以直接设 `persist-credentials: false`，凭据连落盘这一步都省掉。

注意 v6 文档里有一条硬约束："Running authenticated git commands from a Docker container action requires Actions Runner v2.329.0 or later"。如果你的 step 在 `container:` 字段里跑认证 git 命令，runner 版本必须够新。

## 输入参数速查

下面是完整的输入参数表（以 v7 的 action.yml 为准；v4/v5/v6 的差异在前两节）：

| 参数 | 默认值 | 作用 |
| --- | --- | --- |
| `repository` | `${{ github.repository }}` | 要拉取的 owner/repo，默认就是当前触发 workflow 的仓库 |
| `ref` | 触发事件对应的 ref/SHA | 要切到哪个分支、tag 或 SHA；checkout 其他仓库时用其默认分支 |
| `token` | `${{ github.token }}` | 拉取仓库用的 PAT |
| `ssh-key` | 空 | 走 SSH 协议时的私钥 |
| `ssh-known-hosts` | 空 | 追加到 known_hosts 的主机公钥（可用 `ssh-keyscan` 生成）；github.com 的公钥始终隐式加入 |
| `ssh-user` | git | SSH 连接使用的用户名 |
| `ssh-strict` | true | SSH 严格主机密钥检查（`StrictHostKeyChecking=yes`） |
| `path` | `${{ github.workspace }}` | 工作区下的相对路径 |
| `fetch-depth` | 1 | fetch 的 commit 数，`0` 表示全历史 |
| `fetch-tags` | false | 即使 `fetch-depth > 0` 也拉 tags |
| `show-progress` | true | fetch 时是否显示进度输出 |
| `clean` | true | fetch 前执行 `git clean -ffdx && git reset --hard HEAD` |
| `submodules` | false | 是否拉子模块；`true` 浅拉，`recursive` 递归拉 |
| `lfs` | false | 是否下载 Git LFS 文件 |
| `sparse-checkout` | 空 | sparse 模式拉取指定模式 |
| `sparse-checkout-cone-mode` | true | cone 模式（祖先目录包含） |
| `filter` | 空 | 部分克隆 `git clone --filter`；设置后覆盖 `sparse-checkout` |
| `set-safe-directory` | true | 把仓库路径加入 git `safe.directory` 全局配置 |
| `github-server-url` | 自动 | 用于 GHES 私有部署 |
| `persist-credentials` | true | 是否把 token/SSH key 写到 git config |
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

如果 sparse 拉到的代码要交给 `docker build` 用，先确认 Dockerfile 里的 `COPY` 路径仍然存在——被 sparse 排除掉的目录不会出现在构建上下文里，构建会直接失败。

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

注意 `github-actions[bot]` 的邮箱是 `{user.id}+{user.login}@users.noreply.github.com`，README 注释里特别提示这套账号信息在 GHES 上不会生效。

## 认证方式的选择

`token` 与 `ssh-key` 是 `actions/checkout` 提供的两条认证路径，分别对应 HTTPS 和 SSH 协议。它们的取舍主要看下游 step 的需求：

- **只用 `GITHUB_TOKEN`**：默认 `token: ${{ github.token }}` 已经够用。Post-job 会自动清掉凭据，适合 CI 流水线本身不做 push 的场景。
- **必须 push 回同一仓库**（例如 release 流程里修改 tag、生成 changelog commit）：仍然用 `GITHUB_TOKEN`，但 workflow 顶层需要把 permissions 调到 `contents: write`。
- **跨私有仓库 checkout**：默认 token 只对当前仓库有效，必须自带 PAT（`token: ${{ secrets.GH_PAT }}`）。README 明确建议 PAT 用服务账号、并按最小权限 scope 生成。
- **必须 SSH**：用 `ssh-key` 私钥 + `ssh-known-hosts` 注入 known_hosts，必要时关闭严格检查 `ssh-strict: 'false'`。SSH 模式下要注意：未提供 `ssh-key` 时，`git@github.com:` 开头的子模块 URL 会被自动转成 HTTPS；如果不想转，单独提供 ssh-key。

另有一条触发器层面的边界，和认证直接相关：fork 的 PR 在 `pull_request` 触发器下，`GITHUB_TOKEN` 是只读的、secrets 不可访问；`pull_request_target` 才会切换到 base 仓库的 token 与 secrets——这正是 v7 要用 `allow-unsafe-pr-checkout` 把守的场景。

GitHub Enterprise Server 上还要设 `github-server-url`，否则 checkout 会试图连公共 `github.com`。

## 推荐权限

不管是用默认 `GITHUB_TOKEN` 还是自带 PAT，README 的 "Recommended permissions" 都建议把 workflow 的权限收窄到最小：

```yaml
permissions:
  contents: read
```

如果某个 job 必须 push，把它单独放到一个 job，并把该 job 的 permissions 显式写成 `contents: write`。这与 GitHub 的 least-privilege 原则一致，token 意外泄露时能限制影响范围。

## 浅克隆与历史相关的边界情况

`fetch-depth: 1` 是大多数 workflow 的最佳选择：足够算 commit 元数据（短 SHA、作者、tree hash）、够 checkout 文件、不浪费带宽。但以下场景需要拉更多：

- `actions/setup-node` 之类的依赖缓存按 `package-lock.json` 哈希计算命中。浅克隆本身不影响 lock 文件，但如果你在 workflow 里跑 `npm version` 或 `lerna version`，这些命令会读 git tag，这时要 `fetch-depth: 0` 或者 `fetch-tags: true`。
- 跑 `git diff --stat HEAD~1` 做增量检查，需要 `fetch-depth: 2`。
- `git tag --list` 在浅克隆下默认只返回 fetch 到的 tag，`fetch-tags: true` 才能看到全部。
- 子模块如果是显式 gitlink hash 提交，浅克隆也能正常 update；但要把子模块历史用于 blame 时需要 `submodules: recursive` + `fetch-depth: 0`。

## `clean` 与 `set-safe-directory` 的角色

这两个参数容易被忽略，但都会影响 workflow 的稳定性。

`clean` 默认为 true，会在 fetch 前执行 `git clean -ffdx && git reset --hard HEAD`。这意味着前一次 workflow 运行遗留的任何未跟踪文件、修改过的 tracked 文件都会被冲掉。在 self-hosted runner 复用缓存目录、或者用 matrix 跑多语言构建时，这个默认通常是正确的——但如果你的 workflow 在 checkout 之后写了一些临时文件并希望保留到下一步，就要把 `clean: false`。

`set-safe-directory` 默认为 true，会执行 `git config --global --add safe.directory <path>`。这是为了应对 Git 2.35.2 之后引入的"目录所有权保护"：当 Git 检测到当前用户对仓库目录的所有权与系统记录不一致时，会拒绝执行 `git status` 等操作。在 runner 镜像里，因为挂载点和文件权限的缘故几乎一定会触发这条保护，所以默认开启是合理的。用 rootless 容器跑 runner 且没有权限问题的团队，可以关闭它，减少全局 config 污染。

## 升级路径与回退

升级 major 版本前建议这样测：

1. 在测试 workflow 的 pin 上改成 `@v7`，把 `pull_request_target` 与 `workflow_run` 触发场景单测一遍，确认 `allow-unsafe-pr-checkout` 没被遗漏。
2. 内部 docker 镜像如果在 `run:` 步骤里用 git 凭据，确认 runner ≥ v2.329.0（v6 引入 `$RUNNER_TEMP` 凭据存储后的最低版本）。
3. self-hosted runner 跑 node24（v5+）之前要确认 ≥ v2.327.1。
4. 在私有 fork 流程里，刻意构造一个 fork PR，验证新默认是否真的拒绝了 fork 代码——避免"以为安全实则绕开"。
5. 即便没升级，也要复核所有沿用浮动 major tag（`@v4`/`@v5`/`@v6`）的 `pull_request_target` workflow：它们可能已在 2026-07-20 自动继承了新保护。如果 CI 开始在 fork PR 上报错，先想到这一层，而不是去查仓库最近改了什么。

pin 的粒度上，`@v7` 这类 major tag 由维护者随 release 移动，指向最新的正式版本；`@main` 指向默认分支，可能包含未发布的变更。生产 workflow 用 major tag 或具体 SHA，不用 `@main`。

如果需要紧急回退到上一个 major，把 pin 改回 `@v6` 或 `@v5` 即可；运行时差异在 README 的 "What's new" 里都列了。但要注意：回退只能换回凭据存储与 runtime 行为，2026-07-20 之后受支持 major 上的 fork PR 保护是默认继承的，靠换 tag 并不能绕开安全默认。

## 适用边界

`actions/checkout` 只负责把仓库代码准备好，是一个"获取代码"原语，不是一个完整的 CI 工具。理解这一点，就不会在它身上找不该有的功能。

适合：

- 任何 GitHub Actions workflow 的第一步。
- 拉取当前仓库、跨仓库拉取、PR head 拉取。
- 文档项目用 sparse-checkout 做轻量克隆。

不适合：

- 安装依赖（用 `actions/setup-node`、`actions/setup-python` 等）、缓存（用 `actions/cache`）、构建测试发布（后面的 step）。
- 不是 Git 仓库的产物下载（比如拉 release artifact，用 `gh release download` 或 `actions/download-artifact`）。
- GitHub API 写操作（用 `gh` CLI 或专门的 octokit Action，checkout 只管代码）。
- 对 fork PR 做代码执行（在 v7 之后这正是它的默认拒绝行为）。

## 小结

`actions/checkout` 是 GitHub Actions 的入口原语。v7 把"fork PR 在高权限上下文中执行"这条已知风险修成了默认拒绝；v6 把凭据持久化从 `.git/config` 搬到了 runner 临时目录；其余输入（`fetch-depth`、`sparse-checkout`、`submodules`、`path`、`ref`）只是把"按什么形态取代码"这件事讲得更细。日常把版本钉到 major tag 或具体 SHA、按需设 `permissions: contents: read`，CI 里与凭据和拉取相关的问题就解决了大半。

## 常见问题 FAQ

**Q1: v4/v5/v6/v7 之间能直接升级吗？**

不能。每个 major 版本有运行时差异（node 版本、凭据存储位置、安全默认），升级前应先在测试 workflow 上验证。README 的 "What's new" 节列出了完整变更。

**Q1b: 我才 pin 在 `@v4`，怎么突然就收到了 fork PR 被拦的错误？**

这不是升级。2026-07-20 起，v7 的 fork PR 保护被回移植到除 v1 外所有受支持的 major 版本（官方 2026-07-15 的编辑注把执行日期从 7 月 16 日推迟到 7 月 20 日），只要你的 workflow 用的是浮动 major tag（如 `@v4`、`@v5`），会自动继承新默认。只有 pin 到具体 SHA 或 minor/patch 的不会自动获得，需要显式升级。

**Q2: `persist-credentials: false` 后怎么 push？**

不设 `persist-credentials` 或设为 true 时，凭据自动可用，`git push` 直接执行。如果设为 false，需要在 push 前手动设置 remote URL 携带 token：`git remote set-url origin https://x-access-token:$GITHUB_TOKEN@github.com/owner/repo.git`。

**Q3: fork 来的 PR 在 pull_request 和 pull_request_target 下有什么区别？**

`pull_request` 触发时 token 是只读的、secret 不可访问。`pull_request_target` 切换到 base 仓库的 token 与 secret，但 v7 起默认拒绝 checkout fork 代码，需要显式设置 `allow-unsafe-pr-checkout: true` 并确认风险。

**Q4: sparse-checkout cone mode 什么时候该关？**

cone 模式会把模式解析为"包含祖先目录"。如果只想拉单个文件或一组不共享祖先目录的文件，必须关掉 cone mode（`sparse-checkout-cone-mode: false`）。

**Q5: 自建 runner 升级前要检查什么？**

v5+ 需要 runner ≥ v2.327.1（node24）；v6 的 Docker container 认证 git 命令需要 runner ≥ v2.329.0；runner 上 Git 版本低于 2.18 时会回退到 REST API 下载文件，这条路径下子模块、LFS 等依赖 git 协议的功能可能不可用。

## 自测题

**问题 1：`actions/checkout` 的 fetch-depth 默认值是多少？如果要做 `git diff HEAD~1`，需要设多少？**

<details>
<summary>答案</summary>
默认 1（只 fetch 触发 commit）。`git diff HEAD~1` 需要 fetch-depth: 2。
</details>

**问题 2：v7 最重要的安全变更是哪条？**

<details>
<summary>答案</summary>
默认拒绝 checkout fork PR 代码（pull_request_target 触发时；workflow_run 仅在由 pull_request* 事件引起时同样拦截）。需要显式设置 `allow-unsafe-pr-checkout: true` 才能继续。
</details>

**问题 3：v6 的凭据持久化位置从哪搬到了哪？为什么？**

<details>
<summary>答案</summary>
从仓库的 `.git/config` 搬到了 `$RUNNER_TEMP` 下的独立文件。防止 `git config --list` 或其他操作意外泄露 GITHUB_TOKEN。
</details>

**问题 4：跨私有仓库 checkout 时需要额外提供什么？为什么默认 `${{ github.token }}` 不够？**

<details>
<summary>答案</summary>
需要额外提供 PAT（`token: ${{ secrets.GH_PAT }}`）。默认 GITHUB_TOKEN 只对当前触发 workflow 的仓库有效，跨仓库需要携带自己的 PAT。
</details>

**问题 5：sparse-checkout cone mode true 和 false 有什么区别？**

<details>
<summary>答案</summary>
true（默认）把模式解析为"包含祖先目录"，适合拉整个子目录。false 做精准匹配，适合拉单个文件。
</details>

**问题 6：pull_request 触发器下默认 checkout 的是什么？怎么拿到 PR 源分支的代码？**

<details>
<summary>答案</summary>
默认 checkout merge commit。用 `ref: ${{ github.event.pull_request.head.sha }}` 拿到 PR 的 head commit。
</details>

## 练习

**练习 1：最小权限配置**

写一个 workflow，只给了 `contents: read` 权限，但其中一个 job 需要 push 一个 generated commit。实现这个 job 级别的权限提升。

**练习 2：多仓库 checkout**

一个项目依赖两个私有仓库。写一个 workflow step，把主仓库 + 两个私有依赖都 checkout 到工作区，并确保私有仓库能正常拉取。

**练习 3：sparse-checkout 优化**

一个 monorepo 有 10 个 package，你的 CI 只需要其中一个 package 的代码。写一个优化后的 checkout 配置，减少 clone 时间。

## 进阶路径

**阶段 1：基础掌握（1 天）**

- 理解 fetch-depth、path、ref、token 四个核心参数的作用
- 在个人项目里尝试 `fetch-depth: 0` 和 `fetch-depth: 1` 的时间差
- 熟悉适用边界——知道什么不该用 actions/checkout 做

**阶段 2：安全配置（2-3 天）**

- 理解 v7 的 `allow-unsafe-pr-checkout` 安全模型
- 在自己的 workflow 里收紧 permissions 到最小范围
- 测试 pull_request vs pull_request_target 的 token 差异

**阶段 3：复杂场景（1 周）**

- 在生产项目中配置多仓库 checkout
- 处理子模块和 Git LFS 场景
- 从 v4/v5 升级到 v7，跑完整测试

## 参考资料

以下链接与事实核对截至 2026-09-07。

- actions/checkout 仓库与 README（含 v4–v7 的 "What's new" 与全部输入参数）：<https://github.com/actions/checkout>
- actions/checkout release 记录（v7.0.0 于 2026-06-18 发布；2026-07-20 各 major 回移植版本同日发布）：<https://github.com/actions/checkout/releases>
- GitHub Changelog：Safer `pull_request_target` defaults for GitHub Actions checkout（含 2026-07-15 编辑注、执行日期推迟与 v1 例外说明）：<https://github.blog/changelog/2026-06-18-safer-pull_request_target-defaults-for-github-actions-checkout/>
- 官方安全指引："Securely using pull_request_target"（GitHub 文档）：<https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target>
- CVE-2025-30066（tj-actions/changed-files 供应链事件）：<https://github.com/advisories/GHSA-mrrh-fwg8-r2c3>
- AsyncAPI npm 供应链事件分析（2026-07-14，Datadog Security Labs）：<https://securitylabs.datadoghq.com/articles/compromised-asyncapi-npm-packages/>
