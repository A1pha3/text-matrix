---
title: "Cline：超越代码补全的 AI 编程助手"
slug: "cline-ai-coding-agent-guide"
description: "Cline 是一个基于 Claude Sonnet 的 AI 编程助手，可以创建和编辑文件、执行终端命令、使用浏览器、创建自定义 MCP 工具。它支持多种 API 提供商，包括 OpenRouter、Anthropic、OpenAI、Google Gemini、AWS Bedrock 等。"
date: "2026-04-24T11:40:00+08:00"
categories: ["技术笔记"]
tags: ["AI 编程", "Claude", "VS Code", "MCP", "开源工具"]
---

# Cline：把 AI 编程助手从补全推进到自主编程的边界

Cline 想回答的不是"AI 能不能写代码"，而是"AI 写代码时，人应该站在哪一层"。它的答案是：**模型负责自主编程能力，人负责每一步变更的审核与放行**。这与 GitHub Copilot 把人放在"接受/拒绝补全建议"那一层完全不同——Copilot 处理的是行级补全，Cline 处理的是"读文件 → 改文件 → 跑命令 → 看结果 → 再改"的多步循环。

Cline 适合谁：需要在 VS Code 里完成多文件改动、跑构建/测试、做端到端验证的开发者，尤其是 Web 应用场景下愿意为每一步变更点确认按钮的人。Cline 不适合谁：只想要行内补全、不想审核任何变更、或者任务本身就是单点问答的人——前者用 Copilot 更轻，后者直接问 Claude Desktop 或 ChatGPT 更直接。它和 Claude Code 的本质差异在入口形态：Cline 是 VS Code 扩展，把 Agent 循环嵌进编辑器；Claude Code 是 CLI，把 Agent 循环嵌进终端。两者底层都能调 Claude Sonnet，但工作流和审核姿态完全不同。

