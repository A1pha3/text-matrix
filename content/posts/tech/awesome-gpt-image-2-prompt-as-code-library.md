---
github_repo: "freestylefly/awesome-gpt-image-2"
source_key: "gh:freestylefly/awesome-gpt-image-2"
date: '2026-08-26T03:45:00+08:00'
lastmod: "2026-09-30T00:00:00+08:00"
draft: false
title: 'awesome-gpt-image-2：把提示词当作代码管理的图像生成资产库'
slug: 'awesome-gpt-image-2-prompt-as-code-library'
description: 'awesome-gpt-image-2 收录 544 个逆向案例与 20 多套工业级提示词模板，把散文式提示词压缩成主体/光照/材质/布局可组合的结构化协议，本文拆解其原子化 schema、Agent 接入方式与防坑经验。'
categories: ['技术笔记']
tags: ['GPT-Image-2', '提示词工程', '图像生成']
---

## 核心判断

先说结论：这不是又一份"AI 图片 prompt 合集"。它真正值得看的，是把提示词从散文升级为**结构化协议**的完整方法论——544 个案例逆向拆解出可组合的原子字段，再沉淀为 20 多套带防坑指南的工业级模板，每套模板都提供面向 Agent 调用的 JSON 版本。当你的需求从"生成一张图"变成"批量、可控、可复用地生成图"，这种 Prompt-as-Code 的组织方式就开始值钱了。

## 项目概览

