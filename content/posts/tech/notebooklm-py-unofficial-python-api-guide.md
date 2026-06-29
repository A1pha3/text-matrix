+++
date = '2026-05-22T10:20:00+08:00'
draft = false
title = 'notebooklm-py：Google NotebookLM 非官方 Python API'
slug = 'notebooklm-py-unofficial-python-api-guide'
description = 'notebooklm-py 是 Google NotebookLM 的非官方 Python API，支持播客生成、视频处理和 Quiz 生成等自动化功能。'
categories = ['技术笔记']
tags = ['AI', 'Python', 'Google', '教程']
+++

## 学习目标

学完本文，你应该能够：

1. **部署 notebooklm-py 开发环境**：选择合道的认证方式（`--browser-cookies chrome`、交互式 `notebooklm login`、或指定浏览器 Profile），完成 Google 账号认证。
2. **使用 CLI 操作 NotebookLM**：创建 Notebook、添加来源（URL、本地文件）、基于文档问答、生成播客（Audio Overview）、生成视频、生成 Quiz 和闪卡。
3. **把 notebooklm-py 集成到 Python 应用**：用 `NotebookLM()` 类创建 Notebook、添加来源、问答、生成音视频。
4. **把 notebooklm-py 集成到 AI 智能体（Claude Code / Codex / OpenClaw）**：设计多智能体协作工作流，让 Claude Code 调用 NotebookLM 处理研究任务。
5. **评估 notebooklm-py 的适用边界**：根据你的使用场景（学术研究、竞品分析、新闻追踪等），判断 notebooklm-py 是否是最合适的工具，并知道何时应该选择官方 NotebookLM UI。

---

## 目录

