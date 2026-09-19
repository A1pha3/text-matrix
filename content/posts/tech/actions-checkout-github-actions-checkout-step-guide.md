---
title: "actions/checkout 拆解：一个只负责取代码的步骤，从哪里开始替你判断代码可不可信"
date: "2026-07-02T21:02:26+08:00"
lastmod: "2026-09-19T00:00:00+08:00"
draft: false
categories: ["技术笔记"]
tags: ["GitHub Actions", "CI/CD", "DevOps", "TypeScript"]
description: "按 v7.0.1 源码拆解 actions/checkout：fork PR 守护到底在比较什么、2026-07-20 回移植到 v2–v6 的时间线、v6 凭据落进 $RUNNER_TEMP 的 includeIf 机制、fetch 与 checkout 的真实命令形状，以及一份对得上日志的排查表。"
author: text-matrix
slug: actions-checkout-github-actions-checkout-step-guide
github_repo: "actions/checkout"
source_key: "gh:actions/checkout"
---

`actions/checkout` 的全部职责是把一个 Git 工作区放到 `$GITHUB_WORKSPACE` 下，供后面的 `npm install`、`cargo build`、`pytest` 去读。它不构建、不缓存、不发布。2026 年夏天之后，这个步骤多了一层新工作：它会先判断"这次要拉下来的代码，是不是来自一个不可信的来源"，判断不过就直接抛错退出。

这层新工作带来一个不太直观的后果。v7 在 2026-06-18 把"拒绝检出来自 fork（派生仓库）的 PR 代码"设成默认。不到一个月，2026-07-20，同一条判断被回移植到 v2 到 v6 的所有受支持版本。于是一行多年没被改过的 `uses: actions/checkout@v4`，可以在你不提交任何改动的前提下换掉行为。

下面按 v7.0.1 的源码拆开三件事：守护实际在比较什么、凭据被搬去了哪里、fetch 与 checkout 每一步真正执行了哪些 git 命令。文中断言逐条对照 `action.yml`、`src/`、`CHANGELOG.md`、release 记录与 GitHub Changelog，核对日期 2026-09-19。

## 一次 checkout 走过的六个阶段

`src/git-source-provider.ts` 的 `getSource()` 是主干，读它比读参数表更能建立整体判断。六个阶段各自的职责和失败出口：

| 阶段 | 实现位置 | 做什么 | 失败时日志里出现的句子 |
| --- | --- | --- | --- |
| 解析输入 | `src/input-helper.ts` | 把 21 个输入归一成 settings；把形如 40 或 64 位十六进制的 `ref` 改归类为一次提交；跑 fork PR 守护 | `Invalid repository '…'. Expected format {owner}/{repo}.` |
| 准备目录 | `src/git-directory-helper.ts` | 工作区已存在时删本地分支、删 `.git/index.lock` 与 `.git/shallow.lock`，按 `clean` 决定是否清扫 | `Unable to clean or reset the repository. The repository will be recreated instead.` |
| 探测 git 与对象格式 | `src/git-command-manager.ts`、`src/github-api-helper.ts` | PATH 里没有 git 就整体回退到 REST（表述性状态转移）接口下载归档；SHA-256 仓库走 `git init --object-format=sha256` | `Minimum required git version is 2.18. …` |
| 配置认证 | `src/git-auth-helper.ts` | 写 `http.<origin>/.extraheader` 或 SSH 私钥与 `GIT_SSH_COMMAND` | 后续 git 命令的 403 / host key 报错 |
| fetch 与 checkout | `src/ref-helper.ts`、`src/git-command-manager.ts` | 组 refspec、`git fetch`（失败最多重试到 3 次）、`git checkout --force` | `The ref '…' does not point to the expected commit '…'.` |
| 收尾 | `src/git-source-provider.ts`、`src/main.ts` | 子模块、输出 `ref` 与 `commit`、比对 PR 合并提交的 message | `A branch or tag with the name '…' could not be found` |

看这张表有两个用处。参数名对应的是"输入"，而 CI 出问题几乎总发生在后面五个阶段之一；先定位阶段，再去找参数，比反过来快。另外，输出只有两个（`ref` 和 `commit`），这个 Action 不向你暴露"我做了哪些 git 调用"，排查时得靠它打进日志的分组标题（`Fetching the repository`、`Setting up auth`、`Checking out the ref` 等）来对齐阶段。

## v7 的守护在比较什么

实现集中在 `src/unsafe-pr-checkout-helper.ts`，整个文件 88 行，`assertSafePrCheckout()` 约占其中 70 行。它一次都不问 GitHub，只读 workflow 的事件负载（event payload，也就是 `github.context.payload`）和自己的输入参数。整个判断按顺序往下走，任何一步不满足就 `return`，也就是放行：

