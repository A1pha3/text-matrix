---
title: "Prime Agent 拆解：上下文当变量、改进进状态，RLM 编程模型的落地样本"
date: 2026-08-15T03:24:06+08:00
lastmod: 2026-10-01T00:00:00+08:00
slug: "prime-agent-self-improving-rlm-agent"
github_repo: "PrimeIntellect-ai/prime-agent"
source_key: "gh:PrimeIntellect-ai/prime-agent"
description: "按 2026-10-01 的 main 分支实物拆解 Prime Agent：自研 CPython REPL 与 rlm.spawn 递归子代理、Continual Harness 的四类状态与 refine 的精确时机、TypeScript 到 Rust 的重写现状，以及 RLM 消融数据能说明和不能说明什么。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "RLM", "递归语言模型", "Prime Intellect", "Rust"]
---

# Prime Agent 拆解：上下文当变量、改进进状态，RLM 编程模型的落地样本

Prime Agent 押了两个主张：上下文管理不该靠摘要压缩，而该交给模型用 Python 代码自己解决（RLM，递归语言模型）；智能体的持续改进不该动权重，而该写进 harness 的持久状态（Continual Harness）。这两个主张都有论文背书，而 Prime Agent 是它们目前最完整的产品化实现——README、主论文 arXiv:2608.23552 和 Continual Harness 论文 arXiv:2605.09998 三处互相印证。想理解 RLM 这一范式从实验脚手架走向日常工具的过程，读它的源码比读论文具体得多。

这篇按 2026-10-01 的仓库实物（GitHub API 读数、`main` 分支浅克隆、安装脚本实测）拆解三件事：RLM 在产品里长什么样、Continual Harness 的改进机制实际怎么运转、以及 RLM 博客里那组消融数据能说明和不能说明什么。核到的写成事实，论文与源码对不上的地方单独指出。

## 目录

