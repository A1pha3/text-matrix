---
title: "Claude Cookbooks 深度拆解:Anthropic 官方的 47.8K stars 实战模式库"
slug: anthropics-claude-cookbooks-recipes-and-patterns-guide
date: 2026-07-12T02:58:14+08:00
lastmod: 2026-07-12T02:58:14+08:00
draft: false
categories: ["技术笔记"]
tags: ["claude", "anthropic", "prompt-engineering", "rag", "tool-use", "jupyter-notebook"]
description: "Claude Cookbooks 是 Anthropic 官方维护的实战代码库。本文按 capabilities / tool_use / multimodal 三大类拆解其模式,解释为何 47.8K stars 但真正的工程价值集中在 5-7 个核心 notebook。"
---

# Claude Cookbooks 深度拆解:Anthropic 官方的 47.8K stars 实战模式库

## 核心判断

Claude Cookbooks 不是「教程合集」,而是 Anthropic 官方维护的**实战模式库**——按 RAG、Tool Use、Multimodal、Sub-agents 等能力维度组织 Jupyter notebook,每个 notebook 是一段可独立运行、可拷贝到生产项目的代码片段。47.8K stars 的真正价值不在数量(约 60+ 个 notebook),而在质量:这是 Anthropic 工程师自己写、自己 review、自己用在生产环境的代码模板,比第三方博客的可信度高一个量级。

## 项目速览

