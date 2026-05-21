---
title: "Agency Agents：AI agency 全套智能体开箱即用"
date: 2026-05-20
category: tech
tags:
  - 开源
  - AI Agent
  - 自动化
  - 社交媒体
summary: "Agency Agents 是一套开源 AI agent 工具包，每个 agent 都是某一领域的专家，从前端开发到 Reddit 运营再到内容营销，提供可配置的自动化解决方案。"
---

# Agency Agents：AI agency 全套智能体开箱即用

## 一、项目概述

**Agency Agents**（[msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents)）是一套完整的 AI Agency 解决方案，项目汇集了多个垂直领域的 AI Agent，每个 Agent 都是某项工作的专业高手。

> 仓库：[msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents)｜⭐ 1,714｜Python

## 二、核心 Agent 一览

### 1. Frontend Wizard（前端巫师）

**能力：** 快速生成响应式 UI 组件

- React 组件生成（TypeScript）
- Tailwind CSS 样式编写
- 从草图/描述生成页面
- 组件库集成（shadcn/ui、MUI、Ant Design）

### 2. Reddit Community Ninja（Reddit 社区忍者）

**能力：** Reddit 社交媒体运营

- 自动发布帖子（遵守版规）
- 评论互动与回复
- 帖子热度监控
- Karma 增长策略执行

### 3. Whimsy Injector（创意灵感注入器）

**能力：** 生成创意文案和脑洞内容

- 标题生成（A/B 测试变体）
- 创意文案（推文/广告语/产品描述）
- 梗图/表情包推荐
- 品牌调性文案适配

### 4. Reality Checker（事实核查员）

**能力：** 内容质量把关

- 事实核查（防止虚假信息传播）
- 文法/拼写检查
- 合规性审查（广告法/版权）
- 风格一致性检查

## 三、架构设计

```
┌──────────────────────────────────────────────┐
│                Agency Agents                  │
│                                              │
│  ┌──────────────┐  ┌──────────────┐         │
│  │ Frontend     │  │ Reddit       │         │
│  │ Wizard       │  │ Ninja        │         │
│  └──────────────┘  └──────────────┘         │
│                                              │
│  ┌──────────────┐  ┌──────────────┐         │
│  │ Whimsy       │  │ Reality      │         │
│  │ Injector     │  │ Checker      │         │
│  └──────────────┘  └──────────────┘         │
│                                              │
│            ┌──────────────────┐              │
│            │  Shared Memory   │              │
│            │  & Config        │              │
│            └──────────────────┘              │
└──────────────────────────────────────────────┘
         │
    ┌────┴────┐
    ▼         ▼
 LLM API   External APIs
 (OpenAI/  (Reddit,
 Claude)   GitHub, ...)
```

**设计理念：**

- **独立运行**：每个 Agent 可单独使用
- **可组合**：多个 Agent 协同完成复杂任务
- **配置化**：通过配置文件定制行为
- **可扩展**：易于添加新的 Agent 类型

## 四、快速开始

### 安装

```bash
git clone https://github.com/msitarzewski/agency-agents.git
cd agency-agents
pip install -r requirements.txt
```

### 配置 API Keys

```bash
# 复制配置模板
cp config.example.yaml config.yaml

# 编辑 config.yaml 填入你的 API keys
```

```yaml
# config.yaml 示例
llm:
  provider: openai  # 或 anthropic
  model: gpt-4o
  api_key: your-api-key-here

agents:
  frontend:
    enabled: true
    output_dir: ./outputs/frontend
  
  reddit:
    enabled: true
    subreddit_rules_path: ./config/subreddit-rules.json
    credentials:
      username: your-reddit-bot
      password: xxx
      client_id: xxx
      client_secret: xxx
  
  whimsy:
    enabled: true
    brand_guidelines_path: ./config/brand.md
  
  reality_checker:
    enabled: true
    strict_mode: false
```

### 运行单个 Agent

