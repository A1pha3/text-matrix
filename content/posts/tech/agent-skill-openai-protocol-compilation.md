---
title: "Agent Skill 的 HTTP 底层：Skill 如何被编译成 OpenAI 协议原语"
date: "2026-05-30T22:33:00+08:00"
slug: "agent-skill-openai-protocol-compilation"
description: "Skill 不是协议层概念，而是一个纯粹的应用层抽象。本文通过 7 步协议交互拆解 Skill 的完整生命周期，揭示 Skill 如何被 Cursor 等 IDE 编译成 system prompt 片段、tool schema 和多轮 tool calling 循环的组合。"
draft: false
categories: ["技术笔记"]
tags: ["Agent Skill", "OpenAI协议", "LLM", "HTTP", "Cursor", "Tool Calling"]
---

# Agent Skill 的 HTTP 底层：Skill 如何被编译成 OpenAI 协议原语

Skill 是这两年 AI 编程工具最火的概念之一。读网页、写文件、执行命令——各种 skill 听起来像在给大模型装插件。但追问一句"这个 skill 在 HTTP 层面怎么跟大模型交互的"，大多数人就卡住了。

这篇文章来自腾讯云开发者张敏在司内论坛的一次技术追问。他实现了一个读取微信公众号文章的 skill 后，顺藤摸瓜梳理了整个底层链路。结论反直觉但很清晰：**Skill 在 OpenAI 兼容协议里根本不存在**——它本质是一种"给 LLM 写使用手册，让 LLM 通过已有工具自己照着做"的设计模式。

---

## 协议映射：Skill 在 HTTP 层面究竟是什么

在 OpenAI 兼容协议中，不存在 `skill` 这个字段或角色。Skill 最终被 Cursor（或其他 AI IDE）**编译**成三种协议原语的组合：

1. **System/Developer Message** — 把 Skill 的指令文本注入到 system prompt 中
2. **Tools Definition** — 把 Skill 需要用到的工具（如 Shell、Read）注册为 `tools` 数组
3. **Multi-turn Tool Calling Loop** — LLM 根据注入的指令，自主决策发起 `tool_calls`，宿主执行后把结果喂回去

用一句话总结：

> **Skill = 动态注入的 system prompt 片段 + 预定义的 tool schema + 多轮 tool calling 循环**

它完全复用了 OpenAI 协议已有的 tool calling 机制，不需要任何协议扩展。Skill 的全部"魔法"都发生在 system prompt 的措辞和 SKILL.md 文件的编写质量上——本质是一种 prompt engineering + 文件系统的组合。

---

## 前提：OpenAI 兼容协议的基础

本文面向对 OpenAI 兼容协议有基本了解的同学。如果刚接触这个领域，只需知道一件事：大模型只会"对话"，所谓的工具调用（tool calling）也只是特化的聊天功能——模型输出一个结构化的 `tool_calls` 字段，客户端负责执行对应的工具，然后把结果通过 `role: "tool"` 消息塞回给模型继续处理。

协议本身不知道也不关心什么是"skill"。

---

## Skill 生命周期：7 步协议交互拆解

以 Cursor + mp-read skill 为例，完整走一遍 Skill 从发现到执行的 7 个步骤。其他工具（OpenClaw）也是完全相同的机制。

### 第 0 步：Skill 发现与描述摘要注入

在你打开 Cursor、还没说话的时候，Cursor 就已经扫描了 `.cursor/skills/`、`.agents/skills/` 等目录，收集了所有 Skill 的 `name` + `description`（来自 SKILL.md 的 YAML frontmatter），然后把它们作为**静态上下文**塞进 system prompt。

以 mp-read skill 为例，SKILL.md 的 frontmatter 是：

```yaml
name: mp-read
description: >-
  Extract plain text from Tencent MP (mp.weixin.qq) articles
  using a headless Chrome browser. Use when the user wants to
  read, fetch, extract, summarize, or reference a MP article,
  or when a mp.weixin.qq URL appears in conversation.
```

