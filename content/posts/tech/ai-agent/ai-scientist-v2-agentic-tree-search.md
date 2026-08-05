---
title: "AI Scientist-v2：智能体树搜索驱动的自动化科研论文生成"
date: "2026-03-29T15:47:00+08:00"
slug: "ai-scientist-v2-agentic-tree-search"
github_repo: "SakanaAI/AI-Scientist-v2"
aliases:
  - /posts/tech/ai-scientist-v2-agentic-tree-search/
description: "AI Scientist-v2 是 SakanaAI 开源的自动化科研系统，用智能体树搜索替换 v1 的人类模板，让模型自主提出假设、设计并运行实验、撰写论文。它生成的一篇论文曾以均分 6.33 通过 ICLR 2025 workshop 评审，后按实验协议撤稿。"
draft: false
categories: ["技术笔记"]
tags: ["智能体", "自动化", "LLM"]
---

# AI Scientist-v2：把实验设计从模板改成树搜索

AI Scientist-v2 的贡献不在"更会写论文"，而在把实验设计这一步从 v1 的人类模板手里交还给模型。代价是成功率下降、成本上升，换来的是更开放的探索空间——以及一篇完全由 AI 生成、在同行评审中拿到高于接收线分数的论文。本文拆解树搜索机制、那条评审结果该怎么读，以及现在该在什么场景用它。

## 一、v1 和 v2 差的不是写作，是实验设计从哪来

v1（SakanaAI/AI-Scientist）里，模型能产出的东西被人类模板框住。系统只能在 NanoGPT、2D Diffusion、Grokking 这类模板里选一个，把 idea 填进模板预留的插槽，实验怎么跑基本是定死的。这一步可靠，因为变异范围小，但也就限制了系统能探索的假设。

v2 把这一步也交给模型。给定一个宽泛的研究主题，系统自己提出假设、自己决定实验怎么做、失败了自己换个方向。这从"在一条固定路径上填参数"变成了"在一棵实验树上搜索"。README 里说得很直白：v2 不必定比 v1 好，有强起始模板时 v1 成功率更高、产出更稳，v2 是给开放式探索用的。

## 二、系统总览

三段流水线，中间那段是 v2 的命门。

```mermaid
flowchart TD
    A[研究主题 Markdown] --> B[阶段1：假设生成 ideation]
    B --> C[结构化研究想法 JSON]
    C --> D[阶段2：BFTS 树搜索实验]
    D --> E[实验结果 + 树可视化 unified_tree_viz.html]
    E --> F[阶段3：论文撰写 writeup]
    F --> G[完整论文 PDF]

    D --> D1[实验管理器 agent_manager]
    D1 --> D2[并行 Worker]
    D1 --> D3[并行 Worker]
    D1 --> D4[并行 Worker]
    D2 & D3 & D4 --> D5[自适应调试]
    D5 --> D1
```

