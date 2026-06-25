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

`alexzhang13/rlm` 改造的对象是"如何调用 LLM"这件事本身。传统接口 `llm.completion(prompt, model)` 把整段 prompt 塞进上下文窗口；RLM 提出的 `rlm.completion(prompt, model)` 把 prompt 当成代码环境里的变量，让 LLM 在 REPL 里**编程式**地审视、拆解、递归调用自己。截至 2026 年 6 月，这个由 MIT OASYS 实验室开源的项目（5,108+ Stars、842+ Forks、MIT 许可证、配套论文 arXiv:2512.24601）已经发展出 7 种 sandbox 适配器（local / ipython / docker / modal / prime / daytona / e2b），并附带基于 Prime Intellect prime-rl 的训练环境。

## 学习目标

读完本文后你应当能够：

1. 说清 RLM 与 RAG / 长上下文窗口在抽象层上的差异
2. 画出 RLM 客户端 + REPL + 后端 LM 的三层结构，并解释每层职责
3. 区分主 LM 与子 LM 的输入边界、token 消耗来源
4. 在 7 种 sandbox 之间做出与场景匹配的选型决策
5. 用 `rlm.completion` 写出一段可跑通的递归调用示例
6. 列出 RLM 适用 / 谨慎 / 不适用三类场景的判断依据

## 目录

