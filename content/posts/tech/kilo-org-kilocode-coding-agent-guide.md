---
title: "Kilo Code 全平台编码 Agent：500+ 模型切换、Open Pricing 与 MCP 生态"
date: "2026-06-18T21:03:00+08:00"
slug: "kilo-org-kilocode-coding-agent-guide"
description: "Kilo-Org/kilocode 是开源 AI 编码 Agent，覆盖 VS Code / JetBrains / CLI / Cloud Agent / KiloClaw 五大入口，500+ 模型 mid-task 切换、零加价按 provider 计费、自带 MCP 市场。"
draft: false
categories: ["技术笔记"]
tags: ["KiloCode", "AI编码Agent", "MCP", "VSCode", "JetBrains", "CLI", "CodeAgent"]
---

# Kilo Code 全平台编码 Agent：500+ 模型切换、Open Pricing 与 MCP 生态

`Kilo-Org/kilocode` 想回答的不是"AI 写代码能写多好"，而是"AI 写代码的边界到底在哪一层"。它的答案是：**入口要全、模型要可选、价格要透明、能力要可插拔**。和大多数 AI IDE 把模型绑死在自家后端不同，Kilo Code 直接把 500+ 模型摆在台面上，让用户在中途切换——同一个任务里，先用 GPT-5.5 起草、再用 Claude Sonnet 4.6 review（截至撰写时这两个模型均在可用列表内），账单按 provider 实际费率走，零加价。

## 目录

