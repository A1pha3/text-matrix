---
title: "Agent Lightning：微软 AI 智能体强化学习训练框架完全指南"
slug: "agent-lightning-microsoft-ai-agent-training-guide"
github_repo: "microsoft/agent-lightning"
source_key: "gh:microsoft/agent-lightning"
aliases:
  - /posts/tech/agent-lightning-microsoft-ai-agent-training-guide/
date: "2026-04-01T01:20:00+08:00"
lastmod: "2026-09-21T12:00:00+08:00"
categories: ["技术笔记"]
tags: ["微软", "AI智能体", "强化学习", "RL", "PyTorch", "Python"]
description: "微软开源的 agentic RL 训练框架，v1.0 完全重构后仅约 3500 行代码：用 OpenAI 兼容代理把任意 agent harness 接入 verl 强化学习训练，Qwen3.5-9B 编码智能体 SWE-bench Verified 41.8%→56.4%。本文以 v1.0.1 为口径解读架构、配置与实战。"
---

# Agent Lightning：微软 AI 智能体强化学习训练框架完全指南

训练一个能干活的智能体，难点往往不在模型，而在模型外面那圈「马具」：工具调用、上下文管理、多轮控制流、环境交互。这些逻辑写在了生产代码里，传统强化学习训练却要求把交互循环交给训练引擎接管，等于把已验证的 harness 推倒重写。

