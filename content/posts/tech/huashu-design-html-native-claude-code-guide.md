---
title: "Huashu Design：HTML 原生的 AI 设计 Skill，从入门到精通完全指南"
date: "2026-04-30T11:30:00+08:00"
slug: "huashu-design-html-native-claude-code-guide"
description: "深入解析 alchaincyf/huashu-design（10,251 stars）—— 一款 Agent-agnostic 的 HTML 原生设计 Skill。涵盖 20 种设计哲学、5 维评审体系、MP4/GIF 导出、交互原型、幻灯片、动画引擎的全套技术架构与实战指南。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "HTML设计", "AI设计工具", "原型设计", "设计系统"]
---

# Huashu Design：HTML 原生的 AI 设计 Skill，从入门到精通完全指南

> 📅 更新日期：2026-04-30｜⭐ GitHub 10,251 stars｜🦞 整理：钳岳星君

## 一、项目概述与定位

**Huashu Design**（花叔 Design）是目前 AI Agent 设计工具领域最具影响力的开源 skill 之一，由独立开发者花生（花叔）创建，于 2026-04-19 公开，不到两周时间即斩获超过 10,000 star，fork 数高达 1,478，成为 GitHub Trending 榜上的现象级项目。

### 核心理念：一句话 prompt，换一份能交付的设计

传统设计工具（Figma、Sketch、Adobe XD）依赖 GUI 操作，需要设计师手动排版、调色、添加动画。Huashu Design 的核心创新在于**将设计能力封装为 Agent 可调用的 skill**，用户只需在 Claude Code（或其他支持 skills 的 AI Agent）中描述需求，Agent 即可自动完成从设计方向选择、品牌资产采集、高保真原型制作到视频导出的全流程。

### 与 Claude Design 的定位差异

| 维度 | Claude Design | Huashu Design |
|------|---------------|---------------|
| **形态** | 浏览器 Web 产品 | Claude Code skill |
| **交互方式** | GUI（点、拖、改） | 对话（说话、等 agent 做完） |
| **交付物** | 画布内 + 可导 Figma | HTML / MP4 / GIF / 可编辑 PPTX / PDF |
| **动画能力** | 有限 | Stage + Sprite 时间轴，60fps 导出 |
| **跨 Agent** | 专属 Claude.ai | 任意 agent 通用（Claude Code / Cursor / Codex / OpenClaw） |
| **配额限制** | 订阅 quota | API 消耗，并行 agent 不受限 |

Huashu Design 的本质不是「更好的图形工具」，而是「**让图形工具这层消失**」——用户不再需要打开任何设计软件，直接用自然语言驱动 AI 完成设计工作。

## 二、原理分析：HTML 原生设计理念

### 2.1 为什么是 HTML？

大多数设计工具的输出格式是专有的（如 Figma 的 `.fig`、Sketch 的 `.sketch`），需要专用软件才能打开和编辑。Huashu Design 选 HTML 作为设计媒介，蕴含着深刻的技术哲学：

**1. 天然的可执行性**
HTML 是浏览器可以直接解释和渲染的语言，无需任何转换步骤。设计产出物本身就是可交互的 Demo——用户不仅「看到」设计，还能「点击」设计、体验交互动效。这比静态设计稿（Figma 截图、PDF 排版）高了一个维度。

**2. 无平台依赖**
HTML 文件在 Windows / macOS / Linux / 移动端均能直接打开，不存在格式兼容问题。导出的 MP4/GIF 也不依赖任何设计软件生态。

**3. 与 AI Agent 的天然契合**
AI Agent 的工作介质是代码（而非图形界面）。HTML 作为纯文本格式，Agent 可以精确操控每一个像素、每一帧动画、每一种字体。Figma 的 GUI 操作对 Agent 来说是黑箱，但 HTML 的 DOM/CSS 对 Agent 来说是完全透明的。

### 2.2 反 AI Slop 原则

