---
title: "RLM 推理范式拆解：用 CodeAct REPL 让 LLM 自己递归处理无限长上下文"
date: "2026-06-18T15:06:00+08:00"
slug: "alexzhang13-rlm-recursive-language-models-guide"
description: "alexzhang13/rlm 是 MIT OASYS 实验室开源的 Recursive Language Models 推理引擎，用 CodeAct REPL 让 LLM 在代码环境里递归调用自己处理近无限长上下文。本文拆解其 RLM 范式与多 sandbox 适配器。"
draft: false
categories: ["技术笔记"]
tags: ["RLM", "CodeAct", "REPL", "长上下文", "Python", "递归推理"]
---

# RLM 推理范式拆解：用 CodeAct REPL 让 LLM 自己递归处理无限长上下文

`alexzhang13/rlm` 想颠覆的不是"如何让 LLM 更准"，而是"如何调用 LLM 本身"。传统接口是 `llm.completion(prompt, model)`——把整段 prompt 塞进上下文窗口；RLM 提出的是 `rlm.completion(prompt, model)`——把 prompt 当成代码环境里的变量，让 LLM 在 REPL 里**编程式**地审视、拆解、递归调用自己。截至 2026 年 6 月，这个由 MIT OASYS 实验室开源的项目（4,977 Stars、MIT、配套 arXiv:2512.24601）已经发展出 7 种 sandbox 适配器（local / ipython / docker / modal / prime / daytona / e2b），并附带基于 Prime Intellect prime-rl 的训练环境。

本文是一篇原理拆解。文章会先讲 RLM 与传统 completion 调用范式的边界，再拆 CodeAct REPL、递归子调用、多 sandbox 适配三层机制，最后用一个具体任务跑通"超长 prompt → 编程式拆解 → 递归子 LM"的完整链路。

## 一、核心判断：RLM 不是"更长的上下文窗口"，而是"调用范式"的重写

RLM 论文的开篇就给出了与 RAG / 长上下文窗口完全不同的思路：

> Recursive Language Models (RLMs) are a task-agnostic inference paradigm for language models (LMs) to handle near-infinite length contexts by enabling the LM to programmatically examine, decompose, and recursively call itself over its input.

三个关键词值得拆解：

- **task-agnostic**：不绑定"摘要"、"问答"或"RAG"这类具体任务，RLM 提供的是调用范式本身
- **programmatically**：LLM 不是用自然语言读 prompt，而是在代码环境里写代码来访问 prompt
- **recursively**：LLM 可以在自己的代码里调用自己（子 LM），构成递归结构

这意味着 RLM 和 200k token 的 Gemini 1.5 不在同一抽象层——后者是"窗口更大"，前者是"调用方式改变"。论文作者把这个范式叫做 "language model"，因为从外部看，整个递归系统仍然是一个"从文本到文本的概率映射"，只是内部多了"代码执行 + 子调用"的能力。

## 二、系统地图：RLM 客户端 + REPL + 后端 LM 的三层结构

整张地图可以分成三层：

```
┌────────────────────────────────────────────────────────────────┐
│  L3 用户接口层                                                 │
│    rlm.completion(prompt, model) → response                    │
│    与传统 llm.completion 调用形态保持一致（drop-in 替换）       │
├────────────────────────────────────────────────────────────────┤
│  L2 REPL 环境层（可插拔 7 种 sandbox）                         │
│    LocalREPL / IPythonREPL / DockerREPL / ModalREPL /          │
│    PrimeREPL / DaytonaREPL / E2BREPL                           │
│    LLM 在这里写 Python 代码来访问 prompt 变量                 │
├────────────────────────────────────────────────────────────────┤
│  L1 LM 调用层                                                  │
│    主 LM（"根"）：负责写代码 / 做决策                          │
│    子 LM（"递归"）：被主 LM 在代码里调用，处理局部上下文     │
│    backend: openai / anthropic / vllm / ...                    │
└────────────────────────────────────────────────────────────────┘
```

下面逐层看每一层的关键机制。

## 三、L1 调用层：主 LM + 子 LM 的递归结构

RLM 的核心是把 `llm.completion` 包装成两层调用：

### 3.1 主 LM（root LM）

主 LM 拿到的不再是"原始 prompt + 上下文"，而是"一个 REPL 环境 + prompt 作为变量"。它的任务是**写代码**：

- 读取 prompt 的某一段
- 调用子 LM 处理该段
- 汇总子 LM 的输出
- 返回最终答案

