---
title: "GPT Image 2 提示词完全指南：四大开源库精华合集"
date: 2026-05-01T13:11:58+08:00
slug: "gpt-image-2-prompts-complete-guide"
description: "基于 EvoLinkAI、YouMind、freestylefly 与 Anil-matcha 四个开源仓库，系统拆解 GPT Image 2 提示词的选库方法、结构化写法、高频场景模板与常见误区。"
draft: false
categories: ["技术笔记"]
tags: ["AI绘图", "GPT-Image-2", "提示词工程", "图像生成", "OpenAI"]
---

> **目标读者**：已经在用 AI 生图，想把提示词从“能出图”提升到“更稳定、更可复用”的设计师、运营、独立开发者与内容创作者
> **核心问题**：四个热门 GPT Image 2 提示词仓库，到底该先看哪一个？优秀案例真正值得抄的是什么？如何把零散 prompt 提炼成自己的稳定模板？
> **数据说明**：文中仓库规模、 stars 与仓库结构，均以 2026 年 5 月 2 日可公开访问的 GitHub 页面为准；本文统一使用官方命名 **GPT Image 2**，不沿用社区里的非官方代称
> **预计阅读时间**：18 - 25 分钟

---

## 🎯 本文目标

完成本文后，你应该能：

- 用 30 秒判断四个仓库各自最适合的任务
- 看懂优秀 prompt 的结构，而不是只会照抄长文本
- 为人像、广告、电商、UI / 信息图、参考图改写 5 类高频任务写出稳定起点
- 避开中文排版、跨图一致性、构图失控、商用归属这 4 类高频坑

## 1. 先说结论：四个仓库分别该怎么用

如果你只想先拿到一个可执行结论，可以先看下面这张表。

