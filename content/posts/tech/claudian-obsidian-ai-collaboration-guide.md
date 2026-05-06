---
title: "Claudian：在Obsidian笔记库中嵌入Claude Code的AI协作插件"
date: "2026-04-09T20:40:00+08:00"
slug: "claudian-obsidian-ai-collaboration-guide"
description: "Claudian是首个将Claude Code嵌入Obsidian笔记库的插件，让笔记成为AI的工作目录。本文深入解析其核心功能、内联编辑、Skills系统、MCP服务器集成，以及在知识管理中的应用。"
draft: false
categories: ["技术笔记"]
tags: ["Claudian", "Obsidian", "Claude Code", "AI协作", "笔记工具", "知识管理", "MCP", "第二大脑"]
---

# Claudian：在Obsidian笔记库中嵌入Claude Code的AI协作插件

## §1 项目概述

### 1.1 核心定位

**Claudian**是首个将AI编程助手（Claude Code、Codex）嵌入Obsidian笔记库的插件，让你的笔记库成为AI的**工作目录**。

> "An Obsidian plugin that embeds AI coding agents in your vault. Your vault becomes the agent's working directory — file read/write, search, bash, and multi-step workflows all work out of the box."

```
┌─────────────────────────────────────────────────────────────┐
│              Claudian 核心洞察                                     │
├─────────────────────────────────────────────────────────────┤
│                                                                │
│  传统笔记系统：                                                │
│  笔记 → 静态文字 → 无法与AI交互                                   │
│                                                                │
│  Claudian模式：                                               │
│  笔记库 ←→ AI工作目录 ←→ 动态协作                                 │
│                                                                │
│  核心突破：                                                     │
│  笔记不仅是"记录"，更是"工作空间"                                    │
│  AI可以读取、编辑、搜索、运行命令                                   │
│                                                                │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 与传统笔记AI的对比

| 维度 | 传统笔记AI | Claudian |
|------|------------|---------|
| **交互方式** | 问答式 | 对话+操作双轨 |
| **执行能力** | 仅生成文字 | 读写文件、搜索、bash |
| **上下文** | 单次对话 | 持久化会话 |
| **工具调用** | 无 | MCP/内置工具 |
| **多Agent** | 无 | 多Tab+子Agent |

### 1.3 项目统计

| 指标 | 数值 |
|------|------|
| **Stars** | 6.5k |
| **Forks** | 383 |
| **最新版本** | 2.0.1 (2026-04-06) |
| **贡献者** | 15 |
| **语言** | TypeScript 97.3% |
| **许可证** | MIT |

## §2 核心功能深度解析

### 2.1 内联编辑（Inline Edit）

**核心特性**：选中文字+快捷键，直接在笔记中进行AI编辑，带词级别diff预览。

```markdown
## 使用流程

1. 选中笔记中的文字（或在光标位置）
2. 按快捷键触发
3. AI编辑区域出现，实时预览diff
4. 确认后替换原文
```

**Diff预览示例**：

```diff
- 传统的机器学习需要大量标注数据
+ 传统的机器学习需要大量标注数据，
+ 而迁移学习可以复用预训练模型的知识，
+ 大幅减少目标任务所需的标注样本数量。
```

### 2.2 Slash Commands & Skills

**核心特性**：输入`/`或`$`触发可复用的提示词模板。

```markdown
## 触发方式

/  → 内置Skills（如/write、/edit、/debug）
$  → 用户自定义Skills

## 内置Skills

| Skill | 用途 |
|-------|------|
| /write | 写作助手 |
| /edit | 编辑修改 |
| /debug | 代码调试 |
| /explain | 解释代码 |
| /summarize | 总结内容 |

## 自定义Skills

用户可以在 vault 级别或笔记级别定义自己的Skills。
```

### 2.3 @提及系统

**核心特性**：`@mention`任何内容，让AI处理。

```markdown
## @提及类型

@文件 → 让AI读取并处理指定文件
  示例: @project/proposal.md

@子Agent → 委托给专门的AI处理
  示例: @researcher 分析这个主题

@MCP服务器 → 调用外部工具
  示例: @filesystem 搜索包含关键词的文件

@外部目录 → 处理非笔记库的文件
  示例: @~/projects/code 分析代码库
```

### 2.4 Plan Mode

**核心特性**：AI先探索、制定计划，人工批准后再执行。

```markdown
## Plan Mode 工作流

1. 用户: "帮我重构这个项目"
2. AI (Plan Mode): 
   - 探索代码库结构
   - 分析依赖关系
   - 制定重构计划
   - 展示计划待批准
3. 用户审查计划
4. 用户: "批准"
5. AI (执行 Mode): 
   - 按计划执行重构
   - 逐步确认
```

**快捷键**：`Shift+Tab` 切换Plan Mode

### 2.5 Instruction Mode

**核心特性**：从聊天输入精细化自定义指令。

```markdown
## 使用方式

