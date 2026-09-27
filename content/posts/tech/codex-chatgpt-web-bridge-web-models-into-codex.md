---
title: "codex-chatgpt-web：把 ChatGPT 网页版塞进 Codex 模型选择器的非官方桥接器"
date: "2026-09-28T04:10:00+08:00"
slug: "codex-chatgpt-web-bridge-web-models-into-codex"
github_repo: "miuuyy/codex-chatgpt-web"
source_key: "gh:miuuyy/codex-chatgpt-web"
description: "codex-chatgpt-web 是一个非官方桥接工具，让 Codex 原生调用 ChatGPT 网页版模型（含 Pro），走网页版独立用量、不耗 Codex 配额，支持上下文、流式、图片与 MCP 全工具模式。本文拆解其三种模式边界、Full harness 链路与安全模型。"
draft: false
categories: ["技术笔记"]
tags: ["Codex", "ChatGPT", "浏览器自动化", "MCP"]
---

# codex-chatgpt-web：把 ChatGPT 网页版塞进 Codex 模型选择器的非官方桥接器

先给判断：这个项目赌的是一个很具体的缝隙——OpenAI 的 ChatGPT 订阅（尤其 Pro）与 Codex 的配额是两本账，很多用户网页版额度用不完、Codex 配额却总不够。codex-chatgpt-web 用浏览器自动化把网页版 ChatGPT 包装成 Codex 模型选择器里的一个"本地模型"，让两本账并成一本用。它 12,000+ Stars、953 Forks（TypeScript），同时登上 GitHub monthly 趋势榜，最新版本 v6.1.2。但它是**非官方工具**，走的是 UI 自动化而不是 API，这决定了它的全部优点和全部风险都来自同一个事实：它在模拟人。

## 三种运行模式：自动化程度换安全性

理解这个项目的钥匙是它的三档模式，README 用一张表讲清了边界：

| 模式 | 发消息 | 本地 Codex 工具 |
|------|--------|----------------|
| Browser-only（仅浏览器） | 自动 | 无 |
| Full harness（全自动 + MCP） | 自动 | 有，经 MCP |
| Zero Risk（零风险） | 手动粘贴发送 | 有，经独立 MCP 连接器 |

- **Browser-only**：launcher 内嵌浏览器自动操作 ChatGPT 页面，但没有工具调用能力，接近"代你在网页上打字"。
- **Full harness**：核心卖点。通过官方的 OpenAI tunnel-client（隧道客户端）把 ChatGPT 的工具调用接回当前 Codex 任务——文件、终端、审批全部可用。隧道是**出站**连接，不开入站端口、不需要路由器转发，这点是安全设计上的亮点。
- **Zero Risk**：不读取、不操作 ChatGPT 页面。launcher 只准备好 prompt，你自己粘贴到网页发送，再回来点确认。工具调用走单独的 MCP 连接器。这一档牺牲自动化换最小攻击面，名字起得很直白。

模型侧，launcher 按账号能力自动探测：无推理选择器的账号（Free/Go）看到 Luna/Think；有推理控制的账号看到 Instant–High 档位，Extra High 与 Pro（如 GPT-5.6 Sol Pro、GPT-6 Astra）在账号开放时独立出现。所有自动模式模型名以 **(Web)** 结尾，在 Codex 里和原生模型并列可选。

## Full harness 的接线图

Full 模式的完整设置链路（README 给了视频教程入口）：

1. launcher 的 **MCP** 页创建 Tunnel 与 API key，点 Connect harness；
2. ChatGPT 侧开启 **Developer Mode**（开发者模式），新建名为 `Codex Native2` 的 Tunnel 连接器，Authentication 设 None、Allow all actions；
3. 回到 launcher 跑 **Verify runtime**，确认连接器挂载成功。

注意两个硬边界：写/改操作还需要 ChatGPT workspace 的管理员策略允许（对应 OpenAI 官方的 developer mode 与 MCP 应用文档）；审批提示默认**失败关闭**（fail closed），只有显式开 `--auto-approve-tool-calls` 才会自动点 Allow once——而且是"每次允许"，从不给永久授权。这个默认值的选择能看出作者对"自动化碰账号"的克制。

上下文方面：Plus Medium/High 档实测 90,000 token 窗口，实验性 **3× context** 开关可到 270,000，且全程兼容 Codex 原生压缩（compaction）。各模型的具体消息限额在项目 Discussions #309 维护。

## 安装与日常

v6.1.2 提供 macOS（arm64/x64）、Windows x64、Linux x64 安装包，AppImage/DMG/EXE 都从 Releases 下载；launcher 自带浏览器与运行时，不依赖本机 Chrome/Node/Bun。也提供终端一键安装脚本（macOS/Linux `curl | sh`、Windows `irm | iex`），脚本会校验发布的 SHA-256 清单并保留已有配置。

快速上手四步：装 launcher → 内嵌浏览器登录 ChatGPT 并跑冒烟测试 → 安装模型并重启 Codex → 需要 coding 工具就进 MCP 页完成 Full harness 设置。

运维细节不少：Settings → Run doctor 做端到端健康检查；子代理（subagents）有两种协议——Compatibility V1 跨后端兼容、Native 保留 Codex 特性并支持 Web-to-Web V2 委派，切换后需重启 Codex；`codex-chatgpt-web subagents status` 可查状态。

## 安全模型：用它之前必须读的部分

作者在 README 里反复强调的几条，逐条都值得当真：

- **非官方浏览器自动化**，不是 OpenAI API。ChatGPT UI 一改版选择器就可能失效——项目的设计原则是"漂移显式失败"（drift fails explicitly），宁可报错也不静默换模型或换传输，这是对"悄悄降级"这类最危险故障的防御。
- **浏览器状态是敏感登录凭证**。launcher 的 loopback 监听可被同机同用户进程访问，所以不要共享 launcher profile，只在可信工作站上用。
- **安装包未做平台签名**，macOS Gatekeeper / Windows SmartScreen 会告警；安装脚本校验 SHA-256 清单是唯一的来源完整性保障。
- 完整的架构（docs/architecture.md）与安全模型（docs/security-model.md）文档在仓库里，开 Full 模式前建议通读。

## 适用边界与采用建议

适合的人：同时付 ChatGPT 订阅与 Codex、想合并用量的人；想要 Pro 级模型但不想消耗 Codex 配额的重度用户；能接受"非官方、可能随 UI 变更中断"的工具属性的人。

不适合的场景：企业合规敏感环境（非官方自动化 + 登录凭证托管，多数 IT 政策过不了）；需要稳定 API 语义的生产链路（UI 改版即断，且明确不是 API）；对零点击自动化有洁癖的人——Zero Risk 模式虽然安全但牺牲了核心体验。

采用顺序建议：先 Browser-only 跑几天确认账号探测与稳定性，再评估是否上 Full harness；Zero Risk 作为过渡或高价值账号的保守选项。无论哪档，都做好"某天早上突然失效"的心理预期——这是这类工具的宿命，也是它 MIT 开源、可以自己 fork 维护的理由。

项目地址：[miuuyy/codex-chatgpt-web](https://github.com/miuuyy/codex-chatgpt-web)，提供包括简体中文在内的四语 README。