1. `allow-unsafe-pr-checkout` 为 true → 直接返回。
2. 事件名不是 `pull_request_target` 也不是 `workflow_run` → 返回。`pull_request`、`push`、`workflow_dispatch` 都不在拦截范围内。
3. 事件是 `workflow_run` 时，再看 `workflow_run.event` 是否以 `pull_request` 开头；不是则返回。所以只有由 PR 类事件引起的 `workflow_run` 受约束，定时或 `push` 引起的不受影响。
4. fork 判定按仓库 ID 而不是名字：取 `repository.id` 作为 base，取 `pull_request.head.repo.id`（`workflow_run` 下是 `workflow_run.head_repository.id`）作为 PR 头端仓库；两个 ID 相同，或者任何一个不是数字，都返回。
5. 确认是 fork PR 之后，还要本次 checkout 的目标确实指向那份 PR 代码，命中以下任一条才拦：
   - `repository` 输入与 PR 头端仓库的 `full_name` 相等（忽略大小写）；
   - `ref` 匹配 `/^refs\/pull\/[0-9]+\/(?:head|merge)$/`；
   - 解析出的 commit 落在事件负载记录的 SHA 集合里。
6. 抛出错误。

第 5 条里的 SHA 集合在不同事件下取法不一样，这个差异值得记：`pull_request_target` 收 `pull_request.head.sha` 和 `pull_request.merge_commit_sha`；`workflow_run` 收 `workflow_run.head_commit.id`，另外只有在 `workflow_run.event` 不是 `pull_request_target` 时才收 `workflow_run.head_sha`——因为后者场景下 `head_sha` 指的是 base 默认分支，收进来会把可信目标误判成可疑目标。

同一仓库内部的 PR 走不到第 5 条，第 4 条就返回了。这条保护针对的只有"把某个 fork 的 PR 代码拉进高权限上下文执行"这一个模式。

### 它没覆盖什么

守护只被调用一次，位置在 `src/input-helper.ts` 里。它不检查 `run:` 块里手写的 `git fetch`，不认识 `gh pr checkout`，也管不到其他 Action 的拉取行为。事件不是那两个触发器时它根本不运行——`issue_comment` 下执行 fork 代码仍然属于同类攻击面。

还有一条例外要单独看，它决定了"裸 checkout 会不会被拦"（`src/input-helper.ts:192`）：

```ts
// The default self-checkout (this repository with no explicit ref) always
// resolves to the trusted ref/commit GitHub set for the triggering event, so
// the fork-checkout guard only needs to run when the caller customized the
// repository or ref.
const isDefaultCheckout = isWorkflowRepository && !core.getInput('ref')
if (!isDefaultCheckout) {
  unsafePrCheckoutHelper.assertSafePrCheckout({
    qualifiedRepository,
    ref: result.ref,
    commit: result.commit,
    allowUnsafePrCheckout: result.allowUnsafePrCheckout
  })
}
```

`repository` 没改、`ref` 没填的默认自检不进入守护。理由写在注释里：这种情况下解析出的目标就是 GitHub 为本次事件设好的可信 ref 与 SHA，`pull_request_target` 下它是 base 分支。v7 因此没有改变"默认 checkout 拿到 base 代码"这个既有语义，它拦的是你自己把目标改到 fork 那边去。

判断第 4 条时如果 `repository.id` 取不到数字，函数也会返回。守护的覆盖面因此依赖事件负载里带没带这些字段，不能把它当成一道独立于负载的攻击屏障。

### v7.0.1 顺手补掉的一个旁路

v7.0.1 的 `CHANGELOG.md` 有两条与守护直接相关：`Skip running unsafe pr check if input is default`（#2518，上面那段短路逻辑）和 `Trim only ascii whitespace for branch`（#2521）。第二条是一次真正的旁路修复，源码注释把风险讲得很直白：

```ts
// core.getInput()'s default trim strips a range of Unicode characters such as a
// leading BOM (U+FEFF) or NBSP (U+00A0). Those are valid in a git ref name, so
// a fork branch named "<BOM>" + 40 hex chars would trim down to a bare SHA and
// be silently reclassified as a commit, bypassing the unsafe fork PR checkout
// guard.
```

`@actions/core` 的 `getInput()` 默认会裁掉一段 Unicode 空白，BOM（U+FEFF，也叫零宽不换行空格）和不换行空格（U+00A0）都在其中，而这两种字符在 git 分支名里合法。攻击者可以把 fork 的分支名做成 `<BOM>` 加 40 位十六进制：裁剪后它变成一个裸 SHA，于是 `input-helper.ts` 走"SHA 分支"那条路径，把 `ref` 清空、只留 commit，绕过 `PR_REF_PATTERN` 的形状匹配。修复方式是把对 `ref` 的裁剪限制在 ASCII 空白（`\t\n\v\f\r` 和空格），这些字符在 git ref 名里本来就是非法的，裁掉不改变语义。

这个坑值得记住的不是细节而是形状：一个"输入归一化"步骤悄悄改变了安全判断的分类结果。同类问题在任何靠正则识别意图的守护里都会重现。

## 2026-07-20：为什么 `@v4` 上的行为也变了

误判高发在这里。GitHub 在 2026-06-18 的 Changelog 里公告 v7 的新默认，又在 2026-07-15 加了一条编辑注，把回移植的执行日期从 7 月 16 日推迟到 7 月 20 日星期一。同一条注里写明 `V1 of actions/checkout will not receive this change. The security update will be backported to all other supported versions.`

7 月 20 日当天六个 release 依次发出：