- 仓库: [anthropics/claude-cookbooks](https://github.com/anthropics/claude-cookbooks) (旧名 anthropic-cookbook)
- Stars / 语言: 47.8K / Jupyter Notebook
- 定位: Claude API 实战代码库
- License: MIT
- 关联资源: [Claude API Fundamentals course](https://github.com/anthropics/courses/tree/master/anthropic_api_fundamentals)

## 为什么值得看

当你需要做以下事情时,Cookbooks 通常能给出可工作的最小例子:

- 接到一个需求「用 Claude 做 RAG」,不知道从哪里开始
- 想用 Tool Use 集成外部 API,不知道 JSON schema 怎么写
- 评估 Claude 在分类任务上的表现,需要 few-shot 模板

社区博客的代码往往缺依赖版本、有 hardcoded API key、或者已经过时半年以上。Cookbooks 由 Anthropic 工程师维护,每个 notebook 都通过内部 review,代码质量明显高于社区平均。

## 系统地图

```
anthropic-cookbook/
├── capabilities/        # 基础能力
│   ├── classification/          # 文本分类(prompt vs fine-tune)
│   ├── retrieval_augmented_generation/  # RAG 多变体
│   ├── summarization/           # 摘要(Map-Reduce, 增量)
│   └── ...
├── tool_use/            # 工具调用
│   ├── customer_service_agent.ipynb
│   ├── calculator_tool.ipynb
│   ├── sql_queries.ipynb
│   ├── extracting_structured_json.ipynb
│   └── ...
├── multimodal/          # 多模态
│   ├── vision.ipynb
│   └── best_practices_for_vision.ipynb
├── agents/              # Agent 编排
├── evaluation/          # 模型评估
├── misc/                # 杂项
└── README.md            # 索引
```

## 关键模式

### 1. RAG 三种粒度

`capabilities/retrieval_augmented_generation/` 下有三个核心 notebook,对应 RAG 的三种工程取舍:

| Notebook | 检索粒度 | 适用场景 |
|---------|---------|---------|
| `01_embeddings_and_similarity.ipynb` | 句子级(基于 embedding 余弦) | FAQ、文档搜索 |
| `02_rag_on_pdf_files.ipynb` | 文档块级(分块 + 重排) | 长文档问答 |
| `03_rag_with_citations.ipynb` | 引用级(给每段回答标 source) | 研究、法律、医疗 |

这三个粒度覆盖了 90% 的生产 RAG 场景。Anthropic 没有强推某一个,而是让工程师根据延迟预算和准确率需求选择。

### 2. Tool Use JSON Schema 写法

`tool_use/extracting_structured_json.ipynb` 给出 Anthropic 推荐的 JSON schema 写法,核心要点:

- 用 `description` 字段说明每个 property,而不是依赖 property 名称推断
- 用 `enum` 限制取值范围,减少模型幻觉
- `required` 显式列出,不要依赖默认
- 嵌套对象用 `$ref` / `definitions`,避免重复

例如:

```python
tools = [{
    "name": "get_weather",
    "description": "Get current weather for a US city",
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "US city name, e.g. 'San Francisco'"},
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"], "description": "Temperature unit"}
        },
        "required": ["city"]
    }
}]
```

### 3. Prompt caching 实战

Claude API 支持 prompt caching(2024 年发布),Cookbooks 有专门的 `prompt_caching.ipynb` 说明:

- 在 system prompt 顶部放静态上下文(如背景文档),可显著降低长 prompt 的成本和延迟
- cache hit 的费用约为 miss 的 10%
- 但 cache TTL 仅 5 分钟,适合会话级复用,不适合异步任务

### 4. Sub-agents 与并行工具调用

`agents/` 目录下展示了 Anthropic 推荐的多 agent 编排模式:

- 主 agent 负责路由(决定调哪个工具)
- 子 agent 负责执行(每个子 agent 一个职责)
- 用 `tool_choice: any` 强制模型必须调用工具
- 并行工具调用:一次 `messages.create` 返回多个 `tool_use` block,客户端并发执行

### 5. 评估方法

`evaluation/` 提供两种评估框架:

- `evaluation/` 目录:用 Claude 评估 Claude(LLM-as-judge),适合主观质量评估
- `classification/` 目录:用精确率/召回率评估,适合客观标签任务

## 实战建议

**第一次访问 Cookbook 该看哪 3 个 notebook**:

1. `capabilities/retrieval_augmented_generation/01_embeddings_and_similarity.ipynb` — 学会最基础的 RAG 写法
2. `tool_use/extracting_structured_json.ipynb` — Tool Use 是 Claude 的核心差异化能力
3. `misc/prompt_caching.ipynb` — 长 prompt 场景下必读,直接降本

**该跳过哪些**:

- 多模态 vision 相关的 notebook(2024 年初的版本,API 已多次升级,先看官方 docs)
- 已被合并到 `agents/` 的早期 notebook
- 教学性 notebook(如 `prompt_engineering_intro.ipynb`)—— 内容已分散到 Anthropic docs

## 适用边界

**适合用 Cookbooks 的场景**:

- 第一次集成 Claude API,需要可工作的最小例子。
- 评估 Claude 在某个具体任务上的可行性(分类、抽取、摘要)。
- 团队内部分享「Claude 怎么用」时的代码示范。

**不适合用 Cookbooks 的场景**:

- 生产级 RAG 系统——Cookbooks 是教学代码,生产需要自己加缓存、重试、错误处理、监控。
- 复杂的 agent 编排——Cookbooks 给出最小例子,但生产需要错误恢复、超时控制、并发限制。
- 想学 prompt engineering 基础——这部分已迁移到 [Anthropic courses](https://github.com/anthropics/courses),Cookbooks 不再重点维护。

## 上手示例

```bash
git clone https://github.com/anthropics/anthropic-cookbook.git
cd anthropic-cookbook
pip install -r requirements.txt

export ANTHROPIC_API_KEY=sk-ant-...

jupyter notebook capabilities/retrieval_augmented_generation/01_embeddings_and_similarity.ipynb
```

## 总结

Claude Cookbooks 的真正价值不是「数量多」,而是「质量稳」。47.8K stars 反映了开发者社区对 Anthropic 官方维护代码模板的信任,但实际工程价值集中在 5-7 个核心 notebook 上。建议第一次接入 Claude 时优先读 RAG、Tool Use、Prompt Caching 三个 notebook,其余按需查阅。

## 参考

- 仓库: <https://github.com/anthropics/anthropic-cookbook>
- Claude API 文档: <https://docs.claude.com>
- Claude API 课程: <https://github.com/anthropics/courses>