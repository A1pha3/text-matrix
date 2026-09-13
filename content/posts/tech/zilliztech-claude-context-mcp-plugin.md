---
title: "zilliztech/claude-context：把整个代码库做成可检索上下文的 MCP 插件"
slug: zilliztech-claude-context-mcp-plugin
github_repo: "zilliztech/claude-context"
source_key: "gh:zilliztech/claude-context"
date: "2026-04-22T16:35:00+08:00"
description: "zilliztech/claude-context 是一个 MCP 插件，为 Claude Code 等 AI 编码助手提供混合检索（BM25 + 稠密向量）代码搜索，索引存入 Milvus 或 Zilliz Cloud，按需加载相关代码，官方对照评估在检索质量相当前提下省约 40% token。"
categories: ["技术笔记"]
tags: ["MCP", "Claude Code", "向量数据库"]
---

# zilliztech/claude-context：把整个代码库做成可检索上下文的 MCP 插件

## 概述

代码库一大，AI 编码助手就开始把预算花在找代码上：多轮 grep、来回翻目录、读错文件。**zilliztech/claude-context** 把这一步外包给向量数据库——先离线索引全库，查询时按相关度召回片段，只把命中的代码送进模型上下文。它是 Zilliz 开源的 MCP（Model Context Protocol）插件，官方对照实验给出的结论是：同等检索质量下省约 40% token。

