---
title: "Pake：一条命令将任何网页变成桌面应用，比Electron轻20倍"
date: "2026-04-07T17:15:00+08:00"
slug: pake-turn-any-webpage-into-desktop-app
description: "深度解析Pake项目：如何用Rust Tauri实现轻量级桌面应用打包，支持macOS/Windows/Linux，比Electron小20倍，一行命令将任何网页变成原生应用。"
categories: ["技术笔记"]
tags: ["Tauri", "Rust", "桌面应用", "Electron替代", "跨平台"]
draft: false
---

# Pake：一条命令将任何网页变成桌面应用

## 项目概述

**Pake**是由开发者[twa](https://github.com/tw93)创建的开源项目，核心功能是将任何网页通过一条命令打包成桌面应用。与传统Electron方案相比，Pake打包出的应用体积小约20倍，性能更高，内存占用更低。

| 指标 | 数值 |
|------|------|
| **GitHub Stars** | 47.6k |
| **Forks** | 9.5k |
| **最新版本** | V3.11.0 (2026-03-27) |
| **编程语言** | Rust 92.4%, Dockerfile 6.9%, TypeScript 0.7% |
| **许可证** | MIT |
| **代码提交** | 2,007次 |
| ** Contributors** | 55+ |

**官方定位**：Turn any webpage into a desktop app with one command, supports macOS, Windows, and Linux

---

## 核心特性

### 🎐 轻量级

**体积对比**：Pake打包的应用通常只有约**5MB**，而同等功能的Electron应用往往需要50-100MB。这意味着：

- 下载速度更快
- 安装更便捷
- 更新包更小，节省带宽
- 磁盘占用更低

### 🚀 高性能

**技术选型**：基于**Rust + Tauri**框架构建，相比传统JavaScript框架具有以下优势：

```rust
// Tauri的核心优势
// 1. 直接调用系统API，无需Node.js运行时
// 2. 内存占用极低（通常50-100MB vs Electron的200-500MB）
// 3. 启动速度更快
// 4. 二进制直接分发，无需安装运行时
```

### ⚡ 易用性

**三种使用方式**，满足不同用户需求：

```
┌─────────────────────────────────────────────────────────────┐
│                    Pake 使用方式分层                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  【初学者】下载现成应用包 / GitHub Actions在线构建           │
│      ↓ 无需配置环境，直接使用                              │
│                                                             │
│  【开发者】CLI命令行一键打包                                │
│      ↓ pnpm install -g pake-cli                           │
│                                                             │
│  【高级用户】本地克隆定制开发                               │
│      ↓ git clone + pnpm install + pnpm run dev             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 📦 功能丰富

| 功能 | 说明 |
|------|------|
| **快捷键支持** | 支持全局快捷键，提高操作效率 |
| **沉浸式窗口** | 原生窗口体验，无浏览器边框 |
| **拖放功能** | 支持文件拖放到应用窗口 |
| **样式定制** | 可自定义窗口大小、图标、背景色等 |
| **广告去除** | 支持注入CSS/JS去除网页广告 |
| **多窗口管理** | 支持新建窗口、窗口管理等 |

---

## 技术架构深度解析

### 技术栈

```
Pake 技术架构
├── Rust (Tauri Core)     核心框架，系统API调用
├── WebView2/RWK         系统WebView渲染网页
├── Node.js (pnpm)        构建工具链
├── TypeScript            CLI工具开发
└── Cargo/pnpm            包管理
```

**关键组件**：

1. **src-tauri/** - Rust后端核心
   - `main.rs` - 应用入口
   - `lib.rs` - 库定义
   - `commands/` - Tauri命令
   - `window/` - 窗口管理

2. **bin/** - CLI打包工具
   - `cli.ts` - 命令行接口
   - `build.ts` - 构建逻辑

3. **dist/** - 构建产物
   - 各平台的安装包输出目录

### 与Electron对比

| 对比维度 | Electron | Pake (Tauri) |
|---------|----------|--------------|
| **包大小** | 50-200MB | 5-20MB |
| **内存占用** | 200-500MB | 50-150MB |
| **启动速度** | 3-10秒 | 0.5-2秒 |
| **运行时依赖** | Node.js | 无（原生二进制） |
| **系统API** | 受限 | 完整系统权限 |
| **安全性** | 需要手动配置 | 默认沙箱 |

**架构差异图**：

```
Electron架构：
┌─────────────────────────────────────────┐
│           Chromium Browser               │
│  ┌─────────────────────────────────┐   │
│  │     Node.js Runtime (45MB+)      │   │
│  │  ┌───────────────────────────┐  │   │
│  │  │    Your App (Renderer)    │  │   │
│  │  └───────────────────────────┘  │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘

Pake架构：
┌─────────────────────────────────────────┐
│           System WebView (系统自带)       │
│  ┌─────────────────────────────────┐   │
│  │      Your App (只有你+UI)         │   │
│  └─────────────────────────────────┘   │
│           Rust Binary (5MB)             │
└─────────────────────────────────────────┘
```

---

## 快速上手

### 方式一：下载现成应用（推荐新手）

Pake官方提供了大量预构建的流行应用，直接下载即可使用：

| 应用 | macOS | Windows | Linux | 说明 |
|------|-------|---------|-------|------|
| **WeRead** | [下载](https://github.com/tw93/Pake/releases/latest/download/WeRead.dmg) | [下载](https://github.com/tw93/Pake/releases/latest/download/WeRead_x64.msi) | [下载](https://github.com/tw93/Pake/releases/latest/download/WeRead_x86_64.deb) | 微信读书 |
| **Twitter** | [下载](https://github.com/tw93/Pake/releases/latest/download/Twitter.dmg) | [下载](https://github.com/tw93/Pake/releases/latest/download/Twitter_x64.msi) | [下载](https://github.com/tw93/Pake/releases/latest/download/Twitter_x86_64.deb) | Twitter/X |
| **Grok** | [下载](https://github.com/tw93/Pake/releases/latest/download/Grok.dmg) | [下载](https://github.com/tw93/Pake/releases/latest/download/Grok_x64.msi) | [下载](https://github.com/tw93/Pake/releases/latest/download/Grok_x86_64.deb) | xAI Grok |
| **DeepSeek** | [下载](https://github.com/tw93/Pake/releases/latest/download/DeepSeek.dmg) | [下载](https://github.com/tw93/Pake/releases/latest/download/DeepSeek_x64.msi) | [下载](https://github.com/tw93/Pake/releases/latest/download/DeepSeek_x86_64.deb) | DeepSeek官网 |
| **ChatGPT** | [下载](https://github.com/tw93/Pake/releases/latest/download/ChatGPT.dmg) | [下载](https://github.com/tw93/Pake/releases/latest/download/ChatGPT_x64.msi) | [下载](https://github.com/tw93/Pake/releases/latest/download/ChatGPT_x86_64.deb) | OpenAI ChatGPT |
| **Gemini** | [下载](https://github.com/tw93/Pake/releases/latest/download/Gemini.dmg) | [下载](https://github.com/tw93/Pake/releases/latest/download/Gemini_x64.msi) | [下载](https://github.com/tw93/Pake/releases/latest/download/Gemini_x86_64.deb) | Google Gemini |
| **YouTube Music** | [下载](https://github.com/tw93/Pake/releases/latest/download/YouTubeMusic.dmg) | [下载](https://github.com/tw93/Pake/releases/latest/download/YouTubeMusic_x64.msi) | [下载](https://github.com/tw93/Pake/releases/latest/download/YouTubeMusic_x86_64.deb) | YouTube音乐 |
| **Excalidraw** | [下载](https://github.com/tw93/Pake/releases/latest/download/Excalidraw.dmg) | [下载](https://github.com/tw93/Pake/releases/latest/download/Excalidraw_x64.msi) | [下载](https://github.com/tw93/Pake/releases/latest/download/Excalidraw_x86_64.deb) | 白板协作工具 |
| **XiaoHongShu** | [下载](https://github.com/tw93/Pake/releases/latest/download/XiaoHongShu.dmg) | [下载](https://github.com/tw93/Pake/releases/latest/download/XiaoHongShu_x64.msi) | [下载](https://github.com/tw93/Pake/releases/latest/download/XiaoHongShu_x86_64.deb) | 小红书网页版 |

[更多应用下载](https://github.com/tw93/Pake/releases)

### 方式二：CLI命令行打包（推荐开发者）

**安装CLI工具**：

```bash
# 使用pnpm全局安装
pnpm install -g pake-cli
```

**基本用法**：

```bash
# 基础打包（自动获取网站图标）
pake https://github.com --name GitHub

# 高级用法（自定义配置）
pake https://weekly.tw93.fun \
  --name Weekly \
  --icon https://cdn.tw93.fun/pake/weekly.icns \
  --width 1200 \
  --height 800 \
  --hide-title-bar
```

**CLI参数说明**：

| 参数 | 说明 | 示例 |
|------|------|------|
| `--name` | 应用名称 | `--name MyApp` |
| `--icon` | 应用图标URL | `--icon https://.../icon.png` |
| `--width` | 窗口宽度 | `--width 1200` |
| `--height` | 窗口高度 | `--height 800` |
| `--hide-title-bar` | 隐藏标题栏 | 沉浸式体验 |
| `--user-agent` | 自定义User-Agent | 模拟移动端等 |

### 方式三：GitHub Actions在线构建（无需本地环境）

```yaml
# .github/workflows/pake.yml
name: Build Pake App

on:
  workflow_dispatch:
    inputs:
      url:
        description: 'Website URL'
        required: true
      name:
        description: 'App Name'
        required: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build with Pake
        uses: tw93/Pake@main
        with:
          url: ${{ github.event.inputs.url }}
          name: ${{ github.event.inputs.name }}
```

### 方式四：本地开发定制

**环境要求**：

- Rust >= 1.85
- Node >= 22

**开发步骤**：

```bash
# 1. 克隆项目
git clone https://github.com/tw93/Pake.git
cd Pake

# 2. 安装依赖
pnpm install

# 3. 本地开发调试
pnpm run dev  # 右键打开调试模式

# 4. 构建应用
pnpm run build
```

---

## 进阶用法

### 自定义样式

在项目根目录创建 `pake.config.js`：

```javascript
// pake.config.js
module.exports = {
  // 窗口配置
  windows: {
    width: 1200,
    height: 800,
    titleBarStyle: 'hidden', // macOS隐藏标题栏
  },
  
  // 注入CSS去除广告
  injectCSS: `
    .ad-banner { display: none !important; }
    .sidebar-ad { display: none !important; }
  `,
  
  // 注入JS增强功能
  injectJS: `
    // 禁用右键菜单
    document.addEventListener('contextmenu', e => e.preventDefault());
  `,
  
  // 图标
  icon: './assets/icon.png',
}
```

### 多窗口管理

```javascript
// 创建多个窗口
const { WebviewWindow } = window.__TAURI__.window;

// 打开新窗口
const webview = new WebviewWindow('second', {
  url: 'https://example.com',
  title: '新窗口',
  width: 800,
  height: 600,
});

webview.once('tauri://created', () => {
  console.log('窗口创建成功');
});

webview.once('tauri://error', (e) => {
  console.error('窗口创建失败:', e);
});
```

### 窗口通信

```javascript
// 主窗口发送消息
window.__TAURI__.event.emit('message', { 
  type: 'update', 
  data: 'Hello from main' 
});

// 子窗口接收消息
window.__TAURI__.event.listen('message', (event) => {
  console.log('Received:', event.payload);
});
```

---

## 应用场景分析

### 适用场景

| 场景 | 说明 | 示例 |
|------|------|------|
| **Web应用桌面化** | 将Web版应用变成原生体验 | ChatGPT、Notion |
| **内部工具** | 企业内部Web系统快速打包 | OA系统、CRM |
| **个人工具** | 常用网页一键桌面化 | Twitter、YouTube |
| **轻量级客户端** | 不需要Electron的重量 | 音乐播放器、阅读器 |
| **隐私敏感应用** | 避免Electron的全量权限 | 密码管理器 |

### 不适用场景

| 场景 | 原因 |
|------|------|
| **需要Node.js原生模块** | Tauri不支持Node原生模块 |
| **复杂系统托盘功能** | 功能相对Electron有限 |
| **需要多个BrowserWindow** | Tauri窗口模型不同 |
| **重度依赖Chrome扩展** | WebView不支持扩展API |

---

## 项目结构详解

```
Pake/
├── src-tauri/              # Rust后端核心
│   ├── src/
│   │   ├── main.rs       # 应用入口
│   │   ├── lib.rs        # 库定义
│   │   └── commands/     # Tauri命令
│   │       ├── window.rs # 窗口控制命令
│   │       ├── app.rs    # 应用控制命令
│   │       └── config.rs # 配置命令
│   ├── Cargo.toml        # Rust依赖
│   └── tauri.conf.json   # Tauri配置
│
├── bin/                   # CLI工具
│   ├── cli.ts           # 命令行入口
│   ├── build.ts         # 构建逻辑
│   └── icon.ts          # 图标处理
│
├── dist/                 # 构建产物输出
│   ├── macos/           # macOS应用
│   ├── windows/         # Windows安装包
│   └── linux/           # Linux包
│
├── docs/                 # 文档
│   ├── cli-usage.md     # CLI使用指南
│   ├── github-actions-usage.md
│   └── advanced-usage.md # 高级用法
│
├── package.json
├── pnpm-lock.yaml
└── pake.config.js       # 用户配置文件
```

---

## 常见问题FAQ

### Q: 打包后的应用安全吗？

**A**: Pake基于Tauri构建，默认使用系统WebView（macOS用WKWebView，Windows用WebView2，Linux用WebKitGTK），每个应用都是独立的沙箱环境。但需要注意：

- 应用可以访问完整的系统文件（需要用户授权）
- 建议只从可信来源打包应用
- 不要在打包的应用中输入敏感信息（除非是自己信任的应用）

### Q: 如何处理登录状态？

**A**: Pake支持Cookie持久化：

```javascript
// 首次登录后，下次打开应用会自动保持登录状态
// 如果需要强制重新登录，可以清除应用数据
```

### Q: 可以打包需要WebGL的应用吗？

**A**: 可以，Pake使用的WebView都支持WebGL。但如果WebGL性能不佳，可以考虑使用Tauri的webview tag配合原生OpenGL。

### Q: 如何调试打包后的应用？

```bash
# 开发模式启动
pnpm run dev

# 查看日志
# macOS: ~/Library/logs/tw93-Pake/
# Linux: ~/.local/share/tw93-Pake/logs/
# Windows: %APPDATA%\tw93-Pake\logs\
```

### Q: 为什么打包的应用比预期大？

可能原因：
1. 包含调试符号（发布版本应该用 `pnpm run build --release`）
2. 应用图标太大（建议PNG格式，256x256即可）
3. 多语言资源未剥离

---

## 与同类项目对比

| 项目 | 体积 | 性能 | 易用性 | 生态 |
|------|------|------|--------|------|
| **Electron** | 重（~100MB） | 一般 | ⭐⭐⭐⭐⭐ | 成熟 |
| **Pake** | 轻（~5MB） | 优秀 | ⭐⭐⭐⭐ | 活跃 |
| **Flutter Web** | 中（~30MB） | 优秀 | ⭐⭐⭐ | 一般 |
| **Tauri** | 轻（~10MB） | 优秀 | ⭐⭐⭐ | 活跃 |
| **Neutralino.js** | 轻（~1MB） | 优秀 | ⭐⭐⭐ | 一般 |

**Pake的优势**：
- 专门针对"网页桌面化"场景优化
- CLI工具开箱即用
- 预构建了大量流行应用
- 文档完善，中文支持好

---

## 总结

Pake是一个解决实际问题的开源项目：当你需要把一个网页变成桌面应用时，Electron太重、配置复杂，而Pake只需要一条命令就能完成。

**核心价值**：

1. **极简主义**：一行命令，打包完成
2. **性能优先**：Rust+Tauri，小而美
3. **开箱即用**：提供现成应用包
4. **开发者友好**：CLI工具完善

**推荐使用场景**：

- ✅ 将常用Web应用变成桌面客户端（ChatGPT、Twitter等）
- ✅ 快速打包内部Web工具
- ✅ 创建轻量级专用客户端
- ✅ 不适合需要复杂原生功能的场景

**项目地址**：[https://github.com/tw93/Pake](https://github.com/tw93/Pake)

---

*本文基于Pake V3.11.0版本编写，发布时间：2026-04-07*
