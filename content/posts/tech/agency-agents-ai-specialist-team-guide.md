---
title: "The Agency：147个专业化AI Agent组成的虚拟团队"
date: "2026-05-05T11:25:00+08:00"
slug: "agency-agents-ai-specialist-team-guide"
description: "The Agency是一个包含147个专业化AI Agent的开源项目，覆盖工程、设计、销售、营销等12个领域。每个Agent拥有独特人格、专业流程和可衡量产出，可接入Claude Code、Cursor、Windsurf等主流AI编程工具。本文详解其架构设计、Agent分类、集成方式与实际应用场景。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Claude Code", "Cursor", "多工具集成", "AI团队", "OpenClaw"]
---

## 项目概览

[The Agency](https://github.com/msitarzewski/agency-agents) 源于一个Reddit帖子，经数月迭代发展为一个包含**147个专业化AI Agent**的开源项目。每个Agent不是泛泛的提示词模板，而是拥有独特人格、沟通风格、专业流程和可衡量产出的专家级角色。

**核心数据：**
- GitHub Stars：1,189
- Agent总数：147个
- 覆盖领域：12个（工程、设计、销售、营销、产品、项目管理、测试、支持、空间计算、专业化、财务、游戏开发、学术）
- 支持工具：Claude Code、GitHub Copilot、Antigravity、OpenClaw、Cursor、Aider、Windsurf等11种主流AI工具
- 开源协议：MIT

**为什么值得写：**
- 覆盖了AI Agent从"能用"到"专业"的完整实践
- 支持多工具生态，可直接对接现有工作流
- Agent分工细致，从前端开发到法律咨询都有对应专家

本文面向想要用AI Agent提升研发、设计、营销等团队效能的开发者、产品经理和技术负责人。

---

## 核心设计理念

### 从通用提示词到专业Agent的范式转变

传统AI Agent方案本质上是"万能型"——一个提示词模板应对各种场景。The Agency的思路完全不同：**每个Agent都是某个细分领域的深度专家**，拥有：

| 要素 | 说明 |
|------|------|
| **人格（Personality）** | 独特的沟通风格和思维方式，不千篇一律 |
| **核心使命（Mission）** | 明确的职责边界和成功标准 |
| **工作流程（Workflow）** | 经过生产环境验证的执行步骤 |
| **交付物（Deliverables）** | 可量化的具体产出，不是模糊建议 |
| **学习记忆（Memory）** | 持续改进的能力积累 |

### 12个专业部门一览

The Agency的组织架构模拟了真实公司结构：

| 部门 | Agent数量 | 代表角色 |
|------|-----------|---------|
| 💻 工程部 | 25+ | 前端开发者、后端架构师、AI工程师、安全工程师 |
| 🎨 设计部 | 8 | UI设计师、UX研究员、品牌守护者 |
| 💼 销售部 | 10 | 外展策略师、交易策略师、销售工程师 |
| 📢 市场部 | 30+ | 增长黑客、内容创作者、Twitter运营、知乎专家 |
| 📊 产品部 | 5 | Sprint优先排序器、趋势研究员、行为推动引擎 |
| 🎬 项目管理 | 7 | 制片人、项目牧羊人、实验追踪员 |
| 🧪 测试部 | 9 | 证据收集员、性能基准测试员、API测试员 |
| 🛟 支持部 | 7 | 支持响应员、分析报告员、财务追踪员 |
| 🥽 空间计算 | 6 | XR界面架构师、visionOS工程师 |
| 🎯 专业部 | 40+ | MCP构建器、智能合同审计员、Salesforce架构师 |
| 💵 财务部 | 5 | 簿记员、财务分析师、税务策略师 |
| 🎮 游戏开发 | 20+ | Unity/Unreal/Godot专项工程师 |

---

## 快速开始

### 方式一：接入Claude Code（推荐）

```bash
# 克隆仓库
git clone https://github.com/msitarzewski/agency-agents.git
cd agency-agents

# 安装所有Agent到Claude Code目录
./scripts/install.sh --tool claude-code

# 在Claude Code中激活
# "Hey Claude, activate Frontend Developer mode and help me build a React component"
```

### 方式二：接OpenClaw

```bash
# 先生成OpenClaw格式文件
./scripts/convert.sh --tool openclaw

# 安装
./scripts/install.sh --tool openclaw

# 重启OpenClaw网关
openclaw gateway restart
```

Agent会以独立workspace形式出现在`~/.openclaw/agency-agents/`下，每个Agent拥有自己的`SOUL.md`、`AGENTS.md`和`IDENTITY.md`。

### 方式三：接入Cursor

```bash
cd your-project
/path/to/agency-agents/scripts/install.sh --tool cursor
```

Agent转化为`.mdc`规则文件存于`.cursor/rules/`目录。

---

## 工程部Agent详解

工程部是整个仓库最核心的部分，包含25+个专业化工程师角色：

### 核心技术Agent

**Frontend Developer** — 专精React/Vue/Angular、UI实现、Web Vitals优化
```
使用场景：现代Web应用开发、像素级精确UI实现、Core Web Vitals优化
```

**Backend Architect** — API设计、数据库架构、可扩展性规划
```
使用场景：服务端系统设计、微服务架构、云基础设施规划
```

**AI Engineer** — ML模型部署、流水线构建、AI集成
```
使用场景：机器学习功能开发、数据管道、LLM应用集成
```

**Security Engineer** — 威胁建模、安全代码审计、安全架构
```
使用场景：应用安全评估、漏洞分析、安全CI/CD设计
```

**Autonomous Optimization Architect** — LLM路由、成本优化、影子测试
```
使用场景：需要智能API选择和成本护栏的自主系统
```

### 特殊领域Agent

| Agent | 专长 | 使用场景 |
|-------|------|---------|
| Embedded Firmware Engineer | ESP32/STM32 bare-metal | 嵌入式系统、物联网设备 |
| Solidity Smart Contract Engineer | EVM合约、gas优化 | DeFi协议、安全智能合约 |
| Codebase Onboarding Engineer | 源码阅读、代码路径追踪 | 新人快速熟悉陌生代码库 |
| Feishu Integration Developer | 飞书开放平台、机器人 | 飞书生态集成开发 |
| Email Intelligence Engineer | 邮件解析、MIME提取 | 将邮件线程转化为结构化上下文 |

---

## 多工具集成架构

The Agency的集成脚本支持11种工具，通过`convert.sh`和`install.sh`两个脚本统一管理：

```bash
# Step 1: 生成各工具对应的格式文件
./scripts/convert.sh              # 串行生成
./scripts/convert.sh --parallel  # 并行生成（更快）

# Step 2: 安装（交互式，auto-detect已安装的工具）
./scripts/install.sh
```

安装脚本会扫描系统，自动检测已安装的工具，以复选框UI呈现。

---

## 应用场景示例

### 场景一：构建创业公司MVP

**团队配置：**
1. 🎨 Frontend Developer — 构建React应用
2. 🏗️ Backend Architect — 设计API和数据库
3. 🚀 Growth Hacker — 规划用户增长策略
4. ⚡ Rapid Prototyper — 快速迭代
5. 🔍 Reality Checker — 上线前质量验证

**输出：** 每个环节都有专业化Agent保障质量和效率。

### 场景二：多渠道营销活动

**团队配置：**
1. 📝 Content Creator — 活动内容策划
2. 🐦 Twitter Engager — Twitter策略与执行
3. 🤝 Reddit Community Builder — Reddit社区运营
4. 📊 Analytics Reporter — 效果追踪优化

---

## 适用场景与边界

### 适合的场景
- 需要在不同专业领域快速获得专家级AI辅助
- 已使用Claude Code/Cursor/Windsurf等AI编程工具，希望扩展Agent能力
- 需要组建临时AI团队完成特定项目
- 希望AI输出更专业化、减少泛泛建议

### 边界与局限
- Agent本身是Markdown文件定义的人格+工作流，不含实际执行代码
- 输出质量依赖底层AI模型能力（需自备API Key）
- 部分细分Agent（如法律、医疗）仅作参考，不能替代专业咨询
- 147个Agent全部安装需要较大的token消耗

---

## 总结

The Agency将AI Agent从"一个通用助手"细分为"147个专业专家"，覆盖了现代企业几乎所有职能领域。通过统一的安装脚本和标准化的Agent格式，实现了跨工具（Claude Code、OpenClaw、Cursor等）的无缝接入。

**核心价值：**
- 开箱即用的专业化AI团队
- 多工具生态支持，一套Agent定义多平台使用
- 每个Agent都是生产验证过的实战流程

如果你已经在使用AI编程工具，The Agency是扩展能力的最佳选择；如果你还在用通用提示词，The Agency展示了专业化Agent的真正价值。

**参考链接：**
- GitHub：https://github.com/msitarzewski/agency-agents
- 官方文档：https://github.com/msitarzewski/agency-agents#readme