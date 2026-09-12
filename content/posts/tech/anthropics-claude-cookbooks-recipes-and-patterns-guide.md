---
title: "Claude Cookbooks 深度拆解:Anthropic 官方的 47.8K stars 实战模式库"
slug: anthropics-claude-cookbooks-recipes-and-patterns-guide
github_repo: "anthropics/claude-cookbooks"
source_key: "gh:anthropics/claude-cookbooks"
date: 2026-07-12T02:58:14+08:00
lastmod: 2026-07-12T02:58:14+08:00
draft: false
categories: ["技术笔记"]
tags: ["Claude", "Anthropic", "Prompt Engineering", "RAG"]
description: "Claude Cookbooks 是 Anthropic 官方维护的实战代码库。本文按 capabilities / tool_use / multimodal 三大类拆解其模式,解释为何 47.8K stars 但真正的工程价值集中在 5-7 个核心 notebook。"
---

# Claude Cookbooks 深度拆解:Anthropic 官方的 47.8K stars 实战模式库

## 核心判断

Claude Cookbooks 是 Anthropic 官方维护的 Jupyter（交互式笔记本）实战代码库，按 RAG（检索增强生成）、Tool Use（工具调用）、多模态（multimodal）等能力维度组织。它最值得信任的一点不是 notebook 数量多，而是官方维护这一属性：官方最新 API 的用法通常会先落到这些 notebook，再扩散到第三方博客。也正因为是「最小可用示例」，它不是一套生产框架，照着抄会在错误处理、缓存、监控上缺一块。真正该反复对照的，集中在 RAG、Tool Use、Prompt Caching 这一个子集上。

## 项目速览

