---
title: "Claude HUD：实时显示 Claude Code 状态的智能仪表盘"
date: "2026-03-29T15:50:00+08:00"
lastmod: "2026-09-22T10:00:00+08:00"
slug: "claude-hud-realtime-status-dashboard"
github_repo: "jarrodwatts/claude-hud"
source_key: "gh:jarrodwatts/claude-hud"
aliases:
  - /posts/tech/claude-hud-realtime-status-dashboard/
description: "Claude HUD 是 28k+ Stars 的 Claude Code 插件，实时显示上下文使用量、工具活动、智能体状态、Git 信息，让 AI 编程过程一目了然。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "AI 编程", "终端工具"]
---

# Claude HUD：实时显示 Claude Code 状态的智能仪表盘

> 预计阅读时间：20 分钟 | 难度：⭐⭐

用 Claude Code 干活的人大多遇到过同一个尴尬：AI 在终端里安静地跑着，你看不到上下文还剩多少、它正在读哪个文件、子智能体跑到哪一步——直到会话突然被压缩或打断，才发现上下文早就满了。**Claude HUD 把这些状态搬到了终端输入框下方，常驻显示**。它不发明新协议、不依赖 tmux，只在 Claude Code 原生 statusline API 上做了一层精细的渲染，属于典型的"小工具解决真问题"。

读完本文你能做三件事：装好插件让状态栏常驻、读懂默认的两行显示、按需开关每个模块并在显示异常时自己定位原因。

本文以 2026 年 8 月发布的 v0.8.0 为口径，数据复核于 2026-09-22。

---

## 一、项目概览

**Claude HUD** 是 jarrodwatts 开发的 Claude Code 插件（开源仓库 `jarrodwatts/claude-hud`，2026 年 1 月创建），在终端输入框下方实时显示当前会话的关键状态：上下文使用量、活跃工具、运行中的子智能体、待办进度、Git 信息等。

### 1.1 它解决什么问题

Claude Code 本身不提供这些信息的持续展示：

1. **上下文窗口不可见**：无法判断还剩多少上下文、何时会触发自动压缩
2. **工具执行不透明**：不知道 Claude 正在读文件、改代码还是搜索
3. **智能体状态未知**：子智能体在跑什么、跑了多久，没有直观呈现
4. **进度跟踪困难**：多步任务的完成度只能靠翻对话记录

Claude HUD 把这四类信息变成常驻终端的状态栏，看一眼就有答案。

### 1.2 技术统计

| 指标 | 数值（2026-09-22 复核） |
|------|------|
| Stars | 28,091 |
| Forks | 1,302 |
| Commits | 771+ |
| 最新提交 | 2026-09-19 |
| 分支数 | 60 |
| 最新版本 | v0.8.0（2026-08-18） |
| 许可证 | MIT |

一点说明：GitHub 仓库的语言条显示 JavaScript 占比更高，那是因为编译产物 `dist/` 目录随仓库分发（约 244 个文件）；实际源码是 TypeScript（`src/` 目录），工具链用 TypeScript 编译。

### 1.3 半年演进：从 0.0.x 到 0.8.0

本文初稿写于 2026 年 3 月底，当时项目还在 0.0.x 阶段。此后半年它以几乎每月一个功能版本的速度迭代，几个对使用体验影响较大的变化：

- **v0.1.0（6 月）**：新增中文标签（`zh-Hans`/`zh-Hant`，引导式配置中选择）、会话成本显示、prompt cache 倒计时、外部用量快照
- **v0.3.0（6 月）**：新增 Skills 与 MCP 活动行、advisor 模型显示、`autoCompactWindow`（上下文百分比按自动压缩窗口计算）
- **v0.4.0（7 月）**：繁体中文标签、Bedrock/Vertex 等路由供应商的成本显示与供应商标签、认证方式显示、effort 等级显示
- **v0.6.0（7 月）**：`pathLevels: "full"` 显示完整绝对路径、首行元素可自定义排序；此间还加入了 Jujutsu（jj）仓库支持
- **v0.7.0–v0.8.0（8 月）**：模型级每周用量窗口（如 Fable）、右对齐合并行、`$CLAUDE_CONFIG_DIR/claude-hud.json` 按配置目录覆盖设置，以及一轮系统性安全加固（配置校验、终端输出清洗、私有权限）

