---
title: "反推 AI 视频提示词完整指南：用 Gemini 视频理解从视频逆向拆解生成提示词"
date: "2026-05-26T23:55:48+08:00"
lastmod: "2026-05-28T17:20:00+08:00"
slug: "gemini-reverse-engineer-ai-video-prompt-guide"
description: "基于 Google 官方视频理解、Files API、上下文缓存、媒体分辨率、结构化输出与社区高颗粒度模板，系统讲清如何用 Gemini 从视频逆向拆回可复用的生成条件，并把结果沉淀成长期可复用的 prompt 资产。"
draft: false
categories: ["技术笔记"]
tags: ["AI视频", "提示词工程", "Gemini", "反推", "Google AI Studio", "结构化输出", "AI生成"]
---

<!-- markdownlint-disable-file MD003 MD041 -->

这篇文章写给已经在用 Runway、可灵、Pika、Veo 或同类工具的人。这里说的“反推提示词”，更接近逆向拆镜：从成片里把主体、动作、镜头、声音、空间关系和速度感重新捞出来，同时把该留白的地方留出来。

Gemini 能同时读视频帧、音频和时间戳，再配合强约束提示词或结构化输出，把证据层和改写层拆开。最后留下的，最好是一份能喂回视频模型、能复盘、能存档、还能继续改的中间稿，而不是一大段看上去很专业的说明文字。

下面的方法基于 Google 官方视频理解、Files API、上下文缓存、媒体分辨率、结构化输出、提示工程文档，以及社区流传很广的 HYPER-GRANULAR VIDEO ANALYSIS 模板。模型名字、AI Studio 界面、费率和配额会继续变，但“先观察、再重组、最后验收”的工作流不会变。若你打算把它用于他人作品的商业复刻，版权、商标、肖像权和平台条款仍要单独判断。

先记这 3 条：

- 先把视频拆成证据，再写 prompt，不要反过来。
- `unknowns` 必须留着，不要把猜测装成参数。
- 验收看第二次生成出来的视频，不看分析稿写得多漂亮。

## 1. 学习目标

下面几件事读完应该能上手：

- 判断一段视频适不适合做反推，避免一上来就整段上传碰运气。
- 说清“可用反推”和“原文还原”的区别，别把目标设错。
- 用 Gemini 把视频拆成时间块、字段和 `unknowns`，而不是一段笼统总结。
- 根据素材长度、复用频次、动作密度选择 AI Studio、内嵌视频、Files API、上下文缓存和自定义 `FPS`。
- 把分析稿重写成一条长 prompt、一条短 prompt 和一份 shot list。
- 用一套可复查的验收表判断偏差出在主体、动作、镜头还是节奏。
- 把一次反推沉淀成字段资产，而不是散落在聊天记录里的灵感碎片。

## 2. Gemini 适合做的是“可用反推”，不是“原文还原”

第一次上手最容易错的，就是把目标设成“还原原文”。可视频只是结果层，不是生产日志。你看到的是成片，不是当时的完整创作过程，所以它更适合帮你找回一组高概率生成条件，而不是唯一答案。

| 你想找回什么 | 反推状态 | 为什么 |
| ---- | ---- | ---- |
| 主体、服装、场景、构图、主动作、镜头运动、声音线索 | 通常能反推出可用程度 | 它们直接暴露在画面和音轨里 |
| 节奏、情绪强弱、运动物理、对焦变化、空间关系 | 多数可以逼近，但容易受采样粒度和压缩质量影响 | 这些信息存在，但在快动作和快切里很容易丢失 |
| 风格措辞、摄影语言的具体命名 | 能逼近，但不保证用词一致 | 不同模型会用不同词概括同一视觉现象 |
| `seed`、负面提示词、参考图、局部重绘、后期剪辑顺序、精确焦段和机型参数 | 通常不可见 | 这些信息并不稳定暴露在单条成片表面 |
| 原始输入框里的那一版 prompt 原文 | 几乎不可能可靠还原 | 多条不同 prompt 本来就可能收敛到很像的结果 |

更实际的目标，是拿回一份可复用的生成条件清单。它足够接近，也留得出修改空间，能让你第二次生成时沿着正确方向收敛，这就已经有用了。

## 3. 一条 `8` 秒视频怎么被拆回 prompt

