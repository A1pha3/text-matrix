---
title: "JetBrains Go Modern Guidelines：让 AI 智能体写出现代 Go"
date: 2026-09-04T03:27:35+08:00
slug: "jetbrains-go-modern-guidelines"
github_repo: "JetBrains/go-modern-guidelines"
source_key: "gh:JetBrains/go-modern-guidelines"
description: "JetBrains 发布的 go-modern-guidelines 是一份面向代码智能体的 Go 编码规范，针对训练数据滞后与频率偏置两大病根，让 agent 按项目 go.mod 版本使用现代 Go 语法。本文拆解其动机、机制与在 Junie、Claude Code、Codex、Cursor 中的接入方式。"
draft: false
categories: ["技术笔记"]
tags: ["Go", "AI Agent", "JetBrains", "编码规范", "LLM"]
---

## 核心判断

代码智能体写出的 Go 总带着"上一个时代的味道"：能写出 `for i := range n` 却默认输出 `for i := 0; i < n; i++`，会写 `errors.AsType[T]`（Go 1.26）却因为没在训练数据里见过而退回到 `errors.As`。JetBrains 的 go-modern-guidelines 把这个问题拆成两个可解释的根因——训练数据滞后（training data lag）和频率偏置（frequency bias）——然后用一份显式规范给 agent 补上参考。

截至本文写作时，项目 GitHub 3.1k stars，Apache-2.0 许可，官方 JetBrains 项目。覆盖 Go 1.0 到 1.27 的最有用特性，与 `modernize` 分析器目标一致。

## 病根：为什么 agent 总写老 Go

**训练数据滞后**：模型训练截止点之后的特性它没见过，自然用不出来。Go 1.26 的 `errors.AsType[T]`、`new(42)` 取指针这类新语法，在模型知识里是空白。

**频率偏置**：即使模型认识新特性，训练语料里老写法的样本量远大于新写法，采样时老写法更容易"冒出来"。`for i := range n` 在数据里比 `for i := 0; i < n; i++` 少得多，所以模型倾向输出后者。

两条原因叠加，agent 写出的代码自然偏保守。规范的价值在于把"应该怎么写"从隐性知识变成显式参考。

## 机制：规范如何起作用

核心思路是**版本感知**：agent 先读项目的 `go.mod` 确定 Go 版本，再只使用该版本及之前可用的语言特性和标准库能力，优先现代惯用法。

覆盖的具体模式包括：

- `max(a, b)` 取代 if-else 比较
- `slices.Contains` 取代手写循环遍历
- `cmp.Or(a, b, c)` 取代一串 nil 检查
- `new(42)` 直接取指向值的指针（Go 1.26）
- `errors.AsType[T](err)` 类型安全的错误匹配（Go 1.26）
- `for i := range n` 取代 `for i := 0; i < n; i++`

这些与 Go 官方 `modernize` 分析器的目标一致——`modernize` 负责改造存量代码，这份规范让 agent 从源头写出新代码，减少日后返工。

## 接入方式

规范以 marketplace/plugin 形式分发，官方支持四个入口：

### Junie（JetBrains 自家）

```
/extensions marketplace add JetBrains/go-modern-guidelines
/extensions install modern-go-guidelines
```

### Claude Code

```
/plugin marketplace add JetBrains/go-modern-guidelines
/plugin install modern-go-guidelines@goland-claude-marketplace
```

安装后遇到 Go 任务自动触发，也可显式 `/modern-go-guidelines:use-modern-go` 调用。

### Codex

```
codex plugin marketplace add JetBrains/go-modern-guidelines
codex plugin add modern-go-guidelines@goland-codex-marketplace
```

### Cursor

```
cursor-agent plugin marketplace add https://github.com/JetBrains/go-modern-guidelines
```

然后在 Cursor 会话里 `/plugins` 安装。

其他 agent（OpenCode 等）走 skills.sh：

```bash
npx skills add JetBrains/go-modern-guidelines
```

## 实现细节

- **要求 Go 工具链**：首次使用 `go install` 安装一个小 CLI，缓存到 `~/.cache/go-modern-guidelines`，不修改项目
- **目标 Go 1.25+**：老版本 Go 只要开启自动工具链切换（`GOTOOLCHAIN=auto`，默认开启）也能工作
- **本地开发**：`make dev-install` 构建到缓存，设 `GO_MODERN_GUIDELINES_DEV=1` 让 agent 用本地构建版
- **完整特性清单**：见仓库 `FEATURES.md`，包含逐条说明与示例

## 适用边界

- **只解决"写得新"**：规范提升的是语法与标准库用法的新旧程度，不替代项目自身的编码规范、架构约定
- **依赖模型遵守**：规范的效力取决于 agent 是否在推理时遵循注入的上下文，弱模型可能部分忽略
- **面向 Go 代码生成场景**：对纯人工维护、不依赖 AI 生成代码的团队价值有限

## 结论

go-modern-guidelines 抓住了代码智能体一个真实而具体的痛点，并且解法克制：不是再训练模型，而是把 Go 团队的现代化方向做成一份 agent 可消费的规范，随版本感知自动适配项目。对重度使用 AI 写 Go 的团队，这是一份几乎零成本的"代码生成质量基线"；对正在选型 agent 规范体系的团队，它的"版本感知 + marketplace 分发"模式也值得借鉴。
