---
title: "CodeBurn：AI 编码 Token 消耗可视化仪表盘"
date: "2026-04-16T11:32:26+08:00"
slug: "codeburn-ai-coding-token-observability"
github_repo: "getagentseal/codeburn"
source_key: "gh:getagentseal/codeburn"
description: "CodeBurn 读取 AI 编码工具写在本地磁盘的会话文件，把账单算不到的细节——按项目、模型、任务类型的 Token 去向，以及一次性编辑成功率——全部算出来。本文拆解它的数据采集、任务分类与定价引擎，并给出从查账到省钱的完整命令路径。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "Cursor", "Codex", "Token", "TypeScript"]
lastmod: "2026-10-02T00:00:00+08:00"
---

# CodeBurn：AI 编码 Token 消耗可视化仪表盘 ⭐⭐⭐ 进阶分析

账单只告诉你这个月花了多少钱，不告诉你钱花在哪个项目、哪个模型、哪类任务上，更不告诉你其中有多少是白烧的。CodeBurn 解决的就是这个断层：它读取 AI 编码工具已经写在磁盘上的会话文件，把每一笔 Token 消耗还原成可追问的明细——按项目、按模型、按任务类型，甚至按 git 分支。

它做这件事的方式决定了它的天花板：不装代理、不要 API Key、不改变任何工具的工作方式，纯被动地解析本地文件。代价也同样来自这里——工具改了存储格式，它就得跟着改。这个项目 2026 年 4 月 13 日创建，当天发布 npm 首版，半年内迭代 56 个版本、适配 40 种工具，是这种模式的最新注脚。

## 项目坐标

