---
title: "ClawSweeper：OpenClaw 的自动化维护机器人"
date: "2026-04-26T11:50:00+08:00"
lastmod: 2026-10-04T00:00:00+08:00
slug: clawsweeper-openclaw-automated-code-review
github_repo: "openclaw/clawsweeper"
source_key: "gh:openclaw/clawsweeper"
description: "ClawSweeper 是 OpenClaw 官方的保守派维护机器人：提案与执行分离，只在证据充分时关闭 Issue/PR，五个月里从单文件审查脚本长成带修复与 automerge 通道的多仓库维护平台。本文拆解它的双 Lane 架构、安全模型与演进过程。"
draft: false
categories: ["技术笔记"]
tags: ["OpenClaw", "代码审查", "自动化", "GitHub Actions", "Codex", "TypeScript"]
hiddenFromHomePage: false
---

[ClawSweeper](https://github.com/openclaw/clawsweeper) 是 OpenClaw 官方的维护机器人，README 对自己的定位是 "the conservative OpenClaw maintenance bot"——保守派。它不追求把积压清零，而是保证每一笔自动操作都有据可查、可撤销、可审计。

本文 2026 年 4 月 26 日发表时，它还是一个 13 个文件的仓库，`src/` 下只有一个 3,927 行的 `clawsweeper.ts`。到 2026 年 10 月 4 日复核时，仓库已膨胀到 1,900+ 文件，长出了第三条 Lane，接管了 `openclaw` 组织下一批仓库的日常维护。这是观察"AI 维护者"如何在真实仓库里长出信任边界的难得样本，所以这篇解读按双时点写：先讲发表时的架构（当时的事实以 `52bda011` 提交为锚），再讲五个月里它变成了什么。

## 问题有多大

积压的量级可以先感受一下。目标仓库 [openclaw/openclaw](https://github.com/openclaw/openclaw)（391,254 stars，2026-10-04 读数，下同）历史上累计的 Issue 编号已经超过 16.4 万——ClawSweeper 状态仓库里出现的最大编号是 #164725。2026 年 4 月 26 日发文当天，仓库 README 记录的开放项是 4,927 个 Issue 加 4,228 个 PR，共 9,155 项；复核当天，GitHub API 读数是 5,991 个开放 Issue 加 3,288 个开放 PR，共 9,279 项。半年过去，积压总量几乎没变——这正是它存在的意义：消化速度跟得上涌入速度。

人工逐条处理不可能，放任不管会让 bug 报告淹没在重复项里。ClawSweeper 的答案是让模型做判断，但把判断的每一次输出都写下来，把执行的每一次变更都锁起来。

## 设计原则：宁可放过，不可错杀

整个系统围绕一条纪律展开：**提案便宜，执行昂贵**。Review 阶段可以大量生成"这个可以关"的判断，因为那只是写文件；真正动 GitHub 的 Apply 阶段则要过一道道闸门。项目现在的 [VISION.md](https://github.com/openclaw/clawsweeper/blob/main/VISION.md) 把这个立场讲得很直白——"abundant intelligence, scarce trust"（智能充裕，信任稀缺）：模型调用越来越便宜，工程师时间和信任不会，所以凡是能用"模型判断 + 可审计输出"替代的机械逻辑都应该交给模型，而代码只保留给信任边界——认证、幂等、只追加的动作账本、花费上限和破坏性操作闸门。

落地形态是：每个被审查的 Issue/PR 生成一份 Markdown 报告，记录决策（keep_open 或 proposed_close）、证据摘要、建议评论、运行时元数据和 GitHub 快照哈希。发文时报告写在 `items/<number>.md`（关闭后移入 `closed/`）；现在路径变成了 `records/<repo-slug>/items/<number>.md`，因为一个机器人要同时伺候多个仓库。

## Review Lane：只提议，不关闭

Review Lane 是提案生产线，它从不关闭任何项。发文时的工作方式：

1. Planner 扫描全部开放项，把精确的项编号分配到分片（shard）；
2. 每个分片独立 checkout `openclaw/openclaw` 的 `main`；
3. Codex 逐项审查。当时用的模型是 `gpt-5.5`、high 推理档、fast 服务等级、单项 10 分钟超时——这四个值在当时的源码常量里写得明明白白（`DEFAULT_CODEX_MODEL`、`DEFAULT_REASONING_EFFORT`、`DEFAULT_SERVICE_TIER`）；
4. 审查结果落成报告文件，高置信度且政策允许的关闭判断标记为 `proposed_close`。

节奏覆盖不是一刀切，而是按活跃度分层。发文时 README 的快照：每小时档覆盖约 1%（活跃项），每日档覆盖 PR 和 30 天内新 Issue 的 98% 上下，每周档覆盖更老的沉寂 Issue。值得单说的是**每 5 分钟一班的热通道**（hot intake）——最新、最活跃的项走单独的低延迟队列，这在当时 workflow 的 cron（`*/5 * * * *`）里可以直接看到。只看"每小时/每日/每周"三层概括会漏掉这条最快的通道。

五个月后的变化集中在两点。一是模型与认证方式换代：直接 API 认证（`login` 和 `proxy` 模式）下改用 `gpt-6.1-sol`、medium 推理档；走 `clawrouter` 模式时用私有推理别名。服务等级也改成动态——维护者本人创建的项走 priority（fast），其余走 standard。二是容量显式化：全局 Codex worker 预算由 `config/automation-limits.json` 的 `workers.max` 控制，当前值 128，手动常规审查默认 89 个分片、热通道 44 个；调度通道有独立的 32 槽准入上限，整体瞄准每小时 220 次审查的准入目标。目标仓库还可以安装 dispatcher workflow，通过 `repository_dispatch` 把单条 Issue/PR 事件直接推过来，做到准实时的单项审查。

## Apply Lane：闸门后的执行侧

Apply Lane 读取现成报告，只在存量审查仍然有效时才动 GitHub。它负责：原地更新那条带标记的 Codex 审查评论（一项一条，不刷屏）、只关闭"报告生成后项没有变化"的高置信度提案、把已关闭的报告归档、把被重新打开的归档报告移回去并标记 stale。

发文时的运行参数：默认只关 Issue 不关 PR、无年龄下限、每次关闭间隔 2 秒、每个检查点最多 50 个新鲜关闭，达到上限就再排一轮同配置的 Apply。这些值与当时 workflow 定义的默认输入（`apply_kind: issue`、`apply_close_delay_ms: 2000`、`apply_checkpoint_size: 50`）一一对应。

现在有两处关键变化。其一，apply 每 15 分钟自动唤醒一次，没有待执行提案就快速空转退出；检查点配额从 50 降到 40，且是硬顶——为了让每个 GitHub App token 在生命周期内跑完。其二，**"默认只关 Issue"反转了**：现行 README 明确 apply 默认处理所有类型（`--apply-kind all`），按仓库配置文件（repository profile）收紧；`openclaw/clawhub` 和自审场景依然刻意更严格，只允许关闭"main 已实现"类 PR。

## 关闭条件：一张不断变长的清单

机器人何时可以提议关闭一个项？这是全文最值得盯住的部分，因为清单一直在变长。发文时的七类（键名以当时源码 `CloseReason` 类型为准）：

| 键名 | 含义 |
|------|------|
| `implemented_on_main` | 当前 main 分支已实现 |
| `cannot_reproduce` | 当前 main 分支无法复现 |
| `clawhub` | 更适合作为 ClawHub skill/plugin，而非核心问题 |
| `duplicate_or_superseded` | 重复，或已被某个规范 Issue/PR 取代 |
| `not_actionable_in_repo` | 描述具体但在本仓库无法执行 |
| `incoherent` | 语无伦次到无法采取任何行动 |
| `stale_insufficient_info` | 超过 60 天陈旧且信息不足以验证 |

顺带修正一个常见误读：网上流传的 `not_reproducible`、`better_for_clawhub`、`stale_older_than_60d` 等键名在源码里并不存在，写脚本解析报告时以上表为准。

现行清单在这七类之外新增了三条主要针对外部 PR 的：分支内容大多无关或不可合并的低信号 PR、要求真实行为证明（real-behavior proof）却始终没交且闲置 14 天以上的低评分外部 PR、以及搁置 30 天以上的 draft/等作者/检查失败的外部 PR。`closeReasonText` 函数里现在注册了 17 种关闭原因，还包括超大 PR（变更超过 5 万行在 hydration 之前就走独立通道提议关闭）、过期版本 bug、超出作者 PR 预算等，其中"产品方向未获维护者确认"和"作者 PR 预算"两条默认关闭，需要显式开启。

配套的保护规则也在加细：维护者创建的项，发文时的规则是"永不自动关闭"，现行措辞松动为"除非能验证该请求已在当前 main 实现"；用 `Fixes #123` 语法关联了开放 PR 的 Issue 保持开放，直到 PR 落地；同一作者的 Issue/PR 对一起保持开放；把一个 PR 关成"被另一个 PR 取代"时，系统会先验证那个"取代者"本身是活的——closed-unmerged、F 评分、不可合并的 PR 没有资格当规范目标。

## 安全模型：五层防线

发文时的五层防御，全部可以在当时的 README 和 workflow 里逐条对上：

1. **维护者保护**。作者关联为 OWNER、MEMBER 或 COLLABORATOR 的项不进入自动关闭（`MAINTAINER_AUTHOR_ASSOCIATIONS` 常量）。
2. **标签保护**。带 `security`、`beta-blocker`、`release-blocker`、`maintainer` 四个受保护标签之一的项不会被提议关闭。
3. **只读审查**。Codex 运行时不持有 GitHub 写 token；CI 把目标仓库检出设为只读；审查结束时如果发现 Codex 留下了跟踪或未跟踪的更改，本次审查直接判失败。
4. **快照验证**。每份报告记录审查时的 GitHub 快照哈希，Apply 前重新比对——快照变了就阻止执行，唯一放行的变化是机器人自己那条评论。这是乐观锁在自动化系统里的直接应用。
5. **审计**。`npm run audit`（现行 `pnpm run audit`）不动文件，只对比生成记录与 GitHub 实时状态，报告缺失开放记录、已归档开放记录、陈旧记录、重复项、受保护标签误提议、陈旧审查状态六类问题；缺失记录还会细分为 eligible、维护者创建、受保护、新创建四档，让严格模式只对真正的漂移报警。

五个月里这五层没有被拆掉，反而各自加厚：维护者身份从静态关联扩展为实时查权限（`write`/`maintain`/`admin` 任一即算）；审查环境新增了 checksum 钉死的 TruffleHog 3.97.4 秘密扫描前置——扫描不干净，模型根本看不到代码；Codex 的网络访问被收进代理白名单，只放行 GitHub、npm、Node、MDN 和 OpenClaw 文档，且仅限 GET/HEAD/OPTIONS；token 流向也收紧了——`OPENAI_API_KEY` 现在只喂给每任务一个的本地 Responses 代理，Codex 子进程继承的是代理环境的 `CODEX_HOME`，摸不到裸 key；GitHub App 不再回退 PAT 写 token，权限不足就在发 token 那一步失败。

## 五个月里长出来的：Repair Lane

这是发文时完全不存在的第三条 Lane，也是 ClawSweeper 从"审查机器人"变成"维护平台"的分水岭。维护者在目标仓库的 Issue/PR 评论里发命令（首选形式 `@clawsweeper ...`）：

```text
@clawsweeper review        # 重新审查，只读
@clawsweeper autofix       # 进入有界修复循环，不合并
@clawsweeper automerge     # 修复 + 门禁通过后自动合并
@clawsweeper approve       # 解除人工审查暂停，按正常门禁合并
@clawsweeper implement issue  # 为可行 Issue 开一个受守卫的实现 PR
@clawsweeper stop          # 摘掉修复标签，标记 human-review
```

autofix/automerge 的工作方式值得注意：Codex 负责 rebase、修 CI、回应审查意见、跑验证，产出一个结构化修复工件；但所有 GitHub 变更——推分支、打标签、合并——由确定性执行器（deterministic executor）完成。模型产出建议，代码执行变更，这条边界和 Review/Apply 的分离一脉相承。automerge 要等精确 head 审查、必需检查、可合并性、安全与策略门禁全部通过；贡献者分支推送前默认等 90 秒再拉一次 PR head，变了就重新排队。由 Issue 自动生成的 PR 打 `clawsweeper:autogenerated` 标签且永不自动合并。

配套的可观测面也建起来了：规范审查记录存在 Cloudflare Durable Object，快照到 R2，操作账本、发布资产和重试缓存放 R2 的 `ledger/v1/` 与 `artifacts/`；`openclaw/clawsweeper-state` 仓库承载仪表板渲染与剩余运营状态（state 分支现有 1.1 万+ 文件，audit 结果覆盖 `openclaw` 组织几十个仓库）；实时流水线仪表板在 [clawsweeper.openclaw.ai](https://clawsweeper.openclaw.ai/)，官网是 [clawsweeper.bot](https://clawsweeper.bot)。顺带一提，托管实例不为第三方仓库提供免费审查——想用就 fork 了在自己组织里部署。

## 运行数据

发文当天（2026-04-26 03:45 UTC README 快照）的仪表板读数：

| 指标 | 数值 |
|------|------|
| 近 7 天新鲜审查 | 8,957（Issue 4,855 + PR 4,102） |
| 提议关闭 Issue / PR | 569（11.7%）/ 140（3.4%） |
| 待执行关闭提议 | 709（7.9%） |
| 累计由 Apply 执行的关闭 | 7,992 |
| 失败/陈旧审查 | 27 |
| 近 24 小时审查 / 关闭决策 / 保持开放 | 11,094 / 2,527 / 8,567 |
| 近 24 小时实际关闭 / 评论同步 | 5,568 / 416 |

比例比绝对值更有信息量：Issue 的提议关闭率（11.7%）是 PR（3.4%）的三倍多——审查对 PR 明显更手软，符合"误关 PR 代价更高"的直觉。彼时文章举例的三条审查记录都真实可查：[#65156](https://github.com/openclaw/openclaw/issues/65156)（sqlite-vec 加载成功但未注册函数，SQLite ABI 不匹配，判 keep_open）、[#65123](https://github.com/openclaw/openclaw/pull/65123)（Discord 目标类型解析修复）、[#65115](https://github.com/openclaw/openclaw/pull/65115)（webchat Control UI 八个 GUI bug 修复，判 proposed_close）。如今三条都已关闭——#65115 在发文当天下午就被关闭，不过它最终没有合并。

这些读数天然会漂移，最新值以 state 仓库和仪表板为准。

## 本地运行

发文时的跑法（Node 24+，npm）：

```bash
source ~/.profile
npm install
npm run build
npm run plan -- --batch-size 5 --shard-count 50 --max-pages 250 \
  --codex-model gpt-5.5 --codex-reasoning-effort high --codex-service-tier fast
npm run review -- --openclaw-dir ../openclaw --batch-size 5 --max-pages 250 \
  --artifact-dir artifacts/reviews --codex-model gpt-5.5 \
  --codex-reasoning-effort high --codex-service-tier fast --codex-timeout-ms 600000
npm run apply-artifacts -- --artifact-dir artifacts/reviews
npm run audit -- --max-pages 250 --sample-limit 25
npm run reconcile -- --dry-run
```

现行命令整体迁到 pnpm（`corepack enable && pnpm install`），参数面也变了——仓库选择显式化，审查一条命令包办：

```bash
source ~/.profile
corepack enable
pnpm install
pnpm run build
pnpm run plan -- --target-repo openclaw/openclaw --batch-size 5 --shard-count 89 \
  --max-pages 250 --codex-model internal
pnpm run review -- --target-repo openclaw/openclaw --target-dir ../openclaw \
  --batch-size 5 --max-pages 250 --artifact-dir artifacts/reviews \
  --output-retention debug --codex-model internal --codex-timeout-ms 600000
pnpm run apply-artifacts -- --target-repo openclaw/openclaw --artifact-dir artifacts/reviews --skip-dashboard
pnpm run audit -- --target-repo openclaw/openclaw --max-pages 250 --sample-limit 25 --update-dashboard
pnpm run reconcile -- --target-repo openclaw/openclaw --dry-run
```

两个面向个人的新玩法：`pnpm review -- --local-only --item-number 123` 做单条咨询式审查（不动 GitHub，输出默认即用即删）；`pnpm local-review`（2026 年 7 月接替退役的 commit-review lane）审查本地提交区间，不要求有开放的 PR。技术栈方面，TypeScript + Node 24 没变，oxlint/oxfmt 没变，构建从 tsgo 换回了 `tsc`（TypeScript ^7.0.2）。

## 局限

发文时文章列过三条局限，现在看要修正一条、保留两条：

- ~~"Hourly 覆盖不足，新鲜项要等很久"~~——这条当时就不成立：每 5 分钟一班的热通道专管新鲜项，只是覆盖率统计里 hourly 档只显示 1%，容易被误读。
- **对 Codex 的单点依赖**仍在，而且更深了——修复与 automerge 通道让整个系统对模型服务的可用性、定价和能力边界更敏感。模型从 gpt-5.5 换到 gpt-6.1-sol 的升级路径倒是走通了，说明抽象层起了一定的隔离作用。
- **自托管门槛不低**。要复刻这套系统，你需要 GitHub App、OpenAI 凭证、Cloudflare Worker/R2 这套基础设施，还要维护仓库配置文件。对绝大多数项目，值得借鉴的是设计而非部署。

还有一个观察维度的局限：保守策略的另一面是温和。9,000+ 开放项在半年里几乎没有净减少，ClawSweeper 的价值不在"清空积压"而在"让积压保持可审、让维护者的注意力只花在需要人判断的地方"——这是 VISION.md 原话的意思，也是评价这类系统时容易被忽略的基准。

## 常见问题

### 它会误关我的 Issue 或 PR 吗？

发文以来的设计让这件事需要连闯多关：提案必须是高置信度、证据充分；执行前快照哈希比对确认项没变过；维护者创建的项受保护（现行唯一的例外是"已验证在 main 实现"）；四个受保护标签直接挡掉提案；Codex 全程没有写权限。此外 PR-to-PR 的"重复"关闭还要求取代目标本身可合并。误关后恢复也留了口子——VISION.md 的质量标准是"错误的关闭必须能通过一条评论复活"。

### Review Lane 和 Apply Lane 为什么要分开？

因为两者的风险等级完全不同。Review 只是写文件，错了没有副作用，可以放心跑大量模型调用；Apply 每一次都是对真实仓库的变更，必须小步、验证、可中断。分开之后，Review 的吞吐可以独立扩（现在有 128 worker 的预算旋钮），Apply 的闸门可以独立收紧（15 分钟一班、每检查点 40 项硬顶）。

### 我可以自己部署吗？

可以，仓库开源（MIT），但注意它自认"不是公共服务"：不会替你的仓库免费审查，需要 fork 后在自己的组织里配置 GitHub App 与凭证。如果只是想要类似的审查能力，`pnpm local-review` 和 `--local-only` 模式不需要任何基础设施，本地就能跑。

### 为什么默认参数一再收紧？

从"只关 Issue"到"全类型"，从 50 到 40，从手动排队到 15 分钟一班——这些不是随意调参，而是随着信任积累逐步放开的口子，每一步都对应一条新的守卫（token 生命周期、仓库 profile、配对保护）。观察一个自动化系统的成熟度，看它的默认值变化比看它的功能列表更准。

---

**参考链接**：

- ClawSweeper 仓库：https://github.com/openclaw/clawsweeper
- 目标仓库：https://github.com/openclaw/openclaw
- 状态与审计数据：https://github.com/openclaw/clawsweeper-state
- 实时仪表板：https://clawsweeper.openclaw.ai/
- 官网：https://clawsweeper.bot

> 事实边界：文中 2026-04-26 时点的事实以该日提交 `52bda011` 的 README、workflow 与源码为锚；现行状态以 2026-10-04 的 GitHub API 读数、main 分支 README（1,285 行）与源码为锚。运行数字天然漂移，引用前请以 state 仓库当日读数为准。