**AI slop = AI 训练语料里最常见的"视觉最大公约数"**——紫渐变、emoji 图标、圆角卡片+左 border accent、SVG 画人脸。这些元素之所以是 slop，不是因为它们本身丑，而是因为它们是 AI 默认模式下的产物，**不携带任何品牌信息**。

Huashu Design 通过以下机制对抗 AI slop：

**核心资产协议**：涉及具体品牌时，强制执行 5 步硬流程——问用户资产清单 → 搜官方渠道 → 下载 Logo/产品图/UI 截图 → grep 提取色值 → 固化 `brand-spec.md`。这个协议直接决定了输出质量是 40 分还是 90 分。

**禁止清单**：

| 元素 | 违规原因 |
|------|---------|
| 激进紫色渐变 | AI 训练语料里"科技感"的万能公式，任何品牌用了都长一样 |
| Emoji 作图标 | 训练语料里每个 bullet 都配 emoji，是"不够专业就用 emoji 凑"的病 |
| 圆角卡片 + 左彩色 border accent | 2020-2024 Material/Tailwind 时期的烂大街组合 |
| SVG 画人脸/场景 | AI 画的 SVG 人物永远五官错位，比例诡异 |
| CSS 剪影代替真实产品图 | 生成的就是「通用科技动画」，品牌识别度归零 |
| Inter/Roboto/Arial 作 display | 太常见，读者看不出这是"有设计的产品"还是"demo 页" |

**正向做法**：
- ✅ `text-wrap: pretty` + CSS Grid + 高级 CSS 排版细节
- ✅ `oklch()` 或 spec 里已有的色，**不凭空发明新颜色**
- ✅ 真图优先（Wikimedia/Unsplash/AI 生成），没有就用诚实 placeholder
- ✅ 文案用「」引号不用 ""，中文排印规范

## 三、架构分析：系统架构与模块设计

### 3.1 整体架构

```
huashu-design/
├── SKILL.md                 # 主文档（给 agent 读，核心工作流定义）
├── README.md                # 本文件（给用户读）
├── assets/                  # Starter Components
│   ├── animations.jsx       # Stage + Sprite + Easing + interpolate 动画引擎
│   ├── ios_frame.jsx        # iPhone 15 Pro bezel 设备边框
│   ├── android_frame.jsx
│   ├── macos_window.jsx
│   ├── browser_window.jsx
│   ├── deck_stage.js        # HTML 幻灯片引擎（单文件架构）
│   ├── deck_index.html      # 多文件 deck 拼接器
│   ├── design_canvas.jsx    # 并排变体展示
│   ├── showcases/           # 24 个预制样例（8 场景 × 3 风格）
│   └── bgm-*.mp3            # 6 首场景化背景音乐
├── references/              # 按任务深入读的子文档
│   ├── design-styles.md     # 20 种设计哲学详细库
│   ├── critique-guide.md    # 5 维评审体系
│   ├── video-export.md      # MP4/GIF 导出完整指南
│   ├── slide-decks.md       # 幻灯片制作规范
│   ├── editable-pptx.md     # 可编辑 PPTX 导出
│   ├── workflow.md          # 完整工作流程
│   └── ...
├── scripts/                 # 导出工具链
│   ├── render-video.js      # HTML → MP4
│   ├── convert-formats.sh   # MP4 → 60fps + GIF
│   ├── add-music.sh         # MP4 + BGM 混音
│   ├── export_deck_pdf.mjs
│   ├── export_deck_pptx.mjs
│   └── html2pptx.js        # HTML → 可编辑 PPTX 翻译器
└── demos/                   # 9 个能力演示（中英双版 GIF/MP4/HTML）
```

### 3.2 主要模块详解

#### 3.2.1 动画引擎 `animations.jsx`

借鉴自 **Remotion** 的设计思想，但做了极简化的轻量实现。关键概念只有两个：

**Stage**：整个动画的时间轴容器，管理全局时间、播放状态、duration。

