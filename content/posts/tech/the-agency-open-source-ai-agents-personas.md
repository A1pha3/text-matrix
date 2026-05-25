---
title: "The Agency：100K Stars的开源AI Agent人格库，让AI拥有专业角色"
date: "2026-05-19T20:25:00+08:00"
slug: "the-agency-open-source-ai-agents-personas"
description: "The Agency是一个开源AI Agent人格集合，包含60+专业角色（前端工程师、后端架构师、安全工程师等），每个Agent拥有独立人格、专长和工作流程，可集成到Claude Code等多种AI工具中。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Claude Code", "开源", "AI开发助手", "多工具集成"]
---

## 先给判断

The Agency解决的不是一个技术问题，而是一个体验问题：通用AI很强，但当你需要专业深度时，"什么都会一点"的通用助手不如"专精一项"的专业角色。这个项目为AI编码工具提供了60+专业人格，让AI在特定领域更像专家。

100K Stars说明很多人有同感。它的核心价值是**把AI从通用助手变成专业搭档**——不是替代通用AI，而是给它加上专业身份。

<!--more-->

## 系统地图

```
┌─────────────────────────────────────────────────────────────────┐
│                       The Agency                                │
│                    Agent人格库                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   💻 工程部          🎨 设计部          💰 付费媒体部            │
│   ├─ 前端工程师      ├─ UI设计师        ├─ PPC策略师            │
│   ├─ 后端架构师     ├─ UX研究员        ├─ 搜索分析师           │
│   ├─ AI工程师       ├─ 品牌守护者       ├─ 媒体审计师          │
│   ├─ DevOps自动化   ├─ 视觉叙事师      └─ ...                 │
│   └─ ...            └─ ...                                   │
│                                                                  │
│   💼 销售部          🔧 数据/基础设施部                        │
│   ├─ 外呼策略师     ├─ 数据库优化师                            │
│   ├─ 发现教练       ├─ SRE                                    │
│   ├─ 交易策略师     └─ ...                                    │
│   └─ ...                                                      │
└─────────────────────────────────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                              ▼
     Claude Code              其他AI工具 (Copilot, Cursor, etc.)
```

## 核心能力

### 1. 专业人格定义

每个Agent包含：

- **身份与人格**：独特的沟通风格和专业视角
- **核心使命**：明确的工作范围和优先事项
- **工作流程**：经过验证的执行步骤
- **交付物示例**：真实代码和可测量成果
- **成功指标**：如何评估工作质量

### 2. 多工具集成

支持以下AI工具的一键安装：

- Claude Code（推荐）
- GitHub Copilot
- Antigravity
- Gemini CLI
- OpenCode
- OpenClaw
- Cursor
- Aider
- Windsurf
- Kimi Code

```bash
# 安装所有Agent到Claude Code
./scripts/install.sh --tool claude-code

# 安装到特定工具
./scripts/install.sh --tool openclaw
./scripts/install.sh --tool cursor
```

### 3. 转换工具

如果你的工具不在默认支持列表，可以用转换脚本生成兼容格式：

```bash
# 生成所有工具的集成文件
./scripts/convert.sh

# 安装（自动检测已安装工具）
./scripts/install.sh
```

## 工程部Agent一览（部分）

| Agent | 专长 | 使用场景 |
|-------|------|----------|
| 前端开发者 | React/Vue/Angular, UI实现 | 现代Web应用、像素级UI |
| 后端架构师 | API设计、数据库架构 | 服务端系统、微服务 |
| AI工程师 | ML模型部署、AI集成 | 机器学习特性、数据管道 |
| DevOps自动化 | CI/CD、基础设施自动化 | 部署流水线、监控 |
| 安全工程师 | 威胁建模、安全代码审查 | 应用安全、漏洞评估 |
| 数据库优化师 | Schema设计、查询优化 | PostgreSQL/MySQL调优 |
| SRE | SLO、错误预算、可观测性 | 生产可靠性、容量规划 |
| 嵌入式固件工程师 | 裸金属、RTOS、ESP32 | 嵌入式系统、IoT |

## 快速开始

### 方式1：与Claude Code一起使用（推荐）

```bash
# 克隆仓库
git clone https://github.com/msitarzewski/agency-agents.git
cd agency-agents

# 安装所有Agent
./scripts/install.sh --tool claude-code

# 在Claude Code中激活
# "激活前端开发者模式，帮我构建React组件"
```

### 方式2：作为参考使用

浏览`engineering/`、`design/`、`paid-media/`等目录，复制需要的人格定义到你的项目中。每个文件都是独立的，可以单独使用。

### 方式3：与其他工具集成

```bash
# 转换为你的工具格式
./scripts/convert.sh

# 查看生成的文件
ls output/
```

## 适用边界

**该用：**
- 需要AI在特定领域提供深度专业支持
- 想让AI coding assistant拥有更具体的专业角色
- 团队需要标准化AI工作流程和交付质量

**不该用：**
- 只需要通用AI回答问题——通用AI更合适
- 没有明确的领域需求——人格库可能过度
- 对AI角色有特定心理预期——实际效果可能不符合想象

## 结论

The Agency是一个有明确价值主张的开源项目：它不试图替代通用AI，而是给它加上专业身份。对于需要AI在特定领域提供深度支持的开发者，这是一个实用的资源库。

100K Stars说明社区对这类工具有真实需求。如果你使用Claude Code或其他AI coding工具，试试安装几个专业Agent——有时候，一个有明确人格的AI比一个万能AI更有用。

---

**仓库信息**：https://github.com/msitarzewski/agency-agents | Stars: 100,697 | License: MIT | 语言: Shell