[Agent Lightning](https://github.com/microsoft/agent-lightning)（微软研究院项目，2025 年 6 月公开）给出了相反的思路：把训练引擎藏到一个 OpenAI 兼容的模型端点后面，智能体照常运行，训练系统在旁边记录每一次模型调用，用这些数据更新策略。2026 年 8 月发布的 v1.0 对项目做了完全重构，本文以 v1.0.1（2026-08-24）为口径。

## 为什么需要它：harnessed agentic RL

v1.0 技术报告（[arXiv:2608.17528](https://arxiv.org/abs/2608.17528)）给这个思路起了名字——**harnessed agentic RL**（带 harness 的智能体强化学习）。它与传统 agentic RL 的本质区别是：交互循环由 harness 拥有，而不是训练引擎；训练器能观察到的，只有一串串 LLM 请求-响应对。

> the harness, rather than the training engine, owns the environment interaction loop, while the trainer observes only sequences of LLM request-response pairs.

这个形态带来一批传统训练里不存在的问题：文本重新分词导致的 token 漂移（retokenization）、多轮调用如何合并成训练样本、优势函数怎么算、损失怎么归一化、推理后端怎么调度。Agent Lightning 的价值在于它把这些问题的工程解法做成了一个约 3500 行代码的可运行框架，既能拿来训练，也能当研究这些问题的试验台。

这个范式已经不孤立。技术报告指出，Agent Lightning 首创的「训练-执行解耦 + LLM 端点代理」路线，先后被 verl Uni-Agent、AReaL 2.0、slime、Polar 等框架采纳。

## 项目概况

| 指标 | 数值（2026-09-21 读数） |
|------|------|
| **Stars** | 18,409 |
| **Forks** | 1,624 |
| **Watchers** | 86 |
| **提交数** | 约 660 |
| **Open Issues / PRs** | 100 / 59 |
| **Releases** | 9（latest: v1.0.1，2026-08-24） |
| **许可证** | MIT |
| **语言** | Python ≈98.5%，Shell ≈1.5% |
| **Python 要求** | ≥ 3.12 |
| **PyPI** | `agentlightning` 1.0.1 |

版本时间线里有一个关键节点：

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2025-08-04 | 首个公开版本 |
| v0.2.x | 2025-10 ~ 11 | 稳定性与生态迭代 |
| v0.3.0 | 2025-12-24 | v0.x 线最后一个版本，以预览特性引入 TLA（轨迹级聚合，配合 VERL） |
| **v1.0.0** | 2026-08-17 | **完全重构**，架构与 API 不向下兼容 |
| v1.0.1 | 2026-08-24 | 当前最新，首发官方 Agent Skill |

v1.0 的重构是破坏性的。官方 README 明确写着：

> Agent Lightning was completely refactored in v1.0. For legacy releases earlier than v1.0, see the v0.x branch.

v0.x 时期的 LightningStore、`agl.emit_*`、Tracer 那套接口只存在于 [v0.x 分支](https://github.com/microsoft/agent-lightning/tree/v0.x)，网上大量教程基于旧版，阅读时注意区分。语言构成的变化也能看出重构幅度：v0.x 附带 TypeScript 写的 dashboard，v1.0 的仓库里已经没有它，只剩几乎纯 Python 的核心。

重构后的代码非常克制。核心包 `agentlightning` 只依赖 FastAPI、Hydra、kr8s、Jinja2 这类胶水库，不含任何训练框架本身；「轻量」不是口号，是依赖清单里的事实。

## 架构：三个组件

v1.0 的全部架构就是三个组件，各自独立部署、独立伸缩：

| 组件 | 启动命令 | 职责 |
|------|------|------|
| **API Gateway** | `agl-server` | 中心服务：存储 rollout、模型端点与事件；对外提供 OpenAI 兼容模型代理 |
| **Rollout Controller** | `agl-controller` | 把排队的 rollout 变成真实的智能体执行：本地进程或 Kubernetes Job |
| **Customized Trainer** | `run_ppo` 入口 | 基于 verl：发起 rollout、收集数据、算优势、更新策略 |

数据流是一条直线：Trainer 创建 rollout → Controller 启动智能体 → 智能体的模型请求经 Gateway 代理转发并被记录 → Gateway 把交互变成训练数据 → Trainer 更新策略。

### Rollout 与事件模型

**Rollout** 是「智能体在一次输入上的一次执行」，有全局唯一 ID 和四种状态：`QUEUING`（等 Controller 启动）、`RUNNING`、`SUCCEEDED`、`FAILED`。注意 rollout 不等于训练样本——GRPO 这类算法会对同一个输入创建多个 rollout，通过比较它们的奖励来计算优势。

每个 rollout 挂着只增不改的事件流：

- `model_request`：每次模型调用自动记录，内容包括 prompt token IDs、response token IDs、选中 token 的 log probabilities；
- `reward`：通常由智能体在执行结束时上报；
- 自定义事件：用于诊断和监控。

token 级别的记录是这套架构的胜负手。训练器需要的不是文本，而是精确的 token 序列和 log 概率——在代理层直接拿，就绕开了重新分词带来的漂移。vLLM 团队 2025 年 10 月那篇 [No More Retokenization Drift](https://blog.vllm.ai/2025/10/22/agent-lightning.html) 讲的就是这件事为什么重要。

### OpenAI 兼容代理

智能体接入的方式朴素到近乎无聊：把 OpenAI 客户端的 `base_url` 指向 Gateway 的 rollout 专属路径：

```text
POST /proxy/rollout/{rollout_id}/attempt/{attempt_id}/mode/train/openai/v1/chat/completions
```

验证流量走 `mode/val` 路径。rollout ID 编在 URL 里，每一次模型调用自动关联到正确的执行，智能体不需要知道 rollout 或训练的任何概念。

### Controller 的两种模式

Controller 一次只跑一种模式：

- **local 模式**：每个 rollout 起一个短生命周期本地子进程，进程池默认上限 50（`local_runner.maximum_size`），适合开发调试。依赖 POSIX 进程组信号，原生 Windows 不支持，需走 WSL。
- **k8s 模式**：每个 rollout 渲染一个 Jinja Job 模板、创建一个 Kubernetes Job，默认每分钟最多创建 100 个 Job（`max_jobs_per_minute`），完成的 Job 保留 1200 秒后自动回收。依赖隔离、并发能力强，也是官方生产推荐的形态——智能体跑在自己的 K8s 集群里，不必依赖商业沙箱服务。

两种模式下，Controller 都会向智能体注入三个环境变量：`AGL_OPENAI_BASE_URL`（模型代理地址）、`AGL_EVENT_URL`（事件上报地址）、`AGL_KEY`（共享密钥）。智能体读环境变量就够了。

## 接入一个真实智能体：Calc-X 为例

空谈架构不如看代码。官方 Calc-X 示例（[`examples/calc_x/calc_agent.py`](https://github.com/microsoft/agent-lightning/blob/main/examples/calc_x/calc_agent.py)）里的智能体是一个不含任何 Agent Lightning 依赖的普通 Python 程序，用 AutoGen 加一个 MCP 计算器工具做数学题：

```python
question = os.environ["QUESTION"]        # 由 env_map 从 rollout 的 input 映射
result = os.environ["RESULT"]
agl_key = os.environ["AGL_KEY"]
event_url = os.environ["AGL_EVENT_URL"]
openai_base_url = os.environ["AGL_OPENAI_BASE_URL"]
```

AutoGen 的 `OpenAIChatCompletionClient` 用 `base_url=openai_base_url`、`api_key=agl_key` 构造，并把重试次数设为 6——异步训练时网关会短暂暂停服务做权重更新，带重试的客户端能平滑度过暂停窗口。

智能体算完题，自己判断对错，把奖励用一次普通 HTTP POST 交回去：

```python
reward = 1.0 if scalar_are_results_same(answer, result, 1e-2) else 0.0

httpx.post(
    event_url,
    json={"event_type": "reward", "data": {"value": reward}},
    headers={"Authorization": f"Bearer {agl_key}"},
    timeout=10.0,
).raise_for_status()
```

这就是「零代码改动」的准确含义：智能体的交互逻辑一行不改，改动只有两处外围——模型端点指向网关、加一次 reward 上报。如果任务奖励可以从外部判卷（比如跑测试），连 reward 上报都可以挪到智能体外面。

## 训练配置：数据怎么变成策略更新

Trainer 挂在 [verl](https://github.com/volcengine/verl) 的 `ppo_trainer` 之上，verl 原有的 Hydra 配置全部可用，Agent Lightning 在 `agentlightning.*` 命名空间下追加自己的配置。

### 数据接口

verl 通常用文件路径配置数据集，Agent Lightning 改成直接传内存数据——只要能表示成 JSON 对象列表即可，每个元素就是一个 rollout 的 `input`：

```python
from datasets import Dataset
from agentlightning.verl.entrypoint import run_ppo

train_dataset = Dataset.from_parquet("data/train.parquet").to_list()
val_dataset = Dataset.from_parquet("data/test.parquet").to_list()

run_ppo(config, train_dataset=train_dataset, val_dataset=val_dataset)
```

`input` 的字段可以通过 `env_map` 映射成智能体的环境变量（local 模式），或渲染进 Kubernetes Job 模板（k8s 模式）。单个 rollout 最长执行时间由 `rollout_timeout_seconds` 控制，默认 1800 秒。

### Trace 聚合：多轮调用怎么变成训练样本

一次多轮交互会产生多次模型调用，聚合策略直接决定训练效率。Agent Lightning 提供两种模式：

- **transition**：每次调用独立成为一个训练样本，历史对话作为冻结上下文（不计损失）。实现简单、对分词错误鲁棒，但共享前缀被反复计算，冗余大。
- **trajectory**（v1.0 默认推荐）：把整条轨迹合并成一个训练样本。合并条件苛刻——下一次调用的 prompt 必须与上一次的 prompt+response 的 token 序列精确连续；工具返回值等中间插入的 token 保留为上下文但不计策略损失。连续性一旦断裂，就从断点另起一行，不做有损拼接。

```yaml
agentlightning:
  trace_aggregator:
    level: trajectory            # transition | trajectory
    trajectory_max_prompt_length: 2048
    trajectory_max_response_length: 8192
```

`trajectory_max_response_length` 要设得宽裕些，因为它要装下后续所有轮次的 prompt 和 response；超限内容截断，初始 prompt 超限的行直接丢弃，丢弃与截断数量都会上报 W&B。

### 算法正确性：rollout 级别的记账

轨迹合并带来一个连锁问题：一个 rollout 产出的训练行数是可变的，如果按行独立算优势、按行归一化损失，产出多行的 rollout 会不公平地占更大的优化权重。v1.0 默认打开两个修正：

```yaml
algorithm:
  enable_rollout_level_advantage: true    # 优势在 rollout 级别计算
actor_rollout_ref:
  actor:
    policy_loss:
      loss_mode: per_rollout_mean         # 损失按 rollout 归一化
```

细节推导在技术报告里。另有一个保险丝 `agentlightning.max_ppo_update_times`：单批数据聚合出的样本可能过多，限制单批 PPO 小批量更新次数（官方建议 2）可防训练失稳，默认不设上限。

### 异步训练

智能体 rollout 时长短差异很大，同步训练会被最慢的那个拖住。v1.0 支持**共置异步训练**：生成与更新共享同一组 GPU，未完成的 rollout 组滚入后续步骤。核心参数是一对批量：

```yaml
data:
  train_batch_size: 32        # 每次更新消耗的组数
agentlightning:
  async_rollout:
    enabled: true
    async_train_batch_size: 64   # 同时保持在途的组数，必须大于上行
```

官方给的起点是 `B_async = 2 × B_train`。更新权重前，网关先暂停新请求、等在途请求排空（drain），更新完再恢复。旧策略产出的数据会过时，官方建议配合 verl 的 rollout correction，用 token 级重要性采样（TIS）、裁剪阈值 2 做修正。

同一个 prompt 组内的兄弟 rollout 必须全部完成才能进入优化（比如 `rollout.n=4` 时四个都要完成），这是保住 GRPO/RLOO 组统计的前提。

### 安装：轻的是框架，重的是 GPU 栈

```bash
cd <this-repo>
uv sync
bash scripts/setup_verl.sh 0.8.0 cu130
```

`setup_verl.sh` 负责装经过配套测试的 GPU 栈：verl 0.8.0 配 vLLM 0.20.2（或 verl 0.7.1 配 vLLM 0.12.0），CUDA 12.9/13.0 两种 wheel，并从源码编译 flash-attn 2.8.3——视 CPU 核数要 10 到 30 分钟。训练日志默认上传 Weights & Biases，跑之前先 `uv run wandb login`。

## 训练战果与官方示例

README 最醒目的数字来自编码智能体示例：只用约 **6000 条训练样本**，Qwen3.5-9B 端到端工作流把 **SWE-bench Verified 从 41.8% 提到 56.4%**（+14.6 个百分点）。训练数据从 SWE-smith 数据集（59,136 个任务、128 个 Python 仓库）过滤而来：去掉空题、缺分支、测试超 200 个的任务，用 Qwen3.5-9B 跑四轮难度探针，保留有难有易的混合集，最终约 6000 训练 + 400 验证。整条管线——数据清洗、防 reward hacking、训练脚本——全部开源。

防 reward hacking 的两道防线值得细读，它们针对的是编码智能体真实会走的捷径：

- **仓库隔离**：任务分支先 checkout，`.git` 挪到测试环境可见范围之外，Git 操作、装包、下载文件、改测试框架的命令全部拦截——否则智能体可以从 Git 历史里翻出参考补丁；
- **网络隔离**：用 Kubernetes NetworkPolicy 掐断智能体 Pod 除网关外的全部出站流量——否则 `curl` 一下上游仓库就能白拿奖励。

官方示例覆盖了从入门到重型的完整梯度：

| 示例 | 内容 | 规模 |
|------|------|------|
| [Calc-X](https://microsoft.github.io/agent-lightning/stable/50-example-calc-x/) | AutoGen + MCP 计算器做数学题 | 1×A100 80GB，本地或 Minikube |
| GSM8K | 小学数学推理 | POC 级 |
| ScienceWorld | 文本环境交互式科学任务 | — |
| Search-R1 | 多轮检索-推理智能体 | — |
| LLM-in-Sandbox | 带计算机与代码执行工具的通用智能体 | — |
| [Coding Agent](https://microsoft.github.io/agent-lightning/stable/75-example-coding-agent/) | SWE-smith 上按仓库测试判卷的编码智能体 | 4×B200，K8s 模式 |
| Multimodal QA | 多模态问答 | — |

硬件门槛要如实说：框架本身轻，但策略推理和 GRPO 更新离不开 verl/vLLM 的 GPU 栈。官方快速开始只要求一台带单张 A100 的机器，覆盖从安装到真实 rollout 训练的最短路径；Minikube 演示 K8s 模式则要求至少 64 GB 内存。

## 生态与社区

README 点名的社区项目验证了框架在真实场景的弹性：

- [Youtu-Agent](https://github.com/TencentCloudADP/Youtu-agent)（腾讯云 ADP）：基于 Agent Lightning 修改分支训练，验证到 **128 GPU** 规模的 RL 训练，数学、代码、搜索能力稳定收敛；
- [DeepWerewolf](https://github.com/af-74413592/DeepWerewolf)：用 AgentScope + Agent Lightning 训练中文狼人杀智能体的案例研究；
- [AgentFlow](https://agentflow.stanford.edu/)（斯坦福）：planner/executor/verifier/generator 四角色模块化框架，配 Flow-GRPO 算法处理长时序稀疏奖励任务。

v1.0.1 还首发了官方 **Agent Lightning Skill**，方向很有意思：让 Claude Code、Codex、GitHub Copilot 这类编码智能体去优化另一个 AI 智能体——给它一个可编辑的智能体和一套基准，按测量迭代的方式改进提示词、工具、工作流和模型配置。安装：

```bash
gh skill install microsoft/agent-lightning agent-lightning --agent claude-code
```

这项能力与微软的 SkillOpt 研究（[microsoft/SkillOpt](https://github.com/microsoft/SkillOpt)）一脉相承，基准测试显示编码智能体配合 Agent Lightning 后在 SpreadsheetBench、OfficeQA、ALFWorld 上的平均提升进一步扩大。

官方文章按时间倒序挑几篇值得读的：

| 日期 | 文章 |
|------|------|
| 2026-08 | 技术报告 [Agent Lightning v1.0: Towards Harnessed Agentic RL](https://arxiv.org/abs/2608.17528) |
| 2025-12-17 | [Adopting the Trajectory Level Aggregation for Faster Training](https://agent-lightning.github.io/posts/trajectory_level_aggregation/)（TLA，轨迹级聚合的动机与实现） |
| 2025-11-04 | [Tuning ANY AI agent with Tinker ✕ Agent-lightning](https://medium.com/@yugez/tuning-any-ai-agent-with-tinker-agent-lightning-part-1-1d8c9a397f0e)（上/下两篇） |
| 2025-10-22 | vLLM 博客 [No More Retokenization Drift](https://blog.vllm.ai/2025/10/22/agent-lightning.html)（为什么代理层返回 token IDs 很关键） |
| 2025-08-05 | 原始论文 [Agent Lightning: Train ANY AI Agents with Reinforcement Learning](https://arxiv.org/abs/2508.03680) |

原始论文提出了分层 RL 算法 LightningRL（带信用分配模块，可把任意智能体的轨迹分解成训练转移）与 Training-Agent Disaggregation 架构，实验覆盖 text-to-SQL、RAG、数学工具调用——这两篇论文加上官方文档，基本构成了这个项目全部的理论与工程脉络。

## 常见问题

**Q1：真的零代码改动吗？**

智能体交互逻辑零改动，但两件事省不掉：模型端点要指向网关（改配置即可），奖励要么由智能体上报（一次 HTTP POST），要么由外部判卷程序上报。若做异步训练，客户端需要带重试。把它理解成「接入成本一次、之后与训练完全解耦」更准确。

**Q2：v0.x 的代码能迁移到 v1.0 吗？**

不能直接迁移。v1.0 是完全重构，LightningStore、`agl.emit_*`、Tracer 接口都不在了，旧代码只能参考 v0.x 分支。架构思想上是一脉相承的：v0.x 用 tracer 收集 span，v1.0 用网关记录模型请求，都是「训练器只看模型交互」这一个思路。

**Q3：支持哪些训练算法？**

v1.0 通过 verl 的 `ppo_trainer` 做强化学习（GRPO 等组相对算法即开即用），官方文档与示例全部围绕 RL。v0.x 时期 README 还提到过自动提示优化（APO）与监督微调（SFT），v1.0 文档中已不见这些入口，需要的话应查 v0.x 分支。

**Q4：最少要多少硬件？**

单张 A100 就能跑通快速开始（Calc-X，Qwen2.5-1.5B-Instruct）。编码智能体示例用的是 4×B200 加独立 K8s 集群的两机方案。K8s 演示环境 Minikube 至少 64 GB 内存。

**Q5：Windows 上能用吗？**

`runner_type=local` 依赖 POSIX 进程组信号，原生 Windows 不支持，Controller 会在启动时直接退出，请用 WSL。`runner_type=k8s` 不受影响。

## 小结

Agent Lightning 押注的是一个正在成形的共识：智能体的 harness 是资产，训练基础设施应该围着它转，而不是反过来。v1.0 用三个组件、约 3500 行代码把这个立场落成了可部署的系统——网关记 token、控制器管执行、verl 管更新，中间没有魔法。如果你想给自己的智能体接上 RL 训练，从 Calc-X 单卡示例起步是成本最低的路径；如果想研究 harnessed agentic RL 的问题本身，技术报告与源码都是公开的试验台。

## 参考来源与口径说明

- 本文数据（stars、forks、issues/PR、提交数、release 列表）为 GitHub API 2026-09-21 读数，语言占比按 GitHub languages API 字节数计算；
- 架构、配置、代码行为以 v1.0.1（2026-08-24）的仓库 README、`docs/` 全套官方文档（安装、快速开始、Basics、Trainer/Gateway/Controller 配置、异步训练、Calc-X 与 Coding Agent 示例）及 `examples/calc_x/calc_agent.py` 源码为准；代码片段均为仓库原文摘录；
- 两篇论文摘要经 arXiv API 核实：原始论文 arXiv:2508.03680（2025-08-05），v1.0 技术报告 arXiv:2608.17528（2026-08）；
- 社区项目 Youtu-Agent、DeepWerewolf、SkillOpt 的仓库信息经 GitHub API 核实；Youtu-Agent 128 GPU 训练、SWE-bench Verified 41.8%→56.4% 引自官方 README 与 v1.0.0 发布说明原文；
- v0.x 相关描述（LightningStore、emit 接口、APO/SFT、TypeScript dashboard）以 v0.x 分支 README 及发布历史为据，属遗留接口，不适用于 v1.0。
