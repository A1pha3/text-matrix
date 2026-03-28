---
title: "last30days-skill：AI 全网研究助手从入门到精通"
date: 2026-03-28T17:30:00+08:00
slug: "last30days-skill-ai-agent-research"
description: "深度解析 last30days-skill：13.1k stars 的 AI Agent 研究助手，支持 Reddit/X/YouTube/HN/Polymarket 等8大平台，详解两阶段搜索架构、多维度评分算法、完整安装配置与开发扩展指南。"
draft: false
categories: ["技术笔记"]
tags: ["last30days-skill", "AI Agent", "全网研究", "Reddit", "Polymarket"]
---

# last30days-skill：AI 全网研究助手从入门到精通

> **目标读者**：对 AI 辅助研究、信息聚合、趋势追踪感兴趣的用户。包括：研究人员、投资者、产品经理、开发者、内容创作者
> **核心问题**：如何让 AI Agent 自主研究任意话题，聚合全网最新信息，生成有理有据的深度报告？
> **难度**：⭐⭐⭐（中级）
> **预计阅读时间**：60 分钟

---

## 一、原理分析：为什么需要 last30days-skill

### 1.1 AI 的知识截止日期困境

大语言模型（LLM）存在一个根本性局限：**知识有时间边界**。GPT-4、Claude 3.5 的训练数据有明确的截止日期，无法回答此后发生的事件、新发布的工具、最近的社区讨论。

这在以下场景会造成严重问题：

| 场景 | 问题 |
|------|------|
| 投资决策 | 需要知道某公司最近的动态、市场情绪 |
| 技术选型 | 需要了解某工具的真实用户反馈 |
| 竞品分析 | 需要追踪对手的产品更新和社区反应 |
| 趋势研究 | 需要发现正在爆发的新话题/工具/方法 |

**传统解决方法的缺陷**：

1. **搜索引擎**：返回大量噪音，缺乏社区智慧的聚合
2. **RSS 订阅**：需要手动整理，无法自动综合
3. **社交媒体浏览**：耗时且容易遗漏重要来源

### 1.2 last30days-skill 的核心思想

**核心理念**：让 AI Agent 拥有「上网冲浪做研究」的能力。

