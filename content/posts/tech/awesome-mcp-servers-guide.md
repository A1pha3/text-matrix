---
title: "awesome-mcp-servers：9.5 万 Stars 的 MCP 服务器地图"
date: 2026-09-02T03:25:46+08:00
slug: "awesome-mcp-servers-guide"
github_repo: "punkpeye/awesome-mcp-servers"
source_key: "gh:punkpeye/awesome-mcp-servers"
description: "awesome-mcp-servers 收录 4100+ 个 MCP 服务器、覆盖 61 个分类，是目前最大的 MCP 生态导航。本文拆解它的组织方式、图标图例与 glama 交叉验证信号，并给出一条从识别能力到跑起来的查找路径。"
draft: false
categories: ["技术笔记"]
tags: ["MCP", "AI Agent", "开源", "生态导航"]
---

# awesome-mcp-servers：9.5 万 Stars 的 MCP 服务器地图

> **事实边界**：本文基于 `punkpeye/awesome-mcp-servers` 仓库 README（2026-09-18 快照）与 glama.ai 公开索引整理。当日统计：README 条目 4113、分类 61、🎖️ 官方标记 363、stars 95162。这些数字随生态漂移，文中用于说明量级；需要精确值时，以仓库 README 与 GitHub 页面为准。

MCP（Model Context Protocol，模型上下文协议）生态增长最快的地方不在协议文档里，而在这一份清单里。要给 Claude Desktop、Cursor 这类客户端接一个现成的 MCP 服务器，`punkpeye/awesome-mcp-servers` 通常是第一站：4100 多个服务器、61 个分类，2026-09-18 的 stars 是 95162。它不只是一个链接汇总，更是生态现状的切片——谁在官方维护、什么语言占主流（带语言标记的条目中 TypeScript 约 2270 个、Python 约 1350 个）、哪些能力已经成熟到有十几个竞品。

这篇文章不复述清单内容——清单每天都在变。更有用的是讲清它的组织方式和筛选信号：你带着一个具体能力进来，带着三个候选出去。

## 〇、先讲清一个前提：MCP 服务器到底是什么

MCP 服务器的定位，是一个智能体与外部世界的适配器。协议本身只规定三件事：客户端如何发现工具（tools）、资源（resources）与提示（prompts），如何通过 JSON-RPC 调用它们，以及上下文如何在两端之间传递。

一个服务器干的事，就是把读文件、查数据库、调浏览器、打 API 这类具体能力，包装成协议里统一的工具声明，再通过固定的传输通道暴露给客户端——本地跑用 stdio，远程跑用 Streamable HTTP。这样 Claude Desktop、Cursor 这类客户端不必为每种能力写私有的集成代码，只要会讲 MCP，就能调用任何实现了协议的服务器。

这份清单收的就是这些服务器。收归收，怎么选才是难点。

## 一、这份清单解决什么问题

问题来自三个方向的膨胀：服务器数量增长快、质量参差、没有统一入口。它们散落在 GitHub、npm、PyPI，命名也未必能看出能力。`awesome-mcp-servers` 的价值就是把它们分类、标注特征，把查找成本压缩到一次浏览。

它服务两类读者：

- **应用开发者**：想给自家产品接一个读 PDF、查数据库的现成服务器，先在这里筛候选，省去从零造轮子。
- **AI 使用者**：想给 Claude Desktop 或 Cursor 配一个工具，又不知道有哪些选择，把这里当目录翻。

## 二、系统地图：清单怎么组织

这份清单是三层结构：

| 层级 | 内容 | 作用 |
|------|------|------|
| 顶层分类 | 61 个主题分类（数据库、浏览器自动化、代码执行、金融、医疗……） | 按领域缩小范围 |
| 条目标注 | 每行附编程语言、运行位置、支持系统图标 | 快速过滤技术栈与运行环境 |
| 双链接 | 多数条目（约三分之二）同时给出 GitHub 链接与 glama.ai 评分徽章 | 交叉验证活跃度与可用性 |

三层叠加的结果是：一个条目自带四重信息——它用什么写、在哪跑、是否官方、社区评分如何。绝大多数情况下，你不需要逐个点进 README 就能完成第一轮筛选。

### 语言、范围与系统图例

清单用一组 emoji 标注每个服务器。先看全这套图例，再刷列表才不会误解：

- **语言**：🐍 Python、📇 TypeScript/JavaScript、🏎️ Go、🦀 Rust、#️⃣ C#、☕ Java、🌊 C/C++、💎 Ruby
- **范围**：☁️ 云服务（调远程 API）、🏠 本地服务（操作本机软件）、📟 嵌入式系统
- **系统**：🍎 macOS、🪟 Windows、🐧 Linux

判定标准在 README 的 Legend 里写得很清楚：🏠 本地指服务器在操作本机已安装的软件（例如接管本机 Chrome），☁️ 云指它在调远程 API（例如天气接口）。这两个记号最容易混淆，先分清它们，后续筛选才不跑偏。

这套图例是第一道筛选器。比如你要一个本地跑、Python 写的 PDF 处理工具，到 File Systems 分类里按 🐍 + 🏠 两列图标就能扫出候选，不必理会标 ☁️ 的远程版本。

### 官方标记：最硬的筛选信号

