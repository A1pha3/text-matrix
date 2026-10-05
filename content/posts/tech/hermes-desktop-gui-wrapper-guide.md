---
title: "Hermes One（原 Hermes Desktop）：给 25 万星 Hermes Agent 套上桌面外壳的社区项目，19 个工具集 + 20 个消息网关"
date: "2026-06-09T17:59:00+08:00"
lastmod: "2026-10-03T00:00:00+08:00"
slug: "hermes-desktop-gui-wrapper"
github_repo: "fathah/hermes-desktop"
source_key: "gh:fathah/hermes-desktop"
aliases:
  - "/posts/tech/hermes-desktop-gui-wrapper/"
description: "Hermes One（原名 Hermes Desktop）是社区维护的 Hermes Agent 桌面外壳，非官方出品：把安装引导、Provider 配置、Profile 切换、19 个工具集启停、20 个消息网关、定时任务、记忆系统、SOUL.md 编辑全部做成图形界面。本文核查锚点为 2026-10-03 的 v0.7.7。"
draft: false
categories: ["技术笔记"]
tags: ["Hermes Agent", "Hermes One", "Electron", "Nous Research", "GUI"]
---

# Hermes One（原 Hermes Desktop）：给 25 万星 Hermes Agent 套上桌面外壳的社区项目，19 个工具集 + 20 个消息网关

