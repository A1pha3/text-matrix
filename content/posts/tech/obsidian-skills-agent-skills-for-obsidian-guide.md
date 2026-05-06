---
title: "Obsidian Skills：Obsidian 智能体技能完全指南"
date: "2026-04-06T21:34:00+08:00"
slug: "obsidian-skills-agent-skills-for-obsidian-guide"
description: "全面介绍 20.2k Stars 的 Obsidian Skills 技能集，涵盖 obsidian-markdown、obsidian-bases、json-canvas、obsidian-cli、defuddle 五大技能，以及在 Claude Code、Codex CLI、OpenCode 中的安装和用法。"
draft: false
categories: ["技术笔记"]
tags: ["Obsidian", "Agent Skills", "Claude Code", "Markdown", "知识管理"]
---

## 学习目标

通过本文，你将全面掌握以下核心能力：

- 深入理解 Obsidian Skills 的项目定位和设计理念
- 掌握 5 个核心技能的功能和使用场景
- 学会在不同 AI Agent 平台安装和配置这些技能
- 理解 Agent Skills 规范与 Obsidian 的集成方式
- 掌握 obsidian-markdown、obsidian-bases、json-canvas、obsidian-cli、defuddle 的用法
- 理解如何用这些技能提升 Obsidian 使用效率

---

## 1. 项目概述

### 1.1 是什么

Obsidian Skills 是一套**面向 Obsidian 的 Agent 智能体技能集合**，让 AI Agent 能够理解和使用 Obsidian 的各种特定格式和功能。

这些技能遵循 **Agent Skills 规范**，因此可以与任何兼容 Agent Skills 的 AI Agent 配合使用，包括 Claude Code、Codex CLI 和 OpenCode。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | **20.2k** |
| GitHub Forks | **1.3k** |
| 维护者 | **kepano** |
| License | **MIT** |
| 技能数量 | **5 个** |

### 1.3 5 个核心技能

| 技能 | 功能 |
|------|------|
| **obsidian-markdown** | Obsidian  flavored Markdown 编辑（wikilinks、embeds、callouts、properties） |
| **obsidian-bases** | Obsidian Bases 数据库编辑（views、filters、formulas、summaries） |
| **json-canvas** | JSON Canvas 文件编辑（nodes、edges、groups、connections） |
| **obsidian-cli** | 通过 Obsidian CLI 与保险库交互（插件/主题开发） |
| **defuddle** | 使用 Defuddle 从网页提取干净 Markdown（节省 tokens） |

### 1.4 与竞品对比

| 特性 | Obsidian Skills | 其他方案 |
|------|-----------------|----------|
| **平台支持** | Claude Code + Codex + OpenCode | 通常只支持单一平台 |
| **技能数量** | 5 个核心技能 | - |
| **Markdown 支持** | Obsidian 特有格式完整支持 | 一般只支持标准 Markdown |
| **Defuddle 集成** | ✅ 原生集成 | ❌ 不支持 |
| **活跃度** | 20.2k stars，持续更新 | - |

---

## 2. obsidian-markdown 技能

### 2.1 功能概述

**obsidian-markdown** 是最重要的技能，它让 AI Agent 能够正确理解和编辑 **Obsidian Flavored Markdown**（Obsidian 特有格式）。

### 2.2 支持的 Obsidian 特有语法

```markdown
### Wikilinks（双向链接）
[[Obsidian]]                    # 链接到 Obsidian 页面
[[Obsidian|显示文本]]           # 带显示文本的链接
[[Obsidian#章节]]               # 链接到特定章节
[[Obsidian#章节|显示文本]]      # 组合使用

### Embeds（嵌入）
![[Obsidian]]                   # 嵌入整个页面
![[Obsidian#章节]]              # 嵌入特定章节
![[Obsidian#^block-id]]        # 通过块 ID 嵌入

### Callouts（标注块）
> [!note]                       # 笔记标注
> [!warning]                   # 警告标注
> [!todo]                      # 待办标注
> [!abstract]- 摘要内容        # 摘要标注

### Properties（属性/前置元数据）
---
aliases: ["Obsidian", "知识管理"]
tags: [obsidian, markdown]
cssclasses: [highlight]
---

### Dataview 语法
```dataview
TABLE file.ctime AS 创建时间
FROM ""
WHERE file.folder = "待整理"
SORT file.mtime DESC
```

### 其他 Obsidian 特有语法
- 高亮：==这是高亮文字==
- 脚注：[^1] 和 [^1]: 脚注内容
- 任务列表：- [ ] 未完成 / - [x] 已完成
```

