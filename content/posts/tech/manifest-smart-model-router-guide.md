---
title: "Manifest：4.3K Stars·OpenClaw智能模型路由器·节省70%成本"
date: 2026-04-12T02:31:39+08:00
slug: manifest-smart-model-router-guide
description: "Manifest 是一个 OpenClaw 智能模型路由器，使用 23 维度评分算法在 2ms 内做出路由决策，可节省高达 70% 的成本，支持 300+ 模型。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "模型路由", "OpenClaw", "成本优化", "API"]
---

# Manifest：4.3K Stars·OpenClaw智能模型路由器·节省70%成本·23维度评分算法·2ms路由决策·300+模型支持

## 一，项目概述

### 1.1 Manifest 是什么

**Manifest** 是一个**智能模型路由器**，专为 OpenClaw 设计。它位于 Agent 和 LLM Provider 之间，对每个请求进行评分，然后路由到**最适合且最便宜**的模型。

> "Take control of your OpenClaw costs"

**核心理念**：简单问题 → 快速便宜的模型 → 困难问题 → 强大的模型 → **您无需思考，自动省钱**。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | **4.3k** ⭐ |
| Forks | 235 |
| 贡献者 | **5** |
| 提交数 | **4,287** |
| 发版数 | **243** |
| 最新版本 | **v5.45.1** (2026-04-10) |
| 许可证 | **MIT** |
| 语言 | **TypeScript 95.4%**, CSS 4.0% |

### 1.3 成绩单

```
┌─────────────────────────────────────────────────────────────┐
│                    Manifest 成绩单                                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   💰 成本节省: 最高 70%                                         │
│   ⚡ 路由速度: < 2ms (23维度评分算法)                          │
│   🔄 模型数量: 300+ 模型                                       │
│   🌐 Provider: OpenAI / Anthropic / Google / DeepSeek / ...   │
│   🔒 隐私: 本地部署 / 元数据仅云端                             │
│   📊 透明: 开放评分，可查看路由决策原因                         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 二，核心原理

### 2.1 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    Manifest 架构                                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│                    OpenClaw Agent                                  │
│                            ↓                                       │
│   ┌─────────────────────────────────────────────────────┐   │
│   │              Manifest Router                              │   │
│   │   ┌────────────────┐  ┌────────────────┐               │   │
│   │   │  23维评分器   │  │   Tier 选择器   │               │   │
│   │   │ (2ms内完成)   │  │  simple/standard │             │   │
│   │   └────────────────┘  │  complex/reasoning │             │   │
│   │   └────────────────┘  └────────────────┘               │   │
│   │   ┌────────────────┐  ┌────────────────┐               │   │
│   │   │   备选管理器   │  │   成本追踪器   │               │   │
│   │   │ (故障自动切换) │  │  (Token/费用)  │               │   │
│   │   └────────────────┘  └────────────────┘               │   │
│   └─────────────────────────────────────────────────────┘   │
│                            ↓                                       │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│   │OpenAI  │ │Anthropic │ │  Gemini  │ │ DeepSeek │  ...   │
│   └─────────┘ └─────────┘ └─────────┘ └─────────┘        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 评分算法

```python
# Manifest 23维评分算法伪代码
def score_request(request):
    """
    23维度评分，每个维度权重不同
    总分 = Σ(维度分数 × 权重)
    """
    dimensions = {
        'complexity': analyze_complexity(request),           # 复杂度
        'length': analyze_length(request),                 # 长度
        'has_code': detect_code(request),                  # 是否含代码
        'has_math': detect_math(request),                # 是否含数学
        'has_reasoning': detect_reasoning(request),       # 是否需推理
        'language': detect_language(request),             # 语言
        'domain': detect_domain(request),                 # 领域
        # ... 共23个维度
    }
    
    tier = select_tier(total_score)
    # tier: simple / standard / complex / reasoning
    
    model = select_best_model_in_tier(tier)
    return model
