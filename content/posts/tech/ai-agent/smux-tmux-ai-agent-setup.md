---
title: "smux：一键 tmux 配置，让 AI Agent 操控终端"
date: "2026-03-29T21:10:00+08:00"
lastmod: "2026-09-24T01:10:00+08:00"
slug: "smux-tmux-ai-agent-setup"
github_repo: "ShawnPana/smux"
source_key: "gh:ShawnPana/smux"
aliases:
  - /posts/tech/smux-tmux-ai-agent-setup/
description: "深入解读 smux 项目，一键配置 tmux 环境，支持 Option 键绑定、鼠标操作、窗格标签，并提供 tmux-bridge CLI 实现 AI Agent 间的跨窗格通信。"
draft: false
categories: ["技术笔记"]
tags: ["终端", "AI Agent", "自动化", "Claude Code"]
---

# smux：一键 tmux 配置，让 AI Agent 操控终端

AI Agent 正在搬进终端：Claude Code、Codex、Gemini CLI 一开就是好几个窗格。tmux 本该是它们的天然舞台——多窗格、可分离、会话可复连——但默认形态对人和机器都不算友好。人类要先按 Ctrl-b 前缀，再记一串单字母快捷键；Agent 侧则没有现成的跨窗格接口，想让 Claude Code 把任务递给隔壁窗格的 Codex，得自己拼 `tmux send-keys` 和 `capture-pane`。

