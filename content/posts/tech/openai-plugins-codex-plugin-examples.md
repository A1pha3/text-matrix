---
title: 'openai/plugins：Codex 插件如何打包工作流、应用连接与 MCP'
date: "2026-06-07T15:03:00+08:00"
slug: "openai-plugins-codex-plugin-examples"
description: "openai/plugins 是 Codex 插件的官方范例仓库。它展示了如何把 Skills、Apps 和 MCP 配置打包成可安装的工作流，而不只是给 Codex 加一个外部服务入口。"
draft: false
categories: ["技术笔记"]
tags: ["OpenAI", "Codex", "Plugin", "MCP", "AI Agent", "开源项目深拆"]
toc: true
---

## 核心判断

`openai/plugins` 值得看，因为它给了 Codex 插件的官方样板。

这个仓库容易被看成"Codex 的应用商店示例"。这样理解不算错，但只看到了一半。Gmail、Binance、Brex 这类插件主要解决外部服务连接；`build-ios-apps`、`build-web-apps`、`notion`、`figma` 这类插件更值得读，它们把 Agent 做事的步骤也写进了插件。

Codex plugin 打包的是三类东西：

- **Skills**：遇到某类任务时怎么做。
- **Apps**：能连接哪些外部应用。
- **MCP servers**：能调用哪些工具或上下文服务。

如果只是给当前项目加一条本地工作流，写 skill 就够了。需要跨团队分发、绑定 OAuth 应用、附带 MCP 配置时，再做 plugin。

## 插件结构

一个插件的入口是：

```text
.codex-plugin/plugin.json
```

它可以只包含 skill，也可以同时带上 App 和 MCP。

| 层 | 管什么 | 常见文件 |
|---|---|---|
| Skills | 任务流程、参考文档、脚本 | `skills/*/SKILL.md` |
| Apps | 外部应用连接和认证 | `.app.json` |
| MCP | 工具协议配置 | `.mcp.json` |
| Marketplace | 插件来源、安装和认证策略 | `.agents/plugins/marketplace.json` |

这几个部分应该分开看。Skill 写的是方法，App 写的是连接，MCP 写的是工具入口，marketplace 写的是分发策略。把这些边界弄清楚，才知道一个插件到底改变了 Codex 的哪部分行为。

## 一个任务怎么流过插件

以 `build-ios-apps` 为例。开发者让 Codex 排查 "SwiftUI 列表卡顿" 时，插件可能这样工作：

1. Codex 匹配到 `swiftui-performance-audit` skill。
2. Skill 先要求阅读 `references/code-smells.md`，从代码层面排查 broad observation、identity churn、复杂布局、主线程图片处理等问题。
3. 如果代码审查不够，再按 `references/profiling-intake.md` 收集复现步骤、设备、构建模式和 trace 证据。
4. 需要模拟器、日志或 UI 自动化时，插件通过 `.mcp.json` 启动 `xcodebuildmcp`。
5. 进入 ETTrace 分析时，再用插件里的脚本处理 dSYM 和火焰图 JSON。

这就是 plugin 比普通 prompt 强的地方：流程不再只存在于某个人的经验里，而是被放进可安装、可复用的目录结构里。团队成员装上同一个插件，拿到的是同一套步骤、参考资料和辅助脚本。

## 两类插件

仓库里的插件大致分两类。

第一类是薄壳连接器，通常只有：

```text
.app.json
.codex-plugin/plugin.json
assets/
```

它们把 SaaS 放进 Codex 的插件目录，统一 OAuth、权限提示、品牌信息和可发现性。装上之后，Codex 能访问对应服务，但不会自动获得一套新工作流。

第二类是工作流包，通常有：

```text
skills/
references/
scripts/
agents/openai.yaml
```

README 里列出的 richer examples 基本都属于这一类：`figma` 管设计稿到代码，`notion` 管计划和知识整理，`build-web-apps` 管前端、浏览器验证、Stripe 和 Supabase，`expo` 管 React Native / EAS / 发布流程，`netlify` 管部署，`remotion` 管 React 视频生成。