> **GitHub**: [zilliztech/claude-context](https://github.com/zilliztech/claude-context)  
> **许可证**: MIT  
> **运行时**: Node.js ≥ 20  
> **向量数据库**: Milvus 或 Zilliz Cloud

### 系统地图

仓库是 monorepo，三个包各管一段：

| 包 | 职责 |
|------|------|
| `@zilliz/claude-context-core` | 核心索引引擎：代码分块、embedding、向量库读写 |
| `@zilliz/claude-context-mcp` | MCP 服务器，把 4 个检索工具暴露给 AI 客户端 |
| VS Code 扩展（Semantic Code Search） | 不经过 agent，在编辑器里直接做语义搜索 |

多数读者接触的是第二个包：`npx @zilliz/claude-context-mcp@latest` 拉起一个 stdio 传输的 MCP 服务器，Claude Code、Codex CLI、Cursor 等客户端都能挂载。

---

## 快速开始

### 1. 前置条件

- 一个向量数据库。最省事的路径是在 [Zilliz Cloud](https://cloud.zilliz.com/signup) 注册免费档，拿到公网地址 `MILVUS_ADDRESS` 和 API Key `MILVUS_TOKEN`；想自托管，就部署一套开源 Milvus，把地址指向它。
- 一个 OpenAI API Key（用于默认 embedding 模型，形如 `sk-...`）。

### 2. 为 Claude Code 添加 MCP 服务器

```bash
claude mcp add claude-context \
  -e OPENAI_API_KEY=sk-your-openai-api-key \
  -e MILVUS_ADDRESS=your-zilliz-cloud-public-endpoint \
  -e MILVUS_TOKEN=your-zilliz-cloud-api-key \
  -- npx @zilliz/claude-context-mcp@latest
```

### 3. 使用

在项目目录启动 Claude Code，依次执行：

```text
Index this codebase            # 索引当前代码库
Check the indexing status      # 查看索引进度
Find functions that handle user authentication   # 用自然语言搜索
```

三条命令依次完成索引、查状态、语义检索。注意顺序：`get_indexing_status` 显示进度百分比，索引完成后 `search_code` 才查得到东西。

---

## 提供的 MCP 工具

| 工具 | 作用 |
|------|------|
| `index_codebase` | 为当前目录建立混合检索（BM25 + 稠密向量）索引 |
| `search_code` | 用自然语言检索已索引代码库 |
| `clear_index` | 清空某个代码库的索引 |
| `get_indexing_status` | 查询索引状态，显示进行中代码库的进度百分比 |

---

## 工作原理

整条流水线：

```text
索引侧：代码库 → AST 分块 → BM25 稀疏信号 + Embedding 稠密向量 → 存入 Milvus / Zilliz Cloud
增量：  Merkle 树比对文件快照，只重索引变更过的文件
查询侧：自然语言查询 → 双路召回 → 融合排序 → 片段注入上下文 → 模型作答
```

索引侧有三个关键设计：

1. **AST 分块，解析失败自动回退**。默认按抽象语法树切分代码，按语法结构下刀而不是按固定字符数硬切；解析不了的文件自动回退到 LangChain 字符分割器。
2. **双路信号**。每个片段同时生成 BM25 关键词信号和 embedding 向量：前者接得住精确符号名（比如 `parseConfig` 这种必须逐字命中的查询），后者接得住"处理用户登录的那段代码"这类自然语言描述。两路各管一种查询习惯，这是"混合检索"的实际含义。
3. **Merkle 树增量索引**。为文件快照建 Merkle 树，代码变更后比对树差异，只重新索引改动过的文件，不做全量重建。

查询侧只有一步：BM25 与向量双路召回、融合排序，把相关片段连同文件路径返回给模型。

支持的语言：TypeScript、JavaScript、Python、Java、C++、C#、Go、Rust、PHP、Ruby、Swift、Kotlin、Scala、Markdown。

---

## 一次查询的完整流转

以在 Claude Code 里问 "Find functions that handle user authentication" 为例：

1. Claude 调用 `search_code` 工具，把查询原文交给 MCP 服务器。
2. 服务器生成两条信号：查询的 embedding 向量，加上 BM25 关键词信号。
3. 向量数据库双路召回、融合排序，返回得分最高的代码片段及所在文件路径。
4. Claude 拿到片段后决定下一步：直接作答，或用普通 read 工具展开某个文件的完整上下文。

如果这期间代码库发生了改动，下次索引时 Merkle 树先比对快照，只有变更文件重新走分块和 embedding，其余直接复用。

官方评估里测的正是更完整的版本：agent 拿到 bug 报告后，基线代理靠 grep 反复试探——试一个关键词、读几个文件、再换关键词；装了 claude-context 的代理先用一次自然语言检索定位相关文件，直接进入修改环节。下文的 token 节省就是这么省出来的。

---

## 评估数据怎么看

README 上一句"省 40% token"，背后是官方 evaluation 目录里一场设计完整的对照实验，值得拆开看：

- **测什么**：token 效率和工具调用效率，不是回答正确率。
- **怎么测**：从 SWE-bench_Verified 挑 30 个实例（限定"15–60 分钟难度、恰好修改 2 个文件"的题）；基线代理只有 read、grep、edit 等基础工具，实验组额外加上 claude-context；两组用同一个模型（GPT-4o-mini）各跑 3 次，共 6 次运行。
- **数字**：平均 token 用量 73,373 → 44,449（-39.4%，每实例省 28,924）；工具调用 8.3 → 5.3 次（-36.3%）；检索质量用 precision / recall / F1 衡量，两组平均 F1 都是 0.40。

这组数字的读法：节省来自"少走弯路"——语义检索把多轮 grep 探路压缩成一两次定向查询。F1 持平说明它没有让检索更准，只是让"达到同样的检索效果"变得更便宜。README 另有一句补充：当上下文长度受限、装不下完整探路过程时，用它的检索和回答效果更好。

同样要看清数字推不出什么：30 个实例是小样本，LLM 输出有非确定性，官方自己说明数值会在不同运行间波动；实验基于 `claude-context-mcp@0.1.0` 测试；题目限定中等难度、两文件修改，"任何任务都省 40%"这个结论不成立。把它当方向性参考，比当精确承诺合适。

---

## 进阶配置

- **更换 embedding 模型**：支持 OpenAI、VoyageAI、Gemini、Ollama 四家提供商，可选模型如 `text-embedding-3-large`、`voyage-code-3`，配置示例见[各嵌入商配置](https://github.com/zilliztech/claude-context/blob/master/packages/mcp/README.md#embedding-provider-configuration)。
- **文件包含 / 排除**：可自定义哪些文件入索引、哪些跳过，规则说明见 [File Inclusion & Exclusion Rules](https://github.com/zilliztech/claude-context/blob/master/docs/dive-deep/file-inclusion-rules.md)。
- **向量库选择**：`MILVUS_ADDRESS` 既可以指向 Zilliz Cloud 端点，也可以指向自托管 Milvus。embedding 用 Ollama、向量库用自托管 Milvus，两条都换成本地组件后就不再依赖云服务；官方 FAQ 也专门讨论了"完全本地部署"这个话题。
- **环境变量**：各 MCP 客户端的环境变量配置见 [Environment Variables Guide](https://github.com/zilliztech/claude-context/blob/master/docs/getting-started/environment-variables.md)。

---

## 支持的客户端

除 Claude Code 外，官方给出了 Codex CLI（TOML）、Gemini CLI、Qwen Code、Cursor、Void、Claude Desktop、Windsurf、VS Code、Cherry Studio、Cline、Augment、Roo Code、Zencoder 及 LangChain / LangGraph 的接入方式。服务器走标准 stdio 传输，任意兼容 MCP 的客户端都可用 `npx @zilliz/claude-context-mcp@latest` 拉起。

---

## 常见问题与排查

- **搜索没有结果**：先确认索引已完成——`get_indexing_status` 会显示进度百分比，索引完成前 `search_code` 查不到东西。
- **索引内容不对或想重来**：`clear_index` 清空指定代码库，再重新 `index_codebase`。
- **哪些文件会被收录**：官方在 [file-inclusion-rules 文档](https://github.com/zilliztech/claude-context/blob/master/docs/dive-deep/file-inclusion-rules.md)里给出了完整规则。
- **多项目管理、与 Serena / Context7 / DeepWiki 的定位差异**：仓库 FAQ 逐条列出了这些话题，入口见 [README](https://github.com/zilliztech/claude-context)。

---

## 谁该现在用，谁可以等等

适合先上：

- 代码库到了 grep 要来回试探的规模，agent 经常在"找位置"上花掉大半预算。
- 按 token 计费、对上下文成本敏感的团队。
- 已经在用 Claude Code、Codex CLI 这类支持 MCP 的客户端做日常开发。

可以等等：

- 几千行以内的小仓库，一次 read 就能看完，建索引是纯开销。
- 代码不允许出网、又不想承担一套 Milvus + Ollama 运维的团队。

落地路径从最短的那条开始：Zilliz Cloud 免费档加默认 OpenAI embedding，先索引一个真实项目跑一周，看 token 账单和检索命中质量，再决定要不要换 embedding 模型或自托管向量库。

---

## 资源链接

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | [zilliztech/claude-context](https://github.com/zilliztech/claude-context) |
| Zilliz Cloud | [cloud.zilliz.com](https://cloud.zilliz.com) |
| 评估代码与数据 | [evaluation 目录](https://github.com/zilliztech/claude-context/tree/master/evaluation) |
| 文件过滤规则 | [file-inclusion-rules.md](https://github.com/zilliztech/claude-context/blob/master/docs/dive-deep/file-inclusion-rules.md) |
