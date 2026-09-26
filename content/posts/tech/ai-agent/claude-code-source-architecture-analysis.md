---
title: "Claude Code 源码架构拆解:Tool、Command、MCP 与权限系统"
date: "2026-03-31T21:54:05+08:00"
lastmod: "2026-09-25T10:00:00+08:00"
slug: "claude-code-source-architecture-analysis"
github_repo: "anthropics/claude-code"
source_key: "gh:anthropics/claude-code"
aliases:
  - /posts/tech/claude-code-source-architecture-analysis/
description: "基于 2026-03-31 源码快照的 Claude Code 架构拆解:工具系统、命令系统、服务层、Bridge、权限模型与扩展机制,并对照 2026 年 9 月的官方文档标注哪些设计延续至今。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "Anthropic", "TypeScript", "MCP", "智能体架构"]
---

# Claude Code 源码架构拆解:Tool、Command、MCP 与权限系统

Claude Code 真正值得研究的不是它接了哪个模型,而是模型外面那一圈:工具系统、权限系统、服务层和扩展机制。2026 年 3 月底泄露的源码快照,第一次让外界看清这一圈的真实结构。本文以这份快照为材料拆解它的架构,并把关键设计对照到 2026 年 9 月的官方文档,标注哪些延续至今、哪些已经演进。

如果你是在快照刚泄露时关注这件事的,需要先知道一个新情况:当时承接快照的 `instructkr/claude-code` 仓库已经易主,变成了一个完全无关的项目;原始快照如今要看当天的 fork 存档。本文所有镜像侧内容均以 2026-03-31 当日的 fork 存档为准,细节见 §1 与 §3。

## §0 先看结论

时间有限的话,记住下面六个判断就够了:

- Claude Code 的官方定位是**智能体式编程工具**(agentic coding tool)。它做的事是把自然语言目标转成一串可控的工程动作,回答文本只是副产品。
- `instructkr/claude-code` 是公开快照镜像,不是 Anthropic 的开源仓库。该仓库现已转移到 `ultraworkers/claw-code` 并被改造成别的项目,原始快照以泄露当日的 fork 存档为准。
- 决定 Claude Code 工程价值的,是**工具系统、权限系统与工作流编排**的组合,而不是模型的回答效果。
- 命令系统面向用户意图,工具系统面向代理动作,服务层负责把外部复杂性隔离在主循环之外。
- MCP、插件、技能、hooks 与 subagents 构成五条彼此独立的扩展通道,各有分工。
- 快照适合学架构,不能当作今天线上版本的实现依据;本文在权限模式、hooks 事件等处补充了 2026 年 9 月的官方现状对照。

带着不同任务来读,可以这样取材:想建立整体认识,读 §0、§2、§7、§19;想理解内部架构,读 §6 到 §14;想做扩展开发,读 §15、§16;想判断团队是否该用,读 §4、§16、§17。

## §1 事实边界:本文口径

这篇文章讨论的是两个相关但不能混为一谈的对象:

- **Claude Code 官方产品**:Anthropic 发布的智能体式编程工具,官方 README 说明它可在终端、IDE 以及 GitHub 中使用。
- **源码快照镜像**:2026 年 3 月 31 日出现的 `instructkr/claude-code`,收录了泄露的 `src/` 目录,不是 Anthropic 的开发仓库。

本文的写法原则:

- 官方文档能确认的内容,直接作为事实陈述。
- 快照 README 写出的内容,视为"镜像维护者的公开声明",不写成 Anthropic 官方承诺。
- 无法从公开材料稳定核验的内容,不做断言。
- 时间敏感数据(如仓库 stars)不作为核心结论。

