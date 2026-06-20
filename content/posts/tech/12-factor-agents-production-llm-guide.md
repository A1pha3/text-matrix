---
title: 12-Factor Agents - 构建生产级LLM应用的12条原则
date: 2026-05-18
slug: 12-factor-agents-production-llm-guide
categories: ["技术笔记"]
description: "12-Factor Agents 不是另一套 Agent 框架，而是一组从生产环境里长出来的工程约束，分布在输入层、执行层、控制层和架构层，解决 LLM 应用中上下文控制、工具设计、安全护栏等核心工程问题。"
tags:
  - AI Agent
  - LLM应用
  - 工程实践
  - 架构设计
---

# 12-Factor Agents：构建生产级 LLM 应用的 12 条原则

12-Factor Agents 解决的是「如何用软件工程手段把 LLM 的不确定性关进笼子里」。它是一组从生产环境里长出来的工程约束，不是另一套 Agent 框架——每条原则都在回答同一个问题：什么东西该由代码管、什么东西可以交给模型。

官方仓库给出 12 条正式原则加 1 条荣誉提及（Factor 13：预取上下文）。本文按「输入层 → 执行层 → 控制层 → 架构层 → 荣誉提及」的顺序拆开，每条原则补工程动机和边界判断，最后给一个代码审查 Agent 的完整任务流和落地顺序。

## 学习目标

读完本文，可以掌握以下能力：

- 说出 12 条原则各自要解决的具体工程问题，以及把它们分布在四个层面的原因
- 区分「交给模型决策」和「交给代码掌控」的边界，能在新场景里判断哪些环节该收回控制权
- 为 Factor 1（结构化输出）、Factor 8（控制流）、Factor 12（无状态 Reducer）写出可运行的 Python 示例
- 跟踪一次代码审查 Agent 从触发到退出的完整路径，说清楚每条原则在这条路径上落在哪里
- 按收益和成本排序，给出自己团队未来 3 个月的落地优先级

## 目录