这段信息被注入成类似这样的 system prompt 片段（简化版）：

```
<available_skills>
<agent_skill fullPath="/path/to/mp-read/SKILL.md">
  Extract plain text from Tencent MP (mp.weixin.qq) articles
  using a headless Chrome browser. Use when the user wants to
  read, fetch, extract, summarize, or reference a MP article,
  or when a mp.weixin.qq URL appears in conversation.
</agent_skill>
</available_skills>
```

注意此时 SKILL.md 的**正文还没有被读取**。这就是 Cursor 文档里说的 "Progressive Loading"——只先放名字和描述，不浪费 token。

### 第 1 步：用户发问，触发 Skill

假设用户说：

> 帮我读一下这篇公众号文章：https://mp.weixin.qq.com/s/HHPK6QvclYaxlDg28elN8w

Cursor 作为客户端，构造出的第一次 API 请求大致如下（忠实于 OpenAI 协议）：

```json
{
  "model": "claude-4.6-opus",
  "messages": [
    {
      "role": "system",
      "content": "You are an AI coding assistant...\n\n<available_skills>\n<agent_skill fullPath=\"/Users/123456/.../mp-read/SKILL.md\">\n  Extract plain text from Tencent MP...\n</agent_skill>\n</available_skills>\n\nWhen a skill is relevant, read and follow it IMMEDIATELY as your first action..."
    },
    {
      "role": "user",
      "content": "帮我读一下这篇公众号文章：https://mp.weixin.qq.com/s/HHPK6QvclYaxlDg28elN8w"
    }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "Read",
        "description": "Reads a file from the local filesystem...",
        "parameters": {
          "type": "object",
          "properties": {
            "path": { "type": "string", "description": "The absolute path of the file to read." },
            "offset": { "type": "integer" },
            "limit": { "type": "integer" }
          },
          "required": ["path"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "Shell",
        "description": "Executes a given command in a shell session...",
        "parameters": {
          "type": "object",
          "properties": {
            "command": { "type": "string" },
            "description": { "type": "string" },
            "working_directory": { "type": "string" },
            "block_until_ms": { "type": "number" }
          },
          "required": ["command"]
        }
      }
    }
  ],
  "tool_choice": "auto"
}
```

两个关键点：

1. `tools` 数组是 Cursor **预定义好**的，不是 Skill 定义的。Skill 本身不声明工具——它只是告诉 LLM "你可以用 Read 来读文件，用 Shell 来执行命令"。
2. system prompt 里有 Skill 的描述摘要加上一条关键指令：**"When a skill is relevant, read and follow it IMMEDIATELY"**。

### 第 2 步：LLM 响应——决定先读 SKILL.md

