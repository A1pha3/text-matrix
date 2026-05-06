---
title: "CodeBurn：AI 编码 Token 消耗可视化仪表盘"
date: "2026-04-16T11:32:26+08:00"
slug: "codeburn-ai-coding-token-observability"
description: "本文从问题动机、架构设计、数据采集原理、任务分类机制等维度，对 AI 编码 Token 可视化工具 CodeBurn 进行了深度剖析，涵盖交互式 TUI 仪表盘、多 Provider 支持、One-Shot 成功率等核心功能的完整使用指南与开发扩展路径。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "Claude Code", "Cursor", "Token", "开发者工具", "TypeScript"]
---

# CodeBurn：AI 编码 Token 消耗可视化仪表盘 ⭐⭐⭐ 进阶分析

> **目标读者**：使用 Claude Code、Codex、Cursor 等 AI 编码工具的开发者
> **核心问题**：你的 AI 编程工具烧了多少钱？Token 花在了哪里？如何优化？
> **预计时间**：约 20 分钟
> **前置知识**：了解 Claude Code 或类似 AI 编程工具的基本使用

---

## §1 学习目标

完成本教程后，你将能够：

- [ ] 理解 CodeBurn 的核心定位与解决的问题
- [ ] 掌握 CodeBurn 的技术架构与数据采集原理
- [ ] 熟练使用 CodeBurn 的交互式 TUI 仪表盘
- [ ] 配置多币种结算与菜单栏小组件
- [ ] 基于 CodeBurn 数据优化 AI 编码成本

---

## §2 原理分析

### 2.1 问题动机：为什么需要 CodeBurn？

AI 编程工具正在成为开发者的日常生产力引擎，但与此同时，一个被忽视的问题是：**Token 成本的不透明性**。

当你使用 Claude Code 完成一个项目时，你往往只看到"用了多少钱"的模糊数字，却无法回答以下问题：

- 这周花在调试（Debugging）上的 Token 占比是多少？
- 哪个项目的 AI 成本最高？是新功能开发还是代码审查？
- Claude Opus 和 Sonnet 的使用比例是否合理？是否过度使用了昂贵模型？
- Cursor 的"Auto"模式实际消耗了多少 Token？

这些问题催生了 CodeBurn 的设计：**一个无代理、无侵入的 Token 消耗可视化工具**。

### 2.2 核心设计原则

CodeBurn 遵循三个核心设计原则：

**1. 无 API Key 依赖**
大多数 Token 监控工具需要你提供 AI 平台的 API Key，这带来额外的安全风险和配置成本。CodeBurn 另辟蹊径，直接读取本地会话文件——这是 AI 编码工具在磁盘上存储的原始数据，不涉及任何第三方服务。

**2. 无需 Wrapper 或代理**
不像一些方案需要你通过代理路由流量，CodeBurn 完全是被动的——它只是读取已有的数据文件，不影响 AI 工具的正常运行。

**3. 提供上下文，而不只是数字**
单纯的"今天花了 $X"没有太大意义。CodeBurn 将消费数据与任务类型、使用的模型、提供商进行交叉分析，帮助你理解**钱花在哪里、为什么花在那里**。

### 2.3 数据采集原理

CodeBurn 支持六种主流 AI 编码工具，数据采集方式各有不同：

#### Claude Code

Claude Code 将每次会话的完整交互记录为 JSONL 文件，存储在 `~/.claude/projects/<项目路径>/<会话ID>.jsonl`。每条记录包含：

- 模型名称（opus-3-5, sonnet-4-20250514 等）
- Token 消耗明细（input tokens、output tokens、cache read、cache write）
- 工具调用记录（tool_use 块）
- 时间戳

CodeBurn 的 `providers/claude.ts` 模块负责发现这些文件、解析 JSONL 并进行去重（通过 API message ID）。

#### Codex (OpenAI)

Codex 将会话存储在 `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`，格式与 Claude Code 不同：

- 使用 `token_count` 事件记录每次调用的 Token 总量和累计量
- 使用 `function_call` 条目记录工具调用

CodeBurn 的 `providers/codex.ts` 还需要做额外的**工具名规范化**：因为 Codex 的工具名（如 `exec_command`）与 Claude 的命名习惯不同，CodeBurn 将其映射到统一名称（如 `Bash`），确保跨提供商的统计口径一致。

#### Cursor

Cursor 将数据存储在 SQLite 数据库中（macOS: `~/Library/Application Support/Cursor/User/globalStorage/state.vscdb`），这带来两个挑战：

