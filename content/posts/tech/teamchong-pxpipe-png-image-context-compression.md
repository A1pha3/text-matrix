---
title: "teamchong/pxpipe：把 Claude Code 上下文塞进 PNG，省下 70% token"
slug: teamchong-pxpipe-png-image-context-compression
date: "2026-07-08T19:25:00+08:00"
description: "pxpipe 是 Anthropic API 的本地代理，把大段 tool_result / system prompt / 历史对话渲染成 PNG 图像块塞回请求，让 vision 通道读上下文，token 削减 59-70%。它有完整的盈利能力门控、缓存对齐、事实摘要回退机制。"
categories: ["技术笔记"]
tags: ["Claude Code", "Token优化", "代理", "图像压缩", "VLM", "提示缓存"]
---

# teamchong/pxpipe：把 Claude Code 上下文塞进 PNG，省下 70% token

> **GitHub**: [teamchong/pxpipe](https://github.com/teamchong/pxpipe)
> **Stars**: 4,931 ⭐
> **Forks**: 391
> **License**: MIT
> **核心语言**: TypeScript
> **首次提交**: 2026-05-20

第一眼看上去反直觉：把文字渲染成图片，再让视觉通道读回去。但 vision token 按像素面积计费，不按字符数——一张 1928×1928 的 PNG 装下 9.2 万字符、只收 4761 个 token；同样的字符按 text 走要 2.5 万 token。压缩比约 5×。

这不是 OCR。OCR 引擎把每个字符切成 glyph、分类、输出带置信度的字符；VLM 不这么干，它把图像切成固定网格的 patch，每个 patch 投影成一个连续 embedding，然后语言模型在 embedding 上做 attention。从头到尾，**没有任何字符被实体化为离散符号**。视觉通道读错了不会"报不清"，而是用语言先验填一个看着合理的答案——这种失败模式叫 silent confabulation，pxpipe 整套设计都围着它转。

## 30 秒上手

```bash
npx pxpipe-proxy                                  # 代理监听 127.0.0.1:47821
ANTHROPIC_BASE_URL=http://127.0.0.1:47821 claude  # 把 Claude Code 指向它
```

Dashboard 开在 <http://127.0.0.1:47821/>，能看到每一次 text→image 转换的并排对比、kill switch、实时模型徽章。响应流照常走——pxpipe 只压缩**请求**，从不碰模型的输出。

适用面很窄：token 密集的内容（代码、JSON、tool 输出，约 1 字符/token）大赢，稀疏散文（~3.5 字符/token）反而亏钱。盈利门控是按请求算的，校准过 391 行生产数据，**只在数学上赢了时才渲染**。其余内容字节级透传。

## 关键数据

| 测试 | N | 文字 arm | pxpipe (图像) | Token 变化 |
|---|---:|---:|---:|---:|
| 新型算术，claude-fable-5 | 100 | 100% | **100%** | **−38%** |
| 新型算术，claude-opus-4-8 | 100 | 100% | 93% | −38% |
| gist 回忆 A/B（决策、值、路径、名字、取反，带干扰项，15k–45k 字符会话），Fable 5 | 98/arm | 98/98 | **98/98** | — |
| 状态追踪（值被改 3 次，final/first/count），Fable 5 | 18/arm | 18/18 | **18/18** | — |
| 从未陈述事实的瞎编率（越低越好），Fable 5 | 16/arm | 0/16 | **0/16** | — |
| 密集渲染下 12 字符 hex 逐字回忆，Opus | 15 | 15/15 | **0/15** | — |
| 密集渲染下 12 字符 hex 逐字回忆，Fable 5 | 15 | — | **13/15** | — |

逐字回忆低，是设计上的取舍，不是 bug。`/compact` 也做不到逐字——它把老内容丢进散文摘要就再也回不来了。pxpipe 反而保留了内容（**在像素里**），只是不能保证精确读出。

## 三个压缩路径

1. **大块 `tool_result`**（文件读取、命令输出、日志），超过 ~6k 字符的 token 密集内容
2. **已坍缩的旧历史**：实时尾巴之后的旧 turns 重新渲染成图像页，最近的 turns 始终保持文字
3. **静态系统提示 + 工具文档**

其他都字节级透传：你的消息、最近 turns、模型输出（代理从来不碰）、稀疏散文、任何小到不值得压缩的东西。模型白名单外的请求**整条透传**——默认只压 Fable 5 和 GPT 5.6。Opus 4.7/4.8 读图像出错率约 7%，GPT 5.5 在图像上下文上退化，两者都走 opt-in。`PXPIPE_MODELS=off` 直接关掉图像化。

## 工作流

```
tool_result 字符串 ──► 1928px 宽列包装 ──► 每页塞 ~9.2 万字符 ──► PNG[]
```

代理拦下 `/v1/messages`，把符合条件的大块重写成图像块，**按缓存友好方式插回去**（保留静态前缀，prompt caching 继续工作），再转发。1928×1928 的图像大约 4761 个 vision token，能装约 9.2 万字符，text 赢的临界点约在 19 字符/token——Claude Code 实测 1.91（N=391）。每个请求跑个估算器，稀疏的散文就保留文字。事件日志写到 `~/.pxpipe/events.jsonl`。

## 库用法（不开代理）

```ts
import { renderTextToImages, transformAnthropicMessages } from "pxpipe-proxy";

const { pages } = await renderTextToImages(toolResultText);     // pages[i].png: Uint8Array
const { body, applied, info } = await transformAnthropicMessages({
  body: requestBytes,
  model: "claude-fable-5",
});
```

`options.keepSharp(block)` 把指定 block 钉成文字；`options.emitRecoverable` 返回被图像化的 block 的原文。运行时是纯 JS（Node + edge/Workers），`@napi-rs/canvas` 只在构建时用。完整 API 见 `src/core/index.ts`。

## 测量方法

**端到端，不只是改写那块。** 多数压缩工具只报告"我摸过的 input 切片"省了多少，那个数会偏胖。pxpipe 的分母是**整张账单**——所有生产请求里它正确放过的小请求、所有 cache 写入和读取、所有输出 token（代理从来不压缩输出）。在 13,709 个请求的快照上是 59%（$100 → ~$41），更晚的 8,904 个压缩请求 trace 是 ~70%。仅压缩切片单独跑会高到 ~72–74%，那是分开报的，从不当作头条数字。

**两边同一时刻。** 每个 `/v1/messages` POST 发出后，代理并行发一次免费的 `count_tokens` 探测原 body（反事实），再读 Anthropic 实际计费 usage 块。两次落在 `~/.pxpipe/events.jsonl` 的同一行，没有 turn 数或 run 间方差。美元换算用 Fable 5 列表比：input ×1.0、cache write ×1.25、cache read ×0.1、output ×5。Cache 定价两边一样应用，cache 折扣相消，不会被双重计入"省了多少"。自己重算就行——公式和字段名写在 `src/core/baseline.ts`。

## 模型视觉不是 OCR

OCR 引擎会切片、分类、出字符加置信度，错了能说"unreadable"。VLM 没这几步：

1. 图像切成固定网格的 patch
2. 每个 patch 投到一个连续 embedding（这是图像 token 按像素数计费、不按字符数的原因——tokens = patches。密集文字每个 token 装的信息更多，整个盈利空间就压在这里）
3. 语言模型照常 attend patch embedding。"读"就是解码器结合语言先验重建语义

整个 stack 里**没有任何字符变成离散符号**。没有 per-glyph 置信度，没东西可以"响亮地失败"。当像素不足以定一个 glyph，**语言先验会填一个看着合理的词**。

这就是这套机制预测的全部失效签名，pxpipe 的 eval 也一一对应上：

- **散文扛密度、标识符腐化。** 语言先验能修复低熵文本（你也读得懂"jumbled wrods"），对 hex 字符串零信号。实测：gist 回忆 98/98 每 arm；12 字符 hex 逐字 Fable 5 13/15 对 Opus 4.8 0/15，同一批页面。
- **错误是 plausible 不会是 garbled。** Opus 语义 needle 跑 6/15，命中全是先验会猜的圆数；错的都是别的 plausible 圆数。真实用了几周唯一的现场失败就是一个自信的错误名字，不是报错。
- **准确率随像素/glyph 平滑下降。** 没有可读/不可读的悬崖——分辨率扫描测出来就是这样（Opus 4.8，n=20 ids/size）：

  | glyph 单元 | 相对面积 | 逐字准确率 |
  |---|---:|---:|
  | 5×8（生产） | 1× | 10% |
  | 7×10 | 1.75× | 35% |
  | 10×16 | 4× | 95% |
  | 20×32 | 16× | 100% |

- **盲读会撞 glyph 混淆矩阵。** 可读性审计在密集标识符上 63% 封顶（24 token 盲测），每条错都落在混淆矩阵预测的 0/8、e/4 类。
- **符号编码是死胡同。** "把 hash 画成 QR 码 / 盲文"需要**这套 stack 没有的离散解码**。条码要解码器，这里只有先验。

## DeepSeek-OCR 早就被打脸了，不是吗？

不是。它证明的是**通道能工作**——用一个 380M 编码器 + 3B 解码器专门训练，10× 压缩以下报 97% 准确率，20× 附近掉到 60%。

仔细看，那篇论文是**支持**这个通道的证据：text-as-pixels 在 reader 能读的时候能高保真。问题是 2025 年 10 月的时候，**没有任何生产级通用模型能读**。围绕它产生的"光学压缩不 work"的怀疑是那代模型的正确观察，**但过期了**。

pxpipe 自己测出了过期的时间点。同样 harness，两个模型：

| 测量 | Opus 4.8 | Fable 5 |
|---|---:|---:|
| 图像上下文新型算术 (N=100) | 93% | 100% |
| 密集渲染 12 字符 hex (n=15) | 0/15 | 13/15 |
| 5×8 生产 glyph 单元 | 10% 逐字；需要约 4× 面积到 95% | 能读（即 13/15 那行） |
| pxpipe 状态 | opt-in（读错 ~7%） | 默认 reader |

一个 vendor 代际把可读密度 knee 往**好的方向**推了约 4× 面积。这就是 pxpipe 的故事：能力跨过了盈利阈值，pxpipe 落在阈值后面这侧。也解释了 Opus 留作 opt-in、README 报**逐模型**数字而不是一个混合声明的原因。

## 那个赤裸的部分

**它是有损的。** 密集图像化内容里精确 12 字符 hex 串：Fable 5 **13/15**，Opus **0/15**——错的是 **silent confabulation**，不是报错。逐字节的值（ID、hash、密钥）必须保持文字；最近的 turns 保持文字。专用的 verbatim-risk guard 还没造。

**逃逸通道：** 白名单外模型上的子代理整条以文字透传——把逐字节工作路由过去（`CLAUDE_CODE_SUBAGENT_MODEL=claude-sonnet-4-6`，或 agent frontmatter 里 `model: sonnet`）。

**真实工作：** SWE-bench Lite 试点两 arm **10/10**（请求大小 −65%）；SWE-bench Pro **14/19 ON 对 15/19 OFF**（−60%），裁决 18/19 一致，**唯一分叉重跑 3/3 重合**——是 run 间方差不是压缩。n 很小；回执在 `eval/`。

**Workload-dependent。** Token 密集内容（约 1 字符/token）赢，稀疏散文（~3.5 字符/token）亏钱；盈利门控（用 N=391 行生产数据校准）只在数学赢了时才图像化。

**模型范围：** 默认 `PXPIPE_MODELS=claude-fable-5,gpt-5.6`。Opus 4.7/4.8 读错 ~7% 渲染，GPT 5.5 在图像上下文上退化——两者都 opt-in，走 `PXPIPE_MODELS` 或 dashboard 徽章。`PXPIPE_MODELS=off` 禁用图像化。其他全部字节级透传。GPT 路径上，tool 定义保持原生 JSON，不发 Anthropic `cache_control` 标记。

## API 限幅：你付了钱但没拿到像素

[legibility audit](docs/LEGIBILITY-AUDIT-2026-07-01.md) 揭了一条隐藏的免费保真杠杆：

> **Anthropic API 把每张图像降采样到同时满足「长边 ≤1568 px」和「~1.15 MP」，然后按 ≈ px/750 计费（每张）。**

旧 1932×1932 页按上限收费但**被 0.555× 降采样**——5×8 glyph 到 vision encoder 那里只有 ~2.8×4.4 px。**你付了全价的像素、API 把它在传输中毁了**。

修复：**页面几何夹到 1568×728 = 1.14 MP**（所见即所得：计费/实际像素比从 3.25 降到 1.04）。每张图像 token 成本不变；614/614 测试绿。

讽刺的是：encoder 上限还是每图 ~1.15 MP，所以每张成本 ~不变，但**新页只装 28,080 字符，旧页 92,160**——同样语料需要 ~3.3× 张图。旧的"16× vs text"压缩比是**部分虚构的**——靠的是把像素当静默模糊在 API 边界扔掉。真实可读率约 5× vs text。这次改动不加成本——让模型为它**已经被收了但从没收到**的可读性**付可见的代价**。

## Glyph 混淆矩阵

Spleen 5×8 字体，94 个可打印 ASCII。**45/94 的字符最近邻 Hamming ≤ 3 px**（总共 40 px）。最差：`,~;` `.~:` `H~K` 距离 1；`0~O` `3~8` `5~S` `6~8` `8~B` `U~u` `V~v` `W~w` `X~x` 距离 2。`H~K` 距离 1 是字体缺陷（glyph-surgery 候选）。旧页 0.555× 降采样把很多距离 2 的对往距离 0 推——不可区分。

## 事实摘要：让精确值骑在图像旁边

逐字读得差是真的，但 pxpipe 不把这件事完全甩给图像通道。它在每张图像旁边**附一张 verbatim 事实摘要**——把渲染内容里精度关键、难 OCR 的字符串（文件路径、URL、SHA/UUID、版本号、CLI flag、大数字、CONST_IDS）挑出来，**以纯文本和图像并排**。模型直接引文字，**不必再读 PNG**，而且还在缓存前缀里。

实现细节：

- **决定性优先排序**——不是按 token 长度，是按 token 形状。70 字符 URL 结构化、可重建，落在 tier 2；7 字符 hex SHA 零冗余、错了就 silently wrong，落在 tier 0。64 token 预算吃紧时，短的高后果 token 不会被长的低风险 URL 挤掉。
- **确定性格式**——固定 pattern 顺序、长度降序 + 字典序、无 Date/随机。**输出字节级稳定**——跨 turn 不 bust Anthropic prompt cache。
- **经验占比 ~5%**（生产历史中位数 4.9%、最大 12.1%、N=10）——保住了图像化的 token 赢面。
- **ReDoS-safe 正则**——按空白分块先，每块 ≤512 字符，**严格 O(n)**。base64 / 压缩包不会触发路径 pattern 的回溯爆炸。

**效果：9 条错里 7 条已经在摘要里**（SHA、数、URL 都已经文字附在旁边）——图像读错不致命。剩 2 条是 camelCase 标识符，**不是摘要的形状**——code dump 里有 >64 个不同 camelCase 符号，64 token 预算装不下，得走 re-fetch 路径。scaffolding（`RecoverableBlock` + `rec_<sha>` + 原文 + 出处）已经写好，但还没接到模型可调的工具上。

## 缓存对齐：别把 cache 折扣算成 pxpipe 的功劳

Anthropic prompt cache 是 prefix-based：

- cache key 来自每个 `cache_control` 断点前**精确渲染的 prompt 字节**
- 渲染顺序：`tools` → `system` → `messages`
- 断点是内容块上的 `"cache_control": {"type": "ephemeral"}` 标记
- 响应 usage 块报 `input_tokens`、`cache_creation_input_tokens`、`cache_read_input_tokens`
- 该请求总 prompt token = `input_tokens + cache_creation_input_tokens + cache_read_input_tokens`

| 桶 | 含义 | 倍率 |
|---|---|---:|
| `input_tokens` | uncached input | `1.0×` |
| `cache_creation_input_tokens` (`cc`) | 写 cache | `1.25×` |
| `cache_read_input_tokens` (`cr`) | 读 cache | `0.1×` |
| output | 模型回复 | Fable 5 上 5× input |

稳定前缀缓存后便宜，但每 turn 都变的前缀反复付写溢价。pxpipe 的 cache 对齐工作就是**把图像前缀稳住**。

关键不变量：

> **pxpipe 不加新 cache-control 标记。** 它把 caller 已有的标记**搬到同一逻辑内容产生的最后一个图像块上**。

断点留在重写后稳定内容的末尾。Provider 缓存图像前缀的方式跟缓存文本前缀一样，只是该 cache entry 下的 input token 更少。重写后的请求形状：

```text
system:
  账单行 / 动态上下文 / 其他 text-only system 内容

messages[0] user:
  图像块
  图像块
  图像块 + cache_control
  [End of rendered context.]
  原始 user 内容 / 实时尾巴
```

图像**必须**放在 user 消息里——Anthropic 在 `system` 字段不接受图像。

## Gate 的一次性 burn

原始压缩 gate 比较图像 token 成本和文字 token 成本。Anthropic 这边，图像成本从像素面积估，文字成本从对应桶配置的 字符/token 估。

切换模式也会烧热 cache。文字前缀热时切到图像，第一次图像 turn 可能要付一次写。图像前缀热时切回文字，文字路径可能要付那次写。对称 burn 项把那个成本算进去：

```text
burnImageSide = priorWarmTokens      * (1.25 - 0.10)
burnTextSide  = priorWarmImageTokens * (1.25 - 0.10)

compress iff imageTokens + burnImageSide < textTokens + burnTextSide
```

这跟 dashboard 报告的省分是分开的两件事。gate 决定要不要转；dashboard 报转后那个请求**实付**对**测量到的文字反事实**。

## 真实翻过车

有一次，几周的日常用里唯一的现场失败：模型从图像化的聊天历史里回忆一个人的名字，**自信地错了**。不是报错，就是 plausible 的错误名字。这是记录在案的失败模式：图像化内容里的精确字符串**不字节安全**。编码 session 能忍——agent 改文件前会重读；纯聊天回忆没这个检查。

这个失败模式**是测出来的不是听来的**：legibility audit 在密集标识符上盲读封顶 63%，每条错都落在 glyph 混淆矩阵预测的（0/8、e/4 类）。已发布的修复是页面几何夹到 API 的 resample 上限，**计费像素真的能到 vision encoder**，外加精确标识符（SHA、数）以文字形式并排。

## 渲染尺寸：为什么看起来是方块

页面是**定宽变高**的，**不是故意做成方形**，**也从不横向收缩去塞短行**。

- 宽度对每条路径恒定，**由列数决定不是由内容**：`width = 2·PAD_X + cols·CELL_W`。静态 slab 用 `DEFAULT_COLS=313` → `8 + 313·5 = 1573px`；密集 tool/history 用 `DENSE_CONTENT_COLS=384` → `8 + 384·5 = 1928px`。
- 高度**长到塞下该页所有行**，封顶后翻页：`height = 2·PAD_Y + nLines·CELL_H` → `8 + 8·nLines`。
- 垂直封顶 → 翻页：`maxLines = floor((MAX_HEIGHT_PX − 2·PAD_Y) / CELL_H) = floor(1924/8) = 240` 行。溢出进下一张，**不把画布拉大**。

这个 `~1932×1932` 上限是 Fable / Opus 4.8 接收**不被服务端 resize 的最大页**。那些模型长边能到 2576 px，但**>20 张图像**的请求（pxpipe 总会发很多）受更严的 ≤2000 px/边 限制，`1928×1928` = `69×69` = **4761 vision token**，刚好压在每图 **4784** token cap 下面。再大请求**被拒**，不是被降采样。

每个字符占 **5px 宽 × 8px 高**的 cell。`ATLAS_CELL_W=5`、`ATLAS_CELL_H=8`，字形表是预烤好的 glyph 块，文字白底黑字渲染再反相成黑底白字。cell 最早是 **7×10**，**后来缩到 5×8**——更小的 cell，目标模型上同样可读，每像素装的字符更多。

## 容量上界：为什么渲染 trick 都被 park 了

逐字读准确率是**像素/glyph 的单调函数**（Opus 4.8：生产 5×8 cell 10% 逐字，10×16 95%，20×32 100%；n=20 ids/size），加上 API 的 resample 上限（更大的页在 encoder 看到之前就被降采样），**任何固定密度上**、超出 encoder 转录能力的**那部分都带保证的错误下限**。错误可以**挪到先验能修复的内容上**（散文）、**被检测出来**、**或被付价**。它们**不能**在同密度下被字体/颜色/排版消除。每条提案怎么死的：

| 提案 | 死因 |
|---|---|
| patch-grid 对齐字体 | 服务端 resample 毁掉像素相位；encoder 内部不公开也不稳定 |
| QR / DataMatrix / 盲文 / 自定义 glyph 映射 | 需要离散解码——这套 stack **没有**（见下）；精确 id 已经以文字并排 |
| RGB 页多路复用、彩色 lane、色度边纹 | 文字阅读以亮度为主；分通道或重叠文字**远在训练分布外** |
| 字体形状交换 | 扫描结果：混淆随 cell 面积消失，**不随 glyph 形状** |

## 已 park 的研究：留给接班人

2026-07-05 跑完一轮"奇技淫巧渲染"提案域（ViT patch-grid 对齐、RGB 通道多路复用、QR/盲文/matrix glyph 编码、色度边纹、背景锚定网格、彩色文字 lane）。**全没活下来**。把为什么写下来，下一个人能从这停的地方继续，不用重新推。

**接班的开放线索（带沉淀状态）：**

1. **Glyph-style A/B**（`eval/glyph-matrix/`）：暂停；120 页已预渲染，2/40 trials 入库，limit-aware resume 步骤在 `HANDOFF.md`。扫描结论是「resolution-not-shape」，预期效果温和（个位数 pp，但 token 成本中性如果某个 style 赢）。
2. **运行时 canary + re-fetch**：每页渲染一段已知短串（~92k 字符页上一个 ~30 字符 canary）；消费方转写它；对不上当 erasure 处理，按文字重新拉。**把 silent misread 变成 detected、priced 重传**。也是将来安全提密度的前提——**未检测到的错误逼着保守密度，检测到的错误可以简单付价**。
3. **Surrogate-reader pre-flight**（新，未测）：代理对每张渲染页持有 ground truth，所以本地 VLM 可以在发出前 proofread；本地 VLM 读错的任何 span 重新画大或走文字。go/no-go 是一个免费实验：在已沉淀的 glyph-matrix 页和外部页上，**本地 VLM 和 Fable 的 miss-set 关联**。高关联就造，低关联这想法就死，本文件如实记。

**决策：park。** 绑定约束在一个模型代际里**零投入**改善了约 4× glyph 面积。**触发器：每个模型发布**重跑扫描（~20 次便宜调用）：

```bash
MODEL=<id> TAG=<tag> bash eval/glyph-matrix/sweep/run_sweep.sh
```

新模型 5×8 读到接近 100% → 提密度（省分免费上升）。provider 出厂原生光学上下文压缩 → 这个 repo 退役，结果挺好。

## 限制

- **有损**（上）；逐字回忆从图像**不可靠**
- PNG 编码给大请求**出去前**加延迟
- ASCII/Latin-1 测得充分；CJK 能用但偏保守

## 路线图

渲染研究 2026-07-05 起 park：逐字读错是**容量绑定**不是 trick 绑定，所以没有字体/颜色/排版改动能在盈利密度上修好逐字回忆。原因在 `docs/NOT-OCR.md`；带日期的分析 + 三条记录在案的跟进线（glyph-style A/B with banked pages、运行时 canary + re-fetch、surrogate-reader pre-flight）在 `FINDINGS.md` 2026-07-05 那条。

**观察条件：** 每个模型发布重跑逐字扫描；可读密度从 Opus 4.8 到 Fable 5 在 glyph 面积上移了 ~4×，一个能把生产 cell 读到 ~100% 的模型意味着省分免费上升。

**还开着、不变：** 图像化大块是否真把有效上下文撑大（约 2× 真实内容进同样的 1M 窗口），以及更小的活动上下文是否改善长任务准确度。**假设，不是声明**——带 n 才会发数字，否则砍。

## 为什么 README 读着像 AI 写的

因为就是。这个 repo 的大多数 commit——代码和文档——都是 **Opus/Fable agent session 写的，session 背后就是 pxpipe 自己**，工作的时候**读自己的坍缩历史当图像页**。