LLM 看到用户提到了 `mp.weixin.qq`，匹配到了 system prompt 中 mp-read skill 的描述，于是按照指令"先读 Skill 文件"。它返回的响应是：

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_abc123",
            "type": "function",
            "function": {
              "name": "Read",
              "arguments": "{\"path\": \"/path/to/mp-read/SKILL.md\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ]
}
```

这就是 Skill 的"加载"——本质上就是 **LLM 自己发起了一次 Read tool call，读取 SKILL.md 文件**。Skill 不是被"安装"进去的，而是被 LLM 自己"学"进去的。

### 第 3 步：Cursor 执行 tool call，返回结果

Cursor 在本地执行 `Read("/Users/123456/.../mp-read/SKILL.md")`，拿到文件内容，然后构造下一轮请求：

```json
{
  "messages": [
    { "role": "system", "content": "（同上，省略）" },
    { "role": "user", "content": "帮我读一下这篇公众号文章..." },
    {
      "role": "assistant",
      "content": null,
      "tool_calls": [
        {
          "id": "call_abc123",
          "type": "function",
          "function": {
            "name": "Read",
            "arguments": "{\"path\": \"/Users/123456/.../mp-read/SKILL.md\"}"
          }
        }
      ]
    },
    {
      "role": "tool",
      "tool_call_id": "call_abc123",
      "content": "---\nname: mp-read\ndescription: >-\n  Extract plain text from MP...\n---\n\n（...完整 SKILL.md 内容...）"
    }
  ],
  "tools": [ "（同上，Shell、Read 等工具定义）" ]
}
```

到这一步，SKILL.md 的全部内容已经通过 `role: "tool"` 消息进入了 LLM 的上下文窗口。LLM 现在拥有了完整的"技能说明书"。

### 第 4 步：LLM 按照 Skill 指令行动——前置检查

LLM 读完 SKILL.md 后，按照 "Prerequisites Check" 章节的指示，先检查环境（章节中要求用户必须准备好一个 `cookie.txt` 文件）。它返回：

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_def456",
            "type": "function",
            "function": {
              "name": "Shell",
              "arguments": "{\"command\": \"which mp-read\", \"description\": \"Check mp-read is installed\"}"
            }
          },
          {
            "id": "call_ghi789",
            "type": "function",
            "function": {
              "name": "Read",
              "arguments": "{\"path\": \".../cookie.txt\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ]
}
```

注意这里**一次返回了两个 `tool_calls`**——这是 OpenAI 协议支持的**并行 tool calling**。LLM 判断这两个检查互相独立，所以同时发起。

### 第 5 步：工具结果回传

Cursor 并行执行两个 tool call，然后把结果都塞进 messages：

```json
{
  "messages": [
    "（...之前的所有消息...）",
    {
      "role": "assistant",
      "tool_calls": [
        { "id": "call_def456", "function": { "name": "Shell", "arguments": "..." } },
        { "id": "call_ghi789", "function": { "name": "Read", "arguments": "..." } }
      ]
    },
    { "role": "tool", "tool_call_id": "call_def456", "content": "/usr/local/go/bin/mp-read" },
    { "role": "tool", "tool_call_id": "call_ghi789", "content": "skey=xxxxxxx; p_skey=yyyyyyy; RIO_TCOA=zzzzzz..." }
  ]
}
```

### 第 6 步：LLM 执行核心命令

前置检查通过，LLM 按照 SKILL.md 中的 Usage 章节，构造并发起实际的 mp-read 命令：

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_jkl012",
            "type": "function",
            "function": {
              "name": "Shell",
              "arguments": "{\"command\": \"mp-read 2026/0316_mp_read/cookie.txt 'https://mp.weixin.qq.com/s/HHPK6QvclYaxlDg28elN8w'\", \"description\": \"Extract MP article text\", \"block_until_ms\": 120000}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ]
}
```

注意 `block_until_ms: 120000`——这正是 SKILL.md 中明确要求的。LLM 从 Skill 文档中"学到"了这个参数应该设多大。整个过程没有任何魔法，只是 LLM 在认认真真地照着手册执行。

### 第 7 步：最终响应

Shell 执行完毕，mp-read 的 stdout 输出（文章全文）通过 `role: "tool"` 消息回传给 LLM。LLM 最终生成一个纯文本响应：

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "这篇公众号文章的内容如下：\n\n# 文章标题\n\n文章正文内容...",
        "tool_calls": null
      },
      "finish_reason": "stop"
    }
  ]
}
```

---

## 协议交互时序图

