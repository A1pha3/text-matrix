---
title: "ECC：给 AI 编码 Agent 的 harness 操作系统，293 个技能、本能学习与 AgentShield 安全扫描"
date: "2026-05-25T20:16:19+08:00"
lastmod: "2026-10-03T12:00:00+08:00"
slug: "ecc-agentic-work-system-for-ai-agents"
github_repo: "affaan-m/ECC"
source_key: "gh:affaan-m/ECC"
aliases:
  - "/posts/tech/ecc-agentic-work-system-for-ai-agents/"
description: "ECC 把计划、TDD、新鲜上下文评审、会话记忆和持续学习做成一套装一次就生效的 harness 原生系统：293 个技能、68 个子代理、21 个语言规则包，适配 Claude Code、Codex、Kimi Code 等 13 个安装目标，27 万 stars 的单维护者项目。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Claude Code", "Codex", "工作流自动化"]
---

# ECC：给 AI 编码 Agent 的 harness 操作系统，293 个技能、本能学习与 AgentShield 安全扫描

> **目标读者**：每天用 Claude Code / Codex / Cursor 之类编码 Agent 干活，想找一套现成的工程纪律往上装的人
> **要解决的问题**：为什么 Agent 的计划总丢在聊天记录里、"用 TDD"的叮嘱总被忘掉、换个会话就失忆——以及一套仓库级配置能不能治好这些
> **难度**：⭐⭐（装插件即可起步，吃透机制要看 hooks 与安装状态）
> **核对口径**：本文初版发表于 2026-05-25（v2.0.0-rc.1 发布当天），现按 2026-10-03 的 v2.2.3 全面更新；文中读数与机制以当日 GitHub API、README 与浅克隆源码为准

---

## 核心判断

ECC 解决的问题不是"给 Agent 装什么插件"，而是**把工程流程本身装进 harness**：计划先落成可编辑的产物、测试先行成为带证据的门禁、评审从新鲜上下文发起、会话结束自动蒸馏成摘要和"本能"、反复验证有效的模式沉淀为可复用技能。官方把它压缩成一条循环：

```text
plan -> test -> implement -> review -> verify -> remember -> improve
```

配套的立场是一句值得记住的话：**"Optimize the context window. Persist everything else."**——上下文窗口是稀缺资源，其余一切都该落盘。这个理念贯穿它的五层设计：技能按需加载、规则选择安装、hooks 在模型上下文之外跑、记忆写进文件而非聊天记录。

体量层面，这是当前最成功的单维护者开源项目之一：2026-10-03 读数 271,654 stars / 40,576 forks / 371 名贡献者。作者 Affaan Mustafa 自述从 Claude Code 实验期就开始重度使用，2025 年 9 月与 @DRodriguezFX 搭档拿了 Anthropic x Forum Ventures 黑客松冠军（作品是全程用 Claude Code 构建的 zenith.chat）；README 里"single maintainer ships weekly across 7 harnesses"是官方对发版节奏的原话。仓库前身名为 everything-claude-code，后更名 ECC，MIT 协议从未变过。

---

## 它装上了什么：五层概念

ECC 的 293 个技能、68 个子代理、94 条命令不是一堆并列的文件，五层各有分工，理解分工才知道为什么它不会把整个仓库塞进每个会话：

| 概念 | 职责 | 上下文行为 |
|---|---|---|
| Skills（293 个） | TDD、安全评审、深度研究等可复用工作流 | 任务需要时才加载 |
| Agents（68 个） | 有独立上下文和工具权限的子代理 | 隔离计划、实现与评审 |
| Rules（22 个目录） | 项目或语言的持久标准 | 始终加载，所以要按需安装 |
| Hooks | 由 harness 事件触发的脚本 | 在模型上下文之外运行 |
| Instincts（本能） | 从真实会话学到的模式，带置信度 | 相关时才被召回 |

README 里 "Without a system / With ECC" 对比表把动机说得很直白：没有系统时，计划消失在聊天记录里、"请用 TDD"是模型可能忘记的指令、同一段上下文既写代码又评审代码；装上系统后，计划变成实现前可编辑的产物、TDD 变成带 RED 证据的门禁、评审由新鲜上下文的 reviewer 找回归和盲区。

技能目录的覆盖面已经超出纯编码：django/laravel/springboot/quarkus/rails 五套框架的 patterns-security-tdd-verification 全家桶、cpp/golang/perl/python/swift 的语言专项、`investor-materials` 和 `market-research` 这类商业技能、`frontend-slides` 零依赖 HTML 演示构建器，甚至有 `ito-market-intelligence` 预测市场研究包。语言规则包则从 v1.9.0 时的 12 个生态扩到当前 22 个目录（common + 21 个语言/框架包，新增 ruby、dart、vue、angular、react、react-native、csharp、nuxt 等）。