**Sprite**：时间片段，定义 `start` 和 `end` 时间点，在该时间段内显示，配合 `useSprite()` hook 读取本地进度。

```jsx
// 导出 API
window.Animations = {
  Stage,       // 时间轴容器
  Sprite,      // 时间片段
  useTime,     // 读全局时间（秒）
  useSprite,   // 读本地进度 {t: 0→1, elapsed, duration}
  Easing,      // 缓动函数集
  interpolate, // 插值工具
};
```

**Easing 缓动函数集**：

```javascript
const Easing = {
  linear: t => t,
  easeIn: t => t * t,
  easeOut: t => 1 - (1 - t) * (1 - t),
  easeInOut: t => t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2,
  expoOut: t => t === 1 ? 1 : 1 - Math.pow(2, -10 * t),  // Anthropic 级主 easing
  overshoot: t => { /* 带弹性的 toggle 弹出 */ },
  spring: t => { /* 弹簧效果 */ },
  anticipation: t => { /* 预备动作效果 */ },
};
```

**典型用法**：

```jsx
<Stage duration={10}>
  <Sprite start={0} end={3}>
    <Title />
  </Sprite>
  <Sprite start={2} end={5}>
    <Subtitle />
  </Sprite>
  <Sprite start={4} end={7}>
    <HeroImage />
  </Sprite>
</Stage>
```

#### 3.2.2 设备边框组件

提供精确的设备外壳（bezel），让原型看起来像真实设备上的体验：

- **`ios_frame.jsx`**：iPhone 15 Pro 精确机身，含灵动岛、状态栏、Home Indicator
- **`android_frame.jsx`**：Android 设备边框
- **`macos_window.jsx`**：macOS 窗口 chrome
- **`browser_window.jsx`**：浏览器窗口外壳

#### 3.2.3 幻灯片引擎

两种架构并存：

**多文件架构（推荐 ≥10 页）**：`deck_index.html` 拼接器 + `slides/*.html`，每个 slide 独立 HTML 文件，iframe 聚合。天然 CSS 隔离、并行开发、零冲突 merge。

**单文件架构（≤10 页）**：`deck_stage.js` + `<deck-stage>` web component，所有 slide 在一个 HTML 里。适合需要跨页共享状态的小 deck。

## 四、20 种设计哲学

Huashu Design 内置了 20 种经过验证的设计哲学体系，来源于真实世界顶级设计公司和设计师的实践。所有风格按流派分类，**设计方向顾问模式（Fallback）要求推荐的方向必须来自不同流派**，确保差异化。

### 4.1 五大流派概览

| 流派 | 视觉气质 | 代表风格 |
|------|---------|---------|
| **信息建筑派（01-04）** | 理性、数据驱动、克制 | Pentagram / Stamen / Information Architects / Fathom |
| **运动诗学派（05-08）** | 动感、沉浸、技术美学 | Locomotive / Active Theory / Field.io / Resn |
| **极简主义派（09-12）** | 秩序、留白、精致 | Experimental Jetset / Müller-Brockmann / Build / Sagmeister |
| **实验先锋派（13-16）** | 先锋、生成艺术、视觉冲击 | Zach Lieberman / Raven Kwok / Ash Thorp / Territory Studio |
| **东方哲学派（17-20）** | 温润、诗意、思辨 | Takram / Kenya Hara / Irma Boom / Neo Shen |

### 4.2 风格 × 场景 速查表

