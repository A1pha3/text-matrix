---
title: "AWS Agent Toolkit：AWS 官方给 AI 编码助手准备的 MCP + Skills 工具集"
slug: "aws-agent-toolkit-for-aws-mcp-skills-plugins-guide"
github_repo: "aws/agent-toolkit-for-aws"
date: "2026-06-25T21:05:40+08:00"
draft: false
categories: ["技术笔记"]
tags: ["AWS", "MCP", "Claude Code", "Cursor"]
description: "AWS Agent Toolkit 是 AWS 官方在 2026 年 4 月推出的 AI 编码助手增强包，把托管的 AWS MCP Server、Skills、Rules 打包成插件，覆盖 Claude Code、Codex、Cursor，并支持 Kiro 等 agent 通过 MCP + Skills 接入。"
---

## 快速信息卡

| 项目 | 信息 |
|------|------|
| **仓库地址** | [aws/agent-toolkit-for-aws](https://github.com/aws/agent-toolkit-for-aws)（agent 即智能体） |
| **Stars** | 2,470+ |
| **Forks** | 275+ |
| **许可证** | Apache-2.0 |
| **首发** | 2026-04-23 |
| **状态** | GA，仍在活跃更新 |
| **插件覆盖** | Claude Code、Codex、Cursor |
| **其他 agent** | MCP Server + Skills 接入（如 Kiro） |
| **数据核验** | 2026-08-29 |

## 读完本文能掌握什么

读完本文你能：

1. **说清 AWS Agent Toolkit 是什么**：不是单一工具，而是「托管 AWS MCP Server + Skills + Rules」三层资产，外加 4 个面向不同场景的插件入口，底层共享同一个托管 AWS MCP Server。
2. **区分 4 个插件的边界**：`aws-core`（通用开发）、`aws-agents`（AI Agent 构建）、`aws-data-analytics`（数据湖）、`aws-agents-for-devsecops`（安全与发布），知道什么场景装哪个。
3. **在不同入口完成接入**：Claude Code / Codex / Cursor 装插件，Kiro 和其他 agent 走「先连 MCP Server、再装 Skills」两步，也可以直接用 AWS CLI（命令行工具）。
4. **在 OAuth 和 SigV4 两种认证里选对一种**，理解各自适用的场景。
5. **理解 Skills / Rules / MCP Server 三层资产的分工**，并评估是否值得从 AWS Labs 旧版迁移。

## 目录

- [核心判断](#核心判断)
- [系统地图](#系统地图)
- [接入路径](#接入路径)
- [AWS MCP Server：执行层到底干了什么](#aws-mcp-server执行层到底干了什么)
- [认证：OAuth 还是 SigV4](#认证oauth-还是-sigv4)
- [Skills / Rules / MCP 的边界](#skills--rules--mcp-的边界)
- [一个任务怎么流过这套系统](#一个任务怎么流过这套系统)
- [跟 AWS Labs 的关系](#跟-aws-labs-的关系)
- [适用人群与采用顺序](#适用人群与采用顺序)
- [已知限制](#已知限制)
- [常见问题与故障排查](#常见问题与故障排查)
- [自测题](#自测题)
- [上手路线](#上手路线)
- [仓库信息卡](#仓库信息卡)

## 核心判断

AWS Agent Toolkit for AWS 是 AWS 官方在 2026-04-23 发布的「AWS × AI 编码助手」增强包，定位是此前散落在 AWS Labs 下的 MCP servers / skills / plugins 的后继版。它把「300+ AWS 服务接入 + 沙箱脚本执行 + 实时文档检索 + 审计与可观测」打包进一个托管的 AWS MCP Server（托管区域为 us-east-1 与 eu-central-1），再通过 Skills 和 Rules 把官方经验喂给编码助手。

仓库不是单一工具。4 个插件（`aws-core` / `aws-agents` / `aws-data-analytics` / `aws-agents-for-devsecops`）分别面向通用开发、AI Agent、数据湖、DevSecOps，插件入口覆盖 Claude Code、Codex、Cursor 三个 IDE（集成开发环境）的市场；Kiro 等其它 agent 没有插件市场，走「先连 MCP Server、再装 Skills」的路径。截至 2026-08-29 核验，仓库 2,470 Star / 275 Fork（派生）（Apache-2.0，主语言 Python，211 commits），最近 push（推送）在 2026-08-28，仍在快速迭代。

> 判断这套东西值不值得上，看三点：(1) 与 AWS Labs 的关系——官方明确这是「后继版」，旧仓库仍可用、仍接受 PR，最佳实践会逐步迁移；(2) IAM 条件键区分「人」和「agent」的动作——可以给 agent 单独写只读策略，即使底层角色有写权限；(3) CloudWatch 指标 + CloudTrail 审计覆盖每次请求——企业合规场景的硬需求。

## 系统地图

仓库的逻辑不是「一个工具干所有事」，而是分层组织。读懂这张图就知道什么时候装哪个。

| 层级 | 资产 | 作用 |
|------|------|------|
| 插件（plugins/） | `aws-core` / `aws-agents` / `aws-data-analytics` / `aws-agents-for-devsecops` | 把 MCP Server 配置 + Skills 打包成一键安装包，覆盖 Claude Code、Codex、Cursor 的市场 |
| Skills（skills/） | 任务导向的指令集与参考材料 | 编码助手按需加载——发现当前任务相关时才检索 |
| Rules（rules/） | 项目级建议配置 | 告诉 agent「用 AWS MCP Server」「先查文档再动手」 |
| AWS MCP Server | 托管的 Model Context Protocol 端点 | 真正干活的执行层，300+ AWS 服务、Python 沙箱、文档检索都走它 |

### 4 个插件的功能边界

| 插件 | 解决的问题 | 官方覆盖 | 起点 |
|------|-----------|----------|------|
| `aws-core` | 通用 AWS 应用开发 | 服务选型、CDK / CloudFormation、serverless（无服务器）、容器、存储、数据库、可观测、账单、SDK（软件开发包）用法、部署；内置 13 个技能（billing-and-cost-management、aws-serverless、cdk、cloudformation、observability、containers、storage、bedrock、aws-sdk-python-usage、aws-sdk-js-v3-usage、aws-sdk-swift-usage、aws-blocks、aws-database（数据库）） | **Start here**（README 明确写明） |
| `aws-agents` | 在 AWS 上构建 AI agent | 用 Amazon Bedrock 与 AgentCore 构建 agent | 写 agent 才装 |
| `aws-data-analytics` | 数据湖与分析 | S3 Tables、AWS Glue、Athena 的数据湖 / 分析 / ETL | 跑数仓才装 |
| `aws-agents-for-devsecops` | 安全与发布就绪 | 调查事故、代码评审与 UAT、漏洞扫描、渗透测试，配合 AWS DevOps Agent / AWS Security Agent | 安全 / 发布门禁才装 |

### 资产关系图

```text
+--------------------------------------------------------------+
|                    用户侧接入                                  |
|  插件市场：Claude Code / Codex / Cursor                       |
|  MCP + Skills：Kiro 等其它 agent                              |
|  AWS CLI：aws configure agent-toolkit                       |
+--------------------------------------------------------------+
                          │
                          ▼
+--------------------------------------------------------------+
|                  4 个插件 (plugins/)                           |
|  aws-core | aws-agents | aws-data-analytics | devsecops      |
+--------------------------+-----------------------------------+
                          │  按需加载
                          ▼
+--------------------------------------------------------------+
|   Skills（指令+参考）   +   Rules（项目级建议）                |
+--------------------------------------------------------------+
                          │  MCP 协议
                          ▼
+--------------------------------------------------------------+
|       AWS MCP Server（托管：us-east-1 / eu-central-1）        |
|  search_documentation（无需认证）   retrieve_skill（无需认证）|
|  call_aws（300+ 服务）              run_script（Python 沙箱）|
|  · IAM 条件键区分 agent/人  · CloudWatch 指标                 |
|  · CloudTrail 审计日志                                        |
+--------------------------------------------------------------+
```

## 接入路径

不同入口的接入方式不一样，下面是仓库 README 公开的命令。先确认 `uv`（https://docs.astral.sh/uv/）已经装好；需要 API（应用程序接口）调用和脚本执行时，本地还得有配好凭证的 AWS 账户，光查文档、拉 Skills 不强求。

### AWS CLI

如果只想在终端里直接驱动 agent，不经过 IDE 插件：

```bash
aws configure agent-toolkit
```

完整的配置、认证与用法见官方 [AWS CLI integration guide](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/aws-cli.html)。

### Claude Code

`claude-plugins-official` 市场默认就在 Claude Code 里，直接装：

```bash
# 通用入口，先装这个
/plugin install aws-core@claude-plugins-official

# 写 agent 用
/plugin install aws-agents@claude-plugins-official

# 数据分析用
/plugin install aws-data-analytics@claude-plugins-official

# 安全 / DevSecOps
/plugin install aws-agents-for-devsecops@claude-plugins-official
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

### Kiro（MCP + Skills 两步）

Kiro 没有插件市场，接入分两步，且这两步互相独立：MCP Server 管运行时的 AWS API 和文档检索，Skills 管任务级指导。Skills 不依赖 MCP Server，MCP Server 也不服务本地装的 Skills。

第一步，在 `.kiro/settings/mcp.json` 里配 MCP Server：

```json
{
  "mcpServers": {
    "aws": {
      "command": "uvx",
      "args": [
        "mcp-proxy-for-aws@1.6.4",
        "https://aws-mcp.us-east-1.api.aws/mcp",
        "--metadata", "AWS_REGION=us-west-2"
      ]
    }
  }
}
```

> README 明确建议钉死版本（当前示例是 `@1.6.4`），原因有两个：(1) 行为可复现；(2) 规避供应链（supply chain）风险。PyPI 上有新稳定版应定期更新。

第二步，装 Skills：

```bash
npx skills add aws/agent-toolkit-for-aws/skills
```

这条命令把 Skills 装到 `~/.kiro/skills/`（全局）或 `.kiro/skills/`（项目级），每个 Skill 是一个目录，内含一个 `SKILL.md`，可选配 `references/` 子目录放补充材料。Kiro 自动发现并按任务按需激活。

### 其他 agent

先按官方 [AWS MCP Server getting started](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/getting-started-aws-mcp-server.html) 配置 MCP Server，再装 Skills，逻辑都是「先连上 MCP Server，再装 Skills」。

```bash
npx skills add aws/agent-toolkit-for-aws/skills
```

## AWS MCP Server：执行层到底干了什么

Skills 和 Rules 是给 agent 看的「说明书」，真正调用 AWS 的执行层是 AWS MCP Server——一个托管的远程 MCP 服务，公开四类能力（对应 4 个工具）：

1. **`search_documentation`**——实时检索 AWS 当前文档、API 参考和服务能力，无需认证，避免训练数据过期。
2. **`retrieve_skill`**——按需发现并检索相关 Skills，无需认证。
3. **`call_aws`**——通过单一认证端点调用 300+ AWS 服务，agent 不用为每个服务单独配凭据。
4. **`run_script`**——在隔离沙箱里执行 Python 脚本，处理多步复合操作（比如先查 EC2 状态、再决定要不要启停）。

托管区域目前两个：us-east-1（弗吉尼亚北部）`https://aws-mcp.us-east-1.api.aws/mcp` 和 eu-central-1（法兰克福）。**端点区域决定连哪个服务器**，`AWS_REGION` 元数据参数才是设置 agent 操作默认区域的，不设默认 us-east-1。很多人在这一步把两者混在一起，先分清再配。

企业级控制默认全开：CloudWatch 指标、IAM 条件键（区分 agent vs. 人的动作）、CloudTrail 审计日志。IAM 条件键那条值得展开：可以给 agent 写一条策略，限制它只能做只读操作（即使底层 IAM 角色拥有写权限），这是给生产环境「agent 误删资源」上保险的常用手段，也是 AWS Labs 旧版 MCP 没有、企业用户最常要求的特性。

## 认证：OAuth 还是 SigV4

AWS MCP Server 支持两种认证方式，先分清再配，否则容易卡在「浏览器弹不出授权」或「多账户切不过来」上。

| 决策问题 | 选哪个 |
|----------|--------|
| 想不装 uvx、不装 AWS CLI、不配本地凭证就起步？ | OAuth |
| 客户端只支持远程 MCP Server（不跑本地进程）？ | OAuth |
| 同一个会话里要跨多个 AWS 账户？ | SigV4 |
| 需要只读模式，干脆把写类工具对 agent 隐藏？ | SigV4 |
| 组织限制了 OAuth 登录所需的 `signin:AuthorizeOAuth2Access`、`signin:CreateOAuth2Token` 权限？ | SigV4 |
| 要设置会话默认区域（不用每次查询都带 `AWS_REGION`）？ | SigV4 |

**OAuth（简单）**：客户端自动处理 OAuth 流程，首次调用工具时浏览器弹出 AWS Sign-in。需要给 IAM 角色或用户挂托管策略 `AWSMCPSignInOAuthAccessPolicy`。访问令牌首次授权后 1 小时有效，AWS Sign-in 自动刷新最长 12 小时。Claude Code、Cursor、Kiro IDE、Gemini CLI、Codex CLI 等大多支持，部分客户端要在端点 URL 后追加 `?oauth=initialize`。注意 OAuth 不支持多账户切换。

**SigV4（进阶）**：用 MCP Proxy for AWS（代理，https://github.com/aws/mcp-proxy-for-aws）以 SigV4 签名请求。前置：AWS CLI 2.32.0 以上，`aws login` 登录（凭据每 15 分钟轮换、会话最长 12 小时），`aws sts get-caller-identity` 验证，装好 uv。适合终端 / IDE 类编码助手（Claude Code、Kiro、Codex），支持多配置文件跨账户。

## Skills / Rules / MCP 的边界

仓库文档反复出现这三个词，分清它们才能知道「agent 到底从哪里拿答案」：

- **Skills** 是「任务型」指令包——「如何用 CDK 写 Lambda + API Gateway（网关）」「如何用 Bedrock AgentCore 接 MCP 工具」「如何用 S3 Tables + Glue 跑数据湖」。agent 按需加载，不相关的 Skills 不会进入上下文，节省 token（词元）。安装命令：`npx skills add aws/agent-toolkit-for-aws/skills`。
- **Rules** 是「项目级」建议——把「用 AWS MCP Server」「先查文档再动手」「遵循 CDK best practice」这些策略写进项目仓库的 `rules/` 目录。agent 启动会话时会自动读。
- **AWS MCP Server** 是「执行层」——按 agent 的指令去调 AWS、跑 Python、查文档。

写 agent 提示词时，三者的关系是：Rules 给「原则」、Skills 给「流程」、MCP Server 给「动作」。

## 一个任务怎么流过这套系统

把抽象分层串起来看一个具体任务：让 agent「用 CDK 部署一个带 API Gateway 的 Lambda，并核对这周的成本」。

1. 会话开始，项目里的 Rules 被自动读入，agent 知道该用 AWS MCP Server、先查文档再动手。
2. agent 判断这个任务相关，从本地 Skills 里按需加载 `cdk`、`aws-serverless`、`billing-and-cost-management`，不相关的 Skill 不进上下文。
3. 对拿不准的 API 细节，先调 `search_documentation` 查当前文档——这一步不需要任何凭证。
4. 需要真实操作时，`call_aws` 带上凭据调用 CloudFormation / Lambda / API Gateway，动作受 IAM 条件键约束（比如 agent 只能改这个环境、不能碰生产）。
5. 需要把参数算一遍、写个小工具时，`run_script` 在沙箱里跑 Python。
6. 每次调用都落进 CloudWatch 指标和 CloudTrail 审计，团队事后能复盘 agent 到底动了什么。

这条链上没有任何一步要求为每个 AWS 服务单独配凭据，这就是它和「给 agent 一把 AdministratorAccess 让它自己拼 boto3」的差别。

## 跟 AWS Labs 的关系：后继版，不是替代

仓库 README 明确写了一段 2025 年的故事：AWS Labs（https://github.com/awslabs）下曾经有散落的 MCP servers / skills / plugins，Agent Toolkit for AWS 是它们的「后继版本」。选择迁移的理由有三个：

1. **IAM 条件键**——能区分「人」和「agent」的动作，agent 即便拿到高权限角色，也可以被策略压成只读。
2. **可观测 + 审计**——CloudWatch 指标 + CloudTrail 日志覆盖每次请求，团队能审计编码助手在生产环境干了什么。
3. **Skills 端到端评估**——Agent Toolkit 的 Skills 经过完整 e2e 评估，AWS Labs 旧版未必都跑过同等流程。

旧版仍然可用，也仍然接受 PR，但「最佳的那部分」会逐步迁过来。对已经在用 AWS Labs 旧版的团队，评估迁移成本时只算「用到的子集」，不用一刀切全切。

## 适用人群与采用顺序

不是所有团队都需要立刻装。

**适合立刻装 `aws-core`**：已经在用 Claude Code / Codex / Cursor / Kiro 写 AWS 应用的团队。装完之后 agent 能直接查 AWS 文档、写 CDK / CloudFormation、调 Lambda / API Gateway，省掉「手翻 AWS 文档 + 自己写 IAM 策略 + 拼 boto3 代码」这一长串。

**再考虑 `aws-agents`**：在 AWS 上做 agent 项目的团队。Bedrock AgentCore、Strands、LangGraph 都是 agent 开发的新框架，agent 自己写很容易踩坑（cold start、限流、IAM 越权），Skills 里把这些都封装好。

**再考虑 `aws-data-analytics`**：跑数据湖 / 数仓 / ETL 的团队。S3 Tables 是 2025 年才 GA 的新服务，自己接 Glue + Athena 链路容易写错。

**最后看 `aws-agents-for-devsecops`**：release pipeline 里有 UAT 评审、漏洞扫描、渗透测试环节的团队。配合 AWS DevOps Agent / AWS Security Agent 用。

**不建议装的场景**：(1) 团队不在 AWS 上——这套工具栈强绑 AWS API 和 AWS 文档，跨云场景覆盖不到；(2) 团队只用本地 LLM（大语言模型）或自托管模型——AWS MCP Server 的云端执行层是必备组件；(3) 项目还在 PoC 阶段、agent 还没真接入生产——先用 `aws-core` 试水，再决定要不要扩到全 4 个插件。

## 已知限制

读仓库时同时注意几件事，避免在生产里翻车：

- **版本钉死**：README 建议钉死 `mcp-proxy-for-aws@x.y.z` 版本（当前示例 `1.6.4`），定期跟 PyPI（https://pypi.org/project/mcp-proxy-for-aws/）同步。固定版本不是「可选项」，是 README 明确点名的安全实践。
- **托管区域有限**：目前只有 us-east-1 和 eu-central-1 两个托管区域。`AWS_REGION` 元数据参数控制的是 agent 操作的默认区域（示例用 us-west-2），别把两者混为一谈。
- **权限最小化**：agent 拿到的 IAM 角色用「够用就行」的标准写，不要把 AdministratorAccess 直接给编码助手；要只读兜底就上 IAM 条件键。
- **Skills 是子集**：`npx skills add aws/agent-toolkit-for-aws/skills` 装的是仓库 `skills/` 目录下的全集；按需裁剪可以减少上下文开销，但仓库目前没提供「按服务选装」的细粒度 CLI。
- **审计与日志的合规对齐**：CloudWatch 指标和 CloudTrail 日志默认开启，但 retention（保留期）按账户默认走，长时间合规留痕需要单独配 S3 / Glacier 归档。

仓库本身是 GA 状态，但 AWS 仍在快速迭代——AgentCore 框架、AWS MCP Server 端点、Skills 列表都是月度更新级别的节奏，评估时以发布当时的 README 和 PyPI 版本为准。

## 常见问题与故障排查

**Q1：`/plugin install` 报 `Plugin not found` 怎么办？**
A：先运行 `/plugin marketplace update claude-plugins-official` 更新索引，再重试。如果仍是同样错误，检查插件名是否拼写正确（区分大小写）。

**Q2：MCP 端点区域和 `AWS_REGION` 是一回事吗？**
A：不是。MCP Server 只有 us-east-1 和 eu-central-1 两个托管端点，`https://aws-mcp.us-east-1.api.aws/mcp` 是默认参考端点；`AWS_REGION` 元数据参数（示例 us-west-2）设置的是 agent 操作 AWS 时的默认区域，不设则默认 us-east-1。

**Q3：为什么 README 建议钉死 `mcp-proxy-for-aws` 版本？**
A：两个原因：(1) 行为可复现；(2) 避免供应链风险。PyPI 上有新稳定版应定期更新，但不要在生产环境里用 `latest`。

**Q4：IAM 角色给了 AdministratorAccess，还需要额外配置吗？**
A：需要。按权限最小化原则，agent 拿到的 IAM 角色应该用「够用就行」的标准写。可以给 agent 单独写只读策略，即使底层 IAM 角色拥有写权限，也可以被策略压成只读。

**Q5：Skills 会全部进入上下文吗？**
A：不会。Skills 是按需加载的——agent 发现当前任务相关时才检索。但 `npx skills add aws/agent-toolkit-for-aws/skills` 装的是 `skills/` 目录下的全集，如果上下文窗口紧张，可以手动删除不相关的 Skill 文件。

**Q6：OAuth 登录后弹 400 错误页，或者根本没弹浏览器？**
A：先确认 IAM 角色 / 用户挂了托管策略 `AWSMCPSignInOAuthAccessPolicy`（涉及 `signin:AuthorizeOAuth2Access`、`signin:CreateOAuth2Token` 权限）。若客户端对远程 MCP 的自动发现不生效，在端点 URL 后追加 `?oauth=initialize` 强制触发授权流程。

**Q7：报 `ExpiredTokenException` 或 `No AWS credentials found` 怎么办？**
A：大多是临时凭据过期或没配好。SigV4 用户重新跑 `aws login`（每 15 分钟自动轮换，会话最长 12 小时），或通过 SSO（单点登录）执行 `aws sso login --profile 你的profile`；再用 `aws sts get-caller-identity` 验证凭据被识别。改完重启 MCP 客户端让服务器重新初始化。

**Q8：怎么确认 MCP Server 已经连上？**
A：在客户端里跑 `/mcp` 看已安装的 MCP 服务器，跑 `/tools` 看工具是否加载。应能看到类似 `aws___search_documentation`、`aws___retrieve_skill` 的工具名，再用一句「当前有哪些可用区域？」测一次调用。

## 自测题

1. **AWS Agent Toolkit 的 4 个插件分别解决什么问题？如果你只在 AWS 上做通用应用开发，应该先装哪个？**
   > `aws-core`（通用开发）、`aws-agents`（AI Agent）、`aws-data-analytics`（数据湖）、`aws-agents-for-devsecops`（安全）。通用开发先装 `aws-core`（README 明确写 "Start here"）。

2. **Skills / Rules / MCP Server 三层资产的分工是什么？写一个 AWS Lambda 函数时，这三层分别提供什么？**
   > Rules 给原则（「用 AWS MCP Server」「先查文档再动手」）；Skills 给流程（「如何用 CDK 写 Lambda + API Gateway」）；MCP Server 给动作（真正调 AWS API、跑 Python 沙箱）。

3. **为什么 AWS MCP Server 能区分「人」和「agent」的动作？举一个 IAM 条件键的使用场景。**
   > MCP Server 支持 IAM 条件键。场景：给 agent 单独写一条策略，限制它只能做只读操作（即使底层 IAM 角色拥有写权限），防止 agent 误删资源。

4. **从 AWS Labs 旧版 MCP servers 迁移过来，应该评估哪三条理由？**
   > IAM 条件键（区分人/agent）、可观测+审计（CloudWatch + CloudTrail）、Skills 端到端评估。评估时只算「用到的子集」，不用一刀切全切。

5. **Kiro 的接入为什么是「先配 MCP Server、再装 Skills」的两步走？其他 IDE 是一键安装吗？**
   > Kiro 没有插件市场，MCP Server 和 Skills 是相互独立的两步：MCP 管运行时 API 与文档检索，Skills 管任务级指导。Claude Code、Codex、Cursor 有插件市场，可以一键安装（插件包里已包含 MCP 配置和 Skills）。

6. **你需要在同一个会话里切换多个 AWS 账户，应该选哪种认证？为什么？**
   > SigV4，配合多个命名配置文件。OAuth 不支持多账户切换。

7. **想让 agent 只能读、不能写，有哪两条手段？**
   > 一是 IAM 条件键只读策略（即使底层角色有写权限也能压住）；二是 SigV4 只读模式，把写类工具对 agent 整体隐藏。

## 上手路线

**阶段一：会用（1-2 天）**
- 在主力 IDE 里装 `aws-core` 插件，跑通一个「查 AWS 文档 + 写 CDK 构造」的任务。
- 对比「有 MCP Server」和「没 MCP Server」两种场景下，agent 写出的 IAM 策略质量差异。
- 读一遍 `skills/` 目录下列表的 Skill 文件，理解 AWS 官方推荐的 agent 任务流程。

**阶段二：会配（1-2 周）**
- 按最小权限原则给 agent 单独写 IAM 策略，用 CloudTrail 审计 agent 的实际调用。
- 在 OAuth 和 SigV4 里按你的场景选一种配好，钉死 `mcp-proxy-for-aws` 版本，配置定期更新检查。
- 在项目 `rules/` 目录里加入 AWS 官方建议（「用 AWS MCP Server」「先查文档再动手」）。

**阶段三：会扩（1 个月+）**
- 按需装 `aws-agents`、`aws-data-analytics` 或 `aws-agents-for-devsecops`，覆盖 Agent 开发或数据湖场景。
- 把 Skills 里不相关的文件删掉，减少上下文开销。
- 为团队写一份「AWS Agent Toolkit 使用规范」，定义什么场景允许 agent 写操作、什么场景必须人工确认。

**阶段四：会推（团队采纳）**
- 在团队内统一 IDE 插件版本和 MCP Server 端点配置。
- 建立 agent 操作审计流程（CloudWatch 指标 + CloudTrail 日志 + 定期 review）。
- 参与 AWS 官方论坛或 GitHub Discussions，反馈使用问题或贡献新 Skill。

## 仓库信息卡

| 字段 | 值 |
|------|-----|
| 仓库 | [aws/agent-toolkit-for-aws](https://github.com/aws/agent-toolkit-for-aws) |
| 首发 | 2026-04-23 |
| 最近 push | 2026-08-28（仍在活跃更新） |
| Stars / Forks | 2,470 / 275 |
| License | Apache-2.0 |
| 主语言 | Python |
| 状态 | GA |
| 入口 | https://github.com/aws/agent-toolkit-for-aws |
| 用户指南 | https://docs.aws.amazon.com/agent-toolkit/latest/userguide/ |
| MCP Server 端点 | us-east-1：https://aws-mcp.us-east-1.api.aws/mcp；eu-central-1：https://aws-mcp.eu-central-1.api.aws/mcp |
| 4 个插件 | `aws-core` / `aws-agents` / `aws-data-analytics` / `aws-agents-for-devsecops` |
| 插件覆盖 | Claude Code、Codex、Cursor |
| Skills 安装命令 | `npx skills add aws/agent-toolkit-for-aws/skills` |
| 后继关系 | 替代 AWS Labs 下散落的 MCP servers / skills / plugins |
| 数据核验 | 2026-08-29（Stars / Forks / push 时间 / 版本号随仓库变化，以当时 README 为准） |
