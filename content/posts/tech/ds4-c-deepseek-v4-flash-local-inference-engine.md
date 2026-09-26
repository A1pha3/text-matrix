---
title: "ds4 拆解：不接 GGML、不跑任意 GGUF，省下的通用性全押在前缀复用上"
date: "2026-05-09T09:27:03+08:00"
lastmod: "2026-09-21T00:00:00+08:00"
slug: "ds4-c-deepseek-v4-flash-local-inference-engine"
github_repo: "antirez/ds4"
source_key: "gh:antirez/ds4"
description: "对着 antirez/ds4 的 main@8db1d1d 逐条核查后拆解它：为什么它拒绝做通用 GGUF 运行器、磁盘 KV 缓存按什么寻址、为什么恢复会话不是瞬时动作、SSD streaming 与跨机张量并行各自换到什么、DSpark 与 MTP 现在是什么关系，以及那份官方向量回归怎么挡住「贪婪 token 没变但 logits 坏了」。"
draft: false
categories: ["技术笔记"]
tags: ["DeepSeek", "推理引擎", "Metal", "CUDA", "架构分析", "开源项目解读"]
---

> **判断**：这个项目真正下注的，不是「在个人机器上把大语言模型（LLM）跑起来」，而是智能体（代理）负载里那笔反复支付的 prefill 开销——同一份系统提示与历史，每轮请求都要从词元（令牌，即 token）序列的开头重算一次。它为此让掉了通用性：不链接 GGML、只认自己产出的权重包、模型支持明写「机会主义」，换来一条把会话状态当资产管理的路：可寻址、有预算、带淘汰、跨重启还在。看懂这条主线，`ds4.c`、engine、session、server、KVC 文件里每个字段才各归其位；把它当成又一个 llama.cpp 分叉来读，处处会觉得多余。
>
> **读完后能做什么**：说清一次 Claude Code 冷启动在这个引擎里经历过哪几次状态写入；判断磁盘缓存为什么没命中、该调哪个参数；分辨内存会话、磁盘 checkpoint、跨机恢复三者的代价差别；解释 SSD streaming 与张量并行各自换的是什么、不换什么；知道哪些性能数字不能拿来比较；以及按什么顺序读它的源码与文档。
>
> **依据**：[antirez/ds4](https://github.com/antirez/ds4) 钉在 `main@8db1d1d`（末次提交 2026-09-16；GitHub API（应用程序接口）2026-09-21 读到 22,582 stars / 2,163 forks、MIT 许可证、无 tag、无 release，`main` 此后已推进到 797 个提交，本文结论仍以钉住的提交为准）。事实取自 `README.md`、`MODEL_CARD.md`、`docs/`（SERVER、MODELS、PERFORMANCE、CLIENTS、TESTING、SSD_STREAMING、SPECULATIVE_DECODING、DISTRIBUTED）、`download_model.sh`、`Makefile`、`ds4_help.c` 与 `ds4.c` / `ds4_server.c` / `ds4_kvstore.c` 的定点读取；行号引用见文末。

## 目录

- [§1 系统地图：四条线，一条主线](#1-系统地图四条线一条主线)
- [§2 边界：它拒绝做什么，以及怎么发布](#2-边界它拒绝做什么以及怎么发布)
- [§3 权重包是引擎的一部分](#3-权重包是引擎的一部分)
- [§4 三条硬件线，构建目标先行](#4-三条硬件线构建目标先行)
- [§5 会话与并发：从一条时间线到多个 slot](#5-会话与并发从一条时间线到多个-slot)
- [§6 磁盘 KV 缓存：按什么寻址，就能复用什么](#6-磁盘-kv-缓存按什么寻址就能复用什么)
- [§7 恢复的代价并不相同](#7-恢复的代价并不相同)
- [§8 装不下之后：SSD streaming 换的是容量](#8-装不下之后ssd-streaming-换的是容量)
- [§9 投机解码：DSpark 上位的这一年](#9-投机解码dspark-上位的这一年)
- [§10 接口层：五条路由、四套工具语法、三档思考](#10-接口层五条路由四套工具语法三档思考)
- [§11 接入四个客户端，以及一次请求到底经过了什么](#11-接入四个客户端以及一次请求到底经过了什么)
- [§12 性能数字怎么读：先问测的是什么](#12-性能数字怎么读先问测的是什么)
- [§13 它凭什么说自己没算错](#13-它凭什么说自己没算错)
- [§14 常见故障与排查入口](#14-常见故障与排查入口)
- [§15 采用边界、采用顺序与下一步读哪份代码](#15-采用边界采用顺序与下一步读哪份代码)
- [§16 六个自测问题](#16-六个自测问题)
- [§17 事实核验与引用](#17-事实核验与引用)

## §1 系统地图：四条线，一条主线

`ds4.c` 顶部的自述就把范围划死了：它同时管着 GGUF 加载、写死的模型张量布局、CPU 参考内核、整模型的 Metal 图驱动和分词器（tokenizer）接线，形状校验只认已知布局，其余一律早失败。这份自述说明它是一条「刻意纵向」的切片，不是一座分层机房。

要读它，先把四条线分开，混在一起读是绝大多数误解的来源：

| 线 | 主要代码 | 负责什么 | 规模（行） |
| --- | --- | --- | --- |
| 引擎核心 | `ds4.c` / `ds4.h` | GGUF 与张量布局、图调度、分词、会话状态语义 | 85,257 / 641 |
| 后端内核 | `ds4_metal.m`、`ds4_cuda.cu`，另有 `metal/*.metal`、`rocm/*.cuh` 与 CPU 参考路径 | 同一套语义在每个平台上的实现 | 50,528 / 34,039 |
| 状态与容量 | `ds4_kvstore.c`、`ds4_ssd.c`、`ds4_engram.c`、`ds4_tp.c`、`ds4_distributed.c` | 磁盘 checkpoint、专家缓存预算、n-gram 表、跨机并行 | 1,352 / 215 / 308 / 3,220 / 8,437 |
| 前端 | `ds4_cli.c`、`ds4_server.c`、`ds4_agent.c`、`ds4_bench.c`、`ds4_eval.c` | 交互、HTTP 服务、原生编码智能体、测量、能力回归 | 2,438 / 22,194 / 13,635 / 1,043 / 4,998 |

`make` 的默认产物是五个可执行文件（`Makefile:78`）：`ds4`、`ds4-server`、`ds4-bench`、`ds4-eval`，以及给编码智能体（代理）用的原生前端 `ds4-agent`。没有独立的 Web 服务二进制——`ds4_web.c` 是链进 `ds4-agent` 的浏览器控制模块（链接 `ds4_web.o` 的只有 `ds4-agent`），给智能体提供搜索与打开网页一类的能力。`rax.c`（2,747 行）是作者自己的基数树库，`linenoise.c`（2,801 行）是行编辑库，两者都不是推理代码。

主线只有一条：状态复用。引擎核心负责让会话状态可回放、可快照；状态层负责把它写进磁盘并管住容量；前端负责让多轮请求尽量命中同一前缀；验证体系负责证明复用之后结果没走样。其余一切都是这条主线的代价与配套。

## §2 边界：它拒绝做什么，以及怎么发布

README 开宗明义：它是 self-contained 且刻意窄的，「不是一个通用 GGUF 运行器：你得用本项目自己产出的 GGUF」。模型支持也被明写成「intentionally opportunistic」：跟着最有用的开放权重走，重点是 128 GB 笔记本与 256/512 GB 工作站这几档。而且它留了一句更硬的话——更好的替代品出现时，某个模型可能被移除。

对 llama.cpp 的关系，README 说得比大多数衍生项目老实：`ds4.c` 不链接 GGML，但承认自己建立在 llama.cpp 开辟的路径上。它有若干源级部件按 MIT 许可证保留或改写过来：GGUF 量化布局与码表、CPU 量化与点积逻辑、部分内核。`LICENSE` 里因此保留了 GGML 作者的署名。

发布形态也很特别，三件事叠在一起看：

- 没有 tag，没有 GitHub release，最新状态就是 `main`。要复现本文任何一条断言，只能钉住具体提交。
- 质量口径是 beta。README 的原话是 "Consider it beta quality"，同时说明软件变化很快、每次发布前会跑一轮大 QA，但稳定性和回归肯定还会发生（以下为本文作者的概括）。
- 开发方式在 README 里单列一节声明："developed with strong assistance from AI coding agents and with humans leading the ideas, testing, and debugging"。作者还直接建议用户把编码智能体当成发现与改造项目的入口，并主张软件更应该按「几个主用例的可用样板」发布，而不是穷举所有配置。

这三条合起来是一致的设计取向：先钉死核心路径，再谈支持面。它不适合需要稳定 ABI（应用程序二进制接口）与版本化发布的场合，§15 会把这条落回决策。

## §3 权重包是引擎的一部分

引擎只认自家布局，那权重包就成了引擎的一部分。官方下载入口是仓库根的 `./download_model.sh`（自己造权重走 `gguf-tools/`），文件落到 `gguf/`，同一条命令重跑即可续传；默认模型 `ds4flash.gguf` 是一个由主模型下载更新的链接。代表性目标名与体量：

| 目标 | 体量 | 起点机器 |
| --- | --- | --- |
| `ds4f-q2` | 约 81 GB | 96 / 128 GB，Flash 0731 的默认起点 |
| `ds4f-q2-q4` | 约 98 GB | 128 GB，末六层路由专家升 Q4 |
| `ds4f-q4` | 约 153 GB | 256 GB 及以上，或跨机执行 |
| `ds4f-mxfp4` | 约 156 GB | 保留官方 MXFP4 路由专家、不重量化 |
| `ds41f-q2` | 文件 341 GiB（主权重 152 GiB + Engram 189 GiB） | 一台 128 GB Mac 走 SSD streaming |
| `pro-q2-imatrix` | 约 430 GB | 512 GB 常驻，或 streaming |
| `glm53-q4` | 约 178 GiB | 两台 Mac 张量并行，或单机 streaming |
| `qwen38-q2` | 文件 137.10 GiB（主权重与 MTP 41.73 GiB） | 64 GB Mac，从 `--ctx 8192 --prefill-chunk 1024` 起步 |

量化配方写在文件名里。Flash 的 Q2 是 `DeepSeek-V4-Flash-IQ2XXS-w2Q2K-AProjQ8-SExpQ8-OutQ8-chat-v2-imatrix-0731.gguf`，`docs/MODELS.md` 对它的解释值得逐段读：压缩几乎全花在路由专家（routed expert）上，gate/up 走 IQ2_XXS、down 走 Q2_K，而投影、共享专家与输出用 Q8，另有 F16/F32 张量。文档在这里特别补了一句：它们并非全是未改动的原始权重。整条路由量化由 imatrix 引导。混合专家模型（MoE）里被激进压缩的只有路由部分，这条边界是这套权重包能成立的原因。

同一份配方在不同模型上并不通用：Qwen3.8 的 Q2 同样是 IQ2_XXS gate/up 加 Q2_K down，但把 640 个逻辑输入维度 pad 到 768；它的 Q4 反过来是 Q4_K gate/up 加 MXFP4 down。GLM 5.3 Flash 的 Q2 又是 IQ2_XXS 加 Q2_K。也就是说，「2-bit 档」在这个仓库里不是一个可移植的假设，而是一份份独立的配方。

还有两类数据干脆不进内存。DeepSeek V4.1 Flash 的两个量化目标都带 189 GiB 的 Engram 表，文档要求「每种模式下都按需直接从文件读，绝不作为常驻表加载」，所以 GGUF 必须放在本地快盘上；Qwen3.8 的 GGUF 里另有 95.37 GiB 原始 BF16 n-gram，同样直读磁盘。这两条决定了它把「快 SSD」当成和内存同级的硬件前提。

## §4 三条硬件线，构建目标先行

Metal 是主线，README 给的是 96 GB 及以上的 Mac，更小的机器靠 SSD streaming；CUDA 线以 DGX Spark 为主要目标，同时覆盖其它后端不支持的多卡组合（比如在 Ada Lovelace / L40S 上跑 Flash）；ROCm 线对准 Strix Halo 这一类机型，例如 Framework Desktop。

后端由构建决定，而不是运行时投票：

| 构建 | 目标 | 前置 |
| --- | --- | --- |
| `make` | Metal（Apple Silicon） | Xcode 命令行工具 |
| `make cuda-spark` | DGX Spark，`sm_121` | CUDA 12.8+ |
| `make cuda-generic` | 本机架构的 NVIDIA 卡 | CUDA 12.8+ |
| `make cuda CUDA_ARCH=sm_89` | Ada / L40S 一类 | CUDA 12.8+ |
| `make strix-halo`（别名 `make rocm`，`Makefile:320`） | `gfx1151` | hipcc |

构建前置的版本号需要单独交代来源。CUDA 12.8 出自发布 QA 手册的构建要求（`QA_BEFORE_RELEASES.md:130`）。ROCm 7.14 是 `speed-bench/gfx1151-prefill-results.md:6` 的实测记录，ROCm 10.0 则是 `docs/STRIX_HALO.md:12` 给的容器方案。这三条都不在主构建文档里。

`ds4-server` 对 `--metal` / `--cuda` / `--cpu` / `--backend NAME` 是正常的参数解析（`ds4_server.c:15553-15571`），并没有把它们拒掉。帮助文本里那行可选后端名按 `DS4_ROCM_BUILD` 分岔：ROCm 构建列 `metal, rocm, or cpu`，其余构建（Metal 与 CUDA）列 `metal, cuda, or cpu`（`ds4_help.c:153-158`）。CPU 路径的定位是参考与调试实现，帮助文本里那条 CPU 调试示例就是 `./ds4-eval --cpu --questions 1 --tokens 32`（`ds4_help.c:504`）。

关于 CPU 有一条要澄清：macOS 上虚拟内存记账可能导致内核崩溃的警告确实存在，但它写在 `CONTRIBUTING.md` 与 `AGENT.md` 里，代码注释在 `ds4.c:14352` 附近，README 并没有这段话。另外，本文核查的提交里没有对 macOS 最低版本作任何要求——网上流传的「需要 macOS 14+」在仓库里找不到出处。

## §5 会话与并发：从一条时间线到多个 slot

服务端的并发默认极简：不加参数时只有一条常驻会话。`docs/SERVER.md` 的措辞是「Without `--batched-session`, there is one resident session」。这条线在 2026 年上半年还是全部真相，现在只是一个默认分支。

`--batched-session N` 会预分配 N 份独立 KV 状态，每个 slot 有自己的活动状态，全部占满时新请求排队。省内存的关键一句是：模型支持时，这些 slot 共享同一份 prefill 工作区，多一个 slot 只多它自己的那几份缓存。这句话对 Qwen3.8 Flash Next 最要紧——它的瞬态大小由 prefill chunk 而不是上下文长度决定，默认 chunk 下每会话要占几个 GiB。启动行会把这两个数字一起打出来。

但「有 N 个 slot」不等于「快 N 倍」，得看解码是原生成批还是逐行回退：

| 后端与模型 | 解码执行方式 |
| --- | --- |
| Metal，常驻 Flash | 在支持的部位做原生 shared-expert / QKV 成批 |
| Metal，常驻 V4.1 Flash | 2-8 会话原生解码 |
| Metal RDMA 张量并行，V4.1 Flash | 3-8 会话原生，两个反而是有序回退 |
| Metal，SSD streaming 的 V4.1 Flash | 有序回退 |
| Metal，GLM 5.2 | 有序回退 |
| Metal，GLM 5.3 | 可见 token 到 2051 之前原生成批，之后有序回退 |
| Metal，Qwen3.8 Flash Next | 共享部分原生成批，循环状态、缓存与 PLE 历史仍按会话各存一份 |
| CUDA，受支持的多卡 Flash 张量并行布局 | 原生分组解码，prefill 与 decode 可混批 |
| 单卡 CUDA（含 Spark） | 有序回退 |

文档对回退的定义不含糊：逐行执行，提供的是并发与调度公平，不是原生成批的聚合加速；原生分组还可能轻微改变浮点归约顺序。长 prefill 会让位给正在解码的会话，让位粒度默认 128 token（`--mixed-prefill-quantum`，GLM-5.3 最小 1024）。另外，会话成批服务一般用普通目标解码，除 Metal 上的 Qwen3.8 可以连投机解码一起成批——其它模型在成批模式下不走 MTP/DSpark。

README 里那个「八张 L40S、16 会话、聚合约 126 t/s 生成」的数字，出处是 `QA_BEFORE_RELEASES.md` 的一张标注为历史参考的行：`16-row decode oracle`，126.0 aggregate t/s。同一节还留着 110 aggregate t/s 的数字，但那是复测门槛而非产品承诺。文档当场附了一条限定：那台主机在生产，未经许可不得连。注意 126 是并发聚合吞吐，不是单会话延迟。

## §6 磁盘 KV 缓存：按什么寻址，就能复用什么

这是全项目最能说明「通用性换前缀复用」的地方，也是最容易被误读的一块。它默认关闭，要显式指定目录：

```sh
./ds4-server --ctx 100000 --kv-disk-dir /tmp/ds4-kv --kv-disk-space-mb 8192
```

`--kv-disk-dir` 没有默认目录，`--kv-disk-space-mb` 在启用时默认 4096 MB。注意区分：`~/.ds4/kvcache` 是 `ds4-agent` 的会话存储目录，不是服务端的默认缓存位置，两者格式相同但策略各写各的（`ds4_kvstore.c:1-9` 明写 server 与 agent 共用文件格式）。

**寻址用的是文本，不是 token 序列。** `ds4_kvstore.h:36-40` 的注释把这件事讲得很直白：文件名是渲染后的字节前缀的哈希，负载里仍然存着精确的 token 与图状态。哈希只回答一个问题：这份 checkpoint 是不是代表新请求提示词开头的那些字节。匹配时先 `SHA1(渲染文本)` 比对，再对字节前缀做一次 `memcmp`。这么做的原因在查找顺序里：服务端先试内存里的活 token 前缀，再试磁盘上兼容的渲染文本前缀，最后只对新后缀做 prefill（`docs/SERVER.md`）。文本前缀这一路存在的理由写在 `ds4_kvstore.c:35-40` 的注释里：它用来兜住「同样的字节被归一化渲染拼成不同 token」那一类情况。除了「渲染文本」这一类键，还有两类键按客户端可见转录来算：thinking 可见性一类，Responses 可见性一类。剥掉思考块之后的历史是另一条时间线，所以必须分开。

`ds4_server.c:10765-10780` 那段注释是理解整套设计最划算的一读，它把三条不变量写在一起：缓存键是渲染字节前缀的 SHA1；文件用普通读写载入现有的图张量，**故意不用 mmap**，免得在一个已经映射了巨大 GGUF 的进程上再加一层虚拟内存映射；以及，只在活图已经走到想要持久化的那个边界时才写，绝不为了造一条缓存而把会话回滚，理由写在同一句里："that would turn cache population into a second hidden prefill"。

文件本身不复杂，48 字节固定头加一段文本再加负载（`ds4_kvstore.c:393-415`）：

| 偏移 | 字段 |
| --- | --- |
| 0-3 | `KVC` 魔数与版本号 |
| 4 / 5 / 6 / 7 | 路由专家量化位数、保存原因、扩展标志位、模型标识 |
| 8 / 12 / 16 | token 数、命中数、上下文大小（小端 32 位） |
| 20 | 负载 ABI 版本 |
| 24 / 32 / 40 | 创建时间、最近使用时间、负载字节数（小端 64 位） |

头后紧跟 4 字节的文本长度与渲染文本，再是 `ds4_session_save_payload()` 写出的引擎负载：checkpoint 的 token 序列、下一 token 的 `float32` logits（`DS4_N_VOCAB` 个）、每层压缩行数与 indexer 行数、raw 滑窗 / compressed / indexer 三类张量状态。下一 token 的分布也一并落盘，恢复时不必再解一步（本文只核实了写入侧，未追读侧是否消费这份 logits）。扩展标志位里有四项，其中一项就是 §7 要讲的工具 ID 映射表。

那三类张量不是实现细节，它们是模型架构的直接投影，也是「前缀复用能落盘」这件事成立的前提。`MODEL_CARD.md` 的架构一节给的数字很具体：43 层，每层保留最近 128 个 token 的高分辨率原始滑窗；从第 2 层起偶数层按 4 个 token 压成一行并额外维护一路 indexer，奇数层按 128 个 token 压成一行；当压缩历史超过配置上限时，indexer 打分并只取 512 行进注意力。换句话说，1M token 的上下文并不是 1M 行全精度 KV 乘 43 层，滑窗加两档时间轴压缩才是它的实体。模型卡接着说，这就是它能开放 1M token 上下文而不必为每一层每个 token 存一份完整 KV 的实际原因。落盘时记录的是每层的压缩行数，恢复时按同样的行布局灌回张量——没有这层设计，一条百 K 级前缀的 checkpoint 就不是几十 GB 而是几百 GB。

**为什么要裁尾和对齐。** 这两个旋钮只作用在冷启动的边界写盘上（帮助文本原话是 cold boundary saves）：默认裁掉 32 个尾部 token（`--kv-cache-boundary-trim-tokens`），再向下对齐到 2048 的整数倍（`--kv-cache-boundary-align-tokens`）。`ds4_kvstore.c:35-40` 给的分工是：分词器可能跨提示词边界合并文本，裁一小段尾巴能提高「便宜的 token 前缀」这条路径的成功率，而文本前缀查找负责兜住归一化渲染拼法不同的情况；2048 对齐则去贴后端 prefill chunk 的节奏，让压缩行的收尾和一条完整的冷提示一致。这里的取舍是提高复用率，而不是把缓存长度尽量做满。

顺带把 2048 这个数的三个来源分清，它们不是同一个东西：它是边界对齐的默认值，是 CUDA 张量并行的 prefill chunk 默认，也是官方向量测试为严格比对而钉住的那个值。而 `--prefill-chunk` 本身的默认早已按配置分档——普通 DeepSeek 4096、CUDA 张量并行 2048、PRO 长提示 8192，GLM 自己选并且拒绝你改；有解码在跑时让位的粒度是 `--mixed-prefill-quantum`，默认 128。

另外三个门槛参数决定了什么规模的前缀才值得落盘：短于 512 token 不存也不读，冷启动首段提示最长存到 30000 token（0 关闭），活跃会话每增加 10000 token 存一次对齐前沿。

**写入时机是七种，不是四种。** 枚举定义在 `ds4_kvstore.h:20-28`：`unknown`、`cold`、`continued`、`evict`、`shutdown`，加上 `ds4-agent` 写的 `agent-system` 与 `agent-session`。其中 `cold` 是长首段提示先 prefill 到稳定边界、写盘、再继续跑后缀；`evict` 的准确触发点是「磁盘快照即将替换某个 slot 的活状态之前」，而不是泛泛的「新请求来了」。`cold`、`evict`、`shutdown` 三类被算作 anchor——注释的说法是它们是有意留下的锚点而非自动产物——打分时乘 2.0 受软保护。

**预算和淘汰是有公式的。** 超预算时按 `score = (effective_hits + 1) × tokens / file_size` 选受害者：命中数按 6 小时半衰期衰减（低于 0.01 记零），anchor 类别乘 2.0，作为新写入严格前缀的 `continued` 条目被降权。写入前先估算文件大小、装不下就不写；写是原子的（先 `<path>.tmp.<pid>` 再改名）；命中时原地回写命中数与最近使用时间。上下文大小还有方向性：小上下文存下的 checkpoint 可以被更大的上下文加载，反之不行（`ds4_kvstore.c:859`、`:1207`）。

量化版本之间默认可共享兼容前缀，加 `--kv-cache-reject-different-quant` 才要求同量化；被认知的路由专家量化档已经是 2/4/5/6/8 bit 五种（`ds4_kvstore.c:417-421`），不再是 2 与 4 两档。

命中情况不需要猜：三个接口各有各的字段名：OpenAI 风格是 `prompt_tokens_details` 下的 `cached_tokens` 与 `cache_write_tokens`（`ds4_server.c:7069`），Responses 风格是 `input_tokens_details`（`:8641`），Anthropic 风格则直接给 `cache_read_input_tokens` 与 `cache_creation_input_tokens`（`:9101-9104`）；`--trace /tmp/ds4-trace.txt` 会为每次请求记一行 `cache_source`，取值是那八个字面量之一——`memory-token`、`memory-text`、`disk-text`、`thinking-visible`、`responses-visible`、`responses-tool-output`、`anthropic-tool-output`、`memory-rewind`——没命中时写 `none`，同时附上磁盘命中的 token 数与命中的文件名。没有 `/metrics` 这类指标端点，仓库里的路由表只有五条路径。

最后一条是运维层面的：缓存文件里有提示词原文和模型状态，这个目录要当私密数据处理；同时它是可丢弃的，清空前先停服务。

## §7 恢复的代价并不相同

磁盘上有 checkpoint，不等于恢复都很快。按代价从低到高排：

1. 内存里的活 slot 前缀——不重算。
2. 磁盘渲染文本前缀——读文件、灌回现有图张量，省掉整段 prefill。
3. 跨机张量并行——两个 rank 各自重建保存的 token 前缀，`docs/DISTRIBUTED.md` 里就一句「Expect prefill on restore」，`docs/SERVER.md` 说得更硬：它不是两块 GPU 的瞬时恢复。
4. 被 `/strip` 处理过的会话——只留文本与标题，KV 负载已删，必然重新 prefill。

流水线并行（`--dist-*` 那一族）是另一回事：它按层区间把状态沿路由重新分发，目的是把几台机器的内存加起来，让每个 token 走完整条路由。文档因此明确它只适合容量与长 prefill，不是解码加速。

还有一个不能恢复的类别：带图片的会话存不了。README 在 `ds4-agent` 的会话命令一节写的是「含图片的会话还不能保存」，服务端代码里同样有这道闸门——只在非多模态请求上写 checkpoint（`ds4_server.c:13447`）。投机解码的 draft 状态也不在持久化范围内，V4.1 与 Qwen 的 MTP 有自己的回滚快照，但那属于内存会话内部机制，不随 checkpoint 走。

工具调用历史则有一个专属的精确回放映射。服务端会保留采样出来的 DSML 工具块，并给它们分配不可猜测的 ID；重放这些 ID 就避开了「客户端把 JSON 换个格式再发回来导致重新分词不一致」这个坑。这张映射有界（`--tool-memory-max-ids`，默认 100000），可以作为扩展段落写进缓存文件；`--disable-exact-dsml-tool-replay` 能关掉它做对照实验。关掉之后，归一化渲染可能要求重建部分前缀——这也是为什么有些前缀看起来一模一样却 miss。

## §8 装不下之后：SSD streaming 换的是容量

`docs/SSD_STREAMING.md` 开头就把这件事定性成一次交换：常驻更快，streaming 用速度换容量，而且它不解决「内存连上下文和运行时缓冲都不够」的情况。机制说起来很朴素：把路由专家做成一个有界缓存放在内存里，缺失的专家直接从 GGUF 读。所以没有独立的缓存目录，前提是 GGUF 本身在本地快盘上。

```sh
./ds4 --ssd-streaming                          # 自动预算
./ds4 --ssd-streaming --ssd-streaming-cache-experts 32GB
./ds4 --ssd-streaming --ssd-streaming-full-layers 12
```

`--ssd-streaming-cache-experts` 接受 `N`（专家槽位数）或 `NGB`（字节数，并且额外保留两个完整 prefill 层），两者都可能被自动下调以容下模型、图、上下文与后端工作集；`--ssd-streaming-full-layers N` 是 GLM 在 Metal 上流式时的选项，让前 N 个路由层完整常驻，默认由专家预算推算，`0` 关闭；`--simulate-used-memory NGB` 是诊断开关，在加载模型前先锁住 N GiB 来模拟一台内存更小的机器。日常使用要留着默认的热度预加载，`--ssd-streaming-cold` 与 `--ssd-streaming-preload-experts N` 主要在做对照测量时才用。

一个反直觉的规模事实：`ds4_ssd.c` 只有 215 行，干的是参数解析、内存锁定与预算计算；真正的 streaming 逻辑散在引擎与后端里。这条线代码量小，硬件前提却最硬。

它换到什么，文档给的是 2026 年 9 月 6 日一台 128 GB M5 Max、自动缓存、不开投机解码的数：

| 模型 | 首次 prefill | 追加 prefill | 生成 |
| --- | ---: | ---: | ---: |
| GLM 5.3 Flash Q4_K，177.77 GiB | 121 t/s | 104 t/s | 11.9 / 14.9 t/s |
| DeepSeek Flash Vision Exp MXFP4，145.26 GiB | 300 t/s | 263 t/s | 11.9 / 19.3 t/s |

两组条件不同：GLM 用 2K 提示加 1K 追加，DeepSeek 用 8K 加 4K 追加，每个前沿生成 128 token，GLM 一行取三次运行的中位数，DeepSeek 一行是单次运行；DeepSeek 那一行最新的一次跑用的是 86.2 GiB 专家缓存和更新过的淘汰优先级，文档自己声明它不能和更早的 64 token 测量直接比。生成速度含首 token 等待。这一节的收尾也写得克制：缓存复用取决于提示词，这些是工作负载参考值，不是所有超过内存的模型都能拿到这个速度。

同一节里还有一条更值得注意的对照：满血 GLM 5.3 IQ2_XXS（196.58 GiB）在 8K 上下文、61.35 GiB 有效专家缓存下，一次 16 token 的追加从 30.8 秒降到 2.9 秒。其后的生成从 4.09 t/s 升到 5.11 t/s，取三次运行中位数、每次生成 64 token。文档同时写明，所有对照过的 logits 与生成文本完全相同。这条比上面两行更能说明 streaming 的收益形状——它救的是短追加，不是首次 prefill。

## §9 投机解码：DSpark 上位的这一年

`docs/SPECULATIVE_DECODING.md` 的定性没有半点营销味：用一小段草稿预测后续 token、交给主模型一次校验，接受的前缀让生成一次推进多步；**它不加速 prefill**；默认关闭；收益取决于提示词、模型、后端和上下文长度，接受率差时反而更慢——「测你自己的负载，不要假设草稿模型一定有帮助」。

DeepSeek Flash 这一侧现在走 DSpark：一个独立的支持文件而非独立语言模型，每次最多提出 5 个 token。

```sh
./download_model.sh ds4f-q2
./download_model.sh ds4f-dspark
./ds4 --dspark --mtp-model gguf/DeepSeek-V4-Flash-DSpark-support-0731.gguf
```

支持文件与主模型 checkpoint 一一对应，Flash 0731 与 Vision Experimental 各有一份，不能混用，PRO 不支持。它多带约 5.6 GiB 权重加运行时状态；在 Metal 上主模型可以常驻也可以走 streaming。文档里那句定位很重要：「DSpark replaces the legacy one-stage MTP drafter for that run; the two are not stacked」。旧的一级 MTP 草稿器是被替代，不是叠加。同样的参数在 `ds4-agent` 与未成批的 `ds4-server` 请求上可用。

GLM 与 Qwen 的草稿块本来就打进主 GGUF，`--mtp` 即启用，`--mtp-timing` 顺带打印接受率与计时。GLM 每轮最多提交两个 token；Qwen 默认只前进一步，但近期第一级草稿全对时会自动挂上第二级链式草稿（多一层 nextn，用 3 行一次校验吸收），第二级连续被拒就退回；`DS4_QWEN4_MTP_DEPTH=2|3` 固定深度，`0`（默认）就是上面的自适应策略。

采样语义分两档，这一档最容易被写错。温度为 0 时，被接受的草稿必须与目标模型的贪婪延续一致；非零温度下默认是机会主义模式——普通 token 走请求指定的采样设置，但与草稿匹配的贪婪结果直接接受，一旦提出的后缀不匹配就恢复采样。文档自己承认「这比通常的采样更确定」。要严格保持目标分布得显式加 `--mtp-exact-sampling`，它按目标概率接受贪婪提案、被拒时从剩余分布采样。置信度剪枝阈值 `--dspark-confidence` 的默认值也按后端分档：贪婪与机会主义模式下 Metal 0.6、CUDA 与 ROCm 0.7，精确采样 0.8。

两条代价摆在台面上。接受后的 token 保留成批校验器产出的状态，浮点归约顺序可能与逐 token 解码不同，因此长的贪婪延续不保证逐字节相同；要和只跑目标模型的路径对照，得用 `--quality` 或 `--dspark-strict` 关掉投机接受路径——而文档同样写明，这两个开关也不承诺跨硬件的一致输出。另外，会话成批服务用普通目标解码；`docs/SPECULATIVE_DECODING.md` 说得不留余地——不会把 DSpark/MTP 和会话批次合起来用，而 `docs/SERVER.md` 在这条上留了一个例外：Metal 上的 Qwen3.8 可以连投机解码一起成批（§5）。还有一个只在服务端出现的细节：当一个已校验块跨过工具采样模式边界（比如解码中途进入工具调用语法），服务端会回退到块起点重算那个边界 token，让下一次采样用新模式；精确采样模式下这次回退恢复的是校验前的循环状态快照，而不是重置整张图，免得每遇边界就重放一遍长上下文。

## §10 接口层：五条路由、四套工具语法、三档思考

服务端只注册了五条路由（`ds4_server.c:15089-15122`），没有 `count_tokens`、没有 `/health`、没有 `/metrics`：

| 方法与路径 | 用途 |
| --- | --- |
| `GET /v1/models` | 已加载模型信息；`/v1/models/<别名>` 走前缀匹配加别名校验 |
| `POST /v1/chat/completions` | OpenAI 风格对话 |
| `POST /v1/responses` | Responses 风格请求与续跑 |
| `POST /v1/completions` | 文本补全 |
| `POST /v1/messages` | Anthropic 风格消息，含流式 |

请求里的模型名只是兼容别名，真正决定跑哪个模型的是启动时那个 GGUF。默认监听 `http://127.0.0.1:8000`，`--host 0.0.0.0` 才换接口；`--cors` 只负责加跨域资源共享的响应头，不改监听地址也不做访问控制，面向公网得自己在前面放鉴权和 TLS。

工具调用的难点从来不在 HTTP 字段，而在模型侧的文本语法。引擎内部有四套模板：`SERVER_MODEL_SYNTAX_DEEPSEEK`、`_GLM`、`_DEEPSEEK41`、`_QWEN`（`ds4_server.c:672-676`），按引擎选取。DeepSeek 家族输出 DSML，分隔符常量就是 `#define DS4_DSML "｜DSML｜"`（`ds4_server.c:5824`），V4.1 用的是带空格的变体标签；GLM 是另一套 `</tools>` 加 `<tool_call>` 的结构，Qwen 是 `<function=…>` 那一族 XML。客户端侧的 schema 与工具块在两种协议间来回转换，模型侧永远只看到自家那套语法——这就是「兼容断在协议细节而不是 HTTP 路径」的具体含义。

思考模式在服务端有三档语义，几条边界值得逐条记：

- DeepSeek 默认开思考；`--nothink` / `/nothink` 关掉。V4.1 还可以给精力度打分：`--think-level 25`，1 到 100 是强度，0 是关闭，`--think` 相当于 75，`--think-max` 是 100，会话中改档会重建缓存前缀。
- `reasoning_effort` 的映射是 `low` 与 `minimal` 归低档、`medium` 归中档、`high` 和 `xhigh` 都归高档、只有 `max` 归最高档。`xhigh` 不等于 Think Max，这一条坑过不少人。
- Think Max 需要 `--ctx` 至少 393216，否则静默回落到高档而不是报错（`ds4.c:427` 的常量，判定函数 `ds4_think_mode_for_context()`）。模型卡独立给的建议是「Think Max 至少用 384K 上下文窗口」，与这个常量对得上。V4.1 家族不走这个门，因为它自己用精力度刻度。
- 关闭思考有三条路：`think: false`、把 thinking 对象设为 disabled、或者用非思考别名（`model_alias_disables_thinking()` 认 `deepseek-chat` 这一类）；反过来 `deepseek-reasoner` 是强制思考。

采样默认值是温度（temperature）1、top-p 1、min-p 0.05，`--temp 0` 选贪婪。这里有一条与帮助文本相反的现状：**思考模式下客户端显式给出的采样参数现在会生效**，那套 DeepSeek 风格的默认值只补客户端没提供的旋钮。`ds4_server.c:817-818` 的注释就是这么写的，靠的是 `temperature_set` 一组位标记。帮助文本里还留着「思考时忽略客户端旋钮」的旧表述，以代码和 `docs/SERVER.md` 为准。工具调用侧的限制则收窄了：只在 DSML 结构 token 上强制贪婪，工具参数正文仍走正常采样。

## §11 接入四个客户端，以及一次请求到底经过了什么

`docs/CLIENTS.md` 给的是四个客户端的完整配置，接口选择各不相同：

| 客户端 | 走哪条路 | 配置里真正要紧的地方 |
| --- | --- | --- |
| Pi | OpenAI 兼容 | 提供 `thinkingFormat: "deepseek"` 与 `requiresReasoningContentOnAssistantMessages: true`，思考内容必须原样回传 |
| OpenCode | 软件开发包（SDK）侧的 `@ai-sdk/openai-compatible` 适配层 | 官方示例只填 `baseURL` 与 `apiKey` 占位符，没有任何思考格式字段 |
| Codex 命令行工具 | Responses 接口 | `wire_api = "responses"`，并把 `stream_idle_timeout_ms` 放大到 1000000 |
| Claude Code | Anthropic 兼容 | 用 shell 包装脚本一次指定主模型与各个角色模型，URL 不带 `/v1` |

Claude Code 的官方写法是这样（`docs/CLIENTS.md:108-121`），和常见的 `ANTHROPIC_API_KEY` 写法不同：

```sh
#!/bin/sh
unset ANTHROPIC_API_KEY
export ANTHROPIC_BASE_URL="http://127.0.0.1:8000"
export ANTHROPIC_AUTH_TOKEN="dsv4-local"
export ANTHROPIC_MODEL="deepseek-v4-flash"
export ANTHROPIC_DEFAULT_SONNET_MODEL="deepseek-v4-flash"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="deepseek-v4-flash"
export ANTHROPIC_DEFAULT_OPUS_MODEL="deepseek-v4-flash"
export CLAUDE_CODE_SUBAGENT_MODEL="deepseek-v4-flash"
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
export CLAUDE_STREAM_IDLE_TIMEOUT_MS=600000
exec claude "$@"
```

包装脚本的名字要和 `claude` 不同。文档还给了两条通用约束：客户端的上下文上限不要高于服务端，输出 token 同样吃这份预算；配置里的 `dsv4-local` 只是占位符，服务端本身不做鉴权。

把前面几节串成一条真实路径。假设服务端 `./ds4-server --ctx 100000 --kv-disk-dir /tmp/ds4-kv --kv-disk-space-mb 8192`，Claude Code 第一次带着数万 token 的系统提示与工具表进来：

1. 请求被解析成 chat 消息，按 DSML 语法渲染提示词并分词，进入常驻会话。
2. 冷启动走分块 prefill。由于这是「长首段提示」，引擎先推到稳定边界——先裁掉 32 个尾部 token、再向下对齐到 2048 的整数倍——在那里以 `cold` 原因写一份 KVC 文件，键是这段渲染字节的 SHA1，然后继续跑剩下的后缀。
3. 生成阶段解码出 DSML 工具调用块，服务端为它登记一个不可猜测的工具 ID；响应以 SSE 流回客户端。
4. 第二轮请求把整段历史重新发回来。服务端先看内存里的活 token 前缀，命中就只补后缀；如果这期间 slot 已被别的会话换掉，就拿渲染文本前缀去磁盘里找，命中的那份是刚才的 `cold` 文件，读回来灌进现有图张量，仍然只对新增后缀做 prefill。
5. Claude Code 走 Anthropic 接口，响应里的 `usage.cache_read_input_tokens` 会体现命中的输入量（OpenAI 与 Responses 接口分别是 `prompt_tokens_details` 和 `input_tokens_details`）。`--trace` 里对应的一行是 `cache_source = disk-text`。如果这次没命中，先按 §14 那张排查表逐条比对，而不是先怀疑缓存坏了。

第一次的价值有限，第二次才开始回本——这正是「磁盘 KV 缓存不是附加功能，而是这套架构存在的理由」的意思。

## §12 性能数字怎么读：先问测的是什么

`ds4-bench` 是仓库给出的上下文扫描口径（另有 `session-concurrency-bench` 这类并发性基准与若干内核级基准）。README 末尾「Speed」一节那张 M5 Max 吞吐图就是这类扫描的产物。测量定义写在 `docs/PERFORMANCE.md`：按上下文前沿逐段推进，**每个 prefill 数字只测新增加的那一段**；生成用固定的贪婪、非 EOS 探针；探针之间通常恢复一次内存快照，网络 TP 与超出快照内存上限的情况改用前缀重放——而重放时间不能当追加 prefill 速度读。基准提示词是清洗过的公版《I Promessi Sposi》。这张表的 prefill 列全是「该前沿新增区间的速度」，与 §8 里「首次 / 追加」那种两段式口径不是同一个测量，别把它们并排比大小。

现行记录的是 Flash Q2 在两种 128 GB 机器上的扫描，2048 token 间隔、每前沿 128 个贪婪生成 token：

| 机器 | 上下文 | Prefill | 生成 |
| --- | ---: | ---: | ---: |
| M5 Max，128 GB | 2048 | 790.18 t/s | 39.35 t/s |
| M5 Max，128 GB | 16384 | 572.53 t/s | 36.14 t/s |
| M5 Max，128 GB | 32768 | 557.04 t/s | 34.36 t/s |
| M5 Max，128 GB | 65536 | 398.50 t/s | 27.64 t/s |
| DGX Spark，128 GB | 2048 | 825.76 t/s | 18.05 t/s |
| DGX Spark，128 GB | 16384 | 872.44 t/s | 15.10 t/s |
| DGX Spark，128 GB | 32768 | 855.94 t/s | 14.43 t/s |
| DGX Spark，128 GB | 65536 | 822.98 t/s | 13.84 t/s |

这组对照的价值在于它的形状，不在于谁赢：Spark 的 prefill 更快而且几乎不随上下文衰减（822-872 t/s），生成却稳定只有 Metal 的一半上下（18.05 对 39.35、13.84 对 27.64），并且同样随上下文继续下滑。把它读成「Spark 更强」或「Metal 更快」都是误用。prefill 由算力与权重带宽主导，解码则要把全部权重与 KV 每 token 走一遍，两台机器的瓶颈根本不在同一处。

`QA_BEFORE_RELEASES.md` 的第 16 节是跨系统的历史对照表，那里有更杂的条目：M3 Ultra 512 GB 跑 GLM 5.3 Flash Q4 是 437.62 / 24.74 t/s；两台 M5 Max 走 Metal RDMA 张量并行跑 GLM 5.2 IQ2_XXS 约 214 / 16.7 t/s；DGX Spark 跑 GLM 5.3 Flash Q2 是 531.39 / 14.35 t/s；Strix Halo 的 ROCm 在同一个代码提示下给出 16.26（普通）、12.28（机会主义投机）、13.52（精确采样）三种 t/s；八张 L40S 的 Flash Q4 是 1524.84 t/s prefill、46.93 t/s 解码，另一行 16 行的解码 oracle 给到 126.0 aggregate t/s。这张表的自我约束也写在同一节里：它们是「同一模型同一负载下的比较点，不是可移植的吞吐承诺」，缺基线就自己补一次匹配条件的测量。L40S 那两行另要打折看，文档标它们是历史留存数据。

有三类结论从这些数字里推不出来。第一，聚合吞吐推不出单会话延迟，16 会话的 126 t/s 与单会话的 39.35 t/s 是两个问题。第二，有序回退的成批结果不能当原生成批的证据。第三，SSD streaming 与常驻是两种容量策略，跨策略比较会同时混进并行收益与容量收益。文档因此要求比较张量并行时保持量化与提示词一致——否则「两台常驻 Q4 对一台流式 Q4」量的就不只是并行。

## §13 它凭什么说自己没算错

一个只认自家权重的引擎，最大的风险不是跑不出来，而是「跑出来了但悄悄算歪了」。这个仓库对此的回答分三层，每层都可运行。

最外面是官方对齐层。`tests/test-vectors/` 下的向量来自真实调用官方 DeepSeek V4 Flash API：`deepseek-v4-flash`、贪婪解码、关闭思考、`top_logprobs=20`；文档同时承认托管 API 不暴露完整 logits，所以文件里存的是「API 能给的那一片」。这一层有两个容易忽略的设计：

- 按 checkpoint 分目录。`flash-0731/` 是当前默认，`flash-pre-0731/` 是历史；名字里含 `0731` 的 GGUF 必须配 `flash-0731`，「测试夹具（fixture）与 checkpoint 不匹配是无效测试，不是模型质量结果」。
- 除了对官方的 `official.vec`，还有一份 `local-golden.vec`——它从匹配的 GGUF 上采集本地 top-k/logit 快照，专门用来抓「贪婪 token 没变、但 logits 分布已经坏掉」这种后端漂移。只有前一层的话，这类错误会一路漏过去。

```sh
./ds4_test --logprob-vectors
./ds4_test --local-golden-vectors
```

跑严格校验时它会关掉各条加速快路并把 `DS4_METAL_PREFILL_CHUNK` 钉在 2048；文档提醒不要把这一设置推广到所有基准。GLM 这一路另开目录，用 OpenRouter 取向量和 `manifest.tsv`（默认路由到 `parasail/fp8` 并要求参数严格匹配，否则 top-logprobs 切片拿不到）。`tests/test-vectors/README.md` 还留了一个具体到 issue 的定向复现，用来暴露分层成批解码在命令缓冲未完成时复用专家缓存缓冲区导致的错误 logits，它要求显式给出 0731 那份 GGUF：

```sh
DS4_TEST_MODEL=gguf/DeepSeek-V4-Flash-0731-IQ2XXS-w2Q2K-AProjQ8-SExpQ8-OutQ8-chat-v2-imatrix.gguf \
  ./ds4_test --metal-ssd-streaming-cache-pressure
```

它强制 16 GiB 的专家缓存，并且只跑 `short_code_completion` 这一个用例。

中间是排查工具层。`./ds4 --dump-tokens -p "..."` 不推理就能看模板差异；`./ds4 --dump-logprobs /tmp/out.json --logprobs-top-k 20 --temp 0 -p "..."` 与 `--dump-logits` 用来把「采样变了」和「图算错了」分开；`./ds4-server --trace /tmp/ds4-trace.txt` 会记录提示词渲染、缓存决策、生成文本与工具解析事件——文档提醒这些文件可能含敏感内容。模型无关的检查可以先跑：`make ds4_test ds4_agent_test test-session-state`（最后那个查的就是会话状态）、`./ds4_test --server`，Metal 上还有三个不加载 GGUF 的小张量测试；`make test` 则包含需要模型的用例，多卡 QA 时别顺手加载大模型，ROCm 有自己的 `make test-rocm`。

最里面是能力与发布层。`ds4-eval` 对真实 GGUF 跑内嵌的能力回归，默认 `core` 套件，另有 `hard`、`hard-smoke`、`all`，`--list-cases` 可以在不加载模型前列出用例，`--regrade-trace` 允许对已有 trace 重新打分。README 给它的定性是一句需要认真读的话：这些是 DwarfStar 的集成检查，**不是官方排行榜分数**，题目来源与许可证列在 `EVAL_DATA.md`。发布前则走 `QA_BEFORE_RELEASES.md`（13 万字节）：硬件矩阵、与 checkpoint 匹配的质量测试、长上下文智能体任务、速度检查。它同样要求把没跑完的检查记录下来。`docs/TESTING.md` 的原话是「smoke test 不是完整 QA」。

对改动者的对应要求也写得很具体：碰状态处理，要覆盖回放/回退、保存/加载、图片、多会话以及一条全新提示；碰分布式，要在两个 rank 上都跑并包含失败路径，「本地参数解析测试不是物理张量并行的 QA」。

## §14 常见故障与排查入口

按现象查，比按日志字符串查稳——仓库里现成可依赖的入口是 `--trace`、`usage` 里的命中计数和 `--help`。

**缓存目录里空空如也。** 第一步确认 `--kv-disk-dir` 真的传了：磁盘缓存是 opt-in，没有默认目录，`~/.ds4/kvcache` 那个路径属于 `ds4-agent`。第二步看长度门槛，短于 512 token 的前缀既不存也不读；第三步看首段是否超出 `--kv-cache-cold-max-tokens`（默认 30000，超出即不再为冷启动写盘）。

**前缀看起来一样却 miss。** 按顺序排：模型标识必须相同；`ctx_size` 只能从小到大兼容，大上下文存的 checkpoint 不会被小上下文请求用上；加了 `--kv-cache-reject-different-quant` 时跨量化复用被禁；`--disable-exact-dsml-tool-replay` 会让归一化渲染要求重建部分前缀；张量并行下的恢复本来就是重建。判断依据是 `--trace` 里的 `cache_source`，值为 `none` 时再去看 `disk_cached_tokens`。

**404 或客户端连不上。** 服务端只有 §10 那五条路由；OpenAI 兼容客户端的 base URL 要指到 `/v1`，Claude Code 的 `ANTHROPIC_BASE_URL` 则到主机根为止。未知参数会被直接拒绝并打印 `ds4-server: unknown option: ...`，随后 usage 与 `exit(2)`——启动即退先查这一条。

**Think Max 没生效。** `--ctx` 要至少 393216，`xhigh` 不是 `max`；V4.1 不看这两个开关，用 `--think-level`。

**OOM 或者越跑越慢。** 上下文与 slot 数要一起定（`docs/SERVER.md` 的提醒是「能塞下一份的上下文未必塞得下四份」）；成批模式下每 slot 的 prefill 瞬态按 chunk 而非上下文长度定大小；从常驻改成 streaming 之后要先区分冷缓存与热缓存再谈速度；DSpark 开了反而慢是接受率问题，`--mtp-timing` 给计数。

**输出与官方对不上。** 先确认 fixture 目录与 GGUF 的 checkpoint 同代；再确认比较的是同一条路径——严格向量测试关掉了加速快路并钉了 chunk，投机解码下长贪婪延续本来就不保证逐字节一致，要比较请显式 `--quality` 或 `--dspark-strict`。

## §15 采用边界、采用顺序与下一步读哪份代码

跨机那一层要先补一句安全前提：`docs/DISTRIBUTED.md` 明写网络协议没有鉴权也没有加密，只能用可信机器和可信网络。它还要求每个对等端跑同一个提交（commit）、模型路径与产物一致，改版本要一起改。两台 128 GB Mac 的张量并行是 50/50 且**恰好一个 worker，不要传 `--layers`**；RDMA 要有 active verbs 设备加 IPv4-mapped GID，「ping 得通不代表这个条件满足了」。

**现在就可以上手的场景**：机器在 96 GB 以上（Metal）、或是一台 DGX Spark、或是 Strix Halo 这一类机型，跑的正好是它带的那几个模型；负载形态是智能体式的——长系统提示、多轮重发历史、工具调用密集；并且你能接受按 commit 跟进、自己承担 beta 版本的回归风险。前缀复用这条主线在这样的负载里回本最快，因为省下来的就是每轮都要重付的那次 prefill。

**建议再等一等的场景**：要跑任意 GGUF 或任何开源模型（它只认自家布局，且模型支持是机会主义的，可能被移除）；要多模型混部或需要版本化发布与稳定接口（没有 tag、没有 release）；要靠它做面向公网的多人服务（HTTP 层不鉴权、跨机协议不加密，`--cors` 也不提供访问控制）；要把很多张便宜卡当低成本推理云（八卡 L40S 那类组合它是能做，但这是它最不像「消费级硬件」的一条路，运维复杂度全在你这边）。

如果决定上手，一个省时间的顺序：

1. 先按 `docs/METAL.md` 或对应平台指南编一条构建，用 `./download_model.sh ds4f-q2` 下当前默认档，只跑 `./ds4` 确认能出字、能 `/read 文件`。
2. 开服务但**先不开磁盘缓存**（`./ds4-server --ctx 32768`），接一个客户端，把工具调用与流式跑通。
3. 再加 `--kv-disk-dir` 与 `--kv-disk-space-mb`，用 `--trace` 观察一次冷启动到第二次请求的 `cache_source` 变化，确认真的在复用——这一步别跳，否则后面所有关于「快了多少」的判断都没有基线。
4. 内存不够再考虑 streaming 或跨机，并且明确自己换的是容量；模型与 checkpoint 换了代，就把 §13 那两层向量测试跑一遍。

按问题定位文件，比从头通读快得多：

| 想搞清 | 读 |
| --- | --- |
| 为什么这套设计成立 | `ds4_server.c` 的磁盘缓存段落注释（10765 起）与 `docs/SERVER.md` |
| KV 状态的三种类别从哪来 | `MODEL_CARD.md` 的 Architecture 一节 |
| checkpoint 的确切格式 | `ds4_kvstore.h`（结构与枚举）+ `ds4_kvstore.c` 的 `fill_header` / 淘汰打分 |
| 负载到底存了什么 | `ds4.c` 的 `ds4_session_save_payload()` |
| 后端如何拼起来 | `Makefile` 的 `CORE_OBJS` 与 `metal/` 下 26 个 `.metal` 文件的头注释 |
| 多会话的成批能力 | `docs/SERVER.md` 的 Multiple sessions 表格 |
| 投机解码的真实边界 | `docs/SPECULATIVE_DECODING.md` 全文（107 行） |
| 所有参数的当前默认值 | `./ds4-server --help` 与 `ds4_help.c` |

## §16 六个自测问题

答不上来时，回到括号里的小节再看一遍——它们考的都是机制边界，不是名词。

1. 一次冷启动的长提示，引擎为什么坚持先推到对齐边界再写盘，而不是边算边存？（§6、§7）
2. 缓存键为什么选渲染字节前缀而不是 token 序列？换成 token 序列会在什么情况下失效？（§6）
3. `--batched-session 4` 之后，为什么某些模型并没有变快？此时内存里多出来的是哪几份东西？（§5）
4. 一个在单机上命中率很好的前缀，为什么到了两台 Mac 的张量并行下还是要重算？（§7、§15）
5. 「贪婪 token 与官方一致」为什么不足以证明实现正确？仓库用哪个文件补这个洞？（§13）
6. DGX Spark 的 prefill 更快而解码更慢，这两件事各自由什么主导，能不能由此判定谁更强？（§12）

## §17 事实核验与引用

**核查方法与版本**。全部结论对着本地一份 `--depth 1` 克隆（`main@8db1d1d`，末次提交 2026-09-16，标题为 Document Qwen Metal batching and its quality checks）逐条读取，2026-09-21 对同一提交做了第二轮全量复核，行数、行号、默认值与性能数字全部复认；文件行数用 `wc -l`，参数默认值取自 `ds4_help.c` 的 `opt()` 行与 `./ds4-server --help` 文本，性能数字逐个回查 `docs/PERFORMANCE.md`、`docs/SSD_STREAMING.md` 与 `QA_BEFORE_RELEASES.md` 的表格行。仓库总行数约 419 万（含 `tests/` 与 `gguf-tools/` 下的数据），因此本文没有对「全仓搜索某标识符不存在」这类否定式断言作强声明，凡是这类结论都限定在上面核实过的文件里。

**外部数据**。GitHub API 于 2026-09-21 读到 22,582 stars / 2,163 forks、MIT、`created_at` 2026-05-06、`pushed_at` 2026-09-20、语言 C；`main` 在钉住提交之后继续推进，2026-09-21 读到 797 个提交（772 是钉住 `8db1d1d` 时的总数，由 commits 端点的分页上限读出）；releases 端点返回空数组，`git ls-remote --tags` 无输出，因此「无 tag、无 release」是当天的实况。Hugging Face 上作者名下的权重仓库包括 `antirez/deepseek-v4-gguf`、`antirez/deepseek-v4.1-flash-gguf`、`antirez/glm-5.2-gguf`、`antirez/glm-5.3-gguf`、`antirez/glm-5.3-flash-gguf`、`antirez/qwen3.8-flash-next-gguf`（六个仓库 2026-09-21 均在）。

**未实跑项**。本机没有 96 GB 以上的 Apple Silicon、没有 DGX Spark、也没有 RDMA 链路，因此本文所有命令的语法与默认值取自仓库文件与 `--help` 文本。编译、下载、服务启动、`ds4-eval`、两层向量测试、`--batched-session` 与跨机张量并行均未实际执行。凡涉及「跑起来会怎样」的句子，都是对文档与代码的转述，不是复现结果。

**unresolved**。三条。其一，`ds4_server.c:10766` 的注释仍写着「The server has one live Metal session」，而 `docs/SERVER.md` 已经描述多 slot；本文按文档与参数实现写，把那句注释当作未更新的历史。其二，帮助文本 `ds4_help.c:364` 关于思考模式忽略客户端采样的说法与 `ds4_server.c:817` 的注释和 `docs/SERVER.md` 冲突，本文以后两者为准，但没有去查这条差异是哪次提交留下的。其三，各模型 Q2 里 indexer、共享专家、注意力投影的具体张量类型，除 Flash 与 Qwen3.8 之外在仓库里查不到完整清单，本文不猜。

**失效条件**。四类断言最容易过期，重核成本也在它们身上：参数名与默认值（`--kv-cache-*` 一族和后端选择在过去五个月里已经动过一轮）；权重目标名与体量（下载表每上一个新 checkpoint 就变）；`docs/SERVER.md` 的原生成批与有序回退归属表（每个模型逐条在推进）；以及 §12 所有 t/s 数字——README 自己称其为记录基线而非每次提交的测量。重核一遍的成本是一份浅克隆加十几条 `grep`，二十分钟内可以完成。

**参考**：[antirez/ds4](https://github.com/antirez/ds4)、仓库内 `README.md` / `MODEL_CARD.md` / `docs/SERVER.md` / `docs/MODELS.md` / `docs/PERFORMANCE.md` / `docs/SSD_STREAMING.md` / `docs/SPECULATIVE_DECODING.md` / `docs/DISTRIBUTED.md` / `docs/CLIENTS.md` / `docs/TESTING.md` / `tests/test-vectors/README.md`、[antirez/deepseek-v4-gguf](https://huggingface.co/antirez/deepseek-v4-gguf)、[ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp)（本项目不链接 GGML，但按 MIT 保留了其若干源级部件，见 `README.md` 的致谢一节）。
