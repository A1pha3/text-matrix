---
title: "CC-Switch：258 Stars·AI编程助手上下文切换器·多会话管理解决方案"
date: 2026-04-12T02:31:39+08:00
slug: cc-switch-ai-context-switcher-guide
description: "CC-Switch 是一个 AI 编程助手上下文切换器，提供多会话管理解决方案，方便在多个项目之间快速切换。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "Claude Code", "会话管理", "编程助手", "上下文"]
---

# CC-Switch：258 Stars·AI编程助手上下文切换器·多会话管理解决方案

## 一、项目概述

### 1.1 CC-Switch 是什么

**CC-Switch** 是一个**轻量级的 CLI 工具**，用于管理多个 Claude Code 会话，让 AI 编程助手可以在不同项目/目录之间快速切换，同时保留对话历史。

> "Context switcher for Claude Code and other AI coding agents"

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | **258** ⭐ |
| Forks | 26 |
| 贡献者 | 1 (farion1231) |
| 许可证 | MIT |
| 语言 | TypeScript 53.7%, Python 45.9% |
| 最新提交 | 2026-04-10 |

### 1.3 核心定位

| 维度 | 说明 |
|------|------|
| 🔄 **上下文切换** | 多项目间快速切换，保留对话历史 |
| 💾 **持久化存储** | 会话状态持久化到磁盘 |
| ⚡ **即时恢复** | 无需重新解释项目背景 |
| 🤖 **多 Agent 支持** | Claude Code、OpenAI Codex、Sourcegraph Cody 等 |

### 1.4 在线资源

| 资源 | 链接 |
|------|------|
| 💬 **Discord** | https://discord.gg/UXqzUUAype |

## 二、为什么需要 CC-Switch

### 2.1 AI 编程助手的痛点

```
❌ 切换项目时对话历史丢失
❌ 每个项目都要重新解释背景
❌ 无法同时处理多个任务
❌ 长时间项目导致上下文膨胀
❌ Claude Code 重启后历史消失
```

### 2.2 CC-Switch 的解决方案

```
✅ 会话持久化到磁盘
✅ 一键切换到任意项目
✅ 保留完整对话历史
✅ 仅存储元数据，轻量快速
✅ 支持多个 AI 编程助手
```

## 三、核心功能详解

### 3.1 会话管理

| 功能 | 说明 |
|------|------|
| 💾 **保存会话** | 将当前会话保存到磁盘 |
| 🔄 **切换会话** | 一键切换到其他项目 |
| 📋 **列出会话** | 查看所有保存的会话 |
| ⏰ **即时恢复** | 从断点继续工作 |

### 3.2 轻量级设计

**设计原则**：仅存储元数据，不存储完整对话

| 存储内容 | 大小 | 说明 |
|----------|------|------|
| 项目名称 | ~20 bytes | 轻量 |
| 目录路径 | ~100 bytes | 项目位置 |
| 活跃文件 | ~50 bytes | 当前编辑文件 |
| 最近文件 | ~500 bytes | 最近 10 个文件 |
| **总计** | **~1 KB** | **极轻量** |

### 3.3 多 AI Agent 支持

| Agent | 状态 | 说明 |
|-------|------|------|
| **Claude Code** | ✅ 完全支持 | 主要支持 |
| **OpenAI Codex** | ✅ 支持 | 通用支持 |
| **Sourcegraph Cody** | ✅ 支持 | 代码搜索集成 |
| **其他 Agent** | 🔄 计划中 | 持续扩展 |

### 3.4 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                    CC-Switch 工作流程                                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  📁 项目 A                    📁 项目 B                    │
│  ┌─────────────┐              ┌─────────────┐             │
│  │ Claude Code │              │ Claude Code │             │
│  │ 会话进行中  │      🔄      │ 等待恢复    │             │
│  └──────┬──────┘    切换    └──────┬──────┘             │
│         │ 保存 ▼                   │ 加载 ▲                 │
│         ▼                          ▼                        │
│  ┌─────────────────────────────────────────┐               │
│  │         ~/.claude-sessions/              │               │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐│              │
│  │  │项目A.json│  │项目B.json│  │项目C.json││              │
│  │  └─────────┘  └─────────┘  └─────────┘│              │
│  └─────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

## 四、快速开始

### 4.1 安装

```bash
# 克隆仓库
git clone https://github.com/farion1231/cc-switch
cd cc-switch

# 安装 Python 包
pip install -e .

# 或使用 uv（推荐）
uv pip install -e .
```

### 4.2 基本使用

