# Claude-Mem：48K Stars·AI记忆系统·让Claude跨越会话持续学习

## 一、项目概述

### 1.1 Claude-Mem 是什么

**Claude-Mem** 是专为 Claude Code 打造的**持久化记忆压缩系统**，让 AI 在多次会话之间保持上下文连续性。

> "Persistent memory compression system built for Claude Code."

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | **48k** ⭐ (48,000!) |
| Forks | 3.7k |
| 贡献者 | 93 |
| 最新版本 | v12.1.0 (2026-04-09) |
| 提交数 | 1,662 commits |
| 许可证 | AGPL-3.0 |
| 语言 | TypeScript 82.8%, JavaScript 11.2% |

### 1.3 核心定位

| 维度 | 说明 |
|------|------|
| 🧠 **持久记忆** | 跨会话保持上下文 |
| 📊 **渐进式披露** | 分层记忆检索，Token 成本可见 |
| 🔍 **自然语言搜索** | 用 mem-search 技能查询项目历史 |
| 🌐 **多 IDE 支持** | Claude Code / Gemini CLI / Cursor / Windsurf / Codex |

### 1.4 在线资源

| 资源 | 链接 |
|------|------|
| 文档 | https://docs.claude-mem.ai |
| 官网 | https://claude-mem.ai |
| Discord | https://discord.com/invite/J4wttp9vDu |
| Twitter | @Claude_Memory |

## 二、为什么需要 Claude-Mem

### 2.1 问题：会话隔阂

传统 AI 编码助手每次新会话都是从零开始：

```
❌ 会话 1：Claude 学习了项目架构
❌ 会话 2：Claude 完全不记得之前学了什么
❌ 会话 3：又要重新解释一遍上下文
```

### 2.2 Claude-Mem 的解决方案

```
✅ 会话 1：Claude 学习并存储记忆
✅ 会话 2：Claude 自动加载相关记忆
✅ 会话 3：Claude 已经有项目上下文
```

### 2.3 核心优势

| 优势 | 说明 |
|------|------|
| 🚀 **零手动操作** | 自动捕获，无需人工干预 |
| 💰 **Token 高效** | ~10x Token 节省（渐进式披露） |
| 🔒 **隐私控制** | `<private>` 标签排除敏感内容 |
| 🌐 **全平台** | Claude Code / Gemini CLI / Cursor / Windsurf / Codex |

## 三、快速开始

### 3.1 一键安装（Claude Code）

```bash
npx claude-mem install
```

### 3.2 安装到 Gemini CLI

```bash
npx claude-mem install --ide gemini-cli
```

### 3.3 从插件市场安装

```bash
/plugin marketplace add thedotmack/claude-mem
/plugin install claude-mem
```

### 3.4 OpenClaw 网关安装

```bash
curl -fsSL https://install.cmem.ai/openclaw.sh | bash
```

### 3.5 验证安装

重启 Claude Code 或 Gemini CLI，新会话将自动出现之前会话的上下文记忆。

## 四、工作原理

### 4.1 五大生命周期钩子

Claude-Mem 通过 **5 个生命周期钩子** 自动捕获所有操作：

| 钩子 | 触发时机 | 作用 |
|------|----------|------|
| **SessionStart** | 会话开始时 | 加载历史记忆 |
| **UserPromptSubmit** | 用户提交提示时 | 记录用户意图 |
| **PostToolUse** | 工具执行后 | 捕获观察结果 |
| **Stop** | Claude 停止时 | 总结会话 |
| **SessionEnd** | 会话结束时 | 持久化存储 |

### 4.2 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Claude-Mem 系统架构                      │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │   Claude    │    │  Lifecycle  │    │   Worker    │ │
│  │   Code      │───▶│   Hooks     │───▶│   Service   │ │
│  └─────────────┘    └─────────────┘    └──────┬──────┘ │
│                                                │          │
│  ┌─────────────┐    ┌─────────────┐          │          │
│  │   mem-      │◀───│   SQLite   │◀─────────┤          │
│  │   search    │    │  Database  │          │          │
│  └─────────────┘    └─────────────┘          │          │
│         │                                       │          │
│  ┌──────▼──────┐    ┌─────────────┐          │          │
│  │   Chroma    │◀───│   Vector    │◀─────────┘          │
│  │   Database  │    │   Search    │                     │
│  └─────────────┘    └─────────────┘                     │
│         │                                                   │
│  ┌──────▼──────┐                                       │
│  │   Web UI     │  (localhost:37777)                    │
│  │   Viewer     │                                       │
│  └─────────────┘                                       │
└─────────────────────────────────────────────────────────┘
```

### 4.3 数据流

```
用户操作 → Hook 捕获 → Worker Service → SQLite 存储
                              ↓
                         Chroma 向量库
                              ↓
                       检索 → 渐进式披露 → 注入上下文
