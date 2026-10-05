---
title: "Open Claude Cowork：把 Claude Agent SDK 装进桌面的最小参考实现"
date: "2026-04-12T02:31:39+08:00"
lastmod: "2026-10-03"
slug: open-claude-cowork-composio-guide
github_repo: "composio-community/open-claude-cowork"
source_key: "gh:composio-community/open-claude-cowork"
description: "Composio 开源的桌面 AI 助手：约 5,400 行代码演示 Claude Agent SDK + Opencode 双引擎、SSE 流式与会话恢复，但 README 仍宣传已删除的第二产品，主分支已停更五个月。"
draft: false
categories: ["技术笔记"]
tags: ["Claude", "AI Agent", "桌面应用"]
---

# Open Claude Cowork：把 Claude Agent SDK 装进桌面的最小参考实现

Composio 团队开源的这个项目，真正值钱的不是"又一个桌面 ChatGPT"，而是一份可以直接抄的接线图：怎么用两百来行 Express 代码，把 Claude Agent SDK 的会话恢复、技能加载和 MCP 工具调用包装成一组 HTTP 端点，再配一个 Electron 壳。整个仓库约 5,400 行源码，两小时能读完。

但它也是一份需要带 Warning 使用的代码：官方 README 至今宣传"桌面应用 + Secure Clawdbot 消息机器人"两个产品，而 Clawdbot 的全部代码在 2026 年 3 月 5 日已被整体删除，README 却没有同步；主分支最后一次提交停在 2026 年 5 月 3 日，之后没有版本发布，仓库也从 ComposioHQ 组织迁到了 composio-community。照着 README 走，第二步就会撞上 `cd clawd: no such file or directory`。

这篇文章基于 2026-10-03 的仓库读数与 master 分支源码（commit 52335ef5），把真实留存的部分讲清楚，也把 README 与代码的落差交代明白。

## 先给地图：这个仓库里到底有什么

| 组件 | 位置 | 职责 |
|------|------|------|
| Electron 壳 | `main.js` + `preload.js` + `renderer/` | 窗口、安全隔离、把后端 SSE 桥接给页面 |
| Express 后端 | `server/server.js`（244 行） | 四个 HTTP 端点，SSE 流式输出 |
| Provider 抽象 | `server/providers/`（4 个文件，798 行） | claude / opencode 双引擎，可注册扩展 |
| Composio 接入 | 后端内联 | 登录后换取 MCP URL，注入 provider |
| 内置技能 | `.claude/skills/` | 两个示例：Anthropic 品牌规范、Remotion 视频最佳实践 |

README 里承诺的第五块——`clawd/`（Secure Clawdbot）——已经不在仓库里了，细节见下一节。

技术栈：Electron 39 做壳，Express 5 做后端，AI 层是 `@anthropic-ai/claude-agent-sdk`（^0.2.7）加 `@opencode-ai/sdk`，工具面走 Composio Tool Router（`@composio/core`），通过 MCP（Model Context Protocol，模型上下文协议）把 Gmail、Slack 这类 SaaS 工具挂给模型。语言构成上 JavaScript 约 98 KB 独占 64%，其余是 CSS 和 HTML，没有任何构建步骤——没有 TypeScript，没有打包器，源码即产物。

## Secure Clawdbot：一份 README 时间胶囊

这是读这个仓库前必须知道的事，因为它直接决定你该怎么对待 README。

时间线是这样的：2026 年 1 月 27 日，作者以 `feat: add clawdbot` 提交了消息平台机器人——一个支持 WhatsApp、Telegram、Signal、iMessage 四平台的个人助手，带持久记忆、浏览器自动化、cron 定时任务，删除时共 22 个文件、五千余行源码（光 `cli.js` 就 843 行）。1 月 29 日还在加功能。然后是 3 月 5 日的一个提交：提交信息写着 `docs: Update README`，实际改动是把 `clawd/` 目录整体删除，README 本身只动了一行。

此后 README 再没更新过。它的"What's Inside"对照表、Quick Start 第二段、Project Structure 目录树，至今都在介绍这个已经不存在的子项目。仓库的 demo GIF 的 alt 文本还写着 "Secure Clawdbot Demo"。org 下也找不到 clawd 的独立仓库——代码不是搬走了，是删了。

给读者的操作建议：把 README 当 2026 年 3 月的历史文档读，以仓库实际文件为准。本文剩下的部分全部基于后者。

## 四个端点与一次请求的完整旅程

后端的全部 API 面就四个端点：

| 端点 | 方法 | 作用 |
|------|------|------|
| `/api/chat` | POST | 发消息，SSE 流式返回 |
| `/api/abort` | POST | 按 chatId 中止正在跑的查询 |
| `/api/providers` | GET | 列出可用引擎（`claude`、`opencode`），默认 claude |
| `/api/health` | GET | 健康检查，顺带返回引擎列表 |

