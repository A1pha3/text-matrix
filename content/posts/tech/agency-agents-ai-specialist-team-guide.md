---
title: "The Agency：147个专业AI Agent组成的虚拟团队"
date: "2026-05-05T11:25:00+08:00"
slug: "agency-agents-ai-specialist-team-guide"
aliases:
  - "/posts/tech/agency-agents-complete-ai-agency-toolkit/"
  - "/posts/tech/the-agency-open-source-ai-agents-personas/"
  - "/posts/tech/ai-agent/agency-agents-multi-agent-framework-guide/"
description: "The Agency是一个包含147个专业AI Agent的开源项目，覆盖工程、设计、销售、营销等12个领域。每个Agent拥有独特人格、专业流程和可衡量产出，可接入Claude Code、Cursor、Windsurf等主流AI编程工具。本文详解其架构设计、Agent分类、集成方式与实际应用场景。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Claude Code", "Cursor", "多工具集成", "AI团队", "OpenClaw"]
---

# The Agency：147 个专业 AI Agent 组成的虚拟团队

## 学习目标

读完本文后，你应该能：

1. 说清 The Agency 与通用提示词模板在结构上的差异，并指出差异落在哪 5 个字段上。
2. 列出 12 个部门的边界，判断自己团队职能对应哪几个 Agent。
3. 在 Claude Code、Cursor、OpenClaw 三类工具中选一种完成首次安装，并解释为什么选这一种。
4. 复述一次"工程部 Agent 审查 PR"的任务流转路径，说明每个环节的输入和输出。
5. 根据团队规模和现有工具栈，给出一个分阶段的采用顺序。

## 目录

