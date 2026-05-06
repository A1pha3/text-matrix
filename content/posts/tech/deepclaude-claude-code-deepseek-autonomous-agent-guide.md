---
title: "deepclaude: Claude Code 自主 Agent 循环遇上 DeepSeek V4 Pro"
date: "2026-05-06T11:41:17+08:00"
slug: "deepclaude-claude-code-deepseek-autonomous-agent-guide"
description: "deepclaude 保留 Claude Code 的工具循环，让你通过直连或本地 proxy 接入 DeepSeek V4 Pro、OpenRouter、Fireworks，并补上跨 provider 使用时最关键的兼容层。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "DeepSeek", "AI Agent", "OpenRouter", "API 代理"]
---

<!-- markdownlint-disable-file MD003 MD041 -->

deepclaude 不是重新造一个 Claude Code 替代品，而是把最贵的那一层拆出来。README 和几个关键脚本放在一起看，思路很清楚：Claude Code 已经成熟的执行框架基本不动，文件编辑、Bash、Git、子 Agent 还是原来的那套，变化集中在模型请求链路。

README 写了"17 倍更便宜"，但这只是引子。deepclaude 真正做过事的地方，是第三方后端最容易出问题的兼容层补得比较完整：模型名与档位映射、thinking block 清理、`usage` 修复、Remote Control 下的 bridge 分流。很多同类方案演示一轮问答跑得通，一到长会话和工具循环就开始出错，deepclaude 至少走过这些坑。

它把直连和本地 proxy 分成了两条路径，也没把自己包装成 Anthropic 的无损替代。

## 什么时候值得用

如果你已经习惯 Claude Code，又不想把大部分日常编码都放在 Anthropic 的价位上，deepclaude 可以做默认档位：脚手架、重构、批量修补、日常探索先走 DeepSeek；碰到复杂架构判断、含糊需求澄清、关键代码审查再切回 Anthropic。

它的边界也不藏着掖着。视觉输入、MCP server、Anthropic 原生 prompt caching 这些地方都谈不上等价；Remote Control 还需要本地 proxy 和 Anthropic bridge 配合。把它当成 Claude Code 的便宜档位，这套取舍就很好理解。

## 它没碰 Claude Code 的执行层

普通启动路径下，脚本会在当前进程链里设置一组 Anthropic 兼容环境变量，然后直接 `exec claude`：

| 环境变量 | 作用 |
| ------ | ------ |
| `ANTHROPIC_BASE_URL` | 模型 API 的目标端点 |
| `ANTHROPIC_AUTH_TOKEN` | 目标后端的 API key |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | 主任务模型 |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | 中档任务模型 |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | 轻量 / 子任务模型 |
| `CLAUDE_CODE_SUBAGENT_MODEL` | 子 Agent 模型 |
| `CLAUDE_CODE_EFFORT_LEVEL` | 默认 effort level |

这些变量都是临时注入的。POSIX 版本在脚本进程里 `export` 后直接 `exec claude`，Windows 版本则在子进程结束后清理临时环境变量，所以不会把你的系统环境长期污染掉。

因此，Claude Code 那套核心执行能力基本没动：

- 文件读写、编辑和补丁应用。
- Bash / PowerShell 执行。
- Glob / Grep 搜索。
- Git 操作。
- 多步自主工具循环。
- 子 Agent 派生。
- `/init` 这类项目初始化流程。

deepclaude 管的是模型链路，不是执行框架。

## 两条实际运行路径

直连、proxy 和 Remote Control 的关系放在一起读容易绕，拆成两条主路径就清楚了：终端直连，以及 Remote Control 搭配本地 proxy。

### 路径一：普通 CLI 直连

普通 CLI 直连没有额外桥接层，最接近“原来的 Claude Code，只是后端换了”。

要跑起来，只需要：

- 已安装 Claude Code CLI。
- 有对应 provider 的 API key。
- 不需要为了这条路径先做 `claude auth login`。
- 也不需要先启动本地 proxy。