时间口径上有两点需要交代。其一,快照反映的是 2026-03-31 时点的实现,不等于今天线上版本的逐行真相;Anthropic 从未官方确认过这份源码的完整性。其二,`instructkr/claude-code` 已于本文修订时(2026-09-25 经 GitHub API 核实)重定向到 `ultraworkers/claw-code`,仓库内容已被替换为一个 Rust 语言的实验项目,与 Claude Code 无关。原始快照内容以泄露当天(2026-03-31)创建的 fork 存档为准,例如 [xFrye/claude-code](https://github.com/xFrye/claude-code);本文引用镜像 README 处,均已对照这份存档核实。

## §2 Claude Code 是什么

### 2.1 官方产品定位

Anthropic 官方 README 对 Claude Code 的描述很直接:一个运行在终端中的智能体式编程工具,理解你的代码库,通过自然语言帮你执行常规开发任务、解释复杂代码、处理 Git 工作流,可在终端、IDE 与 GitHub(tag `@claude`)三种场景中使用。

这个定义把它与两类常见工具区分开:它不是单纯的聊天助手,也不是只生成一段代码的补全工具,而是带有上下文感知、工具调用与工作流编排能力的工程代理。

### 2.2 快照镜像是什么

快照 README 的自我介绍写得很清楚:收录泄露的 `src/` 目录,目的包括教育用途、防御性安全研究与软件供应链分析;同时声明不拥有原始代码、不代表官方、不应被解读为 Anthropic 官方仓库。

研究这份材料,正确的姿态不是"Claude Code 正式开源了",而是:一次泄露让外界得以观察一个真实生产级 AI 工程代理的内部结构。这样的样本并不多。

### 2.3 为什么值得研究

抛开事件本身,这份快照覆盖了现代 AI 编程工具最重要的几个维度:

- **CLI 产品形态**:如何在终端里做出可交互、可扩展的复杂产品
- **工具编排**:如何把文件、搜索、网络、子智能体、MCP 等能力统一到一个框架
- **权限治理**:如何让高权限工具在真实用户环境里安全运行
- **多通道集成**:如何同时支持终端、IDE、GitHub 与远程控制
- **扩展能力**:如何为命令、插件、技能、hooks、MCP 留出边界清晰的扩展点

## §3 泄露经过与研究边界

### 3.1 已知事实

综合快照 README 与公开传播线索,可以确认:

- 泄露被发现于 **2026 年 3 月 31 日**,发现者是 Chaofan Shou([@Fried_rice](https://x.com/Fried_rice/status/2038894956459290963)),他在 X 上发了帖子。
- 泄露方式:npm 分发包中的 source map 文件暴露了完整、未混淆的 TypeScript 源码路径,源码可以从 Anthropic 的 R2 存储桶以 zip 形式下载。
- 快照规模:约 **1,900 个文件,超过 51 万行代码**。
- 镜像仓库保存的只是 `src/` 目录快照,不是完整的官方开发历史。

这意味着我们能研究的是一次具体时刻的源码组织方式、当时的产品能力结构;不能自动推出的是"这是当前官方最新实现"、所有细节都与今天上线版本一致。

### 3.2 这类研究的价值

快照材料不是拿来八卦的,它能帮我们认真回答几个工程问题:

- 一个真实 production 级 AI 编程代理,到底有哪些核心模块?
- 自然语言请求如何转成工具调用与结果回传?
- 为什么权限系统必须是架构核心,而不是附属功能?
- 为什么扩展体系要同时包含命令、插件、技能、MCP、hooks?
- 为什么终端产品最后会长成"CLI + UI + 服务层 + 协议层 + 权限层"的形态?

### 3.3 伦理边界

这类公开快照只能用于教学研究、防御性分析、供应链安全讨论与工程架构学习;不应用于伪装官方代码、商业性复制、绕过安全控制或构造恶意衍生工具。这不是礼貌问题,是研究边界问题。

## §4 从入门开始:官方产品怎么用

先不谈源码,回答最实际的问题:把 Claude Code 用起来,官方公开材料告诉了你什么。

### 4.1 三种使用入口

官方 README 列出的使用场景是终端、IDE 与 GitHub。三种入口对应三种工作方式:

- **终端**:日常编码、调试、阅读代码、执行命令
- **IDE**:在编辑器上下文中边看边改
- **GitHub**:让代理参与 PR、Issue 与代码评审

### 4.2 安装方式

官方 README 目前给出四种推荐安装方式,npm 安装仍列出但已标记为 Deprecated:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

```bash
brew install --cask claude-code
```

```powershell
irm https://claude.ai/install.ps1 | iex
```

```powershell
winget install Anthropic.ClaudeCode
```

```bash
npm install -g @anthropic-ai/claude-code  # Deprecated
```

安装路径的迁移方向很清楚:官方希望用户走原生二进制分发,而不是依赖 Node 生态。

### 4.3 CLI 入口

官方 CLI 参考页中的典型入口形式:

```bash
claude "explain this project"
```

```bash
claude -p "explain this function"
```

```bash
claude -c -p "Check for type errors"
```

三种形式对应三类需求:`claude "query"` 带初始提示启动交互会话;`-p`(print 模式)单次查询后退出,适合脚本与批处理;`-c`(continue)继续当前目录最近一次会话,适合长任务续跑。

### 4.4 一个典型的入门流程

第一次使用,顺序大致是:安装,进入项目目录,运行 `claude`,用自然语言描述任务,按需批准工具调用,观察输出后继续追问或验收。

流程背后能看到三条设计取舍:用户给的是**目标**;系统负责把目标拆成上下文理解、工具执行与结果回收;用户在关键副作用节点保留**控制权**。第三条到 §12 权限系统时会再展开。

## §5 技术栈全景

快照 README 给出的技术画像如下:

| 类别 | 技术 | 作用 |
| ---- | ---- | ---- |
| 运行时 | Bun | 启动、打包、特性裁剪 |
| 语言 | TypeScript(strict) | 类型安全与大型工程维护 |
| 终端 UI | React + Ink | 终端交互界面 |
| CLI 解析 | Commander.js | 命令行参数与入口管理 |
| 模式验证 | Zod v4 | 工具输入与配置校验 |
| 搜索 | ripgrep | 高性能代码搜索 |
| 协议 | MCP SDK、LSP | 外部工具与语言服务集成 |
| API | Anthropic SDK | 模型调用 |
| 遥测 | OpenTelemetry + gRPC | 可观测性 |
| 特性开关 | GrowthBook | 功能开关与条件加载 |
| 认证 | OAuth 2.0、JWT、macOS Keychain | 身份与密钥管理 |

这组选型对应五类需求:运行效率(Bun、动态加载、并行预取)、复杂交互(React + Ink)、工程可靠性(TypeScript strict + Zod)、外部连接(MCP、LSP、OAuth、Keychain)、产品化运营(遥测、特性开关、权限控制)。

### 5.1 为什么是 Bun

快照 README 提到,选 Bun 影响三个工程目标:启动性能、构建时 dead code elimination、原生 TypeScript 友好性。终端工具用户对"打开即用"的敏感度比 Web 用户更高,启动阶段每一点额外成本都会放大体感延迟。dead code elimination 则和 §13 的特性开关机制直接配套——未启用的能力在构建期就被剥掉,不占运行时体积。

### 5.2 为什么是 Ink + React

如果只把终端程序理解成"命令输入 + 文本输出",Claude Code 给出的信号是:终端被当成真正的交互式 UI 容器来设计。Ink 让 CLI 界面可以用组件化、状态驱动、增量更新的方式组织,流式输出、状态切换、进度展示、键盘交互、多面板界面都依赖这一点。这不是套了终端皮肤的脚本,而是把终端当应用平台做。

## §6 目录结构:光看目录就能读出架构

### 6.1 入口与核心文件

```text
src/
├── main.tsx
├── commands.ts
├── tools.ts
├── Tool.ts
├── QueryEngine.ts
├── context.ts
├── cost-tracker.ts
```

这组文件构成核心引擎层:`main.tsx` 是入口编排,`commands.ts` 是命令注册,`tools.ts` / `Tool.ts` 是工具系统的定义与注册,`QueryEngine.ts` 驱动模型交互主循环,`context.ts` 收集环境上下文,`cost-tracker.ts` 统计消耗。

### 6.2 功能目录的职责切分

快照 README 列出的目录超过二十个,主要的包括:

```text
commands/    tools/       components/  hooks/       services/
screens/     types/       utils/       bridge/      coordinator/
plugins/     skills/      remote/      server/      tasks/
state/       schemas/     keybindings/ vim/         voice/
memdir/      migrations/  entrypoints/ outputStyles/ query/
```

职责上明显做了分层:`commands/` 是用户可见入口,`tools/` 是代理可执行能力,`components/`、`screens/` 是终端界面,`services/` 隔离外部系统,`bridge/` 负责 IDE 与远程桥接,`plugins/`、`skills/` 是扩展,`tasks/`、`state/` 管任务与状态,`schemas/` 做约束与验证,`memdir/` 管持久记忆,`vim/`、`voice/`、`keybindings/` 是交互增强。

系统扩展时不会只有"往一个巨型文件里堆逻辑"一条路,这是目录分层换来的直接好处。

### 6.3 核心大文件的规模

快照 README 标出了几个大文件,体量本身就说明复杂度分布:

| 文件 | 规模 | 职责 |
| ---- | ---- | ---- |
| `QueryEngine.ts` | 约 46,000 行 | LLM 调用、流式响应、工具循环、重试、Token 计数 |
| `Tool.ts` | 约 29,000 行 | 工具基类、输入模式、权限模型、进度状态 |
| `commands.ts` | 约 25,000 行 | 命令注册与执行,按环境条件导入不同命令集 |
| `main.tsx` | — | Commander.js 解析 + Ink 渲染初始化,启动期并行预取 |

复杂度集中在三个方向:模型回路、工具抽象、命令分发。这也是大多数 AI 编程代理最终会变复杂的地方。单个 `QueryEngine.ts` 超过四万行,说明"模型交互主循环"在这个系统中承担了极多职责——这既可以是批评它的理由,也提醒你自己做同类系统时,主循环的复杂度要有意识地管理。

## §7 总体架构:一次修 bug 的完整流转

把系统抽象成主链路:

```text
用户输入
  ↓
CLI / IDE / GitHub 入口
  ↓
命令解析与上下文收集
  ↓
Query Engine 调用模型
  ↓
模型决定是否调用工具
  ↓
权限系统检查
  ↓
工具执行 / 服务访问 / 外部协议调用
  ↓
结果回流给 Query Engine
  ↓
格式化输出给用户
```

这条链路带出三个判断:每一步都在推进工作流,生成回答只是其中一环;工具与权限必须深度耦合,因为每一步执行都可能有副作用;模型被包裹在完整的软件执行框架里,从不单独工作。

熟悉传统架构的读者可以这样对应:`main.tsx` 像应用入口,`commands.ts` 像命令路由层,`QueryEngine.ts` 像业务编排核心,`tools/` 像能力适配器集合,`services/` 像基础设施服务层,`bridge/` 像外部接入层,`hooks/toolPermission/` 像安全网关。

### 7.1 具体案例:修一个时区 bug

假设用户输入"帮我修复 `src/utils/format.ts` 里 `parseDate` 函数的时区 bug"。上面的抽象结构这样串起来:

1. **入口**:`main.tsx` 接收输入,启动交互会话。
2. **上下文收集**:`context.ts` 抓取项目结构、打开的文件和 Git 状态。
3. **Query Engine** 把用户目标连同上下文发给模型。
4. **模型调用工具**:先 `GrepTool` 搜 `parseDate` 的定义位置,再 `FileReadTool` 读文件内容,定位到出问题的那行。
5. **权限检查**:读文件自动通过;后续修改文件时触发人工确认。
6. **工具执行**:模型用 `FileEditTool` 修改时区处理逻辑,期间也可能并行调 `WebSearchTool` 查时区 API 的实践。
7. **结果回流**:每次工具执行的结果都回到 Query Engine,模型据此决定下一步。
8. **输出**:修改完成后经终端 UI 展示,用户继续追问或接受改动。

工具负责执行,权限守住副作用底线,Query Engine 负责调度。Bridge 在这个场景没参与;如果用户从 VS Code 发起请求,它会在 CLI 核心与编辑器之间同步上下文与执行结果。

## §8 工具系统:真正的执行内核

### 8.1 为什么工具系统排在第一位

用户感受到"智能"的地方,不在模型说得多漂亮,而在它能不能把事做完;把事做完靠的是工具。快照 README 把 Tool System 放在架构总结第一位,位置站得住。

快照中出现的工具,覆盖了工程代理最关键的能力面:

| 工具类别 | 代表工具 | 解决的问题 |
| -------- | -------- | ---------- |
| 执行类 | `BashTool` | 执行系统命令 |
| 文件类 | `FileReadTool`、`FileWriteTool`、`FileEditTool` | 读写与局部修改文件,读支持图片、PDF、Notebook |
| 搜索类 | `GlobTool`、`GrepTool` | 定位文件与内容 |
| 网络类 | `WebFetchTool`、`WebSearchTool` | 获取外部信息 |
| 智能体类 | `AgentTool`、`SendMessageTool` | 派生子智能体、代理间通信 |
| 协议类 | `MCPTool`、`LSPTool` | 调外部协议能力 |
| 技能类 | `SkillTool` | 执行技能工作流 |
| 任务类 | `TaskCreateTool`、`TaskUpdateTool` | 管理执行过程 |
| 团队类 | `TeamCreateTool`、`TeamDeleteTool` | 多智能体团队协作 |
| 模式类 | `EnterPlanModeTool`、`ExitPlanModeTool` | 切换计划/执行模式 |
| 隔离类 | `EnterWorktreeTool`、`ExitWorktreeTool` | Git worktree 隔离 |
| 调度类 | `CronCreateTool`、`RemoteTriggerTool` | 定时与远程触发 |
| 其他 | `ToolSearchTool`、`SleepTool`、`SyntheticOutputTool` | 延迟工具发现、主动模式等待、结构化输出 |

Claude Code 不是只会改文件的工具,它把软件工程全链路收进了一块操作面板。

### 8.2 标准化的调用外壳

快照 README 给出的执行框架是:每次工具调用经历权限检查、输入验证、执行、结果序列化四步。模型不能"想到什么就调什么",所有工具都套着统一外壳。

这个设计换来四样东西:安全(先判断能不能做)、稳定(先验证输入是否合法)、可观测(每种工具产出统一格式的结果)、可扩展(新工具接入不必重新发明调用协议)。

### 8.3 抽象稳定,数量才能增长

快照 README 对工具系统的概括是"每个工具定义自己的输入模式、权限模型和执行逻辑"。这三件事稳定下来,工具数量就能持续增长而系统不失控。想自己做 AI 工具平台,这是最值得先抄的一条:**先把工具抽象做对,再去扩工具数量**。

## §9 命令系统:面向用户心智的产品层

### 9.1 斜杠命令

快照 README 显示 Claude Code 暴露了大量 `/` 前缀命令:`/commit`、`/review`、`/compact`、`/mcp`、`/config`、`/doctor`、`/login`、`/logout`、`/memory`、`/skills`、`/tasks`、`/diff`、`/theme`、`/resume`、`/share` 等。

这些命令把复杂能力按任务意图拆成可发现的入口:`/review` 对应代码审查,`/compact` 对应上下文压缩,`/mcp` 对应外部工具管理,`/doctor` 对应环境诊断,`/tasks` 对应执行过程管理。

### 9.2 命令与工具的分工

初次看这类系统容易混淆"命令"和"工具"。两者解决不同问题:命令系统面向用户,回答"用户怎么表达意图";工具系统面向代理,回答"代理怎么执行动作"。命令是产品界面层,工具是执行能力层。

### 9.3 为什么命令注册会长成大文件

`commands.ts` 约 25,000 行,支持按环境条件导入不同命令集。命令系统实际承担了汇总定义、按环境启停、对接特性开关、延迟加载重型模块这些工作。命令越多,这一层越像控制中心——既是能力强的表现,也是维护难点。

## §10 服务层:外部复杂性的隔离带

### 10.1 服务清单

| 服务 | 主要职责 |
| ---- | -------- |
| `api/` | Anthropic API、文件 API、引导配置 |
| `mcp/` | MCP 服务器连接与管理 |
| `oauth/` | OAuth 2.0 登录流程 |
| `lsp/` | 语言服务器接入 |
| `analytics/` | GrowthBook 特性开关与分析 |
| `plugins/` | 插件加载 |
| `compact/` | 上下文压缩 |
| `policyLimits/` | 组织策略限制 |
| `remoteManagedSettings/` | 远程托管设置 |
| `extractMemories/` | 自动记忆提取 |
| `tokenEstimation.ts` | Token 估算 |
| `teamMemorySync/` | 团队记忆同步 |

服务层做的是一件事:把外部系统的复杂性从 Query Engine 和 UI 层隔离出去。没有这层,模型主循环很快会被 API 认证细节、Token 估算、压缩策略、插件加载、LSP/MCP 协议处理、组织策略等事项污染,系统失去清晰边界。

### 10.2 compact 服务:长会话的生存条件

Claude Code 面对的是长时间迭代、多轮工具调用、大量项目上下文与任务状态延续,不是普通聊天。没有 compact 这样的压缩服务,上下文会很快膨胀到不可控。这个能力在 AI 编程代理里是生存条件,不是可有可无的装饰。官方后来的 hooks 事件里专门加了 `PreCompact` / `PostCompact`,可见压缩已经重要到需要外部干预的程度。

### 10.3 policyLimits 的信号

`policyLimits/` 目录说明 Claude Code 从设计上就考虑了团队约束、组织级策略与企业环境的权限边界。这是个人玩具级工具与企业可落地产品之间的分水岭之一。

## §11 Bridge:CLI 如何长成统一执行核心

快照 README 将 Bridge System 定义为连接 IDE 扩展(VS Code、JetBrains)与 Claude Code CLI 的双向通信层。这说明 Claude Code 的产品设计把 CLI 当成统一执行核心,再通过 Bridge 把能力延伸到其他宿主环境。

IDE 与 CLI 的运行约束完全不同:CLI 接近本地直接控制,IDE 强调编辑器上下文、会话同步与 UI 集成,远程控制还涉及认证、消息协议、权限回调与会话管理。不单独抽出桥接层,这些差异会直接把主应用搞乱。

快照列出的文件已经说明这是一个真正的接入子系统,不是转发几条消息的薄层:

| 文件 | 职责 |
| ---- | ------------ |
| `bridgeMain.ts` | 桥接主循环 |
| `bridgeMessaging.ts` | 消息协议 |
| `bridgePermissionCallbacks.ts` | 权限回调 |
| `replBridge.ts` | REPL 会话桥接 |
| `jwtUtils.ts` | 认证 |
| `sessionRunner.ts` | 会话执行管理 |

## §12 权限系统:能否进入真实生产环境的前提

### 12.1 为什么权限是架构核心

这类产品最危险的地方不是回答错一个概念,而是执行了不该执行的命令、改了不该改的文件、把敏感信息暴露给外部服务、在错误上下文中做了破坏性操作。权限系统因此是 Claude Code 能否成为真实生产力工具的前提。

### 12.2 快照中的权限模型

快照 README 明确写到:权限检查发生在**每一次工具调用**时,要么提示用户批准或拒绝,要么按配置的权限模式自动解决;快照列出的模式包括 `default`、`plan`、`bypassPermissions`、`auto` 等。

权限控制放在动作级别,而不是"先验一次身份、后面随便跑",粒度才够细:同一个会话里,读文件可以自动通过,写文件需要确认,执行 shell 命令可以更严格。这种精细化是 AI 工程代理进入真实工程环境的必要条件。

### 12.3 半年后的官方现状

对照 2026 年 9 月的官方权限文档,快照里的模式名全部延续,并且长出了更完整的谱系。官方目前定义六种模式:

| 模式 | 官方定义(2026-09) |
| ---- | ---- |
| `default` | 每个工具首次使用时提示(界面标签为 Manual,`manual` 是别名) |
| `acceptEdits` | 自动接受文件编辑与常见文件系统命令(`mkdir`、`touch`、`mv`、`cp`) |
| `plan` | 只读探索:可以读文件、跑只读命令,不编辑源文件 |
| `auto` | 自动批准工具调用,由后台安全检查核实动作与请求一致 |
| `dontAsk` | 自动拒绝所有本应提示的调用,已预授权的动作除外 |
| `bypassPermissions` | 跳过权限提示;官方仍警告只应在容器、虚拟机等隔离环境使用 |

对比快照时期,`acceptEdits` 与 `dontAsk` 是后来显式化出来的两个档位;`auto` 从快照里的一个模式名,发展成了带分类器安全检查的完整机制。快照与现状互相印证了一个判断:权限谱系的扩展方向是"让用户按风险场景选择信任边界",而不是简单地"放开"或"收紧"。

## §13 特性开关、惰性加载与启动性能

### 13.1 特性开关与构建期裁剪

快照 README 提到 Claude Code 使用 Bun 的 `bun:bundle` 配合特性开关做 dead code elimination:

```typescript
import { feature } from 'bun:bundle'

// 未启用的能力在构建期被完全剥离
const voiceCommand = feature('VOICE_MODE')
  ? require('./commands/voice/index.js').default
  : null
```

快照列出的标志包括 `PROACTIVE`、`KAIROS`、`BRIDGE_MODE`、`DAEMON`、`VOICE_MODE`、`AGENT_TRIGGERS`、`MONITOR_TOOL`。这些开关承担三件事:产品分层(不同用户或环境看到不同能力)、构建裁剪(未启用能力不进产物)、风险隔离(实验特性不强行进入所有运行路径)。

### 13.2 并行预取

`main.tsx` 在启动期并行预取 MDM 设置、Keychain 读取、API 预连接与 GrowthBook 初始化,且作为副作用在其他模块求值之前发出。这是产品级启动优化——只有当启动路径已经足够复杂、团队开始认真关注冷启动体验时,才会出现这类设计。

### 13.3 惰性加载

重型模块通过动态 `import()` 延迟到真正需要时才加载。快照 README 给了两个量级样本:OpenTelemetry 约 400KB,gRPC 约 700KB——对 CLI 冷启动来说,这两块不延迟加载,启动开销会立刻显现。遥测、语音、桥接、部分命令都属于"不是每次都会用到"的能力,默认路径因此可以保持轻量。

## §14 多智能体、技能与任务系统

### 14.1 子智能体与团队

快照 README 明确列出了 `AgentTool`、`coordinator/`、`TeamCreateTool`、`TeamDeleteTool` 与多智能体团队协作示例。`AgentTool` 派生子智能体,`coordinator/` 负责多智能体编排,`TeamCreateTool` 支持团队级并行。

多智能体的工程意义在于角色分工:Planner 拆解任务,Coder 负责实现,Reviewer 挑错校验。不同角色的偏置不同,拆开后系统才能在同一个总任务下形成内部分工。

### 14.2 技能系统

快照 README 将 `skills/` 描述为可复用工作流定义目录,通过 `SkillTool` 执行,用户可以添加自定义技能。技能的价值不是"多一个 prompt 文件",而是把高频工作流沉淀为可重用资产,让团队形成标准化的做事方式。命令面向用户的单次入口,技能更像面向团队与流程的工作模板。

### 14.3 任务系统

`tasks/` 目录与 `TaskCreateTool` / `TaskUpdateTool` 同时存在,说明执行过程没有被完全埋进"黑箱对话",任务状态是显式的。复杂工程任务需要拆分、状态追踪、阶段反馈与结果回收;没有任务系统,代理容易变成"看上去很忙,实际上难以审计"的黑盒。

## §15 扩展开发:官方提供的五个扩展面

这一节只讲官方文档确认的扩展方式,与快照无关,今天依然有效。Claude Code 的扩展体系是多通道的:命令、子智能体、技能、hooks、MCP 各管一段。

### 15.1 插件目录结构

官方插件文档给出的标准结构:

```text
plugin-name/
├── .claude-plugin/
│   └── plugin.json
├── commands/
├── agents/
├── skills/
├── hooks/
├── .mcp.json
└── README.md
```

`commands/` 扩展斜杠命令,`agents/` 扩展专业子智能体,`skills/` 扩展工作流能力,`hooks/` 扩展事件驱动逻辑,`.mcp.json` 接外部 MCP 工具。

值得注意的一个官方态度变化:当前插件参考文档明确建议**新插件优先用 `skills/`**,`commands/` 仍支持但不再是首选——命令与技能两种形态在官方推荐里的权重,半年间发生了倾斜。

### 15.2 plugin.json

`plugin.json` 放在 `.claude-plugin/` 下,是插件的元数据清单;按当前官方文档,`name` 是唯一必填字段,其余如 `displayName`、`version`、`description`、`author`、`license` 等可选。插件不是"把文件随手丢进目录",而是有明确元数据边界的正式扩展机制。

### 15.3 自定义命令与 allowed-tools

命令用 Markdown 文件定义,frontmatter 描述接口:

```markdown
---
description: Generate documentation for file
argument-hint: [source-file]
---

Generate comprehensive documentation for @$1
```

声明式定义、参数提示、本质是给代理下结构化任务说明——这是命令定义的三个特点。frontmatter 还支持 `allowed-tools`:按当前官方文档,它声明调用该命令(技能)的回合内**无需再询问即可使用**的工具,授权在回合结束自动清除。扩展系统因此能划出授权边界,而不是"写了命令就能随便调用所有能力"。`disallowed-tools` 则从相反方向兜底,适用于绝不该调某些工具的自治场景。

### 15.4 MCP

Claude Code 通过 MCP 把外部工具接入协议化。本地 stdio 服务器用:

```bash
claude mcp add <name> <command> [args...]
```

远程服务器如今的主流形式是:

```bash
claude mcp add --transport http <name> <url>
```

外部工具独立演进,Claude Code 不必内置所有能力,团队按需接自己的数据源与自动化系统——协议化的好处在这里体现得很直接。

### 15.5 hooks

hooks 支持事件驱动的自动化。快照时期可见的事件名(`UserPromptSubmit`、`Notification`、`Stop`、`SubagentStop`)至今全部有效;官方 hooks 文档目前列出的事件已大幅扩展,覆盖会话生命周期(`SessionStart`、`SessionEnd`)、工具调用前后(`PreToolUse`、`PostToolUse`)、上下文压缩(`PreCompact`、`PostCompact`)等阶段。`PreToolUse` 甚至能直接阻断一次工具调用。

典型用途:提交请求前做预处理,任务结束后做通知,子智能体结束后补充记录,在关键节点执行统一的团队规则。

### 15.6 自定义 subagents

CLI 支持 `--agents` 标志,用 JSON 动态定义自定义子智能体(当前文档注明启动时会校验 JSON 的合法性):

```bash
claude --agents '{"reviewer":{"description":"Reviews code","prompt":"You are a code reviewer"}}'
```

可扩展性不限于扩工具、扩命令,还包括扩角色。团队常常需要审查型、文档型、测试型、基础设施型、安全型代理各司其职;把角色扩展做成一等能力,是智能体系统比传统 CLI 先进的地方。

## §16 适用场景与采用建议

### 16.1 适合的场景

基于官方定位与快照体现的能力边界,Claude Code 适合:大型代码库理解(搜索、上下文、命令、解释联动)、多步骤工程任务(定位、编辑、执行、验证)、代码评审与修复建议、环境诊断与维护性工作、团队标准化工作流(用技能、命令、插件、hooks、MCP 沉淀规范),以及需要终端、IDE、GitHub 体验一致的场景。

### 16.2 需要谨慎的场景

几类情况要三思:高风险生产操作必须有清晰权限边界与人工确认;确定性要求极强的任务仍需要传统自动化与测试兜底;数据流转敏感的环境要先明确组织策略与合规边界;只需要单一命令的小工具场景,Claude Code 显得过重。

### 16.3 谁该先用

代码库大、上下文复杂的团队,希望把工程知识沉淀为技能与命令的团队,以及对工具治理、权限治理、流程标准化有要求的团队,收益最大;反之,代码量小、流程简单的个人项目,可以先从官方文档里的基础用法试起,不必一上来就搭扩展体系。

## §17 怎么研究这类系统

想真正看懂 Claude Code 这类工具,顺序比速度重要:

**第一步,先用一遍。** 走完 §4 的入门流程,重点体会三件事:命令与工具怎么配合,权限提示在哪些节点出现,长会话里上下文压缩何时触发。

**第二步,再读快照。** 从目录结构入手(§6),再进核心大文件。带着问题读:`QueryEngine.ts` 的主循环怎么处理工具调用失败?权限检查挂在工具生命周期的哪个位置?compact 的触发条件是什么?

**第三步,走官方扩展路径。** 用官方文档(而非快照)学插件、技能、hooks、MCP——这一段的生态演进很快,快照里的实现细节可能已经过时,官方文档才是接口契约的权威来源。

读完后可以用这几个问题检验自己:拿掉权限系统,Claude Code 会在哪些地方立即变得危险?拿掉服务层,`QueryEngine.ts` 最先被哪些复杂性污染?如果没有 Bridge 与 MCP,扩展上限卡在哪里?为自己的团队设计内部 AI 工程代理时,工具抽象、权限模型、扩展边界分别放在哪一层?——这几个问题答不顺,说明还没读懂,值得回头把 §8、§10、§12 再看一遍。

## §18 常见问题

**这是 Claude Code 官方开源吗?**
不是。镜像 README 明确强调它是泄露快照的存档,不应被视为 Anthropic 官方仓库。

**这份快照能代表今天的官方实现吗?**
不能。它是 2026-03-31 时点的快照,适合做架构研究;官方实现半年间持续演进(权限模式、hooks 事件、扩展推荐都有变化),接口契约以官方文档为准。

**原镜像仓库怎么打不开了?**
`instructkr/claude-code` 已重定向到 `ultraworkers/claw-code`,内容被替换为无关项目。原始快照请访问泄露当日的 fork 存档,如 [xFrye/claude-code](https://github.com/xFrye/claude-code)。

**能直接照着快照做自己的产品吗?**
架构思想可以学,快照本身不是最佳实践模板。值得迁移的是几条原则:工具抽象统一,权限控制到动作级,服务层隔离外部复杂性,扩展机制边界清晰,长会话必须处理上下文压缩与任务状态。

## §19 架构总结

把全文压缩成五个结论:

1. Claude Code 的本质是工程代理平台,聊天只是它的交互外壳。
2. 工具系统是执行核心,命令系统是产品入口,服务层是外部复杂性的隔离带。
3. 权限系统是架构级核心,不是附属功能;它决定了这类工具能否进入真实生产环境。
4. Bridge、MCP、插件、技能、hooks 五条扩展通道各有分工,共同支撑生态。
5. 公开快照适合做研究材料,不能替代官方文档与官方实现。

半年过去,快照里的判断经受住了检验:权限谱系在扩展而非收缩,任务与多智能体机制成了官方文档的一等公民,扩展生态的中心从命令移向技能。这份快照的最大价值,是让后来者看到一个生产级 AI 工程代理必须同时做对哪些事——模型之外的那些事。

## §20 延伸阅读与下一步

- **想把 Claude Code 用顺手**:读 [Claude Code 最佳实践大全:高热度 AI 编程指南解读]({{< relref "claude-code-best-practice-guide.md" >}}),补齐命令、工作流与常见使用误区。
- **想自己做扩展**:读 [Claude Code Skills & Plugins:AI 编程智能体技能库完全指南]({{< relref "claude-code-skills-agent-plugins-guide.md" >}}),搞明白命令、技能、插件与跨平台转换链路。
- **想系统追踪生态**:读 [Awesome Claude Code 资源指南:从看过到用起来]({{< relref "awesome-claude-code-resources-guide.md" >}}),收集常用扩展、社区项目与资料入口。
- **想做自家 AI 工程代理**:回看本文 §8、§10、§12、§15,把工具抽象、权限模型与扩展边界画成自己的架构图。

## §21 参考来源

**官方来源**

- Anthropic 官方仓库与 README:`https://github.com/anthropics/claude-code`
- 官方文档站(原 `docs.anthropic.com/en/docs/claude-code/` 已重定向至此):`https://code.claude.com/docs/en/`
- 权限模式:`https://code.claude.com/docs/en/permissions` ｜ hooks:`https://code.claude.com/docs/en/hooks` ｜ CLI 参考:`https://code.claude.com/docs/en/cli-reference`
- 插件 manifest 参考:`https://code.claude.com/docs/en/plugins-reference` ｜ 插件目录:`https://github.com/anthropics/claude-code/tree/main/plugins`

**快照与公开线索**

- 快照存档(2026-03-31 当日 fork,本文镜像侧内容据此核实):`https://github.com/xFrye/claude-code`
- 原镜像仓库(已转移,现指向无关项目):`https://github.com/instructkr/claude-code`
- 泄露发现者帖子:`https://x.com/Fried_rice/status/2038894956459290963`

**取材说明**:本文优先依据快照 README(以当日 fork 存档为准)中的目录、技术栈与架构摘要,以及 Anthropic 官方 README 与文档站中的产品定位、安装方式、权限模式、hooks 事件与扩展机制。官方侧内容核查于 2026-09-25;凡缺乏稳定公开来源支撑的内容,本文不写成确定事实。

---

文档版本 3.0 ｜ 初稿 2026-03-31,2026-09-25 修订:核实镜像仓库现状(原仓库已易主,改以当日 fork 存档为口径),对照官方文档更新权限模式、hooks 事件与扩展机制现状 ｜ 仅供教育研究用途
