---
title: "Agent Governance Toolkit：在工具调用前用代码拦住 Agent 的危险动作"
date: 2026-05-23T13:09:23+08:00
lastmod: 2026-09-07T00:00:00+08:00
draft: false
categories:
  - 技术笔记
tags:
  - GitHub-Trending
slug: agent-governance-toolkit-microsoft-ai-agent-security
github_repo: "microsoft/agent-governance-toolkit"
author: 钳岳星君
description: "微软出品的 AI Agent 治理工具包。每一次工具调用、消息发送和 Agent 委托都在到达网络之前被确定性代码拦截，策略执行、零信任身份、执行沙箱和可靠性工程四层可选叠加，官方自评覆盖 OWASP Agentic Top 10 中的 7 类完整、3 类部分。"
---

# Agent Governance Toolkit：在工具调用前用代码拦住 Agent 的危险动作

## 判断：治理不该靠求模型自律

Agent 一旦部署就是自主决策的。它调工具、查数据库、发消息、委托其它 Agent。要管住它，得先回答三个问题：这个动作允许吗、是哪个 Agent 干的、能不能证明发生过。提示词级的"请遵守规则"只是对随机系统的一次请求，不是控制面。

Agent Governance Toolkit（AGT）换了一条路：在模型意图到达工具之前，用确定性代码拦截每一次工具调用、消息发送和委托。被内核拒绝的动作不是"不太可能发生"，而是结构上不可能发生。这是"请求 Agent 守规矩"和"让它没有能力违规"的根本区别。