```bash
# 运行 Frontend Wizard
python -m agents.frontend --description "生成一个登录页面"

# 运行 Reddit Ninja
python -m agents.reddit --action post --subreddit tech --title "Hello"

# 运行 Whimsy Injector
python -m agents.whimsy --product "AI写作工具" --count 5
```

### 组合使用

```python
from agency import Agency

agency = Agency(config_path="config.yaml")

# 任务：生成前端页面并检查质量
result = agency.run(
    task="创建产品落地页",
    agents=["frontend", "reality_checker"],
    pipeline_mode=True  # frontend输出给reality_checker审查
)
```

## 五、Agent 详细说明

### Frontend Wizard

**输入：** 页面描述、组件草图、设计稿链接
**输出：** 完整的 React + TypeScript 代码文件

```python
from agents.frontend import FrontendWizard

wizard = FrontendWizard()
component = wizard.generate(
    description="一个电商产品卡片，包含图片、标题、价格、添加到购物车按钮",
    framework="react",
    styling="tailwind"
)
print(component.code)
```

### Reddit Ninja

**输入：** 目标 subreddit、帖子内容
**输出：** 已发布帖子的链接和互动数据

```python
from agents.reddit import RedditNinja

ninja = RedditNinja(credentials=reddit_creds)
result = ninja.post(
    subreddit="technology",
    title="I built an AI agent that does Reddit marketing automatically",
    content="...",
    schedule_time=None  # None=立即发布
)
```

### Whimsy Injector

**输入：** 产品/品牌基本信息
**输出：** 多种风格变体的文案

```python
from agents.whimsy import WhimsyInjector

injector = WhimsyInjector()
variants = injector.generate(
    product="AI写作助手",
    count=10,
    styles=["professional", "playful", "technical", "casual"]
)
for v in variants:
    print(f"[{v.style}] {v.copy}")
```

### Reality Checker

**输入：** 任何文案内容
**输出：** 核查报告（问题列表+修改建议）

```python
from agents.reality import RealityChecker

checker = RealityChecker(strict=False)
report = checker.check(
    content="我们的AI准确率高达99.99%！同类产品最好！",
    checks=["facts", "grammar", "compliance"]
)
# report.issues → [Issue(type="exaggerated_claim", suggestion="...")]
```

## 六、应用场景

| 场景 | Agent 组合 |
|------|------------|
| **独立开发者快速建站** | Frontend Wizard + Reality Checker |
| **社交媒体增长** | Reddit Ninja + Whimsy Injector |
| **内容营销团队** | Whimsy + Reality Checker + Frontend |
| **个人品牌打造** | 所有 Agent 协同 |

## 七、对比同类工具

| 对比项 | Agency Agents | AutoGPT | LangChain Agents |
|--------|---------------|---------|-----------------|
| 专注领域 | **多垂直场景** | 通用任务 | 通用框架 |
| 开箱即用 | ✅ | 一般 | 需自己组装 |
| Reddit 能力 | ✅ 专属 | ❌ | ❌ |
| 社区规模 | 小 | 大 | 大 |
| 维护活跃度 | 活跃 | 中 | 活跃 |

## 八、项目结构

```
agency-agents/
├── agents/
│   ├── __init__.py
│   ├── frontend/
│   │   ├── wizard.py
│   │   └── prompts.py
│   ├── reddit/
│   │   ├── ninja.py
│   │   └── subreddit_rules.py
│   ├── whimsy/
│   │   └── injector.py
│   └── reality/
│       └── checker.py
├── config/
│   └── example.yaml
├── tests/
├── README.md
└── requirements.txt
```

## 九、注意事项

⚠️ **使用提醒：**

1. **Reddit 机器人**：遵守各 subreddit 规则，频繁发帖可能封号
2. **事实核查**：AI 判断不100%准确，关键场景需人工复核
3. **API 成本**：组合使用多个 Agent 会消耗较多 token
4. **合规性**：自动化发帖请注意平台 ToS

## 十、资源链接

- GitHub：[msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents)
- 文档：README 内置详细配置说明
- Star 趋势：今日 ⬆️（1,714★）

---

*AI Agent 领域的垂直解决方案包，适合需要自动化运营的开发者和小型团队。*