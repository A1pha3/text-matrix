---
title: "OpenCLI：把任意网站变成 CLI，让 AI Agent 操控你的登录态浏览器"
date: "2026-05-17T09:10:00+08:00"
slug: "opencli-ai-agent-browser-cli-framework"
description: "OpenCLI 是一个 JavaScript/Node.js 的 AI 原生 CLI 框架，可将任意网站、浏览器会话、Electron 桌面应用转换为标准化命令行接口，供人类和 AI Agent 使用。支持 100+ 内置适配器、零 LLM 运行成本、多 Chrome Profile 路由，以及通过 Chrome DevTools Protocol 实现确定性浏览器自动化。"
draft: false
categories: ["技术笔记"]
tags: ["OpenCLI", "浏览器自动化", "AI Agent", "CDP", "Node.js", "CLI工具"]
---

## 前言

如果有一个工具能让你：

- 在终端里直接调用 `opencli bilibili hot`、`opencli hackernews top`、`opencli zhihu hot`，不需要打开浏览器
- 让 AI Agent（Claude Code、Cursor 等）像人一样操控你的已登录浏览器——导航、点击、填表、抓数据
- 把本地工具 `gh`、`docker`、`notion` 全部通过 `opencli` 统一调用
- 为任何网站写一个新的 CLI 命令，花几分钟而不是几小时

这就是 **OpenCLI**。

本文基于 GitHub API 核实信息（Stars: 21,248, Forks: 2,156, Language: JavaScript），是一篇从入门到精通的完整技术文档，涵盖原理、架构、使用和开发扩展。

---

## 一、核心定位：三类场景，一个入口

OpenCLI 是一个统一的 CLI 界面，涵盖三种不同的自动化场景：

| 场景 | 说明 | 典型命令 |
|------|------|---------|
| **内置适配器** | 100+ 站点的确定性 CLI 命令，无需浏览器 | `opencli bilibili hot --limit 5` |
| **AI Agent 浏览器控制** | 通过 Chrome CDP 操控你的已登录浏览器，Agent 驱动 | `opencli browser work open <url>` |
| **CLI Hub** | 把本地二进制工具（gh/docker/ntn 等）通过 OpenCLI 统一暴露 | `opencli gh pr list` |

### 与传统 CLI 工具的区别

传统 CLI 工具通常专注于一个站点或一种能力。OpenCLI 的核心创新在于：**把浏览器会话当作 CLI 的执行后端**。你的登录态、Cookie、Session 直接复用，不需要额外认证。

```bash
# 确定性命令（无浏览器）
opencli hackernews top --limit 5

# AI Agent 驱动浏览器（需要登录态）
opencli browser work open https://twitter.com
opencli browser work click ".compose-area"
opencli browser work type "Hello from CLI" --selector "div[contenteditable]"
```

---

## 二、安装与配置

### 环境要求

- **Node.js**: >= 21.0.0（npm 安装路径要求）
- **Bun**: >= 1.0（可选替代运行时）
- **Chrome/Chromium**: 正常运行，已登录目标站点

### 安装步骤

```bash
# 1. 确认 Node.js 版本
node --version  # 需要 >= 21.0.0

# 2. 全局安装
npm install -g @jackwener/opencli

# 3. 安装 Browser Bridge 扩展
# 方式 A（推荐）：Chrome Web Store
# 访问 https://chromewebstore.google.com/detail/opencli/ildkmabpimmkaediidaifkhjpohdnifk 安装

# 方式 B：手动加载
# 1. 下载 https://github.com/jackwener/opencli/releases 最新版 opencli-extension-v{version}.zip
# 2. 解压，打开 chrome://extensions，启用开发者模式
# 3. 点击"加载已解压的扩展程序"，选择解压目录

# 4. 验证安装
opencli doctor
```

### 验证与 Profile 管理

