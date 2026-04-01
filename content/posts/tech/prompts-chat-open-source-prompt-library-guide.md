---
title: "Prompts.chat：全球最大开源提示词库完全指南"
date: 2026-04-02T01:37:00+08:00
slug: prompts-chat-open-source-prompt-library-guide
categories: ["技术笔记"]
tags: ["Prompts.chat", "提示词库", "AI", "Claude", "ChatGPT", "开源"]
description: "Prompts.chat 全球最大开源提示词库完全指南，涵盖提示词库浏览、互动书籍、儿童提示工程、自托管部署、CLI/Claude Code/MCP集成，从入门到精通的全方位讲解。"
---
# Prompts.chat：全球最大开源提示词库完全指南

## 一、项目概述

### 1.1 什么是 Prompts.chat

**Prompts.chat**（f/prompts.chat）是全球最大的开源 AI 提示词库，前身为 Awesome ChatGPT Prompts。支持 ChatGPT、Claude、Gemini、Llama、Mistral 等主流 AI 助手。

### 1.2 关键数据

| 指标 | 数值 |
|------|------|
| **GitHub Stars** | 156,000 |
| **GitHub Forks** | 20,500 |
| **GitHub Watchers** | 1,600 |
| **贡献者** | 397 |
| **协议** | CC0 1.0 Universal (公共领域) |
| **作者** | f (Fatih Kadir Akın) |

### 1.3 核心定位

| 定位 | 说明 |
|------|------|
| **全球最大** | 开源提示词库，社区驱动 |
| **多模型支持** | ChatGPT、Claude、Gemini、Llama、Mistral |
| **免费开源** | CC0 1.0 协议，无需署名 |
| **自托管** | 支持私有化部署 |

### 1.4 荣誉认可

| 荣誉 | 来源 |
|------|------|
| **Forbes 报道** | Forbes |
| **哈佛引用** | 哈佛大学 |
| **哥伦比亚引用** | 哥伦比亚大学 |
| **40+ 学术引用** | Google Scholar |
| **Hugging Face 最受欢迎数据集** | Hugging Face |
| **GitHub Staff Pick** | GitHub 官方精选 |
| **首个提示词库** | 2022年12月 |

---

## 二、核心功能

### 2.1 提示词库浏览

| 功能 | 说明 |
|------|------|
| **浏览提示词** | prompts.chat/prompts |
| **分类浏览** | 按主题、场景、难度筛选 |
| **搜索功能** | AI 驱动的搜索和生成 |

### 2.2 提示词书籍

| 功能 | 说明 |
|------|------|
| **互动提示工程指南** | 免费，25+ 章节 |
| **链式思考推理** | Chain-of-thought reasoning |
| **少样本学习** | Few-shot learning |
| **AI Agent** | 智能体构建 |

### 2.3 儿童提示工程

| 功能 | 说明 |
|------|------|
| **Promi** | 互动游戏化冒险 |
| **目标人群** | 8-14 岁儿童 |
| **寓教于乐** | 通过谜题和故事教授 AI 沟通 |

---

## 三、数据格式

### 3.1 可用格式

| 格式 | 链接 |
|------|------|
| **CSV 文件** | prompts.csv |
| **Markdown 格式** | PROMPTS.md |
| **Hugging Face 数据集** | huggingface.co/datasets/fka/prompts.chat |

### 3.2 数据结构

提示词数据包含：
- 提示词内容
- 分类标签
- 作者信息
- 使用场景
- 适用模型

---

## 四、安装部署

### 4.1 快速开始

**方式一：NPX 一键创建**

```bash
npx prompts.chat new my-prompt-library
cd my-prompt-library
```

**方式二：手动安装**

```bash
git clone https://github.com/f/prompts.chat.git
cd prompts.chat
npm install && npm run setup
```

### 4.2 配置选项

安装向导支持配置：
- 品牌定制
- 主题选择
- 认证方式（GitHub/Google/Azure AD）
- 功能模块

### 4.3 部署文档

| 文档 | 说明 |
|------|------|
| **自托管完整指南** | SELF-HOSTING.md |
| **Docker 部署指南** | DOCKER.md |

---