- 仓库：[anthropics/claude-cookbooks](https://github.com/anthropics/claude-cookbooks)（旧名 `anthropic-cookbook`，已改名，旧链接会跳转）
- 形态 / 规模：Jupyter Notebook，数十个 notebook，数量随仓库持续增长
- 定位：Claude API 实战代码库，不是教程合集
- License：MIT
- 关联：[Claude API Fundamentals course](https://github.com/anthropics/courses/tree/master/anthropic_api_fundamentals)

## 先分清三组边界

读之前先弄清这套库的切分方式，否则容易被目录绕晕。它有两条独立的轴，不要混在一起看：

- 按**能力**分：capabilities（分类、RAG、摘要）、tool_use（工具调用）、multimodal（图像与文档）。
- 按**使用方式**分：一部分是「拿来就能跑的集成」，另一部分是「讲原理的教学示例」。前者适合直接抄，后者内容往往已流入 Anthropic 官方文档。

另外要区分「库的目录」和「API 的能力」：同一个能力（比如 RAG）会散在多个目录（capabilities、third_party），理解这点才能快速定位，而不是把每个目录当成一个独立话题。

## 系统地图

```text
claude-cookbooks/
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
├── misc/                # 杂项(prompt caching 等)
└── README.md            # 索引
```

## 关键模式

### RAG 的三种粒度

`capabilities/retrieval_augmented_generation/` 下的三个 notebook，对应 RAG 的三种工程取舍：

| Notebook | 检索粒度 | 适用场景 | 代价 |
|---------|---------|---------|------|
| `01_embeddings_and_similarity.ipynb` | 句子级（基于 embedding（嵌入向量）余弦） | FAQ、文档搜索 | 实现最简，但命中靠语义相似度，精确引用能力弱 |
| `02_rag_on_pdf_files.ipynb` | 文档块级（分块 + 重排） | 长文档问答 | 需要分块与重排，控制块大小和重叠 |
| `03_rag_with_citations.ipynb` | 引用级（给每段答案标 source） | 研究、法律、医疗 | 准确度最高，成本与返回体积也最大 |

三个粒度不必一次到最细，按「延迟预算 vs 准确率需求」选即可。FAQ 用句子级就够用，上 `03` 只是给自己加成本。

### Tool Use 的 JSON Schema 约束

`tool_use/extracting_structured_json.ipynb` 讲的是让模型稳定输出结构化数据的写法，核心不是语法，而是「把约束写进 schema，而不是靠提示词求它」：

- 用 `description` 字段说明每个 property，不靠 property 名称猜含义。
- 用 `enum` 锁死取值范围，模型幻觉空间随之缩小。
- `required` 显式列出，不依赖默认值。
- 嵌套对象用 `$ref` / `definitions` 复用，避免重复定义。

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

schema 越严，程序侧越省事：参数错、类型错在解析层就能拦下，不用拿字符串去碰运气。

### Prompt Caching：成本与延迟的取舍

Claude API 支持 prompt caching（2024 年发布），`prompt_caching.ipynb` 说明用法。要点是别缓存「动态内容」，只缓存「每次都一样的静态前缀」：

- 把背景文档、系统说明放在 system prompt 顶部，作为稳定的前缀。
- cache hit 的费用约为 miss 的一成，长 prompt 场景下直接降本。
- 但缓存 TTL 短（分钟级），它适合会话级复用，不适合「过几小时再取」的异步任务。

判断是否值得开缓存，先看 prompt 的前缀是否够长、够稳定；前缀短则收益有限。

### Sub-agents 与并行工具调用

`agents/` 目录展示多 agent 编排的推荐分法——主 agent 管路由，子 agent 管执行，每个子 agent 只做一件事。这样职责清晰，也方便给每个子 agent 配置不同的模型或提示词。

并行工具调用的机制值得单独理解：一次 `messages.create` 可以返回多个 `tool_use` block，客户端并发执行后再把结果一起回传。它省的不是模型推理时间，而是「来回对话」的次数。

### 评估：先分清在测什么

`evaluation/` 同时提供两类评估，别混用：

- `evaluation/`：用 Claude 评 Claude（LLM-as-judge），适合「主观质量」的排序型任务。
- `classification/`：用精确率 / 召回率，适合「标签对不对」的客观任务。

看这两个目录时先明确三个问题，否则数字没有意义：它在测什么指标？数字变化更可能反映召回、还是提示词、还是分块策略哪一环？从这些数字里不能推出哪些结论——比如分数字高不等于答案可信任，还需人工抽检边界样本。

## 一个任务如何流过这些模式

把上面几个模式串起来看，更清楚每个 notebook 卡在哪一环。以「客服 agent 查询订单状态」为例：

1. 用户问题进来，主 agent 先用 `classification` 判断意图（是查订单，还是转人工）。
2. 判断要查数据后，走 `tool_use`：用 JSON schema 约束参数（`order_id` 必填、格式枚举），模型据此生成一次标准化的工具调用。
3. 工具执行返回订单 JSON，agent 再把它组织成回答。
4. 如果问题是「这个订单里的政策条款是什么」，则切到 `RAG with citations`：检索知识库片段，让答案带上来源。

一个任务把 classification、tool_use、RAG 三套模式顺序用上，这正是 Cookbooks 各 notebook 组合起来的方式。阅读时不妨按「某一步卡住时该查哪个 notebook」来记忆，而不是按目录顺序扫读。

## 上手示例

```bash
git clone https://github.com/anthropics/claude-cookbooks.git
cd claude-cookbooks
```

仓库现推荐用 `uv` 管理依赖：

```bash
uv sync --all-extras
cp .env.example .env     # 在 .env 填入 ANTHROPIC_API_KEY
```

之后用 Jupyter 打开目标 notebook，从上到下逐格执行即可——notebook 自带示例数据，不需要额外准备：

```bash
jupyter lab capabilities/retrieval_augmented_generation/01_embeddings_and_similarity.ipynb
```

历史版本依赖 `pip install -r requirements.txt`，旧文章里常见，按当前 README 走 `uv` 即可。

## 推荐阅读顺序与采用建议

第一次进 Cookbooks，按这个顺序看，每步都对应一个高频问题：

1. `capabilities/retrieval_augmented_generation/` 里的 RAG 入门 notebook —— 学会最基础的检索问答写法。
2. `tool_use/extracting_structured_json.ipynb` —— Tool Use 是 Claude 的差异化能力，先把 JSON 约束写法练稳。
3. `misc/prompt_caching.ipynb` —— 长 prompt 场景必读，直接降本。

需要做决策时，可以这样判断是否采用：小团队做原型、验证 Claude 在某个具体任务上的可行性，Cookbooks 是低成本起点；团队里要统一「Claude 怎么用」的示范，也可以照它写内训材料。反之，如果是正式生产系统的依赖，别把它当基座——它的定位是示例，不是带监控、重试、成本治理的运行时。

## 适用边界

**适合**：

- 第一次集成 Claude API，要一个可工作的最小例子。
- 评估 Claude 在分类、抽取、摘要等具体任务上的可行性。
- 团队内部分享「Claude 怎么用」时的代码示范。

**不适合**：

- 生产级 RAG——教学代码缺缓存、重试、错误处理、监控，这些要自己补。
- 复杂 agent 编排——Cookbooks 给最小例子，生产要额外处理错误恢复、超时、并发限制。
- 学 prompt engineering 基础——这部分已迁移到 [Anthropic courses](https://github.com/anthropics/courses)，Cookbooks 不再重点维护。

对已过时的内容放宽预期：多模态 vision 相关 notebook、并入 `agents/` 的早期 notebook、`prompt_engineering_intro.ipynb` 这类教学示例，晚点再看甚至跳过，都以官方 docs 为准。

## 常见问题与排查

- **API key 没生效**：确认 `.env` 里的 `ANTHROPIC_API_KEY` 已写入，且没被提交到 git。notebook 通常从环境变量读 key。
- **依赖装不上 / 版本冲突**：优先按仓库当前推荐的 `uv sync --all-extras`，而不是照博客里的 `pip install -r requirements.txt`。老 notebook 可能与最新 SDK 不兼容。
- **跑出来的行为过时**：notebook 是针对当时版本写的，部分调用了旧的 beta 接口或已退休的功能；报错先查该目录的 README 和 issue，再决定是修一行还是换 notebook。
- **不确定该用哪个模式**：回到「先分清三组边界」，先确认你要的是能力、集成还是教学示例，再定位目录，别从目录反推需求。

## 维护：如何判断它是否还新鲜

Cookbooks 是活跃仓库，接口、目录、推荐依赖会变。判断值不值得照抄，三个检查就够了：看仓库最近提交是否在这个季度；看 notebook 用的 API 版本与官方 docs 是否对得上；看某个 notebook 的 README 里是否标注了 deprecated。本文提到的目录结构是一个时点快照，读的时候以仓库当前 README 为准。

## 总结

Claude Cookbooks 的价值在「官方维护」这一属性，而不在 notebook 数量。它真正给的，是「官方当前怎么用 Claude」的一组最小可信示例，尤其集中在 RAG、Tool Use、Prompt Caching 上。第一次接入时，按这三个顺序读，先用起来，再把生产要补的边界补上。

## 参考

- 仓库：<https://github.com/anthropics/claude-cookbooks>
- Claude API 文档：<https://docs.claude.com>
- Claude API 课程：<https://github.com/anthropics/courses>