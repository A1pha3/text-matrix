---
title: "xiaohongshu-mcp：小红书 MCP 服务完全指南"
slug: "xiaohongshu-mcp-xiaohongshu-model-context-protocol-guide"
github_repo: "xpzouying/xiaohongshu-mcp"
source_key: "gh:xpzouying/xiaohongshu-mcp"
aliases:
  - /posts/tech/xiaohongshu-mcp-xiaohongshu-model-context-protocol-guide/
date: "2026-03-31T17:05:00+08:00"
lastmod: "2026-09-24T10:00:00+08:00"
categories: ["技术笔记"]
tags: ["MCP", "小红书", "AI助手", "Claude Code", "Cursor", "OpenClaw", "社交媒体"]
description: "全面解析 xiaohongshu-mcp (16k Stars)：小红书 Model Context Protocol 服务，让 AI 助手直接发布内容、搜索、评论、点赞、收藏，提供 18 个 MCP 工具，支持 Claude Code/Cursor/Cline 等多种客户端。"
---

# xiaohongshu-mcp：小红书 MCP 服务完全指南

> 预计阅读时间：21 分钟 | 难度：⭐⭐⭐

---

## 学习目标

读完本文，你能够：

- 理解 xiaohongshu-mcp 的定位：它解决什么问题，怎么解决
- 用二进制、源码或 Docker 三种方式之一把服务跑起来
- 把 Claude Code、Cursor、Cline 等客户端接入服务
- 查阅全部 18 个 MCP 工具的参数与行为
- 避开登录冲突、发布失败、账号风控这几类常见坑

---

## §2 项目概述

### 2.1 什么是 xiaohongshu-mcp？

**xiaohongshu-mcp**（官方仓库：[xpzouying/xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp)）是一个基于 **Model Context Protocol (MCP)** 的小红书服务端实现，让你的 AI 助手直接访问小红书数据。

官方描述只有一句话：

> MCP for 小红书 / xiaohongshu.com。让你的 AI 助手直接访问小红书数据。

具体来说，它是一个 Go 编写的 MCP 服务端，底层驱动一台无头浏览器模拟真人操作网页版小红书。AI 助手（Claude Code、Cursor 等）通过 MCP 协议调用它，就能发布图文和视频、搜索内容、读笔记详情、发表和回复评论、点赞收藏，以及查看用户主页和通知。

小红书没有开放的内容发布 API，这个项目用浏览器自动化绕过了这一层——无头浏览器负责像人一样操作网页，MCP 协议负责把这些操作暴露给 AI 助手。

### 2.2 价值定位

| 价值 | 说明 |
|------|------|
| **AI 驱动** | 用自然语言指挥 AI 助手完成小红书操作 |
| **MCP 协议** | 标准 Streamable HTTP 接口，客户端选择面宽 |
| **全功能** | 发布图文/视频、搜索、评论、点赞、收藏、通知处理 |
| **拟人化操作** | 内置 humanize 模块，模拟真人鼠标移动与输入节奏 |
| **开源透明** | Apache-2.0 许可证，可商用 |
| **活跃社区** | 微信群编号已排到 26 群，飞书群 4 个 |

### 2.3 核心数据

| 项目 | 数据（2026-09-24 核实） |
|------|------|
| Stars | 15,958 |
| Forks | 2,353 |
| 最新版本 | v2.5.5（2026-09-22 发布） |
| 发布版本累计 | 135 个 |
| 贡献者 | 33 人（GitHub contributors 口径） |
| 语言构成 | Go 81.2%，Python 17.7% |
| 许可证 | Apache-2.0 |

### 2.4 版本说明

项目 2026 年 7 月 26 日从日期式版本号（如 v2026.03.09.0605）切换到语义化版本，同日发布 v1.2.9 和 v2.0.0。本文以 **v2.5.5** 为口径。早期网上教程多基于旧版，部署方式与工具清单可能对不上，注意分辨。

---

## §3 核心功能详解

服务共注册 **18 个 MCP 工具**。官方 README 的工具清单仍写着 13 个，落后于代码，本节以源码 `mcp_server.go` 为准。

