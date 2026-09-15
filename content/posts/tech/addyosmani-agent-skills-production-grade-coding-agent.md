---
title: "addyosmani/agent-skills：把 25 个生产级工作流封进 Coding Agent"
date: "2026-07-09T02:55:00+08:00"
lastmod: '2026-09-14T00:00:00+08:00'
slug: "addyosmani-agent-skills-production-grade-coding-agent"
github_repo: "addyosmani/agent-skills"
source_key: "gh:addyosmani/agent-skills"
description: "Addy Osmani 的 agent-skills 把资深工程师的开发流程拆成 25 个可被 AI 调用的 skill，按 Define/Plan/Build/Verify/Review/Ship 六阶段组织，9 个斜杠命令做入口。本文拆解其分层结构与设计原则，用一次任务的完整流转串起各机制，并给出与 Superpowers、Matt Pocock skills 的官方对比。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Agent Skills", "Claude Code", "工作流", "Cursor"]
---

# addyosmani/agent-skills：把 25 个生产级工作流封进 Coding Agent

## 一句话核心判断

「我让 Agent 写了一堆代码，但它从来不写测试、不做 review、不打 tag。」不少团队用 Coding Agent 都撞上过这堵墙。addyosmani/agent-skills 的切入点是把资深工程师的开发流程拆成 **25 个可被 Agent 调用的 skill**，按 Define→Plan→Build→Verify→Review→Ship 六阶段组织，每阶段都带验证门。它不带新模型，也不定义新协议，产出物是一份给 Agent 的工程作业指导：何时调用哪个 skill、按什么顺序、卡什么验证。

如果团队已经在用 Claude Code / Cursor / Codex / Copilot / Cline，并在为「Agent 容易跨阶段跳过验证」发愁，这个 skill 包值得先评估；如果只是临时写一次性脚本，收益不明显。

## 系统地图：六阶段 + 25 skills

skill 包按开发生命周期组织，前后两道门（defining 与 shipping）中间是四个执行态：

```
  DEFINE          PLAN           BUILD          VERIFY         REVIEW          SHIP
 ┌──────┐      ┌──────┐      ┌──────┐      ┌──────┐      ┌──────┐      ┌──────┐
 │ Idea │ ───▶ │ Spec │ ───▶ │ Code │ ───▶ │ Test │ ───▶ │  QA  │ ───▶ │  Go  │
 │Refine│      │  PRD │      │ Impl │      │Debug │      │ Gate │      │ Live │
 └──────┘      └──────┘      └──────┘      └──────┘      └──────┘      └──────┘
  /spec          /plan          /build        /test         /review       /ship
```

25 个 skill 按这六个阶段归类，其中 24 个是生命周期 skill，剩下 1 个是入口 meta skill：

| 阶段 | skill 数量 | 阶段角色 |
| --- | --- | --- |
| Meta（入口） | 1 | 判定当前任务该走哪个 skill |
| Define（澄清） | 4 | 把模糊需求变成确定 spec，定下质量门槛 |
| Plan（拆解） | 1 | 把 spec 切成可执行的小任务 |
| Build（实施） | 7 | 在不同上下文中按方法论写代码 |
| Verify（证明） | 2 | 用工具跑验证 |
| Review（把关） | 4 | 质量/安全/性能/可读性 |
| Ship（上线） | 6 | 部署、迁移、可观测、文档 |
| 合计 | 25 | |

分相的意义在于把 Agent 钉在单一阶段里：问「怎么开始一个新项目」，它跑 `/spec` 接 `/plan`；问「这个 bug 为什么坏了」，它钻进 `/test` 的验证链路。一条 prompt 一锅烩的做法在这里走不通。

命令入口有 9 个，比阶段多出 3 个专项：Define 阶段占两个入口（`/spec` 管需求规格，`/constraints` 管质量门槛），`/webperf` 和 `/code-simplify` 是挂在 Review 前后的两个专项检查。完整清单：

| 场景 | 命令 | 核心原则 |
| --- | --- | --- |
| 决定做什么 | `/spec` | 先 spec 后代码 |
| 计划怎么做 | `/plan` | 小而原子的任务 |
| 增量构建 | `/build` | 一次只做一片 |
| 证明它可用 | `/test` | 测试即证明 |
| 定下质量门槛 | `/constraints` | 一次决定，处处执行 |
| 合并前评审 | `/review` | 提升代码健康 |
| 审计前端性能 | `/webperf` | 先测后优化 |
| 简化代码 | `/code-simplify` | 清晰胜于聪明 |
| 上生产 | `/ship` | 更快即更安全 |

