---
title: "UI-TARS：字节跳动的开源 GUI Agent 全栈，和它已经停服的远程操控"
date: "2026-05-11T13:05:00+08:00"
lastmod: "2026-09-28T10:30:00+08:00"
slug: "bytedance-ui-tars-desktop-multimodal-agent"
github_repo: "bytedance/UI-TARS-desktop"
source_key: "gh:bytedance/UI-TARS-desktop"
description: "拆解 bytedance/UI-TARS-desktop：MCP 内核、DOM/视觉/混合三种浏览器控制模式的模型适配边界，免费远程操控从 2025 年 6 月上线到 8 月停服的完整时间线，以及 2026 年这套栈还剩什么、该怎么用。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "多模态", "MCP", "浏览器自动化", "字节跳动", "TypeScript"]
hiddenFromHomePage: true
---

# UI-TARS：字节跳动的开源 GUI Agent 全栈，和它已经停服的远程操控

bytedance/UI-TARS-desktop 把「让模型看懂屏幕、动手操作」这件事拆成了三层：GUI（Graphical User Interface，图形用户界面）操作模型 UI-TARS、面向终端用户的桌面应用 UI-TARS Desktop、面向开发者的通用 Agent 框架 Agent TARS。三层共用一个仓库，TypeScript 实现，Apache-2.0 许可，GitHub 星标 39,143（2026-09-28 API 读数）。

它 2025 年上半年最出圈的卖点是「免费远程操控」——点一下按钮，就能让 AI 替你操作云端电脑和浏览器。这个卖点已经失效：官方文档明确 Remote Operator 服务于 2025 年 8 月 20 日停服。今天再评估这个项目，值得看的不是远程操控，而是它作为 GUI Agent 的完整参考实现：MCP（Model Context Protocol，模型上下文协议）内核、DOM 与视觉两条控制路线、事件流协议，都在一个仓库里给出了可运行的答案。

## 先分清仓库里的三样东西

这个仓库的名字最容易让人混淆：桌面应用叫 UI-TARS Desktop，模型也叫 UI-TARS，CLI 又叫 Agent TARS。三者关系是「模型 → 应用 → 框架」：

