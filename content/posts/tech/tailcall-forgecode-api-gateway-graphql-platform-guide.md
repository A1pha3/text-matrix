---
title: "ForgeCode 解读：Tailcall 团队转身之后，GraphQL 网关变成了终端 coding agent"
date: "2026-04-12T02:31:39+08:00"
lastmod: "2026-10-03"
slug: tailcall-forgecode-api-gateway-graphql-platform-guide
github_repo: "tailcallhq/forgecode"
source_key: "gh:tailcallhq/forgecode"
description: "Tailcall GraphQL 网关已停更：npm 停在 2026-01-22，GitHub 主仓库被删除，官网重定向到 forgecode.dev。同一团队接棒的项目是 ForgeCode——Rust 写的终端 coding agent，靠 ZSH `:` 前缀命令系统把 AI 缝进 shell。本文基于 2026-10-03 的仓库与官网读数。"
draft: false
categories: ["技术笔记"]
tags: ["Coding Agent", "AI 编程", "Rust", "CLI", "终端工具"]
---

# ForgeCode 解读：Tailcall 团队转身之后，GraphQL 网关变成了终端 coding agent

这篇文章写过一版完全不同的内容。原标题叫"Tailcall ForgeCode：19.3K Stars·API Gateway + GraphQL 平台"，通篇在讲一个 GraphQL 网关怎么配置——那些内容现在是双重错误的：数字是错的，项目本身也已经没了。2026-10-03 重新核查时，事实链是这样的：Tailcall 的 npm 包停在 2026-01-22 的 v1.6.14，GitHub 主仓库 `tailcallhq/tailcall` 已被删除（404，无重定向），官网 `tailcall.run` 301 到 `forgecode.dev`。团队把全部精力投给了一个新东西：ForgeCode（仓库名 `tailcallhq/forgecode`，二进制叫 `forge`），一个 Rust 写的终端 coding agent，当前 7,638 stars / 1,463 forks（2026-10-03 GitHub API 读数），最新版本 v2.14.0 发布于 2026-10-01。

所以本文做两件事：给搜 Tailcall 进来的读者把停更时间线交代清楚；把 ForgeCode 按当前仓库的真实状态重新讲一遍。旧文里所有 TypeScript 配置示例已整体作废——Tailcall 的真实配置从来都是 GraphQL SDL 文件加 `@server`、`@http` 指令，`defineConfig` 那套 API 在它身上从未存在过。

## 一、先把三个名字理清

围绕这个团队有三个名字，容易混：

| 名字 | 是什么 | 现状 |
|------|--------|------|
| Tailcall | Rust 写的高性能 GraphQL 网关（npm 包 `@tailcallhq/tailcall`） | 2026 年初停更，仓库已删除，官网重定向 |
| ForgeCode | 团队新业务，终端 coding agent，公司主体仍叫 Tailcall, Inc. | 活跃开发，官网 forgecode.dev |
| Forge | 上面这个产品的 CLI 二进制名和仓库名（`tailcallhq/forgecode`） | 与 ForgeCode 同物 |

仓库地址本身也有一段沿革：`antinomyhq/forge` 现在 301 重定向到 `tailcallhq/forgecode`，npm 上 `@antinomyhq/forge` 和 `forgecode` 两个包名指向同一个 2.13.21 版本——项目从 Antinomy 名下迁到 Tailcall 名下，两个品牌最终合并成一家。公开资料显示 Tailcall 创始人 Tushar Mathur 现在以 ForgeCode CEO 的身份活动，两个项目是同一拨人。

ForgeCode 的自我定位经历了微调：GitHub 仓库描述写 "AI enabled pair programmer"，README 标题是 "Forge: AI-Enhanced Terminal Development Environment"，官网则叫它 "World's #1 Coding Harness"。三种说法指向同一类东西——常驻终端、能读改代码、能跑命令的 AI 编程工具，与 Claude Code、Codex CLI 同一赛道。

## 二、Tailcall 停更时间线：给旧文读者的交代

如果你正在用或考虑用 Tailcall 网关，这些日期是决策依据，全部可复核：

