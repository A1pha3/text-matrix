---
title: "Harper：用 Rust 重写的本地隐私语法检查器"
date: 2026-07-24T03:00:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["Rust", "Grammar Checker", "Privacy", "LSP", "WASM"]
description: "Automattic 出品的开源语法检查器，用 Rust 实现全部规则引擎，数据不出本机，内存占用仅为 LanguageTool 的五十分之一。"
---

## 为什么值得看

语法检查这个领域长期被两个名字占据：Grammarly 和 LanguageTool。前者是闭源 SaaS，你敲的每一个字符都会发到它的服务器；后者是 Java 开源项目，虽然可以本地部署，但完整运行需要约 16GB 内存来加载 n-gram 数据集。

Harper 是 Automattic（WordPress 母公司）用 Rust 从头写的第三个选择。它的核心判断是：**语法检查不应该是云服务，也不应该吃掉你一半的内存。**

这个判断值得认真看一看，因为它代表了"用工程语言重新解决一个被认为已经定型的问题"的思路。

## 核心能力速览

| 维度 | Harper | Grammarly | LanguageTool |
|------|--------|-----------|--------------|
| 隐私 | 完全本地 | 数据上传服务器 | 可本地部署 |
| 内存 | ~数十 MB | N/A（云端） | ~16GB（含 n-gram） |
| 延迟 | 毫秒级 | 依赖网络 RTT | 数秒级 |
| 语言 | 仅英语 | 多语言 | 30+ 语言 |
| 架构 | Rust + WASM | 云端 SaaS | Java |

Harper 目前的局限很明确：**只支持英语**。README 中也坦诚说明了这一点，并表示核心引擎是可扩展的，欢迎其他语言的贡献。

## 技术架构

Harper 的技术栈由三层构成：

**规则引擎（Rust）**：所有语法规则用 Rust 实现，编译为原生机器码执行。这是它能做到毫秒级响应的关键——没有 JVM 预热，没有 GC 停顿，没有网络往返。

**Language Server（`harper-ls`）**：实现了 Language Server Protocol，这意味着它可以接入任何遵循 LSP 标准的编辑器。目前官方文档列出了 VS Code、Neovim、Helix、Emacs、Zed 的集成指南。

**WASM 前端（`harper.js`）**：整个引擎可以编译为 WebAssembly，在浏览器中直接运行。Automattic 的在线写作平台 [writewithharper.com](https://writewithharper.com) 就是这个方案的实例——你的文本永远不会离开浏览器。

### 分发形态

Harper 的分发覆盖了多个层次：

- **Crates.io**：`harper-ls` 作为 Rust crate 发布，可以集成到任何 Rust 项目中
- **NPM**：`harper.js` 面向 JavaScript/TypeScript 生态
- **Obsidian 插件**：直接在 Obsidian 笔记应用中使用
- **二进制下载**：GitHub Releases 提供 macOS / Linux / Windows 预编译二进制

这种多层级分发策略让 Harper 能够覆盖从终端用户到开发者的完整链路。

## 与 LanguageTool 的工程取舍

Harper 的作者在 README 中花了不少篇幅解释为什么不用 LanguageTool。核心矛盾不在"能不能用"，而在"工程上是否合理"：

1. **内存成本**：LanguageTool 的 n-gram 数据集约 16GB，这对大多数开发者的机器来说是一个沉重的负担。Harper 选择用规则引擎而非统计模型，把内存压到几十 MB 的量级。

2. **速度成本**：LanguageTool 对中等长度文档的检查需要数秒。在一个实时编辑器里，这意味着每次按键后的反馈都有可感知的延迟。Harper 的 Rust 原生引擎把这个延迟压到毫秒级。

3. **隐私成本**：这是 Harper 最根本的设计约束。Grammarly 把用户文本上传服务器来训练模型，这在隐私敏感场景（企业文档、个人通信、医疗记录）是不可接受的。Harper 的所有检查都在本地完成，数据零外传。

这个取舍也有代价：Harper 目前只支持英语，且规则引擎的覆盖面不如经过大规模统计训练的模型。它选择了一个明确的位置——**快、小、私密，但暂时只覆盖英语**。

## 快速上手

如果你用的是 VS Code，最简单的方式是安装 Harper 扩展。安装后打开任何 Markdown 或文本文档，它就会自动开始检查。

对于 Neovim / Helix / Emacs / Zed 用户，配置 `harper-ls` 作为 LSP 服务器即可。具体步骤参考 [官方集成文档](https://writewithharper.com/docs/integrations/language-server)。

如果你想在自己的 Web 应用中使用，通过 NPM 安装 `harper.js`：

```bash
npm install harper.js
```

然后在 JavaScript 中调用 WASM 引擎进行检查——整个过程在浏览器内完成，无需后端 API。

## 适用边界

**适合**：

- 隐私敏感场景下的英语写作（企业、法律、医疗）
- 嵌入到 Web 应用中作为内置语法检查（通过 WASM）
- 在 Obsidian / VS Code / Neovim 等本地编辑器中替代 Grammarly
- 对启动速度和内存占用敏感的环境

**不适合**：

- 需要非英语语法检查的场景（目前仅支持英语）
- 需要 Grammarly 级别的风格建议和语气调整（Harper 专注于语法正确性）
- 需要统计型 NLP 能力（如上下文语义消歧）的场景

## 阅读路径

- [GitHub 仓库](https://github.com/Automattic/harper) — 源码和文档
- [writewithharper.com](https://writewithharper.com) — 在线试用 + 官方文档
- [Discord 社区](https://discord.com/invite/JBqcAaKrzQ) — 问题讨论和贡献指南