| 版本 | 发布时间（UTC） | runtime | 对应浮动 major tag 的当前指向 |
| --- | --- | --- | --- |
| v7.0.1 | 07-20 15:10 | node24 | `v7` → v7.0.1（`3d3c42e5`） |
| v6.1.0 | 07-20 15:23 | node24 | `v6` → v6.1.0（`d23441a4`） |
| v5.1.0 | 07-20 15:27 | node24 | `v5` → v5.1.0（`fbc6f399`） |
| v4.4.0 | 07-20 15:36 | node20 | `v4` → v4.4.0（`11d5960a`） |
| v3.7.0 | 07-20 15:40 | node16 | `v3` → v3.7.0（`a37ce912`） |
| v2.8.0 | 07-20 15:43 | node12 | `v2` → v2.8.0（`0717577d`） |

六个 `action.yml` 里都能查到 `allow-unsafe-pr-checkout`，而 runtime 各自保持原样：v2.8.0 仍是 `node12`，v4.4.0 仍是 `node20`。回移植只搬安全行为，没有顺带把老 major 推上新 runtime，也就没有把"runner 版本不够"的风险塞进这次变更里。

浮动 major tag（floating major tag，指 `@v主版本号` 这种由维护者随 release 移动的标签）的当前指向可以直接验证：`git ls-remote` 下 `refs/tags/v4` 与 `refs/tags/v4.4.0` 是同一个提交 `11d5960a326750d5838078e36cf38b85af677262`。所以只要 workflow 写的是 `@v4`、`@v5`、`@v6`，2026-07-20 之后它就带着这条保护，不需要你做任何事。pin 到具体 SHA 或 minor/patch 的不会自动获得，得按正常升级流程升上来。

还要提醒一层：多数 `pull_request_target` 用例（打 label、发评论、跑只读检查）本来就不需要 fork 的代码。遇到拦截时先问"我是不是真的要在高权限上下文里执行某人的 fork 代码"，比急着加 `allow-unsafe-pr-checkout` 有效。

## v6 的凭据模型：一个 UUID 文件、一组 `includeIf`

v4 及更早版本把令牌直接写进仓库的 `.git/config`。风险不在"存了凭据"，而在存的位置太容易被顺手读到：任何 step 跑 `git config --list`、任何 artifact 拷了 `.git`，`GITHUB_TOKEN` 就出现在明面上。

v6（#2286）改的是位置。`configureToken()` 做的事按顺序是：

1. 生成文件名 `git-credentials-<randomUUID>.config`，放在 `$RUNNER_TEMP` 下（`src/git-auth-helper.ts:425`）。
2. 先执行一次 `git config --file <那个路径> http.github.com/.extraheader "AUTHORIZATION: basic ***"`，把占位符写进去。
3. 读回文件，把占位符替换成真实值，再整体写回。
4. 在仓库的 `.git/config` 里写指向上面那个文件的 `includeIf`。

第 2 步的原因写在源码注释里：避免凭据出现在进程创建审计事件里。Windows 的命令行进程审计会把 argv 记进安全日志，用 `git config http…extraheader "AUTHORIZATION: basic <真值>"` 一行写完就等于把令牌抄进了审计流。走占位符再改文件，argv 里始终只有 `***`。真实值本身是 `AUTHORIZATION: basic <base64("x-access-token:<token>")>`，同时会调 `core.setSecret()` 把这段 base64 注册为 secret，让 runner 在日志里把它打码。

第 4 步的接线是这套设计里更实用的部分。仓库 `.git/config` 里留下的是：

```ini
[includeIf "gitdir:/github/workspace/my-repo/.git/"]
    path = /github/runner_temp/git-credentials-<uuid>.config
```

宿主与容器两套路径各写一条，`<gitdir>/worktrees/*.path` 也补一条（v6.0.1 的 #2327 就是为 worktree 支持），子模块则往各自的 `.git/modules/<name>/config` 里写同样的一对。这也是"后续 `git fetch`、`git push` 不需要改 workflow 写法"能成立的原因。git 读配置时按当前仓库目录匹配 `includeIf`，条件不满足的那份凭据完全不参与，仓库自身的 config 里也就没有明文。

README 里那句"在 Docker container action 里跑认证 git 命令需要 Actions Runner v2.329.0 或更高"和这套机制是连着的。代码给容器写的凭据路径是 `/github/runner_temp/…`，而 v2.329.0 的发布说明里对应的一条正是 `Map RUNNER_TEMP for container action`。没有这个挂载，容器内的 `includeIf` 就指向一个不存在的位置。

清理发生在两个时点。`persist-credentials` 为 true 时，post-job 的 `cleanup()` 移除 `includeIf` 条目、删除 `http.…/.extraheader`，并删掉凭据文件——只删位于 `$RUNNER_TEMP` 之下的路径，别处的同名文件只记一条 debug 就跳过。设成 false 时不用等 post-job，`getSource()` 的 `finally` 里立刻 `removeAuth()`。