- [读仓库前先对齐三个口径](#读仓库前先对齐三个口径)
- [系统地图：Rust 外壳、Python 内核、12 个技能](#系统地图rust-外壳python-内核12-个技能)
- [RLM 范式：从 Alex Zhang 的提案到 Prime Intellect 的产品](#rlm-范式从-alex-zhang-的提案到-prime-intellect-的产品)
- [内核怎么工作：自研 REPL 与 rlm.spawn](#内核怎么工作自研-repl-与-rlmspawn)
- [Continual Harness：把改进写进四类状态](#continual-harness把改进写进四类状态)
- [一次长评测任务怎么流过系统](#一次长评测任务怎么流过系统)
- [daemon 与长任务三件套](#daemon-与长任务三件套)
- [RLM 到底帮不帮：博客消融数据怎么读](#rlm-到底帮不帮博客消融数据怎么读)
- [安全边界与成熟度](#安全边界与成熟度)
- [采用建议](#采用建议)

## 读仓库前先对齐三个口径

**第一，这是 Rust 项目，不是 TypeScript。** 仓库的 1,189 个 `.rs` 文件构成一个九个 crate 的工作区，Python 侧只有 49 个文件（运行时内核），TypeScript 只剩 1 个差分测试驱动。`AGENTS.md` 第一句就是 "Development rules for Prime Agent (Rust)"，并写明 TypeScript 实现如今是只读的行为基准（"parity ground truth"）：工程靠差分测试对照旧的 TS 二进制来保证重写没跑偏，`pa-daemon` 的 crate 文档里至今逐条标注每个机制对应的 TS 原函数名（如 `_checkCompaction`）。网上不少资料仍把它标成 TypeScript 项目——那是重写之前的旧状态。

**第二，发版节奏极快，稳定版和滚动测试版并行。** 仓库 2026-05-08 创建，到 2026-10-01 已发 64 个 release：stable 通道最新 v0.9.8（2026-09-29 发布），9 月就发了 v0.9.4 到 v0.9.8 五个稳定版；同时 `rust` 分支每次 push 都会发布一个新的 rolling beta（tag 已到 v0.9.9-beta.14，一天能出好几个）。安装脚本默认装 stable 通道，可用环境变量 `PRIME_AGENT_RELEASE_CHANNEL` 切换。GitHub 上 21,446 star、2,365 fork（2026-10-01 读数），MIT 许可。

**第三，README 就是文档。** 仓库里没有 `docs/` 目录；安装、上手、机制说明全在 README 里，更深的细节要去读 crate 级 README 和源码。本文的引用路径都可以按此核对。

## 系统地图：Rust 外壳、Python 内核、12 个技能

Prime Agent 的进程结构是"外壳跑在 Rust 里，模型写的代码跑在 Python 里"。九个 crate 按依赖方向单向组合（`pa-types` 是唯一共享 crate）：

| 组件 | 语言 | 职责 |
| --- | --- | --- |
| `pa-tui` / `pa-cli` | Rust | 终端界面与 `prime-agent` 二进制；会话切换、自动补全、agents 视图 |
| `pa-daemon` | Rust | 会话监督与后台服务；终端断开后会话继续跑，负责自动压缩（compaction）与 refine 调度 |
| `pa-agent` | Rust | agent 循环：驱动模型流、分发工具调用、执行轮次上限 |
| `pa-core` | Rust | 会话引擎：斜杠命令、cron 调度（心跳/定时）、内核管理 |
| `pa-ai` / `pa-models` | Rust | 模型接入层与在线模型目录 |
| `prime-agent-runtime` | Python | RLM 内核：持久 REPL、`rlm` 递归桥、harness 状态（仅依赖 `mcp` 和 `tyro` 两个包） |
| `skills/` | Python | 12 个内置技能：refine、agent-message、agent-observe、goal、compact、skill-creator 等 |

两个语言层的分工很清楚：Rust 侧管进程、传输和会话生命周期，Python 侧只做"模型的执行环境"——repl.py 自述是一个"说换行分隔 JSON 协议的 minimal CPython REPL"。模型在 REPL 里写代码，代码通过这层 JSON 协议向 Rust 宿主请求派生子代理、读写 harness 状态。

## RLM 范式：从 Alex Zhang 的提案到 Prime Intellect 的产品

RLM（Recursive Language Model，递归语言模型）是 Alex Zhang 在 2025 年 10 月以博客形式提出的，后成论文（arXiv:2512.24601）。核心两条：上下文当变量（prompt-as-a-variable）——庞大的输入数据不进上下文窗口，而是挂在 Python 变量上，模型用代码检索和变换它；递归子代理当函数调用（programmatic sub-agent calling）——模型在 REPL 里派生"新鲜的自己"去处理分片任务，结果以编程方式回收。Prime Intellect 在博客《Recursive Language Models: the paradigm of 2026》（2026-01，Sebastian Müller）里把 RLM 归入"上下文折叠"（context folding）谱系：与摘要压缩不同，RLM 从不摘要上下文，因此不产生摘要式信息损失——代价是模型得自己写代码决定看什么、跳过什么。

Prime Intellect 认为 RLM 是这个谱系里最简单、最灵活的一支，值得用强化学习直接训练。这段背景解释了 Prime Agent 的产品形态为什么长这样：它是"RLM 应当被训练"这一研究路线的工程配套——先让 RLM 脚手架在日常工具里跑起来、攒到真实使用模式，再喂给训练管线。

注意区分两套实现。博客里做消融的是 verifiers 里的实验版 RLMEnv：答案只能通过 `answer` 变量返回（`content` 写内容、`ready` 置真才结束），REPL 每轮输出截断 8192 字符，单次 REPL 调用限时 120 秒，跑在 Prime Sandboxes 微虚拟机里，递归深度固定为 1。Prime Agent 不是这套脚手架的直移——它有自己的内核 API、会话系统和 harness 状态（下两节），论文口径也不提 answer 变量。读博客数据时不能把实验版的设定直接套到产品头上。

还有一个三处口径不一致的细节值得单独记录：主论文摘要写 "a persistent IPython REPL"，README 只说 "a persistent Python REPL"，而当前源码是自研的 minimal CPython REPL（`prime-agent-runtime` 的依赖清单里没有 IPython）。以源码为准：产品现在跑的不是 IPython；论文措辞对应的是更早的实现。这种 README、论文、源码三方各说各话的情况，是读这个仓库时要保持的习惯。

## 内核怎么工作：自研 REPL 与 rlm.spawn

REPL 本身刻意做薄：每个代码单元（cell）支持 top-level await，跑在单一持久的 `__main__` 命名空间和单个 asyncio 事件循环里；会话变量可以快照持久化（默认上限 256 MB、单变量 16 MB，dill 序列化）。薄的 REPL 加厚的宿主协议，换来的是模型的一切动作都走代码：文件操作、shell 命令、MCP 工具、子代理、上下文管理，没有"内置工具"和"代码"的边界。

递归子代理是内核的一等原语，但 `rlm` 本身不可调用——源码里留着一条报错文案教正确用法：

```python
handle = await rlm.spawn('sub-task', name='worker')
result = await rlm.collect(handle)      # 回收子代理结果
children = await rlm.list_subagents()   # 花名册：状态、工具调用数、答案预览
```

`spawn` 返回句柄，`collect` 回收结果，`list_subagents` 给出可编程观察的子代理花名册——父代理不只是在"派活"，它能像检查函数返回值一样检查子代理；运行中的子代理也可以用 `rlm.progress_note` 向父会话报告进度。递归深度默认为 2（daemon 源码中的 `DEFAULT_RLM_MAX_DEPTH`），可用 `/rlm-max-depth` 命令查看和设置。这套 API 与实验版的 `llm_batch` 不同名也不同构，但设计意图一致：让"拆任务、派子代理、收结果"成为模型代码里的一等表达式。

## Continual Harness：把改进写进四类状态

Continual Harness 的思路是：智能体的改进不发生在权重里，而发生在一组持久化的补充状态里。状态分四类——补充提示（prompt）、记忆（memory）、技能描述（skill）、可复用子代理规格（subagent）——默认存会话本地，`global_=True` 时写跨会话的全局库。这条路线的源头是 Prime Intellect 的 Gemini Plays Pokemon 实验：靠迭代式的人工在环 harness 改进，GPP 成为第一个通关 Pokemon Blue 与 Yellow Legacy（硬模式）的 AI 系统，arXiv:2605.09998 把这套方法总结成了论文。

产品化之后的入口是 `/refine` 命令（内核侧对应 `await refine.run()`），它的精确语义比"自我改进"这个标签克制得多：

- refine 请求立即返回，实际分析排在当前轮次结束之后——不会在模型代码执行中途改状态；变更应用后 harness 会重建系统提示，再自动恢复会话。
- 每轮最多一个 refine 请求，重复调用只是更新指示；每次更新是小步的、要有证据支撑的，并记录历史、可回滚快照。
- 不可变的基线系统提示永远不会被重写。README 还特意补了一句：refine 沉淀的是提示、记忆和技能描述，不能替代对可执行技能本身的打包与审查。

配套的 `skills/` 目录把"技能"落成可导入的 Python 包（12 个内置：refine、agent-message、goal、compact、websearch、skill-creator 等），内置的 skill-creator 能把反复出现的工作流固化成项目级或个人级技能。也就是说，改进有三个落点，粒度从轻到重：一条记忆、一份提示补充、一个可执行技能包。

## 一次长评测任务怎么流过系统

用一个具体任务把上面的机制串起来：让 Prime Agent 跑一组需要联网检索的长周期评测。

1. 在评测目录启动 `prime-agent`，首次 `/login` 选订阅或 API-key 提供方；给目标后主会话把任务拆成子问题。
2. 模型在 REPL 里 `rlm.spawn` 派生若干子代理并行检索，每个子代理独立上下文，工具调用产生的海量网页 token 留在子代理里，不占主会话窗口——这正是 RLM "上下文当变量"的产品化收益。
3. `rlm.collect` 逐个回收结果，主会话交叉核对后写入评测记录；发现的复用模式（比如某个网站的解析套路）用 `/refine` 沉淀成记忆或技能描述，供后续会话复用。
4. 终端关掉，`pa-daemon` 继续跑；之后 `prime-agent attach <agent>` 重连，REPL 变量、子代理、调度全都还在。
5. 若任务需要长期驻守：`/goal` 挂一个跨轮次的目标，`/heartbeat`（默认每 5 分钟，Steer 模式投递）周期性唤醒会话，或用 `prime-agent schedule` 定时触发。

这个流程里没有哪一步是魔法：每一步都对应上文的一个组件，也都能在会话记录里查到对应的代码调用。

## daemon 与长任务三件套

README 把长任务能力归成一组特性，其中三个值得展开，因为它们的边界比功能列表更能说明设计取舍。

**自动压缩（compaction）是兜底，不是首选。** `pa-daemon` 里实现了三条压缩触发路径（上下文溢出重试、模型主动请求、阈值触发），超限时压缩上下文再重跑当轮。它的存在不改变 RLM 的主张——上下文管理主要靠模型写代码解决，压缩只是最后的安全网。

**持久目标（`/goal`）让任务跨轮次存活。** 目标和它的进度在会话里持续有效，直到完成、暂停或清除；daemon 侧有专门的 goal continuation 逻辑在轮次间续接。这解决的是"多轮对话里目标漂移"这个老问题，机制上是把目标从对话历史里拿出来单独持久化。

**自主模式（`/autonomous`）是有界的，且 README 明确警告了边界的含义：** 它只在配置的轮次、token、时间预算内继续运行，可以挂用户自定义的质量门（quality gates），但原文是 "A passed gate checks only what that gate verifies; reaching a limit does not imply task success"——门通过只说明门验证的那件事成立，预算耗尽也不代表任务成功。这句话值得所有做智能体自动化的人抄下来。

## RLM 到底帮不帮：博客消融数据怎么读

Prime Intellect 的博客用四个环境做了 RLM 与普通 LLM 的消融（GPT-5-mini 主测，GLM 4.6、GLM 4.5 Air、INTELLECT-3 参与，每格 50 个样本，不调超参、只看相对差异）。先说清测的是什么：verifiers 的实验版 RLMEnv，不是 Prime Agent 产品；测的是 RLM 脚手架对既有模型的即时增益，不是训练后的上限。数字要按这个口径读：

- **长上下文任务是 RLM 的主场。** Oolong real 子集（真实 D&D 对局记录的信息提取与聚合，约 150 万字符、30 万到 40 万 token）上，RLM 显著好于 LLM；再长，所有模型都失败。verbatim-copy（逐字复制）上 RLM 总体占优——各长度档位全面领先，仅 UUID 码这一内容类型落后，作者自己也怀疑那是 50 样本下的偶然。
- **反例同样有信息量。** math-python 上 RLM 反而更差——环境给的 Python 工具与 REPL 几乎等价，模型在标准脚手架上过拟合了基准，换上更复杂的 RLM 脚手架就掉分。DeepDive 上无提示的 RLM 也不如 LLM，给了策略提示（拆问题、并行派子代理）才反超。
- **增益高度依赖模型会不会用脚手架。** GLM 4.6 在 DeepDive 上 RLM 带来近一倍的提升，但同一个提示让它在另一个场景反而崩掉——被要求大量使用子 LLM 时它偏偏不用了。GPT-5-mini 是用得最好的。
- **子代理的主要收益是隔离 token，不是变聪明。** DeepDive 里网页内容的巨量 token 由子 LLM 消化，主模型上下文保持紧凑，主模型 token 效率显著提升——代价是总 token 和总耗时都明显增加。

从这些数字**不能**推出什么：不能推出 Prime Agent 产品在编码任务上有同等增益（博客测的是研究环境，非编码工作流）；不能推出某个模型的绝对水平（作者反复强调只比较相对表现）；也不能推出 RLM 已经优于摘要压缩路线（博客的立场是"训练后才会释放真正潜力"，并把"训练模型使用 RLM"列为未来工作）。Prime Agent 的 README 自己也没有给出任何编码基准数字——这个产品的说服力目前建立在机制设计和研究路线上，而不是跑分上。

## 安全边界与成熟度

README 的警告原文值得完整转述：Prime Agent 以你的用户权限执行模型生成的 Python 和项目命令；worker 与 kernel 进程改善了生命周期隔离和故障恢复，但**不是安全沙箱**。官方建议用一次性 clone、干净 worktree 或可检查可回滚的 checkpoint，只运行可信的仓库、指令、技能与扩展；不可信代码放进外部沙箱。

几个设计细节补全这张边界图。agent 间通信被限制在"直系家庭"内（skills/agent-message 的原话是 parent、siblings、direct children），发送者身份由 daemon 派生、不许伪造——智能体互联的范围被刻意收窄。refine 不可触碰基线系统提示且有快照回滚，自主模式有预算和质量门。这些约束共同指向一个立场：改进和互联都要在可审计的轨道上发生。

成熟度方面按仓库实物说话：活跃度没有问题（本文核查当天仍在提交，beta 一天数发），工程纪律在 `AGENTS.md` 里成文（crate 单一职责、循环依赖禁止、2000 行文件软上限、修复必须带回归测试）。但两点要如实告知：一是 Rust 重写仍在对照 TS 基准做差分验证，说明移植尚未完全收尾；二是 RLM 与 Continual Harness 都是 2025 年底才出现的范式，API 面临快速演进，`rlm.run` 更名为 `rlm.spawn` 就是已发生的一次。外部贡献门槛也高：PR 只接受维护者和经担保（vouched）的贡献者。

## 采用建议

- **长周期评测、研究自动化、需要并行子代理的工作流**：值得现在就试。这是 Prime Agent 设计的主要场景，daemon、心跳、目标、refine 的组合在同类工具里少见。
- **想跟进 RLM 范式的工程师**：把它当可运行的参考实现读——内核 API（`spawn`/`collect`/`list_subagents`）、harness 状态机、TUI 的 agents 视图，都是范式落地问题的现成答案。
- **要在生产里跑不可信代码的团队**：先等。没有沙箱这一点是官方明示的边界；要么自建隔离层，要么等生态成熟。
- **期待"开箱即胜过 Claude Code"的人**：降低预期。RLM 的增益证据来自研究环境且依赖模型会不会用脚手架，Prime Intellect 自己的判断也是"训练后才会释放潜力"。

上手只要两步：

```bash
curl -fsSL https://app.primeintellect.ai/prime-agent/install.sh | sh
cd /path/to/project && prime-agent
```

维护相关命令：`prime-agent status` 看后台服务，`doctor [--fix]` 检查修复，`update [--force]` 升级，`shutdown [--force]` 停掉全部代理与后台服务。

## 进一步阅读

- 仓库 README（即文档）：<https://github.com/PrimeIntellect-ai/prime-agent>
- 主论文《Prime Agent: A Self-Improving RLM Harness》（arXiv:2608.23552，2026-08-24 提交）：<https://arxiv.org/abs/2608.23552>
- 《Continual Harness: Online Adaptation for Self-Improving Foundation Agents》（arXiv:2605.09998，含 Gemini Plays Pokemon 起源）：<https://arxiv.org/abs/2605.09998>
- RLM 范式博客（Sebastian Müller，2026-01，含四环境消融）：<https://www.primeintellect.ai/blog/rlm>
- RLM 原始提案：Alex Zhang 的博客（2025-10）与论文 <https://arxiv.org/abs/2512.24601>
