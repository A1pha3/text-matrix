---
title: "AWS Agent Toolkit：AWS 官方给 Claude Code / Codex / Cursor / Kiro 准备的 MCP + Skills 工具集"
slug: "aws-agent-toolkit-for-aws-mcp-skills-plugins-guide"
date: "2026-06-25T21:05:40+08:00"
draft: false
categories: ["技术笔记"]
tags: ["AWS", "MCP", "Claude Code", "Cursor", "Kiro"]
description: "AWS Agent Toolkit 是 AWS 官方在 2026 年 4 月推出的 AI 编码助手增强包，把 AWS MCP Server、Skills、Rules 整合成 4 个可一键安装的插件，覆盖 Claude Code、Codex、Cursor、Kiro 等 IDE。"
---

## 核心判断

AWS Agent Toolkit for AWS 是 AWS 官方在 2026-04-23 发布的「AWS × AI 编码助手」官方增强包，定位是替代此前面向 AWS Labs 的 MCP servers / skills / plugins 散件。它把「300+ AWS 服务接入 + 沙箱脚本执行 + 实时文档检索 + 审计与可观测」打包成一个托管的 AWS MCP Server（端点 `https://aws-mcp.us-east-1.api.aws/mcp`），再通过 Skills 和 Rules 把官方经验封装给编码助手。

到 2026-06-25 时，仓库 1,021 Star / 109 Fork（Apache-2.0），结构上是 Python（557K）做工具调度、TypeScript（124K）做插件定义、Shell（118K）做安装脚本，发布状态徽章已经打上 GA。这个仓库不是单一工具，而是 4 个面向不同场景的插件入口（`aws-core` / `aws-agents` / `aws-data-analytics` / `aws-agents-for-devsecops`），下游用户在 Claude Code、Codex、Cursor、Kiro 任意一个 IDE 里都能装。

> 关键看三点：(1) 它跟 AWS Labs 的关系——这是「后继版」，AWS Labs 的旧仓库仍可继续工作并接受 PR，但最佳实践会逐步迁过来；(2) IAM 条件键区分「人」和「agent」的动作——可以给 agent 单独写只读策略；(3) CloudWatch 指标 + CloudTrail 审计每个 MCP 请求——企业合规场景的硬需求。

## 系统地图：4 个插件 + 3 类资产

仓库的逻辑不是「一个工具干所有事」，而是分层组织。读懂这张图就知道什么时候装哪个。

| 层级 | 资产 | 作用 |
|------|------|------|
| 插件（plugins/） | `aws-core` / `aws-agents` / `aws-data-analytics` / `aws-agents-for-devsecops` | 把下面三类资产打包成一键安装包，对应 4 个 IDE 的市场 |
| Skills（skills/） | 任务导向的指令集与参考材料 | 编码助手按需加载——发现当前任务相关时才检索 |
| Rules（rules/） | 项目级建议配置 | 告诉 agent「用 AWS MCP Server」「先查文档再动手」 |
| AWS MCP Server | 托管的 Model Context Protocol 端点 | 真正干活的执行层，300+ AWS 服务、Python 沙箱、文档检索都走它 |

### 4 个插件的功能边界

| 插件 | 解决的问题 | 关键服务覆盖 | 起点 |
|------|-----------|--------------|------|
| `aws-core` | 通用 AWS 应用开发 | CDK、CloudFormation、SAM、Lambda、API Gateway、Step Functions、ECS/Fargate、ECR、IAM、Bedrock（含 Knowledge Bases / Guardrails）、CloudWatch、XRay、CloudTrail、ADOT、SQS、SNS、EventBridge、Kinesis、MSK、SDK（boto3 / JS v3 / Swift）、成本优化 | **Start here**（README 明确写明） |
| `aws-agents` | 在 AWS 上构建 AI agent | Bedrock AgentCore（Strands、LangGraph）、Gateway + MCP、多 agent / A2A 编排、记忆、Cedar 策略、评估、可观测、debug trace、生产硬化（入站认证、IAM、限流、冷启动调优） | 写 agent 才装 |
| `aws-data-analytics` | 数据湖与分析 | S3 Tables、Glue、Athena 及相关 ETL | 跑数仓才装 |
| `aws-agents-for-devsecops` | 安全与发布就绪 | 调查事故、UAT 评审、代码漏洞扫描、渗透测试，配合 AWS DevOps Agent / AWS Security Agent | 安全 / 发布门禁才装 |

### 资产关系图

```
+--------------------------------------------------------------+
|                        用户 IDE                               |
|  Claude Code / Codex / Cursor / Kiro                         |
+--------------------------------------------------------------+
                          │  /plugin install
                          ▼
+--------------------------------------------------------------+
|                  4 个插件 (plugins/)                          |
|  aws-core  |  aws-agents  |  aws-data-analytics  |  devsecops |
+----------------------+--+--+--------------------------------+
                       │  │  │  按需加载
                       ▼  ▼  ▼
+--------------------------------------------------------------+
|   Skills（指令+参考）   +   Rules（项目级建议）               |
+--------------------------------------------------------------+
                          │  MCP 协议
                          ▼
+--------------------------------------------------------------+
|          AWS MCP Server（托管）                              |
|  https://aws-mcp.us-east-1.api.aws/mcp                      |
|  · 300+ AWS 服务调用 · Python 沙箱 · 实时文档检索             |
|  · IAM 条件键区分 agent/人  · CloudWatch 指标                |
|  · CloudTrail 审计日志                                       |
+--------------------------------------------------------------+
```

