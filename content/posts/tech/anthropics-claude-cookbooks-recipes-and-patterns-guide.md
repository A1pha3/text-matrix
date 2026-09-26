---
title: "Claude Cookbooks 深度拆解：Anthropic 官方的 53K stars 实战模式库"
slug: anthropics-claude-cookbooks-recipes-and-patterns-guide
github_repo: "anthropics/claude-cookbooks"
source_key: "gh:anthropics/claude-cookbooks"
date: 2026-07-12T02:58:14+08:00
lastmod: 2026-09-24T00:00:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["Claude", "Anthropic", "Prompt Engineering", "RAG"]
description: "Claude Cookbooks 是 Anthropic 官方维护的实战代码库，全仓 101 个 notebook。本文按当前目录结构拆解 RAG、Tool Use、Prompt Caching、Agent 编排四条主线，并解释为什么它的工程价值集中在少数几个文件上。"
---

# Claude Cookbooks 深度拆解：Anthropic 官方的 53K stars 实战模式库

## 核心判断

Claude Cookbooks 是 Anthropic 官方维护的 Jupyter（交互式笔记本）实战代码库。它最值得信任的一点不是 notebook 数量多，而是官方维护这一属性：官方最新 API 的用法通常先落到这些 notebook，再扩散到第三方博客。也正因为是「最小可用示例」，它不是生产框架，照着抄会在错误处理、缓存、监控上缺一块。真正值得反复对照的，集中在 RAG（检索增强生成）、Tool Use（工具调用）、Prompt Caching（提示缓存）这一个子集上。

一个需要知道的背景：仓库在 2026 年经历过大改版。RAG、分类、摘要这些能力目录从「一组编号 notebook」合并成了「单文件 guide.ipynb」，早期的 `agents/`、`evaluation/` 目录也被拆并。网上大量旧文章描述的目录结构已经失效，读旧教程时先对照本文的快照。

## 项目速览