---

## 四个月从 18 万到 27 万星：版本演进

这张表按 releases API 与各版 release notes 逐条核对。原文写作时停在 rc.1，现在正式版之后又走了六个版本：

| 版本 | 时间 | 重点 |
|------|------|------|
| v1.2.0 | 2026-02 | Python/Django、Java Spring Boot 技能；instinct 学习 v2（置信度评分、导入导出） |
| v1.3.0 | 2026-02-05 | OpenCode 插件支持（hooks 经插件事件桥接） |
| v1.4.0 | 2026-02-06 | rules 目录化（common + 语言包）；configure-ecc 交互式安装向导；PM2 / multi-* 编排命令；中文翻译 |
| v1.4.1 | 2026-02-06 | 修复 `parse_instinct_file()` 导入丢内容（#148、#161） |
| v1.5.0 | 2026-02-11 | npm 包 ecc-universal 首发，Cursor/OpenCode/Claude Code 三平台 |
| v1.6.0 | 2026-02-24 | Codex CLI 支持（/codex-setup）；AgentShield 集成（102 条规则）；GitHub Marketplace 上架 |
| v1.7.0 | 2026-02-27 | Codex app + CLI 直支持；frontend-slides；5 个商业/内容技能 |
| v1.8.0 | 2026-03-05 | 定位转向 "agent harness performance system"：ECC_HOOK_PROFILE 三档、/harness-audit 等五条新命令、NanoClaw v2 |
| v1.9.0 | 2026-03-21 | 选择性安装（--with/--without）；12 语言生态；ECC Tools Pro 上线；SQLite 状态库 |
| v2.0.0-rc.1 | 2026-05-25 | 操作流扩展、Tkinter 仪表板、Rust 控制平面原型入树、公开目录计数同步（61 agents / 246 skills / 76 command shims） |
| v2.0.0 | 2026-06-10 | **The Agent Harness Operating System**：harness 无关的会话适配器（ecc.session.v1）、MCP inventory、worktree 生命周期服务、orch-* 编排技能族、Discord 社区 |
| v2.1.0 | 2026-07-27 | Plan Canvas 浏览器评审、Kimi Code 安装目标、Itô GPU 自托管路径、Hermes 与 OpenClaw 目标 |
| v2.2.0–v2.2.3 | 2026-08-28 起 | universal installer 升为一等分发路径：多 harness 引导式安装、原生 Antigravity 2.0 支持、staging dist-tag 逐字节验证后 promote 的发布门禁 |

组件计数的演进链本身是个有意思的口径样本：rc.1 时 61 agents / 246 skills / 76 shims（rc.1 release notes 写 243 public skills，README 写 246，打包口径与目录口径差 3），2.0.0 出厂 64 / 261 / 84，2.1.0 时 67 / 281 / 94，当前 README 主口径 68 / 293 / 94——与浅克隆实测的目录计数完全一致。

---

## 核心机制深读

### 技能与命令：skills-first 的迁移未完

ECC 明确技能是第一工作面，命令降级为"便利入口和兼容垫片"。`commands/` 里的 94 条维护中的斜杠命令是迁移期的兼容层，退役的短名（/tdd、/eval、/verify 等 13 个）被挪进 `legacy-command-shims/` 只做显式选用；新工作流一律先进 `skills/`。插件装好后命令用命名空间形式（`/ecc:plan "Add auth"`），手动安装则保留短形式。

找组件不用翻目录，顾问命令会返回匹配组件、相关 profile 和预览安装命令：

```bash
npx ecc-universal@2.2.3 consult "security reviews" --target claude
```

`consult` 只做检索和建议，不落盘；真正安装走 `install --profile ... --with ...`。这两个角色别混。

### 本能系统：把踩过的坑变成带置信度的资产

持续学习 v2 的思路是让 Agent 从真实会话里自动提取模式，存成带置信度评分的"本能"，再由 `/evolve` 把相关本能聚类成技能。`/instinct-status` 查看已学本能、`/instinct-import` / `/instinct-export` 在团队里交换本能集合。

注入侧的调控比初版细了很多：SessionStart 默认只注入 6 条本能（`ECC_MAX_INJECTED_INSTINCTS`），置信度阈值默认 0.7（`ECC_INSTINCT_CONFIDENCE_THRESHOLD`），且默认开启"置信度 + 项目/技术栈相关性"的混合排序（`ECC_INSTINCT_RELEVANCE_RANKING`）——项目作用域和领域匹配的本能会获得小幅加权，压过置信度更高但不相关的那条。这个设计在工程上很诚实：高置信度不等于与当前任务相关。

