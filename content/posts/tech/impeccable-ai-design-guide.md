---
title: "Impeccable：AI 前端设计技能套件完全指南"
date: 2026-03-31T15:55:00+08:00
slug: "impeccable-ai-design-guide"
description: "全面解析 Impeccable (15k Stars)：1个技能+20个命令+反模式库，帮助AI写出专业前端代码。基于Anthropic frontend-design技能，支持Cursor/Claude Code/OpenCode等9个工具。"
draft: false
categories: ["技术笔记"]
tags: ["Impeccable", "AI设计", "Claude Code", "Cursor", "OpenCode", "前端设计", "UI设计", "设计系统"]
---

# Impeccable：AI 前端设计技能套件完全指南

## §1 学习目标

完成本文档后，你将能够：

- ✅ 理解 Impeccable 的核心定位与设计理念
- ✅ 掌握 Impeccable 的 20 个命令
- ✅ 熟练使用 7 个专业参考文件（typography/color/spatial/motion/interaction/responsive/ux-writing）
- ✅ 熟练安装 Impeccable 到各种 AI 编码工具
- ✅ 使用 /audit 进行技术质量检查
- ✅ 使用 /critique 进行 UX 设计审查
- ✅ 使用 /normalize 对齐设计系统标准
- ✅ 使用 /polish 进行发布前最终检查
- ✅ 组合使用多个命令构建完整工作流
- ✅ 为 Impeccable 贡献代码

---

## §2 项目概述

### 2.1 什么是 Impeccable？