| 时间 | 事件 | 出处 |
|------|------|------|
| 2023-11 | npm 首发 `@tailcallhq/tailcall` 0.14.11 | npm registry |
| 2024-07 | GitHub 主仓库约 1,214 stars | Wayback Machine 快照 |
| 2024-12 | `tailcallhq/forgecode` 仓库创建，团队转向开始 | GitHub API created_at |
| 2025-05-07 | npm 发布 1.6.11 后中断 | npm registry |
| 2025-12 至 2026-01 | 零星发布 1.6.12–1.6.14，最后一步 2026-01-22 | npm registry |
| 2026-05-26 之后 | GitHub 主仓库被删除（现为 404，无改名重定向） | Wayback 快照 + 当日 API |
| 现在 | `tailcall.run` 301 到 `forgecode.dev` | 2026-10-03 实测 |

旧 Tailcall 的真实形态值得留一句记录，因为它和旧文的描述完全不同：配置就是一个标准的 `.graphql` 文件，加上 `@server`、`@upstream`、`@http` 几个指令，把 schema 和解析方式写在同一个文件里，`tailcall start ./xxx.graphql` 启动——这是删除前 README 的原话。旧文里那套 `defineConfig`、`live: true`、`rateLimiting` 的 TypeScript API 属于凭空构造，照着写跑不通。

还在跑 Tailcall 的团队要注意：npm 上的 1.6.14 是终版，不会再有安全修复；主仓库删除意味着 issue、文档、benchmark 仓库的入口都没了，只能靠镜像和 Wayback 找资料。把它当冻结组件继续跑可以，把它写进新项目的技术选型不行。

## 三、Forge 的系统地图

Forge 的全部复杂性可以放进一张四行表里，先看分界再看细节：

| 层 | 组成 | 作用 |
|----|------|------|
| 使用模式 | TUI 交互、One-shot CLI、ZSH 插件 | 同一个 `forge` 二进制的三种入口 |
| Agent | forge（默认）、sage、muse | 写代码 / 只读研究 / 出计划三种角色 |
| 托管服务 | ForgeCode Services | 可选的云端上下文引擎与语义搜索 |
| 扩展层 | skills、AGENTS.md、自定义 agent、自定义命令、MCP | 行为定制与外部工具接入 |

判断先给在这里：Forge 在这条赛道上的差异点不是模型多、不是 prompt 写得好，而是 ZSH 插件模式——它不要求你搬进一个专属 TUI，而是把 `:` 前缀命令缝进现有 shell，让"问 AI"和"跑 ls"变成同一种动作。官网首页也把 "Built atop ZSH" 放在特性第一位。代价是明显的：这套体验深度绑定 zsh，bash/fish 用户拿不到它的核心卖点。

## 四、三种使用模式

### TUI 交互模式

裸跑 `forge` 进入交互界面，这是多步任务的主战场：

```bash
forge                              # 新会话
forge --agent sage                 # 以指定 agent 启动
forge -C /path/to/project          # 指定项目目录
forge --sandbox experiment-name    # 建 git worktree + 分支，在隔离环境里折腾
forge conversation resume <id>     # 恢复某次保存的会话
```

`--sandbox` 值得单独说：它用 git worktree 加独立分支制造隔离现场，试验性改动不碰工作区，这在同类工具里不算常见配置项。

### One-shot 模式

带 `-p` 参数跑完即退，适合脚本和管道：

```bash
forge -p "Explain the purpose of src/main.rs"
echo "What does this do?" | forge
forge commit                # AI 生成提交信息并提交
forge commit --preview      # 只打印建议的提交信息
forge suggest "find large log files"   # 自然语言翻译成 shell 命令
```

### ZSH 插件模式

`forge setup` 安装插件后，shell 里以 `:` 开头的行会被拦截送给 Forge，其余照常执行：

```zsh
: refactor the auth module        # 发给当前 agent
:sage how does the cache work?    # 指定只读研究 agent
:commit                           # AI 读 diff、写信息、直接提交
:suggest "list files by size"     # 生成的命令进输入缓冲区，回车前可改
```

`:` 命令覆盖会话管理（`:new`、`:conversation`、`:clone`、`:retry`、`:compact`、`:dump`）、配置切换（`:model` 仅当前会话生效，`:config-model` 写入全局配置）、诊断（`:doctor`、`:info`、`:tools`）等约三十条，别名体系完整（`:c` 等于 `:conversation`，`:a` 等于 `:agent`），全表见仓库 README 的 "Quick Reference" 节。在 prompt 里输入 `@` 再按 Tab，可以模糊搜索并把文件以 `@[filename]` 形式挂进上下文。

## 五、三个内置 agent：读写分离

Forge 的 agent 分工建立在一条约束上：谁能改文件，谁只能看。