- [学习目标](#学习目标)
- [一、仓库定位：5 大入口的 Agentic 编码平台](#一仓库定位5-大入口的-agentic-编码平台)
- [二、5 个内置 Agent 与"切 Agent"心智](#二5-个内置-agent-与切-agent-心智)
- [三、核心机制：500+ 模型 + Mid-Task Switching](#三核心机制500-模型--mid-task-switching)
- [四、能力清单与 MCP 市场](#四能力清单与-mcp-市场)
- [五、任务如何流过系统：从 Plan 到 Review 的端到端案例](#五任务如何流过系统从-plan-到-review-的端到端案例)
- [六、Autonomous Mode（CI/CD 场景）](#六autonomous-modecicd-场景)
- [七、安装与各入口差异](#七安装与各入口差异)
- [八、适用边界](#八适用边界)
- [九、采用顺序与决策建议](#九采用顺序与决策建议)
- [十、自测题](#十自测题)
- [十一、进阶路径](#十一进阶路径)
- [十二、参考与延伸](#十二参考与延伸)

## 学习目标

读完本文后，你应当能够：

1. 说清 Kilo Code 5 大入口（VS Code / JetBrains / CLI / Cloud Agent / KiloClaw）各自的使用场景与限制，并判断自己该从哪个入口入手
2. 解释 mid-task switching 在工程上的两个直接收益（实时折中、降级路径），并知道何时该切模型、何时不该切
3. 区分 5 个内置 Agent（Code / Plan / Ask / Debug / Review）的职责边界，避免在错误阶段调用错误 Agent——尤其是 `Ask` 只读不改、`Plan` 先出方案再动文件
4. 根据"是否需要 MCP 扩展、是否需要 CI/CD 自治、是否接受联网"判断团队是否适合采用 Kilo Code
5. 在本地复现一次"Plan → Code → Review"的端到端任务流，并至少完成一次 mid-task 模型切换

## 一、仓库定位：5 大入口的 Agentic 编码平台

Kilo Code README 把"哪里都能跑"放在最前面：

| 入口 | 形态 | 关键能力 |
|---|---|---|
| **VS Code** | Marketplace 扩展 | 默认 IDE 体验，inline autocomplete、tab 接受 |
| **JetBrains** | Marketplace 插件 | PyCharm / IntelliJ / GoLand 等原生 IDE 适配 |
| **CLI (`kilo`)** | npm / Homebrew / AUR | `kilo run --auto` 跑 CI/CD |
| **Cloud Agent** | Web（app.kilo.ai/cloud） | 远程执行，本地无需机器 |
| **KiloClaw** | Always-on 后台 Agent | 持续任务调度 |

README 里有一句值得单独拎出来："open source with open pricing"——开源 + 开放定价。前者意味着整个 Agent 逻辑、模型路由、自定义 Agent 框架都在 GitHub 上；后者意味着 Kilo 不会在模型调用上加 markup。

## 二、5 个内置 Agent 与"切 Agent"心智

Kilo Code 提供了 5 个开箱即用的 Agent 角色：

1. **Code**：默认 Agent，从自然语言生成 / 修改代码
2. **Plan**：先出架构和实现计划，再动文件
3. **Ask**：只读不改，专做代码库问答
4. **Debug**：故障定位 + trace
5. **Review**：PR 评审，覆盖性能、安全、风格、测试覆盖度

切换 Agent 是一次心智切换——`Plan` 不是"写完代码再写计划"，而是"先写计划、用户确认、才动代码"；`Ask` 完全不动文件，只回答问题。这种设计把"什么时候需要 AI 改、什么时候只是问"拆得很干净。

> 文档里明确支持"自定义 Agent"，可以组合能力面，但 README 没有展开自定义 DSL 的细节，本文不深入。

## 三、核心机制：500+ 模型 + Mid-Task Switching

Kilo Code 的"模型可换"不是简单的下拉框——它支持 **mid-task switching**，即同一个任务执行到一半可以切换模型。README 原话：

> You pick from 500+ models, switch between them mid-task, and pay the model provider's rate with zero markup.

这对实际工程有两个直接收益：

- **延迟 vs 质量 vs 成本的实时折中**：起草阶段用便宜快模型（Gemini Flash / Claude Haiku），最终交付前再切到 Opus / GPT-5.5
- **降级路径**：当首选模型在某些 provider 上 rate-limit 或挂了，可以无感切走

定价上 Kilo Code 不在模型调用上加 markup。README 用了 "zero markup" 这个词——用户实际付的钱等于 provider 列表价。对比很多 AI IDE 把"自营模型"作为默认入口的玩法，Kilo Code 这条路更接近"中间层 / 路由器"，而不是"模型 + IDE 一体机"。

## 四、能力清单与 MCP 市场

Kilo Code 的功能矩阵（直接取自 README）：

- **Code generation**：从自然语言生成跨多文件改动
- **Inline autocomplete**：ghost-text + tab 接受
- **Self-checking**：Agent 自己 review 自己写的代码
- **Terminal & browser control**：跑命令、自动化浏览器
- **MCP marketplace**：接入第三方 MCP server 扩展能力
- **500+ models + mid-task switching**

MCP marketplace 是它的"可插拔面"。模型本身不擅长直接操作外部系统（数据库、CI、监控），MCP 提供了一套标准协议——Kilo Code 不需要为每个外部系统写专门适配，只要接 MCP server 就行。市面上 MCP server 越多，Kilo Code 能直接调用的外部系统就越多，不用等官方逐个写适配。

## 五、任务如何流过系统：从 Plan 到 Review 的端到端案例

抽象的"5 个 Agent + 500+ 模型 + MCP"很难想象在一次真实任务里如何配合。下面用一个最小但完整的例子把机制串起来。

场景：用户在 VS Code 里要给一个 Python 项目加"日志脱敏"功能，要求覆盖 `logging` 模块输出的 token、email、手机号。

### Step 1：Plan Agent 出方案

用户在 Kilo Code 面板选 `Plan` Agent，输入需求。Plan Agent 不动文件，只产出一份实现计划：

- 新增 `src/utils/redact.py`，提供 `redact_record(record: logging.LogRecord) -> str`
- 在 `src/logger.py` 的 `setup_logging()` 里挂一个 `logging.Filter`
- 单测放 `tests/test_redact.py`，覆盖三类敏感字段
- 不动现有 handler 配置

用户审完计划，点确认，Kilo Code 自动切到 `Code` Agent。

### Step 2：Code Agent 起草，mid-task 切模型

Code Agent 默认用一个便宜快模型（假设 Gemini Flash）先把 `redact.py` 和 `test_redact.py` 骨架写出来。写到正则细化阶段，用户在面板里把模型切到 Claude Sonnet 4.6——因为正则边界 case 多，需要更强的推理。切换不需要重启会话，上下文保留。

### Step 3：Terminal 控制跑测试

Code Agent 写完代码后，通过 Kilo Code 的 terminal control 能力直接在 VS Code 集成终端里跑 `pytest tests/test_redact.py`。如果测试失败，Agent 读取失败输出，回到 Step 2 修代码，循环直到测试通过。

### Step 4：Review Agent 评审

用户切到 `Review` Agent，让它对本次改动做 PR 评审。Review Agent 不改代码，只输出意见：性能（正则是否预编译）、安全（是否漏了 SSRF 日志）、风格（是否符合现有 naming convention）、测试覆盖度（是否覆盖了多行日志）。

### Step 5：Ask Agent 答疑

如果 Review 提了"为什么不覆盖 structlog"，用户可以用 `Ask` Agent 问"本项目有没有用 structlog"——Ask 只读不改，扫一遍代码库给出回答，不会偷偷动文件。

### 机制串场

这一次任务里穿过了：Agent 切换（Plan → Code → Review → Ask）、mid-task 模型切换（Flash → Sonnet）、terminal control（跑 pytest）、只读与可写 Agent 的边界隔离（Ask 不动文件）。如果接了 MCP server（比如内部代码规范库），Review 阶段还能自动比对团队规范。这就是 Kilo Code 把"入口、模型、能力"三层可插拔设计在一次任务里的实际形态。

## 六、Autonomous Mode（CI/CD 场景）

Kilo CLI 提供 `--auto` 开关，把所有权限提示关掉，Agent 进入完全自治模式：

```bash
kilo run --auto "run tests and fix any failures"
```

README 给了一个非常明确的警告：

> `--auto` disables all permission prompts and lets the agent execute any action without confirmation. Only use it in trusted environments.

这是给 CI/CD 设计的——pipeline 里跑测试、跑 fix、跑 deploy，不能每一步都卡在权限弹窗。但反过来说，本地开发、PR 评审、生产运维这些场景里 `kilo run`（不带 `--auto`）会更安全。

## 七、安装与各入口差异

### VS Code

直接装 `kilocode.Kilo-Code` 扩展。安装完注册账号就能拿到 500+ 模型访问权，截至撰写时包括 GPT-5.5、Claude Opus 4.7、Claude Sonnet 4.6、Gemini 3.1 Pro Preview（具体可用列表以官方页面为准）。

### CLI

```bash
# npm
npm install -g @kilocode/cli

# 一行安装
curl -fsSL https://kilo.ai/cli/install | bash

# Homebrew (macOS / Linux)
brew install Kilo-Org/tap/kilo

# Arch Linux (AUR)
paru -S kilo-bin
```

装完在项目根目录 `kilo` 即可。

### JetBrains

到 JetBrains Marketplace 装插件，或在 IDE 里 `Settings → Plugins` 搜 "Kilo Code"。

### 二进制（GitHub Releases）

对于不能跑 Node.js 的环境，仓库 Releases 页提供多平台二进制：

| 平台 | 资产 |
|---|---|
| Windows | `kilo-windows-x64.zip` |
| macOS Apple Silicon | `kilo-darwin-arm64.zip` |
| macOS Intel | `kilo-darwin-x64.zip` |
| Linux x64 | `kilo-linux-x64.tar.gz` |
| Linux ARM | `kilo-linux-arm64.tar.gz` |

注意 `x64-baseline` 是给没有 AVX 的老 CPU 用的兼容构建，`musl` 是给 Alpine / 极简 Docker 镜像用的静态构建。

## 八、适用边界

**适合**：

- 已经在 VS Code / JetBrains / 终端里写代码，需要 AI Agent 嵌入工作流
- 希望跨 IDE、跨平台用同一个 Agent
- 想自己选模型、不愿意被锁定到某家 provider
- 需要 MCP 扩展（数据库 / CI / 内部工具）
- CI/CD pipeline 想接自治 Agent 跑测试 + 修代码

**不适合**：

- 只想用单一最强模型、不关心模型切换——这种情况下官方客户端可能体验更顺
- 完全不接受任何外部依赖的离线环境——Kilo Cloud Agent / Marketplace 都要联网
- 对 `--auto` 模式信任度低、但又必须 CI/CD 自治的场景——目前没有"半自治 + 审计"档位

## 九、采用顺序与决策建议

### 入门顺序

1. **从 VS Code 扩展入手**：体验门槛最低，能直接感受 5 个 Agent 角色
2. **把 CLI 装上**：在终端跑 `kilo`，熟悉非 IDE 交互
3. **试一次 mid-task switching**：在长任务里中途切换模型，对比效果
4. **再上 `--auto` / Cloud Agent / KiloClaw**：把这三个当"高阶开关"用，不要一上来就全开

### 决策矩阵

| 场景 | 推荐入口 | 推荐 Agent | 是否需要 MCP |
|---|---|---|---|
| 日常 IDE 编码 | VS Code 扩展 | Code + Ask | 视团队工具链而定 |
| 大型重构前的方案设计 | VS Code / JetBrains | Plan | 否 |
| PR 评审 | VS Code / Cloud Agent | Review | 接代码规范 MCP 更好 |
| CI/CD 跑测试 + 修代码 | CLI (`kilo run --auto`) | Code + Debug | 接 CI / 监控 MCP |
| 长期后台任务 | KiloClaw | 自定义 | 通常需要 |
| 无本地机器的远程任务 | Cloud Agent | 任意 | 视任务而定 |

### 关键决策点

- **是否需要 mid-task switching**：如果你的任务都是短任务（< 5 分钟），切换收益不大；长任务（多文件重构、跨模块改动）才值得用
- **是否接受联网**：Cloud Agent / Marketplace / KiloClaw 都依赖网络，纯离线场景只能用本地 CLI + 本地模型
- **是否信任 `--auto`**：CI/CD 环境可以开，本地开发建议关——目前没有"半自治 + 审计日志"的中间档位

## 十、自测题

以下问题用来检验你是否真的读懂了上面的机制。答案都在正文里，但建议先自己回答再回头核对。

1. **Agent 边界**：`Ask` Agent 和 `Code` Agent 在文件系统权限上的区别是什么？如果你只想让 AI 帮你理解一段陌生代码，该选哪个？
2. **模型切换**：mid-task switching 和"开新会话换模型"的区别在哪？前者保留了什么、省掉了什么？
3. **定价模型**：Kilo Code 的 "zero markup" 具体指什么？如果你用 Claude Sonnet 4.6 跑了一个任务，账单是怎么算的？
4. **Autonomous Mode**：`kilo run --auto` 适合什么场景、不适合什么场景？为什么 README 强调 "only use it in trusted environments"？
5. **MCP 价值**：如果不接任何 MCP server，Kilo Code 还能做什么？接了 MCP server 之后多了什么能力？
6. **入口选择**：一个纯终端用户（不用 VS Code / JetBrains）想用 Kilo Code，该走哪个入口？一个想在 CI/CD 里跑自治 Agent 的团队呢？
7. **任务流**：回顾第五节的端到端案例，如果 Review Agent 发现了安全漏洞，下一步该切到哪个 Agent？为什么不能直接让 Review Agent 改代码？

## 十一、进阶路径

### 入门 → 核心

1. 装 VS Code 扩展，跑一次 `Code` Agent 写个简单函数
2. 试一遍 5 个 Agent，感受"什么时候该切"
3. 在一个长任务里做一次 mid-task switching，观察上下文是否保留

### 核心 → 进阶

1. 把 CLI 装上，在终端跑 `kilo`，对比 IDE 内外的交互差异
2. 接一个 MCP server（比如 GitHub MCP），让 Agent 直接操作外部系统
3. 在 CI/CD 里试 `kilo run --auto`，但先在沙箱环境跑

### 进阶 → 专家

1. 研究自定义 Agent 框架（README 提了但没展开，需要看源码）
2. 对比 Kilo Code 的模型路由策略与自建 LiteLLM / OpenRouter 的差异
3. 评估 KiloClaw（always-on Agent）在长期任务调度上的适用边界

## 十二、参考与延伸

- 仓库：`https://github.com/Kilo-Org/kilocode`
- VS Code Marketplace：`https://marketplace.visualstudio.com/items?itemName=kilocode.Kilo-Code`
- CLI npm：`https://www.npmjs.com/package/@kilocode/cli`
- Cloud Agent：`https://app.kilo.ai/cloud`
- Code Reviews：`https://app.kilo.ai/code-reviews`
- KiloClaw：`https://app.kilo.ai/claw`

> 本文证据全部来自 Kilo Code README。未在 README 中明确给出的"自定义 Agent DSL 细节"、"模型路由策略"、"MCP 鉴权机制"，本文未作推断。文中提到的模型版本号（GPT-5.5、Claude Opus 4.7、Claude Sonnet 4.6、Gemini 3.1 Pro Preview）截至撰写时在可用列表内，后续可能变动。
