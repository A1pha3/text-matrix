---
title: "Karpathy LLM Wiki：把知识库交给 AI 维护"
slug: "karpathy-llm-wiki-agent-skill-guide"
date: "2026-04-08T11:10:00+08:00"
lastmod: 2026-04-08T11:10:00+08:00
categories: ["技术笔记"]
tags: ["AI", "知识管理", "Wiki", "Agent Skills", "LLM"]
description: "Karpathy 提出的 LLM Wiki 理念：人类只管阅读和提问，LLM 负责撰写、编目和修复。本文拆解其社区实现，覆盖 Ingest/Query/Lint 三条主线的运转方式和落地的坑。"
draft: false
---

# Karpathy LLM Wiki：把知识库交给 AI 维护

2026 年 4 月，Andrej Karpathy 扔出一个简短但方向明确的主张：

> **"The LLM writes and maintains the wiki; the human reads and asks questions."**
> （LLM 负责撰写和维护 wiki，人类只管阅读和提问。）

这句话戳中的不是技术难度，而是知识管理里的一个死循环：人类负责记录 → 人类负责整理 → 人类负责检索 → 然后没时间了。LLM Wiki 的思路是把「维护」这件事从人类身上剥离出去，只剩两件事——往里扔材料，和向它提问。

下面拆解的并非 Karpathy 本人发布的成品，而是社区基于他的理念实现的 Agent Skill：[Astro-Han/karpathy-llm-wiki](https://github.com/Astro-Han/karpathy-llm-wiki)。它遵循 [Agent Skills](https://agentskills.io) 开放标准，可以在 Claude Code、Cursor、Codex CLI 等支持 SKILL.md 的工具中直接安装。

## 一张图看清这套系统

先不急着看目录结构。从「一次知识摄入」的视角看，整个系统只有三条主线，各走各的路：

| 主线 | 谁触发 | 做什么 | 产物 |
|------|--------|--------|------|
| **Ingest** | 你说「摄入这篇文章」 | 抓取原文 → 存入 raw/ → 编译为 wiki 页面 → 更新索引 | wiki 新页面 + 更新后的 index.md |
| **Query** | 你问「我对 X 了解多少」 | 搜索 wiki/ → 综合多页面 → 附引用回答 | 带引用的答案（可存档） |
| **Lint** | 你说「检查我的 wiki」 | 扫描断链、索引缺口、孤立页面、矛盾内容 | 修复报告，自动修复可修项 |

这三条线共享 `raw/`（不可变源材料区）和 `wiki/`（LLM 维护的知识区），但它们的触发场景和产出完全不同。先记住这个对照关系，后面看目录结构和操作细节时就不会混在一起了。

## 1. 学完你能做什么

读完这篇文章并跟着操作一遍之后，你应该能做到：

- 在 Claude Code 或 Cursor 中装好 karpathy-llm-wiki 技能
- 用 `Ingest` 命令从 URL 或本地文件向 wiki 注入知识
- 用 `Query` 自然语言搜索知识库，并能把查询结果存档
- 用 `Lint` 定期检查 wiki 健康状态
- 判断自己的使用场景适不适合这套方案，以及从哪一步开始

## 2. 目录结构与设计约束

整个项目只有两个核心目录，其余的 `.agents/skills/` 放的是技能定义文件本身：

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

三条硬约束决定了这个结构的可靠性：

1. **raw/ 只增不改**——源材料一旦写入就不再修改。这保证了任何 wiki 页面的结论都能追溯到原始材料，而不是 LLM 的二次加工。
2. **wiki/ 完全由 LLM 维护**——人类不直接编辑 wiki 下的任何文件；所有变更都通过 Ingest 或 Lint 触发，由 LLM 执行。这避免了人类手动改 wiki 后与索引脱节。
3. **log.md 只追加**——每次操作写一行日志，不覆写历史。出了问题时，回看 log 比猜 LLM 做了什么更靠谱。

## 3. 三条主线拆开看

### 3.1 Ingest（摄入）：从原始材料到可检索的知识

Ingest 是使用频率最高的命令。你给 LLM 一个 URL 或一段文本，它完成五步：

1. **Fetch**：获取 URL 内容或接收你直接粘贴的文本
2. **Store**：原始内容写入 `raw/topic/YYYY-MM-DD-source-name.md`
3. **Compile**：LLM 分析源材料，提取核心概念，生成 wiki 页面
4. **Link**：扫描现有 wiki，建立交叉引用（用 `[[WikiLink]]` 语法）
5. **Index**：更新 `wiki/index.md`，把新页面挂到索引树上

触发示例：

```
"Ingest this article: https://example.com/attention-is-all-you-need"
"Ingest the paper at ./papers/transformer.pdf"
"Ingest my notes about RLHF from today's research session"
```

编译 wiki 页面时 LLM 遵循几条内部规则：一个概念对应一个页面；每个页面以一段摘要开头；每条结论都附源材料引用；页面之间通过双向链接互相引用。这些规则的目的不是形式规范，而是让后续 Query 能准确命中，让 Lint 有据可查。

### 3.2 Query（查询）：问你的知识库，而不是搜文件名

Query 不是 grep，也不是全文搜索。它用语义搜索匹配 wiki 内容，然后综合多个页面生成答案。

一次 Query 的执行路径：

- `"What do I know about attention mechanisms?"`
  → 语义搜索 wiki/ 中所有相关页面
  → 综合多个页面的内容生成答案
  → 每条结论附上来源页面的引用链接
  → 如果加了 `"archive the findings"`，答案会被写成一个新的 wiki 页面

支持的模式：

```
"What do I know about attention mechanisms?"
"Research diffusion models and archive the findings"
"How does the attention mechanism relate to my notes on neural networks?"
```

最后那条跨领域查询才是这套系统真正的价值点——传统笔记工具很难回答「A 和 B 之间有什么关联」这种问题，但 LLM 在综合多个 wiki 页面时可以做到。

### 3.3 Lint（检查）：自动化 wiki 健康检查

Lint 是维护命令，触发方式就是一句话：

```
"Lint my wiki"
```

它扫描五类问题：

| 检查项 | 实际问题 | 自动修复 |
|--------|---------|---------|
| 断链 | wiki 页面引用了不存在的页面 | ✅ 移除或替换为有效链接 |
| 索引缺口 | index.md 遗漏了某些 wiki 页面 | ✅ 补入索引 |
| 孤立页面 | 没有被任何页面引用的 wiki 页面 | ⚠️ 报告并建议关联 |
| 矛盾内容 | 不同页面中对同一概念描述冲突 | ⚠️ 报告，需人类确认 |
| 陈旧内容 | 源材料更新后 wiki 页面未同步 | ⚠️ 报告，需重新 Ingest |

前两项 LLM 可以直接修；后三项需要你判断。建议每周跑一次 Lint——不需要记在日历里，把它挂到你的 AI 编码工具的自动化规则里就行。

## 4. 一个完整任务怎么流过系统

假设你在研究 Transformer 架构，走了下面这轮操作：

**第一步：摄入论文**

```
"Ingest this paper: https://arxiv.org/abs/1706.03762"
```

系统做的事：抓取论文 → 存入 `raw/transformer/2026-04-03-attention-is-all-you-need.md` → 提取 Self-Attention、Multi-Head Attention、Positional Encoding 等概念，为每个概念创建 `wiki/transformer/self-attention.md` 等页面 → 在页面间建立 `[[Multi-Head Attention]]` 这类交叉引用 → 更新 `wiki/index.md`。

**第二步：摄入一篇解读文章**

```
"Ingest this article: https://example.com/transformer-explained"
```

系统做的事：存入 raw/ → 发现这篇文章讨论了 Self-Attention 的计算复杂度，于是**更新**（而非覆盖）`wiki/transformer/self-attention.md`，追加复杂度分析段落，保留之前的引用来源。

**第三步：查询**

```
"How does self-attention compare to RNNs?"
```

系统做的事：搜索 wiki/ 中 Self-Attention 和 RNN（循环神经网络）相关页面 → 综合信息生成对比答案，每条结论附引用链接。

**第四步：存档查询结果**

```
"Archive that comparison to my wiki"
```

系统做的事：把刚才生成的对比答案写成 `wiki/transformer/self-attention-vs-rnn.md`，更新 index.md。

**第五步：健康检查**

```
"Lint my wiki"
```

系统做的事：检查有没有断链（比如引用了尚不存在的 `[[Cross-Attention]]`）、确认所有页面都在索引中、报告孤立页面。

这五步走完，你的 wiki 里多了一个概念簇（Self-Attention、Multi-Head Attention、对比页面），每个页面都可追溯到原始论文或解读文章，索引自洽，引用完整。

## 5. 安装与环境

**环境要求**：Node.js >= 18（用于 npx），以及一个支持 Agent Skills 的 AI 编码工具。

**Claude Code**：

```bash
npx add-skill Astro-Han/karpathy-llm-wiki
```

**Cursor**：

```bash
npx add-skill Astro-Han/karpathy-llm-wiki
# Cursor 会自动转换 SKILL.md 格式
```

**Codex CLI**：手动复制到技能目录：

```bash
mkdir -p ~/.agents/skills/karpathy-llm-wiki
git clone https://github.com/Astro-Han/karpathy-llm-wiki.git /tmp/karpathy-llm-wiki
cp /tmp/karpathy-llm-wiki/SKILL.md ~/.agents/skills/karpathy-llm-wiki/
cp -r /tmp/karpathy-llm-wiki/references ~/.agents/skills/karpathy-llm-wiki/
```

**其他工具**：把 `SKILL.md` 和 `references/` 复制到该工具的技能目录即可。

安装后在项目根目录初始化：

```bash
mkdir -p raw wiki
```

或者直接让 LLM 做：

```
"Initialize my wiki structure"
```

## 6. 扩展方向

### 6.1 自定义编译规则

在 `references/` 下添加模板和规则文件，可以控制 LLM 生成 wiki 页面的格式：

```
references/
├── templates/
│   ├── concept.md      # 概念页模板
│   ├── tutorial.md     # 教程页模板
│   └── reference.md    # 参考页模板
└── rules.md           # 编译规则
```

### 6.2 多语言

修改 `references/lang.md` 可以定义术语表和目标语言风格。如果你的源材料混用中英文，这一步很值得做——LLM 会在编译时统一术语。

### 6.3 与其他技能联动

这套技能可以和几个常用技能形成工作流：

| 配套技能 | 接入方式 |
|---------|---------|
| obsidian-skills | 在 Obsidian 中直接以 wiki 目录为 vault |
| deep-research | 研究结果直接 Ingest 到 wiki |
| memory-skills | wiki 作为长期记忆的外部存储 |

一个组合命令的例子：

```
"Research the topic, ingest findings to wiki, then summarize for my memory"
```

## 7. 使用节奏与常见坑

### 什么时候摄入

每学到一个新概念就立刻 Ingest，不要攒。攒到 50 篇再一起摄入，LLM 面临的交叉引用复杂度是指数级的，反而容易出错。小量高频是最稳的策略。

尽量摄入原始文档而不是别人的摘要。LLM 从原文提取概念和从二手摘要里提取概念，准确度差别很大——这个差异会随着 wiki 增长被逐步放大。

### Lint 频率

每周一次 `Lint my wiki`。你可以把它写进 Claude Code 的 CLAUDE.md 规则里，让它在合适的时机自动触发。

### 三个容易踩的坑

**坑 1：手动改 wiki 页面**

wiki 目录下的文件由 LLM 维护，有它自己的内部引用逻辑。如果你手动编辑了某个页面，下次 Lint 或 Ingest 可能会因为格式不一致而产生误报。必须手动改的话，先在 `log.md` 里记一笔，回头出问题至少有线索。

**坑 2：raw/ 里堆积了没用的材料**

raw/ 设计上是只增不改的，但这不代表什么都要往里扔。如果你 Ingest 了一篇后来发现质量很差的文章，正确的处理方式不是删 raw/ 里的文件——那会让引用它的 wiki 页面出现断链——而是跑一次 `Lint my wiki`，让 LLM 检测到陈旧或低质量引用后重新处理。

**坑 3：概念页面重复建立**

摄入前先 Query 一下。如果你已经有一页关于 Attention 的 wiki 页面，再摄入一篇注意力机制的文章时，LLM 会尝试更新已有页面而不是新建——前提是你摄入了**原文**而非高度重叠的摘要。如果摄入的是别人写的 Attention 总结，LLM 可能判断为「另一个视角的新材料」而创建新页面，导致概念分裂。

## 8. FAQ

**Q: raw/ 里的文件可以删除吗？**

A: 技术上可以，但 wiki 中所有引用该源材料的页面会变成断链。如果要清理，先跑 `Lint my wiki`，让 LLM 处理后事。

**Q: wiki 页面可以手动编辑吗？**

A: 能，但不建议。LLM 维护的 wiki 页面有内部引用一致性约束。一定要手动改的话，参考 `references/templates/` 里的格式规范，并在 `log.md` 里记录。

**Q: 怎么迁移到另一个工具？**

A: 复制 `raw/`、`wiki/`、`.agents/skills/` 三个目录即可。所有数据和配置都在里面，不依赖工具外部存储。

**Q: 支持离线吗？**

A: 支持。这个技能完全本地运行，不依赖任何云服务。当然，抓取 URL 内容时需要网络。

**Q: 源材料支持哪些格式？**

A: Markdown、纯文本、URL（自动抓取网页内容）。PDF 需要额外的提取步骤。

## 9. 自测：判断你是不是用对了

不看你装没装好，看这几件事：

1. 用 `"What do I know about X?"` 问一个你确实摄入过的概念，回答有没有附带引用来源？
2. 跑 `"Lint my wiki"`，有没有报断链或孤立页面？有的话修掉。
3. 打开 `wiki/index.md`，索引的层级能让你在 10 秒内找到你想找的概念吗？
4. 连续摄入 3 篇主题相近的文章后，LLM 是更新了已有页面还是新建了重复页面？

第 4 条如果答案是「新建了重复页面」，说明你摄入的材料粒度太粗——试试直接用原文而非二手摘要。

## 10. 这套方案适合你吗（以及从哪开始）

LLM Wiki 不是所有人的默认答案。它最适合的场景是：

- 你在持续研究一个领域（ML、系统设计、安全），需要频繁摄入新论文和文章
- 你发现自己的笔记已经多到「只有写了才安心、但从不回看」的程度
- 你已经在用 Claude Code 或 Cursor 作为主力编码工具

不那么适合的场景：

- 你只需要一个个人备忘录，偶尔记几笔——Notion 或 Apple Notes 足够
- 你的知识管理以项目文档为主，而非跨项目概念关联——普通 Markdown + 目录树更直接
- 你对 LLM 生成的内容有严格的审计要求——raw/ 虽然保留原文，但 wiki 页面本身是 LLM 编译的

如果决定用，建议的启动顺序：

1. 先装好技能，跑 `"Initialize my wiki structure"`
2. 先摄入 3 篇你最熟悉的文章，跑 Query 看结果质量
3. 确认满意后，再逐步把存量笔记摄入进去
4. 第一周每天跑一次 Lint，熟悉常见的健康问题类型
5. 稳定后每周一次 Lint 即可

把 LLM Wiki 当成一个持续生长的知识图谱而非一次性交付的文档库，它的价值会随使用时间递增。

---

*🦞 每日 08:00 自动更新*