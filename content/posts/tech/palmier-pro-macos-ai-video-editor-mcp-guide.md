---
title: "Palmier Pro 解读：把视频时间线做成 AI Agent 可编程对象的 macOS 编辑器"
date: "2026-06-19T21:04:05+08:00"
lastmod: "2026-09-28T00:00:00+08:00"
slug: "palmier-pro-macos-ai-video-editor-mcp-guide"
github_repo: "palmier-io/palmier-pro"
source_key: "gh:palmier-io/palmier-pro"
description: "Palmier Pro 用本地 MCP 服务器把视频时间线暴露成 Claude、Codex、Cursor 可直接操作的对象，50 个工具覆盖导入、剪辑、生成、导出全流程。它曾以 GPLv3 开源，v0.7.6 之后转为专有——本文拆解它的 MCP 设计、订阅边界，以及这次开源退场值得注意的方式。"
draft: false
categories: ["技术笔记"]
tags: ["视频编辑", "macOS", "MCP", "AI Agent", "Swift"]
---

## 开场判断

Palmier Pro 真正做对的一件事，是把视频编辑器的内部状态——轨道、剪辑、标记、生成任务——包装成了 50 个语义清晰的 MCP（Model Context Protocol，模型上下文协议）工具，让 Claude Code、Codex、Cursor 这类编程 Agent 无需任何视频编辑器经验，就能像改代码一样改时间线。UI 只是这套工具面的一个消费者。