### 3.1 内容发布

#### 3.1.1 发布图文

`publish_content` 用于发布图文内容：

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `title` | string | ✅ | 标题，小红书限制不超过 20 个中文字或英文单词 |
| `content` | string | ✅ | 正文，不超过 1000 字；不要把 `#` 开头的话题写进正文，一律交给 `tags` |
| `images` | string[] | ✅ | 图片路径列表（至少 1 张），支持 HTTP 链接或本地绝对路径，官方推荐本地路径 |
| `tags` | string[] | 可选 | 话题标签列表，如 `["美食", "旅行"]` |
| `schedule_at` | string | 可选 | 定时发布时间，ISO8601 格式，支持 1 小时至 14 天内，不填立即发布 |
| `is_original` | boolean | 可选 | 是否声明原创，默认不声明 |
| `visibility` | string | 可选 | 可见范围：`公开可见`（默认）/ `仅自己可见` / `仅互关好友可见` |
| `products` | string[] | 可选 | 商品关键词或商品 ID，绑定带货商品；系统自动搜索并选中第一个匹配结果，需账号已开通商品功能 |

图片支持两种输入：HTTP/HTTPS 链接（自动下载）和本地绝对路径。官方推荐本地路径——不依赖网络、上传更快、不会有链接失效问题。

#### 3.1.2 发布视频

`publish_with_video` 用于发布视频内容：

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `title` | string | ✅ | 标题 |
| `content` | string | ✅ | 正文 |
| `video` | string | ✅ | 本地视频文件绝对路径（仅支持单个视频），建议不超过 1GB |
| `tags` | string[] | 可选 | 话题标签列表 |
| `schedule_at` | string | 可选 | 定时发布时间 |
| `visibility` | string | 可选 | 可见范围 |
| `products` | string[] | 可选 | 商品关键词列表 |

视频只接受本地文件，不接受 HTTP 链接。服务会上传并等待平台处理完成后自动发布，处理时间较长，调用时耐心等待。

### 3.2 登录与认证

#### 3.2.1 检查登录状态

`check_login_status` 检查当前账号的登录状态（无参数）。

#### 3.2.2 获取登录二维码

`get_login_qrcode` 获取登录二维码，返回 Base64 图片和超时时间（无参数）。

#### 3.2.3 删除 Cookies

`delete_cookies` 删除 cookies 文件并重置登录状态，删除后需要重新登录。登录态保存在 `~/.xiaohongshu/cookies.json`。

**⚠️ 重要提示**：

- 小红书同一账号不允许在多个网页端同时登录
- 登录 MCP 后，不要在其他网页端登录该账号，否则会被"踢出登录"
- 想查看账号信息，用手机 App

### 3.3 内容获取

#### 3.3.1 获取首页推荐

`list_feeds` 获取小红书首页推荐列表（无参数）。

#### 3.3.2 搜索内容

`search_feeds` 按关键词搜索：

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `keyword` | string | ✅ | 搜索关键词 |
| `filters.sort_by` | string | 可选 | 排序：`综合`（默认）/ `最新` / `最多点赞` / `最多评论` / `最多收藏` |
| `filters.note_type` | string | 可选 | 笔记类型：`不限`（默认）/ `视频` / `图文` |
| `filters.publish_time` | string | 可选 | 发布时间：`不限`（默认）/ `一天内` / `一周内` / `半年内` |
| `filters.search_scope` | string | 可选 | 搜索范围：`不限`（默认）/ `已看过` / `未看过` / `已关注` |
| `filters.location` | string | 可选 | 位置距离：`不限`（默认）/ `同城` / `附近` |

#### 3.3.3 获取帖子详情