| 风格 | 网页 | PPT | PDF | 信息图 | 封面 | 最佳路径 |
|------|:---:|:---:|:---:|:-----:|:---:|:-------:|
| 01 Pentagram | ★★★ | ★★★ | ★★☆ | ★★☆ | ★★★ | HTML |
| 02 Stamen | ★★☆ | ★★☆ | ★★☆ | ★★★ | ★★☆ | 混合 |
| 03 Info Architects | ★★★ | ★☆☆ | ★★★ | ★☆☆ | ★☆☆ | HTML |
| 04 Fathom | ★★☆ | ★★★ | ★★★ | ★★★ | ★★☆ | HTML |
| 05 Locomotive | ★★★ | ★★☆ | ★☆☆ | ★☆☆ | ★★☆ | 混合 |
| 06 Active Theory | ★★★ | ★☆☆ | ★☆☆ | ★☆☆ | ★★☆ | AI 生成 |
| 07 Field.io | ★★☆ | ★★☆ | ★☆☆ | ★★☆ | ★★★ | AI 生成 |
| 08 Resn | ★★★ | ★☆☆ | ★☆☆ | ★☆☆ | ★★☆ | AI 生成 |
| 09 Experimental Jetset | ★★☆ | ★★☆ | ★★☆ | ★★☆ | ★★★ | 混合 |
| 10 Müller-Brockmann | ★★☆ | ★★★ | ★★★ | ★★★ | ★★☆ | HTML |
| 11 Build | ★★★ | ★★★ | ★★☆ | ★☆☆ | ★★★ | HTML |
| 12 Sagmeister & Walsh | ★★☆ | ★★★ | ★☆☆ | ★★☆ | ★★★ | AI 生成 |
| 13 Zach Lieberman | ★☆☆ | ★☆☆ | ★☆☆ | ★★☆ | ★★★ | AI 生成 |
| 14 Raven Kwok | ★☆☆ | ★★☆ | ★☆☆ | ★★☆ | ★★★ | AI 生成 |
| 15 Ash Thorp | ★★☆ | ★★☆ | ★☆☆ | ★☆☆ | ★★★ | AI 生成 |
| 16 Territory Studio | ★★☆ | ★★☆ | ★☆☆ | ★★☆ | ★★★ | AI 生成 |
| 17 Takram | ★★★ | ★★★ | ★★★ | ★★☆ | ★★☆ | HTML |
| 18 Kenya Hara | ★★☆ | ★★★ | ★★★ | ★☆☆ | ★★★ | HTML |
| 19 Irma Boom | ★☆☆ | ★★☆ | ★★★ | ★★☆ | ★★★ | 混合 |
| 20 Neo Shen | ★★☆ | ★★☆ | ★★☆ | ★★☆ | ★★★ | AI 生成 |

### 4.3 代表风格详解

#### 01 · Pentagram（Michael Bierut）— 字体即语言，网格即思想

**哲学内核**：设计是沟通工具，不是艺术表达。极度克制的颜色、精准的瑞士网格、字体排印作为主要视觉语言、战略性使用负空间（60%+ 留白）。

**视觉特征**：
- 极度克制的颜色（黑白 + 1 个品牌色）
- 瑞士网格系统的现代演绎
- 字体排印作为主要视觉语言
- 负空间的战略性使用

**代表作**：Hillary Clinton 2016 campaign identity

#### 07 · Field.io — 运动诗学

**哲学内核**：技术不是目的，是通向诗意体验的媒介。数字运动不是动画，是情感叙事。

**视觉特征**：
- 粒子系统与流体动力学模拟
- 低饱和色调 + 精准光效
- 数字运动作为情感载体
- 沉浸式全屏体验

**最佳路径**：AI 生成（图片直出效果最好）

#### 18 · Kenya Hara — 东方极简

**哲学内核**：「无」的设计。设计不是加法，是发现事物本来的样子。留白不是空白，是呼吸的空间。

**视觉特征**：
- 大量留白（60%+）
- 自然色调（米白、炭灰、竹青）
- 极度克制的排版
- 材质感的微妙暗示

**代表作**：无印良品设计系统

## 五、5 维评审体系

设计完成后，Huashu Design 提供专家级 5 维度评审，以雷达图形式呈现，并输出 Keep / Fix / Quick Wins 可操作修复清单。

### 5.1 五维定义

