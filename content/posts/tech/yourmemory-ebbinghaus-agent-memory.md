---
title: "YourMemory 解析：把遗忘曲线做成机制的 Agent 记忆系统"
date: "2026-04-27T08:17:54+08:00"
lastmod: "2026-09-30T00:00:00+08:00"
slug: "yourmemory-ebbinghaus-agent-memory"
github_repo: "sachitrafa/YourMemory"
source_key: "gh:sachitrafa/YourMemory"
description: "YourMemory 把艾宾浩斯遗忘曲线写成按类别分 λ 的衰减公式，配合 BM25+向量+实体图两轮检索与 N→1 记忆合并，LoCoMo-10 Recall@5 59%（Zep Cloud 28%），LongMemEval-S Recall@5 89.4%。默认 DuckDB 本地零设置，哈希链审计与数据导出端点内置，适合需要跨会话记忆且数据不出本机的 AI 开发工作流。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "MCP", "记忆系统"]
---


## 📋 目录

- [先看判断](#先看判断)
- [记忆的生命周期：一张地图](#记忆的生命周期：一张地图)
- [核心问题：会囤积的记忆不是好记忆](#核心问题：会囤积的记忆不是好记忆)
- [遗忘曲线机制：艾宾浩斯方程的工程实现](#遗忘曲线机制：艾宾浩斯方程的工程实现)
- [混合检索：两轮召回与排序公式](#混合检索：两轮召回与排序公式)
- [合并：相关记忆压缩成一条](#合并：相关记忆压缩成一条)
- [一条记忆的完整流转](#一条记忆的完整流转)
- [存储架构：默认本地，按需扩展](#存储架构：默认本地，按需扩展)
- [快速开始：注册、配置、可选本地抽取](#快速开始：注册、配置、可选本地抽取)
- [MCP 工具与无 LLM 问答](#mcp-工具与无-llm-问答)
- [多 Agent 与团队记忆池](#多-agent-与团队记忆池)
- [审计链与数据权利](#审计链与数据权利)
- [性能基准：三套公开基准与两笔效率账](#性能基准：三套公开基准与两笔效率账)
- [适用场景与采用建议](#适用场景与采用建议)

---

## 先看判断

多数"Agent 记忆"产品解决的是存不下：把对话塞进向量库，检索时捞回来。YourMemory（sachitrafa/YourMemory）处理的是另一头——存下之后怎么办：不重要的记忆该多快淡出，相近的记忆该不该合并，召回时靠什么排序。它把艾宾浩斯遗忘曲线写成按类别分 λ 的衰减公式，配上 BM25 + 向量 + 实体图的两轮检索，在 LoCoMo-10 基准上拿到 59% Recall@5，是对照系统 Zep Cloud（28%）的两倍多。

| 快速信息 | |
|---------|------|
| 仓库 | [sachitrafa/YourMemory](https://github.com/sachitrafa/YourMemory) |
| Stars | 270（@2026-09-30） |
| 语言 | Python（3.11–3.14） |
| 许可证 | CC BY-NC 4.0（个人/教育/学术/开源免费，商用需书面协议） |
| 最新版本 | 1.4.87（PyPI） |
| 官网 | [yourmemoryai.xyz](https://yourmemoryai.xyz/) |

---

## 记忆的生命周期：一张地图

YourMemory 把记忆当成一个有生老病死的系统，而不是一张只增不减的表。全部机制围绕一条管线展开：

| 环节 | 机制 | 关键参数 |
|------|------|---------|
| 抽取 | 内置启发式；可选 Ollama 本地模型（qwen2.5:7b）或 Anthropic 抽取 | setup 时选择 |
| 去重 | 主语感知：按句子主语的嵌入判断是否同一实体 | spaCy |
| 存储 | 向量嵌入 + spaCy NER 抽实体建图边 | DuckDB 默认 |
| 衰减 | 艾宾浩斯指数衰减，按类别分 λ | strategy 0.10 → failure 0.35 |
| 合并 | 相关记忆攒够后压缩成一条摘要，原件归档 | 事件驱动 |
| 检索 | 第一轮 BM25+向量混合，第二轮图扩展 | `0.4×BM25 + 0.6×余弦` |
| 修剪 | 强度低于 0.05 每日清理；图邻居仍强则豁免 | APScheduler |

下面逐段拆开。

---

## 核心问题：会囤积的记忆不是好记忆

每次新会话，AI 助手都把你当陌生人：偏好重新问一遍，技术栈重新学一遍。现成的补救多数是"给金鱼换个大碗"——向量库照单全收，近似重复的记忆越攒越多，直到检索被噪音淹没。

YourMemory 的做法是把"忘"写进系统：记忆按类别（strategy / fact / assumption / failure）分配不同的衰减速率，重要的衰减慢，无关的自然淡出。官方的说法是"memory that works like a brain, not a database"——这句话可以争论，但衰减、合并、修剪这三件事它确实都做了实现，而不只是口号。

---

## 遗忘曲线机制：艾宾浩斯方程的工程实现

核心公式位于 `src/services/decay.py`：

```text
effective_λ = base_λ × (1 − importance × 0.8)
strength    = min(importance × e^(−effective_λ × active_days) × (1 + recall_count × 0.2), 1.0)
```

- **base_λ**：类别基础衰减率，由 `DECAY_RATES` 字典定义
- **importance**：记忆重要性（0–1），越高衰减越慢
- **active_days**：只数用户活跃的天数——记录在 `user_activity` 表里，休了一周假，记忆不会在假期里衰减
- **recall_count**：被召回次数，每次召回强度加成 20%

四种类别对应不同的衰减速度：

| 类别 | 衰减率 λ | 存活期* | 典型用途 |
|------|:-------:|:------:|---------|
| **strategy** | 0.10 | ~38 天 | 验证过的成功模式、架构决策 |
| **fact** | 0.16 | ~24 天 | 用户偏好、身份信息 |
| **assumption** | 0.20 | ~19 天 | 推断出的上下文 |
| **failure** | 0.35 | ~11 天 | 报错、走错的路、环境问题 |

\* 存活期是源码注释给出的口径：importance=0.5、从不被召回、修剪阈值 0.05 条件下的近似天数。

这组参数的直觉很朴素：三个月前的限速报错大概率已经失效，不该继续占用检索结果；而跑通过的工作流值得留得久一些。低于强度阈值 `0.05` 的记忆由 APScheduler 驱动的每日任务清理。

修剪有一条例外：**chain-aware pruning**。一条已经衰减的记忆，只要图上还有任何一个邻居的强度在阈值之上，就保留不动——它可能是某条活跃记忆的支撑上下文，删了会把别人带塌（`graph_store.py` 的 `chain_safe_to_prune()`）。

---

## 混合检索：两轮召回与排序公式

### 第一轮：BM25 + 向量

单纯向量相似度会漏掉"词汇不同但语义相关"的记忆，单纯关键词匹配又扛不住换说法的查询。YourMemory 第一轮同时跑两路，按固定权重合成：

```text
hybrid_score = 0.4 × bm25_norm + 0.6 × cosine_similarity
```

### 第二轮：图扩展

以第一轮结果为种子做 BFS 图遍历，把"你忘了问、但相关"的记忆捞回来。图边有两种：

- **语义边**：存储时与新记忆余弦相似度 ≥ 0.4 的既有记忆相连，边权 = 相似度 × 动词权重（SVO 抽取）
- **实体边**：spaCy NER 在存储时抽取命名实体，共享同一实体的记忆互连，边权固定 0.45

实体边是 HotpotQA 成绩的关键：多跳问题里，第二条事实往往在讲第一条事实的"答案"，与原始问题的嵌入相似度很低，纯向量检索到第一条就停了——实体边却能从第一条直接走到第二条（数据见基准一节）。

### 排序不用记忆强度

一个容易想当然的设计：把衰减强度乘进排序，"频繁召回的记忆排名靠前"。YourMemory 明确不这么做。官方基准文档给出的理由：相似度乘强度，会压低那些"旧但仍然有效"的记忆，让它们排在新近但无关的记忆之下。所以衰减强度只管两件事——每日修剪（阈值 0.05）和图节点评分；排序本身只看 BM25 与余弦相似度。

召回强化也有门槛：只有相似度 ≥ 0.75 的召回才给 `recall_count` 加一，顺带的查询不会把记忆越点越硬。

---

## 合并：相关记忆压缩成一条

衰减只解决"旧的该走"，解决不了"多的该并"。Consolidation 机制监控相关记忆的聚集：同主题的事实攒够之后，触发一次聚类加 LLM 摘要，把 N 条压成 1 条干净的总结，原件移入归档——不删除，之后可以从 `GET /users/{id}/archive` 找回。

官方给的生产实例：某个真实存储里，444 条记忆合并成 16 条摘要，同样的知识，检索噪音少一个量级。触发是事件驱动的（相关记忆堆积到阈值），不是每晚无脑跑的定时任务。

与衰减合在一起，这套系统对"记忆规模"的回答是三条腿：该忘的衰减掉，该并的合并掉，剩下的一条都不少。

---

## 一条记忆的完整流转

把前面的机制串成一个具体场景——告诉 Agent 一个偏好之后发生了什么。

**存储**：`store_memory("Alex prefers tabs over spaces in Python", importance=0.9, category="fact", context_paths=["/projects/backend"])`。spaCy 切出主语 "Alex" 做去重判断：主语相同的是同一实体的记忆，将来 "Alex hates semicolons" 入库时有合并的基础；而 "YourMemory uses DuckDB" 这类主语不同的记忆不会被错误合并进来。NER 抽出命名实体建好图边，向量连同路径标签写入 DuckDB。

**衰减**：importance=0.9 让衰减率降到 0.16 × (1 − 0.9 × 0.8) ≈ 0.045——不到默认 fact 记忆的三分之一，这条偏好能活很久。此后的每个活跃日，每日任务按这个速率重算强度；只要图上邻居还有强的，即使它自己冷却到阈值以下也不会被剪。

**合并**：若接下来 "Alex hates semicolons"、"Alex formats SQL in lowercase" 陆续入库，同主题记忆攒够后触发一次事件驱动的合并，三条压成一条 "Alex 的代码风格偏好" 摘要，原件归档可找回。

**召回**：几天后新会话里 Agent 调 `recall_memory("Python formatting", current_path="/projects/backend")`。第一轮 BM25 命中 "formatting" 这类词、向量补上语义相近的，路径匹配再给一条加成；第二轮从已命中的记忆沿实体边走一步，把 "Alex hates semicolons" 这类你没直接问的记忆带回来。相似度过了 0.75 的那条 `recall_count` 加一，下次更抗衰减——整个过程 Agent 无需任何人工提醒。

---

## 存储架构：默认本地，按需扩展

| 组件 | 技术 | 说明 |
|------|------|------|
| 向量存储 | **DuckDB**（默认） | 单文件本地库，原生余弦相似度，`~/.yourmemory/memories.duckdb` |
| 图存储 | **NetworkX**（默认） | pickle 持久化，`~/.yourmemory/graph.pkl`；可选 Neo4j 后端 |
| 嵌入模型 | **sentence-transformers** | `multi-qa-mpnet-base-dot-v1`，768 维，检索调优（question→passage） |
| NLP | **spaCy** | 去重与实体抽取，全部本地 |
| 定时任务 | **APScheduler** | 每日衰减 + 修剪 |
| 关系存储 | **PostgreSQL + pgvector** | 团队/大规模场景，`pip install 'yourmemory[postgres]'` |

嵌入模型值得单独说一句：早期版本用对称相似度的 `all-mpnet-base-v2`，当前默认已换成检索调优的 `multi-qa-mpnet-base-dot-v1`。换模型不是白赚——LoCoMo 会话摘要检索上它反而略低（55% 对 59%），但换来了 LongMemEval 原始对话轮检索的大幅提升（84.8% 对 84.0%）。细节见基准一节。

并发场景有个已知坑：DuckDB 是单写者锁，MCP 服务器和 HTTP 服务器同时跑会互相卡住。官方 troubleshooting 给的解法是改用 SQLite——`DATABASE_URL=sqlite:///~/.yourmemory/memories.db`，它对并发读写更宽容。

---

## 快速开始：注册、配置、可选本地抽取

Python 3.11–3.14，无需 Docker：

```bash
pip install yourmemory
yourmemory-register <your-token>
yourmemory-setup
```

token 在 [yourmemoryai.xyz](https://yourmemoryai.xyz/) 用邮箱加 6 位验证码换取。`yourmemory-setup` 会自动探测本机装了哪些客户端——Claude Code、Claude Desktop、Cursor、Windsurf、Cline——并直接写好 MCP 配置，然后询问后端选择（DuckDB 默认，或提供 `DATABASE_URL` 的 Postgres）。

抽取后端默认是内置启发式，开箱即用。想要更高质量的事实抽取，装 [Ollama](https://ollama.com) 后 setup 会自动拉取 `qwen2.5:7b`（约 4.7 GB）全本地运行；或者设 `YOURMEMORY_EXTRACT_BACKEND=anthropic` 走云端。

不想碰 pip 的用户有二进制发行版：macOS（Apple Silicon/Intel）、Linux、Windows 四个平台的独立可执行文件，自带 Python、全部依赖和两个 ML 模型，下载即用且完全离线——代价是约 2 GB 体积。仓库里的 `build-binary.sh` 一条命令可自建。

老命令 `yourmemory-path`（打印可执行文件路径）保留给手动配置的 Power user；`sample_CLAUDE.md` 也还在仓库里，想要手动定制记忆工作流可以参考。

---

## MCP 工具与无 LLM 问答

YourMemory 以 stdio MCP 服务器运行，向客户端暴露三个工具，由 AI 在合适的时机自动调用：

| 工具 | 调用时机 | 功能 |
|------|---------|------|
| `recall_memory(query, user_id?, api_key?, top_k?, current_path?)` | 每个任务开始 | 混合召回；路径匹配的记忆获得相关性加成 |
| `store_memory(content, importance, category?, context_paths?)` | 学到新信息后 | 嵌入、去重、入库并挂上衰减 |
| `update_memory(id, new_content, importance)` | 已存事实过时 | 重新嵌入替换，变更写入审计链 |

空间参数是实用的小设计：存记忆时带上 `context_paths`，之后在同一目录工作时召回会自动加成：

```python
store_memory(
    "Alex prefers tabs over spaces in Python",
    importance=0.9, category="fact",
    context_paths=["/projects/backend"],
)

recall_memory("Python formatting", current_path="/projects/backend")
# → {"content": "Alex prefers tabs over spaces in Python", "strength": 0.87}
```

两个不走 MCP 的入口：

**`yourmemory ask`**——不调用任何 LLM，直接从记忆库答题。记忆足够强就秒答，零 token、零延迟；不够强就明确说"记忆不足以回答"，而不是编一个。官方称这是唯一能做到零 LLM 调用问答的记忆系统。

**API Proxy**——把客户端的 `base_url` 指向 `localhost:3033/proxy/anthropic`（或 `/proxy/openai`），代理拦截每次 LLM 调用并自动注入相关记忆，store/update 也无需模型配合。MCP 工具靠 AI 自觉调用，代理把这个不确定性去掉了。

---

## 多 Agent 与团队记忆池

多个 Agent 可以共享同一个 YourMemory 实例。单实例内的权限隔离走 `register_agent`（源码 `src/services/api_keys.py`）：

```python
from src.services.api_keys import register_agent

result = register_agent(
    agent_id="coding-agent",
    user_id="sachit",
    can_read=["shared", "private"],
    can_write=["shared", "private"],
)
# 返回 {"api_key": "ym_xxxx"}，仅显示一次
```

带 `api_key` 调用工具时，Agent 看到 shared 记忆加自己的 private 记忆；不带则只有 shared。

跨用户的团队场景是 **Team Memory Pools**：一个池子的成员共享"机构知识"，各自的私有上下文留在各自名下。REST 接口管理建池、加成员（带角色）、贡献共享记忆、跨池召回：

```bash
POST /pools                  # 建池
POST /pools/{id}/members     # 加成员（带角色）
POST /pools/{id}/memories    # 贡献共享记忆
POST /pools/{id}/retrieve    # 跨池召回
```

---

## 审计链与数据权利

企业不敢用黑盒记忆系统，YourMemory 的回应是把每一步都变成可验证的：读、写、更新、删除、合并，全部追加进一条**哈希链审计账本**——每行的 `row_hash = sha256(前一行哈希 + 数据)`，改动任何历史记录都会让链条从那一行断开，`GET /audit/verify` 可以密码学验证完整链条。

几个值得注意的口径：审计日志是 fail-open 的（记账失败不阻塞记忆操作）；仪表盘自身渲染产生的读写事件被排除，账本里留的是信号不是噪音；保留期有 90 天的硬下限，`POST /audit/prune` 不能删得更短。

数据权利对应一组端点，官方声明与 SOC 2 控制项对齐（详见 SECURITY.md）：

| 权利 | 端点 | 用途 |
|------|------|------|
| 访问（DSAR 导出） | `GET /users/{id}/export` | 导出某用户的全部记忆 |
| 遗忘权 | `DELETE /users/{id}/memories` | 一条命令清除 |
| 可携带 | `POST /users/{id}/import` | 重新导入此前的导出 |
| 可恢复 | `GET /users/{id}/archive` | 找回被合并归档的原件 |

---

## 性能基准：三套公开基准与两笔效率账

官方基准文档（BENCHMARKS.md）覆盖三个外部数据集加两项内部效率测量，脚本都在仓库 `benchmarks/` 目录里，声称每个数字可独立复现。先说测的是什么，再看数字。

### LoCoMo-10：多会话对话记忆

LoCoMo 是 Snap Research 发布的长对话基准，这里取 10 个跨越数周到数月的多会话样本，1,534 个 QA 对。输入是各系统相同的会话摘要文本，指标 Recall@5——正确答案是否出现在前 5 条检索结果里，命中规则为精确子串或过半有效词元匹配，对所有系统一致。

| 系统 | Recall@5 | 95% CI | 样本 |
|------|:--------:|:------:|:----:|
| **YourMemory**（BM25+向量+图+衰减） | **59%** | 56–61% | 10/10 |
| Zep Cloud | 28% | 26–30% | 10/10 |
| Supermemory | 31%* | 28–33% | 4/10 |
| Mem0 | 18%* | 16–20% | 6/10 |

\* Supermemory 在第 5 个样本耗尽免费配额（1 万次查询），Mem0 在第 7 个样本耗尽（1 千次操作）；未完成样本按 0 计，跑满的话数字大概率更好看。

YourMemory 对 Zep Cloud +31 个百分点（相对提升 111%），且在全部 10 个样本上逐个领先。官方对差距的解释是架构性的：YourMemory 保留完整的会话摘要，而 Zep Cloud 用 LLM 把会话压缩成抽象事实，压掉了具体的日期、人名和事件——恰是 LoCoMo QA 对考的东西。

这个表不能直接推出的：59% 是旧嵌入模型 `all-mpnet-base-v2` 测出的成绩，当前默认模型在 LoCoMo 摘要检索上只有 55%，换模型是拿这里的一点点换 LongMemEval 上的大幅提升。另外 Recall@5 高不等于最终回答正确——这里没有 LLM 生成环节的评测。

### LongMemEval-S：长程记忆检索

LongMemEval 被官方称为"最难的长期记忆标准基准"：500 个问题，每个埋在约 53 个干扰会话里，输入是原始对话轮而非摘要。

| 指标 | 得分 |
|------|:----:|
| Recall@5（top-5 含任一正确会话） | 89.4% |
| Recall-all@5（top-5 含全部正确会话） | 84.8% |
| nDCG@5（排序质量） | 87.4% |

分题型看，时间推理和多会话题最难——找到"某一条"正确会话的概率在 95% 以上，但把"所有"该找的会话都凑进 top-5 掉到 75.9%。这两类最依赖时间锚定的关联。

### HotpotQA：多跳事实拼接

从 HotpotQA distractor 集抽 200 个多跳问题（166 道桥接题、34 道对比题），两条支持事实分开存储，考察两者是否都进 top-5：

| 配置 | BOTH_FOUND@5 |
|------|:------------:|
| **向量+BM25+实体图** | **71.5%** |
| 仅相似度图（无实体边） | 59.5% |

实体边贡献 +12 个百分点，桥接题上收益最大（+14pp）——正是前文说的"第二条事实与问题相似度低，只能靠图走过去"的场景。剩下 28.5% 的缺口也交代了原因：桥接实体既不在问题里、也不在任何已取回的事实里，图无法连接它没索引过的东西。

### 一个诚实的消融：时间加成没用

v1.4.26 加了时间推理（temporal boost）：查询含"上周""最近"这类相对时间表达时，给时间窗内记忆加 0.25 分。作者自己跑的消融显示这个加成在 LongMemEval 上是 **0pp**——500 题里只触发了 6%，因为基准里的时间问题是事件锚定的（"X 是什么时候发生的"），不是窗口锚定的（"上周聊了什么"）。LoCoMo 上时间类问题确实高 17pp（66% 对 49%），但归因分析说明增益来自 BM25 的关键词重叠，不是时间窗。这个加成为真实使用场景设计，基准上无效——作者把无效结果原样发了出来，这在自报基准里不常见。

### 两笔效率账

**Token 账**：3 会话的模拟开发工作流里，无记忆基线的上下文线性增长（978 → 1,170 → 1,170 tokens），YourMemory 保持约 76–91 tokens 的扁平记忆块，总计省 19.7%；拉到 30 会话，成本差距拉大到 84.1%——线性对扁平，差距只会随会话数扩大。

**LLM 调用账**：基线 14 次调用里 4 次是重新问偏好之类的澄清，YourMemory 12 次，省 14%。幅度不大，但省的都是最烦人的那种来回。

小规模下修剪的收益也要如实说：15 条合成记忆里只剪掉 3 条，top-5 上下文 token 只省 4.1%——衰减修剪的价值要等记忆规模上来才显现。

---

## 适用场景与采用建议

**适合：**

- 需要跨会话记忆的 AI 编程助手（Claude Code、Cursor、Cline、Windsurf）
- 长期运行的 Agent，需要区分重要与过时信息、控制上下文膨胀
- 数据不能出本机的场景——嵌入、抽取、检索全在本地，审计链和导出端点对合规审查友好
- 多 Agent 或团队共享知识池，需要 shared/private 隔离

**不适合：**

- 商业产品——CC BY-NC 4.0 禁止未经书面授权的商业使用，商用要联系作者（mishrasachit1@gmail.com）
- 毫秒级响应要求的实时系统——本地嵌入加混合检索有延迟
- 超大规模记忆——官方建议那类场景直接上 PostgreSQL + pgvector

**采用顺序建议**：个人用户从 `pip install yourmemory` 加默认 DuckDB 开始，setup 会自动接好现有客户端，十分钟内能验证"它记不记得你"；MCP 和 HTTP 同时跑遇到锁冲突就切 SQLite；小团队要共享记忆再上 Postgres 和 Pools；任何商用集成先把许可证谈下来。

---

## 总结

YourMemory 的价值不在"又一个向量库"，而在把记忆系统里最容易被回避的问题——遗忘、合并、排序、信任——各自做成了显式机制：艾宾浩斯衰减按类别分层、Consolidation 事件驱动压缩、排序明确排除强度、审计链可密码学验证。LoCoMo-10 上 59% 对 Zep Cloud 28% 的成绩有完整的基准脚本背书，作者连自家时间加成无效的消融都公之于众。对需要跨会话记忆又不想把数据交给第三方的开发者，这是目前少数把"记住"和"忘掉"一起想清楚的开源方案。

- 仓库地址：[github.com/sachitrafa/YourMemory](https://github.com/sachitrafa/YourMemory)
- 官网与 token 注册：[yourmemoryai.xyz](https://yourmemoryai.xyz/)
- 在线演示：[交互式 Demo](https://sachitrafa.github.io/YourMemory/marketing/interactive.html)
- 基准详情：[BENCHMARKS.md](https://github.com/sachitrafa/YourMemory/blob/main/BENCHMARKS.md)
- 技术解读：[I built memory decay for AI agents using the Ebbinghaus forgetting curve](https://dev.to/sachit_mishra_686a94d1bb5/i-built-memory-decay-for-ai-agents-using-the-ebbinghaus-forgetting-curve-1b0e)
