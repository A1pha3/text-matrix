---
title: "book-to-skill：把一本书编译成代理按需加载的技能"
date: 2026-08-02T02:59:48+08:00
slug: "virgiliojr94-book-to-skill-distillation"
github_repo: "virgiliojr94/book-to-skill"
source_key: "gh:virgiliojr94/book-to-skill"
description: "virgiliojr94/book-to-skill 用确定性 Python 提取器加规格驱动生成器，把 PDF/EPUB/DOCX 等技术书或文档蒸馏成符合 Agent Skills 标准的技能包：常驻约 4K token 的 SKILL.md 加按需加载的章节文件，回答一个问题的上下文开销比整本塞入低 24–51 倍，转换成本约 1 美元一本。"
draft: false
categories: ["技术笔记"]
tags: ["Agent Skills", "文档蒸馏", "Claude Code", "Copilot CLI", "Amp", "RAG"]
---

## 一句话判断

`virgiliojr94/book-to-skill` 解决的是一个具体的阅读失效：技术书读完一遍，三个月后想不起第 7 章讲过什么。它的做法是把"读懂书的结构"这件事从每次查询挪到转换时一次付清——书的框架、决策规则、反模式被编译进一个技能包，之后代理每次回答只加载相关章节。技能包遵循 Agent Skills 开放标准，Claude Code、GitHub Copilot CLI（命令行工具）等宿主读的是同一份 `SKILL.md`，装一次即可跨宿主使用。官方实测：回答一个定向问题，进入上下文的 token（词元）比整本书塞进去**低 24–51 倍**。

理解这个项目要抓住它的两半架构：**一半是确定性程序，一半是代理本身**。

## 系统地图：两半架构

| 阶段 | 执行者 | 做什么 | 产出 |
|------|--------|--------|------|
| 提取 | Python（确定性代码） | 逐格式选最佳工具解析文档，剥离隐形字符 | 干净全文 + `metadata.json`（页数、词数、章节、ToC） |
| 生成 | 代理（执行 `SKILL.md` 规格的 Steps 0–10） | 分析结构，按预算给每章写摘要，汇总术语/模式/速查表 | `SKILL.md` + `chapters/` + 三个辅助文件 |
| 查询 | 代理 | 常驻核心约 4K token，按问题加载单个章节文件 | 答案基于对应章节的真实内容 |

提取器（`book_to_skill/` 包）没有任何智能：它按格式挑工具——PDF 走 `pdftotext` 或 `pypdf`，EPUB 走 `ebooklib`，DOCX 走 `python-docx`——每个格式都有标准库兜底，单个源文件损坏只跳过不中断。生成器则不是代码：仓库根目录那份 `SKILL.md` 是一份分步规格，由 Claude Code、Copilot CLI 这类代理读着执行，先问这本书是技术型还是文字型（决定深度预算），再决定产出是 reference 档还是 study 档。**书的结构由作者写好了，提取器负责不弄丢它，代理负责把它重组为技能。**

生成物的体积是刻意设计的：

| 文件 | 内容 | 体积 |
|------|------|------|
| `SKILL.md` | 核心心智模型 + 章节索引 | ~4,000 token |
| `chapters/ch01-*.md` … | 每章一个文件，问到了才加载 | ~1,000 token/章 |
| `glossary.md` | 术语表，带章节引用 | ~1,500 token |
| `patterns.md` | 技巧、算法、设计模式 | ~2,000 token |
| `cheatsheet.md` | 决策表和速查规则 | ~1,000 token |

章节文件不加载就不计 token。`SKILL.md` 把最重要的内容放最前——上下文压缩从尾部截断，头部的内容活到最后。

## 为什么不是"整本塞进去"，也不是 RAG（检索增强生成）

