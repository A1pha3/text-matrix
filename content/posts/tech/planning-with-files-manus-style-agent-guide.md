---
title: "Planning with Files：Manus风格的AI Agent持久化规划工作流"
date: 2026-04-12T18:00:00+08:00
slug: planning-with-files-manus-style-agent-guide
description: "18.6k Stars的AI Agent规划Skill，实现Manus风格的3-文件持久化规划模式。基准测试通过率96.7% vs 6.7%（无Skill），支持16+平台（Claude Code/Cursor/Codex/Gemini CLI/OpenClaw等）。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Claude Code", "规划工作流", "上下文工程", "Manus", "持久化记忆"]
---

# Planning with Files：Manus风格的AI Agent持久化规划工作流

## 📋 学习目标

- 理解Manus为什么值20亿美元——上下文工程的核心奥秘
- 掌握3-文件规划模式的原理与使用方法
- 理解Hooks如何实现"每次决策前重读计划"
- 学会在16+平台上安装和配置Planning with Files
- 理解基准测试背后的验证方法论
- 能够在实际项目中应用持久化规划工作流

---

## 📖 项目概述

### 什么是Planning with Files

**Planning with Files**是一个Claude Code插件，实现了Manus风格的**持久化Markdown规划模式**——这正是Manus在8个月内从上线到1亿美元+收入的秘密。

2025年12月29日，Meta宣布以**20亿美元收购Manus**。这个Skill正是把Manus的核心工作流复现给所有AI Agent用户。

### 核心数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | 18.6k |
| Forks | 1.7k |
| Watchers | 82 |
| 贡献者 | 30人 |
| 最新版本 | v2.33.0 (2026-04-09) |
| 许可协议 | MIT |

### 技术栈

- Python 60.9%
- Shell 20.6%
- PowerShell 18.5%

---

## 🤔 为什么需要这个Skill

### AI Agent的三大痛点

| 痛点 | 表现 | 后果 |
|------|------|------|
| **volatile memory（易失内存）** | TodoWrite工具在context reset后消失 | 进度丢失 |
| **Goal drift（目标漂移）** | 50+次工具调用后忘记原始目标 | 产出偏离 |
| **Hidden errors（隐藏错误）** | 失败不被追踪，重复同样错误 | 效率低下 |
| **Context stuffing（上下文塞填）** | 所有东西都塞进context | 性能下降 |

### Manus的答案

> "Markdown is my 'working memory' on disk. Since I process information iteratively and my active context has limits, Markdown files serve as scratch pads for notes, checkpoints for progress, building blocks for final deliverables." — Manus AI

**核心原则：**
```
Context Window = RAM (易失, 有限)
Filesystem = Disk (持久, 无限)
→ 任何重要信息都写入磁盘
```

---

## 🧱 3-文件模式详解

### 三个文件的作用

```
task_plan.md    → 追踪阶段和进度
findings.md     → 存储研究和发现
progress.md     → 会话日志和测试结果
```

### 文件结构示例

**task_plan.md（任务计划）**
```markdown
# 项目任务计划

## 阶段一：需求分析
- [x] 收集用户需求
- [x] 编写PRD文档
- [ ] 评审并定稿

## 阶段二：系统设计
- [ ] 架构设计
- [ ] 数据库设计
- [ ] API设计

## 错误记录
- 阶段一中发现：原始需求中身份验证模块遗漏
```

**findings.md（研究发现）**
```markdown
# 研究发现

## 用户研究
- 目标用户：独立开发者
- 核心痛点：多平台管理混乱

## 技术调研
- 方案A：原生开发 - 成本高
- 方案B：跨平台框架 - 推荐
```

**progress.md（进度日志）**
```markdown
# 会话进度日志

## 2026-04-12 14:30
- 创建了项目脚手架
- 完成了认证模块
- 遇到问题：第三方API响应超时
- 解决：增加了重试机制

## 2026-04-12 15:45
- 完成了用户管理模块
- 测试覆盖率：78%
```

---

## 🛠️ 安装配置

### 方式一：npx一键安装（推荐）

```bash
npx skills add OthmanAdi/planning-with-files --skill planning-with-files -g
```

### 支持的平台（16+）

| 平台 | 安装方式 |
|------|----------|
| Claude Code | npx / Plugin |
| Cursor | Skill |
| Codex | Skill |
| Gemini CLI | Skill + Hooks |
| OpenClaw | Skill |
| Kiro | Skill |
| Continue.dev | Skill |
| Mastra Code | Skill |
| GitHub Copilot | Hooks |
| Pi Agent | npm package |
| BoxLite | Sandbox |

### Claude Code命令

| 命令 | 自动补全 | 说明 |
|------|----------|------|
| `/planning-with-files:plan` | `/plan` | 启动规划会话 (v2.11.0+) |
| `/planning-with-files:status` | `/plan:status` | 显示规划进度 (v2.15.0+) |
| `/planning-with-files:start` | `/planning` | 原始启动命令 |

### 多语言支持

从v2.33.0开始支持：
- 🇺🇸 English（默认）
- 🇸🇦 Arabic
- 🇩🇪 German
- 🇪🇸 Spanish
- 🇨🇳 Chinese Simplified (v2.25.0+)
- 🇹🇼 Chinese Traditional (v2.28.0+)

---

## 📊 基准测试结果

### 测试方法

使用Anthropic的skill-creator框架（v2.22.0）进行正式评估：
- 10个并行子Agent
- 5种任务类型
- 30个客观可验证的断言
- 3次盲A/B对比

### 测试结果

