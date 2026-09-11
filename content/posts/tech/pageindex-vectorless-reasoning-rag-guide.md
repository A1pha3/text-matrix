---
title: "PageIndex：无向量数据库的推理型 RAG"
date: "2026-05-08T03:11:04+08:00"
slug: "pageindex-vectorless-reasoning-rag-guide"
github_repo: "VectifyAI/PageIndex"
description: "PageIndex 是一种无向量、基于推理的 RAG 引擎，不建向量索引、不做文档分块，而是先把长文档组织成层级树索引，再让 LLM 通过树搜索推理找到最相关的段落。本文解析其核心原理、SDK 用法、MCP 接入与适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["RAG", "LLM", "向量数据库"]
---

## 你会拿到什么

读完这篇文章，应该能回答：

1. 传统向量 RAG 在长文档、复杂推理场景里缺什么，PageIndex 用"相似不等于相关"这个判断把它换掉。
2. PageIndex 的索引与检索到底怎么运作：不建向量索引、不切块，靠一棵树 + LLM 推理。
3. 用 Python SDK 索引一份文档并提问的完整流程，以及前置条件和验证步骤。
4. 通过 MCP 把 PageIndex 接进自有 Agent 的方法。
5. PageIndex 适合哪些工作，哪些场景仍该用向量 RAG。

---

## 一、它要解决的问题

向量 RAG 的套路很固定：拆块（chunk）→ 嵌入（embedding）→ 存入向量库 → 检索时算相似度返回 Top-K。这套流程在长文档上会露出三个毛病：

- **分块切断了上下文**。固定尺寸的分块常在语义边界生切，命中的块缺前因后果。
- **相似 ≠ 相关**。向量空间里"长相接近"不等于"回答这个问题的关键信息"。多义词、需要跨段落综合的推理，仅靠几何相似度经常够不着真正相关的部分，却把不相干但形似的片段捞上来。
- **重排序补刀**。为了让 Top-K 够准，通常还得再套一层重排序阶段，延迟和成本一起涨。

PageIndex 抓住的正是"相似 ≠ 相关"：检索真正需要的是相关性，而相关性判断靠的是推理，不是距离计算。既然 LLM 本身会读文档、会推理，就让它直接读文档结构去找答案，而不是把文档压成向量再碰运气。

## 二、核心原理：树索引 + 树搜索