[smux](https://github.com/ShawnPana/smux) 的答案是"一份配置加一个脚本"。给人类的 `.tmux.conf` 把高频操作全部改绑 Option 键，免前缀，一步直达；给 Agent 的 `tmux-bridge` 提供 `read`、`type`、`keys`、`message` 等原子命令，任何能执行 shell 命令的 Agent 都能读写任意窗格、互发消息。全部代码只有一个 2.7 KB 的 tmux 配置、一个 11 KB 的 shell CLI 和一份教 Agent 用法的 Skill 文档，没有后台服务，装完即用。

## 学习目标

读完本文后，你应该能：

1. 用一条命令装好 smux，说清它装了什么、装在哪、怎么卸载，包括旧配置的备份与恢复路径。
2. 说出常用的 Option 键位（窗格导航、开关、布局、标记交换），并解释"免前缀"设计对人与 Agent 共用终端的意义。
3. 用 `tmux-bridge` 的 `list`/`read`/`type`/`keys` 四个命令完成一次跨窗格操作，并解释"先读后写"守卫为什么存在。
4. 用 `message` 命令在两个 Agent 之间发起一轮带发送者头的问答，按 read-act-read 循环收尾。
5. 判断自己的工作流是否需要 smux：单 Agent 用户与多 Agent 协作用户的收益差异。

---

## 一、项目概述

### 1.1 是什么

smux 的官方定位是"内置终端自动化与 Agent 间通信的 tmux 配置"（tmux config with built-in terminal automation and agent-to-agent communication）。它同时服务两端：

- **人类侧**：一份 `.tmux.conf`，提供 Option 键绑定、鼠标支持、窗格标签和极简状态栏；
- **Agent 侧**：`tmux-bridge` CLI，让任何 Agent 都能读取、写入、控制任意 tmux 窗格。

### 1.2 两套机制，一次装好

这两套机制独立工作，又在一个点上交汇——窗格标签：

| | 人类侧 | Agent 侧 |
|---|---|---|
| 载体 | tmux 配置（键位与外观） | tmux-bridge CLI（shell 脚本） |
| 入口 | Option 组合键，免前缀 | `tmux-bridge <命令>` |
| 典型操作 | 分屏、切换、滚动、复制 | 读窗格、输入文本、发按键、贴标签 |

两套机制在一个点上交汇：窗格标签。`name` 命令写入的标签会显示在窗格边框上——人看得见，Agent 拿它当寻址入口。

### 1.3 项目数据

以下为 2026-09-24 GitHub API 读数：

- ⭐ 1,529 Stars | 89 Forks | 29 Commits
- 语言：Shell 100%
- 许可证：MIT
- 版本：install.sh v1.0.0，tmux-bridge v2.0.0（无正式 release tag）
- 作者 ShawnPana 独立维护；29 个提交中 14 个带 Claude 协作署名（Co-Authored-By），是典型的"人机结对"仓库

---

## 二、安装与配置

### 2.1 一键安装

```bash
curl -fsSL https://shawnpana.com/smux/install.sh | bash
```

这条链接会 302 跳转到仓库的 raw 文件。脚本做的事，按 install.sh（v1.0.0）的执行顺序：

1. 识别操作系统（仅 macOS 与 Linux）；tmux 缺失时用 brew/apt/dnf/pacman/apk 自动安装，macOS 上必须有 Homebrew。建议 tmux 3.2+，版本不足只警告不阻断。
2. Linux 上若没有 xclip/xsel，自动装 xclip（鼠标拖选复制到系统剪贴板要用）。
3. 把 tmux.conf 和 tmux-bridge 下载到 `~/.smux/`，并把 `~/.smux/bin` 写进 shell rc 文件的 PATH。
4. 备份已有配置：`~/.config/tmux/tmux.conf` 与老式的 `~/.tmux.conf` 都会带时间戳备份到 `~/.smux/backups/`。
5. 建软链 `~/.config/tmux/tmux.conf → ~/.smux/tmux.conf` 生效——不覆盖你的 `~/.tmux.conf`；正在运行的 tmux 会话会自动重载配置。

装完后的目录布局：

```text
~/.smux/
├── tmux.conf        # tmux 配置本体
├── bin/tmux-bridge  # 跨窗格通信 CLI
├── bin/smux         # 管理命令（install.sh 本身的另一个名字）
└── backups/         # 配置备份
```

### 2.2 更新与卸载

```bash
smux update      # 重新拉取 tmux.conf 与 tmux-bridge
smux uninstall   # 删除软链与 ~/.smux/，并恢复最近一份备份
```

注意：卸载会自动还原最近一份备份配置，但写进 shell rc 的那一行 PATH 需要手动删。

---

## 三、为人类设计的键盘流

tmux 的默认交互围绕 Ctrl-b 前缀展开：先按前缀，再按功能键，两步才能完成一个动作。smux 把高频操作全部改绑 Option（Alt）键，不用前缀，一步直达。

**窗格操作**

| 按键 | 动作 |
|---|---|
| `Option+i/k/j/l` | 上下左右切换窗格（到边界不环绕） |
| `Option+n` | 新建窗格（水平分割并自动平铺） |
| `Option+w` | 关闭当前窗格 |
| `Option+o` | 轮换布局 |
| `Option+g` / `Option+y` | 标记窗格 / 与标记的窗格交换位置 |

**窗口操作**

| 按键 | 动作 |
|---|---|
| `Option+m` | 新建窗口 |
| `Option+u` / `Option+h` | 下一个 / 上一个窗口（到边界不环绕） |

**滚动**

| 按键 | 动作 |
|---|---|
| `Option+Tab` | 进入 / 退出滚动模式 |
| `i` / `k` | 上 / 下滚动（每次两行） |
| `Shift+I` / `Shift+K` | 上 / 下翻半页 |
| `q` 或 `Escape` | 退出滚动模式 |

**鼠标**：点击选窗格，拖选即复制（自动送系统剪贴板，macOS 走 pbcopy，Linux 走 xclip/xsel），滚轮直接滚动，滚到底自动退出滚动模式。

外观上还有几处顺手的默认：回滚缓冲 1 万行；活动窗格红色边框；窗格顶部边框显示标签（没打标签就显示当前目录名）；状态栏只留窗口号和名字，当前窗口红色加粗，两侧留空；`allow-rename off` 保证窗口名不被运行的程序改来改去。

用 [Ghostty](https://github.com/ShawnPana/smux/tree/main/ghostty) 终端的用户，仓库还附带一份同套键位的 `ghostty/config`（2026 年 5 月加入），把 alt+j/l/i/k 等映射对齐到 tmux 侧，两个终端里的肌肉记忆一致。

---

## 四、tmux-bridge：给 Agent 的终端接口

tmux-bridge 的设计原则是**命令原子化**：`type` 只打字不回车，`keys` 只发按键，`read` 只读内容。没有"一发入魂"的 send 命令——每一步之间都可以（后面会看到，某些步骤之间是必须）插入 `read` 验证。

完整命令集（按源码 v2.0.0 的 usage 列出）：

| 命令 | 作用 |
|---|---|
| `tmux-bridge list` | 列出所有窗格：目标、会话：窗口、尺寸、进程、标签、当前目录 |
| `tmux-bridge read <目标> [行数]` | 读窗格最后 N 行（默认 50） |
| `tmux-bridge type <目标> <文本>` | 向窗格输入文本，不含回车 |
| `tmux-bridge keys <目标> <键>...` | 发送特殊键（Enter、Escape、C-c 等） |
| `tmux-bridge message <目标> <文本>` | 输入文本并自动附加发送者信息头（别名 `msg`） |
| `tmux-bridge name <目标> <标签>` | 给窗格贴标签（显示在窗格边框上） |
| `tmux-bridge resolve <标签>` | 由标签反查窗格目标 |
| `tmux-bridge id` | 打印自己所在窗格的 ID |
| `tmux-bridge doctor` | 诊断 tmux 连通性 |
| `tmux-bridge version` | 打印版本 |

**目标怎么写**：可以是 tmux 原生格式——窗格 ID（`%3`）、`会话:窗口.窗格`（`shared:0.1`）、纯数字窗口号——也可以是 `name` 设置的标签。标签解析自动完成，所以 `tmux-bridge type codex "hello"` 能直接工作。

**底层怎么找 tmux**：CLI 依次尝试 `TMUX_BRIDGE_SOCKET` 环境变量、`$TMUX` 里的 socket，再扫描 `/tmp/tmux-<uid>/` 下的所有 socket，最后才落到默认 server。Agent 的执行环境里 `$TMUX` 经常失效（终端重启、子 shell 继承），这套探测加 `doctor` 命令就是为这种情况准备的。

`list` 输出里还有一个贴心细节：进程列会往下追一层子进程，所以在窗格里跑着的 `claude` 或 `node` 会被直接认出来，而不是只显示外层 shell。

---

## 五、先读后写：守卫与消息协议

### 5.1 读后写守卫

tmux-bridge 在 CLI 层强制执行"先读后写"：`type`、`keys`、`message` 之前必须先 `read` 过目标窗格，否则直接报错：

```bash
$ tmux-bridge type codex "hello"
error: must read the pane before interacting. Run: tmux-bridge read codex
```

实现很朴素：`read` 时在 `/tmp/tmux-bridge-read-<窗格ID>` 落一个标记文件，写入类命令检查这个标记，动作成功后标记清除。也就是说，**每一次交互都必须以一次新的观察开始**——Agent 不能凭上一次的记忆盲发按键。

### 5.2 read-act-read 循环

官方 Skill 文档把标准交互固化成四步：

```bash
tmux-bridge read codex 20       # 1. 读——满足守卫，顺便看对方当前状态
tmux-bridge message codex 'Please review src/auth.ts'
                                # 2. 发——自动附加发送者头
tmux-bridge read codex 20       # 3. 读——确认文本已经落上去
tmux-bridge keys codex Enter    # 4. 提交
# 到此停手。不要 sleep，不要轮询，不要反复读对方窗格等回复。
```

最后那条纪律值得展开。`type` 和 `keys` 分开、中间夹一次 `read`，是因为输入和提交之间可能隔着手滑和 TUI 渲染时差；而"发完就停"则源于下一条协议。

### 5.3 回复协议：头里带着回信地址

`message` 命令会在文本前面自动加一个头。收方 Agent 看到的是这样一行：

```text
[tmux-bridge from:claude pane:%4 at:3:0.0] Please review src/auth.ts
```

头里带了三样东西：谁发的（`from`），回信送到哪个窗格（`pane`），发送者位于哪个会话、哪个窗口（`at`）。甚至还有一句直接写给收方 Agent 的指令——源码里的头文本以 "load the smux skill to reply" 结尾。

协议的另一半是**禁止轮询**：对端 Agent 会主动把回复 `message` 回你的窗格，所以发完消息的 Agent 应该直接去干别的事，回复会自己出现在你的输入行里。等待、sleep、循环读对方窗格都是协议明确禁止的动作——这把多 Agent 协作从"轮询问题"变成了"收件箱问题"。

### 5.4 非 Agent 窗格是例外

对端是普通进程（跑着测试的窗格、等待确认的部署脚本）时，没有 Agent 来主动回话，就得自己读结果。官方给的最小审批示例：

```bash
tmux-bridge read worker 10     # 看清提示在问什么
tmux-bridge type worker "y"    # 输入确认
tmux-bridge read worker 10     # 确认字符落上去了
tmux-bridge keys worker Enter  # 提交
tmux-bridge read worker 20     # 自己读结果——非 Agent 窗格必须如此
```

---

## 六、实战：Claude Code 与 Codex 跨窗格协作

把前面的机制串成一个完整场景：上半窗格跑 Claude Code，下半窗格跑 Codex，让 Claude Code 委托 Codex 审查一段代码。

留给人类的工作只有一次布置：

```bash
# 终端上半格
claude

# 终端下半格
codex
```

之后的事发生在 Claude Code 里。它先自报家门、摸清环境：

```bash
tmux-bridge name "$(tmux-bridge id)" claude   # 给自己贴标签，方便对端回信
tmux-bridge list                              # 列出所有窗格，找到 codex 的目标
```

然后发起委托：

```bash
tmux-bridge read codex 20
tmux-bridge message codex 'Please review the changes in src/auth.ts'
tmux-bridge read codex 20
tmux-bridge keys codex Enter
# 停手，去干别的事。回复会出现在 Claude Code 自己的窗格里。
```

Codex 那边，这条消息以上文 5.3 节的格式出现在它的输入行。它按头里的 pane ID 回信：

```bash
tmux-bridge read %4 20
tmux-bridge message %4 '87% line coverage. Missing the OAuth refresh token path (lines 142-168).'
tmux-bridge read %4 20
tmux-bridge keys %4 Enter
```

一轮问答结束：Claude Code 的窗格里多出一行审查结论，Codex 回到空闲。同样的循环可以拉长成流水线——主 Agent 出测试计划，子 Agent 写测试、跑测试，结果回流汇总——分工怎么变，通信模式都是同一条 read-act-read 循环。

---

## 七、AI Agent Skills：让 Agent 自己学会用

人类可以读完本文再上手，Agent 的路径是装一个技能文档：

```bash
npx skills add ShawnPana/smux
```

README 的口径是它兼容 Claude Code、Codex、Cursor、Copilot 等 40 余种 Agent——这里的 40+ 指的是 skills 安装器（skills.sh 生态）能往多少种 Agent 的配置目录里写入技能。tmux-bridge 本身不挑 Agent：判断标准只有一条，能不能执行 shell 命令。

装进来的技能包含 SKILL.md 主文档和 references/ 下两份参考（tmux-bridge 命令详解、原始 tmux 命令手册）。主文档的 frontmatter 写明了触发条件：用户提到 tmux 窗格、跨窗格通信、给其他 Agent 发消息、读取别的窗格时加载。正文教的除了命令全集，还有前面第五节的全部纪律——守卫是强制的、禁止等待轮询、标签要趁早贴、`type` 是字面模式、原始 `tmux` 命令只在需要低阶控制时兜底。frontmatter 里还声明了运行要求：需要 tmux 与 tmux-bridge 两个可执行文件，支持 macOS 与 Linux。

这样一来，人类只装一次技能，之后每个 Agent 在需要时自己读文档、自己遵守协议。

---

## 八、常见问题

### Q：为什么用 Option 键而不是 Ctrl 系？

A：tmux 默认的 Ctrl-b 前缀要两步，而 Option/Alt 组合在终端里被交互式程序占用的比例低，冲突相对少。免前缀、一步直达是 README 明说的设计目标（"no prefix required"），绑到 Option 上是实现这个目标的自然选择。

### Q：tmux-bridge 安全吗？

A：它本身只做三件事——`capture-pane` 读、`send-keys` 写、`set-option` 贴标签，全部经由 tmux 的 Unix socket 完成，不直接碰文件系统和网络，跨用户不可达。但要清楚"写"意味着什么：打进目标窗格的文本会被那个窗格里的 shell 当作命令执行，把键盘交给 Agent，等于把键盘交给它要操控的窗格。读后写守卫强制每轮交互前先观察，避免了盲操作；在此基础上，建议只在受信任的环境里放开使用。

### Q：支持 Windows 吗？

A：官方支持 macOS（装 tmux 需要 Homebrew）和 Linux。install.sh 按 `uname` 只识别这两种系统。Windows 用户可在 WSL 里使用——WSL 对脚本而言就是 Linux。

### Q：连不上 tmux 怎么调试？

A：先跑 `tmux-bridge doctor`。它会依次检查环境变量、socket 健康度、当前窗格对 server 的可见性、窗格总数。最常见的故障是终端重启后 `$TMUX` 环境变量过期，doctor 会给出提示，兜底办法是设置 `TMUX_BRIDGE_SOCKET` 显式指定 socket 路径。`tmux-bridge list` 则用来确认窗格目标和标签是否如你所想。

### Q：和直接用 tmux send-keys/capture-pane 有什么区别？

A：raw tmux 命令当然可行，tmux-bridge 在其上包了四层：socket 自动探测（Agent 环境里 `$TMUX` 不可靠）、标签寻址（不用记 `%N`）、读后写守卫（raw 命令没有的纪律层）、`message` 消息协议（带发送者头的约定）。需要会话管理、窗口操作这类低阶控制时，Skill 文档也给了 raw 命令的完整参考。

---

## 九、总结与采用建议

smux 用不到八百行 shell（tmux-bridge 一个脚本占 400 来行）把"AI Agent 操控终端"从拼命令的手艺变成了标准接口：人类得到一套免前缀的 tmux 键位，Agent 得到一个带纪律约束（先读后写、禁止轮询）的通信协议，两边通过窗格标签共用同一套地址系统。

**建议现在就用**：同时跑两个以上 coding Agent、需要它们互相评审或分工的人；想把子任务派给后台窗格的主 Agent 使用者；以及重度 tmux 用户——就算不用 Agent 功能，这套免前缀键位本身也值回安装时间。

**可以再等等**：单 Agent 工作流已经够用的人（Claude Code 自带的子代理机制能覆盖大部分分派需求）；Windows 原生环境；对 `curl | bash` 敏感的团队——脚本只有 8 KB 且 Shell 100%，先读后装不难，也可以 fork 一份自己维护。

**采用顺序**：先装配置部分当顺手的 tmux 配置用几天；需要程序化操控终端时，从 `list`/`read`/`type`/`keys` 四个命令起步；真要 Agent 间协作，再 `npx skills add`，把文档交给 Agent 自己读。

一个现实边界：仓库 2026-02-28 创建，单人维护，无正式 release tag，接口随 main 分支演进——tmux-bridge 从 v1 到 v2.0.0，`message` 和 `doctor` 都是后加的命令。引用具体行为时留意版本，或者钉住某个 commit。

---

## 十、资源链接

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | https://github.com/ShawnPana/smux |
| 官方安装脚本 | https://shawnpana.com/smux/install.sh |
| smux Skill | `npx skills add ShawnPana/smux` |
| tmux 官网 | https://tmux.github.io/ |
| Homebrew | https://brew.sh/ |

---

## 参考来源与口径说明

- 本文 2026-03-29 首发，2026-09-24 按仓库 main 分支全面复核重写：机制描述逐一对照 raw.githubusercontent.com 上的 README、install.sh（v1.0.0）、`.tmux.conf`、`scripts/tmux-bridge`（v2.0.0）与 skills/smux/ 全套文档。
- Stars、Forks、提交数为 2026-09-24 GitHub API 读数（1,529 / 89 / 29）；首发时读数为 393 / 21 / 24。仓库创建于 2026-02-28，最近推送 2026-08-26。语言占比与许可证（Shell 100%、MIT）同日核实。
- tmux-bridge v2.0.0 的命令集比仓库 README 表格多 `message` 与 `doctor` 两个，本文按源码 usage 全集列出。
- skills/smux/references/tmux-bridge.md 参考文档仍写"手动拼 `[tmux-bridge from:]` 头"的旧约定，与 SKILL.md 及 CLI 源码不一致（现为 `message` 命令自动加头），本文以源码为准。
- 第六节示例对话中的 "87% line coverage" 为 SKILL.md 官方教学示例数字，非实测结果。
- "兼容 40+ 种 Agent"为仓库 README 对 skills.sh 生态兼容面的表述；tmux-bridge 本身的兼容判据是能否执行 shell 命令（README 原话 "Any tool that can run bash can use it"）。
- 外链核实：安装脚本链接 302 跳转至 raw.githubusercontent.com 后正常返回；tmux.github.io、brew.sh、skills.sh、GitHub 仓库与 Sponsor 页均为 200。
