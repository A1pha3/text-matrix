---
title: "tech-leads-club-release-bot：一个闭源 GitHub App 背后的开源发布流水线"
date: 2026-05-17T20:25:00+08:00
lastmod: 2026-10-03
slug: "tech-leads-club-release-bot-github-automation-guide"
github_repo: "tech-leads-club/agent-skills"
source_key: "gh:tech-leads-club/agent-skills"
description: "tech-leads-club-release-bot 本体闭源，但它驱动的 agent-skills 发布流水线完全开源：GitHub App 身份层、Nx Release 分组发布、Snyk Agent Scan 前置门禁与防自触发设计，本文逐层拆解"
draft: false
categories: ["技术笔记"]
tags: ["CI/CD", "GitHub Actions", "Nx", "TypeScript"]
---

# tech-leads-club-release-bot：一个闭源 GitHub App 背后的开源发布流水线

先说结论：**tech-leads-club-release-bot** 这个 GitHub App 本体并不开源（Tech Leads Club 组织下的公开仓库里找不到它的源码），它值得解读的地方在于用法——它所驱动的 [agent-skills](https://github.com/tech-leads-club/agent-skills) 发布流水线完全开源，完整展示了多包 monorepo 如何做到**权限精控、安全扫描前置、防自触发**这三件事。任何维护多包 npm 项目、又要往发布链路里塞安全门禁的团队，都能直接从这套 workflow 里抄作业。

本文机制描述以文章发表时点的 workflow 快照为基准（commit `81e7e0dd`，2026-04-28），仓库读数与演进状态截至 2026-10-03 刷新。

## 系统地图：谁在干什么

这套体系里容易混为一谈的角色，实际分工是：

| 层 | 承担者 | 职责 |
|------|------|------|
| 身份层 | tech-leads-club-release-bot（GitHub App） | 在 workflow 内换取短期 token，提供 git 提交身份与推送权限 |
| 触发层 | GitHub Actions（release.yml 的 `on` 段） | 监听 push / pull_request / merge_group 三类事件 |
| 发布引擎 | Nx Release（`npx nx release`） | 版本计算、changelog、tag、npm publish，按分组执行 |
| 安全门禁 | 自研编排器 scan-skills.ts + Snyk Agent Scan | 逐技能扫描，critical/high 阻断发布 |
| 审批层 | GitHub Environments（`publish` 环境） | 发布前人工审批 |
| 旁路 | snapshot job | PR 打 label 即发测试版本，不进正式发布链 |

注意一个关键澄清：**App 不订阅任何 webhook**。workflow 的触发靠 GitHub Actions 自身的事件机制，App 的全部作用发生在 workflow 运行期间——被 `actions/create-github-app-token` 换成一个一小时有效的 token。原文常见"bot 订阅 push 事件"的说法，是把 workflow 触发器和 App webhook 混为一谈了。

## 它服务的仓库：agent-skills

agent-skills 是一个面向专业 AI 编程 Agent 的技能库（README 自我定位是 "The secure, validated skill registry for professional AI coding agents"），支持 Claude Code、Cursor、Copilot、Windsurf 等约 20 个代理工具。仓库 2026-01-19 创建，截至 2026-10-03 有 7,024★、558 forks，MIT 许可，TypeScript 为主，累计发出 81 个 release。

`packages/` 下有四个包：`cli`、`skills-catalog`、`mcp`、`marketplace`（部署到 GitHub Pages 的技能市场站点），外加共享库 `libs/core`。其中三个走 npm 发布，在 `nx.json` 里注册为三个 release 分组，tag 模式各不相同：

| 分组 | npm 包 | tag 模式 | 触发路径 |
|------|------|------|------|
| cli | @tech-leads-club/agent-skills | `v{version}` | packages/cli/ 或 libs/core/ 变更 |
| skills-catalog | @tech-leads-club/skills-catalog | `skills-catalog-v{version}` | packages/skills-catalog/ 变更 |
| mcp | @tech-leads-club/agent-skills-mcp | `mcp-v{version}` | packages/mcp/ 或 libs/core/ 变更 |

marketplace 不发布 npm，由单独的 deploy-marketplace.yml 部署。截至 2026-10-03，三个包在 npm 上的最新版本分别是 1.4.10、0.17.8、0.1.6——三个版本号完全独立，这正是分组发布的结果。

多包项目的发布痛点在这里具体化为四条：三个包的版本联动但又不必同步发版（CLI 和 MCP 都依赖 libs/core，改一次核心库可能两个都要发）；发布前必须过安全扫描（技能库是提示词供应链，被投毒的技能会直接进入用户的 agent 上下文）；PR 阶段需要可安装的测试版本；bot 自己 push 的 release commit 不能再次触发发布。后面逐一对应到机制。

## 身份层：GitHub App 干的三件事

用 GitHub App 而不是 Personal Access Token，收益是通用的：权限按仓库粒度授予、操作归属显示为 `app[bot]` 而非个人账号、token 由 JWT 换取且一小时自动过期。这套 workflow 里 App 的作用集中在三处：

```yaml
- name: Generate App Token
  uses: actions/create-github-app-token@v1
  id: app-token
  with:
    app-id: ${{ secrets.RELEASE_APP_ID }}
    private-key: ${{ secrets.RELEASE_APP_PRIVATE_KEY }}
```

其一，token 生成。release 和 snapshot 两个 job 都先换取 App token，再把它同时用在 checkout（拉代码）和 `GITHUB_TOKEN` 环境变量（nx release 调 GitHub API 建 release）上。

其二，git 身份。提交者信息不在 workflow 里逐条配置，而是封装在 `.github/actions/setup` 这个 composite action 中，由 `git-config: true` 输入触发：`user.name` 设为 `<app-slug>[bot]`，email 用 GitHub 官方的 noreply 域名，remote 换成 `x-access-token:<token>` 形式。这也是一处容易误读的地方——你在 agent-skills 的 release.yml 里找不到 `git config` 命令，它在 composite action 里。

其三，防自触发的主体。这层设计值得单独展开。

## 防自触发：为什么需要，怎么做的

问题的根源恰恰来自 App 的优势本身。GitHub Actions 的默认 `GITHUB_TOKEN` push 的 commit 不会触发新 workflow，这是平台层保护；但 App token 或 PAT push 的 commit **会**触发。一旦用上 App token，"bot 发布 → push release commit → 又触发发布"的死循环就打开了，必须自己关上。

关闭方式是两个过滤条件的组合，出现在 approve-release 和 security-scan 两个 job 的 `if` 里，workflow 原文共四行：

```yaml
if: |
  github.event_name == 'push' &&
  github.ref == 'refs/heads/main' &&
  github.actor != 'tech-leads-club-release-bot[bot]' &&
  !startsWith(github.event.head_commit.message, 'chore(release):')
```

双重保险各有分工：actor 检查防住 bot 账号发起的一切事件，commit message 前缀检查防住"人以 bot 的提交消息格式手动 push"的漏网情况——bot 的发布提交统一用 `chore(release):` 前缀（包括自动提交的技能数据更新 `chore(release): update generated skills data`），消息不符合前缀才算人工改动。release job 本身没有 `if`，它靠 `needs: [approve-release, security-scan]` 依赖传导：上游两个 job 被 skip，下游自然不运行。

这里还有一个容易忽略的细节：release job 的 checkout 用了 `filter: tree:0`（部分克隆，只取提交与目录树、不取文件内容）配合 `fetch-depth: 0`（完整历史）。前者省流量，后者是硬需求——Nx 的变更检测和 release 的 tag 比较都要读完整 git 历史。

## 发布引擎：分组检测与 Nx Release

`npx nx release` 是整个体系里唯一管版本的工具（README 挂着 semantic-release 的徽章，但仓库依赖里没有 semantic-release——徽章表达的是"遵循 Conventional Commits 语义化发布"的理念，引擎是 Nx Release）。workflow 在调用它之前，先自己算清楚"这次该发哪几组"：

```bash
# 每组找到自己前缀的最新 tag，再 diff 判断有无源码变更
CLI_TAG=$(git tag --sort=-creatordate --list 'v[0-9]*' | head -1)
CLI_CHANGES=$(git diff --name-only "$CLI_TAG"..HEAD -- packages/cli/ libs/core/ | head -1)
[ -n "$CLI_CHANGES" ] && GROUPS_TO_RELEASE="cli"
# skills-catalog 与 mcp 同理，路径列表拼接进 GROUPS_TO_RELEASE

# 最终一次调用，只发有变更的组
npx nx release --yes --groups=$GROUPS_TO_RELEASE
```

三组各自独立判断，`libs/core` 同时挂在 cli 和 mcp 的检测路径里——核心库一动，两个下游组都进入候选。没有任何组有变更时，整个发布静默跳过。publish 阶段带 `NPM_CONFIG_PROVENANCE: true`（npm provenance 出处证明，这也是 workflow `permissions` 段里 `id-token: write` 的用途），并有一条贯穿全 workflow 的回退：每条 `npx nx` 命令失败时用 `|| NX_NO_CLOUD=true ...` 重跑一遍，让 Nx Cloud 不可用的环境照样能发。

整个 main 分支发布链的编排：

```text
push to main（非 bot、非 release commit）
        │
        ├─► approve-release   environment: publish，人工审批
        ├─► security-scan     Snyk Agent Scan，critical/high 即失败
        │
        └── needs 两者全部成功 ──► release
                                     ├─ generate:data（重新生成注册表数据）
                                     ├─ 有变更则 bot 身份提交
                                     ├─ 分组检测
                                     └─ nx release --groups=...
```

merge_group 事件有独立的 security-scan-merge-queue job：走 Merge Queue 的 fork PR 能用上基础仓库的 secrets 完成合并前扫描——fork PR 默认拿不到 secrets，这是官方给的解法。

## 安全门禁：比"Snyk 扫描"更具体的机制

把 security-scan job 展开看，扫描不是简单调一次 Snyk CLI。实际结构是三层：

**编排器**是仓库自研的 `packages/skills-catalog/src/scan-skills.ts`（Nx target `security-scan`），逐个技能调用底层扫描器：`uvx snyk-agent-scan@latest --skills <dir> --json`。底层工具即 Snyk Agent Scan，源码注释标注它的前身是 mcp-scan——一个专为 MCP/Agent 生态做提示词注入与恶意行为分析的开源扫描器，所以扫描结果的结构里保留着 `risk_score`、`thought_process` 这类 LLM 分析痕迹。`SNYK_TOKEN` 是硬依赖，缺失直接报错退出。

**增量缓存**按技能内容哈希工作：内容没变的技能直接读缓存，变了的才重新扫。有一处反直觉的设计：扫描器自身的基础设施错误（`SCANNER_PROCESS_FAILED`、`SCANNER_MISSING_OUTPUT` 等五种 `SCANNER_*` 错误码）不会被写入缓存，下次运行自动重试——扫描失败和"扫出问题"是两回事，前者不该被记住。

**豁免机制**走 `security-scan-allowlist.yaml`：误报的第一方集成可以登记豁免，条目要求写明 `allowedBy`、`allowedAt`，可选 `expiresAt`。本地跑 `npm run scan -- --update-allowlist` 可以交互式添加。

阻断线设在 critical/high：workspace 根目录的 `.security-scan-results.json` 被读出来、按严重度打印、`exit 1` 失败整个 job。CI 里并行度 `PARALLEL_JOBS: 8`，本地默认 `min(CPU 核数, 10)`。

对于"技能库"这个特定场景，这套门禁的存在理由写在 README 里：引用 Snyk Agent Scan 团队的报告，公开市场上 13.4% 的技能含有严重问题。扫描前置于发布，意味着每个 npm 版本里的技能都过了同一道闸。

## 旁路：label 触发的 snapshot 发布

正式发布链之外还有一条测试版通道。给 PR 打上 `action: snapshot` label，独立的 snapshot job 就会：

1. 用 `check-ci-status` action 确认该 PR 的 CI 已通过；
2. checkout PR 分支本身（不是 main）；
3. 计算版本号 `0.0.0-pr<PR号>.<短SHA>`，例如 `0.0.0-pr123.abc1234`，用 `nx release version` 写入但不建 tag 不提交（`--git-tag=false --git-commit=false --stage-changes=false`）；
4. `nx release publish --tag snapshot --provenance` 发布到 npm 的 `snapshot` dist-tag；
5. 回到 PR 评论安装命令，并移除 label 防止重复触发：

```text
🚀 Snapshot Published!
npm install @tech-leads-club/agent-skills@0.0.0-pr123.abc1234
```

`0.0.0-` 前缀保证 semver 上永远低于任何正式版，测试者显式指定 `@snapshot` 或完整版本号才装得到。

## 一次合并的完整旅程

把机制串起来：贡献者向 agent-skills 提交一个新技能，PR 触发 ci job（lint、test、build、技能结构校验、安全扫描），维护者审查后打上 `action: snapshot` label——CI 已过，job 检出 PR 分支，发布 `0.0.0-pr124.xxxx` 到 npm snapshot tag，PR 下出现安装命令，label 自动移除。维护者实测没问题，合并进 main。

main 上的 push 同时点亮 approve-release（publish 环境等审批）和 security-scan（全量技能增量扫描）两个 job。审批人确认、扫描通过后，release job 启动：重新生成技能注册表数据，若数据有变则以 bot 身份提交；随后分组检测发现 `packages/skills-catalog/` 相对 `skills-catalog-v0.17.8` 有变更、其余两组无变化，于是执行 `npx nx release --yes --groups=skills-catalog`——算版本、写 changelog、打 `skills-catalog-v0.17.9` tag、发布 npm，全部以 bot 身份完成。

最后这个 push 带着干净的 `chore(release):` 前缀回到 main，workflow 再次被触发，但 actor 检查和消息前缀检查双双拦截，approve-release 与 security-scan 被跳过，release 因 needs 不满足而终止。循环闭合。

## 复用这套架构需要准备什么

照着搭建一个同款，准备清单如下：

**Secrets**（仓库或组织级）：`RELEASE_APP_ID` 与 `RELEASE_APP_PRIVATE_KEY`（GitHub App 的 ID 和私钥，私钥在 App 设置页生成后下载 `.pem` 文件，**文件内容原样存入 secret 即可**，不需要任何预处理）；`SNYK_TOKEN`（Snyk 账户 token，扫描必需）；`NX_CLOUD_ACCESS_TOKEN`（可选，没有它 workflow 会走 `NX_NO_CLOUD=true` 回退路径）。

**App 权限**：从 workflow 的 `permissions` 段反推最低需求——`contents: write`（推 tag 与提交）、`pull-requests: write`（snapshot 评论）、`issues: write`（评论走 issues API）、`actions: read`（读 CI 状态）、`id-token: write`（npm provenance 签名）。`publish` 环境的审批人是 GitHub 环境配置，不是 App 权限。

**workflow 触发器**：`push`（限 main）、`pull_request`（含 labeled 事件）、`merge_group` 三项，与 release.yml 的 `on` 段一致。

**前置约束**：仓库须用 Nx（`nx.json` 里注册 release 分组），发布目标是 npm。Nx 之外的 monorepo 工具（Turborepo、pnpm workspace 等）没有等价的 `nx release --groups`，照搬前先确认这一层有替代。

## 定位：它不是 semantic-release 的替代品

| 特性 | 这套流水线 | release-please | semantic-release |
|------|------|------|------|
| 驱动方式 | GitHub App 身份 + Actions 编排 | GitHub Action / App | GitHub Action / CLI |
| 多包分组 | Nx groups，按 tag 前缀独立版本 | 单一版本流为主 | 支持 fixed/independent 模式，需配置 |
| 安全扫描前置 | Snyk Agent Scan 内建 | 无，自行集成 | 无，自行集成 |
| PR 快照版本 | label 触发，npm dist-tag | 无此概念 | 无内建等价物 |
| 防自触发 | actor + commit 前缀双重检查 | 依赖默认 token 的平台保护 | 同左 |

与两个老牌工具相比，这套设计的差异化不在版本计算（Nx Release 已经做了），而在把**身份、审批、扫描、快照**四件事压进同一条 workflow。release-please 和 semantic-release 处理"怎么发版本"是成熟的，但"发之前必须过什么"要自己往上叠。

## 采用建议

三类团队适合直接参考：Nx + npm 的多包 monorepo（机制可整体照搬）；技能/提示词/插件类供应链项目（安全扫描前置几乎是必选项，Snyk Agent Scan 的技能扫描方向恰好对口）；高频发版且发布需要人工审批的团队（environment gate 加 bot 身份是现成范式）。

两类团队不必急：单包项目（四个 job 的编排收益撑不起复杂度，semantic-release 更省事）；发版频率低、信任边界简单的内部项目（environment gate 之外的三层防护多数用不上）。

两点风险要如实说明：bot 本体闭源，你无法审计 App 自身的行为，能审计的只有它在 workflow 里的用法——对安全敏感场景，建议自建一个功能等价的 GitHub App（配置文件照 workflow 的引用关系抄即可）；agent-skills 仓库最后一次 push 是 2026-09-20，两个 release 组的 npm 包停在 8 月底，项目仍活跃但节奏放缓，抄作业时以当时最新的 workflow 为准。

这套流水线最值得带走的不是某个具体命令，而是一个判断：**当自动化系统持有写权限时，它自己的输出必须被自己的触发条件排除**。一个 `github.actor` 检查加一个 commit message 前缀，两组各四行的条件表达式，换来的是发布循环可以放心地全自动运转。
