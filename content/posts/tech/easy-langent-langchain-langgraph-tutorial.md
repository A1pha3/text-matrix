---
title: "Easy-langent：158 Stars的LangChain/LangGraph学习教程——Datawhale出品从入门到实战"
date: 2026-04-18T18:25:00+08:00
slug: "easy-langent-langchain-langgraph-tutorial"
description: "Easy-langent是Datawhale出品的158 Stars开源教程，专注解决LangChain/LangGraph入门难题。8章递进式内容覆盖框架认知→组件实操→多智能体协作→综合实战，配套谁是卧底等实战项目。"
draft: false
categories: ["技术笔记"]
tags: ["LangChain", "LangGraph", "AI Agent", "LLM", "Python", "教程", "Datawhale"]
---

# Easy-langent：158 Stars的LangChain/LangGraph学习教程——Datawhale出品从入门到实战

> **目标读者**：想入门AI Agent开发的高校学生、寻求技术落地的Python开发者、对LangChain/LangGraph有兴趣的自学者
> **预计阅读时间**：50-70分钟
> **前置知识**：Python基础、了解大模型基本概念、对Agent核心概念有初步认知
> **难度定位**：⭐⭐⭐⭐ 专家设计

---

## §1 学习目标

1. **理解LangChain与LangGraph的定位差异**：何时用LangChain、何时用LangGraph
2. **掌握LangChain核心组件**：模型调用、提示词模板、输出解析、记忆、工具
3. **掌握LangGraph有状态工作流**：StateGraph、节点、边、条件路由
4. **能够开发多智能体协作系统**：基于LangGraph的多Agent协作模式
5. **完成综合实战项目**：构建"谁是卧底"游戏智能体引擎

---

## §2 项目概述：打破理论与实战的壁垒

### 2.1 为什么需要Easy-langent

当前AI Agent开发面临三大困境：

| 困境 | 描述 | 影响 |
|------|------|------|
| **框架概念繁杂** | LangChain/LangGraph术语多、新人难理解 | 学习曲线陡峭 |
| **实操无从下手** | 看文档容易，但不知道如何落地项目 | 理论与实践脱节 |
| **技术与应用脱节** | 掌握了框架基础，不知如何解决真实问题 | 无法完成实际开发 |

**Easy-langent的定位**：让读者"在系统掌握智能体核心逻辑的同时，真正学会运用LangChain、LangGraph框架解决实际开发问题，实现从'懂概念到会开发'的跨越"。

### 2.2 项目信息

| 属性 | 值 |
|------|-----|
| **Stars** | 158 |
| **语言** | TypeScript（项目文档）、Python（示例代码） |
| **许可证** | Apache 2.0 |
| **组织** | Datawhale（数据巢） |
| **在线文档** | datawhalechina.github.io/easy-langent |
| **国内镜像** | easy-langent.datawhale.cc |

**核心贡献者**：
- 牧小熊（项目负责人）- Datawhale成员
- 柯慕灵（项目贡献者）- Datawhale成员

### 2.3 配套项目

除了8章主教程，Easy-langent还提供多个实战项目：

| 项目 | 框架 | 描述 |
|------|------|------|
| 狼人杀（上帝视角） | LangGraph | 多Agent协作游戏 |
| 智能知识库问答 | LangChain | Agentic RAG实践 |
| MCPChat | LangChain | MCP协议集成 |
| 数据处理智能体 | LangChain | 数据自动化处理 |

---

## §3 框架认知：LangChain与LangGraph的关系

### 3.1 核心结论

**LangChain和LangGraph不是竞争关系，而是互补关系**：
- LangChain：帮你快速搭建简单到中等复杂度的大模型应用（"乐高积木"）
- LangGraph：帮你管控复杂的多步骤任务、多Agent协作（"建筑设计图"）

### 3.2 LangChain：大模型应用的"基础设施工具箱"

**定位**：快速搭建简单到中等复杂度的大模型应用

**核心价值**：降低入门门槛、提高开发效率

**适用场景**：
- 简单的LLM调用（文本生成、翻译）
- 基础的RAG（让模型结合本地文档回答问题）
- 单步骤的工具调用
- 快速验证想法

**三层架构**（LangChain 1.0+）：

| 模块 | 职责 | 说明 |
|------|------|------|
| `langchain_core` | 核心抽象 | Runnable、BaseParser等基础组件 |
| `langchain` | 高级工程组件 | Chains、Parsers、Memory等 |
| `langchain_openai` | 第三方模型适配 | OpenAI、Google等集成 |