```mermaid
sequenceDiagram
    participant C as Cursor（客户端）
    participant L as LLM（服务端）

    Note over C: 启动时扫描 .cursor/skills/<br/>提取 name + description

    rect rgb(240, 248, 255)
        Note right of C: Round 1
        C->>L: POST /chat/completions<br/>system: skills 摘要 + tools<br/>user: "帮我读公众号文章"
        L-->>C: assistant.tool_calls<br/>[Read(SKILL.md)]
    end

    Note over C: 本地执行 Read(SKILL.md)

    rect rgb(255, 248, 240)
        Note right of C: Round 2
        C->>L: tool: SKILL.md 完整内容
        Note over L: LLM 获得完整技能说明书
        L-->>C: assistant.tool_calls<br/>[Shell("which mp-read"),<br/>Read(cookie.txt)]
    end

    Note over C: 并行执行两个 tool call

    rect rgb(240, 255, 240)
        Note right of C: Round 3
        C->>L: tool: "/usr/local/go/bin/mp-read"<br/>tool: "skey=xxx;p_skey=yyy..."
        L-->>C: assistant.tool_calls<br/>[Shell("mp-read cookie.txt URL",<br/>block_until_ms=120000)]
    end

    Note over C: 执行 mp-read（耗时约 30s）

    rect rgb(255, 240, 255)
        Note right of C: Round 4
        C->>L: tool: 文章全文
        L-->>C: assistant.content: "这篇文章..."<br/>finish_reason: "stop"
    end
```

---

## Skill 的协议映射表

把 Skill 的概念一一对应到 OpenAI 协议层面：

| Skill 概念 | 协议映射 |
|------------|----------|
| Skill 发现（scan directories） | 纯客户端行为，不涉及协议 |
| Skill 摘要（name + description） | 注入到 `messages[0].role = "system"` 的文本中 |
| Skill 加载（读取 SKILL.md） | LLM 发起 `tool_calls: [Read(SKILL.md)]`，结果通过 `role: "tool"` 回传 |
| Skill 指令执行 | LLM 按读到的 SKILL.md 内容，自主发起后续 `tool_calls` |
| Progressive Loading | 先在 system prompt 放摘要（省 token），LLM 需要时再 Read 全文 |
| `scripts/` 目录 | LLM 通过 `Shell` tool call 执行脚本 |
| `references/` 目录 | LLM 通过 `Read` tool call 按需读取参考文档 |

---

## 核心洞察：Skill 是一种给 LLM 写使用手册的设计模式

Skill 在协议层面**完全不存在**。它是一种"给 LLM 写使用手册，让 LLM 通过已有工具自己照着做"的设计模式。

整个过程就是：

1. 在 system prompt 里告诉 LLM "你有这些技能手册可以查"
2. LLM 通过 `Read` 工具自己去读手册
3. LLM 读完手册后，按手册说的步骤，通过 `Shell`/`Read` 等工具一步步执行

这种设计的精妙之处在于：**它完全复用了 OpenAI 协议已有的 tool calling 机制，不需要任何协议扩展**。

Skill 的全部"魔法"都发生在两处：

- **system prompt 的措辞**：如何让 LLM 在合适的时机主动去读 SKILL.md
- **SKILL.md 文件的编写质量**：描述是否清晰、指令是否可执行、前置检查是否完备

这就是为什么 skill 的编写者需要既懂业务逻辑、又懂 prompt engineering——skill 本质上是一份给 AI 看的操作手册，而不是一个代码插件。

---

## 实战：在 HTTP 层面观测 Skill 协议交互

既然 Skill 的一切都在 HTTP 中发生，最直接的验证方式就是抓包。以下是实操指南。

### 1. 使用 mitmproxy 拦截 HTTPS 流量

```bash
mitmproxy --mode regular --listen-port 8080 -s inspect_skill.py
```

需要编写一个简单的 mitmproxy 插件 `inspect_skill.py` 来过滤和格式化 `/chat/completions` 请求：

