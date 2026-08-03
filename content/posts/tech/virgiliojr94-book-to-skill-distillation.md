---
title: "book-to-skill：把书/文档蒸馏成可被代理加载的技能"
date: 2026-08-02T02:59:48+08:00
slug: "virgiliojr94-book-to-skill-distillation"
github_repo: "virgiliojr94/book-to-skill"
description: "virgiliojr94/book-to-skill 把 PDF/EPUB/DOCX/MD/HTML/RTF/MOBI 等任意技术书或文档目录蒸馏成符合 Agent Skills 标准的能力包，按章节拆解、按需加载，让代理回答问题时 token 消耗相比\"整本喂入\"降低 24–51 倍。"
draft: false
categories: ["技术笔记"]
tags: ["Agent Skills", "文档蒸馏", "Claude Code", "Copilot CLI", "Amp", "RAG"]
---

## 一句话判断

`virgiliojr94/book-to-skill` 的核心命题是"**不要把书整个塞进上下文**"——它把任意一本书或一份文档目录蒸馏成一个符合 Agent Skills 标准的技能包：保留框架、决策规则、反模式、按章节文件，让代理按需加载相关章节回答问题，相比"整本塞进上下文"的方式**节省 24×–51× tokens**。

## 三步用法

README 把整个流程压成 3 步：

1. **Point** —— 把目录/文件交给它：`/book-to-skill ./my-book.pdf`
2. **Distill** —— 它把书蒸馏成"框架、决策规则、反模式、按章节文件"，是结构，不是摘要
3. **Load on demand** —— 代理按 `/my-book <query>` 调用，按章节加载、按需回答

关键不是"摘要书"，而是"重建书的骨架 + 保留可被定位的章节文件"——这和 RAG 的 chunk 切片有本质差异。

## 关键性能指标

> **24×–51× fewer tokens than dumping the book into context** to answer one question, measured on real books.

仓库提供了完整的 [docs/PERFORMANCE.md](https://github.com/virgiliojr94/book-to-skill/blob/main/docs/PERFORMANCE.md) 和 [docs/ARCHITECTURE.md](https://github.com/virgiliojr94/book-to-skill/blob/main/docs/ARCHITECTURE.md)。架构文档解释为什么"分章节 + 决策规则 + 反模式"的结构对代理比对"chunked text"更有用。

## Discovery Loop Tax

仓库专文讨论 [The Discovery Loop Tax](https://github.com/virgiliojr94/book-to-skill#-the-discovery-loop-tax)——指把书"塞进上下文"再问问题时，代理需要在整个上下文中做近似检索，每次问答都要付一次"全文重读"的税。skill 化后代理只加载相关章节，相当于把税从"每次都付"变成"按需付"。

## 支持格式与代理

| 类别 | 详情 |
|------|------|
| 输入格式 | PDF、EPUB、DOCX、MD、HTML、RTF、MOBI |
| 目标代理 | GitHub Copilot CLI、Amp、Claude Code |
| 标准 | Agent Skills Open Standard |

## 与同类项目的位置

| 项目 | 形态 | 适合 |
|------|------|------|
| `virgiliojr94/book-to-skill` | 整本 → skill | "我想把手上这本手册/参考书交给代理" |
| `emilkowalski/skills` | 主题决策 → skill | "我想让代理在 UI 上更有品味" |
| `NomaDamas/k-skill` | 公共服务 → skill | "我想让代理帮我处理韩国本地生活" |
| `earthtojake/text-to-cad` | 工件格式 → skill | "我想让代理帮我处理 CAD" |

四个仓库加起来基本覆盖了 Agent Skills 这条赛道的四种技能颗粒度。

## 适用边界与不适用边界

**适用**：

- 手上有一本或几本技术参考书（DDD、Designing Data-Intensive Applications、SRE Book 等），希望代理能在工作中按章节调用
- 已经用 Claude Code / Copilot CLI / Amp 之一做开发
- 团队希望把内部 wiki / SOP 文档也用同一套 skill 协议沉淀

**不适用**：

- 非技术书籍（小说、随笔）—— 蒸馏后只剩骨架反而丢失价值
- 强依赖表格、图示、公式的数学书——章节切分后跨章节引用成本高
- 单人 1–2 本小文档的项目——蒸馏的工程开销大于收益

## 一次端到端使用流

1. 你拿到《Designing Data-Intensive Applications》PDF
2. 在代理里输入 `/book-to-skill ./ddia.pdf`
3. 几分钟内得到 `~/.claude/skills/ddia/` 目录，含：
   - `SKILL.md`（总览 + 决策规则）
   - `chapters/01-*.md` 到 `chapters/12-*.md`
   - `antipatterns.md`
4. 之后在代理里输入 `/ddia replication` —— 代理只加载相关章节（latency、consensus、partitioning），回答 token 消耗比"整本 PDF 塞入"低一个数量级
5. 回答里出现具体章节引用，可以直接点回原书核对

这条流程决定了 `book-to-skill` 的真正身份：**把"知识资产"和"代理工作流"用同一个标准接起来**。