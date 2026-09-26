---
title: "baoyu-skills：宝玉的 AI Agent 内容创作技能集"
slug: "baoyu-skills-ai-agent-guide"
github_repo: "JimLiu/baoyu-skills"
source_key: "gh:JimLiu/baoyu-skills"
aliases:
  - /posts/tech/baoyu-skills-ai-agent-guide/
date: "2026-03-31T15:45:00+08:00"
lastmod: "2026-09-21T12:00:00+08:00"
categories: ["技术笔记"]
tags: ["AI Agent", "Claude Code", "Agent Skills", "内容创作"]
description: "宝玉（JimLiu）开源的 26k Stars AI Agent 技能集：21 个技能覆盖内容生成、多平台发布与效率工具，含 11 家图像 API 统一入口、微信公众号三通道发布与 EXTEND.md 定制机制。本文以 v2.5.2 为口径拆解其结构、机制与工程取舍。"
---

# baoyu-skills：宝玉的 AI Agent 内容创作技能集

在 Agent Skills 生态里，绝大多数技能仓库解决的是"怎么让 Agent 写好代码"；[JimLiu/baoyu-skills](https://github.com/JimLiu/baoyu-skills) 解决的是另一件事——怎么让 Agent 替你产出和分发内容。宝玉（Jim Liu）把日常用 AI Agent 做内容的工作流拆成了 21 个技能：从小红书图文卡片、信息图、漫画、幻灯片，到微信公众号、微博、X 的一键发布，再到长文翻译、YouTube 字幕下载、Electron 应用源码提取。仓库 2026 年 1 月创建，8 个多月拿到 26,000+ Stars——在内容创作方向的技能集里，这个体量很少见。

本文以 v2.5.2（2026-06-18 发布）为口径，数据时点 2026-09-21。

## 仓库全景：21 个技能的三张地图

README 把技能分成三类，每一类对应内容工作流的不同环节：

**内容技能（10 个）**——生成和分发：

| 技能 | 干什么 |
|------|--------|
| `baoyu-xhs-images` | 小红书图文卡片系列，12 种风格 × 6 种信息密度布局 |
| `baoyu-infographic` | 高密度信息图，21 种布局 × 22 种视觉风格 |
| `baoyu-diagram` | 架构图/流程图/时序图，Claude 手写 SVG 而非调图像模型 |
| `baoyu-cover-image` | 文章封面图，五维系统（类型×调色板×渲染×文字×情绪） |
| `baoyu-slide-deck` | 幻灯片整套生成，16 种预设风格，产出自动合并为 .pptx 和 .pdf |
| `baoyu-comic` | 知识漫画，5 种画风 × 7 种基调，内置 3 个题材预设 |
| `baoyu-article-illustrator` | 通读文章后自动决定哪里该配图、配什么类型的图 |
| `baoyu-post-to-x` | 发布到 X，普通帖与 X Articles 长文 |
| `baoyu-post-to-wechat` | 发布微信公众号，贴图与文章两种模式 |
| `baoyu-post-to-weibo` | 发布微博，普通帖与头条文章 |

**AI 生成后端（2 个）**：

| 技能 | 干什么 |
|------|--------|
| `baoyu-image-gen` | 11 家图像生成 API 的统一命令行入口 |
| `baoyu-danger-gemini-web` | 逆向 Gemini Web 网页版生成文本和图像 |

**效率工具（9 个）**：

| 技能 | 干什么 |
|------|--------|
| `baoyu-translate` | 长文翻译，快译/常规/精修三档模式 |
| `baoyu-wechat-summary` | 微信群聊记录转结构化精华摘要 |
| `baoyu-youtube-transcript` | YouTube 字幕下载，支持翻译、章节、说话人识别 |
| `baoyu-url-to-markdown` | 网页转 Markdown，保存渲染后的 HTML 快照 |
| `baoyu-danger-x-to-markdown` | 推文和 X Articles 转 Markdown |
| `baoyu-format-markdown` | 整理草稿为带 frontmatter 的规范 Markdown |
| `baoyu-markdown-to-html` | Markdown 转微信兼容 HTML，支持主题与外链尾注 |
| `baoyu-compress-image` | 图片压缩 |
| `baoyu-electron-extract` | 从已安装的 Electron 应用提取资源并尽量还原源码 |

带 `danger-` 前缀的两个技能共用逆向工程 API（后文详说）。README 还单独推荐了一个独立项目 [JimLiu/baoyu-design](https://github.com/JimLiu/baoyu-design)：把 Claude Design 跑在 Cursor、Claude Code、Codex 里，产出 HTML 形式的 UI 稿、原型和落地页，不在本仓库 21 个技能之列。

## 作者与定位

宝玉是中文 AI 圈的活跃译者和写作者，GitHub ID 为 JimLiu。这个仓库的定位在 README 第一句话就说完了："宝玉分享的 AI Agent 技能集（适用于 Claude Code、Codex 等），提升日常工作效率。"它不是框架，也没有 SDK，就是一批直接可装的技能文件，每个技能一个目录、一份 SKILL.md。

技能集本身也被写成了教材：宝玉出版了《图解 Skill——AI 提效实战指南》，配套仓库 [JimLiu/Illustrated-Agent-Skills](https://github.com/JimLiu/Illustrated-Agent-Skills)，系统讲技能的设计、编写、安装和迭代。读这套技能的实现，某种程度上就是在看一本打开的技能设计参考书——每个 SKILL.md 里对确认流程、参数默认值、失败回退的处理，都是可以直接借鉴的写法。

从 CHANGELOG 能看出一个明显的演进方向：2026 年 1 月建仓（最早的技能是 gemini-web），1 月中旬一次性铺开内容生成与发布矩阵——小红书卡片、幻灯片、封面、漫画、微信公众号和 X 发布都在 1 月 15 日前后入库，1 月下旬图像后端 `baoyu-image-gen` 落地；3 月加入翻译和微博发布，4 月加入 SVG 图表，5 月起重心转向多后端整合与中文场景深挖——`baoyu-wechat-summary`、`baoyu-electron-extract` 相继入库，v2.0.0 把分散的图像技能收敛进 `baoyu-image-gen`。技能与技能之间也开始互相咬合——`baoyu-article-illustrator` 的输出可以直接喂给 `baoyu-image-gen` 的批量模式，`baoyu-post-to-wechat` 内置了 `baoyu-markdown-to-html` 的转换流程，不需要单独安装后者。

## 内容生成：矩阵化的是参数，不是套路

内容技能的共同结构是"风格 × 布局"矩阵加自动推荐：技能先读你的内容，推荐一组组合，确认后生成。以信息图技能为例，21 种布局（桥型、鱼骨图、漏斗、冰山、时间轴、文氏图等）对应不同的信息结构，22 种视觉风格（默认 `craft-handmade` 手作纸艺风）对应不同的美学取向，还支持 `--aspect` 指定 16:9 到 2.35:1 的画幅。小红书卡片走同样的路数，只是矩阵更克制：12 种风格、6 种布局，外加 macaron/warm/neon 三个调色板覆盖。

两个设计选择值得注意。

其一，`baoyu-diagram` 刻意不走图像生成。README 写明它"不是图像生成技能——不调用任何 LLM 图像模型"，Claude 直接手写 SVG，布局坐标自己算。好处是图里的文字精确可控（图像模型写中文标注经常出错），且输出是自带 `<style>` 块的单文件 SVG，内嵌 `@media (prefers-color-scheme: dark)`，同一份文件在浅色和深色模式下都能正确渲染。

其二，`baoyu-slide-deck` 的产出不止是图片。它先出大纲（可 `--outline-only` 跳过出图），再逐页生成图片，最后自动合并成 `.pptx` 和 `.pdf` 文件。风格系统是四维组合（质感×情绪×字体×密度），16 个预设都是这些维度的预配置——`blueprint`（默认）是网格+冷色+技术字体，适合架构文档；`chalkboard` 是有机纹理+暖色+手写字，适合教程。

漫画技能 `baoyu-comic` 的预设更具体：`ohmsha`（欧姆社风格，漫画画风+教学特规——视觉比喻、禁"说话头"、道具揭晓式分镜）、`wuxia`（水墨+动作——真气特效、打斗画面）、`shoujo`（少女漫+浪漫——装饰元素、眼部细节）。这类预设实际上是把某个成熟品类的视觉规范编码进了提示词，比裸的"画风+基调"组合多了一层品类知识。

## 图像生成：一个入口对接 11 家 API

`baoyu-image-gen` 是全套技能里工程化最重的。它把 11 家图像 API 收进一个命令行入口：Google、OpenAI、Azure OpenAI、OpenRouter、DashScope（阿里通义万象）、Z.AI（智谱 GLM-Image）、MiniMax、即梦（火山引擎）、Seedream（豆包）、Replicate、Agnes。每家有默认模型（OpenAI 默认 `gpt-image-2`，Google 默认 `gemini-3-pro-image`，Replicate 默认 `google/nano-banana-2`），也都可以 `--provider`、`--model` 显式指定。

几个细节能看出对接的深度：

- **参考图不是所有 provider 都通用**。`--ref` 只对 Google、OpenAI、Azure、OpenRouter、Replicate 部分模型、MiniMax 和 Seedream 5.0/4.5/4.0 生效；即梦不支持参考图，Z.AI 的 GLM-Image 也不支持。技能没有假装统一，README 逐家写明了差异。
- **自动选择有明确优先序**。指定 `--provider` 就用它；给了 `--ref` 没指定提供方，按 Google → OpenAI → Azure → OpenRouter → Replicate → Seedream → MiniMax → Agnes 逐个试；只配了一把 key 就用那家；配了多把默认走 Google。
- **批量模式有并发上限**。`--batchfile` 传 JSON 任务清单，`--jobs` 控制并发，环境变量 `BAOYU_IMAGE_GEN_MAX_WORKERS` 默认封顶 10，每家还有单独的并发与请求间隔控制——这是对着各家 API 的限流现实做的设计。
- v2.2.0 起还多了个不花 API 钱的选项：`codex-cli` 后端包装 Codex 订阅内的 `image_gen` 工具，走用户已有的 Codex 订阅，不需要 `OPENAI_API_KEY`。

## 发布到中文平台：公众号三通道是最有辨识度的部分

`baoyu-post-to-wechat` 支持贴图（多图+短文字）和文章（完整 Markdown/HTML）两种模式，发布走三条通道：

| 通道 | 速度 | 前提 |
|------|------|------|
| API（推荐） | 快 | 公众号开发密钥，本机 IP 在微信白名单内 |
| 浏览器 | 慢 | Chrome + 登录会话 |
| 远程 API | 快 | 密钥 + 一台 IP 在白名单内的 SSH 可达服务器 |

第三条通道是应对微信 IP 白名单的务实设计：本机不在白名单时，通过 SSH SOCKS5 动态端口转发，把微信 API 调用隧道到白名单内的服务器执行，远端不落任何文件，`AppSecret` 不出本地进程。凭据放在 `.baoyu-skills/.env`（项目级）或 `~/.baoyu-skills/.env`（用户级），多账号用 `EXTEND.md` 配置账号清单，每个账号有隔离的 Chrome 登录会话，发布时 `--account <alias>` 选择。浏览器通道首次运行扫码登录，会话保留；v1.116.5 起还支持把登录二维码推送到 Telegram（配 `TELEGRAM_BOT_TOKEN` 即可），方便无头环境远程登录。

微博和 X 的发布技能走浏览器路线：脚本用 Chrome CDP（Chrome DevTools 协议，程序操控浏览器的通道）填充内容，**用户审查后手动点发布**——发布类技能都不自动发帖，这是全套技能一致的边界。微博普通帖最多带 18 个媒体文件，头条文章支持 Markdown 输入，标题上限 32 字、摘要上限 44 字。

`baoyu-wechat-summary` 是另一个中文生态特供：依赖 wx-cli 读微信群消息，把指定时间段的群聊整理成结构化摘要——话题提取（带出处和原话引用）、消息排行榜、用户画像，还支持"毒舌版"文风和增量模式（从上次摘要断点继续）。v2.4.0 加了 `@bot` 问答：群里 `@bot` 提的问题会在摘要里专门回答；v2.5.0 加了群级事实记忆，群里被纠正过的客观事实（某个报错的真正原因、某个产品的正确名称）会写进 `memory.md` 跨次持久化，并带注入护栏。要求微信 4.x 在 macOS 上登录运行。

## 效率工具：翻译和源码提取

`baoyu-translate` 的三档模式对应不同投入：`quick` 直接译，`normal` 先分析再译，`refined` 走分析→翻译→审校→润色的完整流程。受众和文风各有预设——受众分通用/技术/学术/商务四档（控制译注密度），文风从默认 `storytelling` 到 `formal`、`literal`、`humorous`、`elegant` 九档，也接受自定义描述。超过 4000 词的长文自动分块并行翻译，术语表走 `EXTEND.md`，内置英中术语表打底。输出目录保留全部中间文件，方便回查每一步的处理。

`baoyu-electron-extract` 解决的是"想看某个 Electron 应用怎么实现的"：按应用名定位 `app.asar`，提取资源；如果 `.js.map` 里嵌了 `sourcesContent`，直接重建原始源码树（含 TypeScript/JSX），没有 sourcemap 就地用 Prettier 格式化压缩后的 JS/CSS。默认跳过 `node_modules`，支持 `--dry-run` 预览，输出带 `extract-report.json` 统计报告。macOS 和 Windows 直接可用，其他平台传 `--asar` 路径。

其余工具都短小直接：`baoyu-youtube-transcript` 下载字幕支持多语言优先序、按视频描述切章节、说话人识别（需 AI 后处理）和原始数据缓存；`baoyu-url-to-markdown` 用 Chrome CDP 抓渲染后的页面，Defuddle 提取失败自动回落到旧提取器，登录页用 `--wait` 等你手动登入后再抓。

## 安装、配置与定制

前置要求只有两条：Node.js 环境，能跑 `npx bun`。

**四条安装路径**，按场景选：

```bash
# 快速安装（推荐），装到当前 Agent
npx skills add jimliu/baoyu-skills

# Claude Code 插件市场方式
/plugin marketplace add JimLiu/baoyu-skills
/plugin install baoyu-skills@baoyu-skills

# ClawHub（OpenClaw 生态）按个安装
clawhub install baoyu-image-gen
```

Codex 用户可以走项目级安装：Codex 会扫描项目内的 `.agents/skills`，把需要的技能目录复制或符号链接进去即可。微信公众号工作流的最小集是 `baoyu-cover-image`、`baoyu-article-illustrator`、`baoyu-post-to-wechat` 三个。

装完之后有两层配置机制。**环境变量**管密钥和默认模型：`.env` 文件按 CLI 环境变量 → 系统 `process.env` → 项目级 `.baoyu-skills/.env` → 用户级 `~/.baoyu-skills/.env` 四层优先级加载，高优先级覆盖低优先级。**EXTEND.md** 管偏好定制：放在 `.baoyu-skills/<skill-name>/EXTEND.md`（项目级，团队共享）或 `~/.baoyu-skills/<skill-name>/EXTEND.md`（用户级），技能执行前加载，可以覆盖默认风格、加自定义调色板、定义自己的预设。`baoyu-image-gen` 走得更远——首次运行如果没有 EXTEND.md，会先阻塞式引导你选好默认提供方、模型、质量和保存位置，写完配置才开始干活，之后的每次生成都免掉重复询问。

更新走插件市场：Agent 里运行 `/plugin`，切到 Marketplaces 标签选 baoyu-skills 更新，也可以直接开自动更新。

## 版本节奏与两条工程纪律

这个仓库的版本节奏是典型的高频迭代：tag 已经打了 239 个，GitHub Releases 从 v1.114.0（2026-05-05）开始建，到 v2.5.2 共 26 个。几个月里有两次值得注意的破坏性整理：v2.0.0（2026-05-24）删掉 `baoyu-imagine` 和 `baoyu-image-cards`，功能全部并入 `baoyu-image-gen`（旧 EXTEND.md 路径自动改名兼容）；v1.116.3 起把 README 里的 Claude Code 字样换成泛 Agent 措辞，明确多 Agent 支持。

两条纪律贯穿全部技能，写文章的人容易忽略，但它们决定了这套技能能不能真在日常里用：

**确认与回退**。所有生成类技能默认交互确认——技能先出方案，你确认了才执行，赶时间可以 `--yes`（小红书卡片）或 `--quick`（封面图）跳过。发布类技能一律停在"内容已填好"这一步，按下发布键的永远是人。处理失败有显式回退：Markdown 转 HTML 的 Defuddle 提取失败会回落旧提取器，图像批量任务里 Codex 后端会校验"本轮真的跑过 image_gen"，防止拿旧图蒙混过关。

**逆向 API 的风险明示**。两个 `danger-` 技能的 Disclaimer 写得很直白：`baoyu-danger-gemini-web` 用逆向的 Gemini Web API（浏览器 cookie 认证），`baoyu-danger-x-to-markdown` 用逆向的 X API——"非官方 API，风险自担"，可能随时失效，账号可能因检测被限制，X 技能首次使用还要求确认已知悉风险。命名里的 `danger-` 前缀本身就是警告：官方 API 能做的，优先走 `baoyu-image-gen` 和官方通道。

## 常见问题

**免费吗？** 技能本身 MIT 开源（ClawHub 分发的技能按其注册表规则用 MIT-0）。但图像生成调用的是各家付费 API，按量计费；`codex-cli` 后端走你已有的 Codex 订阅，不额外要 key。

**21 个技能要全装吗？** 不要。README 特别提醒：仓库有 20+ 技能，只装你实际需要的——全装会给 Agent 每轮运行增加不必要的上下文开销。按工作流挑：写公众号就装封面、配图、发布三件套。

**支持哪些 Agent？** README 的定位是 Claude Code、Codex 等；ClawHub 通道面向 OpenClaw；image-gen 的文档还覆盖了 Cursor 原生 `GenerateImage` 后端的接入规则。核心运行依赖只是 Node.js 加 `npx bun`，不绑死某家 Agent。

**会替我自动发帖吗？** 不会。所有发布类技能都是脚本填充内容、人审查后手动发布，这是刻意的边界而不是能力缺失。

## 适用边界

**适合**：以内容产出为日常工作的个人创作者和团队——尤其同时运营多个中文平台（公众号、小红书、微博）的人；想把"写完文章"到"多平台分发"这段手工活交给 Agent 的人；想学习技能（Skill）设计的人，这套 SKILL.md 是少见的、经过 26k 用户实际使用检验的样本库。

**不适合**：找一体化内容平台的团队——这是技能集不是产品，没有 Web 界面，没有内容排期和协作功能；对逆向 API 零容忍的环境——两个 danger 技能虽已明示风险，但用不用需要自己掂量；重度依赖数据实时性的金融、电商场景——这套技能不做行情和交易数据。

## 判断

baoyu-skills 的价值不在单个技能的生成质量——风格矩阵加自动推荐的套路，任何熟练的技能作者都能写。它的护城河在三处：对中文发布渠道的适配深度（微信 IP 白名单的 SSH 隧道方案、多账号隔离、微博字数限制这类脏细节），图像后端对接的完整性（11 家 API 的差异被逐家写清而不是假装统一），以及"人审发布"这条贯穿始终的边界——它清楚内容发布是要署名担责的事，Agent 做到"填好内容"为止。

局限也明显：技能之间除了少数显式衔接（article-illustrator 喂 image-gen 批量模式），整体还是 21 个独立入口，没有一条"写完文章自动出全套衍生内容再分发"的编排层；风格矩阵覆盖的是图文品类，音频和视频内容完全缺席。下一个版本的看点是它会不会从技能集长成工作流——从 CHANGELOG 的走向看，作者正在朝这个方向走。

## 项目信息

| 项目 | JimLiu/baoyu-skills |
|------|---------------------|
| 作者 | 宝玉（Jim Liu） |
| 创建 / 最近推送 | 2026-01-13 / 2026-09-10 |
| Stars / Forks | 26,054 / 2,878（2026-09-21） |
| 贡献者 / 提交数 | 49 人 / 736 次 |
| 版本口径 | v2.5.2（2026-06-18），GitHub Releases 共 26 个 |
| 许可证 | MIT（ClawHub 分发的技能为 MIT-0） |
| 作者图书 | 《图解 Skill——AI 提效实战指南》（[配套仓库](https://github.com/JimLiu/Illustrated-Agent-Skills)） |

## 参考来源与口径说明

本文事实核查于 2026-09-21，主要信源：

- **GitHub API**：仓库元数据（stars、forks、创建时间、topics）、releases 列表（26 个，v1.114.0 至 v2.5.2）。
- **README.md / README.zh.md（main 分支，v2.5.2 后无结构性变更）**：技能分类与逐技能功能、安装命令、`.env` 加载优先级、EXTEND.md 机制、微信三通道发布、danger 技能 Disclaimer、Credits、License。文中的功能描述与引语均出自此处。
- **SKILL.md 源文件**：`baoyu-image-gen`（EXTEND.md 首次设置阻塞流程、XDG 配置路径）、`baoyu-infographic`（21 布局 × 22 风格，经 `references/layouts/` 与 `references/styles/` 目录文件数交叉验证；README 表格中的 20×17 为未同步的旧口径）。
- **git 历史（本地克隆）**：提交总数 736、贡献者 49 人、tag 239 个；技能加入时间线（`baoyu-diagram` 2026-04-11、`baoyu-wechat-summary` 2026-05-13、`baoyu-electron-extract` 2026-05-24）与 v2.0.0 破坏性变更（`baoyu-imagine`、`baoyu-image-cards` 移除）出自 commit 记录与 release notes。
- **版本锚点**：文章原发布于 2026-03-31，内容已整体更新至 v2.5.2 口径；正文中标注"v2.5.2 后新增"的特性均给出对应版本号。
