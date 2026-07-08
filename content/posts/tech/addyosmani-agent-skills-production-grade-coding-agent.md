---
title: "addyosmani/agent-skills：把 24 个生产级工作流封进 Coding Agent"
date: "2026-07-09T02:55:00+08:00"
slug: "addyosmani-agent-skills-production-grade-coding-agent"
description: "Addy Osmani 的 agent-skills 把资深工程师的开发流程拆成 24 个可被 AI 调用的 skill，覆盖 Define/Plan/Build/Verify/Review/Ship 全生命周期。本文拆解其分层结构、关键设计原则与 24 个 skill 的依赖图，并讨论与现有 Agent Skills 标准的差异。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Agent Skill", "Claude Code", "工作流", "Cursor"]
---

# addyosmani/agent-skills：把 24 个生产级工作流封进 Coding Agent

## 一句话核心判断

"我让 Agent 写了一堆代码，但它从来不写测试、不做 review、不打 tag。" 这是 Coding Agent 落地过程中最常见的问题。addyosmani/agent-skills 的切入点是：**把资深工程师的开发流程拆成 24 个可被 Agent 调用的 skill，按 Define→Plan→Build→Verify→Review→Ship 六阶段组织，每阶段都带验证门**。它不是新模型或新协议，而是给 Agent 一份"何时调用哪个 skill、按什么顺序、卡什么验证"的工程作业指导。

如果团队已经在用 Claude Code / Cursor / Codex / Copilot / Cline，并在为"Agent 容易跨阶段跳过验证"发愁，这个 skill 包值得先评估；如果只是临时写一次性脚本，收益不明显。

## 系统地图：六阶段 + 24 skills

skill 包按开发生命周期组织，前后两道门（defining 与 shipping）中间是四个执行态：

```
  DEFINE          PLAN           BUILD          VERIFY         REVIEW          SHIP
 ┌──────┐      ┌──────┐      ┌──────┐      ┌──────┐      ┌──────┐      ┌──────┐
 │ Idea │ ───▶ │ Spec │ ───▶ │ Code │ ───▶ │ Test │ ───▶ │  QA  │ ───▶ │  Go  │
 │Refine│      │  PRD │      │ Impl │      │Debug │      │ Gate │      │ Live │
 └──────┘      └──────┘      └──────┘      └──────┘      └──────┘      └──────┘
 /spec          /plan          /build        /test         /review       /ship
```

24 个 skill 不是一个扁平清单，而是按这六个阶段归类：

| 阶段 | skill 数量 | 阶段角色 |
| --- | --- | --- |
| Meta（入口） | 1 | 判定走哪个 skill |
| Define（澄清） | 3 | 把模糊需求变成确定 spec |
| Plan（拆解） | 1 | 把 spec 切成可执行的小任务 |
| Build（实施） | 7 | 在不同上下文中按方法论写代码 |
| Verify（证明） | 2 | 用工具跑验证 |
| Review（把关） | 4 | 质量/安全/性能/可读性 |
| Ship（上线） | 6 | 部署、迁移、可观测、文档 |

这种划分方式最大价值是：**让 Agent 不再"为一个 prompt 跨阶段"**——问"一个新项目怎么开始"时它跑 `/spec` + `/plan`，问"如何修这个 bug"时它跑 `/test` + `/debug`。每条命令进入一条独立链路，而不是一锅烩。

## 关键设计原则

读 24 个 SKILL.md 后，能抽出几条贯穿全局的原则，这也是它区别于"随便写几条 prompt 模板"的根因：

### 1. 步骤 / 验证门 / 反合理化表三件套

每个 skill 都不是单独一行规则，而是结构化为：

- **Steps**（执行步骤）
- **Verification gate**（验证门）
- **Anti-rationalization table**（反合理化表：把"我以为可以省掉这一步"的借口提前堵掉）

比如 `test-driven-development` 里就明确写了"对'这是个简单改动不需要写测试'的反合理化"。这是工程师常犯的认知偏移，提前列出能减少 Agent 跳过验证的概率。

### 2. 量化的质量目标

skill 里常出现"5-axis review"、"~100 lines / commit"、"80/15/5 测试金字塔"、"Beyonce Rule（if you liked it then you should've put a test on it）"等具体阈值或口诀。不是空泛的"写好测试"，而是 **"测试金字塔 80/15/5，分别对应单元/集成/E2E"** 这种可直接验收的指标。

### 3. TDD 不留妥协

`test-driven-development` 写明"Red-Green-Refactor, test pyramid (80/15/5), test sizes, DAMP over DRY"，对 "DAMP over DRY"（Descriptive And Meaningful Phrases）的偏向直接写在 skill 里——这与主流"DRY 到极致"的教条相反，值得正视。

### 4. 触发语境（context-driven activation）

Skills 也支持**自动激活**：当你让 Agent 设计 API，会自动激活 `api-and-interface-design`；构建 UI 会自动激活 `frontend-ui-engineering`。这是"显式命令 + 隐式触发"双轨—— 既能用 `/spec` 直接跳进，也能让 Agent 自己判定。

### 5. 一致性协作（`/build auto` 模式）

新增 `/build auto`：用户只需审一次 plan，所有任务一次性自动实施；但每步仍是 test-driven + 单 commit + 失败时停。换句话说：**自动化的是"人在中间的步骤"，不是"验证"**。这是份界限不糊涂的设计，对实际工程更安全。

## 24 个 Skill 一览

按开发生命周期阶段展开。下表仅揭示 skill 全景，**所有用法以仓库为准**：

### Meta

- `using-agent-skills`：session 起始判定该跑哪条 skill。
- 一句话价值：让你不"用什么都是同一条 skill"。

### Define（澄清）