| 维度 | 满分 | 评审要点 |
|------|:----:|---------|
| **哲学一致性** | 10 | 设计是否完美体现选定哲学的核心精神，每个细节是否有哲学依据 |
| **视觉层级** | 10 | 用户视线是否自然沿设计者意图流动，信息获取是否零摩擦 |
| **细节执行** | 10 | 像素级精确，对齐、间距、颜色是否无瑕疵 |
| **功能性** | 10 | 每个设计元素是否服务于目标，是否有冗余装饰 |
| **创新性** | 10 | 是否令人耳目一新，在哲学框架内找到了独特表达 |

### 5.2 评分标准

**哲学一致性评分标准**：
- 9-10：设计完美体现了选定哲学的核心精神
- 7-8：整体方向正确，核心特征到位，个别细节偏离
- 5-6：能看出意图，但执行时混入了其他风格元素
- 3-4：仅在表面模仿，未理解哲学内核
- 1-2：与选定哲学基本无关

**视觉层级评分标准**：
- 9-10：用户视线自然沿设计者意图流动，零摩擦
- 7-8：主次关系清晰，偶有 1-2 处层级模糊
- 5-6：能分出标题和正文，但中间层级混乱
- 3-4：信息平铺，没有明确的视觉入口
- 1-2：混乱，用户不知道先看哪里

**细节执行评分标准**：
- 9-10：像素级精确，对齐、间距、颜色无任何瑕疵
- 7-8：整体精致，有 1-2 处微小对齐/间距问题
- 5-6：基本对齐，但间距不统一，颜色使用不够系统
- 3-4：明显的对齐错误、间距混乱、颜色过多
- 1-2：粗糙，看起来像草稿

**功能性评分标准**：
- 9-10：每个设计元素都服务于目标，零冗余
- 7-8：功能导向明确，有少量可删减的装饰
- 5-6：基本可用，但有明显的装饰性元素分散注意力
- 3-4：形式大于功能，用户需要努力寻找信息
- 1-2：完全被装饰淹没，失去了传达信息的能力

**创新性评分标准**：
- 9-10：令人耳目一新，在该哲学框架内找到了独特表达
- 7-8：有自己的想法，不是简单的模板套用
- 5-6：中规中矩，看起来像模板
- 3-4：大量使用了 cliché（如渐变圆球代表 AI）
- 1-2：完全是模板或素材拼凑

### 5.3 常见设计问题 Top 10

1. **AI 科技 cliché**：渐变圆球、数字雨、蓝色电路板、机器人脸
2. **字号层级不足**：标题和正文差距太小（<2.5 倍）
3. **颜色过多**：使用 5 种以上颜色，没有主次
4. **间距不统一**：元素间距随意，没有系统
5. **留白不足**：所有空间都被内容填满
6. **字体过多**：使用 3 种以上字体
7. **对齐不一致**：有的左对齐，有的居中
8. **装饰大于内容**：背景图案/渐变/阴影抢了主要内容风头
9. **赛博霓虹滥用**：深蓝底 `#0D1117` + 霓虹色发光效果
10. **信息密度与载体不匹配**：PPT 里放了一整页文字

### 5.4 评审输出模板

```markdown
## 设计评审报告

**总体评分**：X.X/10 [优秀(8+)/良好(6-7.9)/需改进(4-5.9)/不合格(<4)]

**分项评分**：
- 哲学一致性：X/10 [一句话说明]
- 视觉层级：X/10 [一句话说明]
- 细节执行：X/10 [一句话说明]
- 功能性：X/10 [一句话说明]
- 创新性：X/10 [一句话说明]

### 优点（Keep）
- [具体指出做得好的地方，用设计语言描述]

### 问题（Fix）
**1. [问题名称]** — ⚠️致命 / ⚡重要 / 💡优化
- 当前：[描述现状]
- 问题：[为什么这是问题]
- 修复：[具体操作，含数值]

### 快速修复清单（Quick Wins）
如果只有 5 分钟，优先做这 3 件事：
- [ ] [最有影响力的修复]
- [ ] [第二重要的修复]
- [ ] [第三重要的修复]
```