- [项目概览](#项目概览)
- [快速上手](#快速上手)
- [AI 智能体集成](#ai-智能体集成)
- [核心认证机制](#核心认证机制)
- [功能对比：官方 UI vs. notebooklm-py](#功能对比官方-ui-vs-notebooklm-py)
- [注意事项与限制](#注意事项与限制)
- [相关资源](#相关资源)
- [结语](#结语)
- [学习目标](#学习目标)
- [自测题](#自测题)
- [练习](#练习)
- [进阶路径](#进阶路径)
- [资料口径说明](#资料口径说明)

---

## 项目概览

| 指标 | 数值 |
|------|------|
| **仓库** | [teng-lin/notebooklm-py](https://github.com/teng-lin/notebooklm-py) |
| **今日新增 Stars** | 🔥 今日新上榜 |
| **总 Stars** | ⭐ 14,379 |
| **主语言** | Python |
| **功能定位** | Google NotebookLM 非官方 Python SDK + CLI |
| **支持场景** | Python / CLI / Claude Code / Codex / OpenClaw 智能体 |

---

## 🔥  为什么这个项目值得关注？

Google **NotebookLM** 是 Google 实验室推出的 AI 笔记助手，最大亮点是能将任意文档（PDF、网页、音频、视频）转换为**可交互的播客**、**Quiz**、**思维导图**。它背后的 Audio Overview 功能可以将论文、技术文档变成两个 AI 主播的对话播客，在通勤时听——体验极其惊艳。

但 NotebookLM 的能力大部分只暴露在网页 UI 里，API 没有官方公开，智能体和工作流里想自动化调用非常困难。

**notebooklm-py** 填补了这个空白——一个完整的非官方 Python SDK + CLI，支持 NotebookLM 几乎所有功能：

- 📝 文档转播客（Audio Overview）
- 🎬 视频生成（白板/电影风格）
- 📋 Quiz / 闪卡生成
- 💬 基于文档的问答
- 🔑 支持 Google 账号 cookie 认证
- 🐍 纯 Python，**无需 Playwright / Chromium**（~10MB）
- 🤖 支持 Claude Code / Codex / OpenClaw 等 AI 智能体

---

## ⚡ 快速上手

### 安装

```bash
pip install notebooklm-py
```

### 认证登录

```bash
# 方式1：打开浏览器交互式登录（默认）
notebooklm login

# 方式2：使用已登录浏览器的 Cookie（无需再开浏览器）
notebooklm login --browser-cookies chrome

# 方式3：指定浏览器 Profile
notebooklm login --browser-cookies 'chrome::Profile 1'
notebooklm login --browser-cookies msedge  # 需要 Edge 的企业 SSO

# 方式4：验证认证状态
notebooklm auth check --test --json
# 期望返回: {"status": "ok"}
```

### 基本使用（CLI）

```bash
# 1. 创建 Notebook 并添加来源
notebooklm create "My Research Project"
notebooklm use <notebook_id>
notebooklm source add "https://en.wikipedia.org/wiki/Artificial_intelligence"
notebooklm source add "./paper.pdf"

# 2. 基于文档问答
notebooklm ask "What are the key themes?"
notebooklm ask --prompt-file ./long_question.txt  # 从文件读取长问题

# 3. 生成播客（Audio Overview）
notebooklm generate audio "make it engaging" --wait

# 4. 生成视频
notebooklm generate video --style whiteboard --wait
notebooklm generate cinematic-video "documentary-style summary" --wait

# 5. 生成 Quiz
notebooklm generate quiz --difficulty hard

# 6. 生成闪卡
notebooklm generate flashcards --quantity more
```

### 作为 Python 库使用（嵌入你的应用）

```python
from notebooklm import NotebookLM

nlp = NotebookLM()

# 创建 Notebook
notebook = nlp.create_notebook("Research Notes")
nlp.set_notebook(notebook['id'])

# 添加来源
nlp.add_source("https://arxiv.org/abs/2303.17760")  # 论文 URL
nlp.add_source("./document.pdf")

# 问答
answer = nlp.ask("Summarize the main contributions of this paper")
print(answer)

# 生成播客
audio = nlp.generate_audio("A 5-minute engaging podcast summary", wait=True)
print(f"Audio URL: {audio['audio_url']}")
```

---

## 🤖 AI 智能体集成

这个项目最令人惊喜的特性是**对 AI 智能体的原生支持**：

### Claude Code 使用示例

在 Claude Code 中直接调用 NotebookLM 处理研究任务：

```python
# 在 Claude Code 的 tool_use 中调用
result = nlp.ask("Compare the approach in this paper with recent advances in RAG")
```

### 多智能体协作

```
用户请求 → Claude Code 分析文档 → 调用 notebooklm-py 
         → NotebookLM 生成播客 → Claude Code 分析播客内容 → 汇总报告
```

这个工作流特别适合：
- **学术研究**：批量下载论文 → 自动生成播客 → AI 提炼要点
- **竞品分析**：抓取竞品文档 → NotebookLM 生成摘要 → 对比报告
- **新闻追踪**：定期抓取新闻 → NotebookLM 生成每日简报

---

## 🔑 核心认证机制

NotebookLM 要求 Google 账号认证。项目支持三种认证方式，按推荐顺序：

| 认证方式 | 优点 | 缺点 |
|---------|------|------|
| `--browser-cookies chrome` | 无需打开浏览器，最省事 | 需要手动导出 Cookie |
| `--browser msedge` | 支持企业 SSO（Edge 特有） | 需要 Edge 浏览器 |
| 交互式 `notebooklm login` | 通用 | 需要每次打开浏览器 |

> 💡 **推荐**：先在浏览器登录 Google 账号，然后用 `--browser-cookies chrome` 复用 session。

---

## 📊 功能对比：官方 UI vs. notebooklm-py

| 功能 | 官方 UI | notebooklm-py |
|------|---------|---------------|
| 文档上传 | ✅ | ✅ |
| Audio Overview（播客）| ✅ | ✅ |
| Video（白板风格）| ✅ | ✅ |
| Video（电影风格）| ✅ | ✅ |
| Quiz 生成 | ✅ | ✅ |
| 闪卡生成 | ✅ | ✅ |
| 问答 | ✅ | ✅ |
| 自动化/CLI | ❌ | ✅ |
| Python SDK | ❌ | ✅ |
| AI Agent 集成 | ❌ | ✅ |

notebooklm-py 的关键价值在于**把 NotebookLM 的交互式能力变成了可编程的 API**，这是官方没有提供的。

---

## ⚠️ 注意事项与限制

1. **非官方项目**：使用 Google NotebookLM 后端，非 Google 官方维护，存在账号封禁风险（目前社区反馈稳定）
2. **依赖 Google 服务**：需要稳定访问 Google NotebookLM 服务
3. **Cookie 有效期**：Google Cookie 会过期，长时间运行可能需要重新认证
4. **Linux Playwright 问题**：`playwright install chromium` 在某些 Linux 环境可能失败，详见 [troubleshooting](docs/troubleshooting.md#linux)

---

## 🔗 相关资源

- 📦 [PyPI: notebooklm-py](https://pypi.org/project/notebooklm-py/)
- 🐛 [Issue Tracker](https://github.com/teng-lin/notebooklm-py/issues)
- 📖 [完整文档](https://github.com/teng-lin/notebooklm-py#readme)
- 🎥 [Demo 视频（Asciinema）](https://asciinema.org/a/767284)

---

## 自测题

1. **notebooklm-py 支持哪三种认证方式？各有什么优缺点？**
<details>
<summary>查看答案</summary>

| 认证方式 | 优点 | 缺点 |
|---------|------|------|
| `--browser-cookies chrome` | 无需打开浏览器，最省事 | 需要手动导出 Cookie |
| `--browser msedge` | 支持企业 SSO（Edge 特有） | 需要 Edge 浏览器 |
| 交互式 `notebooklm login` | 通用 | 需要每次打开浏览器 |

> 💡 **推荐**：先在浏览器登录 Google 账号，然后用 `--browser-cookies chrome` 复用 session。

</details>

2. **如何使用 CLI 创建 Notebook、添加来源、生成播客？**
<details>
<summary>查看答案</summary>

```bash
# 1. 创建 Notebook 并添加来源
notebooklm create "My Research Project"
notebooklm use <notebook_id>
notebooklm source add "https://en.wikipedia.org/wiki/Artificial_intelligence"
notebooklm source add "./paper.pdf"

# 2. 基于文档问答
notebooklm ask "What are the key themes?"

# 3. 生成播客（Audio Overview）
notebooklm generate audio "make it engaging" --wait
```

关键点：
- 使用 `create` 创建 Notebook，`use` 切换到指定 Notebook。
- 使用 `source add` 添加来源（URL 或本地文件）。
- 使用 `ask` 基于文档问答。
- 使用 `generate audio` 生成播客，`--wait` 参数等待生成完成。

</details>

3. **如何把 notebooklm-py 集成到 Python 应用？写出关键代码。**
<details>
<summary>查看答案</summary>

```python
from notebooklm import NotebookLM

nlp = NotebookLM()

# 创建 Notebook
notebook = nlp.create_notebook("Research Notes")
nlp.set_notebook(notebook['id'])

# 添加来源
nlp.add_source("https://arxiv.org/abs/2303.17760")  # 论文 URL
nlp.add_source("./document.pdf")

# 问答
answer = nlp.ask("Summarize the main contributions of this paper")
print(answer)

# 生成播客
audio = nlp.generate_audio("A 5-minute engaging podcast summary", wait=True)
print(f"Audio URL: {audio['audio_url']}")
```

关键点：
- 使用 `NotebookLM()` 创建客户端。
- 使用 `create_notebook()` 创建 Notebook，`set_notebook()` 切换到指定 Notebook。
- 使用 `add_source()` 添加来源（URL 或本地文件路径）。
- 使用 `ask()` 基于文档问答。
- 使用 `generate_audio()` 生成播客，`wait=True` 等待生成完成。

</details>

4. **如何把 notebooklm-py 集成到 AI 智能体（如 Claude Code）？设计一个简单的工作流。**
<details>
<summary>查看答案</summary>

工作流示例：

```
用户请求 → Claude Code 分析文档 → 调用 notebooklm-py 
         → NotebookLM 生成播客 → Claude Code 分析播客内容 → 汇总报告
```

关键代码（在 Claude Code 的 tool_use 中调用）：

```python
# 在 Claude Code 中调用 notebooklm-py
result = nlp.ask("Compare the approach in this paper with recent advances in RAG")
```

适用场景：
- **学术研究**：批量下载论文 → 自动生成播客 → AI 提炼要点。
- **竞品分析**：抓取竞品文档 → NotebookLM 生成摘要 → 对比报告。
- **新闻追踪**：定期抓取新闻 → NotebookLM 生成每日简报。

</details>

5. **notebooklm-py 有哪些限制和注意事项？**
<details>
<summary>查看答案</summary>

1. **非官方项目**：使用 Google NotebookLM 后端，非 Google 官方维护，存在账号封禁风险（目前社区反馈稳定）。
2. **依赖 Google 服务**：需要稳定访问 Google NotebookLM 服务。
3. **Cookie 有效期**：Google Cookie 会过期，长时间运行可能需要重新认证。
4. **Linux Playwright 问题**：`playwright install chromium` 在某些 Linux 环境可能失败，详见 [Troubleshooting](docs/troubleshooting.md#linux)。

</details>

---

## 练习

### 练习 1：部署 notebooklm-py 并验证认证

**场景**：你想在本地开发环境部署 notebooklm-py，并验证 Google 账号认证是否成功。

**任务**：
1. 选择合适的认证方式（假设你的环境是 macOS，使用 Chrome 浏览器）。
2. 写出安装和认证命令。
3. 验证认证状态（使用 `notebooklm auth check --test --json`）。

<details>
<summary>参考答案</summary>

1. 认证方式：`--browser-cookies chrome`（推荐，无需打开浏览器）。
2. 安装和认证命令：
   ```bash
   # 安装
   pip install notebooklm-py
   
   # 认证（使用 Chrome 的 Cookie）
   notebooklm login --browser-cookies chrome
   
   # 验证认证状态
   notebooklm auth check --test --json
   # 期望返回: {"status": "ok"}
   ```
3. 验证认证状态：
   - 如果返回 `{"status": "ok"}`，说明认证成功。
   - 如果返回错误，需要重新认证（`notebooklm login`）。

</details>

### 练习 2：集成到 Python 应用

**场景**：你想把 notebooklm-py 集成到你的 Python 应用，实现"上传论文 → 生成播客 → 发送邮件通知"的自动化工作流。

**任务**：
1. 设计工作流（分几个步骤？每个步骤调用什么 API？）。
2. 写出关键代码（创建 Notebook、添加来源、生成播客、发送邮件）。
3. 处理错误（如果生成播客失败，如何重试？）。

<details>
<summary>参考答案</summary>

1. 工作流设计：
   - 步骤 1：创建 Notebook（`create_notebook()`）。
   - 步骤 2：添加论文来源（`add_source()`）。
   - 步骤 3：生成播客（`generate_audio()`，带 `--wait` 参数）。
   - 步骤 4：发送邮件通知（使用 `smtplib` 或第三方邮件服务）。

2. 关键代码：
   ```python
   from notebooklm import NotebookLM
   import smtplib
   from email.mime.text import MIMEText
   
   nlp = NotebookLM()
   
   # 创建 Notebook
   notebook = nlp.create_notebook("Paper Podcast")
   nlp.set_notebook(notebook['id'])
   
   # 添加论文来源
   nlp.add_source("https://arxiv.org/abs/2303.17760")
   
   # 生成播客（等待完成）
   audio = nlp.generate_audio("A 10-minute technical podcast", wait=True)
   
   # 发送邮件通知
   msg = MIMEText(f"Podcast generated: {audio['audio_url']}")
   msg['Subject'] = 'NotebookLM Podcast Ready'
   msg['From'] = 'your-email@example.com'
   msg['To'] = 'user@example.com'
   
   with smtplib.SMTP('smtp.gmail.com', 587) as server:
       server.starttls()
       server.login('your-email@example.com', 'password')
       server.send_message(msg)
   ```

3. 错误处理：
   - 如果 `generate_audio()` 失败，可以重试 3 次（使用 `for` 循环 + `try...except`）。
   - 如果 Cookie 过期，需要重新认证（`notebooklm login --browser-cookies chrome`）。

</details>

---

## 进阶路径

如果你已经读懂了本文，可以进一步关注这些方向：

1. **深入 notebooklm-py 的源码**：阅读 `notebooklm/` 目录下的源码，理解它如何调用 Google NotebookLM 的非官方 API。
2. **调试认证流程**：打开 `notebooklm login --browser-cookies chrome` 的调试日志，观察它如何导出 Chrome 的 Cookie 并用于认证。
3. **添加新功能**：尝试给 notebooklm-py 添加新功能（例如，支持更多文档格式、支持批量生成播客等），并提交 PR 到 GitHub。
4. **集成到 AI 智能体框架**：把 notebooklm-py 封装成一个 Tool，供 Claude Code、OpenClaw 等 AI 智能体调用。
5. **研究 Google NotebookLM 的官方 API**：如果 Google 将来开放了官方 API，学习如何迁移到官方 API。
6. **部署到生产环境**：把 notebooklm-py 部署到生产环境（例如，用 Docker 容器化），并配置自动化的 Cookie 刷新机制。

---

## 资料口径说明

1. **本文基于 notebooklm-py 仓库的 README 和源码**。具体实现可能随版本演进而变化，建议以最新 main 分支为准。
2. **功能对比（官方 UI vs. notebooklm-py）基于公开信息**，可能随 Google NotebookLM 的版本更新而变化。如果你发现对比信息过时，欢迎指正。
3. **认证方式的优缺点基于社区反馈**，可能随 Google 的认证策略调整而变化。如果你发现某种认证方式失效，欢迎在 GitHub 上提 issue。
4. **AI 智能体集成的工作流示例是作者设计的**，不是官方文档。如果你有更好的工作流，欢迎分享。
5. **限制和注意事项基于社区反馈**，可能随 notebooklm-py 的版本更新而变化。如果你发现新的限制或注意事项，欢迎在 GitHub 上提 issue 或 PR。

---

## 结语

notebooklm-py 把 Google NotebookLM 的强大能力从网页端释放出来，让研究人员和开发者可以在 Python 脚本和 AI 智能体中自由调用。对于需要批量处理文档、自动生成播客、或将 NotebookLM 集成到自动化工作流的场景，这是一个目前无可替代的工具。

---

*本文基于 2026-05-22 GitHub Trending 数据撰写。*