```
langchain-core = 地基和规则
langchain = 用标准构件搭建的功能房间
langchain_openai等 = 连接外部服务的门窗和管线
```

### 3.3 LangGraph：复杂应用的"架构设计框架"

**定位**：处理多步骤、需要协作的复杂任务（基于LangChain的进阶扩展）

**核心价值**：
- **状态管理**：统一状态对象，支持字段级状态合并策略
- **复杂流程管控**：通过条件边、循环边原生支持分支与循环
- **多智能体协作**：支持多Agent之间的协调与通信

**适用场景**：
- 多步骤流程（论文总结多步骤任务）
- 需要保存中间结果的场景
- 多智能体协作（检索Agent+分析Agent+协调Agent）
- 需要人机交互的流程（某步需用户确认）

### 3.4 两者对比

| 维度 | LangChain | LangGraph |
|------|-----------|-----------|
| **流程灵活性** | 链式流，适合线性固定步骤 | 图结构，支持分支、循环、并行 |
| **状态管理** | 分散存储，无统一入口 | 统一状态对象，内置持久化 |
| **循环与分支** | 需手动控制 | 原生支持，可配置终止条件 |
| **上手难度** | 低 | 中 |
| **适用规模** | 轻量级应用 | 生产级复杂系统 |

### 3.5 选择指南

```
快速搭建原型、任务流程固定 → LangChain链式流
任务复杂、有分支/循环、需状态追溯 → LangGraph图结构流
```

---

## §4 环境搭建：5分钟准备开发环境

### 4.1 环境要求

- **Python版本**：3.10及以上（推荐3.10）
- **网络**：能访问互联网（下载依赖、调用LLM API）
- **编辑器**：PyCharm或VS Code（需安装Python插件）

### 4.2 创建虚拟环境（必须）

**方式一：venv（Python自带，通用）**

```bash
# 创建虚拟环境
python -m venv langent-env

# 激活（Windows cmd）
langent-env\Scripts\activate
# 激活（macOS/Linux）
source langent-env/bin/activate
```

**方式二：Conda**

```bash
conda create -n langent-env python=3.10 -y
conda activate langent-env
```

**方式三：uv（推荐，Agent开发首选）**

```bash
# 创建项目
uv init easy-langent --python 3.10
cd easy-langent

# 添加国内镜像（可选）
# 编辑 ~/.config/uv/uv.toml
[[index]]
url = "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple/"
default = true

# uv会创建虚拟环境并自动管理
```

### 4.3 安装核心依赖

```bash
# LangChain核心库
pip install langchain

# LangGraph（推荐 ≥1.0.0）
pip install langgraph

# OpenAI集成（示例使用DeepSeek）
pip install openai
pip install langchain_openai

# 环境变量管理
pip install python-dotenv
```

### 4.4 配置API密钥

创建`.env`文件（**注意：不要提交此文件到Git**）：

```bash
API_KEY=your_api_key_here
BASE_URL=https://api.deepseek.com  # 或其他LLM API地址
```

---

## §5 LangChain核心组件实操

### 5.1 模型调用

**基础调用**：

```python
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(
    model="deepseek-chat",
    temperature=0.7,
    max_tokens=500
)

response = llm.invoke("解释什么是RAG")
print(response.content)
```

### 5.2 提示词模板

**模板定义与调用**：

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个专业的{domain}助手"),
    ("user", "请解释{concept}，用{language}语言回答")
])

chain = prompt | llm

result = chain.invoke({
    "domain": "计算机科学",
    "concept": "算法",
    "language": "中文"
})
```

### 5.3 输出解析

**结构化输出**：

```python
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List

class Answer(BaseModel):
    explanation: str = Field(description="概念的解释")
    examples: List[str] = Field(description="相关例子")

parser = JsonOutputParser(pydantic_object=Answer)

prompt = prompt.partial(format_instruction=parser.get_format_instructions())
chain = prompt | llm | parser

result = chain.invoke({"concept": "算法"})
# result = {"explanation": "...", "examples": [...]}
```

### 5.4 记忆组件

**对话记忆**：

```python
from langchain_core.messages import AIMessage, HumanMessage
from langchain.chat_message_histories import ChatMessageHistory

history = ChatMessageHistory()
history.add_user_message("我想学习Python")
history.add_ai_message("Python是一门易学难精的语言，你想知道哪方面？")

