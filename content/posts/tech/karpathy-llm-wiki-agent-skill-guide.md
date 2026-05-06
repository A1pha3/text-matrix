---
title: "Karpathy LLM Wiki：让AI自动维护你的知识库"
slug: "karpathy-llm-wiki-agent-skill-guide"
date: "2026-04-08T11:10:00+08:00"
lastmod: 2026-04-08T11:10:00+08:00
categories: ["技术笔记"]
tags: ["AI", "知识管理", "Wiki", "Agent Skills", "LLM"]
description: "Karpathy LLM Wiki 是一个基于 Agent Skills 的知识库管理技能，让 LLM 自动维护 wiki，人类只管阅读和提问。掌握 Ingest/Query/Lint 三大操作，构建个性化知识图谱。"
draft: false
---

# Karpathy LLM Wiki：让AI自动维护你的知识库

## 1. 学习目标

通过本文你将掌握：

- 理解 Karpathy LLM Wiki 的核心哲学
- 熟练使用 Ingest、Query、Lint 三大操作
- 在 Claude Code/Cursor/Codex 中安装和配置本技能
- 构建个人知识库并实现自动维护
- 解决实际使用中的常见问题

## 2. 背景与原理

### 2.1 Karpathy 的 LLM Wiki 理念

2026年4月，AI 大神 Andrej Karpathy 提出了一个简洁而强大的概念：

> **"The LLM writes and maintains the wiki; the human reads and asks questions."**
> （LLM 负责撰写和维护 wiki，人类只管阅读和提问。）

传统知识管理的问题在于：
- 人类需要手动整理、分类、维护大量笔记
- 知识随着时间碎片化，难以检索
- 跨文档的关联和引用难以维护

Karpathy 的解决方案是：**让 LLM 成为知识库的管理者**。人类只需不断向 wiki 注入知识（文档、链接、笔记），LLM 负责：
- 将源材料编译成结构化的 wiki 页面
- 建立文档间的交叉引用
- 维护统一的索引和目录
- 自动检测和修复断链、矛盾等问题

### 2.2 Agent Skills 标准