```bash
# 查看所有已连接的 Chrome Profile
opencli profile list

# 为特定 Profile 设置别名
opencli profile rename <contextId> work

# 使用指定 Profile 执行命令
opencli --profile work browser state

# 当只有一个已连接 Profile 时，OpenCLI 自动选中
```

---

## 三、架构深度解析

### 3.1 Daemon-Extension 架构

OpenCLI 的浏览器控制层由三个组件构成：

```
┌─────────────────────────────────────────────────────┐
│  OpenCLI (Node.js)                                  │
│  ├── CLI Parser & Command Router                    │
│  ├── Adapter System (100+ built-in)                 │
│  └── Browser Bridge Client (WebSocket)              │
└──────────────────┬──────────────────────────────────┘
                   │ WebSocket (OPENCLI_DAEMON_PORT=19825)
┌──────────────────▼──────────────────────────────────┐
│  OpenCLI Daemon (Node.js, auto-start)              │
│  └── Bridge Protocol Handler                        │
└──────────────────┬──────────────────────────────────┘
                   │ Chrome DevTools Protocol (CDP)
┌──────────────────▼──────────────────────────────────┐
│  Browser Bridge Extension (Chrome Extension)       │
│  ├── manifest.json: extension ID, permissions       │
│  ├── background.js: CDP connection manager          │
│  ├── popup.js: 用户交互界面                          │
│  └── scripts/: 内容脚本与桥接                        │
└──────────────────┬──────────────────────────────────┘
                   │ CDP (Chrome Remote Debugging)
┌──────────────────▼──────────────────────────────────┐
│  Chrome/Chromium (with Remote Debugging Port)       │
│  └── 保持登录态的浏览器会话                          │
└─────────────────────────────────────────────────────┘
```

**数据流：**
1. 用户/AI Agent 执行 `opencli browser work open https://twitter.com`
2. OpenCLI 通过 WebSocket 将命令发送给 Daemon（默认端口 19825）
3. Daemon 通过 Chrome 扩展的 CDP 连接将指令发送到浏览器
4. 浏览器执行操作，结果通过同一路径返回

**设计优势：**
- **凭证不离开浏览器**：Cookie/Session 始终在 Chrome 中，OpenCLI 只发送指令
- **多 Profile 隔离**：每个 Chrome Profile 有独立的扩展实例和会话
- **零 token 消耗**：确定性输出，不需要 LLM 介入（浏览器型命令除外）

### 3.2 核心命令系统

#### `opencli browser` — 浏览器控制原语

`opencli browser <profile> <command>` 是 AI Agent 的主要交互接口，session 路由通过 `<profile>` 参数指定：

```bash
# 会话管理
opencli browser work open <url>           # 打开 URL，返回 targetId
opencli browser work tab list             # 列出所有 tab
opencli browser work tab new [url]        # 新建 tab
opencli browser work tab select <targetId> # 切换默认 tab
opencli browser work tab close <targetId> # 关闭 tab
opencli browser work close                # 关闭整个会话

# 页面操作
opencli browser work state                # 获取当前页面状态
opencli browser work click <selector>     # 点击元素
opencli browser work type <text> --selector <sel>  # 输入文本
opencli browser work fill <selector> <value>  # 填充表单字段
opencli browser work select <selector> <option>  # 选择下拉选项
opencli browser work keys <key>            # 按键（如 Enter, Escape）
opencli browser work wait <selector> [timeout]  # 等待元素

# 内容提取
opencli browser work get <selector>        # 获取元素文本
opencli browser work find <selector>       # 查找元素
opencli browser work extract <selector>   # 提取结构化数据
opencli browser work frames                # 列出所有 iframe

# 页面控制
opencli browser work screenshot [path]     # 截图
opencli browser work scroll <selector> [direction]  # 滚动
opencli browser work back                  # 后退
opencli browser work eval <js>            # 执行 JS

# 网络监控
opencli browser work network <filter>     # 拦截/过滤网络请求
```