- 仓库：[anthropics/claude-cookbooks](https://github.com/anthropics/claude-cookbooks)（旧名 `anthropic-cookbook`，已改名，旧链接 301 跳转；注意 README 内部链接和 pyproject 包名仍用旧名，一样能访问）
- 规模：全仓 101 个 notebook（2026-09-24 核实），语言 Jupyter Notebook，要求 Python 3.11+
- 数据：52,954 stars / 6,357 forks（GitHub API，2026-09-24）；创建于 2023-08-15，最近推送 2026-09-23，活跃
- License：MIT
- 定位：Claude API 实战代码库，不是教程合集；入门课程另见 [Claude API Fundamentals](https://github.com/anthropics/courses/tree/master/anthropic_api_fundamentals)（README 官方推荐）

## 先分清三组边界

读之前先弄清这套库的切分方式，否则容易被目录绕晕。它有两条独立的轴，不要混在一起看：

- 按**能力**分：capabilities（分类、RAG、摘要等，每个能力一个目录）、tool_use（工具调用）、multimodal（图像与文档）。
- 按**使用方式**分：一部分是「讲原理的教学示例」，一部分是「围绕某个 SDK 或集成的可抄工程」。前者看 capabilities 就够，后者的代表是 `claude_agent_sdk/` 和 `third_party/`。

另外要区分「库的目录」和「API 的能力」：同一个能力会散在多处，比如 RAG 同时出现在 `capabilities/retrieval_augmented_generation/` 和 `third_party/Pinecone/`。理解这点才能快速定位，而不是把每个目录当成一个独立话题。

## 系统地图

```text
claude-cookbooks/
├── capabilities/        # 基础能力，每个能力一个目录
│   ├── retrieval_augmented_generation/   # RAG（guide.ipynb 单文件教学）
│   ├── classification/、summarization/   # 同为 guide.ipynb 模式
│   └── content_moderation/、text_to_sql/、knowledge_graph/、contextual-embeddings/
├── tool_use/            # 工具调用（结构化抽取、并行调用、Pydantic、memory）
├── multimodal/          # 图像与文档（vision 入门与最佳实践、图表、转录）
├── patterns/agents/     # agent 工作流模式（orchestrator-workers、evaluator-optimizer…）
├── claude_agent_sdk/    # 用 Claude Agent SDK 从零到部署建 agent（00–08 系列）
├── managed_agents/      # Managed Agents：Anthropic 托管的持久化 agent 运行时
├── misc/                # 杂项（prompt caching、citations、批处理、SQL、JSON mode…）
├── evals/、tool_evaluation/  # 专项评估（agentic search、工具调用评估）
├── cost_optimization/、observability/、extended_thinking/、finetuning/、coding/、skills/
├── third_party/         # Pinecone、VoyageAI、MongoDB、LlamaIndex 等集成
└── README.md            # 索引（部分链接仍指旧仓库名，会跳转）
```

能力目录现在遵循统一模式：`README.md` + `guide.ipynb` + `data/` + `evaluation/`。要学一个能力，进目录跑那一个 notebook 就行，不用再在编号文件之间找顺序。

## 关键模式

### RAG：一个 notebook 里的三级阶梯

`capabilities/retrieval_augmented_generation/guide.ipynb` 把 RAG 的工程递进压缩成三级，对应三种成本与效果的取舍：

| 阶段 | 做法 | 代价 |
|------|------|------|
| Level 1 | 基础向量 RAG：embedding 检索 + 生成 | 实现最简，命中靠语义相似度 |
| Level 2 | 摘要增强检索：先让 Claude 给文档块生成摘要，用摘要建索引 | 多一轮 LLM 调用，换取更准的召回 |
| Level 3 | 用 Claude 做重排（re-ranking）：先粗召回，再让模型精排 | 准确率最高，成本与延迟也最高 |

这个 notebook 的特别之处是评估内建：每升一级，都用同一组检索指标（精确率 Precision、召回率 Recall、F1、排序质量 MRR@k）和端到端准确率对比一次，最后还接了 Promptfoo 做自动化评估。读它不只是学 RAG 写法，更是学「每做一次优化怎么证明有效」。选级时按延迟预算与准确率需求来：FAQ 场景 Level 1 就够，直接上 Level 3 只是给自己加成本。

需要带引用来源的答案（研究、法律场景），看 `misc/using_citations.ipynb`，它演示 Citations 功能让答案逐段标注来源。

### Tool Use：把约束写进 schema，而不是靠提示词求它

`tool_use/extracting_structured_json.ipynb` 讲怎么让模型稳定输出结构化数据，五个示例覆盖文章摘要、命名实体识别、情感分析、分类和「schema 之外的字段怎么办」。它的核心写法有两条：

- 每个 property 都写 `description`，不靠字段名猜含义。notebook 里连 `coherence` 这样的整数评分都标注了「0-100（含）」。
- `required` 显式列出必填字段，不依赖默认值。

schema 越严，程序侧越省事：参数缺失、类型错误在解析层就能拦下，不用拿字符串碰运气。enum（枚举锁定取值）同样是 API 层支持的手段，适合取值可穷举的字段；仓库另有 `tool_use/tool_use_with_pydantic.ipynb`，展示用 Pydantic 模型定义 schema 再自动校验的路线。

下面是 notebook 里 Example 1 的工具定义，原样照录：

```python
tools = [
    {
        "name": "print_summary",
        "description": "Prints a summary of the article.",
        "input_schema": {
            "type": "object",
            "properties": {
                "author": {"type": "string", "description": "Name of the article author"},
                "topics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": 'Array of topics, e.g. ["tech", "politics"]. Should be as specific as possible, and can overlap.',
                },
                "summary": {
                    "type": "string",
                    "description": "Summary of the article. One or two paragraphs max.",
                },
                "coherence": {
                    "type": "integer",
                    "description": "Coherence of the article's key points, 0-100 (inclusive)",
                },
                "persuasion": {
                    "type": "number",
                    "description": "Article's persuasion score, 0.0-1.0 (inclusive)",
                },
            },
            "required": ["author", "topics", "summary", "coherence", "persuasion", "counterpoint"],
        },
    }
]
```

### Prompt Caching：先看新的自动模式

`misc/prompt_caching.ipynb` 现在从自动缓存讲起：请求顶层加一个 `cache_control` 参数，系统自动管理缓存断点，断点会随对话增长自动前移，不用手动挪标记。需要精细控制时再用显式断点——把 `cache_control` 放在具体内容块上，还可以给不同块配不同 TTL。

经济账用官方文档的口径算：缓存读取是基础输入价格的 0.1 倍（写入一次 5 分钟档是 1.25 倍），TTL 默认 5 分钟，可付费延长到 1 小时。notebook 自己的结论是重复任务下「延迟降一半以上、成本省最多九成」。所以它只适合会话级复用：把稳定的长前缀（背景文档、系统说明）送进缓存，别缓存每次都变的内容；「过几小时再取」的异步任务，5 分钟 TTL 等不起，要么上 1 小时档先算笔账，要么放弃缓存。同目录还有 `speculative_prompt_caching.ipynb` 讲预取式缓存的进阶玩法。

### Agent 编排：三层递进，别一步登天

编排内容现在分散在三处，难度递进：

1. `patterns/agents/` 讲工作流模式本身：basic_workflows、orchestrator_workers（主 agent 拆任务、子 agent 执行）、evaluator_optimizer（生成器-评审器循环），外加异步编排与延迟优化两个专题。这五个 notebook 是 Anthropic「Building Effective Agents」思路的代码版，先把这里的模式吃透。
2. `claude_agent_sdk/` 用 Claude Agent SDK 把模式落到工程：从 00 号「一行代码研究 agent」开始，到 chief-of-staff、可观测性、漏洞检测 agent，直到 08 号动态工作流和托管部署，是一条从原型到上线的完整路径。
3. `managed_agents/` 是 Anthropic 托管运行时的示例：定义一次 agent 和沙箱环境，会话跨轮次持久化文件、工具状态和对话，适合不想自己维护基础设施的团队。

并行工具调用的机制值得单独理解：一次 `messages.create` 可以返回多个 `tool_use` block，客户端并发执行后把结果一起回传，省的是来回对话的次数而不是模型推理时间。`tool_use/parallel_tools.ipynb` 专门演示这件事。

### 评估：指标内建在能力目录里

改版后评估不再是独立的教学目录，而是长进了各个能力目录：RAG、分类、摘要的 guide.ipynb 都带同一套评估框架，检索类任务看精确率、召回率、F1 和 MRR，分类任务看精确率与召回率，端到端质量交给 Promptfoo 自动跑。仓库级还有三处专项：`misc/building_evals.ipynb` 教用 Claude 自动化评估流程，`tool_evaluation/` 评估工具调用质量，`evals/agentic_search/` 评估搜索型 agent。

看这些数字前先明确三个问题，否则没有意义：它在测什么指标？数字变化更可能反映召回、提示词还是分块策略哪一环？从数字里不能推出什么——分数高不等于答案可信任，边界样本仍需人工抽检。

## 一个任务如何流过这些模式

以「客服 agent 查询订单状态」为例（这正是 `tool_use/customer_service_agent.ipynb` 的场景）：

1. 用户问题进来，先判断意图：查订单，还是转人工。分类能力对应 `capabilities/classification/guide.ipynb`。
2. 确认要查数据后走工具调用：notebook 定义了 `get_customer_info`、`get_order_details`、`cancel_order` 三个工具，`order_id` 这类参数显式列入 required，含义写进 description，模型据此生成标准化调用。
3. 工具返回订单 JSON，agent 组织成回答；商品政策等背景文档放进缓存前缀，多轮对话直接吃缓存折扣。
4. 如果用户问的是「这个订单适用的退货条款是什么」，切到 Citations：检索知识库片段，让答案逐段带来源。

一个任务把分类、工具调用、缓存、Citations 串了一遍。阅读时不妨按「某一步卡住时该查哪个 notebook」来记忆，而不是按目录顺序扫读。

## 上手示例

```bash
git clone https://github.com/anthropics/claude-cookbooks.git
cd claude-cookbooks
```

按 CONTRIBUTING.md 的口径，仓库用 `uv` 管理依赖，要求 Python 3.11+：

```bash
uv sync --all-extras
cp .env.example .env     # 在 .env 填入 ANTHROPIC_API_KEY
```

不想用 uv 就 `pip install -e ".[dev]"`。之后用 Jupyter 打开目标 notebook 逐格执行，notebook 自带示例数据：

```bash
jupyter lab capabilities/retrieval_augmented_generation/guide.ipynb
```

两个省心细节：根目录 `.env.example` 默认开了 `TEST_MODE=true`、`MAX_TOKENS=10`，跑通流程时几乎不花钱，正式实验再关掉；`claude_agent_sdk/` 子目录有独立依赖，README 要求在子目录里再跑一次 `uv sync` 并把 venv 注册成 Jupyter kernel。

## 推荐阅读顺序与采用建议

第一次进 Cookbooks，按这个顺序看，每步对应一个高频问题：

1. `capabilities/retrieval_augmented_generation/guide.ipynb` —— 学最基础的检索问答，顺便学会用指标验证每步优化。
2. `tool_use/extracting_structured_json.ipynb` —— Tool Use 是 Claude 的差异化能力，先把 schema 约束写法练稳。
3. `misc/prompt_caching.ipynb` —— 长 prompt 场景必读，直接降本。
4. 要做 agent 再往下走：`patterns/agents/` 模式 → `claude_agent_sdk/` 工程，按需再看 `managed_agents/`。

采用判断：小团队做原型、验证 Claude 在某个具体任务上的可行性，Cookbooks 是低成本起点；团队要统一「Claude 怎么用」的示范，可以照它写内训材料。反之，正式生产系统别把它当基座——它的定位是示例，不带监控、重试、成本治理这些运行时能力。

## 适用边界

**适合**：

- 第一次集成 Claude API，要一个可工作的最小例子。
- 评估 Claude 在分类、抽取、摘要等具体任务上的可行性。
- 团队内部分享「Claude 怎么用」时的代码示范。

**不适合**：

- 生产级 RAG——教学代码缺缓存、重试、错误处理、监控，这些要自己补。
- 复杂 agent 编排——Cookbooks 给最小例子，生产要额外处理错误恢复、超时、并发限制。
- 学 prompt engineering 基础——原来的 `prompt_engineering_intro.ipynb` 已从仓库移除，这部分内容以官方 docs 和 courses 为准。

对旧教程里出现、现已失效的路径（编号版 RAG notebook、`agents/`、`evaluation/` 目录）放宽预期：它们已被合并或拆并，别按旧文章的路径找文件。

## 常见问题与排查

- **API key 没生效**：确认 `.env` 里的 `ANTHROPIC_API_KEY` 已写入，且没被提交到 git。notebook 从环境变量读 key，子目录（如 `tool_use/`、`claude_agent_sdk/`）各有自己的 `.env.example`。
- **依赖装不上 / 版本冲突**：仓库要求 Python 3.11+，优先 `uv sync --all-extras`；网上旧文章写 `pip install -r requirements.txt` 的，只有个别子目录（如 `tool_use/`）还适用，根目录按 CONTRIBUTING.md 走。
- **跑出来的行为过时**：notebook 针对当时版本写的，部分调用了已变化的接口；报错先查该目录 README 和 issue，再决定是修一行还是换 notebook。这也是优先选 guide.ipynb 单文件教学的原因——它们随改版更新得最勤。
- **不确定该用哪个模式**：回到「先分清三组边界」，先确认要的是能力、SDK 工程还是第三方集成，再定位目录，别从目录反推需求。

## 维护：如何判断它是否还新鲜

Cookbooks 是活跃仓库，接口、目录、推荐依赖会变。判断值不值得照抄，三个检查就够：看仓库最近提交是否在这个季度；看 notebook 用的模型与 API 版本和官方 docs 是否对得上；看能力目录是否还是「README + guide.ipynb + evaluation」这一模式——再改版时这条会最先失效。本文的目录结构是 2026-09-24 的快照，读的时候以仓库当前 README 为准。

## 总结

Claude Cookbooks 的价值在「官方维护」这一属性，而不在 notebook 数量。它真正给的，是「官方当前怎么用 Claude」的一组最小可信示例，集中在 RAG、Tool Use、Prompt Caching 三个能力上；agent 编排则按 patterns → Agent SDK → Managed Agents 三层递进。第一次接入按推荐顺序读，先用起来，再把生产要补的边界补上。

## 参考

- 仓库：<https://github.com/anthropics/claude-cookbooks>
- Claude API 文档（含 Prompt Caching 定价与 TTL）：<https://platform.claude.com/docs/en/build-with-claude/prompt-caching>
- Claude API 课程：<https://github.com/anthropics/courses>
