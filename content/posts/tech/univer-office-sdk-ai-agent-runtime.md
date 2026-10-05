---
title: "Univer 1.0：把 Office 变成 AI Agent 的运行时"
date: 2026-09-27T03:23:02+08:00
draft: false
description: "dream-num/univer 以插件架构、Canvas 渲染引擎与统一 Facade API，把电子表格、文档、演示文稿做成可嵌入、可无头运行的 Office SDK，并在 1.0 版本把主轴转向 AI Agent 的工作面。本文拆解其架构分层、一次 Agent 任务如何流过系统，以及开源与 Pro 的边界。"
categories: ["技术笔记"]
tags: ["Univer", "Office SDK", "AI Agent", "TypeScript", "前端架构"]
github_repo: "dream-num/univer"
source_key: "gh:dream-num/univer"
slug: univer-office-sdk-ai-agent-runtime
---

## 核心判断

绝大多数「开源 Office」项目止步于做一个能用的在线表格；Univer 走的是另一条路——它不做产品，做**运行时**（runtime）。2026 年 9 月 24 日，v1.0.0 / v1.0.1 / v1.0.2 一天内连发，仓库描述同步换成 "The Office Harness for AI Agents"：同一个运行时，既渲染在浏览器里供人编辑，也跑在 Node.js 里供 Agent 读写。这个「同构 + 无头」的组合，是它区别于同类项目的关键。

给 Luckysheet 老用户补一句背景：Univer 就是它的官方后继。dream-num 已把 Luckysheet 仓库标注为 "Luckysheet upgraded to Univer" 并归档，迁移的目标就是这里。

截至 2026 年 9 月底，仓库 19,981 stars / 1,695 forks，TypeScript 为主语言，Apache-2.0 协议，1.0 发布当周仍有持续提交。

## 系统地图

理解 Univer 的最短路径，是把它的能力栈切成四层：

| 层 | 提供物 | 对应模块 |
|---|---|---|
| 渲染层 | Canvas 渲染引擎，支撑大文档表面 | `@univerjs/engine-render` |
| 计算层 | 公式引擎，独立于 UI | `@univerjs/engine-formula` |
| 业务层 | Sheets / Docs / Slides / Bases 等领域功能，全部以插件交付；Boards 已公布，PDF 在路上 | `@univerjs/sheets*`、`@univerjs/docs*` |
| API 层 | Facade API，浏览器与 Node.js 共用一套调用面 | `FUniver.newAPI(univer)` |

分层中最值得记住的一条：**公式引擎与渲染引擎都是独立包**。表格应用的性能瓶颈通常不在 UI 组件，而在公式重算与大面积重绘，Univer 把这两件事做成基础设施——README 的原话是 "Canvas-based rendering and a dedicated formula engine keep complex workbooks responsive"——数字格式、筛选这类业务能力才以插件形态叠上去。

## 插件形态的两种用法

README 给出了明确的二分法。

**Preset 模式**（快速集成）：安装 `@univerjs/presets` 与 `@univerjs/preset-sheets-core` 两个包，后者把精选插件集合、样式与 Facade 注册打包成一条 preset，几行代码得到能用的表格。适合原型与标准场景。

**Plugin 模式**（完全控制）：手动 `registerPlugin` 逐个装配。代价看得见——README 的 Sheets 示例要 import 二十多个模块、写约六十行初始化代码；收益是包列表、按需加载和 bundle 体积都由你决定。

取舍很清楚：preset 不是阉割版，只是「替你做了组合决策」的插件集合；两条路最终落在同一套 Facade API 上。从 preset 起步、需要裁剪时再切到 Plugin 模式，不用推翻已有代码。

## Agent 主轴：三条工作流，一圈卫星仓库

1.0 阶段 Univer 在 README 里专门开了 "Office Workflows for AI Agents" 一节，提出三条工作流：

1. **程序化编辑**——Agent 通过结构化 API 检查与修改 Office 内容，而非模拟鼠标键盘；
2. **输出验证**——Agent 通过内容检查、渲染截图与布局诊断确认自己的产出；
3. **Worktree 协作**——Agent 在隔离草稿里干活，人类审阅后决定合并什么。

配套动作是一圈卫星仓库，全部公开在 dream-num 组织下：`univer-workspace`（可自托管的人机协作工作区，Agent 能生成「表格小程序」——网页上的指标、图表与控件直接绑定单元格，支持数据读写与协同更新）、`univer-cli`（本地命令行工作区）、面向 DeepSeek Harness 与 OpenClaw 的 Office 集成插件、面向 WorkBuddy 的集成（README 标注为开发预览），以及 `univer-sdk-skills`——一份给 Agent 用的指令集，覆盖 SDK 集成、插件开发与 Node 后端场景。

把这些环节串起来，一次典型的 Agent 任务是这样流过系统的：Agent 在 Node.js 里无头启动 Univer（要求 Node ≥ 18.17），用 Facade API 建工作簿、写数据与公式，这一步不渲染任何 UI；产出后用内容检查、渲染截图、布局诊断做一轮自检；再把结果放进 Workspace 的隔离草稿，人在网页里审阅，决定合并哪些改动；如果这份报表最终以「表格小程序」形态交付，浏览器里跑的仍是同一个运行时，页面上的图表控件直接读写单元格。

## 开源与 Pro 的边界

需要划清的是：实时协同编辑、共享修订与 Worktree 工作流依赖对应的 Web SDK 与协作能力，包的可用性和授权随功能而异（README 原话："package availability and licensing vary by feature"）。开源仓库覆盖核心运行时与单机插件——浏览器应用、Node.js 无头运行、Web Worker/RPC 模式、多实例；协同的客户端/服务端包、SSR、服务端计算委托这些在 Univer Pro 一侧。选型前应过一遍仓库的 Open Source and Pro 章节与 univer.ai/capabilities 能力矩阵。

## 采用建议

- **产品要嵌入电子表格/文档编辑**，且不想被托管 SaaS 锁死 → Univer 是当前 TypeScript 生态里架构最完整的选择之一；
- **要在服务端批量生成/校验 Office 内容**（报表流水线、Agent 产出验证）→ 无头运行 + Facade API 是它最突出的差异化能力，同一套调用面贯穿浏览器与 Node.js 的设计在这个生态里并不多见；
- **只想快速预览 xlsx 文件** → 杀鸡用牛刀，轻量 viewer 更合适；
- **需要协同编辑等 Pro 能力** → 先确认授权条款再投入集成。

阅读路径建议：README → docs.univer.ai 的 preset 快速上手 → 需要深度定制时再回到 Plugin 模式与 Facade API 参考。1.0 意味着 API 面已承诺稳定，现在进入的集成成本是可预期的。

项目地址：https://github.com/dream-num/univer（v1.0.2，Apache-2.0）