`get_feed_detail` 获取笔记详情，返回内容、图片、作者信息、互动数据（点赞/收藏/分享数）和评论列表。视频笔记额外返回 `video` 字段，含各编码档位的视频直链与字幕地址（带签名、有时效）。

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `feed_id` | string | ✅ | 笔记 ID，从 Feed 列表或搜索结果获取 |
| `xsec_token` | string | ✅ | 访问令牌，从 Feed 列表或搜索结果的 `xsecToken` 字段获取 |
| `load_all_comments` | boolean | 可选 | 是否滚动加载全部评论，默认 false 只返回前 10 条一级评论 |
| `limit` | number | 可选 | 一级评论数量上限，默认 20。仅当 `load_all_comments=true` 时生效 |
| `click_more_replies` | boolean | 可选 | 是否展开二级回复，默认不展开。仅当 `load_all_comments=true` 时生效 |
| `reply_limit` | number | 可选 | 跳过回复数超过该阈值的评论，默认 10。仅当 `click_more_replies=true` 时生效 |
| `scroll_speed` | string | 可选 | 滚动速度：`slow` / `normal` / `fast`。仅当 `load_all_comments=true` 时生效 |

`feed_id` 与 `xsec_token` 缺一不可，两者都从 Feed 列表或搜索结果里拿。

### 3.4 评论互动

#### 3.4.1 发表评论

`post_comment_to_feed` 发表评论到笔记：

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `feed_id` | string | ✅ | 笔记 ID |
| `xsec_token` | string | ✅ | 访问令牌 |
| `content` | string | ✅ | 评论内容 |

#### 3.4.2 回复评论

`reply_comment_in_feed` 回复笔记下的指定评论：

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `feed_id` | string | ✅ | 笔记 ID |
| `xsec_token` | string | ✅ | 访问令牌 |
| `content` | string | ✅ | 回复内容 |
| `comment_id` 或 `user_id` | string | ✅ | 目标评论 ID 或评论用户 ID，至少提供一个 |

### 3.5 点赞与收藏

#### 3.5.1 点赞

`like_feed` 点赞或取消点赞。工具有状态检测：已点赞时跳过点赞，未点赞时跳过取消点赞，不会重复操作。

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `feed_id` | string | ✅ | 笔记 ID |
| `xsec_token` | string | ✅ | 访问令牌 |
| `unlike` | boolean | 可选 | true 为取消点赞，默认为点赞 |

#### 3.5.2 收藏

`favorite_feed` 收藏或取消收藏，同样带状态检测。

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `feed_id` | string | ✅ | 笔记 ID |
| `xsec_token` | string | ✅ | 访问令牌 |
| `unfavorite` | boolean | 可选 | true 为取消收藏，默认为收藏 |

### 3.6 用户主页

`user_profile` 获取指定用户的主页：

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `user_id` | string | ✅ | 用户 ID |
| `xsec_token` | string | ✅ | 访问令牌 |
| `tab` | string | 可选 | 主页标签页：`note`（笔记，默认）/ `fav`（收藏）/ `liked`（点赞），后两者可能被对方设为不公开 |

`get_my_profile` 获取当前登录用户的主页，返回基本信息、关注/粉丝/获赞量和指定 tab 下的内容，参数只有可选的 `tab`（含义同上）。

### 3.7 通知处理

这组工具让 AI 助手接管消息中心：

| 工具 | 功能 | 关键参数 |
|------|------|------|
| `get_unread_count` | 查询「评论和@」「赞和收藏」「新增关注」三个分区的未读数，不清除未读标记 | 无 |
| `list_notifications` | 拉取通知列表，返回评论内容、评论者和对应笔记的 `feed_id`/`xsec_token`；注意会清除该分区未读标记 | `tab`（`mentions` 评论和@，默认 / `likes` 赞和收藏 / `connections` 新增关注）、`limit`（默认 20） |
| `reply_notification` | 回复「评论和@」里的一条评论，无需先定位笔记 | `comment_id`、`content` |
| `like_notification` | 给「评论和@」里的一条评论点赞或取消点赞 | `comment_id`、`unlike` |

---

## §4 安装与部署

### 4.1 方案 A：下载预编译二进制文件（推荐）

#### 4.1.1 下载程序