还有一条与认证相关的改写行为：没提供 `ssh-key` 时，`insteadOf` 会把 `git@github.com:` 开头的 URL 改写成 HTTPS。有 `workflowOrganizationId` 时还会多写一条 `org-<id>@github.com:` 的改写规则，覆盖企业内部以组织 ID 形式书写的 SSH URL。

## 一次真实流转：CI 在 fork PR 上突然红了

一个常见的预览部署 job，`pull_request_target` 触发，要拿 PR 头端代码构建预览：

```yaml
on:
  pull_request_target:
    branches: [main]
jobs:
  preview:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
        with:
          ref: ${{ github.event.pull_request.head.sha }}
      - run: npm ci && npx vite build
```

`ref` 指到的是 fork PR 的 head SHA，守护在解析输入阶段就把 job 判死，还没走到 fetch。日志里是原文这一段：

> Refusing to check out fork pull request code from a 'pull_request_target' workflow. This workflow runs with the base repository's GITHUB_TOKEN, secrets, default-branch cache scope, and runner access. Fetching and executing a fork's code in that trusted context commonly leads to "pwn request" vulnerabilities. To opt in, review the risks at https://gh.io/securely-using-pull_request_target and set 'allow-unsafe-pr-checkout: true' on the actions/checkout step.

按三条修法排一下优先级。真的只需要 base 代码（跑 lint、生成文档索引）就把 `ref` 删掉，让默认自检接管，守护根本不参与。需要 PR 的元数据而不需要它的代码时用事件负载（`github.event.pull_request.number`、标题、diff 统计），仍然不用 checkout。

确实必须构建 fork 代码，就把 job 拆成两半：低权限那一半用 `pull_request` 触发、跑不可信代码、只产出一个构建物；高权限那一半用 `workflow_run` 触发、只消费构建物、不 checkout fork 代码。`allow-unsafe-pr-checkout: true` 留给前两种都不适用的场景，加之前先确认这个 job 能读到哪些 secrets、`GITHUB_TOKEN` 有哪些权限、产物会不会被下游复用。

2026-07-14 的 AsyncAPI npm 包投毒事件就是这条链路的实际成本。Datadog Security Labs 的分析里，攻击者通过一个 fork PR 触发了项目 CI 里的 `pull_request_target` 文档预览 job（Netlify 部署），拿到发布机器人账号的凭据，再往 npm 上发包。checkout 的这道守护拦的是"拉取并执行 fork 代码"这一步，它不修复触发器选择本身。拆 job 那条设计约束，仍然得自己守。

## 输入参数速查

下表以 v7.0.1 的 `action.yml` 为准，21 个输入全部列出：

| 参数 | 默认值 | 作用 |
| --- | --- | --- |
| `repository` | `${{ github.repository }}` | owner/repo 形式的目标仓库 |
| `ref` | 触发事件对应的 ref 或 SHA | 要切到哪个分支、tag 或 SHA；跨仓库检出时用该仓库默认分支 |
| `token` | `${{ github.token }}` | 拉取用的 PAT（个人访问令牌） |
| `ssh-key` | 空 | 走 SSH 协议时的私钥 |
| `ssh-known-hosts` | 空 | 追加进 known_hosts 的主机公钥（可用 `ssh-keyscan` 生成）；github.com 的公钥始终隐式加入 |
| `ssh-user` | `git` | SSH 连接用户名 |
| `ssh-strict` | `true` | 严格主机密钥检查，加 `StrictHostKeyChecking=yes` 与 `CheckHostIP=no` |
| `persist-credentials` | `true` | 是否让后续 step 继续能用这份凭据；v6 起写入 `$RUNNER_TEMP` 下的独立文件 |
| `path` | 空（等价 `.`） | 相对 `$GITHUB_WORKSPACE` 的落盘路径，解析后仍须在工作区内 |
| `clean` | `true` | 复用工作区时先 `git clean -ffdx && git reset --hard HEAD` |
| `filter` | 空 | 部分克隆的 `--filter` 值，设置后覆盖 `sparse-checkout` 的效果 |
| `sparse-checkout` | 空 | 稀疏检出模式，逐行给 |
| `sparse-checkout-cone-mode` | `true` | cone 模式，把模式解释为目录 |
| `fetch-depth` | `1` | 拉多少层历史，`0` 为全历史 |
| `fetch-tags` | `false` | 即使 `fetch-depth > 0` 也拉 tag |
| `show-progress` | `true` | fetch 是否输出进度 |
| `lfs` | `false` | 是否下载 Git LFS 文件 |
| `submodules` | `false` | `true` 检出子模块，`recursive` 递归检出；深浅由 `fetch-depth` 决定 |
| `set-safe-directory` | `true` | 把仓库路径加进 `safe.directory` |
| `github-server-url` | 空 | 覆盖实例地址，默认取 `GITHUB_SERVER_URL` |
| `allow-unsafe-pr-checkout` | `false` | v7 新增，见前文 |

输出两个：`ref`（解析后实际使用的 ref）与 `commit`（`git log -1 --format=%H` 的结果）。`runs.using` 从 v5 起是 `node24`，对应 runner 最低 v2.327.1。

## 场景配置与各自的坑

下面每条示例都取自 README 的 Scenarios 节，坑点是按源码补的。

### 只拉根目录，或者只拉一个文件

