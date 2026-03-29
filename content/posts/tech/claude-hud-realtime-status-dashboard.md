---
title: "Claude HUD：实时显示 Claude Code 状态的智能仪表盘"
date: 2026-03-29T15:50:00+08:00
slug: "claude-hud-realtime-status-dashboard"
description: "Claude HUD 是 14.8k Stars 的 Claude Code 插件，实时显示上下文使用量、工具活动、智能体状态、Git 信息，让 AI 编程过程一目了然。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "Claude HUD", "AI编程", "状态监控", "终端工具"]
---

# Claude HUD：实时显示 Claude Code 状态的智能仪表盘

## 一、项目概览

**Claude HUD** 是由 jarrodwatts 开发的 Claude Code 插件，能够实时显示 Claude Code 会话中的关键状态信息：上下文使用量、活跃工具、运行中的智能体、待办事项进度等。这些信息始终显示在终端输入框下方，让开发者对 AI 编程过程一目了然。

### 1.1 核心定位

Claude Code 作为一款强大的 AI 编程工具，在使用过程中开发者往往面临几个痛点：

1. **上下文窗口不可见**：无法准确判断上下文还剩多少、何时会触及上限
2. **工具执行不透明**：不知道 Claude 正在读取、编辑还是搜索文件
3. **智能体状态未知**：无法了解子智能体正在执行什么任务
4. **进度跟踪困难**：任务完成度不清晰

Claude HUD 正是为解决这些痛点而生。

### 1.2 技术统计

| 指标 | 数值 |
|------|------|
| Stars | 14.8k |
| Forks | 603 |
| Commits | 326 |
| 最新提交 | 2026-03-23 |
| 分支数 | 36 |
| 许可证 | MIT |
| 主要语言 | TypeScript |

## 二、核心功能

### 2.1 五大显示模块

Claude HUD 提供五大核心信息显示：

| 显示模块 | 说明 | 价值 |
|----------|------|------|
| **Project path** | 项目路径（可配置 1-3 级目录） | 清楚当前在哪个项目工作 |
| **Context health** | 上下文窗口使用量（绿→黄→红渐变） | 及时了解上下文余量，避免措手不及 |
| **Tool activity** | 工具活动（读取/编辑/搜索文件） | 实时观察 Claude 的操作行为 |
| **Agent tracking** | 子智能体运行状态 | 了解并行任务的执行进度 |
| **Todo progress** | 待办事项完成进度 | 追踪任务完成情况 |

### 2.2 默认显示（2 行）

```
[Opus] │ my-project git:(main*) Context █████░░░░░ 45% │ Usage ██░░░░░░░░ 25% (1h 30m / 5h)
```

**第一行**：模型名称、提供商/认证标签（如 Bedrock 或 API）、项目路径、Git 分支

**第二行**：上下文进度条（绿→黄→红）+ 使用量进度条 + 会话时长

### 2.3 可选显示线（通过 `/claude-hud:configure` 启用）

```
◐ Edit: auth.ts | ✓ Read ×3 | ✓ Grep ×2 ← 工具活动
◐ explore [haiku]: Finding auth code (2m 15s) ← 智能体状态
▸ Fix authentication bug (2/5) ← 待办进度
```

## 三、工作原理

### 3.1 技术架构

Claude HUD 利用 Claude Code 原生的 **statusline API** 实现，无需独立窗口、不需要 tmux、在任何终端都能工作。

```
Claude Code → stdin JSON → claude-hud → stdout → 终端显示
                        ↘ transcript JSONL（工具、智能体、待办数据）
```

### 3.2 核心特性

- **原生数据**：直接从 Claude Code 获取 token 数据（非估算值）
- **自适应上下文**：跟随 Claude Code 报告的上下文窗口大小，支持新版 1M context 会话
- **实时解析**：解析 transcript 获取工具/智能体活动
- **高频更新**：约 300ms 刷新一次

### 3.3 数据来源

Claude HUD 解析两类数据：

1. **stdin JSON**：Claude Code 实时推送的会话状态
2. **transcript JSONL**：完整的操作记录，用于提取工具调用和智能体状态

## 四、安装配置

### 4.1 安装步骤

**第一步：添加插件市场**

