---
title: "Lightpanda Browser：25.5k Stars 从零构建的 Zig 无头浏览器"
date: "2026-03-28T21:30:00+08:00"
slug: "lightpanda-browser-zig-headless"
aliases:
  - /posts/tech/lightpanda-browser-zig-headless/
description: "深度解读 Lightpanda Browser：25.5k Stars 的 AI 自动化无头浏览器，从零构建（非 Chromium Fork）、用 Zig 编写、内存占用仅 Chrome 的 1/9、速度提升 11 倍。"
draft: false
categories: ["技术笔记"]
tags: ["Lightpanda", "无头浏览器", "Zig", "AI自动化", "CDP"]
---

# Lightpanda Browser：25.5k Stars 从零构建的 Zig 无头浏览器

> **目标读者**：需要无头浏览器进行 AI 自动化、爬虫、测试的开发者
> **核心问题**：Chrome 太重太慢，有没有轻量替代品？
> **难度**：⭐⭐⭐⭐（专家设计）
> **来源**：GitHub lightpanda-io/browser，2026-03-28

---

## 一、项目概览

### 1.1 为什么这个项目值得关注

[Lightpanda Browser](https://github.com/lightpanda-io/browser) 是专为 AI 和自动化设计的**从零构建的无头浏览器**，不使用 Chromium 或 WebKit，使用 Zig（系统编程语言）编写。

**核心数据：**

| 指标 | 数值 |
|------|------|
| GitHub Stars | **25.5k** |
| Forks | 1k |
| Contributors | 38 |
| License | AGPL-3.0 |
| 语言 | Zig 74.3%、HTML 24.6% |

**核心优势：**

| 特性 | Lightpanda | Chrome |
|------|-----------|--------|
| **内存占用** | 超低（9x less） | 基准 |
| **执行速度** | 超快（11x faster） | 基准 |
| **启动时间** | 即时 | 较慢 |
| **二进制大小** | ~50MB | ~300MB+ |

### 1.2 定位

> The headless browser built from scratch for AI agents and automation.
> Not a Chromium fork. Not a WebKit patch. A new browser, written in Zig.

**不是 Chromium Fork，也不是 WebKit 补丁。是从零开始构建的全新浏览器。**

### 1.3 为什么需要新浏览器

**现代网页离不开 JavaScript：**

- Ajax、单页应用、无限加载、"点击显示"、即时搜索等
- React、Vue、Angular 等 JS 框架无处不在

**Chrome 不是正确工具：**

- 内存和 CPU 占用重，运行成本高
- 难以打包、部署和维护
- 功能过于臃肿，无头场景用不上

**Lightpanda 的设计理念：**

- 不基于 Chromium、Blink 或 WebKit
- 使用底层系统编程语言（Zig）优化性能
- 专为无头场景设计，无图形渲染

---

## 二、核心特性

### 2.1 已实现的功能

| 功能 | 说明 | 状态 |
|------|------|------|
| **JavaScript 执行**（v8 JavaScript 引擎） | 执行 JS | ✅ |
| **HTML 解析器** | html5ever | ✅ |
| **HTTP 加载器** | Libcurl | ✅ |
| **DOM 树** | 完整 DOM 结构 | ✅ |
| **DOM APIs** | 标准 DOM 接口 | ✅ |
| **Ajax** | XHR API + Fetch API | ✅ |
| **DOM dump** | 页面内容导出 | ✅ |
| **CDP/WebSocket 服务器**（Chrome DevTools Protocol） | 调试协议 | ✅ |
| **Click** | 元素点击 | ✅ |
| **Input form** | 表单输入 | ✅ |
| **Cookies** | Cookie 管理 | ✅ |
| **Custom HTTP headers** | 自定义请求头 | ✅ |
| **Proxy support** | 代理支持 | ✅ |
| **Network interception** | 网络拦截 | ✅ |
| **robots.txt** | `--obey-robots` 选项 | ✅ |

### 2.2 缺失的功能（进行中）

| 功能 | 说明 | 状态 |
|------|------|------|
| **CORS** | 跨域资源共享 | ❌ 进行中 |

> NOTE: Web APIs 有数百个，开发浏览器（即使只是无头模式）工作量巨大，功能会随时间完善。

---

## 三、与传统浏览器对比

### 3.1 性能对比

| 指标 | Lightpanda | Chrome | 备注 |
|------|-------------|--------|------|
| **内存占用** | 最低 | 基准 | 9x less |
| **执行速度** | 最快 | 基准 | 11x faster |
| **启动时间** | 即时 | 较慢 | - |
| **二进制大小** | ~50MB | ~300MB+ | - |

### 3.2 兼容性

| 工具 | 兼容性 | 说明 |
|------|--------|------|
| **Playwright** | ✅ | 通过 CDP |
| **Puppeteer** | ✅ | 通过 CDP |
| **chromedp** | ✅ | 通过 CDP |

### 3.3 技术栈对比

| 组件 | Lightpanda | Chromium |
|------|-----------|----------|
| **渲染引擎** | 从零构建 | Blink |
| **JS 引擎** | v8 | v8 |
| **HTML 解析器** | html5ever | Blink HTML 解析器 |
| **HTTP 客户端** | Libcurl | Chromium 网络栈 |
| **开发语言** | Zig | C++ |
| **许可证** | AGPL-3.0 | BSD |

---

## 四、快速开始

### 4.1 安装（夜间构建）

**Linux：**

```bash
curl -L -o lightpanda \
  https://github.com/lightpanda-io/browser/releases/download/nightly/lightpanda-x86_64-linux && \
chmod a+x ./lightpanda
```

**macOS：**

```bash
curl -L -o lightpanda \
  https://github.com/lightpanda-io/browser/releases/download/nightly/lightpanda-aarch64-macos && \
chmod a+x ./lightpanda
```

### 4.2 Docker 安装

```bash
docker run -d --name lightpanda -p 9222:9222 lightpanda/browser:nightly
```

支持 Linux amd64 和 arm64 架构。

### 4.3 基本使用

**抓取网页：**

```bash
./lightpanda fetch --obey-robots --log-format pretty \
  --log-level info https://example.com/
```

**启动 CDP 服务器：**

```bash
./lightpanda serve --obey-robots --log-format pretty \
  --log-level info --host 127.0.0.1 --port 9222
```

### 4.4 Puppeteer 示例

```javascript
'use strict'
import puppeteer from 'puppeteer-core';

const browser = await puppeteer.connect({
  browserWSEndpoint: "ws://127.0.0.1:9222",
});

const context = await browser.createBrowserContext();
const page = await context.newPage();

await page.goto('https://example.com/', {waitUntil: "networkidle0"});

const links = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('a')).map(a => a.getAttribute('href'));
});

console.log(links);

await page.close();
await browser.disconnect();
```

---

## 五、从源码构建

### 5.1 环境要求

| 工具 | 版本 |
|------|------|
| Zig | 0.15.2 |
| Rust | 最新版 |
| CMake | - |
| libglib2.0-dev | - |

**Debian/Ubuntu：**

```bash
sudo apt install xz-utils ca-certificates \
  pkg-config libglib2.0-dev \
  clang make curl git
```

**macOS：**

```bash
brew install cmake
```

**Nix（推荐）：**

```bash
nix develop
```

### 5.2 构建步骤

```bash
# 克隆仓库
git clone https://github.com/lightpanda-io/browser.git
cd browser

# Debug 构建
make build-dev

# Release 构建
make build

# 直接运行
zig build run
```

### 5.3 嵌入 v8 Snapshot

```bash
# 生成 snapshot
zig build snapshot_creator -- src/snapshot.bin

# 使用 snapshot 构建
zig build -Dsnapshot_path=../../snapshot.bin
```

---

## 六、测试

### 6.1 单元测试

```bash
make test
```

### 6.2 端到端测试

```bash
# 克隆 demo 仓库到 ../demo
# 安装依赖
make end2end
```

### 6.3 Web Platform Tests

Lightpanda 通过标准化 Web Platform Tests 测试：

```bash
# 克隆 WPT fork
git clone -b fork --depth=1 git@github.com:lightpanda-io/wpt.git

# 配置 hosts
./wpt make-hosts-file | sudo tee -a /etc/hosts

# 生成 MANIFEST
./wpt manifest

# 启动 WPT HTTP 服务器
./wpt serve

# 运行 Lightpanda
zig build run -- --insecure-disable-tls-host-verification

# 运行 wptrunner
cd wptrunner && go run .
```

---

## 七、适用场景

| 场景 | 说明 |
|------|------|
| **AI 自动化** | AI Agent 网页交互 |
| **网页爬虫** | 需要 JS 执行的动态页面 |
| **LLM 训练数据** | 网页内容抓取 |
| **自动化测试** | UI 测试 |
| **网页截图** | 无头渲染 |

---

## 八、资源链接

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/lightpanda-io/browser |
| 官网 | https://lightpanda.io |
| Discord | https://discord.gg/K63XeymfB5 |
| Twitter | https://twitter.com/lightpanda_io |
| Docker Hub | https://hub.docker.com/r/lightpanda/browser |

---

## 九、总结与展望

### 9.1 核心价值

Lightpanda 的核心价值在于**为 AI 和自动化场景提供轻量级高性能的无头浏览器解决方案**。

| 传统方式 | Lightpanda 方式 |
|----------|----------------|
| Chromium Fork | 从零构建，全新架构 |
| C++ | Zig 底层系统编程 |
| 臃肿功能 | 专为无头场景优化 |
| 高内存占用 | 9x 内存节省 |
| 慢启动 | 即时启动 |

### 9.2 技术亮点

1. **从零构建**：不是 Chromium Fork，不是 WebKit 补丁
2. **Zig 语言**：底层系统编程，极致性能优化
3. **CDP 兼容**：无缝接入 Playwright/Puppeteer/chromedp
4. **极致性能**：内存 1/9，速度 11x
5. **AGPL 开源**：完全开源可定制

### 9.3 未来展望

| 功能 | 状态 |
|------|------|
| CORS 支持 | 进行中 |
| 更多 Web API | 持续完善 |
| Windows 原生支持 | 规划中 |

---

**相关话题标签**

#Lightpanda #无头浏览器 #Zig #AI自动化 #CDP #浏览器

**来源**

- GitHub：https://github.com/lightpanda-io/browser

---

*Lightpanda Browser 由 lightpanda-io 开发，采用 AGPL-3.0 许可证，使用 Zig 语言从零构建。*
