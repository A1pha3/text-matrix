---
title: "ACE-Step UI：开源版 Suno 来了，Spotify 风格的本地 AI 音乐生成界面"
date: "2026-04-29T16:41:29+08:00"
slug: ace-step-ui-ai-music-generation-guide
github_repo: "ace-step/ACE-Step-1.5"
source_key: "gh:ace-step/ACE-Step-1.5"
description: "ACE-Step UI 是 ACE-Step 1.5 AI 音乐生成模型的第三方 Web UI，Spotify 风格界面，完全本地运行、免费无限制，是 Suno 的开源替代方案。"
draft: false
categories: ["技术笔记"]
tags: ["React", "TypeScript", "AI音乐", "Tailwind CSS", "开源"]
---

# ACE-Step UI：开源版 Suno 来了，Spotify 风格的本地 AI 音乐生成界面

## 学习目标

阅读本文后，你将能够：

1. 说出 ACE-Step UI 与 Suno（在线 AI 音乐生成平台）等商用方案在数据流向、成本和部署形态上的差异。
2. 复述 ACE-Step UI 的三层结构——React 前端、Express 服务端、ACE-Step 1.5 引擎——各自的职责边界与两层通信方式。
3. 在本地完成引擎与 UI 的安装对接，并跑通一次完整的生成—播放—归档流程。
4. 根据硬件条件和使用场景，判断是否采用 ACE-Step UI，并选择合适的部署路径。

## 目录

