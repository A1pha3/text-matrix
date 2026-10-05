---
title: "Kilo Code 解读：五个入口一个 Agent，500+ 模型任务中途可换"
date: "2026-06-18T21:03:00+08:00"
lastmod: "2026-10-02T00:00:00+08:00"
slug: "kilo-org-kilocode-coding-agent-guide"
github_repo: "Kilo-Org/kilocode"
source_key: "gh:Kilo-Org/kilocode"
description: "Kilo-Org/kilocode 是开源 AI 编码 Agent，覆盖 VS Code、JetBrains、CLI、Cloud Agent 与 Code Reviews 五个入口，500+ 模型可在任务中途切换、按 provider 实价计费，CLI 部分源自 OpenCode。"
draft: false
categories: ["技术笔记"]
tags: ["AI 编程", "MCP", "VS Code", "CLI", "开源"]
---

# Kilo Code 解读：五个入口一个 Agent，500+ 模型任务中途可换

大多数 AI 编码工具会替你做三个决定：在哪个环境里跑、用哪家的模型、按谁的价目表付费。`Kilo-Org/kilocode` 把这三个决定全部摊开给用户——入口横跨 VS Code、JetBrains、终端和网页，模型列表 500+ 且支持在任务执行到一半时切换，账单按模型 provider 的实价走、不抽成。README 用一句话概括自己的定位："open source with open pricing"。

