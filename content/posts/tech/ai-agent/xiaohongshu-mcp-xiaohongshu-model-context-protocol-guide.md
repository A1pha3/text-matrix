---
title: "xiaohongshu-mcp：小红书 MCP 服务完全指南"
slug: "xiaohongshu-mcp-xiaohongshu-model-context-protocol-guide"
aliases:
  - /posts/tech/xiaohongshu-mcp-xiaohongshu-model-context-protocol-guide/
date: 2026-03-31T17:05:00+08:00
categories: ["技术笔记"]
tags: ["xiaohongshu-mcp", "MCP", "小红书", "AI助手", "Claude Code", "Cursor", "OpenClaw", "自动化运营", "社交媒体"]
description: "全面解析 xiaohongshu-mcp (12.4k Stars)：小红书Model Context Protocol服务，让AI助手直接发布内容、搜索、评论、点赞、收藏，支持Claude Code/Cursor/OpenClaw等多种客户端。"
---

# xiaohongshu-mcp：小红书 MCP 服务完全指南

## §1 学习目标

完成本文档后，你将能够：

- ✅ 理解 xiaohongshu-mcp 的核心定位与设计理念
- ✅ 掌握 xiaohongshu-mcp 的完整功能体系
- ✅ 熟练部署 xiaohongshu-mcp（Binary/Docker/源码）
- ✅ 配置多客户端接入（Claude Code/Cursor/Cline/OpenClaw）
- ✅ 使用 MCP 工具发布小红书内容（图文/视频）
- ✅ 使用搜索和内容获取功能
- ✅ 进行评论互动（发表评论/回复评论/点赞/收藏）
- ✅ 排查常见问题
- ✅ 为 xiaohongshu-mcp 贡献代码

---

## §2 项目概述

### 2.1 什么是 xiaohongshu-mcp？

**xiaohongshu-mcp**（官方仓库：[xpzouying/xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp)）是一个基于 **Model Context Protocol (MCP)** 的小红书服务端实现，让你的 AI 助手直接访问小红书数据。

**官方描述**：

> MCP for 小红书 / xiaohongshu.com。让你的 AI 助手直接访问小红书数据。

**翻译**：xiaohongshu-mcp 是一个 MCP 协议服务端，用于小红书平台。它允许 AI 助手（如 Claude Code、Cursor 等）直接操作用户的小红书账号，包括发布内容、搜索、评论、获取用户信息等功能。

### 2.2 核心价值主张

| 价值 | 说明 |
|------|------|
| **AI 驱动** | 让 AI 助手直接操作用户小红书账号 |
| **MCP 协议** | 标准化接口，支持多种 AI 客户端 |
| **全功能** | 发布图文/视频、搜索、评论、点赞、收藏等 |
| **多客户端** | Claude Code/Cursor/Cline/OpenClaw 等 |
| **开源透明** | 代码开源，慈善捐赠模式 |
| **活跃社区** | 微信群 20+ 群、飞书群 4 个、33 位贡献者 |

### 2.3 核心数据

```
Stars:     12,400 (12.4k)
Forks:     1,900 (1.9k)
Watchers:  33
贡献者:    33 人
提交数:   340+ 次
发布版本:  90 个
最新版本:  v2026.03.09.0605-0e16f4b (2026-03-09)
语言:     Go 71.3%, Python 27.5%
```

### 2.4 项目定位

xiaohongshu-mcp 填补了 AI 助手与小红书平台之间的Gap。通过 MCP 协议，AI 助手可以像人类一样操作小红书账号，实现自动化运营、内容发布、社群互动等功能。

---

## §3 核心功能详解

### 3.1 内容发布

#### 3.1.1 发布图文

`publish_content` 工具用于发布图文内容到小红书：

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `title` | string | ✅ | 标题（不超过 20 字） |
| `content` | string | ✅ | 正文（不超过 1000 字） |
| `images` | string[] | ✅ | 图片路径列表（至少 1 张），支持 HTTP 链接或本地绝对路径 |
| `tags` | string[] | 可选 | 话题标签列表，如 `["美食", "旅行"]` |
| `schedule_at` | string | 可选 | 定时发布时间，ISO8601 格式，支持 1 小时至 14 天内 |
| `is_original` | boolean | 可选 | 是否声明原创，默认 false |
| `visibility` | string | 可选 | 可见范围：`公开可见`（默认）/ `仅自己可见` / `仅互关好友可见` |
| `products` | string[] | 可选 | 商品关键词列表，用于绑定带货商品 |

