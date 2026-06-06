---
title: "openai/plugins：OpenAI 官方维护的 Codex 插件精选合集"
date: "2026-06-06T09:50:00+08:00"
slug: "openai-codex-plugins-curated-collection"
aliases:
  - "/posts/tech/openai-codex-plugins-curated-collection/"
description: "openai/plugins 是 OpenAI 官方维护的 Codex 插件精选合集，覆盖 Figma、Notion、iOS/macOS/Web 应用构建、Expo、Netlify、Remotion、Google Slides 等场景，每个插件以 plugin.json 清单为入口，可挂载 skills、agents、commands、hooks、MCP 等组件。"
draft: false
categories: ["技术笔记"]
tags: ["Codex", "OpenAI", "Plugin", "MCP", "AI Agent"]
---

# openai/plugins：OpenAI 官方维护的 Codex 插件精选合集

> **目标读者**：使用 OpenAI Codex 的开发者；想给 Codex 扩展 Figma/Notion/iOS/macOS/Web 等工作流能力的人
> **核心问题**：如何为 OpenAI Codex 安装官方精选的领域插件，让它能直接操作 Figma、Notion、构建 iOS/macOS/Web 应用、对接 Netlify/Remotion/Google Slides？
> **难度**：⭐⭐（即装即用）
> **来源**：GitHub [openai/plugins](https://github.com/openai/plugins)，1,546 ★ / 2026-06-06

---

## 一、核心判断

[openai/plugins](https://github.com/openai/plugins) 不是单一工具，而是 **OpenAI 官方维护的 Codex 插件精选合集（curated collection）**。它把已经在生产场景中被验证过的 Codex 插件集中托管，**省去你自己写 plugin.json 和挂载 skills 的工作**。

每个插件对应一个真实工作流：

- **Figma** — `use_figma`、Code to Canvas、Code Connect、设计系统规则
- **Notion** — 计划、研究、会议、知识捕获
- **build-ios-apps** — SwiftUI 实现、重构、性能调优、调试
- **build-macos-apps** — macOS SwiftUI/AppKit 工作流、build/run/debug 循环、打包
- **build-web-apps** — 部署、UI、支付、数据库工作流
- **expo** — Expo & React Native 应用、SDK 升级、EAS 工作流、Codex Run actions
- **netlify / remotion / google-slides** — 公共 skill- + MCP-backed 插件

---

## 二、关键数据

| 指标 | 数值 |
|------|------|
| Stars | 1,546 |
| Forks | 243 |
| License | 未指定（需查证后再商用） |
| 主语言 | JavaScript（plugin manifests） |
| 创建时间 | 2026-03-04 |
| 最近推送 | 2026-06-06（持续维护） |
| 收录插件 | 9 个（figma / notion / build-ios-apps / build-macos-apps / build-web-apps / expo / netlify / remotion / google-slides） |
| 维护方 | openai 组织（OpenAI 官方） |

---

## 三、Codex 插件结构

每个插件都按统一目录结构组织：

```
plugins/<name>/
├── .codex-plugin/
│   └── plugin.json     # 必需：插件清单
├── skills/             # 可选：技能集合（Markdown 描述 + 脚本）
├── .app.json           # 可选：app 元数据
├── .mcp.json           # 可选：MCP server 配置
├── agents/             # 可选：插件级 subagents
├── commands/           # 可选：斜杠命令
├── hooks.json          # 可选：生命周期钩子
└── assets/             # 可选：静态资源
```

**核心入口是 `plugin.json` 清单**——它声明插件的名字、版本、依赖、入口。其它目录都是可选的"扩展面"。

### 3.1 plugin.json 是什么

`plugin.json` 是 Codex 识别插件的**唯一入口**。它告诉 Codex：

- 这个插件叫什么
- 暴露哪些 skills / agents / commands / hooks
- 需要哪些 MCP server
- 依赖哪些 npm/pip 包

**没有 plugin.json，Codex 不会把这个目录当作插件**。

### 3.2 可选扩展面一览

| 扩展面 | 作用 | 典型用途 |
|--------|------|----------|
| `skills/` | Markdown 描述的技能（带可选 scripts/） | "读 figma 设计稿" → 调用 Figma API |
| `agents/` | 插件级 subagent | 把"iOS SwiftUI 工程师"作为子 agent 调度 |
| `commands/` | 斜杠命令 | `/figma-export` 一键导出 Figma 资源 |
| `hooks.json` | 生命周期钩子 | "Codex 启动时自动 sync Figma 文件" |
| `.mcp.json` | MCP server 配置 | 挂载 Figma MCP / Notion MCP 等 |
| `.app.json` | app 元数据 | 插件显示名称、图标、分类 |
| `assets/` | 静态资源 | logo、icon、模板文件 |

---

## 四、精选插件矩阵

| 插件 | 主要能力 | MCP 依赖 | 适合谁 |
|------|---------|---------|--------|
| **figma** | `use_figma`、Code to Canvas、Code Connect、设计系统规则 | Figma MCP | 前端/全栈：要落地设计稿的 |
| **notion** | 计划、研究、会议、知识捕获 | Notion MCP | PM/研究：要在 Notion 沉淀工作流的 |
| **build-ios-apps** | SwiftUI 实现、重构、性能调优、调试 | — | iOS 工程师 |
| **build-macos-apps** | macOS SwiftUI/AppKit 工作流、build/run/debug 循环、打包 | — | macOS 工程师 |
| **build-web-apps** | 部署、UI、支付、数据库工作流 | — | Web 全栈 |
| **expo** | Expo/React Native 应用、SDK 升级、EAS、Codex Run actions | — | RN/Expo 工程师 |
| **netlify** | Netlify 部署、Functions、表单 | Netlify MCP | 静态站/边缘函数开发者 |
| **remotion** | 用 React 写视频 | — | 内容创作/视频自动化 |
| **google-slides** | 自动化生成 Google Slides | Google Slides API | 商务/营销自动化 |

> 📌 这些都是 **OpenAI 自己选过的"生产级"插件**——不是个人作品，质量有保证。

---

## 五、典型使用场景

### 5.1 落地 Figma 设计稿

装上 `plugins/figma` 后，Codex 能：

- 用 `use_figma` skill 直接拉取 Figma 文件的组件树
- 应用 **Code Connect** 把 Figma 组件映射到代码库里的真实组件
- 执行 **Code to Canvas** 把设计稿转成可运行的代码骨架

```
codex: "根据 Figma 这个设计稿 [链接] 生成对应的 React 组件"
```

### 5.2 在 Notion 沉淀会议纪要

装上 `plugins/notion` 后：

```
codex: "把刚才的会议内容整理成 Notion 页面，放在 [某 database]"
```

Codex 会自动调用 Notion MCP 创建页面、填字段、加标签。

### 5.3 iOS / macOS 应用开发

`build-ios-apps` 和 `build-macos-apps` 是两个独立插件，分别针对：

- **iOS**：SwiftUI 实现、性能调优、调试
- **macOS**：SwiftUI/AppKit 工作流、build/run/debug 循环、打包

它们都内嵌了 **lifecycle knowledge**——Codex 知道 iOS/macOS 工程的目录约定、build 工具、常见坑点。

### 5.4 Expo / React Native

`plugins/expo` 覆盖：

- Expo SDK 升级（从 51 → 52 → 53 等）
- EAS Build / Submit 工作流
- Codex Run actions（在 EAS 云端跑 Codex 任务）

### 5.5 Remotion：React 写视频

Remotion 是用 React 组件声明式生成视频的框架。`plugins/remotion` 让 Codex 能直接写 `.tsx` 视频文件、调整时长、加字幕、加转场。

### 5.6 Netlify 部署

`plugins/netlify` 提供 Netlify Functions、表单、Edge Functions 的脚手架，Codex 写完代码能直接部署。

---

## 六、典型 plugin.json 解读

虽然 README 完整 plugin.json 没贴，但根据 OpenAI 通用插件规范，典型结构是：

```json
{
  "name": "figma",
  "version": "1.0.0",
  "description": "Figma design system integration",
  "skills": [
    "use_figma",
    "code_to_canvas",
    "code_connect"
  ],
  "mcp_servers": [
    {
      "name": "figma",
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "figma-mcp"]
    }
  ],
  "agents": [
    {
      "name": "figma-reviewer",
      "instructions": "You are a Figma design reviewer."
    }
  ],
  "commands": [
    {
      "name": "figma-export",
      "description": "Export Figma assets to local directory"
    }
  ]
}
```

**核心是 skills + mcp_servers**。其它都是锦上添花。

---

## 七、为什么值得用

1. **官方维护，质量有底**：OpenAI 自己在用，自己在维护
2. **即装即用**：不需要自己写 plugin.json，直接克隆对应子目录就行
3. **覆盖广**：9 个插件覆盖 Figma/Notion/iOS/macOS/Web/RN/Netlify/Remotion/Google Slides
4. **节省学习成本**：每个插件都内嵌了对应领域的 lifecycle knowledge

---

## 八、风险与未知

| 风险 | 说明 |
|------|------|
| **License 未指定** | 仓库根目录没看到 LICENSE 文件，**商用前必须确认**（plugin.json 里的组件可能各自有 license） |
| **依赖 MCP 第三方** | 很多插件依赖外部 MCP server（图、Notion、Netlify、Google Slides），这些 server 的稳定性直接影响 Codex 体验 |
| **生态较新** | Codex 插件生态 2026 年才起步，规范还在迭代，可能有 breaking change |
| **部分功能需要凭证** | 任何接外部 API 的插件（Figma、Notion、Netlify、Google Slides）都需要 OAuth/API Key |

---

## 九、适用边界

### 9.1 适合

- 已经在用 OpenAI Codex 的人
- 想把 Codex 接到 Figma/Notion 等现有工具链的团队
- iOS/macOS/Web/Expo 应用开发者，希望 Codex 知道对应 lifecycle
- 自动化视频/演示文稿生成（Remotion / Google Slides）

### 9.2 不适合

- **不用 Codex 的人**——这套插件就是给 Codex 用的
- **完全自研 UI 工具链**——如果你的团队有自己内部的"插件规范"，迁移成本不划算
- **需要严格 license 审查的商用项目**——仓库根目录没看到 LICENSE，落地前必须法务确认

---

## 十、和同类项目的关系

| 项目 | 维护方 | 范围 | 关系 |
|------|--------|------|------|
| **openai/plugins** | OpenAI | Codex 插件精选 | 官方集合，参考实现 |
| 各插件对应 MCP server | 社区 | 单个能力（如 Figma MCP） | 提供底层能力，openai/plugins 调用 |
| 各种自研 plugin | 个人/团队 | 各自领域 | openai/plugins 收集"被验证过"的 |

**一句话定位**：**这是 Codex 插件生态的"应用商店精选区"**。

---

## 十一、快速开始

```bash
# 1. 安装 Codex CLI（假设已装）
# 2. 克隆 openai/plugins
git clone https://github.com/openai/plugins ~/.codex/plugins

# 3. 让 Codex 加载某个插件
codex plugin install figma
codex plugin install notion
codex plugin install expo
```

> ⚠️ 具体安装方式以 Codex CLI 文档为准（plugin install 是 Codex 当前的设计目标语法）

装完后，Codex 自动识别这些插件的能力。

---

## 十二、相关链接

- [openai/plugins 仓库](https://github.com/openai/plugins)
- [OpenAI Codex 文档](https://platform.openai.com/docs/codex)
- [Anthropic 的等价物：Claude Code Plugins](https://docs.claude.com/en/docs/claude-code/plugins)
- [Figma MCP](https://www.figma.com/developers/mcp)
- [Notion MCP](https://developers.notion.com/docs/mcp)
- [Remotion](https://www.remotion.dev/)
- [Expo](https://expo.dev/)

---

> **最后更新**：2026-06-06
> **许可证**：未指定（请在商用前确认每个子插件的 license）
> **仓库**：[openai/plugins](https://github.com/openai/plugins)