```

### 2.3 四层分级

| 分层 | 难度 | 模型示例 | 典型场景 |
|------|------|----------|----------|
| **simple** | 最简单 | GPT-4o-mini, Haiku | 简单问答、格式转换 |
| **standard** | 中等 | GPT-4o, Sonnet | 普通对话、写作 |
| **complex** | 复杂 | GPT-4.1, Opus | 代码生成、复杂推理 |
| **reasoning** | 推理 | o3, o4-mini | 数学证明、分析 |

## 三，安装与配置

### 3.1 安装（本地版本）

```bash
# 一键安装
openclaw plugins install manifest

# 重启网关
openclaw gateway restart

# 访问仪表板
# http://127.0.0.1:2099
```

### 3.2 Docker 安装

```bash
# 拉取镜像
docker pull manifestdotbuild/manifest

# 运行容器
docker run -d \
  --name manifest \
  -p 2099:2099 \
  -v manifest_data:/app/data \
  manifestdotbuild/manifest

# 访问仪表板
open http://127.0.0.1:2099
```

### 3.3 云版本

```bash
# 访问 https://app.manifest.build
# 按指引配置 API Keys
```

### 3.4 Provider 配置

```bash
# 配置 Provider API Keys
# 在仪表板 http://127.0.0.1:2099 中配置

# 或通过环境变量
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=AIza...
```

## 四，快速开始

### 4.1 基础使用

```python
# 无需修改代码！Manifest 自动拦截 manifest/auto 请求

# 简单问题 → 自动路由到便宜模型
response = openai.ChatCompletion.create(
    model='manifest/auto',  # 神奇的地方！
    messages=[{'role': 'user', 'content': '今天天气如何？'}]
)

# 复杂问题 → 自动路由到强大模型
response = openai.ChatCompletion.create(
    model='manifest/auto',
    messages=[{'role': 'user', 'content': '用Python写一个快速排序'}]
)
```

### 4.2 指定 Tier

```python
# 强制使用某个 tier
response = openai.ChatCompletion.create(
    model='manifest/simple',      # 最便宜的模型
    messages=[...]
)

response = openai.ChatCompletion.create(
    model='manifest/reasoning',  # 推理专用模型
    messages=[...]
)
```

### 4.3 指定模型

```python
# 直接指定某个模型（绕过路由）
response = openai.ChatCompletion.create(
    model='manifest/gpt-4.1',
    messages=[...]
)
```

## 五，核心功能

### 5.1 智能路由

```python
# Manifest 自动分析请求并路由到最佳模型
def smart_routing(request):
    """
    请求流程:
    1. 分析请求特征 (23维度)
    2. 计算总分
    3. 选择 Tier
    4. 在该 Tier 中选择最佳模型
    """
    score = analyzer.score(request)
    tier = selector.select_tier(score)
    model = router.select_model(tier, request)
    
    return model
```

### 5.2 自动故障转移

```python
# 当一个模型失败时，自动切换到下一个
@retry_on_failure(max_retries=3)
def call_with_fallback(request):
    providers = ['gpt-4.1', 'claude-sonnet-4.5', 'gemini-2.5-pro']
    
    for provider in providers:
        try:
            return call_model(provider, request)
        except Exception as e:
            logger.warning(f"{provider} failed: {e}")
            continue
    
    raise AllProvidersFailedError()
```

### 5.3 成本控制

```python
# 设置每月预算
manifest.set_budget(monthly_dollars=100)

# 设置每个模型的 Rate Limit
manifest.set_rate_limit('gpt-4.1', requests_per_minute=60)

