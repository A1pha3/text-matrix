---
title: "awesome-mac：17K Stars·macOS软件资源大全·开发者工具/设计/媒体/效率工具"
date: "2026-04-12T02:29:31+08:00"
slug: awesome-mac-macos-software-resource-guide
description: "awesome-mac 是一个精心策划的 macOS 应用资源集合，收录了各类优质的 macOS 软件，涵盖开发者工具、设计工具、媒体工具、游戏、效率工具等多个领域。"
draft: false
categories: ["技术笔记"]
tags: ["macOS", "Homebrew", "开发工具", "效率工具", "软件"]
---

# awesome-mac：17K Stars·macOS 软件资源大全·开发者工具/设计/媒体/效率工具·Homebrew/Mac App Store

## 一，项目概述

### 1.1 awesome-mac 是什么

**awesome-mac** 是一个精心策划的 **macOS 应用资源集合**，收录了各类优质的 macOS 软件，涵盖开发者工具、设计工具、媒体工具、游戏、效率工具等多个领域。

> " This project is a curated collection of quality macOS applications"

**核心理念**：为 macOS 用户提供一站式的软件推荐导航，从开发环境到日常效率工具全覆盖。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | **17k** ⭐ |
| Forks | 1.7k |
| 许可证 | **CC0-1.0** (公共领域) |
| 最新更新 | **2026-04-11** |

### 1.3 软件分类

```
┌─────────────────────────────────────────────────────────────┐
│                    awesome-mac 软件分类                                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   💻 开发者工具                   │ 🎨 设计工具                           │
│   ├── IDEs                        │ ├── 设计软件                           │
│   ├── 终端                        │ ├── 图像处理                           │
│   ├── 版本控制                     │ ├── 颜色工具                           │
│   ├── 数据库                      │ └── 字体管理                           │
│                                                               │
│   📦 系统工具                     │ 🎮 游戏                               │
│   ├── Homebrew                   │ ├── Mac 游戏                           │
│   ├── 窗口管理                   │ └── 云游戏                            │
│   ├── 截图工具                   │                                       │
│                                                               │
│   🎵 媒体工具                    │ 📚 学习工具                           │
│   ├── 音频处理                   │ ├── RSS 阅读                          │
│   ├── 视频处理                   │ ├── 电子书                            │
│   └── 下载工具                   │ └── 编程学习                          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 二，开发者工具

### 2.1 IDEs & 编辑器

```bash
# 推荐的 macOS IDE 和编辑器
# ==========================================

# 1. Visual Studio Code
# https://code.visualstudio.com/
# 轻量级但强大的代码编辑器
brew install --cask visual-studio-code

# 2. JetBrains 全家桶
# https://www.jetbrains.com/
# IntelliJ IDEA / PyCharm / WebStorm / Rider
brew install --cask intellij-idea
brew install --cask pycharm
brew install --cask webstorm

# 3. Sublime Text
# https://www.sublimetext.com/
# 速度和优雅并重的编辑器
brew install --cask sublime-text

# 4. BBEdit
# https://www.barebones.com/products/bbedit/
# macOS 原生文本编辑器
brew install --cask bbedit

# 5. Nova
# https://nova.app/
# Panic 出品，现代化 IDE
brew install --cask nova
```

### 2.2 终端工具

```bash
# ==========================================
# macOS 终端工具推荐
# ==========================================

# iTerm2 - 终端模拟器
# https://iterm2.com/
brew install --cask iterm2

# Warp - 现代终端
# https://www.warp.dev/
brew install --cask warp

# Hyper - 基于 Electron 的终端
# https://hyper.is/
brew install --cask hyper

# Alacritty - GPU 加速终端
# https://alacritty.org/
brew install --cask alacritty

# kitty - 跨平台终端
# https://sw.kovidgoyal.net/kitty/
brew install --cask kitty

# Fish Shell - 智能 shell
# https://fishshell.com/
brew install fish
```

### 2.3 版本控制

```bash
# ==========================================
# Git 和版本控制工具
# ==========================================

