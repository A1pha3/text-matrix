---
title: "SIA 解读：两条改进杠杆都开源了，选杠杆的动作却回到了命令行"
date: "2026-06-12T21:08:43+08:00"
lastmod: "2026-09-19T11:20:00+08:00"
slug: "sia-self-improving-ai-harness-weights"
github_repo: "hexo-ai/sia"
source_key: "gh:hexo-ai/sia"
aliases:
    - "/posts/tech/sia-self-improving-ai-harness-weights/"
description: "对照 hexo-ai/sia 仓库（sia-agent 0.6.0，commit 7fd04d0）与论文 arXiv:2605.27276 v2，拆解 SIA 的三 Agent 循环、--focus 的 harness/weights 两条通道、LawBench 与 TriMul 与 scRNA-seq 去噪的三套分数口径、Profile/Provider 配置层和 evaluate.py 契约。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Harness Engineering", "Benchmark"]
---

## 目录

- [一、先把判断说清楚](#一先把判断说清楚)
- [二、系统地图：角色、两条通道与一次 run 的边界](#二系统地图角色两条通道与一次-run-的边界)
  - [2.1 三个角色，两处实现](#21-三个角色两处实现)
  - [2.2 两条通道，一次 run 选一条](#22-两条通道一次-run-选一条)
  - [2.3 论文里权重通道具体做什么](#23-论文里权重通道具体做什么)
- [三、仓库结构：代码里的循环长什么样](#三仓库结构代码里的循环长什么样)
- [四、一次任务流的落地路径：内置 lawbench 跑五代](#四一次任务流的落地路径内置-lawbench-跑五代)
- [五、Benchmark 数字：三套口径要先对齐](#五benchmark-数字三套口径要先对齐)
- [六、Profile、Provider 与 agent_impl](#六profileprovider-与-agent_impl)
- [七、评估契约：整条循环只认 results.json](#七评估契约整条循环只认-resultsjson)
- [八、常见报错与排查](#八常见报错与排查)
- [九、什么时候值得跑，什么时候先别上](#九什么时候值得跑什么时候先别上)
- [十、动手练习](#十动手练习)
  - [练习 1：跑通一代，并核对产物清单](#练习-1跑通一代并核对产物清单)
  - [练习 2：只读代码，确认"选杠杆"这件事没有实现](#练习-2只读代码确认选杠杆这件事没有实现)
  - [练习 3：给一个没有评估器的任务补上](#练习-3给一个没有评估器的任务补上)
- [十一、自测题](#十一自测题)
- [十二、下一步读哪份代码](#十二下一步读哪份代码)
- [十三、资料口径与未定项](#十三资料口径与未定项)
- [引用](#引用)
- [参考链接](#参考链接)

---

## 一、先把判断说清楚

SIA 处理的对象是智能体（Agent）系统本身：谁来改它的脚手架，谁来改它的权重。仓库由 hexo-ai 维护，Python 包名写作 `sia-agent`，版本 0.6.0，MIT 许可，要求 Python 3.11 以上；配套论文 arXiv:2605.27276 在 2026-05-26 提交，5-28 修到 v2，作者七人，分类 cs.AI。论文的出发点是把两条各自为政的改进路线摆平：harness-update 一派让上层模型反复重写任务侧脚手架——工具、提示词（prompt）、重试逻辑、搜索流程——权重冻住；test-time training（测试时训练）一派用人工写好的强化学习（RL）管线更新模型自身的权重，脚手架冻住。两派各转一个旋钮。SIA 的方案是让同一个 Feedback-Agent 在同一条循环里两个都转：每跑完一次执行，它读完轨迹和分数，选择下一步做 harness 更新还是权重更新。

读完整套代码之后，我的判断落在一个差别上：论文描述的那层设计是完整的，仓库交付的是另一层。`sia run` 用 `--focus harness|weights` 决定这次运行改什么，默认 `harness`；这个值是运行级参数，一次 run 从头到尾只走一条通道，一轮迭代在目录里记作 `gen_{n}`、下文称"一代"，两条通道生成的产物、装的依赖包、要的环境变量都不一样。仓库里也没有任何"由 Agent 挑杠杆"的实现分支：`SIA-W+H` 这个论文记号在 `sia/` 源码里没有任何对应物，只在 README 的三句配图说明里出现过。改进循环本身——读日志、找失败模式、重写下一代的代码——是真实的、可跑的、可检查的；把两种改进动作调度在一起的那层决策，留在论文里。

这层差别不是缺点，反而让 SIA 变成一个比多数"自改进 Agent"更好评估的对象。要复现论文的 70.1%，缺的不是框架结构，而是自己的 Tinker 与 Modal 账号、一份能给出标量的 verifier，以及一个明确的任务目录。

---

## 二、系统地图：角色、两条通道与一次 run 的边界

### 2.1 三个角色，两处实现

| 角色 | 论文里的职责 | 代码里在哪 | 留下什么 |
| --- | --- | --- | --- |
| Meta-Agent | 从任务说明书和参考实现出发，搭出第一代脚手架 $A_1$ | `sia/prompts.py` 的 `build_meta_prompt()`（weights 模式走 `_build_weights_meta_prompt()`） | `gen_1/target_agent.py` 或 `gen_1/train.py`、`meta_agent_prompt.txt` |
| Target / Task-Specific Agent | 在沙箱里执行任务：数据集目录只读，工作目录可写 | `sia/agent_impls/{claude,openhands,pydantic_ai}.py` 提供执行后端 | 提交文件、`agent_execution.json`、`target_agent_stdout.log` |
| Feedback / Improvement Agent | 读执行轨迹 $\tau_g$ 与上一代分数，产出下一代 | `sia/prompts.py` 的 `build_feedback_prompt()`，由 `sia/orchestrator.py` 调起 | `gen_{n+1}/` 的改进版代码、`improvement.md`、`feedback_agent_prompt.txt` |

三个角色共用两个模型槽位：Meta 与 Feedback 都读 `--meta-agent-profile`（同一个 `agent_impl`、同一个模型），Target 读 `--target-agent-profile`，所以"用强模型改进弱模型"这种配置在代码里就是给 target 换一个便宜的 profile。角色之间没有共享内存状态，信息靠磁盘上的文件传递：上一代的代码、上一代的执行日志、上一代评估出的 `results.json`，以及一份记录整条 run 演化史的 `context.md`。这也是它跟"单 Agent + 自我反思"最实际的区分——反思结果要落成能被下一代替旧代码的文件，而不是对话里的一段话。

### 2.2 两条通道，一次 run 选一条

| 维度 | `--focus harness`（默认） | `--focus weights` |
| --- | --- | --- |
| 改什么 | Target 的代码、提示词、工具调用与解析逻辑，模型权重不动 | 用 RL 调模型自身的权重，脚手架冻住 |
| 每代产物 | `gen_{n}/target_agent.py` | `gen_{n}/train.py`（要返回训练后模型的 checkpoint URL） |
| 执行日志 | `target_agent_stdout.log` | `train_stdout.log` |
| 每 run 的 venv 里装什么 | `VENV_PACKAGES` 那 10 个包（含 `scikit-learn`、`pandas`、`anthropic`、`openai`） | 同一批基础包，再加 `vllm`、`tinker`、`tinker-cookbook[modal]`（从 GitHub nightly 装） |
| 必需环境变量 | 所选 provider 的 `api_key_env` | `TINKER_API_KEY`；`--training_sandbox modal` 时还要 `MODAL_TOKEN_ID` 与 `MODAL_TOKEN_SECRET` |
| 训练代码跑在哪 | Target 沙箱：`--sandbox none`（宿主）或 `docker` | `--training_sandbox modal`（默认）或 `sandboxfusion` |
| 启动时校验 | 缺 key 只警告一句 | 缺 `TINKER_API_KEY` 直接抛 `RuntimeError` 退出 |

`orchestrator.py` 在读取当代代码时就分叉了：`focus == "weights"` 去读 `train.py`，否则读 `target_agent.py`。整个循环的骨架不变，换的是"被改进的那个对象"到底是什么文件。论文里 Feedback-Agent 在两种动作之间来回切换的那段设计（§5.1 称两个阶段是 soft label，不是刚性顺序），代码给出的对应物是一个启动参数。

### 2.3 论文里权重通道具体做什么

weights 通道的提示词是一整篇 RL 集成指南：要求模型基于 `tinker-cookbook` 搭出任务专属的 `Env`、`EnvGroupBuilder` 与 `RLDataset`，并用 Modal 的 `@app.function` 做代码执行沙箱。交付物是一个接受 `--dataset_dir`（只读）与 `--working_dir`（读写）的 `train.py`，提示词里还硬性要求把这两个绝对路径原样写进发给目标模型的提示中，免得模型自己去猜数据在哪。论文侧的实现是基座模型上的 LoRA（低秩适配）适配器，训练算法由 Feedback-Agent 按当下的奖励景观挑。论文观察到两种选择：PPO + GAE 出现在步级奖励密集、一次崩掉就毁掉策略的长任务上；GRPO 出现在 rollout 便宜、验证器只在回合末打分的分类与短答案任务上。LawBench 最后那 20.1 个百分点就是 GRPO 拿的。

---

## 三、仓库结构：代码里的循环长什么样

下面这份结构树按 `main` 分支 2026-08-26 那次提交（`7fd04d0`）的本地副本核对。

```text
sia/
├── sia/
│   ├── cli.py                    # run / web 两个子命令的参数定义与向后兼容
│   ├── orchestrator.py           # 主循环：35 KB，含 run_evaluation()
│   ├── prompts.py                # 40 KB，meta 与 feedback 两族提示词
│   ├── context_manager.py        # 写 run 级 context.md，抽 improvement.md 要点
│   ├── layout.py                 # BUNDLED_TASKS 与所有文件名字面量
│   ├── run_setup.py              # 建 run 目录、按 focus 装 venv 依赖
│   ├── profiles.py providers.py  # profile/provider 的加载与校验
│   ├── config_files.py           # 内置目录与用户目录（$SIA_*_DIR）的解析
│   ├── agent_reference.py        # agent_reference 三种写法的解析与拷贝
│   ├── results.py api_keys.py    # 结果读取、密钥检查
│   ├── agent_impls/              # claude / openhands / pydantic_ai 三个后端
│   ├── web/                      # server.py + runs.py，runs/ 的可视化数据层
│   ├── defaults/
│   │   ├── providers/            # 7 个内置 provider
│   │   └── profiles/             # 11 个内置 profile
│   ├── tasks/                    # 4 个随 wheel 发布的内置任务
│   │   ├── _shared/              # reference_target_agent.py + 样例轨迹
│   │   ├── gpqa/  lawbench/  longcot-chess/  spaceship-titanic/
│   └── prepare_mlebench_dataset.py
├── docs/                         # architecture / walkthrough / configuration
│                                 # evaluator_design / troubleshooting，另有 7 张配图
├── tests/                        # 22 个 test_*.py，含 context 与 prompt 快照
└── EVALUATION_GUIDE.md           # evaluate.py 契约
```

一轮运行写出的目录，字段名全部来自 `sia/layout.py` 的 `Names`：

```text
runs/run_1/
├── context.md                    # run 级：元信息块 + 每代条目 + 收尾统计
├── venv/                         # 每个 run 一个隔离虚拟环境
└── gen_1/
    ├── target_agent.py           # 或 train.py（weights 模式）
    ├── meta_agent_prompt.txt     # 只有第一代是 meta 提示词
    ├── feedback_agent_prompt.txt # 第二代起换成 feedback 提示词
    ├── agent_execution.json      # 执行轨迹；多问题任务另有 agent_execution/
    ├── target_agent_stdout.log   # 或 train_stdout.log
    ├── evaluation.log            # 评估子进程的 stdout + stderr
    ├── results.json              # 由任务的 evaluate.py 自己写出
    └── improvement.md            # 第二代起才有
```

提交文件的形状不属于框架约定，属于任务约定。LawBench 的评估器在 `submission.csv` 与 `predictions.csv` 里挑，LongCoT Chess 要 `responses.json`，GPQA 只认 submission JSON，找哪个文件由各任务的 `evaluate.py` 自己决定。`context.md` 在 run 目录而不是代目录里，`prompts.py` 拼 feedback 提示词时会把它的绝对路径写进去，让 Feedback-Agent 自己读整条演化史。

---

## 四、一次任务流的落地路径：内置 lawbench 跑五代

内置任务里 `lawbench` 的数据是自足的，拿它串一遍最容易验证。任务包 `sia/tasks/lawbench/` 分成三块：`data/public/` 有 `task.md`、`classes.json`（191 个罪名标签的穷举列表）、`test.csv`（913 条 `id,text`，正文是判决书里的事实段）和 `evaluate.py`；`data/private/test.csv` 只有 `id,label` 两列，是答案卷；`reference/` 放参考实现与样例任务描述。另外还有一份 `data/training_data/`，`train.csv` 是带标签的 5,332 条，与论文 Table 2 报的训练量对得上。

`task.md` 里写明了约束与目标：只能从 `classes.json` 的 191 个标签里选，输出 `submission.csv` 且列名为 `id,label`，913 个 id 必须齐全，指标是 accuracy；还给了一条模型要求——所有基于大语言模型（LLM）的预测都用 `openai/gpt-oss-120b`。文件末尾抄了一段基线情报：零样本约 7%，一个 few-shot harness 方案（文中点名 Meta-Harness）约 45%，目标是 70% 以上。

启动：

```bash
export ANTHROPIC_API_KEY="..."
sia run --task lawbench --max_gen 5 --run_id 1
```

接着发生的事，按 `orchestrator.py` 的顺序：

1. 解析 profile，打印 meta 与 target 各自的模型、provider、`agent_reference` 类型；某个 provider 的 `api_key_env` 没设，只警告一句"该 Agent 可能认证失败"，继续跑。
2. 建 `runs/run_1/`，起 venv，装上 `VENV_PACKAGES` 列出的 10 个包，写 run 级 `context.md` 的头部。
3. 第一代：把 `task.md`、样例任务描述、参考实现的正文拼进 meta 提示词（目录型参考只给路径，让 Agent 用工具自己读），并硬性要求产物 `target_agent.py` 接受 `--dataset_dir`（只读）与 `--working_dir`（读写）。执行后落到 `gen_1/target_agent.py`。
4. Target 执行任务：`python -u target_agent.py --dataset_dir <data/public> --working_dir <gen_1>`；`--sandbox docker` 时这两个路径换成挂载点 `/data:ro` 与 `/work:rw`。跑完 913 条预测写 `gen_1/submission.csv`，191 个标签之外的值一律算错，轨迹进 `agent_execution.json`。
5. `run_evaluation()` 找到 `data/public/evaluate.py`，用那个 venv 的 python 起子进程：`python evaluate.py --gen-dir runs/run_1/gen_1`，超时 600 秒，输出合并写进 `evaluation.log`。
6. 脚本自己把分数写进 `gen_1/results.json`，内容为 `accuracy`、`n_correct`、`n_total` 和一个 `per_class` 字典。顶层标量会被 `context_manager.py` 抽进 `context.md` 的当代条目，并出现在 `sia web` 的跨代准确率折线图上。
7. 第二代起，feedback 提示词里同时有上一代代码、执行状态、分数摘要和 `context.md` 路径，产出 `gen_2/target_agent.py` 与 `gen_2/improvement.md`。

论文 §6.3.1 与 §7.2 记下了这条循环在 LawBench 上实际改了什么。早期几代把可用的分类流程搭起来，后续几代将其重构成 TF-IDF + LinearSVC，反复调字符 n-gram 范围与正则化系数 $C$。再往后补了两样东西：一个结构化的答案抽取层，一个在模型 top 候选上做重排的 SVC re-ranker。整个过程 `gpt-oss-120b` 的 checkpoint 没动过，13.5% 抬到 50.0% 全部来自脚手架。接权重通道之后 GRPO 把 top-1 推到 70.1%。

有三件事得先讲明，免得照着上面几步就去看数字。论文的评测任务里只有 LawBench 带内置任务目录，TriMul 内核与单细胞去噪都不在这个仓库里。LawBench 的评测切分与论文同源（913 条），但 `task.md` 指定用 `gpt-oss-120b` 做求解模型，内置的 `_shared/reference_target_agent.py` 却是照着 Anthropic 的客户端写的。那份模板有 303 行，模型常量写死成 `claude-haiku-4-5-20251001`，配 `write_file`、`read_file`、`bash` 三个工具。第三，论文没交代每个 benchmark 跑了多少代、花了多少算力。

---

## 五、Benchmark 数字：三套口径要先对齐

论文里做横向对照的是 Table 3，四列依次是初值、此前最优、只做 harness、harness 加权重：

| 任务 | 指标（越大越好） | Initial | Prev. SOTA | SIA-H | SIA-W+H |
| --- | --- | --- | --- | --- | --- |
| LawBench（191 类罪名） | top-1 准确率 | 13.5% | 45.0% | 50.0% | **70.1%** |
| AlphaEvolve TriMul | reward = 1500 / 运行时间 | 0.105 | 1.292 | 0.120 | **1.475** |
| MAGIC scRNA-seq 去噪 | `mse_norm` ∈ [0, 1] | 0.048 | 0.240 | 0.241 | **0.289** |

先把译名钉住：论文 Table 2 里那列 verifier 下文译作"验证器"，指判分的规则；仓库里那个 `evaluate.py` 叫"评估器"，是验证器的实现。每个 benchmark 测什么、数字反映哪一层、不能推出什么，逐项看：

**LawBench（Fei et al., 2023）** 给 913 条真实刑事判决书事实描述，从 191 个罪名里选一个，验证器是留出的测试集。13.5% 这一列是"gpt-oss-120b 套最小脚手架"的构造性基线，随机猜在这个任务上不到 1%。数字差里能读出的东西比较硬：脚手架把 13.5% 抬到 50.0%，权重更新又抬 20.1 个百分点，两段的量级不重叠，所以"只调提示词也能到 70%"这种推论不成立；反过来，Prev. SOTA 那一列的 45.0% 在任务包 `task.md` 里被标成一个 few-shot harness 方案（点名 Meta-Harness）的成绩，说明这套任务对脚手架确实敏感。不能推出的：`evaluate.py` 只算 `accuracy`，没有 top-5；`per_class` 是逐类正确率，论文没给长尾类别上的分解。

**AlphaEvolve TriMul** 测的是能不能在 H100 上把 AlphaFold2 Evoformer 的三角乘性更新写成 Triton 内核并把运行时间压下来。验证器就是 H100 计时，reward 定义为 1500 除以运行时间，因此 reward 与微秒数成反比。论文给出的具体值是：harness 通道最好成绩 12,483 μs，权重通道压到 1,017 μs，相对前者省下 91.9% 的运行时间，也即相对未优化初版 14.02×。此前最优是 1,161 μs，SIA-W+H 快它 12.4%。分母要逐个认：14.02× 是相对未优化初版，12.4% 才是相对既有最优，而 91.9% 那句按 §6.3.2 的原文是相对 harness 峰值；摘要把三个数一并挂在 "over the initial baseline" 底下，读的时候容易串。论文对这一节的解释也值得抄给同事看——让内核变快的是共享内存分块、寄存器内 fp32 累加、block size 选择这类硬件直觉，"任何脚手架编辑都编码不进去"。

**MAGIC scRNA-seq 去噪** 在胰腺单细胞数据上补被丢弃的基因表达值，`mse_norm` 归一到 [0, 1] 且越大越好，验证器是拿 MAGIC 参考做比对。SIA-H 拿到 0.241，几乎贴着 0.240 的既有最优；SIA-W+H 到 0.289。README 里的 +502% 是对 0.048 那个初值算的，对既有最优只有 20.4%。这一行给出的信息是两条杠杆贡献不对称：去噪任务的瓶颈在模型本身会不会，不在提示词怎么写。

**README 里的 MLE-Bench Hard 那句要单独处理。** "a gauntlet of real Kaggle ML competitions" 与 "SIA ranks #1 across all generations tested" 这两句只在仓库首页的配图说明里出现。论文 v1 与 v2 正文都检索不到 `MLE-Bench` 或 `Kaggle` 字样，Table 3 里也没有对应行。它的口径更像是"在 MLE-Bench 的 leaderboard 上按代际排名"的展示性结论，不要作为论文结果引用，也不要和上面三行放进同一张表比较。

几条推不出来的结论，连同它们的依据：

- 推不出跨任务泛化。三域的验证器都是确定性打分（留出题、计时、参考比对），LawBench 的训练/测试量是 5,332 / 913，TriMul 与去噪没有留出集概念。
- 推不出"权重通道单独跑更好"。论文只报了 SIA-H 与 SIA-W+H 两个操作点，没有 SIA-W-only 这一列，而 SIA-W+H 的定义是"在 harness 最好成绩之上叠加权重更新"。
- 推不出循环稳定收敛。论文 §8 把这条列为主要失效风险：harness 搜索与 RL 更新优化的是同一个固定 verifier，两边各自塑造对方看到的分布。于是联合不动点相当于两个优化器之间的 Nash 均衡，而它们对彼此的更新历史是盲视的——在训练验证器上可以很强，对任一组件做扰动就脆。§9 也承认，选杠杆的那个策略目前是一个冻结的 LLM（大语言模型）先验，把它本身变成可学习对象属于 future work。

---

## 六、Profile、Provider 与 agent_impl

配置层只有两个概念：provider 是一个 endpoint 加一套凭据，profile 配置一个角色。meta profile 绑 `(agent_impl, model, provider)`，target profile 绑 `(model, provider, agent_reference)`，都是 JSON 文件。内置 provider 七个：

| provider_id | client_kind | base_url | api_key_env |
| --- | --- | --- | --- |
| `anthropic` | `anthropic` | — | `ANTHROPIC_API_KEY` |
| `gemini` | `google` | — | `GEMINI_API_KEY` |
| `openai` | `openai` | `https://api.openai.com/v1` | `OPENAI_API_KEY`（应用程序接口密钥变量） |
| `openrouter` | `openai` | `https://openrouter.ai/api/v1` | `OPENROUTER_API_KEY` |
| `nebius` | `openai` | `https://api.tokenfactory.us-central1.nebius.com/v1/` | `NEBIUS_API_KEY` |
| `together` | `openai` | `https://api.together.ai/v1` | `TOGETHER_API_KEY` |
| `tinker` | `openai` | `https://tinker.thinkingmachines.dev/services/tinker-prod/oai/api/v1` | `TINKER_API_KEY` |

`client_kind` 只接受 `anthropic`、`openai`、`google` 三个值，`openai` 那一类靠 `base_url` 适配各种兼容端点。自建端点写两个文件即可：

```jsonc
// providers/my-endpoint.json
{
  "provider_id": "my-endpoint",
  "name": "My Endpoint",
  "client_kind": "openai",
  "base_url": "https://api.example.com/v1",
  "api_key_env": "MY_ENDPOINT_API_KEY"
}
```

```jsonc
// profiles/my-target.json
{
  "profile_id": "my-target",
  "name": "My model on My Endpoint",
  "model": "vendor/my-model",
  "provider_id": "my-endpoint",
  "agent_reference": "default"
}
```

```bash
export MY_ENDPOINT_API_KEY="..."
sia run --task gpqa --target-agent-profile my-target          # 按名字解析 ./profiles/
sia run --task gpqa --target-agent-profile ./profiles/my-target.json  # 或给显式路径
```

用户目录默认是当前工作目录下的 `./providers/` 与 `./profiles/`，可以用 `$SIA_PROVIDERS_DIR` / `$SIA_PROFILES_DIR` 改。`agent_reference` 有三种写法：`"default"` 用任务包自带的参考实现；`{"source": "./my_agent.py"}` 给单文件；`{"source": "./dir/", "entrypoint": "main.py"}` 给多文件目录，目录里的 `requirements.txt` 每代都会装一次。它是 Meta-Agent 的起点，也是 Feedback-Agent 改的底座。

角色之间的模型可以分开配。README 举的例子是 target 换成 `kimi-nebius-target`（`moonshotai/Kimi-K2.6` 走 Nebius）、meta 保持默认；把 meta 挪到别的实现要给 meta profile 换 `agent_impl`，`openhands` 或 `pydantic-ai` 都行，`claude` 那条路只接 Anthropic 自家模型。内置的 11 个 profile 覆盖 default、gemini、kimi、gptoss、qwen、openrouter 几组。这里有一处口径差要先说明：**默认的 `default-meta` 与 `default-target` 都指向 Claude Haiku**（模型 ID 分别写作 `haiku` 与 `claude-haiku-4-5-20251001`）。OpenRouter 那两个内置 profile 用的同样是 `anthropic/claude-haiku-4.5`，而论文的数字是在 `gpt-oss-120b` 上测出来的。拿默认配置跑出来的准确率，和本文第五节的表不在同一个坐标系里。

还有一层配置不在 profile 里，而在 `sia/config.py`：`--max_gen` 默认 3，Meta 与 Feedback 每次调用最多 20 个 turn，评估子进程 600 秒超时。Docker 沙箱用 `python:3.11-slim`，限 2 GB 内存、2 张 CPU、3600 秒；`context.md` 与执行日志分别限制在 10 MB 与 50 MB。大部分项能被 `SIA_*` 环境变量覆盖（`SIA_MAX_GENERATIONS`、`SIA_MAX_TURNS`、`SIA_SANDBOX_MODE`、`SIA_AGENT_IMPL`、`SIA_TASK_MODEL` 等），代码里的非法值会被 `contextlib.suppress` 静默丢掉，改完最好确认一下启动横幅。

---

## 七、评估契约：整条循环只认 results.json

自改进的信号来源不是模型自评。orchestrator 每代结束后做的事就一句：找到脚本，起子进程，等 `results.json` 出现。

`evaluate.py` 的实际形状（`EVALUATION_GUIDE.md` 与 `sia/tasks/lawbench/data/public/evaluate.py` 一致）：

```python
"""与 lawbench 的 evaluate.py 同构，省掉了 per_class 与多文件名回退。"""
import argparse, json
from pathlib import Path
import pandas as pd

TASK_DIR = Path(__file__).parent.parent.parent
TRUTH = TASK_DIR / "data/private/test.csv"

def evaluate(submission_path: Path) -> dict:
    truth = pd.read_csv(TRUTH)                              # id,label
    pred = pd.read_csv(submission_path)                    # id,label（列名容错见原文件）
    merged = truth.merge(pred, on="id", how="left", suffixes=("", "_pred"))
    ok = merged["label"] == merged["label_pred"]
    return {"accuracy": float(ok.mean()),
            "n_correct": int(ok.sum()),
            "n_total": int(len(ok))}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen-dir", type=Path, required=True)
    args = ap.parse_args()
    results = evaluate(args.gen_dir / "submission.csv")
    (args.gen_dir / "results.json").write_text(json.dumps(results, indent=2))
```

三段要点都在里面：入参是**提交文件路径**而不是代目录，找哪个提交文件由脚本自己决定，`results.json` 也由脚本自己写——orchestrator 只负责读。`main()` 收 `--gen-dir`，是为了让同一个文件既被流水线调用，也能被人工调用。

`find_evaluate_script()` 写的查找顺序是先 `<task_dir>/data/public/evaluate.py`，再退到 `<task_dir>/evaluate.py`；而 `run_evaluation()` 拿到的实参已经是任务的 `data/public`，所以真正生效的位置就是 `data/public/evaluate.py` 一处。两处都找不到时，它打一行 "skipping evaluation" 并返回 `{"status": "skipped", ...}`，循环照跑，只是 Feedback-Agent 那一代没有分数可读。四个内置任务里 `spaceship-titanic` 恰好就是这一种：它带 `data/public/{task.md, train.csv, test.csv, sample_submission.csv}` 和 `data/private/test.csv`，没带 `evaluate.py`。想跑 Kaggle 那条路，得自己补一个评分脚本，或者用 `prepare_mlebench_dataset` 从比赛引导出目录。

返回字典怎么写有讲究，但不是格式讲究。`context_manager.py` 抽的是**顶层标量**，嵌套结构要放到 `details` 之类的键里，否则下一代的提示词读不到主分数。`docs/evaluator_design.md` 整篇都在讲另一件事：评估器就是任务规格，奖励错了循环会稳定地放大那个错误。它给的清单里几条特别容易忽略——`data/private/` 只是 harness 层面的约定，Target 以宿主权限跑的时候它不是安全边界，需要硬隔离就上 `--sandbox docker`；指标要带切片（易/难、常见类/罕见类、public/私有留出、此前失败/新引入），否则一个标量藏住过拟合；主分数跨代保持稳定；评估器必须能脱离整条 run 单独跑通（`python data/public/evaluate.py --gen-dir /tmp/example-gen` 加 `python -m json.tool` 看产物）。

---

## 八、常见报错与排查

按现象找比按模块找快。前四行的现象出自 `docs/troubleshooting.md`，其余五行取自代码里的启动校验与 `run_evaluation()` 分支。

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| `Run directory already exists` | orchestrator 拒绝覆盖已有 run | 换 `--run_id`，或删掉 `runs/run_1` |
| Target 跑完但没提交文件 | 任务里写的是相对路径 | 任务与提示词统一用绝对路径；看 `gen_1/agent_execution.json` |
| `ImportError: No module named 'anthropic'` | 每 run 一个 venv，包没装进去 | `runs/run_1/venv/bin/pip install anthropic`，或让目录型参考带 `requirements.txt` |
| `PermissionError: Kaggle authentication failed!`（Kaggle 身份认证失败） | `mlebench prepare` 要 Kaggle 凭证 | 设 `KAGGLE_USERNAME` / `KAGGLE_KEY`，或放 `~/.kaggle/kaggle.json`；并先在 Kaggle 接受比赛规则 |
| 启动横幅里 `⚠ XXX_API_KEY is not set` | profile 指向的 provider 缺 key | 补 export，别指望它自动失败，Agent 会在中途报认证错 |
| weights 模式启动即 `RuntimeError: TINKER_API_KEY not set` | RL 通道必须连 Tinker | 设 `TINKER_API_KEY`；`--training_sandbox modal` 还要 `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` |
| weights 模式卡在训练代码执行 | `--training_sandbox sandboxfusion` 要求服务在跑 | 本机 `localhost:8080` 起服务，或用 `SANDBOX_URL` 指到别处；启动警告还要求给 Docker 留 40 GB 以上磁盘 |
| `results.json` 一直不出现，`evaluation.log` 有 traceback | 评估脚本超过 600 秒，或自己没写文件 | 先按第七节那样脱离 run 单测；重的评估要把 `details` 收窄 |
| 折线图空着 | 指标藏在嵌套字典里 | 主分数提到顶层标量，明细放 `details` |

一次 run 里最贵的失败往往是"跑完了但分数没有"。所以第一次接自定义任务，先只跑 `--max_gen 1`，确认 `gen_1/results.json` 有内容再谈代际。

---

## 九、什么时候值得跑，什么时候先别上

适合的情形有四类：你已经有确定性的验证器（留出题、单元测试、计时、参考比对），并且愿意为它写 `evaluate.py`；任务改进是长链路的，改的是"这套代码怎么组织搜索和重试"；你需要一份可审计的演化记录，`runs/` 下每代的源码、提示词、日志和分数都在，`diff` 两代 `target_agent.py` 就能看出循环做了什么；或者你在研究两条杠杆各自的贡献边界，需要一套能把它们分开跑的脚手架。

不适合的情形也能列具体：任务没有标量反馈，只有"人看着满意"——`run_evaluation()` 找不到脚本就静默 skip，循环退化成没有度数的重写；想验证一次 run 内自动切换 harness 与 weights——这个开关在命令行参数上，不在 Agent 手里；要的是单轮反思式改进——提示词里加一段自我批评就够，不必起一代一次的目录树；数据量小到单代只有几十条——`per_class` 这类切片指标的方差会盖过代际差，读不到稳定信号。

采用顺序，按投入产出排：

1. 先跑 `lawbench` 或 `longcot-chess`，都是数据自带、评估器自带，`--max_gen 2 --run_id 1 --sandbox docker` 起步。
2. 打开 `sia web`（或者什么都不做，仪表盘（dashboard）默认起在 `127.0.0.1:8000`），确认能看到跨代折线；看不到就先修第七节，别加代。
3. 想对表论文数字，target profile 换成 `gptoss-tinker-target`（模型 `openai/gpt-oss-120b`，走 Tinker）或 `gptoss-nebius-target`（`openai/gpt-oss-120b-fast`，走 Nebius）。默认的那两个 Haiku profile 不具备可比性。注意内置 profile 的名字按文件名解析（`<name>.json`），而 `gptoss-tinker-target.json` 里的 `profile_id` 写的是 `gptoss-tinker`，两处不一致。
4. 接自己的任务：`--task_dir ./my-tasks/x`，`data/public/task.md` + `data/private/` + `reference/reference_target_agent.py`（模板从 `sia/tasks/_shared/` 拷），先 `--max_gen 1`。
5. harness 通道跑到分数曲线平了，再考虑 weights——那条通道另要 Tinker 与 Modal 两个外部服务，`train.py` 也是生成的而不是现成脚本。
6. Kaggle 比赛走 `python -m sia.prepare_mlebench_dataset -c spaceship-titanic`（先装 `sia-agent[mlebench]` 和 GitHub 上的 mle-bench），跑完记得补 `evaluate.py`。

---

## 十、动手练习

三个练习都用真实命令，第二个和第三个不联网也能做。

### 练习 1：跑通一代，并核对产物清单

```bash
git clone https://github.com/hexo-ai/sia.git && cd sia
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"           # 开发装法；只跑的话按 README 用 'sia-agent[claude]' 或 [openhands]
export ANTHROPIC_API_KEY="..."
sia run --task longcot-chess --max_gen 1 --run_id 1 --no-web
find runs/run_1 -maxdepth 2 -type f | sort
```

验收：`gen_1/` 下同时出现 `target_agent.py`、`agent_execution.json`、`meta_agent_prompt.txt`、`evaluation.log`、`results.json`，`runs/run_1/context.md` 里有第一代条目。`improvement.md` 和 `feedback_agent_prompt.txt` 不该出现，它们从第二代开始写。

### 练习 2：只读代码，确认"选杠杆"这件事没有实现

```bash
grep -rn '"--focus"' sia/cli.py
grep -rn 'args.focus' sia/orchestrator.py | head
grep -rn 'train.py' sia/orchestrator.py | head -3
```

验收：能说出三件事——`--focus` 的 `choices` 是 `["harness", "weights"]`，`args.focus` 在运行期只被读、从没被改写；weights 分支读的是 `gen_{n}/train.py`；`run_evaluation()` 的入参里没有 focus，说明两条通道共用同一套评估契约。

### 练习 3：给一个没有评估器的任务补上

```bash
mkdir -p my-tasks/demo/data/public my-tasks/demo/data/private my-tasks/demo/reference
cp sia/tasks/_shared/reference_target_agent.py my-tasks/demo/reference/
python - <<'PY'
import json, random
rows = [{"id": i, "a": random.randint(1, 9), "b": random.randint(1, 9)} for i in range(40)]
json.dump(rows, open("my-tasks/demo/data/public/questions.json", "w"))
json.dump({str(r["id"]): r["a"] * r["b"] for r in rows},
          open("my-tasks/demo/data/private/answers.json", "w"))
PY
```

在 `data/public/task.md` 里写清输入文件、输出文件名与格式，再照第七节写 `data/public/evaluate.py`。

验收：`python my-tasks/demo/data/public/evaluate.py --gen-dir /tmp/any` 能退出码 0 并写出 `results.json`；`sia run --task_dir ./my-tasks/demo --max_gen 1` 的横幅里不出现 `skipping evaluation`。

---

## 十一、自测题

1. **代码里的 harness 通道和 weights 通道分别在改什么，产物差在哪？**
   <details>
   <summary>参考答案</summary>
   由 `--focus` 决定，一次 run 只走一条通道。harness 每代生成 `target_agent.py`，改提示词、工具、解析与重试，权重不动；weights 每代生成 `train.py`，用 `tinker-cookbook` 搭 RL 管线更新权重，脚手架不动。执行日志相应地是 `target_agent_stdout.log` 与 `train_stdout.log`；weights 另需 `TINKER_API_KEY`，训练代码跑在 Modal 或 SandboxFusion 里。
   </details>

2. **论文 Table 3 里 LawBench 的四列各是多少，能读出什么、不能读出什么？**
   <details>
   <summary>参考答案</summary>
   Initial 13.5%、Prev. SOTA 45.0%、SIA-H 50.0%、SIA-W+H 70.1%。能读出：脚手架只把 13.5% 抬到 50.0%，剩下 20.1 个百分点来自权重更新。不能读出权重通道单独能到多少（表里没有 SIA-W-only 这一列），也不能读出来自 70.1% 的是哪个指标族——内置 `evaluate.py` 只算 `accuracy`。
   </details>

3. **README 说 MLE-Bench Hard "#1 across all generations tested"，这句话能当论文结果引用吗？**
   <details>
   <summary>参考答案</summary>
   不能。论文 v1、v2 正文都检索不到 `MLE-Bench` 或 `Kaggle`，Table 3 也没有对应行；这句只在仓库首页的配图说明里，口径是 leaderboard 排名，与三个 benchmark 的消融表不同源。
   </details>

4. **为什么"评估器要能脱离整条 run 单独跑通"是硬要求？**
   <details>
   <summary>参考答案</summary>
   因为 orchestrator 只用子进程调它：`python evaluate.py --gen-dir <gen>`，600 秒超时，stdout/stderr 进 `evaluation.log`，非零退出码只被记成 `status: error` 而不中断循环。脚本自己没跑过，整条自改进信号就会静默变成 skipped 或 error，代际继续白烧。
   </details>

5. **默认 profile 能直接对表论文的 LawBench 70.1% 吗？**
   <details>
   <summary>参考答案</summary>
   不能。`default-meta` 与 `default-target` 都指向 Claude Haiku，论文的实验模型是 `gpt-oss-120b`；要对表得把 target profile 换成 gptoss 系列，并且自带对应的 provider 端点与额度。
   </details>

---

## 十二、下一步读哪份代码

按"想知道什么就读哪里"的顺序，不用从头读到尾：

- 循环骨架：`sia/orchestrator.py`。`run_evaluation()` 从 185 行起，feedback 按 focus 选文件在 575-577 行，主循环里的三处分支在 823、882、948 行。
- 提示词到底注入了什么：`sia/prompts.py`，`build_meta_prompt()`、`build_feedback_prompt()`、`_build_weights_meta_prompt()` 三个入口，权重模式那篇 RL 指南从第 39 行开始。
- 代际之间怎么传上下文：`sia/context_manager.py`，注意它写的是 run 级 `context.md`，并从 `improvement.md` 里抓要点。
- 文件名与目录常量的唯一来源：`sia/layout.py`，含 `BUNDLED_TASKS` 和 `resolve_task_dir()` 的 `_shared` 解析规则。
- 想加任务或换后端：`docs/walkthrough.md`、`sia/agent_reference.py`、`sia/agent_impls/`。
- 评估器怎么写才不被刷分：`EVALUATION_GUIDE.md` 打底，`docs/evaluator_design.md` 讲对抗性自审。
- 论文侧的机制叙述与消融：arXiv:2605.27276 v2 的 §5、§6.3、§7、§8。
- 回归基线：`tests/` 里的 `test_prompts_snapshot.py` 与 `tests/golden/context.md`，改提示词前先看它们会不会挡住。

---

## 十三、资料口径与未定项

- 仓库侧：`https://github.com/hexo-ai/sia` 的 `main`，完整提交号 `7fd04d07bd2f47a110115674432b73622ebf7455`（2026-08-26），包版本 0.6.0。文中所有文件名、默认值、命令行参数、内置任务与 provider/profile 清单都取自这份本地副本。
- 论文侧：arXiv:2605.27276 v2（2026-05-28）。第五节的四列数字取自 Table 3，任务设定与验证器取自 Table 2，机制描述取自 §5.1-§5.2 与 §6.2。逐任务的改进内容取自 §6.3 与 §7.2-§7.3，局限与后续工作取自 §8-§9。
- 口径换算：LawBench 的 +56.6% 是 70.1 减 13.5（百分点，对初值），+25.1% 是 70.1 减 45.0（对既有最优），§6.3.1 里的 +20.1 是相对 SIA-H；去噪的 +502% 对 0.048，+20.4% 对 0.240；TriMul 的 91.9% 按正文是 12,483 → 1,017 μs。三行的分母各不相同，不能混用。另外按 Table 2 定义的 reward = 1500/runtime 反推，Table 3 的 0.105 / 0.120 / 1.475 分别约当 14,286 / 12,500 / 1,017 μs，与正文的 12,483 → 1,017 μs 和 14.02× 互相吻合。这层换算只用于校验口径，不作为新的数字引用。
- 未定项（unresolved）：论文实验脚本没有随仓库发布，三个 benchmark 的代际数、算力与随机种子在 README 和 docs 里都没写；`SIA-W+H` 在代码层没有对应实现，无法确认它是由人工按"先 harness 后 weights 两次 run"拼出来的还是另有脚本；MLE-Bench Hard 的"#1"缺少可核对的表格；`spaceship-titanic` 未带评估器是否有意为之，仓库里没有说明。

---

## 引用

```bibtex
@article{hebbar2026sia,
  title   = {SIA: Self Improving AI with Harness \& Weight Updates},
  author  = {Hebbar, Prannay and Manawat, Yogendra and Verboomen, Samuel
             and Ivanova, Alesia and Palanimalai, Selvam and Bhatia, Kunal
             and Baskaran, Vignesh},
  journal = {arXiv preprint arXiv:2605.27276},
  year    = {2026},
  url     = {https://arxiv.org/abs/2605.27276}
}
```

## 参考链接

- 仓库：<https://github.com/hexo-ai/sia>
- 论文：<https://arxiv.org/abs/2605.27276>
- 架构文档：<https://github.com/hexo-ai/sia/blob/main/docs/architecture.md>
- 自定义任务走查：<https://github.com/hexo-ai/sia/blob/main/docs/walkthrough.md>
- 配置与命令行工具（CLI）参考：<https://github.com/hexo-ai/sia/blob/main/docs/configuration.md>
- 评估契约：<https://github.com/hexo-ai/sia/blob/main/EVALUATION_GUIDE.md>
- 评估器设计清单：<https://github.com/hexo-ai/sia/blob/main/docs/evaluator_design.md>
- 排错手册：<https://github.com/hexo-ai/sia/blob/main/docs/troubleshooting.md>
- PyPI：<https://pypi.org/project/sia-agent/>
