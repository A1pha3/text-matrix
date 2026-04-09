---
title: "文颜CLI：Markdown一键发布微信公众号的多平台排版工具"
date: 2026-04-09T12:20:00+08:00
slug: "wenyan-cli-markdown-multi-platform-publishing-guide"
description: "文颜CLI是一款多平台Markdown排版与发布工具，支持将Markdown一键转换并发布至微信公众号、知乎、今日头条等内容平台，让写作者专注内容而非排版。"
draft: false
categories: ["技术笔记"]
tags: ["Markdown", "微信公众号", "CLI工具", "内容发布", "自动化"]
---

# 文颜CLI：Markdown一键发布微信公众号的多平台排版工具

## §1 学习目标

通过本文，你将掌握：
- 文颜CLI的核心设计理念与使用方法
- 本地模式与Server模式的架构差异与适用场景
- 多种内容输入方式（本地路径、URL、参数、管道）
- 多公众号发布与CI/CD集成
- AI Agent自动发布集成方案

## §2 背景与痛点

**内容创作者面临的三重困境：**

| 困境 | 具体表现 | 痛点等级 |
|------|----------|----------|
| 排版耗时 | 微信公众号不支持Markdown，需手动排版 | ⭐⭐⭐⭐⭐ |
| 图片上传 | 手动上传图片、配置封面、处理本地/网络图片 | ⭐⭐⭐⭐ |
| 多平台适配 | 知乎、今日头条等平台格式不一 | ⭐⭐⭐ |

文颜的目标很简单：**让写作者专注内容，而不是排版和平台适配。**

## §3 核心功能

### 3.1 一键发布到多平台

文颜CLI支持一键发布至：

- **微信公众号**（核心功能）
- **知乎**
- **今日头条**
- 以及其他内容平台（持续扩展中）

### 3.2 智能图片处理

文颜能自动处理以下所有图片格式：

| 图片类型 | 示例 | 支持情况 |
|----------|------|----------|
| 本地绝对路径 | `/Users/xxx/image.jpg` | ✅ |
| 网络路径 | `https://example.com/image.jpg` | ✅ |
| 相对路径 | `./assets/image.png` | ✅（仅本地模式） |

### 3.3 精美排版主题

内置多套主题，支持自定义，满足不同品牌风格需求。

## §4 技术架构

### 4.1 两种运行模式对比

文颜CLI提供**本地模式**和**远程客户端模式**两种架构：

#### 本地模式（Local Mode）

```
┌─────────────────┐     ┌─────────────────┐
│   wenyan-cli    │────▶│   微信公众号API   │
│  (TypeScript)  │     │   (上传图片/发布) │
└─────────────────┘     └─────────────────┘
```

**特点：**
- CLI直接调用微信公众号API
- 适合有固定IP的服务器或开发者本机
- 需配置IP白名单

#### 远程客户端模式（Client-Server Mode）

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   wenyan-cli    │────▶│  Wenyan Server   │────▶│   微信公众号API   │
│  (TypeScript)  │     │   (云服务器)     │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**特点：**
- CLI作为客户端，将请求发送到云端Server
- Server完成API调用
- 适合无固定IP、需团队协作、CI/CD场景

**适用场景：**
- ✅ 无本地固定IP，需频繁添加IP白名单
- ✅ 团队协作
- ✅ CI/CD自动发布
- ✅ AI Agent自动发布

### 4.2 技术栈

| 组件 | 技术 | 占比 |
|------|------|------|
| 核心语言 | TypeScript | 67.6% |
| 运行时 | Node.js | - |
| 包管理 | pnpm | - |
| 代码质量 | ESLint | - |
| 部署 | Docker | - |

## §5 快速开始

### 5.1 安装

```bash
npm install -g @wenyan-md/cli
```

### 5.2 配置凭据

设置环境变量：

```bash
export WECHAT_APP_ID=your_app_id
export WECHAT_APP_SECRET=your_app_secret
```

### 5.3 发布文章

**方式一：本地路径（推荐）**

```bash
wenyan publish -f article.md
```

**方式二：URL**

```bash
wenyan publish -f http://example.com/article.md
```

**方式三：直接传入内容**

```bash
wenyan publish "# 文章标题"
```

**方式四：管道（适合CI/CD）**

```bash
cat article.md | wenyan publish
```

### 5.4 Server模式发布

```bash
wenyan publish -f article.md \
  --server https://api.example.com \
  --api-key your-api-key
```

## §6 命令详解