OWASP 在 [Top 10 for LLM Applications 2025](https://genai.owasp.org/llm-top-10/) 的 Prompt Injection 条目里明确写了："目前不清楚提示词注入是否有万无一失的预防方法"。Andriushchenko 等人在 ICLR 2025 论文 [Jailbreaking Leading Safety-Aligned LLMs with Simple Adaptive Attacks](https://arxiv.org/abs/2404.02151) 中报告：利用 logprob 访问、对提示词后缀（suffix）做随机搜索的自适应攻击，在 GPT-4o、GPT-3.5、Llama-3-Instruct-8B 等模型上拿到 100% 攻击成功率（GPT-4 担任评审）；不暴露 logprob 的 Claude 全系，用迁移或 prefilling 攻击同样达到 100%。这些数据指向同一个结论：在提示词这一层把注入挡干净做不到，能做的是保证注入成功后的危险动作在代码层被挡住。

**项目地址：** [github.com/microsoft/agent-governance-toolkit](https://github.com/microsoft/agent-governance-toolkit)

**核心数据（GitHub API 2026-09-07 验证）：** Python 主语言、MIT 许可证、main 分支、Stars 约 6.2k、Forks 约 1.1k、创建于 2026-03-02、最近推送 2026-09-04、最新标签 v5.0.0（提交于 2026-07-27）。一个容易混淆的点：PyPI 上 core/cli/integrations/protocols 四个发行版已是 5.0.0，但 meta 包 `agent-governance-toolkit` 仍停在 4.1.0；整体处于 Public Preview。仓库定位"Policy enforcement, zero-trust identity, execution sandboxing, and reliability engineering for autonomous AI agents"。

## 系统地图：四条独立主线，一层审计横切

AGT 的架构有四条独立主线，分别回答四个问题：动作是否允许、哪个 Agent 干的、危险代码如何隔离、失控后如何止损。审计日志横切四层，记录每一次决策的完整上下文。

```
Agent ──► 策略引擎 ──► 身份验证 ──► 审计日志
            (YAML/OPA/Cedar)  (SPIFFE/DID/mTLS)  (防篡改)
                 │                                    │
                 ├── 允许 ──► 工具执行（可选沙箱）    │
                 └── 拒绝 ──► 抛出 GovernanceDenied   │
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

关键在哪里：四层都是可选的。多数团队从策略执行加审计日志起步，其余层按风险面扩大再补。README 原话是"用 `govern()` 起步，随风险画像增长再加层，多数团队跑策略执行加审计日志就够，永远不需要全套"。

## 第一道关：策略执行引擎

策略引擎是 AGT 的第一道关卡，每一次工具调用都被拦截并求值。`default_action` 配置项缺省是 `deny`——没命中任何规则的动作不放行，遗漏的规则不会导致越权；策略求值出错时也按命中处理（fail-closed），宁可错杀不放行。下一节的示例策略显式写了 `default_action: allow`，那是团队自己选择放开这个默认值，换来的便利要以"规则写漏即放行"为代价。

AGT 支持三种策略后端：

- **YAML 策略**：项目原生格式，声明式规则，适合大多数团队。
- **OPA**：用 Rego（OPA 策略语言）编写，适合已有 OPA 基础设施的团队。
- **Cedar**：Amazon 出品的策略语言，适合需要细粒度权限模型的场景。

这一层补的是提示词约束和 OAuth 都管不到的位置。提示词约束是对模型的概率性请求；OAuth 2.0（开放授权 2.0）的 scope 和 IAM 角色只控制 Agent 能访问哪些服务，对 Agent 连上服务后执行什么动作没有约束。持有 `query_database` 权限的 Agent 同样可以执行 `drop_table`，scope 在此处失效。策略引擎补的就是这一层：在工具调用真正发生之前，用代码判断动作是否允许。

## 第二道关：零信任身份验证

在多 Agent 系统里，五个 Agent 可能共享一个 API key。出问题时无法定位是哪个 Agent 发起的危险调用。AGT 的身份层为每个 Agent 分配独立身份：

- **SPIFFE**：工作负载身份框架，为 Agent 颁发可验证的身份凭证。
- **DID（去中心化标识符）**：跨组织 Agent 协作时的身份互信。
- **mTLS**：Agent 与工具之间的双向加密认证。

身份层与 MCP（Model Context Protocol，模型上下文协议）安全网关配合。MCP 是协议，安全网关做的是工具投毒检测、漂移监控、名称抢注（typosquatting）和隐藏指令扫描。MCP 工具来源不可信时，攻击者可以在工具描述里嵌入隐藏指令诱导 Agent 执行危险动作；安全网关在注册阶段扫描工具元数据，在调用阶段校验参数与声明一致。

## 第三道关：隔离执行沙箱

代码执行类工具（`execute_code`、`shell_exec`）一旦被恶意提示词触发，可能影响宿主系统。AGT 的 Agent Runtime 用四特权环隔离执行，把危险工具调用路由到低权限环。即使代码逃逸了模型约束，也无法触达宿主系统的敏感资源。这也解释了为什么用了沙箱打开 `execute_code` 时，审计里会记录参数哈希和审批者身份——执行的不是"代码"，是"在受限环境里跑的代码"。

## 第四道关：可靠性工程

Agent 在生产环境可能失控：无限循环、资源耗尽、级联失败。AGT 的 Agent SRE 模块提供：

- **熔断器（Circuit Breaker）**：连续失败超过阈值后自动断路，防止级联故障。
- **Kill switch**：一键停止失控 Agent，无需重启服务。
- **SLO 监控**：基于错误预算（error budget）自动降级。
- **限流（Rate Limiting）**：防止单个 Agent 耗尽配额。
- **混沌测试**：主动注入故障，验证治理策略是否生效。

## 审计：普通日志做不到的防篡改决策记录

审计日志不是普通日志，而是防篡改的决策记录（Decision Record）。每一条记录包含：哪个 Agent（DID）、什么时间、请求了什么动作、命中了哪条策略、结果是允许还是拒绝。审计员和合规团队可以据此还原任意一次决策的完整上下文。这层能力对应的合规映射在仓库里可以直接查到：[SOC 2 控制映射](https://github.com/microsoft/agent-governance-toolkit/blob/main/docs/compliance/soc2-mapping.md)、EU AI Act 和 NIST AI RMF 对齐文档——合规审计需要的是"谁能证明某次决策发生过、结果是什么"。

## 快速上手

### 安装

```bash
pip install "agent-governance-toolkit[full]"
```

引号要带上：zsh 会把不带引号的 `[full]` 当作 glob 模式展开，直接报"no matches found"。前置条件是 Python 3.11+——PyPI 上 core/cli/integrations/protocols 四个 5.0.0 发行版的元数据都写明 `requires_python >= 3.11`，README 的 Quick Start 同口径（底部 Prerequisites 一节仍写 3.10+，两处以发布物元数据的 3.11+ 为准）。只用 TypeScript SDK 时需要 Node.js 18+ 和 npm 9+。`[full]` extra 会装进核心治理模块；基础 wheel 只装合规 CLI。旧版 `agent_os` 导入会触发 `DeprecationWarning`，改用 `agent-governance-toolkit-core` 或 `[full]` 即可。

### 用 govern() 包装工具

用 `govern()` 包装一个工具函数，让它每次调用都走策略求值：

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
  Destructive operations require human approval
```

### CLI 工具

```bash
agt doctor                                         # 检查安装
agt verify                                         # OWASP 合规检查
agt verify --evidence ./agt-evidence.json --strict # 弱证据时 CI 失败
agt red-team scan ./prompts/ --min-grade B         # 提示词注入审计
agt lint-policy policies/                          # 校验策略文件
```

### 集成方式

README 里除了 `govern()`，还有两类接入：

- **AgentControl API**：无状态、确定性、fail-closed 的策略决策运行时（Rust 内核），用 `AgentControl.from_path("manifest.yaml")` 按清单求值，适合程序化控制。
- **Claude Code 插件**：`/plugin marketplace add microsoft/agent-governance-toolkit` 注册市场，再 `/plugin install agt-governance@agent-governance-toolkit` 装插件。README 的原话是"Copilot CLI and Claude Code are first-party developer surfaces built on the TypeScript SDK"；OpenCode 另有独立的 npm 包 `@microsoft/agent-governance-opencode`。

## 任务如何流过系统

用一个具体任务走一遍四层护盾的配合：用户让 Agent 清理数据库旧数据，Agent 决定调用 `drop_table` 工具。

```
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

```
1-3. 同上，但策略引擎决策：允许
4. 身份层验证 → mTLS 双向认证通过
5. 沙箱层判断 → web_search 不需要沙箱，直接执行
6. SRE 层监控 → 记录延迟、检查限流
7. 审计层写入 → 决策记录 + 执行结果
8. 工具执行 → 返回搜索结果给 Agent
```

这条路径里没有"模型决定要不要守规矩"的环节：`drop_table` 调用被拦在工具执行之前，Agent 拿到的是 `GovernanceDenied` 异常和一条审计记录。换成提示词级方案，同样的请求能否被挡住，取决于模型当次的表现。

## 它到底覆盖了什么：对照 OWASP，别只看徽章

仓库徽章写的是"OWASP Agentic Top 10：10/10 Covered"。但这个数字是微软自己的自我评估，不是第三方认证。仓库自带的 [OWASP 合规对照文档](https://github.com/microsoft/agent-governance-toolkit/blob/main/docs/compliance/owasp-agentic-top10-architecture.md) 反而更诚实：对着 OWASP Agentic 2026（ASI01–ASI10）逐条标注，结果是 **7/10 完整覆盖、3/10 部分覆盖、0 缺口**。

部分覆盖的 3 项值得单独看：

| ASI 编号 | 风险 | AGT 覆盖 | 缺口在哪儿 |
|---------|------|---------|-----------|
| ASI04 | Agentic 供应链 | ⚠️ 部分 | 策略 YAML 能 pin 住工具名，但没有 SBOM |
| ASI06 | 记忆与上下文投毒 | ⚠️ 部分 | 审计用哈希链，但没有记忆沙箱 |
| ASI09 | 人类-Agent 信任利用 | ⚠️ 部分 | 有审计轨迹，没有 UI 级护栏 |

所以"覆盖 10 类"要读成"10 类都有对应机制，其中 3 类只做到部分"。AGT 真正做扎实的是 LLM06（过度授权）和 LLM10（无界消耗）这类应用层风险；对注入这类模型层根因，它做的是注入成功后的损害控制，而不是预防注入本身。

## 模块从 45 个收成 5 个：理解包结构

45 个包收成 5 个顶层发行版发生在 v4.0.0（CHANGELOG 列为破坏性变更，当时的五个是 core/runtime/sre/cli 加元包）。此后结构又动过一轮：以 PyPI 当前实际发布的清单为准，runtime 已并入 core（官方描述"Core runtime, kernel, and trust layer"）、SRE 并进 cli（"CLI tools, SRE observability, and sandbox isolation"），另拆出 integrations 和 protocols——README 折叠块里那份 core/runtime/sre/cli 清单已经过时，装 `agent-governance-toolkit-runtime` 或 `-sre` 会直接失败：

| 发行版 | 包含什么 |
|-------|---------|
| `agent-governance-toolkit[full]` | 元包，`[full]` extra 一键拉齐下述全部（当前停在 v4.1.0） |
| `agent-governance-toolkit-core` | 策略引擎、核心运行时与内核、信任层；README 折叠块口径还含能力模型、审计、MCP 网关、零信任身份、信任评分、A2A/MCP/IATP 桥接 |
| `agent-governance-toolkit-cli` | `agt` CLI、OWASP 验证、完整性检查、策略校验；SRE 可观测与沙箱隔离也在这个包里（熔断、Kill switch、SLO、混沌、特权环） |
| `agent-governance-toolkit-integrations` | 框架适配层：LangChain、CrewAI、OpenAI Agents 等 |
| `agent-governance-toolkit-protocols` | 协议实现：MCP governance、信任协议、A2A、MCP receipts |

旧包名（`agent-os-kernel`、`agentmesh-*` 等）保留为 stub 包，装了会重定向到新发行版。五门语言 SDK（Python、TypeScript、.NET、Rust、Go）都实现核心治理（策略、身份、信任、审计），Python 是唯一有完整栈的。

## 该不该用：采用顺序与适用边界

如果团队决定引入 AGT，建议按这个顺序：

1. **先上策略执行 + 审计日志**。用 `govern()` 包装现有工具，写 YAML 策略拦破坏性动作。覆盖过度授权和无界消耗，不依赖额外基础设施，投入产出比最高。
2. **多 Agent 场景再上身份层**。Agent 超过 3 个或跨团队协作时，引入 SPIFFE/DID 做身份隔离，出问题能定位到具体 Agent。
3. **高风险工具再上沙箱**。只有 Agent 持有代码执行权限时，才需要四特权环。
4. **生产规模再上 SRE**。Agent 日均调用量上规模或对延迟敏感时，启用熔断、限流和 Kill switch。

哪些团队该先上：金融、医疗、企业内部 IT 自动化这类有合规要求、且 Agent 持有高风险工具（`execute_code`、`drop_table`、`send_email`）的团队。哪些团队可以等：还在原型验证阶段、Agent 只做信息查询、没有不可逆副作用的团队，先引入反而增加运维成本。

几个不适用场景要认清：纯对话型应用（Agent 不调工具，没有拦截点）、个人脚本级 Agent（单用户低风险无合规要求）、训练数据治理（AGT 不解决数据投毒根因）。

## 常见问题与错误处理

### GovernanceDenied 异常处理

```python
from agentmesh.governance import govern, GovernanceDenied

safe_tool = govern(my_tool, policy="policy.yaml")

try:
    result = safe_tool(action="drop", table="users")
except GovernanceDenied as e:
    # 规则名和原因挂在 e.decision（PolicyDecision）上
    print(f"动作被拒：{e.decision.matched_rule} - {e.decision.reason}")
    # 走人工审批流程
    request_human_approval(e)
```

两个易错点：异常对象上只有 `.decision` 一个属性，规则名是 `e.decision.matched_rule`、原因是 `e.decision.reason`——直接在异常上找 `rule_name` 会得到 `AttributeError`。另外不要捕获 `Exception` 后忽略 `GovernanceDenied`，这等于把治理层重新打开一个口子。正确做法是捕获特定异常，记录上下文，走审批流程。

### 版本相关注意点

- 旧版 `agent_os` 导入会触发 `DeprecationWarning`，不是 bug，是迁移信号。改用 `agent-governance-toolkit-core` 或 `[full]`。
- 部分 Azure 集成功能（如 AI Foundry）需要 `AZURE_CLIENT_ID`、`AZURE_TENANT_ID`、`AZURE_CLIENT_SECRET` 环境变量。没有 Azure 订阅不影响核心治理功能。
- 项目是 Public Preview，正式 GA 前可能有 breaking change。上线前锁版本，别追最新。

### OpenAI 合规检查失败

`agt verify` 是在对照 OWASP 做自评，不是认证。结果里 `--evidence` 弱就配 `--strict` 让 CI 失败，逼自己补证据。别把 `agt verify` 的输出当成"通过审计"的证明。

## 参考资源

- [AGT GitHub 仓库](https://github.com/microsoft/agent-governance-toolkit)
- [AGT 官方文档](https://microsoft.github.io/agent-governance-toolkit/)
- [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/llm-top-10/)
- [OWASP 合规对照文档（ASI01–ASI10 自评）](https://github.com/microsoft/agent-governance-toolkit/blob/main/docs/compliance/owasp-agentic-top10-architecture.md)
- [SOC 2 控制映射](https://github.com/microsoft/agent-governance-toolkit/blob/main/docs/compliance/soc2-mapping.md)
- [CHANGELOG（版本演进与破坏性变更）](https://github.com/microsoft/agent-governance-toolkit/blob/main/CHANGELOG.md)
- [OPA Rego 文档](https://www.openpolicyagent.org/docs/latest/policy-language/)
- [SPIFFE 工作负载身份规范](https://spiffe.io/)

---

## 资料口径说明

本文基于 GitHub API 与仓库 README、CHANGELOG、OWASP 合规文档、`policy.py`/`govern.py` 源码、PyPI 各发行版元数据（2026-09-07 验证）编写。核心数据（Stars、Forks、语言、许可证、版本、最近推送）来自 GitHub API，随仓库变化会过时，引用时以当时 API 为准。

三点边界需要说明：

- 仓库徽章的"10/10 Covered"是微软的自我评估，不是第三方认证。本文采用仓库自带合规文档的诚实口径：7/10 完整、3/10 部分、0 缺口。
- 文中 `govern()` 签名、YAML 策略格式、`agt` 命令、AgentControl 用法均与 README 一致，但 AGT 仍处 Public Preview，API 可能随版本调整，落地前以官方文档当前版本为准。
- Python 版本要求以 PyPI 5.0.0 发行版元数据（`>=3.11`）与 README Quick Start 为准；README 底部 Prerequisites 的"3.10+"与上述两处不一致，属于文档内部口径分歧。