前端发一条消息后会发生什么？Renderer 页面不直接碰网络，而是调用 preload 脚本经 `contextBridge` 暴露的 `electronAPI.sendMessage()`——这是 Electron 的标准安全姿势：页面进程关掉 Node 集成（`nodeIntegration: false`、`contextIsolation: true`），唯一的出网口是 preload 里那几个函数，目标地址写死 `http://localhost:3001`。

请求体是四个字段，不是常见的 `messages` 数组：

```json
{
  "message": "帮我把 GitHub 通知整理成清单",
  "chatId": "c-1735812345678",
  "provider": "claude",
  "model": "claude-sonnet-4-5-20250514"
}
```

服务端拿 `chatId` 查会话，把 Composio 的 MCP 配置和模型参数一起交给选中的 provider，然后以 `text/event-stream`（SSE，Server-Sent Events）回传。SSE 事件有明确类型：`session_init`（会话建立）、`text`（正文块）、`tool_use`（模型要调工具了，带工具名和入参）、`tool_result`（工具执行结果）、`done` 或 `aborted`（收尾）。每 15 秒发一次心跳注释行防代理断连。前端据此把"正在调用 Gmail 工具"这类状态实时画进侧边栏——这就是 README 说的 Tool Visualization，实现比想象的朴素：就是把 SSE 事件原样渲染。

## Provider 抽象：可抄的部分

`server/providers/` 是这个仓库最值得读的目录，77 行的 `base-provider.js` 定义了全部契约：

```javascript
export class BaseProvider {
  constructor(config = {}) {
    this.config = config;
    this.sessions = new Map();
  }
  get name() { throw new Error('Provider must implement name getter'); }
  async *query(params) { throw new Error('Provider must implement query method'); }
  setSession(chatId, sessionId) { this.sessions.set(chatId, sessionId); }
  abort(chatId) { return false; }
}
```

核心是 `query()`——一个异步生成器，入参是一组结构化字段：`prompt`、`chatId`、`userId`、`mcpServers`、`allowedTools`、`maxTurns`。它接的不是裸的 messages 数组，因为它对接的本来就不是"补全 API"，而是 agent 运行时。注册新引擎只需 `registerProvider(name, ProviderClass)`，`/api/providers` 会自动把它列出来。

ClaudeProvider 的实现揭示了三个关键默认值。第一，工具白名单是十个：Read、Write、Edit、Bash、Glob、Grep、WebSearch、WebFetch、TodoWrite、Skill，server.js 把单次任务轮数上限放宽到 100（provider 默认 20）。第二，`permissionMode` 设为 `bypassPermissions`——所有工具调用不经确认直接执行，包括 Bash 和文件写入。这让产品体验顺滑，但也意味着你发给它的任何一句话都可能变成一条无提示执行的 shell 命令。自己改代码时，这里是最该先收紧的一行。第三，`settingSources: ['user', 'project']` 打开了文件系统技能加载——`.claude/skills/` 目录下的 SKILL.md 就是这样被 agent 识别的，仓库内置的两个技能（Anthropic 官方品牌规范、Remotion 视频最佳实践）就是这个机制的演示，想扩展能力就往目录里加自己的 SKILL.md，不用改任何代码。

OpencodeProvider 走另一条路：它通过 `@opencode-ai/sdk` 在本机拉起一个 opencode server（默认 `127.0.0.1:4096`），模型 ID 用 `providerID/modelID` 格式。前端内置的模型清单值得一看——opencode 侧默认是 `opencode/big-pickle`，另有 gpt-5-nano、glm-4.7-free、grok-code、minimax-m2.1-free 几个免费档，也挂了 Anthropic 三款；claude 侧三款就是 Opus 4.5、Sonnet 4.5（默认）、Haiku 4.5。一套界面切换两个引擎，免费模型跑日常任务、付费模型跑复杂任务，这是作者留的真实用法空间。

## 会话持久化：两层各管一半

"持久会话"在这个项目里是两层机制，README 只字未提，但这是理解它怎么工作的关键。

客户端这层：所有聊天记录、当前会话 ID、选中的 provider 和模型，全部存在 Electron 的 localStorage 里。关掉应用再打开，界面上的历史都在。但它只是"聊天记录"，不包含模型的上下文。

服务端这层才是真正的上下文延续：每个 chatId 第一次请求时，ClaudeProvider 从 Agent SDK 的 `system/init` 消息里抓出 `session_id` 存进 Map；同一 chatId 的后续请求带上 `resume: sessionId`，让 Agent SDK 在 Anthropic 侧恢复之前的完整对话状态。换句话说，"记住之前聊了什么"靠的是 Claude Agent SDK 的会话恢复机制，这个项目自己只维护了一张 chatId 到 sessionId 的映射表。这个设计意味着服务端重启后 Map 清空，老会话的上下文就续不上了——界面上历史还在，但模型失忆。排查"它怎么不记得我了"，先看后端是不是重启过。

## Composio 怎么把 500+ 应用接进来

