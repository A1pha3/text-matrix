---
title: "awesome-free-apps：每个平台最值得收藏的免费软件清单"
date: "2026-05-25T20:16:19+08:00"
slug: "awesome-free-apps-curated-list-free-software"
aliases:
 - "/posts/tech/axorax-awesome-free-apps-guide/"
description: "awesome-free-apps 是一个按平台和场景分类的免费软件精选清单，覆盖 Windows、macOS、Linux 三大桌面平台和 Android、iOS 两大移动端，按音频、浏览器、开发工具、文档、图像、安全等场景组织，每个条目标注平台兼容性和开源状态。"
draft: false
categories: ["技术笔记"]
tags: ["免费软件", "Windows", "macOS", "Linux", "开源", "工具推荐"]
---

## 核心判断

awesome-free-apps 解决的是"这个场景该用什么免费软件"的决策问题。它靠维护者手动挑选条目，去广告、无营销套路，与搜索引擎的广告排名和应用商店的算法推荐形成对照。截至 2026 年 6 月 22 日，仓库在 GitHub API 上返回 **6657 Stars / 351 Forks**（数据来源：`https://api.github.com/repos/Axorax/awesome-free-apps`），365 次提交，最近一次推送在 2026 年 6 月 20 日，处于活跃维护状态。

它与其他 awesome 列表的关键差异在过滤层：仓库把桌面端拆成 Windows Only、macOS Only、Linux Only、Open-source Only、Recommended Only 五个视图，移动端再单独拆出 Android Only 和 iOS Only，共七个过滤维度。读者按平台或属性精准定位，不必在一份长列表里翻找。

## 仓库结构

```
awesome-free-apps/
├── README.md              # 主列表（桌面平台，约 806 行）
├── MOBILE.md              # 移动端专项
├── archived.md            # 已归档条目（失效或停止维护）
├── contributing.md        # 贡献格式与提交规范
├── full-guide.md          # 完整使用指南
├── how-to-make-a-pr.md    # PR 提交教程
├── code-of-conduct.md     # 行为准则
├── logo.svg               # 项目图标
├── index.js               # 链接可达性测试脚本
├── .github/               # CI 配置
└── filter/                # 过滤视图
    ├── windows-only.md
    ├── macOS-only.md
    ├── linux-only.md
    ├── open-source-only.md
    ├── recommended-only.md
    ├── android-only.md
    └── iOS-only.md
```

`README.md` 是主入口，按场景分 30 余个二级分类；`MOBILE.md` 单独维护移动端；`filter/` 下的七个文件由 `index.js` 自动生成，与主列表保持同步。`archived.md` 收录失效条目，便于追溯历史。

## 分类精选

下面从仓库的几个主要分类中各挑若干代表性条目，平台标记沿用仓库图标约定（🪟 Windows、🍎 macOS、🐧 Linux）。需要说明的是，仓库的"全平台"指桌面三端，移动端需查 `MOBILE.md`。

### 音频与音乐制作

- **Audacity** 🪟 🍎 🐧 · 开源录音/音频编辑器 — 仓库 ⭐ 推荐，跨平台音频编辑入门首选。
- **LMMS** 🪟 🍎 🐧 · 开源 DAW — 虚拟乐器加 MIDI 支持，零成本音乐制作。
- **MuseScore** 🪟 🍎 🐧 · 乐谱软件 — 写谱、播放、分享，社区活跃。
- **Ardour** 🪟 🍎 🐧 · 专业 DAW — 录音、编辑、混音全流程，开源。
- **Furnace** 🪟 🍎 🐧 · 开源 chiptune tracker — 多系统复古芯片音乐制作。

### 浏览器

- **Tor Browser** 🪟 🍎 🐧 — 隐私浏览，流量走 Tor 网络，仓库 ⭐ 推荐。
- **ungoogled-chromium** 🪟 🍎 🐧 — 移除 Google 服务的 Chromium 分支。
- **LibreWolf** 🪟 🍎 🐧 — 隐私优先的 Firefox 分叉，增强安全默认值。
- **Mullvad Browser** 🪟 🍎 🐧 — 集成 Mullvad VPN 的隐私浏览器。
- **qutebrowser** 🪟 🍎 🐧 — 键盘驱动，Vim 风格操作。
- **Zen Browser** 🪟 🍎 🐧 — 设计精美的隐私浏览器，支持自定义模组。

### 开发工具

仓库的开发工具区拆成 API Development、Database、Network Analysis、Game Engines、Virtualization 等子类，下面按子类各取代表。

- **Wireshark** 🪟 🍎 🐧 · Network Analysis — 网络协议分析器，仓库 ⭐ 推荐。
- **Docker** 🪟 🍎 🐧 · Virtualization — 容器化平台，仓库 ⭐ 推荐。
- **VirtualBox** 🪟 🍎 🐧 · Virtualization — 开源虚拟机，仓库 ⭐ 推荐。
- **Insomnia** 🪟 🍎 🐧 · API Development — REST/GraphQL 客户端，仓库 ⭐ 推荐。
- **DBeaver** 🪟 🍎 🐧 · Database — 通用 SQL 数据库工具，仓库 ⭐ 推荐。