## 六、MP4 / GIF 导出体系

### 6.1 导出规格

| 格式 | 规格 | 适合场景 | 典型大小（30s） |
|---|---|---|---|
| MP4 25fps | 1920×1080 · H.264 · CRF 18 | 公众号嵌入、视频号、YouTube | 1-2 MB |
| MP4 60fps | 1920×1080 · minterpolate 插帧 · H.264 | 高帧率展示、B 站、作品集 | 1.5-3 MB |
| GIF | 960×540 · 15fps · palette 优化 | Twitter/X、README、Slack 预览 | 2-4 MB |

### 6.2 完整导出流水线

```bash
# 1. 录 25fps 基础 MP4
NODE_PATH=$(npm root -g) node "$SKILL/scripts/render-video.js" my-animation.html

# 2. 派生 60fps MP4 和 GIF
bash "$SKILL/scripts/convert-formats.sh" my-animation.mp4

# 产出清单：
# my-animation.mp4         (25fps · 1-2 MB)
# my-animation-60fps.mp4   (60fps · 1.5-3 MB)
# my-animation.gif         (15fps · 2-4 MB)
```

### 6.3 背景音乐（BGM）

`add-music.sh` 脚本支持给无声 MP4 混入场景化背景音乐：

```bash
bash add-music.sh <input.mp4> [--mood=<name>] [--music=<path>] [--out=<path>]
```

内置 BGM 库：

| mood | 风格 | 适配场景 |
|------|------|---------|
| `tech`（默认） | Apple Silicon / 苹果发布会，极简合成器+钢琴 | 产品发布、AI 工具 |
| `ad` | upbeat 现代电子，有 build + drop | 社交媒体广告、产品预告 |
| `educational` | 温暖明亮、轻吉他/电钢琴 | 科普、教程介绍 |
| `tutorial` | lo-fi 环境音，几乎无存在感 | 软件演示、编程教程 |

### 6.4 60fps 模式选择

| 模式 | 命令 | 兼容性 | 使用场景 |
|---|---|---|---|
| 帧复制（默认）| `convert-formats.sh in.mp4` | QuickTime/Safari/Chrome/VLC 全通 | 通用交付、社交媒体 |
| minterpolate 插帧 | `convert-formats.sh in.mp4 --minterpolate` | macOS QuickTime/Safari 可能拒打 | B 站等需要真插帧的场景 |

**为什么默认改成帧复制？** minterpolate 输出的 H.264 elementary stream 有 known compat bug——macOS QuickTime 打不开的问题。之前多次踩到，默认值因此改为更安全的帧复制。

## 七、使用说明：安装、配置与实战演示

### 7.1 安装

一行命令，即装即用：

```bash
npx skills add alchaincyf/huashu-design
```

跨 agent 通用，支持：
- **Claude Code**
- **Cursor**
- **Codex**
- **OpenClaw**
- **Hermes**

### 7.2 核心工作流：Junior Designer 模式

Huashu Design 默认采用 Junior Designer 工作流，核心理念是**「理解错了早改比晚改便宜 100 倍」**：

**Step 1 · 开工前先展示假设**
HTML 文件开头写下 assumptions + reasoning + placeholders，尽早 show 给用户确认方向。

**Step 2 · 用户确认后填充内容**
React 组件填 placeholder，再 show 一次让用户看进度。

**Step 3 · 迭代细节**
填充实际内容 → variations → Tweaks 三步分别再 show 一次。

**Step 4 · 交付前验证**
用 Playwright 肉眼过一遍浏览器，截图确认各时间点状态正确。

### 7.3 典型使用场景

#### 场景一：设计方向顾问（需求模糊时）

当用户说"做个好看的"、"帮我设计"、"不知道要什么风格"时，触发 Fallback 模式：

```
「做一份 AI 心理学的演讲 PPT，推荐 3 个风格方向让我选」
```