#### 3.1.2 发布视频

`publish_with_video` 工具用于发布视频内容：

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `title` | string | ✅ | 标题 |
| `content` | string | ✅ | 正文 |
| `video` | string | ✅ | 本地视频文件绝对路径（仅支持单个视频文件） |
| `tags` | string[] | 可选 | 话题标签列表 |
| `schedule_at` | string | 可选 | 定时发布时间 |
| `visibility` | string | 可选 | 可见范围 |
| `products` | string[] | 可选 | 商品关键词列表 |

### 3.2 登录与认证

#### 3.2.1 检查登录状态

`check_login_status` 用于检查当前小红书账号的登录状态（无参数）。

#### 3.2.2 获取登录二维码

`get_login_qrcode` 用于获取登录二维码，返回 Base64 图片和超时时间（无参数）。

#### 3.2.3 删除 Cookies

`delete_cookies` 用于删除 cookies 文件，重置登录状态，删除后需要重新登录（无参数）。

**⚠️ 重要提示**：
- 小红书同一账号不允许在多个网页端登录
- 登录 MCP 后，不要在其它网页端登录该账号，否则会被"踢出登录"
- 可以使用移动 App 端查看账号信息

### 3.3 内容获取

#### 3.3.1 获取首页推荐

`list_feeds` 用于获取小红书首页推荐列表（无参数）。

#### 3.3.2 搜索内容

`search_feeds` 用于搜索小红书内容：

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `keyword` | string | ✅ | 搜索关键词 |
| `filters.sort_by` | string | 可选 | 排序依据：`综合`（默认）/ `最新` / `最多点赞` / `最多评论` / `最多收藏` |
| `filters.note_type` | string | 可选 | 笔记类型：`不限`（默认）/ `视频` / `图文` |
| `filters.publish_time` | string | 可选 | 发布时间：`不限`（默认）/ `一天内` / `一周内` / `半年内` |
| `filters.search_scope` | string | 可选 | 搜索范围：`不限`（默认）/ `已看过` / `未看过` / `已关注` |
| `filters.location` | string | 可选 | 位置距离：`不限`（默认）/ `同城` / `附近` |

#### 3.3.3 获取帖子详情

`get_feed_detail` 用于获取帖子详情：

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `feed_id` | string | ✅ | 帖子 ID |
| `xsec_token` | string | ✅ | 安全令牌 |
| `load_all_comments` | boolean | 可选 | 是否加载全部评论，默认 false 仅返回前 10 条一级评论 |
| `limit` | number | 可选 | 限制加载的一级评论数量，默认 20 |
| `click_more_replies` | boolean | 可选 | 是否展开二级回复，默认 false |
| `reply_limit` | number | 可选 | 跳过回复数过多的评论阈值，默认 10 |
| `scroll_speed` | string | 可选 | 滚动速度：`slow` / `normal` / `fast` |

### 3.4 评论互动

#### 3.4.1 发表评论

`post_comment_to_feed` 用于发表评论到小红书帖子：

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `feed_id` | string | ✅ | 帖子 ID |
| `xsec_token` | string | ✅ | 安全令牌 |
| `content` | string | ✅ | 评论内容 |

#### 3.4.2 回复评论

`reply_comment_in_feed` 用于回复帖子下的指定评论：

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `feed_id` | string | ✅ | 帖子 ID |
| `xsec_token` | string | ✅ | 安全令牌 |
| `content` | string | ✅ | 回复内容 |
| `comment_id` 或 `user_id` | string | ✅ | 评论 ID 或用户 ID（至少提供一个） |

### 3.5 点赞与收藏

#### 3.5.1 点赞

`like_feed` 用于点赞或取消点赞：

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `feed_id` | string | ✅ | 帖子 ID |
| `xsec_token` | string | ✅ | 安全令牌 |
| `unlike` | boolean | 可选 | true 为取消点赞，默认为点赞 |

#### 3.5.2 收藏

`favorite_feed` 用于收藏或取消收藏：

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `feed_id` | string | ✅ | 帖子 ID |
| `xsec_token` | string | ✅ | 安全令牌 |
| `unfavorite` | boolean | 可选 | true 为取消收藏，默认为收藏 |