| Agent | 别名 | 职责 | 改文件 |
|-------|------|------|--------|
| forge | （默认） | 实现：写功能、修 bug、跑测试 | 是 |
| sage | `:ask` | 研究：读架构、追数据流 | 否 |
| muse | `:plan` | 规划：分析结构，把实现计划写进 `plans/` 目录 | 仅限 plans/ |

这个设计把"问"和"做"拆开：探索性问题交给 sage，不会顺手改坏东西；muse 产出的计划是落盘的文件，可以被审阅、被 `execute-plan` skill 消费，而不是停在聊天记录里。三者共享会话上下文，切换用 `:agent` 或直接 `:sage <prompt>`。

自定义 agent 放 `.forge/agents/`（项目级）或全局对应目录，Markdown 加 YAML front-matter，可指定模型、工具集和系统提示；仓库里 `crates/forge_repo/src/agents/` 下的三个内置定义就是现成模板。项目级覆盖全局级。

## 六、任务流案例：一个登录 bug 走完 Forge

把机制串起来看一次真实使用。假设登录接口在并发下偶发 401：

```zsh
:sage 用户报了偶发登录 401，帮我查 token 校验的逻辑链路
```

sage 只读，翻代码、追中间件调用顺序，给出结论：token 刷新存在竞态，两个请求同时触发 refresh 时后者会拿到已作废的 token。这段分析留在会话里。

```zsh
:muse 出一个修复计划，要考虑向后兼容
```

muse 接手同一会话的上下文，把方案写进 `plans/fix-token-refresh-race.md`：引入单飞刷新、失败重放队列、三个测试点。你打开这份计划文件改了两处措辞。

```zsh
: 按 plans/fix-token-refresh-race.md 执行，先改再补测试
```

默认的 forge agent 读计划、改代码、跑测试。跑偏了 `:retry` 重来；上下文太长 `:compact` 收缩。

```zsh
:commit-preview
```

生成的提交信息进缓冲区，你补上 issue 编号再回车。整个过程没离开过 zsh，也没有一个环节要求你复制粘贴代码块。

这个案例里每一步的机制——sage 只读约束、muse 写 plans/、会话跨 agent 共享、`:commit-preview` 进缓冲区——都来自 README 对应小节的原文描述，不是演绎。

## 七、ForgeCode Services：本地工具加一层云端运行时

Forge 的二进制完全本地，但它有一层可开启的云服务。官网称其为 "runtime layer"，三项能力均系官网自述口径：上下文引擎（自称在检索基准上以最多少 93% 的 token 达成更优召回）、工具调用护栏（拦截非法参数并自动纠正）、skill 引擎（帮模型在对的时机选对的 skill）。

启用流程：`:login` 选 ForgeServices，Google 或 GitHub 浏览器认证，无需手动申请 API key；然后 `:sync` 索引当前项目，`:tools` 里看到 sem_search 即生效。语义搜索的索引默认发往 `api.forgecode.dev`，可用 `FORGE_WORKSPACE_SERVER_URL` 指到自建服务器。

数据边界要划清楚：执行 `:sync` 时，项目文件内容会被送到 ForgeCode 的服务器做索引——官方文档明确写了这一点，`.ignore` 文件可以排除不想同步的路径。不开 Services、不跑 `:sync`，代码不离开本机；开了，就按"文件内容上传"理解。对源码敏感的团队，这是一个需要写进安全评审的开关，不是背景噪音。

## 八、配置、扩展与那些容易踩的路径

Forge 的定制面分四层，各自的落点不同：

**forge.yaml**（项目根）管模型与行为边界：`model` 定默认模型，`temperature`、`max_walker_depth`（目录遍历深度）、`custom_rules`（全员遵守的规约）、`max_tool_failure_per_turn` 和 `max_requests_per_turn`（防失控的两道闸，后者触发时会先问你）。

**AGENTS.md**（项目根或全局）放持久指令：编码规范、提交信息风格、禁区。每次会话开始自动读取。

**Skills** 是可复用工作流，SKILL.md 加 YAML front-matter。内置三个：`create-skill`（脚手架）、`execute-plan`（执行 plans/ 里的计划）、`github-pr-description`（从 diff 生成 PR 描述）。查找顺序：项目 `.forge/skills/` > 全局 > 二进制内嵌，上层覆盖下层。

**MCP** 走标准协议：项目根 `.mcp.json` 优先于全局配置，`forge mcp list/import/show/remove/reload` 管理生命周期，stdio 和 SSE（`url` 字段）两种服务器都能接。