# Git
brew install git

# GitHub Desktop - GitHub 官方客户端
# https://desktop.github.com/
brew install --cask github

# Sourcetree - Git 客户端
# https://www.sourcetree.com/
brew install --cask sourcetree

# GitKraken - 跨平台 Git 客户端
# https://www.gitkraken.com/
brew install --cask gitkraken

# Sublime Merge - Sublime Text 出品
# https://www.sublimemerge.com/
brew install --cask sublime-merge

# Tower - 专业 Git 客户端
# https://www.git-tower.com/
brew install --cask tower

# Lazygit - 终端 Git UI（本文档已介绍）
# https://github.com/jesseduffield/lazygit
brew install lazygit
```

### 2.4 数据库工具

```bash
# ==========================================
# 数据库管理工具
# ==========================================

# TablePlus - 多数据库客户端
# https://tableplus.com/
brew install --cask tableplus

# DataGrip - JetBrains 出品
# https://www.jetbrains.com/datagrip/
brew install --cask datagrip

# Postico - PostgreSQL 客户端
# https://eggerapps.at/postico/
brew install --cask postico

# PSequel - PostgreSQL GUI
# https://www.psequel.com/
brew install --cask psequel

# MongoDB Compass - MongoDB GUI
# https://www.mongodb.com/products/compass
brew install --cask mongodb-compass

# RedisInsight - Redis GUI
# https://redis.com/redis-enterprise/redis-insight/
brew install --cask redis-insight

# Azure Data Studio - SQL Server / PostgreSQL
# https://docs.microsoft.com/en-us/sql/azure-data-studio/
brew install --cask azure-data-studio
```

## 三，设计工具

### 3.1 设计软件

```bash
# ==========================================
# 设计工具推荐
# ==========================================

# Figma - 协建设计工具
# https://www.figma.com/
# Web / macOS 通用
# Free tier 可用

# Sketch - macOS 原生设计工具
# https://www.sketch.com/
brew install --cask sketch

# Adobe 全家桶
brew install --cask adobe-photoshop
brew install --cask adobe-illustrator
brew install --cask adobe-xd

# Affinity Designer - 矢量图形设计
# https://affinity.serif.com/designer/
brew install --cask affinity-designer

# Affinity Photo - 照片编辑
# https://affinity.serif.com/photo/
brew install --cask affinity-photo

# Affinity Publisher - 出版设计
# https://affinity.serif.com/publisher/
brew install --cask affinity-publisher

# Canva - 在线设计工具
# https://www.canva.com/
# Web 通用
```

### 3.2 图像处理

```bash
# ==========================================
# 图像处理工具
# ==========================================

# Pixelmator Pro - 图像编辑
# https://www.pixelmator.com/pro/
brew install --cask pixelmator-pro

# Acorn - 图像编辑器
# https://flyingmeat.com/acorn/
brew install --cask acorn

# GIMP - 开源图像编辑器
# https://www.gimp.org/
brew install --cask gimp

# ImageOptim - 图像压缩优化
# https://imageoptim.com/
brew install --cask imageoptim

# Squoosh - WebP/AVIF 压缩
# https://squoosh.app/
# Web 工具

# Lens Studio - Snapchat 滤镜
# https://ar.snap.com/lens-studio
brew install --cask lens-studio
```

### 3.3 颜色工具

```bash
# ==========================================
# 颜色工具
# ==========================================

# ColorSnapper - 取色器
# https://colorsnapper.com/
brew install --cask colorsnapper

# Sip - 颜色采样器
# https://sipapp.io/
brew install --cask sip

# Just Color Picker - 取色工具
# https://justdocolor.com/
brew install --cask just-color-picker

# Palette Master - 配色工具
# https://www.palettemaster.com/
# Free

# Color Handoff - 设计交接
# https://colorhandoff.com/
# Web
```

## 四，系统工具

### 4.1 Homebrew

```bash
# ==========================================
# Homebrew - macOS 包管理器
# ==========================================