```

## 五、MCP 搜索工具

### 5.1 三层工作流

Claude-Mem 提供 **4 个 MCP 工具**，遵循高效的 **3 层工作流模式**：

| 工具 | 作用 | Token 消耗 |
|------|------|-----------|
| `search` | 获取紧凑索引（含 ID ~50-100 tokens/result） |
| `timeline` | 按时间获取上下文 ~100-200 tokens/result |
| `get_observations` | 按 ID 获取完整详情 ~500-1,000 tokens/result |

**~10x Token 节省**：先过滤再获取详情

### 5.2 使用示例

```javascript
// 第 1 步：搜索索引
search(query="authentication bug", type="bugfix", limit=10)
// 返回：[{"id": 123, "summary": "...", ...}, ...]

// 第 2 步：查看时间线
timeline(query="authentication bug", limit=5)
// 返回：时间上下文

// 第 3 步：获取完整详情
get_observations(ids=[123, 456])
// 返回：完整的观察记录
```

### 5.3 MCP 工具列表

| 工具 | 说明 |
|------|------|
| `search` | 全文搜索，支持类型/日期/项目过滤 |
| `timeline` | 获取特定观察的时间上下文 |
| `get_observations` | 按 ID 批量获取完整观察详情 |

## 六、配置与调优

### 6.1 设置文件

配置文件位于：`~/.claude-mem/settings.json`（首次运行自动创建）

### 6.2 主要配置项

| 配置项 | 说明 |
|--------|------|
| `ai_model` | AI 模型选择 |
| `worker_port` | Worker 服务端口（默认 37777） |
| `data_dir` | 数据存储目录 |
| `log_level` | 日志级别 |
| `context_injection` | 上下文注入策略 |

### 6.3 隐私控制

使用 `<private>` 标签排除敏感内容：

```markdown
这段代码包含密钥：<private>
sk-xxxxx-xxxxx
</private>
```

标记的内容不会被存储到记忆系统。

### 6.4 上下文配置

```json
{
  "context": {
    "max_tokens": 4096,
    "progressive_disclosure": true,
    "include_types": ["bugfix", "feature", "refactor"]
  }
}
```

## 七、Web UI 查看器

### 7.1 访问

启动后访问：**http://localhost:37777**

### 7.2 功能

| 功能 | 说明 |
|------|------|
| 📊 **实时流** | 查看记忆实时流入 |
| 🔍 **搜索** | 可视化搜索历史 |
| ⚙️ **设置** | 版本切换、配置调整 |
| 🧪 **Beta** | Endless Mode 等实验功能 |

### 7.3 Beta 功能

**Endless Mode**：仿生记忆架构，支持超长会话。

切换方式：Web UI → Settings → 切换 stable/beta 版本

## 八、多 IDE 支持

### 8.1 支持的 IDE

| IDE | 安装命令 |
|-----|---------|
| **Claude Code** | `npx claude-mem install` |
| **Gemini CLI** | `npx claude-mem install --ide gemini-cli` |
| **OpenClaw** | `curl -fsSL https://install.cmem.ai/openclaw.sh \| bash` |
| **Cursor** | 插件市场安装 |
| **Windsurf** | 插件市场安装 |
| **Codex** | `.codex-plugin` 目录 |

### 8.2 OpenClaw 集成

```bash
# 安装到 OpenClaw 网关
curl -fsSL https://install.cmem.ai/openclaw.sh | bash
```

安装程序自动处理：
- 依赖安装
- 插件设置
- AI Provider 配置
- Worker 启动
- 实时观察推送（Telegram、Discord、Slack 等）

## 九、搜索架构

### 9.1 混合搜索

Claude-Mem 使用 **混合搜索**结合：

| 搜索类型 | 说明 |
|----------|------|
| **语义搜索** | Chroma 向量数据库 |
| **关键词搜索** | SQLite FTS5 |
| **融合排序** | Reciprocal Rank Fusion |

### 9.2 向量数据库

```bash
# Chroma 自动安装（通过 uv）
# 数据存储在 ~/.claude-mem/chroma/
```

### 9.3 搜索参数

```javascript
search({
  query: "authentication bug fix",
  type: "bugfix",        // 可选：过滤类型
  date: "2026-04",       // 可选：日期范围
  project: "my-project",  // 可选：项目过滤
  limit: 10              // 限制数量
})
```

## 十、开发指南

