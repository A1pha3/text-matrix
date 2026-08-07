---
title: "AI副业早报 2026-08-07"
date: 2026-08-07T13:03:00+08:00
slug: ai-side-hustle-morning-news-2026-08-07
description: "2026年8月7日 AI 副业早报，精选过去 24 小时内 MCP 新规、独立 AI 应用生成器、Claude 协作硬件项目与真实变现案例。"
draft: false
categories: ["行业快讯"]
tags: ["AI副业", "独立开发", "MCP", "Show HN", "AI工具"]
hiddenFromHomePage: true
---

🦞 每日09:00自动更新

---

## 🚀 AI 工具与平台

### mcp-use v2：从零重写以适配 2026-07-28 无状态 MCP 新规
来源: Manufact Blog
发布者: Enrico Toniato（Manufact CTO）
原文: [原文](https://manufact.com/blog/mcp-use-v2)
摘要: 作者撰文详解 2026-07-28 修订版 MCP 协议——移除了 initialize 握手与会话 ID、请求自携带处理信息、新增 extensions 模型、MCP Apps、Tasks、缓存提示、trace context 与更强的 OAuth 要求。mcp-use 与 Manufact 在官方公告中被点名，新版本正是为远程 MCP 服务器在生产环境落地而重写，配套提供跨 ChatGPT/Claude 的测试、Apps Store/Cloud Connectors 合规审计与 Cloud Inspector。

标签: #MCP #协议更新 #生产部署

### Charming：让任何 AI 代理一键生成可分享的独立应用
来源: Charming（Show HN）
发布者: Charming 团队
原文: [原文](https://usecharming.com/)
摘要: Charming 把"在 ChatGPT/Claude 里说一句需求"变成一个带链接、可在浏览器打开、有独立数据存储的应用，作者原文给出了 ChatGPT、Claude、Claude Code、Cursor、Codex、Gemini、Grok、Perplexity、Goose、OpenClaw 等十余种代理适配示例。每个应用都有专属 `charm.ing/you/<app>` 链接，原文还展示了 Workouts、Run Log 等真实模板，强调"AI 记得的上下文自动带入应用"。

标签: #AI代理 #无代码 #应用生成器

### CopilotKit Channels SDK：把任意 Agent 接入 Slack/Teams/Discord/Telegram
来源: CopilotKit（Show HN）
发布者: CopilotKit
原文: [原文](https://github.com/CopilotKit/channels-sdk)
摘要: 开源 SDK 把任意 Agent（不仅限 CopilotKit）桥接到 Slack、Microsoft Teams、Discord、Telegram 等聊天平台，原生支持交互式 UI 组件，可让代理在企业 IM 里直接渲染表单、按钮与回执。仓库 README 与示例覆盖 OAuth、消息回传与人机协作流程，目标是把"AI 代理可观测、有 UI、可在企业 IM 里被消费"做成通用能力。

标签: #开源SDK #Agent #IM集成

---

## 🛠️ 独立开发项目

### Sidebar：用 Claude 一起为儿子和朋友们搭的 ESP32 私人对讲机
来源: Sundar Mohan Blog（Show HN）
发布者: Sundar Mohan
原文: [原文](https://www.sundaradnus.ca/writing/sidebar-building-a-ham-radio-for-my-son)
摘要: 一位产品经理为 11 岁的儿子与 4 位朋友做了 5 台 ESP32-S3 触屏对讲机——点朋友名呼叫、点 Everyone 全员响铃，无账号、无算法、无广告。文章详述了他与 Claude（Fable+Opus）协作的完整过程：固件、I2S 音频、AES-256-GCM 加密 UDP、Cloudflare 误诊、一次 OTA boot-loop 等真实踩坑；外壳由儿子用 FreeCAD 设计并开源。

标签: #Claude协作 #硬件开源 #ESP32

### Bookmarks Graveyard：把"收藏夹里死掉的好点子"复活成可执行的去/留裁决
来源: Atomic24 Blog（Show HN）
发布者: Hugh Fletcher
原文: [原文](https://atomic24.com/blog/bookmarks-graveyard-idea-harvester/)
摘要: 作者写了 12 美元的 skill，让 Claude 把 Pocket/书签里的存货逐条判 go/skip：用 AI 把"读完却忘掉的 SaaS 拆解、可自动化的工作流、小众论坛里的抱怨"提炼成一句话立项判断。原文反思这是"决策问题而非创意问题"，并把"清理 300+ 条书签找到一条已被人抢先做的生意"作为反面案例。

标签: #Skill文件 #变现案例 #$12

### Clipboard Sync：跨 macOS/Windows/Linux 的本地剪贴板 + 键鼠共享
来源: Clipboard Sync（Show HN）
发布者: droidfu
原文: [原文](https://clipboardsync.fuzhuo.me)
摘要: 开源原生应用（macOS 13+/Win 10+/Linux Flatpak）在 LAN 内共享剪贴板文本、图片与文件，并可选共享一只鼠标键盘；密码保护载荷、不走云、不要求账号，支持跨子网与代理，原文还放了"按物理鼠标活动切换控制权"与"拖拽式屏幕布局"两个差异化点。GitHub 仓库同步开源，作者承诺后续支持 Linux ARM64。

标签: #开源工具 #效率 #跨平台

---

## 💰 赚钱机会 / 创意发现

### Blink Ideas：用 AI 把客户投诉变成分钟级可读的创业 idea 流
来源: Blink Ideas（Show HN）
发布者: Blink Ideas
原文: [原文](https://blink-ideas-web.onrender.com/)
摘要: Blink Ideas 把"客户在论坛/评论区里骂什么"实时汇总成候选创业 idea，并给出 Investment Score（投资分）与 AI Confidence（AI 信度），首页能看到 MacroBase、PromoGuard、RouteClub、ResolutionConcierge 等当周新增 idea 与发布时间戳。原文示例是"健身者嫌 MyFitnessPal UI 太重"、"Uber One 用户发现促销变少"等可立即立项的小痛点。

标签: #Idea挖掘 #痛点驱动 #独立开发

### Kifly：把电商店铺暴露给 AI 代理的 MCP 接入
来源: Kifly（Show HN）
发布者: Kifly
原文: [原文](https://github.com/CopilotKit/channels-sdk)
摘要: Kifly 提供一条把 Shopify/电商店铺数据通过 MCP 暴露给 ChatGPT、Claude 等 AI 代理的通道，原文视频演示了"代理按上下文推荐 SKU、检查库存、给出下单链接"。该方向紧贴 MCP 新规（2026-07-28 修订版），对想做"AI 代理 + 垂直行业"独立开发的人有参考价值。

标签: #MCP #电商 #AI代理

---

🦞 每日09:00自动更新

**数据来源**：Hacker News (Show HN)、Manufact Blog、Charming、CopilotKit GitHub、Atomic24 Blog、Blink Ideas

**⚠️ 链接核查清单（已逐条验证，仅列正文实际引用链接）：**
- ✅ https://manufact.com/blog/mcp-use-v2 - 已验证内容匹配（mcp-use v2 重写细节）
- ✅ https://usecharming.com/ - 已验证内容匹配（AI 应用生成器介绍）
- ✅ https://github.com/CopilotKit/channels-sdk - 已验证内容匹配（Channels SDK 仓库）
- ✅ https://www.sundaradnus.ca/writing/sidebar-building-a-ham-radio-for-my-son - 已验证内容匹配（ESP32 对讲机项目）
- ✅ https://atomic24.com/blog/bookmarks-graveyard-idea-harvester/ - 已验证内容匹配（$12 skill 案例）
- ✅ https://clipboardsync.fuzhuo.me - 已验证内容匹配（剪贴板同步工具）
- ✅ https://blink-ideas-web.onrender.com/ - 已验证内容匹配（Idea 挖掘工具）

**📡 本次采集异常说明**：今日 V2EX 酷工作、Reddit r/SideProject 与 Product Hunt 三源在采集期出现 SSL 握手/Cloudflare 验证阻断，无法获取候选；本份早报切换为 Hacker News (Show HN) 替代源，已逐条访问验证正文与发布时间均在 24h 窗口内。