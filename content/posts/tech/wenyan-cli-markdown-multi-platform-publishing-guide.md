---
title: "文颜CLI：Markdown一键发布微信公众号的多平台排版工具"
date: "2026-04-09T12:25:00+08:00"
slug: "wenyan-cli-markdown-multi-platform-publishing-guide"
description: "文颜CLI是一款多平台Markdown排版与发布工具，支持将Markdown一键转换并发布至微信公众号、知乎，今日头条等内容平台，让写作者专注内容而非排版。涵盖本地模式、Server模式、CI/CD集成和AI Agent集成等进阶用法。"
draft: false
categories: ["技术笔记"]
tags: ["Markdown", "微信公众号", "CLI工具", "内容发布", "自动化", "TypeScript"]
---

# 文颜 CLI：Markdown 一键发布微信公众号的多平台排版工具

## §1 学习目标

读完本文你会了解：

- 文颜 CLI 的核心设计理念与技术架构
- 本地模式与 Server 模式的原理与适用场景
- 多种内容输入方式与完整的 publish 工作流程
- 图片自动处理机制与 frontmatter 规范
- Server 模式 API 接口设计与认证机制
- 多公众号发布、CI/CD 集成与 AI Agent 集成
- 主题定制与代码高亮配置

## §2 问题背景

**内容创作者面临的三重困境：**

| 困境 | 具体表现 | 痛点等级 |
|------|----------|----------|
| 排版耗时 | 微信公众号不支持 Markdown，需手动排版 | ⭐⭐⭐⭐⭐ |
| 图片上传 | 手动上传图片、配置封面、处理本地/网络图片 | ⭐⭐⭐⭐ |
| 多平台适配 | 知乎、今日头条等平台格式不一 | ⭐⭐⭐ |

文颜的目标很简单：**让写作者专注内容，不用管排版和平台适配。**

## §3 核心功能

### 3.1 一键发布到多平台

文颜 CLI 支持一键发布至：

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

内置多套主题，支持自定义主题 CSS，满足不同品牌风格需求。

## §4 技术架构深度解析

### 4.1 两种运行模式对比

文颜 CLI 提供**本地模式**和**远程客户端模式**两种架构：

#### 本地模式（Local Mode）

```
┌─────────────────┐     ┌─────────────────┐
│   wenyan-cli    │────▶│   微信公众号API   │
│  (TypeScript)  │     │   (上传图片/发布) │
└─────────────────┘     └─────────────────┘
```

**特点：**
- CLI 直接调用微信公众号 API
- 适合有固定 IP 的服务器或开发者本机
- 需配置 IP 白名单

**工作流程（6 步）：**
1. 读取 Markdown 内容（文件/stdin/直接输入）
2. 解析 frontmatter（标题、封面等元数据）
3. 自动检测正文和封面中的图片
4. 上传图片到微信公众号素材库
5. 将 Markdown 渲染为微信公众号兼容 HTML
6. 创建公众号草稿，返回发布结果

#### 远程客户端模式（Client-Server Mode）

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   wenyan-cli    │────▶│  Wenyan Server   │────▶│   微信公众号API   │
│  (TypeScript)  │     │   (云服务器)     │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**特点：**
- CLI 作为客户端，将请求发送到云端 Server
- Server 完成 API 调用
- 适合无固定 IP、需团队协作、CI/CD 场景

**Server 核心架构：**
- 作为中间层承接客户端请求
- 统一处理与微信公众号 API 的交互
- 支持流式上传（10MB），安全高效
- 临时文件 10 分钟后自动回收

**适用场景：**
- ✅ 无本地固定 IP，需频繁添加 IP 白名单
- ✅ 团队协作
- ✅ CI/CD 自动发布
- ✅ AI Agent 自动发布

### 4.2 技术栈

| 组件 | 技术 | 占比 |
|------|------|------|
| 核心语言 | TypeScript | 67.6% |
| 运行时 | Node.js | - |
| 包管理 | pnpm | - |
| 代码质量 | ESLint | - |
| 部署 | Docker | - |
| 测试 | Jest | - |

## §5 快速开始

### 5.1 安装

```bash
npm install -g @wenyan-md/cli

# 验证安装
wenyan --version
```

### 5.2 配置凭据

设置环境变量：

```bash
export WECHAT_APP_ID=your_app_id
export WECHAT_APP_SECRET=your_app_secret
```

### 5.3 发布文章

**方式一：本地文件（推荐）**

```bash
wenyan publish -f article.md
```

**方式二：管道（适合 CI/CD）**

```bash
cat article.md | wenyan publish
```

**方式三：直接传入内容**

```bash
wenyan publish "# Hello Wenyan\n\n这是一篇测试文章"
```

### 5.4 Server 模式发布

```bash
wenyan publish -f article.md \
  --server https://api.example.com \
  --api-key your-api-key
```

## §6 publish 命令详解