```yaml
- uses: actions/checkout@v7
  with:
    sparse-checkout: .
```

```yaml
- uses: actions/checkout@v7
  with:
    sparse-checkout: |
      README.md
    sparse-checkout-cone-mode: false
```

cone 模式（默认开）把每条模式解释成目录，所以要精准匹配单个文件必须关掉。两个额外事实：设置了 `sparse-checkout` 且没设 `filter` 时，fetch 会自动带上 `--filter=blob:none`，省的不只是检出而是对象下载；稀疏检出要求 runner 上的 git ≥ 2.28，低于它直接报 `Minimum Git version required for sparse checkout is 2.28.`。把稀疏结果交给 `docker build` 前，先确认 Dockerfile 里的 `COPY` 路径仍在，被排除的目录不会进构建上下文。

### 拉全历史，以及 tag

```yaml
- uses: actions/checkout@v7
  with:
    fetch-depth: 0
```

`fetch-depth: 0` 用的是 `+refs/heads/*:refs/remotes/origin/*` 加 tag refSpec 的组合。工作区是复用的、上一次留下 `.git/shallow` 时，这一次会补 `--unshallow` 把历史补全，而不是重新 clone。

反过来，浅克隆场景下 tag 拿不到不是配置错了：`fetch` 命令恒定带 `--no-tags`，tag 只在 `fetch-tags: true` 或 refspec 明确命中时才进来。`npm version`、`lerna version` 这类要读 tag 的命令，以及 `git tag --list`、`git describe`，都需要显式加 `fetch-tags: true` 或者 `fetch-depth: 0`。

### 看父提交，以及 diff

```yaml
- uses: actions/checkout@v7
  with:
    fetch-depth: 2
- run: git checkout HEAD^
```

默认的 1 层只包含触发 commit 本身，`HEAD^` 和 `git diff HEAD~1` 都会失败。要跨 base 分支比较，`fetch-depth: 0` 通常比猜层数省事。

### PR 的 head，与 PR 关闭事件

```yaml
- uses: actions/checkout@v7
  with:
    ref: ${{ github.event.pull_request.head.sha }}
```

`pull_request` 触发器下默认检出的是 merge commit，不是 PR 自己的 head。也可以写 `ref: ${{ github.head_ref }}` 拿源分支名——注意这个值不带 `refs/heads/`，`getCheckoutInfo()` 会先找 `origin/<name>`，再找同名 tag，都找不到才报 `A branch or tag with the name '…' could not be found`。

PR 被合并时触发的 `closed` 事件上，`github.context.ref` 是不带前缀的分支名，源码里有一段专门把它补回 `refs/heads/<name>`。自己写 `workflow_run` 或 `pull_request_target` 逻辑时同样会碰到这种形状差异，别假定 `context.ref` 总是 `refs/...` 形式。README 另外给了一节把 `closed` 加进 `types` 的 workflow 写法。

### 多仓库：并列、嵌套、私有

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

并列写法给主仓库也显式设 `path`；嵌套写法让第二个仓库落在第一个里面。私有或内部仓库要自带 PAT：README 明确写着 `${{ github.token }}` 的作用域限于当前仓库。`path` 会被解析成绝对路径再校验是否仍在工作区内，越界直接抛 `Repository path '…' is not under '…'`，所以 `../` 走不通。

### 子模块

```yaml
- uses: actions/checkout@v7
  with:
    submodules: recursive
```

实际执行的是 `git submodule sync`、`git submodule update --init --force`（`fetch-depth > 0` 时带 `--depth`）、以及一次 `submodule foreach 'git config --local gc.auto 0'`。`true` 与 `recursive` 的差别只在要不要递归，浅不浅由 `fetch-depth` 决定。凭据方面，`persist-credentials` 为 true 时每个子模块的 `.git/modules/<name>/config` 都会被写入指向共享凭据文件的 `includeIf`。

### 往回推 commit

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

`contents: write` 是前提。`github-actions[bot]` 的邮箱格式是 `{user.id}+{user.login}@users.noreply.github.com`，README 注明这套账号信息在 GHES（GitHub Enterprise Server）上不适用。

要在 PR 触发器下把 commit 推回 PR 源分支，得加 `ref: ${{ github.head_ref }}`。原因在 `getCheckoutInfo()`：`refs/heads/*` 会走到 `git checkout --force -B <branch> refs/remotes/origin/<branch>`，真正建出本地分支；而 PR 默认的 `refs/pull/<N>/merge`、tag 和裸 SHA 都是分离头指针（detached HEAD），此时 `git push` 没有上游分支可推。

## clean 与 set-safe-directory 的实际作用范围

`clean` 只在工作区已存在时起作用，且它的范围比参数名暗示的窄。`prepareExistingDirectory()` 无论 `clean` 是什么都会做三件事：把 HEAD 切成分离状态、删掉全部本地 `refs/heads/*`、删掉与目标分支前缀冲突的 `refs/remotes/origin/*`，另外清掉上次崩溃留下的 `.git/index.lock` 与 `.git/shallow.lock`。`clean` 决定的是最后那步 `git clean -ffdx && git reset --hard HEAD`。

