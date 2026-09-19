---
title: "PhotoGIMP：把 Photoshop 的操作习惯搬进 GIMP 3"
date: 2026-05-20T09:09:49+08:00
slug: "photogimp-gimp-photoshop-layout-patch"
github_repo: "Diolinux/PhotoGIMP"
source_key: "gh:Diolinux/PhotoGIMP"
description: "PhotoGIMP 是 Diolinux 维护的开源补丁，不改 GIMP 一行代码，只覆盖配置文件，把工具布局、快捷键与启动画面对齐到 Photoshop 的习惯。本文讲清它的边界、安装验收与排障方法。"
draft: false
categories: ["技术笔记"]
tags: ["开源", "图像处理", "GIMP"]
---

# PhotoGIMP：把 Photoshop 的操作习惯搬进 GIMP 3

> **事实边界**：本文整理自 [Diolinux/PhotoGIMP](https://github.com/Diolinux/PhotoGIMP) 仓库 README 与 GitHub Releases 页面，stars、forks、下载量与版本号采集自 GitHub API，日期为 2026-09-18。项目没有官方网站，GitHub 仓库是唯一权威来源，安装前请以 README 最新版为准。

GIMP 的功能清单早就够长了：图层、蒙版、曲线、滤镜都有，3.0 又把底层工具包从 GTK2 迁到 GTK3。真正拦住 Photoshop 用户的从来不是功能，而是迁移成本——工具在别的位置，快捷键对不上，每个熟悉的动作都要重新找。PhotoGIMP（`Diolinux/PhotoGIMP`，GPL-3.0）解决的就是这件事：不改 GIMP 一行代码，只覆盖用户配置，把工具排列、面板布局、快捷键和启动画面对齐到 Photoshop 的习惯。1.8 万 star（fork 733）攒的不是"免费用 PS"的幻想，而是 Photoshop 用户迁移意愿的切片——仅 GitHub Releases 记录的下载，Windows/macOS 包就超过 24 万次，Linux 包超过 13 万次。

## 一、先拆掉三个常见误解

PhotoGIMP 最容易被误读成三种东西，先划清边界：

| 常见误解 | 实际情况 |
|---|---|
| "GIMP 的 Photoshop 分支" | 仓库里没有一行 GIMP 源码，本质是一组配置文件与资源的覆盖包 |
| "GIMP 插件" | 不走 GIMP 的插件体系（Script-Fu / Python-Fu），不往插件目录装任何东西 |
| "PS 兼容层，能带来 PS 的功能" | 打开 PSD 是 GIMP 自带的导入能力，与补丁无关；滤镜、插件生态也不通用 |

理解了"只是配置覆盖"，后面几件事就顺理成章：为什么装前要先跑一次 GIMP（配置目录要在首次运行后才生成）、为什么跨大版本会失效（GIMP 3.0 迁到 GTK3 后配置格式大改）、为什么卸载很干净（从头到尾只碰配置目录）。

## 二、补丁包里有什么

以最新版 3.1（2026-07-11 发布）为准，解压后替换的是 GIMP 3.0 用户配置目录（Linux 上即 `~/.config/GIMP/3.0`）里的一组文件：

| 文件 | 作用 |
|---|---|
| `shortcutsrc` | 快捷键映射，按 Adobe 官方 Windows 版 Photoshop 文档对齐 |
| `toolrc` / `sessionrc` / `dockrc` | 工具排列与面板布局，重排成 Photoshop 的经典位置 |
| `gimprc` / `contextrc` / `templaterc` | 默认行为与模板设置，针对最大化画布空间做了调整 |
| `splashes/` / `theme.css` | 自定义启动画面与主题微调 |

Linux 包额外附带 `.desktop` 启动器：装完后应用列表里会出现独立的 "PhotoGIMP" 入口和图标（图标位于 `~/.local/share/icons/`），与原版 GIMP 并存，不互相干扰。

这些文件都是 GIMP 运行时自己读写的用户配置，补丁只是替你改好了默认值。所以它不会动自定义笔刷、字体和插件，也不会因为 GIMP 小版本更新而失效；唯一能让它失效的是跨大版本——GIMP 2.10 与 3.0 的配置格式完全不兼容，PhotoGIMP 3.x 只支持 GIMP 3.0 及以上。2.10 时代的老版 PhotoGIMP（2020 年的 1.x 系列）因此整个作废，别混用。

## 三、安装：覆盖一次配置目录

前提只有两条：装好 GIMP 3.0+（从 [gimp.org](https://www.gimp.org/downloads/) 或 Flathub——后者是 Linux 上主流的 Flatpak 应用商店），并且**先启动一次再关闭**。配置目录要在首次运行后才生成，不跑一次就没有东西可覆盖。

**Linux（Flatpak 与非 Flatpak 通用）**

1. 安装 GIMP，运行一次后关闭。
2. 从 [Releases 页](https://github.com/Diolinux/PhotoGIMP/releases) 下载 `PhotoGIMP-linux.zip`。
3. 解压到主目录（`~`），文件会自动落进隐藏的 `~/.config` 与 `~/.local`（文件管理器按 Ctrl+H 显示隐藏文件）。
4. 提示覆盖时选择替换。
5. 重新打开 GIMP。

非 Flatpak 安装的 GIMP 用的是同一个配置路径 `~/.config/GIMP/3.0`，步骤照用。

**Windows / macOS**

下载 `PhotoGIMP.zip`，把解压出的 `3.0` 文件夹放进对应配置目录：Windows 是 `%APPDATA%\GIMP`，macOS 是 `~/Library/Application Support/GIMP`。macOS 上 Finder 合并文件夹容易失败，README 建议改用 rsync 复制。Windows 另有社区维护的 Chocolatey 一键安装：`choco install photogimp`（维护者为 André Augusto，非官方渠道）。

**装前备份**（README 强烈建议）：

```bash
# Linux
cp -r ~/.config/GIMP/3.0 ~/GIMP-3.0-backup
```

Windows 备份 `%APPDATA%\GIMP` 整个目录，macOS 备份 `~/Library/Application Support/GIMP`。

**验收**：重开 GIMP 后，工具箱排列、启动画面、快捷键应与 Photoshop 习惯一致；Linux 上应用列表出现 PhotoGIMP 独立入口。三项都对上，才算装好。

## 四、装完没变化、打开报错、想反悔

三个最常见的状况，README 的排查答案都很短：

- **没任何变化**：多半是解压位置错了——Linux 必须解压到主目录，让文件真正进入 `~/.config`；也可能覆盖时 GIMP 没有关，退出时把旧配置又写了回去。
- **打开报错**：基本是版本不匹配，2.x 的配置会让 3.x 读不懂。删掉配置目录后重装即可。
- **快捷键想改**：`shortcutsrc` 只是一份默认值，随时可以在 Edit → Keyboard Shortcuts 里改。
- **卸载**：删除配置目录（`rm -rf ~/.config/GIMP/3.0`），重启 GIMP 会自动生成一套全新默认配置；或直接恢复安装前的备份。自定义笔刷、字体、插件不受影响。

## 五、该不该用

PhotoGIMP 改的只是"门面"——布局、快捷键、启动画面。它适合两种人：

- **从 Photoshop 转来的用户**：省掉重新定位每个工具的时间，这是补丁的全部价值所在。
- **管理多台机器的团队或教学环境**：一份 zip 覆盖过去，所有机器的操作习惯保持一致。

两类人不需要它：

- **已经熟悉 GIMP 原生布局的用户**：装上等于把自己练熟的习惯清空重来，纯亏。
- **指望获得 Photoshop 功能的人**：滤镜生态、插件体系、PSD 高级特性都与补丁无关，这些差距只能等 GIMP 自己演进。

一句话结论：如果你因预算或平台原因要从 Photoshop 转向 GIMP，先装 PhotoGIMP 再开始上手，迁移阻力最小；如果你已是 GIMP 老用户，这个补丁对你没有增量。

---

*本文事实核对自 Diolinux/PhotoGIMP 仓库 README 与 GitHub Releases，stars/forks/下载量来自 GitHub API（2026-09-18 采集）。*