主 LM 输出的不再是答案，而是 Python 代码——这段代码在 REPL 里执行后才得到最终答案。

### 3.2 子 LM（sub-LM）

子 LM 是被主 LM 在代码里 `print(rlm.completion(chunk, sub_model))` 调用的实例。它每次只看到 prompt 的局部（一个 chunk），不接触完整 prompt，也不接触 REPL。子 LM 的输出是普通文本，会被主 LM 继续处理。

### 3.3 递归

主 LM 可以在自己的代码里**再次**调用 `rlm.completion`——这就构成了递归。论文里把这种结构叫做 "Recursive LM"，因为从外部看"系统 → 文本"的映射本身就是一个 LM，只是内部递归。

这种范式的最大好处是**token 经济学**：主 LM 只在"做决策"时消耗 token，子 LM 各自只看局部——总 token 数远低于"把所有内容塞进上下文窗口"。

## 四、L2 REPL 环境层：7 种 sandbox 适配器

RLM 的安全性与可移植性来自 7 种可插拔 REPL 环境。论文和 README 把它们分成两组：本地非隔离 + 云端隔离。

### 4.1 本地非隔离（4 种）

- **`local`（默认）**：主进程内 `exec` 执行。同一虚拟环境、共享全局命名空间。适合本地 benchmark 与低风险任务。
- **`ipython`**：真实 IPython 会话，可选 `ipykernel` 子进程模式（提供 `cell_timeout` 与命名空间隔离）。通过 `pip install 'rlms[ipython]'` 安装。
- **`docker`**：在 `python:3.11-slim`（可自定义）容器内执行 REPL。提供文件系统级隔离。
- **默认实现细节**：`LocalREPL` 会构造一份"受限的 globals/locals 命名空间"——它仍然在主进程里跑，但模型能看到的名字是受控的，恶意 prompt 不能直接 `import os` 删本地文件。

### 4.2 云端隔离（3 种）

- **`modal`**：调用 Modal Sandboxes。子 LM 调用从宿主进程发起，确保主 LM 与 sandbox 解耦。需要 `modal setup` 认证。
- **`prime`**：调用 Prime Intellect Sandboxes（beta）。README 标注"目前运行时较慢，是一个 open issue"。
- **`daytona`** / **`e2b`**：Daytona 与 e2b 沙箱。这两家都提供云端代码执行环境，适合在多租户 / 生产场景下完全隔离不可信的 LM 输出。

这种"7 种 sandbox 可换"的设计让 RLM 既能在本地做 benchmark，也能在生产环境安全部署。论文在 7 种环境之间做了对照测试，结论是"功能等价但性能差异显著"。

## 五、L3 用户接口层：drop-in 替换 `llm.completion`

L3 故意做得非常薄，README 给出的最小例子：

```python
from rlm import RLM

rlm = RLM(
    backend="openai",
    backend_kwargs={"model_name": "gpt-5-nano"},
    verbose=True,
)

print(rlm.completion("Print me the first 100 powers of two, each on a newline.").response)
```

调用形态与 `openai.OpenAI().chat.completions.create(...)` 接近一致——这就是 README 强调的 "drop-in replacement"。项目作者显然希望 RLM 不是"另一种 LLM 库"，而是"调用现有 LLM 的另一种方式"。

`backend` 支持多种：`openai` / `anthropic` / `vllm`（本地 vLLM 服务）等。`backend_kwargs` 是透传给底层客户端的参数。

## 六、任务流案例：从 "1000 万行日志里找异常 IP" 到递归调用

下面用一个真实场景跑一遍完整流程。任务：从一段 800 MB 的日志文件里找出出现次数最多的 IP。

**Step 1：用户调用**

```python
rlm = RLM(backend="openai", backend_kwargs={"model_name": "gpt-5-nano"})
with open("huge.log") as f:
    log_text = f.read()  # 800 MB，远超任何 LLM 上下文窗口
print(rlm.completion(
    f"找出这段日志里出现次数最多的 IP 地址。日志如下：{log_text}"
).response)
```

**Step 2：主 LM 写出拆解代码**

主 LM 收到 REPL 环境，看到 `prompt` 变量里是 800 MB 日志。它不会试图"读完"日志，而是写一段 Python：