值得写进事故史的一笔：v1.4.1 修复的 `parse_instinct_file()` 缺陷会在导入时静默丢弃 frontmatter 之后的所有内容（Action、Evidence、Examples 段），导入成功的假象让本能库看起来完整、实则残缺（#148、#161）。对任何"从文件导入知识"的机制，这都是值得对标的失败案例。

### 记忆：从 hook 存档到 Memory Vault

最早的记忆持久化靠 hooks：SessionStart 加载上下文、Stop 阶段写会话摘要、PreCompact 抢在压缩前存状态。2.x 把这件事升级为统一的 **Memory Vault**：Claude、Codex、Hermes、OpenClaw、Kimi 等 harness 共用一种本地、可检查的 `ecc.memory.v1` Markdown 格式，项目记忆在 `.ecc/memory/`、用户记忆在 `~/.ecc/memory/`：

```bash
ecc memory init --scope project
ecc memory handoff --from hermes --target codex \
  --title "Continue authentication migration" --body-file ./handoff.md
ecc memory search "authentication migration" --target-harness codex
ecc memory doctor
```

信任边界的措辞值得逐字读：记忆是"未审查的上下文，不是可执行策略"（unreviewed context, not executable policy）。项目记忆库用 fail-closed 的 .gitignore 保护，团队共享仅限人工检查过的版本库内容，重要的断言必须对照权威来源验证。可选的 `ecc-memory-vault` MCP 服务器只暴露 save/search/read/doctor 四个工具，且必须以小写的 `ECC_MEMORY_HARNESS` 身份启动。在"让 Agent 记住"这件事普遍被做成黑箱的行业氛围里，把不可信状态明说出来的做法不多见。

### 安全：AgentShield、GateGuard 与"只从官方渠道装"

AgentShield 是 ECC 安全叙事的支点，出自另一个黑客松——2026 年 2 月的 Claude Code Hackathon（Cerebral Valley x Anthropic）。官方口径是 1,282 个测试、98% 覆盖率、102 条静态分析规则，扫描 CLAUDE.md、settings.json、MCP 配置、hooks、agent 定义和技能五大类：密钥检测（14 种模式）、权限审计、hook 注入分析、MCP 服务器风险画像、agent 配置审查。`--opus` 旗标会跑三个 Opus 4.6 代理的红队/蓝队/审计管线——攻击者找利用链、防御者评估防护、审计者合成优先级排序的风险评估，输出终端 A–F 评级、JSON、Markdown 或 HTML，关键发现以退出码 2 支持 CI 门禁：

```bash
agentshield scan --path .
agentshield scan --path . --opus --stream
```

注意一个安全姿态的变化：初版 README 直接给 `npx ecc-agentshield scan`，当前版本要求"已安装且经过审查的 AgentShield 二进制"，明确说"仅凭 registry 发布不构成审计"，`/security-scan` 技能同样有此前置。工具的维护者自己把供应链审查责任摆上了台面。

仓库侧还有两道内建防线：GateGuard 在破坏性 shell 命令（rm、force/path git checkout、破坏性 find -exec）执行前拦截；CI 里跑供应链 IOC 扫描。README 顶部还有一个不寻常的警告：只从官方渠道（GitHub 仓库、ecc@ecc 插件、ecc-universal / ecc-agentshield npm 包、ecc-tools GitHub App、ecc.tools）安装，**第三方重上传和非官方镜像未经项目维护或审查，可能含恶意软件**——一个 27 万星项目的名字已经开始被人拿去投毒，这本身就是生态位置的证明。

### 跨 harness 适配：能力分级的诚实样本

"支持 N 种工具"在大多数项目里是一句营销话，ECC 把它做成了带能力等级的矩阵：

| Harness | 状态 | 关键限制 |
|---|---|---|
| Claude Code | Stable primary | 插件会向模型广告完整目录，在意上下文占用时用选择性 profile |
| Codex | 原生插件 | hooks 需显式信任决定，不用 Claude 的四档 hook profile |
| Cursor / OpenCode | Beta | agent 发现随 Cursor 构建而异；OpenCode 只带目录子集 |
| GitHub Copilot | Instruction-only | 无 hooks、无运行时 agent、无委派——只投喂指令与提示文件 |
| Gemini、Zed、Antigravity、Qwen、Hermes、OpenClaw、Kimi、CodeBuddy、JoyCode | Experimental / minimal | 只保证文件放置与指令可移植，不宣称功能对等 |

