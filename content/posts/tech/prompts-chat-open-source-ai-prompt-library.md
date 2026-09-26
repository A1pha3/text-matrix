---
title: "prompts.chat 解读：17 万 Star 开源提示词库怎么用"
date: "2026-04-30T20:00:00+08:00"
lastmod: "2026-09-23T12:00:00+08:00"
slug: prompts-chat-open-source-ai-prompt-library
github_repo: "f/prompts.chat"
source_key: "gh:f/prompts.chat"
description: "prompts.chat（前身 Awesome ChatGPT Prompts）是 GitHub 17 万 Star 的开源提示词库。本文梳理它的四种用法（网页、CLI、Claude Code 插件、MCP）、库内数据结构、双许可证与自托管部署。"
draft: false
categories: ["技术笔记"]
tags: ["ChatGPT", "Prompt Engineering", "开源", "MCP"]
---

# prompts.chat 解读：17 万 Star 开源提示词库怎么用

## 它是什么

[prompts.chat](https://prompts.chat) 前身是 **Awesome ChatGPT Prompts**，仓库创建于 2022 年 12 月 5 日，是提示词工程领域最早的开源集合之一。作者 Fatih Kadir Akın（GitHub 用户名 [f](https://github.com/f)）是 WordPress/Automattic 的开发者布道师，也是 GitHub Stars 项目成员。截至 2026 年 9 月 23 日，仓库有 170,992 个 Star、约 2.2 万个 Fork（GitHub API 实测），README 自称"全球最大的开源提示词库"。

这个体量带来的是一整套背书，README 页面都给了出处：Forbes 在 2023 年 1 月报道过它；哈佛大学 IT 部门和哥伦比亚大学的教学指南引用了它；Google Scholar 上有 40 多篇论文引用；Hugging Face 上同名数据集是最受喜欢的数据集之一；GitHub 官方 Staff Pick 也收录了它。OpenAI 联合创始人 Greg Brockman 和 Wojciech Zaremba、Hugging Face CEO Clement Delangue、前 GitHub CEO Thomas Dohmke 都在 X 上公开提过这个项目。

比背书更值得注意的是另一件事：今天提示词写作里最常见的"I want you to act as a ..."（扮演某个角色）开头，正是从这个仓库推广开的。它把"给 AI 分配角色 + 约束输出格式 + 给出第一句话"固定成了可复制的模板，后来的提示词库大多沿用了这个写法。

## 四种使用方式

### 网页直接用

最省事的入口是 [prompts.chat/prompts](https://prompts.chat/prompts)，按分类浏览，选中后复制到任意对话模型里。提示词原文对模型没有偏好，ChatGPT、Claude、Gemini、Llama、Mistral 都能用——README 首页也按这个口径列了支持模型。

### CLI 命令行工具

```bash
npx prompts.chat
```

启动一个终端交互界面，可以搜索、浏览提示词，适合不想离开终端的开发者。

### Claude Code 插件

项目提供官方 Claude Code 插件，安装分两步（在 Claude Code 会话里执行）：

```text
/plugin marketplace add f/prompts.chat
/plugin install prompts.chat@prompts.chat
```

装上之后不只有搜索：`/prompts.chat:prompts <关键词>` 直接搜提示词，`/prompts.chat:skills <关键词>` 搜技能，两者都支持 `--type IMAGE`、`--category coding`、`--tag productivity` 这类过滤参数；另有 Prompt Manager 和 Skill Manager 两个 Agent 处理多步骤任务。细节见仓库的 [CLAUDE-PLUGIN.md](https://github.com/f/prompts.chat/blob/HEAD/CLAUDE-PLUGIN.md)。

### MCP 服务器

prompts.chat 也可以作为 [MCP](https://prompts.chat/docs/api)（Model Context Protocol）服务器接入任意支持该协议的工具。远程模式只要一个 URL：

```json
{
  "mcpServers": {
    "prompts.chat": {
      "url": "https://prompts.chat/api/mcp"
    }
  }
}
```

本地模式走 npx：

```json
{
  "mcpServers": {
    "prompts.chat": {
      "command": "npx",
      "args": ["-y", "prompts.chat", "mcp"]
    }
  }
}
```

## 库里有什么

### 数据规模与格式

仓库主文件 [prompts.csv](https://github.com/f/prompts.chat/blob/HEAD/prompts.csv) 收录 2,169 条提示词（2026 年 9 月 23 日导出统计），`type` 字段分三类：纯文本提示词 1,836 条、结构化提示词 312 条、图像提示词 21 条。数据同时发布在 [Hugging Face](https://huggingface.co/datasets/fka/prompts.chat) 和全量 Markdown 文件 [PROMPTS.md](https://raw.githubusercontent.com/f/prompts.chat/main/PROMPTS.md) 里，方便直接喂给程序。

提示词里的占位符有自己的约定：`${变量名}` 或 `${变量名:默认值}`，例如面试官提示词里的 `${Position:Software Developer}`。网站还能识别 `[[name]]`、`{{name}}`、`[NAME]`、`%name%` 这些常见写法并自动转换成统一格式（源码 `src/lib/variable-detection.ts`），所以从别处抄来的提示词不用手工改占位符。

### 分类

线上分类页（[prompts.chat/categories](https://prompts.chat/categories)）有 44 个主题分类，粒度比早期版本细得多。2026 年 9 月下旬各分类的量级大致是：图像生成（Image Generation）410 条最多，其后是 Vibe Coding 103 条、Web 开发 93 条、Agent Skill 88 条、营销 38 条、设计 36 条、视频生成 35 条、数据科学 29 条。写作、教育、商业、效率、健康等场景也各有独立分类。

### 一条提示词长什么样

以库里最早的 Linux Terminal 提示词为例，写法是三段式：先指定角色（"I want you to act as a linux terminal"），再约束输出（只回复终端输出、放在代码块里、不解释），最后用一句 `my first command is pwd` 启动对话。这套结构简单，但把"AI 应该怎么响应"交代得足够具体，是库里大多数提示词的共同骨架。

## 配套的免费教程

项目配套了一本免费的交互式提示词教程 [The Interactive Book of Prompting](https://fka.gumroad.com/l/art-of-chatgpt-prompting)，25 个以上章节，从基础写法讲到 Chain-of-Thought（思维链）、Few-Shot Learning（少样本学习）和 AI Agent。教程源码就在仓库的 `src/content/book` 目录，MIT 许可证适用。

## 自托管部署

自托管是企业内部提示词库的主要用法：数据不出内网，品牌和分类可以定制。

### 快速开始

```bash
npx prompts.chat new my-prompt-library
cd my-prompt-library
```

### 手动安装

```bash
git clone https://github.com/f/prompts.chat.git
cd prompts.chat
npm install && npm run setup
```

设置向导会配置品牌、主题、登录方式（GitHub / Google / Azure AD）和功能开关。

### 部署后可以调什么

- **数据库**：PostgreSQL，README 推荐 Neon 的托管实例。
- **运行时定制**：Docker 部署可以通过 `PCHAT_` 前缀的环境变量覆盖配置（站点名称、主题色、登录方式、功能开关等），改配置不需要重新构建镜像。
- **功能开关**：私有提示词、变更请求、分类、标签、评论默认开启，AI 搜索和 AI 生成默认关闭，都可以按需切换。
- **文档**：完整指南见 [SELF-HOSTING.md](https://github.com/f/prompts.chat/blob/HEAD/SELF-HOSTING.md) 和 [DOCKER.md](https://github.com/f/prompts.chat/blob/HEAD/DOCKER.md)。

## 贡献与许可

提交提示词有两个入口：网页 [prompts.chat/prompts/new](https://prompts.chat/prompts/new) 填表后自动同步到 GitHub 仓库；或者走常规的 GitHub PR。

许可证分两块，用途不同时要看清楚：

| 内容 | 许可证 | 意味着 |
|------|--------|--------|
| 源代码和站点自有内容（含教程） | MIT | 可自由使用、修改、商用，保留版权声明即可 |
| 提示词数据（prompts.csv、PROMPTS.md、用户提交） | CC0 1.0 | 公有领域，无需署名，可商用 |

提示词内容按 CC0 发布，做商业产品不用操心版权链路，这是它对比很多提示词站点的实际优势。

## Kids 专区

[prompts.chat/kids](https://prompts.chat/kids) 是给 8 到 14 岁孩子的游戏化 AI 入门：用谜题和互动故事练习"怎么把话说清楚"，角色叫 Promi。做成了闯关形式，成人陪同使用更稳妥。

## 采用建议

- **找提示词直接用**：网页搜索就够了，分类粒度细，复制即走。
- **团队内部建提示词库**：自托管是正经卖点，双许可证扫清了合规障碍，`PCHAT_` 环境变量降低了运维成本。
- **给 Agent 工具接数据源**：MCP 服务器和 Claude Code 插件让提示词检索嵌进工作流，不用切窗口。
- **想学提示词工程**：先读配套教程，再用库里的提示词对照着改——库由社区贡献，质量有高有低，照单全收不如挑着看。
- **介意数字时效的读者**：Star 数、分类数量这类数字随时间变化，以 GitHub API 和官网实时数据为准。

## 自测题

1. **prompts.chat 的前身是什么？**
   <details>
   <summary>点击查看答案</summary>
   Awesome ChatGPT Prompts，仓库创建于 2022 年 12 月。
   </details>

2. **提示词里的变量怎么写？**
   <details>
   <summary>点击查看答案</summary>
   `${变量名}` 或 `${变量名:默认值}`；`{{name}}`、`[[name]]` 等常见写法会被网站自动转换。
   </details>

3. **两种许可证各管什么？**
   <details>
   <summary>点击查看答案</summary>
   源代码和站点自有内容（含教程）用 MIT；提示词数据（prompts.csv、PROMPTS.md、用户提交）用 CC0 1.0，进入公有领域，无需署名。
   </details>

4. **MCP 远程模式的接入点是什么？**
   <details>
   <summary>点击查看答案</summary>
   `https://prompts.chat/api/mcp`，配置在工具的 `mcpServers` 里；本地模式用 `npx -y prompts.chat mcp`。
   </details>

5. **自托管用什么数据库？**
   <details>
   <summary>点击查看答案</summary>
   PostgreSQL，README 推荐 Neon 托管实例；Docker 部署可用 `PCHAT_` 环境变量做运行时定制。
   </details>

## 练习

### 练习 1：用 CLI 搜一条提示词

1. 运行 `npx prompts.chat`，在交互界面里搜索 "code review"
2. 挑一条提示词，注意它的 `${变量}` 占位符，换成你自己的场景
3. 粘贴到任意对话模型里，观察输出是否符合提示词的约束

### 练习 2：接入 MCP 服务器

1. 在 Claude Desktop 的 MCP 配置里加上远程模式（URL 见自测题第 4 题）
2. 重启后用自然语言让它"搜一条关于写作的提示词"，确认数据来自 prompts.chat

### 练习 3：跑一个自托管实例

1. `git clone https://github.com/f/prompts.chat.git && cd prompts.chat`
2. `npm install && npm run setup`，跟着向导完成配置
3. 启动后试着改一个 `PCHAT_` 环境变量，观察配置如何生效

## 进阶路径

1. **读教程**：[The Interactive Book of Prompting](https://fka.gumroad.com/l/art-of-chatgpt-prompting)，重点看 Chain-of-Thought 和 Few-Shot 两章
2. **拆结构**：挑 10 条同一分类的高赞提示词，对比它们的角色定义和输出约束写法
3. **读源码**：`src/lib/variable-detection.ts` 展示了变量识别的工程实现，`src/lib/similarity.ts` 是相似提示词的去重逻辑
4. **搭私库**：按 SELF-HOSTING.md 部署，再对照 `src/lib/config/index.ts` 把功能开关调成团队需要的形态
5. **学协议**：如果要在自有产品里接 MCP，参考仓库的 MCP 实现和 [API 文档](https://prompts.chat/docs/api)

## 相关资源

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | [github.com/f/prompts.chat](https://github.com/f/prompts.chat) |
| 在线浏览 | [prompts.chat](https://prompts.chat) |
| 分类页 | [prompts.chat/categories](https://prompts.chat/categories) |
| Hugging Face 数据集 | [huggingface.co/datasets/fka/prompts.chat](https://huggingface.co/datasets/fka/prompts.chat) |
| DeepWiki 问答 | [deepwiki.com/f/prompts.chat](https://deepwiki.com/f/prompts.chat) |
| 提示词教程 | [fka.gumroad.com/l/art-of-chatgpt-prompting](https://fka.gumroad.com/l/art-of-chatgpt-prompting) |
| Kids 专区 | [prompts.chat/kids](https://prompts.chat/kids) |

## 结语

prompts.chat 的价值分两层。历史层面，它把"Act as ..."写成模板并推广开，是 2022 年底那波提示词热潮里留存下来的少数项目。实用层面，它今天仍然在维护：数据每周在更新，CLI、插件、MCP 三条接入路径覆盖了从个人到团队再到 Agent 工作流的场景，CC0 许可证让数据可以放心拿去用。要挑毛病，社区贡献的提示词质量参差，老提示词对新模型未必还是最优写法——把它当素材库和参考实现，而不是标准答案，是更合适的用法。