典型安装和启动方式如下：

```bash
git clone https://github.com/aattaran/deepclaude.git
cd deepclaude
chmod +x deepclaude.sh
sudo ln -s "$(pwd)/deepclaude.sh" /usr/local/bin/deepclaude
```

如果你在 macOS 上默认使用 zsh，更合理的环境变量写法是：

```bash
echo 'export DEEPSEEK_API_KEY="sk-your-key-here"' >> ~/.zshrc
source ~/.zshrc
```

常用命令也就这几条：

```bash
deepclaude
deepclaude --status
deepclaude --backend or
deepclaude --backend fw
deepclaude --backend anthropic
deepclaude --cost
deepclaude --benchmark
```

这条路径：

- 不启动本地 proxy。
- 不提供可热切换的会话控制平面。

也就是说，普通 `deepclaude` 启动出来的 Claude Code 会直接打到目标 provider，而不是先经过 `127.0.0.1:3200`。

### 路径二：Remote Control + 本地 Proxy

浏览器里的 Remote Control 不能按同样思路处理。`claude remote-control` 本身就分成两部分：

- WebSocket bridge：固定连到 `wss://bridge.claudeusercontent.com`。
- Model API：可以通过 `ANTHROPIC_BASE_URL` 重定向。

这也是本地 proxy 存在的原因。它不能把所有流量一锅端地改到 DeepSeek，不然 bridge 会先坏掉。

启动方式：

```bash
deepclaude --remote
deepclaude --remote -b or
deepclaude --remote -b anthropic
```

这条路径的前提条件更严格：

- 先完成 `claude auth login`。
- 有可用的 `claude.ai` 订阅，因为 bridge 是 Anthropic 基础设施。
- 本机有 Node.js 18+，因为 proxy 由 Node 脚本启动。

Remote 路径里，脚本会按下面的顺序处理：

1. 先启动 `proxy/start-proxy.js`。
2. 再把 `ANTHROPIC_BASE_URL` 指到本地 `http://127.0.0.1:<port>`。
3. 清掉 `ANTHROPIC_AUTH_TOKEN`，把 bridge 认证保留给 Anthropic OAuth。
4. 最后执行 `claude remote-control`。

结果是：模型请求走本地 proxy，bridge 仍然走 Anthropic，两条链路互不干扰。

## 热切换不是默认能力

README 里的"会话内热切换"没有写错，但默认前提经常被忽略：先得有一个正在承载当前会话的本地 proxy。

`deepclaude --switch ...` 的实现很直接：它只是向本地 proxy 发一个 POST 请求。

```bash
deepclaude --switch deepseek
deepclaude --switch anthropic
curl -s http://127.0.0.1:3200/_proxy/status
curl -s http://127.0.0.1:3200/_proxy/cost
```

两条关键约束：

- `--switch` 不是代理启动器，它只是控制接口。
- 普通 `deepclaude` 直连模式默认不走本地 proxy，所以不能把 `--switch` 当成普通 CLI 的默认能力。

这些端点的定位：

- 会话已经在用 `127.0.0.1:3200` 这个 proxy → `/_proxy/mode` 才能改它的后端。
- `deepclaude --remote` 会把会话接到这个 proxy 上，热切换在 Remote Control 场景里最自然。
- README 里的 slash commands、VS Code tasks 和快捷键，本质上都是给已有 proxy 发控制请求。
- 仓库里还带了 standalone proxy 模式，手工把会话接到本地 proxy；但就现有 shell launcher 来看，普通 `deepclaude` 不会自动把 CLI 会话切到这条路径上。

proxy 暴露的几个端点，分别对应状态、切换和成本统计：

| 端点 | 作用 | 适合拿来确认什么 |
| ------ | ------ | ------ |
| `GET /_proxy/status` | 当前模式、运行时长、请求数 | 你的会话是不是已经接到 proxy |
| `POST /_proxy/mode` | 切换 DeepSeek / OpenRouter / Fireworks / Anthropic | 控制平面是否可用 |
| `GET /_proxy/cost` | token 用量和相对 Anthropic 的成本估算 | 长会话有没有真的省钱 |

