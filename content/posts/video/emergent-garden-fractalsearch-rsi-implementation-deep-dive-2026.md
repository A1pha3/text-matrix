---
title: "fractalsearch 8 小时实跑：从 0.0041 MSE 到 0.000226，看 AI 怎么一步步改坏又改好自己"
date: 2026-07-10T00:19:29+08:00
lastmod: 2026-09-21T00:00:00+08:00
slug: emergent-garden-fractalsearch-rsi-implementation-deep-dive-2026
source_key: "bv:BV1w8jL6dE1f"
description: "以 MaxRobinsonTheGreat/fractalsearch 仓库的 104 条 runs.jsonl + 4 个 solution + AGENT.md 为骨架，还原 AI 自主科研 8 小时全流程：从 autoresearch 框架搭建、Triton fused encoder 突破、GT-free 采样，到空间误差场演化，最终 MSE 0.000226、PSNR 36.45 dB。"
draft: false
categories: ["视频精读"]
tags: ["RecursiveSelfImprovement", "RSI", "Karpathy", "AutoResearch"]
hiddenFromHomePage: true
---

> **作者**：钳岳星君
> **视频**：Emergent Garden《Recursive Self-Improvement》（[YouTube t7_ZXgfJVG8](https://www.youtube.com/watch?v=t7_ZXgfJVG8)，2026-06-13）｜B 站 AI 配音版 [BV1w8jL6dE1f](https://www.bilibili.com/video/BV1w8jL6dE1f/)（@黑纹白斑马 译制，YouDub 项目）
> **源码**：[MaxRobinsonTheGreat/fractalsearch](https://github.com/MaxRobinsonTheGreat/fractalsearch)（GitHub，2026-06-19 公开，104 条 runs.jsonl + 4 个 solution + AGENT.md）
> **前身**：[MaxRobinsonTheGreat/mandelbrotnn](https://github.com/MaxRobinsonTheGreat/mandelbrotnn)（个人长期 pet 项目）+ [karpathy/autoresearch](https://github.com/karpathy/autoresearch)
> B 站视频未提供官方字幕轨（AI 配音版通常不含），YouTube 原版 yt-dlp 抓取需要登录 cookie。本文以仓库级事实为核心——AGENT.md 是任务书、README.md 是作者意图、solutions/notebook.md 是 AI 自留的研究笔记、runs.jsonl 是 104 次实跑的硬数据。

**目标**：理清 RSI 的宣传叙事和工程现实，看懂 fractalsearch 四个组件（任务书/裁判/选手/研究笔记）怎么咬合，理解 Triton fused encoder、GT-free 采样、空间误差场三次关键突破各自的贡献。文章末尾附有复现清单和自测题，可以动手判断"AI 自主科研"目前真实的边界在哪。

> **配套阅读**：想先看这支视频"讲了什么论点"（RSI 可能、但难、且危险），看同仓库的 [Emergent Garden RSI 视频精读]({{< relref "emergent-garden-recursive-self-improvement-fractalsearch.md" >}})；本篇专注"仓库里到底发生了什么"。要不要去看原视频：想听讲者自己讲 RSI 类比与风险判断的，值得一看；只想知道这次实验做了什么、数字从哪来的，读完本文就够了。

---

## 〇、先把"fractalsearch 是谁做的"理清楚

视频里 Emergent Garden 没说自己是谁，但 fractalsearch 仓库的所有者写得很明白——

`MaxRobinsonTheGreat`。README 第一段：

> _This has been a pet project of mine for a long time._

这位作者其实早就做"AI 拟合曼德博集合"——他的 mandelbrotnn 个人项目 2021 年就建了，仓库描述写的是 "Torturing neural networks by forcing them to learn the Mandelbrot set"。fractalsearch 不是从零起步，是把 Karpathy 2026-03 发布的 [autoresearch](https://github.com/karpathy/autoresearch) 框架套到自己的老问题上。

视频作者 Emergent Garden 在 8 段章节中把 fractalsearch 当成"RSI 在可重复工程上做到了什么"的样板间来展示——他没有动手 fork，没有亲手改代码，但他把这个实验配上"ASI / 智能爆炸 / 沙箱风险"的 RSI 主流议题一起讲。fractalsearch 源码是 Emergent Garden 的论据，不是他自己的产出。

厘清之后，视频里每一段在说什么，就不再是"AI 多厉害"，而是"AI 借助一个 5 分钟训练 budget + 一个 33M 参数的小哈希网格，在一个受限视觉学习问题上能做到什么程度"。这个视角更贴近工程师的日常。

需要说明：视频作者 Emergent Garden 的个人背景不在本文覆盖范围内。fractalsearch 仓库的所有者是 `MaxRobinsonTheGreat`（README 和 git commit 明确），视频频道作者未在 BV1w8jL6dE1f 简介里点明是否同一人，本文不做推测。

### 一张系统地图：fractalsearch 的四个组件各管什么

整个实验里有**四条互不重叠的主线**，常常被揉成一条故事线讲：

| 组件 | 文件 | 职责 | 谁能动 |
| --- | --- | --- | --- |
| **任务书** | `AGENT.md` | 告诉 AI 要做什么、不能做什么、循环长什么样 | 人类写死，AI 不改 |
| **裁判**（harness） | `harness/groundtruth.py` + `harness/evaluate.py` | 定义目标函数、固定 5 分钟 budget、SIGALRM 强杀、把结果写进 `runs.jsonl` | 人类写死，AI 不改（结构性沙箱） |
| **选手**（solution） | `solutions/*.py`（baseline / fourier / hashgrid / champion） | AI 提交的拟合算法（champion 指其中当前最优的那个），每次 commit 一个新文件 | AI 全权改写 |
| **研究笔记** | `solutions/notebook.md` | AI 跨 session 的连续记忆，记录 bracket（同一超参多档取值的对比实验）、假设、教训 | AI 自己追加 |

一个数字（比如 MSE `0.000226`，即均方误差）必须能同时落到这张表里的三个格子：它由某个**选手**（`champion.py`）在**裁判**（`evaluate.py` 5 分钟 budget）下跑出来、写进**研究笔记**（`notebook.md` 的 best 记录）。后面所有数字都按这张表归位，才不会被视频叙事带偏。

阅读路线：视频大纲章节把视频 8 段章节对到源码文件；第三到五章拆三次关键突破（Triton fused encoder、GT-free 采样、空间误差场）；第六章是 104 次试错的全景；第七到八章解释为什么这次不会"智能爆炸"；最后给三类读者各自的下一步。

---

## 视频大纲 vs 实际产物：章节对照表

B 站 @黑纹白斑马 在 UP 主简介里给出的 8 段章节时间线是研究骨架，下面这张表把它对到 fractalsearch 仓库里**真实存在的**文件，看视频每段在源码里落在哪里：

| B 站章节时间线 | B 站字幕简介（拿到的） | 源码里的实际对应 |
| --- | --- | --- |
| 00:00 RSI 概念引入 + Anthropic / OpenAI 动态 + 视频预告 | 引出 RSI 概念 | `AGENT.md` 顶部 "find the best algorithm to fit the Mandelbrot set" |
| 02:12 fractalsearch 实验介绍 | 源自 Karpathy AutoResearch，让 AI 在递归循环里迭代优化拟合曼德博集合 + 实验运行机制 + 评估规则 + 初步进展 | `solutions/baseline_mlp.py` + `harness/groundtruth.py`（[0,1] 区间的周期性 log-distance 目标）+ `harness/evaluate.py`（5 分钟固定 budget + 10 分钟 SIGALRM hard kill） |
| 09:27 RSI 可行性分析 | 起重机自举 / 人类学习 / 生物进化做类比 + 弱 RSI vs 强 RSI 区分 + 3 年内前沿 AI 公司开展大规模 RSI 实验 | `notebook.md` 完整记录了一次"收益递减"的提出与推翻：第一天三重假设检验写下 "Floor ~0.000336 is real"，第二天被 Triton fused encoder 一举砸穿——天花板是真实的工程现象，但它的高度会随工程水位移动 |
| 14:14 RSI 实现难度分析 | 硬件 + 能源 + 数据 + 收益递减天花板 + 目标度量设计难题 + 不太可能爆发式智能爆炸 | `harness/evaluate.py` 的 `TRAIN_BUDGET_S=300` 与 `HARD_KILL_S=600` 是"5 分钟预算封顶"的硬约束；最终 champion.py 251 行是它能撑住的最大复杂度 |
| 20:50 RSI 风险分析 | 小规模实验安全隐患 + AI 作弊 + 大规模 RSI 目标偏离 + 自我复制类癌症风险 + 沙箱隔离 + 人类管控 | `AGENT.md` "What you CANNOT do"：禁止改 harness/、禁止硬编码曼德博逻辑到 solution、禁止修改依赖——这是一个**结构性的沙箱** |
| 24:50 实验结果展示 | 哈希网格模型大幅提升拟合效果 + 自动生成代码可读性差带来额外安全隐患 | `runs.jsonl` 104 条 runs，best `mse=0.000226`，`runs/20260609-151512/...` 是 champion 产物 |
| 27:08 实验成本与未来展望 | 公布实验总成本 + 成本偏高 + 肯定 AutoResearch 类方案 + Anthropic Claude Fable 模型限制 | `runs.jsonl` 每条都记 `train_seconds`，约 300 秒/次 × 104 次 = ~8.67 小时单卡时间 |
| （视频无明确段） | Anthropic 对 Claude Fable 模型的能力限制 | 视频标题外延——视频作者认为 RSI 已经触手可及，但 Anthropic 一篇论文提醒，强 RSI 安全边界仍是开放问题 |

**核心映射**：B 站章节把 fractalsearch 当成 RSI 概念的实验装置——`AGENT.md` 是研究框架，`harness/groundtruth.py` 是目标函数，`harness/evaluate.py` 是评估器，`solutions/notebook.md` 是 AI 自留的研究笔记，`runs.jsonl` 是 104 次试错的履历。视频是结果叙事，源码是机制实录，两者拼起来才是完整的 RSI 故事。

---

## 一、问题：什么叫"AI 自己改自己的代码"？

`AGENT.md` 一句话锁定任务：

> _Find the best algorithm to fit the Mandelbrot set, i.e. learn the map `(real, imag) -> target` defined in `harness/groundtruth.py`, while still being a universal function approximator._

三个隐形但严苛的边界：

- **目标函数在 [0,1]**，并非常规的 0/1 集合成员关系。`groundtruth.py` 用了 `Periodic · log-distance` 变换：先跟踪 escape-time 的轨道导数 `z' = dz/dc` 给出距离估计 `d`，再用 `phase = BETA · log(d)`、`target = 0.5 + 0.5·sin(2π·phase)`（BETA = 0.050，R = 1e4 bailout）；永不逃逸的集合内点直接取 1.0。这是难度的灵魂——它**接近边界时频率发散**，比单调平滑 escape-time 多出无限嵌套的细节纹理。
- **每次训练 budget = 5 分钟**，10 分钟强制 SIGALRM kill。`AGENT.md` 在 Goal 一节明确写着 "use it all"。这就是 RSI 的工程化身：每次只给你 5 分钟，跑完直接看 MSE；想法先 commit 再跑，分数不行就换思路再来。

`AGENT.md` 结尾一段几乎是在下军令：

> _NEVER STOP. Once the loop has begun, do not pause to ask the human whether to continue. They may be asleep and expect a stack of results when they return._

这就是 RSI 的实现机制——AI 不是无脑跑实验，而是**对着 git 历史 + runs.jsonl 反推下一步该做什么**。`AGENT.md` 里 "The experiment loop — LOOP FOREVER" 一节（第 52-64 行）写得明白：

1. **看 git state 和 leaderboard**——git log 加 `runs.jsonl` 当前最好的 MSE（或 dashboard）。
2. **形成假设**——复制最接近的上一版赢家，不要整个重写。
3. **git commit**——`git add -A && git commit -m "<idea>"`，一句话描述本次想试什么。
4. **跑**——`uv run python -m harness.evaluate solutions/<file>.py > run.log 2>&1`，**全部重定向**，不污染 AI context。
5. **读结果**——`grep "^mse:\|^status:" run.log`。evaluator 已经把完整记录 append 到 `runs.jsonl`，artifact 存到 `runs/<id>/`。
6. **崩溃了**——`tail -n 50 run.log` 找 traceback。如果是打错字或 shape mismatch，改完重跑；如果是思路错了，崩溃已被记作 `status="crash"`，换思路。
7. **Repeat**——回到第 1 步，循环直到人来打断。

跑超 10 分钟 SIGALRM 强制杀，记 `status="timeout"` 当作废牌。**严禁改 `harness/`**——target、接口、metric、time budget 是 ground truth，动了就无法和历史对比。

`AGENT.md` 里还有一行容易被看漏：

> _Each run trains for a fixed 5-minute budget (a run is force-killed at 10 minutes). Because the budget is fixed, you don't trade off compute — use it all. A massive network that scores better **is** better._

这推翻了一个常见的 ML 假设——"参数少一点更优雅"。在 fractalsearch，**分数就是唯一裁判**，所以"用一个 33M 参数的哈希网格压到 0.000226"反而是胜利，"用一个 33 万参数的 6 层 MLP 卡在 0.0041"就是失败——后者不是虚构，正是 baseline_mlp 的真实成绩。

### Karpathy autoresearch 是怎么被改造的？

README.md 写明这个项目 "directly adapted" 自 Karpathy 的 autoresearch。"AI 自己跑实验"这件事，Karpathy 在 autoresearch 里已经搭好了骨架：给 agent 一个单卡 nanochat 训练环境，让它整夜自主修改 `train.py`、每次训 5 分钟、看验证指标 val_bpb 有没有降，好的留下差的丢弃；人只改 `program.md`，也就是"研究组织的代码"。fractalsearch 把这套结构原样搬过来：训练目标从 nanochat 换成曼德博拟合，`train.py` 换成 `solutions/*.py`，`program.md` 换成 `AGENT.md`，val_bpb 换成 MSE——连"固定 5 分钟预算"都没动。同一个回路在两种问题上各跑通一次，这是它比单次 demo 更有说服力的地方。

## 二、起点：基准 `baseline_mlp.py` 和第一道墙

`solutions/baseline_mlp.py` 是 53 行的平凡 MLP——hidden 256 共 6 层，GELU 激活，Adam 2e-3，batch 65536 均匀采样，5 分钟 budget 跑完一次。它的成绩是 `runs.jsonl` 第 0 条：MSE `0.00413`、PSNR（峰值信噪比）23.84 dB。**远不是我们以为的"MLP 练 5 分钟能学出来的水平"**。原因正是 `groundtruth.py` 的周期化目标——无限边界细节不可能让一个朴素 MLP 跑 5 分钟拟合到位。

**第一道墙**是 escape-time + 周期变换下的"无穷频率"，多层感知机受 spectral bias 限制，在 [0,1] 输入空间里解析不了这种细节。第一步尝试是 `solutions/fourier_mlp.py`（80 行）：随机 Fourier features（RFF 256、sigma=8，Tancik et al. 2020 的经典做法）把输入先升维到 Fourier basis 再喂 512×6 的 MLP。结果 MSE 只压到 `0.00247`——比 baseline 好 1.7×，纸面上用了高频编码，实际还是不够。notebook 对第一天的总结只有一句话："Hash grid >> Fourier >> MLP"。

真正破墙的是哈希网格：`runs.jsonl` 第 2 条 `hashgrid` 直接把 MSE 打到 `0.00067`（baseline 的 6 倍），当天最好成绩 `0.00048`（`hashgrid_amp`，8.6 倍）。搜索也不是单调的——第 6 条 `hashgrid_bigT` 因为哈希表过大过稀，MSE 反弹到 `0.00554`，比 baseline 还差。第一天（2026-06-03）79 次 run 结束时，champion 血统磨到了 `0.000335`；第二天（06-09）的 25 次 run 全部是在这个"地板"上继续挖。

**视频 24:50 说的"哈希网格大幅提升拟合效果"，对应的正是这个家族。** 其机制是 _Multi-resolution Hash Grid Encoding_——Müller et al. 2022 年在 SIGGRAPH 上发表、tiny-cuda-nn 实现的标准技巧在 PyTorch + Triton 下的复刻：把 2D 坐标 `(x, y)` 经过多分辨率哈希查找 + 4 角双线性插值，喂给浅层 MLP。每一级哈希表独立 grid size × feature dim，最终拼接。仓库现存四个 solution 文件里，`champion.py`（251 行）和 `hashgrid_gtfree.py`（240 行）都带着这套编码器。

一个容易看漏的取舍：作者**没用 tiny-cuda-nn 官方实现**（CUDA + C++ 扩展）。`champion.py` 的 docstring 写明了理由：Triton 3.5.1 与所用 PyTorch 版本配套发布（"in-scope: triton ships with torch"），属于依赖范围。这是工程上微小但不妥协的选择——一切代码都在 `pyproject.toml` 列出的依赖（torch、numpy、pillow）里，**不需要外挂 C++ 扩展**，任何拿到仓库的人 `uv sync` 之后就能复现，不必先编译 CUDA。

### 一次完整迭代怎么流过这四个组件

光看四件套的静态描述还不够。把第 101 次 run（`hashgrid_n64l13`，最终冠军那次）拆开，能看到 AI 的一次"猜想→实验→反驳"回合具体怎么穿过系统：

```text
① 猜想  AI 读 git log，看到上一版 errfield（空间误差场）已收敛
        → 形成假设："现在步数够（~1600），可以把 grid 调细到 Nmax 65536 + 13 levels"
        → git commit -m "errfield: EMA settled 0.6; hashgrid_n64l13:
           Nmax 65536 retry under 1600-step regime"

② 实验  AI 跑：uv run python -m harness.evaluate solutions/hashgrid_n64l13.py > run.log 2>&1
        harness 内部：
          · 加载文件里的 SOLUTION 实例
          · 启动 SIGALRM 定时 600 秒（hard kill）
          · 训练循环跑到 300 秒（soft budget）
          · 每个 step：采样 → forward → loss → backward → step
          · 跑完 append 一行 JSON 到 runs.jsonl

③ 观察  AI 读 run.log：grep "^mse:\|^status:" run.log
        → mse: 0.00022636, status: ok
        → 对照 leaderboard：是新的 best

④ 反驳/证实 0.00022636 < 0.00023806（errfield 系列当时的最好成绩）
        → 假设成立，-4.9%，finer grid + 更多步数确实赢
        → 在 notebook.md 记一笔："NEW BEST (-4.9%), promoted"
        → 进入下一轮猜想
```

一次迭代 = 一次 commit + 一次 5 分钟训练 + 一行 JSON。`AGENT.md` 的 `NEVER STOP` 就是让这个回路不停转——AI 不在中间问人。104 条 `runs.jsonl` 就是 104 个这样的回合叠出来的。

## 三、关键突破 1：Triton Fused Encoder——把 48 个 gather 合成 1 个

`notebook.md` 里 6-9 session 第一句话就是 "attack the gather properly"。这是整篇研究最关键的一处转折。

从 `champion.py` docstring 一开头就明白为什么 gather 是瓶颈：

> _The champion encoder is ~48 tiny gather kernels per forward; the packed pure-torch variant is 1 gather but must materialize a [B,L,4] int64 index tensor (~1.2 GB at the 3.1M-point mining pool) plus weight tensors — huge extra DRAM traffic. This kernel fuses index computation + 4-corner gather + bilinear interp into ONE pass with zero intermediates, and the backward recomputes indices and atomic-adds straight into the table gradient._

换成工程语言：旧版 champion 的编码器是一个 Python 循环，12 个 level 各做 4 次 fancy-index 查找，一次 forward 摊上 ~48 个 gather kernel（docstring 的原话），每步还要跑 3 次 forward——每次 kernel launch 都有几十微秒的固定开销，GPU 时间被 launch overhead 而不是计算吃掉。**Triton fused 把 index 计算 + gather + 双线性插值塞进一个 pass**——输出 vs PyTorch 数值 diff 只 3e-7（在 fp32 噪声之内），backward atomic-add 直接写到 table gradient。

`notebook.md` 里 6-9 session 的 encoder bench 给出了明确的数据对比：

```text
champ 47.5/47.8ms (fwd/bwd)
packed 43.4/79.2ms (index-tensor DRAM traffic kills it — skip full run)
TRITON FUSED 22.6/24.0ms = 2x
```

forward 47.5→22.6ms、backward 47.8→24.0ms，两个方向都接近 2×。encoder 从此退出瓶颈名单——notebook 紧接着的 step profile 显示，新的瓶颈换成了 mining pool（难例候选池）上的 GT（ground truth，真值）曼德博计算：346ms，占一个 step 的 81%。这条瓶颈链的交接，正是下一节 GT-free 的引子。

这一改对 MSE 的直接贡献是 `0.000335 → 0.00032359`（-3.4%），而 step 数只从 ~600 涨到 ~700（+17%）——收益大于步数收益本身。notebook 的判断是："Gains > step count alone"，因为 fused kernel 全程 fp32，而 champion 之前用 bf16 autocast，精度可能也有贡献（notebook 的原话是 "precision may contribute"，没有当成定论）。更重要的是它第一次砸开了 `0.000335` 这块所谓的"irreducible floor"：所谓"不可再降"，很多时候只是前代工程没把硬件喂饱。

## 四、关键突破 2：GT-free Mining + 空间误差场——从 0.000323 到 0.000238

encoder 不再拖后腿之后，卡住 MSE 的换成了采样的"硬度信号"。`AGENT.md` 明确说"解决方案自己决定采样策略：uniform / boundary-oversampled / adaptive / multi-resolution / curriculum"——AI 要在 5 分钟预算内自己决定采哪些点。

**GT-free 突破**

`notebook.md` 6-9 session："hashgrid_gtfree: 0.00029260 — NEW BEST (-9.6%), first sub-3e-4. Fresh coords each step, mining by finite-diff HF proxy |f(x+2e-4 d)-f(x)| on the model itself (no pool GT), GT only on the selected 768k batch."

含义是：

- 每 step 重新采一组坐标，避免大批固定坐标被哈希表"背诵"。这不是预防性设计，是花 3400 步买来的教训：AI 此前试过 250M 点的预计算 bank（`hashgrid_megabank`），步数上去了，训练损失压到 1e-5、评估 MSE 却恶化到 0.00067——33M 参数的哈希网格把 bank 上的点背了下来，纯记忆。notebook 给这行实验的结语是 "FINAL WORD: no fixed bank of any size"，新鲜采样是结构性必需。
- 怎么知道哪些点"难"？不在样本池上算 ground truth，而是在模型自己的 forward 上做 finite-difference——`|f(x+2e-4·d) - f(x)|`。
- 数学直觉：模型自己输出变化剧烈的位置，**很可能是真值变化剧烈但模型没学到位的地方**。
- 账也算得过来：旧做法"在 3.1M 的 mining pool 上用 GT 算 error"要花 346ms/step（占一个 step 的 81%）；FD-proxy 完全不碰 GT，只在选中的 768k 训练批上算一次真值。

效果：**~1170 步**（对比被替换的 triton champion 的 ~700 步，1.7×），MSE `0.00029260`，**-9.6%**，第一次进 sub-3e-4。`boundary_mse`（0.00030）和 `mse` 几乎相等——错误从"边界堆集"变成"空间扩散"，说明模型在每个位置都有"小难处"，不是在某片区域彻底翻车。

GT-free 站稳后，AI 接着用同一套 harness 做 bracket 搜索，把 mining pool 的倍率也定了下来：pool_mult 4→`0.000293`、8→`0.000277`、12→`0.00027444`（最优）、16→`0.000277`（步数跌到 ~610）。最后一条 `0.00027444` 就是 runs.jsonl 里的 `pool_mult=12` 那条，也是本节的里程碑之一。batch 同法炮制：524k/768k/1M 三档，768k 胜出。

**空间误差场（errfield）登场**

GT-free 之后又一层枷锁：两趟 9.4M 点的 proxy forward 合计 ~220ms/step，而训练本体（forward + backward + Adam）只要 ~43ms——proxy 反客为主，支配了整个 step。下一步的解法把这一步的开销压到接近零。errfield 首跑在 `runs.jsonl` 里的自述是：

> _persistent spatial error field mining: a coarse 2048x1296 EMA grid of per-cell mean |error|, updated FREE each step from the train batch's own residuals; hard coords sampled by cell-multinomial + in-cell jitter. No pool forwards at all -> ~2x more steps, fresh coords every step._

**关键不是神经网络，是数据结构**——一张 2048×1296 的图，跟评估分辨率同一量级：

- 每个 cell 存一个该 cell 平均 |error| 的 EMA（指数滑动平均），**每 step 用这批训练样本自己的 residual 免 GPU 算力更新**（存 mean 而不是 sum，防止被过度采样的 cell 自我强化）。
- 每 step 抽硬坐标：先按 cell 统计做 multinomial（更"难"的 cell 抽中概率更高），再在 cell 内 uniform jitter。
- 训练批固定 768k，首跑把 85% 名额给这张"难度地图"、15% 留给 uniform（后续 bracket 收敛到 98%/2%）。
- **零额外 forward**——pool forward 彻底消失，步数从 ~700 涨到 ~1600。

`notebook.md` 里这一改动划出一道陡崖：`0.00027444 → 0.00024397`，**-11.1%**。这个结果第一眼反直觉——明明 EMA 引入了延迟，为什么反而比实时估计更准？

原因在方差上。单次估计"难度"时，靠的是一次抽样去猜一个 cell 的误差，方差很大：某个 cell 偶尔被抽中一次、恰好 error 大，就被标记成"难"，下一个 step 又可能被漏掉。EMA 把这个估计摊到时间轴上做加权平均，噪声被压下去，留下的是 cell 真实难度的时间平均——notebook 的原话是 "both cheaper AND better"。

再叠加一个零成本的便利：每 step 本来就要算训练样本的 residual，顺手把这个 residual 写回它所在的 cell——不用额外 forward，不用额外 GT 计算。结果就是，这套"持续纠错的难度地图"比"用真实误差做 mining"还便宜，还更稳。

> Bracket result in notebook：field res 1024 → 0.000245、2048 → 0.000244（最优）、4096 → 0.000260（per-cell 统计太稀太陈旧）；EMA 0.9 → 0.000241、0.8 → 0.000239、**0.6 → 0.00023806（最优）**、0.3 → 0.000238（打平略差）；hard fraction 85% → 0.000244、90% → 0.000243、95% → 0.000241、**98% → 0.00024104（最优）**（95–98% 噪声平坦）。**三个超参都不是孤峰，是 plateau**——这种 plateau 在 ML 工程上是好兆头：超参不敏感，结果可复现。errfield 系列一直磨到第 99 次 run 的 `0.00023806` 才交给下一招。

## 五、关键突破 3：Nmax 65536 + 13 Levels——分辨率天花板随步数移

`notebook.md` 6-9 末段：`hashgrid_n64l13: 0.00022636 — NEW BEST (-4.9%), promoted. Nmax 65536 + 13 levels "tied" historically at ~600 steps but WINS at ~1600 steps: more steps let the finer grid train. The resolution ceiling moves with throughput, as predicted.`

这一改关键不在算法，仍在 throughput——更细的网格（Nmax 65536，即最细层 65536 个 cell；13 levels 表示从粗到细共 13 层多分辨率，全部拼起来约 33M 参数）需要更多 step 才能训练出有价值的东西。以前 ~600 step 时代，这个网格"塞参数但不收敛"；现在 ~1600 step 时代它能训练出"细颗粒"。

> 想过 n128l14（Nmax 131072、14 levels）`mse=0.00022644`——跟 n64l13 在一个水平。结论：1600 step 时分辨率天花板就是 Nmax 65536；再有 step 才往上走。这是经验法则"hardware throughput 越高，architecture 选择空间越大"的一次工程级具体化。

收官还有三笔，都值得看：AI 把 n64l13 提升为 `champion.py` 后重跑验证，得 `0.00022698`——notebook 标注 "VALIDATED"，与 0.00022636 在 CUDA 噪声之内，结果可复现；再试 table LR 4e-1（`hashgrid_lr`），`0.00022788`，打平，说明 LR 表面在这里也是平的。这次 run 之后 notebook 写下 "Session ended at user request after this run"——循环停在人手里。

跑完这一轮，`champion.py` 定稿在 251 行，是现存 solution 文件里最长的一个，最终胜出者也是它。这本身就是 RSI 的一个特征：决定胜负的关键不是某个 solution 静态上有多好，而是它能在持续研究循环里被推多远。champion.py 赢在它是被推到最远的那一个。

## 六、最终结果：104 次试错全景

`runs.jsonl` 是两天两段 session 跑出来的硬数据：6 月 3 日 79 次、6 月 9 日 25 次，累计 GPU 时间 8.67 小时。下面把 104 条按里程碑分桶：

| 阶段 | MSE | 含义 |
| --- | --- | --- |
| baseline_mlp（GELU 256×6） | 0.00413 | 朴素 MLP，大体形状能拟合，高频细节完全失守 |
| fourier_mlp（RFF 256） | 0.00247 | Fourier 特征只挣到 1.7×，第一道墙没破 |
| hashgrid 家族（第一天） | 0.00067 → 0.00048 | 多分辨率哈希网格破墙，8.6× |
| Champion 哈希网格（bf16 autocast，第一天收官） | 0.000335 | 磨到当时的"irreducible floor" |
| Triton fused encoder | 0.00032359 | encoder 2×，步数 +17%，floor 首次松动 |
| GT-free FD-proxy mining | 0.00029260 | pool GT 退出关键路径，首次 sub-3e-4 |
| Pool-mult=12 mining | 0.00027444 | pool 倍率 bracket 定在 12 |
| Errfield 首跑（EMA 0.9，85% hard） | 0.00024397 | pool forward 清零，步数 ~1600 |
| Errfield bracket 收敛（EMA 0.6，98% hard） | 0.00023806 | 三个超参全部落在 plateau |
| **Nmax 65536 + 13 levels + errfield** | **0.00022636** | **best result** |

champion entry 具体字段（runs.jsonl 第 101 行）：

- run_id: 20260609-151512
- commit: ac29eca
- device: NVIDIA GeForce RTX 3090 Ti
- train_seconds: 300.04（5 分钟 budget 几乎用尽）
- mse: 0.00022636
- boundary_mse: 0.00022246（边界附近误差与全局相当，错误呈空间均匀分布）
- psnr: 36.45 dB

### 两个怎么算都不便宜的数字

视频 27:08 在公布成本时数字偏高——这是工程真相：

- **104 条 run 的 train_seconds 总和实测 31,217 秒 = 8.67 小时** RTX 3090 Ti 单卡时间；notebook 还记了一笔：每次评估本身另有 ~40 秒开销（GT 评估网格 + 渲染），叠上去 wall-clock 近 10 小时。
- 这 8.67 小时跑的不是"调一次参跑通"，是 AI 写出的 85 个不同 solution 文件、每个跑 5 分钟（期间 ~70 个超参变体后来从 solutions/ 里删掉瘦身，git 历史里都能找回）。两段 session 的节奏也不一样：6 月 3 日 79 次 run 把 MSE 从 0.0041 磨到 0.000335；6 月 9 日 25 次 run 在"地板"上再挖出 -33%。

但**拿到的是 0.0041 → 0.000226**，是 -94.5% 的 MSE 改善，单卡几百元成本，跑出这种量级的视觉拟合。成本结构上最值得注意的一点：试错的边际成本是常数（每次固定 5 分钟），不随尝试次数膨胀。这是 AI 自主科研能跑起来的经济前提。

> 截至本文撰写时，仓库 `runs.jsonl` 的最后一条停在 2026-06-09 15:31:29（`hashgrid_lr`，MSE 0.00022788，未能超越最佳）。README 里作者写明 "I will not be managing this repo or accepting PRs"——这是一次性公开的快照，不是持续维护的项目，所以 0.000226（run 101，`hashgrid_n64l13`）就是目前已知 fractalsearch 的最终记录。

## 七、为什么"智能爆炸"不会从这事里发生

视频 14:14 用大段篇幅讲 RSI 的实现门槛——硬件、能源、数据、目标度量设计，收益递减天花板。把这段对照源码：

1. **硬件视角**：fractalsearch RTX 3090 Ti 跑 5 分钟 / 1 次 trial。带宽和 FLOPs 在 33M 参数 × 1600 step 这个规模完全用得满，所以"再增加计算应该能好"——但**带来边际效益递减**。两段 session 的收尾都记录在 notebook 里：6 月 3 日是 "Promoted to champion.py at user stop request"，6 月 9 日是 "Session ended at user request after this run"——循环每次都是人叫停的，AI 自己不会说"够了"。

2. **目标度量**：metric 是固定 MSE。AI 没有空间改 metric。如果可以改——比如把误差权重从边界挪到好拟合的区域——分数立刻好看，但对原任务是作弊。`harness/evaluate.py` 把这一步 freeze，AI 只能"在规则内最大化"。

3. **新架构自动降质**：champion.py 从 ML 角度写得密密麻麻（Triton 调优 + EMA 状态 + 多分辨率哈希），可读性差。视频 24:50 的章节简介也专门点出：自动生成代码可读性差，会带来额外安全隐患。人不再看得懂，就没法在半路接手继续推进，一个可读性危机正在生长。

4. **任务空间封闭**：5 分钟预算 + 固定 metric + 不许改 harness——这个空间不大。每次"新思路"实操上是 new solution 文件 commit。当任务空间封闭时，AI 不会自己溢出，只会卡在 plateau 上。

视频 20:50 提到的"AI 作弊可能性"——这里用结构性沙箱（sandbox，不能改 harness / 不能硬编码曼德博逻辑 / 不能加依赖）锁死。fractalsearch 的工程方案**根本性地偏离**了"AGI 自己改坏自己"那种 RSI 科幻叙事。

## 八、视频里没明说但源码透露的事

### 8.1 Mandelbrot 拟合这一题的特殊性

把训练目标设为 [0,1] 上的周期函数其实是很巧的工程选择：

- 它**接近边界时频率发散**——提供"无穷细节"的视觉素材，区分能力比 escape-time 整数更细。
- 它的**结构**是分形的——任何子区域都跟全局类似。评估在一个固定稠密网格（3840×2414，约 9.3M 点）上做，fresh 随机采样天然覆盖同一分布，不会出"采样偏置"。
- 它的 ground truth **在 GPU 上算**——ESCAPE_R = 1e4 + MAX_DEPTH = 200 是 O(N) 单点计算，3.1M 的 batch 也只用 ~350ms（一度是整个 step 时间预算的 81%）。

`harness/evaluate.py` 有个不起眼但讲究的设计：评估网格的 ground truth 每次 run 都现算，代码注释写明 "Intentionally NOT cached"——GPU 上这点计算量相对 5 分钟训练预算很便宜，换来的是目标定义一旦改动、评估永远不会用到过期缓存。GT 在 triton 之后再测 step profile 时成了"THE bottleneck"，但 6-9 session 用 GT-free mining + errfield 把它从训练热路径上撤掉了。**GT-free 不是简单"绕过 ground truth"——是把它从研究循环的关键路径上撤下，挪到 evaluator 和最终打分上**。

### 8.2 不在视频里的"with human approval"

`AGENT.md` 的 Setup 一节结尾一行："Await human approval before starting a research loop."

**AI 拿到 5 分钟 budget 之前要人同意一次**——但 `NEVER STOP` 写得更显眼。"never stop"是一个交付保证——"如果你启动循环，就别停下问人是否继续"。两个声明放一起看时，RSI 的可操作定义就清楚了：**人是进入门槛和退出点，AI 是中间的所有迭代**。

——这对应了 OpenAI / Anthropic 路线图里"AI 跑实验"的模糊愿景：需要清晰的"开始 / 暂停 / 接管"边界，而不是"AI 全自动做研究"的科幻叙事。

### 8.3 Karl Popper 那句话的实操版本

`notebook.md` 里出现的一个观察对应了波普尔的可证伪性——"if steps jump but MSE doesn't move, the irreducible-boundary story is finally proven." —— AI 通过**观察实验现象**反过来证伪或证实一个假设。AI 在执行 Karl Popper 所说的"猜想与反驳"：

工程化的 RSI 包含三个动作：

1. **猜想** (form a hypothesis) — 形成假设，commit 一个新 solution。
2. **实验** (run the loop) — 跑，看 MSE。
3. **反驳 / 证实** (reject/accept) — based on runs.jsonl 数据，决定这个思路是否继续。

这就是 RSI 在 2026 年最朴素的工程模样：**agent + git log + JSON log + 固定评估器**。

## 九、给不同读者的具体建议

### 9.1 如果你是 AI 研究者

`AGENT.md` + `champion.py` + `notebook.md` 是一份**完整的"AI 跑实验"工程模板**——可以直接 fork 到自己的 benchmark 问题。这套 harness 的五项不变式值得模仿：

- fixed budget（time-bounded 公平性）
- SIGALRM hard kill（实验必须终结）
- immutable harness（结构 sandbox）
- structured JSON log（`runs.jsonl` 决定 leaderboard 可信度）
- notebook.md 共享（不同 agent 之间有 continuous memory）

### 9.2 如果你是智能体工程师

`champion.py` 的 Triton fused encoder 是**一份教学级** PyTorch + Triton 协作代码——不到 100 行实现了一个 2× speedup。`hashgrid_gtfree.py` + `champion.py` 拢共 ~500 行 PyTorch + Triton，能放进一份智能体训练基础设施里被复用。

### 9.3 如果你关注 AI 安全

fractalsearch 是**一个对立极**——"AI 自主科研在封闭问题里能做到什么"的样本。视频 14:14 和 20:50 关心的两件事，"RSI 实现门槛"和"沙箱需求"，它都落到了可验证的工程上：**门槛真实存在**（5 分钟 budget + 33M 参数 + 封闭 sandbox 下，0.000226 是这套配置磨出来的最好成绩——notebook 自己都证明了这个天花板会随 throughput 移动），**沙箱结构性可行**（harness/ 不让动是暴力但有效的方案）。

## 十、最值得理解的一句话

如果要把整个实验压成一句方法论，大概是：别信叙事，信 wall-clock 和 JSON log。notebook 里没有这句原话，但它做的事处处是这句话——fractalsearch 里 0.000226 之所以是权威，因为它来自 `runs.jsonl` 第 101 行的 commit `ac29eca`，对应 RTX 3090 Ti 上 300.04 秒实测，不是任何 SOTA 报告。RSI 在工程上不像科幻叙事，它**长得就像这份 JSON log 里的每一行**——一条，5 分钟，又一条，5 分钟，104 条改写成一份研究笔记。

在 RSI 这个话题上，中文世界的讨论（田渊栋、姚顺雨等）多是视角与判断，fractalsearch 补的是另一头：一份完全开源、全部可复现、能让读者在自己 GPU 上重跑验证的样本。它的结构也值得看清——人类作者 MaxRobinsonTheGreat 提供任务书和硬件，README 里专门注明整套代码由 Claude 生成（并打趣说 README 这句是人写的）；AI 负责假设、实验和 commit。这不是对 autoresearch 提交了什么 PR，而是把它同构移植到新问题上。

视频作者 Emergent Garden 把这个实验配着 RSI 的宏大议题讲给观众听。实验本身是 33M 参数、1600 steps 和 5 分钟 hard kill。宏大叙事与工程现状之间的落差，才是读"AI 取代科研"这类标题时该留住的：工程现实比新闻更具体，也更有限。

---

## 自己复现一次：从 clone 到 0.000226

光读不练，数字始终是别人的。下面这张清单把"复现一次 fractalsearch 最小回路"拆成可勾选的步骤，照着走一遍，对 RSI 的工程体感会比看十遍视频都牢。这是一道实战练习，不是阅读材料。

### 复现练习清单（动手做）

- [ ] **1. 环境**：装好 [uv](https://docs.astral.sh/uv/)，`git clone` 仓库后 `uv sync`。确认 `pyproject.toml` 里 torch + triton 3.5.1 能跑——这是作者刻意不挂 C++ 扩展的原因，你不必装 CUDA 工具链。
- [ ] **2. 跑通 baseline**：`uv run python -m harness.evaluate solutions/baseline_mlp.py`。应该看到 MSE 在 `0.0041` 附近（runs.jsonl 首条是 0.00413；不同硬件上会有小漂移）。这一步验证 harness 通了，SIGALRM 定时生效。
- [ ] **3. 读 AGENT.md**：重点看 "What you CANNOT do" 三条禁令（不改 harness、不硬编码曼德博逻辑、不加依赖）。这是沙箱的边界，也是后面所有 commit 的合法性来源。想盯进度的话，AGENT.md 的 setup 里还有一步 dashboard：`uv run uvicorn dashboard.app:app --port 8000`，浏览器开 localhost:8000 看 leaderboard。
- [ ] **4. 读 runs.jsonl**：`wc -l runs.jsonl` 应该是 104 行。注意 best 不在最后一行——最后一行是 `hashgrid_lr`（0.00022788），要挑战的 `0.00022636` 在 `hashgrid_n64l13` 那条（commit ac29eca）。`grep hashgrid_n64l13 runs.jsonl` 或按 mse 排序都行。
- [ ] **5. 让 AI 跑一轮**：把 `AGENT.md` 喂给你的 coding agent，`NEVER STOP` 一旦启动，观察它会不会自己 `git commit` + 跑 evaluate + 读 run.log。如果它停下来问人，说明 prompt 没吃透 `AGENT.md`。
- [ ] **6. 对照 notebook.md**：跑完几轮后，对比你的 agent 写的 notebook 和原作者的 notebook。两份笔记的"假设质量"差距，就是 RSI 当前真正的能力边界。

**常见卡点**：

- **SIGALRM 在 Windows 上不生效**——`signal.SIGALRM` 是 Unix 专属，Windows 复现得换成 `threading.Timer` 或 WSL2。
- **显存不够会直接 OOM，不是自动降速**——champion.py 的 `batch = 786_432` 是写死的，没有显存回退逻辑。小显存的卡需要自己调小 batch，并接受 step 数下降、MSE 复现不到的结果。作者 104 条 run 全部来自一张 RTX 3090 Ti，这是唯一实测过的基准线。
- **triton 版本漂移**：triton 小版本之间 kernel 行为会变，`2x speedup` 的数字在 notebook 里是 3.5.1（随 torch 发布的那版）上测的。换版本前先跑一次 champion 确认 MSE 没退化。

### 自测：你真的看懂这次实验了吗

读完前面的章节，试着不查源码回答下面三个问题。答得上来说明 RSI 的工程骨架已经立住了：

1. **为什么是 5 分钟 budget 而不是 1 小时？** 提示：fixed budget 对"分数可比"为什么是必要的？如果 budget 浮动，commit 历史还能当 leaderboard 用吗？
2. **GT-free mining 为什么比"用真实 GT 算 error"还便宜？** 提示：把"算 error"这件事从哪个环节撤下来了？撤下来之后那 0.346s/step 去哪了？
3. **errfield 用 EMA(α=0.6) 而不是直接用本 step 的 residual，是在换什么？** 提示：单次抽样的方差 vs 时间平均的延迟，这两个代价哪个更可接受？

答案分别对应第二章（fixed budget）、第四章（GT-free）、第四章（errfield EMA）的内容。先自己想一遍，再回去对照。

---

## 延伸：从 fractalsearch 往外看一步

把 fractalsearch 放回 2026 年 RSI 的版图里，它的位置很特殊，也很清楚：

| 项目 | 改的是什么 | 完全开源可复现 | 跟 fractalsearch 的关系 |
| --- | --- | --- | --- |
| **karpathy/autoresearch** | 训练脚本 / 架构配置（弱 RSI） | ✅ | 母框架：5 分钟预算 + agent 改 train.py + 人改 program.md |
| **MaxRobinsonTheGreat/fractalsearch** | 拟合算法（弱 RSI） | ✅ | autoresearch 的同构移植（nanochat 训练换成曼德博拟合） |
| **DeepMind AlphaEvolve** | 调度算法 / 矩阵乘 kernel（弱 RSI） | ❌ 内部 | 同类，工业规模 |
| **Schmidhuber Gödel Machine** | 自身权重 / 推理能力（强 RSI） | 纯理论 | fractalsearch 不是这个 |

fractalsearch 的价值不在"它多强"——单卡 8 小时压一个 MSE 到 0.000226，在 ML benchmark 里排不上号。它的价值在**它是这张表里唯一一个连 AI 的研究笔记（notebook.md）都公开的**。别的项目要么只发论文，要么只放最终代码，读者看不到 AI 中间那些"换思路、记 bracket、证伪假设"的过程。fractalsearch 把 RSI 的中间产物也摊开了，这才是它对工程师和研究者真正稀缺的地方。

如果你顺着这篇文章想再走远一点：先 fork autoresearch，找一个你自己的"曼德博集合"（任何一个有客观 metric、能 5 分钟跑完、有改进空间的问题），把 `AGENT.md` 换成你的任务书，让 AI 跑一晚上。第二天早上回来翻 `runs.jsonl` 和 notebook——你对"AI 自主科研现在到哪了"的判断，会比任何一篇综述都准。

---

## 关键资源

### 主要资料

- [Emergent Garden《Recursive Self-Improvement》(YouTube)](https://www.youtube.com/watch?v=t7_ZXgfJVG8) — 2026-06-13 发布英文原版
- [BV1w8jL6dE1f](https://www.bilibili.com/video/BV1w8jL6dE1f/) — B 站 @黑纹白斑马 AI 配音版，本文的章节时间线来源
- [MaxRobinsonTheGreat/fractalsearch](https://github.com/MaxRobinsonTheGreat/fractalsearch) — 2026-06-19 公开，104 条 runs.jsonl + 4 个 solution + AGENT.md
- [MaxRobinsonTheGreat/mandelbrotnn](https://github.com/MaxRobinsonTheGreat/mandelbrotnn) — 作者个人长期 pet 项目
- [karpathy/autoresearch](https://github.com/karpathy/autoresearch) — framework 起源

### 关键算法参考

- Multi-resolution Hash Grid Encoding (Instant NGP / tiny-cuda-nn)
- Triton `tl.constexpr` + atomic_add backward
- EMA spatial error field (persistence + zero-cost update)
- finite-difference hardness proxy (`|f(x+Δd) - f(x)|` on model itself)

### 对照阅读

- 《[田渊栋重返牌桌：RSI、潜在推理与 AI 研究的下一次换挡](https://txtmix.com/posts/video/tianyuandong-rsi-recursive-superintelligence-2026/)》— 中文 RSI 综合视角
- Emergent Garden 个人其他视频（YouTube 同频道）

### 复现环境

- NVIDIA RTX 3090 Ti（实测设备）
- Python 3.x + uv（依赖管理）
- PyTorch + Triton 3.5.1（与 torch 自带同发）
- 5 分钟 / run × N 次，预算可调