### 2.3 使用示例

```markdown
# 创建带完整元属性的笔记

---
aliases: ["项目管理工具", "PM软件"]
tags: [工具, 项目管理, 效率]
created: 2024-01-15
cssclasses: [table-clean]
---

# Obsidian 使用指南

## 简介

Obsidian 是一个强大的知识管理工具，结合了 [[Markdown]] 的简洁性和双向链接的威力。

## 核心功能

> [!tip] 提示
> 使用快捷键可以大幅提升效率！

## 相关主题

- 参见 [[插件推荐]]
- 嵌入会议记录：![[2024-01-Meeting Notes]]
- 查看待办：^todo-list
```

---

## 3. obsidian-bases 技能

### 3.1 功能概述

**obsidian-bases** 让 AI Agent 能够创建和编辑 **Obsidian Bases**（数据库）文件，使用 views、filters、formulas 和 summaries。

### 3.2 Bases 语法

```yaml
# 项目跟踪 .base 文件示例
name: 项目跟踪
description: 跟踪所有进行中的项目

# 视图定义
views:
  - name: 全部项目
    type: table
    columns:
      - name: 项目名
        field: name
        width: 200
      - name: 状态
        field: status
        width: 100
      - name: 负责人
        field: owner
        width: 150
      - name: 截止日期
        field: due_date
        width: 120
    filters:
      - field: status
        operator: not equal
        value: 已完成
    sort:
      - field: due_date
        direction: ascending

  - name: 我的项目
    type: kanban
    group_by: status
    filter:
      field: owner
      operator: equal
      value: 当前用户

# 公式字段
formulas:
  - name: 是否紧急
    expression: if(due_date < today(), "🔴紧急", "✅正常")
  
  - name: 剩余天数
    expression: due_date - today()

# 汇总
summaries:
  - name: 总项目数
    expression: count()
  - name: 进行中
    expression: count() where status = "进行中"
```

### 3.3 使用示例

```yaml
# 读书笔记库 .base 文件
name: 读书笔记库
description: 管理所有书籍阅读笔记

views:
  - name: 读书清单
    type: gallery
    card_fields:
      - name: 书名
        field: title
      - name: 封面
        field: cover_url
      - name: 作者
        field: author
    filters:
      - field: status
        operator: not equal
        value: 已读完

  - name: 按作者分组
    type: table
    group_by: author
    columns:
      - name: 书名
        field: title
      - name: 评分
        field: rating
        type: number
      - name: 阅读日期
        field: read_date
```

---

## 4. json-canvas 技能

### 4.1 功能概述

**json-canvas** 让 AI Agent 能够创建和编辑 **JSON Canvas** 文件，用于创建视觉化的思维导图和关系图。

### 4.2 Canvas 语法

```json
{
  "nodes": [
    {
      "id": "node-1",
      "type": "text",
      "x": 100,
      "y": 100,
      "width": 200,
      "height": 100,
      "text": "中心主题"
    },
    {
      "id": "node-2",
      "type": "text",
      "x": 400,
      "y": 100,
      "width": 180,
      "height": 80,
      "text": "分支主题 A"
    },
    {
      "id": "node-3",
      "type": "file",
      "x": 400,
      "y": 250,
      "width": 180,
      "height": 80,
      "file": "obsidian://open?vault=MyVault&file=笔记A"
    }
  ],
  "edges": [
    {
      "id": "edge-1",
      "fromNode": "node-1",
      "fromSide": "right",
      "toNode": "node-2",
      "toSide": "left"
    },
    {
      "id": "edge-2",
      "fromNode": "node-1",
      "fromSide": "right",
      "toNode": "node-3",
      "toSide": "left"
    }
  ],
  "groups": [
    {
      "id": "group-1",
      "name": "重要",
      "color": "#ff6b6b",
      "nodes": ["node-1", "node-2"]
    }
  ]
}
```

### 4.3 使用示例

