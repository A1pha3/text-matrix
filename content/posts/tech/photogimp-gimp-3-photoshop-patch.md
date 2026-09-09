---
title: "PhotoGIMP：让 GIMP 变成 Photoshop 布局的开源补丁"
date: "2026-05-19T20:25:00+08:00"
slug: "photogimp-gimp-3-photoshop-patch"
github_repo: "Diolinux/PhotoGIMP"
description: "PhotoGIMP 是一个社区维护的开源配置补丁，把 GIMP 3.0+ 的工具布局、快捷键与启动画面调成接近 Adobe Photoshop，帮助从 Photoshop 迁移到 GIMP 的用户降低学习成本。"
draft: false
categories: ["技术笔记"]
tags: ["开源", "图像处理", "设计工具"]
---

## 学习目标

读完本文，你应该能：

1. **说清 PhotoGIMP 的本质**：它是配置补丁，不是独立软件，不改变 GIMP 的能力边界
2. **判断是否值得装**：按你的场景，评估从 Photoshop 迁移到 GIMP 时是否该用它
3. **在三个平台上装好**：在 Linux（Flatpak）、Windows、macOS 上完成安装并验证生效
4. **会备份与还原**：安装前后正确备份 GIMP 配置，能随时回到默认状态
5. **认出版本风险**：知道 GIMP 大版本升级时，PhotoGIMP 可能在哪些环节失效

## 目录

