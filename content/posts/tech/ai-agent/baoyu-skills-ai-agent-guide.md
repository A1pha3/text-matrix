---
title: "baoyu-skills：AI Coding Agent 深度研究市场分析技能套件完全指南"
slug: "baoyu-skills-ai-agent-guide"
aliases:
  - /posts/tech/baoyu-skills-ai-agent-guide/
date: "2026-03-31T15:45:00+08:00"
categories: ["技术笔记"]
tags: ["baoyu-skills", "AI Agent", "Claude Code", "OpenCode", "深度研究", "市场分析", "金融数据"]
description: "全面解析 baoyu-skills (1.8k Stars)：AI Coding Agent 技能套件，包含深度研究、金融数据、市场分析、LinkedIn/X优化等7大技能。"
---

# baoyu-skills：AI Coding Agent 深度研究市场分析技能套件完全指南

> 预计阅读时间：20分钟 | 难度：⭐⭐⭐

---

## 学习目标

完成本文档后，你将能够：

- ✅ 理解 baoyu-skills 的核心定位与设计理念
- ✅ 掌握 baoyu-skills 的七个核心技能
- ✅ 熟练安装和配置 baoyu-skills
- ✅ 使用 /baoyu-research 进行深度研究
- ✅ 使用 /baoyu-financial 获取实时股票数据
- ✅ 使用 /baoyu-market-analyze 分析市场动态
- ✅ 使用 /baoyu-linkedin 优化 LinkedIn 内容
- ✅ 使用 /baoyu-stocks 和 /baoyu-ticker 获取股票报价
- ✅ 使用 /baoyu-x 分析 Twitter/X 趋势

---

## §2 项目概述

### 2.1 什么是 baoyu-skills？