它的故事还有另一条线：这个项目 2026 年 4 月以 GPLv3 开源（[GitHub 仓库](https://github.com/palmier-io/palmier-pro)），靠 "built for AI" 的定位在半年内拿下 14,480 GitHub stars 和官网宣称的 100K+ 下载；2026 年 8 月 19 日的 v0.7.6 成了最后一个开源版本，此后转向专有发行，仓库也不再接受代码贡献。理解这条线，比理解任何一个功能都重要——它决定了你今天拿到手的是什么。

先给一张系统地图：

| 组成部分 | 职责 | 开源状态 |
| --- | --- | --- |
| Swift 编辑器本体 | 多轨时间线、预览、渲染、导出 | v0.7.6 及之前 GPLv3；之后专有 |
| 本地 MCP 服务器 | 在 `127.0.0.1:19789` 暴露 50 个时间线工具 | 同上（源码存于 `last-gpl-source` 分支） |
| 内置 Agent 面板 | 应用内对话式剪辑，v0.9.0 起可跑 Claude Code / Codex | v0.7.6 时点开源，之后随主程序转专有 |
| 云端生成服务 | Seedance、Kling、Nano Banana Pro 等约 20 个模型的视频/图像/音频生成 | 始终闭源，按订阅计费 |

需要 macOS 26 (Tahoe) 和 Apple Silicon（M 系列），Intel Mac 不支持——这是 Swift 原生路线的代价，后文细说。

## 开源边界：从 GPLv3 到专有的五个月

把时间线摆出来，很多说法就不用争了：

| 时间 | 事件 |
| --- | --- |
| 2026-04-07 | `palmier-io/palmier-pro` 仓库创建 |
| 2026-04-21 | v0.1.0 发布，要求自带 fal.ai 和 Anthropic 的 API key |
| 2026-06-19 | 本文初稿写作时点，项目处于 GPLv3 时代的 v0.6.x |
| 2026-08-19 | v0.7.6 发布，**最后一个 GPLv3 版本** |
| 2026-08-28 | v0.8.1 发布，此后版本转为专有，源码不再发布 |
| 2026-09-26 | v0.10.1 发布（当前最新） |

开源退场的方式值得注意。README 顶部现在有一段 IMPORTANT 声明，把边界划得很清楚：v0.7.6 及之前的版本、`last-gpl-source` 分支上的源码，继续按 GPLv3 提供，可以随便用、改、再分发；之后的二进制按单独的专有许可证走。自述也换了措辞——v0.7.6 时的 README 写着 "Palmier Pro is an open source video editor for Mac"，现在改成了 "a macOS video editor with built-in AI generation and MCP support"，"open source" 这个词被拿掉了。Contributing 一节则明确：仓库不再接受代码贡献。

所以今天讨论 "Palmier Pro 开源吗"，答案是分层而非二值的：历史版本开源且可自行构建，现行版本专有，商业化从"生成功能收费"扩大到了"整个编辑器收费、编辑功能免费"。如果你需要一个可以魔改的底座，那应该去 fork [`last-gpl-source`](https://github.com/palmier-io/palmier-pro/tree/last-gpl-source) 分支，而不是等官方回心转意。

## 核心机制一：MCP 服务器，50 个工具的时间线接口

应用运行时会在 `http://127.0.0.1:19789/mcp` 起一个 HTTP MCP 服务器。绑定地址写死为本机回环（源码 `MCPHTTPServer.swift` 里是 `requiredLocalEndpoint = .hostPort(host: "127.0.0.1", ...)`，另有 Origin 校验只放行 localhost），所以没有直接的远程攻击面；风险模型是"本机上能连到这个端口的进程都能操作你的工程"。

四个客户端的接入方式：

**Claude Code**

```bash
claude mcp add --transport http palmier-pro http://127.0.0.1:19789/mcp
```

**Codex**

```bash
codex mcp add palmier-pro --url http://127.0.0.1:19789/mcp
```

**Cursor**

应用内 `Help` → `MCP Instructions` → `Install in Cursor` 一键写入 `~/.cursor/mcp.json`，也可以手动加：

```json
{
  "mcpServers": {
    "palmier-pro": {
      "type": "http",
      "url": "http://127.0.0.1:19789/mcp"
    }
  }
}
```

**Claude Desktop**

应用捆绑了 `.mcpb`（MCP Bundle，一个用 Node 写成的 Desktop Extension，要求 node ≥ 18），`Help` → `MCP Instructions` → `Install in Claude Desktop` 一键加载。

工具面按 v0.7.6 源码（`ToolDefinitions.swift`）统计是 50 个：49 个通用工具加一个 `manage_project`。专有版本的工具有增量改动，以应用内 `Help` → `MCP Instructions` 的实时清单为准。v0.7.6 时的分组如下：

| 分组 | 代表工具 | 能做什么 |
| --- | --- | --- |
| 项目与时间线 | `get_timeline`、`create_timeline`、`set_active_timeline`、`manage_markers`、`export_project` | 读写工程状态；时间线可以复制成副本改（官方称之为版本管理原语），也能嵌套进另一条时间线当一个剪辑 |
| 媒体库 | `import_media`、`search_media`、`inspect_media`、`capture_frame` | 导入素材、按语义搜索、抓帧 |
| 剪辑操作 | `add_clips`、`split_clips`、`move_clips`、`ripple_delete_ranges`、`set_keyframes`、`sync_clips` | 增删改剪辑、关键帧、波纹删除、多轨对齐 |
| 文本与语音 | `add_texts`、`add_captions`、`get_transcript`、`remove_silence`、`detect_beats` | 字幕、转录、去静音、卡点 |
| 调色与效果 | `apply_color`、`apply_effect`、`denoise_audio` | 一级调色可复制到其他剪辑 |
| 生成 | `list_models`、`generate_video`、`generate_image`、`generate_audio`、`upscale_media` | 云端生成，受订阅门槛约束（见下节） |
| 多机位 | `manage_multicam`、`change_cam` | 多机位切换 |

两个设计细节能看出这套接口的成熟度，值得单独说。

**其一，Agent 能"看见"自己的修改。** `inspect_timeline` 返回指定帧的合成渲染图——所有轨道按变换、透明度、裁切叠好的最终画面，还叠了一层 0–1 坐标网格和帧号水印。工具描述里明说这是给 Agent 验证修改用的：画中画位置对不对、标题压没压住主体，看这张图就知道。没有这一环，Agent 改完只能"相信"自己改对了。

**其二，审阅是显式状态机。** `manage_markers` 创建的标记带 `open → review → resolved` 三个状态：Agent 完成修改后置为 review 等人确认，只有用户明确认可才能置为 resolved。v0.10.0 的 changelog 显示 UI 里这个概念已更名为 Comments（评论），但"人审后关闭"的工作流没变。这与 GitHub 上 code review 的 approve 流程同构——人机协作的分工被写进了数据模型。

## 核心机制二：内置 Agent 与订阅边界

除了外接 Agent，应用自己带一个 Agent 面板。v0.7.6 时它是消费同一套工具的内置助手；v0.9.0（2026-09-09）之后边界模糊了——changelog 原话：内置聊天现在支持 Claude Code、Codex 或 Palmier 自己的 harness，**可以自带 API key，也可以直接用你已有的 Claude / Codex 订阅**。也就是说，同一个工程文件，外接 Agent 和内置面板是两条平等的入口。

生成能力则始终走云端，按订阅计费。免费与付费的边界，官网定价页写得很直接：

| 档位 | 价格 | 内容 |
| --- | --- | --- |
| Free | $0 | 完整多轨编辑器、MCP 接入、**无需账号**、本地转录与素材搜索、渲染导出（含 NLE XML，非线性编辑 interchange 格式，可导入 Premiere / DaVinci） |
| Pro | $29/月（限时价，原价 $49） | 每月 5,000 生成积分、全部生成模型、更准的云端转录、内置聊天 |
| Max | $69/月（限时价，原价 $99） | 每月 12,000 积分、优先支持 |
| Enterprise | 议价 | 量购积分、集中计费、私有 Slack、安全评审支持 |

定价页还专门澄清了一句：付费不解锁另一个编辑器，编辑功能永远免费，付费换的是生成积分和云转录精度。换算参考：5,000 积分大约对应 333 张图或 2–7 分钟生成视频。

代码层面，这个门槛藏在 `get_timeline` 返回的 `canGenerate` 字段里：为 false 时生成类工具会直接失败，工具描述要求 Agent 提示用户"登录 Palmier 并订阅"。而 `generate_video` 的描述写得更直白——异步发起、立即返回占位资产 ID、生成完成前不能上轨，并且 "Costs real money and is not undoable"（真金白银，不可撤销）。生成模型的完整清单用 `list_models` 查，官网模型墙列了约 20 个：视频有 Seedance 2.5、Kling V3、LTX 2.3、Runway Aleph 2，图像有 Nano Banana Pro、FLUX 3、GPT Image 2，音频有 ElevenLabs、MiniMax H3，还有 Topaz 做放大。

## 一次真实协作：三分钟产品视频怎么剪

把上面的机制串起来。假设素材已经拍好，坐在 Cursor 里对 Agent 说"把这三段素材剪成一分钟的产品视频，加字幕"：

1. `import_media` 把桌面上的原始素材导入媒体库，`search_media` 按内容定位可用片段。
2. `get_timeline` 读取工程状态——帧率、分辨率、轨道结构和每个剪辑的帧区间。这是会话的第一步，官方文档明确要求先调它。
3. Agent 按 `remove_silence` 和 `detect_beats` 的结果定节奏，`add_clips` / `split_clips` / `move_clips` 把素材铺上时间线。
4. 需要补一个产品特写镜头时，`generate_video` 异步生成，先拿占位资产 ID 继续干活，就绪后自动替换。
5. `add_captions` 挂字幕，`apply_color` 把调色复制到同组剪辑。
6. `inspect_timeline` 渲染几个关键帧回看：字幕有没有出框、Logo 压在什么位置。
7. 人在编辑器里过一遍 Comments，改完的置 resolved，最后 `export_project` 出片，或导出 NLE XML 交给 Premiere / DaVinci 做精修。

前六步都可以不碰 UI。官网引用的用户证言里有 "I made a simple video and did not open the editor at all — everything via Claude Code"，与这套工具面的设计意图一致。人的价值被压缩到两处：审美判断（第 6 步的回看）和最终拍板（第 7 步的 resolved）。

## 姊妹仓库：palmier-skills

`palmier-io/palmier-skills`（[仓库](https://github.com/palmier-io/palmier-skills)，Apache-2.0，2026-09 仍在更新）收录了 13 个针对 Palmier Pro 的 Agent Skills：字幕模板、多机位剪辑、调色、UGC 风格、播客广告、动态图形等，每个是一个 SKILL.md，配 `catalog.json` 和 JSON Schema 做格式校验。它对应编辑器里的 `read_skill` / `manage_skills` 工具——让 Agent 先读技能说明再动手，相当于把"老剪辑师的套路"沉淀成可加载的提示词资产。做垂直场景（比如固定模板的口播视频）时，先翻这个仓库再写自己的 prompt，能省不少摸索。

## 适用边界与采用建议

**适合**：Apple Silicon 用户；短视频、演示、教程这类"模板化程度高、迭代频繁"的产线；已经付费 Claude / Codex 订阅、想让剪辑搭上现有 Agent 工作流的团队；想研究"GUI 应用如何向 Agent 开放内部状态"的工程——这套 MCP 工具的粒度和 `inspect_timeline` 的视觉闭环，是同类设计里少见的完整参考实现。

**不适合**：Windows / Linux 团队（平台锁死在 macOS 26 + Apple Silicon）；长片专业调色和精修（Premiere / DaVinci 仍是主战场，但 NLE XML 导出留了接力口）；期望一个"开源编辑器"来当长期底座的团队——v0.7.6 之后的路线已经不由社区决定。

落地顺序建议这样走：

1. **先零成本试 MCP**：下载 Free 版，接上你已有的 Claude Code 或 Cursor，跑通"导入—粗剪—导出"的最小闭环。这一步不花一分钱，也不用注册账号。
2. **再算生成账**：如果工作流依赖生成素材，按官网换算（5,000 积分 ≈ 333 张图或 2–7 分钟视频）估一下月用量，对照 Pro / Max 定价决定是否订阅。
3. **需要可改底座的另走一条路**：fork `last-gpl-source` 分支自行构建 v0.7.6，接受功能停留在 8 月中的事实。

## 参考来源与口径说明

- 本文初稿发布于 2026-06-19，2026-09-28 全面更新：补充开源转专有的时间线与现状、MCP 工具全量清单、订阅定价、内置 Agent 的 harness 支持与 palmier-skills 仓库。
- GitHub 仓库数据（14,480 stars / 1,128 forks）、版本发布时间、`last-gpl-source` 分支源码（`ToolDefinitions.swift`、`MCPHTTPServer.swift`）读数日期均为 2026-09-28；免费/付费边界与积分换算引自 [palmier.io/pricing](https://palmier.io/pricing) 同日快照。
- MCP 工具数量（50 个）与分组按 v0.7.6 源码统计；之后的专有版本工具集可能随功能增减（v0.9.0、v0.10.0 的 changelog 显示新增了变速、录音、评论等能力），使用时以应用内 `Help` → `MCP Instructions` 的实时清单为准。
- 生成模型清单引自官网模型墙与 README 举例（"SOTA models like Seedance, Kling, Nano Banana Pro"），实际可用列表随版本变动，`list_models` 工具返回的是当前账号的真实可用集。