```python
from mitmproxy import http

def request(flow: http.HTTPFlow) -> None:
    if "/chat/completions" in flow.request.pretty_url:
        body = flow.request.json()
        if not body:
            return
        msgs = body.get("messages", [])
        tools = body.get("tools", [])
        print(f"\n=== Round with {len(msgs)} messages, {len(tools)} tools ===")
        for i, msg in enumerate(msgs):
            role = msg.get("role", "?")
            content = str(msg.get("content", ""))[:120]
            tc = msg.get("tool_calls")
            tc_summary = f", tool_calls={len(tc)}" if tc else ""
            print(f"  [{i}] role={role}{tc_summary} content={content}...")

def response(flow: http.HTTPFlow) -> None:
    if "/chat/completions" in flow.request.pretty_url:
        body = flow.response.json()
        if not body:
            return
        choice = body.get("choices", [{}])[0]
        msg = choice.get("message", {})
        tc = msg.get("tool_calls")
        finish = choice.get("finish_reason")
        if tc:
            names = [t.get("function", {}).get("name", "?") for t in tc]
            print(f"  <- tool_calls: {names}, finish_reason={finish}")
        else:
            content = str(msg.get("content", ""))[:80]
            print(f"  <- content: {content}..., finish_reason={finish}")
```

### 2. 配置 IDE 走代理

Cursor 的 HTTP 代理配置因版本而异，通用做法是设置环境变量：

```bash
export HTTP_PROXY=http://127.0.0.1:8080
export HTTPS_PROXY=http://127.0.0.1:8080
```

然后从同一终端启动 Cursor。如果 IDE 不认系统代理，可以使用 `proxychains` 或在 IDE 的 `settings.json` 中配置 `http.proxy`。

### 3. 观察要点

抓包时重点关注以下信号：

| 观察点 | 含义 | 正常表现 |
|--------|------|----------|
| `messages[0].role="system"` 中包含 `<available_skills>` | Progressive Loading 生效 | 只有 name + description，没有正文 |
| LLM 返回的第一个 `tool_calls` 是否包含 `Read(SKILL.md)` | Skill 触发成功 | `name: "Read"`, `arguments` 指向 SKILL.md |
| 第二轮请求的 `role: "tool"` 消息 | SKILL.md 全文已进入上下文 | content 包含完整的 SKILL.md 文本 |
| 后续 `tool_calls` 是否按 SKILL.md 步骤执行 | Skill 指令被正确理解 | 命令参数与 SKILL.md 一致 |
| `finish_reason` 的变化 | 判断当前处于工具循环还是最终回复 | `tool_calls` → 中间轮次；`stop` → 最终轮次 |

### 4. 用 curl 模拟单轮测试

如果只需要验证 Skill 的 system prompt 注入效果，不需要完整的多轮交互，可以用 curl 直接发单轮请求：

```bash
curl -s https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [
      {
        "role": "system",
        "content": "You are an AI assistant.\n\n<available_skills>\n<agent_skill fullPath=\"/tmp/test-skill/SKILL.md\">\n  When user says ping, respond with pong and nothing else.\n</agent_skill>\n</available_skills>\n\nWhen a skill is relevant, read and follow it IMMEDIATELY."
      },
      {
        "role": "user",
        "content": "ping"
      }
    ]
  }'
```

预期响应：`pong`——证明 system prompt 中的 skill 描述被 LLM 正确理解并执行。

### 5. 常见问题定位

**Skill 没触发**：检查 system prompt 中是否真的注入了 `<available_skills>` 标签块。部分 IDE 只在特定条件下注入（如工作区存在 `.cursor/skills/` 目录）。

**LLM 没读 SKILL.md**：检查 system prompt 中是否包含 "read and follow it IMMEDIATELY" 这类强制性指令，以及 `tools` 数组中是否注册了 `Read` 工具。

**读完后行为不对**：SKILL.md 的指令可能不够明确。抓包对比 LLM 返回的 `tool_calls` 参数和 SKILL.md 中的要求是否一致。

**并行 tool calling 没生效**：并非所有模型都支持并行调用。确认模型能力，并在 `tool_choice` 中确保没有限制为单次调用。

---

## FAQ

### Q1：Skill 和 Function Calling 是什么关系？