**完整 8 Phase 流程**：
1. 深度理解需求（提问最多 3 个）
2. 顾问式重述（100-200 字）
3. 推荐 3 套设计哲学（必须来自不同流派）
4. 展示预制 Showcase 画廊（8 场景 × 3 风格）
5. 并行生成 3 个视觉 Demo
6. 用户选择
7. 生成 AI 提示词
8. 进入主干 Junior Designer 流程

#### 场景二：交互原型（App/Web）

```
「做个 AI 番茄钟 iOS 原型，4 个核心屏幕要真能点击」
```

**专属守则**：
- 默认从 Wikimedia/Met/Unsplash 取真图，不用米白卡摆着
- iPhone 15 Pro 精确机身（灵动岛 / 状态栏 / Home Indicator）
- 每台设备包 AppPhone 状态管理器可交互
- 交付前跑 Playwright 点击测试

#### 场景三：动画导出

```
「把这段逻辑做成 60 秒动画，导出 MP4 和 GIF」
```

**流程**：
1. 写 Stage + Sprite 动画 HTML
2. Playwright 截图验证各时间点
3. `render-video.js` 录制
4. `convert-formats.sh` 派生格式
5. `add-music.sh` 混入 BGM

#### 场景四：HTML Slides → 可编辑 PPTX

```
「做一份 13 页的产品发布幻灯片」
```

**架构选择**：
- ≥10 页 → 多文件架构（`deck_index.html` 拼接器）
- ≤10 页 → 单文件架构（`deck_stage.js`）

**PPTX 导出前提**：从第一行 HTML 起按 4 条硬约束写（文字包在 `<p>`/`<h*>` 里、`<p>` 自身无 background/border/shadow、div 不用 `background-image`、不用 CSS gradient）

### 7.4 设计方向顾问的触发与跳过

**触发条件**：
- 用户需求模糊（"做个好看的"、"帮我设计"）
- 用户明确要"推荐风格"、"给几个方向"
- 没有 design context（Figma/截图/品牌规范都没有）
- 用户主动说"我也不知道要什么风格"

**跳过条件**：
- 用户已经给了明确的风格参考 → 直接走主干流程
- 用户已经说清楚要什么 → 直接进 Junior Designer 流程
- 小修小补、明确的工具调用 → skip

## 八、开发扩展：API、插件与二次开发

### 8.1 核心 API

#### 动画引擎 API

```javascript
// Stage：时间轴容器
<Stage duration={10} playing={true}>
  {children}
</Stage>

// Sprite：时间片段
<Sprite start={0} end={3} fadeOut={0.5}>
  <MyComponent />
</Sprite>

// 读取进度
const { t, elapsed, duration } = useSprite();
const time = useTime();

// 插值
interpolate(currentTime, [0, 5], [0, 100], Easing.easeOut);

// 缓动函数
Easing.expoOut(0.5);  // Anthropic 级主 easing
Easing.spring(0.8);    // 弹簧效果
Easing.overshoot(0.7); // 带弹性的 toggle 弹出
```

#### 设备边框 API

```javascript
import { IPhoneFrame } from './assets/ios_frame.jsx';
// 渲染 iPhone 15 Pro 原型外壳
<IPhoneFrame>
  {/* 屏幕内容 */}
</IPhoneFrame>
```

### 8.2 导出工具链 API

```javascript
// 视频渲染（Node.js）
node render-video.js <html-file> [--duration=30] [--width=1920] [--height=1080] [--trim=2.2] [--fontwait=1.5]

// 格式转换
bash convert-formats.sh <input.mp4> [gif_width] [--minterpolate]

// BGM 混音
bash add-music.sh <input.mp4> [--mood=tech|ad|educational|tutorial] [--music=<path>]

// PDF 导出（多文件架构）
node export_deck_pdf.mjs --slides <slides-dir> --out deck.pdf

// PPTX 导出（多文件架构）
node export_deck_pptx.mjs --slides <dir> --out deck.pptx
```