```
┌─────────────────────────────────────────────────────────────┐
│                    last30days-skill 工作流                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  输入：任意研究主题                                             │
│    ↓                                                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  第一阶段：广度发现                                      │   │
│  │  并行搜索 8 个平台：                                     │   │
│  │  • Reddit（via ScrapeCreators）                        │   │
│  │  • X/Twitter（via 捆绑 Bird 客户端 或 xAI）             │   │
│  │  • YouTube（via yt-dlp 提取字幕）                       │   │
│  │  • Hacker News（via Algolia 免费 API）                  │   │
│  │  • Polymarket（预测市场 via Gamma API）                  │   │
│  │  • TikTok（via ScrapeCreators）                         │   │
│  │  • Instagram（via ScrapeCreators）                      │   │
│  │  • Bluesky（via AT Protocol）                           │   │
│  └─────────────────────────────────────────────────────┘   │
│    ↓                                                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  第二阶段：智能补充搜索                                   │   │
│  │  • 从第一阶段结果提取 @handle 和 subreddit 名称           │   │
│  │  • 针对性追踪相关账号和社区                               │   │
│  │  • 合并去重，综合评分                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│    ↓                                                        │
│  输出：结构化研究报告                                          │
│  • 关键发现摘要                                               │
│  • 社区共识与分歧                                              │
│  • 预测市场数据（如适用）                                       │
│  • 引用来源和参与度指标                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 解决的核心问题

| 问题 | 解决方案 |
|------|---------|
| AI 知识陈旧 | 实时搜索 30 天内的最新讨论 |
| 信息孤岛 | 跨 8 个平台聚合，发现跨平台趋势 |
| 搜索噪音 | 多维度评分算法排序，过滤低质量内容 |
| 缺乏背景 | 发现@handle、subreddit 等社区生态 |
| 预测盲区 | Polymarket 预测市场提供「真金白银」的情绪指标 |

---

## 二、架构分析：技术深度解析

### 2.1 两阶段搜索架构

last30days-skill 采用了**两阶段搜索架构**，这是其与普通搜索工具的核心差异。

#### 第一阶段：广度发现

**Reddit 搜索**（via ScrapeCreators）：

```
• API: api.scrapecreators.com
• 密钥: SCRAPECREATORS_API_KEY（一个密钥覆盖 Reddit + TikTok + Instagram）
• 特点: 一对多关系查询，支持相关性排序
```

**X/Twitter 搜索**（三条路径，按优先级）：

| 路径 | API | 认证方式 | 特点 |
|------|-----|---------|------|
| 1. 捆绑 Bird 客户端 | Twitter GraphQL | AUTH_TOKEN + CT0 Cookie | 本地运行，无需浏览器 |
| 2. xAI 后备 | api.x.ai | XAI_API_KEY | 无需 Cookie，但需 xAI 账号 |
| 3. OpenAI 后备 | api.openai.com | OPENAI_API_KEY | 仅作为最后备选 |

**YouTube 搜索**：

```
• 工具: yt-dlp（需提前安装: brew install yt-dlp）
• 功能: 搜索视频 + 提取字幕作为内容来源
• 理由: 视频标题可能不包含关键词，但字幕会讨论相关内容
```

**Hacker News**（via Algolia）：

```
• API: hn.algolia.com
• 认证: 无需（公共 API）
• 评分: points + comments 双重指标
```

**Polymarket 预测市场**（via Gamma）：

```
• API: gamma-api.polymarket.com
• 认证: 无需（公共 API）
• 价值: 用真金白银反映市场对未来事件的预期
```

#### 第二阶段：智能补充搜索

这是 v2.0 引入的关键创新。

**问题**：第一阶段搜索可能遗漏「当事人自己的帖子」（当事人账号发帖时不带话题关键词）

**解决方案**：

```
┌─────────────────────────────────────────────────────────────┐
│                 第二阶段：智能补充搜索流程                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 实体提取                                                 │
│     从第一阶段结果提取:                                        │
│     • X 帖子中的 @handle（如 @AnthropicAI）                   │
│     • Reddit 帖子中的 r/subreddit（如 r/Claude）              │
│                                                             │
│  2. 针对性追踪                                               │
│     对于发现的账号:                                            │
│     • 搜索 "from:@handle"（不限关键词）                       │
│     • 找到真正由当事人发布的内容                                │
│                                                             │
│  3. 社区发现                                                 │
│     对于发现的 subreddit:                                     │
│     • 使用 free .json 端点进行精准搜索                         │
│     • 无需额外 API 密钥                                       │
│                                                             │
│  4. 合并去重                                                 │
│     • 与第一阶段结果合并                                       │
│     • 基于 URL 去重                                           │
│     • 跨平台热点检测（同一事件多平台讨论→标记为重要）             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 多维度评分算法

**评分公式**（v2.9+）：

```
总评分 = 0.50 × log1p(score) 
       + 0.35 × log1p(comments) 
       + 0.05 × (ratio×10) 
       + 0.10 × log1p(top_comment_score)
```

| 系数 | 指标 | 权重理由 |
|------|------|---------|
| 0.50 | score（ upvotes/points） | 主要参与度指标 |
| 0.35 | comments | 讨论深度 |
| 0.05 | ratio（顶评/总评） | 社区质量信号 |
| 0.10 | top_comment_score | 优质回复的放大效应 |

**为什么用 log1p 而非原始值？**

- 避免大V帖子主导（10k upvotes 和 100 upvotes 差距被压缩）
- 让小众社区的高质量讨论也能浮现

**Polymarket 专用评分**（5 因子加权）：

| 因子 | 权重 | 说明 |
|------|------|------|
| text_relevance | 30% | 与查询的相关性 |
| 24h_volume | 30% | 流动性/市场活跃度 |
| liquidity_depth | 15% | 市场深度 |
| price_movement_velocity | 15% | 价格变动速度 |
| outcome_competitiveness | 10% | 竞争度（接近 50% 说明争议大） |

### 2.3 X Handle 解析机制

**问题**：搜索「Dor Brothers」（一个电影制作团队），关键词搜索找不到他们的帖子，因为他们发帖时不会说「Dor Brothers」。

**解决方案**：