[freestylefly/awesome-gpt-image-2](https://github.com/freestylefly/awesome-gpt-image-2) 是 GPT-Image-2 的提示词引擎与模板库（Prompt as Code），MIT 协议，主语言 JavaScript，33k+ Stars，2026 年 4 月创建，维护活跃（最近一次提交在 2026-09-24）。

它诞生的背景是：GPT-Image-2 普及之后，AI 图像生成的竞争点从"能不能出图"变成了"能不能**稳定、可控、可复用**地出图"。社区里散落的案例是一堆孤立样本，而这个项目做的事是把它们压缩成结构化资产，方便 Agent 与自动化工作流直接复用。README 把设计目标写成三条：原子化 schema（主体、光照、材质、布局、视觉细节各自成段、自由组合），面向 Agent 与脚本的工作流友好，以及对布局、文案、信息层级的结构化控制。

## 内容架构：从案例到模板的两层设计

仓库分两层，对应两种使用方式。

**第一层：案例画廊（544 个）**。按 13 个视觉类别组织，每条案例包含原始提示词与产出图，按案例数排序：

| 类别 | 案例数 |
|------|--------|
| 海报与排版 | 90 |
| 摄影与写实 | 78 |
| UI 与界面 | 73 |
| 插画与艺术 | 59 |
| 图表与信息可视化 | 53 |
| 电商产品 | 42 |
| 角色与人物 | 31 |
| 其他应用场景 | 28 |
| 品牌 Logo | 27 |
| 场景叙事 | 21 |
| 国风历史 | 16 |
| 建筑空间 | 12 |
| 文档出版 | 11 |

画廊分两部分维护（案例 1–165、166–544），最新的社区投稿持续追加在第二部分末尾。

**第二层：工业级模板（20 多套）**。从案例中提炼出的填空式模板，按同样的 13 个类别组织，每个类别附带"防坑指南"。这是整个项目含金量最高的部分。

**附加层：GPT Image 2.5 对比专区**。2026 年 9 月新增。OpenAI 把 GPT-Image-2.5 拆成两个变体：Sunburst 主打图像生成与精确编辑，Flare 主打快速日常出图。专区挑了 4 个画廊案例（#532 柠檬 campaign、#527 里约微缩景观、#523 曼哈顿水彩、#510 比熊店标），保留原图，用完整画廊提示词在无参考图的条件下重新生成一次，提供拖动分割线和并排两种同提示词对比视图。README 特意注明"原始生成条件与确切的工具模型 ID 未经验证"——样本标注做得算诚实，对比结论自己看图判断。

## 原子化 Schema：结构化协议的核心

项目的设计哲学是把一段提示词拆成可组合的原子部分：

- **主体**（subject）——画什么
- **光照**（lighting）——什么氛围
- **材质**（material）——什么质感
- **布局**（layout）——信息怎么排
- **视觉细节**（visual details）——风格收尾

以 UI 截图生成为例，模板同时提供两种形态。文本版直接填空：

```text
为[产品类型]生成一张[平台]界面图。
核心功能：[功能点A]、[功能点B]、[功能点C]。
视觉风格：[极简/科技/拟物]，主色[颜色]，强调色[颜色]。
布局：[顶部导航/双栏/卡片流]，信息层级清晰，留白充足。
输出：高保真UI截图，文字清晰可读，比例[9:16/16:9]。
```

JSON 版面向 Agent 与脚本调用：

```json
{
  "type": "UI Screenshot",
  "platform": "iOS",
  "product": "Fitness App",
  "layout": "Card-based feed with bottom tab bar",
  "style": {
    "theme": "Dark Mode",
    "primary_color": "Neon Green",
    "typography": "Clean sans-serif"
  },
  "content": {
    "header": "Today's Activity",
    "cards": [
      {"title": "Running", "data": "5.2 km", "button": "Start"},
      {"title": "Calories", "data": "340 kcal"}
    ]
  },
  "constraints": "High fidelity, readable text, 9:16 aspect ratio"
}
```

JSON 版的意图很明确：当 Claude Code、Cursor 这类 Agent 要调用图像生成 API 时，结构化字段比自然语言更可控——布局、色彩、约束条件各自独立，改一处不动全身。

## 防坑指南：实战踩出来的规则

每套模板附带的防坑指南是逆向案例后的经验沉淀，UI 类别的几条规则相当具体：

1. **不给模糊指令**：必须明确"平台 + 比例 + 布局"，否则模型会乱排版。
2. **强制文字锁定**：明确要求"文字绝对可读，必须显示指定的中文"，避免出现乱码按钮和占位文本。
3. **区分平台特征**：X 有蓝勾认证与转发/引用区分，抖音有音乐碟片和点赞动画，小红书是双列瀑布流——生成截图前先指定平台，否则模型会混搭出四不像。
4. **直播界面先定场景**：带货直播和才艺直播的 UI 布局差异很大，先锁定直播类型再填细节。
5. **特殊比例写最前**：车机、智能家居等中空屏幕有固定比例（如 21:9），必须写在提示词最前面，否则模型默认输出手机 9:16。

这些规则的价值不在"知道了"，而在于它们是从大量失败案例中归纳出的边界条件——自己踩一遍的成本远高于直接抄。

## 接入 Agent 工作流

仓库内置 `gpt-image-2-style-library` Skill，数据来源与画廊站共用同一份 `data/style-library.json`，用于让 Agent 按风格、模板、类别、场景标签挑选提示词。三种装法：

```bash
# 推荐：装进 Claude Code 与 Codex
npx skills add freestylefly/awesome-gpt-image-2 --skill gpt-image-2-style-library --agent claude-code codex --global --yes --copy
```

```text
# Claude Code 插件市场
/plugin marketplace add freestylefly/awesome-gpt-image-2
/plugin install gpt-image-2-style-library@awesome-gpt-image-2
```

```bash
# npm CLI，写入本地 Agent 目录
npm install -g gpt-image-2-style-library
gpt-image-2-style-library install all
```

`install all` 会把 Skill 写进 `~/.codex/skills`、`~/.claude/skills`、`~/.agents/skills`，装完重启 Agent 会话生效。调用方式就是一句自然语言，比如"用 gpt-image-2-style-library 给 Codex 生成一张信息图的提示词"。

README 另有英文、简体中文、日文三语版本。

## 画廊站与在线生成

[可视化画廊站](https://gpt-image2.canghe.ai/)支持大图预览、完整提示词复制、按风格/场景过滤，并可回跳 GitHub 源案例。它已经不只是展示页：登录用户可以用平台积分在线生成，也可以在浏览器里填自己的 APIMart key 直接调用；积分包与 Stripe、支付宝付费的配置清单也在仓库里。

## 适用边界

- 仓库本身是**提示词资产库**。不接 API 也能照着模板手动填空出图；要批量或自动化才需要自己接入 GPT-Image-2（官方 API 或第三方中转），或者用画廊站的在线生成。
- 案例与模板带有明显的**中文互联网场景偏向**（社交截图、国风、直播带货类模板很细），欧美场景的覆盖密度相对一般。
- 按仓库免责声明的说法，项目"仅整理公开可访问的社区提示词与示例图片"，模板是逆向改写后的产物。参考时以结构为主，不必逐字照搬。

## 小结

awesome-gpt-image-2 把"提示词工程"从灵感问题变成了工程问题。偶尔出图的人，可以把它当按类别查的案例字典；要做批量生产管线的人，它的 JSON 模板加 Skill 封装提供了一条从"抽卡"到"流水线"的现实路径。案例仍在持续追加，模板与防坑指南跟着案例走——把它当一份持续更新的活资产来看，比当成某个时点的快照更合适。