1. [先给判断](#先给判断)
2. [它解决什么问题](#它解决什么问题)
3. [它改了什么](#它改了什么)
4. [兼容性与风险](#兼容性与风险)
5. [安装](#安装)
6. [备份与还原](#备份与还原)
7. [适用边界](#适用边界)
8. [常见问题排查](#常见问题排查)
9. [自测题](#自测题)
10. [练习](#练习)
11. [进阶路径](#进阶路径)
12. [资料口径说明](#资料口径说明)
13. [结论](#结论)

<!--more-->

## 先给判断

PhotoGIMP 是一套被打包好的 GIMP 配置文件（含主题与设置），覆盖到 GIMP 的配置目录后，把默认界面调成接近 Adobe Photoshop 的样子。想从 Photoshop 迁移到免费的 GIMP，又不想重新背一遍工具位置和快捷键，这是目前最省事的上手方式。

但它只动"脸面"，不动"内核"。装之前 GIMP 能做到多少，装之后还是多少——只是看起来像你熟悉的软件了。真正复杂的功能差异（比如某些滤镜、颜色管理、生成式 AI 工具）不会因此消失。

## 它解决什么问题

GIMP 本身功能并不弱，修图、合成、切图都能干，但它和 Photoshop 的操作心智模型差别很大：工具面板默认排布不同、大量快捷键不一样、面板停靠位置也不同。一个用惯了 Photoshop 的人第一次打开 GIMP，最先遇到的不是"功能不够"，而是"哪都不顺手"。

这种摩擦是纯习惯问题，不涉及计算能力。PhotoGIMP 的思路就是：把 GIMP 的界面与按键习惯掰到 Photoshop 的方向上，让迁移者沿用已有的肌肉记忆，把注意力留给真正需要学习的少数功能差异。

它由巴西的开源社区 Diolinux 维护，托管在 [github.com/Diolinux/PhotoGIMP](https://github.com/Diolinux/PhotoGIMP)，以 GPL-3.0 许可发布，仓库代码 100% 是 CSS——这从侧面说明它是一层配置与主题，不是软件本体。截至 2026 年年中，项目在 GitHub 已积累上万星标（约 1.3 万以上，数字因统计渠道略有浮动）。

## 它改了什么

### 工具与面板布局

GIMP 默认的工具箱和 Photoshop 有不少出入。PhotoGIMP 把常用工具重新安排到接近 Photoshop 的位置，包括移动（V）、选区（M）、裁剪（C）、画笔（B）、图章（S）、橡皮擦（E）等，并按 Photoshop 习惯把图层面板放到右侧。

### 快捷键映射

快捷键配置参考了 [Adobe 官方快捷键文档](https://helpx.adobe.com/photoshop/using/default-keyboard-shortcuts.html)，尽量贴近 Photoshop 默认组合，让你保留原来的按键习惯。

| 操作 | Windows/Linux | Mac |
|------|---------------|-----|
| 撤销 | Ctrl + Z | Cmd + Z |
| 重做 | Ctrl + Shift + Z | Cmd + Shift + Z |
| 复制 | Ctrl + C | Cmd + C |
| 粘贴 | Ctrl + V | Cmd + V |
| 自由变换 | Ctrl + T | Cmd + T |
| 新建图层 | Ctrl + Shift + N | Cmd + Shift + N |

注意，映射是"尽量接近"，不是逐键一致。个别快捷键和 Photoshop 仍有差异，以实际生效为准。

### 启动画面与图标

PhotoGIMP 自带一张自定义启动画面（splash screen），并可通过自带的 `.desktop` 文件换掉应用图标和显示名，作为识别标志。

### 画布空间

默认配置对画布空间做了优化，减少面板占用的屏幕面积，尤其在笔记本或低分辨率屏幕上更明显。

## 兼容性与风险

| 维度 | 说明 |
|------|------|
| GIMP 版本 | 面向 GIMP 3.0+，官方主分支配置目录为 `.config/GIMP/3.0`，不支持 GIMP 2.x |
| 平台 | Linux（推荐 Flatpak）、Windows、macOS。macOS 配置目录在 `~/Library/Application Support/GIMP`，官方已补充安装文档 |
| 许可 | GPL-3.0 |
| 主要风险 | 私有生态中依赖配置目录结构，GIMP 大版本升级可能使补丁失效 |

需要特别留意的一点：配置目录跟随 GIMP 小版本变化。截至本文编写时，仓库主分支仍把配置放在 `3.0` 目录，社区里已有 PR（例如 #246）讨论把目录迁移到 `3.2` 以适配 GIMP 3.2，但尚未合入稳定版。也就是说，如果你用的是 GIMP 3.2，PhotoGIMP 的旧目录可能不被读取，界面改动不一定生效，需要手动把配置落到对应版本目录。

## 安装

### 前置条件

- 已安装 GIMP 3.0+（Linux 推荐从 [Flathub](https://flathub.org/apps/org.gimp.GIMP) 安装，Windows/macOS 从 [gimp.org](https://www.gimp.org/downloads/) 下载）
- **先启动一次 GIMP 再退出**，让它生成初始配置文件，否则覆盖可能不完整

### Linux（Flatpak）

```bash
# 1. 备份当前配置
cp -r ~/.config/GIMP/3.0 ~/GIMP-3.0-backup

# 若使用 Flatpak 版 GIMP，路径是：
# cp -r ~/.var/app/org.gimp.GIMP/config/GIMP/3.0 ~/GIMP-3.0-backup

# 2. 下载最新补丁（官方 release）
# https://github.com/Diolinux/PhotoGIMP/releases/download/3.0/PhotoGIMP-linux.zip

# 3. 解压到 home 目录，选择覆盖 .config 与 .local
unzip PhotoGIMP-linux.zip -d ~
```

如果当前 GIMP 配置目录不是 `3.0`（升级到了更高小版本），把补丁里的 `.config/GIMP/3.0` 内容复制到对应版本目录即可。

### Windows

1. 下载 [PhotoGIMP](https://github.com/Diolinux/PhotoGIMP/releases) 的 Windows 包并解压
2. 退出 GIMP，把解压得到的 GIMP 配置文件夹（含 `3.0` 目录）复制到 `%APPDATA%\GIMP`，覆盖同名目录
3. 重启 GIMP 检查界面

安装前建议先把 `%APPDATA%\GIMP` 整个复制一份作为备份。

### macOS

1. 下载补丁包并解压
2. 退出 GIMP，把其中 `3.0` 配置目录复制到 `~/Library/Application Support/GIMP`，覆盖同名目录
3. 重启 GIMP 检查界面

### 安装后校验

装完重启 GIMP 后，按下面几点确认是否生效：

- 工具图标排布是否接近 Photoshop（工具在左、图层面板在右）
- 按 `Ctrl + T`（或 `Cmd + T`）是否触发自由变换
- 启动时是否出现 PhotoGIMP 的自定义启动画面

如果这些都没变化，多半是配置目录写错了位置或版本目录不匹配，回到上一节的版本说明核对。

## 备份与还原

被覆盖的只是配置，GIMP 本体不受影响，所以还原很简单：

1. 备份时把原配置保留好（例如 `~/GIMP-3.0-backup`）
2. 要还原时，删除带补丁的配置目录：`rm -rf ~/.config/GIMP/3.0`
3. 把备份复制回原路径：`cp -r ~/GIMP-3.0-backup ~/.config/GIMP/3.0`
4. 重启 GIMP

Windows 与 macOS 对应操作各自的配置目录（`%APPDATA%\GIMP` 与 `~/Library/Application Support/GIMP`）。

## 适用边界

**适合用：**

- 从 Photoshop 迁移到 GIMP，想保留操作习惯
- 想在 Linux 上搭一个接近 Photoshop 的免费工作环境
- 不想花时间手工重排 GIMP 的工具面板和快捷键

**不适合用：**

- 已经是熟练的 GIMP 用户，有自己固定的配置习惯
- 需要 Photoshop 独有的功能（生成式 AI 填充、神经滤镜等），PhotoGIMP 不提供也不代理
- 追求 100% 还原 Photoshop——它只是视觉与按键层面的补丁，不是功能克隆
- 用 GIMP 2.x：补丁面向 3.0+，直接不兼容

## 常见问题排查

**Q：装完重启，界面一点没变？**

A：先确认配置目录是否与当前 GIMP 小版本一致。GIMP 3.2 等较新版本可能不读 `3.0` 目录，需把补丁内容复制到对应版本目录。其次确认安装前是否先启动过一次 GIMP（生成初始配置）。最后核对是否复制到了正确的平台路径。

**Q：能装回 GIMP 2.10 时代的 PhotoGIMP 吗？**

A：旧版补丁面向 2.10，与 3.0+ 不兼容，别混用。直接用面向 3.0 的 release。

**Q：装了会不会弄坏我的 GIMP？**

A：只覆盖配置文件，不会改动 GIMP 程序本体。只要保留备份，随时可还原到默认状态。

**Q：PhotoGIMP 会让 GIMP 支持 PSD 吗？**

A：PhotoGIMP 不改能力，GIMP 本身对 PSD 的支持由 GIMP 决定，与补丁无关。PS 插件、动作、生成式 AI 功能不因装补丁而出现。

## 自测题

1. **PhotoGIMP 是独立软件还是配置补丁？**
   <details>
   <summary>查看答案</summary>
   配置补丁。它通过覆盖 GIMP 配置目录改变界面与快捷键，不提供独立程序，也不改变 GIMP 的能力。
   </details>

2. **支持哪些平台，macOS 怎么办？**
   <details>
   <summary>查看答案</summary>
   支持 Linux（推荐 Flatpak）、Windows、macOS。macOS 配置目录在 `~/Library/Application Support/GIMP`。
   </details>

3. **安装前为什么必须先运行一次 GIMP？**
   <details>
   <summary>查看答案</summary>
   让 GIMP 先生成初始配置文件，否则补丁覆盖可能不完整，改动不生效。
   </details>

4. **快捷键参考了哪份文档？**
   <details>
   <summary>查看答案</summary>
   Adobe 官方快捷键文档（[helpx.adobe.com](https://helpx.adobe.com/photoshop/using/default-keyboard-shortcuts.html)），映射为尽量接近 Photoshop，并非逐键一致。
   </details>

5. **为什么 GIMP 3.2 用户可能要手动调整？**
   <details>
   <summary>查看答案</summary>
   因为仓库主分支配置目录仍是 `3.0`，GIMP 3.2 可能不读取该目录，需把补丁内容复制到对应版本目录。
   </details>

---

## 练习

### 练习 1：在 Linux 上安装并验证

1. 用 Flatpak 装好 GIMP 3.0+，启动一次后退出
2. 备份配置：`cp -r ~/.config/GIMP/3.0 ~/GIMP-3.0-backup`
3. 下载 PhotoGIMP 并解压覆盖 `.config` 与 `.local`
4. 启动 GIMP，用"安装后校验"一节的标准逐项确认生效

### 练习 2：还原默认配置

1. 删除补丁覆盖的配置目录
2. 从备份恢复
3. 重启 GIMP，确认界面回到默认排布

### 练习 3：手动微调快捷键

不装补丁也能改，目的在理解配置是如何生效的：

1. 打开 GIMP，进入菜单 Edit → Keyboard Shortcuts
2. 搜索某个工具或命令，修改快捷键
3. 导出快捷键文件，看看它与 `.config/GIMP/3.0` 下哪个文件对应

### 练习 4：适配更高版本目录

如果你的 GIMP 是 3.2，手动把补丁中 `3.0` 目录内容复制到 3.2 目录，观察界面是否生效，体会"版本目录绑定"这一风险点。

---

## 进阶路径

1. **用好 GIMP 本体**：参考 [GIMP 官方文档](https://www.gimp.org/docs/)，系统学图层蒙版、色阶曲线、滤镜与选区
2. **扩展插件**：装 [G'MIC](https://gmic.eu/) 等插件集合，GIMP 的图像处理能力会明显加宽
3. **深入配置结构**：阅读 `~/.config/GIMP/3.0` 下的 `gimprc`、`sessionrc`、`tool-options` 等文件，理解 PhotoGIMP 真正改了什么，从而能自己定制
4. **对比其他开源编辑器**：Krita（偏绘画）、Inkscape（矢量）、Darktable（摄影修图），按用途选型
5. **跟进版本适配**：关注 [PhotoGIMP 的 issues](https://github.com/Diolinux/PhotoGIMP/issues) 与 PR，在 GIMP 大版本升级前确认适配状态

---

## 资料口径说明

1. **版本范围**：本文以面向 GIMP 3.0+ 的 PhotoGIMP 为准，不覆盖 2.x 时代的旧版。GIMP 3.2 的适配仍处于社区 PR 阶段，具体以项目仓库最新状态为准。
2. **平台路径**：Flatpak 版 GIMP 配置目录在 `~/.var/app/org.gimp.GIMP/config/GIMP/`，与原生安装在 `~/.config/GIMP/` 不同；Windows 与 macOS 路径见正文。若与你本机不符，以 GIMP 实际生成目录为准。
3. **快捷键差异**：表格列出的是以 Adobe 官方文档为基准的常见映射，个别按键可能因 GIMP 实现而不同，以安装后实际生效为准。
4. **star 数与版本**：仓库星标约为 1.3 万以上（截至 2026 年中，随统计渠道浮动），非固定值；若需精确值请以 GitHub 页面实时显示为准。
5. **获取渠道**：只从官方 [GitHub Releases](https://github.com/Diolinux/PhotoGIMP/releases) 下载，避免第三方来源；如需校验可核对文件的 checksum。
6. **许可**：项目为 GPL-3.0，配置与主题同样遵循该许可。

---

## 结论

PhotoGIMP 解决的是一个具体的、真实存在的摩擦：从 Photoshop 过来的人，手停在 GIMP 的界面上会觉得陌生。它用一套配置把这层陌生感抹掉，让你先能干活，再慢慢接触 GIMP 自己的逻辑。

它不是功能扩展，也不承诺 100% 还原 Photoshop。判断标准很简单：你是不是刚迁移过来、且想保留旧习惯？是，装它很划算；已经熟练使用 GIMP，或者依赖 Photoshop 独占功能，那就没必要。记得装前备份、装后核对版本目录，剩下的交给 GIMP 自己。

---

**仓库信息**：[github.com/Diolinux/PhotoGIMP](https://github.com/Diolinux/PhotoGIMP) | 星标：约 1.3 万+（会变） | License：GPL-3.0 | 语言：CSS（配置/主题为主）