---
title: "StarNet：像素太空站里的真实 Agent——把运行时状态投影成游戏世界的本地优先桌面 Harness"
date: "2026-10-02T03:23:27+08:00"
lastmod: "2026-10-02T03:23:27+08:00"
draft: false
slug: "androoagi-starnet-pixel-art-agent-harness"
github_repo: "androoAGI/starnet"
source_key: "gh:androoAGI/starnet"
description: "StarNet 是一个本地优先的开源桌面 Agent harness：你把 AI Agent 编组成一支「船员」，安置在一座像素风太空站里——房间是权限域、走廊是授权交接通道、摆下的物件是真实的能力授予，画面不是装饰，而是实时运行状态的投影。BYOK、本地状态、真实模型调用与真实开销。"
categories: ["技术笔记"]
tags: ["AI Agent", "桌面应用", "Tauri", "本地优先"]
---

## 本文导读

读完本文你将能够：

- 说清 StarNet 与「AI 套壳聊天机器人」的本质区别：站台是运行时状态的投影，产品契约是字面意义的（房间=权限域，走廊=交接通道）
- 理解它的四层架构（前端 / Node sidecar / Tauri 壳 / 共享契约）以及为什么密钥永远不进前端
- 判断「游戏化 UI」在这里是噱头还是工程决策
- 用 OpenRouter key 或本地 Ollama 在自己机器上跑起来，并接上 Telegram/Discord 远程对话

## 一句话定位：harness，不是 chatbot

打开 StarNet 的截图，第一反应大概率是「这是个游戏」。像素艺术的太空站、房间、小人在工位间走动——但它不是模拟经营，也不是给聊天机器人换皮。README 里有一条硬性产品法则：

> **界面永远不得断言 harness 无法证明的状态。**

这句话值得展开：大多数 AI 应用的 UI 展示的是「乐观渲染」——模型还没答完，界面已经显示了思考中/完成等状态。StarNet 反过来：屏幕上每一个像素级的忙碌、空闲、协作状态，都必须来自本地运行时可验证的真实事件流。小人在工位上干活，是因为 sidecar 真的在流式调用模型；OUTBOX 里出现文件，是因为工具真的执行完写盘了。**不模拟收入、不模拟完成、不模拟模型活动、不模拟开销**——这是它和一切「AI 宠物/模拟器」项目的分水岭。

## 产品契约是字面的：你画的布局就是工作流

StarNet 最有意思的设计是把抽象的 Agent 编排概念全部映射成空间隐喻，而且是**强约束**而非纯装饰：

| 空间元素 | 真实含义 |
|----------|----------|
| 房间（room） | 一个能力受限的团队（capability-scoped team） |
| 走廊（hallway） | 一条被授权的交接通道（handoff lane） |
| 摆放的对象 | 一次真实的能力授予（capability grant） |

这意味着权限模型是「画」出来的：你把某个 agent 放进哪个房间、房间之间是否连通走廊，直接决定了它能调用什么工具、能把任务交接给谁。多 Agent 协作的权限边界第一次变得肉眼可见——不是 YAML 里的 policy 列表，而是一张你能指着讨论的地图。

每个 agent 是一次**真正独立、有边界的运行**：独立的工作区、独立的 transcript、独立的内存、独立的权限集。你可以同时跑多个，每个都是完整的 agent run，有真实成本。

## 核心能力清单：把「桌面 Agent 工作站」该有的都做齐

- **BYOK（bring your own key）**：粘贴 OpenRouter key，或用 Anthropic / OpenAI / Google 账号 OAuth 登录；密钥存操作系统 keychain，永不进前端。
- **消息它从任何地方**：把 agent 接到 Telegram、Discord、Slack、Signal 或 Matrix，离开桌面也能和你的站台对话。
- **Night Shift（夜班）**：让站台整夜运行，agent 在一条显式、可调的「缰绳」（leash）内持续干活，每个离席动作都有日志可审计。
- **Recipes / Skills / 定时任务**：可复用的多步骤配方、技能授予、cron 计划任务，产出可见。
- **Task Briefs（任务简报）**：遇到歧义时不瞎猜，而是把问题压缩成一个带选项的具体提问，通过任何已连接渠道问你。
- **OUTBOX（成品收件箱）**：交付物以真实文件的形式落在 OUTBOX 里，而不是埋在聊天记录里做考古。
- **MCP 连接器**：可挂 MCP server 和 paste-a-key / OAuth 连接器扩展能力面。
- **语音**：按住说话输入，统一的站台语音输出。
- **真实账本**：花费、预算、运行历史落盘并原样展示。