# 你想要的具体要求
# 示例：
# 用TypeScript重写
# 添加完整的类型注解
# 保持原有的函数签名
```

## §3 MCP服务器集成

### 3.1 支持的协议

| 协议 | Claudian支持 | 说明 |
|------|-------------|------|
| **stdio** | ✅ | 标准输入输出 |
| **SSE** | ✅ | Server-Sent Events |
| **HTTP** | ✅ | HTTP请求 |

### 3.2 MCP配置

```json
// Claude的MCP在app内管理
// Codex使用CLI管理的MCP配置

// settings中配置示例
{
  "mcp": {
    "servers": [
      {
        "name": "filesystem",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem"],
        "cwd": "/path/to/vault"
      },
      {
        "name": "github",
        "command": "npx", 
        "args": ["-y", "@modelcontextprotocol/server-github"]
      }
    ]
  }
}
```

### 3.3 内置工具

| 工具 | 功能 |
|------|------|
| **文件读写** | 读取、创建、编辑笔记 |
| **搜索** | 全局搜索内容 |
| **Bash** | 执行Shell命令 |
| **Web搜索** | 搜索互联网 |
| **MCP工具** | 第三方扩展 |

## §4 多会话与对话管理

### 4.1 多Tab支持

```markdown
## 多会话功能

- 新建Tab: 创建独立的AI对话
- 切换Tab: 快速在不同任务间切换
- 合并Tab: 将多个对话合并

## 对话操作

| 操作 | 快捷键/方式 |
|------|-------------|
| 新建 | 工具栏+按钮 |
| 分叉 | 从当前对话创建分支 |
| 恢复 | 重新加载历史会话 |
| 压缩 | 精简上下文 |
```

### 4.2 会话持久化

```markdown
## 存储位置

vault/.claudian/         # Claudian设置和会话元数据
vault/.claude/           # Claude提供商的会话文件
~/.claude/projects/       # Claude转录历史 (macOS/Linux)
~/.codex/sessions/       # Codex转录历史

## 数据保护

- 本地存储，不上传云端
- 加密敏感信息
- 可配置保留策略
```

## §5 安装与配置

### 5.1 系统要求

| 要求 | 版本 |
|------|------|
| **Obsidian** | v1.4.5+ |
| **平台** | Desktop only (macOS/Linux/Windows) |
| **Claude CLI** | Native install (recommended) |
| **Codex CLI** | Optional |

### 5.2 安装方式

**方式1: GitHub Release（推荐）**

```bash
# 1. 下载最新release
# 下载 main.js, manifest.json, styles.css

# 2. 创建插件目录
mkdir -p /path/to/vault/.obsidian/plugins/claudian

# 3. 复制文件到目录

# 4. 启用插件
# Settings → Community plugins → Enable "Claudian"
```

**方式2: BRAT自动更新**

```markdown
# 1. 安装BRAT插件
Settings → Community plugins → BRAT

# 2. 添加Claudian
Settings → BRAT → Add Beta plugin
URL: https://github.com/YishenTu/claudian

# 3. 自动更新
# BRAT会自动检查更新
```

**方式3: 源码开发**

```bash
# 克隆到插件目录
cd /path/to/vault/.obsidian/plugins
git clone https://github.com/YishenTu/claudian.git
cd claudian

# 安装依赖并构建
npm install
npm run build

# 启用插件
Settings → Community plugins → Enable "Claudian"
```

### 5.3 Claude CLI配置

```bash
# 找到Claude CLI路径
# macOS/Linux
which claude
# 示例: /Users/you/.volta/bin/claude

# Windows
where.exe claude
# 示例: C:\Users\you\AppData\Local\Claude\claude.exe

