---
title: "LikeC4：用代码绘制永远最新的架构图"
date: 2026-07-24T03:08:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["Architecture", "C4 Model", "Diagram", "DSL", "DevTools"]
description: "一个受 C4 模型启发的架构即代码工具，用 DSL 描述系统结构并自动生成实时同步的可视化图表，支持自定义 нотации和任意嵌套层级。"
---

## 核心判断

LikeC4 解决的是一个所有技术团队都会遇到的痛点：**架构图永远是过时的。** 你在 Confluence 里找到的那张系统架构图，大概率是三个月前某个人用 Draw.io 画的，之后系统已经变了五次。

LikeC4 的核心判断是：架构图不应该是一个手工维护的产物，而应该是**从代码中生成的、永远与实际同步的**实时视图。它用一种专门的 DSL（Domain Specific Language）来描述架构，然后自动生成可视化图表。

## 它是什么

LikeC4 是一个架构建模语言加工具链，灵感来自 [C4 Model](https://c4model.com/) 和 [Structurizr DSL](https://github.com/structurizr/dsl)，但在两者基础上增加了灵活性：

- **自定义 нотации**：你可以定义自己的元素类型和样式，不限于 C4 的 Person/System/Container/Component 四层
- **任意嵌套层级**：不限于 C4 的四级层次结构，可以按需嵌套
- **代码驱动**：架构描述以纯文本形式存储，可以纳入 Git 版本控制

这意味着 LikeC4 不是 C4 Model 的严格实现，而是一个"C4 风格但更灵活"的架构建模工具。

## 工作方式

### 写 LikeC4 源码

LikeC4 用自己的 DSL 描述架构。你可以定义元素、关系、视图：

```likec4
model {
  user = person '用户'
  frontend = container '前端应用' {
    style {
      shape component
    }
  }
  backend = container '后端 API'
  database = container '数据库' {
    technology 'PostgreSQL'
  }
  
  user -> frontend '使用'
  frontend -> backend 'API 调用'
  backend -> database '读写'
}
```

### 实时预览

运行 CLI 工具启动本地预览服务器：

```sh
npx likec4 start
```

这会启动一个本地 Web 服务器，渲染出架构图。每次你修改 DSL 源码，图表实时更新——不需要导出、不需要截图、不需要手动同步。

### VS Code 集成

LikeC4 提供了官方 VS Code 扩展，支持语法高亮、自动补全和实时预览。对于 JetBrains 用户也有 Open VSX 版本。

## 与其他架构图工具的对比

| 工具 | 方式 | 版本控制 | 实时同步 | 自定义度 |
|------|------|---------|---------|---------|
| Draw.io / Lucidchart | 手动拖拽 | 困难 | 不支持 | 高（但无约束） |
| PlantUML | 代码生成图 | 支持 | 需重新生成 | 中 |
| Structurizr DSL | 代码生成图 | 支持 | 需重新生成 | 低（严格 C4） |
| **LikeC4** | 代码生成图 + 实时预览 | 支持 | 支持 | 高（可自定义 нотации） |

LikeC4 的差异化在于三个维度同时满足：**代码可版本控制 + 实时预览不重新生成 + 高自定义度不被 C4 框架限制**。

## 适用场景

### 微服务架构治理

当你的系统从 3 个服务增长到 30 个服务时，用 LikeC4 描述每个服务的边界、依赖和数据流。新成员加入团队时，`npx likec4 start` 就能看到完整的系统地图。

### 技术决策记录

架构变更可以通过 LikeC4 DSL 的 Git diff 来追踪——谁在什么时候改了什么依赖关系，一目了然。这比翻 Confluence 历史版本可靠得多。

### 架构评审

在架构评审会议中，LikeC4 的实时预览让讨论更高效——"如果我们在这里加一个缓存层？"直接改 DSL，所有人立刻看到效果。

## 快速上手

### 模板项目

最快的方式是使用官方模板：

```bash
# 克隆模板
gh repo create my-architecture --template likec4/template

# 或直接在 StackBlitz 中试用
# https://stackblitz.com/~/github.com/likec4/template
```

### 教程

LikeC4 官方提供了交互式 [Tutorial](https://likec4.dev/tutorial/)，可以在浏览器中跟随引导完成第一个架构模型。

### NPM 安装

```bash
npm install likec4
```

## 适用边界

**适合**：

- 中大型系统的架构文档化和持续维护
- 微服务/分布式系统的依赖关系可视化
- 需要将架构图纳入版本控制的团队
- 频繁进行架构变更并需要实时讨论的场景

**不适合**：

- 只需要画一次性图表的简单项目（Draw.io 更快）
- 需要自由绘制非标准图形的场景（LikeC4 的 нотации 有结构约束）
- 团队对 DSL 学习成本敏感的场景

## 阅读路径

- [GitHub 仓库](https://github.com/likec4/likec4) — 源码和文档
- [likec4.dev](https://likec4.dev/) — 官方文档和教程
- [在线 Playground](https://playground.likec4.dev/) — 浏览器中试用
- [模板项目](https://template.likec4.dev/view/index) — 部署示例
- [Discord 社区](https://discord.gg/86ZSpjKAdA) — 问题讨论