**重要特性：**
- `tab new` 创建新 tab 但不改变默认目标；只有 `tab select <targetId>` 才会把该 tab 设为后续命令的目标
- 可以用 `--tab <targetId>` 显式路由命令到特定 tab
- 支持 `--window foreground|background` 覆盖窗口行为
- `siteSession: 'persistent'` 声明可在适配器中保持稳定的站点 tab

#### 内置适配器命令

100+ 站点的确定性 CLI 命令，格式为 `opencli <site> <command>`：

```bash
# 新闻/社区
opencli hackernews top --limit 10
opencli reddit hot --limit 5
opencli hackernews new --limit 10
opencli reddit search "AI agents" --limit 10

# 中文平台
opencli bilibili hot --limit 5
opencli zhihu hot --limit 10
opencli xiaohongshu search "咖啡" --limit 10
opencli tieba hot --limit 10

# 社交媒体
opencli twitter trending
opencli twitter timeline --limit 10
opencli twitter post "Hello from CLI"
opencli twitter profile <username>

# 视频/内容
opencli youtube search "tutorial" --limit 5
opencli bilibili video <bvid>
opencli douyin hot --limit 10

# 购物/电商
opencli 1688 search "电子产品" --limit 10
opencli amazon bestseller --category "Electronics"

# AI 工具
opencli claude ask "解释量子计算"
opencli gemini ask "什么是 transformer"
opencli deepseek ask "写一段快排代码"
opencli notebooklm summary

# 桌面应用（Electron）
opencli cursor status
opencli codex ask "explain this code"
opencli chatgpt-app ask "帮我写一封邮件"
```

### 3.3 适配器分类与认证策略

OpenCLI 的适配器按认证需求分为五类：

| 策略 | 说明 | 适用场景 | 示例 |
|------|------|---------|------|
| **PUBLIC** | 无需认证，公开数据 | 新闻、热榜、搜索 | HackerNews、Reddit |
| **COOKIE** | 使用浏览器 Cookie | 需要登录但可提取 Cookie | Twitter/X、Zhihu |
| **INTERCEPT** | 拦截网络请求获取 Token | SPA API 调用 | 小红书、1688 |
| **UI** | 需要通过浏览器 UI 操作认证 | 无法提取 Token | 知乎创作端 |
| **LOCAL** | 本地凭证文件（如 JSON） | 独立认证的桌面工具 | 小宇宙播客 |

适配器开发时，`opencli-adapter-author` skill 会引导你选择正确的认证策略。

---

## 四、Browser Bridge 扩展详解

### 扩展结构

```
extension/
├── manifest.json          # 扩展配置（permissions: activeTab, scripting, clipboard等）
├── popup.html/js           # 用户交互界面（Profile 切换、状态显示）
├── background.js           # CDP 连接管理器（WebSocket ↔ Chrome）
├── scripts/
│   ├── content.js         # 注入到目标页面，处理 DOM 操作
│   └── bridge.js          # 消息传递桥接
└── store_assets/          # 图标等资源
```

### manifest.json 关键配置

```json
{
  "manifest_version": 3,
  "name": "OpenCLI Browser Bridge",
  "version": "x.x.x",
  "permissions": [
    "activeTab",
    "scripting",
    "clipboardWrite",
    "clipboardRead"
  ],
  "host_permissions": ["<all_urls>"],
  "background": {
    "service_worker": "background.js"
  }
}
```

### Daemon 通信协议

Daemon 与扩展之间通过 WebSocket 通信，协议设计如下：

```
OpenCLI → WebSocket → Daemon → CDP → Extension → Chrome
         ↑                              ↓
         └─────────── response ←───────┘
```

