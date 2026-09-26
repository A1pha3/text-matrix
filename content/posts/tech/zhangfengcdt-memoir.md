---
title: "Memoir：把 AI 记忆放进 git 仓库，能换来什么、换不来什么"
date: '2026-05-13T19:31:11+08:00'
lastmod: '2026-09-26T03:55:52+08:00'
slug: "memoir-ai-agent-git-versioned-memory"
github_repo: "zhangfengcdt/memoir"
source_key: "gh:zhangfengcdt/memoir"
description: "Memoir 把记忆库做成一个 git 仓库：每次写入一个提交，分支、回滚、溯源全部复用 git 语义。本文按 v0.2.5 逐层拆开存储、路径、合并、检索与加密证明，并给出本机实测数字与文档自述数字的差值。"
categories: ["技术笔记"]
tags: ["AI Agent", "开源", "Git", "记忆系统"]
toc: true
draft: false
---

> **判断先行**：Memoir 没有发明新的存储结构，也没有提出新的检索算法。它只做了一件事——把一个记忆库做成一个真的 git 仓库，于是分支、提交、回滚、溯源这些在代码上磨了二十年的语义，自动长在记忆上。这个选择换来的是可审计和可隔离；代价是每条记忆都要付一次提交的账，以及一整套围绕「路径」而不是「相似度」重建的检索习惯。
>
> 下面所有结论都来自 v0.2.5（提交 `b8b14fc`）在本机的运行与读取，取数时间 2026-09-26。文档里那些没法复现的数字，我会明确标成「文档自述」。

## 目录