skill 之外，仓库还有三类配套：`agents/` 下 4 个评审 persona（code-reviewer、test-engineer、security-auditor、web-performance-auditor），`references/` 下 7 份共享清单（测试、安全、性能、可访问性、可观测性等），以及 `evals/` 下 25 个评测用例——CI 里会检查这些 skill 是否真的按预期路由和执行。

## 关键设计原则

通读这些 SKILL.md，能抽出几条贯穿全局的原则，这也是它和「随便写几条 prompt 模板」拉开差距的地方：

### 1. 步骤 / 验证门 / 反合理化表三件套

每个 skill 都按固定结构写：Steps（执行步骤）、Verification gate（验证门）、Anti-rationalization table（反合理化表）。反合理化表把「我以为可以省掉这一步」的借口提前逐条堵掉——`test-driven-development` 的表里就有现成的一条，借口是「This is too simple to test」，回应是「Simple code gets complicated. The test documents the expected behavior.」。先替 Agent 把借口说出口，再替它把理由摆出来。

### 2. 量化的质量目标

skill 里到处是可直接验收的阈值和口诀：五轴 review（正确性、可读性与简洁、架构、安全、性能）、每次改动约 100 行、测试金字塔 80/15/5（分别对应单元/集成/E2E）、Beyonce Rule（if you liked it then you should've put a test on it）。评审时拿数字对照就行，不用争「测试写得算不算好」。

### 3. TDD 不留妥协

`test-driven-development` 写明 Red-Green-Refactor、test pyramid（80/15/5）、test sizes、DAMP over DRY（Descriptive And Meaningful Phrases）。测试代码宁可描述性重复、不过度抽象，这与「DRY 到极致」的常见教条相反，值得正视。

### 4. 触发语境（context-driven activation）

skill 支持自动激活：让 Agent 设计 API 会带出 `api-and-interface-design`，构建 UI 会带出 `frontend-ui-engineering`。显式命令与隐式触发双轨并行——既能用 `/spec` 直接跳进，也能让 Agent 自己判定。

### 5. 一致性协作（`/build auto` 模式）

`/build auto` 让用户只审一次 plan，所有任务一次性自动实施。自动化只发生在任务之间，验证一步没少：每个任务仍然测试驱动、单独提交，失败或高风险步骤会停下来等确认。两个细节值得知道——批准要求明确答复，「看起来不错」不算数；中途被 blocker 卡住时，处理完重新调用 `/build auto`，它会从下一个未完成任务接着跑。

### 6. 判断有出处

README 明说这套 skill 吸收了 Google 的工程文化：《Software Engineering at Google》与 Google 工程实践指南里的 Hyrum's Law、Beyonce Rule、测试金字塔、Chesterton's Fence、trunk-based、Shift Left，都被直接嵌进了对应 skill 的步骤里。每条规则都能顺藤摸瓜找到原始出处。

## 25 个 Skill 一览

按开发生命周期阶段展开。下表仅揭示 skill 全景，**所有用法以仓库为准**：

### Meta

- `using-agent-skills`：session 起始判定该跑哪条 skill。
- 免得所有任务都挤进同一条工作流。

### Define（澄清）

- `interview-me`：一次只问一个问题，把模糊需求问到 95% 置信。
- `idea-refine`：发散→收敛，把粗概念变成具体提案。
- `spec-driven-development`：写 PRD 含目标、命令、目录、代码风格、测试、边界——再动代码。
- `constraint-driven-development`：把质量门槛写成 CONSTRAINTS.md 契约。访谈最多四个问题、每个都带默认阈值，「不知道」也能出配置；查出来的检查按成本分位置（编辑循环秒级、任务结束 90 秒内、其余进 CI），并盯住 diff——新增 `@ts-ignore`、`eslint-disable`、删测试、拆断言、调低阈值，都会被当成「悄悄降标准」拦下。2026-09-07 加入。
- 四个 skill 覆盖「用户说不清楚」「标准没写下来」这两类最常见的工程入口。

### Plan（拆解）

- `planning-and-task-breakdown`：把 spec 切成带验收标准、排好依赖的小任务。
- 单一 skill 承担「把大事变成小事」的角色。

### Build（实施）—— 这是最大的族

- `incremental-implementation`：纵向切片（thin vertical slice），feature flag、可回滚。
- `test-driven-development`：Red-Green-Refactor，强制写测试。
- `context-engineering`：会话内喂规则文件、context packing、MCP 集成。
- `source-driven-development`：引用官方文档、标注未验证——避免 AI 答假。
- `doubt-driven-development`：对每个非平凡决策做对抗性的 fresh-context 审阅，走 CLAIM→EXTRACT→DOUBT→RECONCILE→STOP 五步，趁「此刻验证」而不是「事后补 debug」。
- `frontend-ui-engineering`：组件架构、设计系统、状态管理、响应式、WCAG 2.1 AA。
- `api-and-interface-design`：契约优先、Hyrum's Law、One-Version Rule、错误语义、边界校验。
- 7 个 skill 共享「写之前先论证、别无脑堆代码」的纪律。