> **项目地址**：[github.com/cline/cline](https://github.com/cline/cline)

## 一、Cline 的组件构成与系统地图

Cline 是一个 VS Code 扩展，把 Claude Sonnet 的自主编程能力嵌进编辑器，让 AI 能在你的监督下完成"读文件 → 改文件 → 跑命令 → 看结果 → 再改"的循环。它不是 IDE 之外的独立产品，也不是 CLI——它的工作面就是 VS Code 的工作区。

```
┌─────────────────────────────────────────────────────────────────┐
│                        VS Code 编辑器                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Cline 扩展                              │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │  │
│  │  │  聊天面板   │  │  diff 视图  │  │  检查点时间线    │   │  │
│  │  │  (任务输入) │  │  (变更审核) │  │  (快照/还原)     │   │  │
│  │  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘   │  │
│  │         │                │                  │            │  │
│  │         ▼                ▼                  ▼            │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │          Agent 循环（核心调度层）                    │ │  │
│  │  │  分析 → 规划 → 执行 → 验证 → 完成                   │ │  │
│  │  └──┬──────────┬──────────┬──────────┬─────────────────┘ │  │
│  │     │          │          │          │                   │  │
│  └─────┼──────────┼──────────┼──────────┼───────────────────┘  │
│        ▼          ▼          ▼          ▼                       │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────┐       │
│  │文件编辑 │ │终端执行 │ │浏览器   │ │ MCP 工具扩展    │       │
│  │(diff)   │ │(shell)  │ │(Computer│ │ (自定义 server) │       │
│  │         │ │         │ │  Use)   │ │                 │       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────────────┘       │
└────────┬───────────┬───────────────────────────┬───────────────┘
         │           │                           │
         ▼           ▼                           ▼
   ┌──────────┐  ┌────────┐              ┌─────────────────┐
   │ 工作区   │  │ 系统   │              │  外部服务       │
   │ 文件树   │  │ shell  │              │ (Jira/AWS/...)  │
   └──────────┘  └────────┘              └─────────────────┘
                        │
                        ▼
              ┌─────────────────────┐
              │  LLM Provider       │
              │  (Claude Sonnet /   │
              │   GPT / Gemini /    │
               │   OpenRouter /      │
              │   本地模型)         │
              └─────────────────────┘
```

四个要点：

- **Cline 是 VS Code 扩展**，不是独立 IDE，也不是 CLI。它的工作面就是 VS Code 工作区，文件编辑、终端、diff 视图都复用 VS Code 的能力。
- **Agent 循环是核心调度层**：分析 → 规划 → 执行 → 验证 → 完成。所有四条机制都由这个循环驱动。
- **LLM 可替换**：默认走 Claude Sonnet，也支持 OpenRouter、OpenAI、Gemini、AWS Bedrock、本地模型。Cline 不绑死模型。
- **MCP 是能力扩展面**：模型本身不擅长直接操作外部系统（Jira、AWS、PagerDuty），MCP 提供标准协议让 Cline 调用自定义工具。

## 二、四条并行机制

Cline 不是"一个能力"，而是四条并行机制。它们各自的触发条件、代价和人工审核姿态不同。

| 机制 | 触发条件 | 代价 | 人工审核 |
|------|----------|------|----------|
| **文件编辑** | 创建/修改源码、配置、文档 | LLM 推理 + diff 视图渲染 | 每个文件变更在 diff 视图点确认 |
| **终端执行** | 安装依赖、跑构建、运行测试、部署 | LLM 推理 + 命令执行时间 + 系统资源 | 每条命令点批准；可选"运行时继续"放行长进程 |
| **浏览器测试** | Web 端到端验证（点击、截图、控制台日志） | LLM 推理 + Computer Use 调用 + 浏览器进程 | 启动浏览器、每次截图/点击可观察 |
| **MCP 工具** | 操作外部系统（Jira 工单、AWS EC2、PagerDuty 事件） | LLM 推理 + MCP server 进程 + 外部 API 调用 | 工具调用前展示参数，需确认 |

四条机制不是互斥的——一次任务里 Cline 可能先编辑文件、再跑终端命令、再启动浏览器验证、再调 MCP 工具拉取外部数据。但每一条都有独立的代价和审核姿态。

### 2.1 文件编辑

Cline 编辑文件时不会直接落盘，而是先在 VS Code 的 diff 视图里展示变更。你可以：

- 在 diff 视图里直接编辑 Cline 的改动
- 还原整个变更
- 在聊天里反馈，让 Cline 再改一轮

所有变更记录在文件的时间线里，方便事后追踪和还原。

### 2.2 终端执行

Cline 借助 VS Code v1.93 的 shell 集成，可以直接在终端里执行命令、接收输出并实时响应。覆盖场景包括安装依赖、运行构建、部署应用、管理数据库、执行测试。

对于长时间运行的进程（如开发服务器），Cline 提供"运行时继续"按钮——点击后命令继续在后台跑，Cline 不等它结束就继续下一步。这是为了让 Agent 循环不被 `npm run dev` 这类长进程卡死。

### 2.3 浏览器测试

Web 任务里 Cline 可以启动浏览器、点击元素、输入文本、滚动页面、捕获截图和控制台日志。这一层依赖 Claude Sonnet 的 Computer Use 能力（原因在第四节展开）。

### 2.4 MCP 工具

借助 Model Context Protocol（MCP），Cline 可以创建自定义工具来扩展能力。只需要求 Cline"添加一个工具"，它就会创建新的 MCP 服务器并注册到扩展中。

典型场景：获取 Jira 工单、管理 AWS EC2 实例、获取 PagerDuty 事件详情。

## 三、为什么需要 MCP

一个常见疑问：**为什么不直接让 Cline 在 prompt 里写"调用 Jira API"，而要绕一层 MCP？**

直接调 API 在工程上有三个硬问题：

1. **凭据管理**：API key 写在 prompt 里会被 LLM 看见，也会进入请求日志。一旦 prompt 被分享或日志被采集，凭据就泄露了。MCP 把凭据留在 server 进程里，LLM 只看到"调用这个工具"的抽象，不接触原始凭据。
2. **协议稳定性**：Jira、AWS、PagerDuty 各家 API 协议不同，版本迭代频繁。MCP 把"如何调外部系统"封装在 server 端，LLM 只需要知道"有这个工具、参数是什么"。
3. **可观测性**：直接调 API 时，调用过程对用户不可见。MCP 把每次工具调用都做成可观察的事件——Cline 会展示"即将调用 Jira MCP 工具，参数是 issue=PROJ-123"，用户可以审核、拒绝、追溯。

MCP 把凭据、协议、可观测性三件事从 LLM 那里剥离出来，让 Agent 调用外部系统变得可审核、可维护、可移植。

## 四、为什么用 Claude Sonnet 的 Computer Use

浏览器自动化这一层，Cline 依赖的是 Claude Sonnet 的 Computer Use 能力。Computer Use 是 Anthropic 给 Claude Sonnet 训练的"看屏幕、点鼠标、敲键盘"能力。它和传统的 Selenium / Playwright 脚本式自动化不同——后者是"写死步骤"，前者是"看截图决定下一步"。

- **优势**：Cline 不需要预先知道页面结构，遇到弹窗、布局变化、动态加载都能自适应。这是脚本式自动化做不到的。
- **代价一：调用成本**：每次 Computer Use 都要发截图给模型，截图越大、调用越频繁，token 消耗越高。一次完整的"测试这个应用"可能消耗数十次 Computer Use 调用，账单比纯文本对话贵一个数量级。
- **代价二：模型绑定**：Computer Use 是 Claude Sonnet 的能力，其他模型（GPT、Gemini、本地模型）目前没有等价能力。这意味着浏览器测试这一层事实上绑死 Anthropic——即便 Cline 的其他机制可以换模型，浏览器测试不能。
- **代价三：不确定性**：模型看截图决策不是确定性的，同样的页面、同样的任务，两次运行可能走不同路径。这对回归测试是缺点（不可复现），对探索性测试是优点（能发现脚本测不到的问题）。

如果完全不需要浏览器测试（后端、CLI 工具、库开发），可以忽略这一层，Cline 仍然能用其他模型工作。

## 五、为什么每个变更都要人工审核

Cline 的设计原则是人在回路（human-in-the-loop）：每个文件变更和终端命令都需要你审核。自动执行在工程上有三类风险：

1. **文件变更的不可逆性**：Cline 改文件时走 diff 视图，但如果自动放行，一次错误的批量重命名、一次误删 import、一次把 `production` 写进测试配置，都可能让代码库进入难以回滚的状态。即便有 Git，"AI 改了 30 个文件、其中 5 个是错的"也比"人改了 3 个文件、全是错的"更难排查。
2. **终端命令的副作用**：`rm -rf`、`DROP DATABASE`、`kubectl delete`、`terraform destroy` 这类命令一旦执行就不可逆。Cline 不知道你的 `~/.aws/credentials` 是不是生产环境凭据，也不知道当前目录是不是真的项目根目录。人工审核是最后一道防线。
3. **MCP 工具的外部影响**：MCP 工具能调 Jira、AWS、PagerDuty，意味着 Cline 能改外部系统状态——关 EC2 实例、改 Jira 工单状态、触发 PagerDuty 事件。这些操作的副作用不在本地代码库里，Git 救不了你。

Cline 的检查点机制（每个步骤拍工作区快照）能还原文件变更，但还原不了已经执行的终端命令和已经调用的 MCP 工具。所以"每个变更都要人工审核"不是过度保守，而是把不可逆操作的放行权留在人手里。

## 六、任务流案例：修复一个 lint 错误

下面追踪一次"修复一个 lint 错误"的完整路径，把四条机制如何配合串起来。

**场景**：你有一个 TypeScript 项目，`src/utils/format.ts` 里有一个 lint 错误 `no-unused-vars`，变量 `tempBuffer` 声明了但没使用。你打开 Cline，输入：

```
@problems 修复所有 lint 错误
```

`@problems` 是 Cline 的上下文添加方式之一，会把工作区当前的错误和警告作为上下文喂给模型。下面是完整执行路径：

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. 上下文收集                                                   │
│    @problems 把 ESLint 报告喂给 Cline                        │
│    Cline 看到：src/utils/format.ts:42 tempBuffer 未使用         │
│                         │                                       │
│ 2. 分析阶段（文件编辑机制）                                     │
│    Cline 读取 src/utils/format.ts 的 AST                       │
│    定位到第 42 行的 tempBuffer 声明                             │
│    分析：tempBuffer 在第 45 行被赋值但从未被读取                │
│                         │                                       │
│ 3. 规划阶段                                                     │
│    Cline 给出方案：删除第 42 行的声明和第 45 行的赋值           │
│    在聊天面板展示计划，等待你确认                               │
│                         │                                       │
│ 4. 执行阶段（文件编辑机制）                                     │
│    你点"同意"                                                  │
│    Cline 在 diff 视图展示变更：                                 │
│      - 第 42 行：const tempBuffer = ...  [删除]                │
│      - 第 45 行：tempBuffer = compute(...)  [删除]             │
│    你在 diff 视图点"保存"                                      │
│                         │                                       │
│ 5. 验证阶段（终端执行机制）                                     │
│    Cline 主动建议：运行 npm run lint 验证                      │
│    你点"批准"                                                  │
│    Cline 在终端执行：npm run lint                              │
│    输出：0 errors, 0 warnings                                  │
│                         │                                       │
│ 6. 完成阶段                                                     │
│    Cline 在聊天面板报告：lint 错误已修复                       │
│    提供 open 命令打开 src/utils/format.ts                      │
│    检查点时间线记录本次任务的所有快照                           │
└─────────────────────────────────────────────────────────────────┘
```

几个细节：

- **机制切换显式**：第 2 步用文件编辑机制，第 5 步切到终端执行机制。Cline 不会偷偷跑命令，每次切机制都会在聊天面板说明。
- **审核分两层**：第 3 步规划阶段确认方案，第 4 步执行阶段在 diff 视图点保存。
- **检查点是任务级**：第 6 步记录的是整个工作区快照，而非单文件快照。
- **浏览器和 MCP 机制未触发**：这个任务不需要端到端验证，也不需要调外部系统。四条机制按需触发，不是每次任务都全开。

## 七、创建一个完整的 MCP 工具

场景：让 Cline 能查询 GitHub 仓库的 Stars 数。

### 7.1 创建 MCP server

在项目根目录创建 `mcp-servers/github-stars/index.ts`：

```typescript
// mcp-servers/github-stars/index.ts
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
  name: "github-stars",
  version: "1.0.0",
});

