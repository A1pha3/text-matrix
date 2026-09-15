---
title: "RLM 推理范式拆解：让 LLM 在 REPL 里递归处理超长上下文"
date: "2026-06-18T15:06:00+08:00"
slug: "alexzhang13-rlm-recursive-language-models-guide"
description: "alexzhang13/rlm 是 MIT OASYS 实验室开源的 Recursive Language Models 推理引擎，把长上下文变成 REPL 环境里的变量，让 LLM 写代码检查、拆解并递归调用自己。本文拆解其调用范式、7 种沙箱环境与论文实验数据。"
draft: false
categories: ["技术笔记"]
tags: ["Python"]
---

# RLM 推理范式拆解：让 LLM 在 REPL 里递归处理超长上下文

`alexzhang13/rlm` 改造的对象是"如何调用 LLM"这件事本身。传统接口 `llm.completion(prompt, model)` 把整段 prompt 塞进上下文窗口；RLM（Recursive Language Models，递归语言模型）提供的 `rlm.completion(prompt, model)` 把长文本当成代码环境里的变量，让 LLM 在 REPL（Read-Eval-Print Loop，交互式代码执行环境）里写代码来检查、拆解输入，并在代码中递归调用自己。截至 2026 年 9 月，这个由 MIT OASYS 实验室开源的项目（约 5.6k Stars、900 Forks、MIT 许可证，论文作者 Alex L. Zhang、Tim Kraska、Omar Khattab，编号 arXiv:2512.24601）已经支持 7 种 REPL 环境（local / ipython / docker / modal / prime / daytona / e2b），并附带基于 Prime Intellect `verifiers` 与 `prime-rl` 的训练环境。

## 学习目标

读完本文后你应当能够：

1. 说清 RLM 与长上下文窗口、compaction 压缩在抽象层上的差异
2. 画出 RLM 客户端 + REPL + 后端 LM 的三层结构，并解释每层职责
3. 区分主 LM 与子 LM 的输入边界、token 消耗来源
4. 在 7 种 REPL 环境之间做出与场景匹配的选型决策
5. 用 `rlm.completion` 写出一段调用形态正确的示例
6. 列出 RLM 适用 / 谨慎 / 不适用三类场景的判断依据

## 目录

