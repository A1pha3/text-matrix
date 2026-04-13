---
title: "Ralph：PRD驱动的自主Agent循环，Claude Code的PRD执行框架"
date: 2026-04-13T11:50:00+08:00
lastmod: 2026-04-13T11:50:00+08:00
draft: false
tags: ["Ralph", "Claude Code", "AI Agent", "PRD", "自动化开发"]
categories: ["技术教程"]
slug: ralph-prd-agent-loop
description: "Ralph是一个自主AI Agent循环框架，基于Geoffrey Huntley的Ralph模式。通过PRD驱动的方式，让Claude Code或Amp自动执行产品需求文档中的每一项任务，直到全部完成。"
---

# Ralph：PRD驱动的自主Agent循环

## 概述

**Ralph**（16.1k stars, 463今日）是一个自主AI Agent循环框架，源自Geoffrey Huntley提出的Ralph模式。它能让Claude Code或Amp自动执行产品需求文档（PRD）中的每一项任务，直到全部完成。

与传统的"一次对话完成所有工作"不同，Ralph将大任务分解为小故事（Stories），每个迭代都是全新的AI实例，拥有干净的上下文，确保不会遗忘或迷失。

🦞 作者：snarktank | ⭐ 16.1k Stars | 🍴 1.6k Forks | MIT License

---

## 核心原理

### 每个迭代 = 全新上下文

每次Ralph循环都会启动一个新的AI实例（Claude Code或Amp），拥有完全干净的上下文。迭代之间只通过以下方式保留记忆：

1. **Git历史** - 之前迭代的提交记录
2. **progress.txt** - 学习笔记和上下文
3. **prd.json** - 哪些故事已完成

### 小任务原则

每个PRD条目应该足够小，能在一个上下文窗口内完成。如果任务太大，LLM会在完成前耗尽上下文，产生劣质代码。

**适当大小的故事：**
- 添加数据库列和迁移
- 在现有页面上添加UI组件
- 更新服务器操作的逻辑
- 在列表上添加筛选下拉框

**太大的任务（需要拆分）：**
- "构建整个仪表板"
- "添加身份验证"
- "重构API"

---

## 工作流程

### 第一步：创建PRD

使用PRD技能生成详细的需求文档：

```
Load the prd skill and create a PRD for [your feature description]
```

回答澄清问题，技能将输出保存到 `tasks/prd-[feature-name].md`。

### 第二步：转换为Ralph格式

使用Ralph技能将Markdown PRD转换为JSON：

```
Load the ralph skill and convert tasks/prd-[feature-name].md to prd.json
```

这会创建 `prd.json`，包含为自主执行结构化的用户故事。

### 第三步：运行Ralph

```bash
# 使用Amp（默认）
./scripts/ralph/ralph.sh [max_iterations]

# 使用Claude Code
./scripts/ralph/ralph.sh --tool claude [max_iterations]
```

Ralph会执行以下步骤：

1. 创建功能分支（来自PRD的 `branchName`）
2. 选择 `passes: false` 的最高优先级故事
3. 实现该单一故事
4. 运行质量检查（类型检查、测试）
5. 如果检查通过则提交
6. 更新 `prd.json` 将故事标记为 `passes: true`
7. 将学习笔记追加到 `progress.txt`
8. 重复直到所有故事通过或达到最大迭代次数

---

## 关键文件

| 文件 | 用途 |
|------|------|
| `ralph.sh` | Bash循环脚本，支持 `--tool amp` 或 `--tool claude` |
| `prompt.md` | Amp的提示模板 |
| `CLAUDE.md` | Claude Code的提示模板 |
| `prd.json` | 用户故事及其通过状态（任务列表） |
| `progress.txt` | 供未来迭代参考的追加式学习笔记 |
| `skills/prd/` | 用于生成PRD的技能（支持Amp和Claude Code） |
| `skills/ralph/` | 用于将PRD转换为JSON的技能（支持Amp和Claude Code） |
| `flowchart/` | Ralph工作原理的交互可视化 |

---

## Claude Code Marketplace支持