server.tool(
  "get_repo_stars",
  "获取 GitHub 仓库的 Stars 数量",
  {
    owner: z.string().describe("仓库所有者，例如 cline"),
    repo: z.string().describe("仓库名，例如 cline"),
  },
  async ({ owner, repo }) => {
    const url = `https://api.github.com/repos/${owner}/${repo}`;
    const response = await fetch(url, {
      headers: {
        Accept: "application/vnd.github+json",
        "User-Agent": "cline-mcp-server",
      },
    });

    if (!response.ok) {
      return {
        content: [{ type: "text", text: `GitHub API 返回 ${response.status}: ${response.statusText}` }],
        isError: true,
      };
    }

    const data = (await response.json()) as { stargazers_count: number };
    return {
      content: [{ type: "text", text: `${owner}/${repo} 当前 Stars: ${data.stargazers_count}` }],
    };
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
```

### 7.2 配置 package.json

```json
{
  "name": "github-stars-mcp",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0",
    "zod": "^3.23.0"
  },
  "devDependencies": {
    "@types/node": "^22.0.0",
    "typescript": "^5.5.0"
  }
}
```

同目录创建 `tsconfig.json`：

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "moduleResolution": "node",
    "outDir": "./dist",
    "rootDir": "./",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["index.ts"]
}
```

### 7.3 构建并注册

```bash
cd mcp-servers/github-stars
npm install && npm run build
```

然后在 VS Code 里打开 Cline，输入：

```
添加一个 MCP 工具，路径是 mcp-servers/github-stars/dist/index.js，用 node 启动
```

Cline 会自动在 `cline_mcp_settings.json` 里写入配置。也可以手动编辑（配置文件路径：`~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`）：

```json
{
  "mcpServers": {
    "github-stars": {
      "command": "node",
      "args": ["/absolute/path/to/mcp-servers/github-stars/dist/index.js"],
      "env": {},
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### 7.4 调用

注册完成后，在 Cline 聊天面板输入：

```
查一下 cline/cline 仓库的 Stars 数
```

Cline 会识别出这是 MCP 工具 `get_repo_stars` 的调用场景，展示调用参数（`owner=cline, repo=cline`），确认后执行。结果回到聊天面板：

```
cline/cline 仓库当前 Stars: 87.2k
```

### 7.5 排查 MCP 工具加载失败

如果工具没出现在 Cline 的可用工具列表里：

1. **检查路径**：`cline_mcp_settings.json` 里的 `args` 必须是绝对路径，相对路径不会生效。
2. **手动跑 server**：在终端执行 `node /absolute/path/to/dist/index.js`，看是否有报错。MCP server 通过 stdio 通信，正常启动后会等待输入不退出，如果立即退出说明启动失败。
3. **检查依赖**：`dist/index.js` 依赖 `node_modules`，如果在非原目录运行可能找不到依赖。
4. **看 Cline 日志**：VS Code 的 Output 面板选 "Cline" 频道，能看到 MCP server 的启动日志和报错堆栈。

## 八、API 提供商与模型选择

Cline 不绑死模型，支持几乎所有主流 AI API 提供商：

| 提供商 | 说明 |
|--------|------|
| **OpenRouter** | 数百种模型，实时获取最新模型列表 |
| **Anthropic** | Claude 系列（Computer Use 必须走这一家或 OpenRouter） |
| **OpenAI** | GPT 系列 |
| **Google Gemini** | Gemini 系列 |
| **AWS Bedrock** | 亚马逊云 AI 服务 |
| **Azure** | 微软 Azure AI |
| **GCP Vertex** | 谷歌云 AI 服务 |
| **Cerebras / Groq** | 超快速推理 / 低延迟推理 |
| **LM Studio / Ollama** | 本地模型 |

**模型选择策略**：

- **需要浏览器测试**：必须用 Claude Sonnet（Computer Use 绑定 Anthropic）。
- **纯文件编辑 + 终端执行**：可以换 GPT、Gemini、本地模型。本地模型成本最低，但能力上限受模型规模限制。
- **复杂多步任务**：Claude Sonnet 综合最稳，尤其是涉及 AST 分析、跨文件改动的场景。

## 九、上下文添加方式与检查点机制

### 9.1 上下文添加方式

| 方式 | 说明 |
|------|------|
| `@url` | 粘贴 URL，将网页内容转换为 Markdown |
| `@problems` | 添加工作区错误和警告 |
| `@file` | 添加文件内容，避免浪费 API 请求 |
| `@folder` | 一次性添加整个文件夹内容 |

`@file` 和 `@folder` 的价值在于显式声明上下文——如果不加，Cline 会自己读文件，但读哪些、读多少由模型决定，可能漏掉关键文件或读太多无关文件浪费 token。

### 9.2 检查点

Cline 在处理任务时会为每个步骤拍摄工作区快照。你可以用"Compare"按钮比较快照与当前工作区的差异，用"Restore"按钮还原到任意时间点。检查点是任务级的——一次任务里的所有快照属于同一条时间线，跨任务的快照不共享。

## 十、与 Claude Code、Copilot 的边界对照

| 维度 | Cline | Claude Code | GitHub Copilot |
|------|-------|-------------|----------------|
| **入口形态** | VS Code 扩展 | CLI 工具 | VS Code / JetBrains 扩展 |
| **人介入层级** | 每个文件变更、每条命令 | 每个文件变更、每条命令 | 行内补全建议 |
| **任务粒度** | 多文件、多步骤 | 多文件、多步骤 | 单行/多行补全 |
| **终端执行** | ✅ 借助 VS Code shell 集成 | ✅ 直接在终端跑 | ❌ |
| **浏览器测试** | ✅ Claude Sonnet Computer Use | ✅ | ❌ |
| **MCP 支持** | ✅ 原生支持 | ✅ 支持 | ❌ |
| **本地模型** | ✅ LM Studio/Ollama | ✅ | ❌ |
| **企业版** | ✅ SSO/审计/私有部署 | ❌ | ✅ |
| **适用场景** | VS Code 内多步任务 | 终端优先、脚本化、远程服务器 | 行内补全、轻量建议 |

**本质差异**：

- **Cline vs Copilot**：Copilot 处理的是"下一行写什么"，Cline 处理的是"这个任务怎么做完"。前者是补全，后者是 Agent。两者不冲突——很多人同时用 Copilot 做行内补全、用 Cline 做多步任务。
- **Cline vs Claude Code**：两者都是 Agent，差异在入口形态。Cline 嵌在 VS Code 里，diff 视图、终端、文件管理器都在同一个窗口；Claude Code 是 CLI，不受编辑器限制，Vim/Emacs/ssh 远程服务器都能用，但没有 IDE 内联的 diff 视图。选哪个看你是不是绑 VS Code。

## 十一、安装与基本使用

### 11.1 安装

1. 在 VS Code 中安装 [Cline 扩展](https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev)
2. 获取 API Key（如果使用 OpenRouter，访问 [openrouter.ai/keys](https://openrouter.ai/keys) ）
3. 在 VS Code 设置中配置 API Key

### 11.2 基本使用

1. **打开 Cline**：按 `Cmd/Ctrl + Shift + C` 或点击侧边栏图标
2. **输入任务**：描述你想完成的任务
3. **添加图片**（可选）：如果根据 UI 设计图生成代码
4. **审核变更**：Cline 展示 diff 视图，审核每一个变更
5. **执行命令**：对于终端命令，点击按钮批准执行
6. **完成任务**：Cline 展示最终结果

### 11.3 技巧：在侧边栏打开 Cline

按照[这个指南](https://docs.cline.bot/features/customization/opening-cline-in-sidebar)将 Cline 打开在编辑器右侧，可以同时看到文件管理器和 Cline 的变更。

## 十二、FAQ 与常见排查

### Cline 与 GitHub Copilot 有什么区别？

Copilot 处理"下一行写什么"（补全），Cline 处理"这个任务怎么做完"（Agent）。两者可以同时用。

### Cline 安全吗？

Cline 的设计原则是人在回路，每个文件变更和终端命令都需要你审核。如果对所有变更都无脑点确认，等同于自动执行，第五节列出的三类风险都会出现。

### 需要多少 API 配额？

一次"修复 lint 错误"任务通常消耗 5k-20k tokens；一次端到端浏览器测试可能消耗 50k-200k tokens（Computer Use 调用很贵）。使用本地模型（LM Studio/Ollama）可以大幅降低成本，但会失去 Computer Use 能力。

### 支持哪些编程语言？

Cline 不限定编程语言，通过分析源码 AST 理解代码结构。具体功能支持取决于使用的 AI 模型——Claude Sonnet 对主流语言（Python、TypeScript、Go、Rust、Java）支持最好。

### API 配额超限怎么办？

1. 切换 provider（Anthropic 直连超限 → 切 OpenRouter）
2. 降级模型（Opus → Sonnet → Haiku）
3. 换本地模型（Ollama，无 API 限流）
4. 降低任务粒度，减少单次 token 消耗

### diff 视图冲突怎么办？

如果 Cline 改文件的同时手动改了同一个文件，先在 diff 视图点"还原"放弃 Cline 的变更，保存手动改动，再让 Cline 重新执行变更，最后合回手动改动。

### 长任务中断如何恢复？

重启 VS Code，在检查点时间线找到中断前的最后一个快照，用 Restore 还原，重新输入任务。Cline 不会自动恢复中断的任务——Agent 循环是同步的，中断即结束。

### Cline 一直跑同一个命令怎么办？

如果 Cline 在某个命令上反复跑，多半是模型陷入了循环。手动停止，在聊天里指出问题，提供更多上下文。

### 企业版有什么额外能力？

SSO（SAML/OIDC）、全局策略和配置、可观测性和审计追踪、私有网络、私有部署、企业支持。详情见 [enterprise page](https://cline.bot/enterprise)。

## 十三、采用顺序与决策建议

### 第一周：先试

1. 装 Cline 扩展，配 OpenRouter API Key
2. 跑一次"修复 lint 错误"任务，体验 diff 视图审核和终端执行审核
3. 跑一次"重构这个函数"任务，体验多文件改动
4. 观察 token 消耗，建立成本直觉

### 第二周：再试

1. 试浏览器测试，观察 Computer Use 的工作方式和 token 消耗
2. 创建一个 MCP 工具，理解 MCP 协议的价值
3. 试检查点机制，体验时间线还原
4. 试 `@url` 和 `@folder`，看大上下文处理

### 长期使用姿态

1. 建立审核习惯——如果无脑点确认，说明该回到 Copilot
2. 建立 MCP 工具库，把团队常用外部系统做成 MCP 工具
3. 建立成本预算，超了就降级或换本地模型

### 什么时候换 Claude Code

- 不在 VS Code 里工作（Vim/Emacs/JetBrains，或 ssh 远程服务器）
- 需要脚本化 Agent 调用（CI/CD、cron 任务、批量处理）
- 不需要 diff 视图审核，信任 Agent 变更
- 任务主要是终端操作（跑命令、看日志、改配置）

### 什么时候不必上 Cline

- 纯代码补全场景，用 Copilot 更轻
- 单点问答（"这段代码什么意思"），直接问 Claude Desktop 或 ChatGPT
- 不想审核任何变更——Cline 的价值在人介入审核

## 延伸阅读

- [Cline 官方文档](https://docs.cline.bot/)
- [Cline Discord](https://discord.gg/cline)
- [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol)
- [Anthropic Computer Use 文档](https://docs.anthropic.com/en/docs/build-with-claude/computer-use)