```
/plugin marketplace add jarrodwatts/claude-hud
```

**第二步：安装插件**

> ⚠️ Linux 用户：点击此处先行操作

```
/plugin install claude-hud
```

**第三步：配置状态栏**

```
/claude-hud:setup
```

**第四步：重启 Claude Code**

完成！重启后 HUD 将显示在终端底部。

> ⚠️ Windows 用户：设置完成后需要完全重启 Claude Code

### 4.2 配置预设

Claude HUD 提供三种预设：

| 预设 | 显示内容 |
|------|----------|
| **Full** | 显示所有信息：工具、智能体、待办、Git、使用量、会话时长 |
| **Essential** | 仅显示活动行 + Git 状态，最小信息干扰 |
| **Minimal** | 仅显示模型名称和上下文进度条 |

选择预设后，可单独开关每个显示元素。

### 4.3 手动配置

高级配置直接编辑配置文件：

```
~/.claude/plugins/claude-hud/config.json
```

运行 `/claude-hud:configure` 会保留手动设置，只更新布局和显示选项。

## 五、配置选项详解

### 5.1 布局配置

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `lineLayout` | string | "expanded" | 布局模式：expanded（多行）或 compact（单行） |
| `pathLevels` | 1-3 | 1 | 项目路径显示的目录层级数 |

### 5.2 Git 状态配置

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `gitStatus.enabled` | boolean | true | 是否显示 Git 分支 |
| `gitStatus.showDirty` | boolean | true | 显示未提交更改的 * 标记 |
| `gitStatus.showAheadBehind` | boolean | false | 显示与远程的 Ahead/Behind 数量 |
| `gitStatus.showFileStats` | boolean | false | 显示文件变更统计 !M +A ✘D ?U |

### 5.3 显示选项

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `display.showModel` | boolean | true | 显示模型名称 [Opus] |
| `display.showContextBar` | boolean | true | 显示上下文进度条 ████░░░░░░ |
| `display.showUsage` | boolean | true | 显示订阅用户使用量限制 |
| `display.showDuration` | boolean | false | 显示会话时长 ⏱️ 5m |
| `display.showSpeed` | boolean | false | 显示输出 token 速度 out: 42.1 tok/s |
| `display.showTools` | boolean | false | 显示工具活动行 |
| `display.showAgents` | boolean | false | 显示智能体活动行 |
| `display.showTodos` | boolean | false | 显示待办进度行 |
| `display.showMemoryUsage` | boolean | false | 显示系统内存使用（仅 expanded 布局） |

### 5.4 颜色配置

支持的颜色名称：`dim`、`red`、`green`、`yellow`、`magenta`、`cyan`、`brightBlue`、`brightMagenta`

也可使用 256 色码（0-255）或十六进制格式 `#rrggbb`。

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `colors.context` | green | 上下文进度条和百分比的基础颜色 |
| `colors.usage` | brightBlue | 使用量进度条的基础颜色 |
| `colors.warning` | yellow | 警告阈值颜色 |
| `colors.usageWarning` | brightMagenta | 接近阈值的警告色 |
| `colors.critical` | red | 达到限制的紧急色 |
| `colors.model` | cyan | 模型徽章颜色 |
| `colors.project` | yellow | 项目路径颜色 |
| `colors.git` | magenta | Git 包装文字颜色 |
| `colors.label` | dim | 标签和次要元数据颜色 |

## 六、使用指南

### 6.1 上下文健康度

上下文进度条的颜色变化提示：

- 🟢 **绿色**（0-60%）：上下文状态良好
- 🟡 **黄色**（60-85%）：需要注意，上下文即将满
- 🔴 **红色**（85%+）：上下文即将耗尽

### 6.2 工具活动监控

工具活动行显示 Claude 当前正在执行的工具：

| 工具 | 显示格式 | 说明 |
|------|----------|------|
| Read | `✓ Read ×3` | 读取了 3 个文件 |
| Edit | `✎ Edit: auth.ts` | 正在编辑 auth.ts |
| Grep | `✓ Grep ×2` | 执行了 2 次搜索 |
| Bash | `$ ls` | 执行了 shell 命令 |

### 6.3 智能体追踪

显示子智能体的运行状态：

```
◐ explore [haiku]: Finding auth code (2m 15s)
```