## 五、集成工具

### 5.1 命令行工具

```bash
npx prompts.chat
```

### 5.2 Claude Code 插件

```bash
/plugin marketplace add f/prompts.chat
/plugin install prompts.chat@prompts.chat
```

详细文档：CLAUDE-PLUGIN.md

### 5.3 MCP 服务器

**远程模式（推荐）：**

```json
{
  "mcpServers": {
    "prompts.chat": {
      "url": "https://prompts.chat/api/mcp"
    }
  }
}
```

**本地模式：**

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

详细文档：prompts.chat/docs/api

---

## 六、项目结构

### 6.1 目录结构

| 目录 | 说明 |
|------|------|
| `.claude/` | Claude Code 配置 |
| `.claude-plugin/` | Claude 插件定义 |
| `.commandcode/` | CommandCode 集成 |
| `.windsurf/skills/` | Windsurf Skills |
| `docker/` | Docker 配置 |
| `messages/` | 多语言消息 |
| `packages/` | NPM 包 |
| `prisma/` | 数据库配置 |
| `public/` | 静态资源 |
| `scripts/` | 构建脚本 |
| `src/` | Next.js 源码 |

### 6.2 核心文件

| 文件 | 说明 |
|------|------|
| `PROMPTS.md` | 提示词 Markdown 格式 |
| `prompts.csv` | 提示词 CSV 格式 |
| `prompts.config.ts` | 提示词配置 |
| `package.json` | NPM 依赖 |

---

## 七，技术栈

### 7.1 语言构成

| 语言 | 占比 |
|------|------|
| **HTML** | 48.4% |
| **MDX** | 36.3% |
| **TypeScript** | 14.9% |
| **JavaScript** | 0.2% |
| **Shell** | 0.1% |
| **CSS** | 0.1% |

### 7.2 主要技术

| 技术 | 用途 |
|------|------|
| **Next.js** | Web 框架 |
| **Prisma** | 数据库 ORM |
| **MDX** | 提示词内容格式 |
| **Vercel** | 部署平台 |
| **Hugging Face** | 数据集托管 |

---

## 八，贡献指南

### 8.1 添加提示词

访问 prompts.chat/promrompts/new 添加新提示词，自动同步到 GitHub。

### 8.2 贡献者

| 贡献者 | 说明 |
|--------|------|
| **f** | 项目创始人 |
| **devisasari** | 核心贡献者 |
| **giorgiop** | 核心贡献者 |
| **sinansonmez** | 核心贡献者 |
| **wkaandemir** | 核心贡献者 |
| **...** | 397 位贡献者 |

### 8.3 提交规范

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修复 |
| `chore` | 维护任务 |
| `docs` | 文档更新 |
| `style` | 格式调整 |
| `refactor` | 重构 |
| `test` | 测试 |

---

## 九，常见问题

**Q1: 如何贡献提示词？**

访问 prompts.chat/prompts/new 提交，自动同步到 GitHub。

**Q2: 支持哪些 AI 模型？**

ChatGPT、Claude、Gemini、Llama、Mistral 等主流模型。

**Q3: 是否可以商用？**

可以。CC0 1.0 是公共领域协议，无需署名即可商用。

**Q4: 如何自托管？**

```bash
npx prompts.chat new my-prompt-library
cd my-prompt-library
npm run setup
```

---

## 十、项目信息

| 信息 | 内容 |
|------|------|
| 许可证 | CC0 1.0 Universal (公共领域) |
| 作者 | f (Fatih Kadir Akın) |
|  Stars | 156,000 |
| Forks | 20,500 |
| 贡献者 | 397 |

---

## 相关链接

💻 **GitHub**：[f/prompts.chat](https://github.com/f/prompts.chat)

🌐 **网站**：[prompts.chat](https://prompts.chat)

📖 **互动书籍**：[The Interactive Book of Prompting](https://fka.gumroad.com/l/art-of-chatgpt-prompting)

🎮 **儿童版**：[Prompts.chat/kids](https://prompts.chat/kids)

🤗 **Hugging Face**：[huggingface.co/datasets/fka/prompts.chat](https://huggingface.co/datasets/fka/prompts.chat)