# 历史自动注入
for msg in history.messages:
    print(f"{msg.type}: {msg.content}")
```

### 5.5 工具调用

**定义与使用工具**：

```python
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """获取城市天气"""
    return f"{city}今天晴天，25度"

# 绑定到LLM
llm_with_tools = llm.bind_tools([get_weather])
response = llm_with_tools.invoke("北京天气怎么样？")
```

---

## §6 LangGraph有状态工作流

### 6.1 核心概念

LangGraph的三大组件：

| 组件 | 作用 | 类比 |
|------|------|------|
| **State（状态）** | 工作流的"共享黑板"，所有节点读写它 | 班级大扫除的公告板 |
| **Nodes（节点）** | 封装具体功能逻辑 | 负责不同任务的同学 |
| **Edges（边）** | 定义节点之间的流转关系 | 任务传递路径 |

### 6.2 状态定义

**TypedDict方式**（教程推荐）：

```python
from typing import TypedDict, NotRequired

class TaskState(TypedDict):
    user_query: str                    # 用户原始查询
    tool_result: NotRequired[str]      # 工具调用结果
    final_answer: NotRequired[str]     # 最终回答
    progress: NotRequired[int]         # 任务进度百分比
```

**Pydantic方式**（企业生产推荐）：

```python
from pydantic import BaseModel, Field
from typing import Optional

class TaskState(BaseModel):
    user_query: str = Field(description="用户原始查询")
    tool_result: Optional[str] = Field(default=None)
    final_answer: Optional[str] = Field(default=None)
    progress: Optional[int] = Field(default=None)
```

### 6.3 节点函数

**节点函数接收状态，返回更新字段**：

```python
def parse_query(state: TaskState):
    query = state["user_query"]
    print(f"解析问题: {query}")
    
    return {
        "tool_result": f"已解析: {query}",
        "progress": 30
    }

def call_tool(state: TaskState):
    result = f"工具结果: 关于『{state['user_query']}』的信息"
    return {
        "tool_result": result,
        "progress": 70
    }

def generate_answer(state: TaskState):
    answer = f"最终回答: 基于 {state['tool_result']}"
    return {
        "final_answer": answer,
        "progress": 100
    }
```

### 6.4 构建工作流

```python
from langgraph.graph import StateGraph, END

# 创建图
graph = StateGraph(TaskState)

# 添加节点
graph.add_node("parse_query", parse_query)
graph.add_node("call_tool", call_tool)
graph.add_node("generate_answer", generate_answer)

# 定义边
graph.set_entry_point("parse_query")          # 入口
graph.add_edge("parse_query", "call_tool")   # 固定流转
graph.add_edge("call_tool", "generate_answer")
graph.add_edge("generate_answer", END)        # 结束

# 编译
app = graph.compile()

# 执行
result = app.invoke({"user_query": "解释量子计算"})
print(result["final_answer"])
```

### 6.5 条件边：动态路由

```python
def should_continue(state: TaskState) -> str:
    """根据状态决定下一步"""
    if len(state.get("user_query", "")) > 100:
        return "long_query"
    return "short_query"

# 条件边
graph.add_conditional_edges(
    "parse_query",
    should_continue,
    {
        "long_query": "call_tool",
        "short_query": "generate_answer"
    }
)
```

---

## §7 综合实战：构建"谁是卧底"游戏智能体

### 7.1 项目概述

**游戏规则简化版**：
- 4个智能体（1个卧底，3个平民）
- 卧底获得与平民相似但不同的词语
- 发言阶段：描述自己拿到的词语（不能直接说词）
- 投票阶段：根据发言投票选出卧底
- 胜负：淘汰卧底则平民获胜；剩余1民1卧底则卧底获胜

### 7.2 游戏状态定义

```python
class GameState(TypedDict):
    civilian_word: str              # 平民词语
    undercover_word: str            # 卧底词语
    role_assignment: dict           # 角色分配
    speeches: dict                  # 当前轮发言
    history_speeches: list         # 历史发言
    votes: dict                     # 当前轮投票
    game_status: str                # running/end
    winner: str                     # civilian/undercover
    eliminated: list                # 被淘汰玩家
    round: int                      # 当前轮次
