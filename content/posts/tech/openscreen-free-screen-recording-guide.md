---
title: "OpenScreen：免费开源的屏幕录制与演示制作工具"
date: 2026-04-06T18:40:00+08:00
slug: "openscreen-free-screen-recording-guide"
description: "全面介绍 OpenScreen 开源屏幕录制工具，涵盖功能详解、技术架构、安装配置、跨平台注意事项等内容。"
draft: false
categories: ["技术笔记"]
tags: ["OpenScreen", "屏幕录制", "Electron", "PixiJS", "开源工具"]
---

# OpenScreen：免费开源的屏幕录制与演示制作工具

## 学习目标

通过本文，你将全面掌握以下核心能力：

- 深入理解 OpenScreen 的项目定位与设计理念
- 掌握 OpenScreen 的完整安装与配置流程
- 学会使用核心录制功能：窗口录制、全屏录制、系统音频
- 掌握自动/手动缩放效果的配置与自定义
- 熟练运用注释、裁剪、速度调节等后期编辑功能
- 理解 PixiJS 和 Electron 在项目中的技术应用
- 掌握跨平台部署的注意事项

---

## 1. 项目概述

### 1.1 是什么

**OpenScreen** 是由 [siddharthvaddem](https://github.com/siddharthvaddem) 开发的一个开源屏幕录制与演示制作工具，旨在为用户提供 Screen Studio 的免费替代方案。它专注于录制产品演示和操作指南这两个核心场景，让用户无需支付 $29/月即可创建精美的屏幕录制内容。

### 1.2 核心定位

| 维度 | OpenScreen | Screen Studio |
|------|------------|--------------|
| 价格 | 完全免费 | $29/月 |
| License | MIT | 专有 |
| 功能复杂度 | 精简核心功能 | 全功能套件 |
| 目标用户 | 基础演示需求 | 专业创作者 |
| 水印 | 无 | 无（付费后）|

### 1.3 核心数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | 23.2k |
| GitHub Forks | 1.6k |
| 贡献者 | 39 位 |
| 最新版本 | v1.3.0（2026年4月2日）|
| 发布版本数 | 11 个 |
| License | MIT |
| 主要语言 | TypeScript 97.7% |

### 1.4 技术标签

```
electron · open-source · screen-recorder · screen-capture · pixijs
```

---

## 2. 核心功能详解

### 2.1 录制模式

OpenScreen 支持多种录制模式，满足不同场景需求：

**窗口录制**：只录制特定应用程序窗口，避免捕获敏感内容或桌面杂乱。适合录制软件教程、Demo 演示等场景。

**全屏录制**：录制整个屏幕内容。适合录制需要展示多窗口协作、快速切换等操作的场景。

### 2.2 音频录制

| 音频源 | macOS | Windows | Linux |
|---------|-------|---------|--------|
| 麦克风 | ✅ 支持 | ✅ 支持 | ✅ 支持 |
| 系统音频 | ✅ macOS 13+ | ✅ 支持 | ⚠️ 需 PipeWire |
| 系统音频 (macOS 12-) | ❌ 不支持 | - | - |

**macOS 音频限制说明**：
- macOS 13+：支持系统音频录制，14.2+ 版本会提示授权音频捕获
- macOS 12 及以下：不支持系统音频录制，麦克风仍可正常使用

### 2.3 缩放效果

缩放是 OpenScreen 与普通屏幕录制工具的核心差异化功能，能够让演示更加流畅和专业：

**自动缩放**：
- 根据鼠标活动或时间自动触发缩放
- 可调节缩放深度级别（Zoom Depth）
- 可自定义缩放持续时间
- 可设置缩放位置（居中、自定义坐标）

**手动缩放**：
- 在录制过程中手动触发缩放
- 精确控制缩放时机和位置
- 适合需要强调特定内容的场景

**运动模糊**：
- 为平移和缩放效果添加运动模糊
- 使画面过渡更加平滑自然
- 显著提升专业感

### 2.4 背景设置

录制时可选择多种背景样式：

| 背景类型 | 说明 | 适用场景 |
|----------|------|----------|
| 壁纸 | 使用系统壁纸或自定义图片 | 保持品牌一致性 |
| 纯色 | 单色背景 | 简洁演示 |
| 渐变 | 两种颜色的渐变过渡 | 现代感设计 |
| 自定义 | 上传自定义背景图片 | 品牌宣传 |

### 2.5 注释功能

录制或编辑时可添加多种注释元素：

- **文字注释**：添加说明文字、标题、步骤编号
- **箭头指示**：指向特定区域或元素
- **图片水印**：添加 Logo、品牌标识

### 2.6 后期编辑

OpenScreen 提供完整的后期编辑能力：

**裁剪**：裁剪视频的任意区域，可用于隐藏敏感信息或调整画面构图。

**片段修剪**：删除不需要的片段，精简内容。

**速度调节**：调整不同片段的播放速度，可实现快进、慢动作等效果。

### 2.7 导出选项

支持多种输出配置：

| 配置项 | 选项 |
|--------|------|
| 宽高比 | 16:9、4:3、1:1、9:16 等 |
| 分辨率 | 720p、1080p、4K 等 |
| 格式 | MP4（H.264/H.265）|

---

## 3. 技术架构深度解析

### 3.1 技术栈概览

```
┌─────────────────────────────────────────────────────────────┐
│                      应用层 (React + TypeScript)                    │
├─────────────────────────────────────────────────────────────┤
│                      渲染引擎 (PixiJS)                              │
├─────────────────────────────────────────────────────────────┤
│                      Electron 主进程                              │
├─────────────────┬─────────────────┬─────────────────────────┤
│   屏幕捕获模块    │   音频处理模块    │      文件系统模块         │
│ (desktopCapturer)│ (Web Audio API) │    (Node.js fs)       │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### 3.2 Electron 架构

OpenScreen 基于 Electron 构建，利用其两大核心能力：

**desktopCapturer API**：这是 Electron 提供的屏幕捕获接口，OpenScreen 使用它来枚举可用屏幕和窗口，并获取媒体流。

```javascript
const { desktopCapturer } = require('electron');

const sources = await desktopCapturer.getSources({
  types: ['window', 'screen'],
  thumbnailSize: { width: 320, height: 180 }
});
```

**主进程/渲染进程分离**：Electron 的主进程处理系统级操作（文件读写、系统通知），渲染进程使用 React 构建用户界面。

### 3.3 PixiJS 渲染引擎

PixiJS 是一个高性能的 2D 渲染引擎，OpenScreen 使用它来实现流畅的缩放和动画效果：

- **硬件加速**：PixiJS 自动使用 WebGL 进行硬件加速渲染
- **平滑过渡**：运动模糊效果由 PixiJS 的滤镜系统实现
- **响应式布局**：支持不同分辨率和宽高比的导出设置

### 3.4 项目目录结构

```
openscreen/
├── .github/           # GitHub Actions 配置
├── electron/            # Electron 主进程代码
├── icons/              # 应用图标资源
├── public/             # 静态资源
├── scripts/            # 构建和脚本
├── src/                # React 渲染进程源码
│   ├── components/    # React 组件
│   ├── hooks/          # 自定义 Hooks
│   ├── stores/         # 状态管理
│   └── utils/          # 工具函数
├── tests/              # 测试文件
├── package.json
├── vite.config.ts
└── tsconfig.json
```

---

## 4. 安装与配置

### 4.1 下载安装包

从 GitHub Releases 页面下载对应平台的最新安装包：

| 平台 | 安装包格式 | 下载地址 |
|------|----------|----------|
| macOS | .dmg / .zip | Releases 页面 |
| Windows | .exe / .msi | Releases 页面 |
| Linux | .AppImage | Releases 页面 |

### 4.2 macOS 安装

**标准安装**：
1. 下载 .dmg 安装包
2. 双击打开，将 OpenScreen.app 拖入应用程序文件夹

**Gatekeeper 绕过**：
如果 macOS Gatekeeper 阻止了应用运行，执行以下命令：

```bash
xattr -rd com.apple.quarantine /Applications/Openscreen.app
```

**必要权限授予**：
1. 进入「系统设置 > 隐私与安全性」
2. 授予「屏幕录制」权限
3. 授予「辅助功能」权限（用于控制其他应用窗口）

### 4.3 Linux 安装

**AppImage 方式**：
```bash
# 下载 AppImage 文件
chmod +x Openscreen-Linux-*.AppImage
./Openscreen-Linux-*.AppImage
```

**沙盒错误处理**：
如果应用因沙盒错误无法启动，使用 `--no-sandbox` 参数：

```bash
./Openscreen-Linux-*.AppImage --no-sandbox
```

**音频支持说明**：
- Ubuntu 22.04+、Fedora 34+：默认使用 PipeWire，支持系统音频
- 旧版 PulseAudio 系统：可能不支持系统音频录制，麦克风通常可用

### 4.4 Windows 安装

Windows 版本开箱即用，无需额外配置。安装程序会自动处理所有依赖。

---

## 5. 使用流程详解

### 5.1 首次设置

首次启动 OpenScreen 时，需要完成以下设置：

1. **选择录制来源**：在欢迎界面选择要录制的屏幕或窗口
2. **配置音频**：选择是否录制系统音频和麦克风
3. **设置背景**：选择录制时使用的背景样式
4. **测试录制**：进行简短测试确保一切正常

### 5.2 录制操作流程

```
开始录制 → 添加缩放标记 → 添加注释 → 结束录制 → 后期编辑 → 导出
```

**开始录制**：
- 点击红色录制按钮或使用快捷键
- 倒计时 3 秒后开始（可配置）

**录制过程中**：
- 使用快捷键触发缩放效果
- 随时添加注释和标记
- 监控录制时长和文件大小

**结束录制**：
- 点击停止按钮或使用快捷键
- 自动进入后期编辑界面

### 5.3 快捷键参考

| 功能 | 快捷键 |
|------|--------|
| 开始/停止录制 | ⌘⇧R（macOS）|
| 全屏缩放 | ⌘⇧Z |
| 窗口缩放 | ⌘⇧W |
| 添加注释 | ⌘⇧A |

---

## 6. 跨平台注意事项

### 6.1 macOS 特定问题

**隐私权限**：
- 屏幕录制权限必须在「系统设置」中单独授予
- 辅助功能权限用于窗口级别的控制

**音频录制限制**：
- macOS 13 以下版本不支持系统音频捕获
- 建议使用外接麦克风录制配音

### 6.2 Linux 特定问题

**PipeWire 要求**：
- 较新的发行版（Ubuntu 22.04+、Fedora 34+）默认包含 PipeWire
- 旧版系统可能需要手动安装 PipeWire

**桌面环境兼容性**：
- GNOME、KDE、XFCE 等主流桌面环境均可正常运行
- 部分极简桌面环境可能存在兼容性问题

### 6.3 Windows 特定问题

Windows 版本无已知限制，所有功能均可正常使用。

---

## 7. 开发者指南

### 7.1 本地开发环境搭建

```bash
# 克隆仓库
git clone https://github.com/siddharthvaddem/openscreen.git
cd openscreen

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 7.2 技术规范

**代码风格**：使用 Biome 进行代码格式化和 Lint 检查：

```bash
# 运行检查
npm run lint

# 自动修复
npm run lint:fix
```

**提交规范**：
- 提交前自动运行 pre-commit hook
- 使用 Biome 进行代码检查

### 7.3 构建发布包

```bash
# 构建 macOS
npm run build:mac

# 构建 Windows
npm run build:win

# 构建 Linux
npm run build:linux

# 构建所有平台
npm run build:all
```

### 7.4 贡献指南

项目欢迎社区贡献！贡献流程：

1. 查看 open issues 和 project roadmap 了解当前开发方向
2. Fork 仓库并创建功能分支
3. 进行开发并确保通过所有测试
4. 提交 Pull Request
5. 等待代码审查和合并

---

## 8. 与类似项目对比

### 8.1 Screen Studio

| 特性 | OpenScreen | Screen Studio |
|------|-----------|--------------|
| 价格 | 免费 | $29/月 |
| License | MIT | 专有 |
| 缩放效果 | ✅ 支持 | ✅ 支持 |
| 运动模糊 | ✅ 支持 | ✅ 支持 |
| 注释功能 | ✅ 支持 | ✅ 支持 |
| 高级编辑 | 基础 | 完整套件 |

### 8.2 OBS Studio

| 特性 | OpenScreen | OBS Studio |
|------|-----------|------------|
| 定位 | 演示录制 | 专业直播/录制 |
| 学习曲线 | 低 | 高 |
| 录制目标 | 应用窗口/全屏 | 任意内容 |
| 缩放效果 | 内置 | 需插件/脚本 |
| 导出格式 | MP4 | 多种格式 |

---

## 9. 常见问题

### Q: macOS 显示"应用已损坏"怎么办？

A: 这是 Gatekeeper 安全机制导致的。执行以下命令即可：

```bash
xattr -rd com.apple.quarantine /Applications/Openscreen.app
```

### Q: 录制时听不到系统音频？

A: 检查以下几点：

1. 确认 macOS 版本是否在 13 以上
2. 在「系统设置 > 隐私与安全性」中检查屏幕录制权限
3. 某些应用（如 Chrome）可能需要单独授权音频捕获

### Q: Linux 版本无法启动？

A: 尝试使用 `--no-sandbox` 参数运行：

```bash
./Openscreen-Linux-*.AppImage --no-sandbox
```

### Q: 如何获得技术支持和反馈问题？

A: 可以通过以下渠道：

- GitHub Issues：报告 Bug 和功能请求
- Discord：加入社区讨论
- GitHub Discussions：提出问题和分享用法

---

## 10. 总结

OpenScreen 是一款专为演示场景设计的屏幕录制工具，它以开源免费的方式提供了 Screen Studio 的核心功能。对于需要创建产品演示、操作教程的创作者来说，OpenScreen 是一个极具性价比的选择。

**核心优势回顾**：

- 完全免费，无隐藏收费或水印
- MIT License，可自由使用和修改
- 专注于演示场景，功能精简但实用
- 跨平台支持（macOS、Windows、Linux）
- 开源社区驱动，持续迭代

**适用场景**：

- 产品演示录制
- 软件操作教程
- Bug 复现录制
- 在线演讲录制
- 客户演示 Demo

**不适用的场景**：

- 直播推流（建议使用 OBS Studio）
- 高级视频编辑（建议使用 Premiere、Final Cut）
- 多机位录制

随着远程办公和在线内容创作的普及，屏幕录制工具的需求日益增长。OpenScreen 以其简洁实用的设计和开源社区的力量，正在成为这一领域的的重要选择。

---

**附录：相关资源**

- GitHub 仓库：https://github.com/siddharthvaddem/openscreen
- 应用官网：https://openscreen.vercel.app
- 最新版本：v1.3.0
- Discord 社区：https://discord.gg/yAQQhRaEeg
- DeepWiki 文档：https://deepwiki.com/siddharthvaddem/openscreen