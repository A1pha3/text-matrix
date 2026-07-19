---
title: "jellium-desktop：Jellyfin 的非官方桌面客户端，CEF + mpv 双引擎"
date: 2026-07-20T03:02:36+08:00
categories: ["技术笔记"]
tags: ["jellyfin", "desktop-client", "rust", "cef", "mpv"]
description: "jellium-desktop 是一个非官方 Jellyfin 桌面客户端，基于 CEF 渲染 UI + mpv 播放视频，跨平台打包 Linux AppImage / macOS DMG / Windows installer，是 Jellyfin 官方没有桌面端时的可靠替代。"
---

# jellium-desktop：Jellyfin 的非官方桌面客户端，CEF + mpv 双引擎

## 一句话判断

jellium-desktop 解决的是一个非常具体的需求——**Jellyfin 没有官方桌面客户端**。它用 CEF（Chromium Embedded Framework，嵌入式 Chromium 框架）渲染 UI、mpv 做视频播放内核，跨平台打包成 Linux AppImage / macOS DMG / Windows installer，三平台原生体验。当前 1.2K stars 说明它在自托管媒体用户圈子里已经站稳了位置。

## 项目定位

- **仓库**：`andrewrabert/jellium-desktop`，GPL-2.0 协议，Rust 实现
- **GitHub Stars**：1.2K，Forks 107（2026-07-19 数据）
- **支持平台**：Linux（x86_64 / aarch64 AppImage + Flatpak）、macOS（Apple Silicon / Intel）、Windows（x64 / arm64）
- **构建工具**：[`just`](https://github.com/casey/just) 作为命令运行器
- **后端依赖**：[Jellyfin](https://jellyfin.org) Media Server（自托管媒体服务）

## 系统地图

| 模块 | 责任 | 技术选型 |
|------|------|----------|
| UI Layer | 渲染 Jellyfin Web UI 并提供桌面壳 | CEF（Chromium Embedded Framework） |
| Player | 视频 / 音频播放 | mpv（业界最强的开源视频播放器） |
| Jellyfin API Client | 跟 Jellyfin Server 通信 | HTTP API |
| Packager | 跨平台打包 | AppImage / DMG / MSIX |

CEF + mpv 的双引擎组合是 jellium-desktop 的核心设计选择：

- **CEF** 提供完整的 Chromium 渲染能力，可以直接承载 Jellyfin 的 Web UI，不做"原生 UI 控件 + WebView"的妥协方案
- **mpv** 是 Linux 社区最被信任的视频播放器，对硬解、字幕、色彩管理、HDR 都有完整支持，比 Electron 内置的 video 标签强得多

这两个引擎的组合让 jellium-desktop 在"自托管媒体客户端"这个细分赛道里做到接近 Plex Desktop Client 的体验，但完全开源、无云依赖。

## 关键机制拆解

### 1. 跨平台打包

README 给出的下载矩阵：

| 平台 | 格式 |
|------|------|
| Linux x86_64 | AppImage |
| Linux aarch64 | AppImage |
| Linux (任意) | Flatpak（非 Flathub bundle） |
| Arch Linux | AUR `jellium-desktop-git` |
| macOS Apple Silicon | DMG |
| macOS Intel | DMG |
| Windows x64 | MSI / MSIX bundle |
| Windows arm64 | MSI / MSIX bundle |

AppImage + Flatpak + AUR 三套 Linux 发行机制意味着无论用户用哪种 Linux 都能装。macOS 提供 Intel / Apple Silicon 双架构 DMG，但 README 提示安装后需要 `sudo xattr -cr /Applications/Jellium\ Desktop.app` 移除 quarantine。

### 2. just 命令运行器

项目用 [just](https://github.com/casey/just) 而非 Makefile 作为命令运行器。`just` 是 Rust 写的 Make 替代品，语法比 Make 简洁很多：

```makefile
# build
build          # Build the app
run *args      # Run the app
run-mpv *args  # Run the mpv CLI

# test
test           # Run tests

# lint
fmt            # Format workspace
clippy         # Lint workspace
strict-lint    # Strict lint workspace

# package
appimage ...   # Linux AppImage
flatpak ...    # Linux Flatpak
dmg            # macOS DMG
```

Rust 项目用 just 而不是 Makefile 是 2024 年后的常见选择——跨平台一致、语法简单、和 Cargo 工具链兼容。

### 3. nightly.link 分发

README 的下载链接全部指向 `nightly.link`，这是 GitHub Actions 的产物代理服务，让用户在不登录 GitHub 的情况下也能下载 nightly build。这意味着 jellium-desktop 没有传统的 release 节奏，每个 commit 都自动出 nightly——对开发体验友好，但对稳定性敏感的用户需要选 nightly link 而不是 latest release。

## 适用人群

- **Jellyfin Server 自托管用户**：想要一个原生桌面客户端，不想在浏览器里看片
- **Linux 桌面用户**：想要 AppImage / Flatpak / AUR 多种安装方式
- **追求 mpv 播放质量的人**：mpv 的硬解、HDR、字幕支持远超 Electron 自带 video 标签
- **想要跨平台一致体验的人**：macOS / Windows / Linux 三平台用同一个客户端

## 不适合谁

- **Jellyfin 用户基数小的人**：1.2K stars + 1 个 maintainer（andrewrabert）的项目长期维护风险需要自己评估
- **想要商业级 SLA 的人**：没有商业支持，遇到问题只能 GitHub Issues
- **macOS Apple Silicon 用户需要 catalyst 优化的人**：DMG 是 Intel 兼容包，不是 Universal Binary 优化

## 仓库地址

https://github.com/andrewrabert/jellium-desktop

## 阅读路径建议

1. 下载对应平台的二进制包，安装后跑通
2. 配 Jellyfin Server URL，验证登录 / 列表 / 播放三条链路
3. 看 [just](https://github.com/casey/just) 的 recipe 列表，了解 build / package 流程
4. 如果要贡献，读源码前先跑 `just strict-lint`，确保环境干净