假设你手里有一段 `8` 秒竖屏 AI 视频：夜晚雨巷里，一个穿银灰夹克的年轻女人向前奔跑，中途快速回头，镜头有明显手持微颤，地面有霓虹反光，音轨里能听见急促呼吸和远处轮胎碾过积水的声音。

真做下来，不用十几轮提示，先把流程压成下面这 4 步就够了：

| 步骤 | 你要拿到什么 | 为什么它重要 |
| ---- | ---- | ---- |
| 第一步：观察 | 时间块拆解稿 | 先确定模型有没有看对视频 |
| 第二步：结构化 | `subject / action / camera / audio / unknowns` | 把证据和修辞拆开 |
| 第三步：重组 | 一条长 prompt、一条短 prompt、一份 shot list | 适配不同平台和不同返工粒度 |
| 第四步：再生成 | 第二次成片的偏差列表 | 下一轮到底修哪里，基本看这一步 |

如果 Gemini 的观察稿里出现这些信息：

| 观察稿里的证据 | 更适合生成模型的写法 |
| ---- | ---- |
| vertical smartphone video | vertical smartphone footage |
| subtle amateur micro-shake | handheld with subtle natural micro-shake |
| rain-soaked neon reflections | wet neon reflections on the pavement |
| she glances back mid-stride | she glances back while still running |
| focus briefly hunts during the turn | slight autofocus breathing during the turn |
| urgent breath and distant traffic hiss | layered ambient audio with breath and distant tire hiss |

那它被重写成 prompt 后，大致会长成这样：

```text
Vertical smartphone footage of a young woman in a silver-gray jacket running through a rain-soaked neon alley at night, handheld with subtle natural micro-shake, wet reflections on the pavement, she glances back mid-stride, slight autofocus breathing during the turn, urgent pace, realistic motion physics, layered ambient audio with breath and distant tire hiss, cinematic but grounded.
```

如果目标平台更偏好短 prompt，再压成一条硬字段版：

```text
young woman in silver-gray jacket running through a neon rain alley at night, vertical handheld smartphone shot, subtle micro-shake, glance back mid-run, autofocus breathing, wet reflections, realistic motion physics, urgent urban ambience
```

这两个版本都不是“原文还原”，但已经足够支持下一次生成。要的是这种能继续试、能继续改的逼近，不是文字考古。

## 4. 这条链路为什么能跑通

```mermaid
flowchart LR
        A["AI 视频片段"] --> B["Gemini 视频理解\n视频帧 + 音频 + 时间戳"]
        B --> C["观察框架\n固定字段 + 明确限制"]
        C --> D["结构化证据层\n时间块 / JSON / Schema"]
        D --> E["生成层重组\n长 prompt / 短 prompt / shot list"]
        E --> F["第二次生成\n偏差回写到字段层"]
```

最后能不能像，往往取决于中间这两层有没有拆开：

1. 先把视频拆成结构化证据，避免模型自由发挥式总结。
2. 再把结构化证据改写成生成语言，避免你把整段分析稿原样塞进另一个视频模型。

很多返工都出在这两层没拆开。观察、推断、修辞、平台适配写成一锅，下一轮就不知道该改哪里。

## 5. 把入口、模型和采样先选对

很多教程一上来就盯着某个模型名。实际做反推时，型号的重要性通常排在任务设计后面。官方视频理解页给得更直接：所有 Gemini 模型都支持视频剪辑和自定义 `FPS`，但 `2.5` 系列在这类视频处理上的质量明显更高；与此同时，当前模型列表已经进入 `3.x / 3.5` 时代。与其死背教程标题里的型号，不如把模型当成执行层，用同一条工作流去比较当前可用的档位。

### 5.1 先定输入通道

不同入口解决的是不同问题。手工诊断、重复追问、长视频复用、高动作精查，别混着做。