本技能遵循 [Agent Skills](https://agentskills.io) 开放标准，这是一个跨平台的 LLM Agent 技能规范。只要工具支持 SKILL.md，就能使用本技能。

支持的工具：

| 工具 | 安装方式 |
|------|---------|
| Claude Code | `npx add-skill Astro-Han/karpathy-llm-wiki` |
| Cursor | `npx add-skill Astro-Han/karpathy-llm-wiki` (自动转换) |
| Codex CLI | 复制到 `.agents/skills/karpathy-llm-wiki/` |
| 其他工具 | 复制 SKILL.md + references/ 到技能目录 |

## 3. 技术架构深度解析

### 3.1 目录结构

```
your-project/
├── raw/              ← 不可变源材料（只增不改）
│   └── topic/
│       └── 2026-04-03-source-article.md
├── wiki/              ← 编译后的知识（LLM 维护）
│   ├── topic/
│   │   └── concept-name.md
│   ├── index.md       ← 知识索引（一页目录）
│   └── log.md         ← 操作日志（只增）
└── .agents/
    └── skills/
        └── karpathy-llm-wiki/
            ├── SKILL.md
            └── references/
```

**设计原则：**

1. **raw/ 只增不改**：源材料是不可变的，任何人（包括 LLM）都不能修改 raw/ 中的内容。这确保了知识溯源。
2. **wiki/ 由 LLM 维护**：LLM 负责将 raw/ 中的源材料编译成结构化的 wiki 页面，并维护索引。
3. **日志追踪**：每次操作都记录在 log.md 中，便于回溯。

### 3.2 三大操作详解

#### Ingest（摄入）

**功能**：抓取源材料 → 编译到 wiki → 更新索引和引用

**触发方式**：
```
"Ingest this article: https://example.com/attention-is-all-you-need"
```

**内部流程**：

1. **Fetch**：获取 URL 内容或直接接收文本
2. **Store**：将原始内容存入 `raw/topic/YYYY-MM-DD-source-name.md`
3. **Compile**：LLM 分析源材料，提取关键概念
4. **Link**：建立与现有 wiki 页面的交叉引用
5. **Index**：更新 `wiki/index.md` 索引

#### Query（查询）

**功能**：搜索 wiki 并回答问题，附引用来源

**触发方式**：
```
"What do I know about attention mechanisms?"
```

**内部流程**：

1. **Search**：在 wiki/ 中语义搜索相关页面
2. **Synthesize**：综合多篇文档内容生成答案
3. **Cite**：附上引用链接，指向具体 wiki 页面
4. **Archive**（可选）：将答案存档为新的 wiki 页面

#### Lint（检查）

**功能**：自动修复断链、索引缺口，报告矛盾和孤立页面

**触发方式**：
```
"Lint my wiki"
```

**检查项**：

| 检查项 | 说明 |
|--------|------|
| 断链 | wiki 页面中引用了不存在的页面 |
| 索引缺口 | index.md 中遗漏了某些 wiki 页面 |
| 孤立页面 | 没有被任何页面引用的 wiki 页面 |
| 矛盾内容 | 不同页面中对同一概念的冲突描述 |
| 陈旧内容 | 源材料更新后相关的 wiki 页面未同步 |

### 3.3 Wiki 编译原则

LLM 编译 wiki 时遵循以下原则：

1. **概念优先**：每个概念对应一个 wiki 页面
2. **引用驱动**：页面间通过 `[[WikiLink]]` 互相引用
3. **摘要引导**：每个 wiki 页面以简短摘要开头
4. **溯源可查**：每个知识点都附上源材料引用

## 4. 安装与配置

### 4.1 环境要求

- Node.js >= 18（用于 npx）
- 支持 Agent Skills 的 LLM 编码工具（Claude Code / Cursor / Codex 等）

### 4.2 安装步骤

**Claude Code**：
```bash
npx add-skill Astro-Han/karpathy-llm-wiki
```

**Cursor**：
```bash
npx add-skill Astro-Han/karpathy-llm-wiki
# Cursor 会自动转换 SKILL.md 格式
```

**Codex CLI**：
```bash
# 手动复制技能到对应目录
mkdir -p ~/.agents/skills/karpathy-llm-wiki
git clone https://github.com/Astro-Han/karpathy-llm-wiki.git /tmp/karpathy-llm-wiki
cp /tmp/karpathy-llm-wiki/SKILL.md ~/.agents/skills/karpathy-llm-wiki/
cp -r /tmp/karpathy-llm-wiki/references ~/.agents/skills/karpathy-llm-wiki/
```

### 4.3 初始化项目

在项目根目录执行：
```bash
mkdir -p raw wiki
```

或让 LLM 自动初始化：
```
"Initialize my wiki structure"
```

## 5. 使用指南

### 5.1 摄入新知识

**摄入 URL**：
```
"Ingest this article: https://example.com/attention-is-all-you-need"
```

**摄入本地文件**：
```
"Ingest the paper at ./papers/transformer.pdf"
```

**摄入笔记**：
```
"Ingest my notes about RLHF from today's research session"
```

### 5.2 查询知识

**基础查询**：
```
"What do I know about attention mechanisms?"
```

**带存档的查询**：
```
"Research diffusion models and archive the findings"
```

**跨领域查询**：
```
"How does the attention mechanism relate to my notes on neural networks?"
```

### 5.3 维护 wiki

**健康检查**：
```
"Lint my wiki"
```

**查看索引**：
```
"Show me my wiki index"
```

**查看最近更新**：
```
"Show me my wiki log"
```

## 6. 开发扩展

### 6.1 自定义编译规则

在 `references/` 目录添加自定义模板：

```
references/
├── templates/
│   ├── concept.md      # 概念页模板
│   ├── tutorial.md     # 教程页模板
│   └── reference.md     # 参考页模板
└── rules.md           # 编译规则
```

### 6.2 多语言支持

修改 `references/lang.md` 来自定义术语表和语言风格。

### 6.3 与其他技能集成

本技能可以与以下技能配合使用：

| 配套技能 | 用途 |
|---------|------|
| obsidian-skills | 在 Obsidian 中使用本 wiki |
| deep-research | 自动化资料搜集 |
| memory-skills | 长期记忆管理 |

集成示例：
```
"Research the topic, ingest findings to wiki, then summarize for my memory"
```

## 7. 最佳实践

### 7.1 知识摄入习惯

- **频繁小量**：不要等到积累大量笔记，每学到新概念就立即摄入
- **源材料完整**：尽量摄入原始文档，而非摘要
- **标签规范**：使用一致的主题标签

### 7.2 Wiki 结构管理

- **定期 Lint**：每周执行一次 `Lint my wiki`
- **索引审查**：每月检查 `index.md` 确保结构清晰
- **日志回顾**：定期回顾 `log.md` 了解知识库演进

### 7.3 常见陷阱

| 陷阱 | 避免方法 |
|------|---------|
| 过度依赖 LLM 生成 | 保持 raw/ 的权威性，LLM 只做编译工作 |
| 孤立页面 | Lint 会报告孤立页面，及时建立引用 |
| 概念重复 | 摄入前先 Query，避免重复建页 |

## 8. FAQ

**Q: raw/ 里的文件可以删除吗？**

A: 可以，但不建议。raw/ 是不可变存储，删除后相关的 wiki 引用会变成断链。正确做法是执行 `Lint my wiki` 让 LLM 清理。

**Q: wiki 页面可以手动编辑吗？**

A: 可以，但不推荐。LLM 维护的 wiki 页面有其内部逻辑。如果必须手动编辑，确保遵循 `references/templates/` 中的格式规范，并在 `log.md` 中记录。

**Q: 如何迁移到新工具？**

A: 只需迁移 `raw/`、`wiki/`、`.agents/skills/` 目录，所有数据和配置都在其中。

**Q: 支持离线使用吗？**

A: 支持。本技能完全本地运行，不依赖任何云服务。

**Q: 源材料支持哪些格式？**

A: 支持 Markdown、纯文本、URL（会自动抓取内容）、PDF（需要额外处理）。

## 9. 总结

Karpathy LLM Wiki 技能将知识管理从手工劳动中解放出来，让 AI 成为知识库的管理者。通过 Ingest/Query/Lint 三大操作，我们可以：

- **持续积累**：随时摄入新知识，不用担心碎片化
- **智能检索**：用自然语言查询，附有引用来源
- **自动维护**：LLM 自动修复断链、更新索引、报告问题

核心价值在于：**知识是活的可执行的代码，而非静态的文档库**。

---

*🦞 每日08:00自动更新*
