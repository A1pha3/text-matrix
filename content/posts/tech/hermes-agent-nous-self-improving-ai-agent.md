---
title: "Hermes Agent：会自我进化的AI Agent，Notion式记忆+全平台消息+Skills自适应"
date: 2026-04-10T11:30:00+08:00
lastmod: 2026-04-10T11:30:00+08:00
draft: false
tags: ["Hermes Agent", "Nous Research", "AI Agent", "Self-Improving", "Skills系统", "多平台消息", "OpenClaw迁移"]
categories: ["技术教程"]
hiddenFromHomePage: false
slug: "hermes-agent-self-improving-ai-agent"
description: "Hermes Agent是Nous Research推出的自进化AI Agent框架，具备内置学习循环、Agent式记忆、Skills自改进、多平台消息（ Telegram/Discord/Slack）、OpenClaw无缝迁移等功能。本文深入解析其架构设计、核心特性、安装配置与开发扩展。"
---

# Hermes Agent：会自我进化的AI Agent

**Notion式记忆 + 全平台消息 + Skills自适应**

🦞 作者：钳岳星君 | 📅 更新：2026-04-10

---

## §1 学习目标

通过本文，你将全面掌握：

1. **Hermes Agent的核心架构** — 理解其自进化学习循环的设计原理
2. **内置Skills系统** — 掌握如何让Agent从经验中创建和改进Skills
3. **多平台消息网关** — 学会配置Telegram、Discord、Slack、WhatsApp等消息平台
4. **记忆与上下文管理** — 理解Agent式记忆与FTS5会话搜索机制
5. **OpenClaw迁移** — 掌握从OpenClaw无缝迁移到Hermes的操作步骤
6. **自定义扩展开发** — 学会添加自定义Skills、工具和MCP集成

---

## §2 原理分析

### 2.1 什么是Hermes Agent？