关键配置变量：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OPENCLI_DAEMON_PORT` | `19825` | Daemon HTTP/WebSocket 端口 |
| `OPENCLI_PROFILE` | — | 指定默认使用的 Chrome Profile |
| `OPENCLI_WINDOW` | `foreground` | 浏览器窗口位置 |
| `OPENCLI_BROWSER_CONNECT_TIMEOUT` | `30` | 连接超时（秒） |
| `OPENCLI_BROWSER_COMMAND_TIMEOUT` | `60` | 单命令超时（秒） |
| `OPENCLI_CDP_ENDPOINT` | — | 远程 Chrome/ Electron CDP 端点 |
| `OPENCLI_CDP_TARGET` | — | 按 URL 过滤 CDP target |
| `OPENCLI_VERBOSE` | `false` | 详细日志 |

---

## 五、AI Agent 集成

### 安装 Skills

```bash
# 完整安装
npx skills add jackwener/opencli

# 按需安装
npx skills add jackwener/opencli --skill opencli-adapter-author
npx skills add jackwener/opencli --skill opencli-autofix
npx skills add jackwener/opencli --skill opencli-browser
npx skills add jackwener/opencli --skill opencli-usage
npx skills add jackwener/opencli --skill smart-search
```

### Skill 选择指南

| Skill | 何时使用 | 示例 Prompt |
|-------|---------|------------|
| **opencli-adapter-author** | 实时操作网站或编写新适配器 | "帮我看看小红书通知"、"做一个抖音热门适配器" |
| **opencli-autofix** | 内置命令失败时修复 | "`opencli zhihu hot` 返回空了，修一下" |
| **opencli-browser** | 浏览器自动化参考 | "帮我填一下这个表单" |
| **opencli-usage** | 快速查找命令 | "OpenCLI 有哪些 Twitter 命令？" |
| **smart-search** | 在现有能力中搜索 | "找一个 B 站热门适配器" |

### 工作流程示例

当你对 AI Agent 说 *"帮我检查小红书通知"*：

1. Agent 调用 `opencli browser <session> open https://www.xiaohongshu.com/notification`
2. Agent 等待页面加载 `opencli browser <session> wait ".notification-list"`
3. Agent 提取通知内容 `opencli browser <session> extract ".notification-item"`
4. 结果以结构化数据返回给你

---

## 六、扩展开发：从零写一个适配器

### 方法一：快速本地适配器（`~/.opencli/clis/`）

```bash
# 初始化一个新适配器
opencli browser init cnn/top

# 编辑适配器文件
vim ~/.opencli/clis/cnn/top.js

# 验证适配器
opencli browser verify cnn/top

# 测试
opencli cnn top
```

适配器文件结构：

```javascript
// ~/.opencli/clis/cnn/top.js
export default {
  site: 'cnn',
  command: 'top',
  auth: 'PUBLIC',  // 或 COOKIE/INTERCEPT/UI/LOCAL

  async run({ ctx }) {
    // ctx.fetch: 封装的 HTTP 客户端
    // ctx.browser: 浏览器操作上下文
    const data = await ctx.fetch('https://cnn.com/api/top-stories');
    return data.articles.map(article => ({
      title: article.title,
      url: article.url,
      timestamp: article.publishedAt,
    }));
  },

  // 可选：输出字段定义
  output: {
    fields: ['title', 'url', 'timestamp']
  }
};
```

### 方法二：插件方式（Git 仓库分享）

```bash
# 创建插件项目
opencli plugin create my-adapter
cd my-adapter
git init

# 安装插件
opencli plugin install file://$(pwd)

# 使用
opencli my-adapter <command>
```

### 方法三：本地覆盖官方适配器

```bash
# 导出官方适配器到本地
opencli adapter eject twitter

# 编辑本地副本
vim ~/.opencli/clis/twitter/hot.js

# 测试
opencli twitter hot --limit 5

# 恢复官方版本
opencli adapter reset twitter
```

### 侦察与验证工具