## 4 个 IDE 的安装路径

不同 IDE 的安装方式不一样，下面是仓库 README 公开的命令。先确认 `uv`（https://docs.astral.sh/uv/）已经装好；需要 API 调用和脚本执行时，本地还得有配好凭证的 AWS 账户，光看文档不调用 API 的话不强求。

### Claude Code

`claude-plugins-official` 市场默认就在 Claude Code 里，直接装：

```bash
# 通用入口，先装这个
/plugin install aws-core@claude-plugins-official

# 写 agent 用
/plugin install aws-agents@claude-plugins-official

# 数据分析用
/plugin install aws-data-analytics@claude-plugins-official

# 安全 / DevSecOps 走自有市场
/plugin marketplace add aws/agent-toolkit-for-aws
/plugin install aws-agents-for-devsecops
/reload-plugins
# 一次性 setup
/aws-agents-for-devsecops:setup
```

如果报 `Plugin not found`，先 `/plugin marketplace update claude-plugins-official` 更新索引再试。

### Codex

终端一行加市场：

```bash
codex plugin marketplace add aws/agent-toolkit-for-aws
```

然后在 Codex 里 `/plugins` 浏览并安装 **aws-core**（同样 `Start here`），其它三个按需。

### Cursor

从 **Settings → Plugins → Team Marketplaces → Add Marketplace → Import from Repo** 导入 `aws/agent-toolkit-for-aws`，Cursor 导入时会读仓库根目录的 [`.cursor-plugin/marketplace.json`](https://github.com/aws/agent-toolkit-for-aws/blob/main/.cursor-plugin/marketplace.json) 索引所有插件。

接着打开 **Plugins** 面板，至少装 `aws-core`；`aws-agents` 和 `aws-data-analytics` 按需。每个插件都自带 AWS MCP Server 配置和 Skills。

### Kiro

Kiro 走的是「先配 MCP Server、再装 Skills」的两步走。

`.kiro/settings/mcp.json` 里加：

```json
{
  "mcpServers": {
    "aws": {
      "command": "uvx",
      "args": [
        "mcp-proxy-for-aws@1.6.2",
        "https://aws-mcp.us-east-1.api.aws/mcp",
        "--metadata", "AWS_REGION=us-west-2"
      ]
    }
  }
}
```

> README 明确建议钉死版本（这里示例写的是 `@1.6.2`），原因有两个：(1) 行为可复现；(2) 避免供应链（supply chain）风险。PyPI 上有新稳定版应定期更新。

装完 MCP 再拉 Skills：

```bash
npx skills add aws/agent-toolkit-for-aws/skills
```

其它编码助手的接入路径见 [AWS MCP Server getting started](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/getting-started-aws-mcp-server.html)，逻辑都是「先连上 MCP Server，再装 Skills」。

## AWS MCP Server：执行层到底干了什么

Skills 和 Rules 是给 agent 看的「说明书」，真正调用 AWS 的执行层是 AWS MCP Server。它公开的能力可以归成四类：

1. **完整 AWS API 覆盖**——通过单一认证端点调用 300+ AWS 服务，agent 不再需要为每个服务单独配凭据。
2. **沙箱脚本执行**——agent 可以在隔离环境里跑 Python，处理多步复合操作（比如先查 EC2 状态、再决定要不要启停）。
3. **实时文档检索**——不需认证就能查 AWS 当前文档、API 参考和服务能力，避免训练数据过期。
4. **企业级控制**——CloudWatch 指标、IAM 条件键（区分 agent vs. 人的动作）、CloudTrail 审计日志全部默认开启。

IAM 条件键那条值得展开：可以给 agent 写一条策略，限制它只能做只读操作（即使底层 IAM 角色拥有写权限），这是给生产环境「agent 误删资源」上保险的常用手段，也是 AWS Labs 旧版 MCP 没有、企业用户最常要求的特性。

## Skills / Rules / MCP 的边界

仓库文档反复出现这三个词，分清它们才能知道「agent 到底从哪里拿答案」：

- **Skills** 是「任务型」指令包——「如何用 CDK 写 Lambda + API Gateway」「如何用 Bedrock AgentCore 接 MCP 工具」「如何用 S3 Tables + Glue 跑数据湖」。agent 按需加载，不相关的 Skills 不会进入上下文，节省 token。安装命令：`npx skills add aws/agent-toolkit-for-aws/skills`。
- **Rules** 是「项目级」建议——把「用 AWS MCP Server」「先查文档再动手」「遵循 CDK best practice」这些策略写进项目仓库的 `rules/` 目录。agent 启动会话时会自动读。
- **AWS MCP Server** 是「执行层」——按 agent 的指令去调 AWS、跑 Python、查文档。

写 agent 提示词时，三者的关系是：Rules 给「原则」、Skills 给「流程」、MCP Server 给「动作」。

## 跟 AWS Labs 的关系：后继版，不是替代

仓库 README 明确写了一段 2025 年的故事：AWS Labs（https://github.com/awslabs）下曾经有散落的 MCP servers / skills / plugins，Agent Toolkit for AWS 是它们的「后继版本」。选择迁移的理由有三个：

1. **IAM 条件键**——能区分「人」和「agent」的动作，agent 即便拿到高权限角色，也可以被策略压成只读。
2. **可观测 + 审计**——CloudWatch 指标 + CloudTrail 日志覆盖每次请求，团队能审计编码助手在生产环境干了什么。
3. **Skills 端到端评估**——Agent Toolkit 的 Skills 经过完整 e2e 评估，AWS Labs 旧版未必都跑过同等流程。

旧版仍然可用，也仍然接受 PR，但「最佳的那部分」会逐步迁过来。这条对已经在用 AWS Labs 旧版的团队意味着：评估迁移成本时只算「用到的子集」，不用一刀切全切。

## 适用人群与采用顺序

不是所有团队都需要立刻装。

**适合立刻装 `aws-core`**：已经在用 Claude Code / Codex / Cursor / Kiro 写 AWS 应用的团队。装完之后 agent 能直接查 AWS 文档、写 CDK / CloudFormation、调 Lambda / API Gateway，省掉「手翻 AWS 文档 + 自己写 IAM 策略 + 拼 boto3 代码」这一长串。

**再考虑 `aws-agents`**：在 AWS 上做 agent 项目的团队。Bedrock AgentCore、Strands、LangGraph 都是 agent 开发的新框架，agent 自己写很容易踩坑（cold start、限流、IAM 越权），Skills 里把这些都封装好。

**再考虑 `aws-data-analytics`**：跑数据湖 / 数仓 / ETL 的团队。S3 Tables 是 2025 年才 GA 的新服务，自己接 Glue + Athena 链路容易写错。

**最后看 `aws-agents-for-devsecops`**：release pipeline 里有 UAT 评审、漏洞扫描、渗透测试环节的团队。配合 AWS DevOps Agent / AWS Security Agent 用。

**不建议装的场景**：(1) 团队不在 AWS 上——这套工具栈强绑 AWS API 和 AWS 文档，跨云场景覆盖不到；(2) 团队只用本地 LLM 或自托管模型——AWS MCP Server 的云端执行层是必备组件；(3) 项目还在 PoC 阶段、agent 还没真接入生产——先用 `aws-core` 试水，再决定要不要扩到全 4 个插件。

## 已知限制

读仓库时同时注意几件事，避免在生产里翻车：

- **版本钉死**：README 建议钉死 `mcp-proxy-for-aws@x.y.z` 版本，定期跟 PyPI（https://pypi.org/project/mcp-proxy-for-aws/）同步。固定版本不是「可选项」，是 README 明确点名的安全实践。
- **MCP 端点区域**：示例写的是 `us-west-2`，按业务就近选区域。`https://aws-mcp.us-east-1.api.aws/mcp` 是仓库 README 给的参考端点，实际生产用之前先核对官方文档。
- **权限最小化**：agent 拿到的 IAM 角色用「够用就行」的标准写，不要把 AdministratorAccess 直接给编码助手。
- **Skills 是子集**：`npx skills add aws/agent-toolkit-for-aws/skills` 装的是仓库 `skills/` 目录下的全集；按需裁剪可以减少上下文开销，但仓库目前没提供「按服务选装」的细粒度 CLI。
- **审计与日志的合规对齐**：CloudWatch 指标和 CloudTrail 日志默认开启，但 retention（保留期）按账户默认走，长时间合规留痕需要单独配 S3 / Glacier 归档。

仓库本身是 GA 状态，但 AWS 仍在快速迭代——AgentCore 框架、AWS MCP Server 端点、Skills 列表都是月度更新级别的节奏，评估时以发布当时的 README 和 PyPI 版本为准。

## 仓库信息卡

| 字段 | 值 |
|------|-----|
| 仓库 | [aws/agent-toolkit-for-aws](https://github.com/aws/agent-toolkit-for-aws) |
| 首发 | 2026-04-23 |
| 最新更新 | 2026-06-25（仍在活跃 push） |
| Stars / Forks | 1,021 / 109 |
| License | Apache-2.0 |
| 主语言 | Python 557K、TypeScript 124K、Shell 118K |
| 状态 | GA |
| 入口 | https://github.com/aws/agent-toolkit-for-aws |
| 用户指南 | https://docs.aws.amazon.com/agent-toolkit/latest/userguide/ |
| MCP Server 端点 | https://aws-mcp.us-east-1.api.aws/mcp |
| 4 个插件 | `aws-core` / `aws-agents` / `aws-data-analytics` / `aws-agents-for-devsecops` |
| 支持的 IDE | Claude Code、Codex、Cursor、Kiro |
| Skills 安装命令 | `npx skills add aws/agent-toolkit-for-aws/skills` |
| 后继关系 | 替代 AWS Labs 下散落的 MCP servers / skills / plugins |