从 [GitHub Releases](https://github.com/xpzouying/xiaohongshu-mcp/releases) 下载对应平台的二进制文件：

**MCP 主程序：**

| 平台 | 文件名 |
|------|--------|
| macOS Apple Silicon | `xiaohongshu-mcp-darwin-arm64` |
| Windows x64 | `xiaohongshu-mcp-windows-amd64.exe` |
| Linux x64 | `xiaohongshu-mcp-linux-amd64` |

**登录工具：**

| 平台 | 文件名 |
|------|--------|
| macOS Apple Silicon | `xiaohongshu-login-darwin-arm64` |
| Windows x64 | `xiaohongshu-login-windows-amd64.exe` |
| Linux x64 | `xiaohongshu-login-linux-amd64` |

目前只支持这三个平台。macOS Intel 与 Linux ARM64 在 v2.0.0 时代曾提供构建，v2.5.0 起已从发布清单移除。

#### 4.1.2 安装步骤

```bash
# 1. 赋予执行权限
chmod +x xiaohongshu-mcp-darwin-arm64
chmod +x xiaohongshu-login-darwin-arm64

# 2. 运行登录工具，扫码登录
./xiaohongshu-login-darwin-arm64

# 3. 启动 MCP 服务（默认无头模式，无浏览器界面）
./xiaohongshu-mcp-darwin-arm64

# 4. 或者以非无头模式启动，可以看到浏览器操作过程
./xiaohongshu-mcp-darwin-arm64 -headless=false
```

首次运行会自动下载无头浏览器（约 150MB），请保持网络畅通，后续运行不重复下载。Windows 用户遇到问题先看官方 [Windows 安装指南](https://github.com/xpzouying/xiaohongshu-mcp/blob/main/docs/windows_guide.md)。

#### 4.1.3 配置代理（可选）

通过 `XHS_PROXY` 环境变量设置代理：

```bash
XHS_PROXY=http://user:pass@proxy:port ./xiaohongshu-mcp-darwin-arm64
```

支持 HTTP/HTTPS/SOCKS5 代理，日志中会自动隐藏代理的认证信息。

#### 4.1.4 访问鉴权（可选）

v2.5.0 起支持为 HTTP API 和 MCP 接口配置 Token 鉴权，默认关闭。生产环境或服务暴露在局域网时建议开启：

```bash
# 环境变量方式
AUTH_TOKEN=your-secret-token ./xiaohongshu-mcp-darwin-arm64

# 或启动参数方式（优先级高于环境变量，但命令行参数可能被进程列表看到）
./xiaohongshu-mcp-darwin-arm64 -token=your-secret-token
```

开启后，所有 MCP 客户端都要带上请求头 `Authorization: Bearer <token>`：

```json
{
  "mcpServers": {
    "xiaohongshu-mcp": {
      "url": "http://localhost:18060/mcp",
      "headers": { "Authorization": "Bearer your-secret-token" }
    }
  }
}
```

### 4.2 方案 B：源码编译

依赖 Go 环境，安装方法见 [Golang 官方文档](https://go.dev/doc/install)。国内网络建议先配置 Go 模块代理：

```bash
# 以下三选一
go env -w GOPROXY=https://goproxy.cn,direct        # 七牛 CDN
go env -w GOPROXY=https://mirrors.aliyun.com/goproxy/,direct  # 阿里云
go env -w GOPROXY=https://goproxy.io,direct        # 官方
```

然后克隆、编译、运行：

```bash
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

不编译直接跑也可以：`go run cmd/login/main.go` 登录，`go run .` 启动服务。

### 4.3 方案 C：Docker 容器（最简单）

无需任何开发环境。官方推荐用 Docker Compose：

```bash
# 下载官方 compose 配置
wget https://raw.githubusercontent.com/xpzouying/xiaohongshu-mcp/main/docker/docker-compose.yml

# 启动服务
docker compose up -d

# 查看日志
docker compose logs -f

# 停止服务
docker compose stop
```

也可以直接拉镜像运行：

```bash
docker pull xpzouying/xiaohongshu-mcp:latest

docker run -d \
  --name xiaohongshu-mcp \
  -p 18060:18060 \
  xpzouying/xiaohongshu-mcp:latest
```

Docker 版本会自动配置内置浏览器和中文字体，挂载 `./data` 存储 cookies 与运行数据、`./images` 存储待发布的图片，并暴露 18060 端口。详细说明见官方 [Docker 部署指南](https://github.com/xpzouying/xiaohongshu-mcp/blob/main/docker/README.md)。

### 4.4 验证服务

用官方 Inspector 验证：

```bash
npx @modelcontextprotocol/inspector
```

打开终端输出的链接，地址填 `http://localhost:18060/mcp`，点击 Connect，再点 List Tools。能列出 18 个工具就是正常的——如果只看到 13 个，说明连到了别的服务或旧版本。

也可以用 curl 直接测试：

```bash
curl -X POST http://localhost:18060/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-secret-token" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}'
```

---

## §5 MCP 客户端接入

服务地址统一为 `http://localhost:18060/mcp`（Streamable HTTP）。任何支持 HTTP MCP 的客户端都能接入，下面是几个主流客户端的最小配置。

### 5.1 Claude Code CLI

```bash
# 添加 HTTP MCP 服务器
claude mcp add --transport http xiaohongshu-mcp http://localhost:18060/mcp

# 检查是否添加成功（确保服务已启动）
claude mcp list
```

### 5.2 Cursor

在项目根目录创建 `.cursor/mcp.json`（全局配置则放在 `~/.cursor/mcp.json`）：

```json
{
  "mcpServers": {
    "xiaohongshu-mcp": {
      "url": "http://localhost:18060/mcp",
      "description": "小红书内容发布服务 - MCP Streamable HTTP"
    }
  }
}
```

保存后重启 Cursor，在聊天界面的 Available Tools 里确认工具已连接。

### 5.3 Cline

在 Cline 的 MCP 设置中添加：

```json
{
  "xiaohongshu-mcp": {
    "url": "http://localhost:18060/mcp",
    "type": "streamableHttp",
    "autoApprove": [],
    "disabled": false
  }
}
```

`autoApprove` 留空表示每个工具调用都手动批准；确认可靠后可以把发布、搜索等工具加进去自动执行。

### 5.4 VS Code 与 Gemini CLI

VS Code 用命令面板运行 `MCP: Add Server`，选 HTTP 方式填入服务地址；或在项目根目录创建 `.vscode/mcp.json`：

```json
{
  "servers": {
    "xiaohongshu-mcp": {
      "url": "http://localhost:18060/mcp",
      "type": "http"
    }
  },
  "inputs": []
}
```

Gemini CLI 在 `~/.gemini/settings.json` 或项目的 `.gemini/settings.json` 中配置：

```json
{
  "mcpServers": {
    "xiaohongshu": {
      "httpUrl": "http://localhost:18060/mcp",
      "timeout": 30000
    }
  }
}
```

### 5.5 OpenClaw（通过 MCPorter）

OpenClaw 目前不原生支持 MCP，官方推荐经 MCPorter 中转。把下面三行命令直接交给 OpenClaw 执行：

```
npm i -g mcporter
npx mcporter config add xiaohongshu-mcp http://localhost:18060/mcp
npx mcporter list xiaohongshu-mcp
```

先在本地把 xiaohongshu-mcp 部署好，**不要**把 GitHub 链接丢给 OpenClaw 让它代为部署。MCPorter 是中间层，可能引入兼容性问题；遇到连接失败、工具调用异常，先排查 MCPorter 配置，不要直接提 Issue。没有强烈的 OpenClaw 需求，建议改用 Claude Code CLI、Cursor 或 Cline。

---

## §6 使用示例

以下提示词都可直接发给已接入的 AI 助手。

**示例 1：用网络图片发布图文**

```text
帮我写一篇帖子发布到小红书上，配图为：https://cn.bing.com/th?id=OHR.MaoriRock_EN-US6499689741_UHD.jpg&w=3840
图片是："纽西兰陶波湖的Ngātoroirangi矿湾毛利岩雕（© Joppi/Getty Images）"
使用 xiaohongshu-mcp 进行发布。
```

**示例 2：用本地图片发布图文（推荐）**

```text
帮我写一篇关于春天的帖子发布到小红书上，使用这些本地图片：
- /Users/username/Pictures/spring_flowers.jpg
- /Users/username/Pictures/cherry_blossom.jpg
使用 xiaohongshu-mcp 进行发布。
```

**示例 3：发布视频**

```text
帮我写一篇关于美食制作的视频发布到小红书上，使用这个本地视频文件：
- /Users/username/Videos/cooking_tutorial.mp4
使用 xiaohongshu-mcp 的视频发布功能。
```

**示例 4：搜索内容**

```text
帮我搜索一下最近关于 AI 写作的小红书帖子，看看有哪些热门内容。
```

**示例 5：评论互动**

```text
帮我给我刚发布的那篇小红书帖子添加一条评论："写得真好，收藏了！"
```

除了 MCP 工具，服务还提供一套 HTTP API（端口同为 18060），适合从 n8n、Cherry Studio、AnythingLLM 等平台或脚本直接调用，接口文档见仓库 [docs/API.md](https://github.com/xpzouying/xiaohongshu-mcp/blob/main/docs/API.md)，集成教程在仓库 examples 目录。

---

## §7 小红书运营须知

| 项目 | 要求 |
|------|------|
| **标题** | 不超过 20 个字（平台硬限制） |
| **正文** | 不超过 1000 个字（平台硬限制） |
| **配图** | 从推荐角度看，图文的流量比视频和纯文字更好 |
| **Tags** | 添加合适的 Tags 能带来更多流量 |
| **每日发帖** | 根据作者实操，建议每天 50 篇以内 |
| **视频大小** | 建议不超过 1GB |

风险说明（来自作者的实操经验）：

1. **账号安全**：项目源自作者的自用项目，稳定运行一年多没有封号，只有 Cookies 过期需要重新登录的情况
2. **实名认证**：没有实名认证的账号（特别是新号）一般会触发实名认证提醒——这不是封号，不用 MCP 平台也会要求，实名后恢复正常
3. **违禁词**：曝光低先检查内容有没有违禁词，网上有很多免费检测工具
4. **引流限制**：不要引流、不要纯搬运，这是官方重点打击对象
5. **多设备登录**：同一账号只允许一个网页端登录，登录 MCP 后再在其他网页端登录会被踢出

---

## §8 项目结构

### 8.1 目录结构

| 目录 | 说明 |
|------|------|
| `browser` | 无头浏览器生命周期管理 |
| `humanize` | 拟人化操作：鼠标轨迹、输入节奏、随机延迟 |
| `xiaohongshu` | 小红书平台核心逻辑 |
| `pkg` | 公共包 |
| `cmd/login` | 登录工具源码 |
| `skills/post-to-xhs` | Agent Skill 形式的发布技能（含 CDP 发布脚本） |
| `examples` | n8n、Cherry Studio、AnythingLLM、Claude Code + Kimi K2 集成教程 |
| `docs` | HTTP API 文档与 Windows 安装指南 |
| `deploy/macos` | macOS launchd 部署配置 |
| `docker` | Dockerfile 与 docker-compose 配置 |
| `configs` / `cookies` / `errors` / `donate` | 配置、登录态存储、错误定义、捐赠记录 |

### 8.2 核心文件

| 文件 | 说明 |
|------|------|
| `main.go` | 主入口 |
| `app_server.go` | 应用服务器，各工具的 handle 逻辑 |
| `mcp_server.go` | MCP 服务端与 18 个工具注册 |
| `mcp_handlers.go` | MCP 请求处理 |
| `service.go` | 业务逻辑服务 |
| `handlers_api.go` | HTTP API 处理器 |
| `routes.go` / `middleware.go` | 路由与中间件 |
| `login_session.go` | 登录会话管理 |
| `types.go` | 类型定义 |

值得单独说的是 `humanize` 模块。浏览器自动化最容易被平台识别的是"机器味"：鼠标瞬间移动、输入节奏均匀。这个模块把指针移动、点击、文字输入都做成带随机性的拟人轨迹，是整个项目能稳定运行的关键之一。

---

## §9 常见问题

### Q1：为什么检查登录时用户名显示 `xiaghgngshu-mcp`？

**A**：用户名是写死的，不影响功能。

### Q2：显示发布成功，但小红书上没有？

**排查步骤**：

1. 用**非无头模式**重新发布一次，观察浏览器行为
2. 换**不同的内容**重新发布
3. 登录网页版小红书，确认账号是否被**风控限制网页版发布**
4. 检查**图片大小**是否过大
5. 确认**图片路径中没有中文字符**
6. 用网络图片时，确认**图片链接可正常访问**

### Q3：程序闪退？

**A**：改用源码安装或 Docker 安装。

### Q4：提示无法连接？

**A**：

- **Docker 环境**：用 `http://host.docker.internal:18060/mcp`
- **非 Docker 环境**：用**本机 IPv4 地址**访问

### Q5：OpenClaw 接入有问题？

**A**：OpenClaw 的 AI 自动部署行为不在本项目维护范围内，MCPorter 中间层可能引入额外的兼容性问题。建议改用 Claude Code CLI、Cursor 或 Cline 等原生支持 HTTP MCP 的客户端。

---

## §10 总结

发布、搜索、互动、通知四组工具，覆盖内容创作自动化、运营提效、社群互动处理、内容调研四类需求。它是单账号设计——一次登录管一个账号，不要指望它做多账号矩阵。

### 10.1 项目信息

| 项目 | 信息 |
|------|------|
| Stars | 15,958 |
| Forks | 2,353 |
| 贡献者 | 33 人 |
| 发布版本 | 135 个 |
| 最新版本 | v2.5.5（2026-09-22） |
| 语言 | Go 81.2%, Python 17.7% |
| 许可证 | Apache-2.0，可商用 |

### 10.2 相关资源

| 资源 | 链接 |
|------|------|
| 官方网站 | https://www.haha.ai/xiaohongshu-mcp |
| GitHub | https://github.com/xpzouying/xiaohongshu-mcp |
| Docker Hub | https://hub.docker.com/r/xpzouying/xiaohongshu-mcp |
| x-mcp 浏览器插件版 | https://github.com/xpzouying/x-mcp |
| 部署疑难杂症汇总 | https://github.com/xpzouying/xiaohongshu-mcp/issues/56 |

不想折腾部署环境的用户，作者还提供了 [x-mcp](https://github.com/xpzouying/x-mcp) 浏览器插件版：零配置，装上即用，直接在 Chrome/Edge 里运行，能避开大部分 Docker 部署问题。已部署好本项目的用户，也可以用社区提供的 [xiaohongshu-mcp-skills](https://github.com/autoclaw-cc/xiaohongshu-mcp-skills) 技能包在 OpenClaw 中调用。

### 10.3 捐赠支持

本项目所有的赞赏都会用于慈善捐赠，捐赠记录见仓库 [DONATIONS.md](https://github.com/xpzouying/xiaohongshu-mcp/blob/main/DONATIONS.md)。捐赠时请备注 MCP 以及名字；如需更正或撤回署名，请开 Issue 或联系邮箱 `xpzouying@gmail.com`。

---

## 参考来源与口径说明

- 本文数据（Stars/Forks/版本/语言构成/贡献者数）核实于 2026-09-24，来自 GitHub API；内容与机制以 v2.5.5（2026-09-22）的 README 与源码为准
- 18 个 MCP 工具的名称、参数与行为逐项对照源码 `mcp_server.go` 核实；官方 README 的工具清单（13 个）落后于代码，缺少 `get_my_profile`、`get_unread_count`、`list_notifications`、`reply_notification`、`like_notification` 五个工具
- "每天发帖建议 50 篇以内""稳定运行一年多未封号"为项目作者在 README 中的自述经验，转述于此，非独立验证结论
- 微信群数量依据 README 展示的群二维码编号（截至 26 群）；贡献者 33 人为 GitHub contributors API 口径，README all-contributors 名单为 31 人，两口径的差异在于后者只统计 PR 贡献
- 官网 haha.ai 对脚本访问返回 403，其官方性依据 GitHub 仓库 homepage 字段