- [1. 项目概述](#1-项目概述)
  - [1.1 ACE-Step UI 是什么](#11-ace-step-ui-是什么)
  - [1.2 核心数据](#12-核心数据)
  - [1.3 为什么需要 ACE-Step UI](#13-为什么需要-ace-step-ui)
  - [1.4 系统总览](#14-系统总览)
- [2. 界面与功能](#2-界面与功能)
  - [2.1 Spotify 风格的视觉语言](#21-spotify-风格的视觉语言)
  - [2.2 生成模式与参数](#22-生成模式与参数)
  - [2.3 库管理与内置工具](#23-库管理与内置工具)
- [3. 架构设计](#3-架构设计)
  - [3.1 技术栈选型](#31-技术栈选型)
  - [3.2 仓库布局与前端结构](#32-仓库布局与前端结构)
  - [3.3 与 ACE-Step 引擎的通信](#33-与-ace-step-引擎的通信)
  - [3.4 可选的外部服务](#34-可选的外部服务)
- [4. 任务如何流过系统](#4-任务如何流过系统)
- [5. 安装与使用](#5-安装与使用)
  - [5.1 环境要求](#51-环境要求)
  - [5.2 安装步骤](#52-安装步骤)
  - [5.3 局域网访问](#53-局域网访问)
  - [5.4 基本使用流程](#54-基本使用流程)
- [6. 代码示例](#6-代码示例)
  - [6.1 生成表单组件](#61-生成表单组件)
  - [6.2 音频播放器封装](#62-音频播放器封装)
  - [6.3 服务层与轮询](#63-服务层与轮询)
  - [6.4 会话上下文](#64-会话上下文)
- [7. 练习与自测](#7-练习与自测)
  - [7.1 练习](#71-练习)
  - [7.2 自测题](#72-自测题)
- [8. 适用场景与局限性](#8-适用场景与局限性)
  - [8.1 最佳使用场景](#81-最佳使用场景)
  - [8.2 当前局限性](#82-当前局限性)
- [9. 常见问题与排查](#9-常见问题与排查)
  - [9.1 引擎或服务端连不上](#91-引擎或服务端连不上)
  - [9.2 生成失败或显存不足](#92-生成失败或显存不足)
  - [9.3 音频无法播放或时长显示 0:00](#93-音频无法播放或时长显示-000)
  - [9.4 历史记录丢失](#94-历史记录丢失)
  - [9.5 系统级排查指引](#95-系统级排查指引)
- [10. 采用顺序与决策建议](#10-采用顺序与决策建议)
  - [10.1 推荐的采用顺序](#101-推荐的采用顺序)
  - [10.2 谁该先用，谁可以等等](#102-谁该先用谁可以等等)
  - [10.3 决策检查清单](#103-决策检查清单)
- [11. 进阶方向](#11-进阶方向)
- [12. 延伸阅读](#12-延伸阅读)

## 1. 项目概述

### 1.1 ACE-Step UI 是什么

**ACE-Step UI**（仓库 [fspecii/ace-step-ui](https://github.com/fspecii/ace-step-ui)，作者 Vali）是 [ACE-Step 1.5](https://github.com/ace-step/ACE-Step-1.5) AI 音乐生成模型的第三方 Web UI。它把 ACE-Step 模型包装成接近 Spotify 的交互界面，让本地生成音乐的操作从命令行参数和 Gradio 原生页面，收敛到填歌词或描述、调参数、点生成三步。

与需要联网和付费订阅的 Suno 不同，ACE-Step UI 跑在你自己的机器上：没有使用次数限制，没有收入分成，也不经过平台审核。生成全程在本地完成，只有两个可选功能（歌词灵感生成、MV 背景素材）会调用外部 API，见 3.4 节。

要注意的一点是：UI 本身不包含音乐生成模型，必须搭配独立的 ACE-Step 1.5 引擎使用。这决定了它的安装是"两段式"的，5.2 节会按这个顺序展开。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | 4,879 ⭐（2026-09-14） |
| Forks | 751 |
| 语言构成 | JavaScript 约 58%，TypeScript 约 28%，其余为 HTML/CSS/Python 等 |
| 前端框架 | React 19（`react@^19.2.4`）、TypeScript 5.8、Vite 6 |
| 服务端 | Express 4 + better-sqlite3 + @gradio/client |
| 最近一次推送 | 2026-06-27（截至数据采集日，已有近三个月未更新） |
| 开放 issue | 55 个 |
| 许可证 | UI 仓库 README 声明 MIT（截至采集日仓库内未附带 LICENSE 文件）；引擎为 MIT |
| GitHub | [fspecii/ace-step-ui](https://github.com/fspecii/ace-step-ui) |
| 后端引擎 | [ace-step/ACE-Step-1.5](https://github.com/ace-step/ACE-Step-1.5)（12,698 ⭐，MIT） |

数据来源：两个仓库的 GitHub API、`package.json` 与仓库 README，采集于 2026-09-15。Star 数、提交时间等指标会随仓库变化，请以实际页面为准。

### 1.3 为什么需要 ACE-Step UI

Suno、Udio 等 AI 音乐生成服务的订阅费在每月 10–50 美元，且生成请求都要经过它们的服务器。对照官方 README 给出的对比，本地方案的差异集中在六点：

| 维度 | Suno / Udio | ACE-Step UI |
|------|-------------|-------------|
| 成本 | $10–50/月订阅 | 免费（自己出电费和 GPU） |
| 数据隐私 | Prompt 和结果经第三方服务器 | 全程本地，数据不出机器 |
| 所有权 | 授权许可制 | 产出归自己 |
| 界面定制 | 封闭 | 前端代码开放，可自行修改 |
| 队列限制 | 按订阅档位限制 | 无限制 |
| 商用 | 商用需更高档订阅 | 无平台侧限制（版权归属仍按当地法律确认） |

其中数据隐私和队列限制是硬差异：如果客户合同禁止创意素材离开内网，或者需要一天批量生成几十版小样，云端订阅方案根本不适用，本地方案是唯一选项。这组差异也对应学习目标第 1 条，是第 10 节决策建议的判断基础。

### 1.4 系统总览

ACE-Step UI 是一个全栈项目，不是纯前端：浏览器里跑的是 React 前端，机器上还有一个 Node.js 服务端（Express + SQLite），由它承接浏览器请求、管理生成队列、把歌曲落库，并通过 Gradio 客户端与真正的模型服务——ACE-Step 1.5 引擎——通信。三者边界如下：

```text
┌──────────────────────────────┐       ┌──────────────────────────────────┐       ┌────────────────────────┐
│ 浏览器：React 前端 (:3000)    │       │ 服务端：Express + SQLite (:3001)  │       │ 引擎：ACE-Step 1.5      │
│                              │ /api  │                                  │Gradio│  (Gradio REST API :8001)│
│ CreatePanel ──► services/api │──────►│ POST /api/generate ──► 任务队列   │──────►│                        │
│                     ▲        │ proxy │        │                         │ client│ ──► 推理，产出音频      │
│ AuthContext / I18nContext    │       │        ▼                         │       │                        │
│ Player (Web Audio) ◄─ songs  │◄──────│ GET /api/generate/status/:jobId  │◄──────│ ◄── 任务状态           │
│                              │  轮询  │ SQLite: songs / playlists / users│       │                        │
└──────────────────────────────┘       └──────────────────────────────────┘       └────────────────────────┘
```

三层各自负责：

- **浏览器（React 前端）**：生成表单、参数控制、歌词编辑、播放器和库管理界面都在这里。它只通过相对路径 `/api/*` 与 Express 服务端对话，不直接接触模型。
- **服务端（Express + SQLite）**：前端与引擎之间的桥梁。接收生成请求并排队、通过 `@gradio/client` 把任务交给引擎、轮询状态、把产出的音频落到本地目录、把歌曲记录写入 SQLite（songs、playlists、users 等表），同时用 JWT 维护本地会话。
- **引擎（ACE-Step 1.5）**：真正跑推理的地方，以 Gradio 服务形式启动并开放 REST API。它独立于 UI，可以单独启动、单独用 Gradio 界面操作。

这条边界决定了排查方向：生成慢找引擎和 GPU，播放卡找浏览器音频层或网络，连不上先分清是 Express 服务端没起，还是引擎 Gradio 服务没起。第 4 节会用一次具体任务把这条链路走一遍。

[↑ 回到目录](#目录)

## 2. 界面与功能

### 2.1 Spotify 风格的视觉语言

ACE-Step UI 的视觉语言直接对标 Spotify——音乐流媒体领域用户接受度最高的 UI 范式，支持深色与浅色两种模式。

**布局**：左侧是导航栏（生成、曲库、播放列表），主区域展示生成面板或歌曲列表，底部固定一条 Spotify 式的迷你播放器，带波形图与可拖拽进度条。播放控制常驻屏幕底部，用户在浏览曲库或调整参数时不会中断试听。

**歌曲卡片**：每首生成结果以卡片展示，封面是程序化生成的渐变图（离线可用，也可以由视频生成流程搭配 Pexels 素材），配合标题、时长、风格标签。列表支持搜索、排序、点赞和自定义播放列表。

**多语言界面**：界面文案通过 `i18n/translations.ts` 管理，支持切换界面语言；歌词内容本身则由 ACE-Step 引擎支持 50 种以上语言。

### 2.2 生成模式与参数

生成面板分两种模式。**Simple 模式**只要求一句话描述，比如"An upbeat pop song about summer adventures with catchy hooks"，其余交给模型。**Custom 模式**开放完整参数：

| 参数 | 作用 | 备注 |
|------|------|------|
| Lyrics（歌词） | 按 `[Verse]`、`[Chorus]` 结构标签书写歌词 | 纯音乐模式可留空 |
| Style（风格） | 曲风、情绪、乐器、节奏标签 | 与歌词互补 |
| Duration（时长） | 30–240 秒 | 引擎本身支持 10 秒到 10 分钟，UI 收窄了范围 |
| BPM | 60–200 | 控制节拍速度 |
| Key（调性） | 如 C major、A minor | 配合拍号一起控制 |
| Seed（种子） | 固定后可复现同一结果 | 复现对比、迭代修改时有用 |
| Inference Steps | 推理步数 | 质量与速度的权衡 |
| Batch Size | 每个任务的变体数，1–4 | 默认 1；8GB 显存建议保持 1 |

引擎本身支持参考音频（Reference Audio）、音频翻唱（Audio Cover）和段落重绘（Repainting），UI 通过 `upload-audio` 接口接入了这些能力，上传上限 25MB，支持 MP3/WAV/FLAC。

两个值得单独说明的增强开关：

| 模式 | 行为 | 代价 |
|------|------|------|
| AI Enhance | 用语言模型把风格标签扩写成详细描述，并补齐 BPM、调性、拍号 | 多花 10–20 秒；LLM 跑在 CPU（PT 后端），不占额外显存 |
| Thinking Mode | 完整的 LLM 推理，先生成歌曲结构蓝图再合成音频 | 最慢，质量最好；显存低于 12GB 时自动禁用 |

官方给了一条实用提示：如果输入"pop, rock"这类简单标签，生成结果总偏向民谣（ballad），打开 AI Enhance 能明显改善曲风命中率。

### 2.3 库管理与内置工具

生成结果不是用完即弃，UI 内置了一套资产管理：

- **曲库（Library）**：所有生成记录入库，支持浏览、搜索、整理；可以点赞并组织成自定义播放列表。
- **音频编辑器（AudioMass）**：在浏览器里剪裁、淡入淡出、加效果，前端通过 ffmpeg.wasm 做音频处理。
- **分轨提取（Demucs）**：把成品拆成人声、鼓、贝斯、其他四轨。
- **MV 生成**：配合 Pexels 图库素材，为歌曲生成带背景视频的 MV。
- **局域网访问**：同一 Wi-Fi 下的手机、平板可以直接打开界面试听，见 5.3 节。

这套组合让 ACE-Step UI 超出了"生成按钮"的定位——生成、试听、剪辑、分轨、归档可以在一个界面里闭环。

[↑ 回到目录](#目录)

## 3. 架构设计

### 3.1 技术栈选型

技术栈围绕"单人可维护的本地全栈工具"选择，前后端各一套 `package.json`：

**前端**：React 19 + TypeScript 5.8 + Vite 6，样式用 Tailwind CSS（通过 CDN 引入，不走构建链），图标用 lucide-react，浏览器端音频处理用 ffmpeg.wasm。没有引入 Redux/Zustand 一类状态库，全局状态靠 React Context（见 3.2）。

**服务端**：Express 4 + better-sqlite3（SQLite 持久化）+ `@gradio/client`（与引擎通信）+ jsonwebtoken（本地会话）+ multer（参考音频上传）+ node-cron（定时任务）+ helmet（安全头）。

这套组合的特点是依赖少、启动快：SQLite 零部署，Tailwind 走 CDN 省掉样式构建，`@gradio/client` 复用引擎现成的通信协议，不需要自己设计推理任务 API。

### 3.2 仓库布局与前端结构

仓库按"前端 + 服务端"分两半，前端在根目录，服务端在 `server/`：

```text
index.tsx / App.tsx   # 前端入口
components/           # React 组件：CreatePanel（生成）、Player（播放器）、
                      # LibraryView（曲库）、TrainingPanel（训练）等
context/              # React Context：AuthContext（会话）、
                      # I18nContext（界面语言）、ResponsiveContext（响应式）
services/             # api.ts（REST 封装）、geminiService.ts（歌词灵感）
i18n/                 # 界面翻译文件

server/               # Node.js 服务端
├── src/routes/       # generate、songs、playlists、auth、lora、training 等路由
├── src/db/           # SQLite 建库与迁移
├── src/services/     # gradio-client、acestep（任务队列）等
├── src/middleware/   # JWT 认证中间件
├── public/audio/     # 生成音频的落盘目录
└── .env.example      # 配置模板（复制为 server/.env 使用）
```

全局状态有三类，分别对应三个 Context：会话状态（登录用户、token）在 `AuthContext`，界面语言在 `I18nContext`，断点适配在 `ResponsiveContext`。组件内局部状态用 `useState`。歌曲、播放列表这类需要跨会话保留的数据不在浏览器里存——它们由服务端写入 SQLite，前端每次通过 REST 接口拉取。

值得注意的一点：`components/` 里有一个 `TrainingPanel`，对应服务端的 `lora`、`training` 路由。也就是说 LoRA 微调不只是引擎侧的能力，UI 里也提供了入口。

### 3.3 与 ACE-Step 引擎的通信

ACE-Step UI 本身不包含音乐生成模型，推理全部委托给独立的 ACE-Step 1.5 Gradio 服务。浏览器不直接访问引擎——请求先到达 Express 服务端，由服务端通过 `@gradio/client` 与引擎交互。这样引擎地址、任务队列、音频落盘这些细节都收敛在服务端，前端只面对一组干净的 REST 接口。

主要端点（前缀 `/api`，均需 JWT 会话，除少数健康检查外）：

| 端点 | 方法 | 作用 |
|------|------|------|
| `/api/generate` | POST | 提交生成任务，返回任务 ID |
| `/api/generate/status/:jobId` | GET | 轮询任务状态与进度 |
| `/api/generate/history` | GET | 拉取生成历史 |
| `/api/generate/upload-audio` | POST | 上传参考音频（25MB 上限） |
| `/api/generate/format` | POST | 歌词/描述格式化 |
| `/api/generate/health`、`/limits`、`/models` | GET | 引擎健康、参数上限、可用模型 |
| `/api/songs`、`/api/playlists` | — | 曲库与播放列表管理 |
| `/api/auth/auto`、`/api/auth/setup` | — | 本地会话：自动登录/首次设置用户名 |

服务端与引擎之间不是简单的 HTTP 转发：`gradio-client` 维护与 Gradio 服务的会话，提交任务后按 Gradio 协议收取进度事件，`acestep` 服务在此之上维护任务队列和清理逻辑。前端拿到的是被整形过的 `{ status, progress }` 形态。

开发模式下，前端的 Vite dev server（3000 端口）把 `/api`、`/audio`、`/demucs-web` 等前缀代理到 `127.0.0.1:3001` 的 Express。`services/api.ts` 里的 `API_BASE` 因此是空字符串——所有请求都是相对路径，由代理转发。这个设计也让局域网访问不需要额外配置跨域，见 5.3 节。

### 3.4 可选的外部服务

核心生成链路完全本地，但有两个功能会调用外部 API，都属于可选增强：

- **歌词灵感生成**：`services/geminiService.ts` 调用 Gemini 2.5 Flash，按主题和风格生成标题、歌词、风格标签。需要在环境里配置 `GEMINI_API_KEY`；没有配置时返回一段 mock 数据（代码里明确标注），功能降级但不报错。
- **MV 背景素材**：视频生成器使用 Pexels 图库，需要在 `server/.env` 里配置 `PEXELS_API_KEY`。

架构上要清楚：这两个调用从浏览器发起（Gemini）或由服务端发起（Pexels），是"本地优先"架构中的显式例外。如果部署环境完全不允许外网访问，关掉这两个功能即可，不影响生成主链路。

[↑ 回到目录](#目录)

## 4. 任务如何流过系统

下面用一次具体的生成任务，把前端、服务端和浏览器音频层串起来，看一段 Prompt 最终变成曲库里可播放的条目经历了哪些步骤。

**场景**：用户想生成一段 120 秒的电子音乐，风格标签 `upbeat electronic, synthesizer, 120 BPM`，自写四句歌词，不固定种子。

**步骤 1：前端组装请求**

用户在 CreatePanel 填好歌词、风格、时长（120 秒），点击生成。组件把参数交给 `services/api.ts`，以 `POST /api/generate` 发出请求，请求头带上 `AuthContext` 里的 JWT token。服务端校验通过后返回一个任务 ID（如 `"job_8f3a2b"`），UI 上出现"排队中"的卡片，并显示队列位置。

**步骤 2：服务端入队并提交引擎**

Express 把任务放进生成队列，按顺序通过 `@gradio/client` 提交给 ACE-Step 1.5 引擎。引擎开始推理后，服务端持续收到 Gradio 协议的进度事件。

**步骤 3：前端轮询状态**

前端以固定间隔调用 `GET /api/generate/status/job_8f3a2b`，拿到 `{ status: 'processing', progress: 0.45 }` 这样的响应，更新卡片上的进度条。`status` 变为完成态时轮询停止。

**步骤 4：服务端落盘与入库**

推理完成后，服务端把音频文件从引擎下载到 `AUDIO_DIR`（默认 `server/public/audio/`），同时把歌曲记录写入 SQLite：标题（未填时从歌词首行或风格标签自动生成）、歌词、风格、BPM、调性、时长、`audio_url` 等字段。生成历史由此在服务端持久化，刷新页面、换浏览器都不丢。

**步骤 5：前端取结果并播放**

曲库刷新后出现这条记录。点击播放，Player 组件通过 `/audio/*` 相对路径取到音频流，用 `HTMLAudioElement` 加载，并把分析节点接到波形可视化上。底部迷你播放器开始显示进度。

**步骤 6：归档与后处理**

用户可以把歌曲加入播放列表、点赞；需要继续加工时，在 AudioMass 里剪裁，或用 Demucs 拆成分轨；点击下载则直接保存 `/audio` 路径下的音频文件。

第 9 节会按这条链路给出排查清单：生成慢查引擎和 GPU，播放卡查浏览器音频层，连不上先分清两跳服务各自是否存活。

[↑ 回到目录](#目录)

## 5. 安装与使用

### 5.1 环境要求

| 组件 | 要求 |
|------|------|
| Node.js | 18 或更高版本 |
| Python | 3.10+（官方推荐 3.11–3.12），标准安装方式需要；Windows 便携包已内置 |
| GPU | NVIDIA 4GB+ 显存可跑基础生成；AI Enhance/Thinking Mode 等语言模型功能建议 12GB+ |
| 其他后端 | 引擎同时支持 Mac（MPS）、AMD（ROCm）、Intel XPU 和纯 CPU，速度相应下降 |
| FFmpeg | 音频处理必需（缺失的典型症状是歌曲时长显示 0:00） |
| uv | Python 包管理器，标准安装方式推荐 |
| 浏览器 | Chrome、Firefox、Safari、Edge 最新版 |

ACE-Step 1.5 引擎对硬件的要求不高：官方口径是低于 4GB 显存即可运行，在 RTX 3090 上生成一首完整歌曲不到 10 秒。显存分层与模型选择的官方建议见引擎 README 的 GPU 兼容性文档。

### 5.2 安装步骤

整套系统是"引擎 + UI"两段依赖，两者都启动后 UI 才能用。官方提供三条路径：Pinokio 一键安装（适合不想碰终端的用户）、各平台一键脚本、手动分步。下面按最常用的顺序展开。

**路径一：Pinokio 一键安装**

[Pinokio](https://pinokio.computer) 会自动处理 Python、Node.js、依赖、模型下载和启动，全平台可用。安装后直接进入使用流程（5.4 节）。

**路径二：一键脚本（Linux/macOS 为例）**

1. 安装并启动引擎：

```bash
git clone https://github.com/ace-step/ACE-Step-1.5
cd ACE-Step-1.5
uv venv
uv pip install -e .        # 模型约 5GB，首次运行时自动下载
```

引擎和 UI 装在同一层目录时，一键脚本可以两个一起拉起：

```bash
git clone https://github.com/fspecii/ace-step-ui
cd ace-step-ui
./setup.sh                 # 安装前后端依赖
./start-all.sh             # 启动引擎 + 服务端 + 前端
```

`start-all.sh` 默认在 `../ACE-Step-1.5` 找引擎；装在别处时先指定路径再启动：

```bash
export ACESTEP_PATH=/path/to/ACE-Step-1.5
./start-all.sh             # 停止：./stop-all.sh
```

启动完成后访问 `http://localhost:3000`（前端端口；服务端默认 3001，由 `server/.env` 的 `PORT` 控制）。

Windows 对应 `setup.bat`、`start-all.bat`，路径变量为 `set ACESTEP_PATH=C:\path\to\ACE-Step-1.5`。Windows 用户也可以选择[便携包](https://files.acemusic.ai/acemusic/win/ACE-Step-1.5.7z)（约 5GB，内置 Python 与 CUDA 12.8，解压即用）。

**路径三：手动分步**

一键脚本做了三件事，手动等价操作如下。

启动引擎（注意 `--enable-api` 是必需的，没有它 Gradio 只开网页界面、不开 REST API，UI 会连不上）：

```bash
cd /path/to/ACE-Step-1.5
uv run acestep --port 8001 --enable-api --backend pt --server-name 127.0.0.1
# 等待终端出现 "API endpoints enabled" 再进行下一步
```

安装并配置 UI：

```bash
cd /path/to/ace-step-ui
npm install                # 前端依赖
cd server
npm install                # 服务端依赖
cp .env.example .env       # 配置文件在 server/ 下
```

`server/.env` 的关键配置：

```bash
PORT=3001                             # 服务端端口
ACESTEP_API_URL=http://localhost:8001 # 引擎地址，须与引擎 --port 一致
DATABASE_PATH=./data/acestep.db       # SQLite 数据库位置
AUDIO_DIR=./public/audio              # 生成音频落盘目录
JWT_SECRET=ace-step-ui-local-secret   # 本地会话签名
PEXELS_API_KEY=                       # 可选：MV 背景素材
```

另开一个终端启动 UI：

```bash
cd /path/to/ace-step-ui
./start.sh                 # Windows: start.bat
```

首次打开页面时，UI 会要求设置一个用户名——这是本地单用户会话（JWT）的初始化，之后自动登录，不需要密码。

**构建生产版本**

```bash
npm run build
npm run preview            # 本地预览生产构建
```

### 5.3 局域网访问

前端 dev server 监听 `0.0.0.0`，局域网内其他设备可以直接访问 `http://<你的内网 IP>:3000`，在手机或平板上试听生成结果。需要两件事配合：

1. 防火墙放行 3000（前端）和 3001（服务端）两个端口。
2. 服务端与引擎都保持运行——局域网设备发起的请求同样经过 `前端 → Express → 引擎` 两跳。

因为所有 API 请求都是相对路径加代理转发，不需要在局域网场景下额外配置跨域或改地址。

### 5.4 基本使用流程

1. **选择模式**：简单需求用 Simple 模式，一句话描述即可；要控制歌词和曲风细节，切到 Custom 模式。
2. **填写内容**：Custom 模式下按 `[Verse]`、`[Chorus]` 结构写歌词，填风格标签；没有头绪时用歌词灵感生成（需配置 Gemini API key，见 3.4 节）。
3. **调整参数**：设置时长（30–240 秒）、BPM、调性；想要复现或对比时固定 Seed；8GB 以下显存保持 Batch Size 为 1。
4. **生成与试听**：点击 Generate，底部播放器自动试听。曲风不准（比如标签写 rock 出来像民谣）时打开 AI Enhance 重新生成。
5. **归档与导出**：入库、点赞、建播放列表；需要进一步加工进 AudioMass 剪辑或 Demucs 分轨；下载按钮直接保存音频文件。

[↑ 回到目录](#目录)

## 6. 代码示例

> 阅读顺序：本节四段代码存在依赖，6.1 用到 6.3 的 `GenerateParams` 类型，建议先读 6.3 再回看 6.1。6.2 和 6.4 相对独立。各段均为示意代码，非仓库原貌，接口形态对齐 3.3 节列出的真实端点。

### 6.1 生成表单组件

以下为示意代码，非仓库原貌，仅用于说明组件结构：

> 提示：下面用到的 `GenerateParams` 类型定义见 [6.3 节](#63-服务层与轮询) 的 `submitGeneration` 入参。为节省篇幅，本节不再重复声明。

```tsx
// components/CreatePanel.tsx（示意）
import { useState } from 'react';

interface GenerateParams {
  lyrics?: string;
  style?: string;
  duration?: number;
}

interface CreatePanelProps {
  onSubmit: (prompt: string, params: GenerateParams) => void;
  disabled?: boolean;
}

export function CreatePanel({ onSubmit, disabled }: CreatePanelProps) {
  const [prompt, setPrompt] = useState('');
  const [lyrics, setLyrics] = useState('');
  const [duration, setDuration] = useState(120);

  const handleSubmit = () => {
    if (!prompt.trim()) return;
    onSubmit(prompt, { lyrics, duration });
  };

  return (
    <div className="space-y-4 p-4 bg-zinc-900 rounded-xl">
      <textarea
        className="w-full bg-zinc-800 text-white rounded-lg p-3
                   focus:ring-2 focus:ring-green-500 outline-none"
        placeholder="描述你想要生成的音乐..."
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        disabled={disabled}
        rows={3}
      />
      <div className="flex items-center gap-4">
        <label className="text-zinc-400">
          时长: {duration}s
          <input
            type="range"
            min={30}
            max={240}
            value={duration}
            onChange={(e) => setDuration(Number(e.target.value))}
            className="ml-2"
          />
        </label>
        <button
          onClick={handleSubmit}
          disabled={disabled || !prompt.trim()}
          className="ml-auto px-6 py-2 bg-green-500 hover:bg-green-600
                     disabled:bg-zinc-700 disabled:cursor-not-allowed
                     rounded-full font-semibold transition-colors"
        >
          {disabled ? '生成中...' : '生成'}
        </button>
      </div>
    </div>
  );
}
```

时长滑杆的上限是 240，与 UI 实际支持的 30–240 秒一致（引擎本身上限更高，见 2.2 节参数表）。

### 6.2 音频播放器封装

以下为示意代码，非仓库原貌，仅用于说明播放器封装思路：

> 注意：`HTMLAudioElement.load()` 返回 `undefined` 而不是 Promise，`await` 它拿不到"加载完成"这个时机——代码会立即往下走，音频实际还没就绪。要知道什么时候能播，得监听事件。下面的代码把反例和正确做法放在一起对照。

```typescript
// components/Player/useAudio.ts（示意）
export class AudioPlayer {
  private audioContext: AudioContext;
  private audioElement: HTMLAudioElement;

  constructor() {
    this.audioContext = new AudioContext();
    this.audioElement = new Audio();
  }

  // ❌ 反例：load() 不返回 Promise，await 之后音频往往还没就绪，
  // 紧接着 play() 可能无声或被浏览器丢弃
  async loadWrong(url: string): Promise<void> {
    this.audioElement.src = url;
    await this.audioElement.load();
    await this.audioElement.play();
  }

  // ✅ 正确做法：监听 canplaythrough 事件，由事件回调驱动 Promise
  async load(url: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const onReady = () => {
        this.audioElement.removeEventListener('canplaythrough', onReady);
        this.audioElement.removeEventListener('error', onError);
        resolve();
      };
      const onError = () => {
        this.audioElement.removeEventListener('canplaythrough', onReady);
        this.audioElement.removeEventListener('error', onError);
        reject(new Error(`Failed to load audio: ${url}`));
      };
      this.audioElement.addEventListener('canplaythrough', onReady);
      this.audioElement.addEventListener('error', onError);
      this.audioElement.src = url;
      this.audioElement.load();
    });
  }

  play(): void {
    this.audioElement.play();
  }

  pause(): void {
    this.audioElement.pause();
  }

  seek(time: number): void {
    this.audioElement.currentTime = time;
  }

  getProgress(): number {
    return this.audioElement.currentTime / this.audioElement.duration;
  }

  onTimeUpdate(callback: (time: number) => void): void {
    this.audioElement.ontimeupdate = () => {
      callback(this.audioElement.currentTime);
    };
  }
}
```

浏览器自动播放策略另有一道约束：未发生用户交互前 `play()` 会被拒绝。真实仓库的 Player 由用户点击歌曲触发播放，天然满足交互要求；如果你要做自动连播，记得在第一次交互后调用 `audioContext.resume()`。

### 6.3 服务层与轮询

以下为示意代码，非仓库原貌，接口形态对齐 3.3 节的真实端点。真实仓库里请求走相对路径加 Vite 代理（见 3.3 节），这里显式写出 `API_BASE` 以便理解：

```typescript
// services/api.ts（示意）
const API_BASE = ''; // 空字符串：所有请求为相对路径，由 Vite proxy 转发到 3001

export interface GenerateParams {
  lyrics?: string;
  style?: string;
  duration?: number;
}

export interface JobStatus {
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress?: number;
  error?: string;
}

export async function submitGeneration(
  prompt: string,
  params: GenerateParams,
  token: string
): Promise<string> {
  const response = await fetch(`${API_BASE}/api/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ prompt, ...params }),
  });

  if (!response.ok) {
    throw new Error(`Generation failed: ${response.statusText}`);
  }

  const data = await response.json();
  return data.jobId;
}

export async function pollJobStatus(
  jobId: string,
  token: string,
  options: { timeoutMs?: number; maxRetries?: number } = {}
): Promise<JobStatus> {
  const { timeoutMs = 5000, maxRetries = 3 } = options;
  let retries = 0;

  while (retries < maxRetries) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(`${API_BASE}/api/generate/status/${jobId}`, {
        headers: { Authorization: `Bearer ${token}` },
        signal: controller.signal,
      });
      clearTimeout(timer);
      if (!response.ok) {
        throw new Error(`Status fetch failed: ${response.statusText}`);
      }
      return await response.json();
    } catch (err) {
      clearTimeout(timer);
      retries += 1;
      if (retries >= maxRetries) {
        throw new Error(
          `pollJobStatus exceeded ${maxRetries} retries for ${jobId}: ${(err as Error).message}`
        );
      }
      // 退避时长与 timeoutMs 挂钩：弱网下把 timeoutMs 调到 10000 时，
      // 退避也放大到 2s、4s、8s、10s，避免重试间隔远小于单次超时
      const backoff = Math.min(2000 * 2 ** (retries - 1), timeoutMs);
      await new Promise((r) => setTimeout(r, backoff));
    }
  }
  throw new Error(`pollJobStatus unreachable for ${jobId}`);
}
```

两个设计点值得注意。其一，`AbortController` 加超时是弱网环境下的自我保护——生成要几十秒到几分钟，轮询请求本身不该挂死。其二，真实仓库用 JWT 会话（`AuthContext` 提供 token），示意代码保留了这一点；本地单用户场景下 token 由 `/api/auth/auto` 自动获取。

### 6.4 会话上下文

真实仓库没有引入状态管理库，会话状态由 React Context 承载。以下为示意代码，非仓库原貌，仅用于说明这一模式：

```tsx
// context/AuthContext.tsx（示意）
import { createContext, useContext, useEffect, useState } from 'react';

interface User {
  id: string;
  username: string;
}

interface AuthContextValue {
  user: User | null;
  token: string | null;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  token: null,
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [auth, setAuth] = useState<AuthContextValue>({ user: null, token: null });

  useEffect(() => {
    // 本地单用户：打开页面即尝试自动登录；
    // 若数据库中还没有用户，前端引导设置用户名（/api/auth/setup）
    fetch('/api/auth/auto')
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((data) => setAuth({ user: data.user, token: data.token }))
      .catch(() => setAuth({ user: null, token: null }));
  }, []);

  return <AuthContext.Provider value={auth}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
```

歌曲、播放列表这类持久数据不进 Context——它们在服务端 SQLite 里，组件通过 REST 接口按需拉取。Context 只放"会话级"状态：当前用户、token、界面语言。这个划分让刷新页面后的恢复逻辑很简单：重新 auto login，再拉一次数据。

[↑ 回到目录](#目录)

## 7. 练习与自测

### 7.1 练习

下面两个练习用来检验你对第 6 节代码的理解，建议动手改一改再对照行为：

1. **扩展 AudioPlayer 支持播放列表切换**：在 `AudioPlayer` 类里增加 `loadPlaylist(urls: string[])` 和 `playNext()` 方法，要求切换时无缝衔接（旧音频淡出 200ms，新音频从 0 开始播放）。提示：可以借助 `AudioContext` 的 `GainNode` 做淡入淡出，避免直接改 `audioElement.src` 造成的爆音。
2. **给 `submitGeneration` 加上请求去重**：当用户连续两次点击"生成"且 Prompt 与参数完全相同时，第二次调用应直接复用上一次的 Promise，不再发一次 POST。提示：在服务层维护一个 `Map<string, Promise<string>>`，key 用 `prompt + JSON.stringify(params)`。

做完练习 1，试着向自己解释为什么 `HTMLAudioElement` 切换 `src` 时会触发一次 `abort` 事件，以及怎么在 `AudioContext` 层面规避它。做完练习 2，再想想去重 key 的设计在并发场景下的边界——比如用户在第一次请求未返回时又改了 `duration`，应当算作新请求还是命中缓存。

### 7.2 自测题

下面 5 道题用来检验对全文核心概念的掌握。点击参考答案前的三角展开解析。

1. 说出 ACE-Step UI 与 Suno 在成本、数据隐私、所有权、界面定制、队列限制上的差异。

<details>
<summary>参考答案</summary>

| 维度 | Suno（商用） | ACE-Step UI（开源本地） |
|------|-------------|------------------------|
| 成本 | $10–50/月订阅 | 免费（自担硬件与电费） |
| 数据隐私 | Prompt 和生成结果经第三方服务器 | 全程本地，数据不出机器 |
| 所有权 | 授权许可制 | 产出归自己 |
| 界面定制 | 封闭 | 前端代码开放可改 |
| 队列限制 | 按订阅档位限制 | 无限制 |

（对应章节：1.3）

</details>

2. 把一次生成任务从点击"生成"到曲库可播放拆成 6 个步骤，并指出每步发生在哪一层。

<details>
<summary>参考答案</summary>

1. **前端组装请求**：CreatePanel 收集歌词、风格、时长，经 `services/api.ts` 发出 `POST /api/generate`（前端）
2. **服务端入队并提交引擎**：Express 队列按序通过 `@gradio/client` 提交给 Gradio 引擎（服务端 → 引擎）
3. **前端轮询状态**：定时调用 `GET /api/generate/status/:jobId` 更新进度（前端 ↔ 服务端）
4. **服务端落盘与入库**：音频下载到 `AUDIO_DIR`，歌曲记录写入 SQLite（服务端）
5. **前端取结果并播放**：Player 经 `/audio/*` 相对路径加载音频，波形与进度开始更新（前端）
6. **归档与后处理**：点赞、播放列表、AudioMass 剪辑、Demucs 分轨、下载（前端 + 服务端）

（对应章节：4）

</details>

3. 生成历史存在哪里？清空 `server/data/` 目录会发生什么？换一台浏览器登录，历史还在吗？

<details>
<summary>参考答案</summary>

- **存储位置**：服务端 SQLite 数据库，路径由 `server/.env` 的 `DATABASE_PATH` 控制（默认 `./data/acestep.db`）。浏览器不持久化生成历史，只保留会话 token 与少量界面设置。
- **清空 `server/data/`**：歌曲记录、播放列表、用户全部丢失，`AUDIO_DIR` 里的音频文件仍在但失去索引；需要重新走 `/api/auth/setup` 初始化用户。
- **换浏览器**：历史仍在——数据在服务端而不在浏览器，另一台设备只要能访问同一个服务端就能看到全部曲库。

（对应章节：3.3、4）

</details>

4. UI 与引擎之间的两跳地址分别由哪个配置决定？引擎启动时少了哪个标志会让 UI 一直连不上？

<details>
<summary>参考答案</summary>

- **第一跳（前端 → 服务端）**：开发模式下由 Vite 代理转发，代理目标在 `vite.config.ts` 中指向 `127.0.0.1:3001`；服务端端口由 `server/.env` 的 `PORT` 控制。
- **第二跳（服务端 → 引擎）**：`server/.env` 的 `ACESTEP_API_URL`，必须与引擎启动时的 `--port` 一致（默认 `http://localhost:8001`）。
- **关键标志**：`--enable-api`。不带它引擎只开 Gradio 网页界面、不开 REST API 端点，UI 的所有生成请求都会失败。这是官方 Troubleshooting 列表的第一条。

（对应章节：3.3、5.2、9.1）

</details>

5. 复述采用顺序的 5 个步骤，并解释为什么引擎要先于 UI 跑通。

<details>
<summary>参考答案</summary>

**5 个步骤**：
1. 先跑通 ACE-Step 引擎（用 Gradio 原生界面生成一段音频）
2. 再安装并启动 ACE-Step UI（`setup.sh` + `start-all.sh`，或手动分步）
3. 用简单 Prompt 验证链路（确认能播放、能下载、能进曲库）
4. 再调参数和批量生成（AI Enhance、固定种子、Batch Size）
5. 最后考虑二次开发（fork 仓库改组件，或脚本化 `/api/generate`）

**为什么引擎先跑通**：前端不跑模型，模型在独立的 ACE-Step 1.5 引擎里。如果引擎没起来，服务端转交失败，前端所有操作都会报错。先验证引擎能独立生成音频，才能隔离问题——是模型/显存问题，还是 UI/网络问题。

（对应章节：10.1）

</details>

[↑ 回到目录](#目录)

## 8. 适用场景与局限性

### 8.1 最佳使用场景

- **独立音乐人和创作者**：快速生成灵感小样，零成本探索不同曲风，分轨提取后可以直接进自己的编曲流程。
- **游戏和视频开发者**：预算有限但需要版权可控的背景配乐；AI 生成的版权归属仍需按当地法律确认，但至少没有平台订阅和分成的约束。
- **隐私敏感项目**：客户合同或合规要求禁止把创意素材上传第三方服务器，本地推理是硬约束。
- **企业内网环境**：私有化部署中提供音乐生成能力，外网不通或安全审计不允许调用 SaaS（软件即服务）——关闭 3.4 节的两个可选外部功能即可完全离线。
- **技术研究者**：研究 ACE-Step 模型的能力边界，或基于 `TrainingPanel` 做 LoRA 风格微调实验。

### 8.2 当前局限性

- **依赖独立引擎**：UI 本身不含模型，安装是"引擎 + UI"两段式，缺一不可。
- **界面开发放缓**：最近一次代码提交是 2026-06-27（截至数据采集日），开放 issue 55 个。项目尚在维护，但迭代速度不如引擎本身，遇到 bug 可能需要自己动手或等社区响应。
- **硬件分层明显**：4GB 显存能跑基础生成，但 AI Enhance、Thinking Mode 等语言模型功能需要 12GB+ 显存（低显存下 Thinking Mode 自动禁用）；XL 系列 4B 模型门槛更高。
- **不是 DAW**：有 AudioMass 剪辑和 Demucs 分轨，但没有多轨编排、混音、母带处理；需要完整制作流程时仍要导出到专业音频工作站。
- **部分功能依赖外部服务**：歌词灵感（Gemini）和 MV 素材（Pexels）需要各自的 API key，纯离线环境不可用（不影响生成主链路）。
- **文档较简**：README 覆盖安装和功能清单，但架构细节和参数语义要读源码；本文 3、4、6 节即为源码阅读后的整理。

[↑ 回到目录](#目录)

## 9. 常见问题与排查

下面把部署和使用中容易踩的坑集中列出，按"现象 → 排查 → 修复"的顺序写。官方 Troubleshooting 表覆盖了引擎侧的多数问题，遇到问题先在这里找一遍，再去看后端日志。

### 9.1 引擎或服务端连不上

**现象**：前端点击"生成"后立刻报错，控制台出现 `Failed to fetch` 或请求 4xx/5xx，卡片状态一直停在"排队中"。

**排查**：请求要过两跳——浏览器 → Express 服务端 → 引擎。先分清是哪一跳断了：

1. 确认引擎以正确参数启动：检查启动命令里有没有 `--enable-api`，这是官方排查表的第一条。直接 `curl http://localhost:8001/`（端口以实际启动为准）看 Gradio 是否有响应。
2. 确认 Express 服务端在跑：`curl http://localhost:3001/api/generate/health`，有响应说明服务端正常。
3. 核对 `server/.env` 的 `ACESTEP_API_URL` 与引擎实际 `--port` 一致。
4. 浏览器 DevTools → Network 面板，看请求实际打到的 URL，开发模式下应为相对路径（由 Vite 代理转发）。

**修复**：

- 引擎补上 `--enable-api` 重启，等待终端出现 "API endpoints enabled"。
- `.env` 改完必须重启对应服务端进程，环境变量不会热加载。
- 引擎装在非默认位置时，一键脚本需要先设置 `ACESTEP_PATH`（见 5.2 节）。

### 9.2 生成失败或显存不足

**现象**：轮询返回 `status: 'failed'`，或引擎日志出现 CUDA out of memory。

**排查**：

1. 看引擎日志，确认是否显存不足（OOM）或模型加载失败。
2. 检查 Batch Size——默认 1 是为了兼容低显存 GPU，手动调高后 8GB 显存很容易 OOM。
3. Thinking Mode 在低于 12GB 显存时会自动禁用；如果手动开启后失败，先关掉它。
4. 缩短时长重试，排除长音频导致的显存峰值。

**修复**：

- 官方建议组合：保持 PT 后端（默认）、Batch Size 降到 1、缩短时长、关闭 Thinking Mode。
- 引擎日志报 `AttributeError: 'NoneType'` 时，更新 ACE-Step-1.5 到最新版（官方注明修复已合入 PR #109）。
- 想尝试更高音质可了解引擎的 XL 系列（4B DiT），但需要 12GB+ 显存（带 offload）。

### 9.3 音频无法播放或时长显示 0:00

**现象**：生成状态显示"已完成"，但点击播放没声音；或曲库里歌曲时长显示 0:00。

**排查**：

1. DevTools → Network 面板看 `/audio/*` 请求是否 200。404 多半是 `AUDIO_DIR` 配置与实际落盘目录不一致。
2. 时长 0:00 是官方列出的典型症状：服务器缺 FFmpeg。Linux 上 `sudo apt install ffmpeg`，Windows 从 [ffmpeg.org](https://ffmpeg.org) 下载。
3. 直接在浏览器地址栏打开音频 URL，能播放说明是前端问题，不能播放说明是服务端文件服务问题。
4. 播放被浏览器自动播放策略拦截时（控制台有 `play() failed` 类报错），先点击页面任意位置再播放。

**修复**：

- 安装 FFmpeg 后重启服务端。
- `AUDIO_DIR` 与 `DATABASE_PATH` 是相对路径时，注意相对的是服务端启动时的工作目录，建议从 `server/` 目录启动。

### 9.4 历史记录丢失

**现象**：重启服务端后，曲库或播放列表变空；或部分设备看不到生成记录。

**排查**：

1. 确认 `DATABASE_PATH` 指向的文件存在且非零字节：`ls -la server/data/`。
2. 是否换过启动目录——`DATABASE_PATH=./data/acestep.db` 是相对路径，从不同目录启动会在不同位置建库，看起来就像"历史丢了"。
3. 检查 `ACESTEP_API_URL` 是否指向了另一台引擎/另一个数据目录（比如误连到官方 Demo）。

**修复**：

- 固定启动方式：始终从 `server/` 目录启动，或把 `DATABASE_PATH`、`AUDIO_DIR` 改为绝对路径。
- SQLite 是单文件数据库，备份曲库就是备份 `acestep.db` 加 `AUDIO_DIR` 里的音频文件。

### 9.5 系统级排查指引

遇到没列在上面的问题时，按这个顺序定位：

1. **先分清两跳**：`curl` 引擎地址和服务端健康接口，能通的是前端问题，不通的是后端或网络问题。
2. **看浏览器 Console 和 Network**：多数前端问题能在这里看到端倪，注意区分 JS 报错、网络错误和 CORS 错误。
3. **看引擎日志**：ACE-Step 的 stderr 会打印模型加载、推理耗时、异常堆栈，是定位生成失败的关键。
4. **隔离变量**：改一个参数重试一次，不要同时改歌词、时长、风格再看结果——出问题时无法归因。
5. **对照官方排查表**：引擎侧问题（OOM、语言模型加载、GPU 兼容）优先查 ACE-Step-1.5 仓库的 Troubleshooting 与 GPU 兼容性文档。

[↑ 回到目录](#目录)

## 10. 采用顺序与决策建议

### 10.1 推荐的采用顺序

上手建议按以下顺序推进，每一步验证通过再进入下一步：

1. **先跑通 ACE-Step 引擎**：前端不跑模型，模型在独立的引擎里。按 [ACE-Step-1.5](https://github.com/ace-step/ACE-Step-1.5) 仓库说明启动 Gradio 服务（记得 `--enable-api`），确认能从命令行或 Gradio 界面生成一段音频。
2. **再装 ACE-Step UI**：引擎就绪后克隆 UI 仓库，`setup.sh` 装依赖，`start-all.sh` 一键拉起或手动分步（见 5.2 节）。第一次启动只验证"UI 能连引擎、能发请求"。
3. **用简单 Prompt 验证链路**：首次生成用简短英文描述（如 `"lo-fi hip hop, 90 BPM"`），确认音频能播放、能下载、能进曲库。
4. **再调参数和批量生成**：链路稳定后尝试 AI Enhance、固定种子复现、Batch Size 变体对比。
5. **最后考虑二次开发**：需要定制界面或接入工作流时，再 fork 仓库改组件，或把 `/api/generate` 脚本化。

### 10.2 谁该先用，谁可以等等

- **先用**：有 4GB+ 显存 GPU、对数据隐私敏感、需要无限制生成的独立创作者和小团队。官方口径下 ACE-Step 1.5 在 RTX 3090 上生成一首歌不到 10 秒，硬件门槛对 2026 年的独立开发者相当友好。
- **没有 GPU 但想先试质量**：引擎官方提供免费托管站 [acemusic.ai](https://acemusic.ai)，无需本地硬件即可体验 ACE-Step 1.5 的生成质量；确认质量满足需求后再投入本地部署。
- **可以等等**：只偶尔生成几首、完全不想维护本地服务、且对界面体验要求接近商用产品的用户——Suno/Udio 的订阅仍是省心选项。注意 ACE-Step 1.5 官方声称质量可比肩多数商用模型，是否达标建议用 acemusic.ai 或本地实测后再下结论。
- **暂不建议**：需要多轨编排、混音、母带处理等完整制作能力的用户。ACE-Step UI 定位是生成加轻量加工（剪辑、分轨），不是 DAW（数字音频工作站）。

### 10.3 决策检查清单

在决定是否采用前，对照以下三个问题：

- 你的机器是否有可用 GPU（NVIDIA 4GB+，或 Mac/AMD/Intel XPU 对应后端）？没有的话，是否接受先用 acemusic.ai 云端验证、纯 CPU 慢速生成本地跑？
- 你能否接受 ACE-Step 1.5 当前的生成质量？官方口径乐观，但耳朵是最终裁判——先实测再决定。
- 你是否需要修改 UI 或集成到现有工作流？需要时这套开源代码是资产；如果只是想生成几首歌，引擎自带的 Gradio 界面或 acemusic.ai 也能满足。

三个问题中如果有两个以上回答"是"，ACE-Step UI 值得一试；否则先用官方托管或商用服务更划算。

[↑ 回到目录](#目录)

## 11. 进阶方向

跑通基本流程后，下面几条方向可以按兴趣挑选：

1. **读引擎源码**：克隆 [ace-step/ACE-Step-1.5](https://github.com/ace-step/ACE-Step-1.5)，重点看推理入口和 LM 规划器（LM 会先生成歌曲蓝图，再由 DiT 合成音频），理解 Prompt 如何变成音频。
2. **LoRA 风格微调**：引擎支持用少量曲目训练个人风格——官方给出的参考量级是 8 首歌、单张 3090 上约 1 小时（12GB 显存）。UI 的 `TrainingPanel` 和服务端 `lora`、`training` 路由提供了界面入口，也可以直接在引擎 Gradio 里做。
3. **尝试 XL 模型**：引擎的 XL 系列（4B DiT 解码器）音质更高，需要 12GB+ 显存（带 offload）。UI 对模型的选择经由 `/api/generate/models` 接口，硬件允许时值得对比。
4. **分轨后接制作流程**：用 Demucs 把生成结果拆成四轨，分别导入编曲软件二次加工——这是"AI 生成 + 人工精修"工作流的第一公里。
5. **脚本化批量生成**：把 `POST /api/generate` 封装成命令行脚本或 CI 步骤，实现批量生成、自动归档；JWT 会话用 `/api/auth/auto` 获取。
6. **给上游提 issue 或 PR**：遇到 bug 或缺失功能时，先在 [fspecii/ace-step-ui](https://github.com/fspecii/ace-step-ui) 搜索现有 issue，没有再提新 issue；引擎侧问题提到 [ace-step/ACE-Step-1.5](https://github.com/ace-step/ACE-Step-1.5)。

[↑ 回到目录](#目录)

## 12. 延伸阅读

想继续深入 ACE-Step UI 涉及的方向，下面这篇站内文章可以作为补充：

- [Music Assistant 深度拆解：2.4K Stars 的开源家庭媒体编排中枢](/posts/tech/music-assistant-server-media-orchestration-guide/)——同样是把多个流媒体服务拼成一张网，关注点在媒体编排而非生成，可以对照两种"音乐基础设施"的设计取舍。

---

*本文基于 ACE-Step UI 项目撰写，相关信息可能随版本更新而变化。文中提及的 GitHub Star 数据、版本号和社区活跃度请以项目仓库的实际页面为准。*

## 资料口径说明

本文基于 ACE-Step UI 仓库（github.com/fspecii/ace-step-ui）、ACE-Step 1.5 引擎仓库（github.com/ace-step/ACE-Step-1.5）的 README 与源码，以及两仓库的 GitHub API 数据撰写，数据采集于 2026-09-15。需要说明的边界：

1. **版本时效性**：UI 仓库最近一次代码推送为 2026-06-27，处于维护阶段。界面布局、组件结构、API 端点可能随后续版本变化，请以[官方仓库](https://github.com/fspecii/ace-step-ui)的最新代码为准。文中 Star 数（4,879）、Fork 数（751）、开放 issue 数（55）均为采集日数值。
2. **引擎依赖**：ACE-Step UI 本身不含音乐生成模型，必须依赖独立的 ACE-Step 1.5 引擎（Gradio REST API 形式运行）。生成质量、支持的参数、速度取决于引擎版本和硬件条件。引擎侧的性能口径（A100 上单曲 2 秒内、RTX 3090 上 10 秒内、4GB 显存可跑）引自引擎官方 README。
3. **许可证状态**：引擎仓库为 MIT 许可（GitHub 已识别 LICENSE 文件）；UI 仓库 README 及页面徽章声明 MIT，但截至采集日仓库根目录未附带独立的 LICENSE 文件，商用前建议向仓库所有者确认。
4. **外部服务依赖**：歌词灵感生成（Gemini 2.5 Flash）与 MV 背景素材（Pexels）需要各自的 API key，未配置时歌词灵感返回 mock 数据、MV 功能不可用。两者均不影响本地生成主链路。
5. **代码示例性质**：第 6 节代码均为示意代码，组件与接口形态对齐仓库源码（React Context、相对路径 + Vite 代理、`/api/generate` 系列端点），但并非仓库原貌。实际实现请以源码为准。
6. **浏览器兼容性**：Web Audio API 与 `HTMLAudioElement` 的行为在不同浏览器上存在差异，尤其是 `canplaythrough` 事件与自动播放策略。实际部署时请充分测试目标浏览器。
7. **版权与生成内容**：使用本工具生成的音乐版权归属取决于当地法律和 AI 生成内容的相关法规，本文不构成法律建议。用于商业项目前请确认相关版权要求。
