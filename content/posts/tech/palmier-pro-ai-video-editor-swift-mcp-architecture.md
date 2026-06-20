---
title: "Palmier Pro 深度拆解：基于 Swift 6.2 + MCP 的 AI 视频编辑器如何把 AI 反转成时间轴的协作者"
slug: palmier-pro-ai-video-editor-swift-mcp-architecture
date: 2026-06-20T14:58:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["视频编辑器", "MCP", "Swift", "AI视频", "开源项目"]
description: "Palmier Pro 是 YC S24 团队 Palmier 推出的 macOS 原生 AI 视频编辑器（Swift 6.2 + macOS 26 Tahoe），把 MCP server 内嵌进 app（127.0.0.1:19789），让 Claude Code/Codex/Cursor 直接读写时间轴。本文从架构反转、21 个模块切片、ToolExecutor 工具集、mcpb 一键安装四个层面拆解。"
---

## 核心判断

Palmier Pro 不是"加了一个 AI 插件的视频编辑器"，而是一次**架构反转**：把视频编辑器从"AI 产物的容器"提升为"AI 协作的 single source of truth"。它把 MCP server 内嵌进 Swift app，绑定 IPv4 loopback（`127.0.0.1:19789`），让 Claude Code、Codex、Cursor 通过同一套 15 个 `ToolExecutor` 直接读写时间轴——in-app chat 与外部 MCP 客户端共用 prompt 与工具，只是 UX 不同。

仓库：`palmier-io/palmier-pro`，Swift 6.2，macOS 26 (Tahoe) on Apple Silicon，GPL-3.0，当前 2,110 stars / 202 forks，v0.1.0（2026-04-07 首个 commit，2026-06-20 仍在持续 push）。

## 系统地图：21 个模块 + 一个 MCP 端口

仓库根目录非常干净：

```
Sources/PalmierPro/
├── Account/        # Clerk 身份验证 + 订阅状态
├── Agent/          # MCP server + ToolExecutor + in-app chat
│   ├── MCP/        # MCPHTTPServer.swift / MCPService.swift
│   ├── Tools/      # 15 个 ToolExecutor+xxx.swift 按职责切片
│   └── Panel/      # 时间轴侧边 chat UI
├── App/            # SwiftUI App 入口、Scene、菜单
├── Editor/         # 编辑器主控（非时间轴本身）
├── Export/         # 渲染管线
├── Generation/     # Seedance/Kling/Nano Banana Pro 集成（闭源）
├── Inspector/      # 选中片段的属性面板
├── MediaPanel/     # 媒体库、文件夹、搜索结果
├── Models/         # 领域模型（Project / Clip / Track / Effect）
├── Preview/        # 播放器 viewport
├── Project/        # 项目读写、版本管理
├── Search/         # 全局搜索（媒体 + 时间轴文本）
├── Settings/       # 偏好设置
├── Telemetry/      # Sentry 错误上报 + 自家指标
├── Timeline/       # 15 个文件构成时间轴渲染与交互核心
├── Toolbar/        # 顶部工具栏
├── Transcription/  # 音频转字幕
├── UI/             # 共享 UI 组件
├── Utilities/      # Foundation 扩展
└── Resources/      # Info.plist、字体、图片、Changelog、MCPB 包
```

`Package.swift` 显式锁住平台：`platforms: [.macOS(.v26)]`，`swift-tools-version: 6.2`。它依赖的关键外部包：

| 依赖 | 用途 |
|---|---|
| `MCP` from `modelcontextprotocol/swift-sdk` 0.11.0 | MCP 协议官方 Swift 实现 |
| `Sparkle` 2.7.0 | macOS 自动更新 |
| `Sentry` 8.40.0 | 错误监控 |
| `Clerk` + `ConvexMobile` | 身份验证 + 后端状态（订阅、用户） |
| `swift-transformers` 1.3.3 | HuggingFace Tokenizers（本地转字幕/搜索） |
| `Lottie` 4.6.1 | 矢量动画 |
| `DSWaveformImage` 14.2.2 | 音频波形 |

依赖列表本身就透露了它的定位：**不是"轻量剪辑工具"，而是把编辑器 + MCP server + 商业化身份验证 + 自动更新打包成一个完整 macOS app**。这与 CapCut 等 Web 优先的产品路径完全不同。

## 关键机制一：MCP server 内嵌 + IPv4 loopback 绑定

`Sources/PalmierPro/Agent/MCP/MCPHTTPServer.swift` 用 Swift 6.2 的 `actor` 模型实现：

```swift
actor MCPHTTPServer {
    private let port: UInt16
    private let makeServer: @Sendable () async -> Server
    private nonisolated(unsafe) var listener: NWListener?

    func start() throws {
        let params = NWParameters.tcp
        params.allowLocalEndpointReuse = true
        // Bind to IPv4 loopback only so the server is never reachable from the LAN.
        params.requiredLocalEndpoint = .hostPort(host: "127.0.0.1", port: endpointPort)
        listener = try NWListener(using: params)
        ...
    }
}
```

