---
title: "Agent Governance Toolkit：微软 AI Agent 安全护盾"
date: 2026-05-23T13:09:23+08:00
draft: false
categories:
  - 技术笔记
tags:
  - GitHub-Trending
slug: agent-governance-toolkit-microsoft-ai-agent-security
author: 钳岳星君
description: "微软出品的 AI Agent 治理工具包，提供策略执行、零信任身份验证、隔离执行环境和可靠性工程四大护盾，系统性覆盖 OWASP Agentic Top 10 全部 10 类安全风险。"
---
# Agent Governance Toolkit：微软 AI Agent 安全护盾

## 这套工具真正解决什么

Agent Governance Toolkit（以下简称 AGT）把 Agent 的不可控行为从模型概率层下沉到确定性代码层。提示词级别的安全约束（"请遵守规则"）依赖模型自律，构不成确定性的控制面。AGT 在模型意图到达工具之前，用代码拦截每一次工具调用、消息发送和 Agent 委托——拦截是否发生不取决于模型是否配合。

OWASP 在 [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/llm-top-10/) 的 LLM01:2025 Prompt Injection 条目中明确指出："it is unclear if there are fool-proof methods of prevention for prompt injection"（提示词注入可能没有万无一失的预防方法）。Andriushchenko 等人在 ICLR 2025 论文 [Jailbreaking Leading Safety-Aligned LLMs with Simple Adaptive Attacks](https://arxiv.org/abs/2404.02151) 中报告，对 GPT-4o、Claude 3、Llama-3 使用自适应攻击，越狱成功率达 100%。

AGT 项目红队测试报告显示，提示词级安全的策略违规率为 26.67%，应用层强制执行的违规率为 0.00%（数据来源：AGT 仓库 README，截至 v3.7.0）。这组数字测的是"在红队构造的注入场景下，危险动作是否真正发生"，反映的是应用层拦截的有效性，而不是模型本身是否更难被越狱。它不能推出 AGT 能消除提示词注入——注入仍可能成功，只是成功后的危险动作被代码层挡住。

**项目地址：** [github.com/microsoft/agent-governance-toolkit](https://github.com/microsoft/agent-governance-toolkit)
**当前版本：** v3.7.0（Public Preview，MIT 许可证，截至 2026 年 5 月）
**支持语言：** Python、TypeScript、.NET、Rust、Go

## 学习目标

读完本文后，你应当能够：

1. 说清 AGT 的四层护盾各自拦截哪类风险，以及为什么提示词级安全无法替代应用层拦截。
2. 用 `govern()` 包装一个工具函数，并编写 YAML 策略拦截危险动作。
3. 描述一次工具调用从 Agent 发起到被拒绝或放行的完整路径，指出四层护盾在哪一步介入。
4. 判断自己的团队是否需要 AGT，以及如果需要，应该先上哪一层。
5. 把 AGT 的能力映射到 OWASP Top 10 for LLM Applications 2025 的具体风险条目。

## 目录

- [这套工具真正解决什么](#这套工具真正解决什么)
- [学习目标](#学习目标)
- [总览：四层护盾与系统地图](#总览四层护盾与系统地图)
- [核心能力](#核心能力)
  - [策略执行引擎](#策略执行引擎)
  - [零信任身份验证](#零信任身份验证)
  - [隔离执行沙箱](#隔离执行沙箱)
  - [可靠性工程](#可靠性工程)
  - [可观测性与审计](#可观测性与审计)
- [快速上手](#快速上手)
- [任务如何流过系统](#任务如何流过系统)
- [风险覆盖：与 OWASP Top 10 for LLM Applications 2025 的映射](#风险覆盖与-owasp-top-10-for-llm-applications-2025-的映射)
- [适用场景与采用顺序](#适用场景与采用顺序)
- [常见问题与错误处理](#常见问题与错误处理)
- [自测检查](#自测检查)
- [相关工具](#相关工具)

## 总览：四层护盾与系统地图

AGT 的架构有四条独立主线，分别回答四个问题：动作是否允许、谁发起的、危险代码如何隔离、失控后如何止损。审计日志横切四层，记录每一次决策的完整上下文。

```text
Agent ──► 策略引擎 ──► 身份验证 ──► 审计日志
            (YAML/OPA/Cedar)  (SPIFFE/DID/mTLS)  (防篡改)
                 │                                    │
                 ├── 允许 ──► 工具执行（可选沙箱）       │
                 └── 拒绝 ──► 抛出 GovernanceDenied    │
                                                      ▼
                                               决策记录
```

四层护盾的职责边界如下：

| 护盾 | 解决的问题 | 技术栈 | 是否必需 |
|------|-----------|--------|---------|
| 策略执行 | 这个动作允许吗 | YAML、OPA（Open Policy Agent，开放策略代理）、Cedar | 是 |
| 身份验证 | 哪个 Agent 干的 | SPIFFE、DID、mTLS（双向 TLS 认证） | 多 Agent 场景必需 |
| 隔离沙箱 | 危险代码跑飞了怎么办 | 四特权环运行时 | 高风险工具必需 |
| 可靠性工程 | Agent 失控了怎么办 | 熔断、Kill switch、SLO 监控 | 生产环境必需 |

四层护盾都是可选的——多数团队从策略执行加审计日志起步，其余层按风险面扩大再补。

## 核心能力

### 策略执行引擎

策略引擎是 AGT 的第一道关卡，每一次工具调用都会被拦截并求值。默认拒绝（default deny）意味着策略不匹配时动作不会放行，遗漏规则不会导致越权。

AGT 支持三种策略后端：

- **YAML 策略**：项目原生格式，声明式规则，适合大多数团队。
- **OPA**：用 Rego（OPA 策略语言）编写，适合已有 OPA 基础设施的团队。
- **Cedar**：Amazon 出品的策略语言，适合需要细粒度权限模型的场景。

为什么需要单独的策略引擎？提示词约束是对模型的概率性请求，OAuth 2.0（开放授权 2.0）的 scope 和 IAM 角色只控制 Agent 能访问哪些服务，对 Agent 连上服务后执行什么动作无约束。持有 `query_database` 权限的 Agent 同样可以执行 `drop_table`，OAuth 2.0 scope 在此处失效。策略引擎补的就是这一层：在工具调用真正发生之前，用代码判断动作是否允许。

### 零信任身份验证

在多 Agent 系统里，五个 Agent 可能共享一个 API key。出问题时"某个 Agent 干的"无法支撑事件响应。AGT 的身份层为每个 Agent 分配独立身份：

- **SPIFFE**：工作负载身份框架，为 Agent 颁发可验证的身份凭证。
- **DID（去中心化标识符）**：跨组织 Agent 协作时的身份互信。
- **mTLS**：Agent 与工具之间的双向加密认证。

身份层与 MCP（Model Context Protocol，模型上下文协议）安全网关配合，可以检测工具投毒、名称抢注（typosquatting）和隐藏指令注入。MCP 是 Anthropic 提出的工具调用协议，AGT 的 MCP Security Gateway 在 MCP 工具注册和调用时做安全校验。MCP 工具来源不可信时，攻击者可以在工具描述中嵌入隐藏指令，诱导 Agent 执行危险动作；安全网关在注册阶段扫描工具元数据，在调用阶段校验参数与声明一致。

### 隔离执行沙箱

代码执行类工具（`execute_code`、`shell_exec`）一旦被恶意提示词触发，可能影响宿主系统。AGT 的 Agent Runtime 用四特权环隔离执行：

- **Ring 0**：内核级，最高权限，几乎不开放给 Agent。
- **Ring 1**：系统级，可访问文件系统和网络。
- **Ring 2**：应用级，受限文件和网络访问。
- **Ring 3**：用户级，仅可计算，无 I/O。

危险工具调用会被路由到低权限环执行。即使代码逃逸了模型约束，也无法触达宿主系统的敏感资源。四特权环借鉴 CPU 保护环设计，分层隔离让单层逃逸不等于全盘失守。

### 可靠性工程

Agent 在生产环境可能失控：无限循环、资源耗尽、级联失败。AGT 的 Agent SRE 模块提供：

- **熔断器（Circuit Breaker）**：连续失败超过阈值后自动断路，防止级联故障。
- **Kill switch**：一键停止失控 Agent，无需重启服务。
- **SLO 监控**：基于错误预算（error budget）自动降级。
- **限流（Rate Limiting）**：防止单个 Agent 耗尽配额，对应 LLM10:2025 Unbounded Consumption 风险。
- **混沌测试**：主动注入故障，验证治理策略是否生效。

### 可观测性与审计

审计日志不是普通的日志，而是防篡改的决策记录（Decision Record）。每一条记录包含：哪个 Agent（DID）、什么时间、请求了什么动作、命中了哪条策略、结果是允许还是拒绝。审计员和合规团队可以据此还原任意一次决策的完整上下文。

这一层对应 SOC 2、ISO 27001 等合规框架对"可追溯性"的要求——合规审计需要的是"谁能证明某次决策发生过、结果是什么"，普通应用日志做不到这一点。

## 快速上手

### 安装

```bash
pip install agent-governance-toolkit[full]
```

前置条件：Python 3.10+。如果只用 TypeScript SDK，需要 Node.js 18+ 和 npm 9+。

### 用 govern() 包装工具

用 `govern()` 包装一个工具函数，让它在每次调用时都走策略求值：

```python
from agentmesh.governance import govern

safe_tool = govern(my_tool, policy="policy.yaml")
# 每次调用都会被检查、记录、强制执行
```

`safe_tool` 在每次调用时求值 YAML 策略，记录决策，如果动作被阻止则抛出 `GovernanceDenied`。

### 定义 YAML 策略

```yaml
# policy.yaml
apiVersion: governance.toolkit/v1
name: production-policy
default_action: allow
rules:
  - name: block-destructive
    condition: "action.type in ['drop', 'delete', 'truncate']"
    action: deny
    description: "破坏性操作需要人工审批"
  - name: require-approval-for-send
    condition: "action.type == 'send_email'"
    action: require_approval
    approvers: ["security-team"]
```

调用效果：

```python
>>> safe_tool(action="read", table="users")
{'table': 'users', 'rows': 42}

>>> safe_tool(action="drop", table="users")
GovernanceDenied: Action denied by policy rule 'block-destructive':
  破坏性操作需要人工审批
```

### CLI 工具

```bash
agt doctor                                          # 检查安装
agt verify                                          # OWASP 合规检查
agt verify --evidence ./agt-evidence.json --strict  # 弱证据时 CI 失败
agt red-team scan ./prompts/ --min-grade B          # 提示词注入审计
agt lint-policy policies/                           # 校验策略文件
```

## 任务如何流过系统

用一个具体任务走一遍四层护盾的配合：用户让 Agent 清理数据库旧数据，Agent 决定调用 `drop_table` 工具。

```text
1. 用户请求 → "清理 users 表的旧数据"
2. Agent 决策 → 调用 drop_table(table="users")
3. AGT 拦截 → 策略引擎求值
   ├─ 命中规则 block-destructive
   ├─ action.type == "drop" 匹配
   └─ 决策：拒绝
4. 身份层记录 → DID:did:mesh:agent-7 发起调用
5. 审计层写入 → 防篡改决策记录
   ├─ agent: did:mesh:agent-7
   ├─ action: drop_table
   ├─ rule: block-destructive
   └─ decision: denied
6. 抛出 GovernanceDenied → Agent 收到异常，无法继续
7. Agent 向用户报告 → "该操作需要安全团队审批"
```

如果策略允许（比如 `web_search`），流程会多走两步：

```text
1-3. 同上，但策略引擎决策：允许
4. 身份层验证 → mTLS 双向认证通过
5. 沙箱层判断 → web_search 不需要沙箱，直接执行
6. SRE 层监控 → 记录延迟、检查限流
7. 审计层写入 → 决策记录 + 执行结果
8. 工具执行 → 返回搜索结果给 Agent
```

策略引擎的拒绝发生在代码层：被 AGT 拒绝的动作，Agent 在代码层面无法绕过。提示词级安全依赖模型自律，AGT 让越权动作在代码层不可执行——这是两者最根本的差别。

## 风险覆盖：与 OWASP Top 10 for LLM Applications 2025 的映射

OWASP Top 10 for LLM Applications 2025 是 OWASP GenAI Security Project 发布的大语言模型应用安全风险权威清单。AGT 项目徽章标注覆盖 OWASP Agentic Top 10 全部 10 类风险，本文按 OWASP 官方的 Top 10 for LLM Applications 2025 进行映射。

| OWASP 编号 | 风险名称 | AGT 防护方式 |
|-----------|---------|-------------|
| LLM01:2025 | Prompt Injection（提示词注入） | 应用层拦截，不依赖模型自律；PromptDefense Evaluator 做 12 向量注入审计 |
| LLM02:2025 | Sensitive Information Disclosure（敏感信息泄露） | 输出过滤，可对接 DLP（Data Loss Prevention，数据防泄漏）系统 |
| LLM03:2025 | Supply Chain（供应链） | SBOM（Software Bill of Materials，软件物料清单）扫描 + 签名验证 + 插件信任评分 |
| LLM04:2025 | Data and Model Poisoning（数据与模型投毒） | 输入校验 + 对比检测，Agent Marketplace 做插件来源审查 |
| LLM05:2025 | Improper Output Handling（输出处理不当） | 策略引擎校验工具输出，沙箱隔离下游执行 |
| LLM06:2025 | Excessive Agency（过度授权） | 最小权限策略 + 零信任身份 + require_approval 人工审批 |
| LLM07:2025 | System Prompt Leakage（系统提示词泄露） | 审计日志记录所有提示词交互，可对接告警 |
| LLM08:2025 | Vector and Embedding Weaknesses（向量与嵌入弱点） | MCP Security Gateway 检测工具投毒和隐藏指令 |
| LLM09:2025 | Misinformation（错误信息） | SRE 层监控输出质量，混沌测试验证降级路径 |
| LLM10:2025 | Unbounded Consumption（无界消耗） | 限流 + 熔断 + Kill switch + SLO 错误预算 |

需要说明边界：AGT 主要解决 LLM06（过度授权）和 LLM10（无界消耗）这两类应用层风险。LLM01（提示词注入）的根因在模型层，AGT 无法消除注入本身，但可以保证注入成功后危险动作仍被拦截。LLM04（数据投毒）和 LLM08（向量弱点）的防护依赖训练数据和嵌入层治理，AGT 在这里提供检测和审计能力，不替代训练数据安全工具。

## 适用场景与采用顺序

### 适用场景

- **企业 Agent 生产部署**：需要满足 SOC 2、ISO 27001 合规审计的团队。
- **高风险工具调用**：Agent 持有 `execute_code`、`drop_table`、`send_email` 等不可逆操作的权限。
- **多 Agent 协作**：多个 Agent 共享资源，需要跨 Agent 权限隔离和身份追溯。
- **MCP 工具生态**：使用 MCP 协议接入第三方工具，需要工具投毒检测。

### 不适用场景

- **纯对话型应用**：Agent 不调用任何工具，没有副作用，AGT 的策略引擎没有拦截点。
- **个人脚本级 Agent**：单用户、低风险、无合规要求，引入 AGT 的运维成本不划算。
- **训练数据治理**：AGT 不解决数据投毒的根因，需要专门的训练数据安全工具。

### 采用顺序建议

如果团队决定引入 AGT，建议按以下顺序：

1. **先上策略执行 + 审计日志**。用 `govern()` 包装现有工具，编写 YAML 策略拦截破坏性动作。这两层覆盖 LLM06（过度授权）和 LLM10（无界消耗），且不依赖额外基础设施，投入产出比最高。
2. **多 Agent 场景再上身份层**。当 Agent 数量超过 3 个或跨团队协作时，引入 SPIFFE/DID 做身份隔离。
3. **高风险工具再上沙箱**。只有当 Agent 持有代码执行权限时，才需要 Agent Runtime 的四特权环。
4. **生产规模再上 SRE**。Agent 日均调用量过万或对延迟敏感时，启用熔断、限流和 Kill switch。

哪些团队该先上：金融、医疗、企业内部 IT 自动化等有合规要求、且 Agent 持有高风险工具的团队。哪些团队可以等：还在原型验证阶段、Agent 只做信息查询、没有不可逆副作用的团队。

## 常见问题与错误处理

### GovernanceDenied 异常处理

```python
from agentmesh.governance import govern, GovernanceDenied

safe_tool = govern(my_tool, policy="policy.yaml")

try:
    result = safe_tool(action="drop", table="users")
except GovernanceDenied as e:
    # 记录被拒原因，通知安全团队
    print(f"动作被拒：{e.rule_name} - {e.description}")
    # 走人工审批流程
    request_human_approval(e)
```

不要捕获 `Exception` 后忽略 `GovernanceDenied`——这等于把治理层重新打开一个口子。正确做法是捕获特定异常，记录上下文，走审批流程。

### 策略文件校验失败

运行 `agt lint-policy policies/` 检查策略文件语法。常见错误：

- `condition` 表达式引用了不存在的字段。
- `action` 值不是 `allow`、`deny`、`require_approval` 之一。
- `apiVersion` 与安装的 AGT 版本不匹配。

### 沙箱性能开销

沙箱模式会引入 10-30% 的延迟开销（数据来源：AGT 仓库文档，具体取决于工具类型和宿主环境）。对延迟敏感的场景，可以只对高风险工具启用沙箱，低风险工具直接执行。

### Azure 集成功能

部分高级功能（如 Azure AI Foundry 集成）需要 `AZURE_CLIENT_ID`、`AZURE_TENANT_ID`、`AZURE_CLIENT_SECRET` 环境变量。没有 Azure 订阅不影响核心治理功能。

## 自测检查

用以下问题检验对上文的理解：

1. 一个 Agent 同时持有 `query_database` 和 `drop_table` 权限，OAuth 2.0 scope 能否阻止它执行 `drop_table`？AGT 的策略引擎在哪一步拦截？
2. 团队有 5 个 Agent 共享一个 API key，出问题时如何定位是哪个 Agent 发起的危险调用？需要启用 AGT 的哪一层？
3. Agent 调用 `execute_code` 工具时，代码逃逸了模型约束，AGT 的哪一层负责限制影响范围？四特权环中哪一环适合执行不可信代码？
4. 团队刚开始引入 AGT，应该先上哪一层？为什么不是同时上所有层？
5. OWASP LLM01（提示词注入）的根因在模型层，AGT 如何在不修改模型的情况下降低这类风险？

## 相关工具

- [Superpowers](superpowers-agentic-development-methodology)
- [Claude Plugins Official](chrome-devtools-mcp-ai-coding-agents-chrome-devtools)
- [aidlc-workflows](aidlc-workflows-ai-driven-lifecycle-automation)
