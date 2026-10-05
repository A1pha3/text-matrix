---
title: "Awesome GPT Image 2：17,700 条提示词背后的众包流水线"
date: "2026-05-03T22:51:57+08:00"
slug: "awesome-gpt-image-2-technical-overview"
github_repo: "YouMind-OpenLab/awesome-gpt-image-2"
source_key: "gh:YouMind-OpenLab/awesome-gpt-image-2"
description: "Awesome GPT Image 2 用 GitHub Issue 收稿，Payload CMS 做单一数据源，TypeScript 脚本定时生成 16 种语言 README，收录 17,700+ 提示词。本文拆解其三条并行机制、提示词结构设计与采用建议，全部数据核对自仓库源码与 GitHub API。"
draft: false
categories: ["技术笔记"]
tags: ["OpenAI", "提示词工程", "开源项目"]
---

# Awesome GPT Image 2：17,700 条提示词背后的众包流水线

Awesome GPT Image 2 把"提示词众包投稿"做成了流水线：GitHub Issue 收稿，Payload CMS 做单一数据源，TypeScript 脚本按调度生成 16 种语言 README，目前收录 17,700 条提示词。它真正值得看的不是提示词本身，而是这套"投稿 → 审核 → 同步 → 发布"的分工方式——三个环节靠标签和定时任务衔接，没有一个专职运维。本文拆解这三条机制，并给出可复用的提示词结构模板与采用建议。

## 目录