代码编辑器在仓库里独立成"Text Editors"分类，VS Code、Neovim、Zed 等都在那里，不在 Developer Tools 下。

### 文档与办公

- **LibreOffice** 🪟 🍎 🐧 · Office Suites — 开源办公套件，仓库 ⭐ 推荐。
- **Obsidian** 🪟 🍎 🐧 · Note Taking — 本地笔记，双向链接，仓库 ⭐ 推荐。
- **Draw.io** 🪟 🍎 🐧 · Graphics Tools — 桌面版流程图工具，开源。
- **Calibre** 🪟 🍎 🐧 · E-book — 电子书管理器，仓库 ⭐ 推荐。
- **Sumatra PDF** 🪟 · PDF Tools — 轻量 PDF 阅读器，仓库 ⭐ 推荐。

仓库没有收录 Zotero、Pandoc 等学术工具，需要这类软件得另找清单。

### 安全工具

仓库的安全区分为 Antivirus、Password Managers、Ad & Tracker Blocking 三个子类。

- **Bitwarden** 🪟 🍎 🐧 · Password Managers — 开源密码管理器。
- **KeePassXC** 🪟 🍎 🐧 · Password Managers — 本地加密数据库的密码管理器。
- **ClamAV** 🪟 🍎 🐧 · Antivirus — 开源杀毒引擎。
- **SaneHosts** 🍎 · Ad & Tracker Blocking — macOS hosts 文件管理器。

7-Zip 在仓库里归入"Compression and Archiving"，不在安全区。仓库未收录 VeraCrypt、BleachBit，磁盘加密和系统清理需求需要从其他来源找。

### 系统定制

仓库的 Customize 区分 System Customization 和 Wallpaper Tools，下面按平台挑出仓库实际收录的条目。

- **启动器**：Windows — Flow Launcher。
- **文件搜索**：Windows — Everything。
- **窗口管理**：Windows — Windhawk；macOS — Rectangle；Linux — KWin、i3、Sway。
- **任务栏定制**：Windows — ExplorerPatcher；macOS — Hidden Bar。

macOS 启动器和 Linux 任务栏定制在仓库里没有对应条目，需要从其他来源补充。

## 任务流案例：在新 Windows 机器上配齐基础工具

假设读者拿到一台全新的 Windows 机器，想用这份清单在 30 分钟内配齐日常工具，流程如下：

1. 打开 `filter/windows-only.md`，拿到仅 Windows 平台的条目子集，避开跨平台噪音。
2. 在 `README.md` 主列表里按场景定位：
   - 浏览器：Browsers 分类下选 Tor Browser 或 ungoogled-chromium。
   - 代码编辑器：Text Editors 分类下选 VS Code 或 VSCodium（去微软遥测版）。
   - 压缩：Compression and Archiving 下选 7-Zip。
   - 密码管理：Security → Password Managers 下选 Bitwarden。
   - 截图：Utility → Screenshot 下选 ShareX。
   - 文件搜索：Utility → File Management 下选 Everything。
3. 想确认是否开源，对照条目后的 🟢 图标，或直接打开 `filter/open-source-only.md`。
4. 想看维护者特别推荐的，打开 `filter/recommended-only.md`，只看带 ⭐ 的条目。

这个流程每一步都有明确的文件入口，读者不必在搜索引擎结果里分辨广告与真实推荐。

## 如何参与贡献

发现好软件想加入仓库，阅读 [contributing.md](https://github.com/Axorax/awesome-free-apps/blob/main/contributing.md) 了解提交格式。仓库还提供 [how-to-make-a-pr.md](https://github.com/Axorax/awesome-free-apps/blob/main/how-to-make-a-pr.md) 作为 PR 教程。想成为长期维护者，在 [Issue #28](https://github.com/Axorax/awesome-free-apps/issues/28) 留言或加入仓库 Discord 服务器。

## 采用建议

这份清单适合三类读者：

- **新装机用户**：按平台过滤视图逐场景挑选，避开搜索引擎广告。
- **跨平台用户**：用主列表对照三端兼容性，优先选 🪟 🍎 🐧 三端齐全的工具，减少切换成本。
- **开源偏好者**：直接走 `open-source-only.md`，跳过闭源条目。

使用时注意两点：一是仓库条目会随维护更新增减，引用具体软件时建议附上访问日期；二是 `archived.md` 里的条目已失效，不要直接采用。如果需要仓库未收录的工具（如磁盘加密、学术文献管理），需要另找专题清单补充。

GitHub：[Axorax/awesome-free-apps](https://github.com/Axorax/awesome-free-apps)。