### 3.6 用户信息

`user_profile` 用于获取用户个人主页信息：

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `user_id` | string | ✅ | 用户 ID |
| `xsec_token` | string | ✅ | 安全令牌 |

---

## §4 安装与部署

### 4.1 方案 A：下载预编译二进制文件（推荐）

#### 4.1.1 下载程序

从 [GitHub Releases](https://github.com/xpzouying/xiaohongshu-mcp/releases) 下载对应平台的二进制文件：

**MCP 主程序：**

| 平台 | 文件名 |
|------|--------|
| macOS Apple Silicon | `xiaohongshu-mcp-darwin-arm64` |
| macOS Intel | `xiaohongshu-mcp-darwin-amd64` |
| Windows x64 | `xiaohongshu-mcp-windows-amd64.exe` |
| Linux x64 | `xiaohongshu-mcp-linux-amd64` |

**登录工具：**

| 平台 | 文件名 |
|------|--------|
| macOS Apple Silicon | `xiaohongshu-login-darwin-arm64` |
| macOS Intel | `xiaohongshu-login-darwin-amd64` |
| Windows x64 | `xiaohongshu-login-windows-amd64.exe` |
| Linux x64 | `xiaohongshu-login-linux-amd64` |

#### 4.1.2 安装步骤

```bash
# 1. 赋予执行权限
chmod +x xiaohongshu-mcp-darwin-arm64
chmod +x xiaohongshu-login-darwin-arm64

# 2. 运行登录工具
./xiaohongshu-login-darwin-arm64

# 3. 启动 MCP 服务（无头模式，无浏览器界面）
./xiaohongshu-mcp-darwin-arm64

# 4. 或者启动 MCP 服务（非无头模式，有浏览器界面）
./xiaohongshu-mcp-darwin-arm64 -headless=false
```

**⚠️ 重要提示**：首次运行时会自动下载无头浏览器（约 150MB），请确保网络连接正常。

#### 4.1.3 配置代理（可选）

如果需要通过代理访问小红书，可以设置 `XHS_PROXY` 环境变量：

```bash
# 设置代理后启动
XHS_PROXY=http://user:pass@proxy:port ./xiaohongshu-mcp-darwin-arm64

# 支持 HTTP/HTTPS/SOCKS5 代理
# 日志中会自动隐藏代理的认证信息
```

### 4.2 方案 B：源码编译

```bash
# 克隆仓库
git clone https://github.com/xpzouying/xiaohongshu-mcp.git
cd xiaohongshu-mcp

# 编译 MCP 主程序
go build -o xiaohongshu-mcp .

# 编译登录工具
go build -o xiaohongshu-login ./cmd/login

# 运行登录
./xiaohongshu-login

# 运行 MCP 服务
./xiaohongshu-mcp
```

### 4.3 方案 C：Docker 部署（最简单）

```bash
# 拉取镜像
docker pull xpzouying/xiaohongshu-mcp:latest

# 运行容器
docker run -d \
  --name xiaohongshu-mcp \
  -p 18060:18060 \
  xpzouying/xiaohongshu-mcp:latest

# 非无头模式
docker run -d \
  --name xiaohongshu-mcp \
  -p 18060:18060 \
  xpzouying/xiaohongshu-mcp:latest \
  -headless=false
```

**⚠️ Docker 环境提示**：在 Docker 环境下，请使用 `http://host.docker.internal:18060/mcp` 而非 `http://localhost:18060/mcp`。

### 4.4 方案 D：OpenClaw 深度集成

对于已部署本项目的用户，可以使用 OpenClaw 集成：

| 版本 | 仓库 | 说明 |
|------|------|------|
| xiaohongshu-mcp-skills | [autoclaw-cc/xiaohongshu-mcp-skills](https://github.com/autoclaw-cc/xiaohongshu-mcp-skills) | 适用于已部署完本项目的用户 |
| xiaohongshu-skills | [autoclaw-cc/xiaohongshu-skills](https://github.com/autoclaw-cc/xiaohongshu-skills) | 开箱即用版 |

---

## §5 客户端接入

### 5.1 Claude Code CLI 接入

```bash
# 添加 HTTP MCP 服务器
claude mcp add --transport http xiaohongshu-mcp http://localhost:18060/mcp

# 检查 MCP 是否添加成功
claude mcp list
```

### 5.2 Cursor 接入

参考 [.cursor](https://github.com/xpzouying/xiaohongshu-mcp/tree/main/.cursor) 目录配置。

### 5.3 Cline 接入

在 Cline 设置中添加 MCP 服务器配置。

### 5.4 验证 MCP 连接

使用 MCP Inspector 验证连接：

```bash
npx @modelcontextprotocol/inspector
```

打开 Inspector 后，配置 MCP endpoint 为 `http://localhost:18060/mcp`，点击 Connect，然后点击 List Tools 查看所有可用工具。

### 5.5 支持的客户端一览

| 客户端 | 支持情况 | 说明 |
|--------|----------|------|
| Claude Code CLI | ✅ 官方推荐 | 最稳定 |
| Cursor | ✅ 支持 | MCP Streamable HTTP |
| Cline | ✅ 支持 | MCP 协议 |
| OpenClaw | ✅ 支持 | 深度集成 |
| n8n | ✅ 社区教程 | 工作流自动化 |
| Cherry Studio | ✅ 社区教程 | AI 客户端 |
| AnythingLLM | ✅ 社区教程 | 多模态 AI |
| Kimi K2 | ✅ 社区教程 | Claude Code 门槛太高时的替代 |

---

## §6 使用示例

### 6.1 使用 Claude Code 发布图文

**示例 1：使用 HTTP 图片链接**

```
帮我写一篇帖子发布到小红书上，配图为：https://cn.bing.com/th?id=OHR.MaoriRock_EN-US6499689741_UHD.jpg&w=3840
图片是："纽西兰陶波湖的Ngātoroirangi矿湾毛利岩雕（© Joppi Getty Images）"
使用 xiaohongshu-mcp 进行发布。
```

**示例 2：使用本地图片路径（推荐）**

```
帮我写一篇关于春天的帖子发布到小红书上，使用这些本地图片：
- /Users/username/Pictures/spring_flowers.jpg
- /Users/username/Pictures/cherry_blossom.jpg
使用 xiaohongshu-mcp 进行发布。
```

### 6.2 使用 Claude Code 发布视频

```
帮我写一篇关于美食制作的视频发布到小红书上，使用这个本地视频文件：
- /Users/username/Videos/cooking_tutorial.mp4
使用 xiaohongshu-mcp 的视频发布功能。
```

### 6.3 搜索小红书内容

```
帮我搜索一下最近关于 AI 写作的小红书帖子，看看有哪些热门内容。
```

### 6.4 评论互动

```
帮我给我刚发布的那篇小红书帖子添加一条评论："写得真好，收藏了！"
```

---

## §7 小红书运营须知

### 7.1 内容规范

| 项目 | 要求 |
|------|------|
| **标题** | 不超过 20 个字 |
| **正文** | 不超过 1000 个字 |
| **配图** | 从推荐角度看，图文的流量比视频和纯文字更好 |
| **Tags** | 添加合适的 Tags 能带来更多流量 |
| **每日发帖** | 建议每天 50 篇以内 |

### 7.2 风险说明

1. **账号安全**：项目原作者的账号稳定运行一年多，没有出现过封号，只有 Cookies 过期需要重新登录的情况

2. **实名认证**：如果账号没有实名认证，特别是新号，一般会触发实名认证的消息提醒（不是封号）

3. **违禁词**：曝光低的话，首先检查内容是否有违禁词

4. **引流限制**：一定不要出现引流、纯搬运的情况，属于官方重点打击对象

5. **多设备登录**：小红书同一账号不允许在多个网页端登录，登录 MCP 后会被踢出

---

## §8 项目结构

### 8.1 目录结构

| 目录 | 说明 |
|------|------|
| `.cursor` | Cursor IDE 配置 |
| `.github` | GitHub 配置 |
| `.vscode` | VS Code 配置 |
| `assets` | 资源文件（截图、演示） |
| `browser` | 无头浏览器相关代码 |
| `cmd/login` | 登录工具源码 |
| `configs` | 配置文件 |
| `cookies` | Cookies 存储 |
| `deploy/macos` | macOS 部署配置 |
| `docker` | Docker 相关文件 |
| `docs` | 文档 |
| `donate` | 捐赠记录 |
| `errors` | 错误定义 |
| `examples` | 集成示例（n8n、Cherry Studio、AnythingLLM 等） |
| `pkg` | 核心包 |
| `skills/post-to-xhs` | Skills 相关 |
| `xiaohongshu` | 小红书核心逻辑 |

### 8.2 核心文件

| 文件 | 说明 |
|------|------|
| `main.go` | 主入口 |
| `app_server.go` | MCP 应用服务器 |
| `mcp_handlers.go` | MCP 处理器 |
| `mcp_server.go` | MCP 服务端 |
| `service.go` | 业务逻辑服务 |
| `handlers_api.go` | API 处理器 |
| `routes.go` | 路由配置 |
| `middleware.go` | 中间件 |
| `types.go` | 类型定义 |
| `go.mod` / `go.sum` | Go 依赖 |

---

## §9 常见问题

### Q1：为什么检查登录用户名显示异常？

**A**：用户名是写死的，不影响功能。

### Q2：显示发布成功后，但实际上没有显示？

**排查步骤**：
1. 使用**非无头模式**重新发布一次
2. 更换**不同的内容**重新发布
3. 登录网页版小红书，查看账号是否被**风控限制网页版发布**
4. 检查**图片大小**是否过大
5. 确认**图片路径中没有中文字符**
6. 若使用网络图片地址，请确认**图片链接可正常访问**

### Q3：程序出现闪退如何解决？

**A**：建议从源码安装，或使用 Docker 安装。

### Q4：提示无法连接？

**A**：
- **Docker 环境**：请使用 `http://host.docker.internal:18060/mcp`
- **非 Docker 环境**：请使用**本机 IPv4 地址**访问

### Q5：OpenClaw 接入有问题？

**A**：OpenClaw 的 AI 自动部署行为不在本项目维护范围内，MCPorter 作为中间层可能引入额外的兼容性问题。建议改用 Claude Code CLI、Cursor 或 Cline 等原生支持 HTTP MCP 的客户端。

---

## §10 总结

### 10.1 核心优势

| 优势 | 说明 |
|------|------|
| **MCP 标准化** | 符合 Model Context Protocol 协议 |
| **多客户端支持** | Claude Code/Cursor/Cline/OpenClaw 等 |
| **全功能覆盖** | 发布/搜索/评论/点赞/收藏/用户信息 |
| **多部署方式** | Binary/Docker/源码/OpenClaw |
| **活跃社区** | 微信群 20+、飞书群 4 个 |
| **慈善捐赠** | 所有赞赏用于慈善 |

### 10.2 适用场景

| 场景 | 推荐指数 |
|------|----------|
| AI 内容创作自动化 | ⭐⭐⭐⭐⭐ |
| 小红书运营效率提升 | ⭐⭐⭐⭐⭐ |
| 多账号管理 | ⭐⭐⭐⭐ |
| 社群互动自动化 | ⭐⭐⭐⭐ |
| 内容分析与调研 | ⭐⭐⭐⭐ |

### 10.3 项目信息

| 项目 | 信息 |
|------|------|
| Stars | 12.4k |
| Forks | 1.9k |
| 贡献者 | 33 人 |
| 发布版本 | 90 个 |
| 最新版本 | v2026.03.09.0605-0e16f4b (2026-03-09) |
| 语言 | Go 71.3%, Python 27.5% |

### 10.4 相关资源

| 资源 | 链接 |
|------|------|
| 官方网站 | https://www.haha.ai/xiaohongshu-mcp |
| GitHub | https://github.com/xpzouying/xiaohongshu-mcp |
| 博客文章 | https://www.haha.ai/xiaohongshu-mcp |
| Docker Hub | https://hub.docker.com/r/xpzouying/xiaohongshu-mcp |
| x-mcp 插件版 | https://github.com/xpzouying/x-mcp |

### 10.5 捐赠支持

本项目所有的赞赏都会用于慈善捐赠。捐赠时，请备注 MCP 以及名字。如需更正或撤回署名，请开 Issue 或通过邮箱联系 `xpzouying@gmail.com`。

---

*文档版本 1.0 | 撰写日期：2026-03-31 | 基于 v2026.03.09.0605-0e16f4b (2026-03-09) | Stars: 12.4k ⭐*