---
title: "SocialAutoUpload: 一键发布视频到抖音、B站、小红书等7大平台"
date: "2026-05-31T10:20:00+08:00"
slug: "dreammis-social-auto-upload-multi-platform"
description: "SocialAutoUpload 是一个开源社交媒体自动化上传工具，支持抖音、B站、小红书、快手、微信视频号、百家号、TikTok 等7大平台。提供 CLI 命令和 OpenClaw/Claude Code Skills，AI Agent 可直接使用。"
draft: false
categories: ["技术笔记"]
tags: ["自动化工具", "社交媒体", "视频上传", "Python", "Browser Automation"]
---

做内容矩阵的同学，最头疼的事情之一就是：**每次录完视频，还要手动登录七七八八的平台一个个上传、填标题、设定时发布**。一个平台 10 分钟，七个平台就一个多小时没了。

**SocialAutoUpload** 这个项目，就是为了解决这个问题而生。它是一个完全开源的社交媒体批量上传工具，支持抖音、Bilibili、小红书、快手、微信视频号、百家号、TikTok 等 7 大主流平台，提供 CLI 命令行工具和 AI Agent Skills，让上传工作可以自动化、甚至被 AI 控制。

GitHub Star 数量已经达到 **9k+**，社群成员 2000+。

---

## 核心功能一览

| 平台 | 登录 | 视频上传 | 图文上传 | 定时发布 | CLI | Skill |
|------|:----:|:--------:|:--------:|:--------:|:---:|:-----:|
| 抖音 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Bilibili | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ |
| 小红书 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 快手 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 视频号 | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| 百家号 | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| TikTok | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |

---

## 项目架构设计

项目采用平台解耦的架构设计，每个平台有独立的 `uploader` 模块，主要文件结构：

```
social-auto-upload/
├── uploaders/              # 各平台 uploader
│   ├── douyin_uploader.py  # 抖音
│   ├── bilibili_uploader.py # Bilibili
│   ├── kuaishou_uploader.py # 快手
│   ├── xiaohongshu_uploader.py # 小红书
│   ├── tencent_uploader.py   # 视频号
│   ├── baijiahao_uploader.py # 百家号
│   └── tiktok_uploader.py   # TikTok
├── skills/                 # AI Agent Skills
│   ├── douyin-upload/
│   ├── kuaishou-upload/
│   ├── xiaohongshu-upload/
│   └── bilibili-upload/
├── sau/                    # CLI 主程序入口
├── examples/              # 示例脚本
└── docs/                   # 文档
```

核心哲学来自项目 README 里的一句话：

> **"AI 这么强，为什么还需要这个项目？"**
> 在你使用 AI 的能力、browser agent 等等，每次都让 agent 重新解析网页、截图理解、临场判断。而上传这种高频、重复、无聊的工作，应该交给脚本和程序去执行。

这就是项目存在的根本价值：**把 AI 不擅长的高频重复操作自动化**，让 AI 把精力放在真正需要推理判断的地方。

---

## 快速上手

### 安装（推荐 uv）

```bash
git clone https://github.com/dreammis/social-auto-upload.git
cd social-auto-upload

# 推荐使用 uv 部署
uv sync --frozen

# 安装 sau CLI
pip install -e .
```

### Docker 部署

```bash
docker-compose up
# 启动后访问 http://127.0.0.1:8501
```

---

## CLI 用法示例

`sau` 是项目的主 CLI 命令（`sau` = social-auto-upload 的缩写），覆盖抖音、快手、小红书、Bilibili 四个平台：

### 抖音

```bash
# 登录账号
sau douyin login --account my_douyin

# 检查账号状态
sau douyin check --account my_douyin

# 上传视频
sau douyin upload-video \
    --account my_douyin \
    --file videos/demo.mp4 \
    --title "示例标题" \
    --desc "示例简介"

# 上传图文笔记
sau douyin upload-note \
    --account my_douyin \
    --images videos/1.png videos/2.png \
    --title "图文标题" \
    --note "图文正文"
```

### 小红书