| 项 | 值 | 来源 |
|------|------|------|
| 仓库 | [getagentseal/codeburn](https://github.com/getagentseal/codeburn) | GitHub |
| 许可证 | MIT | `LICENSE` |
| 语言 | TypeScript | GitHub API |
| 星标 / 复刻 | 11299 / 869 | GitHub API，2026-10-02 取 |
| 创建时间 | 2026-04-13，npm 0.1.0 同日发布 | GitHub API / npm registry |
| 当前版本 | v0.9.25（2026-09-21） | GitHub Releases / npm |
| Node 要求 | 22.13+ | `package.json` engines |
| 运行形态 | CLI（npm / Homebrew）、桌面应用（macOS / Windows / Linux）、菜单栏常驻 | README |
| 官网 | [codeburn.app](https://codeburn.app/) | GitHub API homepage |

上手只要一行 `npx codeburn`，没有账号、没有注册。想留下就用 `npm install -g codeburn` 或 `brew install codeburn`。

## 一条引擎，四个界面

CodeBurn 的所有数字来自同一份本地数据，四个界面只是四种看法：

| 界面 | 形态 | 适合 |
|------|------|------|
| 终端仪表盘 | `codeburn`（Ink TUI） | 快速查看，脚本友好 |
| 桌面应用 | Electron，macOS / Windows / Linux | 深挖会话明细，优化配置 |
| 菜单栏常驻 | macOS 原生 app、Windows 托盘、GNOME 扩展 | 时刻可见的今日花费与额度 |
| 浏览器 | `codeburn web` | 跨设备汇总，大屏查看 |

macOS 桌面版用 Developer ID 签名并通过 Apple 公证；Windows 推荐从 Microsoft Store 安装；Linux 提供 deb、rpm 和 AppImage。如果你在 WSL 里跑 agent，Windows 版会同时读取各个发行版的 home 目录，Linux 侧的会话不会漏计。

## 数据从哪来

每个 AI 编码工具都会把会话写进磁盘：Claude Code 写 JSONL，Codex 写 rollout 文件，Cursor 和 OpenCode 写 SQLite。CodeBurn 内置 40 个 provider，各管一种工具的目录结构和文件格式。安装了哪个、哪个有会话数据，界面上就会出现哪一行，`p` 键在它们之间切换。

四个有代表性的 provider，基本覆盖了它要处理的全部数据形态：

**Claude Code**——会话以 JSONL（每行一条 JSON 记录）存在 `~/.claude/projects/<项目路径>/<会话ID>.jsonl`，每条记录带模型名、input/output/cache read/cache write 四类 Token、工具调用和时间戳。解析时按 API message ID 去重，避免同一条消息被流式写入的多个分片重复计数。

**Codex（OpenAI）**——会话在 `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`，用 `token_count` 事件记录 Token，用 `function_call` 条目记录工具调用。它的工具名与 Claude 习惯不同，CodeBurn 做一层规范化映射（比如 `exec_command` 归到 `Bash`），保证跨工具的统计口径一致。

**Cursor**——数据在 SQLite 里（macOS 路径 `~/Library/Application Support/Cursor/User/globalStorage/state.vscdb`）。数据库可能很大，CodeBurn 把解析结果缓存到 `~/.cache/codeburn/`，按源文件的修改时间和大小判断失效，后续运行基本即时。要留意的是精度：Cursor 的本地库没有每次请求的 Token 明细，CodeBurn 官方 CHANGELOG 承认在某个真实月份里，本地估算约 700 万 Token，而 Cursor 仪表盘显示 6.44 亿——差了两个数量级。精确对账用 `codeburn import cursor <导出.csv>`：在 cursor.com/dashboard/usage 导出 CSV 导入，导出区间内的官方数字会替换本地估算。

**OpenCode**——同样是 SQLite（`~/.local/share/opencode/opencode*.db`），查询 `session`、`message`、`part` 三张表。成本按模型重新计算，而不是直接用 OpenCode 自带的成本字段，避免不同定价标准混入。

数据目录不标准时，环境变量可以逐个覆盖：`CLAUDE_CONFIG_DIR`、`CODEX_HOME`，以及二十多个各工具专属的变量（完整清单在 `docs/configuration.md`）。多套 Claude 配置并存时，`CLAUDE_CONFIG_DIRS`（注意复数）用系统路径分隔符列出多个目录一起扫描，优先级高于单数版本。

## 十三类任务分类

CodeBurn 把每一轮 AI 工作归入 13 类任务。这是纯规则判断——看工具调用模式和用户消息里的关键词，不调 LLM，完全确定：

| 任务类型 | 触发条件 |
|---------|---------|
| Coding | Edit、Write 工具被调用 |
| Debugging | 错误/修复关键词 + 工具使用模式 |
| Feature Dev | "add"、"create"、"implement" 等关键词 |
| Refactoring | "refactor"、"rename"、"simplify" 等关键词 |
| Testing | Bash 中出现 pytest/vitest/jest |
| Exploration | Read、Grep、WebSearch 但无代码编辑 |
| Planning | EnterPlanMode、TaskCreate 工具被调用 |
| Delegation | Agent 工具被调用（AI 调度子任务） |
| Git Ops | Bash 中出现 git push/commit/merge |
| Build/Deploy | npm build、docker、pm2 等命令 |
| Brainstorming | "brainstorm"、"what if"、"design" 等关键词 |
| Conversation | 无工具调用的纯文本对话 |
| General | Skill 工具被调用或无法归类 |

规则分类省了 Token、也省了不确定性，但边界案例靠关键词难免误判——它回答的是"大概把钱花在哪类事上"，不是逐轮精确审计。

## One-Shot 成功率：钱花得值不值

只看花费，看不出模型质量。CodeBurn 用 **One-Shot 成功率** 补上这一维：对涉及代码编辑的任务，统计"一次编辑就成功、无需重试"的比例。

对重试的判定是文件级的：同一文件在被 shell 命令隔开后再次被编辑（Edit foo.ts → Bash → Edit foo.ts）才算一次重试；中间编辑的是不同文件，不算。文件级跟踪目前支持 Claude、Codex 和 Goose，其余工具回退到按工具名模式检测。

Coding 类别 90% 的 One-Shot 意味着十次编辑九次到位。这个数字和花费放在一起看才有意义：Debugging 花钱多但 One-Shot 低，说明模型在反复试错，这时换更强的模型或改提示词，比继续堆 Token 划算。

## 定价引擎

价格数据来自 [LiteLLM](https://github.com/BerriAI/litellm) 维护的全模型价目表，本地缓存 24 小时。每笔调用按 input、output、cache write、cache read、web search 五类 Token 分别计价，Claude 的快速模式（fast mode）按额外倍数处理，超过长上下文阈值（如 272k）的调用套用更高档价。

定价有两层兜底：

- **内置快照**。npm 包里带一份 LiteLLM 价目快照和 fallback 定价表（当前 5896 条主条目、543 条 fallback），离线或上游拉取失败时用快照，常见 Claude 和 GPT 模型另有硬编码价格防止模糊匹配错价。
- **手动覆盖**。`codeburn price-override <model>` 改指定模型单价，`codeburn model-alias <from> <to>` 把内部端点或别名模型映射到标准价目行。走公司内部 LLM 时靠这两个命令对齐真实价格。

展示货币可以随时切换：`codeburn currency JPY`。汇率来自 [Frankfurter](https://www.frankfurter.app/)（欧洲央行参考汇率，免费无 Key），同样缓存 24 小时，任何合法 ISO 4217 代码都能用，`--symbol` 可自定义货币符号，`--reset` 回到 USD。

## 终端仪表盘

不带参数启动 `codeburn` 进入交互式仪表盘。方向键切换时间范围，数字键直达：

| 按键 | 功能 |
|------|------|
| `←` / `→` / `Tab` | 上一个 / 下一个时间范围 |
| `1` – `6` | Today / Week / 30 Days / Month / All / Lifetime |
| `p` | 切换 Provider（工具） |
| `c` | 模型对比视图 |
| `o` | 配置体检（Optimize） |
| `m` | 开关鼠标跟踪（滚轮翻页） |
| `q` 或 `Ctrl+C` | 退出 |

总数字下面是四张表：按工具、按模型、按项目、按任务类型的成本分解。每个数字都可以继续下钻——桌面版里点击今日总额落到 Sessions 页，一行一个会话；再点一行，展开这个会话里的每一轮对话和各自的花费。

偏好纯文本输出的话：

```bash
codeburn today                  # 今日概览
codeburn month                  # 本月概览
codeburn report -p 30days       # 30 天报告（report 是默认命令）
codeburn report --refresh 120   # 每 120 秒自动刷新（最小 60）
codeburn status --format json   # 紧凑状态，供程序消费
codeburn export -f json         # 导出 JSON（-f csv 为表格）
codeburn export --provider claude   # 只导出指定工具
```

`report`/`today`/`month` 都支持 `--project`（只看匹配的项目，可重复）、`--exclude`（排除）、`--from`/`--to`（自定义区间）、`--day`（单日回看）。

## 让花费降下来：四组命令

看数据只是第一步，CodeBurn 把"发现问题 → 验证改进 → 守住预算"做成了完整链路。

**配置体检：optimize**

```bash
codeburn optimize           # 扫描最近 30 天会话 + ~/.claude 配置
codeburn optimize --apply   # 确认后代为修改
codeburn act undo --last    # 撤销上一次修改
codeburn act report         # 数天后核对每项修复的实际效果
```

它找的是"花 Token 却不产出"的东西：agent 每轮都重读的文件、装了几个月从没调用过的 MCP server、长得太长以至于塞进每一次请求的 `CLAUDE.md`。每条发现标明是实测还是模型推算，给出修复方法和预计节省额。整体配置打 A–F 等级——注意评的是配置不是花费，花得多但配置干净照样是 A。修改前有备份，应用前能看到改动内容。

**预算与额度：plan / quota / guard**

```bash
codeburn plan set claude-max   # 声明你订阅的套餐
codeburn quota                 # 各工具实时剩余额度
codeburn guard install         # 给 Claude Code 装花费护栏
```

`quota` 读取你已登录工具的实时限额——五小时窗口和每周窗口都来自工具本身。长任务跑之前先看一眼，比跑一半被限额打断强。

`guard` 是可选的本地护栏：给 Claude Code 装 hooks，会话花费超过软上限（默认 $5）时警告，超过硬上限（默认 $15）时停止。两个数字都可以改，`codeburn guard status` 查看 hooks 位置，`codeburn guard uninstall` 移除。

**模型对比：compare**

```bash
codeburn compare    # 或在仪表盘按 c
```

在你自己的历史数据上并排比较两个模型：One-Shot 率、重试率、自我纠正、单次调用成本、单次编辑成本、缓存命中率。cohorts 模式把范围收窄到同类工作，给出每次编辑回合的成本中位数和 P90。混用两个模型的回合被剔除并计数，不硬分给任何一方。样本足够时，`optimize` 会直接给出"这个项目用某个更便宜的模型、One-Shot 率没有下降"的建议，`codeburn act apply-model <project>` 一键应用。

**花得值不值：yield 与 context**

`yield` 把花费和会话记录的 pull request 关联，看哪些花费真正交付了代码；`codeburn spend` 输出模型 × 项目的花费流向，`--format branch-json` 换到 git 分支维度，一个功能分支从头到尾烧了多少钱一目了然。某个会话花了一小时干五分钟的活？`codeburn context <session>` 拆开看上下文窗口里到底塞了什么——assistant 的文本、推理、工具调用，user 的文本和图片，以及压缩（compaction）次数。压缩次数偏多通常意味着模型在反复重读。

## 架构与关键决策

```text
┌─────────────────────────────────────────────────────┐
│              CLI 入口（Commander.js）                │
│   report · today · month · optimize · quota · ...   │
└────────────────────────┬────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────┐
│      Provider 层（40 个单文件适配器，按需加载）        │
│   claude · codex · cursor · opencode · gemini · …   │
└────────────────────────┬────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────┐
│      解析与缓存（多进程解析、按天分片会话缓存）         │
├─────────────────────────────────────────────────────┤
│      Classifier（13 类任务 · One-Shot 判定）          │
│      Models（LiteLLM 定价 · 快照兜底 · 覆盖）         │
└────────────────────────┬────────────────────────────┘
                         ▼
┌──────────────┬──────────────┬──────────────┬─────────┐
│  终端 TUI    │  桌面应用     │  菜单栏/托盘  │  Web    │
│  (Ink)       │  (Electron)  │  原生/Tauri  │ (serve) │
└──────────────┴──────────────┴──────────────┴─────────┘
```

几个影响日常体验的决策：

**Provider 是单文件插件。** 每种工具一个文件（`src/providers/codex.ts` 是官方推荐的参考实现），实现会话发现、解析和工具名规范化三个接口。新工具的适配成本被压到"一个文件"，这是它能半年覆盖 40 种工具的结构原因。反过来，工具停服它也跟得紧：Roo Code 2026 年 5 月归档，支持随即移除。

**SQLite 读取零原生依赖。** Cursor 和 OpenCode 的数据库通过 Node 内置的 `node:sqlite` 模块读取（早期用 `better-sqlite3`，后来换掉，摆脱了原生编译链）。只读访问，不碰工具自己的数据库。

**会话缓存按天分片。** 缓存按"每天一个文件"组织，查今天只读今天。官方在重负载语料上测得 `overview -p today` 从约 3.1 秒 / 690 MB 内存降到 0.8 秒 / 560 MB；更极端的场景从 3.4 GB 降到 1.2 GB，不再撑爆 1 GB 堆限制。数字口径是官方 CHANGELOG 的对比测试，普通语料上提升小得多。

**四个界面一个引擎。** 终端、桌面、菜单栏、浏览器读同一批文件，数字一致，差别只在各自的刷新时刻。菜单栏组件不再依赖第三方（早期版本的 SwiftBar 方案已弃用）：macOS 是原生 CodeBurnMenubar.app（要求 macOS 14+），Windows 是 Tauri 托盘应用，Linux 走 GNOME Shell 扩展，`codeburn menubar` 一键安装。

## 隐私与边界

CodeBurn 读的是已经在磁盘上的文件，没有账号、没有 API Key、不在你和 agent 之间加任何一层——它哪天坏了，工具照常工作。提示词、代码、项目名都留在本机；给 agent 用的 MCP server（`claude mcp add codeburn -- npx -y codeburn mcp`）从同一批本地文件取数，自己不做网络调用，项目名默认假名化处理。

需要联网的只有两件事：LiteLLM 价目表和 Frankfurter 汇率，都是每天一次的公开数据拉取。断网时用内置快照，功能不中断。

两个已知的精度边界：

- **Cursor 估算**。如前所述，本地库没有请求级 Token 明细，本地数字可能显著偏离 Cursor 官方账目，精确对账走 `codeburn import cursor`。
- **非标准端点**。公司内部 LLM 或中转网关的模型名对不上 LiteLLM 价目时，用 `price-override` / `model-alias` 手工对齐，否则可能计为 $0 或错价。

## 常见问题

**Q：多个工具的数据会重复计算吗？**

不会。去重在每个 provider 内部独立进行，不同工具的会话没有交叉。但同一个任务用两个工具各做一遍，花费会各记各的——它们确实各烧了各的 Token。

**Q：怎么确认某个工具被正确识别了？**

`codeburn doctor` 专门诊断检测问题：各工具的数据目录是否找到、解析出多少会话。某工具升级后换了存储路径，也是先跑它。

**Q：能把数据接进自己的监控系统吗？**

`codeburn report -p today --format json` 输出完整 JSON（顶层 `totalCostUSD`，每日行带 `oneShotRate`），配合 `jq` 和 cron 就能接进任何监控系统：

```bash
codeburn report -p today --format json | jq '.totalCostUSD'
```

**Q：第一次跑 Cursor 支持很慢？**

正常。数 GB 的 SQLite 首次解析需要时间，之后走缓存基本即时。缓存异常时删除 `~/.cache/codeburn/` 下对应的 Cursor 缓存文件重建即可。

## 采用建议

个人开发者重度使用 Claude Code 或 Codex 的，直接 `npx codeburn` 跑一次——看到按项目和按任务的花费分解后，大概率会留下来。订阅制用户（claude-max 之类）加上 `plan set` + `quota`，把"花了多少"变成"还剩多少"。

团队场景的起点是 `export` 和 `status --format json`：先汇总成员的本地数据看结构，再决定要不要把它纳入常规报表。`optimize --apply` 这类会改配置的功能，团队里建议先个人试用、确认回滚路径（`act undo --last`）再推广。

只用 Cursor 且在意精确数字的，先跑 `import cursor` 对一次账，再决定信不信本地估算。

## 总结速查

| 命令 | 用途 |
|------|------|
| `npx codeburn` | 零安装启动交互式仪表盘 |
| `codeburn report -p 30days` | 30 天报告（report 为默认命令） |
| `codeburn status --format json` | 紧凑 JSON 状态 |
| `codeburn export -f csv` | 导出 CSV / JSON |
| `codeburn optimize` | 配置体检，`--apply` 代为修复 |
| `codeburn plan set <plan>` / `quota` | 声明订阅套餐 / 查实时额度 |
| `codeburn guard install` | Claude Code 花费护栏（默认 $5 警告 / $15 停止） |
| `codeburn compare` | 两个模型在你的数据上对比 |
| `codeburn import cursor <csv>` | 用官方导出替换 Cursor 本地估算 |
| `codeburn web` | 浏览器仪表盘 |
| `codeburn menubar` | 安装菜单栏 / 托盘常驻 |
| `codeburn currency JPY` | 切换展示货币 |

---

**文档信息**

- 难度：⭐⭐⭐ | 类型：进阶分析 | 更新日期：2026-10-02 | 预计阅读时间：20 分钟
- 数据口径：GitHub API、npm registry、仓库源码与文档（v0.9.25，2026-09-21），2026-10-02 核实