功能在膨胀，但核心定位没变：读 stdin、读 transcript、渲染状态行。这也是它始终轻量的原因。

## 二、核心功能

### 2.1 五大显示模块

| 显示模块 | 说明 | 价值 |
|----------|------|------|
| **Project path** | 项目路径（可配置 1–3 级目录，或 `"full"` 显示完整路径） | 清楚当前在哪个项目工作 |
| **Context health** | 上下文窗口使用量（绿→黄→红渐变） | 及时了解上下文余量，避免措手不及 |
| **Tool activity** | 工具活动（读取/编辑/搜索文件） | 实时观察 Claude 的操作行为 |
| **Agent tracking** | 子智能体运行状态 | 了解并行任务的执行进度 |
| **Todo progress** | 待办事项完成进度 | 追踪任务完成情况 |

### 2.2 默认显示（2 行）

```text
[Opus] │ my-project git:(main*)
Context █████░░░░░ 45% │ Usage ██░░░░░░░░ 25% (1h 30m / 5h)
```

- **第一行**：模型名称、供应商标签（仅在能确定时显示，如 `Bedrock`、`Vertex`、`MiniMax`）、项目路径、Git 分支
- **第二行**：上下文进度条（绿→黄→红）+ 订阅用量进度条

### 2.3 可选显示行（通过 `/claude-hud:configure` 启用）

```text
◐ Edit: auth.ts | ✓ Read ×3 | ✓ Grep ×2        ← 工具活动
◐ explore [haiku]: Finding auth code (2m 15s)   ← 智能体状态
▸ Fix authentication bug (2/5)                  ← 待办进度
```

此外还有默认关闭的 Skills 活动行、MCP 服务器活动行、会话成本、内存占用等十余个可选元素，全部通过配置开关控制。

## 三、工作原理

### 3.1 技术架构

Claude HUD 基于 Claude Code 原生 **statusline API** 实现——Claude Code 每次交互后把会话状态以 JSON 推给 statusline 命令的 stdin，HUD 解析后输出渲染结果。没有独立窗口、不需要 tmux、任何终端都能用。

```text
Claude Code → stdin JSON → claude-hud → stdout → 显示在终端
           ↘ transcript JSONL（工具、智能体、待办）
```

### 3.2 核心特性

- **原生数据**：直接从 Claude Code 获取 token 数据，不做估算
- **自适应上下文**：跟随 Claude Code 报告的上下文窗口大小，支持 1M context 会话；也可用 `autoCompactWindow` 让百分比与 `/context` 的口径对齐
- **实时解析**：解析 transcript JSONL 获取工具/智能体/待办活动
- **交互驱动刷新**：Claude Code 只在交互后重跑 statusline（新助手消息、`/compact` 完成、权限模式变化、vim 模式切换），HUD 在此基础上做 300ms 防抖。需要"时长、倒计时"这类时间信息持续走动时，可在 `~/.claude/settings.json` 的 `statusLine` 里加 `refreshInterval`（秒），例如 5 秒刷新一次

### 3.3 数据来源

Claude HUD 解析两类数据：

1. **stdin JSON**：Claude Code 在每次 statusline 渲染时推送的会话状态（模型、token、用量限制等）
2. **transcript JSONL**：完整操作记录，用于提取工具调用、智能体状态和待办进度

## 四、安装配置

### 4.1 环境要求

- Claude Code v1.0.80+
- macOS/Linux：Node.js 18+ 或 Bun
- Windows：Node.js 18+

### 4.2 安装步骤

在 Claude Code 会话内依次执行：

**第一步：添加插件市场**

```text
/plugin marketplace add jarrodwatts/claude-hud
```

**第二步：安装插件**