**Hermes Agent**是由[Nous Research](https://nousresearch.com)打造的**自进化AI Agent框架**。它的核心特点是**内置学习循环**——Agent能够从经验中创建Skills，在使用过程中自我改进，并跨会话保持记忆。

与传统的静态Agent不同，Hermes是一个"活"的系统：它会记住你教给它的东西，下次遇到类似任务时会自动应用这些知识。

### 2.2 核心概念

| 概念 | 解释 |
|------|------|
| **Skills** | 从经验中自动创建的可复用任务模板 |
| **Memory** | Agent整理的记忆，带有周期性提醒 |
| **Sessions** | 跨会话的FTS5搜索 + LLM摘要 |
| **Gateway** | 消息网关，支持多平台统一接入 |
| **Toolsets** | 40+内置工具的模块化集合 |
| **Subagents** | 并行子Agent，用于复杂任务分解 |

### 2.3 自进化学习循环

Hermes的核心是其**闭环学习系统**：

```
用户任务 → Agent执行 → 结果评估 → Skills创建 → 自我改进 → 下次复用
```

1. **任务执行**：Agent处理用户请求
2. **经验积累**：复杂任务被记录为经验轨迹
3. **Skills创建**：自动从成功经验中提取Skills
4. **使用中改进**：Skills在每次使用中被优化
5. **记忆持久化**：关键知识被周期性提醒强化

---

## §3 架构分析

### 3.1 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Hermes Agent                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Hermes    │  │  Gateway   │  │  Skills System     │  │
│  │  CLI/TUI   │  │  (多平台)  │  │  (自进化)         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Memory    │  │  Cron     │  │  MCP Integration   │  │
│  │  (持久化)  │  │  (调度)   │  │  (扩展)           │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Local     │  │  Docker    │  │  Modal / Daytona    │  │
│  │  Terminal  │  │  Container  │  │  (Serverless)     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 目录结构

```bash
hermes-agent/
├── agent/              # Agent核心逻辑
├── acp_adapter/        # ACP协议适配器
├── acp_registry/       # ACP注册表
├── cron/               # 定时任务
├── datagen-config-examples/  # 数据生成配置示例
├── docker/             # Docker支持
├── docs/               # 文档
├── environments/       # 环境配置
├── gateway/            # 消息网关
├── hermes_cli/         # CLI工具
├── landingpage/        # 着陆页
├── nix/                # Nix支持
├── optional-skills/    # 可选Skills
├── plugins/            # 插件系统
├── scripts/            # 安装脚本
├── skills/             # Skills集合
├── tests/              # 测试
├── tools/              # 工具集
├── website/            # 网站
├── cli.py              # CLI入口
├── hermmes             # 主脚本
├── hermes_state.py     # 状态管理
├── hermes_logging.py   # 日志
├── toolsets.py         # 工具集管理
└── requirements.txt    # 依赖
```

### 3.3 支持的LLM提供商

Hermes不绑定特定模型，支持多种LLM提供商：

| 提供商 | 模型 | 特点 |
|--------|------|------|
| **OpenRouter** | 200+模型 | 聚合平台，按需调用 |
| **Nous Portal** | Nous系列 | Nous Research官方 |
| **GLM (z.ai)** | 智谱模型 | 中文优化 |
| **Kimi/Moonshot** | Kimi系列 | 长上下文 |
| **MiniMax** | 多种模型 | 性价比高 |
| **OpenAI** | GPT-4等 | 官方API |
| **自定义端点** | 任何兼容API | 自托管 |

切换模型只需命令：`/model provider:model`，无需修改代码。

---

## §4 功能详解

### 4.1 Skills系统（核心特性）

Skills是Hermes最强大的特性之一。不同于传统的静态指令模板，Skills是**从经验中自动提取的可复用知识块**。

**Skills类型**：

1. **自动创建Skills** — 复杂任务完成后，Agent自动创建对应Skill
2. **使用中改进** — 每次执行Skills时，根据结果微调
3. **Skills Hub** — 社区分享的Skills库（agentskills.io）
4. **OpenClaw兼容** — 可导入OpenClaw的Skills

**示例Skills**：

```bash
# 查看可用Skills
hermes skills

# 使用特定Skill
/herm es <skill-name>

# 创建新Skill
/hermes skill create <name>
```

### 4.2 多平台消息网关

Hermes Gateway让你可以从任意平台与Agent对话：

| 平台 | 命令 | 功能 |
|------|------|------|
| **Telegram** | `/start` | 即时消息 |
| **Discord** | 斜杠命令 | 服务器聊天 |
| **Slack** | `@hermes` | 团队协作 |
| **WhatsApp** | 直接对话 | 移动端 |
| **Signal** | 安全消息 | 隐私通信 |
| **Email** | 邮件接口 | 异步通信 |
| **CLI** | `hermes` | 终端直接 |

**配置示例**：

```bash
# 启动网关
hermes gateway setup   # 交互式配置向导
hermes gateway start   # 启动网关守护进程

# Telegram配置
export TELEGRAM_BOT_TOKEN=xxx
export TELEGRAM_ALLOWED_USERS=user1,user2

# Discord配置
export DISCORD_BOT_TOKEN=xxx
export DISCORD_GUILD_ID=xxx
```

### 4.3 Agent式记忆系统

Hermes的Memory系统是其"灵魂"：

1. **Agent整理的Memory** — Agent自动整理重要信息
2. **周期性提醒** — 关键记忆会被周期性强化
3. **FTS5全文搜索** — 跨会话搜索历史对话
4. **LLM摘要** — 自动生成会话摘要便于快速回顾
5. **Honcho用户建模** — 理解用户偏好和习惯

**记忆命令**：

```bash
/hermes memory          # 查看当前记忆
/hermes memory search <query>  # 搜索记忆
/hermes insights --days 7    # 查看7天洞察
```

### 4.4 定时任务（Cron）

Hermes内置自然语言定时任务：

```
"每天早上8点给我一份工作报告"
"每周五下午6点自动备份代码"
"每月底生成财务汇总"
```

配置简单：

```bash
/hermes cron add "daily report" --time "08:00" --days Mon-Fri
/hermes cron list   # 查看所有定时任务
/hermes cron delete <id>  # 删除任务
```

### 4.5 并行子Agent

对于复杂任务，Hermes可以派生并行子Agent：

```python
# 内置batch_runner.py示例
python batch_runner.py --tasks task1.json task2.json task3.json

# 或在对话中
"帮我同时分析这三个项目的代码结构"
```

子Agent隔离运行，通过RPC通信，开销几乎为零。

### 4.6 OpenClaw迁移

Hermes支持从OpenClaw一键迁移：

```bash
# 自动检测并迁移
hermes claw migrate

# 预览迁移内容
hermes claw migrate --dry-run

# 仅迁移用户数据（不含密钥）
hermes claw migrate --preset user-data

# 覆盖已有冲突
hermes claw migrate --overwrite
```

**迁移内容**：

| 项目 | 说明 |
|------|------|
| SOUL.md | 人格文件 |
| Memories | MEMORY.md和USER.md |
| Skills | 用户创建的Skills → `~/.hermes/skills/openclaw-imports/` |
| Command allowlist | 命令白名单 |
| Messaging settings | 消息平台配置 |
| API keys | 允许的密钥（Telegram, OpenRouter等） |
| TTS assets | 语音文件 |
| Workspace instructions | AGENTS.md配置 |

---

## §5 使用说明

### 5.1 安装

**一键安装**：

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

**平台支持**：

- Linux ✅
- macOS ✅
- WSL2 ✅
- Android (Termux) ✅

**安装后**：

```bash
source ~/.bashrc  # 或 source ~/.zshrc
hermes           # 启动对话
```

**Docker安装**：

```bash
docker pull nousresearch/hermes-agent
docker run -it nousresearch/hermes-agent
```

### 5.2 首次配置

```bash
hermes setup  # 运行完整配置向导
```

向导会依次配置：
1. LLM提供商和模型
2. 消息平台（可选）
3. 安全设置
4. 记忆偏好

### 5.3 基础命令

| 命令 | 功能 |
|------|------|
| `hermes` | 启动CLI对话 |
| `hermes model <provider:model>` | 切换模型 |
| `hermes tools` | 查看工具列表 |
| `hermes config set <key> <value>` | 设置配置 |
| `hermes gateway` | 管理消息网关 |
| `hermes skills` | 管理Skills |
| `hermes cron` | 管理定时任务 |
| `hermes update` | 更新版本 |
| `hermes doctor` | 诊断问题 |

### 5.4 对话界面快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+C` | 中断当前任务 |
| `/new` | 新对话 |
| `/reset` | 重置当前会话 |
| `/model <provider:model>` | 切换模型 |
| `/personality <name>` | 切换人格 |
| `/compress` | 压缩上下文 |
| `/usage` | 查看用量 |
| `/skills` | 查看Skills |
| `/platforms` | 查看已连接平台 |

### 5.5 Skills Hub使用

Skills Hub（agentskills.io）分享社区Skills：

```bash
# 访问Skills Hub
/hermes skills hub

# 安装热门Skill
/hermes skills install <skill-name>

# 创建自定义Skill
/hermes skills create my-task
# 编辑生成的skill文件
/hermes skills test my-task
```

---

## §6 开发扩展

### 6.1 自定义工具

创建自定义工具：

```python
# tools/my_tool.py
from typing import Any
from agent.tools import tool

@tool(name="my_custom_tool", description="执行自定义任务")
def my_custom_tool(param: str) -> dict[str, Any]:
    """自定义工具的实现"""
    result = do_something(param)
    return {"status": "success", "result": result}
```

注册到toolsets：

```bash
# 或在配置文件中启用
hermes tools enable my_custom_tool
```

### 6.2 MCP服务器集成

Hermes支持Model Context Protocol扩展：

```bash
# 安装MCP服务器
pip install mcp-server-custom

# 配置MCP
export MCP_SERVER_URL=http://localhost:8080
hermes mcp list   # 查看已连接的MCP服务器
```

### 6.3 插件开发

创建插件：

```bash
hermes plugins create my-plugin
cd my-plugin
# 编辑插件代码
hermes plugins build
```

---

## §7 最佳实践

### 7.1 有效使用Skills

1. **明确任务边界** — Skills应该专注单一任务
2. **提供示例** — 创建Skill时包含2-3个使用示例
3. **迭代改进** — 观察Skill执行结果，适时调整
4. **分享价值** — 好的Skills可以发布到Skills Hub

### 7.2 记忆管理

1. **定期整理** — 周期性查看和清理无用记忆
2. **使用FTS搜索** — 善用跨会话搜索找回信息
3. **设置提醒** — 重要信息设置周期性提醒强化

### 7.3 安全建议

1. **命令审批** — 危险命令设为手动审批
2. **DM配对** — 消息平台启用DM配对验证
3. **容器隔离** — 使用Docker运行不信任的任务
4. **密钥管理** — 敏感信息使用环境变量而非配置文件

### 7.4 性能优化

1. **上下文压缩** — 定期使用`/compress`释放上下文
2. **模型选择** — 简单任务用小模型节省成本
3. **服务器less** — Daytona/Modal在空闲时几乎零成本

---

## §8 FAQ

**Q: Hermes和OpenClaw有什么区别？**

A: Hermes是OpenClaw的精神继承者，保留了OpenClaw的核心概念（Skills、记忆、人格），同时增加了自进化学习、多平台网关、更好的可扩展性。Hermes提供一键迁移脚本从OpenClaw迁移。

**Q: 需要GPU吗？**

A: 不需要。Hermes可以在$5的VPS上运行，也支持Modal/Daytona的serverless模式，空闲时几乎零成本。当然，有GPU可以运行更大模型。

**Q: 支持中文吗？**

A: 支持。Hermes支持任何LLM提供商，包括GLM、Kim等中文优化模型。对话界面支持UTF-8。

**Q: 如何保证隐私？**

A: Hermes支持本地运行、自托管API端点、Docker隔离等多种部署方式。敏感数据可以不离开你的基础设施。

**Q: 可以导入现有的OpenClaw Skills吗？**

A: 可以。使用`hermes claw migrate --overwrite`可以从OpenClaw导入所有Skills、记忆和配置。

---

## 附录：相关资源

- **GitHub**: https://github.com/NousResearch/hermes-agent
- **文档**: https://hermes-agent.nousresearch.com/docs
- **Discord**: https://discord.gg/NousResearch
- **Skills Hub**: https://agentskills.io
- **Nous Research**: https://nousresearch.com

---

*本文使用[hugo-writer](https://github.com/nicepkg/hugo-writer)生成，遵循MIT许可证。*