Ralph可以通过Claude Code Marketplace安装：

```bash
/plugin marketplace add snarktank/ralph
/plugin install ralph-skills@ralph-marketplace
```

安装后可用的技能：
- `/prd` - 生成产品需求文档
- `/ralph` - 将PRD转换为prd.json格式

技能会在以下情况下自动调用：
- "create a prd"、"write prd for"、"plan this feature"
- "convert this prd"、"turn into ralph format"、"create prd.json"

---

## 关键概念

### AGENTS.md更新至关重要

每次迭代后，Ralph会更新相关的 `AGENTS.md` 文件，包含学习笔记。这很关键，因为AI编码工具会自动读取这些文件，所以未来的迭代（和未来的人类开发者）会从发现的模式、陷阱和约定中受益。

**应添加到AGENTS.md的内容示例：**
- 发现的模式（"这个代码库用X做Y"）
- 陷阱（"更改W时不要忘记更新Z"）
- 有用的上下文（"设置面板在组件X中"）

### 反馈循环

Ralph只有在存在反馈循环时才能工作：
- 类型检查捕获类型错误
- 测试验证行为
- CI必须保持绿色（坏代码会在迭代中累积）

### UI故事的浏览器验证

前端故事必须在验收标准中包含"使用dev-browser技能在浏览器中验证"。Ralph会使用dev-browser技能导航到页面，与UI交互，并确认更改有效。

### 停止条件

当所有故事的 `passes: true` 时，Ralph输出 `<promise>COMPLETE</promise>` 并退出循环。

---

## 安装方式

### 方式一：复制到项目

```bash
# 从项目根目录
mkdir -p scripts/ralph
cp /path/to/ralph/ralph.sh scripts/ralph/

# 复制你选择的AI工具的提示模板：
# 对于Amp
cp /path/to/ralph/prompt.md scripts/ralph/prompt.md
# 对于Claude Code
cp /path/to/ralph/CLAUDE.md scripts/ralph/CLAUDE.md
chmod +x scripts/ralph/ralph.sh
```

### 方式二：全局安装技能（Amp）

```bash
cp -r skills/prd ~/.config/amp/skills/
cp -r skills/ralph ~/.config/amp/skills/
```

### 方式三：Claude Code Marketplace

```bash
/plugin marketplace add snarktank/ralph
/plugin install ralph-skills@ralph-marketplace
```

---

## 与其他框架的对比

| 框架 | 特点 | Ralph优势 |
|------|------|----------|
| **Superpowers** | TDD优先，铁律法则 | 更灵活的任务拆分 |
| **Agent SDK** | 工具调用优先 | PRD驱动确保完整性 |
| **Claude Code内置** | 单次会话 | 持久化记忆和迭代 |

---

## 调试技巧

```bash
# 查看哪些故事已完成
cat prd.json | jq '.userStories[] | {id, title, passes}'

# 查看之前迭代的学习笔记
cat progress.txt

# 查看git历史
git log --oneline -10
```

---

## 适用场景

✅ **复杂功能开发** - 需要多步骤的大型功能  
✅ **遗留代码改造** - 任务清晰但工作量大  
✅ **团队协作** - PRD明确后自动执行  
✅ **需要质量保证** - 每次迭代都运行测试和检查

❌ **简单任务** - 一次性完成的小任务  
❌ **探索性工作** - 需求不明确的场景  
❌ **没有反馈循环** - 没有测试/类型检查的项目

---

## 资源链接

- [GitHub仓库](https://github.com/snarktank/ralph)
- [Geoffrey Huntley的Ralph文章](https://ghuntley.com/ralph/)
- [交互式流程图](https://snarktank.github.io/ralph/)
- [PRD生成技能](https://github.com/snarktank/ralph/tree/main/skills/prd)
- [Ralph转换技能](https://github.com/snarktank/ralph/tree/main/skills/ralph)

---

*Ralph代表了AI编程自动化的一个重要方向：通过PRD驱动的任务分解和迭代执行，让AI能够自主完成复杂的多步骤开发任务，同时通过结构化的记忆机制保证长期项目的连贯性。*