# 安装 Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 常用命令
brew update                    # 更新
brew upgrade                   # 升级所有包
brew install <package>         # 安装包
brew install --cask <app>      # 安装应用
brew list                      # 列出已安装
brew uninstall <package>       # 卸载
brew search <keyword>          # 搜索
brew info <package>            # 查看信息
brew cleanup                   # 清理旧版本

# 常用开发工具
brew install git               # Git
brew install node              # Node.js
brew install python             # Python
brew install go                # Go
brew install rust              # Rust
brew install docker             # Docker
brew install kubectl           # Kubernetes
brew install terraform         # Terraform
brew install ansible           # Ansible

# 常用 macOS 应用
brew install --cask google-chrome    # Chrome
brew install --cask firefox           # Firefox
brew install --cask slack             # Slack
brew install --cask discord          # Discord
brew install --cask zoom             # Zoom
brew install --cask 1password         # 1Password
brew install --cask raycast          # Raycast
```

### 4.2 窗口管理

```bash
# ==========================================
# 窗口管理工具
# ==========================================

# Rectangle - 开源窗口管理
# https://rectangleapp.com/
brew install --cask rectangle

# Magnet - 窗口管理器
# https://magnet.crowdcafe.com/
brew install --cask magnet

# BetterTouchTool - 触控板增强
# https://folivora.ai/
brew install --cask bettertouchtool

# Amethyst - 平铺窗口管理器
# https://ianyh.com/amethyst/
brew install --cask amethyst

# kwm - 窗口管理器
# https://koekeishiya.github.io/kwm/
brew install --cask koekeishiya-formula/kwm/kwm

# yabai - 窗口管理器
# https://github.com/koekeishiya/yabai
brew install yabai

# Raycast - 快速启动器
# https://www.raycast.com/
brew install --cask raycast
```

### 4.3 截图工具

```bash
# ==========================================
# 截图和录屏工具
# ==========================================

# CleanShot X - 增强截图
# https://cleanshot.com/
brew install --cask cleanshot

# Skitch - 截图标注
# https://evernote.com/products/skitch
brew install --cask skitch

# Lightshot - 快速截图
# https://app.prntscr.com/
brew install --cask lightshot

# Kap - 录屏工具
# https://getkap.co/
brew install --cask kap

# ScreenFlow - 录屏编辑
# https://www.telestream.net/screenflow/
brew install --cask screenflow

# OBS - 开源录屏
# https://obsproject.com/
brew install --cask obs
```

## 五，媒体工具

### 5.1 音频处理

```bash
# ==========================================
# 音频处理工具
# ==========================================

# Audacity - 开源音频编辑器
# https://www.audacityteam.org/
brew install --cask audacity

# GarageBand - Apple 出品
# 预装应用

# Logic Pro - Apple 专业音频
# https://www.apple.com/logic-pro/
# App Store

# Adobe Audition
# https://www.adobe.com/products/audition.html
brew install --cask adobe-audition

# Soundflower - 音频路由
# https://github.com/mattingalls/Soundflower
brew install --cask soundflower

# Audio Hijack - 音频捕获
# https://www.rogueamoeba.com/audiohijack/
brew install --cask audio-hijack

# Figma - 音频处理
# https://figma.com/
```

### 5.2 视频处理

```bash
# ==========================================
# 视频处理工具
# ==========================================

# DaVinci Resolve - 免费调色
# https://www.blackmagicdesign.com/products/davinciresolve/
brew install --cask davinci-resolve

# Final Cut Pro - Apple 专业视频
# https://www.apple.com/final-cut-pro/
# App Store

# Adobe Premiere Pro
# https://www.adobe.com/products/premiere.html
brew install --cask adobe-premiere-pro

# HandBrake - 视频转码
# https://handbrake.fr/
brew install --cask handbrake

# FFmpeg - 命令行视频工具
# https://ffmpeg.org/
brew install ffmpeg

# IINA - 视频播放器
# https://iina.io/
brew install --cask iina

# VLC - 媒体播放器
# https://www.videolan.org/
brew install --cask vlc

