---
title: "Kaku：把 WezTerm 调校成开箱即用的 AI 编码终端"
date: "2026-04-07T17:15:00+08:00"
lastmod: 2026-10-01
slug: kaku-ai-native-terminal-built-for-ai-coding
github_repo: "tw93/Kaku"
source_key: "gh:tw93/Kaku"
description: "Kaku 是 tw93 基于 WezTerm 引擎打造的 macOS 终端：字体、主题、快捷键、shell 工具全部预设好，AI 助手接你自己的 OpenAI 兼容服务。本文按 V0.21.0 拆解它的默认体验、AI 助手机制与交付工程。"
categories: ["技术笔记"]
tags: ["终端", "Rust", "AI 编程", "macOS", "WezTerm"]
draft: false
---

# Kaku：把 WezTerm 调校成开箱即用的 AI 编码终端

## 核心判断

终端这个品类不缺好引擎，缺的是开箱即用。WezTerm 的渲染和多路复用能力公认扎实，但想用得舒服，你得自己攒字体、配色、快捷键和 shell 插件。tw93（Pake、Mole 的作者）做的 Kaku 就是把这一步替你走完：保留 WezTerm 引擎和完整的 Lua 配置能力，把字体、主题、快捷键、shell 工具全部预设好，再内置一个接你自己 API 服务的 AI 助手。仓库简介的定位是一句话：`A fast, out-of-the-box macOS terminal built for AI coding`。

有一个容易误读的点先说清：Kaku 早期 README 自述是 WezTerm 的"deeply customized fork"，但 GitHub 上 `tw93/Kaku` 是一个独立仓库（2026 年 2 月 7 日创建，并非 fork 关系），fork 指的是代码派生——Kaku 继承了 WezTerm 的引擎代码，独立发布版本。

项目节奏很快：2026 年 2 月创建，4 月初发布 V0.9.0，到 9 月底已迭代到 V0.21.0，GitHub Releases 上累计 29 个发布（含 nightly 通道）。这半年里它的重心也在变化：早期宣传集中在"比上游轻"，现在 README 里已经没有性能对比表，取而代之的是会话恢复、诊断工具、后台更新这类交付工程。判断一个终端值不值得换，这些比体积数字更实在。

