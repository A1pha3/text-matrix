---
title: "Antigravity Awesome Skills：1,400+ AI工具插件生态系统完全指南"
date: "2026-04-12T18:01:00+08:00"
slug: antigravity-awesome-skills-ai-tools-ecosystem-guide
description: "33.3k Stars的Antigravity Awesome Skills专辑，收录1,400+AI工具插件。涵盖官方26个插件、多Agent系统、AI编程、AI搜索、AI音乐等12大分类，是AI工具爱好者的一站式资源库。"
draft: false
categories: ["技术笔记"]
tags: ["AI工具", "Antigravity", "Claude Code", "插件生态", "AI资源导航"]
---

# Antigravity Awesome Skills：1,400+ AI 工具插件生态系统完全指南

## 快速信息卡

> **GitHub 仓库**: [sickn33/antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)
>
> | 指标 | 数值 |
> |------|------|
> | ⭐ Stars | 41,675+ |
> | 🍴 Forks | 6,682+ |
> | 📜 License | MIT |
> | 💻 主要语言 | Python |
> | 📅 最后更新 | 2026-06-25 |
> | 🔗 在线预览 | [GitHub Pages](https://sickn33.github.io/antigravity-awesome-skills/) |

---

## 学习目标

- 理解 Antigravity Awesome Skills 在 AI 工具生态中的定位
- 掌握 Antigravity Tools 官方 26 个插件的功能边界
- 了解 1,400+ AI 工具的 12 大分类体系
- 学会按场景挑选工具组合，避免在选项海里反复试错
- 识别这个资源库的适用边界与时效风险

---

## 目录

- [快速信息卡](#快速信息卡)
- [学习目标](#学习目标)
- [一句话判断](#一句话判断)
- [总览地图](#总览地图)
- [Antigravity Tools 官方插件](#antigravity-tools-官方插件)
- [AI 编程工具生态](#ai-编程工具生态)
- [AI 搜索工具](#ai-搜索工具)
- [AI 对话助手](#ai-对话助手)
- [AI 音乐创作](#ai-音乐创作)
- [AI 视频制作](#ai-视频制作)
- [AI 数据分析](#ai-数据分析)
- [AI 写作助手](#ai-写作助手)
- [AI 思维导图](#ai-思维导图)
- [工作流自动化](#工作流自动化)
- [开发工具](#开发工具)
- [安全与隐私](#安全与隐私)
- [AI 基础设施](#ai-基础设施)
- [精选资源导航](#精选资源导航)
- [资源统计总览](#资源统计总览)
- [任务流案例](#任务流案例从需求到工具组合)
- [实用技巧](#实用技巧)
- [采用建议](#采用建议)
- [自测题](#自测题)
- [进阶路径](#进阶路径)
- [常见问题](#常见问题)

---

## 一句话判断

Antigravity Awesome Skills 是一个由社区维护的 AI 工具索引仓库，把分散在 GitHub 各处的 1,400+ 工具按用途归类，并配套 26 个官方插件做统一接入。它适合做工具发现入口；决策依据需要回到原始仓库核对——仓库里的 Stars、下载量、版本号会随时间漂移。

## 总览地图

仓库把 AI 工具生态拆成两条主线：

| 主线 | 角色 | 代表内容 |
|------|------|----------|
| Antigravity Tools | 底层代理平台，负责 API 路由和账号管理 | 26 个官方插件 |
| Antigravity Awesome Skills | 上层索引，收录 1,400+ 工具的资源链接 | 12 大分类清单 |

Antigravity Tools 解决"如何调用"，Awesome Skills 解决"调什么"。两者通过插件市场衔接：用户在 Awesome Skills 里发现工具，回到 Antigravity Tools 里安装对应插件。

### 仓库核心数据（截至 2026-04-09）

| 指标 | 数值 |
|------|------|
| GitHub Stars | 41,675+ |
| Forks | 6,682+ |
| Watchers | 41,675 |
| 贡献者 | 1 人（sickn33） |
| 最新版本 | v1.0.0（2026-04-09） |
| 许可证 | MIT |

> 注：仓库目前由单人维护，分类标准与收录门槛取决于维护者判断；下文 Stars 等数据均为文章撰写时的快照，最新数字以仓库 README 为准。

---

## Antigravity Tools 官方插件

### 26 个官方插件一览

下表按 Stars 排序，列出头部插件。完整名单见仓库 README。

| 插件名称 | Stars | 下载量 | 核心功能 |
|----------|-------|--------|----------|
| claude-code | ⭐ 28.1k | 高 | Claude Code 官方集成 |
| gemini-cli | ⭐ 15.0k | 高 | Gemini CLI 官方集成 |
| codex | ⭐ 8.5k | 中 | OpenAI Codex 集成 |
| antigravity-manager | ⭐ 6.0k | 高 | 核心管理器 |
| qwen-code | ⭐ 4.2k | 中 | 阿里通义灵码 |
| iflow | ⭐ 3.8k | 中 | iFlow 集成 |
| gemini-studio | ⭐ 2.5k | 低 | Gemini Studio |
| ... | ... | ... | ... |

头部插件集中在编程助手（claude-code、gemini-cli、codex、qwen-code）和管理工具（antigravity-manager），反映出 Antigravity Tools 的主要使用场景是 AI 编程工作流。

### 插件安装方法

```bash
# 通过 Antigravity Tools 内置商店安装
# 1. 打开 Antigravity Tools
# 2. 进入插件市场
# 3. 搜索插件名称
# 4. 点击安装

# 或手动安装
# 将插件文件夹放入 ~/.antigravity/skills/
```

手动安装路径 `~/.antigravity/skills/` 是用户级目录，不需要 root 权限，便于在多账号环境下隔离插件配置。

---

## AI 编程工具生态

### 核心编程助手

| 工具 | Stars | 特色功能 |
|------|-------|----------|
| **Claude Code** | 28.1k | Anthropic 官方 CLI，深度集成 |
| **Cursor** | 65k+ | AI 优先 IDE |
| **Cline** | 25k | VS Code 扩展 |
| **Aider** | 19.6k | 终端 AI 结对编程 |
| **GoCode** | 6.7k | Go 语言专用 |
| **Devin** | 16k | autonomous coder |

这一档工具按集成位置区分：Cursor 改造 IDE，Aider 走终端，Cline 寄生在 VS Code，Devin 走云端 autonomous 模式。选型时先确定工作流入口，再选工具。

### 多 Agent 系统

| 工具 | Stars | 特色功能 |
|------|-------|----------|
| **Multi-Agent Studio** | 精选 | 多 Agent 协作 |
| **Agent Protocol** | 精选 | Agent 通信协议 |
| **CrewAI** | 35k | 多 Agent 编排框架 |
| **AutoGen** | 32k | 微软多 Agent 框架 |
| **LangGraph** | 18k | 状态机 Agent |

CrewAI、AutoGen、LangGraph 三者定位接近，差异在编排范式：CrewAI 走角色分工，AutoGen 走对话驱动，LangGraph 走显式状态机。Multi-Agent Studio 和 Agent Protocol 标注为"精选"，意味着仓库维护者认可但缺少公开 Stars 数据。

### Autonomous Research

| 工具 | Stars | 特色功能 |
|------|-------|----------|
| **AutoResearch** | 7k | 自主研究 Agent |
| **Deep Research** | 精选 | 深度研究模式 |
| **MiniMax** | 精选 | 海螺 AI 研究 |
| **OpenDeepSearch** | 3.4k | 开源深度搜索 |

---

## AI 搜索工具

### 开源替代方案

| 工具 | Stars | 特色功能 |
|------|-------|----------|
| **Perplexica** | 19.6k | 开源 Perplexity 替代 |
| **Free-AskAI** | 5.9k | 免费 AI 搜索 |
| **Open Deep Search** | 3.4k | 深度搜索开源 |
| **Khoj** | 11k | 私有 AI 搜索 |
| **GPT Researcher** | 21k | 研究助手 |

### API 代理支持

| 工具 | 支持协议 | 备注 |
|------|----------|------|
| **Perplexica** | Antigravity 代理 | ⭐推荐 |
| **OpenDeepSearch** | OpenAI | 需 API Key |
| **GPT Researcher** | LangChain | 需配置 |

"Antigravity 代理"列表示该工具可以直接走 Antigravity Tools 的 API 路由，免去单独配置 Key 的步骤；标注 OpenAI 或 LangChain 的工具需要自行准备对应凭据。

---

## AI 对话助手

### 主流平台

| 平台 | 特色功能 |
|------|----------|
| **ChatGPT** | OpenAI 官方 |
| **Claude** | Anthropic 官方 |
| **Gemini** | Google 官方 |
| **Grok** | xAI |
| **Meta AI** | Facebook |
| **Poe** | 聚合平台 |

### 本地部署方案

| 工具 | Stars | 特色功能 |
|------|-------|----------|
| **Ollama** | 90k+ | 本地 LLM 运行 |
| **Jan** | 15k | 本地 ChatGPT 替代 |
| **LocalAI** | 23k | 本地 API 服务 |
| **llamafile** | 12k | 单文件 LLM |

本地部署这一档按易用性与控制力区分：Ollama 牺牲部分定制换开箱即用，LocalAI 走 OpenAI 兼容 API 路线方便迁移，llamafile 把模型打包成单文件便于分发。

---

## AI 音乐创作

| 平台 | 特色功能 |
|------|----------|
| **Suno** | 音乐生成标杆 |
| **Udio** | 高质量音乐 |
| **Splash** | AI DJ 混音 |
| **AI DJ** | 人工智能 DJ |
| **Mureka** | 音乐创作 |

音乐类工具多为闭源 SaaS，仓库只做收录，不提供本地替代。

---

## AI 视频制作

### 视频生成

| 平台 | Stars | 特色功能 |
|------|-------|----------|
| **Runway** | 35k | 视频生成标杆 |
| **Kling** | 25k | 快手可灵 |
| **Pika** | 18k | 轻量视频 |
| **Sora** | OpenAI | 视频生成 |
| **Hai** | 精选 | 新兴工具 |

### 视频处理

| 工具 | 特色功能 |
|------|----------|
| **CapCut** | 剪映海外版 |
| **HeyGen** | AI 虚拟人 |
| **D-ID** | 照片说话 |

---

## AI 数据分析

| 工具 | Stars | 特色功能 |
|------|-------|----------|
| **Mito** | 8k | Python 数据分析 |
| **MindsDB** | 32k | 预测分析 |
| **PandasAI** | 12k | 自然语言 Pandas |

---

## AI 写作助手

| 工具 | Stars | 特色功能 |
|------|-------|----------|
| **Notion AI** | 集成 | 笔记增强 |
| **Copy.ai** | 25k | 营销文案 |
| **Jasper** | 18k | 企业写作 |
| **Writesonic** | 15k | 多语言 |

---

## AI 思维导图

| 工具 | Stars | 特色功能 |
|------|-------|----------|
| **Xmind Copilot** | 精选 | 思维导图 AI |
| **Mapify** | 精选 | 思维导图 |
| **Amy Kris** | 精选 | AI 头脑风暴 |

---

## 工作流自动化

| 工具 | Stars | 特色功能 |
|------|-------|----------|
| **Zapier** | 25k | 工作流自动化 |
| **Make** | 18k | 场景自动化 |
| **n8n** | 48k | 开源工作流 |
| **AutoGPT** | 165k | 自主 Agent |
| **SuperAGI** | 12k | Agent 框架 |

---

## 开发工具

### 版本控制与 CI/CD

| 工具 | Stars | 特色功能 |
|------|-------|----------|
| **GitHub Copilot** | 集成 | 代码补全 |
| **GitLab Duo** | 集成 | GitLab AI |
| **Dependabot** | 集成 | 依赖更新 |

### 数据库与 API

| 工具 | Stars | 特色功能 |
|------|-------|----------|
| **Supabase** | 45k | Postgres+AI |
| **PlanetScale** | 15k | Serverless DB |
| **Postman** | 集成 | API 测试 |

---

## 安全与隐私

| 工具 | Stars | 特色功能 |
|------|-------|----------|
| **Claude Security** | 精选 | 安全分析 |
| **Semgrep** | 12k | 静态分析 |
| **Snyk** | 15k | 漏洞扫描 |

---

## AI 基础设施

### 向量数据库

| 工具 | Stars | 特色功能 |
|------|-------|----------|
| **Pinecone** | 云服务 | 托管向量 DB |
| **Chroma** | 18k | 本地向量 DB |
| **Qdrant** | 32k | Rust 向量 DB |
| **Weaviate** | 25k | 混合搜索 |

### LLM 网关

| 工具 | Stars | 特色功能 |
|------|-------|----------|
| **LiteLLM** | 18k | 统一 LLM 接口 |
| **PortKey** | 8k | LLM 网关 |
| **GPTCache** | 12k | LLM 缓存 |

---

## 精选资源导航

### 学习资源

| 资源 | 特色内容 |
|------|----------|
| **AI 安全** | 对齐研究、安全实践建议 |
| **Prompt 工程** | 提示词技巧、模板库 |
| **AI 法规** | 全球 AI 政策追踪 |

### 社区资源

| 社区 | 特色内容 |
|------|----------|
| **Hugging Face** | 模型库 |
| **AI Reddit** | 最新资讯 |
| **AI Newsletter** | 每周精选 |

---

## 资源统计总览

### 分类分布

| 分类 | 工具数量 | 代表项目 |
|------|----------|----------|
| AI 编程 | 50+ | Claude Code, Cursor, Cline |
| 多 Agent 系统 | 30+ | CrewAI, AutoGen |
| AI 搜索 | 20+ | Perplexica, GPT Researcher |
| AI 音乐 | 10+ | Suno, Udio |
| AI 视频 | 30+ | Runway, Kling, Sora |
| 工作流自动化 | 40+ | n8n, AutoGPT |
| AI 基础设施 | 50+ | 向量数据库、LLM 网关 |

---

## 任务流案例：从需求到工具组合

以"技术调研报告自动化"为例：

1. **定位分类**：在仓库 README 里找"Autonomous Research"和"AI 搜索"两个分类。
2. **筛选工具**：Autonomous Research 给出 AutoResearch、Deep Research、OpenDeepSearch；AI 搜索给出 Perplexica、GPT Researcher。
3. **核对兼容性**：查"API 代理支持"表，Perplexica 支持 Antigravity 代理，OpenDeepSearch 需要 OpenAI Key。
4. **组合工作流**：用 Perplexica 做初步检索，把检索结果喂给 GPT Researcher 做深度报告，最后用 Antigravity Manager 统一管理 API 凭据。
5. **回查时效**：执行前回到每个工具的原始 GitHub 仓库，确认 Stars、版本、维护状态仍然有效。

这个流程的关键在于"先查分类表，再查兼容性表，最后回原始仓库核对"——Awesome Skills 提供入口，决策仍需原始数据支撑。

---

## 实用技巧

### 如何选择 AI 工具

1. **明确需求**：编程、搜索、创作、自动化四类先选一类。
2. **检查兼容性**：是否支持 Antigravity 代理，决定凭据管理复杂度。
3. **评估成本**：免费额度与付费档位的边界。
4. **考虑隐私**：本地部署与云服务的数据流向差异。

### Antigravity 集成推荐组合

| 场景 | 推荐组合 |
|------|----------|
| 日常编程 | Claude Code + Cline + Aider |
| 深度研究 | Perplexica + GPT Researcher |
| 内容创作 | Suno + Runway + Gamma |
| 自动化工作流 | n8n + AutoGPT |

---

## 采用建议

这个仓库定位在索引层，执行层需要回到各工具本身。采用顺序分三步：

1. **入门阶段**：先装 Antigravity Manager 和 claude-code 或 gemini-cli，跑通一个编程工作流，熟悉插件市场机制。
2. **扩展阶段**：按需求分类逐个翻 Awesome Skills 清单，把候选工具加入 Antigravity Manager 的 API 路由。
3. **维护阶段**：定期回查仓库更新，关注 sickn33 的提交记录，因为单人维护意味着收录标准和分类口径可能随时调整。

适用边界：仓库适合做工具发现和初步筛选；涉及生产部署、合规审查、安全评估时，回到每个工具的官方文档和原始仓库做二次确认。仓库数据有快照属性，引用前核对时间戳。

---

## 自测题

1. **Antigravity Awesome Skills 和 Antigravity Tools 的关系是什么？**
   - 参考答案：Awesome Skills 是工具索引（解决"调什么"），Antigravity Tools 是代理平台（解决"如何调用"），两者通过插件市场衔接。

2. **为什么仓库里的 Stars 数据会过时？**
   - 参考答案：文章撰写时快照的数据，随着时间推移，工具的 Stars、版本、维护状态会变化，需要回到原始仓库核对。

3. **如果你需要做一个"技术调研报告自动化"的工作流，你会如何从 Awesome Skills 入手？**
   - 参考答案：先在仓库 README 里找"Autonomous Research"和"AI 搜索"分类 → 筛选工具 → 核对兼容性 → 组合工作流 → 回查时效。

4. **本地部署 AI 工具和云端 SaaS 工具的选择标准是什么？**
   - 参考答案：本地部署（Ollama、LocalAI）适合对数据隐私有要求、需要定制的场景；云端 SaaS（ChatGPT、Claude）适合快速上手、不想维护基础设施的场景。

5. **Antigravity Tools 的"API 代理"功能解决了什么问题？**
   - 参考答案：统一管理多个 AI 工具的 API 凭据，避免在每个工具里单独配置 Key，便于在多账号环境下隔离插件配置。

---

## 进阶路径

### 阶段一：工具发现（1-2 周）
- 目标：熟悉 Awesome Skills 的分类体系和 Antigravity Tools 的插件市场
- 行动：浏览 12 大分类，挑选 3-5 个与当前工作相关的工具，安装试用
- 验收：能独立从分类表定位工具，并成功安装一个插件

### 阶段二：工作流组合（2-4 周）
- 目标：把多个工具串成可重复执行的工作流
- 行动：参考"任务流案例"章节，设计一个自己的自动化场景（如代码审查、技术调研、内容生成）
- 验收：能用 Antigravity Manager 管理 2+ 个工具的 API 凭据，并跑通一个完整任务流

### 阶段三：工具评估与贡献（1-2 个月）
- 目标：从"使用者"进阶到"评估者"，并能贡献新工具
- 行动：对每个使用的工具做深度评估（Stars 趋势、Issue 响应速度、文档质量），尝试提交一个新工具到 Awesome Skills（提 PR）
- 验收：能写出一份工具评估报告，并成功贡献一个工具到仓库

### 阶段四：生态建设（长期）
- 目标：参与 Antigravity 生态建设，开发自己的插件或工具集
- 行动：阅读 Antigravity Tools 的插件开发文档，开发一个解决自己痛点的插件，分享到社区
- 验收：开发出可被他人安装的插件，并获得至少 10 个 Stars

**进阶资源**：
- [Antigravity Tools 插件开发文档](https://github.com/sickn33/antigravity-tools)
- [Awesome Skills 贡献指南](https://github.com/sickn33/antigravity-awesome-skills/blob/main/CONTRIBUTING.md)
- [Agent Skills 协议规范](https://github.com/agent-skills/agent-skills)

---

## 常见问题

### Q1: Awesome Skills 里的工具都是免费的吗？
**A**: 不一定。仓库收录的是工具链接，不是工具本身。很多工具（如 ChatGPT、Claude）有免费额度，但高级功能需要付费。本地部署工具（如 Ollama）本身免费，但需要硬件资源。

### Q2: 为什么有些工具标注为"精选"而没有 Stars 数据？
**A**: "精选"表示仓库维护者认可该工具的价值，但可能因为工具较新、闭源、或不以 GitHub 为主要平台，导致缺少公开的 Stars 数据。这类工具需要更多手动调研。

### Q3: Antigravity Tools 和直接使用 API Key 有什么区别？
**A**: Antigravity Tools 提供统一的 API 路由和账号管理，可以在多个工具间共享凭据、设置配额、切换账号。直接使用 API Key 更简单，但难以管理多个工具和多个账号的场景。

### Q4: 这个仓库适合生产环境使用吗？
**A**: 仓库定位在索引层，不适合直接用于生产环境。生产环境需要：1) 回到每个工具的官方文档核实；2) 做安全评估（特别是闭源 SaaS）；3) 验证工具的 SLA 和支持情况。

### Q5: 如何判断一个工具是否值得长期使用？
**A**: 看四个指标：1) Stars 增长趋势（是否持续活跃）；2) Issue 响应速度（维护者是否积极）；3) 文档质量（是否有清晰的 API 文档和示例）；4) 社区规模（是否有活跃的讨论群体）。

---

🦞
