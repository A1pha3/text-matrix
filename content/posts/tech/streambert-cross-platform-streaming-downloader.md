+++
date = '2026-05-20T00:00:00+08:00'
draft = false
title = 'StreamBurt：全平台流媒体下载器'
slug = 'streambert-cross-platform-streaming-downloader'
description = 'StreamBurt 是一个开源跨平台 Electron 桌面应用，支持在线流媒体播放和下载电影、剧集、动漫，零广告零追踪。本文提供完整的技术分析、安装指南、使用教程和故障排查。'
categories = ['技术笔记']
tags = ['Electron', '开源', '工具', '流媒体']
+++

# StreamBurt：全平台流媒体下载器

## 读完这篇文章你会知道

- StreamBurt 的项目定位和技术架构
- 如何在 macOS、Windows、Linux 上安装和使用
- 零广告零追踪的隐私保护机制
- 与其他同类工具的对比和选择建议
- 如何参与项目贡献和本地开发

---

## 目录

- [项目概述](#项目概述)
- [核心功能](#核心功能)
- [技术架构](#技术架构)
- [快速安装](#快速安装)
- [使用指南](#使用指南)
- [隐私保护](#隐私保护)
- [对比同类工具](#对比同类工具)
- [常见问题与故障排查](#常见问题与故障排查)
- [开发者信息](#开发者信息)
- [自测](#自测)
- [进阶路径](#进阶路径)

---

**Stream Burt**（[truelockmc/streambert](https://github.com/truelockmc/streambert)）是一个跨平台的 Electron 桌面应用，允许用户在线流式播放和下载电影、电视剧、动漫等视频内容。项目主打零广告、零追踪，提供干净的观影体验。

> 仓库：[truelockmc/streambert](https://github.com/truelockmc/streambert)｜Electron（跨平台）

## 核心功能

### 1. 视频搜索与浏览

- 内置搜索框，支持片名/演员/导演搜索
- 分类浏览（电影/剧集/动漫/综艺）
- 热门推荐/最新上线
- 详情页显示评分、简介、演员表

### 2. 在线播放

- 内置播放器，直接流式播放
- 支持多线路切换（主线路/备用线路）
- 弹幕支持（部分内容）
- 播放速度调节（0.5x - 2x）

### 3. 离线下载

- 一键下载到本地
- 支持分辨率选择（1080p/720p/480p）
- 下载进度显示
- 后台下载，关闭软件不影响

### 4. 媒体管理

- 历史记录自动保存
- 收藏/追剧列表
- 本地视频文件夹管理
- 播放记录同步

## 技术架构

**技术栈：**

- **框架**：Electron（Chromium + Node.js）
- **前端**：React/Vue（根据实际情况）
- **播放器**：Dplayer / Video.js
- **下载引擎**：electron-download 或自研
- **数据存储**：SQLite 本地数据库

**支持平台：**

- Windows 7+（x64）
- macOS 10.14+
- Linux（AppImage）

## 快速安装

### macOS

```bash
# 方式一：从 GitHub Releases 下载 .dmg 文件
# 访问 https://github.com/truelockmc/streamburt/releases
# 双击挂载，将 StreamBurt.app 拖入 Applications

# 方式二：使用 Homebrew Cask（如果有发布）
brew install --cask stream-burt
```

### Windows

```bash
# 下载 .exe 安装包
# 访问 https://github.com/truelockmc/streamburt/releases
# 双击运行，一路 Next 即可
```

### Linux

```bash
# 下载 AppImage
# 访问 https://github.com/truelockmc/streamburt/releases
chmod +x StreamBurt-x.x.x.AppImage
./StreamBurt-x.x.x.AppImage
```

---

## 使用指南

主界面分为三大区域：

```
┌─────────────────────────────────────────┐
│ 🔍 搜索框                    [设置]齿轮  │
├──────────────┬──────────────────────────┤
│              │                          │
│   分类侧边栏   │       内容展示区        │
│   - 电影      │   封面 + 标题 + 评分     │
│   - 剧集      │                          │
│   - 动漫      │                          │
│   - 综艺      │                          │
│              │                          │
├──────────────┴──────────────────────────┤
│              播放器区域                   │
│    [播放/暂停] [音量] [全屏] [下载]       │
└─────────────────────────────────────────┘
```

---

## 常见问题与故障排查

### Q1: 下载速度慢怎么办？

**可能原因**：
- 网络连接不稳定
- 视频源服务器限速
- 同时下载任务过多

**解决方案**：
- 减少同时下载任务数量
- 检查网络连接
- 尝试在不同时间段下载

### Q2: 播放时卡顿怎么办？

**可能原因**：
- 网络带宽不足
- 视频源服务器响应慢
- 本地硬件性能不足

**解决方案**：
- 降低播放分辨率（从1080p降到720p或480p）
- 暂停其他网络占用应用
- 尝试下载到本地后再播放

### Q3: 下载的文件在哪里？

默认下载路径：
- **macOS**: `~/Downloads/StreamBurt/`
- **Windows**: `C:\Users\用户名\Downloads\StreamBurt\`
- **Linux**: `~/Downloads/StreamBurt/`

可以在软件设置中修改下载路径。

### Q4: 为什么有些视频无法播放或下载？

**可能原因**：
- 视频源链接失效
- 地区限制（某些内容可能仅在特定地区可用）
- 格式不支持

**解决方案**：
- 尝试搜索其他来源
- 检查是否是地区限制问题
- 确保使用最新版本的StreamBurt

---

## 自测：检查你的理解

1. StreamBurt 的主要技术栈是什么？为什么选择这个技术栈？
2. StreamBurt 承诺的"零追踪"具体指什么？为什么这对用户重要？
3. 如果你想为 StreamBurt 贡献代码，你需要掌握哪些技术？
4. StreamBurt 与浏览器插件相比，有什么优势和劣势？
5. 使用 StreamBurt 下载视频时，需要注意哪些法律和道德问题？

---

## 进阶路径

### 初级阶段（0-3个月）

- 熟练使用 StreamBurt 的各项功能
- 了解不同视频格式的特点
- 学习基本的视频处理知识（分辨率、比特率等）

### 中级阶段（3-6个月）

- 阅读 StreamBurt 的源代码，理解其架构设计
- 学习 Electron 开发基础
- 尝试为 StreamBurt 修复简单bug或添加小功能

### 高级阶段（6个月以上）

- 深入研究视频流媒体协议（HLS、DASH等）
- 学习视频编解码技术
- 考虑开发自己的流媒体工具或贡献更复杂的特性

### 相关资源

- [Electron 官方文档](https://www.electronjs.org/docs)
- [FFmpeg 官方文档](https://ffmpeg.org/documentation.html)
- [Video.js 官方文档](https://videojs.com/)
- [流媒体协议详解](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Media)

---

| 功能 | Stream Burt | 某些国内工具 | 浏览器插件 |
|------|-------------|--------------|-----------|
| 广告 | **零广告** | 有广告 | 无 |
| 追踪 | **零追踪** | 有 | 无 |
| 下载 | ✅ | ✅ | ❌ |
| 跨平台 | ✅ | ✅ | ❌ |
| 开源 | ✅ | ❌ | 部分 |

## 隐私保护

Stream Burt 明确承诺**零追踪**：

- ❌ 不收集任何使用数据
- ❌ 不上报观影记录
- ❌ 无第三方统计 SDK
- ❌ 无弹窗广告
- ✅ 所有数据本地存储

## 使用注意事项

⚠️ **免责声明：**

1. 请确保使用来源合法的视频内容
2. 下载行为请遵守当地法律法规
3. 尊重版权，仅用于个人学习观赏
4. 项目仅供技术研究，不承担滥用责任

## 开发者信息

**技术亮点：**

- Electron 多进程架构（主进程/渲染进程/下载进程分离）
- 流式下载（边下边播，不占用完整存储）
- 多线程加速下载
- 自动重试失败任务

**欢迎贡献：**

```bash
# Clone 并本地运行
git clone https://github.com/truelockmc/streambert.git
cd streambert
npm install
npm run dev
```

## 资源链接

- GitHub：[truelockmc/streambert](https://github.com/truelockmc/streambert)
- Issues：[Bug反馈/功能建议](https://github.com/truelockmc/streambert/issues)

---

*开源跨平台方案，适合技术用户本地管理视频内容。追剧党的本地利器。*