### 8.3 二次开发指南

#### 扩展新的设计哲学

在 `references/design-styles.md` 中添加新风格：

```markdown
### 21. New Style — 风格名
**哲学**：设计理念一句话描述
**核心特征**：
- 特征 1
- 特征 2
- 特征 3

**提示词 DNA**：
```
New Style aesthetic:
- 具体视觉描述 1
- 具体视觉描述 2
- 具体视觉描述 3
```

**代表作**：[作品名]
**搜索关键词**：[可搜索的关键词]
```

#### 扩展 BGM 库

将 MP3 文件放入 `assets/` 目录，命名格式 `bgm-<mood>.mp3`，`add-music.sh` 会自动识别。

#### 扩展设备边框

在 `assets/` 下新增 `<device>_frame.jsx`，参考 `ios_frame.jsx` 的实现方式，使用 React 组件封装设备外壳，内部用 `<slot>` 接收屏幕内容。

### 8.4 品牌资产协议的二次开发扩展

核心资产协议支持扩展新的资产类型：

```javascript
// 在 SKILL.md 的 Step 2 增加新资产搜索路径
const brandAssetSearchPaths = {
  logo: ['<brand>.com/brand', '<brand>.com/press'],
  productImage: ['<brand>.com/<product>', '官方 YouTube launch film'],
  uiScreenshot: ['App Store 产品页', '官网 screenshots section'],
  // 新增资产类型
  videoAsset: ['<brand>.com/video', '官方 YouTube 频道'],
  3dModel: ['<brand>.com/3d', 'Sketchfab 官方'],
};
```

## 九、总结与生态位

### 9.1 Huashu Design 的关键价值

**1. 将设计能力从 GUI 迁移到对话**
传统设计工具（Figma、Sketch）依赖鼠标操作，设计师的手和眼无法离开屏幕。Huashu Design 让设计师（和 AI Agent）通过自然语言描述完成设计，将设计决策层和执行层彻底分离。

**2. 从「工具」到「工作流」的升级**
不是提供一个设计模板让用户套用，而是定义了完整的设计工作流（品牌资产协议 → 设计方向顾问 → Junior Designer 模式 → 5 维评审），覆盖了真实项目中从模糊需求到交付设计的全链路。

**3. Agent-agnostic 的开放生态**
不是绑定某个特定 AI Agent，而是以 skill 为单位输出，任何支持 skills.sh 协议的平台都可以使用。设计能力可以在不同 Agent 之间无缝迁移。

### 9.2 适用边界

**擅长的场景**：
- 高保真交互原型（App / Web）
- 产品发布动画 / 演讲幻灯片
- 设计方向探索与变体对比
- 信息图 / 数据可视化
- 需要导出 MP4/GIF 的动态内容

**不擅长的场景**：
- 需要图层级可编辑的 PPTX（可用 HTML，但导出到 Figma 受限）
- Framer Motion 级别的复杂动画（3D、物理模拟、粒子系统）
- 完全空白的品牌从零设计（质量会掉到 60-65 分）

**这是一个 80 分的 skill，不是 100 分的产品**。对不愿意打开图形界面的人，80 分的 skill 比 100 分的产品好用。

### 9.3 加入生态

**个人使用免费**——学习、研究、创作、给自己做东西、写文章、做副业，随便用，不用打招呼。

**企业商用需授权**——任何公司、团队、或以盈利为目的的组织使用，**必须先和花生联系获得授权**。

| 平台 | 账号 |
|------|------|
| X / Twitter | @AlchainHust |
| 公众号 | 花叔（微信搜索「花叔」）|
| B 站 | 花叔 |
| 官网 | huasheng.ai |

*本文档基于 huashu-design v2.0（2026-04-19 发布）编写，GitHub 地址：[alchaincyf/huashu-design](https://github.com/alchaincyf/huashu-design)*