# 如果遇到"CLI not found"
# 设置 → Advanced → Claude CLI path
```

## §6 架构解析

### 6.1 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                 Claudian 系统架构                                    │
├─────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Obsidian 主界面                           │   │
│  │            侧边栏聊天 | 内联编辑 | 设置面板                  │   │
│  └──────────────────────────┬────────────────────────────┘   │
│                             │                                   │
│                             ↓                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    src/core (核心层)                        │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐             │   │
│  │  │ Runtime  │  │Registry  │  │Security │             │   │
│  │  │ 运行时   │  │ 注册表   │  │ 审批工具 │             │   │
│  │  └──────────┘  └──────────┘  └──────────┘             │   │
│  └──────────────────────────┬────────────────────────────┘   │
│                             │                                   │
│         ┌───────────────────┼───────────────────┐           │
│         ↓                   ↓                       ↓           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│  │   Claude    │    │   Codex     │    │  Features   │   │
│  │   Provider  │    │   Provider  │    │    功能层    │   │
│  │  Claude SDK │    │  JSON-RPC   │    │  Chat/Tabs  │   │
│  │  MCP插件    │    │  HTTP传输   │    │Inline/Edit  │   │
│  └─────────────┘    └─────────────┘    └─────────────┘   │
│                                                                │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 目录结构

```typescript
src/
├── main.ts                 // 插件入口点
├── app/                   // 共享默认值和插件级存储
├── core/                  // Provider-neutral运行时
│   ├── runtime/           // ChatRuntime接口和审批类型
│   ├── providers/        // Provider注册和工作区服务
│   ├── security/          // 审批工具
│   └── ...                // commands, mcp, prompt, storage, tools, types
├── providers/
│   ├── claude/            // Claude SDK适配器
│   │   ├── runtime/       // ChatRuntime实现
│   │   ├── prompt/       // 提示词编码
│   │   ├── storage/      // 会话存储
│   │   └── mcp/         // MCP插件
│   └── codex/            // Codex应用服务器适配器
│       ├── runtime/      // JSON-RPC传输
│       └── history/      // JSONL历史
├── features/
│   ├── chat/            // 侧边栏聊天
│   │   ├── tabs/        // 多Tab管理
│   │   ├── controllers/ // 控制器
│   │   └── renderers/   // 渲染器
│   ├── inline-edit/      // 内联编辑
│   │   ├── modal/       // 编辑弹窗
│   │   └── diff/        // Diff预览
│   └── settings/        // 设置面板
├── shared/                // 可复用UI组件
├── i18n/                 // 国际化 (10种语言)
└── utils/                // 横切工具
```

## §7 应用场景

### 7.1 知识管理

| 场景 | 使用价值 |
|------|----------|
| **卡片笔记** | AI帮你扩展、完善卡片内容 |
| **知识图谱** | AI帮你发现关联 |
| **文献管理** | AI帮你总结论文要点 |
| **概念解释** | AI用你能理解的方式解释 |

### 7.2 写作助手

| 场景 | 使用价值 |
|------|----------|
| **技术文档** | AI帮你写完整文档 |
| **博客文章** | AI帮你润色、扩展 |
| **研究报告** | AI帮你整理思路 |
| **邮件撰写** | AI帮你草稿 |

### 7.3 编程辅助

| 场景 | 使用价值 |
|------|----------|
| **代码注释** | AI帮你生成文档注释 |
| **Bug修复** | AI分析并修复 |
| **代码重构** | Plan Mode确保安全重构 |
| **代码审查** | AI审查代码质量 |

## §8 隐私与安全

### 8.1 数据流

```markdown
## 数据流向

发送至API:
- 你的输入内容
- 附加的文件
- 图片
- 工具调用输出
- 默认: Anthropic (Claude) 或 OpenAI (Codex)
- 可配置

本地存储:
- Claudian设置 → vault/.claudian/
- Claude会话 → vault/.claude/
- 转录历史 → ~/.claude/projects/ (Claude)
- 转录历史 → ~/.codex/sessions/ (Codex)

无遥测:
- 不追踪任何分析数据
```

### 8.2 安全建议

```markdown
## 安全最佳实践

1. 敏感笔记 → 使用Obsidian加密
2. API密钥 → 存储在环境变量
3. 外部命令 → Plan Mode审批后再执行
4. 文件操作 → 定期备份笔记库
```

## §9 故障排除

### 9.1 常见问题

| 问题 | 解决方案 |
|------|----------|
| **Claude CLI not found** | 设置 → Advanced → Claude CLI path |
| **npm/node路径不同** | 设置 → Environment → 添加PATH |
| **API超时** | 检查网络连接 |
| **会话丢失** | 检查vault/.claude/目录 |

### 9.2 平台路径示例

```markdown
## macOS/Linux
which claude
# → /Users/you/.volta/bin/claude

## Windows (native)
where.exe claude
# → C:\Users\you\AppData\Local\Claude\claude.exe

## Windows (npm)
npm root -g
# → {root}\@anthropic-ai\claude-code\cli.js
```

## §10 总结

### 10.1 核心价值

Claudian重新定义了笔记工具的边界：

- ✅ **AI嵌入**：Claude Code成为笔记的一部分
- ✅ **双向交互**：笔记不仅是AI的输入，更是AI的工作目录
- ✅ **工具调用**：内置+MCP扩展的强大能力
- ✅ **Plan Mode**：人工可控的AI执行
- ✅ **多会话管理**：复杂任务的多视角处理
- ✅ **隐私优先**：本地存储，无遥测

### 10.2 适用人群

| 人群 | 使用价值 |
|------|----------|
| **知识工作者** | 构建第二大脑 |
| **程序员** | 文档与代码一体化 |
| **研究者** | 论文阅读与笔记 |
| **写作者** | AI辅助写作 |

---

**官方资源**：

- GitHub：github.com/YishenTu/claudian
- 最新版本：2.0.1 (2026-04-06)
- 文档：内置于Obsidian设置面板

---

🦞 文档版本：v1.0 | 写作日期：2026-04-09
