---
title: "CLIProxyAPI 旧稿说明：内容已并入新版完整指南"
date: "2026-04-12T18:00:00+08:00"
slug: cliproxyapi-openai-compatible-api-proxy-guide
description: "这篇早期 CLIProxyAPI 文章的主要内容已并入新版完整指南。由于项目迭代较快，旧稿中的支持列表、端口和部署细节可能已经过时，请直接阅读新版。"
draft: false
categories: ["技术笔记"]
tags: ["CLIProxyAPI", "更新说明", "Claude Code", "Gemini CLI", "OpenAI Codex"]
---

这是一篇保留旧链接的说明页。

CLIProxyAPI 的完整分析、部署路径、OAuth 与多账号机制、客户端接入、管理面与生态梳理，已经统一并入新版文章：

- [CLIProxyAPI：把 Claude Code、Gemini CLI、Codex 和 Grok 接成统一 API 的完整指南]({{< relref "posts/tech/cliproxyapi-unified-ai-cli-proxy.md" >}})

保留这篇旧稿，主要是为了不让原有链接直接失效；但如果你现在准备上手 CLIProxyAPI，请不要再把这篇文章当成主文。

原因很简单：CLIProxyAPI 迭代速度很快，早期文章里的支持列表、管理能力、默认端口、统计方式和部署细节，可能已经和当前版本不一致。尤其是这类项目，最容易过期的不是概念判断，而是“具体该怎么配”“哪些功能还内建”“哪些端点已经调整”这些细节。

更稳的阅读顺序是：

1. 先读新版完整指南，理解它在系统里的真实定位。
2. 再看项目当前 README、`config.example.yaml` 和官方手册。
3. 真要自动化接入时，再去翻 Management API 文档或 SDK 文档。

如果你是从旧链接进入这篇文章，直接跳到新版即可；它已经把旧稿里仍有价值的安装、认证、接入和生态材料重新整理过，同时去掉了版本漂移明显的部分。