### Verify（验证）

- `browser-testing-with-devtools`：Chrome DevTools MCP，DOM/console/network/performance 联动。
- `debugging-and-error-recovery`：五步分诊（复现→定位→收敛→修复→护栏），stop-the-line 规则。
- 两个 skill 接外部工具（DevTools / debugger），让验证不只靠单元测试。

### Review（把关）

- `code-review-and-quality`：五轴 review、改动约 100 行、严重度标签 Nit/Optional/FYI、评审速度规范。
- `code-simplification`：Chesterton's Fence、Rule of 500、保留行为简化复杂度。
- `security-and-hardening`：OWASP Top 10、auth、密钥、依赖审计、三层边界。
- `performance-optimization`：先测后优化、Core Web Vitals 目标、bundle 分析。
- 对应「我写得对吗？跑得好吗？安全吗？够简洁吗？」四道门。

### Ship（上线）

- `git-workflow-and-versioning`：`trunk-based`、原子提交、约 100 行/提交。
- `ci-cd-and-automation`：Shift Left、Faster is Safer、feature flag、quality gate。
- `deprecation-and-migration`：代码即负债、强制废弃 vs 自愿废弃、清除僵尸代码。
- `documentation-and-adrs`：ADRs、API 文档、注释的 "why"。
- `observability-and-instrumentation`：结构化日志、RED 指标、OpenTelemetry、症状告警。
- `shipping-and-launch`：上线前 checklist、灰度、回滚、监控。
- 手工流程里这些环节常被压缩，skill 包把它们固定成了上线前的步骤。

## 一次任务怎么流过这套系统

用一个常见任务串起这些机制：给一个已有 Node API 项目的「订单列表」接口加游标分页。以下是依据各 skill 文档做的示意推演，仓库本身不附官方案例。

1. **入口判断**。会话开始时 `using-agent-skills` 先判定任务类型：功能改动，进 Define。
2. **定门槛**。项目还没成文约束的话，`/constraints` 先跑一轮：扫 `package.json`、测试运行器、lint 配置和现有覆盖率，最多问四个问题（每个都带默认值），落成 CONSTRAINTS.md——比如改动行覆盖率不低于 80%，这个检查放在任务结束时跑，全量扫描留给 CI。此后 Agent 每次想用 `@ts-ignore` 或删测试换绿灯，都会被对照这份文件拦下。
3. **澄清与规格**。`/spec` 走 `spec-driven-development`：先写 PRD，把目标、命令、目录结构、代码风格、测试策略和边界（游标格式、最大页长、向后兼容）写清楚，然后才动代码。
4. **拆解**。`/plan` 把 PRD 切成带验收标准和依赖顺序的小任务：加游标编解码工具 → 改查询层 → 改路由 → 补测试。
5. **实施**。`/build` 按纵向切片推进，每片走 Red-Green-Refactor：先写失败的测试，再写实现。Agent 冒出「这个改动太简单不用写测试」的念头时，反合理化表里那条回应已经等着它了。
6. **验证**。任务结束跑改动行覆盖率，对照 CONSTRAINTS.md 的数字；测试挂了进 `debugging-and-error-recovery` 的五步分诊，修完补一条防回归测试。
7. **评审与上线**。`/review` 按五轴过一遍，发现的问题标 Nit/Optional/FYI 分级；`/ship` 走上线清单——原子提交、feature flag、灰度和回滚预案。

这条链路里人的位置取决于模式：默认模式下每个任务之间人都在场；用 `/build auto` 则只在开头批一次计划，中途处理被验证门拦下的例外。

## 与 Superpowers、Matt Pocock skills 的对比