Function Calling 是 Skill 的**基础设施**。Skill 本身不是一个独立的协议功能——它依赖 Function Calling 来实现 LLM ↔ 宿主之间的工具交互。区别在于：Function Calling 解决"怎么调用工具"的问题，Skill 解决"什么时候该用什么工具、按什么顺序、设什么参数"的问题。前者是协议层机制，后者是应用层编排。

### Q2：为什么不直接在协议层支持 Skill？

因为没必要。Skill 需要的所有能力——文本注入、工具定义、多轮对话——OpenAI 协议早在 2023 年就全部支持了。在协议层新增 `skill` 字段反而会增加复杂度，且需要所有模型提供商同步跟进，得不偿失。这恰恰是工程设计中的好决策：用组合替代扩展。

### Q3：多个 Skill 共存时，LLM 如何选择触哪个？

完全靠匹配。system prompt 中列出了所有可用 Skill 的 `name` 和 `description`，LLM 根据用户输入与各 Skill 描述的语义相似度来判断。这也是为什么 `description` 字段至关重要——它必须覆盖足够多的触发场景（关键词、用户意图、URL 模式等），否则 Skill 永远不会被触发。

### Q4：Progressive Loading 具体省了多少 token？

以 mp-read 为例，其 SKILL.md 正文约 3000 token，而摘要（name + description）仅约 50 token。在每次对话的 system prompt 中只注入摘要，只有当 LLM 判定需要该 Skill 时才会 Read 全文。如果用户一次对话中从未提起公众号相关话题，那 2950 token 就省下了。这个数字随 Skill 数量线性累积——5 个 Skill 就是约 15000 token 的区别。

### Q5：Skill 和 MCP（Model Context Protocol）有什么区别？

MCP 是一种标准化的客户端-服务端协议，定义了三方（Host、Client、Server）之间的通信规范，包括资源发现、工具注册、提示模板等，属于**协议层抽象**。Skill 则完全没有自己的协议——它就是 markdown 文件 + system prompt 注入 + tool calling 的组合，属于**应用层模式**。两者的共同点是都依赖 tool calling 作为底层执行机制，但 MCP 试图标准化工具接入方式，Skill 则完全依赖自然语言指令驱动。

### Q6：自己编写的 Skill 需要配置工具吗？

不需要。Skill 本身不声明工具。工具（Shell、Read、Write、Grep 等）由 IDE 宿主统一注册到每轮请求的 `tools` 数组中。Skill 的职责是告诉 LLM：在什么情况下、用哪些已有工具、按什么步骤完成任务。你可以把工具理解为"操作系统提供的系统调用"，Skill 就是"告诉程序怎么组合这些系统调用来完成特定任务的文档"。

---

---

## 设计启示

理解了底层机制后，Skill 给人的感觉不再是"神奇的黑盒"，而是一个极其干净的设计。

它没有发明新协议，没有依赖特殊 API，只是把三件已经存在的事情组合到一起：

- **System prompt 注入**（LLM 早就支持）
- **Tool schema 注册**（LLM 早就支持）
- **多轮 tool calling 循环**（LLM 早就支持）

Skill 的出现解决了一个实际问题：如何让 LLM 在面对复杂任务时知道该用什么工具、按什么顺序、设什么参数。以前这些信息要么散落在文档里，要么硬编码在提示词里，Skill 把它们变成了一份可执行、可维护、可共享的操作手册。

理解了这层，你就知道编写 Skill 的关键不是写代码，而是写一份让 LLM 能看懂、能执行、能纠错的操作手册——具体来说，就是写好 `description` 的触发覆盖度、前置检查的完备性、以及每一步指令的可执行性。

---

*本文由腾讯云开发者张敏原创，首发于腾讯云开发者公众号。原文链接：[大模型的Agent Skill功能，在LLM HTTP底层交互流中是怎么承载的？](https://mp.weixin.qq.com/s?__biz=MzI2NDU4OTExOQ==&mid=2247695701&idx=1&sn=a8b5dfd8cee58567104bcccc39af6947)*