因此 `clean: false` 保留的是未被跟踪的文件和上一次运行留下的构建产物，本地分支和最终的 `git checkout --force` 仍然会被改写。想在 step 之间留文件本来就不需要它——同一个 job 里 checkout 只跑一次。反过来在 self-hosted runner 上，`clean: false` 加上工作区复用会让上一次残留继续参与构建，这是"本地能过、CI 挂"的常见来源之一。`git clean` 本身失败时（源码列的三类原因：路径过长、权限、文件被占用，Windows 上尤其常见）会看到 `Unable to clean or reset the repository. The repository will be recreated instead.`，整个目录内容被清空重建。子模块状态检查没过时也会走同一条重建路径，日志里多一句 `Bad Submodules found, removing existing files`。

`set-safe-directory` 的作用范围更值得说清。它确实执行 `git config --global --add safe.directory <path>`，但"global"落到了一个临时位置上：`configureTempGlobalConfig()` 在 `$RUNNER_TEMP/<uuid>/` 下建目录，把真实 `~/.gitconfig` 复制进去，再把 git 子进程的 `HOME` 指过去。收尾时 `removeGlobalConfig()` 撤销这个 `HOME` 覆盖并删除整个临时目录。

两个推论。一是它不污染 runner 镜像的全局配置，关不关它都不影响 `~/.gitconfig`；源码注释给的理由是容器 job 里换了一个用户执行 git 时的所有权不匹配。二是这个 `safe.directory` 只在 Action 自己的 git 调用里有效，你自己的 `run:` 步骤读不到它。在容器 job 里遇到 `dubious ownership` 时，仍需在那个 step 内自己加一条，这是把这个参数调 `false` 之后也不会消失的一层。

这条保护来自 git 自身：当仓库目录的所有者与当前用户不一致时，git 会拒绝在该目录上操作，除非它出现在 `safe.directory` 列表里。`actions/checkout` 能做的只是让自己的调用先通过这道检查，它没有义务、也没有办法替你后面的 step 安排这件事。

## 认证与权限

`token` 与 `ssh-key` 是两条路径，选哪条取决于下游要做什么。

只用默认 `GITHUB_TOKEN` 覆盖大多数情况：CI 本身不 push 时，凭据在 post-job 清掉，不需要额外管理。要 push 回同一仓库时仍然用它，但 job 的 `permissions` 得升到 `contents: write`，并且把需要写的 job 单独拆出来。跨私有仓库要自带 PAT（`token: ${{ secrets.GH_PAT }}`），README 建议用服务账号并按最小 scope 生成。必须走 SSH 时给 `ssh-key`，用 `ssh-known-hosts` 注入主机公钥；确实要跳过严格检查再关 `ssh-strict`，这通常只在 known_hosts 无法预置的 self-hosted runner 上才需要考虑。

`github-server-url` 不是 GHES 必填项。`getServerUrl()` 的取值顺序是：显式输入 → `GITHUB_SERVER_URL` → `https://github.com`。GHES 的 runner 本来就会导出指向自己实例的 `GITHUB_SERVER_URL`，需要显式设置的场景是从 A 实例的 workflow 里去拉 B 实例的仓库。

触发器层面的边界和认证直接相关：fork 的 PR 在 `pull_request` 下 `GITHUB_TOKEN` 只读、secrets 不可用；`pull_request_target` 才切换到 base 仓库的令牌与 secrets，v7 的守护就是把"在这种上下文里拉 fork 代码"这一步收进一次显式确认。

不管是哪种认证，README 建议的权限都是最小一条：

```yaml
permissions:
  contents: read
```

## 排查：把日志里的句子对上原因

| 日志里的句子 | 直接原因 | 改法 |
| --- | --- | --- |
| `Refusing to check out fork pull request code from a '…' workflow.` | 事件是那两个触发器之一，且 `repository`/`ref`/commit 命中了 fork PR 的目标 | 按前文三种修法选一种；实在需要才 `allow-unsafe-pr-checkout: true` |
| `The ref '…' does not point to the expected commit '…'. The ref may have been updated after the workflow was triggered.` | 触发之后分支被推新或 tag 被移动，fetch 完校验没过 | 需要"当时那一刻"就 pin SHA；需要最新就接受重跑；tag 场景检查是否被移动过 |
| `A branch or tag with the name '…' could not be found` | 不带前缀的 `ref` 既没找到 `origin/<name>` 也没找到同名 tag | 写成 `refs/heads/<name>`，或补 `fetch-depth: 0` 让宽 refSpec 能命中 |
| `Minimum Git version required for sparse checkout is 2.28.` | runner 镜像里的 git 太旧 | 升级镜像，或去掉 `sparse-checkout` |
| `Input 'submodules' not supported when falling back to download using the GitHub REST API.` | PATH 里没有 git 2.18+，走了归档下载，而归档里没有 `.git` | 把 git 装进 PATH；注意同样情况下 `ssh-key` 也会直接报错 |
| `Unable to clean or reset the repository. The repository will be recreated instead.` | `git clean -ffdx` 或 `git reset --hard` 失败 | 查路径长度、权限、被占用文件；self-hosted 上考虑换隔离的工作区 |
| `Unable to turn off git automatic garbage collection. …` | `git config gc.auto 0` 没写进去 | 只是提示 fetch 可能被 GC 拖慢，不影响正确性 |
| 私有子仓库拉不下来 | 默认 `${{ github.token }}` 作用域限于当前仓库 | 给那一步单独 `token: ${{ secrets.GH_PAT }}` |

