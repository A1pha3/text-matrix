---
title: "Islands Dark：悬浮玻璃风 VSCode 主题完全指南"
date: "2026-05-06T15:03:39+08:00"
slug: "islands-dark-vscode-theme-guide"
description: "Islands Dark 是一款受 easemate IDE 和 JetBrains Islands 启发的 VSCode 深色主题，以悬浮玻璃面板、圆角元素和暖色语法高亮为核心视觉语言。本文详解其设计理念、安装方式、字体配置及适用场景。"
draft: false
categories: ["技术笔记"]
tags: ["VSCode", "主题", "前端开发工具", "开源", "设计"]
---

## 项目概览

[Islands Dark](https://github.com/bwya77/vscode-dark-islands)（GitHub：bwya77/vscode-dark-islands，7,976 Stars，244 Forks）是一款深度定制的 VSCode 深色主题，灵感来源有两个：一个是 [easemate IDE](https://x.com/easemate)，另一个是 JetBrains 的 Islands 主题。

这个项目不只是换个颜色——它的核心目标是让整个 VSCode 界面"悬浮"起来：面板像玻璃卡片一样漂浮在深色画布上，有圆角、有阴影、有方向性光照模拟。从 activity bar 到通知、从命令面板到侧边栏，所有 UI 元素都被重新设计过。

### 快速信息卡

| 项目 | 内容 |
|------|------|
| 仓库 | bwya77/vscode-dark-islands |
| Stars | 7,976 |
| Fork | 244 |
| 主要语言 | PowerShell（安装脚本） |
| 主题定位 | VSCode 深色 UI 主题 |
| 最近活跃 | 2026 年 2 月持续更新 |

---

## 核心设计理念

传统深色主题的局限在于：它们只改了编辑器的文字颜色，VSCode 的外壳（侧边栏、标签栏、状态栏）依然千篇一律。Islands Dark 的出发点是把整个 IDE 当作一块可设计的画布来对待。

三个视觉关键词：**悬浮（floating）**、**玻璃（glass）**、**圆润（rounded）**。

### 1. 悬浮面板

整个界面的底色是一个极深的深紫黑（`#131217`），而各个面板——侧边栏、通知、命令面板、标签栏——都是"浮"在这个底色上方的独立玻璃卡片。面板边缘有细微的边框光效：顶部/左侧偏亮，底部/右侧偏暗，模拟环境光的照射方向。

### 2. 圆角化改造

VSCode 默认的 UI 是直角矩形。Islands Dark 给所有面板、通知、命令面板甚至滚动条都加上了圆角。特别是命令面板（Command Palette）和通知，视觉上和其他面板形成统一语言，不再是突然弹出的方正对话框。

### 3. Pill 形元素

Activity Bar（左侧图标栏）变成了一列胶囊形状的图标，选中项有磨砂玻璃质感的指示器。滚动条滑块也是胶囊形的，和整体圆润风格保持一致。

---

## 安装与快速上手

### 推荐方式：一条命令安装

#### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/bwya77/vscode-dark-islands/main/bootstrap.sh | bash
```

#### Windows

```powershell
irm https://raw.githubusercontent.com/bwya77/vscode-dark-islands/main/bootstrap.ps1 | iex
```

安装脚本会自动完成以下步骤：

- 安装 Islands Dark 主题扩展
- 安装 Custom UI Style 扩展（实现玻璃面板效果所必需）
- 安装 Bear Sans UI 字体
- 备份你现有的 VSCode settings 并写入 Islands Dark 配置
- 启用 Custom UI Style 并重启 VSCode

> IBM Plex Mono（编辑器字体）和 FiraCode Nerd Font Mono（终端字体）需要单独安装，脚本会有提示。

### 手动克隆安装

```bash
git clone https://github.com/bwya77/vscode-dark-islands.git islands-dark
cd islands-dark
./install.sh    # macOS/Linux
.\install.ps1   # Windows
```

install 脚本的行为和 bootstrap 脚本一致，适合希望查看或自定义配置的用户。

### Nix Flake 安装

如果你使用 Nix 或 NixOS，可以直接通过 Flake 运行预配置好的 VSCode 或 VSCodium：

```bash
# 直接运行（无需安装到系统）
nix run github:bwya77/vscode-dark-islands#vscode

# 或运行 VSCodium
nix run github:bwya77/vscode-dark-islands#vscodium
```

也可以将它加入你的 flake inputs，在 Home Manager 配置中集成：

```nix
# 在你的 flake.nix 中引用
inputs.vscode-dark-islands.url = "github:bwya77/vscode-dark-islands";
```

---

## 功能特性解析

### 语法高亮

Islands Dark 的语法高亮走的是"暖色调"路线，对主流编程语言都有良好覆盖：

- **JavaScript / TypeScript**：关键字暖橙色，函数名浅青色，字符串淡绿
- **Python**：缩进指示清晰，装饰器（decorator）高亮突出
- **Go / Rust**：类型和接口有独立配色
- **HTML / CSS / JSON / YAML / Markdown**：结构化语言的颜色分层清晰

整体色调偏暖，不刺眼，长时间编码时眼睛负担较小。

### 交互细节

- **Tab 关闭按钮**：默认隐藏，鼠标悬停时才淡入显示，保持标签栏整洁
- **Breadcrumb 栏和状态栏**：默认降低亮度，不抢夺注意力，鼠标悬停时恢复正常亮度
- **侧边栏选中项**：有过渡动画（transition），不是生硬的颜色跳变
- **滚动条**：胶囊形状滑块，视觉上和圆角主题语言统一

### 图标主题推荐

Islands Dark 本身的图标并不突出，但配合 [Seti Folder](https://marketplace.visualstudio.com/items?itemName=l-igh-t.vscode-theme-seti-folder) 图标主题使用时，左侧文件夹图标会有颜色匹配的发光（glow）效果，整体感更强。

---

## 字体配置

Islands Dark 对字体有明确建议，在 `settings.json` 中会自动写入：

```json
{
  "editor.fontFamily": "IBM Plex Mono",
  "terminal.integrated.fontFamily": "FiraCode Nerd Font Mono"
}
```

- **IBM Plex Mono**：编辑器和代码的等宽字体，Plex 系列字体本身设计感强，适合长时间阅读代码
- **FiraCode Nerd Font Mono**：终端等宽字体，带 Nerd Font 图标补丁，可以正确显示 Powerline、Font Awesome 等图标符号

两者都需要你自行安装（通过 Homebrew、`curl -L` 或直接下载），安装脚本不会自动处理字体文件。

---

## 技术实现：Custom UI Style 的角色

VSCode 的标准主题 API（color theme）只能修改编辑器区域的文字颜色和背景，无法触及 VSCode 外壳（shell）的圆角、阴影、玻璃模糊等效果。

Islands Dark 的"悬浮面板"效果是通过 [Custom UI Style](https://marketplace.visualstudio.com/items?itemName=niceratio.vscode-custom-ui-style) 扩展实现的。这个扩展允许用户在 VSCode 运行时注入自定义 CSS，从而突破标准主题 API 的限制，重写 VSCode 外壳的视觉样式。

这意味着 Islands Dark 是一个"主题 + 扩展"的组合包，单独安装 color theme 只能得到语法高亮部分，完整的玻璃面板效果需要同时启用 Custom UI Style。

---

## 适用场景与优势

### 适合人群

- 每天长时间在 VSCode 中工作的开发者
- 对 IDE 视觉体验有追求、不满足于默认外观的用户
- 喜欢"悬浮""磨砂玻璃"等现代 UI 风格的设计爱好者

### 优势

- **整体感强**：不只改编辑器，而是把整个 VSCode 外壳纳入设计体系
- **交互细节丰富**：Tab 悬停、侧边栏选中、滚动条等细节都经过打磨
- **暖色调高亮**：相比冷白色高亮，长时间编码更舒适
- **安装门槛低**：一条命令完成全部配置

### 局限

- 依赖 Custom UI Style 扩展，不喜欢折腾扩展的用户会觉得复杂
- 视觉效果偏"重"，在一些低性能机器上可能不如原生主题流畅
- 不适合需要和其他人共享一致编辑体验的团队协作场景

---

## 总结

Islands Dark 代表了一种趋势：IDE 主题不只是换个语法高亮颜色，而是把整个开发环境当作一个产品来设计。它的悬浮玻璃面板、圆角外壳和暖色高亮形成了一套完整的视觉语言。

如果你对 VSCode 默认外观已经审美疲劳，又不想折腾复杂的 VSCode 主题配置，一条命令就能换来完整的新体验——这本身就是值得尝试的理由。

- GitHub 仓库：https://github.com/bwya77/vscode-dark-islands
- easemate IDE：https://x.com/easemate
- Custom UI Style 扩展：https://marketplace.visualstudio.com/items?itemName=niceratio.vscode-custom-ui-style
- Seti Folder 图标主题：https://marketplace.visualstudio.com/items?itemName=l-igh-t.vscode-theme-seti-folder