| 测试指标 | 有Skill | 无Skill | 提升 |
|----------|---------|---------|------|
| **通过率（30个断言）** | **96.7%** (29/30) | 6.7% (2/30) | +90% |
| 3-文件模式遵循率 | 5/5 | 0/5 | 100% |
| 盲A/B胜率 | **3/3** (100%) | 0/3 | 100% |
| 平均评分 | **10.0/10** | 6.8/10 | +47% |

**结论：使用Planning with Files的Agent在复杂任务中的表现显著优于未使用的Agent。**

---

## ⚙️ 核心原理

### Manus五大原则

| 原则 | 实现方式 |
|------|----------|
| **Filesystem as memory** | 信息存储在文件中，不在context中 |
| **Attention manipulation** | 每次决策前重读计划（PreToolUse Hook） |
| **Error persistence** | 错误记录在计划文件中 |
| **Goal tracking** | 复选框显示进度 |
| **Completion verification** | Stop Hook检查所有阶段 |

### Hooks工作流程

```
用户输入
    ↓
PreToolUse Hook
    ↓ 检查是否需要重读计划
    ↓
执行工具
    ↓
PostToolUse Hook
    ↓ 提醒更新状态
    ↓
更新文件
    ↓
Stop Hook
    ↓ 验证完成情况
任务结束
```

---

## 📋 关键规则

| 规则 | 说明 |
|------|------|
| **先建计划** | 没有task_plan.md绝不开始 |
| **2-操作规则** | 每2次view/browser操作后保存发现 |
| **记录所有错误** | 帮助避免重复 |
| **永不重复失败** | 追踪尝试次数，改变方法 |

---

## 🎯 适用场景

### 推荐使用

- ✅ 多步骤任务（3+步骤）
- ✅ 研究任务
- ✅ 构建/创建项目
- ✅ 跨多工具调用的任务

### 不推荐使用

- ❌ 简单问题
- ❌ 单文件编辑
- ❌ 快速查询

---

## 🚀 快速开始

### 步骤1：安装

```bash
npx skills add OthmanAdi/planning-with-files --skill planning-with-files -g
```

### 步骤2：启动规划

```bash
# 在Claude Code中输入
/plan
```

### 步骤3：AI Agent自动完成

1. 如果没有提供描述，AI会询问您的任务
2. 在项目目录创建`task_plan.md`、`findings.md`、`progress.md`
3. 每次重大决策前重读计划（通过PreToolUse Hook）
4. 每次文件写入后提醒更新状态（通过PostToolUse Hook）
5. 将发现存储在`findings.md`而不是塞满context
6. 记录错误供未来参考
7. 停止前验证完成情况（通过Stop Hook）

---

## 📁 项目结构

```
planning-with-files/
├── commands/           # 插件命令
│   ├── plan.md         # /plan 命令
│   └── start.md        # /start 命令
├── skills/             # Skill变体
│   └── planning-with-files/
│       ├── SKILL.md
│       ├── templates/  # 文件模板
│       └── scripts/     # 初始化脚本
├── docs/               # 文档
│   ├── installation.md
│   ├── quickstart.md
│   ├── workflow.md
│   └── troubleshooting.md
├── .claude-plugin/     # Claude Plugin清单
├── .cursor/            # Cursor Skills + Hooks
├── .gemini/            # Gemini CLI Skills + Hooks
└── CHANGELOG.md
```

---

## 🔧 高级配置

### 自定义Hook行为

编辑`.claude/settings.json`：

```json
{
  "hooks": {
    "pre_tool_use": {
      "enabled": true,
      "plan_reread_threshold": 10
    },
    "post_tool_use": {
      "enabled": true,
      "reminder_delay_ms": 500
    }
  }
}
```

### 自定义文件位置

```bash
export PLANNING_FILES_ROOT="./my-planning"
```

---

## 🐛 故障排除

### Skill不激活？

1. 确认安装成功：`npx skills list`
2. 检查平台支持：某些平台需要特定版本
3. 查看文档：`docs/troubleshooting.md`

### Hook不触发？

1. 确认Hook配置正确
2. 检查权限设置
3. 尝试重新安装

---

## 🌍 社区生态

### Fork开发的衍生项目

| Fork | 作者 | 特色功能 |
|------|------|----------|
| devis | @st01cs | 面试优先工作流 |
| multi-manus-planning | @kmichels | 多项目支持 |
| plan-cascade | @Taoidle | 多级任务编排 |
| agentfund-skill | @RioTheGreat-ai | 区块链众筹 |

---

## 📚 资源链接

| 资源 | 链接 |
|------|------|
| GitHub仓库 | https://github.com/OthmanAdi/planning-with-files |
| 官方文档 | https://github.com/OthmanAdi/planning-with-files/tree/master/docs |
| 基准测试报告 | https://github.com/OthmanAdi/planning-with-files/blob/master/docs/evals.md |
| Skills Playground | https://skillsplayground.com/skills/othmanadi-planning-with-files-planning-with-files |
| Loaditout安全评级 | https://loaditout.ai/skills/OthmanAdi/planning-with-files |

---

## ✅ 总结

Planning with Files将Manus的20亿美元秘密带入每一个AI Agent：

1. **持久化优于易失**：Filesystem作为持久化记忆
2. **规划驱动决策**：每次重大决策前重读计划
3. **错误即知识**：记录失败避免重复
4. **进度可视化**：复选框追踪完成情况
5. **验证保证质量**：Stop Hook确保所有阶段完成

这是一个经过A/B验证的提升47%任务完成率的实战方法论。

🦞