一个小坑：README 提到 `google-slides`，但仓库当前的插件目录是 `google-drive`，Slides 只是其中一个 skill。落地时要看实际 `plugin.json` 和目录，不要只看 README 名称。

## manifest 和 marketplace

最小的 `plugin.json` 很短：

```json
{
  "name": "my-first-plugin",
  "version": "1.0.0",
  "description": "Reusable workflow",
  "skills": "./skills/"
}
```

要挂 App 或 MCP，当前仓库更常见的写法是在 `plugin.json` 里放相对路径：

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "skills": "./skills/",
  "apps": "./.app.json",
  "mcpServers": "./.mcp.json"
}
```

具体 App 认证写在 `.app.json`，MCP server 写在 `.mcp.json`。Codex 官方文档支持本地 stdio server 和远程 streamable HTTP server，不要把旧文章里的 SSE 示例当成唯一形态。

插件做好后，还要让 Codex 找得到。仓库级目录放在 `$REPO_ROOT/.agents/plugins/marketplace.json`，个人目录放在 `~/.agents/plugins/marketplace.json`。marketplace 条目里最重要的是四个字段：

| 字段 | 作用 |
|---|---|
| `source.path` | 插件目录位置 |
| `policy.installation` | `AVAILABLE`、`INSTALLED_BY_DEFAULT` 或 `NOT_AVAILABLE` |
| `policy.authentication` | `ON_INSTALL` 或 `ON_USE` |
| `category` | 插件目录分类 |

团队可以用它做轻量治理：内部工作流默认安装，不适合组织场景的插件设为不可用，需要首次使用再授权的插件设为 `ON_USE`。

## 和其他 Agent 生态的关系

Codex 这里叫 plugin，但里面仍然有 skills。更稳妥的理解是：

- Skill 是工作流作者格式。
- Plugin 是安装和分发格式。
- MCP server 是跨 Agent 的工具协议入口。

所以，Codex plugin 不能直接等同于 Claude Code skill。`SKILL.md` 的主体内容可以迁移，但 `.codex-plugin/plugin.json`、marketplace 策略、App 连接和 Codex app 的 `interface` 元数据，都要按目标平台重写。

OpenAI 还维护了 `codex-plugin-cc`，让 Claude Code 用户在 Claude Code 里调用 Codex 做 review 或任务委派。它不属于 `openai/plugins`，但说明了一个趋势：Agent 生态的竞争，不只是谁功能更多，也是谁能进入开发者已经习惯的工作流。

## 谁该看

想写第一个 Codex 插件的人，不要从空目录开始。先 fork `openai/plugins`，选 `notion`、`build-web-apps` 或 `build-ios-apps` 这种结构清楚的插件改。

做 AI 工具产品的厂商，重点看 `figma`、`expo`、`netlify`。它们展示了产品接入 Codex 时，除了提供 API，还要把典型任务的处理方式写清楚。

需要跨平台兼容的团队，重点看 Skills 和 MCP 的分界。MCP server 可以复用，Skill 内容也能复用一部分，但触发描述、权限、UI 元数据和安装策略不能照搬。

如果只是 repo 内部的小流程，先写本地 skill。等流程稳定、需要分发给多人或绑定 App/MCP 时，再打包成 plugin。

## 阅读方式

读仓库时少停留在 README，多看每个插件下面的三类文件：`.codex-plugin/plugin.json`、`skills/*/SKILL.md`、`.mcp.json` 或 `.app.json`。这三处读完，基本就知道一个插件到底在改变 Codex 的哪一部分行为。

## 参考

- 仓库：[github.com/openai/plugins](https://github.com/openai/plugins)
- Codex 插件规范：[developers.openai.com/codex/plugins](https://developers.openai.com/codex/plugins)
- Codex 插件构建指南：[developers.openai.com/codex/plugins/build](https://developers.openai.com/codex/plugins/build)