阶段二里，实验管理器（`ai_scientist/treesearch/agent_manager.py`）在几棵树之间调度资源。每个 Worker 独立探索一条分支，实验失败就触发自适应调试重试，管理器按 best-first 把预算分给更有希望的分支。这套树搜索实现搭在 [AIDE](https://github.com/WecoAI/aideml) 之上。

## 三、树搜索：把"下一步做什么"变成可搜索的状态

v1 是线性推进：假设 → 实验 → 结论，走完拉倒。v2 把实验切开成节点，多个可行方向并行生长，失败的分支被放弃而不是硬走下去。这样系统能同时试几条路，再根据中间结果收缩到最有希望的那条。

第一段是 ideation（`ai_scientist/perform_ideation_temp_free.py`）。你给一个 Markdown 主题文件（含 Title、Keywords、TL;DR、Abstract），它用 LLM 生成一批候选想法，调用 Semantic Scholar 检查新颖性，最后产出结构化的研究想法 JSON。

第二段的搜索参数都写在 `bfts_config.yaml`：

| 参数 | 作用 |
|------|------|
| `num_workers` | 并行探索的分支数 |
| `steps` | 整棵树最多探索的节点数 |
| `num_seeds` | 初始根节点数量，一般跟随 `num_workers` |
| `max_debug_depth` | 一个失败节点最多调试几次才放弃 |
| `debug_prob` | 失败时触发调试的概率 |
| `num_drafts` | 阶段一里独立生长的树的数量 |

## 四、一次任务怎么流过系统

以"探索新的深度学习优化器"这类主题为例。第一步，把主题写成 Markdown 放进 `ai_scientist/ideas/`，跑 ideation：

```bash
python ai_scientist/perform_ideation_temp_free.py \
  --workshop-file "ai_scientist/ideas/my_research_topic.md" \
  --model gpt-4o-2024-05-13 \
  --max-num-generations 20 \
  --num-reflections 5
```

它生成 `my_research_topic.json`，里面是一批带假设、实验方案和相关工作分析的 idea。第二步，用这个 JSON 启动主流水线：

```bash
python launch_scientist_bfts.py \
  --load_ideas "ai_scientist/ideas/my_research_topic.json" \
  --load_code \
  --add_dataset_ref \
  --model_writeup o1-preview-2024-09-12 \
  --model_citation gpt-4o-2024-11-20 \
  --model_review gpt-4o-2024-11-20 \
  --model_agg_plots o3-mini-2025-01-31 \
  --num_cite_rounds 20
```

若干 Worker 并行跑实验，遇到 CUDA 内存不足这类失败，自适应调试会尝试修复（比如换小模型）再重试，调试次数受 `max_debug_depth` 限制。实验结束后，`experiments/"timestamp_ideaname"/logs/0-run/` 目录下会生成树搜索的可视化 `unified_tree_viz.html`。最后进入 writeup 阶段，聚合实验数据、生成图表、写 LaTeX 论文，这一步通常要 20 到 30 分钟，产出 `timestamp_ideaname.pdf`。

## 五、那篇"通过评审"的论文，该怎么读

2025 年 3 月，SakanaAI 宣布一篇完全由 AI Scientist-v2 生成的论文在 ICLR 的 workshop 上走完了同行评审。论文题为《Compositional Regularization: Unexpected Obstacles in Enhancing Neural Network Generalization》，三位评审给了 6、7、6，均分 6.33，高于该 workshop 的接收阈值。据 SakanaAI 所知，这是第一篇完全由 AI 生成、通过标准同行评审流程的论文。

读这个结果时，有几个背景要放进去：

- 那是个 **workshop**，不是主会议。ICLR 之类顶会主会议的接收率通常在 20% 到 30%，而像这次投稿的 ICBINB workshop 接收率在 60% 到 70%。过了 workshop 的线，不等于过了主会议的线。
- 作者自己按主会议标准内部评审了全部 3 篇 AI 论文，结论是都不够主会议门槛。那篇过线的论文，主题是个负结果（negative result）——它报告的是"新正则化方法没能提升组合泛化"——而这恰恰是 ICBINB 鼓励的方向。
- 这次评审是 SakanaAI 与 ICLR 及 workshop 组织方协作的实验。按事前约定，即使论文过线，也会在发表于 OpenReview 前撤稿；也就是说，它达到了接收线，但没有真的被发表。
- 评审中暴露了 AI 系统的毛病：它把"基于 LSTM 的网络"错误引用到了 Goodfellow 2016，而正确出处是 Hochreiter 与 Schmidhuber 1997。

所以正确的读法是：这证明了"AI 能生成达到 workshop 接收标准的论文"这件事发生了，但离"达到顶会主会议标准"还有距离。数字本身（6.33、60%-70%）是评估的语境，不是能力的上限。

## 六、适用边界与采用建议

该在什么场景用它：

- **当你是研究者、想要新的实验方向时**：v2 可以作为 idea 生成器，给定一个宽泛主题，让它产出候选假设和实验方案，你从中挑有潜力的。这一步成本很低，ideation 一般只要几美元。
- **当你有强起始模板、目标明确时**：继续用 v1 更划算。README 明确说 v2 在这种场景不一定更好，反而成功率更低。v2 的"更广探索"是以成功率为代价换来的。
- **当你只想验证流程、不想烧太多钱时**：一次完整运行，实验阶段用 Claude 3.5 Sonnet 大约 $15-20，写作用默认模型约 $5，加上 ideation 几美元，总成本在一个量级。预算和 `num_workers`、`steps` 直接相关，可以先调小跑通再放大。

三条边界必须记住：

1. **成本与成功率挂钩**。成功率取决于实验阶段用的模型和 idea 的复杂度，用 Claude 3.5 Sonnet 一般更高。跑不出 PDF 或 review 是常见结果，不是 bug。
2. **必须在沙箱里跑**。系统会执行 LLM 生成的代码，可能装危险包、访问网络、拉起进程。README 要求用 Docker 容器隔离。
3. **发表要披露**。许可证要求在任何由此产生的论文里清楚披露 AI 的使用，Abstract 或 Methods 里加归属声明。

树搜索的实现基于 AIDE，作者也在 README 里致谢了。这意味着这一层的改进可以顺着 AIDE 的迭代继续走。

## 结语

AI Scientist-v2 的价值要分开看。作为"自动生成论文"的系统，它目前的产出离顶会主会议还有距离，成本也不低。作为"把实验设计交给模型"的工程实验，它把开放式科研探索往前推了一步——第一篇 AI 生成的论文拿到高于接收线的评审分这件事，本身就是测量尺上的一次移动。用的时候别把它当成稳定的论文生产线，当成一个能帮你提出假设、跑通完整科研流程的探索工具更恰当。