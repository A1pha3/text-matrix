---
title: "llmfit：一条命令找出你的硬件能跑哪些大模型"
date: 2026-08-19T03:26:14+08:00
slug: "llmfit-local-model-hardware-fit"
github_repo: "AlexsJones/llmfit"
source_key: "gh:AlexsJones/llmfit"
description: "llmfit 是一个 Rust 编写的终端工具，自动检测本地 RAM、CPU、GPU，为数百个模型计算内存适配度、速度与质量评分，帮你用一条命令选出能在这台机器上顺畅运行的 LLM。"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "Rust", "本地模型", "命令行工具"]
---

# llmfit：一条命令找出你的硬件能跑哪些大模型

本地跑大模型的第一个问题永远是同一个：**我这台机器到底带得动哪些模型？** 每次翻着 Model 卡片的参数量，对照自己 16GB 还是 64GB 内存反复心算，还要担心某个量化版会不会 OOM——llmfit 把这件反复无常的事收敛成了一条命令。

## 一分钟总览

llmfit 是一个 Rust 编写的终端工具（默认 TUI 界面，也提供经典 CLI 模式）。它检测你的硬件（RAM、CPU、GPU/VRAM、后端），然后为目录里几百个模型逐一给出**内存适配度、预估速度、质量、上下文长度**四个维度的评分，并排出一个"在你机器上真的能跑"的榜单。

```
llmfit                # 交互式 TUI：你的硬件 + 每个模型的 fit 排名
llmfit fit            # 表格列出所有模型按适配度排名
llmfit recommend --json   # 输出推荐列表（给脚本/Agent 用）
llmfit info "<model>"     # 单个模型的适配分析 + 验证命令
llmfit bench          # 对正在运行的 provider 实测真实 tok/s 与 TTFT
llmfit doctor         # 硬件检测报告（提 bug 用）
```

它不是"替你下载模型"的工具，而是**决策工具**：告诉你在动手下载之前，某个模型在这台机器上到底行不行、能到什么速度，并给你可验证的命令。

## 它怎么判断"能不能跑"

核心是一个基于内存带宽的估算模型。llmfit 先探测硬件规格，然后对目录中的每个模型，按四个维度打分：

- **内存适配（fit）**：模型权重 + KV cache 是否能塞进你的可用内存/显存。它正确区分 MoE（Mixture-of-Experts，混合专家）架构——只按激活参数而非总参数量估算内存，所以 Mixtral、DeepSeek-V3 这类模型不会被总参数量吓退。
- **速度预估**：由内存带宽模型推算，输入来自运行时采样和社区真实测量。
- **质量与上下文**：模型本身的品质分和上下文窗口。

关键在于**每个预估都带着输入条件**。`llmfit info` 会展示一个数字"假设了什么、怎么在你的机器上验证"。这是 llmfit 1.0 之后最重要的变化：数字不再是无源之水，而是可核实、可替代的。

### 实测闭环

`llmfit bench` 会把"估算"升级成"实测"。下载模型、跑起来、测量真实 tok/s 和 TTFT（time to first token，首 token 延迟），然后把结果**作为 PR 回馈给项目**——不需要 gh CLI，不需要第三方账号。每次运行先存本地，你自己的测量会替换表格里的估算值，合并进下一次发布。之后任何一台相同硬件的人，在你跑 benchmark 之前就能直接看到打勾的实测数字。

这个设计把"社区排行榜"从一个营销概念变成了自举的数据闭环：每个人贡献自己的硬件测量，榜单质量随使用人数增长。

## 安装与上手

llmfit 支持 Homebrew、Scoop、MacPorts、uv/pip、Docker/Podman，以及源码构建：

```sh
brew install AlexsJones/llmfit/llmfit   # macOS/Linux 预编译
# 或
curl -fsSL https://llmfit.axjns.dev/install.sh | sh
# 或
uv tool install -U llmfit
```

第一次跑 `llmfit` 会看到类似这样的 TUI：顶部是你的机器规格，下方是每个模型的四维评分和适配度排名。如果你是脚本或 Agent 场景，`llmfit recommend --json` 输出的 JSON 可以直接被解析：

```sh
llmfit recommend --use-case coding --json | jq '.models[].name'
```

### 本地运行 provider

llmfit 不自己托管模型，而是把推理交给本地运行时：

- **Ollama**
- **llama.cpp**
- **MLX**（Apple Silicon）
- **Docker Model Runner**
- **LM Studio**

配合 `--use-case coding` 这类场景筛选，它会在这些后端之上给出针对性的模型推荐。

## 适用边界

- **适合**：想跑本地模型但不确定该下哪个的人；想比较"换更大模型值不值"的人；做模型选型时想拿实测数据说话的人。
- **不适合**：只依赖云 API、没有本地推理需求的人——llmfit 的整个价值建立在"你有一台要跑模型的机器"之上。
- **注意**：速度是估算，尤其是尚未被社区实测覆盖的硬件组合。真正的确定性来自 `llmfit bench` 实测闭环。

## 和其他工具的关系

README 里明确对比了 `llm-checker`：那是 Node.js 写的、通过 Ollama 直接拉模型实测的工具，走的是"真跑一遍"路线，适合已装 Ollama、想看真实性能的人；但它不区分 MoE，Mixtral 这类模型会被按总参数量估算内存。llmfit 走的是"先估算、后可实测验证"路线，两者的取舍正好互补。

## 小结论

llmfit 解决的不是"哪个模型最好"，而是"哪个模型在我这台机器上最可能跑得动、跑得快"——这个问题的答案，过去要么靠猜，要么靠下载后撞 OOM 才能知道。它把模型选型的决策成本压到一条命令，并且用实测反馈闭环让估算越来越准。如果你正在给本地推理选型，值得跑一次 `llmfit` 看看你的硬件到底有多少潜力。
