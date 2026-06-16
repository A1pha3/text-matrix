---
title: "Obsidian Mind：让 Claude Code 拥有持久记忆的 Obsidian 保险库"
date: "2026-04-04T20:26:00+08:00"
slug: "obsidian-mind-claude-code-memory-system-guide"
description: "Obsidian Mind 是一个让 Claude Code 记住一切的 Obsidian 保险库模板。通过 5 个生命周期钩子、15+Slash 命令和 9 个子代理，自动分类、索引和链接你的工作笔记，构建个人知识图谱和绩效追踪系统。"
draft: false
categories: ["技术笔记"]
tags: ["Obsidian", "Claude Code", "AI Agent", "知识管理", "生产力"]
---

# Obsidian Mind：让 Claude Code 拥有持久记忆的 Obsidian 保险库

> 项目地址：[breferrari/obsidian-mind](https://github.com/breferrari/obsidian-mind)
>
> 今日 Star：462（+0）| Forks：37 | License：MIT
>
> 核心定位：用 Obsidian 给 Claude Code 构建一个「外脑」，让 AI 代理的记忆跨会话持久化

## 学习目标

读完本文后，你会了解：

1. Claude Code「遗忘问题」的本质及其对 AI 协作效率的影响
2. Obsidian Mind 的核心设计理念：Vault-first Memory + 生命周期钩子
3. 15+ Slash 命令完成日常工作流（晨会、复盘、1:1 记录等）
4. 9 个子代理的分工与协作机制
5. 搭建个人 Performance Graph，将工作笔记链接到能力框架
6. 使用 /vault-upgrade 从旧保险库迁移内容

---

## 一、问题：Claude Code 的「遗忘症」

Claude Code 非常强大，但每次会话都从零开始——没有你的目标上下文、没有团队信息、没有你的工作模式。你需要反复解释相同的事情，半年前做出的决策早已忘记。**知识无法积累，经验无法复利。**

这是一个根本性限制：AI 代理的上下文窗口是有限的，而人类的工作和思考是连续递增的。

---

## 二、解决方案：给 Claude 一个「外脑」

Obsidian Mind 的核心思想很简单：**把 Claude Code 的「记忆」外部化到一个 Obsidian 保险库中**，让每次新会话都能加载历史上下文。

### 核心理念

> **Folders group by purpose. Links group by meaning.**
> 笔记归属于一个文件夹（它的「家」），但通过链接连接到多个笔记（它的上下文）。
> Claude 自动维护这张图谱——将工作笔记与人、决策、能力自动关联。

### 工作示意

```
你：「start session」
Claude：（读取 North Star、检查活跃项目、扫描近期记忆）
Claude：「你在做 Project Alpha，被 BE 合约阻塞。上次会话你决定拆分 coordinator。
        你和经理的 1:1 在明天——简报已准备好。」
```

这就是 Vault-first Memory 的威力：**会话之间无缝衔接，上下文自动累积**。

---

## 三、核心技术：5 个生命周期钩子

Obsidian Mind 通过 5 个生命周期钩子实现自动化路由：

| 钩子 | 触发时机 | 功能 |
|------|----------|------|
| 🚀 SessionStart | 启动/恢复会话 | QMD 重建索引、注入 North Star、活跃工作、近期变更、任务、文件列表 |
| 💬 UserPromptSubmit | 每条消息 | 分类内容（决策/事件/成就/1:1/架构/人）并注入路由提示 |
| ✍️ PostToolUse | 写入 .md 后 | 验证 frontmatter、检查 wikilinks、验证文件夹归属 |
| 💾 PreCompact | 上下文压缩前 | 将会话转录备份到 thinking/session-logs/ |
| 🏁 Stop | 会话结束 | 检查清单：归档完成项目、更新索引、检查孤儿笔记 |

### 实际效果

你只需要正常说话，钩子自动处理路由：

```
你："/dump 刚和 Sarah 做了 1:1，她对 auth 工作满意但希望在上线前加错误监控。
    还有，Tom 说缓存迁移推迟到 Q2 了——我们决定先专注 API 合约。决策：推迟 Redis 迁移。
    成就：Sarah 称赞了 auth 架构。"

Claude：→ 更新 org/people/Sarah Chen.md 加入会议上下文
      → 创建 work/1-1/Sarah 2026-03-26.md 含关键要点
      → 创建决策记录：「推迟 Redis 迁移到 Q2」
      → 在 perf/Brag Doc.md 添加：「经理称赞 auth 架构」
      → 在 work/active/Auth Refactor.md 添加错误监控任务
```

---

## 四、15+ Slash 命令详解

Obsidian Mind 定义了 15+ 个命令，覆盖完整工作流：

### 日常命令

| 命令 | 功能 |
|------|------|
| `/standup` | 晨会启动——加载上下文、回顾昨天、浮现任务、建议优先级 |
| `/dump` | 自由捕获——自然讲述任何事情，Claude 自动路由到正确笔记 |
| `/wrap-up` | 完整会话复盘——验证笔记、更新索引、检查链接、发现未捕获成就 |

### 会议与事件

| 命令 | 功能 |
|------|------|
| `/capture-1on1` | 捕获 1:1 会议转录，整理为结构化保险库笔记 |
| `/incident-capture` | 从 Slack 频道捕获事件，写入结构化笔记 |
| `/slack-scan` | 深度扫描 Slack 频道/DM 寻找证据 |
| `/peer-scan` | 深度扫描同事的 GitHub PR，为复盘准备 |

### 复盘与绩效

| 命令 | 功能 |
|------|------|
| `/review-brief manager` | 生成经理复盘简报（含所有关联证据） |
| `/review-brief peer` | 生成同事复盘简报 |
| `/self-review` | 撰写自评——项目、能力、原则 |
| `/review-peer` | 撰写同事评审 |

### 保险库维护

| 命令 | 功能 |
|------|------|
| `/vault-audit` | 审计索引、链接、孤儿笔记、陈旧上下文 |
| `/vault-upgrade` | 从现有保险库导入——版本检测、分类、迁移 |
| `/project-archive` | 将完成项目从 active/ 移动到 archive/，更新索引 |

### 编辑命令

| 命令 | 功能 |
|------|------|
| `/humanize` | 语音校准编辑——让 Claude 起草的文本听起来像你写的 |

---

## 五、9 个子代理：专业化分工

Obsidian Mind 内置 9 个子代理，运行在隔离的上下文窗口中：

| 子代理 | 职责 | 调用方式 |
|--------|------|----------|
| **brag-spotter** | 发现未捕获的成就和能力差距 | /wrap-up, /weekly |
| **context-loader** | 加载关于某人、项目或概念的所有保险库上下文 | 直接调用 |
| **cross-linker** | 寻找缺失的 wikilinks、孤儿笔记、断开的反向链接 | /vault-audit |
| **people-profiler** | 批量从 Slack 个人资料创建/更新人物笔记 | /incident-capture |
| **review-prep** | 汇总复盘周期的所有绩效证据 | /review-brief |
| **slack-archaeologist** | 完整 Slack 重建——每条消息、线程、个人资料 | /incident-capture |
| **vault-librarian** | 深度保险库维护——孤儿笔记、断链、陈旧笔记 | /vault-audit |
| **review-fact-checker** | 验证复盘草稿中每个声明的保险库来源 | /self-review, /review-peer |
| **vault-migrator** | 分类、转换、迁移源保险库内容 | /vault-upgrade |

---

## 六、Performance Graph：绩效图谱

Obsidian Mind 的保险库同时也是一个**绩效追踪系统**：

### 工作原理

1. **能力笔记**（perf/competencies/）定义你的能力框架——每个能力一篇笔记
2. **工作笔记**在它们的 `## Related` 部分链接到能力，并标注展示了什么
3. **反向链接自动累积**——复盘准备变成阅读每个能力笔记的反向链接面板
4. **Brag Doc** 按季度聚合成就，带有到证据笔记的链接

### 证据流

```
/peer-scan <同事> 
→ 深度扫描同事的 GitHub PR
→ 将结构化证据写入 perf/evidence/

/review-brief manager
→ 汇总所有内容生成完整复盘简报：
  - 成就条目
  - 决策
  - 事件
  - 能力证据
  - 1:1 反馈
```

---

## 七、保险库结构

```
Obsidian-Mind/
├── Home.md              # 入口——嵌入 Base 视图、快速链接
├── CLAUDE.md            # 操作手册——Claude 每次会话都读取
├── vault-manifest.json  # 模板元数据——版本、结构、模式
├── brain/               # 🧠 核心记忆
│   ├── North Star.md    # 目标——每次会话都读取
│   ├── Memories.md      # 记忆主题索引
│   ├── Key Decisions.md # 关键决策及理由
│   ├── Patterns.md      # 跨工作观察到的模式
│   └── Gotchas.md       # 犯过的错误及原因
├── work/                # 工作笔记
│   ├── active/         # 活跃项目（保持 1-3 个）
│   ├── archive/YYYY/   # 按年归档的完成工作
│   ├── incidents/       # 事件文档
│   └── 1-1/            # 1:1 会议笔记
├── org/                 # 组织知识
│   ├── people/         # 每人一篇笔记
│   └── teams/          # 每团队一篇笔记
├── perf/                # 绩效追踪
│   ├── Brag Doc.md     # 成就日志
│   ├── competencies/   # 能力笔记
│   └── evidence/       # PR 深度扫描证据
├── reference/           # 代码库知识、架构图
├── thinking/           # 草稿——推广后删除
├── templates/          # Obsidian 模板
├── bases/              # 📊 动态数据库视图
│   ├── Work Dashboard  # 活跃项目仪表板
│   ├── Incidents       # 事件列表
│   ├── People Directory # 人物目录
│   └── Competency Map  # 能力地图
└── .claude/            # Claude Code 配置
    ├── commands/       # 15+ Slash 命令
    ├── agents/         # 9 个子代理
    └── hooks/          # 5 个生命周期钩子
```

---

## 八、快速上手

### 1. 克隆模板

```bash
git clone https://github.com/breferrari/obsidian-mind.git ~/obsidian-mind
cd ~/obsidian-mind
```

### 2. 打开为 Obsidian 保险库

在 Obsidian 中打开文件夹作为保险库。

### 3. 启用 Obsidian CLI

Settings → General → 启用 Obsidian CLI（需要 Obsidian 1.12+）

### 4. 启动 Claude Code

```bash
cd ~/obsidian-mind
claude
```

### 5. 填写你的 North Star

编辑 `brain/North Star.md`，填写你的目标——这为每次会话奠定基础。

### 6. 开始工作

正常谈论你的工作，钩子自动处理路由。

---

## 九、升级现有保险库

已有旧版 obsidian-mind 或任何 Obsidian 保险库？使用 `/vault-upgrade` 迁移：

```bash
# 1. 克隆最新 obsidian-mind
git clone https://github.com/breferrari/obsidian-mind.git ~/new-vault

# 2. 在 Claude Code 中打开
cd ~/new-vault && claude

# 3. 运行升级，指向旧保险库
/vault-upgrade ~/my-old-vault
```

Claude 会：

1. **检测**你的保险库版本（v1–v3.2，或识别为非 obsidian-mind 保险库）
2. **清点**每个文件——分类为用户内容/脚手架/基础设施/未分类
3. **呈现**迁移计划——你精确看到将被复制、转换和跳过的内容
4. **执行**在你批准后——转换 frontmatter、修复 wikilinks、重建索引
5. **验证**——检查孤儿笔记、断链、缺失 frontmatter

旧保险库**永远不会被修改**。使用 `--dry-run` 预览计划而不执行。

---

## 十、可选：QMD 语义搜索

对于跨保险库的语义搜索（找到「我们对缓存的决定」即使笔记标题是「Redis 迁移 ADR」）：

```bash
npm install -g @tobi/qmd
qmd collection add . --name vault --mask "**/*.md"
qmd context add qmd://vault "Engineer's work vault: projects, decisions, incidents, people, reviews, architecture"
qmd update && qmd embed
```

如果未安装 QMD，一切仍然正常工作——Claude 回退到 Obsidian CLI 和 grep。

---

## 十一、定制指南

这是起点，适应你的工作方式：

| 定制内容 | 修改位置 |
|----------|----------|
| 你的目标 | brain/North Star.md |
| 你的组织 | org/——添加经理、团队、关键协作者 |
| 你的能力框架 | perf/competencies/——匹配你的组织能力模型 |
| 你的工具 | .claude/commands/——为你的 GitHub 组织、Slack 工作区编辑 |
| 你的约定 | CLAUDE.md——操作手册，随工作演进更新 |
| 你的领域 | 添加文件夹、.claude/agents/ 中的子代理、或 .claude/scripts/ 中的分类规则 |

---

## 十二、总结

Obsidian Mind 解决了一个根本问题：AI 代理的上下文窗口是有限的，而人类的知识和经验是连续递增的。

通过将 Claude Code 的「记忆」外部化到 Obsidian 保险库，结合 5 个生命周期钩子的自动化路由、15+ Slash 命令的便捷操作、以及 9 个子代理的专业分工，Obsidian Mind 构建了：

1. **持久化记忆系统**——跨会话无缝衔接
2. **自动分类引擎**——自然语言输入，自动路由到正确位置
3. **绩效追踪图谱**——工作笔记自动链接到能力框架
4. **团队知识库**——人物、团队、决策、事件全面关联

重度使用 Claude Code 的话，Obsidian Mind 能把 AI 协作效率提升一个量级。

---

**相关链接：**
- GitHub：https://github.com/breferrari/obsidian-mind
- Obsidian：https://obsidian.md
- Claude Code：https://docs.anthropic.com/en/docs/claude-code
- QMD（可选语义搜索）：https://github.com/tobi/qmd