日志级别也值得一记：`RUNNER_DEBUG=1`（或仓库 secrets 里的 `ACTIONS_RUNNER_DEBUG`）会把 `core.debug` 的内容放出来，包括解析出的 `ref`/`commit`、凭据文件路径、以及 `Unable to delete '<lock>'. …` 这类默认不显示的行。

## 采用顺序与适用边界

按改动收益从大到小排，前三条对绝大多数仓库就够了。

1. 先确认版本形态：pin 到 major tag 还是 SHA，各自在 2026-07-20 之后拿到什么。列出所有 `pull_request_target` 与 `workflow_run` 的 workflow，逐个看它们 checkout 的目标是不是 fork 代码。
2. 把 `permissions: contents: read` 补到每个 workflow 顶层，需要写的 job 单独提出来。
3. 需要历史或 tag 时才动 `fetch-depth` 与 `fetch-tags`，其余情况留在默认的 1。
4. 把 checkout 升到 v5 及以上之前核对 self-hosted runner 版本（`node24` 运行时要求 runner ≥ v2.327.1），容器 job 里要跑认证 git 命令则核对 ≥ v2.329.0。
5. 已经在 v6 以上的仓库，可以顺手检查有没有 step 依赖 `.git/config` 里的凭据明文——那部分在 v6 之后不再存在。

适合它的：任何 GitHub Actions workflow 的第一步；跨仓库拉取；PR head 检出；文档类项目的稀疏检出。

不适合它的：装依赖与缓存（`actions/setup-*`、`actions/cache`）；下载 release 产物（`gh release download`、`actions/download-artifact`）；调用 REST API 做写操作；以及在不拆分 job 的前提下执行 fork 代码。

维护上还有一点背景：这个仓库的 README 里明确写着当前不接受贡献，只保留安全更新与重大破坏性修复。想提 PR 或等社区修复不如去 Community Discussions 报问题，也正因为如此，源码级的排查比等 issue 关闭更实际。

## 常见问题

**Q1：我只把版本写在 `@v4`，为什么突然收到 fork PR 被拦的错误？**

不是升级。2026-07-20 起这条保护被回移植到除 v1 外的所有受支持 major，`refs/tags/v4` 已经移到 v4.4.0。浮动 major tag 会自动指向它。pin 到具体 SHA 或 minor/patch 的不会自动获得。

**Q2：`persist-credentials: false` 之后还要 push 怎么办？**

在 push 前自己把凭据配回去，两条写法：按 Action 的做法写 `http.<origin>/.extraheader`，值是 `AUTHORIZATION: basic ` 加上 `x-access-token:<token>` 的 base64；或者改 remote URL 带上令牌。后者会把令牌放进 argv，Action 自己避开了这条路，你在带进程审计的环境里也最好避开。

**Q3：`pull_request` 和 `pull_request_target` 到底差在哪？**

前者用 fork 的 commit 与只读令牌，secrets 不可用；后者用 base 仓库的 ref、令牌与 secrets。要在高权限上下文里跑不可信代码就有 pwn request（把恶意 PR 代码喂给可信 job 的攻击套路）风险，v7 的守护针对的正是这一步。

**Q4：tj-actions/changed-files 那次（CVE-2025-30066）是同一个套路吗？**

不是，别把它当 v7 这条默认变更的动机。那次是 Action 自身的发布物被投毒。攻击者改动了 `v1.0.0`、`v35.7.7-sec`、`v44.5.1` 这些 tag，让它们指向同一个恶意提交；下游 workflow 拉到被改写的版本后执行了一段内存扫描脚本，把 runner 进程里的 secrets 打进日志。窗口是 2025-03-14 到 03-15，v46.0.1 修复。它支持的是另一条结论：tag 可被移动，pin 到 commit SHA 比 pin 到标签更可靠。

**Q5：为什么我关了 `clean` 还是丢了本地分支？**

`clean` 不管这一层。复用工作区时 `prepareExistingDirectory()` 总会切到 detached HEAD、删掉所有本地 `refs/heads/*`、再清掉 lock 文件。想保住本地分支不要依赖工作区复用。

**Q6：v4 到 v7 能直接跳吗？**

每个 major 的 `action.yml` 都带着自己的 `runs.using`（v2 是 node12，v3 node16，v4 node20，v5 起 node24），跨 major 前先在测试 workflow 上跑一遍。README 的 What's new 节按版本列了差异，`CHANGELOG.md` 能查到每个改动对应的 PR。

## 六个自测题

**1. `pull_request_target` 下写一句裸的 `- uses: actions/checkout@v7`（不带任何输入），会被 v7 拦住吗？为什么？**

<details>
<summary>答案</summary>
不会。`repository` 未改且 `ref` 未填时 `isDefaultCheckout` 成立，守护不运行；解析出的目标就是 GitHub 设定的可信 base ref，拉到的正是 base 分支。
</details>