**Impeccable**（官方仓库：[pbakaus/impeccable](https://github.com/pbakaus/impeccable)）是一套**前端设计技能和命令套件**，帮助 AI 在编写代码时做出更好的 UI 设计决策。

**官方描述**：

> The vocabulary you didn't know you needed. 1 skill, 20 commands, and curated anti-patterns for impeccable frontend design.

**翻译**：你不知道你需要的词汇。1 个技能，20 个命令，以及精心策划的反模式，让前端设计变得无可挑剔。

**快速开始**：访问 [impeccable.style](https://impeccable.style) 下载可直接使用的安装包。

### 2.2 为什么需要 Impeccable？

**问题**：每个 LLM 都从相同的通用模板学习。没有指导时，你会得到相同可预测的错误：

- Inter 字体
- 紫色渐变
- 卡片嵌套卡片
- 彩色背景上的灰色文字

**Impeccable 的解决方案**：

| 组件 | 说明 |
|------|------|
| **扩展技能** | 7 个领域专业参考文件 |
| **20 个引导命令** | 审核、审查、完善、提炼、动画等 |
| **反模式库** | 明确告诉 AI 什么不应该做 |

### 2.3 核心数据

```
Stars:     15,000 (15k)
Forks:     641
Watchers:  25
贡献者:    17 人
提交数:   240 次
最新提交:  db1add7 (2026-03-31)
许可证:    Apache 2.0
语言:     JavaScript 45.4%, CSS 33.1%, HTML 21.5%
```

### 2.4 核心价值主张

| 价值 | 说明 |
|------|------|
| **专业设计参考** | 7 个领域专项（字体/颜色/空间/动效/交互/响应式/文案）|
| **20 个实用命令** | 覆盖设计全流程 |
| **反模式库** | 避免常见设计错误 |
| **多工具支持** | Cursor/Claude Code/OpenCode/Pi/Gemini/Codex/VS Code/Kiro/Trae |
| **开源免费** | Apache 2.0 许可证 |

---

## §3 核心技能详解

### 3.1 前端设计技能（frontend-design）

Impeccable 的核心是一个扩展的设计技能，包含 **7 个专业参考文件**：

| 参考文件 | 覆盖内容 |
|----------|----------|
| **typography** | 字体系统、字体搭配、模块化比例、OpenType |
| **color-and-contrast** | OKLCH、色调中性色、暗色模式、无障碍 |
| **spatial-design** | 间距系统、网格、视觉层次 |
| **motion-design** | 缓动曲线、错开动画、减少动画 |
| **interaction-design** | 表单、焦点状态、加载模式 |
| **responsive-design** | 移动优先、流体设计、容器查询 |
| **ux-writing** | 按钮标签、错误消息、空状态 |

### 3.2 字体系统（typography）

**核心原则**

- 使用高质量字体（避免 Arial、Inter、系统默认字体）
- 字体搭配要有意义
- 模块化比例（1.25/1.333/1.5 等）
- 利用 OpenType 特性（连字、数字样式等）

### 3.3 颜色与对比（color-and-contrast）

**核心原则**

- 使用 OKLCH 色彩空间
- 总是添加色调（避免纯黑/纯灰）
- 暗色模式优先
- 确保对比度满足 WCAG 标准

### 3.4 空间设计（spatial-design）

**核心原则**

- 一致的间距系统（4px/8px/16px 等）
- 网格布局
- 清晰的视觉层次

### 3.5 动效设计（motion-design）

**核心原则**

- 使用自然的缓动曲线（避免 bounce/elastic）
- 错开动画要有意义
- 尊重用户的减少动画偏好

### 3.6 交互设计（interaction-design）

**核心原则**

- 表单要有清晰的标签和反馈
- 焦点状态要明显
- 加载状态要告知用户

### 3.7 响应式设计（responsive-design）

**核心原则**

- 移动优先
- 流体设计
- 使用容器查询（Container Queries）

### 3.8 UX 文案（ux-writing）

**核心原则**

- 按钮标签要清晰（避免模糊的"提交"）
- 错误消息要帮助用户解决问题
- 空状态要引导用户采取行动

---

## §4 二十个命令详解

### 4.1 命令一览表

| 命令 | 功能 | 用途 |
|------|------|------|
| `/teach-impeccable` | 一次性设置 | 收集设计上下文，保存到配置 |
| `/audit` | 技术质量检查 | 无障碍、性能、响应式检查 |
| `/critique` | UX 设计审查 | 层次、清晰度、情感共鸣 |
| `/normalize` | 对齐设计系统 | 修复不一致 |
| `/polish` | 最终完善 | 发布前的最后检查 |
| `/distill` | 提炼 | 剥离复杂性 |
| `/clarify` | 澄清 | 改进不清晰的 UX 文案 |
| `/optimize` | 优化 | 性能改进 |
| `/harden` | 强化 | 错误处理、i18n、边缘情况 |
| `/animate` | 添加动画 | 有目的的动效 |
| `/colorize` | 添加颜色 | 战略性引入颜色 |
| `/bolder` | 增强 | 放大无聊的设计 |
| `/quieter` | 减弱 | 淡化过于大胆的设计 |
| `/delight` | 添加乐趣 | 添加惊喜时刻 |
| `/extract` | 提取 | 拉取为可复用组件 |
| `/adapt` | 适应 | 为不同设备调整 |
| `/onboard` | 引导设计 | 设计入职流程 |
| `/typeset` | 排版 | 修复字体选择、层次、大小 |
| `/arrange` | 排列 | 修复布局、间距、视觉节奏 |
| `/overdrive` | 超越 | 添加技术上前所未有的效果 |

### 4.2 /audit — 技术质量检查

**功能说明**

运行技术质量检查，包括无障碍、性能、响应式等方面。

**使用示例**

```bash
/audit                    # 检查整个项目
/audit blog               # 只检查博客页面
/audit dashboard          # 只检查仪表板
/audit checkout flow       # 只检查结账流程
```

**使用时机**：在做出更改之前，了解需要修复的内容。

### 4.3 /critique — UX 设计审查

**功能说明**

UX 设计审查，关注层次、清晰度、情感共鸣。

**使用示例**

```bash
/critique landing page    # 审查着陆页 UX
/critique onboarding      # 检查入职流程
```

**使用时机**：当你想要设计反馈而不是技术修复时。

### 4.4 /normalize — 对齐设计系统

**功能说明**

对齐设计系统标准，修复不一致。

**使用示例**

```bash
/normalize blog          # 应用设计 token，修复间距
/normalize buttons        # 标准化按钮样式
```

**使用时机**：审核后，修复不一致。

### 4.5 /polish — 最终完善

**功能说明**

发布前的最终检查和清理。

**使用示例**

```bash
/polish feature modal     # 发布前清理模态框
/polish settings page     # 设置页面的最终审查
```

**使用时机**：部署到生产环境前的最后一步。

### 4.6 命令组合使用

**完整工作流**

```bash
/audit /normalize /polish blog
# 完整流程：审核 → 修复 → 完善

/critique /harden checkout
# UX 审查 + 添加错误处理
```

---

## §5 反模式库

### 5.1 什么是反模式？

反模式明确告诉 AI 什么不应该做，这是 Impeccable 与其他工具的核心区别。

### 5.2 禁止列表

| 禁止 | 原因 |
|------|------|
| **使用 Arial、Inter、系统默认字体** | 过于通用，缺乏个性 |
| **彩色背景上的灰色文字** | 对比度不足，阅读困难 |
| **纯黑/纯灰（不添加色调）** | 缺乏层次感 |
| **用卡片包裹一切或嵌套卡片** | 过度使用组件 |
| **使用 bounce/elastic 缓动** | 感觉过时 |

---

## §6 安装与配置

### 6.1 方法一：从网站下载（推荐）

1. 访问 [impeccable.style](https://impeccable.style)
2. 下载适合你工具的 ZIP 包
3. 解压到你的项目

### 6.2 方法二：从仓库复制

**Cursor**

```bash
cp -r dist/cursor/.cursor your-project/
```

**注意**：Cursor skills 需要设置：
1. 在 Cursor Settings → Beta 中切换到 Nightly 频道
2. 在 Cursor Settings → Rules 中启用 Agent Skills

**Claude Code**

```bash
# 项目级别
cp -r dist/claude-code/.claude your-project/

# 全局（应用到所有项目）
cp -r dist/claude-code/.claude/* ~/.claude/
```

**OpenCode**

```bash
cp -r dist/opencode/.opencode your-project/
```

**Pi**

```bash
cp -r dist/pi/.pi your-project/
```

**Gemini CLI**

```bash
cp -r dist/gemini/.gemini your-project/
```

**注意**：Gemini CLI skills 需要设置：
1. 安装预览版本：`npm i -g @google/gemini-cli@preview`
2. 运行 `/settings` 并启用 "Skills"
3. 运行 `/skills list` 验证安装

**Codex CLI**

```bash
cp -r dist/codex/.codex/* ~/.codex/
```

**Trae**

```bash
# Trae 中国版（国内版本）
cp -r dist/trae/.trae-cn/skills/* ~/.trae-cn/skills/

# Trae 国际版
cp -r dist/trae/.trae/skills/* ~/.trae/skills/
```

**注意**：Trae 有两个版本，配置目录不同：
- Trae 中国版：`~/.trae-cn/skills/`
- Trae 国际版：`~/.trae/skills/`

### 6.3 验证安装

安装后，重启你的 IDE 激活技能。

---

## §7 使用示例

### 7.1 基础使用

```bash
/audit           # 找到问题
/normalize      # 修复不一致
/polish         # 最终清理
/distill        # 移除复杂性
```

### 7.2 带参数使用

大多数命令接受可选参数来聚焦特定区域：

```bash
/audit header
/polish checkout-form
/critique navigation
```

### 7.3 Codex CLI 语法

**注意**：Codex CLI 使用不同的语法：

```bash
/prompts:audit
/prompts:polish
```

---

## §8 支持的工具

| 工具 | 支持情况 |
|------|----------|
| **Cursor** | ✅ 完整支持 |
| **Claude Code** | ✅ 完整支持 |
| **OpenCode** | ✅ 完整支持 |
| **Pi** | ✅ 完整支持 |
| **Gemini CLI** | ✅ 完整支持 |
| **Codex CLI** | ✅ 完整支持 |
| **VS Code Copilot** | ✅ 完整支持 |
| **Kiro** | ✅ 完整支持 |
| **Trae** | ✅ 完整支持 |

---

## §9 项目结构

### 9.1 目录结构

| 目录 | 说明 |
|------|------|
| `.agents/skills/` | Agent Skills 配置 |
| `.claude-plugin/` | Claude 插件配置 |
| `.claude/skills/` | Claude Code Skills |
| `.codex/skills/` | Codex CLI Skills |
| `.cursor/skills/` | Cursor Skills |
| `.gemini/skills/` | Gemini CLI Skills |
| `.kiro/skills/` | Kiro Skills |
| `.opencode/skills/` | OpenCode Skills |
| `.pi/skills/` | Pi Skills |
| `.trae-cn/skills/` | Trae 中国版 Skills |
| `.trae/skills/` | Trae 国际版 Skills |
| `source/skills/` | 技能源文件 |
| `public/` | 静态资源 |
| `server/` | 服务器代码 |
| `lib/` | 库代码 |
| `tests/` | 测试 |
| `scripts/` | 脚本 |
| `functions/` | 函数 |

### 9.2 核心文件

| 文件 | 说明 |
|------|------|
| `AGENTS.md` | Agent 说明文档 |
| `CLAUDE.md` | Claude 使用指南 |
| `DEVELOP.md` | 开发者指南 |
| `HARNESSES.md` | 支持的工具列表 |
| `SKILL.md` | 技能定义 |
| `NOTICE.md` | 归属通知 |

---

## §10 常见问题

### Q1：Impeccable 和普通设计系统有什么区别？

| 特性 | Impeccable | 普通设计系统 |
|------|-------------|-------------|
| **目标用户** | AI 编码 Agent | 人类开发者 |
| **工作方式** | 命令驱动 | 组件库 |
| **反馈类型** | 设计建议 | UI 组件 |
| **覆盖范围** | 字体/颜色/空间/动效/交互/响应式/文案 | 主要是组件 |

### Q2：需要设计背景才能使用吗？

**不需要**。Impeccable 的设计知识已经内置在技能中，AI 会自动应用这些原则。

### Q3：支持自定义设计系统吗？

支持。编辑 `source/skills/frontend-design/reference/` 下的文件来添加你自己的设计规范。

### Q4：如何更新 Impeccable？

从 [impeccable.style](https://impeccable.style) 下载最新版本，替换 `dist/` 目录。

### Q5：支持哪些语言？

Impeccable 主要面向英文 UI，但设计原则适用于任何语言。

### Q6：如何贡献？

1. Fork 仓库
2. 查看 `DEVELOP.md` 了解开发指南
3. 提交 Pull Request

---

## §11 总结

### 11.1 核心优势

| 优势 | 说明 |
|------|------|
| **专业设计知识** | 7 个领域专项参考 |
| **20 个实用命令** | 覆盖设计全流程 |
| **反模式库** | 明确避免常见错误 |
| **多工具支持** | 9 个主流 AI 编码工具 |
| **开源免费** | Apache 2.0 许可证 |
| **基于 Anthropic** | 在原始 frontend-design 技能上构建 |

### 11.2 适用场景

| 场景 | 推荐指数 |
|------|----------|
| AI 前端开发 | ⭐⭐⭐⭐⭐ |
| 设计系统实施 | ⭐⭐⭐⭐⭐ |
| UI 审核和改进 | ⭐⭐⭐⭐⭐ |
| 动效和微交互 | ⭐⭐⭐⭐ |
| UX 文案优化 | ⭐⭐⭐⭐ |

### 11.3 项目信息

- Stars：15k
- Forks：641
- 贡献者：17 人
- 最新提交：2026-03-31
- 许可证：Apache 2.0

### 11.4 相关资源

| 资源 | 链接 |
|------|------|
| 官方网站 | https://impeccable.style |
| GitHub | https://github.com/pbakaus/impeccable |
| 案例研究 | https://impeccable.style/#casestudies |

---

*文档版本 1.0 | 撰写日期：2026-03-31 | 基于最新提交 (2026-03-31) | Stars: 15k ⭐*