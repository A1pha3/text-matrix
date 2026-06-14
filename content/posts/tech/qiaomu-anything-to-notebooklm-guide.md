---
title: "qiaomu-anything-to-notebooklm：任意内容一键转播客、PPT、思维导图"
date: 2026-05-16T03:02:00+08:00
slug: "qiaomu-anything-to-notebooklm-guide"
description: "qiaomu-anything-to-notebooklm 是一个 Claude Code Skill，可将微信公众号、付费文章、YouTube、播客、PDF、EPUB 等任意内容自动抓取并上传至 Google NotebookLM，生成播客、PPT、思维导图、Quiz 等多种格式。其核心亮点是 6 层级联付费墙绕过策略，支持 300+ 付费新闻网站。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "NotebookLM", "MCP", "付费墙绕过", "内容处理", "AI工具"]
---

# qiaomu-anything-to-notebooklm：任意内容一键转播客、PPT、思维导图

在信息爆炸的时代，我们每天要处理来自微信文章、付费新闻、播客、PDF、YouTube 视频等各种来源的内容。但每种内容格式各异，获取成本高，整理耗时——你可能想在通勤时听一篇长文做成播客，把一本书做成 PPT 分享给团队，把付费报道做成思维导图理清逻辑。

[qiaomu-anything-to-notebooklm](https://github.com/joeseesun/qiaomu-anything-to-notebooklm)（简称 qiaomu）正是为解决这个痛点而生。这是一个运行在 [Claude Code](https://docs.anthropic.com/claude-code) 中的 Skill，只需一句自然语言，就能把**任意内容**变成**任意你想要的格式**。

> Github: [joeseesun/qiaomu-anything-to-notebooklm](https://github.com/joeseesun/qiaomu-anything-to-notebooklm) · ⭐ 2601 · Python · MIT License

---

## 项目概览

| 项目 | 信息 |
|------|------|
| **作者** | [Joe (joeseesun)](https://github.com/joeseesun) |
| **开源时间** | 2026 年 1 月 |
| **Stars** | 2601 |
| **Forks** | 267 |
| **语言** | Python |
| **许可证** | MIT |
| **定位** | Claude Code Skill，多源内容处理器 |

核心工作流非常简洁：

```
用户自然语言输入（如"把这篇付费文章生成播客"）
        ↓
Claude Code Skill 智能识别内容源类型
        ↓
自动抓取内容（含付费墙绕过）
        ↓
上传至 Google NotebookLM
        ↓
NotebookLM AI 生成目标格式（播客/PPT/思维导图/Quiz 等）
```

---

## 核心能力：15+ 种内容源全覆盖

qiaomu 支持的内容源分为四大类：

### 社交与媒体

| 内容源 | 说明 |
|--------|------|
| **微信公众号** | 通过 MCP 浏览器模拟抓取，绕过反爬虫 |
| **X/Twitter** | 支持推文和长线程 |
| **YouTube** | 自动提取字幕 |
| **播客** | 支持小宇宙、喜马拉雅、B 站 |

### 网页（含付费墙绕过）

| 内容源 | 说明 |
|--------|------|
| **300+ 付费网站** | NYT、WSJ、FT、Economist、The Information 等 |
| **任意公开网页** | 新闻、博客、文档 |
| **搜索关键词** | 自动汇总搜索结果 |

### 电子书与文档

| 内容源 | 说明 |
|--------|------|
| **PDF** | 支持扫描件 OCR |
| **EPUB** | 电子书全文提取 |
| **Markdown** | .md 文件 |
| **纯文本** | .txt 文件 |

### Office 与其他

| 内容源 | 说明 |
|--------|------|
| **Word** | .docx |
| **PowerPoint** | .pptx |
| **Excel** | .xlsx |
| **图片** | JPEG/PNG，自动 OCR |
| **音频** | WAV/MP3，自动转录 |
| **ZIP 压缩包** | 批量处理 |

---

## 技术架构解析

qiaomu 的整体架构分为四层：

```
┌─────────────────────────────────┐
│       用户自然语言输入            │
│  "把这篇付费文章生成播客"         │
└───────────────┬─────────────────┘
                ↓
┌─────────────────────────────────┐
│      Claude Code Skill          │
│  · 智能识别内容源类型             │
│  · 自动调用对应工具              │
└──────┬──────────┬───────────────┘
       │          │
       ↓          ↓
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ 微信 MCP │  │付费墙绕过│  │ 播客转写  │  │markitdown│
│浏览器模拟│  │6层级联策略│  │Get笔记API │  │ 文件转换  │
└────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
     └─────────────┴─────────────┴─────────────┘
                      ↓
           ┌──────────────────┐
           │   NotebookLM API │
           │  · 上传内容源     │
           │  · AI 生成目标格式│
           └────────┬─────────┘
                    ↓
           ┌──────────────────┐
           │   生成文件        │
           │ .mp3/.pdf/.json   │
           └──────────────────┘
```

### 关键模块

**1. 微信 MCP 服务器（wexin-read-mcp）**

微信公众号有严格的反爬虫机制。qiaomu 通过 Playwright 浏览器模拟真实用户访问来获取内容。核心文件：

- `wexin-read-mcp/src/server.py` — MCP 入口
- `wexin-read-mcp/src/scraper.py` — Playwright 浏览器模拟
- `wexin-read-mcp/src/parser.py` — HTML 解析

**2. 付费墙绕过（scripts/fetch_url.sh）**

这是 qiaomu 最具技术含量的部分。实现了 6 层级联策略：

```
Level 1: 代理服务（r.jina.ai / defuddle.md）
Level 2: 站点专属 Bot UA（Googlebot ~50站 / Bingbot ~4站）
Level 3: 通用绕过（UA伪装 + X-Forwarded-For + Referer伪装 + AMP + EU IP）
Level 4: archive.today 存档（CAPTCHA 自动检测）
Level 5: Google Cache
Level 6: agent-fetch 本地工具
```

绕过策略的技术原理：

| 技术 | 原理 | 覆盖率 |
|------|------|--------|
| **Googlebot UA + X-Forwarded-For** | 搜索引擎爬虫白名单，直接获取全文 | ~50 站 |
| **Bingbot UA** | 同上，部分站点对 Bing 更友好 | ~4 站 |
| **Cookie 清空 + Referer 伪装** | 清除计量 cookie，伪装来自 Google/Facebook/Twitter | 计量付费墙 |
| **AMP 页面** | AMP 版付费墙实现较弱 | ~10 站 |
| **JSON-LD 提取** | 从 HTML 内嵌的结构化数据提取 articleBody | 通用 |
| **archive.today** | 从网页存档获取已保存的内容 | 兜底方案 |

**3. 播客转写（scripts/get_podcast_transcript.py）**

通过 Get 笔记 API 转写小宇宙、喜马拉雅、B 站视频音频，再上传 NotebookLM 生成目标格式。

**4. 文件转换（markitdown）**

微软开源的 markitdown 负责将 PDF、Word、PPT、Excel 等文件转换为 Markdown 格式，供 NotebookLM 处理。

---

## 快速开始

### 前置需求

- Python 3.9+
- Git
- Claude Code（已安装或可安装）

### 安装步骤

```bash
# 1. 克隆到 Claude skills 目录
cd ~/.claude/skills/
git clone https://github.com/joeseesun/qiaomu-anything-to-notebooklm
cd qiaomu-anything-to-notebooklm

# 2. 一键安装所有依赖
./install.sh

# 3. 按提示配置 MCP，然后重启 Claude Code
```

### 验证环境

```bash
# NotebookLM 认证（只需一次）
notebooklm login
notebooklm list  # 验证成功

# 环境检查（可选）
./check_env.py
```

### 可选：播客转写配置

如需使用小宇宙/喜马拉雅/B 站转写功能，配置 Get 笔记 API：

```bash
export GETNOTE_API_KEY="your_api_key"
export GETNOTE_CLIENT_ID="your_client_id"
```

---

## 使用场景与示例

### 场景 1：付费文章 → 播客

```
你：把这篇 The Information 文章生成播客 https://www.theinformation.com/articles/...

AI 自动执行：
  ✓ 检测付费墙 → Googlebot UA 绕过
  ✓ 获取完整文章内容
  ✓ 上传到 NotebookLM
  ✓ 生成播客

结果：/tmp/article_podcast.mp3
```

### 场景 2：播客（小宇宙）→ PPT

```
你：这期小宇宙播客做成 PPT https://xiaoyuzhoufm.com/episode/...

AI 自动执行：
  ✓ Get笔记 API 转写音频（2-5 分钟）
  ✓ 上传转写文本到 NotebookLM
  ✓ 生成 PPT

结果：/tmp/podcast_slides.pdf（25 页）
```

### 场景 3：电子书 → 深度分析

```bash
python main.py /Users/joe/Books/sapiens.epub --deep-analysis
```

深度分析模式会自动生成 12 个问题，分 3 轮递进：

| 轮次 | 问题数 | 目的 | 示例 |
|------|--------|------|------|
| 第一轮·概览与框架 | 4 | 建立整体认知 | 概括主题、列出结构、提取核心论点 |
| 第二轮·深度挖掘 | 5 | 深入细节 | 拆解论证逻辑、分析矛盾、提炼核心洞察 |
| 第三轮·综合与反刍 | 3 | 认知升级 | 最大认知改变、行动指南 |

NotebookLM 在同一会话中保持上下文，后轮问题自动受益于前轮回答，形成真正的"递进式"深度分析。

### 场景 4：X/Twitter 线程 → 思维导图

```
你：这个推文线程做成思维导图 https://x.com/user/status/123...

AI 自动执行：
  ✓ 代理级联获取推文内容（含完整线程）
  ✓ 上传到 NotebookLM
  ✓ 生成思维导图

结果：/tmp/tweet_mindmap.json
```

### 场景 5：微信文章 → 飞书文档

```bash
python main.py https://mp.weixin.qq.com/s/abc123 --deep-analysis --to-feishu
```

---

## 深度分析模式详解

qiaomu 的深度分析模式是其核心能力之一，通过三轮递进式提问实现真正有深度的内容理解：

```bash
python main.py <内容路径或URL> --deep-analysis
python main.py <内容路径或URL> --deep-analysis --to-feishu  # 输出到飞书
```

三轮策略：

**第一轮·概览与框架**（4 个问题）
- 概括主题
- 列出结构
- 提取核心论点
- 挖掘颠覆性内容

**第二轮·深度挖掘**（5 个问题）
- 拆解论证逻辑
- 分析矛盾
- 提炼核心洞察
- 提出尖锐批评
- 挖掘未被明确说出的假设

**第三轮·综合与反刍**（3 个问题）
- 最大认知改变
- 行动指南
- 推荐理由

由于 NotebookLM 保持上下文，后轮问题自动受益于前轮回答，形成真正的递进式深度分析，而非孤立的问答堆砌。

---

## 适用场景与优势

### 适合使用 qiaomu 的场景

- **知识工作者**：需要处理大量多源内容（新闻、论文、报告）
- **Claude Code 用户**：已在使用 Claude Code，希望扩展内容处理能力
- **内容创作者**：需要将不同来源的内容转化为不同格式（播客、PPT、思维导图）
- **研究者**：需要对长文/书籍进行深度分析，生成结构化笔记
- **学习者**：想把微信文章、付费报道等做成 Quiz 自测掌握程度

### qiaomu 的核心优势

1. **全自动化**：从内容获取到格式生成，一气呵成，无需手动操作
2. **付费墙绕过**：6 层级联策略，覆盖 300+ 付费新闻网站
3. **多格式输出**：播客、PPT、思维导图、Quiz、报告、信息图、闪卡
4. **智能识别**：自动判断输入类型，无需手动指定
5. **深度分析**：三轮递进式提问，实现真正的内容理解

### 使用边界与限制

- **NotebookLM 限制**：内容长度推荐 1000-10000 字，最短约 500 字，最长约 50 万字
- **付费墙**：部分硬付费墙（如 The Information）需要 archive.today 存档，可能需要人工验证 CAPTCHA
- **微信抓取**：依赖 Playwright 浏览器模拟，需要配置 MCP
- **播客转写**：需要 Get 笔记 API Key（非免费）
- **用途**：仅限个人学习研究，建议支持优质新闻媒体，购买订阅

---

## 项目结构

```
qiaomu-anything-to-notebooklm/
├── SKILL.md                          # Skill 定义文件
├── README.md                         # 项目说明
├── main.py                           # 主入口：CLI 智能处理器
├── install.sh                        # 一键安装脚本
├── check_env.py                      # 13 项环境检查
├── package.sh                        # 打包分享脚本
├── requirements.txt                  # Python 依赖
├── LICENSE                           # MIT
├── scripts/
│   ├── fetch_url.sh                  # URL 抓取 + 付费墙绕过（6 层级联）
│   └── get_podcast_transcript.py     # 播客/视频转写（Get笔记 API）
├── wexin-read-mcp/                   # 微信公众号 MCP 服务器
│   └── src/
│       ├── server.py                 # MCP 入口
│       ├── scraper.py                # Playwright 浏览器模拟
│       └── parser.py                 # HTML 解析
└── feishu-read-mcp/                  # 飞书文档 MCP 服务器
    └── src/
        ├── server.py                 # MCP 入口
        ├── scraper.py                # 飞书文档抓取
        ├── parser.py                 # HTML → Markdown
        └── image_handler.py          # 图片处理
```

---

## 故障排查

### MCP 工具未找到

```bash
# 手动启动 MCP 服务器
python ~/.claude/skills/qiaomu-anything-to-notebooklm/wexin-read-mcp/src/server.py

# 重新安装依赖
cd ~/.claude/skills/qiaomu-anything-to-notebooklm/wexin-read-mcp
pip install -r requirements.txt
playwright install chromium
```

### NotebookLM 认证失败

```bash
notebooklm login     # 重新登录
notebooklm list      # 验证
```

### 付费墙绕过失败

部分硬付费墙网站（如 The Information）服务器端不发送内容，需要 archive.today 存档。脚本会自动检测并提示：

```
⚠️  archive.ph needs human verification.
   已自动打开浏览器，请完成验证后重试
```

---

## 总结

qiaomu-anything-to-notebooklm 是一个将多源内容处理与 NotebookLM AI 生成能力无缝衔接的工具。它的最大价值在于：

1. **极大降低了内容格式转换的成本**——你不需要在各种工具之间切换，只需一句自然语言
2. **付费墙绕过**让它真正成为"全网内容处理器"，不只是能处理公开内容
3. **深度分析模式**提供了一种结构化的内容理解方法，而非简单的摘要

如果你已经在使用 Claude Code，qiaomu 是一个值得加入技能库的工具；如果你是知识工作者或内容创作者，它能显著提升你处理多源内容效率。

---

## 参考链接

- GitHub 仓库：https://github.com/joeseesun/qiaomu-anything-to-notebooklm
- Google NotebookLM：https://notebooklm.google.com/
- Claude Code 文档：https://docs.anthropic.com/claude-code
- 项目作者 Joe：https://github.com/joeseesun
- Twitter：[@vista8](https://x.com/vista8)