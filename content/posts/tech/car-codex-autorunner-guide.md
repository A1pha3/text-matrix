---
title: "CAR Codex Auto-Runner：AI 编程智能体协作框架完全指南"
date: 2026-03-31T12:40:00+08:00
slug: "car-codex-autorunner-guide"
description: "全面解析 CAR（Codex Auto-Runner）：AI 编程智能体元协调框架。658 Stars，MIT 许可证。支持 Codex/Opencode/Hermes 三大智能体，Tickets 即控制平面设计，无人值守长时间任务执行。从入门到精通，包含架构分析、原理讲解、使用说明和最佳实践。"
draft: false
categories: ["技术笔记"]
tags: ["CAR", "Codex", "Opencode", "AI智能体", "自动化", "Tickets", "PMA"]
---

# CAR Codex Auto-Runner：AI 编程智能体协作框架完全指南

## §1 学习目标

学完本文档后，你将能够：

- 理解 CAR（Codex Auto-Runner）的核心概念与设计哲学
- 掌握 CAR 的三种交互方式：Web UI、CLI、聊天应用（Telegram/Discord）
- 了解 Tickets 作为控制平面的工作原理
- 学会在项目中安装、配置和运行 CAR
- 掌握创建和管理 CAR Tickets 的方法
- 理解 Project Manager Agent（PMA）的使用场景
- 能够在团队中推广和应用 CAR 协作工作流

---

## §2 项目概述

### 2.1 什么是 CAR