| 指标 | 数值（2026-10-01 读数） |
|------|------|
| Stars / Forks | 6,048 / 314 |
| 许可证 | MIT |
| 主语言 | Rust（约 97%，另有 Shell、Lua） |
| 最新版本 | V0.21.0（2026-09-26） |
| 提交数 / 贡献者 | 1,682 / 56 |
| 平台 | 仅 macOS |
| 官网 | [kaku.fun](https://kaku.fun) |

## 系统地图：WezTerm 引擎之上加了什么

仓库的 [AGENTS.md](https://github.com/tw93/Kaku/blob/main/AGENTS.md) 给出过一份官方目录地图，按"继承"和"新增"归类后是这样的：

| 层 | 目录 | 职责 |
|---|---|---|
| 继承自 WezTerm | `mux/`、`term/`、`termwiz/`、`window/` | 多路复用（标签/分屏/域）、终端仿真与屏幕缓冲、终端 UI 原语、平台窗口层 |
| 继承自 WezTerm | `config/`、`lua-api-crates/` | Lua 配置加载与版本化默认值、Rust 到 Lua 的 API 绑定 |
| Kaku 新增 | `kaku/` | `kaku` 命令行入口（init/doctor/ai/chat/config 等） |
| Kaku 新增 | `kaku-gui/` | GUI、渲染、窗口生命周期、AI 聊天，以及 `k` 助手二进制 |
| Kaku 新增 | `crates/kaku-ai-utils` 等 | AI 辅助相关的共享工具 crate |
| 交付层 | `assets/`、`docs/`、`.agents/skills/` | 内置默认配置（`Kaku.app/Contents/Resources/kaku.lua`）、文档、面向 AI 代理的项目技能 |

CI 侧同样是交付工程的体现：`checks.yml` 在 macOS 上跑五道门（格式、单测、Relay 构建、Clippy、脚本与发布检查），发布构建用专门的 `release-opt` profile，产物对 `kaku`、`kaku-gui`、`k` 三个二进制做 `lipo` 合并以支持通用二进制。

## 开箱即用，预设的到底是什么

Kaku 的默认值不是"能用"，是按日常编码场景调过的：

- **字体**：JetBrains Mono，CJK 回退 PingFang SC；连字默认关闭（需要时置空 `config.harfbuzz_features` 恢复）。字号按显示器自适应：低分辨率 15px、高分辨率 17px，行高默认 1.28。
- **主题**：新安装默认 Kaku Dark；如果配置里不写 `color_scheme`，则跟随 macOS 外观在 Kaku Dark / Kaku Light 之间自动切换。
- **行为**：选中即复制、`Cmd + Click` 打开 URL 和文件路径（带行号的路径可配置 `file_link_editor` 直接跳进编辑器）、后台标签完成时显示琥珀色圆点提示。
- **Smart Tab**：zsh 里重定义 Tab 键，默认"先接受自动建议、无建议再出补全列表"，可切换为"补全优先"或完全关闭；用环境变量设置时优先级高于 `kaku.lua`。
- **shell 套件**：内置 z 插件（目录跳转）、zsh-completions、zsh-syntax-highlighting、zsh-autosuggestions；fish 用户跑 `kaku init` 生成集成脚本。Starship、Delta、Lazygit、Yazi 四个可选工具由 `kaku init` 通过 Homebrew 安装。

快捷键是标准 Mac 习惯，高频部分如下（完整表见 [docs/keybindings.md](https://github.com/tw93/Kaku/blob/main/docs/keybindings.md)）：

| 操作 | 快捷键 |
|---|---|
| 新建标签 / 窗口 | `Cmd + T` / `Cmd + N` |
| 垂直 / 水平分屏 | `Cmd + D` / `Cmd + Shift + D` |
| 切换标签 / 分屏 | `Cmd + Shift + [` `]`、`Cmd + 1-9` / `Cmd + Opt + 方向键` |
| 清屏（含回滚缓冲） | `Cmd + K` |
| 设置 / 命令面板 | `Cmd + ,` / `Cmd + Shift + P` |
| AI 设置面板 / AI 聊天 | `Cmd + Shift + A` / `Cmd + L` |
| 应用 AI 建议 | `Cmd + Shift + E` |
| Lazygit / Yazi | `Cmd + Shift + G` / `Cmd + Shift + Y` 或 `y` |
| 挂载远程目录（SSH + sshfs） | `Cmd + Shift + R` |

一个贴心的细节：V0.10.0 起智能关闭保护生效——`Cmd + W` 关掉的 pane 里如果跑着 claude、codex、vim、cargo 这类非 shell 进程，会先询问再关；裸 shell 依然静默关闭。

## Kaku AI：接自己的服务，而不是绑定某家

Kaku 内置的 AI 助手不代理任何模型服务，官方原话是"Kaku does not provide or relay the AI service"——它只是把你的 OpenAI 兼容端点接进终端。所有 AI 设置通过 `kaku ai` 面板配置，落盘在 `~/.config/kaku/assistant.toml`。顺带澄清一个流传较广的错误写法：网上一些解读文给出的 `config.kaku_ai_provider`、`config.kaku_ai_api_key` 之类 Lua 配置键并不存在，源码里查无此键，AI 配置从来不在 `kaku.lua` 里。

助手分两个模型档位，按任务分工：

- **Simple Model**：`#` 命令生成、命令修复、轻量聊天。
- **Deep Model**：`Cmd + L` 聊天面板和工具调用的主力模型。面板内 `Shift + Tab` 可在两档间切换。

三个具体能力：

**错误恢复**。命令以非零状态退出时，助手把失败命令、退出码、工作目录和 git 分支一起发给 LLM，在终端内联显示修复建议，按 `Cmd + Shift + E` 把建议粘贴到提示符。注意是"粘贴供审阅"而不是自动执行——`rm -rf`、`git reset --hard` 这类危险命令也只粘贴、绝不自动回车。触发同样有边界：`Ctrl + C` 中断、help 标志、裸包管理器调用、git pull 冲突、非 shell 前台进程都不触发，避免噪音。

**自然语言转命令**。在提示符输入 `# <描述>` 回车，Kaku 在 shell 读到这行之前拦截，连同当前目录和 git 分支发给模型，把生成的命令放回提示符等你确认。zsh 和 fish 都支持；模型给不出安全命令时，注入的是一句解释而不是硬凑的命令。

**聊天面板与 CLI 同源**。`Cmd + L` 打开的聊天面板支持 Markdown 流式渲染、代码高亮、携带终端上下文，还能调用工具读写项目文件、执行 shell 命令、联网搜索和维护记忆。`k` 或 `kaku chat` 从任意 shell（包括 SSH 会话）进入同一个会话存储，是同一个引擎的 TUI 形态。

接入方式上有两类值得展开：

- **Follow Codex 认证**：`auth_type` 设为 `codex` 时，Kaku 直接复用本机 Codex CLI 的登录态（读 `CODEX_HOME`，默认 `~/.codex`），包括 API key 或 ChatGPT 登录、所选 provider、Base URL 和请求头。项目级配置、命名 profile、命令行覆盖被有意排除在外，避免理解成本。
- **API Mode**：默认 `chat_completions`；provider 支持 `/responses` 端点时可切到 `responses`，并开启 provider 托管的 `native_web_search`，无需另配搜索服务的 key。自托管搜索也可选 `brave`、`pipellm` 或 `tavily`。企业代理可加自定义请求头（`Authorization` 和 `Content-Type` 保留不可覆盖）。

Provider 支持这半年收缩过一次：V0.9.0 时代有 OpenAI（推荐 gpt-5.4-mini）和 MiniMax（推荐 MiniMax-M2.7，1M 上下文）的预设下拉，V0.10.0 移除了 Gemini 预设；按当前源码，具名识别只剩 Copilot 和 Codex，其余一律按 Custom 处理，模型名手动填。这符合"接你自己的服务"的定位——预设越少，兼容面越广。

## 一次命令失败后发生了什么

把上面的机制串成一条完整链路。假设 `npm run build` 因缺依赖失败：

1. 进程以非零码退出，Kaku 捕获失败命令、退出码、当前工作目录、git 分支四项上下文；
2. 若启用了 Kaku Assistant，这四项发给你在 `assistant.toml` 里配置的 Simple Model；
3. 模型返回的修复命令（比如 `npm install express`）以内联形式显示在终端里；
4. 你按 `Cmd + Shift + E`，命令被粘贴到提示符——注意此刻它还没有执行；
5. 回车前你有完整的审阅机会；如果建议是 `rm -rf` 级别的危险命令，它被标记出来，且无论怎么按都不会自动执行。

整条链路的关键设计是"建议永远停在审阅态"。终端里跑 AI 助手最大的风险是把不可逆操作交给了模型，Kaku 把自动化的边界画在粘贴这一步，而不是执行那一步。

## 性能数字怎么读

Kaku 早期 README（V0.9.0 口径）登过一张与上游 WezTerm 的对比表：可执行文件约 67 MB 对约 40 MB（手段是符号剥离与功能修剪）、资源文件体积约 100 MB 对约 80 MB（资源优化与懒加载）、shell 启动约 200ms 对约 100ms。标题里常见的"比 WezTerm 小 40%"就是从这张表来的。

读这张表有两点提醒。其一，"资源占用"是当年一些解读文对 "Resources Volume" 的误读——它指的是资源文件的磁盘体积，不是运行内存。其二，当前 README 已经撤下了这张表，这些数字只能当 V0.9.0 时期的历史口径看。性能优化的工程动作是真实的：V0.10.0 的更新日志列了 Lua 字节码缓存、延迟字体与配置初始化、缓存 shell 用户变量等启动优化。合理的使用方式是把"比上游小、启动快"当方向判断，具体数字以自己机器实测为准。

## 配置：改什么、怎么改才不翻车

Kaku 首次启动会自动生成 `~/.config/kaku/kaku.lua`，这个文件先加载内置的 Kaku 默认值，再把你的覆盖叠上去：

```lua
local wezterm = require 'wezterm'

local function resolve_bundled_config()
  local resource_dir = wezterm.executable_dir:gsub('MacOS/?$', 'Resources')
  local bundled = resource_dir .. '/kaku.lua'
  local f = io.open(bundled, 'r')
  if f then f:close(); return bundled end
  return '/Applications/Kaku.app/Contents/Resources/kaku.lua'
end

local config = {}
local bundled = resolve_bundled_config()
if bundled then
  local ok, loaded = pcall(dofile, bundled)
  if ok and type(loaded) == 'table' then config = loaded end
end

-- 你的覆盖写在这里：
config.font_size = 16
config.window_background_opacity = 0.95

return config
```

这个结构有一条纪律：**别用全新的表整体替换 config**。网上不少教程演示过直接 `return { font = ..., color_scheme = ... }` 的写法——那会把 Kaku 预设的全部默认值抹掉，回到裸 WezTerm 状态。官方 FAQ 给的简写是 `local config = require("kaku").config`，效果等同。

自定义快捷键同理：向 `config.keys` 追加（`table.insert`），不要赋值新表，否则 Kaku 的默认键位全部丢失：

```lua
table.insert(config.keys, {
  key = 'RightArrow',
  mods = 'CMD|SHIFT',
  action = wezterm.action.ActivatePaneDirection('Right'),
})
```

常用覆盖的官方示例：透明窗口是 `config.window_background_opacity = 0.92`（0-1 之间的不透明度），可选配 `config.macos_window_background_blur = 20`；换主题写 `config.color_scheme = "Kaku Light"`；关闭选中即复制是 `config.copy_on_select = false`。恢复默认配置用 `kaku reset`——它只清 Kaku 托管的集成与主题块，你自己写的 Lua 会保留。

## 交付工程：这个仓库第二值得读的部分

对想做自托管或桌面软件的工程师，Kaku 的运维链路和终端功能一样有参考价值：

- **kaku doctor**：一条命令体检应用包、PATH、shell 集成。每次运行都会产出诊断包 `~/.local/share/kaku/diagnostics/Kaku-Diagnose.zip`（报告、日志、崩溃记录、GUI 卡顿样本），生成前先脱敏——home 路径、主机名、MAC 地址、序列号和疑似凭据的值都会替换，`assistant.toml` 完全不读，数据不出本机。报 issue 时附上这个 zip 就够。
- **更新策略**：后台每 3 小时（默认 `check_for_updates_interval_seconds = 10800`）检查新版本并静默下载，但永不自动安装——弹通知，点确认才升级，因为升级会关闭所有窗口和运行中的任务。手动 `kaku update` 随时可用。
- **会话恢复**：窗口快照在关闭或隐藏时自动保存，崩溃或强制退出后也能找回最近布局；`Cmd + Opt + Shift + T` 恢复上一次快照，启动时默认重开上次的标签、分屏和工作目录。
- **分发**：V0.21.0 进了 Homebrew 官方 cask（`brew install --cask kaku`），此前需用个人 tap（V0.9.0 时代是 `brew install tw93/tap/kakuku`，老用户不受影响）；应用经 Apple 公证，DMG 拖入即用，无安全警告。

## 和同类终端比，什么时候选它

官方 [compare 页](https://kaku.fun/compare)的口径（注意这是项目方自己的对比，竞品描述以其官方文档为准）：iTerm2 强在多年积累的配置生态，已有顺手配置的用户没必要迁；Warp 把 AI 代理跑在自己的服务器上，付费计划 $20/月起，Kaku 则是无账号、AI 可选且用你自己的服务；Ghostty 是极快的 GPU 终端，但没有预设好的那套工具链；WezTerm 是 Kaku 的上游，需要 Windows 或 Linux 时直接用 WezTerm。

不适合 Kaku 的场景，官方也列得直白：需要 Windows/Linux（暂无时间表）；需要托管或浏览器终端；需要 API、SDK 或 MCP 服务器形式的自动化（它的自动化面只有本地 `kaku cli`，比如 `kaku cli split-pane` 可以从脚本里开分屏）；或者你就是要 iTerm2/WezTerm 的完整能力复刻——Kaku 明确不追求这个。

## 采用建议

安装到可用只需三步：

```bash
brew install --cask kaku   # 或从 GitHub Releases 下载 DMG
kaku doctor                # 体检 shell 集成是否就位
kaku ai                    # 配置你的 API 端点与模型
```

两类人可以现在就换：在 macOS 上重度使用终端、想直接获得一套调好的 AI 编码环境的人；手里已经有一堆 WezTerm Lua 配置、想要更省心的默认值的人（配置基本兼容，渐进迁移即可）。可以再等等的：需要跨平台、依赖 iTerm2 深度功能（如 TMUX 集成外的复杂触发器体系）、或者对 AI 助手有强定制需求（MCP、多代理编排）的团队——Kaku 的 AI 面做得刻意克制，它守住的是"终端内顺手"这条线，而不是做大而全的 agent 平台。

项目地址：[tw93/Kaku](https://github.com/tw93/Kaku)