- [先看全景：12 条原则的分层地图](#先看全景12-条原则的分层地图)
- [为什么是这 12 条](#为什么是这-12-条)
- [输入层：提示词、上下文与工具调用](#输入层提示词上下文与工具调用)
- [执行层：输出、状态与可中断运行](#执行层输出状态与可中断运行)
- [控制层：人工介入、流程与错误处理](#控制层人工介入流程与错误处理)
- [架构层：粒度、触发与无状态化](#架构层粒度触发与无状态化)
- [荣誉提及：Factor 13 — 预取上下文](#荣誉提及factor-13--预取上下文)
- [一个代码审查 Agent 的完整路径](#一个代码审查-agent-的完整路径)
- [从哪里开始](#从哪里开始)
- [常见错误排查](#常见错误排查)
- [常见问题](#常见问题)
- [自测清单](#自测清单)
- [实战练习](#实战练习)
- [参考资源](#参考资源)

## 先看全景：12 条原则的分层地图

12 条原则分布在四个层面，从上到下越来越靠近运行时的确定性：

| 层面 | 原则 | 要解决的问题 |
|------|------|-------------|
| **输入层** | Factor 1-3 | LLM 该看到什么、以什么格式看到 |
| **执行层** | Factor 4-6 | 模型吐出结果后，系统怎么接住、怎么继续 |
| **控制层** | Factor 7-9 | 人工怎么介入、流程谁说了算、出错怎么办 |
| **架构层** | Factor 10-12 | 单个 Agent 的边界、触发方式和状态管理 |

这张表就是全文的地图——从数据进入模型到结果返回调用方的完整流水线。Factor 13（荣誉提及）不归入任何一层，因为它是一种横切上下文组装的优化策略，任何一层都可能用到。

## 为什么是这 12 条

作者 Dex 在 AI Engineer World's Fair 演讲中给过一个观察：目前大多数所谓「AI Agent」，绝大部分代码是确定性的，LLM 只在关键节点做点缀。真正能在生产环境稳定运行的 Agent，靠的是大量软件工程加少量 LLM 智能。

这 12 条原则就是从「大量软件工程」这个方向上提取出来的。每一条都在说：**把某个环节的控制权从模型手里拿回来，交给代码。** 这个方向和「让 Agent 更智能」是正交的——12-Factor 不教你怎么写更聪明的提示词，只教你怎么把不确定性约束在可控范围内。

## 输入层：提示词、上下文与工具调用

### Factor 1 — 自然语言 → 工具调用

工具的本质是结构化输出。Agent 调用工具跟调用 API 没有本质区别——输入自然语言描述、输出结构化结果。把工具当「魔法能力」来设计，反而会让调用链路变得不透明。

**工程动机**：LLM 自由文本输出在下游代码里是灾难——你要写正则提取、处理转义、应对模型偶尔加一句解释。把工具调用约束成 JSON schema，下游代码就能用现成的解析器，失败也能在 schema 校验层统一拦截。

**边界判断**：如果某个「工具」的输出只给人看、不进下游代码（比如生成一段给用户读的摘要），可以保留自由文本。只要输出要被代码消费，就必须走结构化格式。

下面是一个最小可运行示例，展示如何用 Pydantic 定义工具的输出 schema 并校验 LLM 返回：

```python
# pip install pydantic openai
from pydantic import BaseModel, ValidationError
from openai import OpenAI

class CodeReviewDecision(BaseModel):
    """代码审查 Agent 的结构化输出。"""
    intent: str  # "approve" | "request_changes" | "ask_human"
    severity: str  # "info" | "warning" | "critical"
    comment: str

client = OpenAI()

def review_code(diff: str) -> CodeReviewDecision:
    """调用 LLM 审查 diff，返回结构化结果。

    输出不符合 schema 时走重试，重试仍失败则降级为 ask_human。
    """
    prompt = f"""审查以下 diff，按 JSON schema 返回结论：
{diff}

只返回 JSON，字段：intent, severity, comment。"""
    for attempt in range(3):
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        try:
            return CodeReviewDecision.model_validate_json(
                resp.choices[0].message.content
            )
        except ValidationError as err:
            if attempt == 2:
                # 降级：交给人工
                return CodeReviewDecision(
                    intent="ask_human",
                    severity="warning",
                    comment=f"LLM 输出校验失败：{err}",
                )
            continue
    raise RuntimeError("unreachable")

# 用法
decision = review_code("diff --git a/main.py b/main.py\n+eval(user_input)")
print(decision.intent, decision.severity)
```

这段代码体现了 Factor 1 和 Factor 4 的合流：工具调用就是结构化输出，结构化输出靠 schema 校验兜底。

### Factor 2 — 掌控你的提示词

提示词是代码，应该和代码一起进版本管理。散落在配置文件、环境变量或聊天界面里的提示词，会在调试时变成灾难。

**工程动机**：提示词的微小改动会让模型行为发生漂移。如果不进版本管理，你无法回答「上次审查通过率高，这次为什么变低了」——因为没人记得提示词改过什么。把提示词写成 `.md` 或 `.jinja` 文件放在仓库里，每次改动走 code review，行为变化就有迹可循。

**边界判断**：实验阶段允许提示词散落，方便快速迭代。一旦 Agent 进了生产环境或被多人共享，必须收敛到版本管理。一个可操作的判断点：当有人开始问「这个提示词是谁改的」时，就该进仓库了。

### Factor 3 — 掌控上下文窗口

作者把「Context Engineering」放在比「Prompt Engineering」更本质的位置。上下文窗口的大小和内容布局，直接决定了模型能看到什么、记住什么、做出什么判断。如何压缩历史、选择检索片段、组织消息顺序——这些比提示词里的措辞影响更大。

**工程动机**：上下文窗口是稀缺资源。塞太多无关内容，模型注意力被稀释，关键信息反而被忽略；塞太少，模型缺前置信息做判断。Context Engineering 的核心是在有限 token 预算里把「模型做这次决策真正需要的信息」按优先级排好。

**边界判断**：上下文工程不是越多越好，也不是越少越好。判断标准是「模型这次决策缺了哪些信息会出错」——缺什么补什么，不缺的不补。一个常见反例是把整个对话历史原样塞进去，结果模型被早期无关内容带偏。

## 执行层：输出、状态与可中断运行

### Factor 4 — 工具即结构化输出

统一 LLM 的输出格式，消除二义性。不要让下游代码去猜模型返回的是 JSON 还是纯文本、是成功还是失败。

**工程动机**：Factor 1 讲的是「单次工具调用要结构化」，Factor 4 把这个约束推广到 Agent 所有输出。统一格式后，错误处理、重试、降级可以做成一个公共层，不用每个调用点各写一套。

**边界判断**：Agent 对外暴露的接口必须结构化；Agent 内部某些「思考过程」可以保留自由文本，只要不流出 Agent 边界。

### Factor 5 — 执行状态 = 业务状态

消除双重状态带来的同步复杂度。Agent 当前的执行进度，应该就是业务系统里的真实状态。不存在「Agent 内部状态」和「业务状态」两套东西需要对齐。

**工程动机**：双重状态是 bug 温床。Agent 内部记「已审查 3 个文件」，业务系统记「已审查 2 个文件」，一旦对不上就要写同步逻辑，同步逻辑本身又会出错。把 Agent 状态直接落到业务系统的真实状态（数据库行、PR review 状态、工单状态），就只有一份事实来源。

**边界判断**：Agent 内部允许有临时变量（当前这次调用的中间结果），但这些变量不应该跨调用持久化。跨调用的状态必须落到业务系统，而不是 Agent 自己的内存或私有存储。

### Factor 6 — 简单 API 的启动 / 暂停 / 恢复

生产级 Agent 必须支持中断和恢复。运行中的 Agent 可能因为人工审批、外部依赖超时、资源限制等原因停下来，不能每次中断都从零开始。

**工程动机**：长任务（审查大 PR、处理复杂工单）中途断了，从头重跑既浪费 token 又拖慢响应。把执行状态持久化到外部存储，恢复时从断点继续，是生产环境的基本要求。

**边界判断**：短任务（一次问答、一次分类）不需要中断恢复，加了反而增加复杂度。判断标准是「这个任务的中断概率有多高、重跑成本有多贵」——两者都高才需要做。

## 控制层：人工介入、流程与错误处理

### Factor 7 — 用工具调用联系人类

Agent 需要人工介入时，不应该靠「在日志里打印一句话」。应该通过标准化的工具调用机制发出请求、等待响应、超时处理——和调用任何其他工具一样。

**工程动机**：日志里打一句话，没人会看。把人工介入做成工具调用，请求会进队列、有超时、有重试、有审计记录。人和其他工具在 Agent 眼里没有区别，都是「调用 → 等响应 → 处理结果」。

**边界判断**：不是所有「需要人看一眼」的场景都要走工具调用。debug 阶段打日志没问题；生产环境里需要人做决策的环节，必须走工具调用，否则请求会丢。

### Factor 8 — 掌控你的控制流

大多数 Agent 框架让 LLM 决定下一步做什么。但在生产环境里，控制流应该由代码掌控，LLM 只负责需要「智能」的那部分决策。不要让模型替你编排业务流程。

**工程动机**：让模型决定控制流，意味着每次执行路径都可能不同——测试无法覆盖、复现 bug 困难、性能不可预测。把控制流写成代码（`while` 循环、状态机、显式分支），LLM 只在「需要判断」的节点被调用，执行路径就是确定的，可测试、可复现、可监控。

**边界判断**：什么算「需要判断」？标准是「这个决策有没有明确的规则」。有规则就写代码，没规则才让模型判断。比如「这段代码是否有 bug」让模型判断，「审查完要不要继续审查下一个文件」用代码控制。

下面是一个 Factor 8 的最小示例，展示控制流由代码掌控、LLM 只做判断节点：

```python
# pip install openai pydantic
from openai import OpenAI
from pydantic import BaseModel

class LintDecision(BaseModel):
    """LLM 只负责这个判断。"""
    has_issue: bool
    reason: str

client = OpenAI()

def llm_judge(code: str) -> LintDecision:
    """LLM 只做一件事：判断代码是否有问题。"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"代码是否有问题？只返回 JSON：has_issue, reason\n\n{code}"}],
        response_format={"type": "json_object"},
    )
    return LintDecision.model_validate_json(resp.choices[0].message.content)

def review_pipeline(files: list[str]) -> dict:
    """控制流由代码掌控：循环、终止条件、汇总都在这里。

    LLM 只在 llm_judge 调用点参与，不参与流程编排。
    """
    results = {}
    index = 0
    # 控制流是显式的 while 循环，不是「让模型决定下一步」
    while index < len(files):
        code = files[index]
        decision = llm_judge(code)
        results[files[index]] = decision
        if decision.has_issue and decision.reason.startswith("critical"):
            # 关键问题立即停止，这是代码的判断，不是模型的判断
            break
        index += 1
    return results

# 用法
files = ["print('hello')", "eval(input())", "import os"]
report = review_pipeline(files)
for path, decision in report.items():
    print(f"{path}: {decision.has_issue} - {decision.reason}")
```

这段代码里，`while` 循环、终止条件、汇总逻辑都是代码写的，LLM 只在 `llm_judge` 里判断「这段代码是否有问题」。如果让模型决定「下一步审查哪个文件」「要不要继续」，执行路径就不可控了。

### Factor 9 — 将错误压缩进上下文窗口

错误信息是上下文燃料，不是需要隐藏的异常。把工具调用失败的原因、堆栈信息、重试次数写进上下文窗口，模型下一次推理会比任何 prompt 告诉它「注意错误处理」更有效。

**工程动机**：模型不知道发生了什么，就没法调整策略。把错误写进上下文，模型能看到「上次调用 `fetch_git_tags` 超时了」，下一次就会换路径或降级。隐藏错误等于让模型蒙眼走路。

**边界判断**：写进上下文的是「模型能用来的错误」——失败原因、影响范围、已尝试的方案。完整的堆栈可能太长，需要压缩。敏感信息（密钥、内部路径）要脱敏后再写入。

## 架构层：粒度、触发与无状态化

### Factor 10 — 小而专注的 Agent

一个 Agent 做一件事。大模型当工具来用，而不是把所有逻辑塞进一个巨型 Agent 的提示词里。

**工程动机**：巨型 Agent 的提示词会越来越长，模型注意力被稀释，每个功能的输出质量都在下降。拆成多个小 Agent，每个 Agent 的上下文窗口只装自己那件事需要的信息，输出质量更稳。小 Agent 也更容易测试和复用。

**边界判断**：拆分粒度不是越细越好。每个 Agent 之间有协调成本（上下文传递、状态同步）。判断标准是「这两个 Agent 是否经常需要彼此的上下文」——如果经常需要，合并可能更好；如果基本独立，拆开。

### Factor 11 — 触发无处不在，用户在哪就在哪

用事件驱动架构解耦 Agent 的触发源。Agent 不应该只绑定在 HTTP endpoint 上——Slack 消息、GitHub webhook、定时任务、数据库变更，都可以是触发源。

**工程动机**：把 Agent 绑死在 HTTP endpoint 上，意味着用户要主动调用才能用。事件驱动让 Agent 在「事情发生时」自动响应，更贴近真实工作流（PR 创建、工单状态变更、定时检查）。

**边界判断**：事件驱动增加了系统复杂度（消息队列、幂等性、重试）。如果 Agent 只需要被人主动调用，HTTP endpoint 就够了；如果需要在「事情发生时」自动跑，才上事件驱动。

### Factor 12 — 让 Agent 成为无状态 Reducer

每次 Agent 调用 = `f(当前状态, 新输入)` → `新状态`。没有副作用，没有隐式状态累积。纯函数式的推理模型让测试和调试都回到可复现的轨道上。

**工程动机**：有副作用的 Agent 难测试——同样的输入跑两次结果不同，因为内部状态变了。写成 reducer，测试只需要构造 `(状态, 输入)` 对，断言输出状态。调试时也能从任意状态重放。

**边界判断**：reducer 本身无副作用，但 Agent 系统整体可以有副作用（写数据库、调外部 API）。原则是「副作用发生在 reducer 之外」——reducer 计算出新状态，外部代码根据新状态执行副作用。

下面是 Factor 12 的最小 reducer 签名示例：

```python
# pip install pydantic
from pydantic import BaseModel
from typing import Literal

class AgentState(BaseModel):
    """Agent 的全部状态，显式、可序列化。"""
    reviewed_files: list[str] = []
    issues_found: int = 0
    status: Literal["running", "done", "blocked"] = "running"

class AgentInput(BaseModel):
    """单次输入。"""
    file_path: str
    code: str
    has_issue: bool

class AgentOutput(BaseModel):
    """reducer 的输出：新状态 + 要执行的副作用描述。"""
    new_state: AgentState
    side_effects: list[str] = []  # 副作用以描述形式返回，由外部代码执行

def review_reducer(state: AgentState, inp: AgentInput) -> AgentOutput:
    """无状态 reducer：纯函数，输出只依赖输入。

    f(state, input) -> (new_state, side_effects)
    同样的 (state, input) 永远返回同样的 (new_state, side_effects)。
    """
    new_reviewed = state.reviewed_files + [inp.file_path]
    new_issues = state.issues_found + (1 if inp.has_issue else 0)
    effects: list[str] = []
    if inp.has_issue:
        effects.append(f"post_comment:{inp.file_path}")
    new_status = state.status
    if new_issues >= 3:
        new_status = "blocked"
        effects.append("notify_human:too_many_issues")
    new_state = AgentState(
        reviewed_files=new_reviewed,
        issues_found=new_issues,
        status=new_status,
    )
    return AgentOutput(new_state=new_state, side_effects=effects)

# 用法：reducer 本身可测试，副作用在外部执行
state = AgentState()
inp = AgentInput(file_path="main.py", code="eval(x)", has_issue=True)
result = review_reducer(state, inp)
print(result.new_state.status)        # running
print(result.new_state.issues_found)  # 1
print(result.side_effects)            # ['post_comment:main.py']

# 同样的输入永远返回同样的输出，可复现
assert review_reducer(state, inp) == review_reducer(state, inp)
```

这个 reducer 签名里，`review_reducer` 是纯函数，副作用以字符串描述形式返回，由外部代码（不在 reducer 内）执行。测试时只测 reducer，不测副作用执行。

## 荣誉提及：Factor 13 — 预取上下文

Factor 13 是官方仓库的附录（appendix-13-pre-fetch），不在正式 12 条里，但工程价值不低。核心一句话：**如果你已经知道模型大概率会调用某个工具，就直接在代码里预先调用，把结果塞进上下文，别浪费一次 token 往返让模型自己 fetch。**

**工程动机**：每次 LLM 调用都是一次网络往返 + 推理耗时。如果模型 90% 的概率会调 `list_git_tags`，让模型先返回「我要调 list_git_tags」、代码再执行、再把结果回传给模型，多了一次往返。直接在代码里 fetch 好，把结果放进上下文，模型一次推理就能用上。

**边界判断**：预取的前提是「高概率会用到」。如果模型只有 10% 的概率调某个工具，预取就是浪费——90% 的情况下上下文里多了一段无用信息。判断标准是「这个工具在历史调用里被命中的频率」。另一个边界是预取的数据量——如果数据很大（比如整个仓库的文件列表），预取会挤占上下文预算，反而得不偿失。

下面是 Factor 13 的对比示例，展示「让模型自己 fetch」和「代码预取」的差异：

```python
# pip install openai pydantic
from openai import OpenAI
from pydantic import BaseModel
from typing import Literal

client = OpenAI()

class DeployDecision(BaseModel):
    intent: Literal["deploy_backend_to_prod", "done_for_now"]
    tag: str | None = None
    message: str | None = None

# 反例：让模型自己决定要不要 fetch git tags
def deploy_bad(initial_message: str) -> DeployDecision:
    """模型可能先返回 list_git_tags，多一次往返。"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"""
部署任务。你可能需要查看 git tags。
当前事件：{initial_message}

返回 JSON：intent (deploy_backend_to_prod | list_git_tags | done_for_now)
"""}],
        response_format={"type": "json_object"},
    )
    # 如果返回 list_git_tags，这里要再调一次 fetch_git_tags，
    # 然后把结果回传给模型，模型再返回 deploy 或 done——多一次往返
    return DeployDecision.model_validate_json(resp.choices[0].message.content)

# 正例：代码预取 git tags，直接放进上下文
def fetch_git_tags() -> list[str]:
    """模拟从 git 仓库拉取 tags。"""
    return ["v1.0.0", "v1.1.0", "v2.0.0"]

def deploy_good(initial_message: str) -> DeployDecision:
    """代码预先 fetch tags，模型一次推理就能决策。"""
    tags = fetch_git_tags()  # 确定性预取
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"""
部署任务。当前可用的 git tags：{tags}
当前事件：{initial_message}

返回 JSON：intent (deploy_backend_to_prod | done_for_now), tag, message
"""}],
        response_format={"type": "json_object"},
    )
    return DeployDecision.model_validate_json(resp.choices[0].message.content)

# 用法
decision = deploy_good("发布 v1.1.0 到生产环境")
print(decision.intent, decision.tag)
```

`deploy_good` 把 `list_git_tags` 这个工具调用从模型手里收回来，变成代码的确定性预取。模型只做「用哪个 tag 部署」的判断，少一次往返，少一个工具定义。

## 一个代码审查 Agent 的完整路径

假设你在 GitHub 上配置了一个代码审查 Agent，每当有新 PR 就会触发。这条请求穿过 12 条原则的过程如下：

1. **触发（Factor 11）**：GitHub webhook 把 PR 事件推到消息队列，Agent 从队列里拿到事件——触发源和 Agent 本体完全解耦。
2. **组装上下文（Factor 3）**：Agent 从 PR 里提取 diff 内容，从向量数据库里检索相关代码规范，按优先级排列后填入上下文窗口——消息顺序和内容密度都是设计好的，不是随便塞进去的。
3. **构造提示词（Factor 2）**：提示词模板从 Git 仓库里拉取，和代码一起受版本管理。模板里定义了审查维度、输出格式和拒绝审查的条件。
4. **调用 LLM（Factor 1）**：自然语言描述的任务被发给模型，模型返回结构化审查意见。
5. **解析输出（Factor 4）**：返回的 JSON 被校验——是标准格式就继续，格式不对就走重试或降级路径。
6. **更新状态（Factor 5）**：审查结果直接写入 PR 的 review comment，Agent 的执行状态就是 PR 上的真实状态，不存在两套东西需要同步。
7. **人工确认（Factor 7）**：如果 Agent 发现潜在的安全问题，会通过工具调用向指定的代码 owner 发送确认请求，等待回复或超时。
8. **可中断运行（Factor 6）**：等待人工确认期间，Agent 的执行状态被持久化。即使服务重启，恢复后从持久化状态继续，不用重新审查整个 PR。
9. **错误注入上下文（Factor 9）**：调用外部 lint 工具失败时，错误信息被写进上下文窗口。下一次推理时，模型自己会避开同样的调用路径或给出降级建议。
10. **控制流归代码（Factor 8）**：Agent 的执行流程由代码编排——先跑静态检查、再跑 LLM 审查、最后汇总结果——模型只参与「这段代码是否有问题」的判断，不参与编排。
11. **单 Agent 单职责（Factor 10）**：这个 Agent 只做代码审查。生成 release notes、更新 changelog、打标签是另外的 Agent 或普通脚本的事。
12. **无状态推理（Factor 12）**：每次审查调用都是独立的——输入是 PR diff 和规范文档，输出是审查意见。下一次 PR 的审查不会「继承」上一次的内部状态，结果完全可复现。
13. **预取上下文（Factor 13）**：Agent 启动时直接从仓库拉取 PR 元数据、作者信息、最近 commit 列表，不留给模型「我要不要调这个工具」的往返。

## 从哪里开始

如果你正在把 LLM 应用推上生产环境，建议按以下顺序落地这 12 条原则：

**先做这 3 条（收益最大、成本最低）：**

- Factor 8（控制流）：把流程编排权从模型手里拿回来。这是单点改动，但对稳定性的影响立竿见影。
- Factor 9（错误压缩进上下文）：把错误信息写进上下文，不需要改架构。
- Factor 4（统一输出格式）：在 LLM 调用外层加一层 schema 校验，投入小。

**再做这 3 条（需要改架构，但值得）：**

- Factor 12（无状态 Reducer）：改推理模型为纯函数式，测试和调试的收益随 Agent 数量线性增长。
- Factor 6（启动 / 暂停 / 恢复）：长任务必须支持中断。
- Factor 11（事件驱动触发）：Agent 不再只能通过 HTTP 调用。

**最后做这些（属于精细化管理）：**

- Factor 2（提示词版本化）、Factor 3（上下文工程）、Factor 10（Agent 粒度拆分）等，在你已经跑通了基础流程之后再投入。
- Factor 13（预取上下文）放在最后，因为它依赖你对 Agent 调用模式的统计——得先跑一段时间，才知道哪些工具调用值得预取。

如果你的团队还在选框架阶段、Agent 还没上线，不如先把 Factor 8 和 Factor 4 落实——这两条能帮你在选框架时就排除掉一批把控制流交给模型的方案。

## 常见错误排查

落地 12 条原则时，下面这些问题高频出现。按症状定位，比从头排查快。

| 症状 | 可能的原因 | 排查方向 |
|------|-----------|----------|
| Agent 同样的输入跑两次结果不同 | 违反 Factor 12，reducer 有隐式状态或副作用 | 检查 reducer 函数是否读了全局变量、是否在 reducer 内直接调外部 API |
| LLM 输出偶尔导致下游代码崩溃 | 违反 Factor 4，没有 schema 校验层 | 在 LLM 调用出口加 Pydantic / JSON Schema 校验，失败走重试或降级 |
| Agent 长任务中断后无法恢复 | 违反 Factor 6，状态没持久化 | 把 AgentState 序列化到数据库或文件，恢复时反序列化 |
| Agent 行为突然变差，找不到原因 | 违反 Factor 2，提示词改动没记录 | 把提示词移进 Git 仓库，用 `git log` 查最近改动 |
| 人工介入请求丢失 | 违反 Factor 7，靠日志通知人 | 改成工具调用机制，请求进队列，有超时和重试 |
| 模型反复调用同一个失败工具 | 违反 Factor 9，错误没写进上下文 | 把工具失败的错误信息追加到上下文窗口 |
| Agent 提示词越来越长，输出质量下降 | 违反 Factor 10，单 Agent 塞了太多职责 | 按职责拆成多个小 Agent，各自独立上下文 |
| 上下文窗口经常超限 | 违反 Factor 3，没有压缩策略 | 实现历史压缩（保留摘要 + 最近 N 条）、检索片段按相关性裁剪 |
| 模型每次都先调 `list_xxx` 再决策 | 违反 Factor 13，没做预取 | 统计工具调用频率，高频工具改成代码预取 |

排查时先定位症状对应哪条原则被违反，再针对性修复。不要一次性改多条原则——改完一条跑一遍测试，确认有效再改下一条。

## 常见问题

**12-Factor Agents 和 LangChain / LlamaIndex 是什么关系？** 12-Factor 是工程约束集，不是框架。LangChain 这类框架可以用来实现 12-Factor Agent，但默认配置经常违反 Factor 8（让模型决定控制流）和 Factor 12（链路里有隐式状态）。用框架不等于自动满足 12 条，反过来不用框架也能手写满足 12 条的 Agent。

**Factor 12 要求无状态，那 Agent 怎么记住历史？** 历史不在 Agent 内部，在外部状态存储。reducer 的 `state` 参数就是从外部存储读进来的，reducer 算完新状态再写回外部存储。Agent 本身无状态，但系统有状态——状态在 reducer 之外。

**Factor 8 和 Factor 1 是不是重复了？** 不重复。Factor 1 讲「单次工具调用要结构化输出」，Factor 8 讲「整个流程的编排权在代码手里」。前者约束输出格式，后者约束控制流。一个 Agent 可以输出完全结构化（满足 Factor 1），但下一步做什么由模型决定（违反 Factor 8）。

**小团队有必要全部落地 12 条吗？** 没必要。先做 Factor 8、9、4 这三条收益最大的，跑稳之后再按需补。12 条是检查清单，不是上线门槛——但如果你的 Agent 处理的是钱、权限或生产数据，Factor 7（人工介入）和 Factor 6（可中断恢复）建议早做。

**Factor 13 为什么只是荣誉提及？** 因为它依赖前置条件——你得先有 Agent 运行一段时间、统计出工具调用频率，才知道哪些工具值得预取。新项目没数据，预取就是瞎猜。所以 Factor 13 放在最后，作为优化手段而不是基础约束。

**这些原则适用于多 Agent 系统吗？** 单 Agent 的 12 条原则在多 Agent 系统里仍然适用，每个 Agent 各自满足。多 Agent 系统额外需要考虑 Agent 之间的通信协议、状态传递、故障隔离——这些不在 12-Factor 范围内，需要参考其他工程实践。

**12-Factor Agent 和传统状态机有什么区别？** 状态机的状态转移是确定性的，12-Factor Agent 在 reducer 内部允许调用 LLM 做判断（Factor 8 的「判断节点」）。区别在于：状态机的转移规则全部写死，12-Factor Agent 把「需要智能的判断」交给 LLM、「流程编排」交给代码。可以理解为「带 LLM 判断节点的状态机」。

## 自测清单

逐条过一遍，诚实回答「是」或「否」。答「否」的条目，就是你下一步该动手的地方。

### 输入层

| 自测项 | 是/否 |
|--------|-------|
| Agent 调用的每个工具是否都有明确的结构化输出定义？ | |
| 提示词模板是否和代码一起进了版本管理？ | |
| 上下文窗口的内容布局是否有设计原则——什么在前、什么在后、什么可以压缩？ | |

### 执行层

| 自测项 | 是/否 |
|--------|-------|
| 下游代码是否需要「猜」LLM 返回的是什么格式？ | |
| Agent 的执行状态是否就是业务系统的真实状态，不存在两套状态需要对齐？ | |
| 长任务中断后能否从保存点恢复，而不是从头重跑？ | |

### 控制层

| 自测项 | 是/否 |
|--------|-------|
| Agent 需要人工介入时，是通过标准化的工具调用机制还是靠日志里打一句话？ | |
| 业务流程的编排权在代码手里还是模型手里？ | |
| 工具调用失败的错误信息是否写进了上下文窗口，供下一次推理使用？ | |

### 架构层

| 自测项 | 是/否 |
|--------|-------|
| 每个 Agent 是否只做一件事？ | |
| Agent 的触发方式是否只有 HTTP 一种？ | |
| 每次 Agent 调用是否可以写成 f(state, input) → new_state，输出只依赖输入而不是隐式状态？ | |

### 荣誉提及

| 自测项 | 是/否 |
|--------|-------|
| 是否统计过 Agent 的工具调用频率，把高频工具改成代码预取？ | |

## 实战练习

以下三个练习难度递增。第一个半小时内能做完，第三个可能需要一个下午——做完第三个之后，12 条原则就不再只是读过的文字，而是你实际用过的工程约束。

### 审计一个现有 Agent

找一个你正在开发或维护的 LLM 应用，拿出上一节的自测清单逐条打分。不要跳过任何条目。打完分之后，找出得分最低的两个层面，写一段 200 字以内的改进计划。

这个练习的价值不在打分本身，而在于强迫你用 12 条原则的视角重新审视自己写的代码。很多人做完会发现 Factor 8（控制流归代码）和 Factor 9（错误写进上下文）是改起来成本最低但收益最高的——恰好也是文章建议最先落地的。

### 落地 Factor 8 + Factor 4

找一个目前靠「给 LLM 一段提示词，让它自己决定下一步做什么」的 Agent 场景。做两个改动：

1. 把流程编排权从模型手里拿回来——用代码写清楚步骤，LLM 只在需要判断的节点被调用。
2. 在 LLM 调用出口加一层 schema 校验——输出不符合预期格式时不直接传给下游，而是走重试或降级路径。

完成后用同样的测试用例跑一遍，对比改动前后的输出稳定性。你会直观感受到「把控制权交给代码」和「把控制权交给模型」在实际运行中到底差在哪里。

### 从零设计一个符合 12 条原则的 Agent

挑一个你熟悉的业务场景——代码审查、客服分流、数据标注质检都可以——从零设计一个 Agent。要求：

- 写出一份设计文档，逐条说明你如何满足 12 条原则
- 画出触发链路、上下文组装流程、输出处理路径和人工介入节点
- 至少包含一个「任务流过系统」的完整路径描述，参考正文中代码审查 Agent 的写法
- 给出 Factor 13 的预取决策：哪些工具值得预取、依据是什么

这个练习不要求写代码，重点是设计。难的是在一个具体场景里同时满足它们时，不同原则之间的取舍和优先级。

## 参考资源

GitHub: [humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents)（Stars: 20,277 | TypeScript）

- [演讲视频：AI Engineer World's Fair](https://www.youtube.com/watch?v=8kMaTybvDUw)
- [深度解读视频](https://www.youtube.com/watch?v=yxJDyQ8v6P0)
- [Factor 3：掌控上下文窗口（完整原文）](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-03-own-your-context-window.md)
- [Factor 13：预取上下文（附录原文）](https://github.com/humanlayer/12-factor-agents/blob/main/content/appendix-13-pre-fetch.md)
- [npx 脚手架工具](https://github.com/humanlayer/12-factor-agents/discussions/61)：快速创建一个符合 12-Factor 的 Agent 项目