```
┌─────────────────────────────────────────────────────────────┐
│                   X Handle 解析流程                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 触发条件                                                 │
│     用户搜索特定人物/品牌/产品名称                              │
│                                                             │
│  2. WebSearch 解析                                           │
│     查询 "Dor Brothers X twitter handle site:x.com"          │
│                                                             │
│  3. Handle 验证                                             │
│     确认是官方账号（排除 parody/fan accounts）               │
│                                                             │
│  4. 无过滤搜索                                               │
│     执行 "from:@thedorbrothers"（不限内容）                  │
│                                                             │
│  5. 结果合并                                                 │
│     与关键词搜索结果合并、去重、评分                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.4 目录结构

```
last30days-skill/
├── .claude-plugin/          # Claude Code 插件配置
│   └── plugin.json
├── agents/                  # Agent 特定配置
│   └── openai.yaml         # Codex CLI 配置
├── docs/                    # 文档
├── fixtures/                # 测试数据
├── hooks/                   # 生命周期钩子
│   └── SessionStart/        # 会话启动时验证配置
├── plans/                   # 内部规划文档
├── scripts/                 # 核心脚本
│   ├── last30days.py       # 主入口脚本
│   └── lib/
│       └── vendor/
│           └── bird-search/ # 捆绑的 Twitter GraphQL 客户端
├── skills/
│   └── last30days/         # Skill 定义
│       ├── SKILL.md        # Skill 指令（Claude Code 用）
│       └── ...
├── tests/                   # 测试套件（455+ 测试）
├── variants/
│   └── open/               # 开放变体（带 watchlist）
│       └── SKILL.md
├── .gitignore
├── CHANGELOG.md
├── CLAUDE.md               # Claude Code 开发指南
├── LICENSE                 # MIT
├── README.md
├── release-notes.md
├── SKILL-original.md
├── SPEC.md
├── TASKS.md
├── gemini-extension.json
└── test-run.log
```

---

## 三、使用说明：完整指南

### 3.1 安装

#### 方式一：Claude Code Marketplace（推荐）

```bash
/plugin marketplace add mvanhorn/last30days-skill
/plugin install last30days@last30days-skill
```

#### 方式二：ClawHub

```bash
clawhub install last30days-official
```

#### 方式三：手动安装

```bash
# 克隆到 Claude Code skills 目录
git clone https://github.com/mvanhorn/last30days-skill.git ~/.claude/skills/last30days

# 或 Codex CLI
git clone https://github.com/mvanhorn/last30days-skill.git ~/.agents/skills/last30days
```

### 3.2 配置 API 密钥

#### 创建配置文件

```bash
mkdir -p ~/.config/last30days
cat > ~/.config/last30days/.env << 'EOF'
# Reddit + TikTok + Instagram（一个密钥覆盖三个平台）
# 获取地址: https://scrapecreators.com
SCRAPECREATORS_API_KEY=your_key_here

# X/Twitter 搜索（推荐方式）
# 登录 x.com，打开浏览器 DevTools，复制 auth_token 和 ct0 Cookie
AUTH_TOKEN=your_auth_token
CT0=your_ct0_token

# xAI 后备（可选，没有 Cookie 时使用）
XAI_API_KEY=xai-your_key

# Bluesky（可选）
BSKY_HANDLE=your.bsky.social
BSKY_APP_PASSWORD=xxxx-xxxx-xxxx

# Web 搜索 API（可选，增加网络搜索能力）
PARALLEL_API_KEY=your_key          # Parallel AI（推荐）
BRAVE_API_KEY=your_key              # Brave Search（免费额度 2000/月）
OPENROUTER_API_KEY=your_key         # OpenRouter/Perplexity Sonar Pro
EOF
chmod 600 ~/.config/last30days/.env
```

#### 项目级配置（覆盖全局）

```bash
# 在项目根目录创建
mkdir -p .claude
cat > .claude/last30days.env << 'EOF'
# 这里填项目特定的 API 密钥
SCRAPECREATORS_API_KEY=project_specific_key
EOF
```

#### 诊断检查

```bash
python3 scripts/last30days.py --diagnose
```

输出示例：

```
=== Source Availability ===
✓ ScrapeCreators API: configured
✓ X Search (Bird): working
✓ Bluesky: configured
✓ YouTube (yt-dlp): found in PATH
✓ HN Algolia: available (no key needed)
✓ Polymarket Gamma: available (no key needed)
```

### 3.3 基础用法

#### 标准研究

```bash
/last30days [主题]
```

**示例**：

```bash
/last30days Claude Code best practices
/last30days AI Agent frameworks 2026
/last30days 最新的开源LLM进展
```

#### 指定工具的研究

```bash
/last30days [主题] for [目标工具]
```

**示例**：

```bash
/last30days prompting techniques for ChatGPT
/last30days nano banana pro prompting
/last30days remotion animations for Claude Code
```

### 3.4 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--days=N` | 调整回溯天数（默认 30） | `/last30days X --days=7` |
| `--quick` | 快速模式（8-12 个来源） | `/last30days X --quick` |
| `--deep` | 深度模式（50-70 Reddit，40-60 X） | `/last30days X --deep` |
| `--debug` | 详细日志输出 | `/last30days X --debug` |
| `--sources=reddit` | 仅搜索 Reddit | `/last30days X --sources=reddit` |
| `--sources=x` | 仅搜索 X | `/last30days X --sources=x` |
| `--include-web` | 添加原生网络搜索 | `/last30days X --include-web` |
| `--store` | 保存到 SQLite 数据库 | `/last30days X --store` |
| `--diagnose` | 显示源可用性诊断 | `python3 scripts/last30days.py --diagnose` |