| 命令 | 说明 | 文档 |
|------|------|------|
| `publish` | 发布文章 | [publish.md](https://github.com/caol64/wenyan-cli/blob/main/docs/publish.md) |
| `render` | 渲染HTML | - |
| `theme` | 管理主题 | [theme.md](https://github.com/caol64/wenyan-cli/blob/main/docs/theme.md) |
| `credential` | 配置公众号凭据 | [credential.md](https://github.com/caol64/wenyan-cli/blob/main/docs/credential.md) |
| `serve` | 启动Server | [server.md](https://github.com/caol64/wenyan-cli/blob/main/docs/server.md) |

## §7 文章格式规范

每篇Markdown顶部需包含frontmatter：

```yaml
---
title: 在本地跑一个大语言模型(2)
cover: /Users/xxx/image.jpg
author: 作者名
source_url: http://example.com/original
---
```

**字段说明：**

| 字段 | 必填 | 说明 |
|------|------|------|
| `title` | ✅ | 文章标题 |
| `cover` | 否 | 封面图片，支持本地路径或网络URL |
| `author` | 否 | 文章作者 |
| `source_url` | 否 | 原文地址 |

## §8 多公众号发布

### 8.1 配置流程

1. 删除环境变量中的`WECHAT_APP_ID`和`WECHAT_APP_SECRET`
2. 按照[文档](https://github.com/caol64/wenyan-cli/blob/main/docs/credential.md)配置多个公众号凭据
3. 发布时指定公众号：

```bash
wenyan publish -f article.md --app-id your-app-id
```

### 8.2 注意事项

- 每个公众号都需要配置IP白名单
- 强烈建议搭配Server模式使用多公众号功能

## §9 CI/CD集成

### 9.1 GitHub Actions示例

```yaml
name: Publish to WeChat
on:
  push:
    branches:
      - main

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
        with:
          version: 8
      - run: pnpm install
      - env:
          WECHAT_APP_ID: ${{ secrets.WECHAT_APP_ID }}
          WECHAT_APP_SECRET: ${{ secrets.WECHAT_APP_SECRET }}
      - run: |
          cat article.md | pnpm wenyan publish
```

## §10 AI Agent集成

文颜CLI可作为AI Agent的发布工具，配合MCP版本实现自动发布：

| 版本 | 定位 | 适用场景 |
|------|------|----------|
| [macOS App版](https://github.com/caol64/wenyan) | 桌面应用 | 日常写作 |
| [跨平台桌面版](https://github.com/caol64/wenyan-pc) | Windows/Linux | 多平台用户 |
| **CLI版本** | 本项目 | 开发者、CI/CD |
| [MCP版本](https://github.com/caol64/wenyan-mcp) | AI自动发文 | Agent集成 |

## §11 最佳实践

### 11.1 本地开发流程

```bash
# 1. 安装CLI
npm install -g @wenyan-md/cli

# 2. 配置凭据
wenyan credential

# 3. 写作（使用Markdown）
vim article.md

# 4. 本地预览
wenyan render -f article.md

# 5. 发布到公众号
wenyan publish -f article.md
```

### 11.2 Server部署建议

使用Docker快速部署：

```bash
docker pull caol64/wenyan-cli
docker run -d -p 3000:3000 \
  -e WECHAT_APP_ID=xxx \
  -e WECHAT_APP_SECRET=xxx \
  caol64/wenyan-cli serve
```

## §12 常见问题

**Q: IP白名单配置失败？**
A: 确保运行CLI的机器IP已加入微信公众号后台的IP白名单，参考[配置文档](https://yuzhi.tech/docs/wenyan/upload)。

**Q: 图片上传失败？**
A: 检查frontmatter中的图片路径是否正确，本地模式支持绝对路径和相对路径，远程模式建议使用网络URL。

**Q: 多公众号如何切换？**
A: 使用`--app-id`参数指定目标公众号，或配置Server端多个凭据。

## §13 总结

文颜CLI通过简单的命令将复杂的排版和发布流程自动化，让创作者只需专注Markdown写作。它解决了内容创作者的三大痛点：

- ✅ **排版自动化**：Markdown直接转微信公众号格式
- ✅ **图片智能处理**：支持多种图片格式自动上传
- ✅ **多平台支持**：一次写作，多平台发布

**相关资源：**
- 官网：wenyan.yuzhi.tech
- NPM：@wenyan-md/cli
- Docker：caol64/wenyan-cli

---

🦞 文档版本：v2.0 | 写作日期：2026-04-09
