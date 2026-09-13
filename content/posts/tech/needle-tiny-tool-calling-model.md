---
title: "Needle：14MB 的端侧工具调用模型，用字节级语法约束把 token 焊死"
date: 2026-08-15T03:24:06+08:00
slug: "needle-tiny-tool-calling-model"
github_repo: "cactus-compute/needle"
source_key: "gh:cactus-compute/needle"
description: "Needle 是 cactus-compute 开源的端侧小模型：45M 参数、单个 14MB 二进制，面向工具调用、设备控制与结构化抽取。基于 Simple Attention Network，压缩到 CQ2-bit，带置信度门控与受限内存设计，整场会话约 28MB RAM。"
draft: false
categories: ["技术笔记"]
tags: ["端侧AI", "小模型", "工具调用", "Simple Attention Network", "边缘计算"]
---

# Needle：14MB 的端侧工具调用模型，用字节级语法约束把 token 焊死

**核心判断**：Needle 解决的问题是"小到什么程度还能可靠地调用工具"。它的答案是 45M 参数、单个 14MB 二进制、整场会话约 28MB RAM——却把工具调用做成结构化 JSON 输出，并用**字节级语法约束**（byte-level grammar）让解码的每个 token 都必须在合法范围内。语法约束负责输出结构永远合法，置信度门控负责行动质量可托付，这个分工是它区别于普通小模型的地方。

## 为什么值得看

Needle 2 是 cactus-compute 开源的端侧模型，主打工具调用（tool calling）、设备使用（device use）与结构化抽取（structured extraction）。仓库约 1.1 万 star，Apache-2.0 许可（2026 年 9 月查询）。它在 benchmark 上与小模型（FunctionGemma 270M、LFM2.5 230M、Apple FM 等）互有胜负，但体积小 5 到 70 倍，且用 2-bit 对比它们的 f16。

这个"互有胜负"要怎么读，直接决定了要不要用它。README 只给了定性结论和一张体积-质量前沿图，没有逐项分数表。能确定的是：在单位体积的工具调用能力上，Needle 2 与 5 到 70 倍于它的模型有来有回。不能确定的是：benchmark 具体覆盖哪些任务、2-bit 量化损失了多少质量、以及"互有胜负"在任何意义上等于通用能力对等——45M 模型的知识容量和推理深度上限就在那里。

架构来自 **Simple Attention Network**（论文 arXiv:2607.18363），压缩到 CQ2-bit（Cactus Quants 的 2-bit 方案），并烧进自己的推理引擎：权重内嵌在单个 14MB 二进制里，引擎从 Hugging Face 拉取一次后缓存，推理全程不发网络请求。

## 系统地图

```
工具描述（Python 装饰器 / Pydantic schema）
      │
      ▼
Needle 引擎（14MB 单二进制，权重内嵌，推理无网络）
  · 字节级语法约束：从 schema 编译，约束每个 token
  · 置信度门控：learned head 输出校准置信度
  · 工具检索：大目录里每轮只渲染 top5 工具
  · 受限内存：256-token 滑动窗口，工具钉作 KV sinks
      │
      ▼
结构化结果（JSON）→ 执行 → 结果回喂 → 最终响应
```

## 架构：Simple Attention Network

Simple Attention Network 是 Cactus 的稠密小模型配方，四个组件各管一件事：

- **Hadamard MLP 替代 FFN**。传统前馈层是两个大矩阵乘法；这里换成沃尔什-哈达玛变换（Walsh-Hadamard transform）——一个固定正交矩阵，以 n log n 时间完成，没有任何可学习权重需要读。省掉的就是小模型最贵的东西：参数量。
- **GQA 注意力**（Grouped-Query Attention，分组查询注意力）。多个查询头共享一组键值头，压的是 KV 缓存。
- **engram 键值记忆**。键值对不是从投影矩阵算出来的，而是从 n-gram 哈希表里直接取行——相当于把高频模式预制成可查表。engram 站点只在两层触发。
- **多通道超连接**（multi-lane hyper-connections）。网络同时维护四条残差流，每层的更新规则作用在四条流拼平后的 RMS 归一化表示上；路由 logits 经 Sinkhorn 迭代归一化成双随机矩阵。注意力和 MLP 两条残差都做三明治归一化和门控，a、b、g 和所有 σ 门控都是可学习、依赖输入的。