| 场景 | 推荐入口 | 说明 |
| ---- | ---- | ---- |
| 先拆一条片段，边看边追问 | [Google AI Studio](https://aistudio.google.com/) | 界面反馈快，适合把观察框架跑通 |
| 一次性、很短、很小的片段 | 内嵌视频数据 | 适合临时诊断，不适合长期复用 |
| 同一视频要问很多轮 | Files API | 上传一次后可重复引用；文件 `48` 小时后自动删除，项目总存储上限 `20 GB` |
| 视频超过 `10` 分钟，或要围绕同一素材持续分析 | Files API + Context Cache | 先把重活做一次，后续重复使用缓存 token |
| 公开视频的快速试验 | YouTube URL | 仍是预览入口，只适合粗筛，不适合长期资产化 |

这里有一个容易把人看懵的官方细节：视频理解页在“上传视频文件”一段强调总请求体超过 `20 MB`、视频较长或要复用时应使用 Files API；同页的输入方式总览又把内嵌数据写成小文件 `<100 MB` 的入口。别在这个边界上抬杠。工程上只要你满足下面任一条件，就直接切 Files API：

- 你准备围着同一条视频问两轮以上。
- 视频开始逼近长片段或接近 `1` 分钟。
- 请求体已经不再是“随手试一下”的量级。
- 你后面还要缓存、分段、做结构化输出或沉淀资产。

### 5.2 先选片段，再谈模型

第一次反推，别拿整条长片开刀。先找一个信息密度高、镜头意图单一的短片段。经验上最稳的是下面这种：

- 一个主要主体
- 一个主要动作意图
- 一个相对明确的镜头运动
- 不超过一个核心节奏变化

广告成片、混剪短片、多镜头 montage 不适合第一轮就整段喂进去。先拆片段，再做反推。

### 5.3 默认 `1 FPS` 是起点，不是答案

官方视频理解文档写得很明白：Gemini 默认按 `1 FPS` 抽取视频帧。对多数中低运动内容够用，但它会漏掉快动作、快切和高速镜头细节。你如果总觉得“差一口气”，先别急着怪 prompt，先怀疑采样粒度。

| 调整项 | 什么时候用 | 代价 | 更稳的做法 |
| ---- | ---- | ---- | ---- |
| 默认 `1 FPS` | 首轮看结构、主体、场景 | 快动作细节容易丢 | 先用它扫一遍，再局部加密 |
| 更高 `FPS` | 奔跑、打斗、甩镜、对焦拉扯 | token、延迟和安全拦截概率都会升高 | 只对 `3` 到 `5` 秒的问题片段加密采样 |
| 设置剪辑区间 | 只看某一段动作或某一镜头 | 需要 API 路线 | 用 `start_offset / end_offset` 切问题片段 |
| `MM:SS` 时间戳追问 | 某一瞬间总写不准 | 依赖上一轮先拿到粗分析 | 针对具体时间块追问，而不是整条返工 |

如果你只在 AI Studio 里操作，看不到这些参数，也没关系。最直接的替代方法只有两个：把视频切短，把问题收窄。

### 5.4 预算别靠感觉，要看 `media_resolution`

官方文档给了两组很有用的数字：

- 视频理解页把默认媒体分辨率的视频估成大约 `300 tokens/秒`，低媒体分辨率大约 `100 tokens/秒`，音频约 `32 tokens/秒`。
- 媒体分辨率页把视频视觉帧的预算写成同一量级：Gemini `3` 中，视频 `LOW / MEDIUM` 约 `70 token/帧`，`HIGH` 约 `280 token/帧`。

这两份文档的口径不同，一个在讲“每秒总成本”，一个在讲“每帧视觉预算”，但它们都在提醒同一件事：别把整条长视频一路高精度硬跑到底。先低配扫轮廓，再把预算花在真正有问题的局部。

| 分辨率策略 | 适合什么场景 | 风险 |
| ---- | ---- | ---- |
| `LOW` / 默认低成本扫片 | 先看镜头结构、主体关系、节奏轮廓 | 小字、微表情、细小对焦变化可能丢 |
| `HIGH` | 帧内有小字、细节材质、轻微动作、复杂景深 | 延迟和费用更高，不适合全片默认开 |
| 按部分设置分辨率 | 只给局部关键媒体高预算 | 仅 Gemini `3` 支持按 `Part` 精细配置，且目前仍偏实验性 |

对于视频反推，大多数时候你不需要全程高分辨率。只有当你要读画面内密集文本，或者你确定差异出在极细小的帧内视觉信号时，再把 `HIGH` 打开。

## 6. 强系统提示词为什么有效，但别把它当咒语

Pastebin 上那份 HYPER-GRANULAR VIDEO ANALYSIS 模板之所以有用，不在于它用了多少夸张形容词，而在于它把官方多模态提示原则落得很硬：指令具体、任务拆分、输出格式固定、必要时先描述媒体再推理。

| 官方提示原则 | 在反推工作流里的落法 | 解决的问题 |
| ---- | ---- | ---- |
| 指令要具体 | 明确要求摄影视角、动作物理、音频、镜头行为 | 避免模型退回笼统摘要 |
| 复杂任务要拆步 | 先观察，后重组 | 避免把分析和生成语言混在一起 |
| 输出格式要固定 | 时间块、字段、JSON、schema | 方便追问、对比、程序消费 |
| 先描述再推理 | 先写证据，再谈整体判断 | 减少幻觉式补全 |

与其整段照搬，不如保住它抓住的 5 个字段：

| 字段 | 它帮你补上的盲点 |
| ---- | ---- |
| 音频与对话转写 | 避免只看画面，不看节奏 |
| 禁止使用 IP 名称 | 把角色名替换成可复用的物理描述 |
| 镜头作为角色 | 把相机运动、自动对焦、抖动、甩镜写进结果 |
| 运动物理 | 不再只写“跑了”“转身了”，而是写重心、回弹、冲量 |
| 时间戳分块 | 支持局部返工，而不是整段重来 |

其中最影响复现质量的一条，是“把镜头当成角色”。很多反推结果只写主体和场景，最后生成出来像内容，不像拍法。手持微颤、延迟跟拍、对焦呼吸、突然上扬的追拍，这些都不是装饰，而是视频生成里的硬信息。

## 7. 把工作流拆成 3 段来做

拆开以后，整条链路会稳很多。

### 7.1 第一轮只做观察，不急着要 prompt

第一轮先别急着要 prompt，先确认模型有没有把视频看对。提示结构可以长这样：

```text
Analyze this clip as production notes for a video-generation team.
Return chronological blocks with timestamps.
For each block, include:
- visual framing
- subjects
- action and movement physics
- camera dynamics
- audio and pacing

Then add:
- reusable building blocks
- unknowns

Do not use IP names, actor identities, brand assumptions, or unsupported generation settings.
Only describe what is visible or audible in the clip.
```

这一轮里，`unknowns` 这一栏别省。它就是拿来拦住那些看起来专业、其实没证据的参数。

### 7.2 第二轮优先拿结构化中间层

Markdown 观察稿适合人眼复查，结构化中间层适合比较、存档和程序处理。最简单的做法，是让模型返回 JSON：

```text
Return valid JSON only.
Schema:
{
    "clip_summary": "string",
    "timeline_blocks": [
        {
            "start": "MM:SS",
            "end": "MM:SS",
            "visual_framing": "string",
            "subjects": ["string"],
            "action_physics": ["string"],
            "camera_dynamics": ["string"],
            "audio": ["string"],
            "confidence": "high|medium|low"
        }
    ],
    "reusable_blocks": {
        "subject": ["string"],
        "action": ["string"],
        "camera": ["string"],
        "environment": ["string"],
        "audio": ["string"],
        "style": ["string"]
    },
    "unknowns": ["string"]
}
```

如果你只是临时在 AI Studio 里试，这已经够用。如果你走 API，并且真打算把这套流程变成长期资产，建议直接升级为官方的结构化输出：把 JSON Schema 放进 `response_format`，让模型返回语法上符合 schema 的 JSON。官方文档明确把结构化输出定义为“可预测、类型安全、便于从非结构化内容中抽取结构化数据”的机制；它适合数据提取、结构化分类和智能体工作流。要注意的一点也同样明确：结构化输出保证的是语法正确，不保证语义一定正确，所以应用层仍要做校验。

好处很直接：

- 证据层和改写层被硬拆开，哪一层错一眼就能看出来。
- 同一视频多轮分析时，你可以对比 `timeline_blocks`，而不是人工对整段 prose 做 diff。
- 以后要做资产库、镜头表、批量改写不同平台 prompt，这就是天然中间层。

### 7.3 第三轮再重组生成语言

等证据层站稳后，再让模型做生成层重组：

```text
Using only the supported details from the analysis above, produce:
1. one full generation prompt,
2. one shorter platform-friendly prompt,
3. one shot list,
4. one note listing what should remain unspecified.

Do not invent seed values, camera specs, negative prompts, or editing steps that were not evidenced in the video.
```

这一轮要做的，就是把分析语言压回生成语言：去掉解释腔，保留物理对象、动作、镜头和节奏。

## 8. 怎样把分析稿改写成真正能投喂的视频 prompt

分析稿到 prompt，最好分 3 层落笔。否则锚点、镜头和气氛很容易写成一锅。

| 层 | 该放什么 | 不该放什么 |
| ---- | ---- | ---- |
| 第一层：硬锚点 | 主体、服装、场景、主动作、稳定空间关系 | 情绪化修辞、没证据的镜头参数 |
| 第二层：镜头与物理 | 景别、机位、跟拍、抖动、对焦呼吸、重心转移、碰撞回弹 | “高级感”“电影感”这类空泛概括 |
| 第三层：气氛与节奏 | 光线、材质、环境声、对白、节拍、真实度限制 | `seed`、负面提示词、后期流程猜测 |

压成骨架，可以长这样：

```text
[主体 + 外观] in [空间 + 光线]，执行 [主动作 + 动作目标]；
[镜头行为 + 运动物理 + 对焦变化]；
[音频 / 节奏 + 质感限制]。

Leave unspecified: [没有证据的镜头参数 / seed / 后期步骤]
```

这里最常见的误写有 3 种：

- 把解释意味很强的词，误当成证据。比如 `amateur` 更像作者判断，`natural micro-shake` 更像屏幕上真能观察到的镜头状态。
- 把镜头现象写成作者解说。`focus briefly hunts` 如果证据已经足够，可以直接压成 `autofocus breathing`。
- 把声音当背景气氛删掉。很多时候，声音不是装饰，而是在固定动作节奏。

还有一类信息，宁可先空着：

- 具体焦段、传感器、机型参数
- `seed`、负面提示词、参考图、局部重绘流程
- 后期剪辑、调色和音效层里没有直接证据的制作细节

这些东西当然会影响成片，但视频没给够证据时，硬塞进去只会让 prompt 更像行话，不会让结果更像原片。

要从正向写 prompt、拆镜头表和稳定出片这条线建立手感，可以接着读 [Seedance 2.0 视频制作实战指南：从提示词到分镜的全流程教程](../video/seedance-2-video-production-guide.md)。那篇更偏“怎么拍”这一侧。

## 9. 常见失败与修复

| 现象 | 常见原因 | 更稳的修法 |
| ---- | ---- | ---- |
| 输出像影评，不像 prompt | 提示没固定字段，回答退化成概述 | 改成时间块 + 固定字段 + 二次重组 |
| 动作写得笼统，生成后不真实 | 没要求运动物理和重心转移 | 补 `weight transfer`、`momentum`、`impact feedback` |
| 镜头语言几乎没写 | 模型把注意力都放在主体上了 | 强制单列 `camera_dynamics`，并局部追问镜头段 |
| 快动作总丢细节 | 默认采样太粗，片段又太长 | 缩短片段；如走 API，再提升 `FPS` |
| 声音写成情绪词，节奏还是不对 | 只写画面，没有要求音频细分 | 把 dialogue / ambience / impacts 分开写 |
| 一轮分析成本太高，后面懒得继续 | 一开始就把长视频全量高精度处理 | 先低成本扫全片，再把预算集中到问题片段 |
| 输出里出现角色名或 IP 名 | 约束不够硬，或模型被视频上下文带跑 | 在观察层和重组层都重复“不要使用 IP 名称” |
| 生成结果只像风格，不像动作 | 你把分析稿整段照抄，没有做字段提纯 | 回到 `subject / action / camera / audio` 四层再拼 |
| 长视频越分析越糊 | 多镜头、多任务混在一次回答里 | 先分段，再汇总成镜头表或片段库 |

### 9.1 用一张验收表决定下一轮改哪里

验收别靠感觉。每轮都要知道自己修的是哪一层。

| 验收维度 | 过线标准 | 不过线时先改哪里 |
| ---- | ---- | ---- |
| 主体锚点 | 人物、服装、场景和空间关系大体对上 | 回到 `subject` / `environment` |
| 动作物理 | 起势、转折、停顿、回弹基本一致 | 补 `action_physics` |
| 镜头语言 | 景别、跟拍、抖动、对焦变化看得出同一种拍法 | 单独重写 `camera_dynamics` |
| 节奏与声音 | 速度感、呼吸、环境噪声或击打点没跑偏太多 | 回到 `audio` / `pacing` |
| 不确定性纪律 | 第二次 prompt 没偷塞 `seed`、焦段、品牌或后期猜测 | 扩大 `unknowns`，不要继续补猜 |

如果 `5` 项里有 `3` 项不过线，就回到分析稿，不要继续磨长 prompt。问题大多出在证据层，不在修辞层。

## 10. 把一次反推沉淀成字段资产库

反推做过十来次之后，最耐用的通常不是整条完整 prompt，而是一组会反复复用的字段。把它们存成可检索记录，比散落在聊天历史里靠谱得多。

| 字段 | 记录什么 | 为什么要单独存 |
| ---- | ---- | ---- |
| `subject` | 主体身份、外观、服装、姿态 | 多数平台最先稳定复现的层 |
| `action` | 主动作、次级动作、重心转移、碰撞反馈 | 动作像不像，往往在这一层分胜负 |
| `camera` | 景别、机位、运动、对焦变化、手持感 | 很多“像不像原片”其实输在这里 |
| `environment` | 场景、材质、天气、颜色关系 | 方便跨项目复用同类空间和光线 |
| `audio` | 对白、环境声、节奏、声场提示 | 视频节奏经常不是画面单独决定的 |
| `finish` | 质感、媒介感、真实度、风格限制 | 适合给不同平台做最后一层口味适配 |
| `unknowns` | 这次无法可靠确认的部分 | 防止下一轮把猜测误当事实 |
| `evidence` | 哪个时间段支持这条判断 | 方便回看、复查和团队协作 |

一个够用的最小模板，可以长这样：

```yaml
clip_id: neon-alley-run-001
source_type: ai-generated
subject:
    - young woman in silver-gray jacket
action:
    - running forward through wet alley
    - glances back mid-stride
    - visible weight shift before the turn
camera:
    - vertical handheld framing
    - subtle micro-shake
    - autofocus breathing during the turn
environment:
    - neon reflections on wet pavement
    - night alley with compressed depth
audio:
    - urgent breathing
    - distant tire hiss through puddles
finish:
    - cinematic but grounded
unknowns:
    - exact lens length
    - seed and negative prompt
evidence:
    - 00:00-00:03: handheld run-up and wet reflections
    - 00:03-00:05: glance-back plus focus breathing
verification:
    first_regen: partial_match
    next_fix: strengthen delayed camera tracking
```

整理完之后，回到原视频前 `3` 秒，对照 `subject` 和 `camera` 两栏做一次 spot-check。只要这两栏没有凭空长出新内容，这份初稿通常就站得住。

想把这些字段收进真正可搜索、可复用的资产层，可以接着读 [Prompts.chat：开源提示词平台、自托管方案与 MCP 集成完全指南](./llm/prompts-chat-open-source-prompt-library-guide.md)。那篇更适合处理 prompt 片段的沉淀和检索。

## 11. 练手顺序，可以这样排

### 练习 1：单镜头短片

素材控制在 `8` 秒以内，主体单一、动作清晰即可。这一轮只看拆解是否干净，不看文字漂不漂亮；`subject / action / camera / audio / unknowns` 五层必须各自落位。

### 练习 2：高动作片段

把素材切到 `3` 到 `5` 秒，重点练时间戳追问。走 API 的话，可以顺手试一版更高 `FPS`。如果更高 `FPS` 并没有帮你多拿到一条新的动作证据，问题多半不在采样，而在提问角度。

### 练习 3：同一分析稿投两个生成器

把同一份结构化分析稿分别改成长版和短版 prompt，投给两个不同平台，看哪个更吃叙述式、哪个更吃字段式。这种对照很容易暴露平台偏好，也能帮你区分“平台口味差异”和“字段提纯还不够”。

### 练习 4：多镜头视频做镜头表

选一段 `20` 到 `30` 秒、至少有 `3` 个镜头变化的视频。先拆成镜头表，再决定哪些镜头值得单独反推，哪些只需要做节奏和情绪参考。完成这一步后，你就不再是把所有信息塞回一个超长 prompt，而是在拆若干条可执行的镜头任务。

## 12. 练完之后，用这 5 个问题自测

如果你准备把这套方法拿去真的拆一条视频，先问自己这 5 个问题：

1. 我现在追的是“可用反推”，还是还在偷偷追“原文还原”？
2. 这条视频里，哪些信息是证据，哪些只是我主观补上的解释？
3. 如果第二次生成动作不对，我会先回到 `action_physics`，还是还在乱加风格词？
4. 这条素材到底该用 AI Studio、内嵌视频、Files API，还是 Files API 加缓存？
5. 我最后留下的是一条 prompt，还是一组以后还能继续复用的字段资产？

这 `5` 题里只要有 `2` 题答不稳，就先别追求“更像”。回到前面的工作流，把证据层重新站稳，通常比继续磨词更省时间。

## 13. 这套方法适合谁，不适合谁

### 13.1 最适合的场景

- 拆自己以前做过、但 prompt 已经散失的 AI 视频
- 学某类镜头语言和动作组织方式，而不是盲猜
- 给团队做二次创作 briefing，把“像这种感觉”变成结构化描述
- 建内部 prompt 素材库，把好片里的主体、镜头和节奏拆成可复用字段

### 13.2 不适合的场景

- 想做法证级的“原文还原”
- 想从结果视频里推回所有隐藏参数
- 想直接复制商业作品的完整创意流程
- 想把它当成版权、商标或合规判断工具

如果你要把这套方法放进真实商业环境，版权、商标、人物肖像和平台条款仍是另一套问题。模型能描述出来，不代表你就应该原样复刻。

这些字段真正落到出片、转场和后期拼接里是什么样，可以接着读 [AI 广告制作实验：6 小时 vs 30 万美元，广告行业会被颠覆吗？](../video/ai-advertising-production-6-hours-vs-300k.md)。那篇更接近真实视频制作链路里的取舍。

## 14. 结论：把它当成“视频版 prompt diff”来用

把这件事看成“视频版 prompt diff”会好理解很多。Gemini 先把成片里可见、可听、可追问的证据摊开，后面的工作再把这些证据整理回生成模型能消费的字段和镜头指令。

返工通常发生在层级没拆开的时候。把观察、`unknowns`、结构化中间层、生成改写和二次验证分开以后，偏差会落到更具体的位置。最后留下来的，也不只是一条碰巧跑通的 prompt，而是一份下次还能接着改的工作底稿。

第一次上手，按下面这 `6` 步走，一般会顺很多：

1. 先选一段 `5` 到 `12` 秒、主体单一、动作明确的片段。
2. 用 AI Studio 或最轻量入口跑第一轮观察，不急着要最终 prompt。
3. 拿到时间块、字段和 `unknowns` 之后，再转成 JSON 或结构化输出。
4. 基于中间层重组成长 prompt、短 prompt 和 shot list。
5. 用第二次生成结果做验收，而不是被分析稿的文采迷惑。
6. 能复用的字段立刻进资产库，别让它烂在聊天窗口里。

## 参考资料

- [Google Gemini 视频理解文档](https://ai.google.dev/gemini-api/docs/video-understanding)
- [Google Gemini Files API 文档](https://ai.google.dev/gemini-api/docs/files)
- [Google Gemini 上下文缓存文档](https://ai.google.dev/gemini-api/docs/caching)
- [Google Gemini 媒体分辨率文档](https://ai.google.dev/gemini-api/docs/media-resolution)
- [Google Gemini 结构化输出文档](https://ai.google.dev/gemini-api/docs/structured-output)
- [Google Gemini 模型列表](https://ai.google.dev/gemini-api/docs/models)
- [Google Gemini 提示工程文档](https://ai.google.dev/gemini-api/docs/prompting-strategies)
- [Google Gemini 更新日志](https://ai.google.dev/gemini-api/docs/changelog)
- [Google AI Studio](https://aistudio.google.com/)
- [社区系统提示词模板：HYPER-GRANULAR VIDEO ANALYSIS](https://pastebin.com/H8DeXq1G)