- [项目总览](#项目总览)
- [GPT Image 2 的能力边界](#gpt-image-2-的能力边界)
- [仓库架构与工程实现](#仓库架构与工程实现)
- [提示词结构设计深度解析](#提示词结构设计深度解析)
- [多语言国际化实践](#多语言国际化实践)
- [如何高效利用这个仓库](#如何高效利用这个仓库)
- [技术局限性与适用边界](#技术局限性与适用边界)
- [采用建议](#采用建议)

## 项目总览

| 指标 | 数据 |
|------|------|
| 仓库名称 | awesome-gpt-image-2 |
| 所属组织 | YouMind-OpenLab |
| GitHub Stars | 9,987（2026-10-01 快照） |
| Forks | 884 |
| 提示词总量 | 17,700（README 统计栏，2026-09-30 生成） |
| README 实际展示 | 126 条（6 条精选 + 120 条常规） |
| 支持语言 | 16 种 |
| 内容许可 | CC BY 4.0 |
| CMS | Payload（外部托管，API Key 认证） |
| 主要语言 | TypeScript |
| 创建时间 | 2026 年 4 月 16 日 |
| 最近推送 | 2026 年 9 月 30 日 |

项目官网（Web Gallery）：[https://youmind.com/gpt-image-2-prompts](https://youmind.com/gpt-image-2-prompts)

> 指标采集自 2026 年 10 月 1 日的 GitHub API 与仓库 README，stars/提示词数为时点值；GPT Image 2 模型能力描述转述自仓库 README 的社区测试总结，非 OpenAI 官方 benchmark，请以最新版本为准。

### 三条并行机制地图

整个系统由三条工作流组成，靠标签和定时任务衔接：

```text
┌──────────────────────────────────────────────────────────────┐
│ 机制 A：内容生产（人 + GitHub Issue）                         │
│   用户填投稿表单（自动打 prompt-submission 标签）              │
│   → 维护者 48h 内审核 → 加 approved 标签                      │
│   产物：带双标签的 Issue                                      │
└──────────────────────────────────────────────────────────────┘
                          ↓ labeled 事件触发
┌──────────────────────────────────────────────────────────────┐
│ 机制 B：CMS 同步（sync-approved-to-cms.ts）                   │
│   解析 Issue 正文 → 下载图片上传 CMS → POST/PATCH 提示词      │
│   产物：Payload CMS 中的结构化数据（单一数据源）               │
└──────────────────────────────────────────────────────────────┘
                          ↓ cron 每 12 小时
┌──────────────────────────────────────────────────────────────┐
│ 机制 C：README 生成（generate-readme.ts）                     │
│   按 locale 从 CMS API 拉取 → 精选优先排序 → 写 README_*.md   │
│   产物：16 份 README 文件（仓库门面）                          │
└──────────────────────────────────────────────────────────────┘
```

三条机制各管一段：A 管内容质量，B 管数据一致性，C 管发布覆盖面。它们之间唯一的耦合点是 CMS——A、B 什么时候跑都行，C 错过一次等 12 小时即可，任一环节延迟不会阻塞其他两个。

## GPT Image 2 的能力边界

仓库 README 对 GPT Image 2 的介绍只有一句：OpenAI 的下一代图像模型，代号 "duct-tape"。正式技术报告没有公开，README 列出的能力全部标注为社区测试反馈，集中在六个场景：

**像素级文字渲染**。中、英、日长句排版基本不出错字、不变形。文字渲染是图像生成模型的老大难，这也是这个提示词库敢把"文本/排版"做成一个主体分类的前提。

**跨图像一致性**。同一角色、风格、IP 在多张图之间保持一致，故事板、IP 形象、产品系列图这类需要多图协同的活儿才跑得起自动化。

**商用级插画**。插画输出不需要人工精修就能直接用。

**艺术风格诱导**。README 的原话是"唤起一种风格的感觉，而不是近似参考图"——按风格的语言重新组织画面，而不是复刻笔触。

**故事板与产品系列**。多分格、多面板输出。

**多语言排版**。社交卡片、Banner、海报一次出图带多语言文字。

> 仓库自己的 FAQ 把 GPT Image 2 写成"Google 的多模态模型"，与 README 和仓库描述（OpenAI）冲突。这个仓库的文档更新明显滞后于代码，查证时建议以源码为准，下文还会遇到两处同类问题。

## 仓库架构与工程实现

### 技术栈选型

```text
主语言：TypeScript（ESM）
包管理：pnpm 9.15.9
运行依赖：
  - node-fetch ^3.3.2     # CMS API 调用
  - qs-esm ^7.0.2         # Payload REST API 查询串构造
开发依赖：
  - @octokit/rest ^20.0.2 # GitHub Issue 交互
  - dotenv ^17.2.3
  - typescript ^5.3.3
  - tsx ^4.7.0            # 免编译直接执行
```

CMS 本体不在仓库里——是 YouMind 托管的 Payload 实例，地址和 API Key 从环境变量 `CMS_HOST`、`CMS_API_KEY` 注入。仓库里跑的只有两个 npm script：`generate` 和 `sync`，入口脚本分别只有 57 行和 246 行，逻辑主体在 `scripts/utils/` 四个模块里：`cms-client.ts`（CMS API 封装）、`markdown-generator.ts`（README 渲染）、`i18n.ts`（界面文案翻译）、`image-uploader.ts`（图片上传）。最大的一个文件反而是 i18n 翻译文案，近 1,400 行，大多是字符串。仓库管数据流，CMS 管数据。

### 目录结构

```text
awesome-gpt-image-2/
├── .env.example              # 环境变量示例
├── .github/
│   ├── workflows/            # 4 个 workflow（见下）
│   └── ISSUE_TEMPLATE/
│       └── submit-prompt.yml # 投稿表单，自动打 prompt-submission 标签
├── docs/
│   ├── FAQ.md
│   ├── CONTRIBUTING.md       # 投稿指南
│   └── LOCAL_DEVELOPMENT.md
├── public/images/            # 封面等静态图（提示词成品图不进 Git）
├── scripts/
│   ├── generate-readme.ts    # 机制 C
│   ├── sync-approved-to-cms.ts # 机制 B
│   └── utils/                # cms-client / markdown-generator / i18n / image-uploader
├── package.json
└── README*.md                # 16 种语言的 README
```

`.github/workflows/` 下有四个 workflow：`update-readme.yml`（定时生成 README）、`sync-approved-to-cms.yml`（标签触发同步）、`sync-labels.yml`（标签管理）、`auto-close-stale-issues.yml`（清理过期 Issue）。核心是前两个。

### 核心脚本：generate-readme.ts

机制 C 的实现，主函数只有一层循环：遍历 16 种语言，每种语言走一遍"拉取 → 排序 → 渲染 → 写文件"。关键在拉取这一步——它**不是**全量拉取：

1. 先拉精选池：`fetchFeaturedPrompts()` 按模型过滤（`model = gpt-image-2`），每语言最多 30 条，排序键为精选优先 → 人工排序权重 → 来源发布时间；
2. 再按"使用场景"的 10 个二级类目逐类拉取，每类最多 20 条，与精选池按 ID 去重；
3. `sortPrompts()` 把结果分成精选和常规两组；
4. `generateMarkdown()` 渲染 Markdown，常规提示词有 120 条的展示上限（源码常量 `MAX_REGULAR_PROMPTS_TO_DISPLAY`）；
5. 写入对应语言的 README。

所以 README 统计栏里的 17,700 是 CMS 里的全库总量（来自 `totalDocs` 字段），README 本身只展示 126 条。这是设计而不是偷懒：GitHub README 承担"橱窗"角色，给浏览器一个精选切面；全库检索、多维筛选交给 Web Gallery。GIF 动图和大图也不进 Git——成品图上传 CMS，由 `cms-assets.youmind.com` 域名服务。

调度上，`update-readme.yml` 的 cron 是 `0 0,12 * * *`，即每天 UTC 0 点和 12 点（北京时间 8 点、20 点）各跑一次，另有 `scripts/**` 变更推送和手动触发两个入口。提交时先检查有无变更，没有就直接退出；推送失败则 rebase 重试，最多 5 次，处理并发运行的竞争。

### 核心脚本：sync-approved-to-cms.ts

机制 B 的实现。触发条件是双重的：Issue 被加上 `approved` 标签，**且** Issue 本身带有投稿表单自动打的 `prompt-submission` 标签——防止给普通讨论加 approved 时误触发。脚本做的事：

1. 按 `### 字段名` 解析 Issue 正文，取出标题、提示词全文、描述、图片 URL、作者、来源、语言；
2. 语言下拉框的文案映射成 locale 代码（`LANGUAGE_MAP`，同样是 16 种）；
3. 下载图片，经 `uploadImageToCMS()` 传到 CMS；
4. 用 Issue 编号查重（`sourceMeta.github_issue` 字段）：已存在走 `PATCH /api/prompts/{id}` 更新，不存在走 `POST /api/prompts` 创建，直接发布无草稿。

第 4 步的幂等设计让重复加标签、改稿重审都安全。同步成功后，workflow 用 `github-script` 给 Issue 发一条英文评论，附上画廊链接——注意评论里写的"4 小时内出现在 README"是文档滞后的说法，实际由机制 C 的 12 小时调度决定。

### 任务流案例：一条提示词从投稿到上线

以投稿一条提示词为例，走完整条链路：

```text
1. 用户打开 submit-prompt.yml 表单，填写：
   标题（≤80 字符）、提示词全文、描述、图片 URL（每行一个）、
   作者、来源链接、语言下拉框
   提交后自动带上 prompt-submission 标签
        ↓
2. 维护者 48h 内审核：原创性、成品质量、可复现性、内容安全
        ↓
3. 维护者加 approved 标签 → labeled 事件触发机制 B
        ↓
4. sync-approved-to-cms.ts：
   解析字段 → 下载图片上传 CMS → 查重 → POST/PATCH /api/prompts
        ↓
5. workflow 给 Issue 发评论，附画廊链接
        ↓
6. 等下一个 cron 窗口（最长约 12 小时），generate-readme.ts
   按 16 个 locale 各拉一遍 → 排序 → 写入 16 份 README
        ↓
7. README 变更由 github-actions[bot] 提交到 main 分支
```

从打标签到 README 上线，1 到 12 个小时不等，取决于落在哪个半天窗口。最后一步之外还有一条隐性出口：Web Gallery 直接读 CMS，不经过 README 这一环——README 只是画廊数据的定时快照。同一个 CMS，两种消费方式。

## 提示词结构设计深度解析

仓库中的提示词采用结构化 JSON Schema，把"自然语言描述"转成"字段化的工程产物"，每个字段对应图像的一个维度。

### 通用结构模板

README 精选第一位就是最好的样本——"VR Headset Exploded View Poster"（作者 wory＠ホッピング中，收录自 X 帖子），下面是它的完整提示词原文：

```json
{
  "type": "exploded view product diagram poster",
  "subject": "VR headset",
  "style": "clean high-tech 3D render, studio lighting, glowing accents",
  "background": "{argument name=\"background color\" default=\"soft purple and blue gradient\"}",
  "header": {
    "logo": "∞ {argument name=\"product name\" default=\"Meta Quest 3\"}",
    "subtitle": "{argument name=\"main catchphrase\" default=\"まったく新しい現実を、まったく新しい構造から。\"}"
  },
  "layout": {
    "centerpiece": "vertically stacked exploded view of a VR headset showing 9 distinct layers of internal components: outer shell, camera sensors, motherboard with chip, pancake lenses, internal frame, battery packs, side straps, top strap, and facial interface cushion.",
    "callout_labels": {
      "count": 8,
      "left_side": [
        "Snapdragon® XR2 Gen 2\n圧倒的な処理性能でリアルタイムな体験を。",
        "調整可能なIPD機構\n幅広いユーザーに快適なフィット感を。",
        "精密設計されたヘッドストラップ\n快適さと安定性を追求したエルゴノミクス。"
      ],
      "right_side": [
        "フェイスプレート\n洗練されたデザインと最適な重量バランス。",
        "トラッキングカメラ\n高精度な位置トラッキングと環境認識を実現。",
        "パンケーキレンズ\n薄型設計で広い視野角と鮮明な映像を提供。",
        "高性能バッテリー\n長時間駆動を支える最適化された電源設計。",
        "柔らかなフェイスインターフェース\n長時間でも快適な装着感を実現。"
      ]
    },
    "footer": {
      "left_text_block": {
        "headline": "{argument name=\"bottom headline\" default=\"体験は、構造から進化する。\"}",
        "body": "一つひとつのパーツに、没入体験を支える最先端テクノロジーとこだわりの設計。Meta Quest 3は、未来を感じさせる体験を内部から生み出しています。"
      },
      "right_logo": "∞ Meta"
    }
  }
}
```

各字段的职责：

- `type`：图像整体形态（"exploded view product diagram poster"，爆炸视图产品海报），是分类和构图的总锚点
- `subject`：主体对象，决定构图焦点
- `style`：渲染质感关键词
- `layout.centerpiece`：核心视觉的精确描述——9 层分解从外壳到面垫按顺序点名，模型照单排布
- `layout.callout_labels`：左右两列部件标注，每条是"部件名 + 换行 + 一句日文卖点"，`count: 8` 与左右 3 + 5 条严格一致
- `header` / `footer`：版式层，让提示词具备排版能力
- `{argument name="..." default="..."}`：Raycast Snippets 动态参数，运行时替换

两条值得学的细节。其一，文案即默认值：`subtitle`、`footer.headline` 的参数默认值是写好的日文成稿，不改参数直接跑就是一张成品，改参数就换一个 SKU——模板的复用零成本来自默认值的完整度。其二，数量自洽：`callout_labels.count` 和数组长度一致，给模型一个可校验的约束，减少漏标、多标。

### Raycast 动态参数

仓库给支持动态参数的提示词打了"🚀 Raycast Friendly"徽章，README 有专门章节介绍。语法来自 [Raycast Snippets](https://raycast.com/help/snippets)：

```text
{argument name="quote" default="Stay hungry, stay foolish"}
{argument name="author" default="Steve Jobs"}
```

把产品名、标语、背景色这类高频变量参数化后，同一模板服务多个具体需求。批量产出同版式、不同内容的海报时，改一个参数就是一张新图，不用重写整段提示词。

### 分类体系

提示词按三个维度交叉分类，README 的"Browse by Category"区完整列出了全部类目：

**使用场景**（10 类）：个人资料/头像、社交媒体帖子、信息图/教育视觉、YouTube 缩略图、漫画/故事板、产品营销、电商主图、游戏素材、海报/传单、App/网页设计。

**风格**（16 类）：摄影、电影/电影剧照、动漫/漫画、插画、草图/线稿、漫画/图画小说、3D 渲染、Q 版/萌风、等距、像素艺术、油画、水彩画、水墨/中国风、复古/怀旧、赛博朋克/科幻、极简主义。

**主体**（15 类）：人像/自拍、网红/模特、角色、团体/情侣、产品、食品/饮料、时尚单品、动物/生物、车辆、建筑/室内设计、风景/自然、城市风光/街道、图表、文本/排版、抽象/背景。

三个维度只有第一个参与了 README 的组织——源码按"使用场景"子类目逐类拉取，所以"All Prompts"区每条标题都以场景开头（"Profile / Avatar - …"）。风格和主体两维体现在画廊的多维筛选里。每条提示词因此都有"场景-风格-主体"坐标，在画廊中可以任意组合过滤。

## 多语言国际化实践

16 种语言是数出来的，不是文档抄的：`generate-readme.ts` 遍历的 `SUPPORTED_LANGUAGES` 数组共 16 项，投稿表单的 `LANGUAGE_MAP` 也是 16 项，仓库根目录 16 份 README 一一对应——英文、简体中文、繁体中文、日语、韩语、泰语、越南语、印地语、西班牙语（西班牙）、西班牙语（拉美）、德语、法语、意大利语、葡萄牙语（巴西）、葡萄牙语（欧洲）、土耳其语。西语和葡语各拆两个变体，分别照顾拉美与西班牙、巴西与欧洲的用语差异。

值得注意的一点：CONTRIBUTING 和 FAQ 写的都是"17 languages"，与源码不符——又是文档滞后。如果照文档做集成，第 17 种语言会扑空。

多语言的实现分两层。提示词正文按投稿时选择的语言存入 CMS，各语言 README 按 locale 拉取自己语言的内容；README 的界面文案（栏目标题、统计标签等）集中在 `i18n.ts` 一个模块里翻译。中英文 README 的统计栏显示同一个总数 17,700，因为 `totalDocs` 只按模型过滤、与 locale 无关——它数的是全库，不是单语言条数。

## 如何高效利用这个仓库

### 场景一：直接搜索使用

访问 [youmind.com/gpt-image-2-prompts](https://youmind.com/gpt-image-2-prompts)，README 里的对比表说得很直白：画廊是瀑布流 + 全文搜索 + 分类筛选 + 一键生图，README 只有线性列表和 Ctrl+F。17,700 条的量级下，画廊是唯一现实的入口；README 适合随机浏览找灵感。每条提示词详情页有"Try it now"深链（`?id=提示词ID`），可直接跳到生成。

### 场景二：参考结构，写自己的提示词

仓库的提示词是经过社区验证的结构化模板，照着写能少走弯路：

1. `type` 定整体形态，类型关键词选准是控制输出的第一步
2. `style` 定质感，与使用场景匹配（电商主图和电影剧照的用词是两个体系）
3. `layout` 系列字段给排版控制，减少随机性
4. 高频变量用 `{argument}` 参数化，默认值写成可直接发布的成稿

### 场景三：投稿贡献

1. 打开 [投稿表单](https://github.com/YouMind-OpenLab/awesome-gpt-image-2/issues/new?template=submit-prompt.yml)，填写标题、提示词全文、描述、图片 URL、作者、来源、语言
2. 等待审核，仓库文档承诺 48 小时内给出结果
3. 通过后自动同步 CMS，等下一个半天窗口出现在 README

投稿要求：原创或已获授权、成品质量高、清晰可复现、有创意、内容安全。图片最小宽度 512px，推荐 1024px–2048px，JPEG/PNG/WebP 格式，单文件小于 5MB，不接受带水印（原作者水印除外）。只收 Issue 投稿，不收 PR——为了格式统一和自动处理。

## 技术局限性与适用边界

1. **CMS 是单点**。README 生成的每一步都依赖 `CMS_HOST` 可达，CMS 不可用则机制 B、C 同时中断，workflow 里没有降级或缓存逻辑。CMS 和画廊（youmind.com）都不在开源范围内——仓库开源的是提示词数据和两个胶水脚本。
2. **README 是子集**。120 条常规展示上限意味着 GitHub 端永远只看到约 0.7% 的库；做数据集、跑批量分析的话，README 帮不上忙——CMS 接口不对外开放（API Key 只存在于仓库 secrets），画廊是唯一的全量入口。
3. **文档滞后是常态**。"17 种语言""每 4 小时刷新"这类说法在 FAQ 和 bot 评论里仍在，与源码不符。引用这个项目的任何数字，先查源码和工作流定义。
4. **提示词不是代码**。仓库不含 API 调用代码，接 GPT Image 2 API 要自己写；内容按 CC BY 4.0 授权，商用需署名。

这套架构的舒适区是"社区众包 + 多渠道发布"的内容项目——提示词库、代码片段库、设计资源库都适用。它的前提条件也要看清：内容更新以半天为粒度可接受、有一个可托管的内容后台、维护者愿意人工把关质量。强实时、强一致的场景不适合照搬。

## 采用建议

不同读者各取所需：

- **AI 图像生成使用者**：直接用画廊搜索，别翻 README；高频模板复制到 Raycast Snippets，改参数批量出图。
- **提示词工程师**：重点看 JSON 结构的分层——`type`/`style` 定调、`layout` 控版式、`{argument}` 参数化且默认值即成稿。这套结构可以把提示词从"一段话"升级为"可复用的工程产物"。
- **开源项目维护者**：值得借鉴的是"Issue 表单收稿 + 标签做审核状态机 + CMS 单一数据源 + 定时生成多语言产物"这条链路。提示词库、片段库、资源库都可套用；注意把"发布产物是子集、全量走前台"设计成显式决策，README 和前台各司其职。
- **想自建类似系统的开发者**：仓库里的自动化代码很薄，真正的重心在内容后台——用 Payload 自建，或换 Notion、Airtable 加一个生成脚本，GitHub Actions 免费额度足够每天跑两轮。技术栈不必照搬。

同一团队还维护着 [awesome-seedance-2-prompts](https://github.com/YouMind-OpenLab/awesome-seedance-2-prompts)，Seedance 2 视频生成提示词库，架构思路相同，README 顶部互相导流。

> 原文：[Awesome GPT Image 2 - GitHub](https://github.com/YouMind-OpenLab/awesome-gpt-image-2)
