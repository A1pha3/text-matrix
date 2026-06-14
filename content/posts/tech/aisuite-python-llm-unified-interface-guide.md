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

LiteLLM 的卖点是"一行切换 provider"，aisuite 表面上看起来一样（`model="openai:gpt-4o"` / `model="anthropic:claude-3-5-sonnet-20240620"`），但读完整套设计后**重心完全不同**：

| 维度 | LiteLLM | aisuite |
|------|--------|--------|
| 主抽象 | Provider router | Provider router + Agent runtime |
| Tool calling | 直通 OpenAI 格式 | `max_turns` 自动循环 + 手动物理调用两条路径 |
| 内建工具集 | 无 | files / git / shell 三个预制 toolkit |
| MCP 支持 | 需自行集成 | 一等公民，CLI / 编程两种方式 |
| State store | 无 | in-memory / file / Postgres 三选 |
| Tool policies | 无 | RequireApprovalPolicy + allow/deny + 自定义 callable |
| 参考应用 | 无 | OpenCoworker 桌面端（macOS / Windows 安装包） |

也就是说，aisuite 在 LiteLLM 的"路由"之上，多盖了一层 **Agent harness**。这一层才是它真正的价值主张。

## 三、系统地图：两层抽象

整个仓库的层次结构很清楚，可以画成一张图：

```text

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
```textpython
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
```textpython
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
```textpython
ai.toolkits.files(root=".")
ai.toolkits.git(root=".")
ai.toolkits.shell(root=".")
```textpython
from aisuite import RequireApprovalPolicy

policy = RequireApprovalPolicy(tools=["shell.run", "git.push"])
```textpython
def my_policy(tool_name, args):
    if tool_name == "shell.run" and "rm" in args.get("command", ""):
        return False
    return True

agent = Agent(name="safe-bot", model="...", tools=[...], tool_policy=my_policy)
```textpython
result = Runner.run(agent, task, state_store="postgres://...")
# 之后
result = Runner.resume("run-id-xxx", "continue with the second part")
```textpython
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
```textpython
async with MCPClient(server_command) as client:
    tools = client.get_tools()
    # ... 把这些 tools 喂给 Agent
```textbash
pip install aisuite               # 仅基础包（不含任何 provider SDK）
pip install 'aisuite[anthropic]'  # 加单个 provider
pip install 'aisuite[all]'        # 装齐全部 provider
```textbash
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

aisuite 的差异化点集中在 **"工具相关抽象"（Toolkits / MCP / Policies / State Stores）**。如果你的 Agent 工作流主要是"调多个外部工具 + 长期 state 持久化 + 关键操作审批"，aisuite 比 LiteLLM 顺手得多；如果只想"切 provider"，LiteLLM 也够用。

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