格式：`◐ 智能体名 [模型]: 当前任务 (运行时长)`

### 6.4 Git 状态显示

**显示级别**：

```
# 仅分支名
[Opus] │ my-project git:(main)

# 带脏标记（有待提交更改）
[Opus] │ my-project git:(main*)

# 带 Ahead/Behind
[Opus] │ my-project git:(main ↑2 ↓1)

# 带文件统计
[Opus] │ my-project git:(main* !3 +1 ?2)
```

标记说明：`!` = 已修改，`+` = 已添加/已暂存，`✘` = 已删除，`?` = 未跟踪

## 七，故障排除

### 7.1 配置不生效

1. 检查 JSON 语法是否正确，无效 JSON 会静默回退到默认配置
2. 确保使用有效值：`pathLevels` 必须为 1、2 或 3；`lineLayout` 必须为 `expanded` 或 `compact`
3. 删除配置文件后运行 `/claude-hud:configure` 重新生成

### 7.2 Git 状态不显示

1. 确认当前目录是 git 仓库
2. 检查配置中 `gitStatus.enabled` 不为 `false`

### 7.3 工具/智能体/待办行不显示

这些行默认隐藏，需要通过 `/claude-hud:configure` 启用。

### 7.4 使用量不显示

**要求**：

- 必须是 Claude 订阅用户（非仅 API key 用户）
- Claude Code 必须在 stdin 中提供 `rate_limits` 数据

**不支持的场景**：

- API key 用户（按 token 计费，无速率限制）
- AWS Bedrock 模型（使用 AWS 管理限制）
- 旧版 Claude Code（不发送 `rate_limits`）

## 八、最佳实践

### 8.1 工作流程优化

1. **关注上下文颜色**：当进度条变黄时，考虑清理上下文或开启新会话
2. **监控工具活动**：观察 Claude 是否在正确执行预期的操作
3. **追踪智能体进度**：使用子智能体时，HUD 帮助了解各任务状态

### 8.2 配置推荐

**开发者（注重信息完整性）**：

```json
{
  "lineLayout": "expanded",
  "display": {
    "showTools": true,
    "showAgents": true,
    "showTodos": true,
    "showDuration": true
  }
}
```

**简洁主义者（最小干扰）**：

```json
{
  "lineLayout": "compact",
  "pathLevels": 1,
  "gitStatus": {
    "showDirty": true,
    "showAheadBehind": false
  }
}
```

## 九、常见问题

**Q: Claude HUD 和 tmux 有什么区别？**

A: Claude HUD 是 Claude Code 的原生插件，使用 statusline API 显示信息，不需要额外的终端复用器。它专注于 Claude Code 会话状态的显示，而 tmux 是通用的终端管理工具。

**Q: 是否影响 Claude Code 性能？**

A: 几乎不影响。HUD 约 300ms 更新一次，且使用 Claude Code 原生数据流，不增加额外负担。

**Q: 支持哪些 Claude Code 版本？**

A: 支持最新版 Claude Code。某些功能（如使用量显示）需要 Claude Code 支持 `rate_limits` 数据推送。

**Q: 可以自定义颜色主题吗？**

A: 可以。支持颜色名称、256 色码和十六进制格式，可为每个显示元素单独配置颜色。

## 十、总结

Claude HUD 是 Claude Code 用户的必备插件：

- ✅ **上下文可见**：再也不用担心上下文突然耗尽
- ✅ **操作透明**：实时了解 Claude 的读写编辑行为
- ✅ **智能体追踪**：清楚掌握子任务执行状态
- ✅ **零学习成本**：安装即用，原生终端体验
- ✅ **高度可定制**：预设 + 细粒度配置，满足不同需求

无论你是日常使用 Claude Code 编程，还是进行复杂的多智能体任务，Claude HUD 都能提供清晰的视觉反馈，让 AI 编程更加高效可控。

---

**相关资源：**

- 🐙 [GitHub](https://github.com/jarrodwatts/claude-hud)
- 📺 [演示视频](https://github.com/jarrodwatts/claude-hud/blob/main/claude-hud-preview-5-2.png)
- 💬 [Discussions](https://github.com/jarrodwatts/claude-hud/discussions)