**baoyu-skills**（官方仓库：[JimLiu/baoyu-skills](https://github.com/JimLiu/baoyu-skills)）是一套**高级 AI Coding Agent 技能套件**，为 Coding Agent 添加深度研究、市场分析、财务数据等功能。

**名称由来**：

> baoyu = 鲍鱼 (abalone)，一种珍贵的海鲜美食。这些技能是 Coding Agent 的高端附加组件。

**设计理念**：

> Like calling a domain expert into the room.

翻译：就像请一位领域专家进入房间。每个技能就像一位专业领域的专家，处理内部的复杂性，让用户只需简单调用。

### 2.2 价值定位

| 价值 | 说明 |
|------|------|
| **深度研究** | 全面研究话题、趋势和技术 |
| **实时数据** | 股票数据、财务指标、SEC 文件 |
| **市场分析** | 使用结构化框架分析市场动态 |
| **社交媒体优化** | LinkedIn/X 内容优化和分析 |
| **开箱即用** | 简单命令，无需复杂配置 |

### 2.3 核心数据

```
Stars:     1,800 (1.8k)
Forks:     157
Watchers:  11
贡献者:    6 人
提交数:   117 次
分支数:    4 个
标签数:    11 个
发布版本:  11 个
最新版本:  v0.9.2 (2026-03-29)
许可证:    MIT
```

### 2.4 技能一览

| 技能 | 功能 | 用途 |
|------|------|------|
| `/baoyu-research` | 深度研究 Agent | 研究话题、趋势、技术 |
| `/baoyu-financial` | 金融数据 | 实时股票、财务指标、SEC 文件 |
| `/baoyu-market-analyze` | 市场分析 | 分析市场动态和竞争定位 |
| `/baoyu-linkedin` | LinkedIn 优化 | 优化 LinkedIn 帖子以获得最大参与度 |
| `/baoyu-stocks` | 股票报价 | 股票报价和财务分析工具 |
| `/baoyu-ticker` | 实时报价 | 主要交易所实时股票报价 |
| `/baoyu-x` | X/Twitter 分析 | 分析 X 趋势、粉丝指标、内容表现 |

---

## §3 核心技能详解

### 3.1 /baoyu-research — 深度研究 Agent

**功能说明**

执行关于话题、趋势和技术的全面研究，使用网络搜索。

**使用场景**

```bash
/baoyu-research
# 输入：研究 AI Agent 领域的最新趋势
# 输出：全面的研究报告，包含趋势分析、技术对比、市场洞察
```

**工作流程**

```
输入研究主题
    ↓
网络搜索和信息收集
    ↓
分析和综合信息
    ↓
生成结构化研究报告
    ↓
包含：趋势分析、技术对比、市场洞察
```

### 3.2 /baoyu-financial — 金融数据

**功能说明**

获取实时股票数据、财务指标、SEC 文件、分析师评级，以及 10+ 年的历史定价数据。

**数据来源**

| 数据类型 | 说明 |
|----------|------|
| **实时报价** | 主要交易所实时股票价格 |
| **财务指标** | P/E、EPS、ROI 等核心指标 |
| **SEC 文件** | 年报、季报、重要事件 |
| **分析师评级** | 买入/持有/卖出评级 |
| **历史数据** | 10+ 年历史定价 |

**使用场景**

```bash
/baoyu-financial AAPL
# 输出：苹果公司的实时报价、财务指标、SEC 文件摘要、分析师评级
```

### 3.3 /baoyu-market-analyze — 市场分析

**功能说明**

使用结构化框架分析市场动态和竞争定位。

**分析框架**

| 框架 | 说明 |
|------|------|
| **SWOT** | 优势、劣势、机会、威胁 |
| **Porter's Five Forces** | 行业竞争力量 |
| **PESTEL** | 政治、经济、社会、技术、环境、法律 |
| **竞争分析** | 市场份额、竞争定位 |

**使用场景**

```bash
/baoyu-market-analyze Tesla
# 输出：特斯拉的市场分析报告，包含竞争格局、行业趋势、SWOT 分析
```

### 3.4 /baoyu-linkedin — LinkedIn 优化

**功能说明**

优化 LinkedIn 帖子以获得最大参与度，支持 A/B 测试不同版本。

**功能特点**

- 内容分析和优化建议
- A/B 版本测试
- 发布时机优化
- 参与度预测

**使用场景**

```bash
/baoyu-linkedin
# 输入：分享一篇关于 AI 的技术文章
# 输出：优化后的 LinkedIn 帖子，包含标题、摘要、标签建议
```

### 3.5 /baoyu-stocks — 股票分析

**功能说明**

提供股票报价和财务分析工具。

**分析工具**

| 工具 | 说明 |
|------|------|
| **报价** | 实时股票价格 |
| **图表** | 价格走势图表 |
| **财务数据** | 收入、利润、增长率 |
| **比较** | 与竞争对手或行业平均对比 |

**使用场景**

```bash
/baoyu-stocks NVDA
# 输出：英伟达的股票报价、财务分析、与 AMD/Intel 对比
```

### 3.6 /baoyu-ticker — 实时报价

**功能说明**

获取主要交易所的实时股票报价和财务指标。

**支持交易所**

| 交易所 | 说明 |
|--------|------|
| **NYSE** | 纽约证券交易所 |
| **NASDAQ** | 纳斯达克 |
| **LSE** | 伦敦证券交易所 |
| **HKEX** | 香港证券交易所 |
| **SSE** | 上海证券交易所 |

**使用场景**

```bash
/baoyu-ticker TSLA
# 输出：特斯拉的实时报价、成交量、价格变动
```

### 3.7 /baoyu-x — X/Twitter 分析

**功能说明**

分析 X（Twitter）趋势、粉丝指标和内容表现。

**分析维度**

| 维度 | 说明 |
|------|------|
| **趋势分析** | 当前热门话题和标签 |
| **粉丝指标** | 粉丝增长、参与率、受众画像 |
| **内容表现** | 帖子的曝光、点赞、转发、评论 |

**使用场景**

```bash
/baoyu-x @elonmusk
# 输出：马斯克 X 账号的分析报告，包含粉丝增长、热门帖子、互动分析
```

---

## §4 安装与配置

### 4.1 前置要求

| 要求 | 说明 |
|------|------|
| **Node.js** | v18+ |
| **包管理器** | npm/pnpm/bun |
| **Coding Agent** | Claude Code/OpenCode/Pi 等 |

### 4.2 安装步骤

**方法一：使用 skills 命令**

```bash
# 使用 npm 安装
npx skills add JimLiu/baoyu-skills

# 使用 pnpm 安装
pnpm dlx skills add JimLiu/baoyu-skills
```

**方法二：手动安装**

```bash
# 克隆仓库
git clone https://github.com/JimLiu/baoyu-skills.git

# 进入目录
cd baoyu-skills

# 安装依赖
npm install
```

### 4.3 配置

将技能复制到你的 Coding Agent 的 skills 目录：

```bash
# 复制技能到 Claude Code
cp -r baoyu-skills ~/.claude/skills/

# 或复制到 OpenCode
cp -r baoyu-skills ~/.opencode/skills/
```

### 4.4 验证安装

```bash
# 查看已安装的技能
skills list

# 验证 baoyu-skills
skills info baoyu-skills
```

---

## §5 使用示例

### 5.1 深度研究示例

**研究 AI Agent 趋势**

```bash
/baoyu-research AI Agent frameworks 2026
```

**输出示例**

```
# AI Agent 框架趋势研究报告

## 主要趋势
1. 多智能体系统兴起
2. 工具调用标准化
3. 持久化上下文成为标配

## 框架对比
| 框架 | 优势 | 劣势 |
|------|------|------|
| LangChain | 生态丰富 | 学习曲线陡 |
| LlamaIndex | 专注 RAG | 工具调用弱 |
| AutoGPT | 自动化强 | 稳定性差 |

## 市场洞察
...
```

### 5.2 金融分析示例

**分析苹果公司**

```bash
/baoyu-financial AAPL
```

**输出示例**

```
# 苹果公司 (AAPL) 财务分析

## 实时报价
- 价格：$178.52
- 涨跌幅：+1.23%
- 成交量：52.3M

## 财务指标
- P/E：28.5
- EPS：$6.26
- ROI：28.3%

## SEC 文件
- 10-K：已提交
- 10-Q：已提交

## 分析师评级
- 买入：32
- 持有：8
- 卖出：1
```

### 5.3 市场分析示例

**分析电动汽车市场**

```bash
/baoyu-market-analyze EV market 2026
```

**输出示例**

```
# 电动汽车市场分析报告

## SWOT 分析
### 优势
- 技术创新领先
- 品牌认知度高
- 充电网络完善

### 劣势
- 价格竞争激烈
- 原材料成本上升

### 机会
- 全球减排政策
- 新兴市场扩张

### 威胁
- 新竞争者涌入
- 技术迭代加速

## Porter's Five Forces
- 行业内竞争：高
- 新进入者威胁：中
- 替代品威胁：低
...
```

---

## §6 项目结构

### 6.1 目录结构

| 目录 | 说明 |
|------|------|
| `skills/` | 技能定义（Markdown 文件）|
| `shared/` | 共享资源和工具 |
| `.claude/` | Claude 配置 |
| `.openclaude/` | OpenClaw 配置 |
| `.opencode/` | OpenCode 配置 |
| `node_modules/` | 依赖包 |
| `skills/` | 技能目录 |

### 6.2 配置文件

| 文件 | 说明 |
|------|------|
| `package.json` | Node.js 包配置 |
| `tsconfig.json` | TypeScript 配置 |
| `eslint.config.mjs` | ESLint 配置 |
| `SKILL.md` | 技能定义文件 |
| `README.md` | 项目说明 |

---

## §7 设计理念

### 7.1 设计出发点

baoyu-skills 的设计出发点**"像请一位领域专家进入房间"**：

| 传统方式 | baoyu-skills 方式 |
|----------|-------------------|
| 手动搜索信息 | 一句话需求，自动研究 |
| 分散的数据源 | 统一的数据获取 |
| 缺乏专业分析 | 结构化框架分析 |
| 重复性工作 | 可复用的技能 |

### 7.2 技能作为专家

每个 baoyu 技能就像一位专业领域的专家：

| 技能 | 专家角色 |
|------|----------|
| `/baoyu-research` | 研究分析师 |
| `/baoyu-financial` | 金融分析师 |
| `/baoyu-market-analyze` | 市场策略师 |
| `/baoyu-linkedin` | 社交媒体营销专家 |
| `/baoyu-stocks` | 股票分析师 |
| `/baoyu-ticker` | 实时数据专家 |
| `/baoyu-x` | 社交媒体分析师 |

### 7.3 与 Coding Agent 的集成

baoyu-skills 无缝集成到你的 Coding Agent 工作流中：

```
你：通过 /baoyu-research 研究新市场
    ↓
baoyu-skills：执行深度研究
    ↓
返回：结构化报告
    ↓
你：根据报告做出决策
```

---

## §8 常见问题

### Q1：baoyu-skills 和普通搜索有什么区别？

| 特性 | baoyu-skills | 普通搜索 |
|------|--------------|----------|
| **深度** | 综合分析，结构化报告 | 零散信息 |
| **专业性** | 领域专家级分析 | 需人工筛选 |
| **格式** | 预格式化，可直接使用 | 原始网页，需整理 |
| **集成** | 与 Coding Agent 无缝 | 需手动复制粘贴 |

### Q2：支持哪些 Coding Agent？

| Agent | 支持情况 |
|-------|----------|
| **Claude Code** | ✅ 完整支持 |
| **OpenCode** | ✅ 完整支持 |
| **Pi** | ✅ 完整支持 |
| **Codex** | ✅ 支持 |
| **Cursor** | ✅ 支持 |

### Q3：数据是实时的吗？

| 数据类型 | 实时性 |
|----------|--------|
| **股票报价** | 实时或延迟（取决于数据源）|
| **SEC 文件** | 提交后更新 |
| **分析师评级** | 定期更新 |
| **社交媒体** | 实时或近实时 |

### Q4：可以自定义技能吗？

**支持**。你可以通过修改 `skills/` 目录下的 Markdown 文件来自定义技能行为。

### Q5：免费使用吗？

**免费**。baoyu-skills 是开源项目，采用 MIT 许可证。

### Q6：如何贡献代码？

1. Fork 仓库
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

---

## §9 总结

### 9.1 核心优势

| 优势 | 说明 |
|------|------|
| **一键深度研究** | 替代繁琐的手动搜索和信息整理 |
| **实时金融数据** | 股票报价、财务指标、SEC 文件 |
| **专业市场分析** | 使用结构化框架 |
| **多平台支持** | LinkedIn、X/Twitter |
| **无缝集成** | 与 Coding Agent 工作流融合 |
| **开源免费** | MIT 许可证 |

### 9.2 适用场景

| 场景 | 推荐指数 |
|------|----------|
| 市场调研 | ⭐⭐⭐⭐⭐ |
| 投资分析 | ⭐⭐⭐⭐⭐ |
| 竞品分析 | ⭐⭐⭐⭐⭐ |
| 社交媒体运营 | ⭐⭐⭐⭐ |
| 技术研究 | ⭐⭐⭐⭐⭐ |

### 9.3 项目信息

- Stars：1.8k
- Forks：157
- 贡献者：6 人
- 最新版本：v0.9.2 (2026-03-29)
- 许可证：MIT

### 9.4 相关资源

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/JimLiu/baoyu-skills |
| 技能市场 | Claude Code Plugin Marketplace |

---

*文档版本 1.0 | 撰写日期：2026-03-31 | 基于 v0.9.2 (2026-03-29) | Stars: 1.8k ⭐*