README 专设一节讲 [The Discovery Loop Tax](https://github.com/virgiliojr94/book-to-skill#-the-discovery-loop-tax)，它指的不是"代理读了全书"这一种浪费，而是更隐蔽的一种：读 PDF 的代理不是在读，是在**导航**——重新拉目录、来回翻页、每一轮对话都把这套流程重做一遍。就算代理足够聪明，用 `grep` 在全文里检索，这个按轮次重复的导航成本也省不掉。book-to-skill 把这份结构化成本在转换时一次付清，之后查询成本只和答案相关。

这和 RAG 的 chunk 切片是两种思路。chunk 把书切成无语义边界的碎片，检索回来的是"可能含答案的段落"，书的章节组织被丢掉了；book-to-skill 保留作者写书时的知识结构——章节就是现成的语义边界，提取的是命名框架、决策规则、反模式，按 README 的说法是"Structure, not a summary"（是结构，不是摘要），并明确绝不复制原文段落。

## 24×–51× 是怎么测出来的

这组数字回答三个问题后才值得引用。

**测的是什么**：回答一个定向问题时进入上下文的 token 数，用 `tiktoken`（cl100k_base）计数，工具 `tools/discovery_tax.py` 可复现。三个基准对照：

| 书（章节粒度） | 整本塞入 | 导航式读 PDF | book-to-skill | 对塞入 / 对导航 |
|----------------|---------:|-------------:|--------------:|:--------------:|
| Think Python 2（小章节） | 119,264 | 12,152 | ~5,000 | 24× / 2.4× |
| Working Backwards（中） | 175,253 | 33,444 | ~5,000 | 35× / 6.7× |
| AI Engineering（大章节） | 256,287 | 77,866 | ~5,000 | 51× / 15.6× |

**数字反映什么**：常驻 ~4K 核心加一个 ~1K 章节，约 5,000 token 是固定值；变化全在对照组。"整本塞入"的账最好算——这笔钱**每轮对话都重付一次**；对导航式读法（代理按真实 ToC 和章节大小定位）的 2.4–15.6 倍才是与"会用工具的代理"的公平比较，差距来自章节文件按需加载替代了每轮重新导航，章节越大优势越大。

**不能推出什么**：这组数字不保证回答质量，只度量上下文开销；样本是四本结构规整的书（前三本加 301K token、自动分出 133 章的 Moby-Dick），Pro Git 这种用小节标题代替"Chapter N"标头的书无法自动分章——章节检测成功率直接决定这套收益能否兑现。另有作者声称回答"来自真实内容，无幻觉"，这是设计目标，不是这组数据能验证的结论。

转换本身也要花钱，但只付一次。按 Claude Sonnet 4.5 定价（$3/$15 每百万 token）估算：Think Python 2 约 $0.88，Working Backwards 约 $0.96，Pro Git 约 $1.23，Moby-Dick 约 $1.42——**一本约 1 美元**，对比每个会话重读一遍 PDF 的累积开销。

## 端到端：一本书怎么变成技能

以《Designing Data-Intensive Applications》为例，走一遍完整路径：

1. 装转换器：`npx skills add virgiliojr94/book-to-skill`（或克隆 clone 到对应宿主的技能目录）
2. 转换：`/book-to-skill ~/books/ddia.pdf`——也接受文件夹、glob 或文件列表，可以把整个 `docs/` 目录合并成一个技能
3. 提取器产出全文和元数据后，代理会先问这本书偏技术还是偏文字：技术书值得等 Docling 慢慢解析（下详），纯文字书用 `pdftotext` 立刻完成
4. 生成技能写入跨代理目录 `~/.agents/skills/designing-data-intensive-apps/`；在 Claude Code 下还会尝试建立到 `~/.claude/skills/` 的验证软链
5. 之后 `/designing-data-intensive-apps replication` 让代理只加载复制那一章来回答；问"第 5 章讲了什么"或"有哪些章节"，代理按 `SKILL.md` 里的章节索引定位到对应文件，只读那一份

宿主识别有差异：手动 clone 到 Copilot CLI 的技能目录后，需要在该会话里跑一次 `/skills reload`；Claude Code 会在下次会话自动识别，无需手动刷新。转换结束后转换器还会提议把技能发布成 GitHub 私有仓库，任何 Agent Skills 宿主用 `npx skills add` 一条命令安装。

## 提取环节的取舍

性能文档里一组对比值得单独看——同一本 103 页的技术 PDF：

| 方法 | 耗时 | 表格保留 | 代码块保留 |
|------|-----:|---------:|-----------:|
| `pdftotext` | 0.1s | 0 | 0 |
| Docling（技术模式） | 164s | 48 | 36 |

`pdftotext` 瞬间完成但把表格和代码全部压平；Docling 约 1.5 秒一页，换来表格和代码以 Markdown 原样保留。转换流程会先问你书的类型再自动选工具——含代码和表格的技术书选错工具，后面的蒸馏全在残缺文本上进行。

## 适用与不适用

**适用**：

- 反复查阅的技术参考书：DDD、《DDIA》、SRE 手册这类"工作中想按章节调用"的书
- 不止是书：内部 `docs/` 文件夹、ADR（架构决策记录）、runbook、品牌与设计规范、论文堆、RFC——README 的说法是"凡是常打开到恨不得背下来的文档，都是候选"
- 已经在用 GitHub Copilot CLI、Amp、Claude Code、Hermes Agent、OpenClaw 之一的开发者，五个宿主读同一份 `SKILL.md` 格式

**不适用**：

- 扫描版、拍照版 PDF：没有文本层，提取器检查前几页会立即中止（这是 PR #130 修的行为），需要先自己跑 `ocrmypdf`
- 没有 "Chapter N" 标头的书：Pro Git 用小节标题当章头，无法自动分章
- 小说、随笔：骨架蒸馏后剩下的东西撑不起原书的价值
- 只查一两次的文档：约 1 美元加整套转换流程的固定开销，不如直接问

**版权红线**：仓库不随附任何书的内容，处理全部在本地完成；生成物被定位为"结构化笔记"而非原文复制品（生成规格明确禁止复制原文段落）。第三方版权书生成的技能必须保持私有——发布流程默认建私有仓库，只有你明确回答 `public` 才会公开。

这个项目对"不可信文档"的防御也做到了工程层：提取时剥离零宽字符和 Unicode 标签区段的隐形注入指令，DOCX 解析拒绝带 DTD 声明的 XML，生成完成后还有一个对产出技能的提示注入扫描。一份文档会流进代理上下文、再固化成技能装进其他代理——这是一条文档到上下文的供应链，作者按供应链的标准做了加固。

## 在 Agent Skills 生态里的位置

以下是 2026-08 撰写时的生态快照。book-to-skill 是 MIT 协议，2026-05-01 建仓，本文核对时 v1.4.0、32.8K stars：

| 项目 | 技能颗粒度 | 适合 |
|------|-----------|------|
| `virgiliojr94/book-to-skill`（32.8K stars） | 整本书/文档集 → 技能 | 把手上这本参考书交给代理 |
| `emilkowalski/skills`（41.5K stars） | 主题决策 → 技能 | 让代理在 UI 上更有品味 |
| `earthtojake/text-to-cad`（16.4K stars） | 工件格式 → 技能 | 让代理产出 CAD/CAE/CAM 文件 |
| `NomaDamas/k-skill`（7.7K stars） | 公共服务 → 技能 | 让代理处理韩国本地生活 |

四个仓库正好覆盖 Agent Skills 赛道的四种颗粒度，book-to-skill 占的是最大也最重的那种：输入是整本书，所以它的全部工程都花在两件事上——转换时别弄丢结构，查询时别多付一个 token。

**采用顺序**：先装转换器，挑一本你最近真的翻过三次以上的书试水；含代码或表格的书等 Docling 跑完再确认章节质量（用 `what chapters do you have?` 检查分章）；满意后把团队内部文档用同一条管线沉淀成私有技能。只查一两次的文档、没有文本层的扫描件，都不必进这条流水线。

## 延伸阅读

- [The Discovery Loop Tax（README）](https://github.com/virgiliojr94/book-to-skill#-the-discovery-loop-tax)：导航式读 PDF 的隐性成本，本文 benchmark 的原始出处
- [docs/performance.md](https://github.com/virgiliojr94/book-to-skill/blob/master/docs/performance.md)：token 计数的完整方法、四本书的逐表数据与 `tools/discovery_tax.py` 复现命令
- [docs/how-it-works.md](https://github.com/virgiliojr94/book-to-skill/blob/master/docs/how-it-works.md)：Steps 0–10 的完整生成流程与提取/生成基准
- [docs/architecture.md](https://github.com/virgiliojr94/book-to-skill/blob/master/docs/architecture.md)：管线组件图与安全加固层（零宽字符剥离、DOCX DTD 防护、生成技能扫描）
- [docs/usage.md](https://github.com/virgiliojr94/book-to-skill/blob/master/docs/usage.md)：全部运行模式（analyze-only、generate-from-analysis、update/fold-in）与示例
