---
title: "andrewyng/aisuite 架构拆解：Python 端 LLM 统一接口的两层抽象（Chat Completions + Agents）和它背后的工程取舍"
date: "2026-06-13T21:03:20+08:00"
slug: "aisuite-python-llm-unified-interface-guide"
description: "拆解 andrewyng/aisuite 的设计：Chat Completions API 统一多 provider，Agents API 提供生产级 agent harness。"
draft: false
categories: ["技术笔记"]
tags: ["Python", "LLM", "MCP", "Agent", "OpenAI"]
---

# andrewyng/aisuite 架构拆解：Python 端 LLM 统一接口的两层抽象（Chat Completions + Agents）和它背后的工程取舍

> 核心判断：aisuite 在 Chat Completions 统一接口之上加了一层 Agents API（Toolkits / MCP / Tool Policies / State Stores），并把"如何用这些能力搭一个生产级 Agent harness"做成参考实现 OpenCoworker 一起发布。仓库的设计重心是让作者本人快速搭 Agent，切换不同 LLM 只是底层能力之一。

## 一、项目坐标

| 字段 | 值 |
|------|------|
| 仓库 | [andrewyng/aisuite](https://github.com/andrewyng/aisuite) |
| 主语言 | Python（包名 `aisuite`） |
| Stars | 约 14k（截至 2026-06，数据来自 GitHub） |
| License | MIT |
| 配套产物 | OpenCoworker（macOS / Windows 桌面应用，源码在 `platform/`） |
| Provider 支持 | OpenAI、Anthropic、Google、Mistral、Hugging Face、AWS、Cohere、Ollama、OpenRouter 等 |

README 第一屏就是 OpenCoworker 的下载链接，这透露出仓库的发布形态：`pip install aisuite` 拿到库，下载 dmg/exe 拿到参考实现，二者共用一套核心抽象。Andrew Ng 把自己的名字放进仓库名，意味着这个项目是他本人搭 Agent 的工作台，顺便开源给社区用。

---

## 学习目标

通过本文，你会了解：

1. aisuite 的两层抽象（Chat Completions API + Agents API）分别解决什么问题
2. Toolkits、MCP、Tool Policies、State Stores 四块拼图如何协同
3. 和 LiteLLM、OpenAI Agents SDK、LangChain 的差异化取舍
4. 什么场景该选 aisuite，什么场景该用别的方案
5. 如何快速上手并评估 aisuite 是否适合你的项目

---

## 二、与 LiteLLM 的分叉点

LiteLLM 的卖点是"一行切换 provider"。aisuite 表面上看起来一样（`model="openai:gpt-4o"` / `model="anthropic:claude-3-5-sonnet-20240620"`），但读完整套设计后会发现重心完全不同：

| 维度 | LiteLLM | aisuite |
|------|--------|--------|
| 主抽象 | Provider router | Provider router + Agent runtime |
| Tool calling | 直通 OpenAI 格式 | `max_turns` 自动循环 + 手动物理调用两条路径 |
| 内建工具集 | 无 | files / git / shell 三个预制 toolkit |
| MCP 支持 | 需自行集成 | 一等公民，CLI / 编程两种方式 |
| State store | 无 | in-memory / file / Postgres 三选 |
| Tool policies | 无 | RequireApprovalPolicy + allow/deny + 自定义 callable |
| 参考应用 | 无 | OpenCoworker 桌面端（macOS / Windows 安装包） |
| 安装门槛 | 低 | 低（opt-in extras） |

aisuite 在 LiteLLM 的"路由"之上多盖了一层 Agent harness——Toolkits、MCP、Policies、State Stores 四块拼图。这层是它和 LiteLLM 拉开差距的地方。

## 三、系统地图：两层抽象

整个仓库分两层。下层是 Chat Completions API，负责把请求路由到不同 provider 并处理 tool calling 循环；上层是 Agents API，负责把 Agent 定义、工具集、审批策略、状态持久化组装成一个可运行的 harness。

```text
┌───────────────────────────────────────────────────────────┐
│                       用户代码                               │
├─────────────────────────┬─────────────────────────────────┤
│   Chat Completions API  │   Agents API                     │
│   (单轮 / 多轮对话)      │   (Agent + Runner)               │
│                         │                                  │
│   client.chat           │   Agent(name, model, tools,      │
│     .completions        │     instructions, tool_policy)   │
│     .create()           │   Runner.run() / Runner.resume() │
├─────────────────────────┴─────────────────────────────────┤
│   共享能力层                                                 │
│   - Provider Router (openai: / anthropic: / ollama: ...)   │
│   - Tool calling (max_turns 自动循环)                       │
│   - Toolkits (files / git / shell)                         │
│   - MCP (CLI 配置 / 编程式 MCPClient)                       │
│   - Tool Policies (RequireApprovalPolicy / callable)       │
│   - State Stores (in-memory / file / Postgres)             │
├───────────────────────────────────────────────────────────┤
│   Provider SDKs (opt-in extras)                             │
│   openai | anthropic | google | mistral | cohere | ...      │
└───────────────────────────────────────────────────────────┘
```

两层之间的关系是：Agents API 内部调用 Chat Completions API 完成实际的模型推理和 tool calling 循环。你可以只用下层（Chat Completions），也可以用上层（Agents）拿到完整的 harness。

### 任务如何流过系统

以仓库里的 repo-helper agent 为例，追踪一个任务从入口到输出的完整路径：

1. **定义 Agent**：`Agent(name="repo-helper", model="anthropic:claude-sonnet-4-6", tools=[files, git], instructions=...)`
2. **启动 Runner**：`Runner.run(agent, "What changed in the last commit?")`
3. **Runner 内部**：把 task 字符串包装成 user message，调用 `chat.completions.create(model, messages, tools, max_turns)`
4. **第一轮推理**：模型返回 tool_call（比如调用 `git.last_commit`）
5. **策略检查**：Runner 检查 tool_policy（如果设了），通过后才执行
6. **工具执行**：Runner 调用 git toolkit 里对应的函数，拿到 commit diff
7. **结果回填**：把 tool 结果作为 tool result message 喂回模型
8. **第二轮推理**：模型基于 diff 生成三条总结
9. **返回**：`result.final_output` 包含最终回答；如果设了 state_store，中间状态已持久化，后续可 `Runner.resume("run-id", ...)` 续跑

这条路径穿过了 Agents API → Chat Completions API → Provider SDK 三层，每一层都有明确的职责边界。

下面逐层拆。

## 四、Chat Completions API：统一接口的细节

最基础的接口：

```python
import aisuite as ai

client = ai.Client()

models = ["openai:gpt-4o", "anthropic:claude-3-5-sonnet-20240620"]

messages = [
  {"role": "system", "content": "Respond in Pirate English."},
  {"role": "user", "content": "Tell me a joke."},
]

for model in models:
  response = client.chat.completions.create(
    model=model,
    messages=messages,
    temperature=0.75,
  )
  print(response.choices[0].message.content)
```

`model` 参数用 `provider:model` 格式（比如 `openai:gpt-4o`）。一个字符串同时携带 provider 信息和模型名，路由器解析后直接分发到对应 SDK，调用方不需要为每个 provider 实例化不同的 client。OpenAI 的 Chat Completions 格式被当作 lingua franca——所有 provider 的响应都被归一化成 `response.choices[0].message.content` 结构，换 provider 时上层代码不动。

API key 通过环境变量传入（`OPENAI_API_KEY`、`ANTHROPIC_API_KEY` 等），`ai.Client()` 在初始化时读取。这和 LiteLLM、OpenAI SDK 的惯例一致。

## 五、Tool calling：max_turns 自动循环

Chat Completions API 内建了 tool calling 自动循环。传入 `tools` 和 `max_turns` 后，框架会自动处理"模型调用工具 → 执行工具 → 把结果喂回模型 → 模型继续"的循环：

```python
def will_it_rain(location: str, time_of_day: str):
  """Check if it will rain in a location at a given time today."""
  return "YES"

client = ai.Client()
response = client.chat.completions.create(
  model="openai:gpt-4o",
  messages=[{
    "role": "user",
    "content": "Can you check the weather and plan an outdoor picnic for me at 2pm in SF?"
  }],
  tools=[will_it_rain],
  max_turns=2,
)
print(response.choices[0].message.content)
```

`max_turns=2` 意味着框架最多自动执行两轮 tool calling。Python 函数直接传给 `tools` 参数，框架从函数签名和 docstring 推断出 JSON schema，再转成模型需要的 tool definition。这比手写 OpenAI 的 tool definition JSON 省事，代价是你得信任框架的 schema 推断。

为什么用 `max_turns` 控制循环上限？因为 tool calling 循环可能失控——模型反复调用工具却不收敛，或者工具一直返回错误导致死循环。设一个硬上限是最直接的防护。如果想要更细的控制（比如每轮检查工具结果再决定是否继续），可以不传 `max_turns`，退回到手动单轮调用模式。

## 六、Agents API：Agent + Runner

Agents API 把"定义 Agent"和"运行 Agent"拆成两个对象：

```python
import aisuite as ai
from aisuite import Agent, Runner

agent = Agent(
  name="repo-helper",
  model="anthropic:claude-sonnet-4-6",
  instructions="You are a careful repo assistant. Use your tools to answer from the code.",
  tools=[*ai.toolkits.files(root="."), *ai.toolkits.git(root=".")],
)

result = Runner.run(agent, "What changed in the last commit? Summarize in 3 bullets.")
print(result.final_output)
```

`Agent` 是纯配置对象——name、model、instructions、tools、tool_policy 全部在这里声明。`Runner` 是执行器，接收 Agent 和 task 字符串，内部完成消息构造、模型调用、tool calling 循环、策略检查、状态持久化。

为什么拆成两个？因为 Agent 的定义是可复用的（同一个 Agent 可以跑不同 task），而 Runner 的执行是一次性的（每次 `Runner.run` 产生一个独立的 run）。这种分离让 Agent 可以被序列化、共享、测试，而运行时的状态隔离在 Runner 里。

`Runner.run` 是同步入口，`Runner.resume` 用于续跑（见 State Stores 一节）。

## 七、Toolkits：预制工具集

aisuite 内建三个 toolkit，覆盖了 Agent 最常见的三类操作：

```python
ai.toolkits.files(root=".")
ai.toolkits.git(root=".")
ai.toolkits.shell(root=".")
```

- `files`：文件读写，`root` 参数限定可访问的目录范围
- `git`：仓库操作（last_commit、diff、log 等），同样受 `root` 约束
- `shell`：命令执行，最危险的一个

为什么预制这三个？因为绝大多数开发类 Agent 的工具需求都落在这三类里。自己写 file 读写工具不难，但每次都要处理路径校验、权限边界、错误格式——这些是重复劳动。toolkit 把这些细节封装好，`root="."` 就把工具的访问范围锁在当前目录。

`tools=[*ai.toolkits.files(root="."), *ai.toolkits.git(root=".")]` 这种写法说明 toolkit 返回的是 tool 列表，用 `*` 解包后拼进 Agent 的 tools 数组。你可以混搭 toolkit 和自定义工具。

## 八、Tool Policies：审批与拦截

shell 和 git 这类工具有破坏性（`rm -rf`、`git push --force`）。Tool Policies 在"模型决定调用工具"和"工具实际执行"之间加了一道闸门。

最简单的形式是白名单审批：

```python
from aisuite import RequireApprovalPolicy

policy = RequireApprovalPolicy(tools=["shell.run", "git.push"])
```

`RequireApprovalPolicy` 列出需要人工确认的工具名，Runner 在执行这些工具前会暂停并等待批准。

如果需要更细的规则（比如允许 `git push` 到 feature 分支但禁止 push 到 main），可以传一个 callable：

```python
def my_policy(tool_name, args):
  if tool_name == "shell.run" and "rm" in args.get("command", ""):
    return False
  return True

agent = Agent(name="safe-bot", model="...", tools=[...], tool_policy=my_policy)
```

callable 接收 `tool_name` 和 `args`，返回 `True` 放行、`False` 拒绝。这种设计把策略逻辑完全交给调用方，框架只负责在正确的时机调用它。

为什么把 policy 做成框架级能力？因为策略需要统一作用于所有工具（包括 toolkit 提供的、MCP 引入的、自定义的），如果分散在每个 tool 函数里，很容易漏掉。集中式 policy 是唯一能保证"所有 tool call 都经过检查"的方式。

## 九、State Stores：断点续跑

Agent 任务可能跑很久（多轮 tool calling、大文件处理、网络等待），中途崩溃或被中断时，如果没有持久化，所有进度丢失。State Stores 解决这个问题：

```python
result = Runner.run(agent, task, state_store="postgres://...")

# 之后
result = Runner.resume("run-id-xxx", "continue with the second part")
```

三种 backend：

- `in-memory`：默认，不持久化，进程结束即丢失
- `file`：写到本地文件，适合单机开发和测试
- `postgres`：生产级持久化，支持多进程共享和断点续跑

`Runner.run` 返回的 result 包含 `run_id`，后续用 `Runner.resume(run_id, new_task)` 可以加载之前的状态继续执行。这相当于给 Agent 加了存档读档能力。

为什么用 Postgres 做主存储？因为 Agent 状态是结构化的（消息历史、tool call 记录、中间结果），需要查询和事务保证，Postgres 的关系模型和 ACID 特性更合适。Redis 适合缓存和会话存储，做持久化状态机的主存储不是它的强项。

## 十、MCP：作为一等公民

MCP（Model Context Protocol）在 aisuite 里是一等公民——框架原生支持，不需要自己写 adapter。

CLI 方式（在 chat completions 里直接声明 MCP server）：

```python
client = ai.Client()
response = client.chat.completions.create(
  model="openai:gpt-4o",
  messages=[{"role": "user", "content": "List the files in the current directory"}],
  tools=[{
    "type": "mcp",
    "name": "filesystem",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/directory"]
  }],
  max_turns=3
)
```

编程方式（用 MCPClient 显式拉取工具列表）：

```python
async with MCPClient(server_command) as client:
  tools = client.get_tools()
  # ... 把这些 tools 喂给 Agent
```

两种方式的区别：CLI 方式把 MCP server 的生命周期交给框架管理，适合简单场景；编程方式让你自己控制 server 的启动和关闭，适合需要复用连接或做连接池的场景。

为什么把 MCP 做成一等公民？因为 MCP 生态已经有大量现成的 server（filesystem、github、slack、postgres 等），框架原生支持意味着这些 server 可以直接作为 Agent 的工具来源，省去为每个工具写 wrapper 的工作。

## 十一、安装与依赖管理

aisuite 的依赖管理走 opt-in extras 路线：

```bash
pip install aisuite    # 仅基础包（不含任何 provider SDK）
pip install 'aisuite[anthropic]'   # 加单个 provider
pip install 'aisuite[all]'   # 装齐全部 provider
```

基础包不包含任何 provider SDK，按需安装。只用 OpenAI 的用户不会被强制装 anthropic、google 等一堆 SDK；用 Ollama 的本地用户不需要装云端 provider 的包。

MCP 支持也是可选的：

```bash
pip install 'aisuite[mcp]'
```

MCP 依赖较重（涉及 subprocess 管理和异步通信），单独拆出来让不需要 MCP 的用户保持轻量安装。

## 十二、和同类方案的对比

| 维度 | aisuite | LiteLLM | OpenAI Agents SDK | LangChain |
|------|--------|---------|-------------------|-----------|
| 跨 provider | 强 | 强 | 弱（仅 OpenAI） | 中 |
| Tool calling 自动循环 | 内建 | 无 | 内建 | 内建 |
| 预制 toolkit | 文件/git/shell | 无 | 需手写 | 部分 |
| MCP 支持 | 一等公民 | 需集成 | 一等公民 | 中等 |
| Tool policy | 内建 | 无 | 内建 | 无 |
| State store | 三选 | 无 | 内建 | 中等 |
| 参考应用 | OpenCoworker | 无 | 无 | LangServe 示例 |
| 安装门槛 | 低（opt-in extras） | 低 | 低 | 高 |

aisuite 的差异化集中在工具相关抽象（Toolkits / MCP / Policies / State Stores）。如果 Agent 工作流主要是"调多个外部工具 + 长期 state 持久化 + 关键操作审批"，aisuite 比 LiteLLM 顺手；如果只想切 provider，LiteLLM 够用。

和 OpenAI Agents SDK 比，aisuite 的优势是跨 provider 和预制 toolkit；劣势是 OpenAI Agents SDK 背靠官方文档和生态，迭代速度可能更快。和 LangChain 比，aisuite 更轻、抽象层级更少，但缺少 graph-based 工作流编排能力。

## 十三、采用建议

适合选 aisuite 的场景：

- **多 provider 混用**（Anthropic / Ollama / 国内云模型），需要统一接口 + 统一工具调用抽象。
- **需要 MCP server 即插即用**，不想自己写 adapter。
- **生产 Agent 需要 tool policy + state store + 审计**——这三块 aisuite 开箱即用。
- **想搭桌面端 AI 应用**，OpenCoworker 是现成的参考实现，源码在 `platform/` 下可直接读。

不太适合：

- **只想切 provider、不要 agent 抽象**——LiteLLM 更轻，没有额外的认知负担。
- **需要 graph-based 工作流编排**（条件分支、循环、子图）——aisuite 目前不主打这块，LangGraph 或 LangChain 更合适。
- **企业级合规要求 RBAC、租户隔离、审计签名**——aisuite 是 MIT 开源库，这些能力需要团队自行包装。

如果"换一个 provider 改一处代码"和"工具调用循环每次自己写"是当前项目的痛点，aisuite 值得花半天评估。库本身写得不重，但每一层抽象都对齐了实际工程痛点：tool calling 循环、工具审批、状态持久化、MCP 集成——这些是从 demo 走向 production 时绕不开的环节。

---

## 十四、常见问题

**Q: aisuite 和 LiteLLM 能一起用吗？**
A: 可以。aisuite 负责统一接口和 Agent harness，LiteLLM 负责 provider 路由。如果你已经用 LiteLLM 且只需要路由，不必换；如果需要 Agent 能力，可以迁移到 aisuite。

**Q: OpenAI Agents SDK 和 aisuite 该选哪个？**
A: 如果用 OpenAI 且不需要跨 provider，选 OpenAI Agents SDK（官方生态迭代快）；如果需要跨 provider + 统一工具调用抽象，选 aisuite。

**Q: State Store 用 Postgres 是不是太重了？**
A: 对于生产级 Agent，State Store 需要事务保证和并发控制，Postgres 是合适选择；开发测试阶段用 `file` 或 `in-memory` 即可。

**Q: Tool Policy 会影响 Agent 的自主性和灵活性吗？**
A: 会。Tool Policy 的本质是在"让 Agent 自主决策"和"防止 Agent 做危险操作"之间做权衡。建议先设 `RequireApprovalPolicy` 只拦危险工具，后续根据运行数据调整策略。

**Q: MCP 服务器启动失败怎么排查？**
A: 先确认命令和参数正确（`npx -y @modelcontextprotocol/server-filesystem /path` 能在本机跑通），再检查框架的 MCPClient 日志。如果是网络隔离环境，需要提前把 MCP server 的 npm 包缓存到本地。

---

## 十五、故障排查

### 安装阶段

- **`pip install aisuite` 后导入失败**：确认 Python 版本 ≥ 3.10。`import aisuite` 报错时，先执行 `python --version` 确认版本。
- **安装 `[all]` 依赖冲突**：`pip install 'aisuite[all]'` 可能和现有环境的包版本冲突。建议先创建虚拟环境，或按需安装单个 provider extra。

### Provider 接入阶段

- **API Key 配置后仍报错**：检查环境变量是否设置正确。可以在 Python 里先 `import os; print(os.environ.get("OPENAI_API_KEY"))` 确认键值已读取。
- **本地 Ollama 连接失败**：确认 Ollama 已启动并监听默认端口（11434）。用 `curl http://localhost:11434/api/tags` 测试连接。

### Agent 运行阶段

- **`max_turns` 上限触发，Agent 未完成任务**：调大 `max_turns` 或改用手动单轮调用模式逐步调试。可以在 `Runner.run` 时打印 `result.messages` 查看中间步骤。
- **Tool Policy 拦截了不该拦截的工具**：检查 policy 函数逻辑。`RequireApprovalPolicy(tools=["shell.run"])` 只拦 `shell.run`，不影响其他工具。

---

## 十六、自测清单

在关闭本文前，检查你是否已经能回答下面这些问题：

1. **aisuite 的两层抽象分别是什么？各解决什么问题？** 下层 Chat Completions API（统一多 provider 接口 + tool calling 循环）；上层 Agents API（Agent 定义 + Runner 执行器 + 工具集 + 审批策略 + 状态持久化）
2. **`model` 参数的 `provider:model` 格式有什么好处？** 一个字符串同时携带 provider 信息和模型名，路由器解析后直接分发，调用方不需要为每个 provider 实例化不同的 client
3. **`max_turns` 的作用是什么？为什么需要它？** 控制 tool calling 循环上限，防止模型反复调用工具却不收敛导致死循环或超成本
4. **Toolkits 预制了哪三类工具？为什么是这三类？** files（文件读写）、git（仓库操作）、shell（命令执行）——绝大多数开发类 Agent 的工具需求都落在这三类里
5. **Tool Policy 的两种形式分别怎么用？** 白名单审批（`RequireApprovalPolicy(tools=[...])` 列出需要人工确认的工具；callable（传入自定义函数）实现细粒度规则
6. **State Store 的三种 backend 分别适合什么场景？** `in-memory`（默认，进程结束即丢失）；`file`（单机开发测试）；`postgres`（生产级持久化，支持多进程共享和断点续跑）
7. **aisuite 和同类方案相比，差异化集中在哪几块？** 工具相关抽象（Toolkits / MCP / Policies / State Stores）

如果以上 7 项你都能确认，说明你已经抓住了 aisuite 的核心设计要点。

---

## 十七、练习

### 练习一：从零跑通 aisuite 的两层抽象

1. 安装 aisuite 和基础 provider：`pip install 'aisuite[openai]'`
2. 写一个最小示例：用 Chat Completions API 调用 GPT-4o，传入一个简单消息
3. 改写为例：用 Agents API 定义一个 Agent，挂载 files toolkit，让它读取当前目录的文件列表
4. 对比两段代码的差异：哪段更短？哪段更易扩展？
5. 记录：安装耗时、首次运行耗时、遇到的错误信息

### 练习二：对比 aisuite 和 LiteLLM 的切换成本

1. 用 LiteLLM 写一个切换 provider 的示例（OpenAI → Anthropic）
2. 用 aisuite 写同样的示例
3. 对比两段代码：哪段更短？哪段需要更少的 import？
4. 如果要加上 tool calling，两段代码分别需要改几行？
5. 记录：切换 provider 时需要改的代码行数、文档查阅次数

### 练习三：为 aisuite Agent 加上 Tool Policy 和 State Store

1. 定义一个 Agent，挂载 shell toolkit
2. 写一个 `RequireApprovalPolicy`，拦截 `shell.run` 工具
3. 运行 Agent，触发工具调用，观察框架是否暂停等待审批
4. 改用 `postgres` State Store，跑一个多轮任务，然后中断程序
5. 重启程序，用 `Runner.resume` 续跑，确认状态已恢复
6. 记录：审批流程的用户体验、State Store 的写入延迟

---

## 十八、进阶路径

### 深入理解 aisuite 架构

- **读源码**：从 `aisuite/client.py` 入手，理解 Provider Router 的实现；然后读 `aisuite/agents/`，理解 Agent 和 Runner 的职责边界
- **对比 OpenAI Agents SDK**：读 OpenAI Agents SDK 的源码，对比两者的 Agent 抽象差异——aisuite 更轻，OpenAI Agents SDK 更完整
- **MCP 协议**：读 [MCP 官方规范](https://modelcontextprotocol.io/)，理解为什么 aisuite 把 MCP 做成一等公民

### 搭建生产级 Agent

- **加 Web UI**：参考 OpenCoworker 的实现（`platform/` 目录），为你的 Agent 加一个 Web 前端
- **集成向量数据库**：为 Agent 加上 RAG 能力（用 Pinecone 或 Chroma 作为知识库）
- **多 Agent 协作**：用 aisuite 搭一个多 Agent 系统（比如一个 Agent 负责代码生成，另一个负责代码审查）

### 贡献到 aisuite

- **提交 PR**：从修复文档 typo 开始，逐步熟悉代码库
- **写一个新的 toolkit**：比如一个 `database` toolkit，封装常用的数据库操作
- **改进 MCP 支持**：当前 MCP 支持还是可选的，可以帮助改进文档或测试用例

---

## 十九、资料口径说明

本文基于 andrewyng/aisuite 仓库的公开代码和 README 整理。以下说明关键判断的取径方式：

1. **两层抽象的设计意图**：来自 README 和 Andrew Ng 的公开演讲。仓库名包含作者名字，暗示这是他的工作台，这个判断有公开证据支持。

2. **和 LiteLLM 的对比**：来自两个仓库的 README 和 API 文档。对比表是本文基于公开信息整理的，不是官方立场。

3. **OpenCoworker 的定位**：README 第一屏就是下载链接，说明这是配套产物。但具体功能需要下载安装后才能确认。

4. **Stars 数**：来自 GitHub 页面（截至 2026-06），实际数字可能已有变化。

5. **代码示例**：来自仓库的 `examples/` 目录和 README。所有代码都经过人工阅读，但未经实际运行验证。

本文持续更新，欢迎通过 GitHub Issues 提交修正建议。

---

> **下一步**：从 `pip install aisuite` 开始，跑通一个最小示例，然后逐步加上 toolkit、MCP、policy、state store。比单纯读文档更有效。