# Permute - 媒体转换
# https://www.chamo.noisekeeper.com/
brew install --cask permute
```

## 六，效率工具

### 6.1 下载工具

```bash
# ==========================================
# 下载工具
# ==========================================

# Folx - 下载管理器
# https://mac.eltima.com/download-manager/
brew install --cask folx

# JDownloader - 下载管理器
# https://jdownloader.org/
brew install --cask jdownloader

# uGet - 下载管理器
# https://ugetdm.com/
brew install --cask uget

# Downie - 视频下载
# https://software.charliemonto.net/downie/
brew install --cask downie

# YouTube Downloader
# https://ytdl-org.github.io/youtube-dl/
brew install youtube-dl

# yt-dlp - YouTube 下载
# https://github.com/yt-dlp/yt-dlp
brew install yt-dlp
```

### 6.2 笔记工具

```bash
# ==========================================
# 笔记和知识管理
# ==========================================

# Notion - 笔记和协作
# https://www.notion.so/
brew install --cask notion

# Obsidian - Markdown 笔记
# https://obsidian.md/
brew install --cask obsidian

# Bear - Markdown 笔记
# https://bear.app/
brew install --cask bear

# Apple Notes - 预装
# 预装应用

# Evernote
# https://www.evernote.com/
brew install --cask evernote

# Craft - 文档工具
# https://www.craft.do/
brew install --cask craft

# Logseq - 大纲笔记
# https://logseq.com/
brew install --cask logseq
```

### 6.3 RSS 阅读器

```bash
# ==========================================
# RSS 阅读器
# ==========================================

# Reeder - RSS 阅读器
# https://reederapp.com/
brew install --cask reeder

# NetNewsWire - RSS 阅读器
# https://netnewswire.com/
brew install --cask netnewswire

# Vienna - 开源 RSS 阅读器
# https://www.vienna-rss.com/
brew install --cask vienna

# Fresh RSS - 自建 RSS 服务
# https://www.freshrss.org/
# Web 服务

# Miniflux - 自建 RSS
# https://miniflux.app/
# Web 服务
```

## 七，安全工具

### 7.1 密码管理

```bash
# ==========================================
# 密码管理工具
# ==========================================

# 1Password - 密码管理器
# https://1password.com/
brew install --cask 1password

# Bitwarden - 开源密码管理
# https://bitwarden.com/
brew install --cask bitwarden

# LastPass
# https://www.lastpass.com/
brew install --cask lastpass

# Dashlane
# https://www.dashlane.com/
brew install --cask dashlane

# KeePassXC - 开源密码管理
# https://keepassxc.org/
brew install --cask keepassxc

# Enpass
# https://www.enpass.io/
brew install --cask enpass
```

### 7.2 安全工具

```bash
# ==========================================
# 安全工具
# ==========================================

# Little Flocker - 防火墙
# https://www.globaldelight.com/little-flocker/
brew install --cask little-flocker

# Knock - Unlock Mac with iPhone
# https://knock.m pyrobenja.com/
brew install --cask knock

# macOS Firewall - 系统自带
# System Preferences > Security & Privacy > Firewall

# LuLu - 开源防火墙
# https://objective-see.org/products/lulu.html
# Free

# RansomWhere? - 勒索检测
# https://objective-see.org/products/ransomwhere.html
# Free

# Malwarebytes - 恶意软件检测
# https://www.malwarebytes.com/mac/
brew install --cask malewarebytes
```

## 八，其他工具

### 8.1 虚拟机

```bash
# ==========================================
# 虚拟化和容器
# ==========================================

# Docker Desktop
# https://www.docker.com/
brew install --cask docker

# OrbStack - 轻量 Docker
# https://orbstack.dev/
brew install --cask orbstack

# Podman - 容器引擎
# https://podman.io/
brew install --cask podman

# UTM - 虚拟机
# https://mac.getutm.app/
brew install --cask utm

# VirtualBox
# https://www.virtualbox.org/
brew install --cask virtualbox

# VMware Fusion
# https://www.vmware.com/products/fusion.html
brew install --cask vmware-fusion