```text
/plugin install claude-hud
```

安装后重载插件即可：

```text
/reload-plugins
```

> ⚠️ **Linux 用户**：旧版 Claude Code 上 `/tmp` 是独立文件系统（tmpfs）时，安装可能报 `EXDEV: cross-device link not permitted`。这个 Claude Code bug 已修复，先升级 Claude Code；实在无法升级，安装前设置 `TMPDIR`：
>
> ```bash
> mkdir -p ~/.cache/tmp && TMPDIR=~/.cache/tmp claude
> ```

也可以在会话外用 CLI 完成前两步：`claude plugin marketplace add jarrodwatts/claude-hud` 与 `claude plugin install claude-hud@claude-hud`，然后进会话跑 `/reload-plugins`。

**第三步：配置状态栏**

```text
/claude-hud:setup
```

> ⚠️ **Windows 用户**：setup 提示找不到 JavaScript 运行时时，先给当前 shell 装 Node.js LTS（`winget install OpenJS.NodeJS.LTS`），重启终端再跑一次 `/claude-hud:setup`。

完成。新版 Claude Code 会自动重载设置，**下一条消息后 HUD 就会出现，无需重启**；如果没出现，再完全重启 Claude Code（旧版本需要重启才能加载 statusLine 变更）。

### 4.3 配置预设

引导命令 `/claude-hud:configure` 负责布局、语言和常用开关，提供三种预设：

| 预设 | 显示内容 |
|------|----------|
| **Full** | 全部显示：工具、智能体、待办、Git、用量、会话时长 |
| **Essential** | 活动行 + Git 状态，最小信息干扰 |
| **Minimal** | 仅模型名称和上下文进度条 |

选择预设后可单独开关每个元素，保存前还能预览效果。首次配置时会让你选标签语言——中文用户直接选简体或繁体，无需手改 JSON。

### 4.4 手动配置

颜色、阈值等高级选项需要直接编辑配置文件 `~/.claude/plugins/claude-hud/config.json`：

```json
{
  "display": { "contextWarningThreshold": 70 }
}
```

`/claude-hud:configure` 会保留这些手动设置，只更新语言、布局和常用开关。通过 `CLAUDE_CONFIG_DIR` 运行多个 Claude 配置目录时，可把差异化设置放进各自的 `$CLAUDE_CONFIG_DIR/claude-hud.json`，加载时叠加在共享配置之上。

## 五、配置选项详解

完整选项有 70 多项（见仓库 README），这里列常用的。选项按组组织：

### 5.1 布局配置

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `language` | string | `en` | 标签语言：`zh`/`zh-Hans` 简体，`zh-Hant`/`zh-TW` 繁体 |
| `lineLayout` | string | `expanded` | 布局模式：expanded（多行）或 compact（单行） |
| `pathLevels` | 1–3 或 `full` | 1 | 项目路径显示的目录层级数，`full` 显示完整绝对路径 |
| `elementOrder` | string[] | 见 README | expanded 模式下元素排列顺序，省略即隐藏 |
| `display.mergeGroups` | string[][] | `[["context","usage"]]` | 相邻元素合并同一行 |

### 5.2 Git 状态配置

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `gitStatus.enabled` | boolean | true | 是否显示 Git 分支 |
| `gitStatus.showDirty` | boolean | true | 显示未提交更改的 `*` 标记 |
| `gitStatus.showAheadBehind` | boolean | false | 显示与远程的 `↑N ↓N` 领先/落后数量 |
| `gitStatus.pushWarningThreshold` | number | 0（禁用） | 未推送提交达到该数量时用警告色标出 |
| `gitStatus.showFileStats` | boolean | false | 显示文件变更统计 `!M +A ✘D ?U` |
| `jjStatus.enabled` | boolean | false | 启用 Jujutsu（jj）状态；检测到 `.jj` 目录时替代 git，两者互斥 |