- [Memoir 到底换了哪个变量](#memoir-到底换了哪个变量)
- [系统地图：三万行 Python 分在十四模块](#系统地图三万行-python-分在十四模块)
- [三个常被混成一谈的问题](#三个常被混成一谈的问题)
- [存储层：一个 git 仓库里的 prolly 树](#存储层一个-git-仓库里的-prolly-树)
- [版本层：每次写一个提交，账单是什么](#版本层每次写一个提交账单是什么)
- [路径层：四套分类数字和一个没被校验的入口](#路径层四套分类数字和一个没被校验的入口)
- [合并策略：同一入口，三种前缀，三种结果](#合并策略同一入口三种前缀三种结果)
- [检索层：四条路径和一次静默降级](#检索层四条路径和一次静默降级)
- [分支跟随代码分支：一个不显眼的关键设计](#分支跟随代码分支一个不显眼的关键设计)
- [加密证明：它到底证明了什么](#加密证明它到底证明了什么)
- [一次任务怎么流过 Memoir](#一次任务怎么流过-memoir)
- [宿主入口：五种插件加三种编程入口](#宿主入口五种插件加三种编程入口)
- [性能：文档说了什么，本机量到了什么](#性能文档说了什么本机量到了什么)
- [按现象分类的排查](#按现象分类的排查)
- [采用顺序与不必用的场景](#采用顺序与不必用的场景)
- [五道自测题](#五道自测题)
- [下一步读哪份代码](#下一步读哪份代码)
- [参考](#参考)

## Memoir 到底换了哪个变量

绝大多数智能体（agent）记忆方案的默认变量是「相似度」：把内容切成片段、算向量、按余弦距离取回 top-k。Memoir 把默认变量换成「位置」——每条记忆必须先落进一条分层路径，比如 `profile.professional.occupation`，取回时按路径直达。

这一个替换带来三处连锁变化，也仅此三处：

1. **可定位**。知道一条记忆存在哪，就能只读它、只删它、只把它单独给某个分支看。向量库里这些操作都要先做一次全库扫描。
2. **可归因**。既然位置固定，写入动作就能排队成历史；`memoir blame` 报出这条记忆是哪一次提交、由谁（其实是一个固定的提交者身份）在什么时候改的。
3. **可分叉**。位置稳定之后，把整个记忆状态复制到另一条时间线才有意义，分支隔离才成立。

它没有解决的是「记不记得住」。分类这一步由大语言模型（LLM）完成，路径判断错了，后面所有精确读取都会精确地读错东西——「检索层」一节会给出这种失败在本机的实际样子。

## 系统地图：三万行 Python 分在十四模块

`src/memoir/` 下 95 个 Python 文件、31,981 行。行数分布本身就在说话：真正的「记忆内核」很薄，厚的部分是给人和给宿主看的界面。

| 模块 | 行数 | 职责 |
|------|------|------|
| `ui` | 7,865 | Web 界面与它的 HTTP 接口层 |
| `services` | 5,770 | 业务层：写入、分支、合并策略、加密、索引 |
| `cli`（命令行工具） | 3,519 | 24 个子命令 |
| `taxonomy` | 3,430 | 分类体系加载、动态扩展 |
| `classifier` | 2,900 | 两个分类器与置信度门控 |
| `tui` | 1,409 | 终端界面，基于 textual |
| `store` | 1,165 | prolly 树适配、git 加固 |
| `integration` | 1,163 | LangGraph 存取接口 |
| `memento` | 1,111 | 画像、时间线、地点三类容器 |
| `search` | 993 | 选路径与取回 |
| `llm` | 871 | 模型调用与提示封装 |
| `core` | 707 | LangMem 兼容的管理器（可选依赖） |
| `mcp` | 595 | MCP 服务端，9 个工具 |
| `sdk` | 435 | 软件开发包，供程序内调用 |

一条外部依赖值得单独记：真正的树形存储在另一个仓库，`zhangfengcdt/prollytree`，PyPI 包名 `prollytree`，Rust 内核加 Python 绑定，Memoir 要求 `>=0.4.0`，本机装到的是 0.4.1。也就是说 Memoir 本体是一个**编排层**：它管路径、管冲突、管宿主集成，不管 B 树怎么分裂。

其余直接依赖只有四个：`langgraph`、`pydantic`、`click`、`litellm`。

## 三个常被混成一谈的问题

读 Memoir 的代码前，先把三件事分开，否则后面每一节都会串味：

| 问题 | 谁负责 | 失败时看见什么 |
|------|--------|----------------|
| 内容存在哪、怎么复制成多份历史 | prollytree + git | 提交数、`.git` 体积、回滚不出来 |
| 一条内容该落在哪条路径 | 分类层（LLM） | 读得很快，但读到不相干的东西 |
| 同一条路径上来了新内容怎么办 | 合并策略（按前缀定类型） | 旧记忆「消失」，其实是后来者覆盖了 |

第二和第三是 Memoir 自己写的，第一是它的作者另一个仓库写的。这三层各自都可替换，这也是它架构文档里那句「依赖注入」的实际含义——不是修辞。

## 存储层：一个 git 仓库里的 prolly 树

`memoir new ./store1` 之后，磁盘上是什么：

```text
store1/
├── .git/                    # 真 git 仓库，不是仿制品
│   ├── memoir-backend       # 后端标记
│   ├── prolly/nodes/        # 文件后端的内容块
│   └── ...
├── data/
│   └── prolly_config_tree_config
└── ...
```

`git init` 是 `ui/initializer.py:165` 直接调的，作者身份固定为 `git-prolly <git-prolly@example.com>`，提交信息形如 `Store preferences.coding.languages in default`。也就是说 `git log`、`git diff`、`git gc` 这些外部工具对 Memoir 的库全部有效——这既是它的省事之处，也是下面那个风险的来源。

打开 `data/prolly_config_tree_config`，能读到分块参数：底数 257、模数 1000000007、最小块 8 字节、最大块 4096 字节、边界掩码 255，根哈希 32 字节。prollytree 的包内文档把自己的定义写得很直白：B 树与 Merkle 树的混合结构，靠内容定义分块得到可验证的完整性。PyPI 上那句短描述用的是 probabilistic tree——只差一个词，很容易读成「概率性再平衡的 B 树」，那是另一种东西。

**一个必须知道的运维细节**：prollytree 的 git 后端把树节点存成悬空对象（dangling blob）——它们在 `.git/objects/` 里，但没有任何分支或标签可达。git 默认的垃圾回收有权删掉悬空对象。Memoir 的做法是在每个库上强制写下两条配置（`store/git_safety.py`），创建时写一次、每次打开再补一次，所以旧库也会在新版本第一次打开时被补上：

```text
gc.auto = 0
gc.pruneExpire = never
```

`memoir new --backend` 现在默认是 `file`，`git` 后端留给需要工具链兼容的场合。两者的差别就在对象可达性：文件后端把块写在 `.git/objects/` 之外（实测落在 `.git/prolly/nodes`），一条手动的 `git gc --prune=now` 也伤不到它；git 后端只挡得住自动触发的那类回收。这是本项目写在源码注释里的口径，不是我的推测。

## 版本层：每次写一个提交，账单是什么

把「每次写入=一个提交」当真之后，就必须回答历史到底多重。我在一台 Apple 芯片的 macOS 机器上做了两组独立测量（Python 3.12，本地 NVMe，走进程内存储接口，即绕开解释器启动与命令行解析），下面给的是两次结果的区间：

- 8 条不同路径上连续写 1,000 次，得到 1,001 个 git 提交（含初始提交），`.git` 目录 20.1 MB 上下（两次分别 20,124 KB 与 20,136 KB），4,004 个松散对象，`.git/prolly/nodes` 下的块文件 1,003 与 1,006 个——一次写入对应一个块。
- 与此同时 `data/prolly_config_tree_config` 始终是 475 字节：它只存配置和根哈希，正文都在块与对象里。
- 单次写入（含落块与提交）中位数 56–65 ms，95 分位最高 79 ms，单次最大 167 ms。从第 200 次写到第 1,000 次没有明显恶化（两次跑的前 200 / 后 800 中位数分别是 56.3 与 62.2、60.6 与 65.5 ms）。
- 按路径直读一条聚合记录，中位数 9.1 µs 与 14.2 µs，最大 67.5 µs。这个数量级下，架构文档写的「0.1-1ms」反而偏保守。
- 同一个读取走命令行（`memoir --json get`），自报耗时稳定在 18–23 ms；`memoir remember` 端到端平均 321.5 ms/条。差额几乎全在解释器启动、依赖导入和开库上，单独测一次打开存储约 59.4 ms。

结论是：**历史成本约等于每条记忆 20 KB**，而**命令行调用的成本里，真正的存储只占不到两成**。评估 Memoir 是否适合高写入场景时，用前者；评估插件里那些钩子会不会拖慢会话时，用后者。

## 路径层：四套分类数字和一个没被校验的入口

「预定义了约 200 个路径」这句话在项目里能找到四个不同的对应物，而且它们互不相等。逐个数过之后是这样：

| 来源 | 条数 | 顶层类目 | 实际用在哪 |
|------|------|----------|------------|
| `taxonomy/data/general/presets.md` | 275 条路径 | 17 个 | `memoir new --taxonomy-builtin` 装进库里，分类器与检索按这份走 |
| 同目录 `examples.md` | 207 条例句，覆盖 201 条不同路径 | — | 提示词里的少样本示例 |
| `taxonomy/semantic.py` 的内置体系 | 64 条路径 | 8 个 | 内部只被 `SemanticClassifier` 读取 |
| `taxonomy/taxonomy.py` 的兜底常量 | 38 条路径 + 16 条例句 | 8 个 | 库没加载分类体系时的降级数据 |

三处对不上，而且都是可复算的：

- `presets.md` 自己的头部写着「~200 paths」，实际列出 275 条；`memoir new --help` 说内置分类体系「~215 examples」，实际 207 条。
- 架构文档里画的那棵树——`profile.identity.name.{first,last,full}`、`personal.interests.{hobbies,sports}`——在这四份清单里一条都找不到。真实的顶层类目是 `context`、`workflow`、`preferences`、`knowledge`、`debugging`、`project`、`experience`、`entity`、`settings`、`system`、`routine`、`communication`、`profile`、`goals`、`topics`、`learning`、`relationships`，全部三层深。
- `TaxonomyVersion` 声明了 `GENERAL` 和 `SIMPLIFIED` 两档，`TaxonomyPresets.PRESETS` 里只有 `SIMPLIFIED`。而 `IntelligentClassifier` 的默认参数写的是 `GENERAL`——查不到就静默退回 `SIMPLIFIED`，不会报错。

还有一个更要紧的：**显式路径入口不做任何校验**。

```bash
memoir remember "x" -p preferences.coding.style   # 存下了，返回提交号
```

`preferences.coding.style` 不在上面任何一份清单里，而它恰好出现在 `memoir remember --help` 的示例中——同一条帮助里的 `preferences.tooling.terminal` 也不在，主帮助里那句 `user.preferences.theme` 同样对不上。这条命令的语义是「跳过分类器直接落盘」，既然跳过了分类，也就跳过了唯一可能拦住错路径的那道检查。想要路径拼写保证，只能自己在外面套一层校验。

## 合并策略：同一入口，三种前缀，三种结果

架构文档里「记忆聚合」的说法很容易让人以为：同一路径下会攒出一个列表。真实行为由路径前缀决定，规则写在 `services/merge_policy.py`。

记忆被归成四型，每型一个默认冲突策略：

```text
context.current   -> WORKING     -> replace
metrics.turn      -> WORKING     -> replace
metrics.code      -> EPISODIC    -> append
experience        -> EPISODIC    -> append
workflow          -> PROCEDURAL  -> llm_merge
behavior          -> PROCEDURAL  -> llm_merge
其余一切           -> SEMANTIC    -> confidence_gated
```

可选策略一共六个：`append`、`replace`、`confidence_gated`、`llm_merge`、`merge_on_read`、`reject`，用 `--merge-policy`（合并策略）或环境变量 `MEMOIR_MERGE_POLICY` 指定，`--replace` 是别名。

于是同一个动作、同一个路径、连写三条，结果分三种。本机实测：

| 写入路径 | 连写 3 条后 `get` 看到什么 |
|----------|-----------------------------|
| `experience.work.projects` | 3 条目全在，投影文本用 `[update]` 前缀串起来 |
| `preferences.work.environment` | 只剩最后 1 条 |
| `workflow.testing.unit` | 只剩最后 1 条 |

第二行不是 bug，是 `confidence_gated` 的定义：新来者置信度 **大于等于** 现存量最高值就整条替换。而用 `-p` 显式落盘时，置信度被固定写成 1.00，于是同路径的后续写入必然满足条件——覆盖。这条语义连项目自己都承认：Claude Code 钩子里维护代码改动日志的那段注释写着「`memoir remember` 按路径是替换，所以追加由钩子自己做」，它因此在钩子层实现了读—合并—写，并给条目数设了上限（`MEMOIR_METRICS_CODE_MAX`，默认 1000）。落盘的条目本身是有版本的容器（`schema_version: 2`，内含 `entries` 列表、每条带 `status: active` 与 `related_keys`），聚合的形状一直在，只是默认策略不给攒。

想把偏好攒起来，写的时候就得点名 `--merge-policy append`，或者让置信度真的参与进来（走分类器那条路会带模型给出的置信度）。旧值并没有丢，它们在 git 历史里，`memoir blame` 看得见。

## 检索层：四条路径和一次静默降级

Memoir 有四种取回方式，能力和前提完全不同。放在一起看最容易建立正确预期：

| 入口 | 要不要模型 | 覆盖范围 | 排序依据 |
|------|-----------|----------|----------|
| `memoir get` 按路径直取 | 不要 | 单个精确路径 | 无 |
| `memoir recall` 收自然语言 | 要 | 全库按路径取回 | 模型先选路径 |
| `memoir search` 向量检索 | 要（本地小模型） | 只有 `watch` 建过索引的内容 | 向量距离，越小越近 |
| MCP 的词面模式 | 不要 | 枚举键后逐条打分 | 关键词 |

`recall` 有两种模式，`single`（默认，一次模型调用选路径）与 `tiered`（逐级下钻：先类目再子级再精确键）。模型解析顺序是 `--model` 参数、环境变量 `MEMOIR_LLM_MODEL`、默认值 `claude-haiku-4-5`。后端选择比想象灵活：设 `MEMOIR_LLM_BACKEND=claude-cli` 会去 shell 调用 `claude -p`；用 Claude 系模型、没有 `ANTHROPIC_API_KEY`、但 `claude` 在 PATH 上时，也会自动落到这条 CLI 通道；其余情况走 `litellm` 直连服务商。

`search` 有个容易踩的边界，命令行帮助自己写明了：向量索引由 `memoir watch` 建立，`memoir remember` 写入的内容**不进这个索引**，所以在这里查不到。`watch` 只收单文件、拒绝目录，解析靠可选 extra `markitdown`，嵌入模型默认是 MiniLM，首次运行要下载约 90 MB 权重到本地缓存目录（`~/.cache/prollytree/embedders`）；因为 prollytree 会把嵌入器的标识与版本记在索引上、换嵌入器就拒绝再打开，实现里是一个命名空间一套索引，测试时才换成 `HashEmbedder` 跳过下载。

**静默降级**是这里最值得记住的一条。我在一台没有可用模型凭证的机器上跑：

```text
Error in LLM path selection: claude CLI exited 1:
[1] context.project.stack
    password=supersecretvalue123
[2] preferences.coding.style
    x
[3] preferences.coding.languages
    Sarah prefers tabs over spaces

Found 3 memories in 1375.4ms
```

出处是 `search/intelligent.py:866-869`：选路径的模型调用抛异常时，它记一条日志，然后返回已发现路径集合的**前 3 个**。用 `--json` 看更清楚——`success: true`，三条结果的 `relevance_score` 全是 `1.0`。也就是说模型不可用时 `recall` 不会失败，它会交回一份看起来相关的东西。JSON 里没有任何字段标记这次降级，能依赖的信号只有 stderr 上那行 `Error in LLM path selection`。生产里如果只读 `--json` 的 `success` 字段做判断，这条一定要额外防。

## 分支跟随代码分支：一个不显眼的关键设计

「上下文污染」这个卖点，光有 `memoir branch` 是不够的：人在终端里 `git checkout feature/b`，智能体进程毫无感知。Memoir 的答案是把「记忆分支=代码分支」做成一个需要在每个入口重新确认的不变式。

机制分两半：

1. 库的位置。插件用 `scripts/derive-store-path.sh` 按项目根算出 `~/.memoir/<slug>`，规则是把绝对路径里的 `/` 和 `.` 换成 `-`，和 Claude Code 自己给项目命名的方式对齐；linked worktree 会折叠到主 worktree，于是同一仓库的多个工作树共用一个记忆库。按项目分库而不是一个大库开命名空间，源码注释里给的理由是「共享库会把历史搅在一起」。
2. 分支的对齐。`common.sh` 里的 `auto_match_memoir_branch` 会在当前代码分支和记忆分支不一致时，从 `main` 建出缺失的分支并切过去。它被挂在 `SessionStart`、`UserPromptSubmit`、`Stop` 三处——注释写得很实在：只在会话开始时对齐一次不够，用户中途在终端切了分支，本次会话后面的捕获就会写错地方；每次提问都跑一次，两分支一致时它是个快速空操作。

不想被自动改分支就 `memoir branch-match off`（还有 `on` 与 `status`），这是库级开关；手工 `checkout` 一次则会留下一个一次性的粘滞选择。整个开关逻辑都在命令行里，宿主无关。

命令行侧还支持**不改检出分支的按次路由**：`remember`、`recall`、`get`、`forget`、`search` 都收 `--branch`（环境变量 `MEMOIR_BRANCH`），`remember --branch` 遇到不存在的分支会从当前提交自动建出来。多智能体并行读写同一个库、各走各的分支，靠的是这个，而不是界面里那段被注释掉的多会话演示。

合并语义有两条，别混淆：`memoir merge` 把源分支并进当前或 `--into` 指定的分支，冲突策略是 `ours`/`theirs`/`skip`，默认 `skip`（最保守）；`memoir sync-branch` 只把源分支 `default` 命名空间下的条目逐条以插入或更新方式应用到目标分支，明确不删任何东西、跳过系统命名空间，且不加 `--yes` 就拒绝落盘。要预演，先看 `--dry-run`。

## 加密证明：它到底证明了什么

`memoir proof <key>` 生成 89 字节的证明（base64 后 120 字符），`memoir verify` 校验。命令行会把证明截断显示（结尾三个点），要拿到完整内容必须加 `-o 文件`。

我在本机做了五组对照，结论比宣传语朴素得多：

| 实验 | 结果 |
|------|------|
| 证明原样校验 | `✓ Proof is VALID` |
| 证明中间某字节翻转 1 位 | `⚠ Proof is INVALID` |
| 用同一库另一个键生成的证明来校验本键 | `✓ Proof is VALID` |
| 用另一个库生成的证明 | `⚠ Proof is INVALID` |
| 写入新记忆后，用写入前的证明 | `⚠ Proof is INVALID` |

第三行是关键：同一库中三个不同键生成的 89 字节证明**逐字节相同**。`crypto_service.py` 确实把键传给了 prollytree 的校验接口，但从结果看，这份证明表达的是「某个库的某个状态」这一层的事实，不构成「这一条键」的绑定。它更像一次库状态的快照见证，能被用来证明「这批记忆当时是这个样子」，不能被用来单独证明「这一条没被改过」。

另一个可复现的小坑：证明判定为 INVALID 时，进程退出码仍然是 0。用脚本包这段校验的人，只能去解析文本或者读 `--json` 结果，不能靠 `$?`。

至于「SHA-256 保证历史不可篡改」这类说法，需要还原到它准确的形式：历史不可篡改来自 git 的对象哈希与链式引用，内容寻址来自 prollytree 的 Merkle 根；哈希在 Memoir 自己的代码里出现的三处是键名摘要、分类器缓存指纹和文件索引指纹，都不是「签名」。

## 一次任务怎么流过 Memoir

把前面几层串起来。场景：一个 Claude Code 会话在 `feature/report` 上干活。

1. 会话开始，`SessionStart` 钩子（超时 15 秒）先确保库存在（不在就创建），发现是新建库时顺手吸收 `~/.memoir/taxonomy/*.md` 与项目根 `.memoir/taxonomy/*.md` 里的自定义分类文件，然后跑 `auto_match_memoir_branch`，于是 `feature/report` 这条记忆分支从 `main` 建出并切过去。状态行显示 `[memoir] feature/report`，条数会把 `taxonomy:v1:*`、`codebase:onboard` 这些脚手架命名空间扣掉再报。
2. 用户每提一次问，`UserPromptSubmit`（10 秒）再对齐一次分支，并提示「有历史记忆可查」。真正的检索是拉式的：`memory-recall` 技能按需触发，读哪几条路径由模型决定。
3. 回合结束，`Stop` 钩子（180 秒、异步）读转录，一次调用抽出「值得长期记的事实」，逐条以显式路径落盘——每条一个 git 提交。同一个钩子还各自独立地维护两条附属记录：按分支累计的回合指标（键形如 `metrics.turn.<branch>`），以及按分支的代码改动日志（`metrics.code.<branch>`，检测本轮有没有文件编辑类工具调用，有就让模型写一行摘要）。三个开关互相独立：`MEMOIR_NO_CAPTURE`、`MEMOIR_NO_METRICS`、`MEMOIR_NO_CODE_SUMMARY`，任何一条路径失败都不影响另外两条；钩子自己调用模型时还会把这三个开关全部置起，避免嵌套触发。它另外会先看 `stop_hook_active`，防止自己的停止动作把自己再唤起一次。
4. 切回 `main` 修线上问题。因为记忆分支跟着代码分支走，`feature/report` 上攒下的实验性约定此刻不在视野里——`memoir get` 直接报 not found，我在本机验证过这个隔离是成立的。
5. 想收编这些约定，跑 `memoir sync-branch feature/report --dry-run` 看清差异，再 `--yes` 应用；`sync-branch` 只做插入和更新，不会把 `main` 上多出来的条目删掉。
6. 事后审计用 `memoir blame <key>`，输出是一条条 git 提交摘要，作者字段都是 `git-prolly`，所以「谁教的」在这里能追到的是**哪一次、什么时候**，而不是哪个人——除非你在钩子里自己写入来源。

## 宿主入口：五种插件加三种编程入口

仓库 `plugins/` 下有三套官方集成，README 还列了两个社区插件；再加上 MCP 服务端、两个界面和 Python SDK，Memoir 的入口比它的内核分散得多，成熟度也不同步：

| 入口 | 位置与版本 | 组成 |
|------|------------|------|
| Claude Code 插件 | 仓库内，0.3.0 | 4 个事件钩子（含 `SessionEnd`）、6 条斜杠命令、2 个技能 |
| Codex 插件 | 仓库内，0.1.0 | 3 个事件钩子、5 个技能（`memory-recall`、`memoir-onboard`、`memoir-remember`、`memoir-status`、`memoir-ui`） |
| Hermes 插件 | 仓库内，0.1.0 | 子进程桥接、声明零 Python 依赖，暴露 5 个工具 |
| OpenClaw 插件 | 独立仓库 `zhangfengcdt/openclaw-memoir` | 占住记忆槽位，注册工具、提示段、钩子与命令 |
| OpenCode 插件 | 独立仓库 `disafronov/opencode-memoir` | 社区维护 |
| MCP 服务端 | `memoir-mcp` | 9 个工具，检索默认走无模型的词面模式 |
| Web 与终端界面 | 随主包 | 7 个视图，其中 4 个进标签栏 |
| Python SDK | `memoir.sdk` | `MemoryClient`，同步与异步两套 |

Hermes 和 OpenClaw 这两条路线值得注意：两者都不把 Memoir 的 Python 代码装进宿主进程，而是用一个零依赖的子进程桥去调命令行——Hermes 的插件清单里干脆不写 Python 依赖。README 还针对 Hermes 点明：捕获与分类跑在宿主选定的模型和服务商接口上，不走 `claude` 那条 CLI 通道。把 Memoir 接进非编码型助手时，模型这一层是被宿主接管的。

社区插件那两条链接的可用性不对等：`disafronov/opencode-memoir` 打得开（它同时也是 `zhangfengcdt/opencode-memoir` 的上游），而 README 与 `docs/openclaw.md` 指向的 `zhangfengcdt/openclaw-memoir` 在 2026-09-26 取不到，GitHub 的仓库查询接口回 404。这意味着 `docs/openclaw.md` 里那条 `openclaw plugins install https://github.com/zhangfengcdt/openclaw-memoir` 现在按原文执行不了；同一份文档还让人用 `memoir log` 查历史，而这个子命令在 v0.2.5 里并不存在（跑起来直接报 `No such command`）。

三件容易记错的事：Claude Code 的钩子是 4 个而不是 3 个（README 只列了会话开始、用户提问、回合停止三处，`SessionEnd` 是第四处，异步、5 秒）；Codex 侧不仅要在 `~/.codex/config.toml` 打开 `[features].hooks = true`（旧名 `codex_hooks` 在 Codex v0.129.0 已告废弃），还要额外一步——Codex v0.130.0 会从插件市场装技能，但不会激活插件自带的 `hooks/hooks.json`（上游 openai/codex#16430），所以 Memoir 附了 `install-codex-hooks.sh`，把等价的三个钩子写进 `~/.codex/hooks.json`，`uninstall` 可撤；Web 界面默认可写、模型能力默认关闭，要 `--readonly` 才锁、要 `--usellm` 才开。

命令行解析有一条降级链，所以「只装了 `uv`」也算满足前提：先找 PATH 上的 `memoir`，没有就用 `uvx --from memoir-ai==0.2.5 memoir`，再退到 `uv tool run`。那个 0.2.5 是硬编码在 `resolve-memoir-cli.sh` 里的钉版。

还有一处安全边界值得单独提醒。识别凭据的正则有七条（OpenAI/Stripe 前缀、AWS 访问键、GitHub 令牌、Slack 令牌、PEM 私钥、连续 13–16 位数字、`password=` 这类带标签的写法），同一份列表复制在两处：`mcp/server.py` 与 `plugins/hermes/__init__.py`，命中就拒绝写入。也就是说这道守卫在**宿主适配层**，而不在存储层。命令行这一侧只给建议不给拦——`memoir remember --help` 的例子是让你自己把这类内容改投一个名为 `secrets` 的命名空间。我拿同一串内容直接走命令行，它照单全收：

```bash
memoir remember "password=supersecretvalue123" -p context.project.stack   # 已存下
```

Claude Code 与 Codex 两套钩子里也没有对应的过滤。记忆是版本化的明文，这个事实不会因为没有界面而改变。

## 性能：文档说了什么，本机量到了什么

架构文档第 189 到 197 行有一张表：语义搜索 0.1–1 ms、智能搜索 100–500 ms、传统向量搜索 150–750 ms、分类 1–5 ms（模式）/100–500 ms（模型）、存储 20–30 ms、版本控制操作 50–100 ms。同节还写着「记忆数量已测到 100 万条」「路径深度可到 8 层」「并发用户：水平扩展就绪」。仓库里另有一个 `benchmarks/` 目录，装的是脚本（`classifier.py` 需要服务商密钥、`locomo/` 是长对话记忆基准的适配器）和测试数据，没有随仓库发布的测量结果。

这三件事必须分开说：

1. **测的是什么**。表里「存储 20–30 ms」和「版本控制 50–100 ms」在实现里是同一次调用完成的，把它们相加来估算一次写入是错的。我量到的单次写入（含落块与提交）中位数 56–65 ms，落在两行之和的区间里，但它是一个数，不是两个数之和。
2. **数字反映哪一层**。文档里 0.1–1 ms 那行写的是「语义搜索」，若指的就是按路径直读，那本机 9 µs 量级比它写得更宽；一旦走命令行，18–23 ms 里大头是启动和开库，不是查找。真正取决于模型的是「选哪条路径」，那一行的实际值随服务商、网络、上下文长度浮动，任何固定数字都不该被当承诺引用。
3. **不能推出什么**。100 万条、8 层深、水平就绪这三句，在我能触到的材料里没有对应证据：随仓库分发的分类体系恰好全是三层，没有任何一条路径深过 3；`benchmarks/` 里也没有产出可复算的规模数据。把它们读成设计目标可以，读成已验证结论不行。

同一份文档里另一处对不上的是分类器。它把 `SemanticClassifier` 描述成「模式匹配，1–5 ms，不调模型」，把写入路径描述成「模式匹配 → 模型 → 扩展」的三段流水线。实际调用关系是反的：`services/memory_service.py` 的写入路径用的是 `IntelligentClassifier`；`SemanticClassifier` 在 `src/` 里唯一的实例化点在 Web 界面的一个异常分支里，注释写的是「模型分类失败时退回模式匹配」。它连自己的构造参数都收一个可选的模型对象。也就是说：模型优先、模式兜底、而且兜底只在一条界面路径上生效。

## 按现象分类的排查

按现象归类。前面两类最常见：读回空结果、读到不相干的结果，而这两类往往都不是存储层的问题。

**读回空结果，但状态显示有记忆。** 先看分支。`memoir status` 会报当前分支与提交数；如果代码切了分支而宿主没触发对齐，你正在读的是另一条时间线。手工 `memoir checkout <branch>` 或 `memoir branch-match on`。

**结果不相干，却给了高相关度。** 这是模型层失败后的降级形态（`search/intelligent.py:866-869`）。先确认 `ANTHROPIC_API_KEY` 或 `claude` 是否真的可用，再看 stderr 有没有那行 `Error in LLM path selection`——返回体本身不会告诉你它降级了。必要时改用 `memoir get` 按路径直取。

**同一路径的旧记忆不见了。** 前缀决定默认冲突策略：语义型走 `confidence_gated`，等置信度即覆盖。显式 `-p` 写入的置信度恒为 1.00，所以必覆盖。要攒就点名 `--merge-policy append`；要找回，`memoir blame <key>` 列出这个键上的提交，再 `memoir time-travel <sha> -b probe` 从那次提交开一条分支去读——实测它会建分支并切过去，读完记得 `memoir checkout main`。别指望 `git log -p data/`：那里只有配置和根哈希，正文在块文件与 git 对象里。

**`memoir search` 一条也搜不到。** 它只覆盖 `watch` 建过索引的内容，`remember` 写的不算。`memoir watch list` 看注册了什么、`watch scan` 重扫；首次运行要有下载约 90 MB 权重的心理准备。换过嵌入器会因索引上记录的版本不符而拒绝打开，这是设计而非故障。

**记忆数据莫名丢失。** 怀疑垃圾回收。检查 `git config --get gc.auto` 与 `gc.pruneExpire`，新版本会在打开时补写；如果你用的是 git 后端又手动跑过 `git gc --prune=now`，配置挡不住，这时只能靠另一份克隆或备份。新项目建议直接用默认的文件后端。

**脚本判不出校验失败。** 证明 INVALID 时退出码为 0，必须读输出内容。

**命令行参数没生效。** 全局选项要放在子命令之前，`memoir --json get x` 对，`memoir get x --json` 会报无此选项；`-q`、`-s` 同理。

## 采用顺序与不必用的场景

如果要上，建议按这个顺序，每一步都能单独验收：

1. 只用命令行，不接宿主。`uv tool install memoir-ai`，`memoir new ./demo`（默认文件后端），写几条显式路径的记忆，用 `memoir get` 读回。验收标准是你对「按路径取回」这件事的速度和形状建立直觉。
2. 单独看版本。`memoir status` 的提交数、`memoir blame`、`memoir diff`、`memoir time-travel <sha> -b probe`。确认你愿意接受每条记忆一次提交的账。
3. 接一个宿主。Claude Code 里两条命令：`/plugin marketplace add zhangfengcdt/memoir` 与 `/plugin install memoir@memoir`，钩子从下一次会话开始生效。Codex 侧照上一节说的手动装钩子。只看两件事：一次会话结束后落了多少提交、状态行显示的分支是否等于代码分支。
4. 再谈检索质量。`memoir recall` 起不来就先退回 `memoir get` 和 MCP 的 `lexical`；要开 `tiered` 之前先确认一次会话愿意为选路径付几次模型调用。
5. 最后才用 `watch`/`search` 与 LangGraph 集成（`ProllyTreeStore` 实现的是 LangGraph 的 `BaseStore` 接口；`ProllyTreeMemoryStoreManager` 需要 `[langmem]` 这个 extra）。

不必用的场景也写清楚：

- **高召回的开放式语义问答**。这里的检索前提是「先猜对路径」，路径猜错就整块漏掉，向量库在这类任务上仍占优。
- **需要多租户或权限边界的托管服务**。记忆库是磁盘上的一个 git 仓库，隔离粒度是库和命名空间，没有租户级加密。
- **把加密证明当合规证据**。加密证明一节的五组对照说明它证明的是库状态，不是单条记录。
- **对写入放大敏感的嵌入式或长会话场景**。约 20 KB/条的历史成本，是仓库体积而不是运行内存的问题，但会累积。
- **想要零外部依赖**。默认依赖里有 `litellm` 和 `langgraph`；`search` 另需 `markitdown` 与本地权重。

一个诚实的成熟度定位：包分类器和 README 徽章都写着 Alpha；611 星、181 次提交、6 位贡献者（作者本人占 175 次）、最近一次发布是 2026-09-08 的 v0.2.5。行为层面的改动仍在发生——`--backend` 的默认值到 v0.2.1（2026-05-26，PR #122）才从 git 切到文件后端，条目容器的 `schema_version` 已经走到 2 并且带一个 v1→v2 的升级函数，冲突策略的代码注释里还留着「旧口径」与「Phase-3 目标默认值」两套语义。把它当一份「记忆如何做成版本化存储」的参考实现来读，比当基础设施依赖更划算。

## 五道自测题

1. 同样三条内容写进 `experience.*` 与 `preferences.*`，为什么一次留下 3 条目、一次只留下 1 条？
2. 一次 `memoir remember` 的耗时里，存储、提交和命令行启动各占什么量级？为什么这决定了插件钩子该怎么写？
3. `memoir recall` 在模型不可用时为什么仍然返回 `success: true`？集成方要靠自己加什么才能把这种降级拦住？
4. `memoir proof` 生成的证明能证明到哪一层，不能证明到哪一层？
5. 用户中途在终端 `git checkout`，Memoir 靠什么把记忆分支拉回来？为什么这个动作要挂在三个不同的时机上？

## 下一步读哪份代码

想弄清「路径即索引」到底怎么落到磁盘：`store/prolly_adapter.py`（845 行的适配器，构造时的两条库校验很能说明设计取舍）和 `services/store_service.py` 里对 git 的封装。

想弄清分类与冲突：`services/merge_policy.py` 一共 353 行，前缀规则、六策略和条目投影都在一处，是全文性价比最高的一份。

想弄清宿主集成：`plugins/claude-code/hooks/common.sh`（1,124 行）里是 `auto_match_memoir_branch`，存储路径怎么算则委托给同目录上一层的 `scripts/derive-store-path.sh`，两个文件都要读。

想弄清「为什么不是向量库」：`docs/theory/related-work.md` 把 MemGPT、A-MEM、Mem0、CoALA 和 IPFS 各自对应到 Memoir 的哪个部件，末尾还专门留了一节 Notable Gaps，点出自己哪两处设计走在公开文献前面。这份自我定位比任何一张对比表都老实。

## 参考

- 仓库：<https://github.com/zhangfengcdt/memoir>（Apache-2.0，v0.2.5，提交 `b8b14fc`，统计取于 2026-09-26）
- 存储内核：<https://github.com/zhangfengcdt/prollytree>，PyPI `prollytree` 0.4.1
- 文档站：<https://zhangfengcdt.github.io/memoir/>；项目页 <https://www.memoir-ai.dev/>
- 包内文档：`docs/architecture.md`（性能与规模自述值）、`docs/theory/classifier.md`、`docs/theory/search.md`、`docs/theory/conflict-merge.md`、`docs/theory/related-work.md`、`docs/cli.md`、`docs/mcp.md`
- 本文实测数据在 macOS（Apple 芯片）、Python 3.12、memoir-ai 0.2.5 与 prollytree 0.4.1 下取得，测试套件在提交 `b8b14fc` 上运行为 698 通过、1 跳过、耗时 127.81 秒。
