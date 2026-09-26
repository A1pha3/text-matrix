---
title: "paper2code 拆解：论文复现的可信度被做成标注协议，核对责任仍留给人"
date: "2026-05-11T17:50:00+08:00"
lastmod: "2026-09-26T05:58:01+08:00"
slug: "paper2code-ai-arxiv-paper-implementation"
github_repo: "PrathamLearnsToCode/paper2code"
source_key: "gh:PrathamLearnsToCode/paper2code"
description: "逐行核查 PrathamLearnsToCode/paper2code：五个阶段的流水线、39 项模糊审计清单、六个出处标签如何在代码里锚定论文；实测两个范例输出的可运行性，并复算出三处论文引文与出处标签的错误。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Claude Code", "机器学习", "代码生成", "论文复现"]
hiddenFromHomePage: true
---

paper2code 把"这段代码是不是论文里说的"从结论问题改成了逐行可查的标注问题：五个阶段的流水线、39 项模糊审计清单、六个出处标签，加上一份禁止"凭常识填空"的护栏文本。这套机制是真实存在的——仓库 8,876 行里 3,939 行是写给模型读的说明文，两个范例输出能在 CPU 上跑通。

它的强度也到此为止。锚点本身没有机器校验：仓库里只有一份人工 review 和两个范例目录。按 README 给的步骤实测，三处被引号标注成"论文原句"的文本在论文全文里检索不到，其中一处超参数值连方向都是反的。缺陷都不在代码路径上，却正好落在它承诺"可以验证"的那一层。

## 目录

