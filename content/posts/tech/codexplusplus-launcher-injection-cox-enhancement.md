---
title: "CodexPlusPlus 解读：不改 app.asar，给 Codex 桌面应用加一层可回滚的增强"
date: "2026-06-04T12:57:00+08:00"
lastmod: "2026-10-01T10:00:00+08:00"
slug: "codexplusplus-launcher-injection-cox-enhancement"
github_repo: "BigPizzaV3/CodexPlusPlus"
source_key: "gh:BigPizzaV3/CodexPlusPlus"
description: "CodexPlusPlus（Codex++）是面向 OpenAI Codex / ChatGPT 桌面应用的外部启动器与管理工具，Rust + Tauri 实现，通过 Chromium DevTools Protocol 注入增强脚本而非改写 app.asar，提供供应商切换、协议转换、会话管理与界面增强。"
draft: false
categories: ["技术笔记"]
tags: ["Codex", "OpenAI", "Tauri", "Rust", "CDP", "AI 编程", "桌面应用"]
hiddenFromHomePage: false
---

先说判断：Codex 桌面应用好用，但它把三件事锁死了——API Key 模式下插件入口不可用、会话只能归档不能删除、换中转 API 就要手工改 `config.toml` 且容易丢登录态。CodexPlusPlus（Codex++）对这三件事各给了一个答案，而且都建立在同一个前提上：不动官方应用的任何文件。它以外部 launcher 拉起 Codex、通过 Chromium DevTools Protocol（CDP，浏览器调试协议）向渲染进程注入脚本，供应商切换则做成可备份、可回滚的配置管理。

这套做法的代价也要先讲清楚：注入依赖 Codex 页面结构，官方应用一更新就可能需要跟着适配——项目自己的 v1.4.0 发布说明里就有一整段处理 ChatGPT-Desktop 更新导致的启动故障。

本文基于 2026-10-01 的仓库状态写作（main 分支提交 fe3fb42，最新 release v1.4.0，发布于 2026-09-28）。

## 项目坐标