这套配方的设计与消融细节在论文里；对使用者的含义是一句话：45M 参数被安排在"注意力 + 查表 + 固定变换"上，几乎没有浪费在冗余前馈上。

## 关键机制

### 字节级语法约束

工具调用以"文本进、JSON 出"为契约。模型从你的 schema 编译出一个字节级 grammar，解码时约束每个 token——模型生成不出不合法的 JSON 结构，参数枚举值、数值边界这类约束也一并编进去。这把"输出结构正确"从概率问题变成硬约束。

### 置信度门控

每个响应都带一个从 learned head 得到的校准置信度。设一个阈值：置信度之上直接行动，之下则升级（escalate）给人或更强模型。这让小模型能在"有把握时自主、没把握时求助"之间划出明确界线，而不是靠 prompt 祈祷它别乱来。

### 工具检索 + 受限内存

可以声明一个很大的工具目录，内置检索头每轮只渲染 top5 工具，并把语法约束限制到该子集。同时用 256-token 滑动窗口，工具作为 KV sinks（键值汇，固定不参与滑动的缓存锚点）钉住。两者合起来，无论对话多长，总内存都稳定在约 28MB。

## 一次工具调用的完整流转

用 README 的天气例子把机制串起来——`what's it like in Lagos right now?`：

1. 你用 `@needle.tool` 装饰 `get_weather`，函数签名给出参数类型，docstring 就是工具描述。Needle 读的就是这些描述来决定调什么、怎么填参数——README 原话是"描述好工具就是全部功夫"（describing them well is the whole game）。
2. 引擎从 schema 编译字节级 grammar。
3. 每轮推理，检索头从工具目录选出 top5，语法约束收窄到这个子集。
4. 模型在 256-token 窗口内解码；工具描述作为 KV sinks 固定，不随窗口滑动。
5. 逐 token 采样时，每个字节都必须落在 grammar 允许的集合内，产出合法 JSON：`{"city": "Lagos", ...}`。
6. Needle 解析 JSON、执行你的 Python 函数、把结果回喂给模型。
7. 模型生成最终自然语言响应；响应附带 learned head 给出的置信度分，`results` 字段带回已执行的工具结果。

整条链路里没有一步"希望模型输出格式正确"——格式由 grammar 保证，要不要采纳这次行动由置信度决定。

## 快速上手

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

逐参数描述、枚举选项、数值约束编入解码 grammar、原始 JSON schema、用 `complete()` 自己驱动循环、system facts、置信度门控参数，这些都在 `doc/apis.md`。离线（air-gapped）设备的安装方式也在那份文档里。

浏览器试玩：

```bash
needle playground    # http://127.0.0.1:7860
needle playground --weights my.cact    # 加载自己微调的模型
```

server 会先下载并初始化模型再开始服务，所以首次查询即时返回。页面上还有个 **Finetune on these tools** 按钮，直接从 UI 跑下面这条微调管线，交回一个可下载的 `.cact` 文件。

## 现成环境：不用从零描述工具

`needle.environments` 内置六套现成工具面：`smart_home`、`media_player`、`productivity`、`wearable`、`kitchen_appliance`、`data_capture`。每套都是手工策划的工具集，枚举、数值边界和描述都对齐 Needle 的受限解码，并附带一个现成 agent 和一套冻结的验收测试：

```python
from needle.environments import smart_home

smart_home.agent.complete("dim the study lights to 30 percent")
smart_home.run_tests()
```

也可以从 shell 跑：`python -m needle.environments.smart_home`。要把环境适配成自家产品，改 `Literal` 值（房间、联系人、类别）而保持结构：闭集用枚举、数值设边界、自由文本原样复制、工具数控制在五个以内。细节在 `doc/environments.md`。

## LoRA 微调

Needle 在冻结基座上做 LoRA（Low-Rank Adaptation，低秩适配）微调，导出时把 adapter 合并回去，微调后的模型仍是单个 `.cact` 文件，跑在同一个引擎上。流程是：合成数据（可选）→ LoRA 微调 → 构建微调后的 `.cact`。

训练栈不随运行时包安装，先装 train extra：

```bash
pip install "cactus-needle[train]"
```