### 6.1 完整参数说明

| 参数 | 简写 | 说明 | 必填 | 默认值 |
|------|------|------|------|---------|
| `--file` | `-f` | Markdown 文件路径 | 否¹ | - |
| `--theme` | `-t` | 排版主题 | 否 | default |
| `--highlight` | `-h` | 代码高亮主题 | 否 | solarized-light |
| `--custom-theme` | `-c` | 自定义主题 CSS（本地或 URL） | 否 | - |
| `--no-mac-style` | - | 禁用代码块 Mac 风格 | 否 | 启用 |
| `--no-footnote` | - | 禁用脚注转换 | 否 | 启用 |
| `--app-id` | - | 公众号 AppId | 否 | - |
| `--server` | - | Wenyan Server 地址 | 否 | - |
| `--api-key` | - | Server API Key | 否² | - |

> ¹ 必须满足以下之一：使用`--file`、使用 stdin、或直接传入 Markdown 内容
> 
> ² 仅在指定`--server`时生效

### 6.2 使用示例

```bash
# 使用指定主题
wenyan publish -f article.md -t lapis --highlight monokai

# 使用自定义主题
wenyan publish -f article.md --custom-theme ./my-theme.css

# 关闭附加样式
wenyan publish -f article.md --no-mac-style --no-footnote

# 使用远程Server
wenyan publish -f article.md \
  --server https://api.wenyan.dev \
  --api-key your-api-key

# 使用管道发布
cat article.md | wenyan publish

# 指定AppId发布
wenyan publish -f article.md \
  --app-id your-app-id \
  --server https://api.wenyan.dev \
  --api-key your-api-key
```

## §7 frontmatter 规范

每篇 Markdown 顶部需包含 frontmatter：

```yaml
---
title: 文章标题
cover: ./cover.jpg
author: 作者名称
source_url: https://example.com
---
```

**字段说明：**

| 字段 | 必填 | 说明 |
|------|------|------|
| `title` | ✅ | 文章标题 |
| `cover` | 否 | 封面图片，支持本地路径或网络 URL |
| `author` | 否 | 文章作者 |
| `source_url` | 否 | 原文链接 |

**自动行为：**
- 如果未指定`cover`，将自动使用正文第一张图片作为封面

## §8 图片处理机制

### 8.1 支持的图片格式

| 类型 | 示例 | 处理方式 |
|------|------|----------|
| 本地绝对路径 | `/Users/lei/image.png` | 直接读取并上传 |
| 相对路径 | `./assets/image.png` | 相对于 Markdown 文件路径读取 |
| 网络图片 | `https://example.com/image.png` | 直接上传 |

### 8.2 图片处理流程

```markdown
![](./image.png)
<img src="./image2.png" />
```

CLI 将自动：
1. 识别 Markdown 中的所有图片引用
2. 上传图片到微信素材库
3. 替换为微信公众号可访问的 URL

### 8.3 常见问题

**Q: 图片上传失败？**
A: 请检查：
- 图片路径是否正确
- 图片文件是否存在
- 图片格式是否支持（jpg、png、gif）

**Q: 发布失败：invalid ip？**
A: 当前机器 IP 未加入微信公众号白名单。解决方法：
- 使用远程 Server 模式
- 或将当前 IP 加入微信公众号后台白名单

**Q: 发布失败：invalid appid or secret？**
A: 请检查环境变量`WECHAT_APP_ID`和`WECHAT_APP_SECRET`是否正确。

## §9 Server 模式开发指南

### 9.1 快速部署

```bash
# 全局安装Wenyan CLI（包含Server功能）
npm install -g @wenyan-md/cli

# 验证安装
wenyan --version

# 基础启动（默认端口3000，无API鉴权）
wenyan serve

# 自定义端口 + 开启API鉴权（推荐生产环境）
wenyan serve --port 8080 --api-key your-secret-api-key-123456
```

### 9.2 启动参数说明

| 参数 | 简写 | 说明 | 必填 | 默认值 |
|------|------|------|------|---------|
| `--port` | - | 指定服务端口 | 否 | 3000 |
| `--api-key` | - | 设置全局 API 密钥（开启鉴权） | 否 | - |

### 9.3 环境变量设置

如果只使用一个公众号进行发布：

```bash
export WECHAT_APP_ID=xxx
export WECHAT_APP_SECRET=xxx
```

这样在调用`publish`接口时就无需传递`wechat_app_id`和`wechat_app_secret`参数。

### 9.4 API 接口设计

#### 健康检查

```bash
curl http://localhost:3000/health
```

#### 文件/图片上传接口

支持上传图片和 Markdown 文件。上传后返回`fileId`供下一步使用：

```bash
curl -X POST http://localhost:3000/upload \
  -H "x-api-key: my-secret-key" \
  -F "file=@/path/to/article.md"
```