```python
# 主 LM 在 REPL 里写的代码
lines = prompt.split("\n")
# 按 10000 行切块
chunks = [lines[i:i+10000] for i in range(0, len(lines), 10000)]
# 并发调用子 LM 找每个 chunk 的 top IP
from concurrent.futures import ThreadPoolExecutor
def top_ip(chunk):
    from collections import Counter
    import re
    ips = re.findall(r"\d+\.\d+\.\d+\.\d+", "\n".join(chunk))
    return Counter(ips).most_common(5)

with ThreadPoolExecutor(max_workers=10) as ex:
    partials = list(ex.map(top_ip, chunks))
# 汇总
total = Counter()
for p in partials:
    for ip, cnt in p:
        total[ip] += cnt
FINAL = total.most_common(1)[0]
print(FINAL)
```

**Step 3：REPL 执行**

`LocalREPL`（或 `DockerREPL` / `ModalREPL`）执行这段代码，并发 10 个子任务（每个仍是同一 REPL 内部的 `top_ip` 函数，不会递归触发主 LM）。

**Step 4：递归子调用（可选）**

如果主 LM 决定"用正则太粗糙，需要 LLM 来识别 IP"，它可以这样写：

```python
# 递归调用：在代码里再次调用 rlm.completion
sub_results = []
for chunk in chunks[:5]:  # 只看前 5 个 chunk 做 demo
    sub = rlm.completion(f"从以下文本里识别 IP 并返回 JSON 列表：{chunk[:5000]}")
    sub_results.append(sub.response)
```

这里 `rlm.completion` 是递归调用——子 LM 只看 5000 token 的局部 chunk，返回 IP 列表，主 LM 在 REPL 里汇总。

**Step 5：主 LM 输出最终答案**

REPL 的 `print(FINAL)` 输出后，主 LM 看到 stdout，返回 "出现最多的 IP 是 1.2.3.4，共出现 4,521 次"。

整个过程中：
- 主 LM 的 token 消耗：~3,000（写代码 + 决策）
- 每个子 LM 的 token 消耗：~1,500（只看局部）
- 总 token 数：约 10,500，远低于"800 MB 直接塞上下文"的不可行方案

## 七、训练环境：从推理到 RL 微调的闭环

仓库 `training/` 目录里附带基于 Prime Intellect `verifiers` 的训练环境，可以"训练你自己的 RLM"。这是 RLM 与其他推理引擎最大的差异——它不仅给出推理代码，还允许把"递归 LM 调用"本身作为 RL 训练的策略。

论文作者把这视为 "RLM 真正发挥潜力"的路径：传统 RL 微调只能优化"单次 completion 的质量"，RLM 风格的训练可以优化"递归拆解的策略质量"。`verifiers` + `prime-rl` 的组合让研究者可以构建自定义 reward（子调用次数、token 总数、答案正确率）来训练"更会拆解"的主 LM。

## 八、采用顺序与适用边界

**适合采用的场景**：

- 需要处理**远超上下文窗口**的输入（GB 级日志、长代码仓库、整本书）
- 任务可自然拆解为"局部处理 + 汇总"（计数 / 分类 / 摘要 / 提取）
- 想在多个 sandbox 之间灵活切换（本地开发 / 云端隔离）
- 研究方向：训练"会递归拆解"的 LM 策略

**谨慎采用的场景**：

- 任务天然就是"短输入 + 单次回答"——RLM 增加 REPL 调度开销反而是负收益
- 需要严格 token 数预算（RLM 的递归调用难以预测总 token）
- 不支持 CodeAct 的 LM（论文认为所有 LM 都应该有"代码环境"接入，但现状并非如此）

**不适用的场景**：

- 强实时性约束（递归 + REPL 执行带来不可忽略延迟）
- 简单关键词搜索（直接用 ripgrep / grep 更快）
- 模型本身没有 code generation 能力（REPL 形同虚设）

## 九、总结：把 LM 调用从"塞 prompt"升级到"编程访问 prompt"

RLM 的真正信号是：在 LLM 上下文窗口被推到 1M+ token 的今天，"如何调用 LM" 比 "LM 容量有多大" 更有优化空间。`rlm.completion(prompt, model)` 这个看似简单的接口替换，把"输入如何被访问"从"塞进上下文窗口"升级为"在代码环境里编程访问"。

`alexzhang13/rlm` 的工程价值不仅在于它是论文的官方实现，更在于它**已经可以生产可用**——7 种 sandbox、PyPI 安装、训练环境、drop-in 调用接口、配套 minimal 仓库——共同构成了一个完整的"RLM 范式工具链"。对于想要探索"长上下文推理"或"递归 LM 训练"的研究者与工程师，这是 2026 年最值得读的源码之一。