- `interview-me`：一次只问一个问题，把模糊需求问到 95% 置信。
- `idea-refine`：发散→收敛，把粗概念变成具体提案。
- `spec-driven-development`：写 PRD 含目标、命令、目录、代码风格、测试、边界——再动代码。
- 三件套覆盖"用户说不清楚"这一最常见的工程入口。

### Plan（拆解）

- `planning-and-task-breakdown`：把 spec 切成可验收的小任务并排序依赖。
- 单一 skill 承担"把大事变成小事"的角色。

### Build（实施）—— 这是最大的族

- `incremental-implementation`：纵向切片（thin vertical slice），feature flag、可回滚。
- `test-driven-development`：Red-Green-Refactor，强制写测试。
- `context-engineering`：会话内喂规则文件、context packing、MCP 集成。
- `source-driven-development`：引用官方文档、标注未验证——避免 AI 答假。
- `doubt-driven-development`：CLAIM → EXTRACT → DOUBT → RECONCILE → STOP，对高风险决策做对抗性审阅。
- `frontend-ui-engineering`：组件架构、设计系统、状态管理、响应式、WCAG 2.1 AA。
- `api-and-interface-design`：契约优先、Hyrum's Law、One-Version Rule、错误语义、边界校验。
- 7 个 skill 共享"写之前先论证、别无脑堆代码"的纪律。

### Verify（验证）

- `browser-testing-with-devtools`：Chrome DevTools MCP，DOM/console/network/performance 联动。
- `debugging-and-error-and-recovery`：复现→定位→最小化→修复→加护栏。
- 两个 skill 接外部工具（DevTools / debugger），让验证不只靠单元测试。

### Review（把关）

- `code-review-and-quality`：五维 review、change ~100 行、Nit/Optional/FYI 严重度。
- `code-simplification`：Chesterton's Fence、Rule of 500、保留行为简化复杂度。
- `security-and-hardening`：OWASP Top 10、auth、密钥、依赖审计、三层边界。
- `performance-optimization`：先测后优化、Core Web Vitals 目标、bundle 分析。
- 走完"我写得对吗？跑得好吗？安全吗？够简洁吗？"四道门。

### Ship（上线）

- `git-workflow-and-versioning`：`trunk-based`、原子提交、~100 行/提交。
- `ci-cd-and-automation`：Shift Left、Faster is Safer、feature flag、quality gate。
- `deprecation-and-migration`：代码即负债、强制废弃 vs 自愿废弃、清除僵尸代码。
- `documentation-and-adrs`：ADRs、API 文档、注释的 "why"。
- `observability-and-instrumentation`：结构化日志、RED 指标、OpenTelemetry、症状告警。
- `shipping-and-launch`：上线前 checklist、灰度、回滚、监控。
- 6 个 skill 覆盖部署生命周期，是"上生产"前最常被跳过的环节。

## 与既有 Agent Skills 标准的差异

市面上 Agent Skills / rules / context packs 不少，addyosmani/agent-skills 的几个差异化点：

| 维度 | 该 skill 包 | 通用 rules / prompts |
| --- | --- | --- |
| 组织 | 六阶段生命周期 | 通常扁平清单 |
| 触发 | 显式命令 + 语境自动激活 | 多数只支持显式触发 |
| 验证 | 每个 skill 含 verification gate | 通常只讲"做什么" |
| 反合理化 | 显式 anti-rationalization 表 | 通常未覆盖 |
| 体量 | 24 个专门 skill | 5-10 条 prompt |

但它有一些限制要承认：

- **覆盖范围偏前端/JS 生态**：5-axis review、Chrome DevTools MCP、Core Web Vitals 都很贴 web 前端，纯后端 / 嵌入式项目用得上但比例低。
- **依赖具体客户端支持**：slash command 在 Claude Code / Cursor 里工作良好，但老 IDE 可能仅能"复制 SKILL.md 到 rules"。

## 接入方式

最快的路径：通过 Vercel Labs 的 `skills` CLI 一行安装到 70+ Agent：

```bash
npx skills add addyosmani/agent-skills            # 全装 24 个
npx skills add addyosmani/agent-skills --list     # 先看看再装
npx skills add addyosmani/agent-skills --skill test-driven-development   # 单装某个
```

Claude Code 用 marketplace：

```
/plugin marketplace add addyosmani/agent-skills
/plugin install agent-skills@addy-agent-skills
```

Cursor 把任何 `SKILL.md` 拷到 `.cursor/rules/`。

## 适用边界

**适合**：

- 工程团队中 Coding Agent 已经普及，但质量门控薄弱
- 想强制 TDD / code review / security scan 这些"日常工程动作"在 Agent 调用链中常驻
- 用 Claude Code / Cursor / Codex 这类支持 slash command 或 marketplace 的 IDE
- 中等规模团队：既能享受 skill 体系的纪律，又不至于被规则淹没

**不太适合**：

- 已经在大型内部 Skills/Cursor rules 系统上的团队——避免与现有体系冲突
- 一次性脚本生成（chat 提问即用即可）
- 重度 IDE 锁定（如 Eclipse / 老 JetBrains）——需要手工复制 SKILL.md
- 纯研究 / 不写生产的 Agent 场景

## 一句话总结

addyosmani/agent-skills 把"开发流程"本身当成可被调用的 skill 而不是 prompt，让 Coding Agent 进入"按阶段作业"的状态。它的强项是验证门、反合理化表与量化指标；限制是面向前端 / JS 生态偏重、不打算取代现有 IDE rules 体系。

## 参考链接

- 仓库：<https://github.com/addyosmani/agent-skills>
- skill 数：24（23 业务 + 1 meta）
- License：MIT
- 兼容 Agent：Claude Code / Cursor / Codex / Copilot / Cline 等