# Parallels Desktop
# https://www.parallels.com/
brew install --cask parallels
```

### 8.2 云存储

```bash
# ==========================================
# 云存储和同步
# ==========================================

# Dropbox
# https://www.dropbox.com/
brew install --cask dropbox

# Google Drive
# https://www.google.com/drive/
brew install --cask google-drive

# iCloud Drive - Apple
# 预装应用

# OneDrive
# https://www.microsoft.com/en-us/microsoft-365/onedrive
brew install --cask microsoft-onedrive

# pCloud
# https://www.pcloud.com/
brew install --cask pcloud

# Syncthing - 开源同步
# https://syncthing.net/
brew install --cask syncthing
```

### 8.3 壁纸工具

```bash
# ==========================================
# 壁纸工具
# ==========================================

# Wallpaper Wizard
# https://wallpaperwizard.se/
brew install --cask wallpaper-wizard

# Pap.er - 壁纸应用
# https://paper.jiange.me/
brew install --cask pap.er

# Unsplash Wallpapers
# https://unsplash.com/wallpapers
# Web

# Desktop Pictures - macOS 预装
# System Preferences > Desktop & Screen Saver
```

## 九，Homebrew 高级用法

### 9.1 Homebrew 技巧

```bash
# ==========================================
# Homebrew 高级技巧
# ==========================================

# 1. 升级特定应用
brew upgrade <package>

# 2. 锁定版本防止升级
brew pin <package>

# 3. 解锁版本
brew unpin <package>

# 4. 查看依赖
brew deps <package>

# 5. 清理所有旧版本
brew cleanup

# 6. 诊断问题
brew doctor

# 7. 切换版本
brew switch <package> <version>

# 8. 查找应用所属的包
brew list --cask | grep <app-name>

# 9. 创建自己的 tap
brew tap user/repo
brew install user/repo/package

# 10. Cask 安装来源
brew install --cask --appdir=/Applications <app>
```

### 9.2 常用开发环境

```bash
# ==========================================
# 完整开发环境安装脚本
# ==========================================

#!/bin/bash

# 开发工具
brew install git
brew install node
brew install python
brew install go
brew install rust
brew install docker

# 数据库
brew install postgresql
brew install redis
brew install mongodb-community

# 开发应用
brew install --cask visual-studio-code
brew install --cask iterm2
brew install --cask docker
brew install --cask tableplus
brew install --cask gitkraken
brew install --cask postman
brew install --cask slack
brew install --cask discord

# 效率工具
brew install --cask raycast
brew install --cask obsidian
brew install --cask 1password
brew install --cask alfred
brew install --cask rectangle
brew install --cask cleanshot
```

## 十，总结

**awesome-mac** 是 **17k Stars 的 macOS 软件资源宝库**：

| 分类 | 代表软件 |
|------|----------|
| 💻 **开发者工具** | VS Code, JetBrains, iTerm2, GitHub Desktop |
| 🎨 **设计工具** | Figma, Sketch, Affinity, Adobe |
| 📦 **系统工具** | Homebrew, Rectangle, CleanShot |
| 🎵 **媒体工具** | DaVinci Resolve, Audacity, IINA |
| 📚 **效率工具** | Notion, Obsidian, Bear |
| 🔐 **安全工具** | 1Password, Bitwarden, LuLu |
| 🎮 **游戏** | Steam, Mac 游戏 |
| ☁️ **云存储** | Dropbox, iCloud, Google Drive |

**核心亮点**：
- ✅ **软件齐全**：开发者到日常用户全覆盖
- ✅ **安装方便**：Homebrew 一键安装
- ✅ **持续更新**：社区活跃维护
- ✅ **免费为主**：CC0-1.0 许可证

---

**🔗 相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/jaywcjlove/awesome-mac |
| Homebrew | https://brew.sh |
| Homebrew Cask | https://formulae.brew.sh/cask/ |
| MacUpdate | https://www.macupdate.com |

---

_🦞 本文由钳岳星君撰写，基于 awesome-mac (17k Stars)_
