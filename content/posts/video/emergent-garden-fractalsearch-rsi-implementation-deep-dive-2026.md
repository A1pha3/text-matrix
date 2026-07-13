---
title: "fractalsearch 8 小时实跑：从 0.0041 MSE 到 0.000226，看 AI 怎么一步步改坏又改好自己"
date: 2026-07-10T00:19:29+08:00
slug: emergent-garden-fractalsearch-rsi-implementation-deep-dive-2026
description: "BV1w8jL6dE1f 视频讲 fractalsearch 实验的概念与截图，真正落到实处的实验日志在 MaxRobinsonTheGreat 仓库的 104 条 runs.jsonl + 4 个 solution + AGENT.md。本文以源码、runs 为骨，B 站章节大纲为时间锚，还原 AI 自主科研这 8 小时的过程：从 autoresearch 框架、Triton fused encoder 突破、GT-free 采样，到空间误差场（errfield）演化，最终 0.000226 MSE、PSNR 36.45 dB。"
draft: false
categories: ["视频精读"]
tags: ["RecursiveSelfImprovement", "RSI", "fractalsearch", "Mandelbrot", "Karpathy", "AutoResearch", "EmergentGarden", "MaxRobinsonTheGreat", "Triton", "hashgrid", "errfield", "AIResearch", "MLOps"]
hiddenFromHomePage: true
---