同类「给 Coding Agent 的 skill 包」里被提得最多的是 [obra/superpowers](https://github.com/obra/superpowers) 和 [Matt Pocock 的 skills](https://github.com/mattpocock/skills)。仓库自带的 [docs/comparison.md](https://github.com/addyosmani/agent-skills/blob/main/docs/comparison.md) 给了一份克制的三方对照——作者刻意不放 star 数，理由是各家引用口径混乱且每周在变：

| | agent-skills | Superpowers | Matt Pocock's skills |
| --- | --- | --- | --- |
| 核心思路 | 把资深工程师全生命周期编码成 skill | 建立在可组合 skill 上的完整开发方法论 | 一个专家的 Claude Code 日常工作流开源 |
| 组织方式 | SDLC 六阶段 + meta 路由 | 单一纪律环：brainstorm → plan → execute → review | 聚焦命令的工具箱 |
| 体量 | 25 skills 覆盖全周期 | 约 14 skills，深耕构建内环 | 约 30 skills，Define/Build 侧重 |
| 特色机制 | 反合理化表、`/ship` 并行评审 persona、CI 里的路由与行为评测 | 子代理开发 + 任务评审员 + 修复环，git worktree 隔离，还有「写 skill 的 skill」 | grill me 一次一问的审问循环、seam-based TDD |
| 适合 | 一个 feature 从头到尾，每个阶段有人工卡点 | 长链路、重推理的自主任务 | 务实的日常循环，需求和 TDD 最强 |

局限照旧要承认：

- **web 前端比重高**：Core Web Vitals、Chrome DevTools MCP、可访问性清单、`/webperf` 都面向 web；工具面其实不窄——constraints 的默认工具链是 Semgrep、gitleaks、osv-scanner 这类语言无关的扫描器，项目探测也覆盖 `pyproject.toml`/`go.mod`/`Cargo.toml`——但后端项目里 web 专项命令和清单会闲置。
- **依赖客户端支持**：slash command 在 Claude Code / Cursor 里体验最好；没有适配目录的客户端，只能把 `skills/` 核心拷进各自的规则位置（README 的项目结构一节写明了这一点）。

## 接入方式

最快的路径：通过 Vercel Labs 的 [skills CLI](https://github.com/vercel-labs/skills) 一行安装，官方称覆盖 70+ Agent：

```bash
npx skills add addyosmani/agent-skills            # 全装 25 个
npx skills add addyosmani/agent-skills --list     # 先看看再装
npx skills add addyosmani/agent-skills --skill test-driven-development   # 单装某个
```

Claude Code 用 marketplace：

```
/plugin marketplace add addyosmani/agent-skills
/plugin install agent-skills@addy-agent-skills
```

Cursor 把工作流 skill 同步到 `.cursor/skills/`，短策略放 `.cursor/rules/*.mdc`，不要把完整 skill 塞进 rules（官方 cursor-setup 文档的原话）。Gemini CLI、Codex、OpenCode、Windsurf、Copilot、Kiro 各有适配文档，见仓库 `docs/` 目录。

采用节奏官方也给了两条路（docs/adoption-guide.md）：新项目从第一天走全生命周期；已有代码库按「验证优先」增量铺开，先上测试和 review，再逐步补齐其余阶段。

两个容易踩的坑：

- 单装限制：`npx skills add --skill <name>` 只复制 `skills/<name>/`，不带仓库层的 `references/` 共享清单目录。skill 本身能用，指向共享清单的路径会失效。上游在 [issue #361](https://github.com/addyosmani/agent-skills/issues/361) 记录了这个限制（issue 已关闭，README 安装说明仍保留此提示），解法是整仓接入、克隆仓库，或把需要的 checklist 拷进已装 skill 的 `references/`。
- SSH 报错：Claude Code 的 marketplace 默认走 SSH 克隆；未配置 SSH key 时，marketplace add 这步改用 HTTPS 完整 URL 即可绕过。

## 适用边界

**适合**：

- 工程团队中 Coding Agent 已经普及，但质量门控薄弱
- 想让 TDD / code review / security scan 这些日常工程动作在 Agent 调用链中常驻
- 用 Claude Code / Cursor / Codex 这类支持 slash command 或 marketplace 的工具
- 中等规模团队：既能吃下 skill 体系的纪律，又不至于被规则淹没

**不太适合**：

- 已有大型内部 Skills / Cursor rules 体系的团队——先评估冲突，别硬叠
- 一次性脚本生成（chat 里直接问就行）
- 重度锁定老 IDE（如 Eclipse / 老 JetBrains）——只能手工拷 SKILL.md
- 纯研究、不写生产的 Agent 场景

## 一句话总结

addyosmani/agent-skills 把开发流程本身当成可调用的 skill：六阶段、25 个 skill、9 个命令入口，每步带验证门和反合理化表。强项是可验收的量化指标与有出处的工程判断；局限是 web 前端偏重、不打算取代已有的 IDE rules 体系。正在给团队挑 skill 包的话，先整仓接入跑一个真实 feature，再决定是全量采用还是只摘 Verify 和 Review 两族。

## 参考链接

- 仓库：<https://github.com/addyosmani/agent-skills>
- skill 数：25（24 个生命周期 skill + 1 个 meta skill）
- 口径：stars 94,130、plugin.json 0.6.9，均为 2026-09-14 快照
- License：MIT
- 官方对比文档：<https://github.com/addyosmani/agent-skills/blob/main/docs/comparison.md>
- 兼容 Agent：npx skills CLI 宣称 70+；Claude Code / Cursor / Codex / Copilot / Cline / Gemini CLI / OpenCode / Windsurf / Kiro 等有官方适配文档
