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

> **阅读目标**：本文适合每天长时间在 VSCode 中工作的开发者，以及希望将整个开发环境当作产品来设计的 UI 爱好者。阅读完本文后，你将能够判断 Islands Dark 是否适合你的工作流，并完成从安装到定制的完整配置。

---

## 学习目标

通过本文，你将掌握以下核心能力：

- 理解 Islands Dark 的设计理念（悬浮、玻璃、圆润）和技术实现（Custom UI Style）
- 学会安装和配置 Islands Dark（一键脚本、手动克隆、Nix Flake）
- 掌握 Islands Dark 的字体配置建议（IBM Plex Mono、FiraCode Nerd Font Mono）
- 了解 Islands Dark 的语法高亮特点和交互细节
- 知道如何配合 Seti Folder 图标主题实现整体统一
- 能够判断 Islands Dark 是否适合你的使用场景

### 快速信息卡

| 项目 | 内容 |
|------|------|
| 仓库 | bwya77/vscode-dark-islands |
| Stars | 8.6k |
| Fork | 273 |
| 主要语言 | Shell（安装脚本） |
| 主题定位 | VSCode 深色 UI 主题 |
| 最近活跃 | 2026 年 6 月持续更新 |

---

## 目录

- [项目概览](#项目概览)
- [核心设计理念](#核心设计理念)
  - [1. 悬浮面板](#1-悬浮面板)
  - [2. 圆角化改造](#2-圆角化改造)
  - [3. Pill 形元素](#3-pill-形元素)
- [安装与快速上手](#安装与快速上手)
  - [推荐方式：一条命令安装](#推荐方式一条命令安装)
  - [手动克隆安装](#手动克隆安装)
  - [Nix Flake 安装](#nix-flake-安装)
- [功能特性解析](#功能特性解析)
  - [语法高亮](#语法高亮)
  - [交互细节](#交互细节)
  - [图标主题推荐](#图标主题推荐)
- [字体配置](#字体配置)
- [技术实现：Custom UI Style 的角色](#技术实现custom-ui-style-的角色)
- [适用场景与优势](#适用场景与优势)
- [常见问题与故障排查](#常见问题与故障排查)
- [自测题](#自测题)
- [进阶路径](#进阶路径)
- [总结](#总结)
- [参考资源](#参考资源)

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

## 常见问题与故障排查

### 问题1：安装后没有悬浮玻璃效果

**现象**：安装 Islands Dark 后，编辑器颜色变了，但没有悬浮玻璃面板效果。

**原因**：Islands Dark 的悬浮玻璃效果依赖 Custom UI Style 扩展。如果只安装了 color theme，不会有玻璃效果。

**解决方案**：
1. 确保已安装 Custom UI Style 扩展：`ext install niceratio.vscode-custom-ui-style`
2. 确保已启用 Custom UI Style：运行命令 `Custom UI Style: Enable`
3. 重启 VSCode
4. 检查 Islands Dark 的安装脚本是否成功注入了自定义 CSS

### 问题2：VSCode 启动缓慢

**现象**：安装 Islands Dark 后，VSCode 启动时间明显增加。

**原因**：Custom UI Style 需要在 VSCode 启动时注入自定义 CSS，会增加启动时间。此外， Islands Dark 的 CSS 文件较大（包含阴影、圆角等效果）。

**解决方案**：
1. 升级到最新版 Islands Dark（持续优化性能）
2. 禁用不需要的效果（通过编辑自定义 CSS）
3. 如果性能影响过大，考虑使用其他轻量级主题

### 问题3：字体显示不正常

**现象**：安装 Islands Dark 后，编辑器字体变成默认字体，不是 IBM Plex Mono。

**原因**：安装脚本写入了字体配置，但系统中没有安装对应的字体。

**解决方案**：
1. 安装 IBM Plex Mono：`brew install font-ibm-plex`
2. 安装 FiraCode Nerd Font：`brew install --cask font-fira-code-nerd-font`
3. 手动检查 `settings.json` 中的字体配置：
   ```json
   {
     "editor.fontFamily": "IBM Plex Mono",
     "terminal.integrated.fontFamily": "FiraCode Nerd Font Mono"
   }
   ```
4. 如果字体已安装但显示不正常，尝试重启 VSCode

### 问题4：与其他扩展冲突

**现象**：安装 Islands Dark 后，其他扩展的 UI 显示异常。

**原因**：Custom UI Style 注入的 CSS 可能影响其他扩展的 UI。

**解决方案**：
1. 检查是否有其他扩展也修改 VSCode 外壳的 CSS
2. 禁用其他主题相关的扩展
3. 在 Custom UI Style 的配置中排除特定 CSS 规则

---

## 自测题

### 题目1：Islands Dark 的核心设计理念

**问题**：Islands Dark 与传统的 VSCode 深色主题（如 Default Dark、One Dark Pro）的主要区别是什么？

<details>
<summary>参考答案</summary>

**传统深色主题**：
- 只修改编辑器的语法高亮颜色
- VSCode 的外壳（侧边栏、标签栏、状态栏）保持默认外观
- 所有 UI 元素都是直角矩形

**Islands Dark 的差异化**：
1. **整体设计**：不只改编辑器，而是把整个 VSCode 外壳纳入设计体系
2. **悬浮面板**：面板像玻璃卡片一样漂浮在深色画布上，有圆角、阴影、方向性光照
3. **圆角改造**：所有 UI 元素都被加上圆角（命令面板、通知、滚动条等）
4. **Pill 形元素**：Activity Bar 变成胶囊形状的图标
5. **交互细节**：Tab 关闭按钮默认隐藏、Breadcrumb 栏降低亮度等

核心价值：把整个开发环境当作一个产品来设计。
</details>

### 题目2：Custom UI Style 的作用

**问题**：为什么 Islands Dark 需要 Custom UI Style 扩展？VSCode 的标准主题 API 有什么限制？

<details>
<summary>参考答案</summary>

**VSCode 标准主题 API 的限制**：
- 只能修改编辑器区域的文字颜色和背景（color theme）
- 无法触及 VSCode 外壳（shell）的圆角、阴影、玻璃模糊等效果
- 无法修改 UI 元素的形状（如将直角改为圆角）

**Custom UI Style 的作用**：
- 允许用户在 VSCode 运行时注入自定义 CSS
- 突破标准主题 API 的限制，重写 VSCode 外壳的视觉样式
- Islands Dark 使用 Custom UI Style 实现悬浮玻璃面板、圆角外壳等效果

**结论**：Islands Dark 是一个"主题 + 扩展"的组合包，单独安装 color theme 只能得到语法高亮部分。
</details>

### 题目3：字体配置

**问题**：Islands Dark 为什么推荐使用 IBM Plex Mono 和 FiraCode Nerd Font Mono？它们分别用于什么场景？

<details>
<summary>参考答案</summary>

**IBM Plex Mono**：
- 用途：编辑器和代码的等宽字体
- 特点：Plex 系列字体设计感强，适合长时间阅读代码
- 安装：`brew install font-ibm-plex`

**FiraCode Nerd Font Mono**：
- 用途：终端等宽字体
- 特点：带 Nerd Font 图标补丁，可以正确显示 Powerline、Font Awesome 等图标符号
- 安装：`brew install --cask font-fira-code-nerd-font`

**为什么需要两种字体**：
- 编辑器字体需要良好的代码可读性（IBM Plex Mono 设计感强）
- 终端字体需要支持特殊符号（FiraCode Nerd Font 带图标补丁）
</details>

### 题目4：适用场景判断

**问题**：以下哪些场景适合使用 Islands Dark？哪些不适合？为什么？
1. 每天在 VSCode 中工作 8 小时的开发者
2. 需要和其他人共享一致编辑体验的团队协作场景
3. 对 IDE 视觉体验有追求、不满足于默认外观的用户
4. 在低性能笔记本上工作的开发者

<details>
<summary>参考答案</summary>

1. **适合**：Islands Dark 的暖色调高亮和整体设计适合长时间编码
2. **不适合**：Islands Dark 的依赖复杂（需要 Custom UI Style 扩展），且视觉效果偏"重"，不适合需要共享一致体验的团队
3. **适合**：Islands Dark 代表了一种趋势——把 IDE 当作产品来设计，适合 UI 爱好者
4. **可能不适合**：Islands Dark 的视觉效果偏"重"，可能在低性能机器上不如原生主题流畅。建议先试用，如果性能影响过大，考虑轻量级主题
</details>

### 题目5：图标主题配合

**问题**：为什么 Islands Dark 推荐配合 Seti Folder 图标主题使用？配合后有什么效果？

<details>
<summary>参考答案</summary>

**推荐原因**：
- Islands Dark 本身的图标并不突出
- Seti Folder 图标主题的左侧文件夹图标会有颜色匹配的发光（glow）效果
- 配合后整体感更强，形成统一的视觉语言

**配合效果**：
- 文件夹图标有发光效果，和 Islands Dark 的悬浮玻璃面板风格一致
- 整体 UI 更加统一，不是简单的"换色"，而是完整的设计体系

**如何配置**：
1. 安装 Seti Folder 图标主题：`ext install l-igh-t.vscode-theme-seti-folder`
2. 在 VSCode 设置中选择 Seti Folder 作为图标主题
</details>

---

## 进阶路径

### 阶段1：深度定制 Islands Dark

- 学习 VSCode 的 color theme 和 CSS 定制机制
- 编辑 Islands Dark 的 CSS 文件，调整阴影、圆角、颜色等参数
- 创建自己的 VSCode 主题（基于 Islands Dark 的修改版）

### 阶段2：探索其他 VSCode 主题

- 尝试其他深度定制的 VSCode 主题（如 Ayu、Dracula、Night Owl）
- 了解不同主题的设计理念和适用场景
- 学习如何混合不同主题的元素（如语法高亮用 A，UI 用 B）

### 阶段3：构建自己的 VSCode 工作流

- 定制 VSCode 的完整工作流（主题、字体、扩展、快捷键）
- 学习 VSCode 的高级特性（多光标、命令面板、调试器）
- 探索 VSCode 的扩展开发，创建自己的定制扩展

### 阶段4：探索 IDE 设计趋势

- 学习现代 IDE 的设计趋势（悬浮面板、玻璃模糊、圆角外壳）
- 了解其他 IDE 的主题系统（JetBrains、Xcode、Sublime Text）
- 探索 AI 时代的 IDE 设计（如 Cursor、GitHub Copilot 的集成）

---

## 总结

Islands Dark 代表了一种趋势：IDE 主题不只是换个语法高亮颜色，而是把整个开发环境当作一个产品来设计。它的悬浮玻璃面板、圆角外壳和暖色高亮形成了一套完整的视觉语言。

如果你对 VSCode 默认外观已经审美疲劳，又不想折腾复杂的 VSCode 主题配置，一条命令就能换来完整的新体验——这本身就是值得尝试的理由。

- GitHub 仓库：https://github.com/bwya77/vscode-dark-islands
- easemate IDE：https://x.com/easemate
- Custom UI Style 扩展：https://marketplace.visualstudio.com/items?itemName=niceratio.vscode-custom-ui-style
- Seti Folder 图标主题：https://marketplace.visualstudio.com/items?itemName=l-igh-t.vscode-theme-seti-folder