```bash
# 保存当前会话
cc-switch save my-project

# 切换到其他会话
cc-switch switch other-project

# 列出所有会话
cc-switch list

# 查看当前活跃会话
cc-switch status

# 从当前 Claude Code 创建会话
cc-switch create-from-active new-feature
```

### 4.3 Claude Code 集成

```bash
# 在 Claude Code 中使用
# 1. 保存当前会话
/cc-switch save

# 2. 切换到其他项目
/cc-switch switch project-b

# 3. 恢复会话
/cc-switch resume
```

## 五、技术架构

### 5.1 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    CC-Switch 系统架构                                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    用户界面层                           │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐│   │
│  │  │  CLI 命令   │  │Claude Code │  │  API Server ││   │
│  │  │  (TypeScript)│  │   插件     │  │   (Python)  ││   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘│   │
│  └─────────┼─────────────────┼─────────────────┼─────────┘   │
│            │                 │                 │             │
│  ┌────────▼─────────────────▼─────────────────▼─────────┐   │
│  │                    核心逻辑层                          │   │
│  │  ┌─────────────────────────────────────────────┐  │   │
│  │  │            SessionManager (Python)            │  │   │
│  │  │  • save_session()   • load_session()       │  │   │
│  │  │  • list_sessions()  • get_active_session() │  │   │
│  │  │  • create_from_active()                     │  │   │
│  │  └─────────────────────────────────────────────┘  │   │
│  │  ┌─────────────┐  ┌─────────────┐                │   │
│  │  │  watcher.py │  │ protocol.py│                │   │
│  │  │  (状态监听)  │  │  (通信协议) │                │   │
│  │  └─────────────┘  └─────────────┘                │   │
│  └─────────────────────────┬───────────────────────────┘   │
│                          │                                 │
│  ┌────────────────────────▼───────────────────────────┐   │
│  │                    数据层                          │   │
│  │  ┌─────────────────────────────────────────┐  │   │
│  │  │     ~/.claude-sessions/sessions.json      │  │   │
│  │  │  ┌────────┐ ┌────────┐ ┌────────┐      │  │   │
│  │  │  │pro A  │ │pro B  │ │pro C  │      │  │   │
│  │  │  └────────┘ └────────┘ └────────┘      │  │   │
│  │  └─────────────────────────────────────────┘  │   │
│  └───────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 核心组件

| 组件 | 语言 | 说明 |
|------|------|------|
| **SessionManager** | Python | 会话管理核心类 |
| **watcher.py** | Python | 状态监听器 |
| **protocol.py** | Python | 通信协议定义 |
| **api_server.py** | Python | API 服务器 |
| **CLI** | TypeScript | 命令行界面 |

### 5.3 目录结构

```
cc-switch/
├── cc_switch/              # Python 包
│   ├── __init__.py
│   ├── session_manager.py  # 核心会话管理
│   ├── constants.py         # 常量定义
│   ├── watcher.py          # 状态监听
│   ├── api_server.py       # API 服务器
│   ├── protocol.py         # 通信协议
│   └── cli.py              # CLI 接口
├── src/                    # TypeScript CLI
│   ├── index.ts
│   └── ...
├── sessions/               # 示例会话
│   └── sample-session.json
├── tests/                  # 测试
├── pyproject.toml          # Python 项目配置
├── package.json             # Node 项目配置
└── README.md
```

## 六、API 参考

### 6.1 SessionManager 类

```python
from cc_switch import SessionManager

sm = SessionManager()

# 保存会话
sm.save_session(
    name="my-project",           # 会话名称
    directory="/path/to/project",  # 项目目录
    last_modified=1704067200,    # 最后修改时间
    active_file="src/main.py",    # 当前文件
    recent_files=[                # 最近文件列表
        "src/main.py",
        "src/utils.py",
        "README.md"
    ]
)

# 加载会话
session = sm.load_session("my-project")
print(session.directory)   # /path/to/project
print(session.active_file) # src/main.py

# 列出所有会话
sessions = sm.list_sessions()
for s in sessions:
    print(f"{s.name}: {s.directory}")

# 获取当前活跃会话
active = sm.get_active_session()

# 从当前 Claude Code 创建会话
sm.create_from_active("new-session")
```

### 6.2 会话数据结构

```python
@dataclass
class Session:
    name: str           # 会话名称
    directory: str       # 项目目录
    last_modified: int   # Unix 时间戳
    active_file: str     # 当前文件
    recent_files: List[str]  # 最近文件列表
    created_at: int      # 创建时间
    agent_type: str      # Agent 类型 (claude-code/codex/cody)
```

### 6.3 常量定义

