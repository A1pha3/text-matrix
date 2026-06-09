---
title: "whichllm：自动检测本机硬件，推荐当下最值得跑的开源大模型"
date: "2026-06-09T17:59:00+08:00"
slug: "whichllm-local-llm-recommender"
aliases:
  - "/posts/tech/whichllm-local-llm-recommender/"
description: "whichllm 用一行命令自动检测 GPU/CPU/RAM，从 HuggingFace 实时拉取候选模型，按 VRAM 适配 + 真实 benchmark + 推理速度三维度给出排名，是本地 LLM 选型的事实标准 CLI。"
draft: false
categories: ["技术笔记"]
tags: ["whichllm", "LocalLLM", "HuggingFace", "GGUF", "GPU", "Python"]
---

# whichllm：自动检测本机硬件，推荐当下最值得跑的开源大模型

> **目标读者**：本地跑开源大模型、想搞清"我这张卡到底能跑什么 / 该选哪个" 的开发者
> **核心问题**：HuggingFace 上万个模型，硬件又是 N 卡 / A 卡 / Apple Silicon / 纯 CPU 各种组合，怎么用一行命令给出可信赖的答案？
> **难度**：⭐⭐（装 Python 3.11+ 跑命令即可）
> **来源**：GitHub [Andyyyy64/whichllm](https://github.com/Andyyyy64/whichllm)，3,742 ★ / MIT / 2026-06-09

---

## 一、核心判断

whichllm 解决的不是"模型能不能塞进显存"——这是 VRAM 算式就能回答的题。它真正解决的是 **"塞得进去的几个模型里，哪个才是当下最值得跑的"**：

- 把"刚好能装下"升级成"综合考虑 benchmark、量化、速度、置信度、时新性之后的最优选"
- 把"过时的 leaderboard 排序"降权，避免 2024 年的老模型靠陈旧分数赢过 2026 年同尺寸新模型
- 把"显存估算"拆成权重 + GQA KV cache + 激活 + 开销，而不是简单 `params × bytes`
- 把"速度"按带宽建模，分清 MoE 活跃参数 vs 总参数、统一内存 vs PCIe 卸载

一句话：**这是一个用基准分数证据链 + 硬件建模做选型的 CLI，不是"按显存找模型"**。

---

## 二、项目概览

| 维度 | 数据 |
|---|---|
| **仓库** | [Andyyyy64/whichllm](https://github.com/Andyyyy64/whichllm) |
| **Stars** | 3,742 ★（2026-06-09 抓取） |
| **License** | MIT |
| **语言** | Python 3.11+ |
| **分发** | PyPI、Homebrew、uvx、pip |
| **协议** | 仅读 HuggingFace 公开 API，无登录要求 |

安装一行：

```bash
uvx whichllm@latest            # 一次性运行，零安装
uv tool install whichllm       # 频繁使用，推荐
brew install andyyyy64/whichllm/whichllm
```

---

## 三、它到底算什么账

### 3.1 硬件自动检测

`whichllm` 不问用户卡型，直接探测：

- NVIDIA / AMD / Apple Silicon / 纯 CPU
- VRAM 容量、系统 RAM、内存带宽
- 是否为统一内存架构（影响部分卸载策略）

例：想升级显卡时，先模拟再下单：

```bash
whichllm --gpu "RTX 4090"
whichllm upgrade "RTX 4090" "RTX 5090" "H100"
```

### 3.2 评分三件套：基准分 × 速度 × 时新性

**基准分**融合多个真实评测源（LiveBench、Artificial Analysis、Aider、Chatbot Arena ELO、Open LLM Leaderboard、multimodal/vision）。每条分数带一个证据标签：

- `direct` — 直接在该模型上跑出
- `variant` — 同架构兄弟模型的分数（折扣使用）
- `base` — 基座模型分数
- `interpolated` — 跨族插值（最低折扣）
- `self-reported` — 上传者自报（默认拒绝跨族继承）

**时新性**：分数会带"快照日期"，对陈旧 leaderboard 的同 lineage 模型降权。这意味着 2024 年的 Qwen2.5-72B 不会用一份 2024 的旧榜赢过 2026 年的 Qwen3.6-27B。

**速度**：按"带宽受限"建模，结合量化效率、后端因子、MoE 活跃 vs 总参数、统一内存部分卸载策略，输出 `estimated_tok_per_sec` + `speed_confidence` + 范围区间。

### 3.3 显存估算拆成四件

```
VRAM = 权重 + GQA KV cache + 激活 + 开销
```

简单 `params × bytes` 的算式会让 `Qwen2.5-72B Q4` 显示"刚好能跑"，但 1k 上下文时 KV cache 把可用显存吃光。whichllm 按上下文长度单独算 KV cache。

---

## 四、五条核心命令

```bash
whichllm                       # 给当前硬件排名 top 模型
whichllm plan "llama 3 70b"    # 反向：跑这个模型需要什么 GPU
whichllm run "qwen 2.5 1.5b gguf"   # 一键拉模型 + 开聊
whichllm snippet "qwen 7b"     # 打印可粘贴运行的 Python 代码
whichllm --top 1 --json        # JSON 输出，接 jq 接脚本
```

`run` 子命令用 `uv` 拉起隔离环境、装依赖、下载模型、开聊；`snippet` 适合直接嵌到自己的 Python 工具里。

---

## 五、典型输出（README 实样）

```text
$ whichllm --gpu "RTX 4090"

#1  Qwen/Qwen3.6-27B     27.8B  Q5_K_M   score 92.8    27 t/s
#2  Qwen/Qwen3-32B       32.0B  Q4_K_M   score 83.0    31 t/s
#3  Qwen/Qwen3-30B-A3B   30.0B  Q5_K_M   score 82.7   102 t/s
```

第三行是 MoE 102 t/s——速度按"活跃参数"算，benchmark 分数按"总参数"算，两者分账展示。

---

## 六、实拍硬件推荐（2026-05 快照）

| 硬件 | VRAM | 首推 | 速度 |
|---|---|---|---|
| RTX 5090 | 32 GB | `Qwen3.6-27B` Q6_K · score 94.7 | ~40 t/s |
| RTX 4090 / 3090 | 24 GB | `Qwen3.6-27B` Q5_K_M · score 92.8 | ~27 t/s |
| RTX 4060 | 8 GB | `Qwen3-14B` Q3_K_M · score 71.0 | ~22 t/s |
| Apple M3 Max | 36 GB | `Qwen3.6-27B` Q5_K_M · score 89.4 | ~9 t/s |
| 纯 CPU | — | `gpt-oss-20b` (MoE) Q4_K_M · score 45.2 | ~6 t/s |

> ⚠️ 这份快照是 README 抓取时的硬编码；线上跑 `whichllm` 会拉取 HuggingFace 实时数据，结果可能更新。

---

## 七、和 Ollama / LM Studio 的关系

whichllm 不替代推理运行时，它做"选型"。和 Ollama 的经典配合：

```bash
# 1. 拿到当前硬件最值得跑的 HuggingFace 模型 ID
whichllm --top 1 --json | jq -r '.models[0].model_id'

# 2. 映射到本地 Ollama 模型名，跑起来
ollama run qwen3.6:27b
```

---

## 八、适用边界

**适合**：
- 想买显卡 / 升级前先模拟
- 已有机器但不知道跑什么模型"最香"
- 需要把模型推荐嵌入 CI / 脚本（`--json` + jq）
- 想本地跑开源模型但被"几千个 GGUF + 几十种量化"劝退

**不适合**：
- 服务端 GPU 集群选型（它假设单卡/单节点）
- 需要做训练/微调选卡
- 想要图形界面——它就是 CLI

---

## 九、阅读路径

```bash
# 0. 一行体验
uvx whichllm@latest

# 1. 看自己机器的 top 3
whichllm --top 3

# 2. 看升级候选
whichllm upgrade "我的卡名" "RTX 5090"

# 3. 反向：跑这个模型需要什么卡
whichllm plan "Qwen2.5-72B"

# 4. 一键开聊
whichllm run
```

如果你已经在本地跑开源模型、只是没找到"最该跑哪个"的可靠答案，whichllm 值得加进工具箱——它做的事比 "Ollama 搜索" 多三件事：**证据链评分、时新性降权、硬件建模**。