两个演化值得注意。一是 Codex 从"同步脚本拷配置"升级为原生 marketplace 插件（`codex plugin marketplace add affaan-m/ECC`），旧 sync 路径降级为兼容选项；二是 2.1 起新增的 Kimi Code 目标背后站着 Moonshot AI 的赞助，配套一条自托管路线：Itô 出 GPU、自托管开放权重 Kimi 模型、Kimi Code + ECC 在上——三段各自独立可换。GitHub Copilot 的边界也写得毫不含糊：没有 hook 系统和子代理 API，就只给指令层，不假装对等。

---

## 安装：一条路径，不要叠装

当前推荐的入口是 2.2 引入的引导式安装，不克隆仓库：

```bash
npx ecc-universal@2.2.3 setup
```

向导会先盘点官方市场和所有原生安装作用域再动手，装完、升级、换作用域、改 hook profile 都重跑同一条命令。要在一次审查过的流程里配置多个 harness，用多 harness 向导（Claude Code / Codex / Kimi Code 三选 N，每步预检、最后确认）：

```bash
npx ecc-universal@2.2.3 install --guided
```

三条纪律，全是官方用事故换来的：

1. **每个 harness 只选一条安装路径。**最常见坏配置是先 `/plugin install` 再跑 `install.sh --profile full`——技能、命令、hooks 全部双份。装了两遍就去 Reset / Uninstall 一节按顺序清理。
2. **插件不分发 rules。**Claude Code 插件机制的上游限制，rules 要手动拷贝，且从 common 加一个你真用的语言包开始：

```bash
git clone https://github.com/affaan-m/ECC.git && cd ECC
mkdir -p ~/.claude/rules/ecc
cp -R rules/common ~/.claude/rules/ecc/
cp -R rules/typescript ~/.claude/rules/ecc/   # 换成你的技术栈
```

3. **Node 21+ 必须升级到 v2.0.0 以上。**v2.0.0 修复了一个静默失效：hook runner 在 `node -e` 下依赖 `require.main`，新版 Node 里它是 undefined，结果所有插件 hooks 干净退出、一条都没跑（#2184）。hooks 是 ECC 的执行层，这个 bug 等于整层系统装了没开。

要求：Node.js 18+、Git、Claude Code CLI 2.1.0+（插件 hooks 约定所必需）。低上下文场景用 `--profile minimal`（有意排除 hooks-runtime）或 `core --without baseline:hooks`；`/multi-*` 多模型命令依赖外部 ccg-workflow 运行时，基础安装不覆盖。

---

## 2.x 的新面：Plan Canvas 与 Itô 算力桥

v2.1 的 Plan Canvas 把计划评审从终端里的一墙 Markdown 变成浏览器里的可视化循环：`/plan` 的确认门禁映射成 Approve / Request changes 按钮，点击元素或选文本就能附编号批注，侧栏聊天、Mermaid 图表原生渲染、文件修改实时刷新。实现上是 loopback-only 的浏览器画布加一个 CLI + JSON 协议（`ecc-plan-canvas`），不绑定 Claude——这是 ECC 一贯的 harness 无关路线在交互层的延续。

Itô 桥的边界设计同样值得读：`ecc ito find` 向官方 Itô CLI 提交实时的、经过认证的 RFQ（询价），但明确"不预留容量、不采购、不运行推理"；凭据型 CLI 垫片直接拒绝；设备令牌默认存 macOS 钥匙串。赞助链接是"被动的"——README 原话，不触发 RFQ、不预留算力、不配置 serving。把赞助商集成写到这个克制程度的项目不多。

工作负载侧，2.0 引入的 `orch-*` 编排技能族和 worktree 生命周期服务（并行 agent 的 worktree 冲突预测与安全回收）、2.2 的原生 Antigravity 2.0 安装和发布门禁（staging dist-tag → 逐字节 registry 校验 → promote latest）持续加固多会话与分发两条线。

---

## ecc2：树内的 Rust 控制平面原型

`ecc2/` 目录是 Rust 写的 ECC 2.0 控制平面原型（17 个 Rust 源文件），提供终端 UI 仪表板、SQLite 会话存储、start/stop/resume 流程和后台守护进程，官方定性是"真实代码、alpha 质量、可本地构建测试"，**不是**完成的 ECC 2.0 产品。

有意思的是现状：v2.0.0 正式版实际落地的"控制平面基座"是 Node 侧的会话适配器（ecc.session.v1）与 worktree 服务，当前 README 已不再提及 ecc2。原文写作时它还是 rc.1 宣传的亮点，四个月后官方重心明显移向了 Node 路线。原型还在树内，观察它会不会长成独立产品，比把它当既成事实介绍更符合现状。

