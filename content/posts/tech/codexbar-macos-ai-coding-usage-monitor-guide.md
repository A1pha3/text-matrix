---
title: "CodexBar：把 89 家 AI 编程服务的额度和重置时间塞进 macOS 菜单栏"
date: "2026-07-07T03:00:17+08:00"
lastmod: "2026-10-03T00:00:00+08:00"
slug: "codexbar-macos-ai-coding-usage-monitor-guide"
github_repo: "steipete/CodexBar"
source_key: "gh:steipete/CodexBar"
description: "CodexBar（steipete/CodexBar，MIT）是一个 macOS 14+ 菜单栏小工具，统一显示 Codex / Claude / Cursor / Gemini / Copilot / Grok / ElevenLabs / AWS Bedrock / OpenRouter / LiteLLM 等 89 家 AI 编程服务的额度、花费和重置倒计时（2026-10-03 核验）。隐私优先：复用已有登录会话，不存密码；另有全平台 CLI、Linux Qt 6 桌面版与社区 Windows 版。"
draft: false
categories: ["技术笔记"]
tags: ["macOS", "AI 编程"]
---

# CodexBar：把 AI 编程服务的额度塞进菜单栏

同时用几家 AI 编程服务的人，每天都在回答同一个问题：Codex 还剩多少、Claude 周额度什么时候重置、OpenRouter 余额够不够今晚这批任务。每家一个 web dashboard，每套窗口规则还都不一样。CodexBar（[steipete/CodexBar](https://github.com/steipete/CodexBar)，MIT）的回答是一个菜单栏状态图标：89 家服务的额度（quota）、花费和重置倒计时悬停可见（provider 数为 2026-10-03 核验值，官方 [providers.md](https://github.com/steipete/CodexBar/blob/main/docs/providers.md) 写明 "currently registers 89 provider IDs"，这个列表还在增长）。

## 学习目标

读完这篇文章，你应该能回答：

- CodexBar 凭什么拿到 89 家 provider 的数据——为什么它不需要你新建账号、存密码；
- GUI 之外，CLI 的 `usage` / `cost` / `guard` / `serve` / `hooks` 各自解决什么问题；
- 它要哪些系统权限、为什么，哪些权限它明确不碰；
- macOS、Linux、Windows 三个平台上它分别以什么形态存在，你该不该用。

## 它要解决的核心痛点

AI 编程服务 2025–2026 进入多 provider 混用阶段。一个重度用户的典型一天：

- 早上用 **Codex CLI** 跑长任务（5 小时窗口）；
- 切到 **Claude Code** 写文档（周窗口）；
- 中午用 **Cursor** debug（订阅 plan）；
- 下午调 **OpenRouter** 跑便宜模型（按 token 计费）；
- 晚上用 **ElevenLabs** 给 demo 配语音（character credits）。

每家各有一套 session / weekly / monthly / credit 口径，重置时间各不相同。同时记五到十个窗口，靠脑子记不现实，靠开五个网页也不现实。

CodexBar 把这件事收成一个状态栏：每家 provider 一个图标（或 Merge Icons 模式合成一个加切换器），悬停看用量条和重置倒计时，状态页轮询还会在服务出事故时给图标加角标。

## 89 家 provider 怎么接

README 列了完整清单，每家配独立文档（`docs/<provider>.md`）。挑有代表性的：

### 主流 coding CLI / IDE

- **Codex** — OAuth API 或本地 Codex CLI，可选 OpenAI 网页 dashboard 补充数据
- **Claude** — OAuth API / 浏览器 cookies / CLI PTY 兜底；session + 周窗口
- **Cursor** — 浏览器会话 cookies 拿 plan、用量和账单重置
- **OpenCode** / **OpenCode Go** — 浏览器 cookies / 用量 API / 本地 SQLite 成本历史
- **Gemini** — 走 Gemini CLI 凭证的 OAuth 额度 API，不碰浏览器 cookies
- **Copilot** — GitHub device flow + Copilot 内部用量 API
- **Devin** — Chrome localStorage 会话或手动 Bearer token

### 编程 plan 服务

- **z.ai** — API token，个人/团队额度、5 小时和小时窗口
- **MiniMax** — API token / cookie header / 浏览器 cookies 三选一
- **Kiro** — CLI 用量，月度 + bonus credits
- **Vertex AI** — gcloud OAuth，token 成本来自本地 Claude 日志
- **Augment** — CLI 或浏览器 cookies
- **Kilo / Codebuff / Qoder / Command Code / StepFun** — 各家订阅口径
- 国内的 **阿里 Coding Plan / Token Plan、Qwen Cloud、Kimi、小米 MiMo、豆包、LongCat** 都在列

### API provider

- **OpenAI** — Admin API key 的用量/成本图表
- **OpenRouter** — API token 按信用额度追踪
- **LiteLLM** — Virtual key + proxy URL，个人/团队预算
- **AWS Bedrock** — Cost Explorer 花费 + 月度预算 + 可选 CloudWatch Claude 活跃度
- **Grok** — CLI billing RPC，grok.com 浏览器会话兜底；**Groq** — 浏览器会话看控制台花费，企业版有 Prometheus API 兜底
- **DeepSeek / Moonshot / Mistral / Deepgram / Doubao / Poe / Chutes / xAI / Hugging Face** — 各家 API key 追踪

### Voice / Speech

- **ElevenLabs** — character credits 和语音槽位

归纳起来，凭证只有三类来源：你已经登录过的会话（OAuth、浏览器 cookies、CLI 本地文件）、你显式配置的 API key、以及无需联网的本地日志。新 provider 按官方的 provider authoring 指南（`docs/provider.md`）接入，部分文档由 `Scripts/regenerate-provider-docs.mjs` 自动生成。

## 隐私与权限

### 复用会话，不新增认证

CodexBar 的关键设计是**复用你已经登录的会话**：Codex 读 `~/.codex/auth.json`（或 `$CODEX_HOME/auth.json`）里的 OAuth token；Claude 读 OAuth 凭证，文件兜底是 `~/.claude/.credentials.json`；Cursor 读浏览器会话 cookies，走 cookie 认证的 cursor.com dashboard API。不建新账户、不存密码、不上传数据，解析默认全部在本机完成，浏览器 cookies 属于可选开启项。隐私模型的外部审计记录在仓库 [issue #12](https://github.com/steipete/CodexBar/issues/12)。

有一个值得知道的边界：默认的 Adaptive 刷新只做轻量检查；另一个**可选**的 Adaptive (agent-aware) 档位会先征求同意，才去读运行进程列表（含命令行）来识别 Codex/Claude 会话。拒绝就回落到普通 Adaptive，且只保留最近活跃时间，不存会话路径。

### 密码不落盘；API key 显式设置才落盘

默认不存任何凭证。唯一例外是你显式执行的 `codexbar config set-api-key`：key 写进解析后的配置文件（新安装是 `~/.config/codexbar/config.json`，老安装继续用 `~/.codexbar/config.json`），写入过程是先在目标卷的 `0700` 私有目录暂存、以 `0600` 权限创建文件、写完原子替换，不用打开设置界面，`--stdin` 传值避免进 shell 历史。

### 权限清单：要什么，不要什么

- **Full Disk Access（可选）**：只有要让 CodexBar 读 Safari cookies 时才需要。不给也行，换别的浏览器、手动 cookie、API key 或 CLI 来源即可。
- **Keychain 访问（macOS 弹窗）**：Chromium cookie 导入需要浏览器的 Safe Storage 项来解密。后台路径拿不到授权就直接跳过，不会反复弹窗；Settings → Advanced → Disable Keychain access 可以整体关掉。
- **明确不要的**：屏幕录制、辅助功能（Accessibility）权限一概不申请，后台也不爬文件系统——只读功能开启后的已知位置（浏览器 cookies、provider 配置文件、本地 JSONL 日志）。

## 三个平台的不同形态

**macOS** 是主场：SwiftUI 菜单栏应用，要求 macOS 14+（Sonoma），无 Dock 图标，`brew install --cask codexbar` 或从 GitHub Releases 下载。构建源码需要 Swift 6.2+。

**Linux** 已经有正牌桌面版：Qt 6 应用支持 Wayland 和 X11，发布档覆盖 x86_64/ARM64，运行要求 glibc 2.39+ 和 Qt 6.4+，需另行安装 CodexBar CLI；Omarchy 上还有共享同一后端的原生 bar widget。GNOME 可能需要装托盘扩展，应用窗口本身不依赖托盘。

**Windows** 没有官方版，README 给了两个社区项目：Win-CodexBar，以及通过 WSL2 驱动原版 CLI 的 CodexBar for Windows（x64/ARM64 安装包）。

**CLI 三端通用**，macOS/Linux 都有预构建 tarball（Linux 另有静态 musl 版），Arch 用户直接 `yay -S codexbar-cli`，Homebrew 用户 `brew install steipete/tap/codexbar`（该 formula 目前面向 Linux）。

## CLI：超出菜单栏的部分

CLI 不是 GUI 的附庸，`codexbar` 默认执行 `usage`，输出 `--format text|json|toon`——`toon` 是给 agent 用的省 token 格式，payload 与 JSON 相同。子命令各有分工：

```bash
# 列出 provider 与启用状态（不发请求）
codexbar config providers

# 启用 / 禁用 provider
codexbar config enable --provider grok
codexbar config disable --provider cursor

# 从 stdin 存 API key
printf '%s' "$ELEVENLABS_API_KEY" | codexbar config set-api-key --provider elevenlabs --stdin

# 本地成本扫描（Claude / Codex / Cursor / Antigravity / Muse Code / Pi）
codexbar cost --provider both
```

几个子命令值得单独说：

- **`guard`** — 把额度变成自动化的闸门。`codexbar guard --provider codex --min-remaining 20 --window weekly --json` 查不到 20% 以上剩余周额度就以退出码 1 结束；0 表示安全，69（`EX_UNAVAILABLE`）表示查不到，加 `--fail-open` 可把 69 放行为 0。脚本里据此决定要不要放行长任务。
- **`serve`** — 起一个本机 HTTP 服务（默认 `127.0.0.1:8080`），暴露 `/usage`、`/cost` 和带 Bearer token 的 `/dashboard/v1/snapshot`。绑非回环地址必须配 token 且显式 `--allow-plain-http`（明文确认），否则拒绝启动。
- **`hooks watch`** — 常驻轮询，在额度、状态真实跳变时触发外部命令（边沿触发，同一事件 600 秒内不重复投递）。没有它，headless 环境配置的钩子永远不会跑。
- **多账号** — `--account <label>` / `--account-index <n>` / `--all-accounts` 按 config 里的 token 账号取数；Codex 则枚举应用切换器里同样的可见账号。

退出码约定：0 成功，2 provider 不存在，3 解析错误，4 超时，1 其他失败。macOS 上装 CLI 最省事的路径是应用内 Preferences → Advanced → Install CLI，符号链接到 `/usr/local/bin` 和 `/opt/homebrew/bin`。

## 架构与刷新

仓库按 Swift 模块分层（[docs/architecture.md](https://github.com/steipete/CodexBar/blob/main/docs/architecture.md)）：

- `Sources/CodexBarCore` — 抓取与解析：Codex RPC、PTY runner、Claude 探针、OpenAI 网页抓取、状态轮询；
- `Sources/CodexBar` — 状态与 UI：`UsageStore`、`SettingsStore`、`StatusItemController`、菜单与图标渲染；
- `Sources/CodexBarWidget` — WidgetKit 桌面小组件，读同一份快照；
- `Sources/CodexBarCLI` — 命令行；另有 Claude PTY 稳定性 helper 与 web 诊断 helper 两个辅助进程。

数据流是一条线：后台刷新 → `UsageFetcher`/各 provider 探针 → `UsageStore` → 菜单、图标、小组件。新装默认 Adaptive 刷新，固定档位 1/2/5/15/30 分钟可选。Codex 本地成本历史存在 WAL 模式 SQLite 里，上限 25,000 条会话记录或 256 MiB；应用更新走 Sparkle 框架。原生的成本历史源有八家：Codex、Claude、OpenAI Admin、Mistral、AWS Bedrock、Vertex AI、Cursor、OpenCode Go，其余 provider 不硬凑空表。

外围生态都长在 CLI 上，而且不是竞争关系：waybar、COSMIC 面板、GNOME 扩展、多个 KDE Plasma 6 widget、Cinnamon 小程序、Noctalia 插件、tmux/SketchyBar/Zellij 的 showy-quota、Stream Deck 集成，甚至一块 ESP32 桌面屏（USB 供电的 AI Monitor）都在读 `codexbar` 的输出。应用本身还带 23 种语言本地化和每周额度重置时的礼花动画（可关）。

## 真实使用场景

### 场景 1：长任务起不起

下面是 `docs/cli.md` 里的官方样例输出（非虚构数据）：

```text
== Codex 0.6.0 (codex-cli) ==
Session: 72% left [========----]
Pace: 12% in deficit | Expected 16% used | Projected empty in 2h 30m
Resets today at 2:15 PM
Weekly: 41% left [====--------]
Credits: 112.4 left
```

Pace 行直接给出预测：按当前节奏，额度撑不到重置点。看这一眼就能决定"现在跑 Claude 还是 Codex"，或者把大任务排到今晚重置之后。

### 场景 2：给自动化上闸门

```bash
codexbar guard --provider claude --min-remaining 30 --window weekly || exit 0
./run-long-batch.sh
```

周额度不足 30% 时脚本直接跳过，不会跑到一半撞墙。

### 场景 3：本地成本对账

```bash
codexbar cost --period month-to-date --json
```

从本地会话日志扫描（Claude/Codex 不联网），JSON 输出带逐日明细和模型拆分，进 cron 就是一份月度对账快照。Settings 里的 Usage & Spend 视图是同一数据的本地估算页，按 7/30/90 天或全部（扫描窗口 365 天）查看，按原生币种分组。

## 与同类工具的对比

| 工具 | 平台 | 覆盖面 | 说明 |
|------|------|--------|------|
| **CodexBar** | macOS GUI + Linux 桌面版 + 全平台 CLI | 89 家 | 跨 provider 监控，GUI/CLI 同源 |
| **ccusage** | CLI | 本地日志用量/成本统计 | CodexBar 在 Credits 中致谢的成本追踪灵感来源 |
| **官方 dashboard**（OpenAI/Anthropic 等） | Web | 各自一家 | 数据最权威，但一家一个页签 |
| **Win-CodexBar / CodexBar for Windows** | Windows | 复用 CodexBar CLI | 社区移植，非官方 |

单家 provider 的监控工具不少；把几十家 provider、GUI、CLI 和配套文档收进同一个仓库的，目前还没有看到同量级的替代品。README 里那一长串第三方移植全都是围绕它的 CLI 生态长出来的，侧面印证了这一点。

## 适用边界

**适合**：

- macOS 14+（或愿意装 Linux 桌面版/CLI）且同时用 3 家以上 AI 编程服务；
- 想在启动长任务前有据可依，而不是刷新五个网页碰运气；
- 在意隐私——不希望新工具另存一份 OAuth/API 凭证；
- 想把额度数据接进脚本、CI、tmux 状态栏或家庭面板。

**不适合**：

- 只用一两家 provider——为这层聚合付出的配置成本不划算；
- 想要系统级 CPU/内存/网络监控——CodexBar 只管 AI 服务的额度；
- 需要官方保证的 Windows 体验——那条路目前只有社区移植。

## 关键事实

以下数字均为 2026-10-03 经 GitHub API 与仓库 main 分支核实：

- **仓库**：[steipete/CodexBar](https://github.com/steipete/CodexBar)，22,140 Stars / 2,036 Forks，活跃维护（当天仍有提交）
- **协议**：MIT；作者 Peter Steinberger（steipete）
- **版本**：最新 release v0.71.0（2026-10-02 发布）
- **provider 数**：89（README 逐条清点、社交卡片、providers.md 三处一致）
- **系统要求**：macOS 14+（Sonoma）；源码构建需 Swift 6.2+
- **官网**：[codexbar.app](https://codexbar.app)
- **灵感来源**：[ccusage](https://github.com/ryoppippi/ccusage)（MIT）的成本追踪部分，README Credits 一节致谢

## 同作者的其他工具

steipete 在 Related 一节列的三个项目都围绕同一条主线——把 AI 编程工作流的摩擦抹掉：

- **[Trimmy](https://github.com/steipete/Trimmy)** — 把多行 shell 片段压平，粘贴进终端直接跑；
- **[MCPorter](https://mcporter.dev)** — Model Context Protocol 服务器的 TypeScript 工具箱与 CLI；
- **[oracle](https://askoracle.dev)** — 卡住时调用 GPT-5 Pro，带上自定义上下文和文件求答。

## FAQ 与排查

**Keychain 弹窗反复出现？** 看 `docs/keychain-prompts.md` 的 Allow Once vs Always Allow 说明；或在 Settings → Advanced 里禁用 Keychain 访问，改用手动 cookie/API key。

**配置文件到底在哪？** 新安装 `~/.config/codexbar/config.json`；从旧版升上来的安装若没有 XDG 配置，继续读 `~/.codexbar/config.json`；支持 `XDG_CONFIG_HOME` 和 `CODEXBAR_CONFIG` 环境变量覆盖。

**Linux 上能自动导浏览器 cookies 吗？** 不能。Linux 支持手动 cookie header，以及 API key、OAuth、CLI/本地文件来源；Cursor 例外，`auto`/`cli` 模式可读已登录应用的 token。

**装完 CLI 提示找不到命令？** macOS 用应用内 Install CLI（或仓库里的 `./bin/install-codexbar-cli.sh`，需要管理员确认）；Linux 直接用 Homebrew formula、AUR 或 Releases 里的 tarball。

## 练习与自测

1. 你同时用 Codex 和 Claude Code，想在启动两小时批处理前确认两家周额度都剩 30% 以上。写出命令和判定方式。（提示：`guard --window weekly`，退出码 0 放行、1 拦下、69 查不到。）
2. 为什么 CodexBar 读 Chromium cookies 需要 Keychain 访问权限，而后台路径不会反复弹窗？（提示：Safe Storage 解密；后台拿不到授权即跳过。）
3. `set-api-key` 存的 key 落在哪个文件、什么权限？写入为什么不会出现半截文件？（提示：`0700` 暂存目录、`0600` 创建、原子替换。）
4. 只用 Claude Code 一家，值不值得上 CodexBar？说出你的判断依据。

## 进阶阅读

- [docs/architecture.md](https://github.com/steipete/CodexBar/blob/main/docs/architecture.md) — 模块划分与数据流；
- [docs/cli.md](https://github.com/steipete/CodexBar/blob/main/docs/cli.md) — CLI 全量参考，含 `serve` 威胁模型与退出码；
- [docs/providers.md](https://github.com/steipete/CodexBar/blob/main/docs/providers.md) — 89 家 provider 的抓取策略总表；
- [docs/provider.md](https://github.com/steipete/CodexBar/blob/main/docs/provider.md) — 自己写一个 provider 的接入指南；
- [docs/keychain-prompts.md](https://github.com/steipete/CodexBar/blob/main/docs/keychain-prompts.md) — Keychain 授权的边界与排障。

## 参考文献

1. steipete/CodexBar 仓库 README（main 分支，2026-10-03 读取）
2. docs/cli.md、docs/cli-configuration.md、docs/architecture.md、docs/providers.md、docs/codex.md、docs/claude.md（main 分支，2026-10-03 读取）
3. GitHub API `repos/steipete/CodexBar`：22,140 Stars / 2,036 Forks / MIT / Swift（2026-10-03 查询）
4. GitHub API `repos/steipete/CodexBar/releases/latest`：v0.71.0，2026-10-02 发布
5. [codexbar.app](https://codexbar.app)（项目官网）

---

如果你已经被"我今天还能跑多少"这个问题骚扰过不止一次，CodexBar 是当前摩擦最低的答案：装上，复用既有登录，看一眼菜单栏，前后不超过五分钟。
