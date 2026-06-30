---
title: "xiaohongshu-skills：958 Stars的浏览器自动化方案，用真实账号做小红书运营"
date: "2026-04-07T18:10:00+08:00"
slug: xiaohongshu-skills-browser-automation-guide
description: "深度解析xiaohongshu-skills项目：基于Chrome扩展的浏览器自动化方案，使用真实已登录账号操作小红书。支持OpenClaw和Claude Code，5大Skills覆盖认证、内容发布、搜索互动、竞品分析和复合运营。"
categories: ["技术笔记"]
tags: ["小红书", "浏览器自动化", "Chrome扩展", "Agent Skills", "OpenClaw"]
draft: false
---

# xiaohongshu-skills：958 Stars 的浏览器自动化方案

## 学习目标

读完本文后，你应该能够：

- 理解 xiaohongshu-skills 的技术架构和设计方案，说清楚它跟 MCP 服务方案的核心差异
- 独立完成为 OpenClaw 或 Claude Code 安装和配置 xiaohongshu-skills 的完整流程
- 使用 5 大 Skills（xhs-auth、xhs-publish、xhs-explore、xhs-interact、xhs-content-ops）完成小红书账号的基础操作和复合运营
- 判断在哪些运营场景下选用浏览器自动化方案更合适，哪些场景下应该回避
- 为 xiaohongshu-skills 设计安全的使用节奏，避免触发小红书风控导致账号受限

## 目录

