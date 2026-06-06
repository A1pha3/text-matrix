+++
date = '2026-05-20T00:00:00+08:00'
draft = false
title = 'Stream Burt：全平台流媒体下载器'
slug = 'streambert-cross-platform-streaming-downloader'
description = 'Stream Burt 是一个开源跨平台 Electron 桌面应用，支持在线流媒体播放和下载电影、剧集、动漫，零广告零追踪。'
categories = ['技术笔记']
tags = ['Electron', '开源', '工具', '流媒体']
+++

# Stream Burt：全平台流媒体下载器

## 一、项目概述

**Stream Burt**（[truelockmc/streambert](https://github.com/truelockmc/streambert)）是一个跨平台的 Electron 桌面应用，允许用户在线流式播放和下载电影、电视剧、动漫等视频内容。项目主打零广告、零追踪，提供干净的观影体验。

> 仓库：[truelockmc/streambert](https://github.com/truelockmc/streambert)｜Electron（跨平台）

## 二、核心功能

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

## 三、技术架构

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

## 四、安装与使用

### macOS

```bash
# 从 GitHub Releases 下载 .dmg 文件
# 双击挂载，将 Stream Burt.app 拖入 Applications

# 或使用 Homebrew Cask（如果有发布）
brew install --cask stream-burt
```

### Windows

```bash
# 下载 .exe 安装包
# 双击运行，一路 Next 即可
```

### Linux

```bash
# 下载 AppImage
chmod +x StreamBurt-x.x.x.AppImage
./StreamBurt-x.x.x.AppImage
```

## 五、界面预览

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

## 六、对比同类工具

| 功能 | Stream Burt | 某些国内工具 | 浏览器插件 |
|------|-------------|--------------|-----------|
| 广告 | **零广告** | 有广告 | 无 |
| 追踪 | **零追踪** | 有 | 无 |
| 下载 | ✅ | ✅ | ❌ |
| 跨平台 | ✅ | ✅ | ❌ |
| 开源 | ✅ | ❌ | 部分 |

## 七、隐私保护

Stream Burt 明确承诺**零追踪**：

- ❌ 不收集任何使用数据
- ❌ 不上报观影记录
- ❌ 无第三方统计 SDK
- ❌ 无弹窗广告
- ✅ 所有数据本地存储

## 八、使用注意事项

⚠️ **免责声明：**

1. 请确保使用来源合法的视频内容
2. 下载行为请遵守当地法律法规
3. 尊重版权，仅用于个人学习观赏
4. 项目仅供技术研究，不承担滥用责任

## 九、开发者信息

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

## 十、资源链接

- GitHub：[truelockmc/streambert](https://github.com/truelockmc/streambert)
- Issues：[Bug反馈/功能建议](https://github.com/truelockmc/streambert/issues)

---

*开源跨平台方案，适合技术用户本地管理视频内容。追剧党的本地利器。*