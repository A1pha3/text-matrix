---
title: "Needle：14MB 的端侧工具调用模型，用字节级语法约束把 token 焊死"
date: 2026-08-15T03:24:06+08:00
slug: "needle-tiny-tool-calling-model"
github_repo: "cactus-compute/needle"
source_key: "gh:cactus-compute/needle"
description: "Needle 是 cactus-compute 开源的端侧小模型：45M 参数、单个 14MB 二进制，面向工具调用、设备控制与结构化抽取。基于 Simple Attention Network，压缩到 CQ2-bit，带置信度门控与受限内存设计，整场会话约 28MB RAM。"
draft: true
categories: ["技术笔记"]
tags: ["端侧AI", "小模型", "工具调用", "Simple Attention Network", "边缘计算"]
---

# Needle：14MB 的端侧工具调用模型，用字节级语法约束把 token 焊死

**核心判断**：Needle 解决的问题是"小到什么程度还能可靠地调用工具"。它的答案是 45M 参数、单个 14MB 二进制、整场会话约 28MB RAM——却把工具调用做成结构化 JSON 输出，并用**字节级语法约束**（byte-level grammar）让解码的每个 token 都必须在合法范围内。这种"语法约束保证输出结构、置信度门控保证行动质量"的组合，是它区别于普通小模型的关键。

## 为什么值得看

Needle（官方称 Needle 2）是 cactus-compute 开源的端侧模型，主打工具调用（tool calling）、设备使用（device use）与结构化抽取（structured extraction）。当前约 5.5k star（Python 包，MIT 许可）。它在 benchmark 上与小模型（FunctionGemma 270M、LFM2.5 230M、Apple FM 等）互有胜负，但体积小 5x 到 70x，且用 2-bit 对比它们的 f16。

核心设计来自 **Simple Attention Network**（论文 arXiv:2607.18363）：用 Hadamard MLP 替代 FFN、GQA 注意力、engram 键值记忆、多通道超连接。压缩到 CQ2-bit（Cactus Quants），并内置到自己的推理引擎里。

## 系统地图

```
工具描述（Python 装饰器 / Pydantic schema）
      │
      ▼
Needle 引擎（14MB 单二进制，权重内嵌）
  · 字节级语法约束：从 schema 编译，约束每个 token
  · 置信度门控：learned head 输出校准置信度
  · 工具检索：大目录里每轮只渲染 top5 工具
  · 受限内存：256-token 滑动窗口，工具钉作 KV sinks
      │
      ▼
结构化结果（JSON）→ 执行 → 结果回喂 → 最终响应
```

## 关键机制

### 字节级语法约束

工具调用以"文本进、JSON 出"为契约。模型从你的 schema 编译出一个字节级 grammar，解码时约束每个 token——模型根本不可能生成不合法的 JSON 结构。这把"输出结构正确"从概率问题变成硬约束。

### 置信度门控

每个响应都带一个从 learned head 得到的校准置信度。你可以设阈值：置信度之上直接行动，之下则升级（escalate）给人或更强模型。这让小模型能在"有把握时自主、没把握时求助"之间找到平衡。

### 工具检索 + 受限内存

可以声明一个很大的工具目录，内置检索头每轮只渲染 top5 工具，并把语法约束限制到该子集。同时用 256-token 滑动窗口，工具作为 KV sinks 钉住，因此无论对话多长，总内存都稳定在约 28MB。

## 快速上手

安装：

```bash
pip install cactus-needle
```

最简单的工具调用——用装饰器描述工具，`run()` 完成闭环：

```python
import needle

@needle.tool
def get_weather(city: str):
    "Get the current weather for a city."
    return {"city": city, "temp_c": 27, "sky": "clear"}

agent = needle.Needle(tools=[get_weather])
print(agent.run("what's it like in Lagos right now?")["results"])
# [{'city': 'Lagos', 'temp_c': 27, 'sky': 'clear'}]
```

结构化抽取——传一个 Pydantic 模型，返回类型化对象：

```python
from pydantic import BaseModel

class Invoice(BaseModel):
    vendor: str
    total: float
    due_date: str

invoice = needle.extract("Invoice from Acme Corp, $1,200.00, due 2026-09-01", Invoice)
print(invoice.vendor, invoice.total)   # -> Acme Corp 1200.0
```

浏览器试玩：

```bash
needle playground    # http://127.0.0.1:7860
```

## LoRA 微调

Needle 在冻结基座上做 LoRA 微调，导出时合并 adapter，微调后的模型仍是单个 `.cact` 文件，跑在同一个引擎上。流程是：合成数据（可选）→ LoRA 微调 → 构建微调后的 `.cact`。

```bash
export OPENROUTER_API_KEY=sk-or-...
needle generate-data --tools my_tools.json --num-samples 500 --output data.jsonl
needle finetune data.jsonl --epochs 10
```

训练用纯 JAX，可在任意 JAX 支持的加速器上跑（NVIDIA 用 CUDA 构建，Apple Silicon 用 `metal` extra 跑 GPU）。

## 适用边界

- **适合**：端侧 / 离线工具调用、设备控制、结构化抽取；内存与体积受限的场景（手机、可穿戴、智能家居、机器人）。
- **边界**：这是 45M 参数小模型，能力上限远低于大模型；"与 FunctionGemma 等互有胜负"是特定 benchmark 上的观察，不代表通用能力对等。
- **设计取舍**：权威信息以论文与 README 为准；离线环境（air-gapped）的搭建方式见 `doc/apis.md`。

## 进一步阅读

- 权重：<https://huggingface.co/Cactus-Compute/needle2>
- Simple Attention Network 论文：<https://arxiv.org/abs/2607.18363>
- API / 微调文档：`doc/apis.md`、`doc/finetuning.md`