如果你只是普通执行一次 `deepclaude`，然后再另开终端跑 `deepclaude --switch anthropic`，多半只会收到一句 “Proxy not running”。问题通常不在 provider，而在于这个会话压根没接到 proxy 上。

## proxy 实际补了什么

proxy 的价值主要在这些兼容细节上。每一项看起来都不大，少一项都可能在长会话里翻车。

### 1. 请求路径和鉴权头的适配

不同 provider 的 base path 并不一致：

| 后端 | 典型 base URL |
| ------ | ------ |
| DeepSeek | `https://api.deepseek.com/anthropic` |
| OpenRouter | `https://openrouter.ai/api` 或 proxy 路径里的 `https://openrouter.ai/api/v1` |
| Fireworks | `https://api.fireworks.ai/inference` 或 proxy 路径里的 `https://api.fireworks.ai/inference/v1` |

如果你自己拼接，很容易把 OpenRouter 这类地址写成 `/api/v1/v1/messages`。proxy 里专门做了 path overlap 处理，就是为了避免这种重复前缀。

鉴权头也不是同一种写法：

- DeepSeek 走 `x-api-key`。
- OpenRouter 和 Fireworks 在 proxy 路径下走 `Authorization: Bearer ...`。

这类差异放在 README 里只是几行配置，进到真实请求链路里就是能不能稳定跑起来的区别。

### 2. 模型名和档位的映射

普通 CLI 直连模式下，deepclaude 启动脚本会直接把各档位模型写成 provider 自己能识别的名字。例如：

- DeepSeek 主模型用 `deepseek-v4-pro`，子任务用 `deepseek-v4-flash`。
- OpenRouter 直连路径里当前把主任务和子任务都指到 `deepseek/deepseek-v4-pro`。
- Fireworks 直连路径里则统一指到 `accounts/fireworks/models/deepseek-v4-pro`。

proxy 路径又多了一层 `MODEL_REMAP`。当会话里仍然出现 Anthropic 语义的模型名时，proxy 会在转发 `/v1/messages` 前把它改写成目标后端能理解的名字。当前源码里，至少 DeepSeek 和 OpenRouter 的映射是显式维护的：

| Anthropic 档位 | DeepSeek proxy 映射 | OpenRouter proxy 映射 |
| ------ | ------ | ------ |
| `claude-opus-4-6` / `claude-opus-4-7` | `deepseek-v4-pro` | `deepseek/deepseek-v4-pro` |
| `claude-sonnet-4-6` | `deepseek-v4-flash` | `deepseek/deepseek-v4-flash` |
| `claude-sonnet-4-5-20250929` | `deepseek-v4-flash` | `deepseek/deepseek-v4-flash` |
| `claude-haiku-4-5-20251001` | `deepseek-v4-flash` | `deepseek/deepseek-v4-flash` |

这张表也暴露了两个边界：

- deepclaude 不是“自动理解一切未来模型名”的通用翻译层，映射表是硬编码维护的。
- 不同运行路径下，子模型的选择并不一定完全相同。普通直连和 proxy 切换模式在档位映射上更像“工程上尽量接近”，不是严格逐项同构。

### 3. thinking block 的双向清理

常见的理解是“非 Anthropic 后端不认识 thinking block，发出去前删掉就行”。源码处理得比这更严格：

- 发往非 Anthropic 后端前，删除所有 thinking block。
- 从非 Anthropic 切回 Anthropic 时，如果会话里已经混入第三方后端生成的 thinking block，也要删。

原因不是表面上的“有没有签名”，而是兼容性语义不同。源码注释写得很直接：第三方后端可能生成“带签名但 Anthropic 不认可”的 thinking block，如果只做半套过滤，切回 Anthropic 时会直接打出 400。

这不是一次性的请求转发问题，而是跨 provider 会话状态的清洁问题。