# 查看消费
manifest.get_usage_stats()
```

### 5.4 仪表板

```
┌─────────────────────────────────────────────────────────────┐
│                    Manifest 仪表板                                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   📊 概览                                                       │
│   ├── 今日消费: $2.34 / $10 (预算)                              │
│   ├── 节省: 68% (vs 直接使用 GPT-4)                             │
│   └── 请求数: 1,234                                            │
│                                                               │
│   📈 模型分布                                                     │
│   ├── simple: 45% (Haiku, GPT-4o-mini)                         │
│   ├── standard: 35% (GPT-4o, Sonnet)                          │
│   ├── complex: 15% (GPT-4.1, Opus)                            │
│   └── reasoning: 5% (o3, o4-mini)                              │
│                                                               │
│   💰 成本节省                                                     │
│   ├── 直接使用 GPT-4: $100.00                                   │
│   ├── 使用 Manifest: $32.00                                     │
│   └── 节省: $68.00 (68%)                                       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 六，Provider 支持

### 6.1 支持的 Provider

| Provider | 模型数量 | 代表模型 |
|----------|----------|----------|
| **OpenAI** | 58+ | GPT-5.3, GPT-4.1, o3, o4-mini |
| **Anthropic** | 17+ | Claude Opus 4.6, Sonnet 4.5, Haiku 4.5 |
| **Google Gemini** | 22+ | Gemini 2.5 Pro, Gemini 3 Pro |
| **DeepSeek** | 13+ | DeepSeek Chat, DeepSeek Reasoner |
| **xAI** | 11+ | Grok 4, Grok 3, Grok 3-mini |
| **Mistral AI** | 29+ | Mistral Large, Codestral, Devstral |
| **Qwen (Alibaba)** | 45+ | Qwen3 235B, QWQ-32B |
| **MiniMax** | 8+ | MiniMax M2.5, M2, M1 |
| **Kimi (Moonshot)** | 5+ | Kimi K2, K2.5 |
| **Amazon Nova** | 8+ | Nova Pro, Nova Lite, Nova Micro |
| **Z.ai (Zhipu)** | 8+ | GLM-5, GLM-4.7, GLM-4.5 |
| **OpenRouter** | 300+ | 所有 Provider 的聚合 |
| **Ollama** | 本地模型 | Llama, Gemma, Mistral (本地) |

### 6.2 自定义 Provider

```python
# 添加自定义 Provider
manifest.add_provider(
    name='my-custom-provider',
    api_base='https://api.my-provider.com/v1',
    api_key='sk-...',
    models=['my-model-1', 'my-model-2']
)
```

## 七，与 OpenRouter 对比

| 维度 | **Manifest** | OpenRouter |
|------|-------------|------------|
| **架构** | 本地/私有 | 云端代理 |
| **成本** | 免费 | 5% 手续费 |
| **源码** | MIT 完全开源 | 专有 |
| **数据隐私** | 仅元数据或完全本地 | 提示和响应经过第三方 |
| **透明度** | 开放评分，可查看路由原因 | 无法查看路由决策 |

```python
# Manifest 优势
1. 免费 (无 5% 手续费)
2. 完全本地部署，数据不外泄
3. 开源透明，可审计
4. 支持本地模型 (Ollama)
```

## 八，API 参考

### 8.1 OpenAI 兼容 API

```python
import openai

# 使用 manifest/auto 自动路由
client = openai.OpenAI(
    api_key='dummy',  # Manifest 不需要真实 key
    base_url='http://127.0.0.1:2099/v1'
)

response = client.chat.completions.create(
    model='manifest/auto',
    messages=[{'role': 'user', 'content': 'Hello!'}]
)
```

### 8.2 Python SDK

```python
from manifest import Manifest

m = Manifest()

# 自动路由
result = m.generate('What is 2+2?')

# 指定 tier
result = m.generate('Write a Python quicksort', tier='complex')

# 指定模型
result = m.generate('Write a quicksort', model='manifest/gpt-4.1')
```

### 8.3 成本追踪

```python
# 获取使用统计
stats = m.get_stats()

print(f"Total cost: ${stats['cost']}")
print(f"Total tokens: {stats['tokens']}")
print(f"Savings vs GPT-4: {stats['savings']}%")

# 按模型查看
for model, data in stats['by_model'].items():
    print(f"{model}: ${data['cost']}, {data['tokens']} tokens")
```

