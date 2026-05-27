---
title: "n8n-MCP：让 AI 编程助手帮你构建 n8n 工作流自动化"
date: "2026-05-03T20:00:00+08:00"
slug: "n8n-mcp-claude-workflow-automation-guide"
aliases:
  - "/posts/tech/n8n-mcp-ai-workflow-automation-guide/"
description: "n8n-MCP 是一个基于 Model Context Protocol 的 MCP 服务器，为 Claude、Cursor、Windsurf 等 AI 编程助手提供 n8n 工作流自动化平台的深度集成能力。本文详细解析其 1,650 个节点库、2,352 个模板、7 大核心工具及 13 个 n8n 管理工具的使用方法与架构设计。"
draft: false
categories: ["技术笔记"]
tags: ["n8n", "MCP", "Claude", "工作流自动化", "AI Agent"]
---

## 项目概览

**n8n-MCP**（仓库地址：[czlonkowski/n8n-mcp](https://github.com/czlonkowski/n8n-mcp)，MIT 许可证）是一个将 n8n 工作流自动化平台与 Model Context Protocol（MCP）接驳的桥梁项目。它以 MCP 服务器的形式运行，让 AI 助手能够理解、操作和构建 n8n 工作流，是目前 n8n 生态中与 AI 编程助手集成度最高的工具之一。

核心数据一览：

- **节点总数**：1,650 个（820 个核心节点 + 830 个社区节点，其中 741 个已验证）
- **节点属性覆盖率**：99%
- **节点操作覆盖率**：63.6%
- **官方文档覆盖率**：87%（含 AI 节点文档）
- **模板库**：2,352 个工作流模板，元数据 AI 标注覆盖率 99.96%
- **AI 工具变体**：265 个具备 AI 能力的工具变体
- **版本**：2.50.0（2026-05-02）

### n8n 是什么

n8n 是一个开源的工作流自动化平台，类似于 Zapier，但支持自托管和数据完全自主。与 AI 编程助手结合后，用户可以通过自然语言描述需求，AI 助手直接构建、修改、验证和部署 n8n 工作流，大幅降低自动化工作流的搭建门槛。

### MCP 在其中的角色

MCP（Model Context Protocol）是 Anthropic 提出的标准化协议，用于让 AI 编程助手与外部工具和数据源进行结构化通信。n8n-MCP 将 n8n 的节点系统、工作流模板和 n8n 实例管理能力封装为标准化的 MCP 工具，AI 助手通过这些工具即可完成从节点选型、参数配置到工作流验证的全流程操作，无需人工干预。

## 核心 MCP 工具详解

n8n-MCP 提供 **7 个核心文档类工具**（无需 n8n 实例即可使用）和 **13 个 n8n 管理工具**（需要配置 N8N_API_URL 和 N8N_API_KEY）。

### 文档类工具（7 个）

#### 1. `tools_documentation`

获取所有 MCP 工具的使用文档。这是使用 n8n-MCP 的起点，AI 助手通过它了解每个工具的输入输出格式和使用约束。

```
tools_documentation()
```

#### 2. `search_nodes`

全文搜索所有 n8n 节点。

```json
search_nodes({
  "query": "slack notification",
  "includeExamples": true
})
```

支持通过 `source` 参数过滤社区节点：

```json
search_nodes({
  "query": "openai",
  "source": "verified"
})
```

#### 3. `get_node`

统一节点信息查询工具，支持多种模式：

```json
// 获取基本信息（默认）
get_node({
  "nodeType": "n8n-nodes-base.slack",
  "detail": "standard",
  "includeExamples": true
})

// 获取极简元数据（约 200 tokens）
get_node({
  "nodeType": "n8n-nodes-base.slack",
  "detail": "minimal"
})

// 获取完整信息（约 3000-8000 tokens）
get_node({
  "nodeType": "n8n-nodes-base.slack",
  "detail": "full"
})

// 获取人类可读的 Markdown 文档
get_node({
  "nodeType": "n8n-nodes-base.slack",
  "mode": "docs"
})

// 搜索特定属性（如认证相关）
get_node({
  "nodeType": "n8n-nodes-base.slack",
  "mode": "search_properties",
  "propertyQuery": "auth"
})

// 版本信息与迁移指南
get_node({
  "nodeType": "n8n-nodes-base.slack",
  "mode": "versions"
})
```

> **注意**：LangChain 节点使用 `@n8n/n8n-nodes-langchain.` 前缀（如 `@n8n/n8n-nodes-langchain.agent`），核心节点使用 `n8n-nodes-base.` 前缀。

#### 4. `validate_node`

节点配置验证工具，支持三级验证策略：

```json
// 级别 1：快速检查，仅验证必填字段（<100ms）
validate_node({
  "nodeType": "n8n-nodes-base.slack",
  "config": {"resource": "message", "operation": "post"},
  "mode": "minimal"
})

// 级别 2：全面验证，含修复建议
validate_node({
  "nodeType": "n8n-nodes-base.slack",
  "config": {"resource": "message", "operation": "post"},
  "mode": "full",
  "profile": "runtime"
})

// 级别 3：AI 友好级别
validate_node({
  "nodeType": "n8n-nodes-base.slack",
  "config": {"resource": "message", "operation": "post"},
  "mode": "full",
  "profile": "ai-friendly"
})
```

**关于默认值的关键警告**：文档明确指出**默认值是运行时失败的第一大原因**，AI 助手在构建工作流时应显式配置所有控制节点行为的参数，而非依赖默认值。

#### 5. `validate_workflow`

工作流完整性验证，包括连接有效性、表达式语法、AI Agent 配置等。

```json
validate_workflow(workflow)
```

#### 6. `search_templates`

模板搜索工具，支持四种搜索模式：

```json
// 按关键词搜索（默认）
search_templates({
  "query": "slack notification"
})

// 按任务类型搜索
search_templates({
  "searchMode": "by_task",
  "task": "webhook_processing"
})

// 按节点类型搜索
search_templates({
  "searchMode": "by_nodes",
  "nodeTypes": ["n8n-nodes-base.slack"]
})

// 按元数据过滤
search_templates({
  "searchMode": "by_metadata",
  "complexity": "simple",
  "maxSetupMinutes": 30,
  "targetAudience": "developers"
})
```

过滤策略建议：

| 受众 | 参数组合 |
|------|---------|
| 初学者 | `complexity: "simple"` + `maxSetupMinutes: 30` |
| 营销人员 | `targetAudience: "marketers"` |
| 快速上手 | `maxSetupMinutes: 15` |
| AI 集成 | `requiredService: "openai"` |

#### 7. `get_template`

获取完整工作流 JSON，包含三种模式：

```json
// 仅节点列表
get_template("template-id", {mode: "nodes_only"})

// 工作流结构
get_template("template-id", {mode: "structure"})

// 完整工作流 JSON（可直接部署）
get_template("template-id", {mode: "full"})
```

### n8n 管理工具（13 个，需要配置 N8N_API_URL 和 N8N_API_KEY）

#### 工作流管理

| 工具 | 功能 |
|------|------|
| `n8n_create_workflow` | 创建新工作流 |
| `n8n_get_workflow` | 获取工作流详情 |
| `n8n_update_full_workflow` | 全量更新工作流 |
| `n8n_update_partial_workflow` | 通过 diff 操作更新工作流（推荐） |
| `n8n_delete_workflow` | 删除工作流 |
| `n8n_list_workflows` | 列表查询与分页 |
| `n8n_validate_workflow` | 在 n8n 实例中验证工作流 |
| `n8n_autofix_workflow` | 自动修复常见错误 |
| `n8n_workflow_versions` | 版本历史与回滚 |
| `n8n_deploy_template` | 从 n8n.io 模板市场直接部署 |

#### 执行管理

| 工具 | 功能 |
|------|------|
| `n8n_test_workflow` | 触发测试执行 |
| `n8n_executions` | 执行记录管理（列表、查看、删除） |

#### 凭证与安全

| 工具 | 功能 |
|------|------|
| `n8n_manage_credentials` | 凭证管理（创建、读取、更新、删除、获取 schema） |
| `n8n_audit_instance` | 安全审计（结合 n8n 内置 audit API 与深度工作流扫描） |
| `n8n_health_check` | n8n API 连接状态与功能特性检查 |

### 关键操作注意事项

#### `n8n_update_partial_workflow` 的 diff 操作

推荐使用 diff 操作而非全量覆盖，可以实现精细化更新：

```json
n8n_update_partial_workflow({
  "id": "wf-123",
  "operations": [
    {"type": "updateNode", "nodeId": "slack-1", "changes": {...}},
    {"type": "updateNode", "nodeId": "http-1", "changes": {...}},
    {"type": "cleanStaleConnections"}
  ]
})
```

#### `addConnection` 的四个参数要求

```json
{
  "type": "addConnection",
  "source": "node-id-string",
  "target": "target-node-id-string",
  "sourcePort": "main",
  "targetPort": "main"
}
```

#### IF 节点多输出路由

IF 节点有两个输出（TRUE 和 FALSE），必须使用 `branch` 参数明确指定路由目标：

```json
// 正确写法
{"type": "addConnection", "source": "If Node", "target": "True Handler",
 "sourcePort": "main", "targetPort": "main", "branch": "true"}
{"type": "addConnection", "source": "If Node", "target": "False Handler",
 "sourcePort": "main", "targetPort": "main", "branch": "false"}
```

## Claude Project 最佳配置

n8n-MCP 仓库提供了针对 Claude Projects 优化的系统指令（CLAUDE.md），推荐将其保存到 Claude Project 配置中以获得最佳效果。核心原则如下：

### 五大核心原则

1. **静默执行**：工具调用期间不输出说明文字，所有工具调用完成后统一响应
2. **并行执行**：独立的操作并行执行以提升效率
3. **模板优先**：始终先搜索模板（2,352 个可用），再从零构建
4. **多级验证**：minimal → full → workflow 三级验证递进
5. **绝不信任默认值**：所有控制节点行为的参数必须显式配置

### 推荐工作流

```
1. 调用 tools_documentation() 获取最佳实践
2. 搜索模板：search_templates() 按复杂度、任务或关键词搜索
3. 如无合适模板：search_nodes() 搜索节点，get_node() 获取配置
4. 配置阶段：validate_node() 以 minimal 和 full 两个级别验证
5. 构建阶段：使用 get_template() 获取完整 JSON，显式设置所有参数
6. 验证阶段：validate_workflow() → validate_workflow_connections()
   → validate_workflow_expressions()
7. 部署阶段：n8n_create_workflow() → n8n_validate_workflow()
```

## 安装与部署

### 最快上手（无需安装）

访问 **[dashboard.n8n-mcp.com](https://dashboard.n8n-mcp.com)**：

- 免费额度：每天 100 次工具调用
- 即时访问，无需基础设施维护
- 始终保持最新的节点和模板

### npx（快速本地安装）

```bash
npx n8n-mcp
```

Claude Desktop 配置（`~/Library/Application Support/Claude/claude_desktop_config.json`）：

```json
{
  "mcpServers": {
    "n8n-mcp": {
      "command": "npx",
      "args": ["n8n-mcp"],
      "env": {
        "MCP_MODE": "stdio",
        "LOG_LEVEL": "error",
        "DISABLE_CONSOLE_OUTPUT": "true"
      }
    }
  }
}
```

> ⚠️ **重要**：`MCP_MODE: "stdio"` 是 Claude Desktop 的必需配置，缺少此环境变量会导致 JSON 解析错误。

开启完整 n8n 管理功能：

```json
{
  "mcpServers": {
    "n8n-mcp": {
      "command": "npx",
      "args": ["n8n-mcp"],
      "env": {
        "MCP_MODE": "stdio",
        "N8N_API_URL": "https://your-n8n-instance.com",
        "N8N_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Docker 部署

```bash
docker run -p 3000:3000 \
  -e MCP_MODE=http \
  -e N8N_API_URL=https://your-n8n-instance.com \
  -e N8N_API_KEY=your-api-key \
  ghcr.io/czlonkowski/n8n-mcp
```

### Railway 一键部署

仓库提供了 Railway 部署按钮和生产级 Dockerfile，支持自动构建和横向扩展。

### HTTP 部署模式

对于远程服务器部署，可以启用 HTTP 模式：

```bash
MCP_MODE=http node dist/mcp/index.js
# 或
npm run start:http
```

仓库提供了详细的 [HTTP Deployment 文档](./docs/HTTP_DEPLOYMENT.md) 和 [N8N HTTP Streamable Setup](./N8N_HTTP_STREAMABLE_SETUP.md)。

## 支持的 IDE

n8n-MCP 与多个主流 AI 编程 IDE 无缝集成：

- **Claude Desktop**：本地桌面集成，适合日常使用
- **Claude Code**：命令行工具，适合 CI/CD 场景
- **Cursor**：支持 MCP 协议的配置
- **Windsurf**：支持项目级规则配置
- **Codex**：OpenAI 的编程辅助工具
- **Antigravity**：另一个 MCP 集成方案

各 IDE 的详细配置文档位于仓库的 `docs/` 目录下。

## 安全注意事项

项目 README 中有一条**重要的安全警示**：

> **⚠️ 永远不要直接在生产环境工作流上使用 AI 编辑！** 始终在操作前：
> - 创建工作流副本
> - 先在开发环境测试
> - 导出重要工作流的备份
> - 部署前验证变更

n8n-MCP 还提供了详细的安全加固文档（`docs/SECURITY_HARDENING.md`）和隐私/遥测说明（`PRIVACY.md`），包含信任模型分析、工作流限制选项等企业级部署所需的内容。

## 架构设计亮点

从源码结构来看，n8n-MCP 采用了清晰的模块化架构：

```
src/
├── mcp/              # MCP 协议入口
├── services/         # 核心服务层（数据库、存储）
├── handlers/          # MCP 工具处理函数
├── n8n/              # n8n API 交互层
├── database/         # SQLite 存储服务
├── templates/        # 模板处理
├── nodes/            # 节点数据管理
├── errors/           # 统一错误处理
├── telemetry/        # 遥测数据收集
└── scripts/          # 数据抓取与维护脚本
```

依赖的核心库：

- `@modelcontextprotocol/sdk`：MCP 协议官方 SDK（版本 1.28.0）
- `n8n-core`、`n8n-nodes-base`、`n8n-workflow`：n8n 核心包
- `@n8n/n8n-nodes-langchain`：LangChain 集成节点
- `sql.js`：SQLite wasm 实现，支持无 native 依赖运行
- `zod`：运行时类型验证
- `express` + `express-rate-limit`：HTTP 模式下的 API 服务

数据存储使用 **SQLite**（通过 sql.js），节点数据库在构建时预填充，包含完整的节点 schema、文档摘要和模板元数据。

## 总结

n8n-MCP 是一个将 AI 编程助手与 n8n 工作流自动化深度集成的成熟方案。它的核心价值在于：

1. **消除记忆负担**：无需记忆 1,650 个节点的用法，AI 助手直接提供配置建议
2. **模板驱动开发**：2,352 个模板覆盖常见场景，AI 可以基于模板快速生成定制化工作流
3. **多级验证保障**：从节点参数到工作流全局的三级验证机制，降低运行时错误风险
4. **双向集成**：不仅能读文档，还能直接创建、更新、验证和部署 n8n 工作流
5. **多 IDE 支持**：Claude Desktop、Claude Code、Cursor、Windsurf 等主流工具均可使用

对于已经在使用 n8n 的团队，n8n-MCP 是将 AI 能力引入工作流设计的高效路径；对于希望学习 n8n 的开发者，它也是一个极佳的交互式学习工具，通过与 AI 助手的对话即可理解每个节点的用法和最佳实践。

---

**延伸阅读**：

- [n8n-MCP 官方 GitHub 仓库](https://github.com/czlonkowski/n8n-mcp)
- [n8n-MCP 在线 Dashboard](https://dashboard.n8n-mcp.com)
- [n8n 官方文档](https://docs.n8n.io)
- [Model Context Protocol 规范](https://modelcontextprotocol.io)
- [n8n-skills 仓库](https://github.com/czlonkowski/n8n-skills)（Claude Skills 增强包）