CAR（Codex Auto-Runner，官方仓库：[Git-on-my-level/codex-autorunner](https://github.com/Git-on-my-level/codex-autorunner)）是一个**AI 编程智能体元协调框架**（meta-harness for coding agents）。它不是另一个编码智能体，而是为已有的 AI 编程工具（如 Codex、Opencode）提供协调能力，让它们能够**长时间运行复杂任务**，而无需人工持续监督。

CAR 的核心理念：**让智能体做它们最擅长的事，不要挡路**（CAR is very bitter-lesson-pilled）。随着模型能力增强，CAR 应该充当放大器，而非约束器。

### 2.2 核心数据

```
Stars:     658
Forks:    52
版本:     v1.11.2（2026-04-15）
提交:     1,289 commits
分支:     30 branches
标签:     37 tags
贡献者:   7 人
许可证:   MIT
语言:     Python 84.7%, TypeScript 5.9%, JavaScript 6.3%
```

### 2.3 支持的智能体

CAR 目前支持以下 AI 编程智能体：

| 智能体 | 协议 | 状态 |
|--------|------|------|
| **Codex** | 原生支持 | ✅ 一线支持 |
| **Opencode** | 原生支持 | ✅ 一线支持 |
| **Hermes** | ACP（Agent Client Protocol） | ✅ 支持（持久线程） |

CAR 被设计为可以轻松集成任何基于 ACP 的智能体。如果你想添加新的智能体支持，欢迎提交 Issue 或 Pull Request。

### 2.4 为什么需要 CAR

传统的 AI 编程工具使用方式存在几个痛点：

**人工监督负担重**：传统方式需要人工持续监督 AI 的工作进度，AI 遇到问题就停止等待。

**上下文窗口限制**：长时间任务会超出上下文窗口，导致 AI 丢失重要上下文。

**多智能体协作困难**：多个 AI 智能体之间无法有效协调，各自为战。

**状态丢失**：AI 重启后丢失之前的进度和决策。

CAR 通过**Tickets 控制平面**和**状态机架构**解决了这些问题：

- **Tickets 即控制平面**：任务被封装为 Markdown 文件，AI 和人类都可以编辑
- **状态持久化**：SQLite 数据库记录任务状态，重启后可恢复
- **无需人工盯守**：AI 完成后主动通知（支持 Telegram/Discord）
- **上下文隔离**：每个 Ticket 有独立的 contextspace，避免上下文膨胀

---

## §3 原理分析

### 3.1 系统架构：Tickets 即控制平面

CAR 的核心设计理念是：**Tickets 是控制平面，模型是执行层**。

```
┌─────────────────────────────────────────────────────────────┐
│                        CAR 控制平面                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  Web UI    │    │    CLI      │    │  聊天应用   │     │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘     │
│         │                   │                   │            │
│  ┌──────┴──────────────────┴──────────────────┴──────┐    │
│  │              CAR Core (Python CLI + SQLite)           │    │
│  │                                                       │    │
│  │  状态机: 检查未完成的 Tickets → 选择下一个 → 执行      │    │
│  └─────────────────────────┬───────────────────────────┘    │
│                            │                                │
│  ┌─────────────────────────┴───────────────────────────┐  │
│  │              Tickets (Markdown + Frontmatter)         │  │
│  │  - 每个 Ticket 包含任务描述、状态、上下文              │  │
│  │  - 人类和 AI 都可以创建和编辑                         │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                        执行层                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Codex    │    │  Opencode  │    │   Hermes   │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 工作流程

CAR 的工作流程非常简单：

1. **创建 Tickets**：用户编写计划，或让 AI 根据对话生成 Tickets（Markdown 格式，包含 frontmatter 元数据）

2. **智能体执行**：CAR 状态机检查未完成的 Tickets，选择下一个并交给智能体执行

3. **通知机制**：智能体完成或需要人工输入时，通过 Telegram/Discord 通知用户

4. **循环迭代**：智能体可以创建新的 Tickets，形成自我改进的循环

```
用户创建 Tickets
       │
       ▼
┌─────────────────┐
│  CAR 状态机      │◄──── 用户/智能体创建新 Ticket
│  检查未完成任务   │
└────────┬─────────┘
         │
         ▼
┌─────────────────┐
│  选择下一个 Ticket│
│  交付给智能体    │
└────────┬─────────┘
         │
         ▼
┌─────────────────┐
│  智能体执行任务  │
│  (Codex/Opencode│
└────────┬─────────┘
         │
         ▼
┌─────────────────┐
│  完成/需要帮助   │
│  → 通知用户     │
└─────────────────┘
```

### 3.3 Contextspace 机制

每个 Ticket 执行时，智能体获得以下上下文：

- **CAR 工作原理**：如何操作 CAR
- **contextspace**：一组预定义的上下文（内部称为 contextspace）
- **当前 Ticket**：当前任务的详细描述
- **上一智能体输出**（可选）：前一个智能体的最终输出，用于多智能体协作

这种设计确保智能体有足够的信息来使用 CAR，同时保持对当前任务的专注。

### 3.4 Tickets as Code（代码化 Tickets）

CAR 将 Tickets 视为一个**新的软件层**。这意味着：

- Ticket 可以**生成子 Tickets**（如特性范围划分 Ticket 生成实现子任务 Tickets）
- Ticket 可以**生成子智能体**（如果智能体支持）
- Ticket 可以**跨仓库复用**（repo-agnostic）或**仓库特定**（repo-specific）

开发者维护了一套"**祝福模板集**"（blessed set of ticket templates），可从任何 CAR 部署访问：[car-ticket-templates](https://github.com/Git-on-my-level/car-ticket-templates)。

---

## §4 架构分析

### 4.1 仓库结构

```
codex-autorunner/
├── .agents/skills/           # 智能体技能配置
├── .codex/                   # Codex 环境配置
├── .codex-autorunner/        # CAR 核心配置
├── .githooks/               # Git hooks
├── .github/                  # GitHub Actions
├── .vscode/                  # VSCode 配置
├── docs/                     # 文档目录
├── schemas/                   # 数据模式
├── scripts/                  # 脚本
├── src/codex_autorunner/     # CAR 核心 Python 代码
├── tests/                    # 测试
├── vendor/protocols/          # 第三方协议
├── AGENTS.md                 # AI 智能体配置
├── Makefile                  # 构建脚本
├── README.md                  # 项目说明
├── codex-autorunner.yml        # CAR 配置文件
├── eslint.config.cjs          # ESLint 配置
├── package.json               # NPM 包配置
├── pyproject.toml            # Python 项目配置
└── tsconfig.json             # TypeScript 配置
```

### 4.2 核心组件

**CAR Core（Python）**
- 位置：`src/codex_autorunner/`
- 功能：状态机、Ticket 管理、SQLite 持久化、CLI 接口
- 依赖：Python 3.x，SQLite3（内置）

**Web UI（TypeScript/JavaScript）**
- 功能：可视化 Ticket 管理、智能体 TUI、Usage Analytics
- 特性：Whisper 集成、文档聊天编辑（适合移动端）

**CLI（Python）**
- 入口：`./car`（仓库本地 shim）或 `codex-autorunner`（安装后）
- 功能：最智能体友好的交互方式

**聊天集成（Telegram/Discord）**
- 功能：持久化聊天体验、多设备同步
- 特性：Project Manager Agent（PMA）支持

### 4.3 数据流

```
用户输入（Web UI / CLI / 聊天）
           │
           ▼
┌─────────────────────┐
│   CAR Core          │
│   - 验证输入        │
│   - 更新 SQLite     │
│   - 触发状态机      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Ticket Store      │
│   (SQLite)         │
│   - tickets 表      │
│   - runs 表         │
│   - state 表        │
└──────────┬──────────┘
           │
           ▼
    ┌──────┴──────┐
    │  智能体执行   │
    │  Codex/Opencode │
    └──────────────┘
```

### 4.4 Ticket 格式

CAR Tickets 使用 Markdown 格式，包含 YAML Frontmatter：

```markdown
---
id: ticket-001
title: 实现用户认证模块
status: pending
agent: codex
priority: high
created_at: 2026-03-31T12:00:00Z
depends_on: []
contextspace:
  - auth-requirements
  - api-spec
---

# 用户认证模块

## 目标
实现基于 JWT 的用户认证系统。

## 验收标准
- [ ] 用户注册接口
- [ ] 用户登录接口
- [ ] JWT Token 生成和验证
- [ ] 单元测试覆盖率 > 80%

## 备注
参考 `/docs/auth-spec.md` 中的详细规格。
```

---

## §5 功能详解

### 5.1 三种交互方式

**Web UI（主控制平面）**

Web UI 是 CAR 的主控制平面，提供最完整的功能：

- **仓库管理**：新建仓库或克隆已有仓库
- **智能体聊天**：使用智能体的 TUI 界面
- **Ticket 运行器**：一键运行 Tickets
- **Whisper 集成**：语音输入
- **文档聊天编辑**：通过 AI 对话编辑文档（适合移动端）
- **Usage Analytics**：使用统计分析

> ⚠️ **安全提示**：Web UI 涉及暴露服务在公网，请阅读 [web UI security posture](docs/web/security.md) 了解安全配置。

**CLI（最智能体友好）**

CLI 是最智能体友好的交互方式，适合：

- 构建自定义 UI 的底层接口
- 直接让智能体调用 CAR

```bash
# 查看帮助
./car --help

# 创建新 Ticket
./car ticket create "实现用户认证模块"

# 列出所有 Tickets
./car ticket list

# 运行 Tickets
./car run

# 查看状态
./car status
```

**聊天应用（Telegram & Discord）**

如果需要多设备持久化聊天体验，且不想暴露 CAR 服务在公网，聊天应用是最佳选择：

- 支持 Telegram 和 Discord
- 可以与管理智能体（PMA）对话
- PMA 可以代表用户执行 CAR 操作

### 5.2 Project Manager Agent（PMA）

PMA 是 CAR 的对话式管理界面，可以：

- **创建/编辑 Tickets**：通过对话创建和修改任务
- **管理仓库和工作树**：设置新仓库，管理分支
- **协调 Ticket 流程**：管理任务流程和依赖
- **响应智能体调度**：处理来自 Ticket 流程智能体的请求
- **从零到一的项目启动**：快速启动新项目并迭代

```bash
# 在 Web UI 或聊天应用中调用 PMA
> 请帮我创建一个新的用户认证模块的 Ticket
> 设置明天完成
```

**Hermes 是优秀的 PMA 选择**，因为它通过共享的 `HERMES_HOME` 维护跨会话的全局记忆，可以跨 CAR 项目记住模式、偏好和学习内容。

### 5.3 支持的智能体集成

**Codex 集成**

```bash
# 配置 Codex
export OPENAI_API_KEY=your_key
./car agent add codex

# 使用 Codex 运行
./car run --agent codex
```

**Opencode 集成**

```bash
# 配置 Opencode
./car agent add opencode

# 使用 Opencode 运行
./car run --agent opencode
```

**Hermes（ACP 运行时）**

Hermes 是支持 ACP 的运行时，具有持久线程：

```bash
# 配置 Hermes
./car agent add hermes
export HERMES_HOME=~/.hermes

# Hermes 支持跨会话记忆
./car run --agent hermes
```

### 5.4 Ticket 模板系统

CAR 维护了一套祝福模板集：[car-ticket-templates](https://github.com/Git-on-my-level/car-ticket-templates)

常用模板类型：

| 模板类型 | 用途 |
|---------|------|
| `feature-scope` | 特性范围划分和子任务生成 |
| `code-review` | 代码审查任务 |
| `tech-debt` | 技术债务清理 |
| `test-coverage` | 测试覆盖率提升 |
| `bug-fix` | Bug 修复任务 |

用户也可以创建自定义模板：

```bash
# 初始化自定义模板
./car template init my-template

# 使用模板创建 Ticket
./car ticket create --template my-template "新的特性"
```

---

## §6 使用说明

### 6.1 环境要求

- **Python 3.8+**
- **Git**
- **支持的智能体**（至少一种）：
  - Codex（需要 OpenAI API Key）
  - Opencode
  - Hermes（ACP 运行时）

### 6.2 安装方式

**方式一：PyPI 安装（推荐）**

```bash
pip install codex-autorunner

# 验证安装
codex-autorunner --version
```

**方式二：从源码安装**

```bash
# 克隆仓库
git clone https://github.com/Git-on-my-level/codex-autorunner.git
cd codex-autorunner

# 使用本地 shim（自动引导）
./car --help

# 或添加到 PATH
export PATH="$PATH:$(pwd)"
```

**方式三：Docker 运行**

```bash
# 使用 Docker 运行 CAR
docker run -it \
  -v ~/.car:/app/.car \
  -v ~/projects:/projects \
  codex-autorunner:latest
```

### 6.3 快速开始

**步骤 1：传递设置指南给 AI**

将 [AGENT_SETUP_GUIDE.md](docs/AGENT_SETUP_GUIDE.md) 的内容发送给喜欢的 AI 智能体，它会交互式地引导完成安装和配置。

**步骤 2：初始化项目**

```bash
# 在项目目录中
cd ~/my-project

# 初始化 CAR
codex-autorunner init

# 或让 AI 帮你初始化
> 请帮我初始化 CAR
```

**步骤 3：创建第一个 Ticket**

```bash
# 创建 Ticket
codex-autorunner ticket create "实现用户登录功能" --agent codex

# 查看 Tickets
codex-autorunner ticket list
```

**步骤 4：运行 Tickets**

```bash
# 运行所有未完成的 Tickets
codex-autorunner run

# 或指定 Ticket
codex-autorunner run --ticket ticket-001
```

**步骤 5：等待通知**

设置好 Telegram 或 Discord 集成后，智能体完成或需要帮助时会主动通知你。

### 6.4 Telegram 集成

```bash
# 获取 Telegram Bot Token（从 @BotFather）
export TELEGRAM_BOT_TOKEN=your_token

# 配置 Telegram
codex-autorunner config set telegram.enabled true

# 启动监听
codex-autorunner telegram
```

详细配置请阅读：[AGENT_SETUP_TELEGRAM_GUIDE.md](docs/AGENT_SETUP_TELEGRAM_GUIDE.md)

### 6.5 Discord 集成

```bash
# 获取 Discord Bot Token
export DISCORD_BOT_TOKEN=your_token

# 配置 Discord
codex-autorunner config set discord.enabled true

# 启动监听
codex-autorunner discord
```

详细配置请阅读：[AGENT_SETUP_DISCORD_GUIDE.md](docs/AGENT_SETUP_DISCORD_GUIDE.md)

### 6.6 Docker 运行时执行

如果需要 Docker 环境执行（包括每个仓库/工作树自定义镜像）：

```bash
# 配置 Docker 运行时
codex-autorunner config set runtime.docker.enabled true

# 指定仓库的 Docker 镜像
codex-autorunner repo set-image my-project --image python:3.11-slim

# 运行
codex-autorunner run --runtime docker
```

详细配置请阅读：[destinations.md](docs/configuration/destinations.md)

---

## §7 开发扩展

### 7.1 创建自定义 Ticket 模板

创建 `~/.car/templates/my-template.md`：

```markdown
---
id: "{{id}}"
title: "{{title}}"
status: pending
priority: medium
contextspace:
  - project-overview
---

# {{title}}

## 目标
<!-- 描述任务目标 -->

## 验收标准
- [ ] 标准 1
- [ ] 标准 2

## 依赖
<!-- 列出依赖的其他 Tickets -->

## 备注
<!-- 额外信息 -->
```

### 7.2 扩展新智能体支持

CAR 被设计为易于扩展。如果要添加新的智能体支持：

1. **创建智能体适配器**：

```python
# src/codex_autorunner/agents/my_agent.py

from codex_autorunner.agents.base import BaseAgent

class MyAgent(BaseAgent):
    name = "my-agent"
    protocol = "acp"  # 或 "native"

    async def execute(self, ticket: Ticket, contextspace: dict) -> ExecutionResult:
        """执行 Ticket"""
        # 实现执行逻辑
        pass

    async def notify(self, message: str) -> None:
        """发送通知"""
        pass
```

2. **注册智能体**：

```python
# src/codex_autorunner/agents/__init__.py

from codex_autorunner.agents.my_agent import MyAgent

AGENTS = {
    "my-agent": MyAgent,
    # ... 其他智能体
}
```

3. **提交 PR**：欢迎提交 Pull Request 来贡献新的智能体支持！

### 7.3 自定义 Contextspace

创建项目特定的 contextspace：

```bash
# 在项目中创建 .car/contextspaces/ 目录
mkdir -p .car/contextspaces

# 添加 contextspace 文件
echo "项目使用 React 18 + TypeScript + Vite" > .car/contextspaces/tech-stack.md
echo "代码规范见 .eslintrc.js" >> .car/contextspaces/tech-stack.md
```

### 7.4 与 CI/CD 集成

```yaml
# .github/workflows/car.yml

name: CAR Ticket Runner

on:
  schedule:
    - cron: '0 */4 * * *'  # 每 4 小时运行一次

jobs:
  run-tickets:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install CAR
        run: pip install codex-autorunner
      - name: Run Tickets
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: codex-autorunner run --agent codex --non-interactive
```

---

## §8 最佳实践

### 8.1 Ticket 编写规范

**好的 Ticket 示例**：

```markdown
---
id: feat-auth-001
title: 实现 JWT 用户认证
status: pending
priority: high
agent: codex
contextspace:
  - auth-requirements
  - api-spec
---

# 实现 JWT 用户认证

## 背景
用户需要安全地登录系统，我们选择 JWT 作为认证方案。

## 目标
- 实现注册接口 `/api/auth/register`
- 实现登录接口 `/api/auth/login`
- JWT Token 有效期 7 天

## 验收标准
- [ ] POST /api/auth/register 正确创建用户
- [ ] POST /api/auth/login 返回有效 JWT
- [ ] 已有 Token 可以访问受保护接口
- [ ] 过期 Token 被正确拒绝

## 技术约束
- 使用 `PyJWT` 库
- 密码使用 bcrypt 哈希存储
- 参考 `/docs/auth-spec.md`

## 依赖
- 无（前序任务）

## 备注
如果遇到数据库迁移问题，请参考 `docs/db-migration.md`。
```

### 8.2 多智能体协作模式

**模式一：流水线模式**

```markdown
<!-- Ticket 1: 架构设计 -->
status: completed

<!-- Ticket 2: 后端实现（依赖 Ticket 1）-->
depends_on: [ticket-001]
status: pending

<!-- Ticket 3: 前端实现（依赖 Ticket 2）-->
depends_on: [ticket-002]
status: pending
```

**模式二：并行模式**

多个独立的 Ticket 可以并行执行：

```markdown
<!-- Ticket A: 用户模块 -->
status: pending

<!-- Ticket B: 商品模块 -->
status: pending

<!-- Ticket C: 订单模块 -->
status: pending
```

### 8.3 状态管理最佳实践

**定期检查状态**：

```bash
# 查看状态摘要
codex-autorunner status

# 查看具体 Ticket 状态
codex-autorunner ticket show ticket-001

# 导出状态报告
codex-autorunner report --format json > status-report.json
```

**备份数据库**：

```bash
# 备份
cp ~/.car/car.db ~/.car/car.db.backup-$(date +%Y%m%d)

# 恢复
cp ~/.car/car.db.backup-20260331 ~/.car/car.db
```

### 8.4 故障排查

**Tickets 不执行**：

1. 检查 Ticket 状态是否为 `pending`
2. 检查 `codex-autorunner run` 是否正常启动
3. 查看日志：`codex-autorunner logs`

**智能体不响应**：

1. 确认 API Key 配置正确
2. 检查智能体是否支持当前任务
3. 尝试切换智能体：`./car run --agent opencode`

**通知不送达**：

1. 确认 Telegram/Discord Bot Token 正确
2. 检查 Bot 是否已添加到对应聊天
3. 查看通知日志：`codex-autorunner notifications history`

---

## §9 常见问题

### Q1：CAR 和直接使用 Codex/Opencode 有什么区别？

| 对比项 | 直接使用智能体 | 使用 CAR |
|--------|--------------|---------|
| 任务持久化 | 无，关闭后丢失 | SQLite 持久化 |
| 多任务管理 | 手动切换 | 自动轮询执行 |
| 人工监督 | 必须持续盯守 | 完成后通知 |
| 长时间任务 | 上下文溢出风险 | Ticket 隔离上下文 |
| 多智能体协作 | 困难 | Ticket 作为协调机制 |

### Q2：需要多强大的模型才能用 CAR？

CAR 是一个**放大器**，不是替代品。如果使用的模型太弱，CAR 可能效果不佳。项目方推荐使用：

- **Codex**：GPT-4 级别
- **Opencode**：支持 GPT-4 和 Claude
- **Hermes**：支持多种 ACP 兼容模型

### Q3：可以离线使用 CAR 吗？

可以。CAR 的核心功能是本地运行的：

- Ticket 文件存储在本地
- SQLite 数据库在本地
- CLI 完全离线可用

但以下功能需要网络：

- 智能体调用（需要 API 访问）
- Telegram/Discord 通知（需要网络）
- 从 GitHub 拉取模板（需要网络）

### Q4：如何贡献 Ticket 模板？

1. Fork [car-ticket-templates](https://github.com/Git-on-my-level/car-ticket-templates)
2. 在 `templates/` 目录创建新模板
3. 确保模板有清晰的文档和使用说明
4. 提交 Pull Request

### Q5：支持哪些操作系统？

CAR 经过测试可在以下系统运行：

- ✅ Linux（Ubuntu、Debian、Fedora、Arch）
- ✅ macOS
- ✅ Windows（通过 WSL2）
- ✅ Docker（跨平台）

### Q6：如何报告问题或请求功能？

- **Bug 报告**：[GitHub Issues](https://github.com/Git-on-my-level/codex-autorunner/issues/new?labels=bug)
- **功能请求**：[GitHub Issues](https://github.com/Git-on-my-level/codex-autorunner/issues/new?labels=enhancement)
- **讨论**：[GitHub Discussions](https://github.com/Git-on-my-level/codex-autorunner/discussions)

---

## §10 总结

CAR（Codex Auto-Runner）是一个创新的 AI 编程智能体协作框架，通过 **Tickets 即控制平面** 的设计，让 AI 智能体能够长时间、无人值守地运行复杂任务。

**核心价值**：

- **无需盯守**：智能体完成后主动通知
- **状态持久化**：任务状态不丢失
- **上下文隔离**：每个任务有独立上下文
- **多智能体支持**：Codex、Opencode、Hermes 无缝协作
- **多种交互方式**：Web UI、CLI、Telegram/Discord

**适用场景**：

- 长时间运行的大型特性开发
- 需要多轮迭代的复杂重构
- 技术债务清理和代码审查
- 跨仓库的系统性改进
- 需要多智能体协作的综合性项目

**链接资源**：

- GitHub 仓库：https://github.com/Git-on-my-level/codex-autorunner
- PyPI 包：https://pypi.org/project/codex-autorunner/
- Ticket 模板：https://github.com/Git-on-my-level/car-ticket-templates
- 官方文档：https://github.com/Git-on-my-level/codex-autorunner/blob/main/docs/

---

*🦞 文档版本 1.0 | 撰写日期：2026-03-31 | 基于仓库 commit 60f8358 (2026-03-31)*