> **作者**：钳岳星君
> **视频**：Emergent Garden《Recursive Self-Improvement》（[YouTube t7_ZXgfJVG8](https://www.youtube.com/watch?v=t7_ZXgfJVG8)，2026-06-13）｜B站 AI 配音版 [BV1w8jL6dE1f](https://www.bilibili.com/video/BV1w8jL6dE1f/)（@黑纹白斑马 译制，YouDub 项目）
> **源码**：[MaxRobinsonTheGreat/fractalsearch](https://github.com/MaxRobinsonTheGreat/fractalsearch)（GitHub，2026-06-19 公开，104 条 runs.jsonl + 4 个 solution + AGENT.md）
> **前身**：[MaxRobinsonTheGreat/mandelbrotnn](https://github.com/MaxRobinsonTheGreat/mandelbrotnn)（个人长期 pet 项目）+ [karpathy/autoresearch](https://github.com/karpathy/autoresearch)
> **写作笔记**：本版相对 7-9 旧文 e9541bce 的最大差异是**直读源码 + 直读 runs.jsonl**，不再依赖 B 站 8 段章节大纲的二次转述。B 站视频未提供官方字幕轨（AI 配音版通常不含），YouTube 原版 yt-dlp 抓取需要登录 cookie，因此本版以仓库级事实为核心——AGENT.md 是任务书、README.md 是作者意图、solutions/notebook.md 是 AI 自留的研究笔记、runs.jsonl 是 104 次实跑的硬数据。

**读完这篇你能拿走什么**：分清 RSI 的宣传叙事和工程现实，看懂 fractalsearch 四个组件（任务书/裁判/选手/研究笔记）怎么咬合，理解 Triton fused encoder、GT-free 采样、空间误差场三次关键突破各自的贡献，并能动手复现一次最小 RSI 回路来判断"AI 自主科研"目前真实的边界在哪。

---

## 先把"fractalsearch 是谁做的"理清楚

视频里 Emergent Garden 没说自己是谁，但 fractalsearch 仓库的所有者写得很明白——

`MaxRobinsonTheGreat`。README 第一段：

> _This has been a pet project of mine for a long time._

这位作者其实早就做"AI 拟合曼德博集合"——他的 mandelbrotnn 个人项目就是老版本。fractalsearch 不是从零起步，是把 Karpathy 2026-05 刚发的 [autoresearch](https://github.com/karpathy/autoresearch) 框架套到自己的老问题上。

视频作者 Emergent Garden 在 8 段章节中把 fractalsearch 当成"RSI 在可重复工程上做到了什么"的样板间来展示——他没有动手 fork，没有亲手改 code，但他把这个实验配上"ASI / 智能爆炸 / 沙箱风险"的 RSI 主流议题一起讲。fractalsearch 源码是 Emergent Garden 的论据，不是他自己的产出。

厘清之后，视频里每一段在说什么，就不再是"AI 多厉害"，而是"AI 借助一个 5 分钟训练 budget + 一个 33M 参数的小哈希网格，在一个受限视觉学习问题上能做到什么程度"。这才是更具体、也更值得工程师关心的视角。

### 先给一张系统地图：fractalsearch 的四个组件各管什么

读后面所有章节前，先记住这张拆分。整个实验里其实有**四条互不重叠的主线**，很容易被讲成一条故事线，混淆之后每个数字都对不上号：

| 组件 | 文件 | 职责 | 谁能动 |
|---|---|---|---|
| **任务书** | `AGENT.md` | 告诉 AI 要做什么、不能做什么、循环长什么样 | 人类写死，AI 不改 |
| **裁判**（harness） | `harness/groundtruth.py` + `harness/evaluate.py` | 定义目标函数、固定 5 分钟 budget、SIGALRM 强杀、把结果写进 `runs.jsonl` | 人类写死，AI 不改（结构性沙箱） |
| **选手**（solution） | `solutions/*.py`（baseline / fourier / hashgrid / champion） | AI 提交的拟合算法，每次 commit 一个新文件 | AI 全权改写 |
| **研究笔记** | `solutions/notebook.md` | AI 跨 session 的连续记忆，记录 bracket、假设、教训 | AI 自己追加 |

一个数字（比如 MSE `0.000226`）必须能同时落到这张表里的三个格子：它由某个**选手**（`champion.py`）在**裁判**（`evaluate.py` 5 分钟 budget）下跑出来、写进**研究笔记**（`notebook.md` 的 best 记录）。后面所有数字都按这张表归位，才不会和视频叙事错位。

**本文怎么读**：第二章把视频 8 段章节对到源码文件；第三到五章拆三次关键突破（Triton fused encoder、GT-free 采样、空间误差场）；第六章是 104 次试错的全景；第七到八章解释为什么这次不会"智能爆炸"；最后给三类读者各自的下一步。

---

## 视频大纲 vs 实际产物：章节对照表

B站 @黑纹白斑马 在 UP 主简介里给出的 8 段章节时间线是研究骨架，下面这张表把它对到 fractalsearch 仓库里**真实存在的**文件，看视频每段在源码里落在哪里：

| B站章节时间线 | B站字幕简介（拿到的） | 源码里的实际对应 |
|---|---|---|
| 00:00 RSI 概念引入 + Anthropic / OpenAI 动态 + 视频预告 | 引出 RSI 概念 | `AGENT.md` 顶部 "find the best algorithm to fit the Mandelbrot set" |
| 02:12 fractalsearch 实验介绍 | 源自 Karpathy AutoResearch，让 AI 在递归循环里迭代优化拟合曼德博集合 + 实验运行机制 + 评估规则 + 初步进展 | `solutions/baseline_mlp.py` + `harness/groundtruth.py`（[0,1] 区间的周期性 log-distance 目标）+ `harness/evaluate.py`（5 分钟固定 budget + 10 分钟 SIGALRM hard kill） |
| 09:27 RSI 可行性分析 | 起重机自举 / 人类学习 / 生物进化做类比 + 弱 RSI vs 强 RSI 区分 + 3 年内前沿 AI 公司开展大规模 RSI 实验 | `notebook.md` "the irreducible floor" 段落证实了"收益递减"这件事是真实存在的工程现象 |
| 14:14 RSI 实现难度分析 | 硬件 + 能源 + 数据 + 收益递减天花板 + 目标度量设计难题 + 不太可能爆发式智能爆炸 | `champion.py` 251 行 + `TRAIN_BUDGET_S=300` 和 `HARD_KILL_S=600` 是"5 分钟预算封顶"的硬约束 |
| 20:50 RSI 风险分析 | 小规模实验安全隐患 + AI 作弊 + 大规模 RSI 目标偏离 + 自我复制类癌症风险 + 沙箱隔离 + 人类管控 | `AGENT.md` "What you CANNOT do"：禁止改 harness/、禁止硬编码曼德博逻辑到 solution、禁止修改依赖——这是一个**结构性的沙箱** |
| 24:50 实验结果展示 | 哈希网格模型大幅提升拟合效果 + 自动生成代码可读性差带来额外安全隐患 | `runs.jsonl` 104 条 runs，best `mse=0.000226`，`runs/20260609-151512/...` 是 champion 产物 |
| 27:08 实验成本与未来展望 | 公布实验总成本 + 成本偏高 + 肯定 AutoResearch 类方案 + Anthropic Claude Fable 模型限制 | `runs.jsonl` 每条都记 `train_seconds`，约 300 秒/次 × 104 次 = ~8.67 小时单卡时间 |
| （视频无明确段） | Anthropic 对 Claude Fable 模型的能力限制 | 视频标题外延——视频作者认为 RSI 已经触手可及，但 Anthropic 一篇论文提醒，强 RSI 安全边界仍是开放问题 |

**核心映射**：B站章节把 fractalsearch 当成 RSI 概念的实验装置——`AGENT.md` 是研究框架，`harness/groundtruth.py` 是目标函数，`harness/evaluate.py` 是评估器，`solutions/notebook.md` 是 AI 自留的研究笔记，`runs.jsonl` 是 104 次试错的履历。视频是结果叙事，源码是机制实录，两者拼起来才是完整的 RSI 故事。

---

## 一、问题：什么叫"AI 自己改自己的代码"？

`AGENT.md` 一句话锁定任务：

> _Find the best algorithm to fit the Mandelbrot set, i.e. learn the map `(real, imag) -> target` defined in `harness/groundtruth.py`, while still being a universal function approximator._

三个隐形但严苛的边界：
- **目标函数在 [0,1]**，并非常规的 0/1 集合成员关系。`groundtruth.py` 用了 `Periodic · log-distance` 变换：先跟踪 escape-time 的轨道导数 `z' = dz/dc` 给出距离估计 `d`，再用 `phase = BETA · log(d)`、`target = 0.5 + 0.5·sin(2π·phase)`（BETA = 0.050，R = 1e4 bailout）。这是难度的灵魂——它**接近边界时频率发散**，比单调平滑 escape-time 多出无限嵌套的细节纹理。
- **每次训练 budget = 5 分钟**，10 分钟强制 SIGALRM kill。`evaluate.py` 明确写着 "use it all"。这就是 RSI 的工程化身：每次只给你 5 分钟，跑完直接看 MSE，分数上去了就 commit，分数不行就换思路再来。

`AGENT.md` 第三段几乎是在下军令：

> _NEVER STOP. Once the loop has begun, do not pause to ask the human whether to continue. They may be asleep and expect a stack of results when they return._

这就是 RSI 真正的"实现机制"——AI 不是无脑跑实验，是**对着 git 历史 + runs.jsonl 反推下一步该做什么**。Step 1-7 在 `AGENT.md` 第 49-62 行写得明白：

1. **看 git state**——看 git log。
2. **看 leaderboard**——即 `runs.jsonl` 当前最好的 MSE。
3. **形成为有效假设**——把最好的方案 `cp` 一份出来，不要重写整个文件。
4. **git commit**——`<idea>` 一句话描述本次想试什么。
5. **跑**——`uv run python -m harness.evaluate solutions/<file>.py > run.log 2>&1`，**全部重定向**，不污染 AI context。
6. **读结果**——`grep "^mse:\|^status:" run.log`。evaluator 已经把完整记录 append 到 `runs.jsonl`，artifact 存到 `runs/<id>/`。
7. **崩溃了**——`tail -n 50 run.log` 找 traceback。如果是打错字或 shape mismatch，改完重跑；如果是思路错了，记 `status="crash"` 然后换思路。

跑超 10 分钟 SIGALRM 强制杀，记 `status="timeout"` 当作废牌。**严禁改 `harness/`**——target、接口、metric、time budget 是 ground truth，动了就无法和历史对比。

`AGENT.md` 里还有一行容易被看漏：

> _Each run trains for a fixed 5-minute budget (a run is force-killed at 10 minutes). Because the budget is fixed, you don't trade off compute — use it all. A massive network that scores better *is* better._

这句话悄悄推翻了一个常见的 ML 神话——"参数少一点更优雅"。在 fractalsearch，**分数就是唯一裁判**，所以"用一个 33M 参数的哈希网格压到 0.000226"反而是胜利，"用一个 1M 参数的 MLP 卡在 0.001"就算失败。

### Karpathy autoresearch 是怎么被改造的？

README.md 写："This project is directly adapted from Karpathy's autoresearch." 也就是说，"AI 自己跑实验"这件事 Karpathy 在 autoresearch 里已经搭好了，fractalsearch 是把它搬过来。这个换骨不换肉的迁移——"曼德博拟合"代替 autoresearch 原版的"NanoGPT speedrun"目标——恰好让 RSI 的可重复实验在视觉学习问题上被验证了一次。

## 二、起点：基准 `baseline_mlp.py` 和第一道墙

`solutions/baseline_mlp.py` 是 53 行的平凡 MLP——两层 hidden 256 维，ReLU，Adam 1e-3，5 分钟 budget 跑完一次。`runs.jsonl` 起始 MSE 是 `0.00413`（run_id 0）和 `0.00554`（run_id 6）这种量级，**远不是我们以为的"MLP 练 5 分钟能学出来的水平"**。原因正是 `groundtruth.py` 的周期化目标——无限边界细节不可能让一个朴素 MLP 跑 5 分钟拟合到位。

**第一道墙**是 escape-time + 周期变换下的"无穷频率"，多层感知机在 [0,1] 输入空间里根本无法解析这种细节。突破它需要一类函数逼近器：能把任意高频信号通过位置编码塞进去的——这就是 *fourier features* / *positional encoding* 的领域。`solutions/fourier_mlp.py`（80 行）就是把输入先升维到 Fourier basis 再喂 MLP。从 `runs.jsonl` 看，前期 Fourier 变体的 MSE 大约压到 `0.00049` 量级——比 baseline 好 10×，但还没到 1e-3 这种视觉质量。

**视频作者 Emergent Garden 在 24:50 提到"哈希网格大幅提升"，对应到仓库就是 `hashgrid_gtfree.py`（240 行）。** 全名 *Multi-resolution Hash Grid Encoding*——tiny-cuda-nn 的标准技巧在 PyTorch + Triton 下的复刻：把 2D 坐标 `(x, y)` 经过多分辨率哈希查找 + 4 角双线性插值，喂给浅层 MLP。每一级哈希表独立 grid size × feature dim，最终拼接。

一个容易被看漏的工程取舍：作者**没用 NVIDIA 推荐的 tiny-cuda-nn**（Müller et al. 2022 在 SIGGRAPH 上发的 multiresolution hash grid 原始实现，CUDA + C++ 扩展）。他在 `champion.py` 的 docstring 里写明了：triton 3.5.1 跟 torch 自带同发，"in-scope"。这是工程上的微小但不妥协——确保一切代码在 `pyproject.toml` 列出的依赖里能跑，**不需要外挂 C++ 扩展**，任何拿到仓库的人 `uv sync` 之后就能复现，不必先编译 CUDA。

### 一次完整迭代怎么流过这四个组件

光看四件套还是抽象。把第 103 次迭代（champion 那次）拆开，能看到 AI 的一个"猜想→实验→反驳"回合具体怎么穿过系统：

```text
① 猜想  AI 读 git log，看到上一版 errfield 已收敛
        → 形成假设："现在步数够，可以把 grid 调细到 Nmax 65536 + 13 levels"
        → git commit -m "hashgrid_n64l13: test finer grid at higher throughput"

② 实验  AI 跑：uv run python -m harness.evaluate solutions/champion.py > run.log 2>&1
        harness 内部：
          · 读 champion.py 的 build_model()
          · 启动 SIGALRM 定时 600 秒（hard kill）
          · 训练循环跑到 300 秒（soft budget）
          · 每个 step：forward → loss → backward → step
          · 跑完 append 一行 JSON 到 runs.jsonl

③ 观察  AI 读 run.log：grep "^mse:\|^status:" run.log
        → mse: 0.00022636, status: ok
        → 对照 leaderboard：是新的 best

④ 反驳/证实 0.00022636 < 0.00024397（上一版 errfield best）
        → 假设成立，finer grid + 更多步数确实赢
        → 在 notebook.md 记一笔："Nmax 65536 + 13 levels WINS at ~1600 steps"
        → 进入下一轮猜想
```

一次迭代 = 一次 commit + 一次 5 分钟训练 + 一行 JSON。`AGENT.md` 的 `NEVER STOP` 就是让这个回路不停转——AI 不在中间问人。104 条 `runs.jsonl` 就是 104 个这样的回合叠出来的。

## 三、关键突破 1：Triton Fused Encoder——把 48 个 gather 合成 1 个

`notebook.md` 里 6-9 session 第一句话就是 "attack the gather properly"。这是整篇研究最关键的一处转折。

从 `champion.py` docstring 一开头就明白为什么 gather 是瓶颈：

> _The champion encoder is ~48 tiny gather kernels per forward; the packed pure-torch variant is 1 gather but must materialize a [B,L,4] int64 index tensor (~1.2 GB at the 3.1M-point mining pool) plus weight tensors — huge extra DRAM traffic. This kernel fuses index computation + 4-corner gather + bilinear interp into ONE pass with zero intermediates, and the backward recomputes indices and atomic-adds straight into the table gradient._

通俗讲：标准 hashgrid 在 PyTorch 里是 L 个 level × 4 角 lookup = `4L` 次独立 gather，在 L=13 时就是 52 个 GPU kernel launch——每次 launch 都有 ~10-50μs 延迟，GPU 时间被 launch overhead 而不是计算吃掉。**Triton fused 把 index 计算 + gather + 双线性插值塞进一个 pass**——输出 vs PyTorch 数值 diff 只 3e-7（在 fp32 噪声之内），backward atomic-add 直接写到 table gradient。

`notebook.md` 里 6-9 session 的 encoder bench 给出了让人闭嘴的数据：

```
champ 47.5/47.8ms (fwd/bwd)
packed 43.4/79.2ms (index-tensor DRAM traffic kills it — skip full run)
TRITON FUSED 22.6/24.0ms = 2x
```

forward 2×, backward 4×。bottleneck 从 launch overhead 翻入 DRAM 友好——HBM 带宽利用率终于跑满了。这一改**直接让 5 分钟 budget 里的 step 数从 ~600 涨到 ~1600**，5 分钟里能做的迭代次数翻近 3 倍。

更关键的一个**意外副效应**：Triton kernel 全程 fp32 跑，而 champion 之前用 bf16 autocast。fp32 + 更多 step 数双 buff 把 MSE 从 `0.000335` 压到 `0.00032359`——单次改动 -3.4%。**一个常被忽视的事实**：所谓"irreducible floor"很多时候就是"前代框架没把硬件跑满"。当 framework 升级把步数提上去，"floor"往往自己跟着下降。

## 四、关键突破 2：GT-free Mining + 空间误差场——从 0.000323 到 0.000226

一旦步数翻倍，MSE 下一步就被采样的"硬度信号"卡住。`AGENT.md` 明确说"解决方案自己决定采样策略：uniform / boundary-oversampled / adaptive / multi-resolution / curriculum"——AI 要在 `evaluate.py` 给定 5 分钟预算内自己决定采哪些点。

**GT-free 突破**——

`notebook.md` 6-9 第二段："hashgrid_gtfree: 0.00029260 — NEW BEST (-9.6%), first sub-3e-4. Fresh coords each step, mining by finite-diff HF proxy |f(x+2e-4 d)-f(x)| on the model itself (no pool GT), GT only on the selected 768k batch."

含义是：
- 每 step 重新采一组坐标，避免大批固定坐标被 hashgrid "背诵"。
- 怎么知道哪些点"难"？不在样本池上算 ground truth，而是在模型自己的 forward 上做 finite-difference——`|f(x+Δd) - f(x)|`。
- 数学直觉：模型自己输出变化剧烈的位置，**很可能是真值变化剧烈但模型没学到位的地方**。
- 替代效果：传统"在 sample pool 上用 GT 算 error"是 0.346s/step 的 GT 计算瓶颈，FD-proxy 不需要 GT，把这一步直接换成 cost 几乎为 0 的 FP32 forward。

效果：**1170 步**（vs pool-4 的 700 步），MSE `0.000293`，**-9.6%**。`boundary_mse` 和 `mse` 几乎相等——错误从"边界堆集"变成"空间扩散"，说明模型在每个位置都有"小难处"，不是在某片区域彻底翻车。

**空间误差场（errfield）登场**——

GT-free 之后又一层枷锁：每 step 跑两次 9.4M-point proxy forward 各 ~110ms（220ms/step），又是 5 分钟 budget 的 36%。`notebook.md` 6-9 第三段给出的解法，把这一步的开销压到接近零：

> _persistent spatial error field mining: a coarse 2048×1296 EMA grid of per-cell mean |error|, updated FREE each step from the train batch's own residuals; hard coords sampled by cell-multinomial + in-cell jitter._

**关键不是神经网络，是数据结构**——一张 2048×1296 的图像，跟训练分辨率同一量级：
- 每个 cell 存一个 EMA(α=0.6) of mean |error|，**每 step 用这批训练样本的 residual 免 GPU 算力更新**。
- 每 step 抽样硬坐标：先按 cell 上的统计做 multinomial（更"难"的 cell 抽中概率更高），再在 cell 内 uniform jitter。
- 把 train batch 固定 768k 中 98% 拿来抽自这个"hard field"，剩 2% 留 uniform。
- **零额外 forward**。

`notebook.md` 里这一改动划出一道陡崖：`0.00027444 → 0.00024397`，**-11.1%**。这个结果第一眼反直觉——明明 EMA 引入了延迟，为什么反而比实时估计更准？

原因在方差上。单次 GT-free pool 估计"难度"时，靠的是一次抽样去猜一个 cell 的误差，方差很大：某个 cell 偶尔被抽中一次、恰好 error 大，就被标记成"难"，下一个 step 又可能被漏掉。EMA 把这个估计摊到时间轴上做加权平均（α=0.6，约 2-3 个 step 的记忆窗口），噪声被压下去，留下的是 cell 真实难度的时间平均。

再叠加一个零成本的便利：每 step 本来就要算训练样本的 residual，顺手把这个 residual 写回它所在的 cell——不用额外 forward，不用额外 GT 计算。结果就是，这套"持续纠错的难度地图"比"用真实误差做 mining"还便宜，还更稳。

> Bracket result in notebook：field res 1024 / 2048 / 4096 三档跑，2048 最好；EMA 0.9 / 0.8 / 0.6 / 0.3 四档，0.6 最好；hard fraction 85% / 90% / 95% / 98% 四档，98% 最好（91-98% 是噪声平坦）。**三个超参都不是孤峰，是 plateau**——这种 plateau 在 ML 工程上是好兆头：超参不敏感，结果可复现。

## 五、关键突破 3：Nmax 65536 + 13 Levels——分辨率天花板随步数移

`notebook.md` 6-9 末段：`hashgrid_n64l13: 0.00022636 — NEW BEST (-4.9%), promoted. Nmax 65536 + 13 levels "tied" historically at ~600 steps but WINS at ~1600 steps: more steps let the finer grid train. The resolution ceiling moves with throughput, as predicted.`

这一改关键不在算法，仍在 throughput——更细的 grid（Nmax 65536 即 65536 cell/level；13 levels 表示最细层分辨率约 65536 cell/level 套上 13 层多分辨率；总共 33M 参数）需要更多 step 才能 train 出有价值的东西。以前 ~600 step 时代，这个 grid "塞参数但不收敛"，现在 ~1600 step 时代它能 train 出"细颗粒"。

> 想过 n128l14（Nmax 131072, 14 levels）`mse=0.00022644`——跟 n64l13 在一个水平。结论：1600 step 时分辨率天花板就是 Nmax 65536；再有 step 才往上走。这是经验法则"hardware throughput 越高，architecture 选择空间越大"的一次工程级具体化。

跑完这次后 champion.py 全文 251 行，跑得最久的就是 champion.py 本身——**历史最长的一个 solution 文件就是最终的胜出者**。这恰好点出 RSI 的核心：决定胜负的从来不是某个 solution 静态有多好，而是它能在持续研究循环里被推多远。champion.py 赢在它是被推到最远的那一个。

## 六、最终结果：104 次试错全景

`runs.jsonl` 是 8 小时跑出来的硬数据。下面我把 104 条按里程碑分桶：

| 阶段 | MSE 量级 | 含义 |
|---|---|---|
| baseline MLP / Fourier | 0.00554 - 0.00049 | 朴素网络尚能拟合大体形状，但高频细节完全失守 |
| Champion 哈希网格 (with bf16 autocast) | ~0.000335 | 哈希 grid 出现，明显提升；卡在"irreducible floor" |
| Triton fused encoder | 0.00032359 | step 数翻倍让 floor 随之下降 |
| GT-free FD-proxy mining | 0.00029260 | 去掉 GT forward 依赖，错误分布更扩散 |
| Pool-mult=12 mining | 0.00027444 | pool size 调到 12 |
| Errfield (2048×1296, EMA 0.6, 98% hard) | 0.00024397 | 把 mining 几乎做成 zero-cost |
| **Nmax 65536 + 13 levels + best errfield** | **0.00022636** | **best result** |

champion entry 具体字段：
- run_id: 20260609-151512
- commit: ac29eca
- device: NVIDIA GeForce RTX 3090 Ti
- train_seconds: 300.04（5 分钟 budget 几乎用尽）
- mse: 0.00022636
- boundary_mse: 0.00022246（错误在边界附近分布均匀）
- psnr: 36.45 dB

### 两个怎么算都不便宜的数字

视频 27:08 在公布成本时数字偏高——这是工程真相：

- **104 条 runs × 300 秒 = ~8.67 小时** RTX 3090 Ti 单卡时间。
- 这 8.67 小时跑的不是"调一次参跑通"，是 AI 改 100 个不同 solution 文件、每个跑 5 分钟。期间还掺着人工核对、commit logging、JSON 持久化——wall-clock 时间远不止 8.67 小时。

但**拿到的是 0.0041 → 0.000226**，是 -94.5% 的 MSE 改善——单卡几百元成本，跑出这种量级的视觉拟合。这件事最该记住的成本特征是：试错的边际成本是常数（每次固定 5 分钟），不会随尝试次数膨胀。这是 AI 自主科研能跑起来的经济前提。

## 七、为什么"智能爆炸"不会从这事里发生

视频 14:14 用大段篇幅讲 RSI 的实现门槛——硬件、能源、数据、目标度量设计，收益递减天花板。把这段对照源码：

1. **硬件视角**：fractalsearch RTX 3090 Ti 跑 5 分钟 / 1 次 trial。带宽和 FLOPs 在 33M 参数 × 1600 step 这个规模完全用得满，所以"再增加计算应该能好"——但**带来边际效益递减**。`notebook.md` 6-9 session 末尾："session ended at user request after this run"，**用户在 engineer 面前才停**——AI 自己不会说"够了"。

2. **目标度量**：metric 是固定 MSE。AI 没有空间改 metric。如果可以改——比如把 boundary 内权重调到 0——分数会高 100× 但跟原意不符。`harness/evaluate.py` 把这一步 freeze，AI 只能"在规则内最大化"。

3. **新架构自动降质**：champion.py 从 ML 角度写得密密麻麻（triton 调优 + EMA 状态 + 多分辨率哈希），可读性差。`notebook.md` 6-9 第三段也注明："自动优化生成的代码可读性差带来的额外安全隐患"。人不再看得懂，也不再能合理地从中间继续推——**这是一个正在生长的可读性危机**。

4. **任务空间封闭**：5 分钟预算 + 固定 metric + 不许改 harness——这个空间不大。每次"新思路"实操上是 new solution 文件 commit。当任务空间封闭时，AI 不会自己溢出，只会卡在 plateau 上。

视频 20:50 提到的"AI 作弊可能性"——这里用结构性 sandbox（不能改 harness / 不能硬编码曼德博逻辑 / 不能加依赖）锁死。fractalsearch 的工程方案**根本性地偏离**了"AGI 自己改坏自己"那种 RSI 科幻叙事。

## 八、视频里没明说但源码透露的事

### 8.1 Mandelbrot 拟合这一题的特殊性

把训练目标设为 [0,1] 上的周期函数其实是很巧的工程选择：
- 它**接近边界时频率发散**——提供"无穷细节"的视觉素材，区分能力比 escape-time 整数更细。
- 它的**结构**是分形的——任何子区域都跟全局类似。这意味着 train 集 = eval 集时，只要随便选个区域就代表整个分布，不会出"采样偏置"。
- 它的 ground truth **在 GPU 上算**——ESCAPE_R = 1e4 + MAX_DEPTH = 200 step 是 O(N) 单点计算，batch 3.1M 也只用 ~350ms（一度是整个 step 时间预算的 81%）。

`notebook.md` 里曾把 ground truth 称为"the bottleneck"，但 6-9 session 之后用 GT-free mining + errfield 把它从 hot path 上彻底拿掉了。**GT-free 不是简单"绕过 ground truth"——是把它从研究循环的关键路径上撤下，挪到 evaluator 和采样验证上**。

### 8.2 不在视频里的"with human approval"

`AGENT.md` 第二段："Await human approval before starting a research loop." 

**AI 拿到 5 分钟 budget 之前要人同意一次**——但 `NEVER STOP` 写得更显眼。"never stop"是一个交付保证——"如果你启动循环，就别停下问人是否继续"。两个声明放一起看时，RSI 的可操作定义就清楚了：**人是进入门槛和退出点，AI 是中间的所有迭代**。

这就是 OpenAI / Anthropic 路线图里"AI 跑实验"那种模糊愿景的工程化身——需要清晰的"开始 / 暂停 / 接管"边界，而不是"AI 全自动做研究"的科幻。

### 8.3 Karl Popper 那句话的实操版本

`notebook.md` 里出现的一个观察让人想起波普尔的可证伪性——"if steps jump but MSE doesn't move, the irreducible-boundary story is finally proven." —— AI 通过**观察实验现象**反过来证伪 / 证实一个假设。这就是 AI 做了 Karl Popper 那句"科学进步靠猜想与反驳"的实操动作。

工程化的 RSI 包含三个动作：
1. **猜想** (form a hypothesis) — 形成为有效假设，commit 一个新 solution。
2. **实验** (run the loop) — 跑，看 MSE。
3. **反驳 / 证实** (reject/accept) — based on runs.jsonl 数据，决定这个思路是否继续。

这就是 RSI 在 2026 年最朴素的工程模样：**agent + git log + JSON log + 固定评估器**。

## 九、给不同读者的具体建议

### 9.1 如果你是 AI 研究者

`AGENT.md` + `champion.py` + `notebook.md` 是一份**完整的"AI 跑实验"工程模板**——可以直接 fork 到自己的 benchmark 问题。`evaluate.py` 的不变 5 项是值得模仿的：
- fixed budget（time-bounded 公平性）
- SIGALRM hard kill（实验必须终结）
- immutable harness（结构 sandbox）
- structured JSON log（`runs.jsonl` 决定 leaderboard 可信度）
- notebook.md 共享（不同 agent 之间有 continuous memory）

### 9.2 如果你是智能体工程师

`champion.py` 的 Triton fused encoder 是**一份教学级** PyTorch + Triton 协作代码——不到 100 行实现了一个 2× speedup。`hashgrid_gtfree.py` + `champion.py` 拢共 ~500 行 PyTorch + Triton，能放进一份智能体训练基础设施里被复用。

### 9.3 如果你关注 AI 安全

fractalsearch 是**一个对立极**——"AI 自主科研在封闭问题里能做到什么"的样本。它做了 video 14:14 和 20:50 里"RSI 实现门槛"和"沙箱需求"两个最关心的问题：**门槛真实存在**（5 分钟 budget + 33M 参数 + 封闭 sandbox 下 0.000226 是当前工程能做到的极限），**沙箱结构性可行**（harness/ 不让动是暴力但有效的方案）。

## 十、最值得理解的一句话

> _Don't trust benchmarks, trust the wall-clock truth and the JSON log._ — `solutions/notebook.md` 行间意

fractalsearch 实验里 0.000226 是权威——因为它来自 `runs.jsonl` 第 104 行的 commit `ac29eca`，对应设备 RTX 3090 Ti 上 300.04 秒实测，不是任何 SOTA 报告。RSI 在工程上不像科幻叙事，它**长得就像这份 JSON log 里的每一行**——一条，5 分钟，又一条，5 分钟，104 条改写成一份研究笔记。

如果把 Anker / 姚顺雨 / 田渊栋 这些 RSI 相关的中文讨论并列起来看，**fractalsearch 是其中唯一一份完全开源、全部可复现、能让读者在自己 GPU 上重跑并验证结果的**——Karpathy autoresearch 框架的一个 PR，人类作者 MaxRobinsonTheGreat，AI 操作者（自己写自己 commits）。

视频作者 Emergent Garden 把这个实验**配着 RSI 这种宏大议题**讲给观众听——但 rsi 的本质其实是 33M 参数、1600 steps 和 5 分钟 hard kill。这种"宏大叙事 × 工程现状"的错位，才是标题党们喜欢讲的"AI 取代科研"的真相——工程现实比新闻乐观得多，也冷静得多。

---

## 自己复现一次：从 clone 到 0.000226

光读不练，数字始终是别人的。下面这张清单把"复现一次 fractalsearch 最小回路"拆成可勾选的步骤，照着走一遍，对 RSI 的工程体感会比看十遍视频都牢。这是一道实战练习，不是阅读材料。

### 复现练习清单（动手做）

- [ ] **1. 环境**：装好 [uv](https://docs.astral.sh/uv/)，`git clone` 仓库后 `uv sync`。确认 `pyproject.toml` 里 torch + triton 3.5.1 能跑——这是作者刻意不挂 C++ 扩展的原因，你不必装 CUDA 工具链。
- [ ] **2. 跑通 baseline**：`uv run python -m harness.evaluate solutions/baseline_mlp.py`。应该看到 MSE 在 `0.004-0.006` 量级。这一步验证 harness 通了，SIGALRM 定时生效。
- [ ] **3. 读 AGENT.md**：重点看 "What you CANNOT do" 三条禁令（不改 harness、不硬编码曼德博逻辑、不加依赖）。这是沙箱的边界，也是后面所有 commit 的合法性来源。
- [ ] **4. 读 runs.jsonl**：`wc -l runs.jsonl` 应该是 104 行。`tail -1` 看最后一条的 `mse` 字段——这就是要挑战的 `0.000226`。
- [ ] **5. 让 AI 跑一轮**：把 `AGENT.md` 喂给你的 coding agent，`NEVER STOP` 一旦启动，观察它会不会自己 `git commit` + 跑 evaluate + 读 run.log。如果它停下来问人，说明 prompt 没吃透 `AGENT.md`。
- [ ] **6. 对照 notebook.md**：跑完几轮后，对比你的 agent 写的 notebook 和原作者的 notebook。两份笔记的"假设质量"差距，就是 RSI 当前真正的能力边界。

**常见卡点**：
- **SIGALRM 在 Windows 上不生效**——`signal.SIGALRM` 是 Unix 专属，Windows 复现得换成 `threading.Timer` 或 WSL2。
- **5 分钟跑不满**：如果 GPU 显存不够，batch size 会被自动降，300 秒里跑的 step 数远少于 1600，MSE 就复现不到。3090/4090 这一档是作者实测的硬件下限。
- **triton 版本漂移**：triton 小版本之间 kernel 行为会变，`2x speedup` 的数字只在 3.5.1 上成立。换版本前先跑一次 champion 确认 MSE 没退化。

### 自测：你真的看懂这次实验了吗

读完前面八章，试着不查源码回答下面三个问题。答得上来说明 RSI 的工程骨架已经立住了：

1. **为什么是 5 分钟 budget 而不是 1 小时？** 提示：fixed budget 对"分数可比"为什么是必要的？如果 budget 浮动，commit 历史还能当 leaderboard 用吗？
2. **GT-free mining 为什么比"用真实 GT 算 error"还便宜？** 提示：把"算 error"这件事从哪个环节撤下来了？撤下来之后那 0.346s/step 去哪了？
3. **errfield 用 EMA(α=0.6) 而不是直接用本 step 的 residual，是在换什么？** 提示：单次抽样的方差 vs 时间平均的延迟，这两个代价哪个更可接受？

答案分别藏在第二章（fixed budget）、第四章（GT-free）、第四章（errfield EMA）——但先自己想一遍，再回去对。

---

## 延伸：从 fractalsearch 往外看一步

把 fractalsearch 放回 2026 年 RSI 的版图里，它的位置很特殊，也很清楚：

| 项目 | 改的是什么 | 完全开源可复现 | 跟 fractalsearch 的关系 |
|---|---|---|---|
| **karpathy/autoresearch** | 训练脚本 / 架构配置（弱 RSI） | ✅ | fractalsearch 的母框架 |
| **MaxRobinsonTheGreat/fractalsearch** | 拟合算法（弱 RSI） | ✅ | autoresearch 的一个 PR 级应用 |
| **DeepMind AlphaEvolve** | 调度算法 / 矩阵乘 kernel（弱 RSI） | ❌ 内部 | 同类，工业规模 |
| **Schmidhuber Gödel Machine** | 自身权重 / 推理能力（强 RSI） | 纯理论 | fractalsearch 不是这个 |

fractalsearch 的价值不在"它多强"——单卡 8 小时压一个 MSE 到 0.000226，在 ML benchmark 里排不上号。它的价值在**它是这张表里唯一一个连 AI 的研究笔记（notebook.md）都公开的**。别的项目要么只发论文，要么只放最终代码，读者看不到 AI 中间那些"换思路、记 bracket、证伪假设"的过程。fractalsearch 把 RSI 的中间产物也摊开了，这才是它对工程师和研究者真正稀缺的地方。

如果你顺着这篇文章想再走远一点：先 fork autoresearch，找一个你自己的"曼德博集合"（任何一个有客观 metric、能 5 分钟跑完、有改进空间的问题），把 `AGENT.md` 换成你的任务书，让 AI 跑一晚上。第二天早上回来翻 `runs.jsonl` 和 notebook——你对"AI 自主科研现在到哪了"的判断，会比任何一篇综述都准。

---

## 关键资源

**主要资料**
- [Emergent Garden《Recursive Self-Improvement》(YouTube)](https://www.youtube.com/watch?v=t7_ZXgfJVG8) — 2026-06-13 发布英文原版
- [BV1w8jL6dE1f](https://www.bilibili.com/video/BV1w8jL6dE1f/) — B站 @黑纹白斑马 AI 配音版，本文的章节时间线来源
- [MaxRobinsonTheGreat/fractalsearch](https://github.com/MaxRobinsonTheGreat/fractalsearch) — 2026-06-19 公开，104 条 runs.jsonl + 4 个 solution + AGENT.md
- [MaxRobinsonTheGreat/mandelbrotnn](https://github.com/MaxRobinsonTheGreat/mandelbrotnn) — 作者个人长期 pet 项目
- [karpathy/autoresearch](https://github.com/karpathy/autoresearch) — framework 起源

**关键算法参考**
- Multi-resolution Hash Grid Encoding (Instant NGP / tiny-cuda-nn)
- Triton `tl.constexpr` + atomic_add backward
- EMA spatial error field (persistence + zero-cost update)
- finite-difference hardness proxy (`|f(x+Δd) - f(x)|` on model itself)

**对照阅读**
- 《[田渊栋重返牌桌：RSI、潜在推理与 AI 研究的下一次换挡](https://txtmix.com/posts/video/tianyuandong-rsi-recursive-superintelligence-2026/)》— 中文 RSI 综合视角
- Emergent Garden 个人其他视频（YouTube 同频道）

**复现环境**
- NVIDIA RTX 3090 Ti（实测设备）
- Python 3.x + uv（依赖管理）
- PyTorch + Triton 3.5.1（与 torch 自带同发）
- 5 分钟 / run × N 次，预算可调

---

## 写作笔记（给后续读者）

**视频无官方字幕** — BV1w8jL6dE1f 是 YouDub AI 配音的中文译制版，B 站 subtitle 轨返回空数组；YouTube `t7_ZXgfJVG8` 字幕需要登录 cookie 绕过 yt-dlp 的 bot 检测。本版没有声称"逐字逐句对照视频"，而是以 `AGENT.md` `README.md` `solutions/notebook.md` `runs.jsonl` 四个仓库级文件为骨架。

**关键外部资料**：
- B站 BV1w8jL6dE1f 章节时间线（UP 主简介直接给出 8 段 + 时间戳）
- [karpathy/autoresearch](https://github.com/karpathy/autoresearch) 框架设计：5 分钟 budget + SIGALRM hard kill + 不可改的 harness + JSON log
- [tiny-cuda-nn](https://github.com/NVlabs/tiny-cuda-nn) multi-resolution hash grid 原始论文 Müller et al. 2022
- Periodic · log-distance 目标的具体工程实现：[mandelbrot_lab.html](https://github.com/MaxRobinsonTheGreat/fractalsearch/blob/master/dashboard/static/mandelbrot_lab.html) 在 fractalsearch 仓库自身

**未确认项**：
- 视频作者 Emergent Garden 的个人背景 — fractalsearch 仓库的所有者是 `MaxRobinsonTheGreat`（README 和 git commit 明确）；视频频道作者未在 BV1w8jL6dE1f 简介里点明是否同一人
- 0.000226 在 fractalsearch 之后是否被进一步压低 — 本文撰写时仓库 `runs.jsonl` 截止 2026-06-09 15:15:12 session，没看到新 commit 后的更好结果