**安全设计要点**：`params.requiredLocalEndpoint = .hostPort(host: "127.0.0.1", ...)` 强制绑定 IPv4 loopback。`NWListener` 不会监听 LAN，避免本机 19789 端口被同网段其他人访问——这是把 MCP server 嵌进 GUI app 时容易忽视的安全决策。

每个 TCP 连接都被独立包装成 `Server + Transport` 对（`init` 接受 `@Sendable () async -> Server`），意味着 MCP server **支持多客户端并发**：Claude Code 与 Codex 同时挂在 19789 上不会互相阻塞。

## 关键机制二：15 个 ToolExecutor 按领域切片

`Sources/PalmierPro/Agent/Tools/` 下的工具实现用了一个非常清晰的"按职责切分"模式：

| 文件 | 工具域 | 示例能力（按 FAQ + manifest 推断） |
|---|---|---|
| `ToolExecutor+Timeline.swift` | 时间轴结构 | 增删轨道、移动片段、设置入出点 |
| `ToolExecutor+Clips.swift` | 片段操作 | 替换、分割、变速 |
| `ToolExecutor+Generate.swift` | 生成调用 | 触发 Seedance / Kling / Nano Banana Pro |
| `ToolExecutor+Import.swift` | 媒体导入 | 把外部文件加入项目 |
| `ToolExecutor+Search.swift` | 全局搜索 | 跨媒体库 + 时间轴文本搜索 |
| `ToolExecutor+Captions.swift` | 字幕 | 写入转录结果 |
| `ToolExecutor+Texts.swift` | 文字层 | 添加/修改文字图层 |
| `ToolExecutor+Folders.swift` | 媒体文件夹 | 组织项目结构 |
| `ToolExecutor+InspectTimeline.swift` | 时间轴只读查询 | 让 LLM 知道"现在时间轴长啥样" |
| `ToolExecutor+ShortId.swift` | 短 ID 解析 | 把 `clip_abc123` 转成完整对象引用 |
| `ToolDefinitions.swift` | 工具 schema | MCP `tools/list` 的 JSON Schema |
| `ToolExecutor.swift` | 调度器 | 根据 tool name 分发到对应子执行器 |
| `ToolResult.swift` | 结果封装 | MCP `tools/call` 响应格式 |
| `OverviewRenderer.swift` | 概览渲染 | 给 LLM 一段"时间轴现状"摘要 |
| `AgentInstructions.swift` | system prompt | LLM 行为约束 + 工具使用指南 |

**值得借鉴的两个工程决策**：

1. **`+InspectTimeline` 与 `+Timeline` 分离**——前者只读、后者可写。把"读"和"写"切成两个工具集，能让 LLM 在只读上下文里"看"时间轴时不至于误改；同时也方便未来给只读操作做更激进的 token 压缩。
2. **mcpb / Claude Desktop / Claude Code / Codex / Cursor 共用 prompt + 工具**——README 明说"the MCP server and the in-app chat share the same prompt and tools"。这意味着 `AgentInstructions.swift` 与 `ToolDefinitions.swift` 是单一事实源，编辑器内的 chat box 与外部 MCP 客户端行为完全一致——只是 UX 不同（in-app chat 支持 `@` 引用媒体、外部 MCP 客户端享受 Claude/Cursor 的成熟上下文管理）。

## 关键机制三：mcpb 一键安装

`mcpb/manifest.json` 是 Claude Desktop Extension 标准：

```json
{
  "manifest_version": "0.4",
  "name": "palmier-pro",
  "version": "0.1.0",
  "server": {
    "type": "node",
    "entry_point": "server/index.js",
    "mcp_config": {
      "command": "node",
      "args": ["${__dirname}/server/index.js"]
    }
  }
}
```

注意一个反直觉的设计：**mcpb 包内嵌了一个 Node.js shim（`server/index.js`）**，而不是直接让 Claude Desktop 连 19789。这是因为 mcpb 协议原本假设 MCP server 是独立进程；为了让 Claude Desktop 能启动 app 时按需唤醒本机服务，mcpb 的 shim 进程作为 proxy 启动并路由到 `127.0.0.1:19789`。

README 给出的接入方式覆盖了四种主流客户端：

```bash
# Claude Code
claude mcp add --transport http palmier-pro http://127.0.0.1:19789/mcp

# Codex
codex mcp add palmier-pro --url http://127.0.0.1:19789/mcp

# Cursor（手动添加 ~/.cursor/mcp.json）
# 或 app 内 Help -> MCP Instructions -> Install in Cursor 一键

# Claude Desktop
# Help -> MCP Instructions -> Install in Claude Desktop（mcpb 一键）
```

这种"四种客户端一份协议"的设计，让用户可以根据自己的偏好（Cursor 的 IDE 体验、Claude Code 的脚本化、Codex 的代码上下文、Claude Desktop 的日常对话）选择入口，**工具行为完全一致**。