### 3.5 Open 变体：持续追踪模式

适用于需要**定时追踪**的场景（配合 cron 或 always-on bot）。

#### 启用 Open 变体

```bash
cp variants/open/SKILL.md ~/.claude/skills/last30days/SKILL.md
```

#### 添加监控主题

```bash
# 添加关注主题
last30 watch 竞争对手公司 每周
last30 watch AI视频工具 每月
last30 watch Y Combinator 热门公司 每年4月和9月
```

#### 运行研究

```bash
# 手动运行所有关注主题
last30 run all

# 查看累积知识
last30 what have you found about AI video?
```

#### 定时任务配置

Open 变体需要外部调度器触发：

```bash
# crontab 示例：每周一早上 9 点运行
0 9 * * 1 cd ~/projects && last30 run all >> ~/logs/last30.log 2>&1

# 或 macOS launchd
```

### 3.6 实际输出示例

#### 示例 1：AI 工具研究

```
Query: /last30days prompting techniques for legal questions in ChatGPT

Research Output:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The dominant theme is hallucination prevention...

Key patterns discovered:
1. Hallucination prevention clauses
2. Role assignment (paralegal, issue-spotter)
3. Structured output requirements
4. Epistemic humility enforcement
5. Scope limitation

Research Stats:
• 10 Reddit threads (1,200+ upvotes)
• 15 X posts (5,000+ likes)
• 8 YouTube videos (200K+ views)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 示例 2：预测市场研究

```
Query: /last30days anthropic odds

Research Output:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Key findings:
• Pentagon standoff: 22% ban probability ( Polymarket)
• Best AI model (Feb): 98% Anthropic ( Polymarket)
• IPO before OpenAI: 64% YES
• $500B+ valuation: 87% YES

Research Stats:
• 25 X posts (218 likes)
• 13 YouTube videos (719K views)
• 6 HN stories (48 points)
• 11 Polymarket markets

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 四、开发扩展：深度定制指南

### 4.1 架构设计

last30days-skill 的设计遵循**模块化原则**：

```
┌─────────────────────────────────────────────────────────────┐
│                    last30days 核心架构                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SKILL.md ← Claude Code 的指令入口                           │
│    ↓                                                        │
│  last30days.py ← 主脚本，协调各模块                          │
│    ↓                                                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    搜索层                             │   │
│  │  • RedditSearch (ScrapeCreators)                     │   │
│  │  • TwitterSearch (Bird/xAI)                          │   │
│  │  • YouTubeSearch (yt-dlp)                           │   │
│  │  • HNSearch (Algolia)                               │   │
│  │  • PolymarketSearch (Gamma)                          │   │
│  │  • BlueskySearch (AT Protocol)                       │   │
│  │  • WebSearch (Parallel/Brave/OpenRouter)             │   │
│  └─────────────────────────────────────────────────────┘   │
│    ↓                                                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    评分层                             │   │
│  │  • TextSimilarityEngine (双向匹配 + 同义词扩展)        │   │
│  │  • EngagementScorer (参与度归一化)                    │   │
│  │  • CrossPlatformDetector (跨平台热点检测)             │   │
│  │  • PolymarketScorer (5因子加权)                       │   │
│  └─────────────────────────────────────────────────────┘   │
│    ↓                                                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    合成层                             │   │
│  │  • LLMSynthesizer (调用 LLM 生成报告)                 │   │
│  │  • CitationManager (引用管理)                         │   │
│  │  • FormatRenderer (Markdown/JSON 输出)                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 添加新的搜索源

#### 步骤 1：创建搜索模块

```python
# scripts/lib/sources/mysource.py
from typing import List, Dict, Any
from .base import SearchSource