[项目地址：Kilo-Org/kilocode](https://github.com/Kilo-Org/kilocode)，TypeScript 编写，MIT 协议，GitHub API 于 2026-10-02 验证：27,472 Stars、3,223 Forks，CLI 最新版 7.8.3（2026-10-01 发布，npm 上累计 248 个版本，发版频率接近日更）。

> 常在几个 IDE 之间切换、想自己挑模型而不愿被锁进某家订阅、或者要在 CI 里跑自治 Agent 的开发者，值得读完这篇。只想用单一模型且不离开官方客户端的，直接看末尾的适用边界。

## 一、系统地图：三层可插拔

Kilo Code 的架构可以拆成三层，每层都能单独替换：

| 层 | 你的选择 | 替换成本 |
|---|---|---|
| **入口** | VS Code 扩展、JetBrains 插件、CLI、Cloud Agent（网页）、Code Reviews（PR 自动评审） | 装哪个用哪个，账号通用 |
| **Agent** | 内置 code / plan / ask / debug，自定义 Agent 用 Markdown 文件定义 | 一个下拉框或一份 `.md` 文件 |
| **模型** | 500+ 模型，任务中途可切换；也可接本地 Ollama / LM Studio 或自带 API key | 模型选择器里点一下 |

三层之间互不绑定：你可以只用 CLI 不装扩展，可以全程用一个模型不切换，也可以一个 MCP server 都不接。本文按这三层展开，最后用一个任务流案例把它们串起来。

## 二、入口层：一套 Agent，五个入口

| 入口 | 形态 | 适合场景 |
|---|---|---|
| **VS Code 扩展** | Marketplace 扩展（`kilocode.kilo-code`） | 日常 IDE 编码，inline 补全 + Agent 面板 |
| **JetBrains 插件** | Marketplace 插件（plugin 28350） | PyCharm / IntelliJ / GoLand 等原生 IDE |
| **CLI（`kilo`）** | npm / Homebrew / AUR / 安装脚本 | 终端工作流、SSH 远程、CI/CD |
| **Cloud Agent** | 网页（app.kilo.ai/cloud） | 本地没有合适机器，任务在云端跑 |
| **Code Reviews** | 网页（app.kilo.ai/code-reviews） | PR / MR 打开时自动 AI 评审 |

注意两点。第一，新版 VS Code 扩展内置了 Kilo CLI 运行时，装扩展不需要单独装 CLI——两者共享同一套 Agent 和配置体系。第二，2026 年 6 月 README 还列着第五个入口 KiloClaw（常驻后台 Agent），现在已从 README 和公开文档撤下（产品页 app.kilo.ai/claw 目前仍可访问），官方重心明显转向了 Code Reviews 和下文的 Agent Manager，不建议新用户押注这个入口。

CLI 这条线有个常被忽略的出身：README 的 FAQ 写明 **Kilo CLI fork 自 OpenCode**，在此之上接入 Kilo 的模型网关和账号体系。所以你在终端里能看到不少 OpenCode 的影子——TUI 交互、`/` 命令风格都一脉相承。感兴趣可以对照阅读[OpenCode 解读](/posts/tech/opencode-open-source-coding-agent-guide/)。

## 三、Agent 层：四个内置角色，外加一套自定义机制

### 内置 Agent

| Agent | 职责 | 工具权限 |
|---|---|---|
| **code**（默认） | 从自然语言实现和修改代码 | 全部工具：`read`、`edit`、`glob`、`grep`、`bash`、`task`、`webfetch` + MCP |
| **plan** | 先出架构和实现计划，再动手 | 只读工具 + 受限写权限（只能写 `.kilo/plans/` 下的计划文件） |
| **ask** | 代码库问答，不改任何文件 | 只读工具 + 只读 bash 命令（`cat`、`git log` 等）；MCP 工具每次调用需批准 |
| **debug** | 故障定位与诊断 | 全部工具 |

这套角色里最容易踩的坑是名字：很多老文章（包括本文旧版）把 **plan** 写成 **Architect**。Architect 是 Kilo 前身（Roo Code 系的 legacy 扩展）里的旧模式名，官方迁移文档明确写了 `architect → plan` 的映射；现行文档站和 README 统一叫 plan。它也不是"完全不动文件"——plan 可以把计划写进 `.kilo/plans/` 目录，写完在编辑器里打开等你审。

**Review agent 的位置变过一次。** 2026 年 6 月的 README 里内置列表还有第五个 Review agent（"检查性能、安全、风格、测试覆盖"），现在 README 和文档都已移除，官方口径是："VS Code 扩展和 CLI 不含内置 Review agent，代码评审交给 code agent、自定义 agent 或 Code Reviews 产品"。如果你在别的文章里看到"Kilo 内置 Review agent"，那是旧版口径。

### Orchestrator 已废弃，别再往这上面设计

一些教程还在教"用 Orchestrator 编排多 Agent 并行"。现状是：**orchestrator 已被官方标记为 deprecated，将在未来版本移除**。替代品内置在 code / plan / debug 里——这三个有完整工具权限的 Agent 现在原生支持用 `task` 工具委派子代理（subagent），子代理有独立会话历史、共享项目目录，可前台等结果也可后台异步，支持并发多个。

编排能力现在分三层，按需取用：

| 机制 | 用途 | 隔离级别 |
|---|---|---|
| `task` 子代理 | 当前会话内的聚焦子任务（探索代码库、并行搜索） | 共享项目目录，不建 worktree |
| **Agent Manager** | 独立的并行工作流：每个会话一个 git worktree、独立终端、diff 面板 | 文件系统级隔离 |
| **Kilo Swarm** | 主会话与其 task 后代之间的消息板（`board_post` / `board_read`） | 只传消息，不启停 Agent |

Agent Manager 是 VS Code 扩展里的一个全面板标签页，用扩展内嵌的运行时，不用另装 CLI；支持从现有分支、外部 worktree 或 GitHub PR URL 导入会话。Kilo Swarm 默认开启，在 `kilo.jsonc` 里把 `shared_agent_board` 设为 `false` 可关掉。

### 自定义 Agent：一个 Markdown 文件的事

自定义 Agent（官方叫 custom modes）现在是 Markdown 文件 + YAML frontmatter：

```markdown
---
description: 只写技术文档的 Agent
mode: primary
permission:
  edit:
    "*.md": "allow"
    "*": "deny"
  bash: deny
---

你是技术文档专家，只编辑 Markdown 文件。
```

把文件放进 `.kilo/agents/`（项目级）或 `~/.config/kilo/agent/`（全局级）即可，文件名就是 Agent 名。`mode` 决定它是用户可直接选（`primary`）还是只能被其他 Agent 委派（`subagent`）；`permission` 用 glob 规则精确控制这个 Agent 能碰哪些工具和文件；`model` 可以把某个 Agent 钉死在特定模型上。不想手写的话，CLI 有交互式命令 `kilo agent create`，或者直接用自然语言让 Kilo 帮你生成。团队场景还有 organization-managed agents：组织统一下发，成员本地删不掉，同名时覆盖内置定义。

这套 frontmatter 机制是从 legacy 扩展的 `custom_modes.yaml` 迁移过来的，旧文件启动时自动转换，不用手工搬家。

## 四、模型层：500+ 模型，任务中途可换

README 原话："You pick from 500+ models, switch between them mid-task, and pay the model provider's rate with zero markup."（从 500+ 模型里挑，任务中途切换，按 provider 实价付费，零加价。）

三个关键词分别对应三件事：

**Mid-task switching。** 同一个任务执行到一半可以换模型——起草用便宜快的，正则边界、并发竞态这类硬骨头切到推理更强的，上下文完整保留，不用开新会话。VS Code 里用模型选择器或 `/models`，CLI 里同样操作；`/variant` 还能调推理强度。切换粒度可以细到"每个 Agent 记住自己上次用的模型"：给 plan 配个便宜模型、code 用主力模型，互不干扰。

**Zero markup。** Kilo 不在模型调用上加价，账单等于 provider 列表价。它赚的不是差价，这决定了它和"模型 + IDE 一体机"类产品的商业逻辑差异——你甚至可以完全不碰 Kilo 自家网关，用自带 API key（BYOK）或者指向本地 Ollama / LM Studio，再在设置里登出 Kilo Gateway，官方文档明确保证了这条路径推理不过网关。

**Auto Model。** 不想自己挑模型的话，Kilo 提供三档自动路由：`kilo-auto/frontier`（按任务类型路由到最强模型）、`kilo-auto/efficient`（会话内实时判断任务难度，路由到"跑分验证过够用"的最便宜模型，判断不了就回退到固定基线）、`kilo-auto/free`（OpenRouter 上的免费模型分流，质量打折）。efficient 档支持自定义模型池，个人和组织都能圈定"只允许用这几个模型"。底层映射在服务端更新——你选的档位不变，它背后接的模型可能换代。

配套的还有模型角色细分：main（主力）、small（会话标题、commit message 生成）、subagent（子代理默认模型）、autocomplete（行内补全）、compaction（上下文压缩）五类可以分别配置；官方在 [kilo.ai/models](https://kilo.ai/models) 维护一份基于真实使用数据的实时榜单，比任何静态推荐都新鲜。

README 里列的"当前可用模型"半年内换了两代：2026 年 6 月是 GPT-5.5、Claude Opus 4.7、Claude Sonnet 4.6、Gemini 3.1 Pro Preview；2026 年 10 月是 GPT-6 Astra、Claude Fable 5.1、Gemini 3.8 Flash、Grok 4.6、DeepSeek V4.1 Flash。列表持续变动，以官方页面为准——这也正是 Auto Model 把映射放服务端的原因。

## 五、扩展层：从 MCP 市场到 Kilo Marketplace

2026 年 6 月时这里还叫 "MCP marketplace"，现在扩成了 **Kilo Marketplace**，能装四类东西：

| 类型 | 装的是什么 | 装完发生什么 |
|---|---|---|
| **Agent** | 可复用的角色（prompt + 权限） | 出现在 Agent 选择器里 |
| **Skill** | 任务相关的指令与资源 | 会话中按需自动加载 |
| **MCP server** | 外部服务的工具（数据库、GitHub、浏览器…） | Kilo 加载 MCP 配置时自动连接 |
| **Plugin** | 钩子、自定义工具、认证与模型 provider | 写入配置的 `plugin` 数组，启动时加载 |

MCP 部分值得单独说一句：模型本身不擅长直接操作外部系统，MCP（Model Context Protocol）是它们之间的标准协议。Kilo Code 不需要为每个外部系统写专门适配，MCP 生态里有什么 server 它就能接什么。CLI 侧有完整的 MCP 管理命令：`kilo mcp add`（支持远程 URL 和本地 stdio）、`kilo mcp auth`（OAuth 授权）、`kilo mcp list`。Marketplace 里的安装都有明确作用域——项目级（`.kilo/` 目录，可提交进版本库团队共享）或全局级（用户配置目录）。

## 六、权限与自治：`--auto` 的真实边界

权限系统是 Kilo 工程化程度最高的部分，规则三动作：`allow`（放行）、`ask`（弹窗询问）、`deny`（拒绝），支持 glob 模式匹配文件路径和 shell 命令，按配置顺序取最后匹配的规则：

```yaml
permission:
  bash:
    "*": ask
    "git status *": allow
    "git push *": deny
```

两个容易被忽略的内置行为：其一，`.env` 和 `.env.*` 的读取被视为敏感操作，任何宽泛的放行规则（包括 auto 模式）都绕不过它的单独确认；其二，shell 命令会先解析再匹配——`cd /project && git status` 会被拆成两条命令分别检查。

`kilo run --auto` 的语义因此比"关掉所有弹窗"精细：**auto-approve 所有未被显式 deny 的权限**。也就是说你可以配出一套"日常操作自动放行、`git push` 和删除类命令拒绝"的自治配置，在 CI 里跑得放心一些。README 的警告也从半年前的一刀切（"disables all permission prompts"）更新成了带例外的版本——"auto-approves permission prompts unless a rule explicitly denies the action. Only use it in trusted environments."。`--auto` 是给 CI/CD 设计的，本地开发保持默认的 ask 档更稳妥。

## 七、任务流：一次"日志脱敏"功能怎么流过系统

把前面的机制串成一个具体任务：给一个 Python 项目加日志脱敏，要求盖掉 token、email、手机号。

1. **Plan 出方案。** 在面板切到 plan agent，输入需求。它读代码库（只读工具），把实现计划写进 `.kilo/plans/`：新增 `src/utils/redact.py` 提供 `redact_record()` 函数、在 `setup_logging()` 挂 `logging.Filter`、单测放 `tests/test_redact.py`。计划文件在编辑器里打开，你审完点确认。
2. **Code 起草，中途换模型。** 切回 code agent（上下文延续）。骨架阶段用便宜快的模型跑着；写到正则边界 case 时，`/models` 把模型切成推理更强的——不重启会话，已写的代码和讨论记录都在。这个 Agent 下次会记住你的选择。
3. **跑测试。** code agent 通过 bash 工具执行 `pytest tests/test_redact.py`。如果你的权限规则对 pytest 设了 `allow`，直接跑；没设就弹一次确认。测试失败它自己读输出修代码，循环到通过。探索性工作（比如"查一下还有哪些模块在直接打日志"）它可能委派给一个 explore 子代理去做，不占主会话上下文。
4. **PR 自动评审。** push 并打开 PR 后，事先在 app.kilo.ai/code-reviews 绑定的仓库（GitHub App 或 GitLab OAuth）会自动触发 AI 评审，从性能（正则是否预编译）、安全（是否漏了敏感模式）、风格、测试覆盖四个维度给结构化意见。仓库里放一份 `REVIEW.md` 可以注入团队自己的评审标准。beta 期间评审计算免费，模型推理消耗 Kilo credits。
5. **Ask 答疑。** 评审问"为什么不覆盖 structlog"，用 ask agent 查——它只读不改，跑 `grep structlog` 这类只读命令没问题，改文件的工具全部被阻断，MCP 调用每次要你点头。

一次任务穿过了：Agent 切换（plan → code → ask）、mid-task 模型切换、权限规则的放行与询问、子代理委派、云端 PR 评审。这些机制没有谁是主角，组合起来才是 Kilo Code 的日常形态。

## 八、安装

```bash
# npm
npm install -g @kilocode/cli

# 官方安装脚本
curl -fsSL https://kilo.ai/cli/install | bash

# pnpm / bun
pnpm add -g @kilocode/cli
bun add -g @kilocode/cli

# Homebrew (macOS / Linux)
brew install Kilo-Org/tap/kilo

# Arch Linux (AUR)
paru -S kilo-bin
```

装完在任意项目目录运行 `kilo` 即可开始，注册账号就能用 500+ 模型，起步不需要自己的 API key。VS Code 用户直接装扩展（`kilocode.kilo-code`），JetBrains 用户在 IDE 内 `Settings → Plugins` 搜 "Kilo Code"。

不方便用包管理器的环境，从 [Releases 页](https://github.com/Kilo-Org/kilocode/releases)下载二进制（以 v7.8.3 为例，附 SHA256SUMS 与 SBOM）：

| 平台 | 资产 |
|---|---|
| Windows x64 | `kilo-windows-x64.zip` |
| macOS Apple Silicon | `kilo-darwin-arm64.zip` |
| macOS Intel | `kilo-darwin-x64.zip` |
| Linux x64 | `kilo-linux-x64.tar.gz` |
| Linux ARM | `kilo-linux-arm64.tar.gz` |

老 CPU（无 AVX）选 `x64-baseline` 后缀，Alpine / 极简 Docker 镜像选 `musl` 后缀（静态链接，不依赖 glibc），Windows ARM64 也有对应资产（`kilo-windows-arm64.zip`）。注意 `kilo-vscode-*.vsix` 是扩展包不是 CLI。

## 九、适用边界与采用顺序

**适合**：

- 在 VS Code / JetBrains / 终端之间切换工作，想要同一套 Agent 和配置跟到哪里都能用
- 在意模型选择权：BYOK、本地模型、货比三家，不接受被锁进单一订阅
- 团队想把权限规则、自定义 Agent、评审标准（REVIEW.md）沉淀成版本库里的配置
- CI/CD 需要自治 Agent 跑测试修代码，且能接受用 permission 规则框住它的动作范围

**不适合**：

- 只想用一家最强模型、不在乎切换——官方客户端省心得多
- 完全离线且不接受任何外部服务的环境——本地 CLI + Ollama 可以离线跑，但 Cloud、Marketplace、Code Reviews 都要联网
- 强合规场景下要求 Agent 动作全程可审计回放——Kilo 的权限规则能挡住动作，但还没有独立的"审计日志"产品

**采用顺序**：

1. VS Code 扩展装起来，用默认 code agent 做一个真实小任务，感受权限弹窗的粒度
2. 配一份项目级自定义 Agent（`.kilo/agents/`）加 permission 规则，提交进版本库给团队复用
3. 在一个长任务里试一次 mid-task 切换，对比便宜的快模型和强模型在你自己的代码上的差距
4. 需要 CI 的话，先在沙箱仓库试 `kilo run --auto`，把 deny 规则配好再放到生产流水线
5. 多任务并行需求出现后，再上 Agent Manager（worktree 隔离）——这是高阶开关，不必一开始就开

## 参考与延伸

- 仓库：`https://github.com/Kilo-Org/kilocode`
- 官网与文档：`https://kilo.ai` / `https://kilo.ai/docs`
- 模型实时榜单：`https://kilo.ai/models`
- VS Code Marketplace：`https://marketplace.visualstudio.com/items?itemName=kilocode.kilo-code`
- JetBrains 插件：`https://plugins.jetbrains.com/plugin/28350-kilo-code`
- CLI npm 包：`https://www.npmjs.com/package/@kilocode/cli`
- Cloud Agent / Code Reviews：`https://app.kilo.ai/cloud` / `https://app.kilo.ai/code-reviews`
- 关键文档页：[Using Agents](https://kilo.ai/docs/code-with-ai/agents/using-agents)、[Auto Model](https://kilo.ai/docs/code-with-ai/agents/auto-model)、[Custom Modes](https://kilo.ai/docs/customize/custom-modes)、[Agent Permissions](https://kilo.ai/docs/customize/agent-permissions)、[Agent Manager](https://kilo.ai/docs/automate/agent-manager)、[Code Reviews](https://kilo.ai/docs/automate/code-reviews)

> 本文 2026-06-18 首发，2026-10-02 按 v7.8.3 与当日 README、官方文档站全面核对更新。文中模型列表、入口清单等时点敏感信息均标注了验证日期；自定义 Agent DSL 与模型路由的更多实现细节以官方文档为准，本文未作推断。