```

### 7.3 核心节点实现

**词语生成节点**：

```python
def generate_words(state: GameState) -> GameState:
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是专业的「谁是卧底」游戏出题人。
要求：
1. 词语类型：日常物品（如"奶茶-果汁"）
2. 语义关系：高度相似但核心特征不同
3. 输出格式：{"civilian": "奶茶", "undercover": "果汁"}"""),
        ("user", "生成一组谁是卧底词语对")
    ])
    chain = prompt | llm | parser
    result = chain.invoke({})
    
    state["civilian_word"] = result["civilian"]
    state["undercover_word"] = result["undercover"]
    return state
```

**角色分配节点**：

```python
import random

def assign_roles(state: GameState) -> GameState:
    agents = ["agent1", "agent2", "agent3", "agent4"]
    undercover = random.choice(agents)
    
    for agent in agents:
        if agent == undercover:
            state["role_assignment"][agent] = ("卧底", state["undercover_word"])
        else:
            state["role_assignment"][agent] = ("平民", state["civilian_word"])
    return state
```

**发言生成节点**：

```python
def generate_speeches(state: GameState) -> GameState:
    speeches = {}
    
    for agent, (role, word) in state["role_assignment"].items():
        if agent in state["eliminated"]:
            continue
            
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""你是「谁是卧底」游戏玩家，当前第{state['round']}轮发言。
角色：{role}，词语：{word}
要求：描述词语特征，10-100字，不能直接说词"""),
            ("user", "生成发言")
        ])
        
        output = chain.invoke({})
        speeches[agent] = output["speech"]
    
    state["speeches"] = speeches
    state["history_speeches"].append(speeches)
    return state
```

### 7.4 完整游戏循环

```python
def should_continue_game(state: GameState) -> str:
    if state["game_status"] == "end":
        return "end"
    return "continue"

# 构建游戏图
game_graph = StateGraph(GameState)
game_graph.add_node("generate_words", generate_words)
game_graph.add_node("assign_roles", assign_roles)
game_graph.add_node("generate_speeches", generate_speeches)
game_graph.add_node("vote", vote_undercover)
game_graph.add_node("check_winner", check_winner)

game_graph.set_entry_point("generate_words")
game_graph.add_edge("generate_words", "assign_roles")
game_graph.add_edge("assign_roles", "generate_speeches")
game_graph.add_edge("generate_speeches", "vote")
game_graph.add_edge("vote", "check_winner")

game_graph.add_conditional_edges(
    "check_winner",
    should_continue_game,
    {"continue": "generate_speeches", "end": END}
)

game_app = game_graph.compile()

# 运行游戏
result = game_app.invoke({})
print(f"游戏结果: {result['winner']}")
```

---

## §8 新手实战：学习路径与建议

### 8.1 循序渐进的学习路径

**第一阶段：框架认知（Chapter 1）**
1. 理解LangChain与LangGraph的定位差异
2. 搭好开发环境，跑通基础案例
3. 感受两个框架的用法差异

**第二阶段：LangChain组件（Chapter 2-3）**
1. 模型调用、提示词模板、输出解析
2. 记忆组件、工具组件
3. 组合实践：构建简单Agent

**第三阶段：LangGraph进阶（Chapter 6-7）**
1. 有状态工作流：StateGraph、节点、边
2. 条件路由、循环控制
3. 多智能体协作模式

**第四阶段：综合实战（Chapter 5, 8）**
1. 智能体应用设计
2. 构建"谁是卧底"游戏智能体
3. 项目文档撰写规范

### 8.2 前置知识补充

若你还不掌握以下知识，建议先学习：

| 前置课程 | 内容 |
|----------|------|
| [Happy-llm](https://github.com/datawhalechina/happy-llm) | 大模型基础概念 |
| [Hello-Agents](https://github.com/datawhalechina/hello-agents) | Agent核心概念入门 |

### 8.3 常见问题

**Q1：LangChain和LangGraph学哪个？**
两者都要学。简单任务用LangChain快速实现，复杂任务用LangGraph管控流程。实际开发中经常融合使用。

**Q2：需要GPU吗？**
不需要。教程中的示例通过API调用LLM，无需本地GPU。

**Q3：API费用高吗？**
使用DeepSeek等国产API成本很低。平均每千token成本约0.001元人民币。

**Q4：学完能做什么？**
可以构建智能问答系统、自动化工作流、多智能体协作系统、Agentic RAG等实际应用。

---

## §9 相关资源

- [GitHub仓库](https://github.com/datawhalechina/easy-langent)
- [在线文档](https://datawhalechina.github.io/easy-langent/)
- [国内镜像](https://easy-langent.datawhale.cc/)
- [Datawhale官网](https://datawhalechina.github.io/)

---

*🦞 撰写于2026年4月18日*
