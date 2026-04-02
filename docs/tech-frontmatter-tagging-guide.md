---
title: "技术文章 Front Matter 模板与标签规范"
date: 2026-04-01T13:00:00+08:00
draft: false
tags: ["Hugo", "Front Matter", "标签治理", "内容规范", "技术写作"]
categories: ["系统基建"]
---

> **🎯 学习目标**
>
> 读完本文，你将了解：
>
> 1. 技术文章的 Front Matter 应该如何标准化书写。
> 2. `categories`、`tags`、`series` 分别承担什么职责。
> 3. 标签应该如何命名，才能避免后期聚合碎片化。
> 4. 如何创建符合当前站点约定的新技术文章。

本文档用于补齐 `content/posts/tech/` 的日常写作规范，帮助后续新增文章在元数据层面保持一致，减少“目录在长大、规则却在变乱”的问题。

---

## 1. 技术文章的标准 Front Matter

技术文章统一使用以下字段：

- `title`
- `date`
- `slug`
- `description`
- `draft`
- `categories`
- `tags`

推荐模板如下：

```yaml
---
title: "文章标题"
date: 2026-04-01T13:00:00+08:00
slug: "article-slug"
description: "用 50 到 100 字概括文章核心问题、解决方案与阅读收益。"
draft: true
categories: ["技术笔记"]
tags: ["Python", "AI Agent", "向量数据库"]
---
```

如果文章属于连续教程或专题连载，可额外增加：

```yaml
series: "系列名称"
```

当前站点尚未正式把 `series` 做成导航入口，因此默认不强制；只有在确实存在连续关系时才添加。

---

## 2. 字段职责与填写规则

### 2.1 `categories`

技术文章统一使用：

```yaml
categories: ["技术笔记"]
```

原因很简单：分类用于表达**内容体裁**，而不是表达主题域。不要把 `AI`、`Python`、`量化交易` 放进分类中，否则会和目录、标签形成重复建模。

### 2.2 `tags`

标签用于表达**具体技术实体与主题**，例如：

- 技术语言：`Python`
- 框架或工具：`LangChain`、`Docker`
- 产品或协议：`Claude`、`MCP`
- 领域词：`量化交易`、`向量数据库`

单篇技术文章建议控制在 **2 到 5 个标签**。如果超过这个范围，通常说明标签粒度不一致，或者把摘要信息错误地写进了标签。

### 2.3 `series`

`series` 只用于以下场景：

- 教程有前后章节
- 某一主题存在连续更新
- 需要表达明确的阅读顺序

如果只是同主题下的普通文章集合，优先用 `tags`，不要滥用 `series`。

### 2.4 `slug`

`slug` 使用小写英文和连字符，避免中文、空格和特殊字符。

推荐写法：

- `agentscope-ai-agent-framework`
- `python-vector-database-guide`
- `quant-trading-backtest-intro`

### 2.5 `description`

`description` 不要重复标题，而要概括：

1. 文章解决什么问题
2. 覆盖哪些核心内容
3. 读者读完能获得什么

建议长度控制在 **50 到 100 字**。

---

## 3. 标签命名规范

标签膨胀最常见的原因，不是标签太少，而是命名不统一。为了避免将来出现大量碎片化聚合页，建议遵循以下规则。

### 3.1 优先使用稳定、具体的名词

推荐：

- `Python`
- `AI Agent`
- `Claude`
- `量化交易`
- `向量数据库`

不推荐：

- `编程`
- `智能`
- `工程实践`
- `技术学习`

### 3.2 同义词只保留一个标准名

| 分散写法 | 统一写法 |
| --- | --- |
| `python` / `Python3` | `Python` |
| `AI agent` / `Agents` | `AI Agent` |
| `向量库` / `Vector DB` | `向量数据库` |

### 3.3 中英文策略保持一致

建议优先采用当前站点已较稳定的展示形式：

- 国际通用产品名或协议名，直接保留英文或官方写法
- 中文领域词，优先保留中文
- 不要对同一概念同时使用中文和英文两个标签

例如：

- 用 `Claude`，不要同时再加 `克劳德`
- 用 `量化交易`，不要再同时加 `Quant Trading`

### 3.4 不把层级关系写进标签

错误示例：

- `AI`
- `AI Agent`
- `AI Agent 框架`
- `AI Agent 开发`

如果一篇文章同时使用这 4 个标签，聚合意义会严重重叠。更好的做法是只保留最能描述文章主题的 2 到 5 个标签。

---

## 4. 推荐的稳定子域

`tech` 目录后续优先围绕以下稳定主题扩展：

- `ai-agent`
- `llm`
- `tools`
- `quant`

补充一条归类规则：**凡与 `Claude` 直接相关的文章，统一归入 `ai-agent`。** 这类内容即使带有明显的编码工具、CLI、API、课程、工作流或工具属性，也优先按 AI Agent 主题归档。

再补充两条归类规则：

- `Claude` 相关内容统一归入 `ai-agent`
- BI、OCR、结构化处理与通用开发工具类内容优先归入 `tools`

是否值得为某个主题新建子目录，可以用以下标准判断：

1. 主题未来一年仍会持续产出
2. 该主题预期累计文章数不少于 10 篇
3. 主题名称稳定，不会频繁改名

如果还达不到这个阈值，就先用标签承接，不急着开新目录。

---

## 5. 新文章创建方式

推荐使用专门的 archetype 创建技术文章：

```bash
/Volumes/mini_matrix/github/a1pha3/web/hugo/hugo new --kind tech content/posts/tech/ai-agent/example.md
```

如果文章暂时没有明确子域，也可以先创建在：

```bash
/Volumes/mini_matrix/github/a1pha3/web/hugo/hugo new --kind tech content/posts/tech/example.md
```

创建后，请重点检查以下 4 项：

1. `categories` 是否固定为 `["技术笔记"]`
2. `tags` 是否为 2 到 5 个具体名词
3. `slug` 是否简洁稳定
4. `description` 是否真正概括文章内容

---

## 6. 发布前检查清单

每篇技术文章发布前，建议至少检查以下内容：

- 标题是否清晰表达主题
- `slug` 是否稳定且可读
- `description` 是否不是标题复述
- `categories` 是否只有 `["技术笔记"]`
- `tags` 是否命名统一、数量合理
- 如果是迁移旧文，是否补了 `aliases`

---

## 7. 一句话规则

对于 `content/posts/tech/`，最重要的不是“多写几个标签”，而是：**用稳定目录控制编辑端，用固定分类控制体裁边界，用受控标签控制检索质量。**