### 5.3 显示选项（部分）

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `display.showModel` | boolean | true | 显示模型名称 `[Opus]` |
| `display.showContextBar` | boolean | true | 显示上下文进度条 `████░░░░░░` |
| `display.contextValue` | string | `percent` | 上下文数值格式：`percent`/`tokens`/`remaining`/`both` |
| `display.showUsage` | boolean | true | 显示订阅用户用量限制 |
| `display.showCost` | boolean | false | 显示会话成本（优先用 Claude Code 原生 `cost.total_cost_usd`） |
| `display.showDailyCost` | boolean | false | 显示当日跨会话累计花费 `Today $12.34` |
| `display.showDuration` | boolean | false | 显示会话时长 `⏱️ 5m` |
| `display.showSpeed` | boolean | false | 显示输出 token 速度 `out: 42.1 tok/s` |
| `display.showTools` | boolean | false | 显示工具活动行 |
| `display.showSkills` | boolean | false | 显示 Skills 活动行 |
| `display.showMcp` | boolean | false | 显示 MCP 服务器活动行 |
| `display.showAgents` | boolean | false | 显示智能体活动行 |
| `display.showTodos` | boolean | false | 显示待办进度行 |
| `display.showTokenBreakdown` | boolean | true | 上下文超过 85% 时显示 token 明细 |
| `display.showMemoryUsage` | boolean | false | 显示系统内存占用（仅 expanded 布局，读的是整机 RAM 而非 Claude Code 进程） |
| `display.contextWarningThreshold` | number | 70 | 上下文警告阈值（百分比） |
| `display.contextCriticalThreshold` | number | 85 | 上下文紧急阈值（百分比） |
| `display.sevenDayThreshold` | 0–100 | 80 | 7 天用量达到该百分比时才显示 |

### 5.4 颜色配置

支持的颜色名称：`dim`、`red`、`green`、`yellow`、`magenta`、`cyan`、`brightBlue`、`brightMagenta`；也可用 256 色码（0–255）或十六进制 `#rrggbb`。

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `colors.context` | green | 上下文进度条和百分比的基础颜色 |
| `colors.usage` | brightBlue | 用量进度条的基础颜色 |
| `colors.warning` | yellow | 警告阈值颜色 |
| `colors.usageWarning` | brightMagenta | 接近阈值的警告色 |
| `colors.critical` | red | 达到限制的紧急色 |
| `colors.model` | cyan | 模型徽章颜色 |
| `colors.project` | yellow | 项目路径颜色 |
| `colors.git` | magenta | Git 包装文字颜色 |
| `colors.gitBranch` | cyan | 分支名颜色 |
| `colors.label` | dim | 标签和次要元数据颜色 |

进度条字符本身也可换：`colors.barFilled`（默认 `█`）和 `colors.barEmpty`（默认 `░`），接受单个可见字符。

## 六、使用指南

把各显示行放进同一个场景：你让 Claude 修复一个登录 bug。它派出名为 `explore` 的子智能体找相关代码，自己开始编辑 `auth.ts`——此时工具行显示 `◐ Edit: auth.ts`，智能体行显示 `◐ explore [haiku]: Finding auth code (2m 15s)`，待办行显示 `▸ Fix authentication bug (2/5)`。子智能体找到三处要读的文件后完成任务，工具行翻成 `✓ Read ×3 | ✓ Grep ×2`，对应图标从转动的 `◐` 变成绿色的 `✓`。整个过程里第二行的上下文条从 45% 缓慢爬升，你随时知道还剩多少余量——这就是 HUD 提供的"过程可见性"。

### 6.1 上下文健康度

上下文进度条按阈值变色（阈值可配置）：

- 🟢 **绿色**（低于 70%）：上下文状态良好
- 🟡 **黄色**（70%–85%）：接近警戒线，考虑收尾或压缩
- 🔴 **红色**（85% 以上）：上下文即将耗尽，默认会在此时显示 token 明细

第二行的订阅用量另有一套颜色逻辑：超过 75% 转警告色，超过 90% 转紧急色；7 天窗口用量默认达到 80% 才显示。

### 6.2 工具活动监控