## 任务流案例：用 Claude Code 一次完成"写脚本 + 生成 + 编辑"

按 FAQ 与工具集描述，一个典型 AI launch video 工作流是这样的：

```
1. 用户在 Claude Code 对话：
   "为新产品 X 写一个 30 秒 launch video 脚本，分 3 个镜头：
    镜头 1：产品特写；镜头 2：用户使用；镜头 3：品牌 logo。"

2. Claude Code 调 palmier-pro 的 inspect_timeline 工具：
   → MCPHTTPServer 返回当前项目结构（空项目 / 已有片段 / 轨道列表）

3. Claude Code 调 generate 工具，每个镜头：
   → palmier-pro 把任务派给 Generation/ 模块（闭源）
   → 闭源部分调用 Seedance / Kling / Nano Banana Pro
   → 生成的 mp4 写回项目媒体库

4. Claude Code 调 import + timeline 工具：
   → 把生成的 mp4 拖到时间轴
   → 设置每段时长（镜头 1：5s、镜头 2：20s、镜头 3：5s）

5. Claude Code 调 captions 工具：
   → 用 Transcription/ 模块给视频加字幕

6. 用户在 Palmier Pro GUI 里：
   → 看到时间轴已经有 3 段素材
   → 用 TimelineView 微调某一帧
   → 用 Export/ 导出成片
```

整个过程中**没有任何"web 端 → 下载 → 拖入"的人力循环**——这是 FAQ 第一段明说的"pain point"：把迭代次数×编辑次数这个乘积从 O(下载导入循环) 降到 O(MCP 调用)。

## 与传统 AI 视频工具的边界

FAQ 团队明说**目前没有**：

1. Effects
2. Transitions
3. Color grading
4. Masking
5. Graphics

这意味着 Palmier Pro 不是 Adobe Premiere Pro 的替代品。它的目标是**做 AI launch video 的内部团队**：把生成式 AI 的产物快速组装成可发布的视频，而不是做传统专业剪辑。

闭源/开源边界也很清晰（FAQ 原话）：

> The video editor (without the generative AI features) is fully open source. The MCP server and the agent chat are also open source. The only thing that is closed source is the generative AI processing.

也就是说，**编辑器 + MCP server + ToolExecutor + in-app chat 全部 GPL-3.0**，只有 Generation/ 里的 AI 模型调用是闭源。这让社区可以贡献剪辑功能，但不能直接复用其商业 AI 管线。

## 风险与未在仓库中明确说明的事项

- **价格未公开**：FAQ 说"Generative AI features require login and subscription"，但 `Subscription` 模块在仓库里没有详细价格表。
- **macOS 26 门槛**：`platforms: [.macOS(.v26)]` 意味着仅支持 2025 年后发布的 macOS Tahoe，老设备（Intel Mac、macOS 14 及以下）无法运行。
- **AI 模型可用性**：`Generation/` 目录为空（README 也说闭源），实际支持的模型清单需要从 app 内或官网确认；README 提到 Seedance、Kling、Nano Banana Pro，但模型版本与计费模型未在仓库内披露。
- **MCP 工具稳定性**：15 个 ToolExecutor 命名清晰但目前没有完整 API 文档，`ToolDefinitions.swift` 是 schema 唯一权威源——第三方写 agent 时需要直接读 swift 源码（这是开源 + 没有官方 SDK 的代价）。
- **多用户协作**：`Models/` 与 `Project/` 模块未提及实时协作，FAQ 只说"The video editor is the single source of truth"，没有说多人同时编辑。

## 采用顺序建议

如果你的团队是以下场景，可以优先评估：

1. **做 AI launch video 的初创团队**（YC 风格的产品发布视频）——核心目标匹配，能把迭代周期从"天"压缩到"小时"。
2. **个人创作者用 Claude Code / Codex 替代 CapCut Web**——MCP 客户端脚本化能力极强，但前提是你能接受 macOS 26 + Apple Silicon。
3. **希望自托管 AI 视频管线**——MCP server 是开源的，可以基于 `ToolExecutor+Generate.swift` 的接口做私有模型替换。

如果你是以下场景，建议暂缓：

1. **专业剪辑师需要 Effects / Transitions / Color grading**——目前完全没有，FAQ 也承认"without AI features, this is quite a bare-bone video editor"。
2. **跨平台需求（Windows / Linux）**——`platforms: [.macOS(.v26)]` 直接排除。
3. **需要企业级合规与审计**——Clerk + Convex 后端是默认依赖，自托管需要二次开发。

## 一句话总结

Palmier Pro 用 Swift 6.2 + MCP + 15 个按领域切片的 `ToolExecutor`，把视频编辑器从"AI 产物的容器"反转为"AI 协作的 single source of truth"。它的价值不在剪辑功能，而在**让 Claude / Codex / Cursor 直接读写时间轴**，从而打掉"web 生成 → 下载 → 导入 → 替换"这个让 AI 视频团队痛不欲生的循环。
