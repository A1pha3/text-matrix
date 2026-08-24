---
title: "潮流周刊 Weekly：用六年 278 期写出来的个人品牌"
date: "2026-08-21T00:00:00+08:00"
slug: weekly-trendy-weekly-personal-blog
github_repo: "tw93/Weekly"
description: "解析 tw93/Weekly：从 2020 年 11 月连载至今的潮流周刊，Astro 静态站、中英双语、Pagefind 搜索、PhotoSwipe 灯箱，内容以封面照片和随笔为主，每周一更新。"
categories: ["技术笔记"]
tags: ["Astro", "Tailwind CSS", "周刊", "个人博客"]
draft: false
---

# 潮流周刊 Weekly：用六年 278 期写出来的个人品牌

## 学习目标

读完本文，你会知道：

- Weekly 是一份什么样的周刊，一期内容由哪些部分组成
- 这个站点的技术栈与内容管线如何组织（Astro + Tailwind + 静态 Markdown）
- 一期内容从拍摄、写作到上线要经过哪些环节
- 想 Fork 自用或借鉴时，该从哪里入手，哪些部分不必照搬

## 目录

- [它是什么](#它是什么)
- [数据快照](#数据快照)
- [一期的内容长什么样](#一期的内容长什么样)
- [技术架构](#技术架构)
- [一期从拍摄到上线](#一期从拍摄到上线)
- [站点周边的工程能力](#站点周边的工程能力)
- [什么时候值得 Fork](#什么时候值得-fork)
- [自测题](#自测题)
- [练习](#练习)
- [进阶路径](#进阶路径)
- [资料口径说明](#资料口径说明)

---

## 它是什么

**Weekly**（潮流周刊，[github.com/tw93/Weekly](https://github.com/tw93/Weekly)）是杭州产品工程师 Tw93 的一份个人周刊，官方描述是「记录工程师 Tw93 的不枯燥生活，每周一发布」。Tw93 也是 Pake、Mole、Kaku、MiaoYan、Waza、Kami 等开源项目的作者。

先给一个判断：这个项目的价值不在技术方案有多精巧，而在于它把「每周记录一次生活」坚持了六年，并且围绕它攒出了一套低维护成本的自动化管线。对想建立个人品牌、想验证长期主义的技术人来说，它比大多数「周报脚手架」更有参考价值——内容真实、可回溯，工程也足够轻。

第 1 期「安吉黄昏」发布于 2020 年 11 月 24 日，当时的定位是「记录每周看到的前端潮流技术」；到第 278 期「大巧若拙」（2026 年 8 月 17 日），它已经演变成以封面照片和随笔为主体、顺带推荐好工具的生活周刊。期数标题普遍很短，三到六个字，比如硬件之美、飞机飞丢、春天小姐、去太子湾。

## 数据快照

以下数据来自 GitHub API 与周刊站点，采集于 2026-08-21：

| 指标 | 数值 |
|------|------|
| 仓库 | [tw93/Weekly](https://github.com/tw93/Weekly) |
| 仓库创建时间 | 2022-02-21（内容连载始于 2020-11-24） |
| Star | 868 |
| Fork | 133 |
| Watch | 35 |
| 已发布期数 | 278（截至 2026-08-17） |
| 提交数 | 1,389 |
| 标签 | V0.8、V0.7.0、V0.6.0、V0.5.0、V0.4.0、V0.1 |
| 主要语言 | CSS 约 46%、Astro 约 25%、TypeScript 约 16%、JavaScript 约 13% |
| 许可证 | package.json 声明 MIT，仓库未单独放置 LICENSE 文件 |
| 贡献者 | 4 人，tw93 占 1,418 次提交，其余 3 人各 1 次 |
| 站点 | https://weekly.tw93.fun |
| RSS | https://weekly.tw93.fun/rss.xml |

几点说明：Star 数增长不快（六年不到 900），但换来了稳定的读者订阅和讨论区互动。语言占比是 GitHub 按字节统计的当前快照，随提交变化，不必当作精确值。网站仓库 2022 年才创建，更早的内容曾以 GitHub Readme 等形式存在，后来用 Astro 重建了官网才迁到 GitHub。

## 一期的内容长什么样

以第 263 期「硬件之美」为例，一期正文由下面几块组成：

- **封面照片加一段封面语**：交代照片背后的场景或心情。
- **新文章发布**：Tw93 在个人博客（tw93.fun）新写的长文，附一段自荐。
- **产品发布、产品更新**：作者自己的开源项目动态，比如 Waza、Kaku 的版本更新。
- **潮流工具**：这一周看到的好工具或好内容，附上手体验。
- **随便写写**：一段随笔，常常藏着方法论。

它不是单纯的生活流水账，而是「个人生活 + 作者自己的项目 + 工具推荐 + 思考」的混合体。封面照片负责情绪，正文负责信息量。

标题短是刻意的设计。传统技术周报习惯起「第 N 期：某某技术专题」这样的长名，Weekly 的短标题降低了每一期的创作门槛——随手就能定，不用为起名纠结。标题门槛低，是六年持续更新的前提之一。

## 技术架构

把站点拆开看，有两条并行线：一条是内容（Markdown 文章如何变成页面），一条是样式与交互（Tailwind 与前端能力）。先拆边界，再分别看。

### 内容线：Astro 静态生成，文件名即元数据

站点基于 Astro（当前为 Astro 5）以 SSG 模式构建，一期文章就是 `src/pages/posts/` 下的一页 Markdown，例如 `263-硬件之美.md`。

关键设计在 `astro.config.mjs` 的 defaultLayoutPlugin：它从文件名解析出期数和标题写入 frontmatter（issueNumber、issueTitle、numericUrl），生成 `/posts/263` 这样的数字路由；同时从正文第一张图片提取封面，从正文抽取 description，日期缺省时用文件创建时间兜底。作者写文章时几乎不用维护元数据，期数、封面、摘要都自动推导。

i18n 配置了 zh 与 en 两种语言，默认中文，英文版放在 `/en/posts/`。仓库内还有一套基于 Grok API 的自动化翻译工作流脚本，负责把中文期同步成英文。

### 样式与交互线：Tailwind 加图片处理

样式用 Tailwind CSS（`tailwind.config.cjs`，Tailwind 3）。图片是这个站的重头，处理链条比较完整：

- `rehype-image.js`：仓库根目录的自定义 rehype 插件（约 6 KB，基于 unist-util-visit），统一处理文章图片。
- 懒加载：lozad（devDependencies 中可见 @types/lozad）。
- 灯箱：PhotoSwipe 5，配合提交记录里的「图片缩放支持键盘导航与动态背景」。
- 构建前探测：`prebuild` 跑 `scripts/probe-images.js`，用 probe-image-size 检查图片是否失效，避免发布死链。
- 社交图：第 110 期起使用 `weekly.tw93.fun/assets/{期数}.jpg` 作为 Twitter 卡片图。

### 搜索与部署

- 站内搜索：Pagefind，`postbuild` 阶段生成索引（`pagefind --site dist`），配 @pagefind/default-ui。
- 部署：仓库根目录有 `vercel.json`，站点托管在 Vercel。
- 其他脚本：`sync:content` 同步内容并生成 AI skill 文件；`check:content` 校验中英文内容一致性；`tests/*.test.js` 用 node:test 做单元测试。

## 一期从拍摄到上线

把上面的机制串起来，一期内容的完整路径大致是：

1. 拍一张封面照片，写一段封面语和几段正文，落成一个 Markdown 文件，文件名是「期数-标题.md」。
2. push 到 main 分支。
3. 构建前 `probe-images.js` 探测文中图片是否有效。
4. Astro 构建：defaultLayoutPlugin 解析期数与标题、抽封面与摘要，生成 `/posts/{期数}` 页面；rehype-image 处理图片（懒加载、灯箱属性）。
5. 构建后 Pagefind 生成搜索索引。
6. Vercel 部署上线，RSS（@astrojs/rss）同步更新。
7. 自动化翻译工作流用 Grok API 生成英文版，落到 `/en/posts/`。
8. 在 Twitter、GitHub 上分发。

这八步里，作者手工参与的集中在第 1 步（写作）和第 8 步（分发），中间基本全是自动化。这也是这个站能长期低成本运行的原因。

## 站点周边的工程能力

- **交流**：仓库启用了 GitHub Discussions，README 邀请读者通过 discussions/22 推荐好东西。
- **AI 运维**：仓库维护了 AGENTS.md、CLAUDE.md 和 `.agents/skills/github-ops`、`.claude/skills/github-ops`，用 AI 编码代理参与发布与仓库维护，提交记录里能看到这类自动化提交。
- **内容校验**：`check:content` 对比中英文内容一致性，`test:unit` 跑单元测试，测试通过才走发布。
- **商业化**：Weekly 本身没有商业化动作，Tw93 的付费尝试发生在另一个产品（Mole for Mac）上，与周刊无关。

## 什么时候值得 Fork

把 Weekly 当「周报脚手架」用时，几点建议：

- 想搭一个类似的照片加随笔周刊：值得 Fork。内容管线（文件名即元数据、图片探测、Pagefind、双语）是现成且验证过的，按仓库里的 Deploy.md 走即可。
- 想直接复制它的「生活方式」：不必。它的核心资产是六年积累的真实内容与读者信任，这部分无法复制；能复制的只有工程结构和发布节奏。
- 只想要一个静态博客：不必从它开始。用 Astro 官方模板更贴合需求，Weekly 的长处不在通用性。

一句话结论：Weekly 值得借鉴的是「低维护成本的内容管线 + 每周一次的稳定节奏」，而不是某一个具体功能。

## 自测题

1. **Weekly 第一期发布于什么时候，当时的定位是什么？**
   <details>
   <summary>查看答案</summary>
   2020 年 11 月 24 日，第 1 期「安吉黄昏」。当时定位是记录每周看到的前端潮流技术，后来演变为以封面照片和随笔为主的生活周刊。
   </details>

2. **站点的技术栈是什么？**
   <details>
   <summary>查看答案</summary>
   Astro 5（SSG）+ Tailwind CSS 3，文章是 src/pages/posts/ 下的 Markdown；搜索用 Pagefind，图片灯箱用 PhotoSwipe，懒加载用 lozad，部署在 Vercel。
   </details>

3. **期数和标题是从哪里来的？**
   <details>
   <summary>查看答案</summary>
   从文件名解析。defaultLayoutPlugin 把「263-硬件之美.md」拆成期数 263 和标题「硬件之美」，据此生成 /posts/263 路由。
   </details>

4. **构建前后各有一个自动化脚本，分别做什么？**
   <details>
   <summary>查看答案</summary>
   prebuild 的 probe-images.js 用 probe-image-size 探测图片是否有效，避免死链；postbuild 的 Pagefind 生成站内搜索索引。
   </details>

5. **英文版内容是怎么来的？**
   <details>
   <summary>查看答案</summary>
   i18n 配置了 zh/en，仓库内有基于 Grok API 的自动化翻译工作流脚本，把中文期同步为 /en/posts/ 下的英文版。
   </details>

## 练习

### 练习 1：读两期，总结栏目

打开 weekly.tw93.fun，挑第 263 期和最近一期，分别列出正文包含哪些栏目，对比它们是否一致。

### 练习 2：追踪一次翻译提交

在仓库提交历史里找最近一次「feat: add issue NNN with English translation」，看它改动了哪些文件，理解翻译工作流如何触发。

### 练习 3：本地跑起来

Fork 仓库，`pnpm install` 后 `pnpm dev`，在 src/pages/posts/ 下新增一页 Markdown，观察路由、封面、摘要是否按文件名自动生成。

## 进阶路径

1. 学 Astro 的内容管线：了解 content collections 与自定义 remark/rehype 插件，理解 defaultLayoutPlugin 这类「文件名即元数据」的做法。
2. 学 Tailwind 与图片性能：把懒加载、灯箱、图片探测这套组合拆开，研究为什么先探测再构建能省事。
3. 学双语站点的翻译流程：i18n 路由与自动化翻译脚本的配合方式。
4. 想把个人品牌做起来，可以参考的方向是：固定节奏、低创作门槛、内容可回溯，而不是追求单篇爆款。

## 资料口径说明

本文数据来自以下来源，采集时间 2026-08-21：

- GitHub API：仓库信息、Star/Fork/提交数、语言占比、标签、贡献者（api.github.com/repos/tw93/Weekly）。
- 周刊站点：期数与标题、栏目结构、第一期发布日期（weekly.tw93.fun）。
- 仓库源码：package.json、astro.config.mjs、README.md、提交记录。

处理原则：随提交变化的数据（Star、语言占比、提交数）标注了快照时间；许可证以 package.json 声明与仓库实际文件为准；翻译工作流等细节以提交记录为准，未逐一运行验证。