```json
// 项目管理 Canvas 示例
{
  "nodes": [
    {
      "id": "project-center",
      "type": "text",
      "x": 500,
      "y": 300,
      "width": 200,
      "height": 80,
      "text": "🚀 项目管理中心"
    },
    {
      "id": "dev-group",
      "type": "group",
      "x": 100,
      "y": 100,
      "width": 300,
      "height": 400,
      "color": "#4dabf7",
      "label": "开发组"
    },
    {
      "id": "design-group",
      "type": "group",
      "x": 700,
      "y": 100,
      "width": 300,
      "height": 400,
      "color": "#ffd43b",
      "label": "设计组"
    }
  ],
  "edges": [
    {
      "id": "edge-dev",
      "fromNode": "project-center",
      "toNode": "dev-task-1",
      "color": "#4dabf7"
    },
    {
      "id": "edge-design",
      "fromNode": "project-center",
      "toNode": "design-task-1",
      "color": "#ffd43b"
    }
  ]
}
```

---

## 5. obsidian-cli 技能

### 5.1 功能概述

**obsidian-cli** 让 AI Agent 能够通过 Obsidian CLI 与保险库交互，包括插件和主题开发。

### 5.2 支持的 CLI 命令

```bash
# 保险库操作
obsidian vault open <path>           # 打开保险库
obsidian vault create <name>         # 创建新保险库
obsidian vault list                  # 列出所有保险库

# 文件操作
obsidian file create <path>          # 创建新文件
obsidian file move <from> <to>       # 移动文件
obsidian file delete <path>           # 删除文件
obsidian file search <query>          # 搜索文件

# 插件管理
obsidian plugin install <plugin-id>   # 安装插件
obsidian plugin enable <plugin-id>    # 启用插件
obsidian plugin disable <plugin-id>   # 禁用插件
obsidian plugin list                  # 列出已安装插件

# 主题管理
obsidian theme install <theme-id>     # 安装主题
obsidian theme apply <theme-id>       # 应用主题

# 开发命令
obsidian dev create-plugin <name>     # 创建插件项目
obsidian dev build                    # 构建插件
obsidian dev reload                  # 热重载插件
```

### 5.3 使用示例

```bash
# 创建新笔记
obsidian file create "我的笔记/新文章.md"
# 内容:
# ---
# created: 2024-01-15
# tags: [文章, 草稿]
# ---
# 
# # 新文章标题
# 
# 正文内容...

# 安装推荐插件
obsidian plugin install obsidian-git          # Git 备份
obsidian plugin install obsidian-tasks-plugin  # 任务管理
obsidian plugin install dataview              # 数据库

# 搜索包含特定标签的笔记
obsidian file search "tag:#工作"
```

---

## 6. defuddle 技能

### 6.1 功能概述

**defuddle** 使用 Defuddle 从网页提取干净的 Markdown，移除杂乱内容以节省 tokens。

### 6.2 Defuddle 简介

Defuddle 是一个专为 AI 设计的内容提取工具，它可以：

- 移除网页广告、导航栏、页脚
- 提取干净的 Markdown 内容
- 保留代码块和结构化内容
- 优化以节省 tokens

### 6.3 使用示例

```bash
# 提取网页为 Markdown
defuddle https://example.com/article

# 指定输出文件
defuddle https://example.com/article -o article.md

# 只提取正文
defuddle https://example.com/article --content-only

# 保留代码块
defuddle https://dev.to/article -o article.md --keep-code
```

### 6.4 与 Obsidian 集成

```bash
# 从网页提取并直接创建 Obsidian 笔记
defuddle https://blog.example.com/tech-article | \
  obsidian file create "Inbox/web-article-$(date +%Y%m%d).md"

# 在 AI Agent 中自动使用
# 当需要从网页提取内容时：
# 1. 使用 defuddle 提取干净 Markdown
# 2. 清理后的内容直接可用于 Obsidian
```

---

## 7. 安装指南

### 7.1 Claude Code 安装

```bash
# 方式一：插件市场安装
/plugin marketplace add kepano/obsidian-skills
/plugin install obsidian@obsidian-skills

# 方式二：手动安装
# 将仓库内容添加到保险库的 /.claude/ 目录
git clone https://github.com/kepano/obsidian-skills.git ~/.claude/obsidian-skills
```

### 7.2 Codex CLI 安装