- [这套技能把信任问题挪到了哪一层](#这套技能把信任问题挪到了哪一层)
- [仓库地图：8,876 行里只有 771 行是脚本](#仓库地图8876-行里只有-771-行是脚本)
- [一次真实调用：从 arXiv 编号到结构化文本](#一次真实调用从-arxiv-编号到结构化文本)
- [结构化抽取交出的清单，比协议假定的薄](#结构化抽取交出的清单比协议假定的薄)
- [标签系统：六个在册，一个野生](#标签系统六个在册一个野生)
- [39 项审计清单和它的裁决顺序](#39-项审计清单和它的裁决顺序)
- [生成的代码确实跑得起来](#生成的代码确实跑得起来)
- [三处引用锚点经核查不成立](#三处引用锚点经核查不成立)
- [出处标签在两份文档里互相矛盾](#出处标签在两份文档里互相矛盾)
- [仓库自己登记的缺陷，实测复现](#仓库自己登记的缺陷实测复现)
- [谁该用，谁不该用](#谁该用谁不该用)
- [怎么自己复算本文的结论](#怎么自己复算本文的结论)
- [常见问题](#常见问题)
- [五个自测题](#五个自测题)
- [三个练习](#三个练习)
- [下一步读哪份文件](#下一步读哪份文件)
- [参考文献](#参考文献)

## 这套技能把信任问题挪到了哪一层

[仓库](https://github.com/PrathamLearnsToCode/paper2code)的 README 在 `Why this exists` 一节给出的诊断，值得逐字读一遍：

```text
Naive code generation fills in every gap silently and confidently. You get
something that runs but doesn't match the paper. Worse, you can't tell which
parts are from the paper and which were invented by the model.
```

它对应的中文意思是：朴素的代码生成会静默而自信地填掉所有空白，产出的东西能跑但不对应论文，更难办的是分不清哪些来自论文、哪些是模型编的。针对这个诊断，README 列出四条主张：引用锚定（Citation Anchoring）、模糊审计（Ambiguity Auditing）、诚实不确定性（Honest Uncertainty）、附录挖掘（Appendix Mining）。

四条的共同点是都不承诺"更正确"，只承诺"更可查"。区别在于落地形态：引用锚定与诚实不确定性落在代码注释里，模糊审计落在流水线第三阶段产出的一份审计文件里，附录挖掘落在采集脚本和检索清单里。把这个分层看清楚，后面的强弱对比才有落点。

一个常被忽略的事实：README 开篇并不是这段诊断，而是一行标语 `arxiv URL in → citation-anchored implementation out`，诊断在第三节。引用它的时候位置要写对。

## 仓库地图：8,876 行里只有 771 行是脚本

`git ls-files` 给出 49 个跟踪文件，扩展名分布是 22 个 `.md`、19 个 `.py`、3 个 `.yaml`、2 个 `.txt`、2 个 `.ipynb`，外加一份 MIT 许可证。按目录统计行数和文件数：

| 目录 | 行数 | 文件数 | 承担什么 |
|---|---|---|---|
| `worked/` | 4,102 | 24 | 两篇论文的完整范例输出，含人工 review |
| `knowledge/` | 1,227 | 4 | 领域知识：Transformer 架构组件、损失函数、训练配方、踩坑对照 |
| `pipeline/` | 1,046 | 5 | 五个阶段的推理协议 |
| `scaffolds/` | 783 | 8 | 输出文件的模板骨架 |
| `scripts/` | 771 | 2 | 唯一可执行的部分：采集与结构化抽取 |
| `guardrails/` | 595 | 3 | 反幻觉、范围控制、烂论文处置 |
| 仓库根 | 240 | 2 | README 与许可证 |
| `SKILL.md` | 112 | 1 | 总编排入口 |

```text
$ git ls-files '*.md' | xargs wc -l | tail -1
    3939 total
$ git ls-files '*.py' | xargs wc -l | tail -1
    3627 total
```

说明文比程序多出 312 行。这个比例是理解本项目的关键：被交付的"能力"大部分不是函数，而是提示词协议的工程化——把"不许猜"拆成可执行的阶段、可检查的清单和可 grep 的标签。Python 只负责两件无法用文字代替的事：把论文取回来，把结构切出来。

`SKILL.md` 的编排指令只有一句话概括流程：

```text
This file governs the high-level flow. Each stage dispatches to a detailed
reasoning protocol in `pipeline/`. Do NOT skip stages. Do NOT combine stages.
Execute them in order.
```

## 一次真实调用：从 arXiv 编号到结构化文本

README 承诺的用法是一行 `/paper2code <url>`，但它依赖的是宿主编码智能体（coding agent）读取 Markdown 协议并逐步执行，脚本部分可以脱离智能体单独跑。把这条链路拆开验证，才看得出每一环的真实产出。

`SKILL.md` 声明的运行前置只有四个 Python 依赖：

```bash
pip install pymupdf4llm pdfplumber requests pyyaml
```

第一阶段调用两个脚本。前者取论文，后者切结构：

```bash
python skills/paper2code/scripts/fetch_paper.py 1706.03762 ./out
python skills/paper2code/scripts/extract_structure.py ./out/paper_text.md ./out
```

实跑第一阶段的输出（2026-09-26，macOS，Python 3.11）：

```text
Arxiv ID: 1706.03762

--- Fetching metadata ---
  Title: Attention Is All You Need
  Authors: Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones...
  Categories: cs.CL, cs.LG

--- Downloading PDF ---
Downloading PDF from https://arxiv.org/pdf/1706.03762.pdf...
  Downloaded: 2163 KB

--- Extracting text ---
Extracting with pymupdf4llm (math-preserving)...

=== Document parser messages ===
Using Tesseract for OCR processing.
OCR on page.number=2/3.
OCR on page.number=3/4.
OCR on page.number=12/13.
  Extracted: 42307 characters
  No official code repositories found.

--- Extraction Summary ---
  Characters: 42,307
  Pages detected: N/A (HTML extraction)
  Math preserved: No
  Figure references found: Yes
  Official code links: 0 found
```

这一段输出里有三处需要解释，因为它们直接决定后续阶段的可用输入。

`Math preserved: No` 不是误报。产物 `paper_text.md` 里反斜杠出现 0 次、美元定界符 0 次、`\frac` 0 次，也就是说公式全部退化成了散文。函数文档写着 `extract_with_pymupdf4llm` "preserves math notation as LaTeX"，但在这篇公式密集的论文上，它一个符号都没留下；抽取过程中第 2、3、12 页还退给了 OCR。

`Pages detected: N/A (HTML extraction)` 是一处标签错配。`<!-- Page N -->` 这种页标记只有 `pdfplumber` 分支会写入，本次跑的是 `pymupdf4llm`，计数为 0 后代码直接把兜底说明打印了出来。换成 DDPM（arXiv 2006.11239）重跑，同样是 `pymupdf4llm` 抽取的 58,906 字符，这一行照样打印 `N/A (HTML extraction)`。

`Official code links: 0 found` 是搜索规则的边界，不是论文的问题。`find_official_code()` 只认两类模式：文本里字面出现的 GitHub、GitLab、Bitbucket 仓库 URL，以及 `code is available at`、`source code:` 这类短语后紧跟的链接。Transformer 论文正文两次提到自家代码库 `tensor2tensor`，却没有给出 URL，于是命中 0。DDPM 论文的摘要里有 `Our implementation is available at https://github.com/hojonathanho/diffusion`，同一套规则就命中 1。这两条差异决定了后面 `[FROM_OFFICIAL_CODE]` 标签能不能存在：全仓库该标签出现在 42 行里，其中 DDPM 范例占 31 行，Transformer 范例 0 行。

## 结构化抽取交出的清单，比协议假定的薄

`extract_structure.py` 是第三阶段（模糊审计）的主要输入之一，它负责把章节、算法框、编号公式、表格、脚注切成单独文件。同一篇 Transformer 论文，它的汇总行是：

```text
--- Extraction Summary ---
  Sections:   27
  Algorithms: 0
  Equations:  0
  Tables:     6
  Footnotes:  0
  Output dir: out
```

协议对这几类东西寄予了明确期望。`pipeline/02_contribution_identification.md` 的第三步标题是 "Find the Algorithm box"，正文称算法框是"gold"，并规定"如果散文说一件事而算法框说另一件，实现算法框"；`pipeline/03_ambiguity_audit.md` 要求逐条检查"附录、图注、脚注"；`hallucination_prevention.md` 把"等式比散文精确"列为裁决规则之一。

而在这篇论文的实际抽取结果里，算法框 0 个、编号公式 0 条、脚注 0 条。论文里客观存在 Algorithm 1、Algorithm 2 和编号到 (3) 的公式，也有页脚注——它们只是没有活过 PDF 抽取这一关。于是"以算法框为准"的优先级规则，在这份输入上无从引用，锚定只能退回散文段落。

27 个小节里还有重复：`01_attention_is_all_you_need.md` 与 `02_attention_is_all_you_need.md` 是同一条标题的两次捕获；`09_scaled_dot-product_attention.md`（553 字节，来自 Figure 2 的图注区）与 `10_321_scaled_dot-product_attention.md`（1,603 字节，正文 §3.2.1）是同名两节，前者内容短得多。审计阶段若按小节文件遍历，重复标题会被当成两个信息源。

6 张表格里有 2 张是误捕。文件名的前缀暴露了这一点：

```text
01_table_1_maximum_path_lengths_per-layer_complexity_and_minimum_number...
02_table_1_a_self-attention_layer_connects_all_positions_with_a_constan...
03_table_2_the_transformer_achieves_better_bleu_scores_than_previous_st...
04_table_2_outperforms_the_best_previously_reported_models_including_en...
05_table_3_variations_on_the_transformer_architecture_unlisted_values...
06_table_4_the_transformer_generalizes_well_to_english_constituency_par...
```

`02` 和 `04` 不是表格标题，而是正文句子被误判成了题注：

```text
Table 1, a self-attention layer connects all positions with a constant numb
Table 2) outperforms the best previously reported models (including ensembl
```

表格识别用的是"Table 加数字加上下文"的宽松匹配，正文里的交叉引用因此被当成题注。真实表格是 4 张。

表格内容本身的可读性另说。Table 3 是这套流程里最吃紧的一张——`REPRODUCTION_NOTES.md` 和 `configs/base.yaml` 的大量节引用都要指向它。抽取产物里它的 base 行完整：`|base|6|512|2048|8|64|64|0.1|0.1|100K|4.92|25.8|65|`，N、d_model、d_ff、h、d_k、d_v、P_drop、ε_ls、步数、困惑度、BLEU、参数量一格不缺。往下第 17、18 行变成 `||||1024|||||||5.12|25.4|53|` 和 `||||4096|||||||4.75|26.2|90|`，只剩一个数值和两个指标，变化项归属哪一列要靠位置数出来；最后一组行更彻底，`(E)` 那一行把"positional embeddings instead of sinusoids"整个句子拆进了七个数据格：

```text
|(E)||posi|tional e|mbedd|ingins|tead of|sinusoi|ds||4.92|25.7||
```

`pipeline/01_paper_acquisition.md` 承诺这一步会 "Extracts tables (especially those containing hyperparameters, learning rates, dimensions)"——表格恰恰是这份产物里唯一真正可用的结构化输入，而它的组标签 `(A)`、`(B)`、`(D)` 已经丢失。

这里也暴露了质量闸门为什么拦不住：`check_text_quality()` 只取文档前 1000 字符，实测该窗口非 ASCII 占比 1.1%、常用英文词 7 个，两项都轻松通过；而 Table 3 从第 262 行、字节偏移 27,043 处才开始，全文非 ASCII 也只占 0.23%。也就是说，一份公式全丢、算法框全丢、表格串列的产物，在这道闸门眼里是合格的——"字符正常"和"信息完整"之间没有映射。

值得补一句的是第二级兜底的质量。`pipeline/01_paper_acquisition.md` 写的探测口径是"扫描前 500 字符，非 ASCII 且非 LaTeX 特殊字符占比超过 20% 判为乱码"，而 `fetch_paper.py:249` 实际取样 `text[:1000]`；20% 阈值一致，取样长度不一致。更要紧的是控制流：质量检查只在 `pymupdf4llm` 与 `pdfplumber` 两支之后执行，`ar5iv` 那一支只在"前面根本没拿到文本"时进入，拿到文本就直接落盘，不再检查。把 DDPM 的 PDF 交给 `pdfplumber` 单独跑一次，能看出为什么它排第二：53,458 字符里词间空格大量丢失，标题作者行成了 `JonathanHo AjayJain PieterAbbeel`，摘要开头是 `Wepresenthighqualityimagesynthesisresults...`。这种文本做人工阅读勉强可用，做字符串检索会系统性漏检。

## 标签系统：六个在册，一个野生

出处标签是这套机制里唯一可 grep 的部分。README 的 `Ambiguity classification` 表定义六种：

| 标签 | 含义 | 落点 |
|---|---|---|
| `§X.Y` | 论文第 X.Y 节明确指定 | 代码注释、配置行尾 |
| `§X.Y, Eq. N` | 实现该节第 N 条公式 | 代码注释 |
| `[UNSPECIFIED]` | 论文未写明，写出所用选择与替代项 | 代码注释、配置 |
| `[PARTIALLY_SPECIFIED]` | 论文提到但含混，附引文 | 代码注释、审计表 |
| `[ASSUMPTION]` | 依上下文推断，写出推理 | 代码注释 |
| `[FROM_OFFICIAL_CODE]` | 取自作者官方实现 | 代码注释、配置 |

按出现行数在仓库内统计（含文档与代码，排除 `.git`）：`UNSPECIFIED` 89 行、`FROM_OFFICIAL_CODE` 42 行、`PARTIALLY_SPECIFIED` 19 行、`ASSUMPTION` 9 行。数量梯度本身是合理的——DDPM 有官方代码可查，Transformer 没有。

问题在于第七个。`worked/attention_is_all_you_need/configs/base.yaml` 的表头自己声明了一条约定：

```yaml
# CONVENTION:
#   - Lines with §X.Y cite the paper section specifying this value
#   - Lines with [UNSPECIFIED] mark choices not stated in the paper
#   - Lines with [FROM_TABLE] reference Table 3 (Architecture hyperparameters)
```

```text
$ grep -rn "FROM_TABLE" --exclude-dir=.git . | wc -l
       1
```

`[FROM_TABLE]` 在全仓库只出现在这一行注释里，README 的标签表没有它，五个流水线文档也没有它。表 3 的取值在配置文件里实际是用 `§3.1, Table 3` 这种普通节引用写的。一处未被登记的约定，恰好说明标签系统靠人工书写维持一致性，没有校验器兜底——仓库确实没有任何测试或 CI 配置，`git ls-files | grep -ic test` 的结果是 0。

`[UNSPECIFIED]` 的写法本身是有协议的，`hallucination_prevention.md` 规定三段式：

```python
# [UNSPECIFIED] Paper does not state activation function in the feed-forward network
# Using: GELU (most common in recent transformer implementations)
# Alternatives: ReLU (original transformer), SiLU/Swish (used in LLaMA, PaLM)
self.activation = nn.GELU()
```

同文件禁止七种"隐藏假设"的措辞：`standard practice`、`as usual`、`obviously`、`typically`、`it's well known that`、`for simplicity`、`should work`，并要求"论文说 512 就用 512，任何偏离都要显式标注"。这条纪律在产物里只被部分执行：`worked/attention_is_all_you_need/src/model.py` 有 6 行含 `[UNSPECIFIED]`，其中 1 行是类文档字符串里的说明，剩下 5 处标注里只有偏置和初始化两处按三段式写全了 `Using` 与 `Alternatives`，其余压成了行尾单行；DDPM 范例的 `src/` 六个文件里 `# Using` 出现 0 次，出处信息全部集中在 `configs/base.yaml` 的行尾注释。协议规定的是注释的最小信息量，产物实际给的是缩写。

## 39 项审计清单和它的裁决顺序

模糊审计是"生成代码之前"那一步，也是这套设计真正吃力的地方。`pipeline/03_ambiguity_audit.md` 给了逐项清单：架构 16 项、训练 14 项、数据 5 项、评估 4 项，共 39 项，每项标注"去哪里找"和"常见藏身处"。

清单里有几条明显来自实际复现的痛感：

- 归一化位置（Pre-norm 还是 Post-norm）标注为"CRITICAL for transformers. Check Figure vs text — they often disagree"。
- 归一化 epsilon 标注"Almost never stated"，并列出 1e-5（框架默认）、1e-6、1e-8 三种常见值。
- 批大小标注"Total or per-GPU? Crucial distinction — often ambiguous"。
- 激活函数标注"Often unstated — do NOT assume ReLU"。

检索动作被规定成七步：方法节、实验节、附录、图注、脚注、表注、关键词全文搜索。阶段末尾还有 8 个复选框，包括"你检查过附录（而不只是方法节）"和"你检查过脚注"。

裁决顺序散落在三个文件里，合起来是一套明确的优先级：算法框高于散文；公式高于散文，即使公式像是笔误也先按公式实现再标注疑点；方法节高于摘要；官方代码是参考而非常识来源——`hallucination_prevention.md` 要求引用官方代码必须精确到 `blob/main/model.py#L42` 这样的行号，并禁止复制粘贴。`badly_written_papers.md` 给出一条五级降级阶梯：论文→官方代码（标 `[FROM_OFFICIAL_CODE]`）→知名复刻（仍标 `[UNSPECIFIED]` 并写出参考）→领域标准选择（仍标 `[UNSPECIFIED]`）→写桩函数并在文档字符串里说明选项。

论文类型也被分档，共六类：(a) 新架构、(b) 新训练方法或损失、(c) 新推理或生成技术、(d) 新数据集或基准、(e) 带实证校验的理论分析、(f) 系统或工程论文。分档直接改变范围：`guardrails/scope_enforcement.md` 的类型 (a) 表里，训练循环是 MINIMAL、数据管道是 SKELETON、分布式训练是 NEVER。类型 (f) 有一条难得的自认："这些论文常常无法用最小实现复现，因为贡献本身就是工程"。

## 生成的代码确实跑得起来

机制之外，产物质量要单独测。仓库带两个范例目录，`attention_is_all_you_need/` 与 `ddpm/`，合计 4,102 行。按范例 README 给的快速开始逐字执行：

```python
from src.model import Transformer, TransformerConfig

config = TransformerConfig()
model = Transformer(config)
src = torch.randint(0, config.vocab_size, (2, 20))
tgt = torch.randint(0, config.vocab_size, (2, 15))
output = model(src, tgt)
```

实测输出形状 `torch.Size([2, 15, 37000])`，参数量 63,082,496。论文 Table 3 的 base 模型标注 65×10^6，`REPRODUCTION_NOTES.md` 的排错条目也写"大约 65M"，实测值与之相差约 3%，量级与差异都属正常（词表与绑定方式会影响计数）。

配置文件内部也有一处会咬人的不一致。`configs/base.yaml` 的 `model` 段有 `max_seq_len: 5000`，注释说明这是位置编码表的最大长度；`data` 段又用同一个键名写 `max_seq_len: 512`，指的是训练时的序列上限。`vocab_size: 37000` 与 `bpe_tokens: 37000` 也是同一件事的两个键。同名键在两段里表示两个不同上限，读配置的人必须靠段名才知道 512 不是位置编码表的长度；而 `REPRODUCTION_NOTES.md` 的"未指定选择"表只登记了 5000 这一条（替代项 `512, 10000`），512 那个上限在审计文档里没有独立条目。README 的"关键文件说明"表把 `base.yaml` 定义为 "Single source of truth for all hyperparameters"（第 125 行），这两处恰好是反例。

同目录的 `train.py` 有三种启动方式，只有一种能用：

```text
$ python src/train.py
ModuleNotFoundError: No module named 'src'

$ python -m src.train
Step 1 | Loss: 10.5569 | LR: 1.75e-07
Logits shape: torch.Size([4, 15, 37000])
```

文件内部写的是 `from src.model import ...`，因此必须在范例根目录以模块方式启动；直接执行脚本会报 `No module named 'src'`，从上级目录执行则报 `No module named 'src.model'`。第二次跑同一条命令得到 `Loss: 10.5605`，形状不变——代码没有固定随机种子，loss 这类数字不能当回归基线。

`notebooks/walkthrough.ipynb` 是 README 承诺"可在 CPU 上用玩具维度跑通"的那一份。它的 24 个单元里 13 个是代码单元，所有单元的 `execution_count` 都是 `None`、`outputs` 全空，也就是说这份 notebook 在仓库里从未带着执行结果被保存过。把它逐单元执行一遍：

```text
Using toy dimensions: d_model=64, n_heads=4, d_ff=128
d_k = d_model / n_heads = 16
✓ Scaled dot-product attention: (2, 4, 10, 16) -> torch.Size([2, 4, 10, 16])
✓ Attention weights sum to 1 (verified)
✓ MultiHeadAttention: (batch=2, seq=10, d_model=64) -> torch.Size([2, 10, 64])
  Parameters: 16,640
  Expected: 4 * d_model^2 + 4 * d_model (biases) = 16,640
✓ PE values bounded in [-1, 1]: min=-0.990, max=1.000
✓ Full Transformer: src (2, 10) + tgt (2, 8) -> logits (2, 8, 100)
  Parameters: 173,824
✓ All 85 parameter tensors have gradients
cells=13 ok=13 failed=0 elapsed=0.9s
```

13 个代码单元全部通过，耗时 0.9 秒。这些检查不是空断言：注意力权重经 softmax 后逐行求和为 1、位置编码取值落在 [-1, 1]、多头投影参数量与公式 `4·d_model² + 4·d_model` 对得上。最后一条尤其有意思——它把偏置项计入，而 `bias` 恰恰被标为 `[UNSPECIFIED]`，也就是说这个"期望值"依赖一个未指定的选择。

一处承诺与产物不符：README 的输出清单里写 `requirements.txt  # Pinned dependencies`，两份范例的该文件实际是三行下界约束：

```text
torch>=2.0.0
numpy>=1.24.0
pyyaml>=6.0
```

版本没有锁。同一批里另一处缺口是脚手架：`scaffolds/` 有 8 个模板，覆盖 model、loss、data、train、evaluate、config、readme、reproduction_notes，唯独没有 `utils`，而 `pipeline/04_code_generation.md` 把 `src/utils.py` 列为生成顺序的第二项，还专门警告"不要把 utils 写成杂物间"。

## 三处引用锚点经核查不成立

上面这些都属于工程整洁度。真正触及项目主张的，是被引号标注成"论文原句"的文本是否真的存在。做法很笨也最可靠：用项目自己的脚本取回论文全文，再用 `ar5iv` 的 HTML 作第二来源，逐条把引文归一化（去标签、去标点、压空白）后做子串比对。

第一条在 README，也在流水线文档，两处文本几乎相同：

```python
# [ASSUMPTION] Using pre-norm based on "we found pre-norm more stable" in §4.1
# The paper uses post-norm in Figure 1 but pre-norm in experiments — ambiguous
```

```text
$ grep -rn "pre-norm more stable" --exclude-dir=.git .
./README.md:165:# [ASSUMPTION] Using pre-norm based on "we found pre-norm more stable" in §4.1
./skills/paper2code/pipeline/04_code_generation.md:65:# [ASSUMPTION] Using pre-norm based on "we found pre-norm more stable" (§4.1)
```

Transformer 论文里检索不到 `pre-norm`，也检索不到 `more stable`（PDF 抽取文本与 ar5iv HTML 两个来源一致，前者 42,307 字符、后者去标签后 45,089 字符）。抽取出的 27 个小节里，第 4 节下没有任何编号子节，示例引用的 `§4.1` 无所指；HTML 源文里 `Parallelizations` 等小节名也是 0 命中。这两处引号里的句子不是引用，是虚构的示例内容——问题不在于示例可以是假的，而在于同一个示例同时充当了协议说明和目标论文的陈述。

更麻烦的是它把结论也说反了。论文 §3.1 描述编码器与解码器 stacks 时逐字给出（两个来源一致）：

```text
We employ a residual connection [11] around each of the two sub-layers, followed by
layer normalization [1]. That is, the output of each sub-layer is
LayerNorm( _x_ + Sublayer( _x_ )), where Sublayer( _x_ ) is
```

下划线是 PDF 抽取残留的斜体标记，去掉后就是 `LayerNorm(x + Sublayer(x))`，也就是 post-norm，而图 1 里那四个 `Add & Norm` 标签（PDF 抽取文本中出现 4 次）表达的是同一件事。也就是说"文字说 pre-norm、图说 post-norm"这个前提两头都不成立：文字与图一致，实现也按 post-norm 落地。范例把这一条登记为 `[UNSPECIFIED]` 并保留 pre-norm 作为替代项，是稳妥的处理；被写进 README 和流水线文档当示例的那句引文，却是一个不存在的反例。

第二条在 DDPM 范例的三处位置（配置、模型源码、审计笔记）：

```text
# Appendix B — "dropout 0.0" (CIFAR-10). "dropout 0.1" for bedroom/church
```

论文附录 B 的实际句子，两个来源一致：

```text
We set the dropout rate on CIFAR10 to 0.1 by sweeping over the values
{0.1, 0.2, 0.3, 0.4}. Without dropout on CIFAR10, we obtained poorer samples
reminiscent of the overfitting artifacts in an unregularized PixelCNN++ [52].
We set dropout rate on the other datasets to zero without sweeping.
```

方向是反的：CIFAR-10 用 0.1，其他数据集才用 0。`REPRODUCTION_NOTES.md` 第 41 行还把 `"dropout 0.0 for CIFAR10"` 作为论文引文写进"论文原句"栏，`src/model.py:46` 的默认参数 `dropout: float = 0.0` 也引用同一句。一处误读被三处一致复用，且都带着引号和节号。

第三条同样在 DDPM 配置里：

```yaml
base_channels: 128           # Appendix B — "128 base channels"
```

`channel` 这个词在 DDPM 论文全文出现 0 次。这一条经过三条独立路径确认：`pymupdf4llm` 抽取文本 0 次、`ar5iv` HTML 0 次、`pdfplumber` 直抽 PDF 也 0 次（尽管它的分词已经塌陷，`channel` 作为子串仍无命中）。附录 B 给出的规模信息是参数量——"Our CIFAR10 model has 35.7 million parameters"——而不是通道数。128 这个值实际来自官方代码，本应标 `[FROM_OFFICIAL_CODE]`，同文件里紧邻的 `channel_mults: [1, 2, 2, 2]` 就是这么标的。

## 出处标签在两份文档里互相矛盾

同一个范例目录内部的标签分歧，比引文错误更常见，也更容易被读者忽略。DDPM 的批大小就撞上这一条：

```text
configs/base.yaml:46    batch_size: 128   # Appendix B — "batch size 128" (CIFAR-10)
review.md:48            **Batch size 128**: [FROM_OFFICIAL_CODE] — paper does not
                        explicitly state batch size
```

配置的说法是对的：附录 B 明写 `We set the batch size to 128 for CIFAR10 and 64 for larger images. We did not sweep over these values.` 而 review.md 的断言"论文没有明确说明批大小"与论文文本直接冲突，并按自家护栏规则把它降成了官方代码来源。

`review.md` 第 52 行还写了 `Data normalization [-1,1]: [FROM_OFFICIAL_CODE] — paper doesn't specify range`，而 `configs/base.yaml` 第 61 行是 `normalize: true  # [UNSPECIFIED] — normalize images to [-1, 1] (standard for diffusion)`。同一个选择，两份文档给了两个不同标签：一个说取自官方代码，一个说论文未写明、用的是领域惯例。这类分歧只要把同一目录里的两份文本并排读一遍就能发现，仓库里没有做交叉检查的脚本。

Transformer 范例的 `REPRODUCTION_NOTES.md` 的"预期结果"表里还有一处更简单的错误：

| Metric | Paper's number | Dataset | Conditions |
|---|---|---|---|
| BLEU | 27.3 | WMT 2014 EN-DE | Table 2, base model |
| BLEU | 38.1 | WMT 2014 EN-FR | Table 2, big model |

论文 Table 2 的两行原文（从抽取文本逐字取回）：

```text
|Transformer (base model)|27.3|38.1|...|
|Transformer (big)|**28.4**|**41.8**|...|
```

27.3 与 38.1 同属 base 模型，分别是 EN-DE 与 EN-FR；big 模型是 28.4 与 41.8。表里把 38.1 记成 big 模型，等于把 big 的提升幅度写小了。摘要里也印证这一点：论文自述的 SOTA 是 28.4（EN-DE）与 41.8（EN-FR）。

要把话说平：这套核查不是为了把范例判成废品。带引号的论文陈述在第一篇范例里共 16 条，逐字命中 11 条，包括 §3.4 的 `share the same weight matrix`、§5.3 的 `warmup_steps = 4000`、§5.4 的 `label smoothing of value ε_ls = 0.1`、§5.1 的 `25000 source tokens and 25000 target tokens`、§6.1 的 `beam search with a beam size of 4` 与 `length penalty α = 0.6`（最后一条实测落在 §6.1 小节内，节号标注是对的）。其余 5 条里，1 条不是论文句子（`The Annotated Transformer` 是参考实现名），3 条用省略号压缩过真句子，1 条把主动句改成了被动。DDPM 范例的 17 条只有 2 条逐字命中，但多数落空的条目是符号被抽取打乱造成的假阴性——`learning rate 2 × 10^−4`、`decay factor of 0.9999` 在论文里都有对应原句，需要人工定案。

剩下的条目按严重度分三档，这个分档直接决定修复代价。最轻的一档是值对、节号或写法对不上。DDPM 配置第 40 行写 `lr: 0.0002  # §4 — "learning rate 2 × 10^−4"`，而抽取出的论文文本里 `learning rate` 只出现在两处：附录 B 那条项目符号（第 503 行）和附录 C 讨论采样器系数的一句（第 523 行），§4 正文没有这句。同一档还有更表面的：`configs/base.yaml` 第 15 行写 `d_model: 512  # §3.1, Table 3 — "d_model = 512"`，论文全文 `d_model = 512` 这个字面串出现 0 次，`d_ff = 2048` 同样如此——值确实能在 Table 3 的 base 行读到，只是论文没有这么写。

中间一档是出处归属错了——值本身没错，来源写错了。`num_samples: 50000  # Standard for FID computation` 把领域惯例当成出处，而论文附录 B 其实明写 `we calculated Inception and FID scores on 50000 samples`，一个本可锚定的值被降级成了惯例；反向的例子是 `image_channels: 3  # §4 — RGB images`，论文里 `RGB` 出现 0 次，但这属于常识而非误读。

最重的一档就是上面那三条：引号里的句子在论文里不存在，其中 dropout 连取值方向都反了。

三档的修复方式完全不同：第一档只需把引号去掉、改成 `Table 3 base row`；第二档要么补锚点要么承认是选择；第三档必须重新读论文。协议里没有区分这三档的写法要求，全部用同一种 `# §X — "quote"` 格式表达，读者无法从格式上判断自己该信哪一条。

还有一个细节值得记一笔。第一篇范例 `REPRODUCTION_NOTES.md` 第 26 到 30 行是一份"核对过什么"的清单，五条里 `Official code (tensor2tensor) — referenced but not line-by-line verified` 是唯一未勾选的那条。也就是说，这份文档自己承认了官方代码没有被逐行验证——这与它把 tensor2tensor 写进论文信息栏的做法是自洽的，也正是本项目最该有的那种诚实。

## 仓库自己登记的缺陷，实测复现

开放问题列表里有一条 2026-04-05 提交的 issue，标题前半句是 `Arxiv ID validation warns but does not reject invalid IDs`，后半句说元数据请求仍用 HTTP 而非 HTTPS。这两条描述都准确，且能直接复现：

```text
$ python fetch_paper.py not-an-arxiv-id ./out2
WARNING: 'not-an-arxiv-id' may not be a valid arxiv ID.
WARNING: Could not fetch metadata from arxiv API: 406 Client Error: Not Acceptable
  FAILED: 404 Client Error: Not Found for url: https://arxiv.org/pdf/not-an-arxiv-id
  ar5iv fetch failed: 404 Client Error: Not Found for url: https://ar5iv.labs.arxiv.org/html/not-an-arxiv-id
ERROR: All extraction methods failed.
Please download the paper manually and provide the text.
```

`normalize_arxiv_id()` 的校验只打印警告并继续走完全流程，最终在三个 404/406 之后退出。元数据请求的地址前缀写成 `http://export.arxiv.org`，服务端把它重定向到 HTTPS（错误消息里的 URL 因此显示为 https），代码里的字面量仍是 HTTP。

另一条登记在册的静态事实是维护状态。以 2026-09-26 取数：1,520 star、180 派生、4 个 watcher、仓库体积 126 KB、MIT 许可证、语言标注 Python。全部 5 次提交都在 2026-04-03 这一天，作者只有 1 人。创建时间 11:56 UTC，最后一次推送 13:03 UTC——从建库到内容定型约 67 分钟，此后 176 天没有新提交。

未关闭条目有 2 条，其中一条是 2026-06-01 由外部账号提交的 PR `Add GitAgent Protocol support (agent.yaml + SOUL.md)`，正文在给项目推销一个第三方"智能体协议"注册表，维护者未回应。这一条与项目质量无关，但它解释了为什么 issue 也处于无人处理状态。

## 谁该用，谁不该用

判断的依据不是"能不能生成代码"，而是"能不能承担核对成本"。

适合三类情形。第一是复现前人论文时的起点搭建：`REPRODUCTION_NOTES.md` 这种"所有未指定选择"的清单，确实能省掉一遍人工翻附录，即使少数条目有误，把它当作待验证的检查表来用也划算。第二是教学：范例 notebook 在 CPU 上 0.9 秒跑完 13 个单元、每个形状都有断言，用来讲注意力机制的实现细节比 PPT 更接近真相。第三是代码评审场景下的"来源分类"实践迁移——三段式 `[UNSPECIFIED]` 注释和"论文说 512 就用 512"这条纪律，即使不用这个项目，也值得直接抄进团队的复现规范。

不适合三类情形。需要可复算结果的正式复现不要用：`requirements.txt` 没锁版本、没有随机种子、没有测试与 CI，两个范例之间连批大小的出处都互相矛盾。论文没有官方代码且大量依赖工程细节的领域（系统类、分布式训练类）不要用，项目自己也把类型 (f) 划入"最小实现难以复现"。也不要把它当成正确性保证——`Won't guarantee correctness` 在 README 的边界声明里排在第一位，六条边界声明（不保证正确、不发明细节、不下数据集、不搭训练基础设施、不实现基线、不重造标准组件）本身写得比多数项目清楚。

采用顺序建议四步。第一步只读 `SKILL.md` 和 `pipeline/03_ambiguity_audit.md`，把 39 项清单变成自己团队的审计模板，这一步不需要装任何东西；第二步跑 `fetch_paper.py` 与 `extract_structure.py`，检查目标论文能不能抽出可用的表格与小节——这一步会筛掉大量"协议写了但输入不配合"的论文；第三步跑一个有官方代码的论文，观察 `[FROM_OFFICIAL_CODE]` 是否被诚实使用；第四步再让智能体按完整流水线出码，并且把"逐条把引文回查论文原文"当作强制验收，因为本项目最容易出错的就是这一步。

## 怎么自己复算本文的结论

本文里所有断言都停在同一台机器（macOS、Python 3.11）上执行过，命令如下。

```bash
git clone https://github.com/PrathamLearnsToCode/paper2code.git
cd paper2code
git ls-files | wc -l                     # 49
git ls-files | xargs wc -l | tail -1     # 8,876 total
git ls-files | grep -ic test             # 0（无测试）
git rev-list --count HEAD                # 5
git log --format='%h %ad %s' --date=short

python3 -m venv v && . v/bin/activate
pip install pymupdf4llm pdfplumber requests pyyaml
python skills/paper2code/scripts/fetch_paper.py 1706.03762 ./out
python skills/paper2code/scripts/extract_structure.py ./out/paper_text.md ./out
python skills/paper2code/scripts/fetch_paper.py 2006.11239 ./out2
```

三条"引文不存在"的定案过程如下。左边是命令，右边是实测返回，两处来源都要判 0 才算成立：

```bash
# Transformer：pre-norm 的说法在论文里没有出处
grep -c "pre-norm"    out/paper_text.md    # 0
grep -c "more stable" out/paper_text.md    # 0
curl -sL https://ar5iv.labs.arxiv.org/html/1706.03762 | grep -c "4.1 Parallelizations"   # 0

# DDPM：channel 一词全文不存在，dropout 的取值方向相反
curl -sL https://ar5iv.labs.arxiv.org/html/2006.11239 | grep -c "128 base channels"      # 0
grep -o "We set the dropout rate on CIFAR10.\{0,45\}" out2/paper_text.md
# We set the dropout rate on CIFAR10 to 0 _._ 1 by sweeping over the values _{_ 0

# Table 2 归属：notes 把 38.1 记成了 big 模型
grep -o "Transformer (base model)|.\{0,60\}" out/paper_text.md
# Transformer (base model)|27.3|38.1|**3****_._3****_·_**|**10**<sup>**18**</sup>|
```

抽取文本里数学符号被写成了 `_._` 这种下划线形式，所以 grep 时要用 `.` 通配而不是照抄 `0.1`。DDPM 的关键数字可以顺带定案：FID 3.17、Inception 9.46、CIFAR-10 模型 35.7 million parameters、800k steps 都能检索到。

总括性的"没有问题"判定只有一份：第一篇范例的 `review.md` 第 89 行写着 `No silent assumptions detected.`，同段还有一句"没有发现实现自信地发明了论文未述细节"。DDPM 那份 `review.md` 通篇没有这种总括判定，它在第 48、52 行给出的是上文提到的两处出处误标。

另有一批锚点是逐条命中的，复核时可以直接引用：

```bash
grep -o "batch size to 128.\{0,50\}" out2/paper_text.md
# batch size to 128 for CIFAR10 and 64 for larger images. We did not
grep -c "decay factor of 0.9999" out2/paper_text.md        # 1
grep -o "share the same weight matrix.\{0,40\}" out/paper_text.md
# share the same weight matrix between the two embedding layers and
```

范例可运行性核对（需在范例目录内以模块方式启动）：

```bash
pip install torch numpy pyyaml
cd skills/paper2code/worked/attention_is_all_you_need
python -m src.train
python src/train.py          # 预期 ModuleNotFoundError，用来确认包内导入写法
```

GitHub 侧的数字（星标数、派生数、创建与最后推送时间）随时会变，正文里的取数日期是 2026-09-26。

## 常见问题

**Q：这套东西真的需要一个技能来做吗？直接让智能体读论文写实现，差别在哪？**

差别在审计这一步是否被强制。直接指令下的实现会把 LayerNorm epsilon、偏置项、初始化方案按框架默认填掉，代码里不留痕迹。`pipeline/03_ambiguity_audit.md` 把这些选择变成必答项，并规定每个 `[UNSPECIFIED]` 都必须写出所用值与替代值。实测范例代码里这类显式标注确实存在——第一篇范例的 `src/model.py` 有 5 处 `[UNSPECIFIED]` 值标注——虽然缩写形式让完整的 `Using` 与 `Alternatives` 只出现在 2 处。把选择显式写出来这一步没有被跳过，这是它相对"直接问"的真实增量。

**Q：`--mode full` 和 `--mode educational` 到底多生成什么？**

`SKILL.md` 写得很具体：默认 `minimal` 只做核心贡献，训练循环仅当贡献本身涉及训练时才有；`full` 加上完整训练循环、数据管道与评估管道；`educational` 与 `minimal` 同码，但补大量内联注释、扩充 notebook 的理论段落，并额外产出 `PAPER_GUIDE.md`。注意最后这份文件在仓库里一份都没有（`find . -name "PAPER_GUIDE*"` 返回 0），两个范例也都没用过 educational 模式，这条承诺目前只有文本依据。

**Q：为什么两个范例的 `[FROM_OFFICIAL_CODE]` 数量差这么多？**

因为取码环节的命中条件不同，不是 Transformer 复现得更差。DDPM 摘要里直接给了官方仓库 URL，`find_official_code()` 命中；Transformer 论文只提代码库名字、不给链接，元数据里 `official_code` 是空列表，于是所有未指定项只能停在 `[UNSPECIFIED]`。同一套检索规则在不同论文上的产出差异，会直接反映到标签分布上。

**Q：结构化抽取这么弱，为什么不影响它的核心用法？**

因为审计真正依赖的是表格和小节边界，这两类实际抽出来了：Transformer 的 Table 3 在产物里是可读的 Markdown 表，base 行的 `N=6, d_model=512, d_ff=2048, h=8, d_k=64, d_v=64, P_drop=0.1, ε_ls=0.1, 100K steps, 65M params` 一格不缺。受影响的是公式与算法框——凡是要按"公式优先于散文"裁决的地方，输入里就没有公式可引用。

**Q：作为排错起点，这份范例代码可信吗？**

架构部分可信，实测形状、参数量、偏置计数都对得上。需要警惕的是配置注释里的出处标注：DDPM 那份的 dropout 值和引文都不成立，`base_channels` 的引文在论文里不存在。错误集中在注释和审计文档，不在 `forward()` 的计算路径上。

## 五个自测题

1. README 的四条主张里，哪一条有可执行脚本支撑，哪几条只落在文本协议上？这个差别为什么重要？
2. `[UNSPECIFIED]` 的三段式协议规定必须写哪三项内容？如果只写 `# standard choice`，会掩盖什么？
3. `extract_structure.py` 在 Transformer 论文上交出 0 条公式、0 个算法框。这对"公式优先于散文"的裁决规则意味着什么？
4. DDPM 范例里批大小的出处在 `configs/base.yaml` 和 `review.md` 中分别是哪个标签？为什么把这两份文本并排读一遍就能发现问题？
5. 如果要把这套标签纪律引入团队复现规范，你会先引入哪三条，跳过哪些？

## 三个练习

**练习一：把审计清单变成自己领域的模板（30 分钟）**

读 `pipeline/03_ambiguity_audit.md`，对照你最近复现过的一篇论文，逐条回答 39 项里属于你领域的那一部分，标出哪些项在你的领域根本不存在、哪些项清单没覆盖。目标是发现这份清单默认偏向 Transformer 与扩散模型这条线。

**练习二：对一份范例输出做引文回查（40 分钟）**

跑 `fetch_paper.py` 取回 DDPM 全文，把 `worked/ddpm/configs/base.yaml` 里每一条带引号的注释抄出来，逐条做归一化子串比对。记录命中、近似、不存在三类各多少条，并给出你的判定口径。这个练习的产出是一份可复用的验收脚本。

**练习三：验证 `[ASSUMPTION]` 的写法边界（20 分钟）**

README 与 `pipeline/04_code_generation.md` 都用了 pre-norm 那条示例。把它改写成符合三段式协议的合法版本：哪些部分是你的推断，哪些部分论文真的写了，缺失的证据该由谁来补。改写后回答：如果协议本身给的示例就是虚构的，模型执行时会学到什么。

## 下一步读哪份文件

想理解机制的强度上限，先读 `guardrails/hallucination_prevention.md`（194 行）——"bright line rule"、"standard"陷阱对照表、被禁止的七种措辞都在这里，它是整个项目里信息密度最高的一份。

想知道产物长什么样，读 `worked/attention_is_all_you_need/REPRODUCTION_NOTES.md` 与同目录的 `review.md`（89 行）对照着看，前者是产物，后者是人类对它的评价，两者的分歧最有价值。

想动手改，先读 `skills/paper2code/SKILL.md`（112 行）确认五个阶段的调度关系，再决定是补 `scaffolds/` 里缺的 utils 模板，还是给标签系统加一个校验器。后者收益更大：本项目现在最缺的不是新协议，而是让协议自证的那段代码。

## 参考文献

- paper2code 仓库：<https://github.com/PrathamLearnsToCode/paper2code>（提交 `fcffce7`，2026-04-03）
- `README.md`：四条主张、安装、产物清单、六条边界声明、标签表与示例注释
- `skills/paper2code/SKILL.md`：五阶段编排、`MODE` 与 `FRAMEWORK` 取值、依赖安装、收尾摘要
- `skills/paper2code/pipeline/`：01 采集、02 贡献识别（六类论文分档）、03 模糊审计（39 项清单）、04 代码生成、05 notebook
- `skills/paper2code/guardrails/`：`hallucination_prevention.md`、`scope_enforcement.md`、`badly_written_papers.md`
- `skills/paper2code/knowledge/`：`transformer_components.md`、`training_recipes.md`、`loss_functions.md`、`paper_to_code_mistakes.md`
- `skills/paper2code/scripts/fetch_paper.py`、`extract_structure.py`
- `worked/attention_is_all_you_need/`、`worked/ddpm/`（含各自 `review.md`）
- Vaswani et al., 2017, *Attention Is All You Need*（标题里的 attention 即注意力机制）：<https://arxiv.org/abs/1706.03762>（HTML 版 <https://ar5iv.labs.arxiv.org/html/1706.03762>）
- Ho, Jain, Abbeel, 2020, *Denoising Diffusion Probabilistic Models*：<https://arxiv.org/abs/2006.11239>（HTML 版 <https://ar5iv.labs.arxiv.org/html/2006.11239>）
- DDPM 官方实现：<https://github.com/hojonathanho/diffusion>
- 仓库 issue #1：`Arxiv ID validation warns but does not reject invalid IDs`（标题后半句另指元数据请求仍用 HTTP）