> **时点说明**：本文 2026-06-09 发表于 v0.5.8 时代，当时项目还叫 Hermes Desktop；2026-06-23 的 v0.7.0 起改名 **Hermes One**，下载站从 hermesagents.cc 迁到 [hermesone.org](https://hermesone.org)（旧域名已 404）。全文事实已于 2026-10-03 按 v0.7.7 源码重新核对，写作时点与核查时点的数字差异均按双时点标注。

## 一、开场判断

先把最容易误判的事说清楚：**这不是 Nous Research 的官方项目**。仓库 README 原话是 "This repo is not affiliated to **Nous Research**. This is a community maintained project."——fathah/hermes-desktop 是社区给 [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)（2026-10-03 读数 250,866★，Python，MIT，自述 "The agent that grows with you"）做的一个桌面外壳。它用官方安装脚本装 Hermes，装完之后的一切配置、聊天、网关管理都在这个 Electron 应用里完成，但项目本身与 Nous Research 无隶属关系。

它真正解决的问题是：Hermes Agent 的能力面很宽——多 Profile、多 Provider、定时任务、消息网关、记忆系统——但这些在 CLI 形态下意味着手改 YAML、手写 cron 表达式、手配 webhook。这个项目把这些配置面全部变成按钮和表单，Agent 本体跑在本地 `~/.hermes`，外壳通过 `127.0.0.1:8642` 的 SSE 流式接口跟它说话。

还有一个值得一说的背景：这个项目演进极快。2026-04-02 建仓，四个月发了 48 个 release（37 个稳定版），文章发表次日就发了 3D 办公室（v0.6.0），一个半月后改名并加入钱包、密钥管理、应用内浏览（v0.7.0）。看这篇文章时请以 v0.7.x 的口径为准，文中旧数字都标了时点。

## 二、项目概览

| 维度 | 数据 |
|---|---|
| **仓库** | [fathah/hermes-desktop](https://github.com/fathah/hermes-desktop)（现名 Hermes One） |
| **Stars / Forks** | 14,349 ★ / 1,623 forks（2026-10-03；发表时 11,389 ★） |
| **License** | MIT |
| **定位** | 社区维护的 Hermes Agent 桌面外壳（非官方） |
| **底层 Agent** | [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) |
| **当前版本** | v0.7.7（2026-09-04；发表时 v0.5.8） |
| **桌面壳** | Electron 44（发表时 39；README 已删 Tech Stack 节，以 package.json 为准） |
| **下载** | [hermesone.org](https://hermesone.org)（原 hermesagents.cc 已下线） |
| **应用内语言** | 12 个 locale，含简体/繁体中文、日语、阿拉伯语（RTL）、希伯来语（RTL） |
| **状态** | README 自述 "active development"，明确警告 "some things might break" |

## 三、三种连接形态：本地、Remote、SSH Tunnel

这是读懂这个应用的第一道分界线，README 只讲了前两种，实际源码和文档里有三种：

| 形态 | 怎么连 | 能用什么 |
|---|---|---|
| **本地（默认）** | 应用在 `~/.hermes` 拉起 Hermes 后端，走 `http://127.0.0.1:8642` + SSE | 全部功能 |
| **Remote（HTTP）** | 填远端 API URL + Key，跳过本地安装 | 只有聊天。管理屏（Sessions、Skills、Memory、Soul 等）仍读本机 `~/.hermes`，看不到远端数据 |
| **SSH Tunnel** | 连到跑着 Hermes 的远程服务器（VPS / 家庭服务器） | 官方文档原话：所有屏幕 "works as if Hermes were installed locally" |

Remote 和 SSH Tunnel 的功能差距写在仓库 `docs/SSH-TUNNEL-VPS.md` 的对照表里：Chat 两者都行，Sessions、Skills、Memory、Soul 只有 SSH Tunnel 能管。**只想要远端聊天，Remote 够用；想把桌面端当远端 Hermes 的完整管理台，必须走 SSH Tunnel**。这个边界直接影响部署决策，选型前先想清楚自己要哪一种。

## 四、屏幕地图：README 写 12 屏，源码已经是 14 屏

README 的 Screens 表格列了 12 个屏幕并沿用至今，但屏幕目录里早已多出两个：

| 屏幕 | 作用 |
|---|---|
| **Chat** | 流式聊天（SSE）、工具进度、markdown、语法高亮、token 用量与费用显示 |
| **Sessions** | SQLite FTS5 全文搜索、按日期分组、断点续聊 |
| **Agents** | 创建 / 删除 / 切换 Hermes Profile（相互隔离的独立环境） |
| **Skills** | 浏览、安装、管理内置与用户安装的 skill |
| **Discover** | 社区注册表浏览器：Skills、MCP、Agents、Workflows 四个标签页 |
| **Kanban** | 多代理任务板：任务可被 Agent 自主领取完成，支持手动 Dispatch 派发 |
| **Providers** | Provider 配置 + 模型管理（原 Models 屏已并入此处） |
| **Memory** | 记忆条目增删改查、用户画像、记忆 provider 切换 |
| **Soul** | 编辑 SOUL.md 人格文件 |
| **Tools** | 按工具集（toolset）逐一启停 |
| **Schedules** | cron 定时任务构建器 + 投递目标 |
| **Gateway** | 消息平台网关配置与运行状态 |
| **Office** | Claw3d 3D 办公室（Three.js 渲染），可从 Agent 桌位直接开聊天窗 |
| **Settings** | Provider、凭据池、备份导入、日志查看、网络、主题、应用内更新 |

Discover 和 Kanban 在文章发表当天（era commit cf15af8b）就已经在源码里，README 表格当时就没跟上；后来 Models 屏反而被撤掉并进了 Providers。读这个项目的任何清单数字，都要记得 **README 一贯滞后于源码**——下面几节的数字都以源码为裁断。

## 五、slash 命令：README 写 22，写作当天源码已 34，现在 41

README 至今写着 "22 slash commands" 并列出 22 个名字。era 源码当天实际有 34 个，v0.7.7 已到 41 个。新增的 7 个是 `/learn`（从文件、URL、笔记或当前对话提炼可复用技能）、`/agents`、`/office`、`/discover`、`/providers`、`/schedules`、`/gateway`。

按类别挑几个有信息量的：

- **上下文控制**：`/compact`、`/compress` 压缩历史；`/goal` 锁定跨轮次持久目标（源码注释称之为 Ralph loop）；`/steer` 在 Agent 执行中不打断地转向；`/queue` 排队追加指令；`/btw` 问旁枝问题不污染主上下文
- **审批**：`/approve`、`/deny` 处理待确认动作
- **工具调用**：`/web` 搜索（Exa、Tavily 等，取决于配置的搜索后端）、`/browse` 开网页（Browserbase）、`/image` 生图（FAL.ai）、`/shell`、`/code`、`/file`
- **维护**：`/usage` 显示 token 用量、费用与限流；`/debug` 出诊断信息；`/update` 升级 Hermes；`/reload-skills` 不重启重载技能目录

## 六、19 个工具集，可以逐个关

README 写 "14 toolsets"，但它自己列了 15 项——这个内部矛盾从文章发表前就存在。源码 `src/main/tools.ts` 的 `TOOLSET_DEFS` 是权威清单，era 与当前完全一致，共 **19 个**：

| 工具集 | 官方描述（i18n 原文直译） |
|---|---|
| web | 联网搜索、抓取网页内容 |
| x_search | 检索 X（Twitter）帖子与内容 |
| browser | 操作浏览器：导航、点击、输入 |
| terminal | 执行 shell 命令与脚本 |
| file | 文件读写、搜索、管理 |
| code_execution | 直接执行 Python 与 shell 代码 |
| computer_use | 控制桌面：移动鼠标、点击、输入 |
| vision | 分析图像与视觉内容 |
| image_gen | 调 DALL-E 等模型生成图像 |
| video_gen | 从文本或图像提示生成视频 |
| tts | 文本转语音 |
| skills | 创建、管理、执行可复用技能 |
| memory | 持久知识的存取 |
| session_search | 跨历史会话检索 |
| clarify | 需要时向用户追问澄清 |
| delegation | 生成子代理并行处理任务 |
| cronjob | 创建与管理定时任务 |
| moa | Mixture of Agents，多模型协作 |
| todo | 任务规划，为复杂任务建待办清单 |

Tools 屏可以单独关掉任何一个。跑长任务时关掉 `computer_use` 和 `terminal` 只留 `web` + `memory`，是控制风险面最直接的手段——这个开关是按 Profile 记忆的，写进该 Profile 的 config.yaml。

## 七、20 个消息网关：国内平台的完整度是它和同类产品的真正差距

README 写 "16 messaging gateways"，源码 `src/shared/messaging-platforms.ts` 里定义了 **20 个**——era 源码与当前完全一致，也就是说 README 的 16 在写作时点就落后了。完整清单：

| 类别 | 平台 |
|---|---|
| 海外 IM | Telegram、Discord、Slack、WhatsApp、Signal、Matrix、Mattermost |
| 邮件 | Email（IMAP / SMTP） |
| 短信 | SMS（Twilio）——README 里写的 Vonage 在源码中零命中，早已只剩 Twilio |
| Apple | BlueBubbles（iMessage） |
| 国内 | 钉钉、飞书 / Lark、企业微信（群机器人 + 回调应用两种形态）、微信公众号、QQ 机器人、腾讯元宝（Yuanbao） |
| 其他 | API server、Webhooks、Home Assistant |

几个对接细节值得展开：飞书要求 `FEISHU_APP_ID` + `FEISHU_APP_SECRET`（加密 key 和验证 token 可选），支持群聊和私聊；企业微信拆成两个条目——群机器人是仅推送的 webhook 形态，回调应用是双向形态。还有一处 README 与源码的偏差：README 把微信写作 "WeChat (iLink Bot)"，但源码里的微信条目从文章发表当天起就叫 "WeChat (Official Account)"，对接的是公众号。每个平台是一组环境变量 + 一份官方文档链接，Gateway 屏里填表即可，不用手写 `~/.hermes/.env`。

给国内团队做共享 AI 助手，钉钉 / 飞书 / 企微 / 微信公众号 / QQ 一次配齐，这是这个项目对中文用户最实在的部分——同类桌面外壳大多只覆盖海外 IM。

## 八、记忆系统：注册表认识 8 个 provider，不止 README 说的 6 个

README 列了 6 个 "discoverable memory providers"。源码 `discoverMemoryProviders()` 的注册表实际有 **8 个**（era 即如此），它扫描上游 `~/.hermes/hermes-agent/plugins/memory/` 目录，装了哪个就显示哪个：

| Provider | 应用内官方描述 | 密钥 |
|---|---|---|
| **Honcho** | AI 原生跨会话用户建模，支持辩证问答与语义检索 | HONCHO_API_KEY |
| **Hindsight** | 带知识图谱的长期记忆，多策略检索 | HINDSIGHT_API_KEY 等 |
| **Mem0** | 服务端 LLM 事实抽取 + 语义检索 + 自动去重 | MEM0_API_KEY |
| **RetainDB** | 云端记忆 API，混合检索，7 种记忆类型 | RETAINDB_API_KEY |
| **Supermemory** | 语义长期记忆，画像召回 + 实体抽取 | SUPERMEMORY_API_KEY |
| **Holographic** | 本地 SQLite 事实存储，FTS5 检索 + 置信度评分 | 不需要 |
| **OpenViking** | 会话托管记忆，分层检索与知识浏览 | OPENVIKING_ENDPOINT 等 |
| **ByteRover** | 持久知识树，经 brv CLI 分层检索 | BRV_API_KEY |

Memory 屏里点一下 Activate 就把 `memory.provider` 写进配置，不需要动 YAML；关闭则退回内置记忆。不想把 API Key 存在明文 `.env` 里的用户，v0.7.0 起还有 Secrets provider：默认仍是 env 方式，可切换为 command 方式——由你配置的外部命令按需吐出密钥（KeePassXC、GnuPG、pass、Bitwarden、1Password CLI 都能接），带 3 秒超时和 1 MiB 输出上限，仅限 POSIX 系统，Windows 保持 env 方式。

## 九、Provider 矩阵：从十来个扩到三十多个入口

发表时的 Provider 清单（OpenRouter、Anthropic、OpenAI、Google、xAI、Nous Portal、Qwen、MiniMax、Hugging Face、Groq + 本地预设）如今扩了一大圈，v0.7.7 的选择器里大致分五类：

- **聚合器**：OpenRouter（官方标 "recommended"）、AI/ML API、NovitaAI
- **直连**：Anthropic、OpenAI、Google、xAI、Mistral、DeepSeek、Groq、Together、Fireworks、Cerebras、Perplexity、Hugging Face、NVIDIA NIM、Z.ai（GLM）、阿里 DashScope（国内 / 国际双端点）、小米 MiMo、MiniMax、Ollama Cloud
- **订阅 / OAuth 计划**：ChatGPT（Codex Plan）、xAI Grok、Qwen、Gemini CLI、MiniMax、Kimi Coding Plan——在应用内完成 OAuth 登录，不碰 API Key
- **本地**：LM Studio、Atomic Chat、Ollama、vLLM、llama.cpp 及任意 OpenAI 兼容端点
- **项目自家**：Hermes One（`inference.hermesone.org/v1`，OpenAI 兼容）

赞助商位现在是两家：Atlas Cloud（OpenAI 兼容网关，base URL 预填）和 Greptile（AI 代码审查，与 Agent 运行时无关，属纯赞助）。

## 十、发表之后这四个月：0.6.0 与 0.7.0 做了什么

以本文发表时的 v0.5.8 为界，之后两次大版本值得单独说：

**v0.6.0（2026-06-10，文章发表次日）**：3D 办公室（Office）成形——Three.js / Troika 渲染的 CEO 办公室，带角色绑定与待机动画，能从某个 Agent 的桌位直接弹聊天窗；网关改为每个 Profile 独立实例 + 动态端口分配。这一版还短暂加过 Bank 房间，功能写进了更新日志，但主分支上随即出现 "Remove Bank Screen" 提交——迭代快到功能来了又走。

**v0.7.0（2026-06-23，改名 Hermes One）**：这版的变化最猛——

- **Profile 钱包**：每个 Profile 可创建或导入 Base 主网以太坊钱包（每 Profile 上限 10 个），助记词用 Electron safeStorage 加密、不离开主进程；Profile 面板显示 $H1 / $HD 代币与原生余额。一个桌面 Agent 外壳内置链上钱包，是全部版本里最激进的决定，用不用见仁见智，但升级前应该知道它来了
- **Secrets provider**：上文第八节的外部密钥管理
- **应用内 Web 预览**：聊天工作区里直接开网页面板，导航做了安全门控
- **侧栏重做**：ChatGPT 风格的最近会话列表、置顶、Cmd/Ctrl+K 全局会话搜索
- **会话级模型覆盖**：单个会话换模型不动全局默认；另有辅助任务专用模型
- **聊天重构**：历史对账算法重写，修复工具调用前后文本流乱序；长代码块折叠
- **i18n**：希伯来语（完整 RTL）、拉美西语；品牌全部换成 Hermes One

## 十一、任务流案例：每天早上 9 点把 AI 早报发进飞书群

把上面的机制串一遍。假设你要一个每日定时摘要投进飞书群：

1. **Gateway 屏**配飞书：填 `FEISHU_APP_ID` / `FEISHU_APP_SECRET`，启用网关。网关按 Profile 独立跑（v0.6.0 起），启动失败会在界面横幅报错而不是静默
2. **Schedules 屏**建任务：cron 构建器支持分钟 / 每小时 / 每天 / 每周 / 自定义表达式；prompt 填"检索今天的 AI 新闻并写 300 字摘要"；投递目标选 Feishu。投递目标共 16 个（local、origin + 14 个消息平台），与网关清单不完全重合——QQ 机器人、元宝、BlueBubbles 能收网关消息但不在投递列表里
3. 任务落进 `~/.hermes/cron/jobs.json`，到点由 Hermes Agent 执行：搜索靠 web 工具集（Exa / Tavily 等），生成靠你配的模型，产出走网关投进飞书群
4. 跑完的会话进 Sessions，`/usage` 能看到这次花了多少 token；如果摘要质量不对，去 Soul 屏调人格或在 Schedules 里改 prompt

整条链路没有一行 YAML，这是这个外壳存在的理由。

## 十二、安装路径

下载入口是 [hermesone.org](https://hermesone.org)（原 hermesagents.cc 已 404，旧文链接需要更新）。v0.7.7 的 release 资产覆盖：macOS（arm64 / x64 的 dmg 与 zip）、Windows（setup.exe 与便携版 portable.exe）、Linux（x86_64 / arm64 AppImage、`.rpm`、`.deb`）。

三个已知坑，README 原话可证，至今没变：

- **Windows 未签名**：首次启动 SmartScreen 拦截，"More info" → "Run anyway"。未签名意味着系统无法验证发行者，这也是下节"信任边界"的一部分
- **Fedora RPM 无 GPG 签名**：强制校验的系统加 `--nogpgcheck`；且 RPM 构建不支持 electron-updater 自动更新，升级靠重装
- **WSL 装 Windows 版时 Playwright 卡 sudo**：安装器在 `Switching to root user...` 处等一个没有 TTY 的 sudo 密码，README 给了临时免密 sudo 的解法，issue 编号 #109

源码开发：`npm install && npm run dev`，需要 Node.js 和 Unix-like shell；测试跑 Vitest。

## 十三、采用建议

**适合**：

- 已经在用或想用 Hermes Agent，但不想手改 YAML / cron / webhook 的用户
- 需要把 Agent 接进钉钉 / 飞书 / 企微 / 微信公众号的国内团队——同类开源桌面外壳里这个覆盖面罕见
- 想要"本地跑、数据不出内网"的自托管人群：本地模式下聊天、记忆、会话库全在本机；介意明文密钥的，用 command 型 Secrets provider 接自己的密码库

**不适合 / 先等等**：

- 拿它当无头服务器的管理面：桌面形态天然不适合，服务端场景直接跑 Hermes Agent 本体
- 对稳定性有硬要求的团队：README 自述 "active development, some things might break"；四个月 48 个 release、Bank 功能朝令夕改，API 与功能面还在动
- 介意链上钱包这类特性的：v0.7.0 起钱包功能默认在 Profile 面板里，不用它也得知道它在
- 需要官方支持背书的：这是社区项目，与 Nous Research 无隶属——出问题找它的 issue 区，不是找 Nous

**建议顺序**：先在本地模式用 OpenRouter 一个 Key 跑通 Chat，确认 Hermes Agent 本身合用；第二步配飞书或钉钉网关验证消息链路；第三步再碰 Schedules、Kanban、多 Profile 和 SSH Tunnel。钱包和 3D 办公室放着别动，不影响主流程。

回到开头那句判断：这个项目赌的是"Agent 的竞争力在能力面，配置面的摩擦才是采用瓶颈"。四个月 14,000 星和 12 个社区翻译 locale 至少说明，愿意为省掉 CLI 配置成本付一次下载的人群是真实存在的。它没有伪装成官方作品，README 把话说得很清楚——把它当一个活跃的社区外壳来评估，而不是当作 Hermes 的官方客户端，是这个项目应得的读法。