值得单独表扬的是 Task Briefs 和 Night Shift 这两个设计：前者把「AI 静默猜错」这个最恼人的失败模式变成了显式提问；后者承认了 agent 工作的现实形态——长任务、非同步、需要审计边界，而不是假装一切都在你的注视下发生。

## 架构：四层拆分与一条铁律

| 路径 | 职责 |
|------|------|
| `frontend/` | 原生 JavaScript 的站台世界与桌面 UI |
| `sidecar/` | 本地 Node agent 运行时：provider、工具、持久化、预算、授权 |
| `shared/` | 跨边界的加法式事件与 schema 契约 |
| `src-tauri/` | Rust/Tauri 桌面壳与捆绑运行时 |

三条架构铁律：

1. **前端只消费真实事件**：通过 localhost HTTP/NDJSON 和 SSE 消费 sidecar 的事件流——UI 状态是投影，不是源头。
2. **密钥归本地权威**：密钥由 sidecar / OS keychain 持有，**永不进前端**。前端被 XSS 也偷不走你的 API key。
3. **加法式契约**（`shared/` 目录的设计约束）：跨边界 schema 只加不改，避免前端与 sidecar 版本漂移时互相破坏。

sidecar 只用 Node 核心模块，零依赖即可运行——这也意味着你可以完全脱离桌面壳、用浏览器访问它，桌面应用只是原生分发形态。

## 上手：三种姿势

**姿势一：装桌面版。** Windows 10/11 与 macOS（Apple Silicon 用 `aarch64.dmg`，别在 M 系芯片上用 x64 包跑 Rosetta）都有签名+公证的安装包，发布流水线拒绝未通过 Authenticode / Developer ID / 公证校验的产物。

**姿势二：跑源码，零安装。** 只要 Node 18+：

```bash
git clone https://github.com/androoAGI/starnet.git
cd starnet
node sidecar/index.js
# 打开 http://localhost:8787，接一个 provider
```

**姿势三：完全免费跑本地模型。** 装 Ollama、`ollama pull llama3.1`，在首屏或 SETTINGS → PROVIDERS 选 OLLAMA。StarNet 只在能列出你本地模型后才报告就绪。README 的诚实提醒：本地模型更小，长任务上预期更慢更糙。

隐私边界很明确：模型请求会离开你的机器（除非你用本地 provider），但站台状态、transcript、内存、账本**全部留在本地 StarNet 工作区**，除非你显式使用网络工具或连接器。

## 冷静面：什么人该用，什么人该等等

该现在就用的人：

- 想在自己机器上长期养几个「数字员工」、对数据出境敏感的个人用户
- 研究 multi-agent 权限/交接机制的实践者——空间化的权限模型是很好的思维实验场
- 从 OpenClaw 或 Hermes 迁移的用户：StarNet 能直接读取磁盘上的 agent 主目录，从 persona、指令、内存和模型配置铸出一个 StarNet agent（API key 不迁移，需在 KEYS 页重输）

该再等等的人：

- Linux 用户：公开发布列车只覆盖 Windows/macOS，Linux 包只是内部构建产物
- 追求打磨体验的 macOS 用户：README 自己承认 Windows 是测试最充分的平台，macOS 真实覆盖较少
- 需要团队/云端多租户的场景：local-first 是产品定位，不是当前目标

另外注意许可的细节：MIT 覆盖**代码**，但 StarNet 的名字、logo、站台美术和品牌标识保留所有权利——可以fork可以商用，但必须换名字换美术，不能以 StarNet 名义分发。

## 写在最后

StarNet 的真正贡献未必是像素美术本身，而是它用一个极端具象的方式回答了一个抽象问题：**multi-agent 系统的状态和权限，如何让人真正「看见」并「审计」？** 房间是权限域、走廊是交接通道、物件是能力授予——这些映射把安全边界从配置文件搬进了空间直觉。加上「界面不得断言无法证明的状态」这条产品法则，它给所有做 agent 可视化/编排界面的团队提供了一个值得抄的基准：可视化不是美化，是状态投影的保真度问题。

项目信息：[androoAGI/starnet](https://github.com/androoAGI/starnet)（JavaScript/Rust · MIT），桌面版在 [starnet-releases](https://github.com/androoAGI/starnet-releases/releases/latest) 发布。