- [学习目标](#学习目标)
- [项目判断](#项目判断)
- [核心设计理念](#核心设计理念)
- [12 个专业部门一览](#12-个专业部门一览)
- [快速开始](#快速开始)
- [工程部 Agent 详解](#工程部-agent-详解)
- [多工具集成架构](#多工具集成架构)
- [Codex 集成（高级选项）](#codex-集成高级选项)
- [任务如何流过系统——一次 PR 审查的完整路径](#任务如何流过系统一次-pr-审查的完整路径)
- [应用场景示例](#应用场景示例)
- [适用场景与边界](#适用场景与边界)
- [常见问题与错误排查](#常见问题与错误排查)
- [动手练习](#动手练习)
- [自测清单](#自测清单)
- [进阶路径](#进阶路径)
- [采用顺序与决策建议](#采用顺序与决策建议)

---

## 项目判断

[The Agency](https://github.com/msitarzewski/agency-agents) 做了一件事：把 AI Agent 从"一个通用助手"拆成 147 个岗位，每个岗位是一份 Markdown 文件，定义人格、使命、工作流、交付物和记忆策略。它不解决模型能力问题。同一个 Claude Opus，挂了 Frontend Developer 的 Agent 文件和挂了 Backend Architect 的 Agent 文件，输出会走两条完全不同的路——但底层模型没变。

这套仓库的实际用法是按团队职能挑几个岗位单独跑或按 pipeline 串联，再通过配置文件替换模型、输出目录和外部凭据。一次装 147 个 Agent 反而是少数场景。把它理解成一组可组合的岗位库比理解成"超大号提示词包"更接近真实用法——后者会让人忽略它里面的工程约束（工作流步骤、交付物格式、退出条件）。

**项目数据**（以下数据来自仓库 [README](https://github.com/msitarzewski/agency-agents#readme) 和 [tags 页面](https://github.com/msitarzewski/agency-agents/tags)，获取时间 2026-05-05）：

- GitHub Stars：1,000+
- Agent 总数：147 个（去重后），按部门计数约 172
- 覆盖领域：12 个部门
- 支持工具：Claude Code、Cursor、OpenClaw、Windsurf 等主流工具（完整列表见仓库 README）
- 开源协议：MIT

---

## 核心设计理念

### 从通用提示词到专业 Agent 的范式转变

传统 AI Agent 方案通常用一个提示词模板应对各种场景。The Agency 按岗位拆分，每个 Agent 专精某个细分领域，定义里包含 5 个固定字段：

| 字段 | 含义 | 作用 |
|------|------|------|
| 人格（Personality） | 沟通风格和思维方式 | 让输出语气符合岗位身份，例如销售工程师和后端架构师的口吻不同 |
| 核心使命（Mission） | 职责边界和成功标准 | 限制 Agent 不会越界回答 |
| 工作流程（Workflow） | 经过生产环境验证的执行步骤 | 把"该怎么做这件事"固化成步骤，减少模型自由发挥 |
| 交付物（Deliverables） | 可量化的具体产出 | 把"给个建议"变成"给一份带字段的结构化文档" |
| 学习记忆（Memory） | 持续改进的能力积累 | 跨会话保留项目上下文 |

这 5 个字段是 The Agency 与通用提示词模板的核心差异点。通用模板通常只有"角色 + 任务"两层，The Agency 多了工作流、交付物和记忆三层约束。

---

## 12 个专业部门一览

The Agency 的组织架构模拟了真实公司结构，按职能拆成 12 个部门。这样组织的好处是团队容易找到对应职能的 Agent，也方便按部门批量管理（例如只装工程部到 Claude Code、只装市场部到 Cursor）：

| 部门 | Agent 数量 | 代表角色 |
|------|-----------|---------|
| 💻 工程部 | 25+ | 前端开发者、后端架构师、AI 工程师、安全工程师 |
| 🎨 设计部 | 8 | UI 设计师、UX 研究员、品牌守护者 |
| 💼 销售部 | 10 | 外展策略师、交易策略师、销售工程师 |
| 📢 市场部 | 30+ | 增长黑客、内容创作者、Twitter 运营、知乎专家 |
| 📊 产品部 | 5 | Sprint 优先排序器、趋势研究员、行为推动引擎 |
| 🎬 项目管理 | 7 | 制片人、项目牧羊人、实验追踪员 |
| 🧪 测试部 | 9 | 证据收集员、性能基准测试员、API 测试员 |
| 🛟 支持部 | 7 | 支持响应员、分析报告员、财务追踪员 |
| 🥽 空间计算 | 6 | XR 界面架构师、visionOS 工程师 |
| 🎯 专业部 | 40+ | MCP 构建器、智能合同审计员、Salesforce 架构师、法务顾问、医疗合规专员 |
| 💵 财务部 | 5 | 簿记员、财务分析师、税务策略师 |
| 🎮 游戏开发 | 20+ | Unity/Unreal/Godot 专项工程师 |

> 表中数字为各部门 README 列出的岗位数（截至 2026 年 5 月主分支），加总约 172。部分 Agent 同时挂靠多个部门，按部门计数会重复——例如 Security Engineer 同时出现在工程部和专业部，Codebase Onboarding Engineer 既属于工程部也被测试部引用，Analytics Reporter 在市场部和支持部都有 entry。这 25 个差值主要来自这类跨部门挂靠。法务、医疗类 Agent 归在专业部下。

12 个部门加起来覆盖了从代码到法务的常见岗位。其中工程部、市场部和专业部是数量最多的三个部门，分别对应"写代码""做增长""处理垂直领域专家任务"三类高频需求。专业部里的 MCP（Model Context Protocol，模型上下文协议）构建器和智能合同审计员是这套仓库里比较少见的岗位，前者负责把外部工具封装成 MCP 服务，后者负责审计 EVM（Ethereum Virtual Machine，以太坊虚拟机）合约的 gas（链上燃料费）消耗和安全漏洞。

---

## 快速开始

### 方式一：接入 Claude Code（推荐）

```bash
# 克隆仓库
git clone https://github.com/msitarzewski/agency-agents.git
cd agency-agents

# 安装所有 Agent 到 Claude Code 目录
./scripts/install.sh --tool claude-code

# 在 Claude Code 中激活
# "Hey Claude, activate Frontend Developer mode and help me build a React component"
```

推荐 Claude Code 的原因是它的 Agent 文件直接落在 `~/.claude/agents/` 下，不需要额外转换层，调试时改 Markdown 就能生效。

### 方式二：接 OpenClaw

```bash
# 先生成 OpenClaw 格式文件
./scripts/convert.sh --tool openclaw

# 安装
./scripts/install.sh --tool openclaw

# 重启 OpenClaw 网关（示意命令，具体子命令以 OpenClaw 版本为准）
openclaw gateway restart
```

Agent 会以独立 workspace（工作区）形式出现在 `~/.openclaw/agency-agents/` 下，每个 Agent 拥有自己的 `SOUL.md`、`AGENTS.md` 和 `IDENTITY.md`（这三个文件名是 OpenClaw 的 workspace 约定，具体字段映射以仓库 `scripts/convert.sh` 实际生成为准）。OpenClaw 用 workspace 隔离每个 Agent，让多个 Agent 能并行运行而不互相覆盖上下文。

### 方式三：接入 Cursor

```bash
cd your-project
# 实际路径以仓库克隆位置为准，例如 ~/projects/agency-agents/scripts/install.sh
/path/to/agency-agents/scripts/install.sh --tool cursor
```

Agent 转化为 `.mdc` 规则文件存于 `.cursor/rules/` 目录。Cursor 用 `.mdc` 文件管理规则，Agent 的人格和工作流被拆成规则片段，在编辑器里按文件类型自动激活。

---

## 工程部 Agent 详解

工程部是仓库里岗位最多、覆盖最广的部门，包含 25+ 个专业工程师角色。

### 核心技术 Agent

| Agent | 专长 | 使用场景 |
|-------|------|---------|
| Frontend Developer | React/Vue/Angular、UI 实现、Web Vitals 优化 | 现代 Web 应用开发、像素级精确 UI 实现、Core Web Vitals 优化 |
| Backend Architect | API 设计、数据库架构、可扩展性规划 | 服务端系统设计、微服务架构、云基础设施规划 |
| AI Engineer | ML 模型部署、流水线构建、AI 集成 | 机器学习功能开发、数据管道、LLM 应用集成 |
| Security Engineer | 威胁建模、安全代码审计、安全架构 | 应用安全评估、漏洞分析、安全 CI/CD 设计 |
| Autonomous Optimization Architect | LLM 路由、成本优化、影子测试 | 需要智能 API 选择和成本护栏的自主系统 |

### 特殊领域 Agent

| Agent | 专长 | 使用场景 |
|-------|------|---------|
| Embedded Firmware Engineer | ESP32/STM32 bare-metal | 嵌入式系统、物联网设备 |
| Solidity Smart Contract Engineer | EVM 合约、gas 优化 | DeFi 协议、安全智能合约 |
| Codebase Onboarding Engineer | 源码阅读、代码路径追踪 | 新人快速熟悉陌生代码库 |
| Feishu Integration Developer | 飞书开放平台、机器人 | 飞书生态集成开发 |
| Email Intelligence Engineer | 邮件解析、MIME 提取 | 将邮件线程转化为结构化上下文 |

特殊领域 Agent 覆盖的是通用 LLM 不擅长的窄场景。例如 Solidity Smart Contract Engineer 会把 gas 优化和重入攻击检查写进工作流，把"审查合约"这种宽泛指令收窄成可执行的检查项——这种窄场景约束是通用提示词做不到的。

---

## 多工具集成架构

The Agency 通过 `convert.sh` 和 `install.sh` 两个脚本统一管理 11 种工具的接入：

```bash
# 第一步：生成各工具对应的格式文件
./scripts/convert.sh              # 串行生成
./scripts/convert.sh --parallel   # 并行生成（更快）

# 第二步：安装（交互式，自动检测已安装的工具）
./scripts/install.sh
```

安装脚本扫描系统，自动检测已安装的工具，以复选框 UI 呈现。`convert.sh` 把统一的 Agent 定义转换成各工具需要的格式（Claude Code 用 `.md`，Cursor 用 `.mdc`，OpenClaw 用 `SOUL.md` + `AGENTS.md`），`install.sh` 把转换后的文件落到对应工具的配置目录。两层分离的好处是新增工具支持只要写一个新的 converter，不用动安装逻辑。

## Codex 集成（高级选项）

除了 Claude Code、Cursor 和 OpenClaw，The Agency 也支持 OpenAI Codex CLI。Codex 的 Agent 格式不同于前三者，需要额外的权限声明文件：

```bash
./scripts/convert.sh --tool codex
./scripts/install.sh --tool codex
```

生成的文件在 `.codex/agents/` 下。Codex 模式下，Agent 的"人格"字段被映射到 Codex 的 `AGENTS.md` 角色描述，"工作流"被映射到 `CODEBUDDY.md` 的步骤约束（Codex 的 Agent 文件格式以 OpenAI Codex CLI 官方文档为准，本节描述需在安装时核实）。如果你在用 Codex 做长会话开发任务，这套映射让你不用在 Codex 和 Claude Code 之间维护两套 Agent 描述。

---

## 任务如何流过系统——一次 PR 审查的完整路径

说清 Agent 之间怎么配合，比列举每个 Agent 的功能更有用。下面用一个具体任务——审查一个新增支付接口的 PR——串起 5 个 Agent 的完整链路。

```text
任务：审查 PR #142（新增 /api/checkout 支付接口）

步骤 1：Codebase Onboarding Engineer
  输入：PR diff + 仓库结构
  输出：一份"这个改动影响了哪些模块"的路径报告
  动作：识别出 checkout 路由、订单模型、支付网关适配器三处变更

步骤 2：Backend Architect
  输入：步骤 1 的路径报告 + PR diff
  输出：API 设计评审（路由命名、错误码、幂等性）
  动作：指出 /api/checkout 缺少 idempotency key

步骤 3：Security Engineer
  输入：步骤 2 的评审 + PR diff
  输出：威胁建模报告（关注支付金额篡改、重放攻击）
  动作：标记 amount 字段未做服务端校验

步骤 4：Autonomous Optimization Architect
  输入：步骤 2 和 3 的报告
  输出：成本与路由建议（哪些检查走小模型，哪些走大模型）
  动作：建议金额校验走 GPT-4o，威胁建模走 Claude Opus

步骤 5：Reality Checker（测试部）
  输入：前面所有报告
  输出：验收清单 + 阻断项
  动作：列出 3 个必须修复的阻断项和 5 个建议项
```

每个 Agent 的输入都来自上游的交付物，输出又成为下游的输入。Agent 之间不直接通信——靠 Markdown 文件传递上下文。这种设计带来三条实际的使用方式：

- **只用两三个 Agent**：你不需要把整条链路跑完。如果只是想审查 API 设计，只跑 Backend Architect 就够了。
- **跑整条链路**：从 Codebase Onboarding 到 Reality Checker，每一步的输出都可以单独存档——六个月后审计这个 PR 为什么通过了某处改动，你能追溯到当时哪个 Agent 给出了什么判断。
- **中间任何一步断了**：如果 Security Engineer 的输入里缺了 Backend Architect 的评审结论，它仍然能工作——但会重复做一些 Backend Architect 已经做过的判断。这是 pipeline 模式的通病：上下文传递靠文件，上游更新了下游文件不会自动刷新。解决方式是在 pipeline 脚本里加一条规则：下游 Agent 启动前检查上游产出文件的修改时间，如果比自己的输入文件旧，先重新读取。

---

## 应用场景示例

### 场景一：构建创业公司 MVP

**团队配置：**
1. 🎨 Frontend Developer — 构建 React 应用
2. 🏗️ Backend Architect — 设计 API 和数据库
3. 🚀 Growth Hacker — 规划用户增长策略
4. ⚡ Rapid Prototyper — 快速迭代
5. 🔍 Reality Checker — 上线前质量验证

这个配置从代码骨架搭建、接口设计、增长策略到上线前质量验证都覆盖到了。Frontend Developer 和 Backend Architect 的产出通过接口约定对接，Growth Hacker 在产品成型后接入，Reality Checker 在上线前做质量验证。如果团队只有一个人，可以先跑 Frontend Developer 和 Backend Architect 两个，把 MVP 的代码骨架搭出来，再按需要补 Growth Hacker 和 Reality Checker。

### 场景二：多渠道营销活动

**团队配置：**
1. 📝 Content Creator — 活动内容策划
2. 🐦 Twitter Engager — Twitter 策略与执行
3. 🤝 Reddit Community Builder — Reddit 社区运营
4. 📊 Analytics Reporter — 效果追踪优化

营销场景下，Content Creator 产出活动主题和核心文案，Twitter Engager 和 Reddit Community Builder 各自改写一次，适配不同平台的语气和长度限制。Analytics Reporter 在最后接入，把各渠道数据汇总成一份带归因的报告。

---

## 适用场景与边界

### 适合的场景

最典型的情况是同一个模型跑不同任务时输出质量波动大。同一个 Claude Opus，写 React 组件时表现不错，审 SQL 查询时漏掉索引问题——The Agency 的工作流字段把"怎么审 SQL"写成固定步骤，模型只负责在步骤内做判断，把模型的自由发挥收窄到可预期的范围里。

如果你已经在用 Claude Code、Cursor 或 Windsurf，但每次都要手动写长篇提示词才能让 AI 按特定角色工作，Agent 文件把这套东西固化下来，下次直接加载就行。需要给不同职能的同事（前端、后端、安全）各配一套 AI 辅助时也是同理——装对应的 Agent 文件即可，不用每个人从零写提示词。还有一种偏管理层面的需求：希望团队共享一套"AI 辅助标准"，所有人用的 Frontend Developer Agent 是同一份文件，产出格式一致，方便事后审计和复盘。

### 不适合的场景

- 你对单个通用提示词的输出已经满意——不需要拆 147 个岗位。
- 你的任务只用一个角色连续工作——比如纯写前端页面，一个 Frontend Developer 就够了。装 147 个 Agent 只会让 token 消耗无意义膨胀。
- 你需要 Agent 自己写代码执行——The Agency 的 Agent 是 Markdown 定义的人格和工作流，不包含可执行代码。Agent 输出的"代码建议"仍然需要人来落地。

### 边界与局限

- Agent 文件里写的是"怎么想""怎么做"，不包含实际的代码执行能力——它不能替你部署、不能替你跑测试。
- 输出质量绑定底层模型——Agent 文件约束的是行为规范，不是模型能力。Claude Haiku 跑的 Backend Architect 和 Claude Opus 跑的 Backend Architect，产出质量会有差距。
- 部分细分 Agent（法律、医疗）只是参考性质的岗位描述，不能替代专业咨询。
- 147 个 Agent 全部安装会带来 token 消耗——每个 Agent 的定义文件都会被加载到上下文，全部安装是额外的 token 开销。建议按需装，不要一键全装。

---

## 常见问题与错误排查

### Q1：安装后 Agent 没有出现在工具里

排查顺序：
1. 检查对应工具的配置目录是否有文件（Claude Code 看 `~/.claude/agents/`，Cursor 看 `.cursor/rules/`）
2. 确认 `convert.sh` 是否执行成功，看终端有没有报错
3. 重启对应工具或网关（OpenClaw 需要执行 `openclaw gateway restart`）

### Q2：Agent 输出和预期不符

常见原因：
- 底层模型能力不足：复杂岗位（如 Backend Architect）建议用 Claude Opus 或 GPT-4 级别模型
- 上下文不够：Agent 的工作流依赖项目上下文，首次使用时先让 Codebase Onboarding Engineer 跑一遍
- Agent 被串错了顺序：pipeline 模式下，上游交付物没传给下游，导致下游 Agent 缺信息

### Q3：token 消耗过大

控制方法：
- 按需安装，不要一次装满 147 个
- 用 Autonomous Optimization Architect 做路由，把简单检查交给小模型
- 在 Agent 定义里限制输出长度，避免长篇大论

### Q4：能否自定义 Agent

可以。Agent 本质是 Markdown 文件，复制一份现有 Agent，修改人格、使命、工作流和交付物字段即可。建议从相近岗位改起——例如从 Backend Architect 改出 Platform Engineer，比从零写一份更稳。改完后放到对应部门的目录下，重跑 `convert.sh && install.sh` 即可生效。

## 动手练习

下面三个练习从浅到深，建议按顺序做。第一个验证基本使用，第二个验证协调链路，第三个让你上手定义合规约束。

### 练习一：装三个工程部 Agent 跑一次代码审查

1. 用 `./scripts/install.sh --tool claude-code` 装三个 Agent：Backend Architect、Security Engineer、Reality Checker
2. 找一段你最近写的 API 代码（没有的话用下面这段模拟）：

```python
# checkout.py
def create_checkout(user_id, items, total):
    # 直接操作数据库，无认证检查
    order = db.insert("orders", {"user_id": user_id, "total": total})
    for item in items:
        db.insert("order_items", {"order_id": order.id, **item})
    return {"order_id": order.id, "status": "created"}
```

3. 依次让 Backend Architect 审查 API 设计 → Security Engineer 审查安全漏洞 → Reality Checker 做最后的阻断判断
4. 记录每个 Agent 产出的交付物格式和时间。回答：
   - Backend Architect 有没有指出缺少幂等性保护？
   - Security Engineer 有没有标记 `user_id` 未校验？
   - Reality Checker 列出的阻断项中有几条是你没注意到的？

### 练习二：用 pipeline 串联三个 Agent 做一次 PR 审查

按本文"任务如何流过系统——一次 PR 审查的完整路径"一节跑一遍：Codebase Onboarding Engineer → Backend Architect → Security Engineer。要求：

1. 每一步的产出写入 Markdown 文件（例如 `01-onboarding.md`、`02-architecture.md`、`03-security.md`）
2. 下游 Agent 读取上游产出文件作为输入——不能在 prompt 里手动复述上游结论
3. 跑完后对比：整条 pipeline 的最终输出和单独跑三个 Agent 各给结论相比，pipeline 版本多发现了什么问题？少了什么问题？

这个练习的重点是感受 Agent 之间通过文件传递上下文时会丢什么信息、会保留什么偏见。pipeline 不一定比单独跑好——这条判断要在练习里自己验证。

### 练习三：基于 Backend Architect 改一个你团队专属的 Code Reviewer

1. 复制 Backend Architect 的 Markdown 文件
2. 修改 5 个字段，让它适配你团队的代码规范：
   - **人格**：改成你们团队 code review 的风格（直接/委婉、逐行批注/汇总评论）
   - **使命**：加上你团队特有的关注点（例如"所有 SQL 必须有 EXPLAIN 注释""所有 API 返回必须带 request_id"）
   - **工作流**：把你们团队的 review checklist 写成步骤
   - **交付物**：定义输出格式——例如"必须在每个问题后标注文件路径和行号"
   - **记忆**：指定记忆存储位置和回溯策略
3. 用同一段代码分别跑你改过的 Agent 和原版 Backend Architect，对比两版输出的差异。记录哪些差异是团队定制带来的、哪些是模型带来的随机性。

## 自测清单

用"能/不能"回答下面 7 题，答"不能"就回对应章节重读。

| # | 自测项 | 答"不能"时回看 |
|---|--------|---------------|
| 1 | 能说出 The Agency 与通用提示词模板在 5 个字段上的差异 | [核心设计理念](#核心设计理念) |
| 2 | 能列出 12 个部门，并指出你团队职能对应哪 3 个以内的部门 | [12 个专业部门一览](#12-个专业部门一览) |
| 3 | 能解释为什么 12 个部门 Agent 数量之和大于 147——以及哪些 Agent 被重复计数 | [12 个专业部门一览](#12-个专业部门一览) |
| 4 | 能在 Claude Code、Cursor、OpenClaw 中选一种完成从安装到跑通一个 Agent 的完整流程 | [快速开始](#快速开始) |
| 5 | 能描述一次 PR 审查 pipeline 中上游产出如何传递给下游、断在中间会发生什么 | [任务如何流过系统](#任务如何流过系统一次-pr-审查的完整路径) |
| 6 | 能根据团队规模和现有工具栈给出分阶段采用顺序 | [采用顺序与决策建议](#采用顺序与决策建议) |
| 7 | 能基于现有 Agent 文件自定义一个团队专属 Agent，并验证它比通用版本更贴合自己的规范 | [动手练习](#动手练习) |

## 进阶路径

读完本文后，按下面的顺序深化：

1. **挑一个部门深读**：打开仓库里该部门的每个 Agent 文件，不要只读概括表。重点关注工作流（Workflow）字段——它直接决定 Agent 的产出稳定性。你会发现同一个部门下不同 Agent 的工作流颗粒度差别很大：有的写死了 5 步检查，有的只写了"分析问题并给出建议"。前者更稳但更僵，后者更灵活但更随模型能力波动。
2. **读 `convert.sh` 和 `install.sh` 源码**：理解 Agent Markdown → 工具配置文件的转换逻辑。这对你之后批量管理 Agent（比如"只装市场部 Agent 到 Cursor、只装工程部到 Claude Code"）是必要的。
3. **设计一个"Agent 间协议"**：当你需要 3 个以上 Agent 协同工作时，靠口头约定传递上下文迟早出问题。定义一个最小协议——例如"每个 Agent 的交付物必须包含 `输入源`、`关键假设`、`结论`、`不确定项` 四个字段"——然后修改 Agent 的交付物字段来执行这个协议。
4. **跟踪 The Agency 仓库的 releases 页面**：作者 Msitarzewski 在持续增加新 Agent 和优化工作流。关注 `CHANGELOG.md` 里工作流变更的条目——这些变更往往反映了"某个 Agent 的旧工作流在生产中暴露了什么缺陷"。

---

## 采用顺序与决策建议

### 分阶段采用路线

**第一阶段：验证（第 1-2 周）**

装工程部 3 个核心 Agent：Frontend Developer、Backend Architect、Codebase Onboarding Engineer。在一个真实小项目上跑"读代码 → 写代码 → 审代码"的闭环。这阶段的目标是确认 Agent 文件格式和你的工具链能配合——命令能不能安装成功、Agent 能不能被加载、输出有没有落到预期格式。产出质量放到第二阶段再盯。

**第二阶段：按需扩展（第 3-4 周）**

根据团队职能补 Agent：有测试团队就装测试部，有增长需求装市场部。把 pipeline 串起来，让上下游 Agent 通过 Markdown 文件传递交付物。这阶段开始盯产出质量——Agent 是否稳定输出了交付物字段要求的格式、上下游之间的信息有没有丢失。

**第三阶段：定制化（第 5 周以后）**

从现有 Agent 改出团队专属版本。把 Autonomous Optimization Architect 用起来做模型路由，控制 token 成本。把记忆策略接上团队的知识库（wiki、设计文档、post-mortem）。

### 谁该先上，谁可以等等

**现在该上的：**

已在用 Claude Code 或 Cursor 的团队优先——Agent 文件直接落到工具目录下，没有额外工程门槛。其次是同一模型在不同任务上输出波动大的团队，The Agency 的工作流约束是直接对症的解法。还有一种情况是需要团队共享一套 AI 辅助标准的组，Agent 文件的版本管理（Git）让所有人都加载同一版约束。

**可以等等的：**

还在用通用提示词、没有固定 AI 编程工具的团队，先选定工具（建议从 Claude Code 起步）再考虑 The Agency。团队不满 3 人且没有跨职能需求的情况也建议缓一缓——单人项目里 Agent 协调的成本（文件管理、pipeline 维护）可能超过收益。至于只有非工程需求（纯营销、纯财务）的团队，可以直接装对应部门的 Agent，不用装工程部，但前提仍然是先选定一个固定的 AI 工具。

### 决策检查清单

回答下面三个问题，答"是"越多，The Agency 越值得试：

- 你是不是经常在同一个 AI 工具里反复写"你现在是 XXX 角色，请按以下步骤..."这类提示词？
- 你的团队有没有跨职能的 AI 使用需求（前端、后端、测试、安全各要一套）？
- 你需不需要让不同人使用同一套 AI 辅助标准（统一输出格式、统一审查步骤）？

三个都答"是"的话，这周装三个 Agent 跑一次练习一的代码审查，感受一下统一约束带来的输出一致性变化。

---

**参考链接：**
- GitHub：https://github.com/msitarzewski/agency-agents
- 官方文档：https://github.com/msitarzewski/agency-agents#readme