| | UI-TARS 模型 | UI-TARS Desktop | Agent TARS |
| --- | --- | --- | --- |
| 是什么 | 视觉语言模型（VLM，Vision-Language Model），专门做 GUI 界面定位与操作 | Electron 桌面应用，连接模型后操作本地电脑和浏览器 | CLI / Web UI / 无头服务器的通用 Agent 框架 |
| 所在位置 | [bytedance/UI-TARS](https://github.com/bytedance/UI-TARS)（独立仓库，11.5k stars） | 本仓库 `apps/ui-tars` | 本仓库 `multimodal/` 目录，npm 包 `@agent-tars/cli` |
| 给谁用 | 模型使用者与部署者 | 终端用户，下载 `.dmg` / `.exe` 即装 | 开发者，`npx` 一行启动 |
| 控制对象 | —— | 本地计算机与浏览器 | 浏览器为主，配合 MCP 工具链 |

本文说的「TARS 技术栈」指后两者。模型层是独立仓库，Desktop 的本地 Operator 需要自行配置模型服务才能跑起来——这一点原文档常被忽略，后文细说。

## 内核：MCP 与事件流

README 对 Agent TARS 架构的表述是「The kernel is built on MCP」：内核建在 MCP 之上，同时支持挂载第三方 MCP Server 连接真实世界的工具。官方文档给出的挂载方式是在配置文件里声明命令：

```ts
// agent-tars.config.ts
import { defineConfig } from '@agent-tars/interface';

export default defineConfig({
  mcpServers: {
    'mcp-server-chart': {
      command: 'npx',
      args: ['-y', '@antv/mcp-server-chart'],
    },
  },
});
```

这条示例来自官方 MCP 文档，用的图表生成服务 mcp-server-chart。文档同时给了一个实用提醒：经 stdio 连接 MCP Server 有固有延迟，会让会话创建变慢。

事件流（Event Stream）是另一条主线：协议驱动的事件流同时支撑上下文工程和 Agent UI。落到使用体验上，Web UI 里有会话管理、原生流式输出、GUI Grounding 的实时光标动画，v0.3.0 又加了 Event Stream Viewer 用于追踪和调试数据流。调试 Agent 时能看到每一步工具调用和计时，这是它比「黑盒 RPA 脚本」更可观察的地方。

## 三种浏览器控制模式：选模式本质是选模型

Agent TARS 的 Hybrid Browser Agent 支持三种浏览器操作方式，官方文档按「DOM、VLM、两者结合」划分：

| 模式 | 工作原理 | 依赖 |
| --- | --- | --- |
| `dom` | 用 Browser Use 工具集解析 DOM、标记可交互元素，不依赖视觉 | 任何能做工具调用的模型，纯文本模型（如 DeepSeek）也能用 |
| `visual-grounding` | 截图交给 GUI Agent（UI-TARS / Doubao 1.5 VL）做定位，模型返回坐标执行点击输入，不挂 DOM 工具 | 需要支持视觉定位的模型 |
| `hybrid` | 合并前两者的动作空间，由模型自行决定用哪个工具 | 同上，视觉模型为佳 |

三种模式都带 `navigate` 和 `tab` 两个基础导航工具。关键约束在模型兼容性上，官方文档的兼容表写得清楚：volcengine 的 Seed1.5-VL 对 Visual Grounding 完整支持；Anthropic 的 claude-3.7-sonnet 和 OpenAI 的 gpt-4o 这一项都标注为「施工中」（🚧）。换句话说，选了 Claude 或 GPT 做驱动，`dom` 模式才是稳妥路线；想用视觉定位，模型基本只有火山引擎系可选。

官方文档用同一个验证码任务对比过三种模式：打开 2captcha 的普通文本验证码并「通过它」。结果是 `dom` 模式因为模型看不到屏幕，操作路径绕来绕去最终失败；`visual-grounding` 模式三轮动作直接完成——`click(point='383 502')` 激活输入框、`type('W9H5K')` 填入验证码、`click(point='339 607')` 点确认。这组对照说明两条路线的分野：结构化页面 DOM 又快又稳，视觉依赖的页面（验证码、Canvas、复杂渲染）只有看得见屏幕的模型能处理。

至于 `hybrid`，官方的说法值得留意：由于 visual-grounding 本身已包含信息提取工具，大多数场景下 hybrid 的实际表现和 visual-grounding 接近；它的价值在容错——某些场景可以先试轻量的 DOM 路线，失败再回落到视觉方案。

## 一次订票任务流过系统

README 的 Showcase 里有这样一条指令：

> Please help me book the earliest flight from San Jose to New York on September 1st and the last return flight on September 6th on Priceline

这条任务在系统里的流转大致是：Agent 拿到自然语言目标后规划步骤，浏览器工具先 `navigate` 打开 Priceline，页面上每个可交互元素随后进入模型视野——走 `visual-grounding` 路线时，模型对着截图返回坐标，浏览器执行点击和输入；走 `dom` 路线时，模型从带编号的元素列表里挑目标。每一步动作、每次工具调用的耗时、模型的思考过程都以事件形式流入事件流，Web UI 上能看到实时的光标动画，事后可用 Event Stream Viewer 回放排查。

需要说明边界：README 只提供了演示视频，没有声明任务完成率，也没有「全程无人工干预」的承诺。涉及支付这类不可逆操作的环节，仍然应该由人来完成或确认——这是使用任何 GUI Agent 的底线，不是这个项目特有的限制。

## 上手：命令与配置

Agent TARS CLI 的启动方式（README 原例，需要 Node.js ≥ 22，npm 元数据的要求是 ≥ 22.15.0）：

```bash
# npx 一行启动，进入交互式 Web UI
npx @agent-tars/cli@latest

# 或全局安装
npm install @agent-tars/cli@latest -g

# 指定模型提供商（官方 README 示例）
agent-tars --provider volcengine --model doubao-1-5-thinking-vision-pro-250428 --apiKey your-api-key
agent-tars --provider anthropic --model claude-3-7-sonnet-latest --apiKey your-api-key
```

CLI 共五个子命令：`agent-tars`（默认，交互式 UI）、`serve`（无头服务器）、`run`（静默模式，结果输出到 stdout）、`request`（直接请求 LLM 提供商）、`workspace`（管理全局工作区）。Web UI 默认端口 8888，可用 `--port` 改。

配置优先级和密钥管理是实用的部分：Agent TARS 依次查找 `agent-tars.config.ts` / `.yml` / `.yaml` / `.json` / `.js`；`--config` 可以传多个文件按序合并，也支持远程 URL；API key 可以写环境变量名，由 CLI 运行时读取：

```bash
npx agent-tars --model.provider openai --model.apiKey OPENAI_API_KEY --model.baseURL OPENAI_BASE_URL
```

UI-TARS Desktop 的路径不同：从 GitHub Releases 下载安装包（macOS 为 arm64/x64 两个 `.dmg`，Windows 为 `.exe`，无官方 Linux 包），然后在设置里配置 VLM Provider。官方 quick-start 文档给出两条路线：

1. **Hugging Face for UI-TARS-1.5**：用 Inference Endpoints 部署 UI-TARS-1.5-7B，拿到 Base URL（需以 `/v1/` 结尾）和 API Key 填入。
2. **VolcEngine Ark for Doubao-1.5-UI-TARS**：开通火山方舟的 `doubao-1.5-ui-tars-250328`，Base URL 为 `https://ark.cn-beijing.volces.com/api/v3`。

选 Provider 时文档特别提醒要选对预设（如「VolcEngine Ark for Doubao-1.5-UI-TARS」），否则 GUI 动作解析会出问题。另外，桌面版的 Browser Operator 模式要求本机装有 Chrome、Edge 或 Firefox。

模型自部署还有第三条路：本地 vLLM（要求 `vllm>=0.6.1`）或 HuggingFace Inference Endpoints，部署指南在 bytedance/UI-TARS 仓库的 `README_deploy.md`。仓库里的 `docs/deployment.md` 已改为指向这份新指南——UI-TARS-1.0 时代的旧部署文档不再维护。

## 版本时间线：高峰、停服与停滞

把 release 历史连起来看，能看清这个项目的节奏：

| 时间 | 事件 |
| --- | --- |
| 2025-01-22 | UI-TARS Desktop v0.0.1 发布，项目开源 |
| 2025-04-17 | v0.1.0：重设计 Agent UI，新增浏览器操作，接入 UI-TARS-1.5 |
| 2025-06-11 | v0.2.0：免费 Remote Computer / Browser Operator 上线——无需配置、点击即用，但仅限中国大陆，每会话 30 分钟 |
| 2025-06-25 | Agent TARS Beta 与 CLI 发布（首个 CLI release 是 0.2.9，2025-07-03） |
| 2025-08-20 | Remote Operator 服务停服；官方指引改走火山引擎 OS Agent Services 自行部署 |
| 2025-11-04 | v0.3.0：多工具流式输出、工具调用与深度思考的计时统计、Event Stream Viewer、AIO Agent Sandbox 隔离执行环境 |
| 2026-09（本文更新时） | v0.3.0 仍是最新正式版；main 分支持续提交（最近一次推送 2026-09-24） |

v0.2.0 和停服只隔了两个多月，「完全免费」的窗口期很短。v0.2.4（2025-08-21）的发布说明里已经把远程版本指向火山引擎的商业部署入口。此后一年多，桌面应用和 CLI 都没有新的正式版——仓库没有死，main 分支仍在动，但对生产使用者来说，这就是「以参考实现的节奏在维护」，不是「以产品的节奏在迭代」。评估时应按前者的预期来管理。

## 适用边界与采用顺序

**值得现在就用：** 想吃透 GUI Agent 工程实现团队。三种控制模式的取舍、MCP 工具挂载、事件流协议、Agent UI 的组织方式，这个仓库都给出了能跑通的完整答案，比读论文直观得多。个人开发者用 `npx` 加一个 API key 就能搭一条自然语言驱动的浏览器自动化流水线，成本低。

**谨慎采用：** 把它当生产级 RPA 引擎。没有 SLA，CLI 正式版停在 v0.3.0 已近一年；关键业务流程要自己兜底（AIO Sandbox 提供了隔离执行环境的起点，但运维责任在你）。需要远程操控能力的场景，官方免费服务已停，选项是火山引擎 OS Agent Services 自建，或自己部署 UI-TARS-1.5 模型。

**不必用：** 纯结构化的页面抓取和表单填充，Playwright 加选择器更轻更可控；跨浏览器测试矩阵是 Playwright / Selenium 的主场，GUI Agent 的每步推理在这个场景里是成本不是收益。

合理的上手顺序：先 `npx @agent-tars/cli@latest` 跑通默认交互 UI，用官方的订酒店示例感受事件流；再按你手头的模型选控制模式（有 Seed1.5-VL 或部署了 UI-TARS 的用 visual-grounding，用 Claude/GPT 的先走 `dom`）；确实需要桌面控制时再装 Desktop 配模型。每一步的退出成本都不高。

## 常见问题

**UI-TARS Desktop 内置模型吗？** 不内置。桌面应用是壳，模型服务要自己接：Hugging Face endpoint 跑 UI-TARS-1.5-7B，或火山方舟的 Doubao-1.5-UI-TARS，或 vLLM 自部署。「下载即用」的只有应用本身。

**还能白嫖官方的免费远程操控吗？** 不能。服务 2025-08-20 停服，此前的「免费」也仅限中国大陆、每会话 30 分钟。替代方案是火山引擎 OS Agent Services（收费的商业部署）或自己部署模型。

**它能过验证码吗？** 官方文档演示过 2captcha 的普通文本验证码：`visual-grounding` 模式能通过，`dom` 模式失败。至于 reCAPTCHA 这类带行为检测的复杂验证码，没有官方结论，也不建议拿生产流程去赌。

**Agent TARS 的代码在仓库哪里？** `multimodal/` 目录下，与 `apps/ui-tars`（桌面应用）、`packages/`（agent-infra 等基础库）同属一个 monorepo。npm 包 `@agent-tars/cli` 的 0.3.0 版实际依赖 `@tarko/agent-cli`。

**和 Playwright 是什么关系？** 两者不在一个层面。Playwright 是给程序用的浏览器自动化库，操作者是代码；Agent TARS 的操作者是模型——`dom` 模式基于 Browser Use 工具集解析页面，`visual-grounding` 模式靠视觉模型定位。前者快而脆（选择器一变就断），后者慢而韧（看得到就能点），按任务稳定性要求选。

## 资料口径

- 数据时点为 2026-09-28：stars / forks 来自 GitHub API 实时读数（39,143 / 3,966）；npm 版本来自 npmjs.com registry。
- 版本与功能描述依据：仓库 main 分支 README（2026-09）、v0.3.0 release notes（2025-11-04）、`docs/quick-start.md`、`docs/setting.md`、v0.3.0 tag 下的官方文档源（CLI / Browser / MCP / Web UI 四篇）。
- 本文未实测任务完成率、响应时间等性能指标；涉及生产采用的部分基于架构与维护状态推断，已在上文标明推断依据。
- 官方文档站 agent-tars.com，社区 Discord：[discord.gg/HnKcSBgTVx](https://discord.gg/HnKcSBgTVx)。
