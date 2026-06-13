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

> 一句话核心判断：**aisuite 不是 LiteLLM 的复刻——它在 Chat Completions 统一接口之上，加了一层 Agents API（Toolkits / MCP / Tool Policies / State Stores），并且把"如何用这些能力搭一个生产级 Agent harness"做成参考实现 OpenCoworker 一起发布。整个仓库的设计重心是"让作者本人快速搭 Agent"，不是"让作者切换不同 LLM"**。

## 一、项目坐标

| 字段 | 值 |
|------|------|
| 仓库 | [andrewyng/aisuite](https://github.com/andrewyng/aisuite) |
| 主语言 | Python（包名 `aisuite`） |
| Stars | 约 14k（截至 2026-06） |
| License | MIT |
| 配套产物 | OpenCoworker（macOS / Windows 桌面应用，源码在 `platform/`） |
| Provider 支持 | OpenAI、Anthropic、Google、Mistral、Hugging Face、AWS、Cohere、Ollama、OpenRouter 等 |

把作者 Andrew Ng 拉进来的另一面是：仓库的 README 第一屏就是 OpenCoworker 的下载链接。这是一个**"库 + 完整参考应用"的混合发布形态**——`pip install aisuite` 拿到库，下载 dmg/exe 拿到参考实现，二者共用一套核心抽象。

## 二、为什么不是 LiteLLM 的复制？

LiteLLM 的卖点是"一行切换 provider"，aisuite 表面上看起来一样（`model="openai:gpt-4o"` / `model="anthropic:claude-3-5-sonnet-20240620"`），但读完整套设计后你会发现**重心完全不同**：

| 维度 | LiteLLM | aisuite |
|------|--------|--------|
| 主抽象 | Provider router | Provider router + Agent runtime |
| Tool calling | 直通 OpenAI 格式 | `max_turns` 自动循环 + 手动物理调用两条路径 |
| 内建工具集 | 无 | files / git / shell 三个预制 toolkit |
| MCP 支持 | 需自行集成 | 一等公民，CLI / 编程两种方式 |
| State store | 无 | in-memory / file / Postgres 三选 |
| Tool policies | 无 | RequireApprovalPolicy + allow/deny + 自定义 callable |
| 参考应用 | 无 | OpenCoworker 桌面端（macOS / Windows 安装包） |

换句话说，aisuite 在 LiteLLM 的"路由"之上，多盖了一层 **Agent harness**。这一层才是它真正的价值主张。

## 三、系统地图：两层抽象

整个仓库的层次结构很清楚，可以画成一张图：

```
┌───────────────────────────────────────────────┐
│                 OpenCoworker                  │   agent harness（日常任务）
├───────────────────────────────────────────────┤
│        Agents API  ·  Toolkits  ·  MCP        │   搭 Agent 的核心抽象
├───────────────────────────────────────────────┤
│             Chat Completions API              │   跨 Provider 统一接口
├────────┬───────────┬────────┬────────┬────────┤
│ OpenAI │ Anthropic │ Google │ Ollama │ Others │
└────────┴───────────┴────────┴────────┴────────┘
```

下面逐层拆。

## 四、Chat Completions API：统一接口的细节

最基础的接口长这样：

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

几个工程细节值得拎出来：

- **命名约定 `<provider>:<model-name>`**。在 client 内部按冒号拆分做路由，字符串前缀就是 provider key，不需要单独传 `provider=` 参数。
- **响应结构强制 OpenAI 风格**。即使底层是 Anthropic SDK，返回的也是 OpenAI 风格的 `choices[0].message.content`，这样上层调用代码不用因 provider 切换而重写。
- **核心参数统一**（`temperature`、`max_tokens`、`tools` 等）走标准化映射表。某些 provider 的"非标准参数"被有意屏蔽——这是**为了跨 provider 兼容性而牺牲 provider 特性**，用之前要确认你不需要某个 provider 独有的怪参数。

### 4.1 加 Provider 的扩展点

要加一个新 provider，只要实现一个 `BaseProvider` 子类，并按命名约定放好文件：

| 元素 | 约定 |
|------|------|
| 模块文件 | `<provider>_provider.py` |
| 类名 | `<Provider>Provider`（首字母大写） |

框架会自动 discover / load 这些 adapter。这是 LiteLLM 那种"需要去中心化注册表"的方式的对立面——aisuite 把发现机制放在文件命名约定上，开发者只要照规矩写，框架就 pick up。

## 五、Tool Calling：`max_turns` 自动循环

这是 aisuite 比大多数同类工具贴心的地方。Tool calling 不只是"把函数 schema 塞给模型"，还要"自动执行工具调用、把结果回灌给模型、循环直到结束"。

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

设了 `max_turns=2` 后，框架替你做：

1. 发请求；
2. 模型返回 tool_call → 执行函数 → 把结果塞回 messages；
3. 再发请求；
4. 直到模型给出最终回答或达到 `max_turns`。

`response.choices[0].intermediate_messages` 留了完整的中间过程——这一段设计很关键：很多 agent 框架把中间调用历史藏起来，aisuite 选择**显式暴露**，方便用户做审计、断点续传、debug。

如果想要完全手控（自己写循环），省略 `max_turns`，传 OpenAI 格式的 JSON tool specs 即可。这种"自动循环 + 手控"两条路径并存是好的工程取舍——研究 / demo 阶段想偷懒用 `max_turns`，生产环境想精细控循环就直接手写。

## 六、Agents API：真正的生产级抽象

`max_turns` 适合一两次工具调用，复杂 Agent 工作流需要更结构化的抽象。aisuite 给的第一类抽象叫 `Agent` + `Runner`：

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

这套 API 的设计借鉴了 OpenAI Agents SDK 的形状（声明 Agent → Runner 执行 → 取最终输出），但自带了几个生产级特性：

### 6.1 Toolkits：预制的"文件/git/shell 工具集"

不用自己写 schema，三个常用 toolkit 直接 import：

```python
ai.toolkits.files(root=".")
ai.toolkits.git(root=".")
ai.toolkits.shell(root=".")
```

每个 toolkit 都是一组受沙盒限制的工具——比如 `files` 只允许读 `root` 下面的路径，`shell` 限制了工作目录。这是个非常重要但容易被忽略的细节：**很多 agent demo 的工具是裸函数调用，等于让 LLM 直接 `rm -rf` 用户的 home**。Toolkits 的沙盒限制了 blast radius。

### 6.2 Tool Policies：调用前的人类决策

生产环境不能"工具调了就跑"——某些操作需要人工审批：

```python
from aisuite import RequireApprovalPolicy

policy = RequireApprovalPolicy(tools=["shell.run", "git.push"])
```

或者完全自定义：

```python
def my_policy(tool_name, args):
    if tool_name == "shell.run" and "rm" in args.get("command", ""):
        return False
    return True

agent = Agent(name="safe-bot", model="...", tools=[...], tool_policy=my_policy)
```

这种"插拔式 policy"比硬编码 if-else 灵活得多——团队可以根据合规要求快速调整。

### 6.3 State Stores：跨进程 / 跨会话持久化

Agent run 完之后，结果可以存到 in-memory / file / Postgres 三种 store，下次从断点继续：

```python
result = Runner.run(agent, task, state_store="postgres://...")
# 之后
result = Runner.resume("run-id-xxx", "continue with the second part")
```

这对"长任务 + 失败恢复 + 多 Agent 协作"是基础能力。

### 6.4 MCP：一等公民

Model Context Protocol 是 Anthropic 2024 年推出的工具描述协议，2025 年开始被广泛采纳。aisuite 直接把它做成 first-class：

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

更高级的用法是用显式 `MCPClient`：

```python
async with MCPClient(server_command) as client:
    tools = client.get_tools()
    # ... 把这些 tools 喂给 Agent
```

MCP 的好处是"工具描述标准化"——任何 MCP server 都能即插即用，不需要为每个工具手写 schema。

## 七、OpenCoworker：参考实现的工程价值

`platform/` 目录下的 OpenCoworker 桌面应用是整个仓库的"实战教科书"。它做的事：

- 读文件（带权限确认）；
- 收发消息（Slack、邮件等）；
- 生成 PDF 报告、文档、表格；
- 支持定时自动化（如每日新闻摘要）；
- 跨 macOS / Windows（带安装包）。

也就是说，**库提供的所有抽象（Agent / Runner / Toolkits / MCP / State Stores / Tool Policies）在 OpenCoworker 里都被实际用过一遍**。这种"库 + 参考应用同仓库"的设计有两个好处：

1. **库的 API 不会漂移到不实用**——任何过度设计都会在 OpenCoworker 里立刻显现为"实现起来别扭"。
2. **用户可以直接 fork 参考应用改造**，不用从零搭 harness。

注意 README 把 OpenCoworker 放在最前面是有意为之——Andrew Ng 显然希望桌面 Agent 用户先看见应用，再去理解库。

## 八、安装与扩展

### 8.1 三种安装档

```bash
pip install aisuite               # 仅基础包（不含任何 provider SDK）
pip install 'aisuite[anthropic]'  # 加单个 provider
pip install 'aisuite[all]'        # 装齐全部 provider
```

这种 opt-in extras 模式很关键：默认不装 OpenAI SDK 的话，用户不会被强制提供 OpenAI API key——对只用本地 Ollama 的用户特别友好。

### 8.2 MCP 安装

```bash
pip install 'aisuite[mcp]'
```

可选，因为不是所有人都需要 MCP。

## 九、和同类方案的对比

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

aisuite 的差异化点集中在 **"工具相关抽象"（Toolkits / MCP / Policies / State Stores）**。如果你的 Agent 工作流主要是"调多个外部工具 + 长期 state 持久化 + 关键操作审批"，aisuite 比 LiteLLM 顺手得多；如果你只想要"切 provider"，LiteLLM 也够用。

## 十、采用建议

适合选 aisuite 的场景：

- **已经在 OpenAI 生态之外（比如 Anthropic / Ollama / 国内云模型）混用**，且需要统一接口 + 统一工具调用抽象。
- **需要 MCP server 即插即用**，不想自己写 adapter。
- **生产 Agent 需要 tool policy + state store + 审计日志**——这三个 aisuite 都开箱即用。
- **想搭一个桌面端 AI 应用**，OpenCoworker 是现成的参考实现。

不太适合：

- **只想切 provider、不要 agent 抽象**——LiteLLM 更轻。
- **需要 LangChain 那种 graph-based 工作流编排**（条件分支、循环、子图）——aisuite 目前不主打这块。
- **企业级合规要求 RBAC、租户隔离、审计签名**——aisuite 是 MIT 开源库，需要团队自行包装。

如果你的 Agent 已经被"换一个 provider 改一处代码"和"工具调用循环每次自己写"折磨过，aisuite 值得花半天评估。库本身写得不重（README 暗示整体在万行级别），但每一层抽象都对齐了实际工程痛点——这正是从 demo 走向 production 时最需要的东西。