class MySource(SearchSource):
    """自定义搜索源示例"""
    
    name = "mysource"
    api_endpoint = "https://api.mysource.com/search"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def search(
        self, 
        query: str, 
        days: int = 30,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """执行搜索并返回结果"""
        # 1. 调用 API
        response = self._call_api(query, days, max_results)
        
        # 2. 解析响应
        results = self._parse(response)
        
        # 3. 标准化格式
        return [self._normalize(r) for r in results]
    
    def _normalize(self, raw: Dict) -> Dict[str, Any]:
        """标准化为统一格式"""
        return {
            "source": self.name,
            "title": raw.get("title"),
            "url": raw.get("url"),
            "published_at": raw.get("published_at"),
            "engagement": {
                "score": raw.get("upvotes", 0),
                "comments": raw.get("comment_count", 0),
            },
            "author": raw.get("author"),
            "raw": raw,  # 保留原始数据供后续处理
        }
```

#### 步骤 2：注册到主脚本

```python
# scripts/last30days.py

from .sources.mysource import MySource

# 在搜索函数中注册
def get_all_sources(config: Config) -> Dict[str, SearchSource]:
    return {
        # 从配置加载已有源...
        "mysource": MySource(config.get("MYSOURCE_API_KEY")),
    }
```

#### 步骤 3：添加到评分管道

```python
# 在 scorer.py 中
class MultiSignalScorer:
    def __init__(self):
        self.source_weights = {
            # 从配置加载已有权重...
            "mysource": 0.15,  # 自定义源的权重
        }
    
    def score(self, results: List[Dict]) -> List[Dict]:
        for result in results:
            source = result["source"]
            base = result.get("engagement", {}).get("score", 0)
            
            # 应用源特定权重
            weight = self.source_weights.get(source, 0.10)
            result["final_score"] = base * weight
            
        return sorted(results, key=lambda x: x["final_score"], reverse=True)
```

### 4.3 自定义评分算法

如果需要调整评分逻辑：

```python
# scripts/lib/scorer.py

class CustomScorer:
    """自定义评分器示例"""
    
    def __init__(
        self,
        score_weight: float = 0.50,
        comment_weight: float = 0.35,
        ratio_weight: float = 0.05,
        top_comment_weight: float = 0.10,
    ):
        self.weights = {
            "score": score_weight,
            "comment": comment_weight,
            "ratio": ratio_weight,
            "top_comment": top_comment_weight,
        }
    
    def score(self, item: Dict) -> float:
        import math
        
        score = item.get("engagement", {}).get("score", 0)
        comments = item.get("engagement", {}).get("comments", 0)
        top_comment = item.get("engagement", {}).get("top_comment_score", 0)
        ratio = top_comment / (score + 1)  # 避免除零
        
        return (
            self.weights["score"] * math.log1p(score) +
            self.weights["comment"] * math.log1p(comments) +
            self.weights["ratio"] * (ratio * 10) +
            self.weights["top_comment"] * math.log1p(top_comment)
        )
```

### 4.4 自定义输出格式

#### 修改 Markdown 输出

```python
# scripts/lib/renderer.py

class MarkdownRenderer:
    def __init__(self, template: str = "default"):
        self.template = template
    
    def render(self, results: List[Dict], synthesis: str) -> str:
        sections = []
        
        # 标题
        sections.append(f"# Research Report: {results[0]['query']}\n")
        
        # 关键发现
        sections.append("## Key Findings\n")
        sections.append(synthesis)
        
        # 按来源分组
        sections.append("\n## Source Breakdown\n")
        by_source = self._group_by_source(results)
        for source, items in by_source.items():
            sections.append(f"### {source} ({len(items)} results)\n")
            for item in items[:5]:  # 每源最多 5 条
                sections.append(
                    f"- [{item['title']}]({item['url']}) "
                    f"(score: {item['engagement']['score']})\n"
                )
        
        # 统计数据
        sections.append("\n## Research Stats\n")
        sections.append(self._render_stats(results))
        
        return "".join(sections)
```

### 4.5 与外部系统集成

#### 集成到 Slack

```python
# scripts/integrations/slack.py

import requests
from typing import List, Dict

class SlackIntegration:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_report(
        self, 
        title: str, 
        summary: str, 
        results: List[Dict]
    ):
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": title}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": summary}
            },
            {"type": "divider"},
        ]
        
        # 添加 Top 3 结果
        for item in results[:3]:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"• <{item['url']}|{item['title']}> ({item['engagement']['score']} points)"
                }
            })
        
        requests.post(
            self.webhook_url,
            json={"blocks": blocks}
        )