PageIndex 的官方定位是 *vectorless, reasoning-based RAG*——没有向量数据库、没有 embedding、没有 chunking。它的做法分两步（见[官方说明](https://github.com/VectifyAI/PageIndex)）：

1. **建目录式树索引**。把文档按真实结构（章节、小节、页码范围）组织成一棵层级树，类似"目录"。这一步不产生向量，只保留结构。
2. **推理式树搜索**。查询到来时，让 LLM 沿这棵树逐层下钻：先判断哪部分相关，再往下定位到具体段落，直到找出能支撑答案的那些内容。

这和"整页当索引单元"是两回事——它索引的是文档的结构树，检索是带推理的树搜索，不是把整页喂给模型。结果能追溯到明确的章节目录和行级引用，不靠模糊的相似度分数解释"为什么是它"。

两个由此而来的性质：

- **可追踪可解释**：每个结果都能指到具体章节和引用位置，检索决策不再是黑盒。
- **不留 Top-K 参数**：不是固定取前 K 个相似片段，而是把相关段落都找出来，省掉重排序那层。

### 官方基准

按[官方发布的基准](https://github.com/VectifyAI/Mafin2.5-FinanceBench)，PageIndex 在 FinanceBench（SEC 申报文件的问答基准）上检索准确率达到 98.7%，报告中对比的向量 RAG 方案约为 50%。这是厂商自报数字，作为参考而非独立结论。

## 三、快速开始

### 前置条件

- Python 环境，能装包和跑脚本。
- 一个推理 LLM 的 API Key（示例用 OpenAI，也支持 Anthropic、OpenRouter 等 OpenAI 兼容端点）。
- 用 Cloud 模式才需要注册 [Developer Dashboard](https://dash.pageindex.ai/api-keys) 拿 API Key；本地模式不需要。

### 1. 安装 SDK

```bash
pip install -U pageindex
```

### 2. 索引进文档并提问

```python
import os
from pageindex import PageIndexClient

os.environ["PAGEINDEX_API_KEY"] = "your-pageindex-key"
os.environ["OPENAI_API_KEY"] = "your-openai-key"

client = PageIndexClient(
    index="cloud",          # 编排+存储走 PageIndex Cloud；本地可换成 "gpt-5.6-luna"
    chat="gpt-5.6-sol",     # 检索树、回答问题的模型，仍是你自己的
)

doc_id = client.submit_document("./2023-annual-report.pdf", wait=True)["doc_id"]

query = "这份报告的核心结论是什么？"
for chunk in client.chat(query, doc_id=doc_id, stream=True):
    print(chunk, end="", flush=True)
```

### 3. 验证是否跑通

- `submit_document` 返回的 `doc_id` 非空，说明文档已索引完成。
- `chat()` 能流式输出回答，且回复里带文档章节引用，说明树搜索正常。
- 若报鉴权错误，检查 `PAGEINDEX_API_KEY` 与 LLM 的 Key 是否都正确设置。

## 四、用 MCP 接入

PageIndex 通过 MCP 暴露为工具，供 Claude、LangChain、OpenAI Agents SDK 等任何 MCP 客户端调用。它在[官方文档](https://docs.pageindex.ai/mcp)中是 HTTP 远程服务，不是 npm 包。**MCP 只作用于已经上传并索引进 Cloud 账户的文档**，接 MCP 前得先用 SDK 或 API 把 PDF 提交进去。

```json
{
  "mcpServers": {
    "pageindex": {
      "type": "http",
      "url": "https://api.pageindex.ai/mcp",
      "headers": {
        "Authorization": "Bearer your_api_key"
      }
    }
  }
}
```

配置好后，对已经索引的文档，就能在自家 Agent 里直接调用 PageIndex 的检索工具。

## 五、Local 与 Cloud 两种运行方式

| 维度 | Local | Cloud |
|------|-------|-------|
| 索引位置 | 自己机器上 | PageIndex 托管 |
| API Key | 不需要 | 需要 |
| 适用文档 | 纯文本 PDF | 扫描件、以图片/图表为主的 PDF |
| OCR / 图像理解 | 无 | 有（生产级 OCR） |
| 成本 | 只用你自己的 LLM 费用 | 解析、OCR、存储按计划计费，Chat 仍走你的模型 |

索引（Local）免费开源，跑在自己机器上；Chat 无论哪种模式都走你自己的模型，费用属于你的 LLM 服务商。

## 六、适用场景与边界

### 适合

官方明确的对口场景是行业长文档分析：金融财报与 SEC 申报件、监管与合规文件、医疗报告、法律合同、技术手册与科学文献。这些文档结构重、追问常在多段落之间来回综合，正是树搜索推理的用武之地。

### 不适合

- **海量文档库检索**：检索是推理任务，查询时要动 LLM，成本与延迟随文档规模和查询数上升，超大规模场景下高于向量搜索。
- **低延迟实时界面**：LLM 推理延迟远高于向量相似度计算，不适合做毫秒级搜索框。
- **简单关键词定位**：只是找某个词在哪，倒排索引更省事。

### 与向量 RAG 的选择

| 场景 | 用哪个 |
|------|--------|
| 人名、日期等简单事实查找 | 向量 RAG |
| 需要跨段落综合的长文档问答 | PageIndex |
| 海量语料 + 通用检索 | 向量 RAG；大规模时可用 PageIndex 的文件级索引层做补强 |
| 快速原型验证 | PageIndex（部署简单） |

## 相关资源

- GitHub：[VectifyAI/PageIndex](https://github.com/VectifyAI/PageIndex)（官方页面显示已超 35k Stars，数字会浮动）
- 官方文档：[https://docs.pageindex.ai](https://docs.pageindex.ai)
- MCP 集成：[https://docs.pageindex.ai/mcp](https://docs.pageindex.ai/mcp)
- 开发者面板：[https://dash.pageindex.ai](https://dash.pageindex.ai)
- Discord：[https://discord.gg/VuXuf29EUj](https://discord.gg/VuXuf29EUj)