- [一、核心判断：RLM 重写的是调用范式，而非上下文窗口](#一核心判断rlm-重写的是调用范式而非上下文窗口)
- [二、系统地图：RLM 客户端 + REPL + 后端 LM 的三层结构](#二系统地图rlm-客户端--repl--后端-lm-的三层结构)
- [三、L1 调用层：主 LM + 子 LM 的递归结构](#三l1-调用层主-lm--子-lm-的递归结构)
- [四、L2 REPL 环境层：7 种沙箱环境](#四l2-repl-环境层7-种沙箱环境)
- [五、L3 用户接口层：drop-in 替换 `llm.completion`](#五l3-用户接口层drop-in-替换-llmcompletion)
- [六、任务流案例：从 800 MB 日志里找异常 IP 到递归调用](#六任务流案例从-800-mb-日志里找异常-ip-到递归调用)
- [七、论文结果与训练环境](#七论文结果与训练环境)
- [八、采用顺序与适用边界](#八采用顺序与适用边界)
- [九、常见问题排查](#九常见问题排查)
- [十、自测题](#十自测题)
- [十一、进阶路径](#十一进阶路径)
- [十二、总结](#十二总结)

本文先划定 RLM 与传统 completion 调用的边界，再按 L1/L2/L3 三层拆开机制，然后用一个日志分析任务把整条链路跑一遍，最后给出论文数据与采用建议。

## 一、核心判断：RLM 重写的是调用范式，而非上下文窗口

RLM 论文的开篇给出了与长上下文路线不同的思路：

> Recursive Language Models (RLMs) are a task-agnostic inference paradigm for language models (LMs) to handle near-infinite length contexts by enabling the LM to programmatically examine, decompose, and recursively call itself over its input.

三个关键词值得拆开：

- **task-agnostic**：不绑定摘要、问答或检索这类具体任务，RLM 提供的是调用范式本身
- **programmatically**：LLM 不再用自然语言通读 prompt，而是写代码访问 prompt
- **recursively**：LLM 可以在自己的代码里调用自己（子 LM），构成递归结构

论文用三组基线检验这条路线：把长输入压缩后再塞进窗口的 compaction；给模型代码执行能力但没有递归结构的 CodeAct with sub-calls（CodeAct，以可执行代码作为模型动作格式的 agent 范式）；以及通用 agent 脚手架 Claude Code。RLM 和它们的差异在抽象层：compaction 决定"丢什么留什么"，CodeAct 解决"模型会不会动手"，RLM 决定"输入如何被访问"——三件事可以叠加，但互不替代。论文作者把这个范式仍叫做 language model，因为从外部看，整个递归系统依然是一个"从文本到文本的映射"，只是内部多了代码执行和子调用。

这条区分直接影响选型：上下文窗口决定单次能装多少，RLM 决定如何分批看、如何汇总。子 LM 本身可以是长上下文模型，两者叠加使用。

## 二、系统地图：RLM 客户端 + REPL + 后端 LM 的三层结构

整张地图可以分成三层：

```text
┌────────────────────────────────────────────────────────────────┐
│  L3 用户接口层                                                 │
│    rlm.completion(prompt, root_prompt) → response              │
│    与传统 llm.completion 调用形态保持一致（drop-in 替换）       │
├────────────────────────────────────────────────────────────────┤
│  L2 REPL 环境层（可插拔 7 种环境）                             │
│    local / ipython / docker / modal / prime / daytona / e2b    │
│    长文本注入为 context 变量，LLM 在这里写 Python 访问它       │
├────────────────────────────────────────────────────────────────┤
│  L1 LM 调用层                                                  │
│    主 LM（根调用）：负责写代码、做决策、提交最终答案           │
│    子 LM：被主 LM 在代码里调用，只处理局部上下文              │
│    backend: openai / anthropic / openrouter / portkey / vllm   │
└────────────────────────────────────────────────────────────────┘
```

下面逐层看关键机制。

## 三、L1 调用层：主 LM + 子 LM 的递归结构

RLM 的核心是把 `llm.completion` 包装成两层调用。

### 3.1 主 LM（根调用）

主 LM 拿到的不再是原始 prompt 文本，而是一个 REPL 环境——长上下文以 `context` 变量的形式注入其中。它的任务是写代码：

- 检查 `context` 的某一段
- 调用子 LM 处理该段
- 汇总子 LM 的输出

主 LM 会经历多轮"写代码 → 看执行结果 → 再写代码"的循环，直到把最终答案存入某个变量并用 `FINAL_VAR("变量名")` 提交。REPL 轮次由 `max_iterations` 参数封顶（默认 30），达到上限后强制产出最终答案。

### 3.2 子 LM

子 LM 是主 LM 在代码里调用的 LM 实例，每次只看到传给它的局部片段，不接触完整上下文，也不接触 REPL。在 `local` 环境中，注入 REPL 的子调用函数是 `llm_query`（发起单次子 LM 调用）与 `llm_query_batched`（批量并发调用）；`docker` 环境额外提供 `rlm_query` / `rlm_query_batched`——递归地生成带完整 REPL 的子 RLM，并发数受 `max_concurrent_subcalls` 限制。

### 3.3 递归

"递归"指的是主 LM 在代码里再次发起 LM 调用，子调用的输出回到 REPL 继续参与计算。需要说明现状：RLM 客户端的 `max_depth` 参数当前默认且仅支持 1——也就是"根调用 + 一层子调用"。论文意义上的任意深度递归是范式能力，库层面的深度保护已经先行落地。

这种结构带来的收益是 token 经济性：主 LM 只在写代码和决策时消耗 token，上下文里出现的只有代码和子 LM 返回的文本；子 LM 各看一段、互不可见，token 不叠加。传统方案里输入越长，每次调用的费用与时延都越高——注意力计算随序列长度平方增长（FlashAttention 优化后仍随长度线性），RLM 把"读 800 MB 日志"变成"主 LM 写几十行 Python + 若干子 LM 各读一小段"，总成本随任务结构而非输入总长增长。

## 四、L2 REPL 环境层：7 种沙箱环境

RLM 的可移植性来自 7 种可插拔 REPL 环境。按执行位置可以分成两组：本地执行（local / ipython / docker）与云端沙箱（modal / prime / daytona / e2b），隔离强度依次递增。

### 4.1 本地执行（3 种）

- **`local`（默认）**：与 RLM 主进程同进程运行，用 Python `exec` 在受限命名空间里执行代码——屏蔽了 `eval`、`exec`、`compile`、`input`、`globals`、`locals` 等危险内置函数，但与宿主共享进程内存、没有网络隔离。官方文档明确建议不要用于生产环境，它适合本地验证与低风险任务。
- **`ipython`**：在真实 IPython 会话里运行代码单元，默认进程内执行，也可以切到独立的 `ipykernel` 子进程模式——后者提供硬性的 `cell_timeout` 超时控制和与宿主完全的命名空间隔离。通过 `pip install 'rlms[ipython]'` 安装。
- **`docker`**：在容器内执行 REPL，默认镜像 `python:3.11-slim`，可自定义。容器与宿主之间通过宿主侧的轻量代理桥接 LM 调用。功能最全：单次与批量子调用（`llm_query` / `rlm_query` 系列）、自定义工具（`custom_tools` / `custom_sub_tools`）、`persistent=True` 多轮会话（带版本化的 `context_N` / `history_N` 变量）、`compaction=True` 自动摘要历史。注意 `LocalREPL` 的内置函数白名单较窄，如果模型需要的标准库被拦截，换 `docker` 环境即可获得容器内完整的 Python。

### 4.2 云端沙箱（4 种）

- **`modal`**：调用 Modal Sandboxes。先 `uv add modal` 安装，再 `modal setup` 完成账号认证。递归子调用从宿主进程发起，主 LM 与沙箱解耦。
- **`prime`**：调用 Prime Intellect Sandboxes（beta）。安装 `uv pip install -e ".[prime]"` 并设置 `PRIME_API_KEY`。README 明确标注：目前运行时较慢，是一个 open issue。
- **`daytona` / `e2b`**：一并列入环境清单，README 未附对比数据。定位都是云端代码执行环境，适合多租户生产场景，选型前以各自文档为准。

这 7 种环境共享同一套 REPL 接口——`context` 变量和 `llm_query` 等注入函数在不同环境里行为一致，差异在隔离强度与运维成本。本地做实验、生产上容器或云端沙箱，代码不用重写。

## 五、L3 用户接口层：drop-in 替换 `llm.completion`

L3 刻意做得很薄。README 给出的最小例子：

```python
from rlm import RLM

rlm = RLM(
    backend="openai",
    backend_kwargs={"model_name": "gpt-5-nano"},
    verbose=True,
)

print(rlm.completion("Print me the first 100 powers of two, each on a newline.").response)
```

调用形态与 `openai.OpenAI().chat.completions.create(...)` 接近一致——这就是 README 强调的 "drop-in replacement"。项目把 RLM 定位成"调用现有 LLM 的另一种方式"，而非"另一个 LLM 库"，存量代码改一行 import 就能切换范式。

`rlm.completion` 的完整签名更能说明设计意图：

```python
result = rlm.completion(
    prompt,        # 长上下文：str | dict | list，注入 REPL 后成为 context 变量
    root_prompt,   # 可选：只有根调用能看到的任务指令
)
```

长上下文与任务指令在这里分开——`prompt` 位置放数据，`root_prompt` 放指令，指令不会污染上下文变量。返回对象上有几个实用属性：`response`（最终答案）、`execution_time`（耗时秒数）、`usage_summary`（根调用与所有子调用的 token 汇总）、`root_model`（根调用模型名）。

`RLM` 构造函数里值得认识的参数：`environment`（选择 REPL 环境，默认 `local`）、`max_depth`（递归深度，当前仅支持 1）、`max_iterations`（REPL 轮次上限）、`other_backends`（给 REPL 内子调用配备额外后端）、`custom_system_prompt`（覆盖默认的 CodeAct 系统提示词）、`logger`（传入 `RLMLogger` 把轨迹落盘为 JSONL）。`backend` 支持 `openai` / `anthropic` / `openrouter` / `portkey`，本地模型推荐 `vllm`（走 OpenAI 兼容接口），更多客户端见仓库 `rlm/clients/` 目录。

## 六、任务流案例：从 800 MB 日志里找异常 IP 到递归调用

用一个真实场景跑一遍完整流程。任务：从 800 MB 的日志文件里找出出现次数最多的 IP。这个体量远超任何单一上下文窗口，传统调用接口在第一步就失效。

**Step 1：用户调用**

```python
from rlm import RLM

rlm = RLM(
    backend="openai",
    backend_kwargs={"model_name": "gpt-5-mini"},
    environment="local",
)

with open("huge.log", errors="replace") as f:
    log_text = f.read()  # 800 MB，不能塞进任何上下文窗口

result = rlm.completion(
    log_text,
    root_prompt="找出这段日志里出现次数最多的 IP 地址。",
)
print(result.response)
print(result.usage_summary)  # 根调用与所有子调用的 token 汇总
```

日志文本走 `prompt` 参数进入 REPL 的 `context` 变量，任务指令走 `root_prompt` 只给根调用。

**Step 2：主 LM 写出拆解代码**

主 LM 不会试图通读日志，它在 REPL 里写下这样的代码：

```python
# 主 LM 在 REPL 里写的代码（示意）
import re
from collections import Counter

chunks = [context[i:i + 10000] for i in range(0, len(context), 10000)]

total = Counter()
for chunk in chunks:
    ips = re.findall(r"\d+\.\d+\.\d+\.\d+", chunk)
    total.update(Counter(ips).most_common(5))

FINAL = total.most_common(1)[0]
FINAL_VAR("FINAL")
```

`FINAL_VAR("FINAL")` 把变量提交为整个调用的返回值，随后 `result.response` 就是它。

**Step 3：REPL 执行**

`LocalREPL` 执行这段代码。注意这段代码全程没有 LM 参与计数——正则加 `Counter` 就够了。RLM 的价值恰恰在于给了模型"先用便宜手段试"的空间：模型看到执行结果后自己判断要不要升级手段。

**Step 4：递归子调用（可选）**

如果正则覆盖不了（比如日志里 IP 被混淆），主 LM 可以对局部片段发起子 LM 调用：

```python
# 主 LM 在 REPL 里继续写：对前 5 个 chunk 用子 LM 做语义识别
sample = "\n".join(chunks[:5])
identified = llm_query(
    f"从下面文本中找出所有 IP 地址，以 JSON 数组返回：\n{sample[:5000]}"
)
```

`llm_query` 是单次子 LM 调用：子 LM 只看到这 5000 字符，看不到 800 MB 全文。在 `docker` 环境里还可以改用 `rlm_query`——子调用本身带着完整 REPL，能对片段再做一轮"写代码检查"，并发受 `max_concurrent_subcalls` 约束。

**Step 5：主 LM 提交最终答案**

REPL 的执行结果回到主 LM 的上下文，它确认 `FINAL` 变量已经就绪并提交。`result.response` 返回"出现最多的 IP 是 x.x.x.x，共出现 N 次"。

整个过程的真实 token 开销不必估算——`result.usage_summary` 会列出根调用与每个子调用的消耗。可以确定的是：根 LM 的上下文里只有代码和子调用返回的文本，成本随任务结构而非输入总长增长。需要控制开销时，用 `max_iterations` 限制 REPL 轮次，在 `root_prompt` 里写明子调用预算。

## 七、论文结果与训练环境

论文（arXiv:2512.24601，v3 更新于 2026 年 5 月）报告了 GPT-5 作为根模型、四个长上下文任务上的结果。先说清这组数字测的是什么：输入长度远超模型上下文窗口时，不同调用策略的答案准确率——不是短上下文任务的通用能力对比。

跨基准中位数下，RLM 相比 compaction 提升 26%，相比 CodeAct with sub-calls 提升 130%，相比 Claude Code 提升 13%，成本与基线相当。数字分布本身有信息量：对 compaction 的优势来自"不丢信息"——压缩后再读必然损失细节，编程式访问保留了按需回查的能力；对 CodeAct with sub-calls 的 130% 是三组里最大的差距，说明收益不只来自"会写代码"，更来自递归结构本身——子调用能带着环境再拆解，而不是一次性返回文本。反过来说，这组数字不能直接推出"RLM 在所有任务上都更好"：输入可自然拆分的任务收益最大，短输入任务上 REPL 调度开销反而是负担；实验以 GPT-5 为根模型，其他模型的表现要看各自的代码生成能力。

训练侧，仓库 `training/` 目录把 `rlm.RLM` 暴露为 `verifiers` 的 Environment，可直接接入 Prime Intellect 的 `prime-rl`，自带 OOLONG 长文本问答示例（`training/environments/oolong/`），训练时使用 subprocess 隔离的本地 REPL，不依赖云端沙箱。论文据此做了小规模后训练：用 Qwen3-8B 训出 RLM-Qwen3-8B，平均比原始 Qwen3-8B 提升 28.3%，在三个长上下文任务上接近原始 GPT-5 的水平。这说明"递归拆解策略"本身可以被训练——reward 里可以纳入子调用次数、token 总量与答案正确率，优化的对象从"如何回答"扩展到了"如何拆解"。

## 八、采用顺序与适用边界

**适合采用的场景**：

- 需要处理**远超上下文窗口**的输入（GB 级日志、长代码仓库、整本书）
- 任务可自然拆解为"局部处理 + 汇总"（计数 / 分类 / 摘要 / 提取）
- 想在多个沙箱环境之间灵活切换（本地开发 / 容器与云端隔离）
- 研究方向：训练"会递归拆解"的 LM 策略

**谨慎采用的场景**：

- 任务天然就是"短输入 + 单次回答"——REPL 调度开销是负收益
- 需要严格 token 预算——递归调用的总量难以事前预测，只能靠 `max_iterations`、子调用预算和 `usage_summary` 事后观察
- 根模型代码生成能力弱——先用 README 的 powers-of-two 例子验证，写不出可执行拆解代码的模型撑不起整个范式

**不适用的场景**：

- 强实时性约束（多轮代码执行与子调用带来不可忽略的延迟）
- 简单关键词搜索（直接用 ripgrep / grep 更快）

### 选型决策清单

落地前先回答这 5 个问题，全部为"是"再投入：

1. 输入规模是否超过目标 LM 上下文窗口的 2 倍以上？
2. 任务能否被描述为"对每一段做 X，再对所有结果做 Y"？
3. 根 LM 是否具备稳定的 Python 代码生成能力（先跑 README 的 powers-of-two 例子验证）？
4. 是否能接受单次调用延迟从秒级上升到分钟级？
5. 沙箱隔离需求是否明确（本地实验选 `local` / `ipython`，生产选 `docker` / `modal` / `e2b`）？

任意一项答"否"，先用传统 `llm.completion` 加手写 chunking 跑通，再评估是否引入 RLM。

## 九、常见问题排查

**1. `ImportError: No module named 'rlm'`**

PyPI 包名是 `rlms`（复数），import 名才是 `rlm`：`pip install rlms`。环境要求 Python 3.11 及以上，用 `pip show rlms` 确认安装。

**2. REPL 代码报 `NameError: name 'context' is not defined`**

`context` 变量由 RLM 客户端注入 REPL。确认长上下文是走 `completion()` 的 `prompt` 参数传入的，而不是拼进了任务指令字符串。排查时先在代码里 `print(len(context))` 确认变量已注入、内容完整。

**3. 子 LM 调用次数失控，token 账单暴涨**

主 LM 写的循环没有上限保护。三道闸门：在 `root_prompt` 里显式写明"最多发起 N 次子调用"；构造时设 `max_iterations`（默认 30）限制 REPL 轮次；`docker` 环境用 `max_concurrent_subcalls` 管住并发。跑完用 `result.usage_summary` 复盘实际消耗。

**4. `prime` 环境启动慢**

README 明确标注这是已知 open issue。生产场景先用 `modal` 或 `e2b`，`prime` 留给需要 Prime Intellect 训练栈的研究场景。

**5. 主 LM 不写代码，直接用自然语言回答**

模型退化为 chat 模式时，检查 `custom_system_prompt` 是否覆盖了默认的 CodeAct 系统提示词；先用 README 的 powers-of-two 例子验证模型的基础代码能力。

**6. 执行挂死或无限循环**

递归深度不用担心——`max_depth` 当前仅支持 1，库层面已杜绝无限递归。真正会挂的是单个代码块：`ipython` 的子进程模式提供硬性 `cell_timeout`；`max_iterations` 则在 REPL 轮次失控时强制收敛出最终答案。

## 十、自测题

用以下 6 题检验理解程度。答案折叠在每题下方。

**Q1**：RLM 与 1M 级长上下文窗口模型解决的是同一个问题吗？为什么？

<details>
<summary>点击查看参考答案</summary>

**答案**：不是。长上下文窗口扩大单次可见容量，RLM 改变的是"输入如何被访问"——分批检查加汇总。两者可叠加（子 LM 用长上下文模型），但属于不同抽象层，不能互相替代。

</details>

**Q2**：主 LM 与子 LM 的输入边界分别是什么？

<details>
<summary>点击查看参考答案</summary>

**答案**：主 LM 拿到 REPL 环境，完整上下文以 `context` 变量注入，任务指令走 `root_prompt`；子 LM 只拿到主 LM 在代码里传给 `llm_query`（或 `rlm_query`）的局部片段，看不到完整上下文，也接触不到 REPL。

</details>

**Q3**：为什么 RLM 的总 token 消耗通常低于"把全部输入塞进上下文"？

<details>
<summary>点击查看参考答案</summary>

**答案**：主 LM 只在写代码和决策时消耗 token，上下文里只有代码与子调用返回的文本；子 LM 各看局部且互不可见，token 不叠加。传统方案的调用成本随输入长度增长（注意力计算平方级、FlashAttention 后线性级），RLM 的成本随任务结构增长。

</details>

**Q4**：7 种环境中哪几种提供进程或容器级隔离？哪几种仅适合本地实验？

<details>
<summary>点击查看参考答案</summary>

**答案**：`docker` 提供容器级隔离；`modal` / `prime` / `daytona` / `e2b` 是云端完全隔离，适合多租户生产。`local` 与宿主共享进程内存、无网络隔离，`ipython` 进程内模式同理——仅子进程模式才有命名空间隔离，两者都只适合本地实验。

</details>

**Q5**：下面这段主 LM 写的代码有什么问题？如何修复？

```python
for chunk in chunks:
    print(llm_query(f"总结：{chunk}"))
```

<details>
<summary>点击查看参考答案</summary>

**答案**：三个问题：(1) 串行调用，N 个 chunk 延迟线性放大；(2) 没有上限，chunk 多时 token 失控；(3) 结果只 `print` 没存变量，也没有用 `FINAL_VAR` 提交，根模型拿不到可返回的最终答案。修复：把结果收集进列表，改用 `llm_query_batched` 并发（`docker` 下受 `max_concurrent_subcalls` 限流），汇总后 `FINAL_VAR` 提交，并用 `max_iterations` 兜底。

</details>

**Q6**：RLM-Qwen3-8B 的后训练相比传统 RLHF，优化对象有什么不同？

<details>
<summary>点击查看参考答案</summary>

**答案**：传统 RLHF 优化单次回答的质量；RLM 风格的后训练把"在 REPL 里拆解上下文、调度子调用"作为策略空间，reward 可以纳入子调用次数、token 总量与答案正确率。论文报告平均提升 28.3%，三个长上下文任务上接近原始 GPT-5。

</details>

## 资料口径说明

本文的判断基于以下来源：

1. **一手来源**（优先级最高）：
   - RLM 论文：arXiv:2512.24601（v3，2026 年 5 月）
   - RLM 仓库：alexzhang13/rlm（GitHub），含 README 与官方文档站
   - 官方文档：alexzhang13.github.io/rlm（客户端 API 与各 REPL 环境页）
2. **二手来源**（供交叉验证）：关于 CodeAct、长上下文压缩与云端沙箱的技术文档。

3. **口径边界**：
   - Stars / Forks 数据截至 2026 年 9 月，会随时间变化。
   - `max_depth` 仅支持 1、`max_iterations` 默认 30 等 API 细节以当前版本文档为准，升级后请复查。
   - 本文未实际运行 RLM，第六节的 REPL 代码是调用形态示意，实际生成代码由模型决定。

如果你发现与最新版本不符的细节，欢迎指正。

## 十一、进阶路径

读完本文后，按以下顺序深入：

1. **跑通最小例子**：`pip install rlms` 后用 `local` 环境跑 README 的 powers-of-two 例子，确认环境正常。
2. **替换 backend**：把 `openai` 换成 `anthropic` 或本地 `vllm`，观察主 LM 写出的代码风格差异——不同模型的代码生成偏好不同。
3. **切换环境**：同一任务分别用 `local` / `docker` / `modal` 跑一遍，记录启动延迟、执行延迟、token 消耗三项指标，建立自己的选型基线。
4. **写一个自定义任务**：选一个真实场景（如"对 10 万条评论做情感分类 + 主题聚类"），对比 RLM 自动拆解与手写 chunking 脚本的效果和成本。
5. **读论文**：arXiv:2512.24601 给出了四个长上下文任务的完整对比、与 compaction / CodeAct / Claude Code 三组基线的中位数数据，以及 RLM-Qwen3-8B 的训练细节，是设计自定义 reward 前的必读材料。
6. **进入训练栈**：clone `training/` 目录，跑通 `verifiers` + `prime-rl` 的 OOLONG 示例，理解 reward 设计如何影响主 LM 的拆解策略。
7. **跟踪 open issue**：`prime` 环境的运行时性能是当前已知的主要问题；仓库生态里已有 DSPy.RLM 等项目把 RLM 接入其他框架，值得关注。

## 十二、总结

在上下文窗口被推到 1M token 的今天，"如何调用 LM"仍然有独立于"窗口有多大"的优化空间。`rlm.completion` 这个接口替换把输入的访问方式从"塞进上下文窗口"改成"在代码环境里按需访问"，token 成本从随输入长度增长变成随任务结构增长。

`alexzhang13/rlm` 的工程完成度足以支撑真实使用：7 种环境、PyPI 安装、训练环境、drop-in 接口覆盖了从本地实验到生产部署的链路。输入超大且可拆解的团队可以直接从 `docker` 环境开始试点；输入不大或任务不可拆的，等一等再回来也不迟。