🎖️ 表示官方实现——项目方自己维护的服务器。2026-09-18 统计，363 个条目带此标记，约占总量 8.8%。选官方实现通常意味着：接口随产品演进同步、文档由维护方保证、出问题能找到人。但官方不等于适配你的场景，它只是把无人维护这条风险降到最低；能力是否匹配，还得走完第三节的完整路径。

## 三、怎么找：一条可复用的路径

以「给 Claude 加一个本地文件系统访问能力」为例，完整走一遍：

1. 打开 README，定位到 File Systems 分类（目录锚点为 `file-systems`），先圈定候选池。
2. 在该分类下扫描，优先看带 🎖️ 的官方实现，再看社区高分的。
3. 对保留的候选，点 GitHub 链接看最近提交与 issue 处理节奏；条目带 glama.ai 徽章的，再点开评分页对照可用性报告，两个来源互相印证——没带徽章的，就多花两分钟翻仓库的 issue 区。
4. 确认运行方式：本地 stdio（`npx` / `uvx` 一条命令装好）还是远程 Streamable HTTP。这决定你把它接进哪个客户端、连哪台机器。
5. 按 README 的 quickstart 实际跑一遍最小调用，确认它真能返回你要的结果，再写进配置。

整条路径的原则：先用分类和图例粗筛，再用 GitHub 与 glama 精筛，最后用一次真实调用兜底。清单只保证你不错过候选，判断权在你。

## 四、接进客户端：配置层面怎么落

找到候选后，把它接进客户端通常是填一段连接配置。以 Claude Code 的 `.mcp.json` 为例，本地 stdio 服务器长这样：

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    }
  }
}
```

远程服务器改用 `type` 加 `url` 字段，指向服务暴露的 Streamable HTTP 端点：

```json
{
  "mcpServers": {
    "my-remote": {
      "type": "http",
      "url": "https://mcp.example.com/mcp"
    }
  }
}
```

Claude Desktop 的本地配置形状一致（`claude_desktop_config.json`，同样用 `mcpServers` 加 `command`/`args`）；远程服务器则一般走界面里的 Connectors，填 URL 即可，不用手写配置。

两点提醒：`npx` 首次会联网下载包，离线环境先用 `npm i -g` 预装，再让 `command` 指向本机可执行文件；远程端点要确认是否要求鉴权 header，未鉴权会直接失败。不同客户端的字段写法有微差，但本地传 `command`+`args`、远程传 `url` 这个骨架是一致的。

## 五、清单没告诉你的事（边界）

- **不评判质量**：条目被收录不等于可用。近年新增了大量基于 x402 微支付的付费 API 服务器（README 里 x402 相关条目已超过 160 个），稳定性差异很大，必须回到 GitHub 与 glama 交叉验证，别只看有链接就采信。
- **分类存在重叠**：数据可视化、数据科学与监控里会出现相近条目；搜索时多看相邻分类，别在一个锚点里停住。
- **清单滞后于生态**：社区维护，新增服务器未必即时收录；停更的旧条目也不会被主动移除。在列表里只是起点，不是质量背书。
- **图标是录入时的快照**：语言和系统图标反映条目录入时的状态，项目后来改语言、跨平台，图标不会实时更新。遇到明显矛盾的，以 README 正文为准。

## 六、该不该用它

- **该用**：你刚接触 MCP，想快速看生态全貌；或你需要某个具体能力、想确认有没有现成实现——它是成本最低的起点。
- **可以绕开**：你已经确定用 glama.ai 的 Web 目录——那边与仓库同步、可搜索，检索更顺手。
- **不必用**：你只需要一两个最知名的服务器（filesystem、github、fetch），直接去各自官方文档更省事，清单对你的价值有限。

一句话收束：`awesome-mcp-servers` 把四千多个选项摊开到一次浏览能扫完的程度，而做决定需要的证据，仍在每个条目背后的 GitHub 与 glama 页面里。

## 七、常见问题

**Q：同一能力有十几条，怎么快速缩到三五条候选？**

先按 🎖️ 把官方实现排到前面，再按语言、范围图例过滤，剩下的一般不超过三四条；最后看 glama 评分挑一条验证。

**Q：`npx` 报 command not found？**

本地 stdio 服务器依赖 Node 运行时，先确认 `node -v` 有输出；离线环境用 `npm i -g` 预装后，让 `command` 指向本机可执行文件路径。仍失败就换 `uvx`（Python 生态）或该服务器提供的 Docker 镜像。

**Q：远程服务器连不上？**

先 `curl` 端点确认可达，再看是否要求 `Authorization` header，最后确认客户端版本支持 Streamable HTTP（老版本可能只认 SSE）。

## 八、自测

1. 不看 README，解释 🏠（本地服务）和 ☁️（云服务）的判定标准。
2. 筛一个本地跑、Rust 写的数据库类服务器，你会依次看哪几列信息？
3. 官方标记解决了哪类风险、没解决哪类风险？
4. 为什么「在清单里出现」不能作为可用的证据？你用什么来补证？

## 九、引用与下一步阅读

- 仓库：<https://github.com/punkpeye/awesome-mcp-servers>
- glama.ai 索引：<https://glama.ai/mcp/servers>
- MCP 协议规范：<https://modelcontextprotocol.io>
- 配合 [chrome-devtools-mcp 调试浏览器]({{< relref "chrome-devtools-mcp-ai-agent-browser-debug-mcp.md" >}}) 阅读，能直观看到一个 MCP 服务器接管真实软件（Chrome）时，客户端与工具的分工长什么样。