```bash
sau xiaohongshu login --account my_xhs
sau xiaohongshu upload-video \
    --account my_xhs \
    --file videos/demo.mp4 \
    --title "示例标题" \
    --desc "示例简介"

sau xiaohongshu upload-note \
    --account my_xhs \
    --images videos/1.png videos/2.png videos/3.png \
    --title "图文标题" \
    --note "图文正文"
```

### Bilibili

```bash
sau bilibili login --account my_bili
sau bilibili upload-video \
    --account my_bili \
    --file videos/demo.mp4 \
    --title "示例标题" \
    --desc "示例简介" \
    --tid 249  # 分区 ID
```

**注意**：Bilibili 的 `biliup` 会在首次运行时自动下载，无需手动安装。

---

## AI Agent 集成

这个项目最大的亮点，是它为 AI Agent 工具（OpenClaw、Claude Code、Codex 等）提供了 Skill 封装。你只需要把仓库和引导提示词发给 AI Agent，它就能自动完成安装和使用。

### Agent Bootstrap Prompt

项目提供了专门的引导提示词：[`docs/agent-bootstrap.md`](https://github.com/dreammis/social-auto-upload/blob/main/docs/agent-bootstrap.md)，告诉 Agent：

- 优先按当前主线安装项目
- 优先使用 `uv`、`sau` CLI 和 `skills/`
- 先验证 `bilibili`、`douyin`、`kuaishou`、`xiaohongshu` 四个平台入口是否可用

对于 AI 内容矩阵运营者来说，这意味着：**你只需要告诉你的 AI 助手"把视频发到抖音和小红书"，剩下的全部由 AI 自动完成**。

---

## 当前重构计划

项目作者在 2026 年 3 月宣布启动一轮整体重构，重点包括：

1. **更隐蔽的自动化方案**：降低被平台检测的风险
2. **补齐图文能力**：小红书/抖音图文功能继续完善
3. **全平台 CLI 化**：所有平台都接入 `sau` 命令行
4. **Skill 化**：面向 OpenClaw、Claude Code 等工具全面 Skill 化
5. **切换到 Patchright**：用 `patchright` 替代 `playwright`，提升兼容性与隐蔽性
6. **无头模式优先**：浏览器后台运行，适合 CLI、服务端、定时任务场景

> 原来的 Web UI 仍然保留，但已经不是主线，不保证与当前 uploader/CLI 完全同步。

---

## 技术亮点

### Patchright 驱动

项目正在从 Playwright 切换到 [Patchright](https://github.com/microsoft/playwright)（微软出品的 Playwright 分支），这是一个更适合自动化场景的反检测浏览器驱动，能有效降低被平台识别为机器人的风险。

### 多账号管理

每个账号对应一个独立的账号文件（`--account <name>`），可以同时管理多个账号，按账号名并发执行任务，非常适合矩阵运营场景。

### 自动更新机制

- Bilibili 的 `biliup` 上传器支持自动检测上游 release 并更新
- 程序会在首次运行时自动下载所需依赖，后续自动检查更新

---

## 常见问题

### 视频上传失败怎么办？

```bash
# 先检查账号状态
sau douyin check --account my_douyin
```

### ImageMagick 安全策略报错

```
ImageMagick的安全策略阻止了与临时文件相关的操作
```

解决：修改 ImageMagick 配置文件中 `policy.xml`，将 `pattern="@"` 条目的 `rights="none"` 改为 `rights="read|write"`。

### 系统打开文件数过多

```
OSError: [Errno 24] Too many open files
```

解决：
```bash
ulimit -n 10240  # 调高系统文件描述符限制
```

---

## 使用场景

这个项目最适合以下几类用户：

1. **内容矩阵运营者**：一个人管 7+ 平台，手动上传太费时间
2. **AI 内容创作者**：用 AI 生成内容，再用自动化工具分发到各平台
3. **独立开发者**：帮客户做社交媒体管理工具，需要底层上传能力
4. **AI Agent 集成**：把上传能力封装进 AI Agent，实现"一句话发布视频"

---

如果你需要批量管理多个社交媒体账号，或者想把视频上传这件事交给 AI Agent 自动完成，SocialAutoUpload 是目前开源社区里功能最完善、平台覆盖最广的选择。