路径方面有一个 README 与源码不一致的点，照源码说：配置主目录现行默认是 `~/.forge`（配置文件 `~/.forge/.forge.toml`），`~/forge` 是旧路径——`FORGE_CONFIG` 环境变量优先，其次已存在的 `~/forge` 会被继续兼容读取，`forge config migrate` 做显式迁移。README 部分段落还写着 `~/forge/.forge.toml`，以源码 `crates/forge_config/src/reader.rs` 的解析顺序为准。

常用环境变量挑几个：`FORGE_TOOL_TIMEOUT`（单工具执行上限，默认 300 秒）、`FORGE_TRACKER=false`（关闭遥测元数据）、`FORGE_LOG`（tracing 过滤语法）。完整的重试、HTTP、TLS 调参面在 README 的 Advanced Configuration 节，够细。

## 九、模型接入：宽 provider 面与凭据管理

`forge provider login` 是官方推荐的凭据配置方式，交互式选择 provider 并录入凭据；直接往 `.env` 写 key 的方式已标记废弃（存量凭据会在首次运行时自动迁移到文件存储）。可列出的 provider 按 README 的凭据变量走一遍：OpenAI、Anthropic、Google Vertex AI、OpenRouter、Requesty、x-ai、z.ai（含 coding plan 订阅变量）、Cerebras、Neuralwatt、OrcaRouter、Meta、IO Intelligence、ForgeCode Services，另有 OpenAI 兼容通道（`OPENAI_URL` 指向任意兼容端点）——Groq 和 Amazon Bedrock 的官方接法就是走这条通道，后者需要先部署 AWS 的 Bedrock Access Gateway。仓库描述宣称 "300+ models"，`forge list model` 看本机实际可用面。

两个特殊路径提醒：Vertex AI 要先 `gcloud` 认证再取 access token 录入；z.ai 这类有订阅计划的 provider 区分普通 API key 和 coding plan 专用变量，选错会话费用按 API 计。

## 十、采用建议

**可以现在就试的**：重度 zsh 用户。`:` 前缀模式解决的是"AI 工具打断 shell 工作流"这个真实痛点，`forge setup` 五分钟就能验出合不合手；想在多个 provider 间自由切换、不想被单一厂商订阅绑定的人，Forge 的 provider 面和 `:model` 会话级切换是同类工具里较宽的。

**该等等的**：bash/fish 用户——插件模式用不上，Forge 退化成一个普通的终端 agent，与现有工具拉不开差距，先观望；把数据边界卡得极严的团队——若既不能接受 `:sync` 上传又不打算自建 workspace server，核心的语义搜索能力直接缺位，需要先算清这笔账。

**对 Tailcall 存量用户**：网关无上游支持已成事实，冻结版本可继续跑但不要新增依赖；迁移方向是社区里其他活跃的 GraphQL 网关项目，别等 Tailcall 复活。

**上手顺序**：`curl -fsSL https://forgecode.dev/cli | sh` 安装 → `forge provider login` 配模型 → 裸跑 `forge` 在 TUI 里熟一遍 → `forge setup` 装 ZSH 插件 → 高频之后再把 AGENTS.md 和自定义 agent 立起来。官网首页那段 "TermBench 2.0 81.8% 领先" 的榜单数据是官网自述（对比项 Open Code 51.7%、Claude Code 58%、Warp 61.2% 同为该页口径），第三方可复核的独立评测尚未见到，把它当参考信息而不是决策依据。

## 十一、资源与核查说明

- 仓库：<https://github.com/tailcallhq/forgecode>（7,638 stars / 1,463 forks，2026-10-03 GitHub API 读数，Apache-2.0，主语言 Rust，创建于 2024-12-08）
- 官网：<https://forgecode.dev>（`tailcall.run` 已 301 至此）
- npm：`forgecode`（2.13.21，2026-07-31 发布；旧包名 `@antinomyhq/forge` 同版本）
- 最新版本：v2.14.0（2026-10-01，含 Claude Opus/Sonnet 5.5 支持修复）
- Tailcall 停更证据：npm registry（`@tailcallhq/tailcall` 终版 1.6.14，2026-01-22）、Wayback Machine（主仓库最后快照 2026-05-26，1,439 stars；官网 2026-03-08 快照仍正常）
- 本文中 Forge 的全部命令、配置项、agent 职责均对照 2026-10-02 的 main 分支（提交 3f55977）README 与源码核实；路径解析以 `crates/forge_config/src/reader.rs` 为准