**2. 守护判定"这是 fork PR"用的是仓库名字还是仓库 ID？为什么这个区别重要？**

<details>
<summary>答案</summary>
用 ID：`repository.id` 对比 `pull_request.head.repo.id`（`workflow_run` 下是 `workflow_run.head_repository.id`）。名字可以相同、可以改名、大小写也可能被拿来做文章，ID 是唯一且稳定的。同一仓库内部的 PR 因此天然不在此列。
</details>

**3. 为什么 `fetch-depth: 1` 下 `git describe --tags` 会失败？该改哪个参数，而不是简单调大 `fetch-depth`？**

<details>
<summary>答案</summary>
因为 fetch 恒定带 `--no-tags`，tag 对象根本没进本地。补 `fetch-tags: true` 就够，不必把历史层数拉高，代价更小。
</details>

**4. v6 之后凭据文件的命名和位置是什么？`.git/config` 里还剩什么？**

<details>
<summary>答案</summary>
`$RUNNER_TEMP/git-credentials-<randomUUID>.config`。`.git/config` 里只剩指向它的 `includeIf.gitdir:…/path` 条目（宿主、worktree、容器、子模块各若干），没有明文凭据。
</details>

**5. 在容器 job 里遇到 `dubious ownership`，把 `set-safe-directory` 设成 `true` 能解决吗？**

<details>
<summary>答案</summary>
不能。Action 写的 `safe.directory` 落在 `$RUNNER_TEMP/<uuid>/.gitconfig`，只对 Action 自己的 git 调用有效，收尾时连目录一起删。用户 step 里要自己执行一次 `git config --global --add safe.directory`。
</details>

**6. 要往 PR 源分支推 commit，为什么必须给 `ref`？**

<details>
<summary>答案</summary>
默认检出的 `refs/pull/<N>/merge` 走的是分离头指针路径，没有可推的上游分支。`ref: ${{ github.head_ref }}` 让 `getCheckoutInfo()` 命中 `origin/<name>`，实际执行 `git checkout --force -B <branch> refs/remotes/origin/<branch>`，建出可推的本地分支。
</details>

## 下一步读什么

想继续往下钻，按问题类型挑入口，都比读参数表划算：

- 想知道守护的准确边界：`src/unsafe-pr-checkout-helper.ts`，88 行一次读完，配套的 `src/input-helper.ts:176-200` 是调用点和短路条件。
- 想知道凭据到底写了什么：`src/git-auth-helper.ts`，看 `configureToken()`、`getCredentialsConfigPath()`、`removeToken()` 三处。
- 想搞清楚为什么检出成了 detached：`src/ref-helper.ts` 的 `getCheckoutInfo()` 与 `getRefSpec()`，两者一起读能顺便解释 tag 为什么默认拿不到。
- 想查某个行为从哪个版本开始：仓库根目录的 `CHANGELOG.md` 按版本列改动并附 PR 链接，比 README 的 What's new 更细。
- 想看 GitHub 侧对整个 pwn request 模式的说明：文档《Securely using `pull_request_target`》（https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target ），`allow-unsafe-pr-checkout` 的提示文本里那个 `gh.io` 短链就指向它。

## 参考资料

以下链接均在 2026-09-19 逐条访问确认可达（HTTP 200）。

- actions/checkout 仓库、README 与全部输入参数：<https://github.com/actions/checkout>
- 源码：`src/unsafe-pr-checkout-helper.ts`、`src/input-helper.ts`、`src/git-auth-helper.ts`、`src/git-directory-helper.ts`、`src/ref-helper.ts`（v7.0.1 标签，非 main）
- `CHANGELOG.md` 与 release 记录（v7.0.0 于 2026-06-18 发布；v7.0.1、v6.1.0、v5.1.0、v4.4.0、v3.7.0、v2.8.0 于 2026-07-20 依次发布）：<https://github.com/actions/checkout/releases>
- GitHub Changelog：Safer `pull_request_target` defaults for GitHub Actions checkout（含 2026-07-15 编辑注与 v1 例外）：<https://github.blog/changelog/2026-06-18-safer-pull_request_target-defaults-for-github-actions-checkout/>
- 官方安全指引《Securely using pull_request_target》：<https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target>
- Actions Runner v2.327.1（node24）与 v2.329.0（`Map RUNNER_TEMP for container action`）：<https://github.com/actions/runner/releases/tag/v2.329.0>
- GHSA-mrrh-fwg8-r2c3 / CVE-2025-30066，tj-actions/changed-files 被投毒事件：<https://github.com/advisories/GHSA-mrrh-fwg8-r2c3>
- Datadog Security Labs 对 2026-07-14 AsyncAPI npm 包投毒事件的分析：<https://securitylabs.datadoghq.com/articles/compromised-asyncapi-npm-packages/>

核对方式记一句：版本形态用 `git ls-remote --tags` 看浮动 tag 的实际指向，跨版本差异解包对应 tag 的 `action.yml` 比对，行为断言以 `src/` 下的具体函数为准——仓库文档给结论，代码给事实。
