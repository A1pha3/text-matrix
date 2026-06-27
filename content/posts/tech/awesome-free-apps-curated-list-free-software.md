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

## 快速信息卡

| 项目 | 信息 |
|------|------|
| **仓库地址** | [Axorax/awesome-free-apps](https://github.com/Axorax/awesome-free-apps) |
| **Stars** | 6657+ |
| **Forks** | 351+ |
| **许可证** | MIT |
| **语言** | JavaScript |
| **最后更新** | 2026-06-20 |

## 学习目标

读完本文你能：

1. **说清这份清单解决什么问题**：不是软件下载站，而是"按场景和平台过滤的免费软件目录"，帮你在广告和算法推荐里找到真实推荐。
2. **用七个过滤维度快速定位**：Windows Only、macOS Only、Linux Only、Open-source Only、Recommended Only、Android Only、iOS Only，不必在一份长列表里翻找。
3. **按场景挑到合适的免费软件**：音频制作、隐私浏览器、开发工具、密码管理、系统定制，每个场景都有仓库实际收录的代表条目。
4. **沿着一条任务流把新机器配齐**：从打开 `filter/windows-only.md` 到逐场景选型，30 分钟内完成。
5. **参与贡献或成为维护者**：读 `contributing.md` 了解格式，读 `how-to-make-a-pr.md` 学 PR 流程，在 Issue #28 留言加入长期维护。

## 目录

- [核心判断](#核心判断)
- [仓库结构](#仓库结构)
- [分类精选](#分类精选)
- [任务流案例](#任务流案例)
- [如何参与贡献](#如何参与贡献)
- [采用建议](#采用建议)
- [常见问题与故障排查](#常见问题与故障排查)
- [自测题](#自测题)
- [进阶路径](#进阶路径)

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

## 常见问题与故障排查

**Q1：`filter/` 下的七个文件是手动维护的吗？**
A：不是，由 `index.js` 自动生成，与主列表保持同步。手动改 `README.md` 后运行 `node index.js` 即可重新生成过滤视图。

**Q2：为什么有些软件在 `recommended-only.md` 里但不在我的平台上？**
A：⭐ 推荐是维护者按"免费 + 好用"标的，不保证全平台兼容。点开软件官网确认系统要求，再决定是否采用。

**Q3：我想推荐一个好用的免费软件，怎么提交？**
A：阅读 `contributing.md` 了解格式（名称、平台图标、一句话描述、开源状态），然后在 `README.md` 的对应分类里提 PR。`how-to-make-a-pr.md` 有图文教程。

**Q4：仓库里的 Stars 数和我自己看的不一致？**
A：文章中的数据截至 2026-06-22，来自 GitHub API 快照。开源项目数据持续变化，以仓库实际显示为准。

**Q5：`archived.md` 里的软件还能用吗？**
A：大部分已失效（官网下线、停止维护、转为付费），不建议直接采用。如果你发现某个归档条目又活了，可以在 Issue 里提，维护者会评估是否移回主列表。

## 自测题

1. **这份清单和其他"最好的 XX 软件"文章的关键差异是什么？举一个使用场景说明过滤视图怎么帮你省时间。**
   > 差异在过滤层：七维过滤（Windows/macOS/Linux/Open-source/Recommended/Android/iOS）让你按平台或属性精准定位。场景：新装 Windows 机器，直接开 `filter/windows-only.md`，避开跨平台噪音。

2. **`README.md` 和 `MOBILE.md` 的关系是什么？如果你要帮一台 Android 手机配软件，应该先看哪个文件？**
   > `README.md` 是桌面端主列表，`MOBILE.md` 是移动端专项。配 Android 手机应先看 `MOBILE.md`，再看 `filter/android-only.md` 拿到纯 Android 条目。

3. **仓库用哪三个标记帮你快速判断一个软件是否开源、是否维护者推荐？**
   > 🔓 图标表示开源；⭐ 图标表示维护者推荐；两者都没有就是闭源且非特别推荐的条目。

4. **假设你需要在一台新 MacBook 上配齐开发环境，写出一个使用这份清单的四步流程。**
   > 1. 开 `filter/macOS-only.md` 拿 Mac 专用条目；2. 按场景（浏览器、编辑器、终端、密码管理）在对应分类里选；3. 用 `filter/recommended-only.md` 优先选带 ⭐ 的；4. 确认开源状态，优先选带 🔓 的。

5. **列表里没有你要的软件（比如磁盘加密工具），下一步应该怎么办？**
   > 这份清单有覆盖边界：未收录 VeraCrypt、BleachBit 等。需要这类工具应另找专题清单（如 awesome-security-hardening），或直接在 GitHub 搜关键词。

## 进阶路径

**阶段一：会用（第一次装机）**
- 按自己的主要平台（Windows/macOS/Linux）打开对应过滤视图。
- 逐场景（浏览器、编辑器、密码管理、截图、文件搜索）挑 1-2 个带 ⭐ 的条目装上。
- 把 `archived.md` 加入黑名单，装软件前先核对是否已失效。

**阶段二：会挑（跨平台或换机器）**
- 对比同软件在不同平台上的替代品，建立自己的跨平台工具矩阵。
- 学会用 `filter/open-source-only.md` 筛选，降低对闭源软件的依赖。
- 给每份装机清单附上访问日期，三个月后复查是否有更新版本。

**阶段三：会贡献（参与维护）**
- 发现好软件但不在列表里，按 `contributing.md` 格式提 PR。
- 发现条目失效（官网 404、转为付费），提 Issue 或 PR 移到 `archived.md`。
- 读 `how-to-make-a-pr.md`，学会 fork + branch + PR 的完整流程。

**阶段四：会维护（成为长期维护者）**
- 在仓库 Discord 或 Issue #28 留言，申请成为维护者。
- 运行 `index.js` 检查链接可达性，修复失效条目。
- 为新条目写一句话描述，保持清单的可扫描性（不超过两行）。

GitHub：[Axorax/awesome-free-apps](https://github.com/Axorax/awesome-free-apps)。