```bash
# 复制 skills/ 目录到 Codex skills 路径
cp -r skills/ ~/.codex/skills/obsidian-skills

# 验证安装
codex skills list
```

### 7.3 OpenCode 安装

```bash
# 克隆整个仓库到 OpenCode skills 目录
git clone https://github.com/kepano/obsidian-skills.git \
  ~/.opencode/skills/obsidian-skills

# 注意：不要只复制内部的 skills/ 文件夹！
# 目录结构必须是：
# ~/.opencode/skills/obsidian-skills/skills/<skill-name>/SKILL.md
```

### 7.4 npx 安装

```bash
# 使用 npx 安装
npx skills add git@github.com:kepano/obsidian-skills.git
```

---

## 8. 在 AI Agent 中使用

### 8.1 Claude Code 使用示例

当你在 Claude Code 中处理 Obsidian 相关任务时，可以这样使用：

```
用户：帮我整理一下这个文件夹里的笔记

Claude Code：
我需要先了解这个文件夹的内容，然后使用 obsidian-markdown 技能来整理。

[使用 obsidian-markdown 技能]
1. 首先扫描文件夹中的所有 .md 文件
2. 识别每个文件中的 wikilinks 和 embeds
3. 检查 properties 是否完整
4. 建议添加缺失的 tags 和 aliases
```

### 8.2 技能组合使用

```markdown
# 项目管理示例：组合使用多个技能

## obsidian-markdown + obsidian-bases + json-canvas

### 1. 创建项目笔记（obsidian-markdown）
---
aliases: ["项目A", "Project A"]
tags: [项目, 重要]
status: 进行中
---

# 项目 A

负责人：@张三
截止日期：2024-03-01

### 2. 创建任务数据库（obsidian-bases）
# 在 .base 文件中定义任务视图...

### 3. 创建项目关系图（json-canvas）
# 可视化任务之间的依赖关系...
```

---

## 9. 常见问题

### 9.1 安装后技能不生效

```bash
# 1. 确认目录结构正确
ls -la ~/.claude/skills/obsidian-skills/

# 2. 重启 AI Agent
# Claude Code: /exit 然后重新启动

# 3. 检查技能是否在可用列表中
/plugin list
```

### 9.2 Wikilinks 无法解析

```markdown
# 确保使用正确的语法
❌ [[笔记]]           # 可能不工作
✅ [[笔记|显示文本]]   # 带显示文本

# 确保文件扩展名正确
✅ [[我的笔记]]       # Obsidian 自动添加 .md
```

### 9.3 Defuddle 提取内容不完整

```bash
# 尝试使用不同的提取模式
defuddle <url> --content-only      # 只提取正文
defuddle <url> --full-page         # 提取整页
defuddle <url> --max-tokens 2000   # 限制 token 数量
```

---

## 10. 总结

Obsidian Skills 是一套**完整的 Obsidian AI Agent 技能集**，包含 5 个核心技能：

**技能概览：**

| 技能 | 用途 | 重要性 |
|------|------|--------|
| **obsidian-markdown** | Obsidian Markdown 格式编辑 | ⭐⭐⭐⭐⭐ |
| **obsidian-bases** | 数据库文件和视图编辑 | ⭐⭐⭐⭐ |
| **json-canvas** | 视觉化思维导图创建 | ⭐⭐⭐ |
| **obsidian-cli** | 命令行交互和开发 | ⭐⭐⭐ |
| **defuddle** | 网页内容提取节省 tokens | ⭐⭐⭐⭐ |

**为什么选择 Obsidian Skills：**

| 优势 | 说明 |
|------|------|
| **多平台支持** | Claude Code、Codex CLI、OpenCode |
| **20.2k stars** | 社区广泛认可和使用 |
| **完整覆盖** | 涵盖 Obsidian 所有核心功能 |
| **节省 tokens** | Defuddle 优化网页内容提取 |
| **开源透明** | MIT License |

**适用场景：**

- Obsidian 知识库管理和整理
- 项目管理和任务追踪
- 插件和主题开发
- 从网页提取内容并保存到 Obsidian
- 创建可视化的笔记关系图

**官方资源：**

- GitHub：https://github.com/kepano/obsidian-skills
- Obsidian 官网：https://obsidian.md
- Agent Skills 规范：https://agentskills.io/specification