| 仓库 | 当前 GitHub 页面显示 | 核心价值 | 最适合先看的场景 |
| ------ | ------ | ------ | ------ |
| [EvoLinkAI/awesome-gpt-image-2-prompts](https://github.com/EvoLinkAI/awesome-gpt-image-2-prompts) | 约 11k+ stars，160+ 公开案例 | 精选案例密度高，广告、电商、产品图都比较“能直接参考” | 电商主图、广告 KV、产品摄影、写实人像 |
| [YouMind-OpenLab/awesome-gpt-image-2](https://github.com/YouMind-OpenLab/awesome-gpt-image-2) | 约 4.1k+ stars，仓库页显示超过 3600 条提示词，支持 17 种语言 | 规模最大，检索与筛选友好，适合先找相似任务 | 找灵感、找同类案例、做多语言检索、快速浏览趋势 |
| [freestylefly/awesome-gpt-image-2](https://github.com/freestylefly/awesome-gpt-image-2) | 约 2.9k+ stars，367 个案例，强调 Prompt-as-Code | 结构化程度最高，最适合沉淀模板与接 Agent | UI、信息图、海报、批量化出图、生产流程 |
| [Anil-matcha/Awesome-GPT-Image-2-API-Prompts](https://github.com/Anil-matcha/Awesome-GPT-Image-2-API-Prompts) | 约 1.8k+ stars，附 API 快速上手与工程提示 | 最像开发者手册，适合把 prompt 接进 API | API 集成、参数排查、工程落地、开发者快速验证 |

再压缩成一句话：

- **想找现成案例**：先看 YouMind。
- **想做电商和广告**：先看 EvoLinkAI。
- **想沉淀可复用模板**：先看 freestylefly。
- **想接 API 跑起来**：先看 Anil-matcha。

### 1.1 按任务倒推，更容易选对库

| 你的任务 | 第一站 | 为什么 |
| ------ | ------ | ------ |
| 电商主图、品牌广告、产品故事板 | EvoLinkAI | 公开案例够集中，构图、光线、陪体安排都比较完整 |
| 先找“别人已经做成过”的相似画面 | YouMind | Web Gallery + 分类浏览 + 语言筛选，找样本最快 |
| UI 截图、信息图、说明海报、拆解图 | freestylefly | 强项不是“词多”，而是把布局与文字层级写成结构 |
| 参考图改写、API 批量生成、接业务系统 | Anil-matcha | 有直接可用的 API 例子和更工程化的说明 |
| 想把零散 prompt 变成自己的模板库 | freestylefly → Anil-matcha | 先结构化，再工程化 |

## 2. 先统一判断标准：别被“超长 prompt”迷惑

研究这四个仓库之后，一个非常清楚的结论是：**真正稳定的 prompt，不是形容词越多越好，而是约束越明确越好。**

对 GPT Image 2 来说，最有价值的约束通常只有 5 类：

1. **任务类型**：你到底在生成什么，是人像、广告、UI 截图、信息图，还是参考图改写。
2. **主体锚点**：画面中心到底是谁或是什么，必须说清楚。
3. **结构约束**：镜头、构图、布局、模块数量、文字区域、面板数量。
4. **材质与光线**：它们决定画面的可信度，而不是“高级感”这种空词。
5. **输出边界**：哪些必须保留，哪些绝对不要出现。

把这 5 类信息压成一个公式，通常比堆一段散文更稳定：

```text
任务类型
+ 主体锚点
+ 结构约束
+ 光线 / 材质 / 色彩
+ 文字与语言要求
+ 保留项 / 排除项
```

### 2.1 一个好 prompt，真正该拆的不是“文采”，而是层次

下面这张表，适合拿来逆向拆解大多数优秀案例。

| 层次 | 该写什么 | 作用 | 人像示例 |
| ------ | ------ | ------ | ------ |
| 任务类型 | editorial portrait / product ad / UI mockup | 先把模型带到正确任务空间 | 写实街头人像 |
| 主体锚点 | subject、product、interface、map | 锁定中心对象 | 年轻女性、便利店门口、中景 |
| 结构约束 | lens、shot、layout、panel count、grid | 防止构图漂移 | 35mm、中景、眼平视角 |
| 光线与材质 | neon、fluorescent、glass reflection、fabric texture | 决定真实感与氛围 | 荧光灯 + 霓虹、玻璃反射、皮肤纹理 |
| 文字要求 | language、line count、headline / label hierarchy | 决定 UI / 海报 / 信息图是否可用 | 简体中文、短标签、不出现乱码长段落 |
| 输出边界 | keep / avoid | 解决翻车点 | 无塑料皮肤、无水印、无多余文字 |

## 3. GPT Image 2 值得用，但也要说清边界

社区案例确实说明了 GPT Image 2 在几个方向上很强，但强不代表无条件稳定。更稳妥的说法如下：

| 能力方向 | 社区案例体现 | 更稳妥的判断 |
| ------ | ------ | ------ |
| 文字渲染 | 信息图、海报、UI 截图里，中文与日文的可读性明显提高 | **多语言文字渲染显著好于早期模型**，但高密度中文正文仍建议减少字数或多轮迭代 |
| 风格跟随 | 摄影、插画、排版、游戏截图都能找到较强案例 | **能较好跟随风格方向与版式意图**，但不等于可以精确复制某位作者作品 |
| 参考图改写 | 地产平面图转 3D、角色设定稿、产品换场景都比较常见 | **参考图编辑能力实用**，前提是保留项和改动项要写得足够具体 |
| 一致性 | 多格海报、角色表、商品多视图案例增多 | **一致性比早期模型更强**，但仍需锁定脸型、服装、镜头和配色 |
| 商业出图 | 电商主图、广告 KV、产品故事板案例很多 | **不少输出已能达到商业草稿甚至接近终稿质量**，但上线前仍要人工审校 |

换句话说，GPT Image 2 的价值不在“神奇”，而在**它终于足够适合做结构化控制**。这也是为什么 freestylefly 那种 Prompt-as-Code 路线会特别重要。

## 4. 研究四个仓库后，我建议你重点学这 5 种写法

### 4.1 写实人像：先锁镜头、光线和皮肤，再谈气质

EvoLinkAI 和 Anil-matcha 里，人像类 prompt 的共同点不是“词藻丰富”，而是会先把以下几件事写死：

- 用什么镜头语言拍：`35mm`、`85mm`、`iPhone`、`old CCD`
- 画面距离和视角：近景、中景、俯拍、眼平、侧脸
- 光线混合关系：荧光灯、霓虹、窗光、闪光灯
- 皮肤要保留什么：自然肤理、毛孔、高光、不过度磨皮
- 背景要承担什么作用：反射、虚化、环境叙事

你可以从下面这个**自写骨架**开始，而不是直接复制别人几百字的长 prompt：

```text
Create a candid editorial portrait of [subject] in [environment].
Camera: [35mm / 85mm / iPhone / CCD], [framing], [angle].
Lighting: [mixed fluorescent and neon / soft window light / harsh flash].
Skin and texture: natural skin texture, visible pores, realistic highlights, no plastic skin.
Wardrobe and pose: [outfit], [pose], [expression].
Background: [2-3 key environment details], shallow depth of field, realistic reflections if needed.
Mood and grade: [cinematic / nostalgic / documentary / casual snapshot].
Output boundary: no watermark, no extra text, no synthetic beauty-filter look.
```

这类 prompt 为什么容易稳定？因为它先解决了“像什么设备拍的”“像什么光线里拍的”，而不是一上来写“高级、唯美、电影感”。

**推荐先看：**

- EvoLinkAI 的人像摄影案例，适合学混合光源与环境叙事
- Anil-matcha 的 `RAW iPhone`、`CCD`、`cinematic minimal portrait`，适合学设备感与材质感

### 4.2 产品广告与电商主图：先写主体结构，再写陪体与叙事

EvoLinkAI 最强的一块，是产品摄影、广告 KV 和分镜式电商图。它的优秀案例通常有 4 个共同点：

- 主体尺寸、角度、材质写得很清楚
- 陪体不是随便加，而是服务品牌叙事
- 光线系统先于风格形容词
- 文案区有没有文字，会被显式说明

适合产品广告的骨架可以这样写：

```text
Create a premium product advertising image for [product].
Hero object: [shape, material, color, orientation, branding zone].
Composition: [centered / three-quarter view / split layout / 9-panel storyboard].
Supporting props: [2-4 props], each with a narrative role.
Lighting: [low-key studio / soft daylight / hard edge light / glossy reflections].
Surface and environment: [wet ground / marble / paper texture / desk / void background].
Color system: [3-5 colors].
Typography rule: [no text / short headline only / Chinese labels with short copy].
Output style: [commercial photography / collectible maquette / storyboard board].
Avoid: cheap e-commerce look, random props, unreadable text, broken geometry.
```

如果你在做电商，不要只抄成片，还应该反向问自己 3 个问题：

1. 这张图的**主体描述**里，哪些词真正决定了产品形状？
2. 这张图的**陪体**是装饰，还是在解释使用场景？
3. 这张图如果要改成 9:16 分镜或 4:5 主图，哪些约束必须一起改？

### 4.3 UI、信息图与海报：布局优先，文字数量优先，风格最后写

这部分是 freestylefly 和 YouMind 最值得看的地方。很多人把 UI 类 prompt 写成“赛博朋克 + 高级 + 科技感”，结果生成出来只是漂亮废图。真正可用的 UI / 信息图 prompt，通常会先写：

- 画布比例
- 区块数量
- 标题与副标题层级
- 每块里应该有什么
- 文本语言和密度

如果你要做中文信息图，建议直接用结构化格式起手：

```json
{
  "type": "infographic or UI mockup",
  "goal": "explain [topic] for [audience]",
  "canvas": {
    "aspect_ratio": "4:5",
    "background": "clean paper texture"
  },
  "layout": {
    "header": "title + subtitle",
    "main_visual": "one central diagram or hero image",
    "modules": 4,
    "footer": "legend or CTA",
    "text_language": "Simplified Chinese",
    "text_density": "short labels only"
  },
  "visual_system": {
    "style": "editorial / futuristic / museum board",
    "palette": ["#0F172A", "#E2E8F0", "#38BDF8"]
  },
  "must_keep": [
    "clear hierarchy",
    "consistent icon style",
    "readable labels"
  ],
  "avoid": [
    "crowded layout",
    "fake tiny paragraphs",
    "random decoration"
  ]
}
```

中文界面尤其要注意两点：

- **长句不如短标签稳定**。先做可读标签，再做长文案。
- **一定要写清文字层级**。比如“1 个主标题、4 个模块标题、每模块 2 行短说明”，比“做一张很高级的信息图”有效得多。

### 4.4 参考图改写：先写保留项，再写改动项

YouMind 与 Anil-matcha 都有不少参考图改写案例，例如平面图转 3D、人物换风格、产品换场景。这类任务最怕的一句话，是“别改太多，只改一点点”。模型并不知道那“一点点”到底是哪一点。

更稳定的写法是：

```text
Use the provided reference image as the structural base.
Preserve: [identity / silhouette / room layout / product geometry / visible labels].
Change only: [camera angle / rendering medium / environment / outfit / mood].
Consistency constraints: same face shape, same color family, same object proportions.
If text must remain, keep exactly these labels: [list].
Avoid adding new objects, changing the composition logic, or altering the core structure.
```

这类 prompt 的核心不是修饰词，而是**保留清单**。你列得越清楚，结果越稳。

### 4.5 角色设定与系列一致性：不要只写“same character”

freestylefly、EvoLinkAI 和 YouMind 里，都能看到角色卡、表情网格、多面板系列图。这里最常见的误区，是只写一句“same character in all panels”。这不够。

如果你要做系列一致性，至少锁定：

- 脸型和五官关系
- 发色、发型、服装轮廓
- 主配色
- 视角和画幅
- 每格允许变化的部分

可以直接用这个骨架：

```text
Create a multi-panel character sheet for the same character.
Identity lock: same face shape, same hair color and hairstyle, same outfit silhouette, same color palette.
Panel structure: [number] panels, each showing [expression / pose / view].
Allowed variation: [facial expression / hand pose / accessories].
Not allowed to change: [age appearance / body proportions / costume design].
Layout: clean reference sheet, readable labels, consistent spacing.
```

## 5. 这四个仓库，正确的使用顺序不是“四选一”

我更建议你把它们串起来用，而不是互相替代。

### 5.1 第一步：在 YouMind 找相似任务

YouMind 的价值，首先是大。它更像一个**提示词搜索入口**，适合你快速回答两个问题：

- 有没有人已经做过和我类似的任务？
- 这个任务更常见的成图方向是什么？

如果你此时还不知道 prompt 怎么写，先别写，先找 5 个相似案例。

### 5.2 第二步：去 EvoLinkAI 看“成熟案例”

EvoLinkAI 不是最大的，但它很适合做**精选案例本**。你会更容易在里面看到完整的广告图、电商图、人像摄影图，而不是很多零散条目。

如果你的目标是：

- 电商主图
- 广告 KV
- 产品故事板
- 真实摄影感的人像

那 EvoLinkAI 往往比直接在大库里翻更省时间。

### 5.3 第三步：用 freestylefly 把案例改造成模板

这是最关键的一步。你不能永远依赖“看到一个案例，复制一次 prompt”。只要任务进入重复阶段，你就应该把 prompt 改写成自己的结构。

freestylefly 的 Prompt-as-Code 思路，本质上是在逼你回答：

- 哪些是**业务变量**
- 哪些是**视觉常量**
- 哪些是**布局协议**

一旦分清这三类，你就能把 prompt 接进表单、脚本、Agent 或批量流程。

### 5.4 第四步：在 Anil-matcha 里落到 API

当你已经有一版稳定模板，Anil-matcha 的价值就很直接了：它提供了足够接近开发现场的 API 说明、基础用法和 prompt 工程提示。

最小可运行示例可以长这样：

```python
from openai import OpenAI

client = OpenAI()

result = client.images.generate(
    model="gpt-image-2",
    prompt=prompt,
    size="1024x1536",
    quality="high",
    n=1,
)

print(result.data[0].url)
```

真正进入生产后，你要做的不是“再找更多 prompt”，而是：

- 参数化业务变量
- 做 A / B 测试
- 保留失败样本
- 逐步收紧模板

## 6. 常见误区与避坑清单

下面这些坑，在四个仓库里都能找到反例。

| 坑点 | 常见错误写法 | 为什么会翻车 | 更稳的改法 |
| ------ | ------ | ------ | ------ |
| 只写风格，不写结构 | “做一张高级的赛博朋克 UI” | 模型不知道画面要分几块、哪块放文字 | 先写比例、模块数、标题层级、语言 |
| 想要人物一致，只写一句 “same person” | “same person in all images” | 五官、服装、镜头都没锁定 | 把脸型、发型、服装、画幅、允许变化项分别写清 |
| 形容词堆太多 | “ultra detailed, masterpiece, breathtaking...” | 有噪声，缺约束 | 少写空话，多写镜头、材质、构图 |
| 中文文案太长 | “生成一张带完整中文说明的海报” | 小字容易失真 | 改成短标题、短标签、模块化信息 |
| 只说“不要改别的” | “keep everything the same except...” | 没定义 keep 的具体内容 | 列出 preserve 清单与 change 清单 |
| 直接搬社区 prompt 商用 | 完整复用原始案例里的品牌、文字和视觉要素 | 可能踩到原作者、商标、人物或平台规则 | 把方法学回来，重写成自己的模板，再核验授权 |

### 6.1 中文文本要特别克制

GPT Image 2 的文字渲染已经很强，但中文场景依然要注意：

- 海报和信息图尽量使用**短标题 + 短标签**，不要一口气塞密集正文。
- 明确写 `Simplified Chinese`、标题数量、每个模块几行字。
- 如果必须做长中文内容，优先先出**结构稿**，再做二次编辑或后期精修。

### 6.2 商用前先看许可与来源

这四个仓库本身的许可并不等于其中所有社区案例都能无条件商用。尤其要分清三件事：

- 仓库的开源许可
- 某条 prompt 与示例图的原始作者归属
- 其中是否出现了品牌、人物、作品风格、商标或平台素材

更稳妥的做法是：**学结构，不直接搬整段案例。**

### 6.3 同一任务，差 prompt 和好 prompt 的区别

很多人并不是不会写，而是还在用“愿望型 prompt”。下面这张表可以直接拿来改写自己的输入。

| 任务 | 容易失败的写法 | 为什么不稳 | 更稳的改写方向 |
| ------ | ------ | ------ | ------ |
| 胶片感人像 | “帮我生成一张有电影感的 35mm 美女写真” | 只有风格愿望，没有镜头、光线、环境和皮肤约束 | 改成“35mm、中景、混合荧光与霓虹、自然肤理、玻璃反射、无塑料感”这类可执行约束 |
| 中文信息图 | “做一张很高级的中文 AI 信息图海报” | 没说比例、模块数、文字层级，最容易变成漂亮废图 | 改成“4:5 画幅、1 个主标题、4 个模块、短标签、简体中文、纸张质感背景” |
| 电商主图 | “给我的产品做一张高级广告图” | 主体角度、材质、陪体角色都没锁定，风格会飘 | 改成“主体三分之二视角、深色背景、两件陪体、镜面台面、无额外文字、商业摄影风格” |
| 参考图改写 | “别改太多，只换个风格” | 模型不知道什么不能动 | 改成“保留构图、主体几何、可见标签；只改材质、环境和光线” |

如果你发现一条 prompt 很难复用，通常不是因为它太短，而是因为它把“想要什么气质”写得太多，把“什么不能变”写得太少。

## 7. 一条可执行的上手路线：30 分钟把灵感变成自己的模板

如果你今天就要开始用，建议按这个顺序走。

1. 在 YouMind 找 5 个相似任务，先看别人都怎么定义目标。
2. 去 EvoLinkAI 或 Anil-matcha 各挑 1 - 2 个成熟案例，观察主体、镜头、光线、文字约束。
3. 把这些案例重写成一个**自己的骨架模板**，删掉与业务无关的描述。
4. 再用 freestylefly 的思路，把它拆成变量、常量、布局协议。
5. 最后接 API，记录 3 组成功样本和 3 组失败样本。

如果你照这个流程走，得到的不是“一次性 prompt”，而是一套**能继续迭代的视觉协议**。

### 7.1 一份适合团队复用的最小检查清单

在把 prompt 放进工作流之前，先确认下面 8 项。

- [ ] 任务类型已经明确，不是笼统的“来一张图”
- [ ] 主体锚点只有 1 个中心，不会互相争夺注意力
- [ ] 画幅、镜头或布局数量已经写明
- [ ] 光线与材质不是空话，而是具体可感知的物理描述
- [ ] 文本语言、标题层级、字数密度已经限定
- [ ] 保留项与禁止项分别列出
- [ ] 商用所需的版权、品牌、人物风险已经审查
- [ ] 成功样本已经沉淀成模板，而不是只保存在聊天记录里

### 7.2 用这 3 个练习检验自己是不是真的会写

如果你想确认自己学到的不是“看懂了”，而是“真的会写了”，建议立刻做下面 3 个练习。

1. 随便找一个写实人像案例，把原始长 prompt 压缩成 8 行骨架，只保留任务类型、主体锚点、镜头、光线、皮肤、背景、情绪和边界。
2. 选一个电商主图案例，把它拆成“业务变量、视觉常量、布局协议”三栏，判断哪些字段未来应该进表单，哪些字段应该固定在模板里。
3. 找一张参考图改写任务，用 `Preserve / Change only / Avoid` 三段式重写 prompt，确保别人不用看原图也能理解你想保留什么。

做完这 3 个练习后，再回头看社区里的长 prompt，你会更容易分辨哪些内容是结构，哪些只是修辞。

### 7.3 三个发布前高频问题

**Q1：写 GPT Image 2 prompt 时，英文一定比中文更好吗？**

不一定。对于镜头、材质、摄影风格、 UI 结构这类约束，英文通常更稳定；对于你明确希望输出中文标签、中文海报、中文界面的场景，则应显式写 `Simplified Chinese`，并限制文字数量与层级。更实用的做法不是二选一，而是**结构约束用英文，文本要求单独写中文输出规则**。

**Q2：什么时候应该把自然语言 prompt 改成 JSON 或 Schema？**

当你满足下面任一条件时，就该开始结构化：

- 同一类任务要反复生成 3 次以上
- 需要交给团队成员、脚本或 Agent 重复调用
- 输出里有明确的模块数、面板数、文字层级或布局协议

一句话判断：**只要 prompt 开始像“流程”而不是“灵感”，就该结构化。**

**Q3：失败样本有必要保存吗？**

非常有必要。高质量模板往往不是从成功案例里一次提炼出来的，而是从失败案例里知道哪些词不能乱加、哪些约束必须补。最值得保留的失败样本通常有 3 类：

- 文字渲染失败：标题能看，正文崩掉
- 构图漂移：主体和陪体争夺注意力
- 一致性崩坏：多图里人物、服装或产品形态不稳定

## 8. 延伸阅读：如果你想继续把 prompt 用到工作流里

这篇文章聚焦的是 GPT Image 2 提示词本身。如果你接下来要继续往“提示词库治理”“工作流编排”“可视化流程”深入，站内有 3 篇文章值得顺着读下去。

- [prompts.chat：全球最大开源 AI 提示词库完全指南](https://txtmix.com/posts/tech/prompts-chat-open-source-ai-prompt-library/)：如果你想把 GPT Image 2 提示词放回更大的提示词库语境里看，这篇更适合补全“提示词库产品形态”和“提示词分发方式”。
- [LangFlow: 可视化 AI 工作流编排平台](https://txtmix.com/posts/tech/langflow-visual-ai-workflow-builder/)：如果你下一步想把 prompt 接入可视化节点流、API 或 MCP，这篇更适合接着看。
- [Sim Studio：开源 AI Agent 工作流编排平台深度解析](https://txtmix.com/posts/sim-studio-ai-agent-workflow-platform/)：如果你关心提示词如何真正进入 Agent 工作流、节点注册和执行引擎，这篇会更进一步。

## 9. 推荐入口：四个仓库最值得先看的页面

- [EvoLinkAI - E-commerce Cases](https://github.com/EvoLinkAI/awesome-gpt-image-2-prompts/blob/main/cases/ecommerce.md)：适合看产品主图、故事板、电商拍法
- [EvoLinkAI - Ad Creative Cases](https://github.com/EvoLinkAI/awesome-gpt-image-2-prompts/blob/main/cases/ad-creative.md)：适合看广告 KV 与品牌叙事
- [YouMind Web Gallery](https://youmind.com/gpt-image-2-prompts)：适合用分类与筛选先找相似任务
- [freestylefly - templates.md](https://github.com/freestylefly/awesome-gpt-image-2/blob/main/docs/templates.md)：适合把 prompt 改造成结构化模板
- [freestylefly - gallery.md](https://github.com/freestylefly/awesome-gpt-image-2/blob/main/docs/gallery.md)：适合按品类补更多参考
- [Anil-matcha - Resources & API Docs](https://github.com/Anil-matcha/Awesome-GPT-Image-2-API-Prompts#resources--api-docs)：适合直接落 API

## 10. 结语：这 4 个仓库真正教会你的，不是“更长的 prompt”

把四个仓库放在一起看，最重要的收获其实只有一句话：

**好 prompt 不是描述得更华丽，而是控制得更清楚。**

你真正应该带走的，不是某一段别人已经写好的长 prompt，而是下面这条工作流：

1. 先找相似任务。
2. 再拆它的主体、结构、光线与边界。
3. 然后改写成自己的模板。
4. 最后再接进脚本、Agent 或业务系统。

只要做到这一步，提示词就不再是灵感型手艺，而会变成可以复用的工程资产。

---

*说明：本文以公开仓库与公开网页为研究对象，重点提炼方法与结构，不直接转载整段长提示词。原始案例、作者归属、许可证与下架规则，请以各源仓库说明为准。商业使用前，请额外核对原始作者、品牌元素、人物肖像与平台规则。*