**数据格式**：JSONL，一行一个样本。`reasoning` 字段可选；跑题样本写 `answers: []`：

```json
{"query": "dim the kitchen to 10", "tools": [{"name": "set_lights", "parameters": {"type": "object", "properties": {"room": {"type": "string"}, "brightness": {"type": "integer"}}, "required": ["room"]}}], "answers": [{"name": "set_lights", "arguments": {"room": "kitchen", "brightness": 10}}], "reasoning": "'kitchen' -> room; 'dim to 10' -> brightness 10"}
```

**1. 合成数据（可选）**。需要 `OPENROUTER_API_KEY`，可从工具 schema 文件生成，也可用 `--augment` 扩充现有数据集；设 `OPENROUTER_URL` 可换成任意 OpenAI 兼容网关：

```bash
export OPENROUTER_API_KEY=sk-or-...
needle generate-data --tools my_tools.json --num-samples 500 --output data.jsonl
needle generate-data --augment data.jsonl --num-samples 500
```

**2. LoRA 微调**。基座 checkpoint 不传 `--checkpoint` 时自动从 Hugging Face 下载；`--generate N` 会先从数据里的工具再合成 N 条样本（同样需要 OpenRouter key）。关键参数：`--epochs` 默认 3、`--lora-rank` 16、`--lora-alpha` 32、`--lr` 1e-4、`--batch-size` 16、`--max-len` 1024、`--val-split` 0.1。adapter 默认写到 `checkpoints/needle_lora.pkl`，每个 epoch 从留出集打印一次验证损失：

```bash
needle finetune data.jsonl --epochs 10
needle finetune data.jsonl --epochs 10 --generate 300 --lora-rank 16 --lora-alpha 32
```

训练是纯 JAX，跑在任意 JAX 支持的加速器上。NVIDIA 机器装 `pip install "cactus-needle[train,gpu]"`；Apple Silicon 用 `metal` extra 跑 GPU：

```bash
pip install "cactus-needle[train,metal]"
```

**3. 构建微调后的 `.cact`**。合并 adapter 并量化，基座缺失时自动下载。默认导出跟随 checkpoint 声明的逐层位图（未声明时回落到 4-bit），加 `--bits 2` 得到更小的模型：

```bash
needle build checkpoints/needle2.pkl --lora checkpoints/needle_lora.pkl --out my_needle.cact
```

设 `NEEDLE_HF_REPO=<you>/<model>` 并加 `--upload` 可发布到 Hugging Face；任何机器上 `needle download <you>/<model>/my_needle.cact` 拉取，`needle download <platform>`（如 `macos-arm64`）拉取对应平台的引擎。

**4. 直接运行**。引擎与权重无关（weights-agnostic），微调后的 `.cact` 无需重新编译：

```python
import needle
agent = needle.Needle(weights="my_needle.cact", tools=[...])
agent.run("...")
```

## 适用边界

- **适合**：端侧 / 离线工具调用、设备控制、结构化抽取；内存与体积受限的场景（手机、可穿戴、智能家居、机器人）。项目描述里点名的目标设备就是这四类。
- **不适合**：需要长链路推理、开放域知识问答或复杂多工具编排的任务——45M 参数的知识容量决定了天花板。需要顶级自然语言生成质量的场景同理。
- **隐私**：推理本身无网络请求，但 Python 包默认收集匿名遥测（函数名、包版本、操作系统，不含 prompt、输出或数据）。介意就用 `NEEDLE_TELEMETRY=0` 或 `DO_NOT_TRACK=1` 关掉。
- **采用顺序建议**：先用 `needle playground` 验证你的任务在基座模型上的可行性，再决定是直接用、套现成环境，还是走微调。要动手描述自己的工具时，把工具描述当成 prompt 的一部分来写——模型调用的依据就是它。

## 进一步阅读

- 权重：<https://huggingface.co/Cactus-Compute/needle2>
- Simple Attention Network 论文：<https://arxiv.org/abs/2607.18363>
- API / 微调 / 环境文档：`doc/apis.md`、`doc/finetuning.md`、`doc/environments.md`
- 学术引用：*Needle 2: A 45M-Parameter Foundation Tool-Calling Model for Tiny Devices*，Cactus Compute 团队（Henry Ndubuaku、Karen Mosoyan 等 8 人），2026