```bash
# 一步侦察目标站点
opencli browser recon analyze <url>

# 初始化新站点适配器
opencli browser recon init <site>/<command>

# 验证适配器正确性
opencli browser verify <site>/<command>

# 验证时写入 fixture（首次需要）
opencli browser verify instagram/collection-create --write-fixture --seed-args opencli-verify
```

---

## 七、CLI Hub：统一本地工具

OpenCLI 不仅能控制浏览器，还能把本地 CLI 工具接入统一入口：

```bash
# 注册本地工具
opencli external register gh        # GitHub CLI
opencli external register docker     # Docker CLI
opencli external register ntn       # Notion CLI

# 使用统一入口
opencli gh pr list --limit 5
opencli docker ps
opencli ntn pages list

# 列出所有外部工具
opencli external list

# 配置文件位置
vim ~/.opencli/external-clis.yaml
```

支持的外部工具：gh、obsidian、docker、longbridge、ntn（Notion）、lark-cli、dws（钉钉）、wecom-cli（企业微信）、tg（Telegram）、discord、wx（微信）、vercel 等。

---

## 八、Electron 桌面应用控制

OpenCLI 支持通过 CDP 直接控制 Electron 桌面应用（Cursor、Codex、ChatGPT、Antigravity 等）：

```bash
# 指定 Electron CDP 端点
OPENCLI_CDP_ENDPOINT=http://localhost:9222
opencli cursor ask "explain this function"

# 按 URL 过滤 target
OPENCLI_CDP_TARGET=cursor.app
opencli codex ask "refactor this module"
```

这使得 AI Agent 可以在 Cursor 编辑器中直接执行代码审查、在 Codex 中运行任务、在 ChatGPT 中发送消息。

---

## 九、配置与环境变量

完整配置清单：

```bash
# Daemon 端口（默认 19825）
export OPENCLI_DAEMON_PORT=19825

# 默认 Chrome Profile
export OPENCLI_PROFILE=work

# 窗口位置
export OPENCLI_WINDOW=foreground  # 或 background

# 超时设置
export OPENCLI_BROWSER_CONNECT_TIMEOUT=30   # 连接超时（秒）
export OPENCLI_BROWSER_COMMAND_TIMEOUT=60   # 命令超时（秒）

# 远程 CDP（Electron / 远程 Chrome）
export OPENCLI_CDP_ENDPOINT=http://localhost:9222
export OPENCLI_CDP_TARGET=cursor.app       # 按 URL 过滤 target

# 日志
export OPENCLI_VERBOSE=true
export DEBUG_SNAPSHOT=1  # DOM 快照调试
```

---

## 十、更新与维护

```bash
# 更新 OpenCLI
npm install -g @jackwener/opencli@latest

# 更新所有 skills
npx skills add jackwener/opencli

# 更新特定 skill
npx skills add jackwener/opencli --skill opencli-adapter-author

# 检查安装状态
opencli doctor

# 查看所有可用命令
opencli list
```

---

## 结语

OpenCLI 的核心价值在于三个统一：

1. **接口统一**：不管目标是网站、Electron 应用还是本地工具，都通过 `opencli` 一个入口访问
2. **认证统一**：登录态在浏览器中复用，不需要为每个站点单独管理凭证
3. **扩展统一**：无论是写一个新的网站适配器还是发布一个插件，工具链完全一致

对于 AI Agent 开发者而言，OpenCLI 提供了确定性的浏览器控制能力——Agent 可以像人一样操作任意网站，而不需要依赖昂贵的 LLM 视觉理解或脆弱的爬虫方案。

**项目信息（已通过 GitHub API 核实）：**
- GitHub: https://github.com/jackwener/OpenCLI
- Stars: 21,248 | Forks: 2,156
- 语言: JavaScript/Node.js（>= 21）
- 许可证: Apache 2.0
- npm: @jackwener/opencli
- Skills: opencli-adapter-author / opencli-autofix / opencli-browser / opencli-usage / smart-search