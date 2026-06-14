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

*本文基于 xiaohongshu-skills 项目编写，发布时间：2026-04-07*