```

#### 集成到 Notion

```python
# scripts/integrations/notion.py

from notion_client import Client

class NotionIntegration:
    def __init__(self, token: str, database_id: str):
        self.notion = Client(auth=token)
        self.database_id = database_id
    
    def create_research_page(
        self,
        title: str,
        summary: str,
        results: List[Dict],
        tags: List[str]
    ):
        properties = {
            "Title": {"title": [{"text": {"content": title}}]},
            "Tags": {"multi_select": [{"name": t} for t in tags]},
            "Summary": {"rich_text": [{"text": {"content": summary[:2000]}}]},
        }
        
        children = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "Top Results"}}]}
            }
        ]
        
        for item in results[:10]:
            children.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {"text": {"content": f"{item['title']} — "}},
                        {"text": {"link": {"url": item["url"]}, "content": "Link"}}
                    ]
                }
            })
        
        self.notion.pages.create(
            parent={"database_id": self.database_id},
            properties=properties,
            children=children
        )
```

### 4.6 测试扩展

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定源的测试
pytest tests/test_reddit.py -v

# 运行带覆盖率
pytest tests/ --cov=scripts --cov-report=html
```

**测试示例**：

```python
# tests/test_mysource.py

import pytest
from scripts.sources.mysource import MySource

class TestMySource:
    @pytest.fixture
    def source(self):
        return MySource(api_key="test_key")
    
    def test_search_returns_results(self, source):
        results = source.search("test query", days=7, max_results=10)
        assert len(results) <= 10
        assert all("title" in r for r in results)
        assert all("url" in r for r in results)
    
    def test_normalize_standardizes_format(self, source):
        raw = {
            "title": "Test Post",
            "url": "https://example.com/post",
            "published_at": "2026-03-28",
            "upvotes": 100,
            "comment_count": 50,
        }
        normalized = source._normalize(raw)
        
        assert normalized["source"] == "mysource"
        assert normalized["engagement"]["score"] == 100
        assert normalized["engagement"]["comments"] == 50
```

---

## 五、最佳实践与常见问题

### 5.1 最佳实践

| 场景 | 建议 |
|------|------|
| 快速了解 | 使用 `--quick` 参数，2-3 分钟完成 |
| 深度研究 | 使用 `--deep` 参数，10-20 分钟完成 |
| 持续追踪 | 使用 Open 变体 + cron job |
| 跨平台热点 | 注意标记为「[also on: Reddit, HN]」的结果 |
| 预测市场 | Polymarket 数据最适合「概率」类问题 |

### 5.2 常见问题

**Q1：搜索返回 0 结果**

A：检查 `--diagnose` 输出，确认 API 密钥配置正确。

**Q2：X 搜索失败**

A：尝试更新 AUTH_TOKEN 和 CT0（Cookie 会过期）。

**Q3：YouTube 字幕未提取**

A：确认 yt-dlp 已安装且在 PATH 中：`which yt-dlp`

**Q4：macOS SSL 证书错误**

```bash
sudo "/Applications/Python 3.12/Install Certificates.command"
```

### 5.3 局限性

| 局限 | 说明 |
|------|------|
| 覆盖范围 | 依赖各平台的 API 可用性 |
| 延迟 | 实时性受限于各平台的爬虫/搜索限制 |
| API 成本 | ScrapeCreators 等服务有使用限制 |
| Cookie 过期 | X 搜索依赖 Cookie，需要定期更新 |

---

## 六、与其他工具对比

| 工具 | 覆盖平台 | 开源 | 实时性 | 适合场景 |
|------|---------|------|--------|---------|
| **last30days-skill** | 8个 | ✅ | 30天内 | 深度研究、趋势发现 |
| Perplexity | Web only | ❌ | 实时 | 快速问答 |
| Custom GPTs | 有限 | ❌ | 依赖配置 | 个人助手 |
| RSS + AI | 依赖订阅源 | 可定制 | 取决于源 | 被动信息流 |

---

## 七、资源链接

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/mvanhorn/last30days-skill |
| 版本 | v2.9.5 |
| Claude Code 插件 | `/plugin marketplace add mvanhorn/last30days-skill` |
| ClawHub | clawhub.ai/skills/last30days-official |
| ScrapeCreators | https://scrapecreators.com |

---

**文档信息**

- 难度：⭐⭐⭐ | 类型：入门到精通 | 更新日期：2026-03-28 | 预计阅读时间：60 分钟