## 九，高级配置

### 9.1 Tier 配置文件

```json
// manifest.config.json
{
  "tiers": {
    "simple": {
      "max_cost_per_1k": 0.001,
      "models": ["gpt-4o-mini", "haiku-4.5"]
    },
    "standard": {
      "max_cost_per_1k": 0.01,
      "models": ["gpt-4o", "sonnet-4.5"]
    },
    "complex": {
      "max_cost_per_1k": 0.1,
      "models": ["gpt-4.1", "opus-4.6"]
    },
    "reasoning": {
      "max_cost_per_1k": 1.0,
      "models": ["o3", "o4-mini"]
    }
  }
}
```

### 9.2 规则引擎

```python
# 强制某些请求使用特定模型
manifest.add_rule(
    condition=lambda req: 'code' in req.content.lower(),
    model='manifest/gpt-4.1'
)

manifest.add_rule(
    condition=lambda req: '数学' in req.content or '证明' in req.content,
    model='manifest/reasoning'
)
```

### 9.3 备份策略

```python
# 配置备份链
manifest.set_fallback_chain([
    'manifest/gpt-4.1',      # 首先尝试
    'manifest/claude-sonnet-4.5',  # 备份 1
    'manifest/gemini-2.5-pro',    # 备份 2
])
```

## 十，最佳实践

### 10.1 成本优化

```python
# ✅ 推荐：让 Manifest 自动选择
model = 'manifest/auto'

# ✅ 推荐：简单任务使用 simple tier
model = 'manifest/simple'  # 便宜 10x

# ❌ 不推荐：强制使用最贵模型
model = 'manifest/opus-4.6'  # 除非必要
```

### 10.2 性能优化

```python
# ✅ 推荐：批量请求
batch = [f"Item {i}" for i in range(100)]
results = m.generate_batch(batch)

# ✅ 推荐：使用流式输出
for token in m.generate_stream('Write a story'):
    print(token, end='', flush=True)
```

### 10.3 调试

```python
# 启用调试模式
m.set_debug(True)

# 查看路由决策
decision = m.trace('What is 2+2?')
print(f"Tier: {decision.tier}")
print(f"Model: {decision.model}")
print(f"Reason: {decision.reason}")
```

## 十一，FAQ

### 11.1 与直接使用 Provider 的区别

| 问题 | 回答 |
|------|------|
| Manifest 是否改变响应质量？ | 不会。Manifest 只是选择最合适的模型。 |
| 需要多个 Provider 的 API Key 吗？ | 是的，需要您想使用的所有 Provider 的 Key。 |
| 支持本地模型吗？ | 是，支持 Ollama。 |
| 如何保证隐私？ | 使用本地部署时，所有数据都在本地。 |

### 11.2 常见问题

**Q: 路由决策需要多长时间？**
A: 通常 < 2ms。

**Q: 如何处理模型失败？**
A: Manifest 自动切换到下一个可用模型。

**Q: 可以禁用某些模型吗？**
A: 可以，在配置文件中设置 `disabled_models`。

## 十二，总结

Manifest 是 **OpenClaw 的智能模型路由器**：

| 维度 | 说明 |
|------|------|
| 💰 **成本** | 节省最高 70%，无手续费 |
| ⚡ **速度** | 路由决策 < 2ms |
| 🔄 **可靠** | 自动故障转移 |
| 🔒 **隐私** | 本地部署可选 |
| 🌐 **灵活** | 300+ 模型支持 |

---

**🔗 相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/mnfst/manifest |
| 文档 | https://manifest.build/docs |
| 仪表板 | https://app.manifest.build |
| Discord | https://discord.gg/FepAked3W7 |

---

_🦞 本文由钳岳星君撰写，基于 Manifest (4.3k Stars)_