1. **数据量大**：首次运行时，数据库可能非常大，解析时间长达一分钟
2. **模型不可见**：Cursor 的"Auto"模式不记录实际使用的模型

针对第一个挑战，CodeBurn 实现了文件缓存（`~/.cache/codeburn/cursor-results.json`），并在数据库变更时自动失效。第二个挑战通过估算解决——Auto 模式的成本按 Sonnet 定价计算，并在界面中标注为"Auto (Sonnet est.)"。

#### OpenCode

OpenCode 同样使用 SQLite，数据库路径为 `~/.local/share/opencode/opencode*.db`。CodeBurn 查询 `session`、`message`、`part` 三张表，提取 Token 数量，并按模型重新计算成本（而非直接使用 OpenCode 自带的成本字段，因为该字段可能使用了不同的定价标准）。

### 2.4 任务分类机制

CodeBurn 的核心分析能力之一是将 AI 的工作分类为 13 种任务类型。这是**纯规则判断**，不涉及 LLM 调用，完全确定性地分类：

| 任务类型 | 触发条件 |
|---------|---------|
| Coding | Edit、Write 工具被调用 |
| Debugging | 错误关键词出现 + 工具使用模式 |
| Feature Dev | "add"、"create"、"implement" 等关键词 |
| Refactoring | "refactor"、"rename"、"simplify" 等关键词 |
| Testing | Bash 中出现 pytest/vitest/jest |
| Exploration | Read、Grep、WebSearch 但无代码编辑 |
| Planning | EnterPlanMode、TaskCreate 工具被调用 |
| Delegation | Agent 工具被调用（AI 调度子任务） |
| Git Ops | Bash 中出现 git push/commit/merge |
| Build/Deploy | npm build、docker、pm2 等命令 |
| Brainstorming | "brainstorm"、"what if"、"design" 等关键词 |
| Conversation | 无工具调用的纯文本对话 |
| General | Skill 工具被调用或无法分类 |

### 2.5 成本计算引擎