### 10.1 系统要求

| 要求 | 版本 |
|------|------|
| Node.js | 18.0.0+ |
| Claude Code | 最新版 |
| Bun | 自动安装 |
| uv | 自动安装 |
| SQLite 3 | 内置 |

### 10.2 本地开发

```bash
# 克隆仓库
git clone https://github.com/thedotmack/claude-mem
cd claude-mem

# 安装依赖
npm install

# 开发模式
npm run dev

# 运行测试
npm test

# 构建
npm run build
```

### 10.3 提交 Bug 报告

```bash
cd ~/.claude/plugins/marketplaces/thedotmack
npm run bug-report
```

自动生成分详细的 Bug 报告。

## 十一、故障排除

### 11.1 常见问题

| 问题 | 解决方案 |
|------|----------|
| Node.js 未识别 | 安装 Node.js 18+ 并添加到 PATH |
| 依赖安装失败 | 重启终端或手动运行 `npm install` |
| 记忆不加载 | 检查 `~/.claude-mem/` 目录权限 |
| 搜索无结果 | 确认有历史观察数据 |

### 11.2 诊断工具

让 Claude 自动诊断：

```
描述你遇到的问题，Claude 会自动运行诊断技能并提供修复方案。
```

## 十二、架构演进

### 12.1 版本历史

| 版本 | 主要变化 |
|------|----------|
| v3 → v5 | 从简单存储到渐进式披露 |
| v5 → v8 | Chroma 向量搜索集成 |
| v8 → v10 | MCP 工具标准化 |
| v10 → v12 | Endless Mode Beta |

### 12.2 设计哲学

**渐进式披露**（Progressive Disclosure）：
- 始终加载：~50 tokens 的紧凑索引
- 按需加载：完整观察数据
- Token 节省：~10x

## 十三、对比竞品

| 特性 | Claude-Mem | Mem0 | SuperMemory | OpenMemory |
|------|-----------|-------|-------------|------------|
| **Stars** | 48k ⭐ | - | - | - |
| **渐进式披露** | ✅ | ❌ | ❌ | ❌ |
| **MCP 工具** | ✅ | ❌ | ❌ | ❌ |
| **Web UI** | ✅ | ❌ | ❌ | ❌ |
| **多 IDE** | ✅ | ❌ | ❌ | ❌ |
| **Token 节省** | ~10x | - | - | - |

## 十四、许可证说明

### 14.1 主许可证

**AGPL-3.0**（Affero General Public License）

| 条款 | 说明 |
|------|------|
| ✅ 自由使用 | 可以免费使用和修改 |
| ✅ 自由分发 | 可以分发副本 |
| 🔒 网络访问 | 如果在网络服务器上部署修改版本，必须开源 |
| ⚠️ 衍生作品 | 衍生作品也必须开源 |

### 14.2 Ragtime 目录

`ragtime/` 目录使用**单独的许可证**：
- **PolyForm Noncommercial License 1.0.0**

## 十五、资源链接

### 15.1 官方资源

| 资源 | 链接 |
|------|------|
| 📚 **文档** | https://docs.claude-mem.ai |
| 🌐 **官网** | https://claude-mem.ai |
| 💬 **Discord** | https://discord.com/invite/J4wttp9vDu |
| 🐦 **Twitter** | @Claude_Memory |
| 📋 **GitHub** | https://github.com/thedotmack/claude-mem |

### 15.2 多语言文档

支持 **20+ 种语言**的 README：
- 🇨🇳 简体中文
- 🇹🇼 繁体中文
- 🇯🇵 日语
- 🇰🇷 韩语
- 🇪🇸 西班牙语
- 🇩🇪 德语
- 🇫🇷 法语
- ...（共 20+ 种）

## 十六、总结

Claude-Mem 是**当前最完整的 AI 编码记忆系统**：

| 维度 | 说明 |
|------|------|
| 🧠 **持久记忆** | 跨会话保持上下文连续性 |
| 📊 **渐进式披露** | ~10x Token 节省 |
| 🔍 **MCP 搜索** | 自然语言查询项目历史 |
| 🌐 **全平台** | Claude Code / Gemini CLI / Cursor / Windsurf / Codex |
| 🔒 **隐私控制** | `<private>` 标签保护敏感内容 |
| 💰 **零成本** | 基于 Claude Code 免费使用 |

---

**🔗 相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/thedotmack/claude-mem |
| 文档 | https://docs.claude-mem.ai |
| Discord | https://discord.com/invite/J4wttp9vDu |

---

_🦞 本文由钳岳星君撰写，基于 Claude-Mem (48k Stars)_