- [一、核心判断：RLM 重写的是调用范式，而非上下文窗口](#一核心判断rlm-重写的是调用范式而非上下文窗口)
- [二、系统地图：RLM 客户端 + REPL + 后端 LM 的三层结构](#二系统地图rlm-客户端--repl--后端-lm-的三层结构)
- [三、L1 调用层：主 LM + 子 LM 的递归结构](#三l1-调用层主-lm--子-lm-的递归结构)
- [四、L2 REPL 环境层：7 种 sandbox 适配器](#四l2-repl-环境层7-种-sandbox-适配器)
- [五、L3 用户接口层：drop-in 替换 `llm.completion`](#五l3-用户接口层drop-in-替换-llmcompletion)
- [六、任务流案例：从 "1000 万行日志里找异常 IP" 到递归调用](#六任务流案例从-1000-万行日志里找异常-ip-到递归调用)
- [七、训练环境：从推理到 RL 微调](#七训练环境从推理到-rl-微调)
- [八、采用顺序与适用边界](#八采用顺序与适用边界)
- [九、常见问题排查](#九常见问题排查)
- [十、自测题](#十自测题)
- [十一、进阶路径](#十一进阶路径)
- [十二、总结](#十二总结)

本文是一篇原理拆解。文章会先讲 RLM 与传统 completion 调用范式的边界，再拆 CodeAct REPL、递归子调用、多 sandbox 适配三层机制，最后用一个具体任务跑通"超长 prompt → 编程式拆解 → 递归子 LM"的完整链路。

## 一、核心判断：RLM 重写的是调用范式，而非上下文窗口

RLM 论文的开篇给出了与 RAG / 长上下文窗口完全不同的思路：

> Recursive Language Models (RLMs) are a task-agnostic inference paradigm for language models (LMs) to handle near-infinite length contexts by enabling the LM to programmatically examine, decompose, and recursively call itself over its input.

三个关键词值得拆解：

- **task-agnostic**：不绑定"摘要"、"问答"或"RAG"这类具体任务，RLM 提供的是调用范式本身
- **programmatically**：LLM 不再用自然语言读 prompt，而是在代码环境里写代码来访问 prompt
- **recursively**：LLM 可以在自己的代码里调用自己（子 LM），构成递归结构

RLM 和 200k token 的 Gemini 1.5 处于不同抽象层：后者扩大窗口容量，前者改变调用方式。论文作者把这个范式叫做 "language model"，因为从外部看，整个递归系统仍然是一个"从文本到文本的概率映射"，只是内部多了"代码执行 + 子调用"的能力。

**为什么这层区分重要**：把 RLM 当成"另一种长上下文方案"会误导选型——长上下文窗口优化的是"单次能看多少"，RLM 优化的是"如何分批看、如何汇总"。两者可以叠加（子 LM 本身可以用长上下文模型），但不能互相替代。

## 二、系统地图：RLM 客户端 + REPL + 后端 LM 的三层结构

整张地图可以分成三层：

```text
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

这种范式带来的主要收益是 token 经济性：主 LM 只在"做决策"时消耗 token，子 LM 各自只看局部——总 token 数远低于"把所有内容塞进上下文窗口"。

**为什么 token 能省下来**：传统长上下文方案里，每多 1 token 输入，注意力计算的代价是 O(n²)（即便有 FlashAttention 也是 O(n)），且每次生成都要重新编码全部上下文。RLM 把"读 800 MB 日志"拆成"主 LM 写 50 行 Python + 100 个子 LM 各读 8 MB"，主 LM 的上下文里只有代码和子 LM 返回的摘要，子 LM 之间互不可见，token 不叠加。

## 四、L2 REPL 环境层：7 种 sandbox 适配器

RLM 的安全性与可移植性来自 7 种可插拔 REPL 环境。论文和 README 把它们分成两组：本地非隔离 + 云端隔离。

### 4.1 本地非隔离（3 种）

- **`local`（默认）**：主进程内 `exec` 执行。同一虚拟环境、共享全局命名空间。适合本地 benchmark 与低风险任务。
- **`ipython`**：真实 IPython 会话，可选 `ipykernel` 子进程模式（提供 `cell_timeout` 与命名空间隔离）。通过 `pip install 'rlms[ipython]'` 安装。
- **`docker`**：在 `python:3.11-slim`（可自定义）容器内执行 REPL。提供文件系统级隔离。

`LocalREPL` 的实现细节值得注意：它会构造一份"受限的 globals/locals 命名空间"——仍然在主进程里跑，但模型能看到的名字是受控的，恶意 prompt 不能直接 `import os` 删本地文件。这种"软隔离"比纯 `exec` 安全，但不如容器级隔离彻底。

### 4.2 云端隔离（4 种）

- **`modal`**：调用 Modal Sandboxes。子 LM 调用从宿主进程发起，确保主 LM 与 sandbox 解耦。需要 `modal setup` 认证。
- **`prime`**：调用 Prime Intellect Sandboxes（beta）。README 标注"目前运行时较慢，是一个 open issue"。
- **`daytona`**：Daytona 沙箱，提供云端代码执行环境，适合多租户 / 生产场景下完全隔离不可信的 LM 输出。
- **`e2b`**：e2b 沙箱，定位与 `daytona` 接近，按用量计费，启动延迟低于自建容器。

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

调用形态与 `openai.OpenAI().chat.completions.create(...)` 接近一致——这就是 README 强调的 "drop-in replacement"。项目作者把 RLM 定位成"调用现有 LLM 的另一种方式"，而非"另一种 LLM 库"，目的是让存量代码改一行 import 就能切换范式。

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

整个过程中（以 Step 4 的 5 个子调用 demo 为例）：
- 主 LM 的 token 消耗：~3,000（写代码 + 决策）
- 每个子 LM 的 token 消耗：~1,500（只看局部）
- 总 token 数：约 10,500（3,000 + 5 × 1,500），远低于"800 MB 直接塞上下文"的不可行方案

实际生产中子调用数量随 chunk 数线性增长，建议在 prompt 里设置 `max_subcalls` 上限或在 reward 里加入子调用次数惩罚。

## 七、训练环境：从推理到 RL 微调

仓库 `training/` 目录里附带基于 Prime Intellect `verifiers` 的训练环境，可以"训练你自己的 RLM"。这是 RLM 与其他推理引擎的关键差异——它不仅给出推理代码，还允许把"递归 LM 调用"本身作为 RL 训练的策略。

论文作者把这视为 RLM 进一步释放潜力的路径：传统 RL 微调只能优化"单次 completion 的质量"，RLM 风格的训练可以优化"递归拆解的策略质量"。`verifiers` + `prime-rl` 的组合让研究者可以构建自定义 reward（子调用次数、token 总数、答案正确率）来训练"更会拆解"的主 LM。

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

### 选型决策清单

落地前先回答这 5 个问题，全部为"是"再投入：

1. 输入规模是否超过目标 LM 上下文窗口的 2 倍以上？
2. 任务能否被描述为"对每一段做 X，再对所有结果做 Y"？
3. 主 LM 是否具备稳定的 Python 代码生成能力（建议先跑 README 的 100 powers of two 例子验证）？
4. 是否能接受单次调用延迟从秒级上升到分钟级？
5. 是否有 sandbox 隔离需求（本地实验选 `local`/`ipython`，生产选 `docker`/`modal`/`e2b`）？

任意一项答"否"，建议先用传统 `llm.completion` + 手写 chunking 跑通，再评估是否引入 RLM。

## 九、常见问题排查

实际跑 RLM 时容易踩的坑与排查路径：

**1. `ImportError: No module named 'rlm'`**

确认安装来源：`pip install rlms`（注意包名是 `rlms` 复数，import 时才是 `rlm`）。用 `pip show rlms` 查看版本，README 标注的最低支持版本以 PyPI 页面为准。

**2. 主 LM 写出的代码在 REPL 里报 `NameError: name 'prompt' is not defined`**

`prompt` 变量由 RLM 客户端注入到 REPL 的 globals 命名空间。`LocalREPL` 默认注入，`DockerREPL` / `ModalREPL` 需要确认 sandbox 镜像里装了项目依赖。排查时在 REPL 里先执行 `print(dir())` 看可见名字。

**3. 子 LM 调用次数失控，token 账单暴涨**

主 LM 写的循环没有上限保护。在 prompt 里显式约束："最多发起 N 次子调用，超出后返回当前汇总结果"。也可以在 `RLM(...)` 构造时设置 `max_subcalls`（若版本支持）或在 reward 里加入子调用次数惩罚。

**4. `prime` sandbox 启动慢**

README 明确标注 `prime` 目前运行时较慢，是一个 open issue。生产场景先用 `modal` 或 `e2b`，`prime` 留给需要 Prime Intellect 训练栈的研究场景。

**5. 主 LM 拒绝写代码，直接用自然语言回答**

部分模型在 system prompt 不够明确时会退化为 chat 模式。检查 `RLM` 构造参数里是否覆盖了默认的 CodeAct system prompt；也可以在用户 prompt 开头加一句 "You must respond with Python code that prints the final answer."

**6. 递归调用栈溢出 / 超时**

主 LM 在子调用里再次触发主 LM，形成无限递归。在 prompt 里限定递归深度："最多 2 层递归，第 3 层必须直接返回结果。" 同时为 `ipython` sandbox 配置 `cell_timeout` 防止单次执行挂死。

## 十、自测题

用以下 6 题检验理解程度。答案折叠在每题下方。

**Q1**：RLM 与 Gemini 1.5 的 200k 上下文窗口解决的是同一个问题吗？为什么？

> **答案**：不是。Gemini 1.5 扩大单次可见窗口容量，RLM 改变的是"如何分批访问 + 汇总"。两者可叠加（子 LM 用长上下文模型），但属于不同抽象层。

**Q2**：主 LM 与子 LM 的输入边界分别是什么？

> **答案**：主 LM 拿到 REPL 环境 + 完整 prompt 作为变量；子 LM 只拿到主 LM 在代码里传给 `rlm.completion(chunk, ...)` 的局部 chunk，看不到完整 prompt，也接触不到 REPL。

**Q3**：为什么 RLM 的总 token 消耗通常低于"把全部输入塞进上下文"？

> **答案**：主 LM 只在写代码和决策时消耗 token，子 LM 各自只看局部 chunk 且互不可见，token 不叠加。传统方案里每次生成都要重新编码全部上下文，成本随输入线性甚至平方增长。

**Q4**：7 种 sandbox 中哪几种提供文件系统级隔离？哪几种适合生产多租户？

> **答案**：`docker` 提供容器级文件系统隔离；`modal` / `daytona` / `e2b` 提供云端隔离，适合多租户生产场景。`local` / `ipython` 共享宿主命名空间，仅适合本地实验。

**Q5**：下面这段主 LM 写的代码有什么风险？如何修复？

```python
for chunk in chunks:
    print(rlm.completion(f"总结：{chunk}").response)
```

> **答案**：风险有两点：(1) 没有并发，N 个 chunk 串行调用子 LM，延迟 N 倍；(2) 没有上限，chunks 很大时 token 失控。修复：用 `ThreadPoolExecutor` 并发，并加 `chunks[:max_subcalls]` 截断。

**Q6**：RLM 风格的 RL 训练相比传统 RLHF，优化目标有什么不同？

> **答案**：传统 RLHF 优化单次 completion 质量；RLM 风格训练把"递归拆解策略"作为策略空间，reward 可以包含子调用次数、token 总数、答案正确率，优化的是"如何拆"而非"如何答"。

## 十一、进阶路径

读完本文后，按以下顺序深入：

1. **跑通 minimal 仓库**：`alexzhang13/rlm` 配套有 minimal 示例仓库，先用 `local` sandbox 跑通 README 的 100 powers of two 例子，确认环境正常。
2. **替换 backend**：把 `openai` 换成 `anthropic` 或本地 `vllm`，观察主 LM 写出的代码风格差异（不同模型的 code generation 偏好不同）。
3. **切换 sandbox**：同一任务分别用 `local` / `docker` / `modal` 跑一遍，记录启动延迟、执行延迟、token 消耗三项指标，建立自己的选型基线。
4. **写一个自定义任务**：选一个真实场景（如"对 10 万条评论做情感分类 + 主题聚类"），手写主 LM 的拆解 prompt，对比 RLM 自动拆解与人工 chunking 的效果差异。
5. **读论文**：arXiv:2512.24601 里给出了 7 种 sandbox 的对照实验数据、token 经济性分析、递归深度对正确率的影响曲线，是设计自定义 reward 的依据。
6. **进入训练栈**：clone `training/` 目录，跑通 `verifiers` + `prime-rl` 的最小训练流程，理解 reward 设计如何影响主 LM 的拆解策略。
7. **关注 open issue**：`prime` sandbox 性能、递归深度上限的自动保护、不支持 CodeAct 的 LM 接入方案，是项目当前活跃的改进方向。

## 十二、总结

RLM 提供的信号是：在 LLM 上下文窗口被推到 1M+ token 的今天，"如何调用 LM" 比 "LM 容量有多大" 还有更多优化空间。`rlm.completion(prompt, model)` 这个接口替换把"输入如何被访问"从"塞进上下文窗口"改为"在代码环境里编程访问"。

`alexzhang13/rlm` 的价值在于它是论文的官方实现，且工程完成度足以支撑真实使用——7 种 sandbox、PyPI 安装、训练环境、drop-in 调用接口、配套 minimal 仓库覆盖了从本地实验到生产部署的链路。对于想要探索"长上下文推理"或"递归 LM 训练"的研究者与工程师，这是 2026 年值得读的源码之一。