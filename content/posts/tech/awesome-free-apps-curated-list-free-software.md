---
title: "awesome-free-apps：每个平台最值得收藏的免费软件清单"
date: "2026-05-25T20:16:19+08:00"
slug: "awesome-free-apps-curated-list-free-software"
description: "awesome-free-apps 是一个按平台和场景分类的免费软件精选清单，覆盖 Windows、macOS、Linux 三大桌面平台和 Android、iOS 两大移动端，按音频、浏览器、开发工具、文档、图像、安全等场景组织，每个条目标注平台兼容性和开源状态。"
draft: false
categories: ["技术笔记"]
tags: ["免费软件", "Windows", "macOS", "Linux", "开源", "工具推荐"]
---

## 核心判断

awesome-free-apps 不只是一个软件列表，而是一套**经过筛选的免费工具清单**。它解决的是"这个场景该用什么免费软件"的问题——不是搜索引擎里的广告排名，也不是应用商店的算法推荐，而是真实维护者手动挑选的、去广告的、无营销套路的工具推荐。182K Stars，说明这东西被相当多的人认可。

和一般的 awesome 列表不同，它按平台拆成了桌面版和移动版，桌面版又分别有 Windows Only、macOS Only、Linux Only、Open-source Only、Recommended Only 五个过滤维度，找工具的效率很高。

---

## 内容结构

```
awesome-free-apps/
├── README.md              # 主列表（桌面平台）
├── MOBILE.md              # 移动端专项
├── filter/
│   ├── windows-only.md   # 仅 Windows
│   ├── macos-only.md     # 仅 macOS
│   ├── linux-only.md     # 仅 Linux
│   ├── open-source-only.md # 仅开源
│   └── recommended-only.md # 仅推荐项
└── assets/               # 封面和图标资源
```

---

## 各分类精选

### 音频与音乐制作

| 软件 | 平台 | 类型 | 推荐理由 |
|------|------|------|----------|
| Audacity | Win/Mac/Linux | 开源录音/音频编辑器 | 免费、开源、跨平台，音频编辑入门首选 |
| LMMS | Win/Mac/Linux | 开源 DAW | 虚拟乐器 + MIDI 支持，音乐制作零成本入门 |
| MuseScore | Win/Mac/Linux | 乐谱软件 | 写谱、播放、分享，开源社区活跃 |
| Ardour | Win/Mac/Linux | 专业 DAW | 录音、编辑、混音，专业功能开源 |
| Furnace | Win/Mac/Linux | 开源 chiptune tracker | 复古芯片音乐制作 |

### 浏览器

| 软件 | 平台 | 特性 |
|------|------|------|
| Tor Browser | 全平台 | 隐私浏览，流量走 Tor 网络 |
| ungoogled-chromium | 全平台 | 去 Google 服务的 Chromium |
| LibreWolf | 全平台 | 隐私优先的 Firefox 分叉 |
| Mullvad Browser | 全平台 | 隐私浏览器 + Mullvad VPN 集成 |
| qutebrowser | 全平台 | 键盘驱动，Vim 风格操作 |
| Zen Browser | 全平台 | 设计精美的隐私浏览器 |

### 开发工具

| 软件 | 平台 | 特性 |
|------|------|------|
| VS Code | 全平台 | 微软出品的代码编辑器 |
| OBS Studio | 全平台 | 开源录屏/直播工具 |
| Wireshark | 全平台 | 网络协议分析器 |
| Docker | 全平台 | 容器化平台 |
| VirtualBox | 全平台 | 开源虚拟机 |

### 文档与办公

| 软件 | 平台 | 类型 |
|------|------|------|
| LibreOffice | 全平台 | 开源办公套件 |
| OBSidian | 全平台 | 本地笔记，支持双向链接 |
| Zotero | 全平台 | 开源参考文献管理 |
| Pandoc | 全平台 | 文档格式转换 |
| draw.io | 全平台 | 在线流程图工具 |

### 安全工具

| 软件 | 平台 | 特性 |
|------|------|------|
| Bitwarden | 全平台 | 开源密码管理器 |
| VeraCrypt | 全平台 | 磁盘加密 |
| 7-Zip | Windows | 开源压缩工具 |
| BleachBit | 全平台 | 磁盘清理，隐私保护 |

### 系统定制（按平台）

| 场景 | Windows | macOS | Linux |
|------|---------|-------|-------|
| 启动器 | Flow Launcher | Alfred（免费版）| Albert |
| 文件管理 | Everything | Easy Find | Catfish |
| 窗口管理 | Windhawk | Rectangle | KWin 脚本 |
| 任务栏定制 | ExplorerPatcher | Hidden Bar | Polybar |

---

## 如何使用

### 直接浏览主列表

打开 [README.md](https://github.com/Axorax/awesome-free-apps)，按分类找自己需要的软件。

### 用过滤器精准定位

只想看某个平台的软件？打开 `filter/` 目录下的对应文件：

- [windows-only.md](https://github.com/Axorax/awesome-free-apps/blob/main/filter/windows-only.md) — 只在 Windows 上跑的
- [macos-only.md](https://github.com/Axorax/awesome-free-apps/blob/main/filter/macos-only.md) — 只在 macOS 上跑的
- [open-source-only.md](https://github.com/Axorax/awesome-free-apps/blob/main/filter/open-source-only.md) — 只收录开源项目
- [recommended-only.md](https://github.com/Axorax/awesome-free-apps/blob/main/filter/recommended-only.md) — 维护者特别推荐的

### 移动端专项

Android 和 iOS 的免费软件清单单独维护在 [MOBILE.md](https://github.com/Axorax/awesome-free-apps/blob/main/MOBILE.md)。

---

## 贡献与维护

发现了好软件想加上？阅读 [contributing.md](https://github.com/Axorax/awesome-free-apps/blob/main/contributing.md) 了解提交格式。想成为维护者？查看 [相关 Issue](https://github.com/Axorax/awesome-free-apps/issues/28)。

---

## 总结

awesome-free-apps 是一个可靠的开源软件精选清单，它的价值在于**有人帮你筛选过**，而不是让你在搜索引擎结果里被广告和套壳软件淹没。按平台、按场景、按开源/闭源过滤的设计，让找工具的效率比大多数软件推荐博客高出一截。每个月维护者还在更新，适合收藏下来定期翻翻。

GitHub：[Axorax/awesome-free-apps](https://github.com/Axorax/awesome-free-apps)。