### 4. SSE 和 JSON 响应里的 `usage` 补齐

Claude Code 会依赖 `usage` 统计 token 消耗。DeepSeek 和 OpenRouter 的部分流式事件可能没有这块字段，典型缺口出现在 `message_start` 和 `message_delta`。如果不补齐，Claude Code 会直接报错：

```text
"$.input_tokens" is undefined
```

proxy 为此做了两层修补：

- 流式 SSE 响应走 `UsageNormalizer`，逐个事件补 `usage`。
- 非流式 JSON 响应走 `normalizeJsonBody()`，同样补齐缺失字段。

这不是让成本面板更好看，而是避免长工具循环被 token 统计错误打断。

### 5. Remote Control 的桥接分流

Remote Control 之所以需要 proxy，不只是为了便宜，而是因为它的两条链路根本不能混在一起：

```text
claude remote-control
  ├── Bridge WebSocket -> wss://bridge.claudeusercontent.com
  └── Model API calls  -> http://127.0.0.1:3200
                           ├── /v1/messages -> 当前激活的第三方后端
                           └── 其他路径     -> 回落到 Anthropic
```

proxy 的设计很克制：只有真正的模型消息路径会被分流，其他 Anthropic 相关请求仍然透传回官方端点。范围收得够窄，Remote Control 才比较稳。

`/_proxy/cost` 给你的也是估算，不是账单。它按源码里写死的每百万 token 价格做静态计算，再和 Anthropic 价格对比。这个数字很适合看趋势和节省比例，不适合拿去做严格结算。

## 选后端要考虑的不只是单价

只看价格表，容易得出“DeepSeek 永远最优”的结论。真用起来，至少要把延迟、推理强度和任务风险一起看。

| 后端 | 输入 $/M | 输出 $/M | 更适合什么场景 |
| ------ | ------ | ------ | ------ |
| DeepSeek | 0.44 | 0.87 | 默认首选，适合大部分日常编码、重构、修补和探索 |
| OpenRouter | 0.44 | 0.87 | 更关心美欧地区连通性或希望走聚合平台时 |
| Fireworks AI | 1.74 | 3.48 | 速度优先，愿意为更快推理多付钱时 |
| Anthropic | 3.00 | 15.00 | 难问题、关键审查、高风险改动或复杂架构判断 |

README 的直观判断大致对得上实际效果：

- 轻度使用时，deepclaude 路线大概可以把成本压到 Anthropic 的一成左右。
- 重度使用时，节省比例仍然很可观。
- 自动循环越多，DeepSeek 的自动上下文缓存越能拉开成本差距。

但"便宜"不等于"完全等价"。适合多数场景的做法是高频日常任务走 DeepSeek，复杂推理、关键审查或高风险修改切回 Anthropic。

## 能力的保留与限制

对已经用惯 Claude Code 的人来说，主体工作流基本没丢。

### 保留得比较完整的能力

- 文件读写、编辑与补丁应用。
- Bash / PowerShell 执行。
- Glob / Grep 搜索。
- Git 操作。
- 多步工具循环。
- 子 Agent 派生。
- `/init` 项目初始化。
- thinking mode 本身仍然可用，只是跨 provider 时需要兼容清理。

### 明确受限的能力

| 能力 | 现状 | 应该怎样理解 |
| ------ | ------ | ------ |
| 图片 / 视觉输入 | 不支持 | DeepSeek 的 Anthropic 兼容端点不支持图像输入 |
| 并行工具调用 | 受限 | README 说后端能力更强，但 Claude Code 默认仍以顺序调用为主 |
| MCP server 工具 | 不支持 | 兼容层没有把 MCP 工具链完整透传过去 |
| Anthropic prompt caching | 不等价 | DeepSeek 有自己的自动缓存，但不是 Anthropic 的 `cache_control` 语义 |

如果你的工作流高度依赖视觉输入、MCP server，或者需要尽量贴近 Anthropic 原生缓存行为，那么 deepclaude 不是近乎无损的替换。