工具活动行分两类：**进行中**的工具（最多显示最近 2 个）用 `◐` 标记，**已完成**的工具按调用次数排序（默认最多 4 个），超出部分折叠为 `+N more`：

| 场景 | 显示格式 | 说明 |
|------|----------|------|
| 正在编辑 | `◐ Edit: auth.ts` | 黄色 ◐ + 目标文件（路径超长会截断） |
| 读取完成 | `✓ Read ×3` | 绿色 ✓ + 累计次数 |
| 搜索完成 | `✓ Grep ×2` | 同上 |
| MCP 工具 | `✓ tool ×1` | 长名 `mcp__server__tool` 可截短为末段 |

### 6.3 智能体追踪

显示子智能体的运行状态：

```text
◐ explore [haiku]: Finding auth code (2m 15s)
```

格式：`状态图标 智能体名 [模型]: 当前任务 (运行时长)`，运行中为 `◐`，完成为 `✓`。

### 6.4 Git 状态显示

按配置逐级丰富：

```text
[Opus] │ my-project git:(main)              ← 默认：分支名
[Opus] │ my-project git:(main*)             ← 未提交更改
[Opus] │ my-project git:(main ↑2 ↓1)        ← 领先/落后远程
[Opus] │ my-project git:(main* !3 +1 ?2)    ← 文件变更统计
```

标记含义：`!` = 已修改，`+` = 已添加/已暂存，`✘` = 已删除，`?` = 未跟踪；数量为 0 的类别自动省略。

## 七、安全设计

一个常驻读取你全部会话数据的工具，安全边界很重要，Claude HUD 在 README 里写得很明确：

- **纯本地运行**：不发起网络请求、不抓取凭据、不调用未公开的 Claude API；只读 stdin JSON、当前会话 transcript 路径、`~/.claude` 下的部分配置文件和当前工作区的 git 元数据
- **缓存收敛**：HUD 缓存文件写在 `~/.claude/plugins/claude-hud` 下，POSIX 文件系统上使用私有权限，内容限于派生的展示元数据
- **任意命令默认禁用**：`--extra-cmd` 可以在每次刷新时执行任意 shell 命令，因此默认关闭，需在 HUD 进程环境里显式设置 `CLAUDE_HUD_ALLOW_EXTRA_CMD=1` 才生效
- **输入加固**：v0.8.0 起对配置文件做大小与嵌套限制、拒绝符号链接与原型污染输入、对输出到终端的标签做控制字符清洗

临时不想看到 HUD 时，用环境变量开关而不用删配置：

```bash
CLAUDE_HUD_DISABLE=1 claude
```

## 八、故障排除

### 8.1 配置不生效

1. 检查 JSON 语法是否正确——无效 JSON 会静默回退到默认配置
2. 确保使用有效值：`pathLevels` 为 1、2、3 或 `"full"`；`lineLayout` 为 `expanded` 或 `compact`
3. 删除配置文件后运行 `/claude-hud:configure` 重新生成

### 8.2 Git 状态不显示

1. 确认当前目录是 git 仓库（jj 仓库需 `jjStatus.enabled: true` 且 `jj` 在 PATH 中）
2. 检查配置中 `gitStatus.enabled` 不为 `false`

### 8.3 工具/智能体/待办行不显示

这些行默认隐藏，需要通过 `/claude-hud:configure` 或配置项启用；而且只在有对应活动时才出现。

### 8.4 用量不显示

**要求**：

- 必须是 Claude 订阅用户（API key 按量计费，没有速率限制）
- Claude Code 必须在 stdin 中提供 `rate_limits` 数据

**常见原因**：

- API key 用户（无速率限制数据）
- AWS Bedrock 模型（显示 `Bedrock` 标签并隐藏用量，限制由 AWS 管理）
- 会话首次响应之前 `rate_limits` 可能还是空的；少数 Claude Code 构建版本和订阅档位始终不提供
- 配置了 `display.externalUsagePath` 时，HUD 会先尝试读取本地用量快照