---

## 商业面：OSS 免费，Pro 养活

ECC 的商业结构一句话能说清：**仓库永远 MIT 免费，ECC Pro 是私有仓库的托管 GitHub App**。Pro 定价 $19/seat/月，按 v1.9.0 公布的口径免费档 10 次分析/月、Pro 50 次/月，加 PR 自动审计和团队池化用量。README 直白地承认这套模式：赞助商和 Pro 订阅养活了"一个维护者每周跨 7 个 harness 发版"。

赞助商名单能看出生态位置：CodeRabbit、Greptile、Moonshot AI（Kimi）、Itô Markets、SerpApi——AI 编码工具链的公司在给一个配置仓库掏钱。Discord 社区由发布工作流自动推送版本公告，维护者直接读 #feedback 和 #feature-requests 定路线图。

---

## 适用判断

**该装的场景**：在 Claude Code / Codex 双线工作想共享技能与规则；想让 TDD、新鲜上下文评审、会话记忆成为默认管线而非口头约定；在意 agent 配置自身的攻击面（hooks、MCP、权限就是可执行配置）；团队想把踩坑经验沉淀成可交换的本能库。

**缓行的场景**：Windows 原生环境——continuous-learning v2 的 observer 守护进程和 memory-vault 写入仍有 open defect（#2489、#2626），shell 依赖特性需要 Git Bash/WSL；期望 Cursor / OpenCode 全功能对齐的用户——官方自评 Beta 且明说不主张对等；只想给单个对话窗口加几条指令的轻量场景——装这个等于开卡车买菜。

**采用顺序建议**：先用引导式安装装插件、只拷 common + 一个语言包的 rules，跑一个真实特性开发循环验证 `/ecc:plan` → `tdd-workflow` → `/code-review` 链路；确认 hooks 在你的 Node 版本上真的在跑（`/context-budget` 和会话摘要文件是证据）；再考虑本能注入调优、Memory Vault 团队共享和第二个 harness。

---

## 常见问题

### 全部装上会不会太重？

会。官方的第一原则就是选择性安装：`--profile minimal` 起步，`--with lang:typescript --with agent:security-reviewer` 按需加组件；rules 是始终加载的上下文，拷之前想清楚。插件会把完整目录广告给模型，在意上下文占用时用选择性 profile。上下文吃紧时 `/context-budget` 直接给出压力读数。

### ECC 和普通插件市场里的插件有什么区别？

市场插件多为单点功能；ECC 把技能、子代理、规则、hooks、记忆做成互相咬合的一层——hook 触发会话摘要，摘要蒸馏成本能，本能聚类成技能，技能在被评审时被新鲜上下文的子代理调用。装单点插件是加一个工具，装 ECC 是换一套流程。

### 团队怎么共享配置？

两条路，信任级别不同。rules、技能、hooks 配置可以进版本库，团队共享同一套显式配置；Memory Vault 的团队作用域更适合"人检查过的交接上下文"，但官方强调即便提交进版本库，记忆仍是未审查上下文——把重要结论提升为受治理的项目文档才是终点。

### 除了 Claude Code 还值得装在别的 harness 上吗？

按平台矩阵对号入座：Codex 原生插件是当前第二成熟路径；Cursor、OpenCode 是 Beta；Copilot 只有指令层；其余目标定位是实验性适配。在 Claude Code 上它是主战场，在别处它是"能用的指令与技能搬运工"——官方自己不掩盖这个落差。

---

## 资源链接

- GitHub：[affaan-m/ECC](https://github.com/affaan-m/ECC)（MIT）
- 官网与 Pro 定价：[ecc.tools](https://ecc.tools)
- GitHub App：[github.com/apps/ecc-tools](https://github.com/apps/ecc-tools)
- npm：[ecc-universal](https://www.npmjs.com/package/ecc-universal) · [ecc-agentshield](https://www.npmjs.com/package/ecc-agentshield)
- 社区：[Discord](https://discord.gg/36yGMHGFbR) · [Discussions](https://github.com/affaan-m/ECC/discussions)
- 深入阅读：仓库内 [the-shortform-guide.md](https://github.com/affaan-m/ECC/blob/main/the-shortform-guide.md)（入门）、[the-longform-guide.md](https://github.com/affaan-m/ECC/blob/main/the-longform-guide.md)（上下文经济学与并行代理）、[the-security-guide.md](https://github.com/affaan-m/ECC/blob/main/the-security-guide.md)（提示注入与 AgentShield）