CodeBurn 使用 [LiteLLM](https://github.com/BerriAI/litellm) 的定价数据作为基准，缓存 24 小时在 `~/.cache/codeburn/`。成本计算涵盖：

- **Input tokens**：模型处理输入的费用
- **Output tokens**：模型生成输出的费用
- **Cache write tokens**：写入上下文缓存的费用
- **Cache read tokens**：读取缓存的费用（通常大幅低于 input）
- **Web search tokens**：网络搜索调用的费用

Claude 的"快速模式"（Haiku）有额外的价格倍数，CodeBurn 也会处理。缓存机制确保每次启动无需重新拉取定价数据，同时保证数据相对新鲜。

---

## §3 架构分析

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                        CLI 入口                          │
│                    (Commander.js)                        │
│         codeburn [command] [options]                    │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                      Parser 层                           │
│              (JSONL 读取、去重、日期过滤)                  │
│   ┌─────────────────────────────────────────────────┐   │
│   │         Provider Registry (Lazy Load)           │   │
│   │  ┌─────────┐ ┌─────────┐ ┌─────────┐            │   │
│   │  │ Claude  │ │  Codex  │ │ Cursor  │ │ OpenCode │   │
│   │  └─────────┘ └─────────┘ └─────────┘ └─────────┘   │
│   └─────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                   Classifier 层                          │
│              (13 类任务分类器)                             │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                   Models 层                              │
│        (LiteLLM 定价数据 + 成本计算引擎)                  │
└──────────────────────┬──────────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  Dashboard  │ │   Export    │ │   Menubar   │
│  (Ink TUI)  │ │  CSV/JSON   │ │  SwiftBar   │
└─────────────┘ └─────────────┘ └─────────────┘
```

### 3.2 项目结构详解

```
src/
├── cli.ts              # Commander.js CLI 入口，命令路由
├── dashboard.tsx       # Ink（React for Terminal）TUI 仪表盘
├── parser.ts           # JSONL 读取器、Provider 协调、去重逻辑
├── models.ts           # LiteLLM 定价数据获取与成本计算
├── classifier.ts       # 13 类任务分类规则引擎
├── types.ts            # TypeScript 类型定义
├── format.ts           # 文本渲染（状态栏）
├── menubar.ts          # SwiftBar/xbar 插件生成器
├── export.ts           # CSV/JSON 多周期导出
├── config.ts           # 配置文件读写 (~/.config/codeburn/)
├── currency.ts         # 货币转换（Frankfurter API）
├── sqlite.ts           # SQLite 适配器（lazy-loads better-sqlite3）
├── cursor-cache.ts     # Cursor 结果文件缓存
└── providers/
    ├── types.ts        # Provider 接口定义
    ├── index.ts        # Provider 注册表
    ├── claude.ts       # Claude Code 会话发现与解析
    ├── codex.ts        # Codex 会话发现与解析
    ├── cursor.ts       # Cursor SQLite 解析
    └── opencode.ts     # OpenCode SQLite 解析
```

### 3.3 关键设计决策

**决策 1：Provider 插件化架构**

添加新的 AI 编码工具支持，只需要实现一个新的 Provider 文件，遵循 `types.ts` 中定义的接口。这种设计使得代码维护成本低，扩展性强。参考 `src/providers/codex.ts` 的实现即可快速添加 Pi、Amp 等新 Provider。

**决策 2：SQLite 懒加载**

`better-sqlite3` 是原生 Node.js 模块，在 Cursor/OpenCode 支持时才需要加载。如果用户只使用 Claude Code，该依赖不会被加载，保持了零额外开销。

**决策 3：文件缓存机制**

对于大文件（如 Cursor 的 SQLite 数据库），CodeBurn 在 `~/.cache/codeburn/` 中维护缓存，并在源文件变更时自动失效。这解决了首次运行慢（最长达一分钟）的问题，后续运行几乎是即时的。

**决策 4：多货币支持**

货币转换使用 [Frankfurter](https://www.frankfurter.app/) API（欧洲央行数据，免费无需 API Key），汇率缓存 24 小时。任何 ISO 4217 货币代码（162 种）都支持，满足国际化团队的需求。

---

## §4 功能详解

### 4.1 交互式 TUI 仪表盘

启动 CodeBurn 不带任何参数，默认进入 7 天视图的交互式仪表盘：

```bash
codeburn
```

界面布局（从上到下）：

- **Header**：总成本、Token 总量、模型分布概览
- **时间维度切换**：Today / 7 Days / 30 Days / Month，通过方向键切换
- **Provider 切换**：按 `p` 键在 Claude / Codex / Cursor / OpenCode 之间切换
- **主图表区**：成本趋势折线图（渐变色）
- **详细面板**：按项目、按模型、按任务类型的成本分解

**键盘快捷键**：

| 按键 | 功能 |
|------|------|
| `↑` / `↓` | 切换时间范围 |
| `1` / `2` / `3` / `4` | 直接跳转到 Today / 7 Days / 30 Days / Month |
| `p` | 切换 Provider |
| `q` | 退出 |

### 4.2 命令行模式

CodeBurn 支持纯命令行输出，适合集成到脚本或 CI 流程中：

```bash
# 今日概览（单行）
codeburn today

# 本月概览
codeburn month

# 报告模式（可带刷新间隔）
codeburn report -p 30days
codeburn report --refresh 60   # 每 60 秒自动刷新

# 状态查询（JSON 格式，便于程序处理）
codeburn status --format json

# 导出数据
codeburn export             # CSV（含今日、7 天、30 天）
codeburn export -f json     # JSON 导出
```

### 4.3 Provider 过滤

使用 `--provider` 参数限制统计范围：

```bash
codeburn report --provider claude    # 仅 Claude Code
codeburn today --provider codex      # 仅 Codex 今日数据
codeburn export --provider cursor    # 仅 Cursor 导出
```

### 4.4 多货币支持

```bash
codeburn currency GBP          # 切换为英镑
codeburn currency AUD          # 切换为澳元
codeburn currency JPY          # 切换为日元
codeburn currency              # 查看当前货币
codeburn currency --reset      # 重置为 USD
```

### 4.5 菜单栏小组件

```bash
codeburn install-menubar    # 安装 SwiftBar 插件
codeburn uninstall-menubar  # 移除插件
```

要求已安装 [SwiftBar](https://github.com/swiftbar/SwiftBar)（`brew install --cask swiftbar`）。菜单栏显示：

- 今日成本（火焰图标）
- 下拉菜单：活动类型分解、各模型成本、Token 统计、提供商对比
- 货币选择器（17 种常用货币）

每 5 分钟自动刷新。

### 4.6 One-Shot 成功率

CodeBurn 独特的 **One-Shot 成功率**指标，衡量 AI 在首次尝试中成功完成任务的比率：

- **检测逻辑**：当检测到"编辑 → Bash → 编辑"模式时，表明首次编辑触发了错误，需要重试
- **统计口径**：仅针对有编辑操作的回合，计算一次编辑就成功的比例
- **用途**：Coding 类别 90% 的一键成功率意味着 AI 在 90% 的情况下第一次编辑就做对了

这个指标是评估 AI 编程效率的重要维度——不仅仅是花了多少钱，更是钱花得值不值。

---

## §5 使用说明

### 5.1 安装

```bash
# 全局安装（推荐）
npm install -g codeburn

# 不安装直接运行
npx codeburn
```

**前置条件**：

- Node.js 20+
- 至少一种 AI 编码工具的会话数据：
  - Claude Code: `~/.claude/projects/`
  - Codex: `~/.codex/sessions/`
  - Cursor: macOS `~/Library/Application Support/Cursor/User/globalStorage/state.vscdb`
  - OpenCode: `~/.local/share/opencode/`

### 5.2 快速开始

**步骤 1：安装**

```bash
npm install -g codeburn
```

**步骤 2：验证安装**

```bash
codeburn --version
```

**步骤 3：运行仪表盘**

```bash
codeburn
```

你应该能看到过去 7 天的 Token 使用情况概览。

**步骤 4：查看今日数据**

```bash
codeburn today
```

**步骤 5：尝试导出**

```bash
codeburn export -f json > usage.json
```

### 5.3 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `CLAUDE_CONFIG_DIR` | `~/.claude` | 覆盖 Claude Code 数据目录 |
| `CODEX_HOME` | `~/.codex` | 覆盖 Codex 数据目录 |

### 5.4 数据目录结构

```
~/.cache/codeburn/
├── litellm-prices.json     # LiteLLM 定价缓存（24h）
├── currency-rates.json     # 汇率缓存（24h）
└── cursor-results.json     # Cursor SQLite 解析结果缓存

~/.config/codeburn/
└── config.json            # 用户配置（货币、Provider 等）
```

---

## §6 开发扩展

### 6.1 添加新的 Provider

假设你需要为新 AI 编程工具 `MyAI` 添加支持，只需创建 `src/providers/myai.ts`：

```typescript
import type { Provider, Session } from './types';

export class MyAIProvider implements Provider {
  name = 'myai';

  async discoverSessions(): Promise<string[]> {
    // 返回会话文件路径列表
  }

  async parseSession(path: string): Promise<Session> {
    // 读取并解析会话文件
    // 返回标准化 Session 对象
  }

  normalizeTool(toolName: string): string {
    // 将工具名映射到 CodeBurn 标准工具名
    return toolName;
  }

  getModelDisplayName(model: string): string {
    // 返回人类可读的模型名称
    return model;
  }
}
```

然后在 `src/providers/index.ts` 中注册：

```typescript
import { MyAIProvider } from './myai';

// 在 providerMap 中添加
const providerMap = {
  claude: ClaudeProvider,
  codex: CodexProvider,
  cursor: CursorProvider,
  opencode: OpenCodeProvider,
  myai: MyAIProvider,  // 新增
};
```

### 6.2 自定义任务分类规则

当前 13 类分类规则定义在 `src/classifier.ts` 中。每个规则由**触发条件**和**权重**组成。添加自定义分类：

```typescript
// src/classifier.ts
const customRules: ClassificationRule[] = [
  {
    name: 'Database Ops',
    keywords: ['sql', 'migration', 'schema', 'prisma'],
    weight: 1.5,  // 权重高于默认规则
    tools: ['Bash'],  // 特定工具触发
  },
];
```

### 6.3 导出到自有监控系统

CodeBurn 的 `status --format json` 输出可以重定向到任何监控系统：

```bash
# 每分钟采集一次并推送到 Prometheus
while true; do
  codeburn status --format json | jq '{codeburn_cost: .totalCostUSD, timestamp}'
  sleep 60
done
```

---

## §7 最佳实践

### 7.1 成本优化策略

**策略 1：监控 One-Shot 成功率低的类别**

如果 Debugging 的 One-Shot 成功率只有 40%，说明 AI 在调试时频繁需要多次尝试。可以通过：

- 提供更清晰的错误信息上下文
- 让 AI 先分析错误再动手修改
- 使用更强大的模型（如 Opus 而非 Sonnet）处理复杂调试

**策略 2：按项目分配成本**

通过 CodeBurn 的 per-project 视图，找出成本异常高的项目。常见原因：

- 频繁的大规模重构（触发高比例 Refactoring）
- 测试覆盖率不足导致反复修复（低 Testing One-Shot）
- 缺乏设计规划导致大量 Delegation

**策略 3：模型使用配比优化**

观察 Opus / Sonnet / Haiku 的使用比例。如果 Opus 使用占比超过 60%，考虑将简单任务（如 Exploration、Conversation）配置为使用 Sonnet 或 Haiku，节省成本同时不影响效率。

### 7.2 数据分析工作流

```bash
# 每周一生成上周周报
codeburn report -p 7days > weekly-report-$(date +%Y-%m-%d).txt

# 按项目导出并对比
codeburn export -f json --provider claude | \
  jq '.projects | to_entries | sort_by(.value.totalCostUSD) | reverse | .[:5]'
```

### 7.3 团队共享

CodeBurn 支持将 CSV 导出分享给团队成员：

```bash
codeburn export --provider claude
# 输出: codeburn-export-2026-04-16.csv
```

可以在表格工具中进一步分析，绘制趋势图。

### 7.4 与 CI/CD 集成

在 CI 中运行 AI 编码任务后，采集成本数据：

```bash
# 在 CI job 结束时记录成本
codeburn status --format json > ci-artifacts/codeburn-status.json
```

---

## §8 FAQ

### Q1: CodeBurn 读取我的数据，会上传到服务器吗？

**A**: 不会。CodeBurn 是纯本地工具，所有数据处理都在本机完成。它读取的是本地会话文件（JSONL 或 SQLite），不与任何外部服务器通信。定价数据从 LiteLLM 公开定价页面获取，汇率从欧洲央行 API 获取，均为公开数据。

### Q2: Cursor 的"Auto"模式成本是估算的，误差有多大？

**A**: Cursor Auto 模式使用 Sonnet 4 的定价作为估算基准。由于 Auto 模式实际可能使用 Opus、Sonnet 或 Haiku，误差范围大约在 ±50%。这个估算在缺乏实际数据的情况下已经是最优近似，界面中已明确标注为"Auto (Sonnet est.)"。

### Q3: 首次运行 Cursor 支持很慢，怎么办？

**A**: 这是正常现象。Cursor 的 SQLite 数据库可能非常大（数 GB），首次解析需要时间。CodeBurn 会缓存解析结果到 `~/.cache/codeburn/cursor-results.json`，后续运行几乎瞬间完成。如果想主动重建缓存，删除该文件后重新运行即可。

### Q4: 我同时使用多个 AI 编码工具，数据会重复计算吗？

**A**: 不会。CodeBurn 的去重机制针对每个 Provider 独立运行，不同 Provider 的会话数据不会有交叉重复。但是，如果同一个 AI 编码任务同时被多个工具处理（如同时打开 Cursor 和 Claude Code 做同一件事），成本会分别计算——这符合预期，因为两者确实各自消耗了 Token。

### Q5: CodeBurn 支持企业防火墙后的 AI 编码工具吗？

**A**: CodeBurn 读取的是本地会话文件，不受网络限制。但如果你的 AI 编码工具使用了自定义端点（如公司内部 LLM 服务器），定价可能与 LiteLLM 默认数据不符。可以通过环境变量覆盖或修改 `src/models.ts` 中的硬编码定价来实现自定义。

### Q6: 如何查看某个特定项目的 Token 消耗？

**A**: 在仪表盘界面中，主图表区会显示 per-project 的成本分解。或者使用 `codeburn export -f json` 导出完整数据后用 `jq` 筛选：

```bash
codeburn export -f json | jq '.projects | to_entries[] | select(.key | contains("my-project"))'
```

### Q7: 菜单栏小组件刷新频率可以调整吗？

**A**: 目前刷新频率固定为 5 分钟（300 秒），暂不支持自定义调整。如果需要更频繁的更新，可以考虑修改 `src/menubar.ts` 中的刷新逻辑，但这需要重新生成 SwiftBar 插件。

---

## 📊 总结速查

### 核心要点

1. **CodeBurn 是本地工具**，不收集数据，不上传信息
2. **支持 4 大主流 AI 编码工具**：Claude Code、Codex、Cursor、OpenCode（Pi/Amp 计划中）
3. **13 类任务分类**，帮助你理解 Token 消耗的具体去向
4. **One-Shot 成功率**是衡量 AI 编程效率的核心指标
5. **多货币支持**，通过 Frankfurter API 实时汇率转换

### 快速命令

| 命令 | 用途 |
|------|------|
| `codeburn` | 交互式仪表盘（默认 7 天） |
| `codeburn today` | 今日概览 |
| `codeburn report -p 30days` | 30 天报告 |
| `codeburn status --format json` | JSON 状态（程序化使用） |
| `codeburn export -f json` | 导出 JSON 数据 |
| `codeburn install-menubar` | 安装菜单栏小组件 |
| `codeburn currency JPY` | 切换为日元结算 |

---

**文档信息**

难度：⭐⭐⭐ | 类型：进阶分析 | 更新日期：2026-04-16 | 预计阅读时间：20 分钟