## 九、推荐做法

### 9.1 工作流程

1. **盯着上下文颜色**：进度条转黄时考虑收尾当前任务或 `/compact`，别等红色
2. **扫一眼工具行**：确认 Claude 在做预期内的事，发现它大规模读不相关文件可以及时打断
3. **多智能体任务开着 Agent 行**：并行子任务谁在跑、谁卡住，一眼可见

### 9.2 配置推荐

信息完整型（全功能开发者）：

```json
{
  "lineLayout": "expanded",
  "language": "zh-Hans",
  "display": {
    "showTools": true,
    "showAgents": true,
    "showTodos": true,
    "showDuration": true
  }
}
```

极简型（单行、少干扰）：

```json
{
  "lineLayout": "compact",
  "pathLevels": 1,
  "gitStatus": {
    "showDirty": true,
    "showAheadBehind": false
  }
}
```

## 十、常见问题

**Q: Claude HUD 和 tmux 有什么区别？**

A: Claude HUD 是 Claude Code 的原生插件，走 statusline API，不需要终端复用器。它只做一件事：显示当前会话的状态。tmux 是通用的终端管理工具，两者不冲突，但用 HUD 不需要先会用 tmux。

**Q: 影响性能吗？**

A: 影响很小。statusline 本来就只在交互后重跑，HUD 在此基础上做 300ms 防抖；配置 `refreshInterval` 后每次刷新会重跑一次 HUD 进程，官方建议 5 秒起步，只为倒计时更平滑才用 1 秒。

**Q: 支持哪些 Claude Code 版本？**

A: v1.0.80+。用量显示还需要 Claude Code 在 stdin 推送 `rate_limits` 数据。

**Q: 界面是英文的吗？**

A: 默认英文，v0.1.0 起支持简体和繁体中文标签，在 `/claude-hud:configure` 里选择或配置 `language` 字段即可。

## 十一、总结与采用建议

Claude HUD 没有多提供信息，只是把"AI 正在做什么"从猜变成了看——上下文余量、工具行为、子智能体进度都常驻终端底部，数据直接取自 Claude Code，不经过估算。

落地建议：

- **重度 Claude Code 用户、订阅制用户**：值得直接装。上下文管理是长会话的第一痛点，用量显示对订阅用户的 5 小时/每周窗口也很实用
- **API key 按量付费用户**：工具/智能体/Git 显示依然有价值，但没有用量行；成本可通过 `showCost` 补上
- **轻度用户**：先用默认的 Minimal 预设，习惯后再加显示元素，避免信息过载
- **企业/Bedrock 用户**：可用，但注意用量与成本显示的边界（见 8.4 节）

半年从 0.0.x 迭代到 0.8.0、issue 与安全修复响应迅速、文档（含中文）完整——这个项目的维护状态本身也是它可靠性的注脚。

---

**相关资源：**

- 🐙 [GitHub 仓库](https://github.com/jarrodwatts/claude-hud)
- 📖 [中文文档 README.zh.md](https://github.com/jarrodwatts/claude-hud/blob/main/README.zh.md)
- 🖼️ [界面预览图](https://github.com/jarrodwatts/claude-hud/blob/main/claude-hud-preview-5-2.png)
- 💬 [Discussions](https://github.com/jarrodwatts/claude-hud/discussions)

**参考来源与口径说明**

- 本文数据复核于 2026-09-22，功能与配置以 v0.8.0（2026-08-18 发布）及 main 分支（2026-09-19 提交）为口径；README 与 `src/` 源码（`config.ts` 默认值、`render/colors.ts` 阈值、`render/tools-line.ts` 工具行）为配置项与行为描述的依据
- Stars/Forks/Commits/分支数为 GitHub API 当日数值，会随时间变化；上下文警告/紧急阈值默认 70%/85%，订阅用量 75%/90%，均为源码默认值且可配置
- 本文初稿发布于 2026-03-29（项目 0.0.x 阶段），1.3 节的演进脉络整理自仓库 CHANGELOG.md
