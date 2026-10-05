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

代码智能体写出的 Go 总带着"上一个时代的味道"：能写出 `for i := range n` 却默认输出 `for i := 0; i < n; i++`，会写 `errors.AsType[T]`（Go 1.26）却因为没在训练数据里见过而退回到 `errors.As`。JetBrains 的 go-modern-guidelines 把这个问题拆成两个根因——训练数据滞后（training data lag）和频率偏置（frequency bias）——然后用一份显式规范给 agent 补上参考。

两条主线一句话分清：**病根在模型侧**（语料旧、老写法多），**对策在上下文侧**（不重训模型，往 agent 的上下文里注入一份版本感知的规范）。

| 病根 | 典型表现 | 规范的对策 |
| --- | --- | --- |
| 训练数据滞后 | 没见过 Go 1.26 的 `errors.AsType[T]`，退回 `errors.As` | 把 Go 1.0–1.27 的关键特性列成清单，补齐知识空白 |
| 频率偏置 | 语料里 `for i := 0; i < n; i++` 远多于 `for i := range n`，采样偏向老写法 | 明确要求优先现代惯用法，压过频率直觉 |

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

## 一次任务的完整路径

以 Claude Code 为例，假设项目 `go.mod` 声明 `go 1.25`，开发者让它写一个"在用户列表里找管理员"的函数。

规范随 Go 任务自动加载后，agent 先读 `go.mod` 确认版本是 1.25，于是落笔时用 `slices.Contains`（Go 1.21 引入）而不是手写循环，用 `for i := range n`（Go 1.22）而不是三段式计数循环——但不会写出 `errors.AsType[T]`，因为那是 1.26 才有的。同一个项目升级到 `go 1.26` 后重跑同样的任务，agent 才会用上 `errors.AsType[T]` 和 `new(42)`。

版本感知的意义就在这里：同一个 agent，面对不同的 `go.mod`，产出不同新旧程度的代码，不会把 1.26 语法塞进 1.25 的项目导致编译失败。

## 接入方式

仓库 Apache-2.0 许可，JetBrains 官方项目，2026 年 9 月底 3.7k stars。规范以 marketplace/plugin 形式分发，官方支持四个入口。

### Junie（JetBrains 自家）

在 Junie CLI 会话内执行：

```text
/extensions marketplace add JetBrains/go-modern-guidelines
/extensions install modern-go-guidelines
```

遇到 Go 任务自动触发。更新用 `/extensions update modern-go-guidelines`。

### Claude Code

在 Claude Code 会话内执行：

```text
/plugin marketplace add JetBrains/go-modern-guidelines
/plugin install modern-go-guidelines@goland-claude-marketplace
```

安装后遇到 Go 任务自动触发，也可显式 `/modern-go-guidelines:use-modern-go` 调用。

有个容易踩的坑：第三方 marketplace 的自动更新默认关闭，需要跑一次 `/plugin`，进入 Marketplaces 选中 `goland-claude-marketplace`，开启 Enable auto-update；此后插件更新了，还要 `/reload-plugins` 才会应用到当前会话。也可以在终端手动更新：

```bash
claude plugin marketplace update goland-claude-marketplace
claude plugin update modern-go-guidelines@goland-claude-marketplace
```

### Codex

在终端执行：

```bash
codex plugin marketplace add JetBrains/go-modern-guidelines
codex plugin add modern-go-guidelines@goland-codex-marketplace
```

更新时刷新 marketplace 后需要删掉重装，Codex 才会替换本地缓存的副本：

```bash
codex plugin marketplace upgrade goland-codex-marketplace
codex plugin remove modern-go-guidelines@goland-codex-marketplace
codex plugin add modern-go-guidelines@goland-codex-marketplace
```

### Cursor

在终端执行：

```bash
cursor-agent plugin marketplace add https://github.com/JetBrains/go-modern-guidelines
```

然后在 Cursor 会话里 `/plugins` 安装。更新先执行 `cursor-agent plugin marketplace update goland-cursor-marketplace`，若插件还停在旧版本，用 `/plugins` 重装——Cursor 目前没有非交互的插件更新命令。

### 其他 agent（OpenCode 等）

走 skills.sh，同一份 skill 包跨 agent 复用：

```bash
npx skills add JetBrains/go-modern-guidelines
```

加 `--skill use-modern-go` 参数可以只安装这一个 skill。更新项目级安装用 `npx skills update use-modern-go -p -y`，全局安装把 `-p` 换成 `-g`。

## 实现细节

- **要求 Go 工具链**：marketplace 集成首次使用时会用 `go install` 安装一个小 CLI，因此 Go 工具链必须装好并在 `PATH` 上；CLI 缓存在 `$XDG_CACHE_HOME/go-modern-guidelines`（默认 `~/.cache/go-modern-guidelines`），从不修改项目
- **目标 Go 1.25+**：老版本 Go 只要开启自动工具链切换（`GOTOOLCHAIN=auto`，默认开启）也能工作，首次运行时 Go 会自行拉取兼容工具链
- **本地开发**：`make dev-install` 构建到缓存，在 agent 运行环境设 `GO_MODERN_GUIDELINES_DEV=1`（启动 agent 前导出），agent 就会用本地构建版；改完 CLI 重新 `make dev-install` 即可，卸载用 `make dev-uninstall`
- **完整特性清单**：见仓库 `FEATURES.md`，包含逐条说明与示例

## 适用边界

- **只解决"写得新"**：规范提升的是语法与标准库用法的新旧程度，不替代项目自身的编码规范、架构约定
- **依赖模型遵守**：规范的效力取决于 agent 是否在推理时遵循注入的上下文，弱模型可能部分忽略
- **面向 Go 代码生成场景**：对纯人工维护、不依赖 AI 生成代码的团队价值有限

## 结论

go-modern-guidelines 抓住了代码智能体一个真实而具体的痛点，并且解法克制：不是再训练模型，而是把 Go 团队的现代化方向做成一份 agent 可消费的规范，随版本感知自动适配项目。对重度使用 AI 写 Go 的团队，这是一份几乎零成本的"代码生成质量基线"；对正在选型 agent 规范体系的团队，它的"版本感知 + marketplace 分发"模式也值得借鉴。