| 项 | 值（2026-10-01 核对） |
|:---|:---|
| 仓库 | [BigPizzaV3/CodexPlusPlus](https://github.com/BigPizzaV3/CodexPlusPlus)，默认分支 `main` |
| 定位 | 面向 OpenAI Codex / ChatGPT 桌面应用的外部启动器与管理工具 |
| Stars / Forks | 31,732 / 2,022（2026-06-04 前后为 12,655，四个月约 2.5 倍） |
| 许可证 | AGPL-3.0-only（README 明确 SPDX 标识；只覆盖自身代码，不含 OpenAI 商标与应用资源） |
| 技术栈 | Rust 54.5%、JavaScript 26.7%、TypeScript 12.4%、CSS 5.8%（按 GitHub languages 字节数）；管理工具用 Tauri 2.x，Rust 下限 1.85 |
| 版本节奏 | 2026-05-06 建库，v1.1.x → v1.2.56（2026-08-27）→ v1.3.0（2026-09-10）→ v1.4.0（2026-09-28），共 76 个 tag |
| 贡献者 | 85 人；BigPizzaV3 以 660 次提交占主导，dongyu23、Rat0323 等 4 人各 50 次以上 |
| 官网 | <https://codexpp.cc/>（GitHub Pages） |

一个容易搞混的点先摆正：**Codex 桌面应用本身是 Electron 应用，不是 Tauri**。Codex++ 处理的本地状态键名带 `electron-` 前缀（`codex_app_state.rs`），注入走的 `--remote-debugging-port` 是 Chromium/Electron 的调试参数；Tauri 2.x 是 Codex++ 自己管理工具的技术栈。原文把两者混在一起了。

## 系统地图

Codex++ 在磁盘上分三块，各管一段：

| 组件 | 位置 | 职责 |
|:---|:---|:---|
| 管理工具 | `apps/codex-plus-manager` | Tauri + React 控制面板：供应商、模型、工具插件、会话、增强功能、脚本、更新、诊断 |
| 静默启动器 | `apps/codex-plus-launcher` | 日常入口，不显示 UI，带调试参数拉起 Codex 并注入 |
| 注入脚本 | `assets/inject/` | 注入到 Codex 渲染进程的增强逻辑，主脚本 `renderer-inject.js` 约 1.35 万行 |

Rust 侧的 `crates/codex-plus-core` 承载启动、注入、配置、协议代理等核心逻辑，`crates/codex-plus-data` 负责会话数据和供应商同步。仓库还有 `apps/codex-plus-mobile-relay`（微信连接的中继服务）和 `services/share-site`（会话分享站点）。

四种供应商模式是理解这个项目的钥匙，它把「用官方还是用第三方 API」从手工改配置变成四个明确档位：

| 模式 | 用途 | 认证位置 |
|:---|:---|:---|
| 官方登录 | 只用 ChatGPT / Codex 官方账号 | 清理自定义 provider，保留官方登录态 |
| 官方登录 + API（混入） | 保住官方账号与插件入口，模型请求走兼容 API | Key 写入 provider bearer token，不动 `auth.json` |
| 纯 API | 不依赖官方账号 | 独立保存 `config.toml` 与 Key |
| 聚合供应商 | 多个 API 之间路由 | 支持故障转移、按会话/按请求/权重轮转 |

当前 README 特意澄清了混入模式的语义：它**不是**「官方优先、额度不足时 API 补偿」——模型请求始终走你配置的 API，官方账号只提供登录状态和插件入口。这一点容易被想当然，配之前值得看一眼。

## CDP 注入怎么工作

从 `Codex++` 入口启动时，launcher 给 Codex 进程加两个参数（`launcher.rs` 的 `build_codex_arguments`）：

```text
--remote-debugging-port=<port>
--remote-allow-origins=http://127.0.0.1:<port>
```

随后通过 loopback 端口的 CDP 端点枚举页面目标，拿到 `webSocketDebuggerUrl` 后把脚本注入渲染进程。整个过程官方应用的二进制和资源文件原封不动——这也是它和「改 `app.asar`」「写 DLL」两类做法的本质区别：Codex 官方升级不依赖 Codex++ 发新包跟进，关闭增强后就是干净的原生应用。

注入侧不是单一脚本。`assets/inject/` 下按功能拆了多份：`api-quota-gate.js` 在混入 Key 模式下解除官方订阅额度的发送锁；`composer-readiness.js` 处理输入框就绪状态；`floating-panel/` 是悬浮面板；用户脚本由 `user-scripts-bootstrap.js` 和 `user-scripts-runtime.js` 加载。注入还有熔断保护：app-server patch 失败达阈值就停止重试并改用指数退避，避免页面反复刷新——v1.4.0（#2256）刚修复过熔断可被 provider 重试绕过的问题。

注入生效的可见标志是 Codex 界面里的 Codex++ 菜单和后端状态指示灯——指示灯有四态（正常/失败/检查中/降级），对应 `renderer-inject.js` 里的 `data-status` 样式。

## 一次「配中转 API、保住官方登录态」的完整流程

把四种模式里最常用的混入模式走一遍，每一步都对应仓库里的真实机制：

1. 打开管理工具，确认已检测到 ChatGPT 登录状态。
2. 添加供应商：填 Base URL 和 Key，选 Responses 或 Chat Completions 协议，配模型列表和每模型上下文窗口（支持 `1M`、`200K` 或纯数字）。如果中转站只有 Chat Completions 协议，Codex++ 的本地协议代理会把它转换成 Codex 使用的 Responses 协议。
3. 点「使用/切换供应商」。Codex++ 先把当前配置和会话元数据备份到 `~/.codex/backups_state/provider-sync`（`provider_sync.rs`），再写入目标配置到 `~/.codex/config.toml`——混入模式下 Key 写进 provider 的 bearer token 字段，`auth.json` 保持官方登录态不动。
4. 切换后旧会话不会消失：provider 同步会处理各供应商的会话元数据，让不同 API 时期的对话在会话列表里都可见。
5. 想回官方，在管理工具里切回官方登录。v1.4.0（#2216）修复了「切回官方」清理不彻底的问题——此前 `custom` provider 的 `base_url` 和根级 `model` 会残留在配置里。

每一步都有出处，也都有失败路径：切换后请求失败时，README 建议先在供应商详情里跑模型测试或 Provider Doctor，确认协议、Base URL、Key 和测试模型匹配；两种模式的认证位置不同，不要手工复制 `auth.json`。

## 界面增强与会话管理

依赖注入的界面增强都在渲染进程里完成，当前 README 列出的包括：

- **会话操作**：悬停删除按钮（支持撤销）、批量删除、Markdown 导出、Token 用量历史、项目移动。Codex 原生只有归档，长期使用积累的旧会话没法真正清掉。
- **插件市场解锁**：API Key 登录模式下，Codex 原生插件入口会提示需要登录 ChatGPT——这句出自项目早期（v1.2.x）README，当时是头号痛点。Codex++ 解锁插件入口并支持插件自动展开；混入模式下这个功能不再需要。
- **中文界面与本地化**：强制中文、原生菜单本地化。
- **输入修复**：富文本粘贴转纯文本。
- **会话体验**：会话宽度、滚动位置恢复、线程 ID 显示。
- **Goals 与 Stepwise**：目标管理和下一步建议，Stepwise 可单独配置 API、模型、建议数量与超时。
- **皮肤管理**：Dream Skin 社区主题的搜索、预览、安装。

要注意 README 的一句提示：依赖注入脚本的设置通常需要保存后重启 Codex++ 才生效——注入发生在启动阶段，这不是即改即用的插件系统。

## 微信连接与拓展系统

两个 2026 年下半年加的功能值得单独说：

**微信连接**。个人微信扫码连接本机 Codex 会话，每个微信联系人映射到独立会话，可配置允许哪些微信用户接入。实现在 `apps/codex-plus-mobile-relay`（WebSocket 中继，分 host/client 两端）和 `codex-plus-core/src/connect`；v1.4.0 把 Windows 侧改用桌面版微信维护的标准 CLI，零配置跑通全链路。对把 Codex 当私人助手的用户，这等于给 Agent 加了一条手机端的入口。

**拓展 API**。用户脚本从「往目录里扔 JS」升级成了有正式契约的拓展系统（`EXTENSIONS.md`，接口版本 `apiVersion = 1`）。脚本放在 `~/.config/Codex++/user_scripts/`（Windows 为 `%APPDATA%\Codex++\user_scripts\`），按文件名排序在独立 IIFE 里执行，通过全局对象 `window.codexPlus` 调用注册行操作、注册页面、调后端接口等能力，仓库同时提供了 TypeScript 类型声明。改完脚本在管理页点热重载即可，不用重启。

一个容易查错的路径顺带纠正：`~/.codex-session-delete/` 不是用户脚本目录，它是 Codex++ 自己的状态与日志目录（`settings.json`、诊断日志等）——这个目录名来自项目早期的会话删除功能，现在装的是应用状态。

## 安装与数据位置

从 [GitHub Releases](https://github.com/BigPizzaV3/CodexPlusPlus/releases) 下载安装包，命名形如 `CodexPlusPlus-1.4.0-windows-x64-setup.exe`（NSIS）、`CodexPlusPlus-1.4.0-macos-x64.dmg`、`CodexPlusPlus-1.4.0-macos-arm64.dmg`，另有 zip 版本。装完有两个入口：`Codex++`（静默启动）和 `Codex++ 管理工具`（配置面板）。首次使用建议先开管理工具确认应用路径和运行状态，再配供应商，最后从静默入口启动。

macOS 安装包未签名/未公证，Gatekeeper 可能提示「已损坏，无法打开」，按 README 给出的方式解除隔离：

```bash
sudo xattr -rd com.apple.quarantine /Applications/Codex++\ 管理工具.app
sudo xattr -rd com.apple.quarantine /Applications/Codex++.app
```

Codex++ 会按顺序识别 `Codex.app`、`OpenAI Codex.app`、`ChatGPT.app` 等候选路径（`app_paths.rs`）；Windows 侧 Codex 随 ChatGPT-Desktop（MSIX 打包）分发，v1.4.0 刚修复过该应用更新后 AUMID 变动导致的启动故障（#2308 / #2310）。

数据位置一张表看清（`~/.codex` 指 Codex 主目录，设置了 `CODEX_HOME` 时以它为准）：

| 路径 | 归属 |
|:---|:---|
| `~/.codex/config.toml` | Codex 配置（Codex++ 切换供应商时写入） |
| `~/.codex/auth.json` | Codex 官方登录态（混入模式不碰它） |
| `~/.codex/sqlite/*.db`（旧版回退 `state_5.sqlite`） | Codex 本地会话数据库 |
| `~/.codex-session-delete/` | Codex++ 状态与日志 |
| `~/.codex/backups_state/provider-sync` | 供应商切换备份 |
| `~/.config/Codex++/user_scripts/` | 用户脚本（Windows 为 `%APPDATA%\Codex++\user_scripts\`） |

## 采用判断

**建议直接上手的**：每天用 Codex 桌面应用、被「插件入口被锁」或「会话只能归档」卡住的人；需要在官方登录态和国内中转 API 之间来回切换的开发者——四种供应商模式加自动备份就是为这个场景设计的；想在微信里调用本机 Codex 的人。

**可以等等的**：只用 Codex CLI / IDE 插件的用户——Codex++ 增强的是桌面应用，不是 CLI；对注入类工具零容忍的环境。

**风险与边界，三条都实在**：

- **升级适配是常态**。Codex++ 依赖官方应用的页面结构、CDP 和本地数据格式，官方一更新部分注入功能就可能失效。v1.4.0 发布说明里那段「该进程没有程序包标识符」的修复就是 ChatGPT-Desktop 更新 AppxManifest 导致的——这不是假设性风险，是这个项目日常维护的一半内容。
- **AGPL-3.0-only 有传染性**。修改分发或网络服务化都需要按同协议开源；企业内部分发前先过一遍合规。
- **维护集中于主作者**。85 位贡献者里 BigPizzaV3 一人 660 次提交，社区活跃但关键路径上的 bus factor 偏低。README 的赞助商区说明项目有持续投入，这条风险是「人」的风险，不是「钱」的风险。用中转时，信任对象是中转服务商，这条不因工具而改变。

另外两个观察：注入本质是「官方默许灰色地带的调试通道」，理论上 OpenAI 可以收紧 CDP 暴露面，这类工具的存续依赖官方态度；README 的推荐内容来自远程广告列表（`ads.rs` 拉取 ads.json），赞助商区挂了多家中转服务商，这个项目深度嵌在中转 API 生态里。

## 参考资料

- 仓库：<https://github.com/BigPizzaV3/CodexPlusPlus>（main 分支提交 fe3fb42，2026-09-30）
- Releases：<https://github.com/BigPizzaV3/CodexPlusPlus/releases>（v1.4.0，2026-09-28，发布说明含 #2308/#2310/#2216/#2256 等修复编号）
- 官网：<https://codexpp.cc/>
- 拓展开发指南：仓库 `EXTENSIONS.md`；协议 AGPL-3.0-only（仓库 LICENSE）
- 数据读数：GitHub API，2026-10-01；历史读数 12,655 stars 见原文 2026-06-04 记录