## 渐进式上手

按复杂度递增的顺序试，可以省掉很多排障时间：

1. 先用普通 CLI 直连跑最核心的文件读写、命令执行和多步修补。
2. 再执行 `deepclaude --status` 和 `deepclaude --benchmark`，确认 key、连通性和基础延迟都正常。
3. 只有确定需要浏览器会话或热切换时，再上 `deepclaude --remote`。
4. 最后再配置 `~/.claude/commands/`、VS Code tasks 或快捷键，把 `/_proxy/mode` 控制平面接进去。

每次只多一层复杂度，出了问题也更容易定位到 provider、proxy、bridge 还是本地环境。

## 常见误区

### 1. `claude auth login` 不是所有路径的通用前提

- 普通 CLI 直连靠的是 provider API key。
- Remote Control 才需要 Anthropic 的 OAuth 和 `claude.ai` 订阅。

把这两条路混在一起，会让很多本来两分钟能跑通的场景平白多出一道门槛。

### 2. `--switch` 不是“顺手帮你启用代理”

`deepclaude --switch` 只会发控制请求，不会自动创建一个正在承载当前会话的 proxy。看到 “Proxy not running” 时，先别怀疑 provider，先确认自己的会话是不是本来就没挂到 `127.0.0.1:3200`。

### 3. `--benchmark` 测的是通路，不是智商

源码里的 benchmark 做的是一次很小的 `POST /v1/messages` 请求，测 HTTP 是否成功以及大致延迟。它适合用来排查 key、端点和网络，不适合拿来判断“这个 provider 的复杂推理到底强不强”。

### 4. 跨 provider 切换后如果仍然出现诡异 400，优先重开会话

proxy 已经尽力清理 thinking block，但跨 provider 的历史上下文本来就是最脆的一层。如果你在 Anthropic 和第三方后端之间频繁来回切，还叠加了长上下文和多轮工具调用，重开一次会话通常比硬扛当前上下文更省时间。

### 5. 不同模式下，低档位模型不一定完全一样

普通 CLI 直连和 proxy 切换模式在模型档位的处理上更像“尽量兼容”，不是“一模一样的严格镜像”。如果你在意子 Agent 用的是 `Pro` 还是 `Flash`，最好直接读一下当前脚本设置，而不是默认它们在所有路径下都严格一致。

## 适用与不适用的场景

deepclaude 大致适合这几类情况：

- 已经在用 Claude Code，不想迁移到另一套 Agent 生态。
- 绝大多数工作是脚手架、重构、排障、批量修补、日常探索。
- 对成本敏感，希望把高频任务压到更便宜的后端。
- 需要 Remote Control，但不想把每一次模型思考都锁死在 Anthropic 价格上。

不太适合的情况也很明确：

- 工作流高度依赖图像理解或截图分析。
- 强依赖 MCP server 工具。
- 经常处理高风险、强推理、错一次代价很高的生产级任务。

后一类场景不是“完全不能用 deepclaude”，而是更适合把它当默认档位，再把 Anthropic 当高难任务的回退档位。

## 总结

如果你的主要工作就是在终端里改文件、跑命令、做重构和排障，先从普通 CLI 直连开始。用几天之后，DeepSeek 能不能覆盖自己的日常任务，自然会有判断。

如果需要浏览器会话、热切换和成本统计，再把 proxy 和 Remote Control 加上。反过来，如果工作高度依赖图片、MCP server 或强推理，直接用 Anthropic 更省心。

deepclaude 的价值不在于替掉一切，而在于把一大批其实没必要用 Opus 解决的问题，从 Opus 的价格带里挪出来。

## 参考资料

- [deepclaude 项目主页](https://github.com/aattaran/deepclaude)
- [deepclaude README](https://github.com/aattaran/deepclaude/blob/main/README.md)
- [proxy/README：Remote Control 代理说明](https://github.com/aattaran/deepclaude/blob/main/proxy/README.md)
