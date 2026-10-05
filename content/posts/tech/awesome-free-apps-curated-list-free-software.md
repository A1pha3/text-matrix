---
title: "awesome-free-apps：每个平台最值得收藏的免费软件清单"
date: "2026-05-25T20:16:19+08:00"
lastmod: "2026-10-04T00:00:00+08:00"
slug: "awesome-free-apps-curated-list-free-software"
github_repo: "Axorax/awesome-free-apps"
source_key: "gh:Axorax/awesome-free-apps"
aliases:
 - "/posts/tech/axorax-awesome-free-apps-guide/"
description: "awesome-free-apps 是一个按平台和场景分类的免费软件精选清单，覆盖 Windows、macOS、Linux 三大桌面平台和 Android、iOS 两大移动端。本文拆解它的过滤视图机制、index.js 维护脚本与贡献规则，并给出新装机、跨平台、开源偏好三类读者的使用路径。"
draft: false
categories: ["技术笔记"]
tags: ["Windows", "macOS", "Linux", "开源"]
---

## 快速信息卡

| 项目 | 信息 |
|------|------|
| **仓库地址** | [Axorax/awesome-free-apps](https://github.com/Axorax/awesome-free-apps) |
| **Stars** | 7,812（2026-10-04 GitHub API 读数） |
| **Forks** | 511 |
| **许可证** | CC BY-NC-SA 4.0（LICENSE 正文；GitHub API 因不识别纯文本协议而显示 NOASSERTION） |
| **语言** | JavaScript |
| **最后更新** | 2026-09-23 |

## 核心判断

awesome-free-apps 解决的是"这个场景该用什么免费软件"的决策问题。它靠维护者手动挑选条目，去广告、无营销套路，与搜索引擎的广告排名和应用商店的算法推荐形成对照。截至 2026 年 10 月 4 日，仓库在 GitHub API 上返回 **7,812 Stars / 511 Forks**（数据来源：`https://api.github.com/repos/Axorax/awesome-free-apps`），最后推送在 2026 年 9 月 23 日。

活跃度有具体数字支撑：2026 年 5 月下旬本文初稿发表时，桌面主列表收录 557 个条目；到 10 月初是 618 个，同期移动端从 172 涨到 198。四个多月里仓库合入 185 个提交，仅 8 月 1 日到 9 月 23 日就合并了编号 #222 到 #321 的约 100 个 PR。增长几乎全部来自社区投稿，主列表新增了 Finance（财务）分类，也删除了当年 5 月停服的 Skype 和工作区浏览器 Station。

它与其他 awesome 列表的差异在过滤层：README 顶部挂了七个过滤视图链接，桌面端是 Windows Only、macOS Only、Linux Only、Open-source Only、Recommended Only 五个，移动端是 Android Only 和 iOS Only 两个。`filter/` 目录里对应 9 个文件——上述 7 个之外，还有 open-source-mobile-only 和 recommended-mobile-only 两个移动端组合视图。读者按平台或属性精准定位，不必在一份长列表里翻找。

## 仓库结构

```
awesome-free-apps/
├── README.md              # 主列表（桌面平台，618 个条目）
├── MOBILE.md              # 移动端专项（198 个条目）
├── archived.md            # 归档条目及原因
├── contributing.md        # 贡献格式与提交规范
├── full-guide.md          # 完整贡献指南（含维护者手册）
├── how-to-make-a-pr.md    # PR 提交图文教程
├── code-of-conduct.md     # 行为准则
├── logo.svg               # 项目图标
├── index.js               # 维护脚本（过滤视图/目录/链接审计）
├── tests/
│   └── index.test.js      # index.js 的单元测试
├── .github/               # CI 配置（3 个 workflow）
└── filter/                # 过滤视图（自动生成，勿手改）
    ├── windows-only.md
    ├── macOS-only.md
    ├── linux-only.md
    ├── open-source-only.md
    ├── recommended-only.md
    ├── android-only.md
    ├── iOS-only.md
    ├── open-source-mobile-only.md
    └── recommended-mobile-only.md
```

`README.md` 是桌面端主入口，23 个顶级分类；`MOBILE.md` 单独维护移动端，24 个顶级分类，多了 Education、Health and Wellness、Sports 这类移动端特有场景。两边都在部分分类下再分子类，桌面端共 35 个子分类（如 Developer Tools 下的 API Development、Database、Network Analysis）。`archived.md` 收录被移出主列表的条目并标注原因。

## 维护机制：index.js 与三个 workflow

这份清单能维持"一份主列表、九个视图、永远同步"，靠的是一个约 300 行的 Node 脚本加三个 GitHub Actions workflow。理解这套机制，才知道为什么不能手改 `filter/` 目录。

`index.js` 是一个多命令维护脚本，`node index.js` 不带参数只打印用法，实际功能全靠子命令：

| 子命令 | 作用 |
|--------|------|
| `--categorize` | 按图标从 README.md / MOBILE.md 生成 9 个过滤视图 |
| `--toc` | 重新生成 README 和 MOBILE 的目录（写入 `<!-- AF-TOC -->` 标记之间） |
| `--format` | 清理条目链接（如去掉 URL 尾部斜杠） |
| `--links` | 统计两个主文件的链接总数 |
| `--analyze` | 输出字数、字符数、链接数统计 |
| `--test-links` | 全量链接可达性审计 |
| `--fastgit <msg>` | `git add -A` + commit + push 一条龙 |
| `--all` | 依次跑完统计、目录、过滤视图 |

过滤视图的生成逻辑值得注意：每个文件的前 20 行原样保留（徽章、图标说明表、导航链接都在这里），之后的每一行先去掉空格再做图标匹配——只要含目标平台或属性之外的平台图标（🪟 🍎 🐧 🟢 ⭐ 🤖），整行剔除。这就是过滤视图与主列表逐行对应的实现方式，也解释了贡献规则里"图标必须紧跟描述"的硬要求：图标位置不对，行就会被错误过滤。

三个 workflow 目前全部是 `workflow_dispatch` 手动触发，没有 push 自动化。`renew-categories.yml` 跑 `node index.js --categorize` 后以 github-actions[bot] 身份提交；`Update main file.yml` 跑 `--all` 生成目录加过滤视图；full-guide.md 的维护者手册写明这个 action "should be run once a week"（应每周跑一次）保持同步。`link count.yml` 稍有不同：PR 触碰 `index.js`、测试或 workflow 文件时自动跑 `node --test tests/index.test.js`（Node 内置 test runner，覆盖链接提取、重定向跟随、HEAD 失败退回 GET 这些路径）；手动触发时才对全仓链接做一次审计——HEAD 优先、失败退 GET、单请求 10 秒超时、并发 12、先去重再测。

## 分类精选

下面从仓库的几个主要分类中各挑若干代表性条目，平台标记沿用仓库图标约定（🪟 Windows、🍎 macOS、🐧 Linux）。需要说明的是，仓库的"全平台"指桌面三端，移动端需查 `MOBILE.md`；⭐ 是维护者推荐，🟢 是一个指向源码仓库的链接（开源标记）。

### 音频与音乐制作

- **Audacity** 🪟 🍎 🐧 · 开源录音/音频编辑器 — 仓库 ⭐ 推荐，跨平台音频编辑入门首选。
- **LMMS** 🪟 🍎 🐧 · 开源 DAW — 虚拟乐器加 MIDI 支持，零成本音乐制作，⭐ 推荐。
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

代码编辑器在仓库里独立成 Text Editors 分类，不在 Developer Tools 下。

### 文档与办公

- **LibreOffice** 🪟 🍎 🐧 · Office Suites — 开源办公套件，仓库 ⭐ 推荐。
- **Obsidian** 🪟 🍎 🐧 · Note Taking — 本地笔记，双向链接，仓库 ⭐ 推荐。
- **Draw.io** 🪟 🍎 🐧 · Graphics Tools — 桌面版流程图工具，开源。
- **Calibre** 🪟 🍎 🐧 · E-book — 电子书管理器，仓库 ⭐ 推荐。
- **Sumatra PDF** 🪟 · PDF Tools — 轻量 PDF 阅读器，仓库 ⭐ 推荐。

### 安全工具

仓库的安全区分为 Antivirus、Password Managers、Ad & Tracker Blocking 三个子类。

- **Bitwarden** 🪟 🍎 🐧 · Password Managers — 开源密码管理器。
- **KeePassXC** 🪟 🍎 🐧 · Password Managers — 本地加密数据库的密码管理器。
- **ClamAV** 🪟 🍎 🐧 · Antivirus — 开源杀毒引擎。
- **SaneHosts** 🍎 · Ad & Tracker Blocking — macOS hosts 文件管理器。

7-Zip 在仓库里归入 Compression and Archiving（🟢 ⭐），不在安全区。磁盘加密、系统清理这类专题，这份清单覆盖有限，需要另找来源。

### 系统定制

仓库的 Customize 区分 System Customization 和 Wallpaper Tools 两个子类。这一区各平台的覆盖并不均匀：

- **启动器**：Windows — Flow Launcher（🟢）。macOS 侧清单没有收录 Raycast、Alfred 这类常被推荐的启动器。
- **文件搜索**：Windows — Everything（⭐，归在 Utility 的 File Management 子类）。
- **窗口管理**：Windows — FancyZones（PowerToys 内，⭐）、AltSnap、平铺式的 GlazeWM 与 Komorebi；macOS — Rectangle（⭐）、Magnet；Linux — KWin、i3、Sway、Niri。
- **任务栏与菜单栏**：Windows — ExplorerPatcher（恢复经典任务栏）、TaskbarX、RetroBar；macOS — Hidden Bar、SaneBar 这类菜单栏图标管理。

macOS 启动器、Linux 任务栏定制这两类需求，目前要靠清单外的来源补。

## 任务流案例：在新 Windows 机器上配齐基础工具

假设读者拿到一台全新的 Windows 机器，想用这份清单在 30 分钟内配齐日常工具，流程如下：

1. 打开 `filter/windows-only.md`，拿到仅 Windows 平台的条目子集，避开跨平台噪音。
2. 在 `README.md` 主列表里按场景定位：
   - 浏览器：Browsers 分类下选 Tor Browser 或 ungoogled-chromium。
   - 代码编辑器：Text Editors 分类下选 Visual Studio Code 或 VSCodium（去微软品牌与遥测的社区构建）。
   - 压缩：Compression and Archiving 下选 7-Zip。
   - 密码管理：Security → Password Managers 下选 Bitwarden。
   - 截图：Utility → Screenshot 下选 ShareX。
   - 文件搜索：Utility → File Management 下选 Everything。
3. 想确认是否开源，点条目后的 🟢 图标——它直接链到源码仓库；或打开 `filter/open-source-only.md` 一览全部开源条目。
4. 想看维护者特别推荐的，打开 `filter/recommended-only.md`，只看带 ⭐ 的条目。

这个流程每一步都有明确的文件入口，读者不必在搜索引擎结果里分辨广告与真实推荐。

## 如何参与贡献

发现好软件想加入仓库，先读 [contributing.md](https://github.com/Axorax/awesome-free-apps/blob/main/contributing.md)，完整版规则在 [full-guide.md](https://github.com/Axorax/awesome-free-apps/blob/main/full-guide.md)，PR 操作有 [how-to-make-a-pr.md](https://github.com/Axorax/awesome-free-apps/blob/main/how-to-make-a-pr.md) 图文教程。想推荐软件也可以直接提 Issue，不必自己改文件。

几条容易被 PR 打回的硬规则：

- 只改 `README.md` 和 `MOBILE.md`，条目加在对应分类的**底部**，不要重排现有顺序。
- 描述以句号结尾，不用感叹号或问号，也不以 "A"/"An"/"The" 开头。
- 开源条目的 🟢 必须是指向源码的链接；条目名优先链官网，没有官网才链源码。
- 目录和 `filter/` 目录是自动生成的，不要手改。
- Commit message 用 `Add: 名称` / `Update: 名称` / `Remove: 名称`，可加 `(PC)` 或 `(MOBILE)` 后缀指定列表。
- 收录标准五条：有像样的 GUI、按类别性能合理（full-guide 举的例子是待办事项应用占 1 GB 内存不合格）、功能有用、开发者可信（开源加分）、有一定知名度。

至于成为长期维护者：README 顶部至今挂着指向 [Issue #28](https://github.com/Axorax/awesome-free-apps/issues/28) 的招募链接，但该 Issue 已于 2026 年 4 月 21 日关闭，更可靠的渠道是仓库的 [Discord 服务器](https://discord.com/invite/nKUFghjXQu)。代码贡献（改 index.js 这类）另有规范：commit message 用 `Feat` / `Update` 前缀，纯重构的 PR 不收。

## 采用建议

这份清单适合三类读者：

- **新装机用户**：按平台过滤视图逐场景挑选，避开搜索引擎广告。
- **跨平台用户**：用主列表对照三端兼容性，优先选 🪟 🍎 🐧 三端齐全的工具，减少切换成本。
- **开源偏好者**：直接走 `open-source-only.md`，跳过闭源条目。

使用时注意两点：一是仓库条目会随维护更新增减——本文初稿发表时 Skype 还在 Communication 分类里，它 5 月停服后就被移出了，引用具体软件时建议附上访问日期；二是 `archived.md` 里的条目已被移出主列表，是否还能用要看归档原因（下文 FAQ 有细节）。清单覆盖不到的工具，需要另找专题清单补充。

## 常见问题与故障排查

**Q1：`filter/` 下的过滤视图是手动维护的吗？**
A：不是，由 `index.js --categorize` 按平台图标自动生成。手改 `README.md` 后在本地运行 `node index.js --categorize`，或在 GitHub Actions 里手动触发 renew-categories / Update main file workflow 即可重新生成。直接改 `filter/` 下的文件会在下次生成时被覆盖。

**Q2：为什么有些软件在 `recommended-only.md` 里但不在我的平台上？**
A：⭐ 推荐是维护者按"免费 + 好用"标的，不保证全平台兼容。点开软件官网确认系统要求，再决定是否采用。

**Q3：我想推荐一个好用的免费软件，怎么提交？**
A：最省事的方式是按 contributing.md 的指引提 Issue。想直接改文件的话，遵循 `名称 — 一句话描述（句号结尾）+ 平台图标 + 开源标记` 的行格式，加到对应分类底部，commit message 写 `Add: 名称`。`how-to-make-a-pr.md` 有逐步截图。

**Q4：仓库里的 Stars 数和我自己看的不一致？**
A：文章中的数据截至 2026-10-04，来自 GitHub API 快照。这个仓库四个月涨了约 600 Stars，开源项目数据持续变化，以仓库实际显示为准。

**Q5：`archived.md` 里的软件还能用吗？**
A：先看条目后的归档原因标签，官方分四种：`Unmaintained`（开发者长期停止维护）、`Subpar`（质量不达主列表标准）、`Deferred`（待复核后再决定是否收录）、`Sunset`（项目已关停）。前两类大概率仍能用只是不够好，`Sunset` 则基本不该再采用。如果你发现某个归档条目又活了，可以在 Issue 里提，维护者会评估是否移回主列表。

GitHub：[Axorax/awesome-free-apps](https://github.com/Axorax/awesome-free-apps)。