500+ SaaS 集成不是这个项目自己写的，全部来自 Composio 平台：后端启动时 `composio.create('default-user')` 创建会话，Composio 返回一个专属的 MCP（Model Context Protocol，模型上下文协议）URL 和认证头；每次 `/api/chat` 都把这个 MCP 配置以 `mcpServers` 参数注入 provider——对 Claude Agent SDK 来说，Gmail、Slack、GitHub 这些工具就是一组远程 MCP 工具。所以用它的前提是注册 Composio 账号：`.env` 里两个变量，`ANTHROPIC_API_KEY` 和 `COMPOSIO_API_KEY`，就这两个。

这里埋着一个真实发生过的事故。后端会把拿到的 MCP URL 和认证头写进 `server/opencode.json`（给 Opencode 引擎用的配置文件），这个文件一度被 git 追踪——2026 年 5 月 3 日，仓库连续三个提交处理此事：先抹掉文件里的真实 Composio API key，再把该文件移出 git 追踪并写进 `.gitignore`（PR #16），提交信息直言 "scrub leaked Composio API key"。虽然泄露发生在文章发表之后，但它暴露的设计习惯值得留意：运行时生成含密钥的文件、依赖 `latest` 标签的依赖声明、以及一个会忘记同步的 README，三件事在这不足万行的仓库里各出现了一次。

## 快速开始：照这个顺序走

环境先说清楚：仓库没有声明 Node 版本，README 时代 Claude Agent SDK 和 Express 5 都只要求 Node 18+；但 `server/package.json` 对 `@composio/core` 用的是 `latest` 标签，该包现今的 0.22.0 要求 Node ≥ 22.22.3——今天从零安装，直接用 Node 22 LTS，别按老教程装 18。

```bash
git clone https://github.com/composio-community/open-claude-cowork.git
cd open-claude-cowork
./setup.sh
```

`setup.sh` 做的事比"装依赖"多：检测并安装 Composio CLI（`curl composio.dev/install`），拉起浏览器完成 Composio 登录，从模板生成 `.env`，交互式收你的 Anthropic key 写进去，再从 `composio whoami` 的输出里抓出 API key 自动填好，最后装根目录和 server 两处依赖。跑完它，`.env` 基本就配好了。

然后两个终端分别启动：

```bash
# 终端 1：后端
cd server && npm start

# 终端 2：桌面应用
npm start
```

后端起来后可以先 `curl http://localhost:3001/api/health` 确认引擎列表，再打开桌面窗口。想核对接口行为，别参考本文之外的旧资料——`/api/chat` 的请求体是 `message` 字段，网上不少转述写成 `messages` 数组，会直接收到 400。

## 现状盘点与采用建议

把风险摊开说：主分支最后提交 2026 年 5 月 3 日，此后五个月无动静；从没有过任何 release 或 tag，没有可锁定的版本，要用就锁 commit；README 与代码脱节未修；opencode 引擎的密钥说明指向的 opencode.dev 已不可达（opencode 本体现在在 sst/opencode 和 opencode.ai）；加上前面说的 `bypassPermissions` 默认值。这不是一个你可以"装完就用"的产品。

那它还剩什么价值？作为参考实现，价值反而更纯了：SSE 流式的端点设计、BaseProvider 的生成器契约、chatId 到 sessionId 的会话恢复、技能目录的加载开关、Composio MCP 的注入方式——每一块都是独立可抄的最小样例，总共五千来行，没有框架魔法。给 Claude Agent SDK 做桌面壳、或者给自己的 agent 加多引擎切换，先读这里再动手，能省掉不少试错。

具体顺序建议这样：想研究接线方式的，直接读 `server/` 目录加 `preload.js`，读完就可以关掉仓库；想跑起来玩的，锁 `52335ef5` 这个 commit，用 Node 22，把 `permissionMode` 改掉再接入真实账号；想要消息平台机器人（WhatsApp/Telegram 那套）的，这个仓库已经给不了了，README 里那段是存档；想要持续维护的生产工具的，等它恢复提交再说——或者干脆把它当骨架，自己 fork 了养。

一个 Composio 官方仓库，半份 README 在讲已删除的功能，主分支停在初夏——它更像一份写完就封存的教学样本。样本的价值在于里头的接线图还准，前提是你得知道哪些页已经撕掉了。

---

**相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub（现属 composio-community） | https://github.com/composio-community/open-claude-cowork |
| Composio Tool Router 文档 | https://docs.composio.dev/tool-router/overview |
| Claude Agent SDK 文档 | https://platform.claude.com/docs/en/agent-sdk/overview |
| Opencode（sst/opencode） | https://opencode.ai |

_本文事实核查基于 2026-10-03 的 GitHub API 读数（4,287 stars / 702 forks / MIT）与 master 分支源码（commit 52335ef5），历史读数经 Wayback Machine 快照（2026-03-12：3,135★；2026-04-01：3,258★；2026-05-01：4,040★）交叉核对。_