响应示例：
```json
{
  "success": true,
  "data": {
    "fileId": "550e8400-e29b-41d4-a716-446655440000.md",
    "originalFilename": "article.md",
    "mimetype": "text/markdown",
    "size": 1024
  }
}
```

#### 远程发布接口

使用上传阶段获得的`fileId`触发服务端的排版渲染和微信发布流程：

```bash
curl -X POST http://localhost:3000/publish \
  -H "x-api-key: my-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "fileId": "550e8400-e29b-41d4-a716-446655440000.md",
    "theme": "default",
    "highlight": "solarized-light",
    "macStyle": true
  }'
```

### 9.5 API 认证机制

当服务启动时指定`--api-key`参数，所有接口（除`/health`）均需通过 API Key 认证：

1. 客户端在请求 Header 中添加`x-api-key: 你的服务端密钥`
2. 服务端验证 Header 中的密钥与启动时设置的密钥是否一致
3. 验证失败返回`401 Unauthorized`，验证通过才处理请求

## §10 多公众号发布

### 10.1 配置流程

1. 删除环境变量中的`WECHAT_APP_ID`和`WECHAT_APP_SECRET`
2. 按照文档配置多个公众号凭据
3. 发布时指定公众号：

```bash
wenyan publish -f article.md --app-id your-app-id
```

### 10.2 注意事项

- 每个公众号都需要配置 IP 白名单
- 强烈建议搭配 Server 模式使用多公众号功能

## §11 CI/CD 集成

### 11.1 GitHub Actions 示例

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
        env:
          WECHAT_APP_ID: ${{ secrets.WECHAT_APP_ID }}
          WECHAT_APP_SECRET: ${{ secrets.WECHAT_APP_SECRET }}
          
      - run: |
          cat article.md | pnpm wenyan publish
```

### 11.2 使用 Server 模式进行 CI/CD

```bash
# 在CI环境中
cat article.md | wenyan publish \
  --server https://api.wenyan.dev \
  --api-key $WENYAN_API_KEY
```

## §12 AI Agent 集成

文颜 CLI 可作为 AI Agent 的发布工具，配合 MCP 版本实现自动发布：

| 版本 | 定位 | 适用场景 |
|------|------|----------|
| [macOS App版](https://github.com/caol64/wenyan) | 桌面应用 | 日常写作 |
| [跨平台桌面版](https://github.com/caol64/wenyan-pc) | Windows/Linux | 多平台用户 |
| **CLI 版本** | 本项目 | 开发者、CI/CD |
| [MCP版本](https://github.com/caol64/wenyan-mcp) | AI 自动发文 | Agent 集成 |

### 12.1 AI Agent 工作流

```
AI写作 → 生成Markdown → wenyan publish → 微信公众号
```

## §13 主题与样式定制

### 13.1 内置主题

| 主题名称 | 说明 |
|----------|------|
| default | 默认主题 |
| lapis | 简洁主题 |

### 13.2 代码高亮主题

| 主题名称 | 说明 |
|----------|------|
| solarized-light | Solarized Light（默认） |
| monokai | Monokai |
| github | GitHub |

### 13.3 自定义主题

```bash
# 使用本地CSS文件
wenyan publish -f article.md --custom-theme ./my-theme.css

# 使用网络CSS
wenyan publish -f article.md --custom-theme https://example.com/theme.css
```

## §14 实践建议

### 14.1 本地开发流程

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

### 14.2 Server 部署建议

使用 Docker 快速部署：

```bash
# 拉取镜像
docker pull caol64/wenyan-cli

# 启动服务
docker run -d -p 3000:3000 \
  -e WECHAT_APP_ID=xxx \
  -e WECHAT_APP_SECRET=xxx \
  caol64/wenyan-cli serve
```

### 14.3 团队协作建议

1. 部署一台共享的 Wenyan Server
2. 团队成员通过`--server`参数使用
3. 使用`--api-key`进行访问控制

## §15 常见问题

| 问题 | 原因 | 解决方法 |
|------|------|----------|
| 图片上传失败 | 路径错误或格式不支持 | 检查路径和格式 |
| invalid ip | IP 未加入白名单 | 使用 Server 模式或添加白名单 |
| invalid appid or secret | 凭据配置错误 | 检查环境变量 |
| 封面自动选择错误 | 未指定 cover | 添加 frontmatter 的 cover 字段 |

## §16 总结

文颜 CLI 通过简单的命令将排版和发布流程自动化，让创作者只需专注 Markdown 写作。它解决了内容创作者的三大痛点：

- ✅ **排版自动化**：Markdown 直接转微信公众号格式
- ✅ **图片智能处理**：支持多种图片格式自动上传
- ✅ **多平台支持**：一次写作，多平台发布

**相关资源：**
- 官网：wenyan.yuzhi.tech
- NPM：@wenyan-md/cli
- Docker：caol64/wenyan-cli

---

🦞 文档版本：v2.0 | 写作日期：2026-04-09
