---
title: "PhotoGIMP：让GIMP 3.x变成Photoshop的视觉补丁"
date: "2026-05-19T20:25:00+08:00"
slug: "photogimp-gimp-3-photoshop-patch"
description: "PhotoGIMP是一个社区驱动的开源补丁，将GIMP 3.x重新配置为接近Adobe Photoshop的布局、快捷键和工作区，帮助从Photoshop迁移到GIMP的用户降低学习成本。"
draft: false
categories: ["技术笔记"]
tags: ["GIMP", "Photoshop", "开源", "图像处理", "设计工具"]
---

## 先给判断

PhotoGIMP 本质上是一个配置文件打包，而不是一个独立软件。它通过覆盖 GIMP 的配置目录，把 GIMP 3.x 的界面改造成 Photoshop 的布局——如果你刚离开 Adobe 生态，这是目前最低成本的 GIMP 上手方案。

但它不改变 GIMP 本身的能力边界。GIMP 能做的、不能做的，装完 PhotoGIMP 还是一样，只是视觉上更像你熟悉的工具了。

<!--more-->

## 系统地图

```
用户工作流：

Photoshop用户 ──► GIMP 3.x + PhotoGIMP补丁 ──► 视觉熟悉的GIMP
                                    │
                    GIMP配置被覆盖为:
                    ├─ 工具面板位置（左侧）
                    ├─ 图层面板位置（右侧）
                    ├─ 快捷键映射（PS映射）
                    └─ 菜单布局（可选）
```

## 核心能力

### 1. Photoshop 工具布局

GIMP 默认的工具面板在左侧，但位置和 Photoshop 有差异。PhotoGIMP 将工具重新排列，接近 PS 的默认布局，包括：

- 移动工具（V）
- 选区工具（M）
- 裁剪工具（C）
- 画笔工具（B）
- 图章工具（S）
- 橡皮擦（E）

等核心工具的位置与 Photoshop 一致。

### 2. Adobe 官方快捷键映射

PhotoGIMP 的快捷键配置直接基于[Adobe官方快捷键文档](https://helpx.adobe.com/photoshop/using/default-keyboard-shortcuts.html)：

| 操作 | Windows/Linux 快捷键 | Mac 快捷键 |
|------|-------------------|----------|
| 撤销 | Ctrl+Z | Cmd+Z |
| 重做 | Ctrl+Shift+Z | Cmd+Shift+Z |
| 复制 | Ctrl+C | Cmd+C |
| 粘贴 | Ctrl+V | Cmd+V |
| 自由变换 | Ctrl+T | Cmd+T |
| 新建图层 | Ctrl+Shift+N | Cmd+Shift+N |

大部分常用快捷键与 Photoshop 相同，减少肌肉记忆的重建成本。

### 3. 自定义启动画面

安装了 PhotoGIMP 的 GIMP 会有一个自定义 splash screen，作为识别标志。

### 4. 最大化画布空间

默认设置针对画布空间做了优化，减少面板占据的屏幕面积。

## 安装说明

### 要求

- GIMP 3.0 或更新版本
- Linux（Flatpak 推荐）或 Windows

### Linux / Flatpak 安装

```bash
# 1. 备份当前GIMP配置
cp -r ~/.config/GIMP/3.0 ~/GIMP-3.0-backup

# 2. 确保GIMP已安装并运行过一次
# 从 Flathub 安装: https://flathub.org/apps/org.gimp.GIMP

# 3. 下载最新版本
# https://github.com/Diolinux/PhotoGIMP/releases/download/3.0/PhotoGIMP-linux.zip

# 4. 解压到 home 目录 (~)
unzip PhotoGIMP-linux.zip -d ~

# 5. 覆盖确认时选择"Replace"

# 6. 启动GIMP
```

### Windows 安装

```bash
# 1. 备份当前配置
# 运行: %APPDATA%\GIMP
# 复制整个 3.0 文件夹到桌面备份

# 2. 下载 PhotoGIMP-windows.zip

# 3. 解压覆盖到 %APPDATA%\GIMP

# 4. 启动GIMP
```

## 注意事项

1. **先备份**：PhotoGIMP 会覆盖 GIMP 配置文件，已有自定义设置的用户请先备份
2. **需要先运行 GIMP**：安装前需要让 GIMP 生成初始配置文件，否则覆盖可能不完整
3. **不包含 GIMP 本体**：PhotoGIMP 只是一个补丁，不是完整软件包
4. **版本绑定**：PhotoGIMP 3.0 只支持 GIMP 3.0+，不兼容 GIMP 2.x

## 适用边界

**该用：**
- 从 Photoshop 迁移到 GIMP，想保留操作习惯
- 想在 Linux 上找到接近 Photoshop 的工作环境
- 不想花时间重新配置 GIMP

**不该用：**
- 已经是 GIMP 用户，有固定配置习惯
- 需要 Photoshop 的特定功能（如某些滤镜、颜色管理）
- 追求 100% Photoshop 兼容——这只是视觉补丁，不是功能克隆

## 技术细节

### 项目结构

PhotoGIMP 发布的是一个`.zip`压缩包，解压后包含：

```
PhotoGIMP-linux/
├── .config/
│   └── GIMP/
│       └── 3.0/
│           ├── gimprc              # GIMP运行时配置
│           ├── tooloptions         # 工具选项
│           └── ...
├── .local/
│   └── share/
│       └── icons/                 # 自定义图标
└── .local/share/applications/     # .desktop文件
```

覆盖后，GIMP 读取这些配置文件而不是默认配置，从而呈现 Photoshop 风格的界面。

### 维护状态

项目相对活跃，最近更新包含安全修复（如 Script-Fu 路径注入漏洞修复）。维护者是 Diolinux，社区驱动。

## 结论

PhotoGIMP 是降低 Photoshop 用户迁移成本的实用工具。它不是魔法，只是配置文件映射——GIMP 的能力边界不会因为安装了 PhotoGIMP 而改变。

如果你刚迁移到 GIMP，花 10 分钟安装 PhotoGIMP 可以让你的操作习惯平滑过渡；如果你已经是熟练的 GIMP 用户，PhotoGIMP 反而可能打乱你的肌肉记忆。

---

**仓库信息**：https://github.com/Diolinux/PhotoGIMP | Stars: 10,412 | License: GPL v3 | 语言： CSS