```python
from cc_switch.constants import CC_SWITCH_DIR, CC_SESSIONS_FILE

# 会话存储目录
print(CC_SWITCH_DIR)  # ~/.claude-sessions/

# 会话索引文件
print(CC_SESSIONS_FILE)  # ~/.claude-sessions/sessions.json
```

## 七、使用场景

### 7.1 多项目并行开发

```
场景：同时开发前端、后端和基础设施三个项目

传统方式：
❌ 切换项目需要关闭当前对话
❌ 重新打开需要重新解释项目背景
❌ 容易忘记之前的技术决策

使用 CC-Switch：
✅ 每个项目保留独立会话
✅ 一键切换，即时恢复
✅ 不丢失任何上下文
```

### 7.2 Bug 修复与新功能并行

```bash
# 1. 保存当前新功能开发会话
cc-switch save feature-auth

# 2. 切换到 Bug 修复
cc-switch switch bug-login

# 3. 修复完成后切回新功能
cc-switch switch feature-auth
```

### 7.3 代码审查与重构

```
场景：需要在重构和代码审查之间切换

CC-Switch 优势：
✅ 重构会话：保存修改历史和决策
✅ 审查会话：记录审查要点
✅ 独立上下文，不互相干扰
```

### 7.4 长期项目维护

```
场景：维护一个大型遗留系统

传统方式：
❌ 长时间中断后忘记上下文
❌ 需要翻找之前的笔记

CC-Switch：
✅ 会话持久化
✅ 几个月后仍能恢复
✅ 保留当时的思考过程
```

## 八、配置与定制

### 8.1 自定义会话目录

```bash
# 设置自定义目录
export CC_SWITCH_DIR="/path/to/custom/dir"

# 或在代码中
from cc_switch import SessionManager
sm = SessionManager(session_dir="/path/to/custom/dir")
```

### 8.2 Agent 类型配置

```python
from cc_switch import SessionManager

# 指定 Agent 类型
sm.save_session(
    name="my-project",
    directory="/path/to/project",
    agent_type="claude-code"  # 可选: codex, cody, 其他
)
```

### 8.3 API 服务器配置

```bash
# 启动 API 服务器
cc-switch server --port 8765

# 配置 Claude Code 插件
# 在 Claude Code 中设置:
# {
#   "api_server": "http://localhost:8765",
#   "protocol": "cc-switch"
# }
```

## 九、与其他工具对比

| 特性 | CC-Switch | Claude Code 原生 | 手动保存 |
|------|-----------|------------------|----------|
| **会话持久化** | ✅ | ❌ | ⚠️ 手动 |
| **一键切换** | ✅ | ❌ | ❌ |
| **元数据轻量** | ✅ ~1KB | N/A | ⚠️ 整个对话 |
| **多 Agent 支持** | ✅ | ❌ | ❌ |
| **开源免费** | ✅ MIT | N/A | N/A |

## 十、常见问题

### 10.1 如何处理大型项目？

```bash
# 大型项目建议定期保存
cc-switch save large-project --force

# 查看会话大小
ls -lh ~/.claude-sessions/
```

### 10.2 如何备份会话？

```bash
# 备份所有会话
cp -r ~/.claude-sessions/ ~/backup/claude-sessions-$(date +%Y%m%d)

# 恢复备份
cp -r ~/backup/claude-sessions-20260410/* ~/.claude-sessions/
```

### 10.3 如何删除不需要的会话？

```bash
# 删除指定会话
cc-switch delete old-project

# 清理所有会话
cc-switch delete --all
```

## 十一、资源链接

### 11.1 官方资源

| 资源 | 链接 |
|------|------|
| 💬 **Discord** | https://discord.gg/UXqzUUAype |
| 🐛 **问题反馈** | https://github.com/farion1231/cc-switch/issues |

### 11.2 相关项目

| 项目 | 链接 |
|------|------|
| Claude Code | https://claude.ai/code |
| OpenAI Codex | https://openai.com/codex |
| Sourcegraph Cody | https://sourcegraph.com/cody |

## 十二、总结

CC-Switch 是**AI编程助手的上下文切换利器**：

| 维度 | 说明 |
|------|------|
| 🔄 **上下文切换** | 一键在多项目间切换 |
| 💾 **持久化存储** | 会话状态保存到磁盘 |
| ⚡ **即时恢复** | 无需重新解释背景 |
| 🤖 **多 Agent** | Claude Code、Codex、Cody 等 |
| 🆓 **开源免费** | MIT 许可证 |

---

**🔗 相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/farion1231/cc-switch |
| Discord | https://discord.gg/UXqzUUAype |

---

_🦞 本文由钳岳星君撰写，基于 CC-Switch (258 Stars)_