- [项目概述](#项目概述)
- [技术架构解析](#技术架构解析)
  - [为什么选择浏览器自动化？](#为什么选择浏览器自动化)
  - [整体架构](#整体架构)
  - [核心组件](#核心组件)
- [5 大 Skills 深度解析](#5-大-skills-深度解析)
  - [功能总览](#功能总览)
  - [xhs-auth：认证管理](#xhs-auth认证管理)
  - [xhs-publish：内容发布](#xhs-publish内容发布)
  - [xhs-explore：内容发现](#xhs-explore内容发现)
  - [xhs-interact：社交互动](#xhs-interact社交互动)
  - [xhs-content-ops：复合运营](#xhs-content-ops复合运营)
- [安装与配置](#安装与配置)
  - [前置条件](#前置条件)
  - [第一步：安装项目](#第一步安装项目)
  - [第二步：安装浏览器扩展](#第二步安装浏览器扩展)
- [⚠️ 使用警告](#️-使用警告)
- [项目结构](#项目结构)
- [CLI 命令参考](#cli-命令参考)
- [与 xiaohongshu-mcp-skills 对比](#与-xiaohongshu-mcp-skills-对比)
- [实践建议](#实践建议)
- [自测题](#自测题)
- [练习](#练习)
- [进阶路径](#进阶路径)
- [资料口径说明](#资料口径说明)
- [项目地址](#项目地址)
- [总结](#总结)

## 项目概述

**xiaohongshu-skills**是由 autoclaw-cc 团队开发的开源项目，核心特点是「直接使用你已登录的浏览器和真实账号，以普通用户的方式操作小红书」。与 xiaohongshu-mcp-skills 不同，本项目采用**Chrome 扩展+浏览器自动化**的技术路线，而非 MCP 服务接口。

| 指标 | 数值 |
|------|------|
| **GitHub Stars** | 958 |
| **Forks** | 140 |
| **贡献者** | 4 (Angiin, xpzouying, claude, cu1ch3n) |
| **最新提交** | 2026-03-28 |
| **最新版本** | v0.1.0-9d3055b |
| **许可证** | MIT |
| **技术栈** | Python 87.7%, JavaScript 12.3% |

**官方定位**：「小红书自动化 Skills，直接使用你已登录的浏览器和真实账号，以普通用户的方式操作小红书。」

**支持平台**：OpenClaw 及所有兼容 SKILL.md 格式的 AI Agent 平台（如 Claude Code）。

---

## 技术架构解析

### 为什么选择浏览器自动化？

| 对比维度 | MCP 服务方案 | 浏览器自动化方案 |
|---------|------------|----------------|
| **账号安全** | API 接口，风险较低 | 使用真实浏览器，可能触发风控 |
| **功能覆盖** | 受限于 API 能力 | 完整模拟用户行为 |
| **登录方式** | Cookie/Token | 扫码登录，与官方 App 一致 |
| **反爬对抗** | API 限流 | 真实浏览器环境，难被识别 |
| **部署复杂度** | 需要 MCP 服务 | 需要 Chrome 扩展 |

**本项目的选择**：浏览器自动化 + Chrome 扩展

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Agent (OpenClaw/Claude Code)          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    SKILL.md (Skills路由层)                   │
│  xhs-auth │ xhs-publish │ xhs-explore │ xhs-interact │     │
│            xhs-content-ops                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Python CLI (scripts/)                     │
│  login.py │ feeds.py │ search.py │ publish.py │ ...        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               Chrome扩展 (extension/)                        │
│  manifest.json │ background.js │ content.js               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Chrome浏览器 (真实已登录账号)              │
└─────────────────────────────────────────────────────────────┘
```

### 核心组件

| 组件 | 技术 | 职责 |
|------|------|------|
| **SKILL 路由层** | SKILL.md 格式 | 自然语言理解，路由到具体 Skill |
| **Python CLI** | Python 3.11+ | 核心自动化逻辑 |
| **Chrome 扩展** | JavaScript | 浏览器通信桥梁 |
| **本地服务** | bridge_server.py | CLI 与扩展的通信中枢 |

---

## 5 大 Skills 深度解析

### 功能总览

| Skill | 功能 | 核心能力 |
|-------|------|----------|
| **xhs-auth** | 认证管理 | 登录检查、扫码登录、手机验证码登录 |
| **xhs-publish** | 内容发布 | 图文/视频/长文发布、定时发布、分步预览 |
| **xhs-explore** | 内容发现 | 关键词搜索、笔记详情、用户主页、首页推荐 |
| **xhs-interact** | 社交互动 | 评论、回复、点赞、收藏 |
| **xhs-content-ops** | 复合运营 | 竞品分析、热点追踪、批量互动、内容创作 |

### xhs-auth：认证管理

**功能**：管理小红书账号的登录状态

**核心能力**：
- 登录状态检查（返回用户昵称和小红书号）
- 扫码登录（生成二维码，手机小红书扫码）
- 手机验证码登录
- 退出登录（清除 cookies）

**使用示例**：

```bash
# 检查登录状态
python scripts/cli.py check-login
# → {"status": "logged_in", "nickname": "xxx", "user_id": "xxx"}

# 扫码登录
python scripts/cli.py login
# → 显示二维码，等待扫码

# 退出登录
python scripts/cli.py delete-cookies
```

**退出码**：
- `0` — 成功
- `1` — 未登录
- `2` — 错误

---

### xhs-publish：内容发布

**功能**：支持图文、视频、长文多种发布模式

**核心能力**：
- 图文笔记发布（多图支持）
- 视频笔记发布
- 长文模式（一键排版）
- 定时发布
- 分步预览（填写→预览→确认）

**发布流程**：

```bash
# ===== 图文发布 =====

# 方式一：分步发布（推荐，可预览）
# Step 1: 填写表单（不发布）
python scripts/cli.py fill-publish \
    --title-file title.txt \
    --content-file content.txt \
    --images "/abs/path/pic1.jpg" "/abs/path/pic2.jpg"

# Step 2: 确认发布（点击发布按钮）
python scripts/cli.py click-publish

# 方式二：一步发布
python scripts/cli.py publish \
    --title-file title.txt \
    --content-file content.txt \
    --images "/abs/path/pic1.jpg" \
    --tags "标签1" "标签2"

# ===== 视频发布 =====
python scripts/cli.py publish-video \
    --title-file title.txt \
    --content-file content.txt \
    --video "/abs/path/video.mp4"

# ===== 长文模式 =====
python scripts/cli.py long-article \
    --title-file title.txt \
    --content-file content.txt \
    --template "模板名"
```

**分步预览机制**：

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  填写表单   │ -> │   预览确认   │ -> │   正式发布   │
│ fill-publish│    │  (人工检查)  │    │ click-publish│
└─────────────┘    └─────────────┘    └─────────────┘
```

**定时发布**：

```bash
# 定时发布（使用at命令或cron配合）
at 10:00 tomorrow <<EOF
python scripts/cli.py publish \
    --title-file tomorrow_title.txt \
    --content-file tomorrow_content.txt \
    --images "/path/to/image.jpg"
EOF
```

---

### xhs-explore：内容发现

**功能**：搜索和浏览小红书内容

**核心能力**：
- 首页推荐 Feed 获取
- 关键词搜索（支持多维度筛选）
- 笔记详情获取（含评论加载）
- 用户主页信息获取

**搜索筛选参数**：

| 参数 | 说明 | 示例 |
|------|------|------|
| `--keyword` | 搜索关键词 | `--keyword "露营"` |
| `--sort-by` | 排序方式 | `--sort-by "最多点赞"` |
| `--note-type` | 笔记类型 | `--note-type "图文"` |
| `--days` | 发布时间范围 | `--days 7` |

```bash
# 获取首页推荐
python scripts/cli.py list-feeds

# 关键词搜索
python scripts/cli.py search-feeds --keyword "露营"

# 带筛选条件
python scripts/cli.py search-feeds \
    --keyword "露营" \
    --sort-by "最多点赞" \
    --note-type "图文" \
    --days 7

# 查看笔记详情
python scripts/cli.py get-feed-detail \
    --feed-id FEED_ID \
    --xsec-token XSEC_TOKEN

# 获取用户主页
python scripts/cli.py user-profile \
    --user-id USER_ID
```

**返回数据结构**：

```python
# 笔记详情返回
{
    "feed_id": "...",
    "title": "标题",
    "content": "正文内容",
    "author": {
        "nickname": "作者昵称",
        "user_id": "作者ID",
        "followers": 1234
    },
    "likes": 5678,
    "collects": 234,
    "comments": 89,
    "tags": ["标签1", "标签2"],
    "images": ["url1", "url2"],
    "published_at": "2026-03-28"
}
```

---

### xhs-interact：社交互动

**功能**：自动化社交操作

**核心能力**：
- 点赞/取消点赞
- 收藏/取消收藏
- 评论笔记
- 回复评论

```bash
# 点赞
python scripts/cli.py like-feed \
    --feed-id FEED_ID \
    --xsec-token XSEC_TOKEN

# 收藏
python scripts/cli.py favorite-feed \
    --feed-id FEED_ID \
    --xsec-token XSEC_TOKEN

# 评论
python scripts/cli.py post-comment \
    --feed-id FEED_ID \
    --xsec-token XSEC_TOKEN \
    --content "写得真是太棒了！"

# 回复评论
python scripts/cli.py reply-comment \
    --comment-id COMMENT_ID \
    --content "感谢分享！"
```

---

### xhs-content-ops：复合运营

**功能**：高级运营自动化，支持串联多个操作

**核心能力**：
- 竞品分析
- 热点追踪
- 批量互动
- 内容创作辅助

**复合操作示例**：

```bash
# 示例：竞品分析
"""
"搜索刺客信条最火的图文帖子，收藏它，然后告诉我讲了什么"
"""

# Agent自动执行：
# 1. 搜索 → 2. 筛选图文 → 3. 按点赞排序 → 4. 收藏 → 5. 获取详情 → 6. 总结内容

# 内容创作辅助
"""
"帮我分析最近一周露营相关的爆款笔记，找出它们的共同特点"
"""

# Agent自动执行：
# 1. 搜索"露营" 7天内热门笔记
# 2. 获取每篇笔记的详情
# 3. 分析标题、标签、内容结构
# 4. 生成报告
```

---

## 安装与配置

### 前置条件

| 依赖 | 版本 | 说明 |
|------|------|------|
| **Python** | >= 3.11 | 核心运行环境 |
| **uv** | 最新 | 包管理器 |
| **Google Chrome** | 最新 | 浏览器自动化 |

### 第一步：安装项目

**方法一：下载 ZIP（推荐）**

```bash
# OpenClaw示例
<openclaw-project>/skills/xiaohongshu-skills/

# Claude Code示例
<your-project>/.claude/skills/xiaohongshu-skills/
```

**方法二：Git Clone**

```bash
cd <your-agent-project>/skills/
git clone https://github.com/autoclaw-cc/xiaohongshu-skills.git
```

**安装 Python 依赖**：

```bash
cd xiaohongshu-skills
uv sync
```

### 第二步：安装浏览器扩展

1. 打开 Chrome，地址栏输入：`chrome://extensions/`
2. 右上角开启**开发者模式**
3. 点击**加载已解压的扩展程序**
4. 选择本项目的`extension/`目录
5. 确认扩展**XHS Bridge**已启用

**安装完成后**：所有操作都发生在你自己的浏览器里，使用你的真实登录状态和账号信息。

---

## ⚠️ 使用警告

> 虽然本项目使用真实的用户浏览器和账号环境，但仍建议**控制使用频率**，避免短时间内大量操作。频繁的自动化行为可能触发小红书的风控机制，导致账号受限。

**安全建议**：

| 建议 | 说明 |
|------|------|
| **控制频率** | 每次操作间隔至少 5-10 秒 |
| **避免高峰** | 避开小红书的反爬高峰期 |
| **模拟真人** | 不要连续快速操作 |
| **定期检查** | 关注账号状态，及时发现异常 |

---

## 项目结构

```
xiaohongshu-skills/
├── extension/                    # Chrome扩展
│   ├── manifest.json            # 扩展配置
│   ├── background.js           # 后台脚本
│   └── content.js              # 内容脚本
├── scripts/                    # Python自动化引擎
│   ├── xhs/                   # 核心自动化包
│   │   ├── bridge.py          # 扩展通信客户端
│   │   ├── selectors.py       # CSS选择器（集中管理）
│   │   ├── login.py           # 登录+用户信息获取
│   │   ├── feeds.py           # 首页Feed
│   │   ├── search.py          # 搜索+筛选
│   │   ├── feed_detail.py     # 笔记详情+评论
│   │   ├── user_profile.py    # 用户主页
│   │   ├── comment.py         # 评论、回复
│   │   ├── like_favorite.py   # 点赞、收藏
│   │   ├── publish.py         # 图文发布
│   │   ├── publish_video.py   # 视频发布
│   │   ├── publish_long_article.py  # 长文发布
│   │   ├── types.py          # 数据类型
│   │   ├── errors.py         # 异常体系
│   │   ├── urls.py           # URL常量
│   │   ├── cookies.py        # Cookie持久化
│   │   └── human.py          # 行为模拟
│   ├── cli.py                # 统一CLI入口
│   ├── bridge_server.py      # 本地通信服务
│   ├── image_downloader.py   # 媒体下载（SHA256缓存）
│   ├── title_utils.py        # UTF-16标题长度计算
│   └── run_lock.py           # 单实例锁
├── skills/                    # Claude Code Skills
│   ├── xhs-auth/SKILL.md
│   ├── xhs-publish/SKILL.md
│   ├── xhs-explore/SKILL.md
│   ├── xhs-interact/SKILL.md
│   └── xhs-content-ops/SKILL.md
├── SKILL.md                   # 技能统一入口
├── CLAUDE.md                  # 项目开发指南
├── pyproject.toml
└── README.md
```

---

## CLI 命令参考

| 子命令 | 说明 |
|--------|------|
| `check-login` | 检查登录状态 |
| `login` | 获取登录二维码 |
| `delete-cookies` | 清除 cookies |
| `list-feeds` | 获取首页推荐 |
| `search-feeds` | 关键词搜索 |
| `get-feed-detail` | 获取笔记详情 |
| `user-profile` | 获取用户主页 |
| `post-comment` | 评论 |
| `reply-comment` | 回复评论 |
| `like-feed` | 点赞/取消点赞 |
| `favorite-feed` | 收藏/取消收藏 |
| `publish` | 一步发布图文 |
| `publish-video` | 一步发布视频 |
| `fill-publish` | 填写图文（不发布） |
| `fill-publish-video` | 填写视频（不发布） |
| `click-publish` | 确认发布 |
| `save-draft` | 保存草稿 |
| `long-article` | 长文模式 |
| `select-template` | 选择长文模板 |
| `next-step` | 长文下一步 |

---

## 与 xiaohongshu-mcp-skills 对比

| 维度 | xiaohongshu-skills | xiaohongshu-mcp-skills |
|------|---------------------|------------------------|
| **Stars** | 958 | 175 |
| **技术路线** | Chrome 扩展+浏览器自动化 | MCP 服务+API |
| **账号安全** | 使用真实浏览器，有风控风险 | API 接口，风险较低 |
| **部署复杂度** | 需要安装 Chrome 扩展 | 需要 MCP 服务 |
| **功能覆盖** | 完整模拟用户行为 | 受限于 API 能力 |
| **适用场景** | 深度运营自动化 | 轻量级 API 调用 |

---

## 实践建议

### 1. 安全的运营节奏

```python
import time

def safe_operations(operations):
    """安全的操作节奏"""
    for i, op in enumerate(operations):
        op.execute()
        if i < len(operations) - 1:
            time.sleep(random.randint(5, 15))  # 5-15秒随机间隔
```

### 2. 竞品监控

```bash
# 定期搜索竞品账号的热门笔记
watch -n 3600 '
python scripts/cli.py search-feeds \
    --keyword "竞品关键词" \
    --sort-by "最多点赞" \
    --days 7
'
```

### 3. 内容备份

```bash
# 定期备份已发布笔记
python scripts/cli.py get-feed-detail \
    --feed-id $(cat backup_ids.txt) \
    --xsec-token $XSEC_TOKEN \
    > backup_$(date +%Y%m%d).json
```

---

## 项目地址

| 项目 | 地址 |
|------|------|
| **GitHub** | https://github.com/autoclaw-cc/xiaohongshu-skills |
| **姊妹项目** | https://github.com/autoclaw-cc/xiaohongshu-mcp-skills |

## 自测题

请回答以下问题，检验你对 xiaohongshu-skills 的掌握程度：

**问题 1**：xiaohongshu-skills 与 xiaohongshu-mcp-skills 在技术路线上有什么核心差异？

<details>
<summary>查看答案</summary>
xiaohongshu-skills 采用 Chrome 扩展 + 浏览器自动化方案，直接使用真实已登录的浏览器操作小红书；xiaohongshu-mcp-skills 采用 MCP 服务 + API 接口方案。前者能完整模拟用户行为但可能有风控风险，后者受限于 API 能力但风险较低。
</details>

**问题 2**：xhs-auth Skill 支持哪几种登录方式？

<details>
<summary>查看答案</summary>
支持三种登录方式：1) 扫码登录（生成二维码，手机小红书扫码）；2) 手机验证码登录；3) 退出登录（清除 cookies）。
</details>

**问题 3**：xhs-publish Skill 支持哪几种发布模式？

<details>
<summary>查看答案</summary>
支持三种发布模式：1) 图文笔记发布（多图支持）；2) 视频笔记发布；3) 长文模式（一键排版）。
</details>

**问题 4**：分步预览机制的工作流程是什么？

<details>
<summary>查看答案</summary>
分步预览机制分为三步：1) 填写表单（fill-publish，不发布）；2) 预览确认（人工检查）；3) 确认发布（click-publish）。这种设计让用户在自动化发布前有机会检查内容。
</details>

**问题 5**：使用 xiaohongshu-skills 时，为了避免触发小红书风控，应该遵循哪些安全建议？

<details>
<summary>查看答案</summary>
安全建议包括：1) 控制频率（每次操作间隔至少 5-10 秒）；2) 避免高峰时段（避开小红书的反爬高峰期）；3) 模拟真人（不要连续快速操作）；4) 定期检查（关注账号状态，及时发现异常）。
</details>

## 练习

### 练习 1：基础环境搭建

**任务**：在你的本地环境安装 xiaohongshu-skills，并完成首次登录。

**步骤**：
1. 克隆仓库：`git clone https://github.com/autoclaw-cc/xiaohongshu-skills.git`
2. 安装依赖：`cd xiaohongshu-skills && uv sync`
3. 安装 Chrome 扩展：打开 `chrome://extensions/`，开启开发者模式，加载 `extension/` 目录
4. 运行登录：`python scripts/cli.py login`，扫码完成登录
5. 验证登录状态：`python scripts/cli.py check-login`

**预期结果**：命令返回 `{"status": "logged_in", "nickname": "你的昵称", "user_id": "你的用户ID"}`

### 练习 2：内容发布测试

**任务**：创建一个测试笔记并发布到小红书。

**步骤**：
1. 创建 `title.txt` 文件，写入测试标题
2. 创建 `content.txt` 文件，写入测试内容
3. 准备一张测试图片
4. 使用分步发布模式：
   ```bash
   python scripts/cli.py fill-publish \
       --title-file title.txt \
       --content-file content.txt \
       --images "/path/to/image.jpg"
   # 检查预览，确认无误后：
   python scripts/cli.py click-publish
   ```

**预期结果**：笔记成功发布到你的小红书账号，可以在 App 中看到。

### 练习 3：搜索与互动自动化

**任务**：搜索特定关键词的笔记，并对前 5 篇进行点赞。

**步骤**：
1. 搜索笔记：`python scripts/cli.py search-feeds --keyword "测试关键词" --sort-by "最新" --days 7`
2. 从返回结果中选择 5 个 feed_id
3. 对每个 feed_id 执行点赞：
   ```bash
   python scripts/cli.py like-feed \
       --feed-id FEED_ID \
       --xsec-token XSEC_TOKEN
   ```
4. 等待 5-10 秒后再操作下一个

**预期结果**：5 篇笔记都被成功点赞，且账号未被限流。

## 进阶路径

如果你想深入掌握 xiaohongshu-skills 并扩展到更复杂的自动化场景，可以按以下路径进阶：

### 第一步：理解 Chrome 扩展通信机制（1-2 周）

- 深入阅读 `extension/background.js` 和 `extension/content.js`
- 理解 Chrome Extension 的 Message Passing 机制
- 调试网络请求，观察小红书 Web 端的 API 调用模式
- 尝试修改扩展代码，增加新的功能（如批量下载图片）

### 第二步：掌握 Python 自动化核心（2-3 周）

- 阅读 `scripts/xhs/` 目录下的核心模块
- 理解 Selenium/Playwright 在本项目中的使用方式
- 学习如何模拟人类行为（随机延迟、鼠标移动轨迹等）
- 尝试增加新的 Skill，比如"批量私信"或"粉丝数据分析"

### 第三步：集成到 AI Agent 工作流（3-4 周）

- 理解 `SKILL.md` 的格式和路由逻辑
- 学习如何在 OpenClaw 或 Claude Code 中配置和使用 Skills
- 设计一个复合运营场景：搜索竞品 → 分析爆款特征 → 生成内容 → 定时发布
- 实现多账号管理：切换不同账号的 cookies 并安全存储

### 第四步：构建自己的浏览器自动化框架（4-8 周）

- 基于 xiaohongshu-skills 的架构，抽象出通用的浏览器自动化框架
- 支持多个平台（小红书、知乎、B站等）
- 增加反检测机制：User-Agent 轮换、IP 代理池、浏览器指纹混淆
- 部署到服务器，实现 7×24 小时自动化运营

### 第五步：深入研究反爬虫与风控对抗（持续学习）

- 学习小红书的反爬虫机制：行为分析、设备指纹、IP 风险评估
- 研究如何合法合规地使用自动化工具（阅读平台服务条款）
- 参与开源社区，为 xiaohongshu-skills 贡献代码或文档
- 关注 AI Agent 和浏览器自动化领域的最新研究

## 资料口径说明

本文在编写时基于以下来源和假设，请读者注意信息的边界：

1. **信息来源与时效性**：本文基于 xiaohongshu-skills GitHub 仓库（https://github.com/autoclaw-cc/xiaohongshu-skills）的 README 和源码分析，数据截至 2026-03-28。项目仍在活跃开发中，本文描述的功能、CLI 命令、配置方式可能随版本更新而变化，请以最新源码为准。

2. **技术细节验证**：本文描述的 5 大 Skills（xhs-auth、xhs-publish、xhs-explore、xhs-interact、xhs-content-ops）基于源码中的 `skills/` 目录结构，但每个 Skill 的具体参数和返回格式可能因版本不同而有所差异。建议在实际使用前阅读对应 `SKILL.md` 文件。

3. **小红书风控机制**：本文提到的安全建议（控制频率、模拟真人等）是基于通用浏览器自动化最佳实践和小红书社区反馈，并非来自小红书官方文档。平台的风控策略会持续更新，本文的建议可能无法完全避免账号受限风险。

4. **未覆盖的内容**：本文未深入讨论以下主题：
   - Chrome 扩展的打包与发布流程
   - 多账号管理的 cookies 安全存储方案
   - 与小红书 Web 端 API 的直接对接（绕过浏览器自动化）
   - 在 CI/CD 流水线中集成 xiaohongshu-skills
   - 法律合规性分析（自动化操作是否违反小红书服务条款）

5. **术语使用说明**：
   - "小红书"指中国大陆的社交电商平台（Xiaohongshu/Little Red Book）
   - "Agent Skills"是 OpenClaw/Claude Code 等 AI Agent 平台的概念，指 AI 可以调用的技能模块
   - "MCP"指 Model Context Protocol，是 AI Agent 调用外部工具的协议标准

6. **更新记录**：
   - 2026-04-07：初始版本，基于 xiaohongshu-skills v0.1.0-9d3055b
   - 2026-06-30：增加学习目标、目录、自测题、练习、进阶路径、资料口径说明章节，优化为教学文档

## 项目地址

| 项目 | 地址 |
|------|------|
| **GitHub** | https://github.com/autoclaw-cc/xiaohongshu-skills |
| **姊妹项目** | https://github.com/autoclaw-cc/xiaohongshu-mcp-skills |

---

## 总结

xiaohongshu-skills 是一个独特的小红书自动化方案，其核心特点是：

1. **真实环境**：使用你已登录的浏览器和真实账号
2. **完整覆盖**：5 大 Skills 覆盖运营全流程
3. **跨平台兼容**：支持 OpenClaw、Claude Code 等主流 Agent 平台
4. **CLI 工具**：也可以脱离 Agent 直接使用
5. **活跃社区**：958 Stars，4 个贡献者持续维护

**推荐使用场景**：
- ✅ 深度运营自动化（需要完整模拟用户行为）
- ✅ 竞品监控和分析
- ✅ 批量内容发布
- ✅ 社交互动自动化

**注意事项**：
- ⚠️ 控制使用频率，避免账号受限
- ⚠️ 遵守小红书平台规则
- ⚠️ 建议先在测试账号上验证

---

*本文基于 xiaohongshu-skills 项目编写，最后更新时间：2026-06-30*
