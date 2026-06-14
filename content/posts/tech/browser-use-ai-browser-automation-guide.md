---
title: "Browser-Use：让 AI Agent 控制浏览器完成任何任务"
date: "2026-04-06T20:12:00+08:00"
slug: "browser-use-ai-browser-automation-guide"
description: "全面介绍 Browser-Use 开源 AI 浏览器自动化库，涵盖安装配置、Claude Code 集成、自定义工具扩展、生产环境部署和故障排除。"
draft: false
categories: ["技术笔记"]
tags: ["Browser-Use", "AI Agent", "浏览器自动化", "Playwright", "Web Scraping"]
---

. 项目概述

. 是什么

Browser-Use 是一个**开源的 AI 浏览器自动化库**，它的基本理念是：**Tell your computer what to do, and it gets it done**——告诉计算机要做什么，它就能完成。

它让 AI Agent（GPT、Claude、Gemini 等）能够像人类一样控制浏览器，填写表单、点击按钮、搜索信息、完成各种网页操作。

. 定位

Browser-Use 有两种使用模式：

- **开源库**：自主托管，完全控制。适合需要自定义工具和深度集成的场景。
- **云服务**：托管浏览器基础设施。适合快速启动、规模化和抗检测场景。

. 技术架构

Browser-Use 的核心组件：

| 组件 | 说明 |
|------|------|
| **Agent** | AI 代理，理解任务并控制浏览器 |
| **Browser** | 浏览器实例管理 |
| **LLM Adapter** | 支持 OpenAI/Google/Anthropic 等 |
| **Tools** | 可扩展的工具集 |
| **CLI** | 命令行界面 |

. 支持的模型

| 提供商 | 模型示例 |
|--------|---------|
| **Browser-Use Cloud** | `ChatBrowserUse()` 优化模型 |
| **OpenAI** | GPT-4o, GPT-4o-mini |
| **Google** | Gemini 3-flash-preview |
| **Anthropic** | Claude Sonnet 4, Claude Opus |
| **本地模型** | 通过 Ollama 支持 |

---

. 核心特性详解

. LLM 优化的浏览器代理

Browser-Use 对 LLM 进行了专门优化：

| 特性 | 说明 |
|------|------|
| **任务理解** | LLM 解析自然语言任务为可执行步骤 |
| **元素识别** | 智能识别网页可交互元素 |
| **状态追踪** | 跟踪页面状态变化 |
| **错误恢复** | 自动从错误中恢复重试 |

. 基准测试表现

根据官方基准测试（BU Bench V1），Browser-Use 在 100 个真实浏览器任务上的表现：

| 模型 | 成功率 | 特点 |
|------|--------|------|
| **ChatBrowserUse** | 最高 | 专门优化，3-5x 更快 |
| **GPT-4o** | 高 | 通用能力强 |
| **Claude Sonnet** | 高 | 推理能力强 |
| **Gemini** | 中高 | 性价比好 |

. 多 LLM 提供商支持

```python
Browser-Use 优化模型
from browser_use import ChatBrowserUse

OpenAI
from browser_use import ChatOpenAI
llm = ChatOpenAI(model='gpt-4o')

Google
from browser_use import ChatGoogle
llm = ChatGoogle(model='gemini-3-flash-preview')

Anthropic
from browser_use import ChatAnthropic
llm = ChatAnthropic(model='claude-sonnet-4-6')

本地模型（Ollama）
from browser_use import ChatOllama
llm = ChatOllama(model='llama3')
```

. 浏览器管理

```python
from browser_use import Browser, BrowserConfig

本地浏览器
browser = Browser()

配置选项
browser = Browser(
    # headless=False,  # 显示浏览器窗口
    # timeout=30,       # 超时时间（秒）
)

云浏览器（推荐生产环境）
browser = Browser(
    use_cloud=True,  # 使用 Browser Use Cloud 托管浏览器
)
```

---

. 安装与快速上手

. 环境要求

- Python >= 3.11
- uv 包管理器（推荐）
- Chromium 浏览器（自动安装或手动安装）

. 使用 uv 安装

```bash
. 创建项目
uv init

. 添加 browser-use
uv add browser-use

. 同步环境
uv sync

. 安装 Chromium（如果没有）
uvx browser-use install
```

. 获取 API Key

**方式一：Browser Use Cloud（推荐）**

1. 访问 https://cloud.browser-use.com/new-api-key
2. 获取 API Key
3. 配置环境变量：

```bash
.env
BROWSER_USE_API_KEY=your-key
GOOGLE_API_KEY=your-key
ANTHROPIC_API_KEY=your-key
```

**方式二：使用本地模型**

```bash
安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

拉取模型
ollama pull llama3
```

. 最简示例

```python
from browser_use import Agent, Browser, ChatBrowserUse
import asyncio

async def main():
    # 创建浏览器实例
    browser = Browser()

    # 创建 Agent
    agent = Agent(
        task="Find the number of stars of the browser-use repo",
        llm=ChatBrowserUse(),
        browser=browser,
    )

    # 运行任务
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())
```

---

. 实战用例

. 表单填写

**任务**: "Fill in this job application with my resume and information"

```python
from browser_use import Agent, Browser, ChatBrowserUse
import asyncio

async def main():
    browser = Browser()
    agent = Agent(
        task="""Fill in this job application:
        - Name: John Doe
        - Email: john@example.com
        - Position: Software Engineer
        - Resume: upload resume.pdf""",
        llm=ChatBrowserUse(),
        browser=browser,
    )
    await agent.run()

asyncio.run(main())
```

. 在线购物

**任务**: "Put this list of items into my instacart"

```python
async def main():
    browser = Browser()
    agent = Agent(
        task="""Shop for these groceries:
        - Milk
        - Bread
        - Eggs
        - Butter
        Add to my cart on instacart.com""",
        llm=ChatBrowserUse(),
        browser=browser,
    )
    await agent.run()
```

. 个人助手

**任务**: "Help me find parts for a custom PC"

```python
async def main():
    browser = Browser()
    agent = Agent(
        task="""Find these PC parts on pcpartpicker.com:
        - NVIDIA RTX 4090
        - AMD Ryzen 9 7950X
        - 64GB DDR5 RAM
        Compare prices and show me the best deals""",
        llm=ChatBrowserUse(),
        browser=browser,
    )
    await agent.run()
```

---

. CLI 工具详解

. 安装 CLI

CLI 随 browser-use 包一起安装：

```bash
验证安装
browser-use --version
```

. 常用命令

```bash
打开网页
browser-use open https://example.com

查看可点击元素
browser-use state

点击元素（通过索引）
browser-use click 5

输入文本
browser-use type "Hello World"

截图
browser-use screenshot page.png

关闭浏览器
browser-use close
```

. 快速迭代工作流

```bash
. 打开目标页面
browser-use open https://example.com

. 查看页面元素
browser-use state

. 点击第个元素
browser-use click 5

. 输入搜索词
browser-use type "search term"

. 截图确认
browser-use screenshot result.png
```

CLI 保持浏览器实例运行，可以快速迭代调试。

---

. Claude Code Skill 集成

. 为什么集成

为 Claude Code 安装 Browser-Use Skill 后，可以直接用自然语言让 AI 控制浏览器完成各种任务，无需编写代码。

. 安装步骤

```bash
. 创建 skill 目录
mkdir -p ~/.claude/skills/browser-use

. 下载 SKILL.md
curl -o ~/.claude/skills/browser-use/SKILL.md \
  https://raw.githubusercontent.com/browser-use/browser-use/main/skills/browser-use/SKILL.md
```

. 使用方式

安装后，直接在 Claude Code 中告诉它要做什么：

```
Use browser-use to search for the cheapest RTX 4090 on Amazon and tell me the price.
```

---

. 自定义工具扩展

. 创建自定义工具

```python
from browser_use import Agent, Browser, Tools
from browser_use.tools import Tools

创建工具实例
tools = Tools()

定义自定义工具
@tools.action(description='Get the current weather for a city')
def get_weather(city: str) -> str:
    """获取城市天气"""
    import requests
    response = requests.get(f"https://api.weather.com/v3/wx/conditions", params={"city": city})
    return response.json()

使用自定义工具
agent = Agent(
    task="Find the weather in Tokyo and then book a flight there",
    llm=llm,
    browser=browser,
    tools=tools,
)
```

. 工具设计实践建议

| 原则 | 说明 |
|------|------|
| **清晰描述** | description 要明确工具做什么 |
| **类型提示** | 使用 Python 类型注解 |
| **错误处理** | 返回有意义的错误信息 |
| **幂等性** | 同一调用总是返回相同结果 |

---

. 高级配置

. 认证处理

**复用 Chrome 配置**：

```python
from browser_use import Browser

使用已登录的 Chrome 配置文件
browser = Browser(
    profile_dir="~/.config/google-chrome/Default"
)
```

**云浏览器同步配置**：

```bash
curl -fsSL https://browser-use.com/profile.sh | \
  BROWSER_USE_API_KEY=XXXX sh
```

. 代理配置

```python
from browser_use import Browser

browser = Browser(
    use_cloud=True,
    proxy="http://my-proxy:8080"  # 代理地址
)
```

. 超时配置

```python
browser = Browser(
    timeout=60,  # 单个操作超时（秒）
)

agent = Agent(
    task="...",
    browser=browser,
    max_steps=50,  # 最大步数限制
)
```

---

. Open Source vs Cloud

. 何时使用开源库

| 场景 | 说明 |
|------|------|
| **需要自定义工具** | 添加专用工具扩展功能 |
| **深度代码集成** | 在现有应用中嵌入浏览器自动化 |
| **完全自主托管** | 数据安全要求，不适合云服务 |

. 何时使用云服务

| 场景 | 说明 |
|------|------|
| **快速启动** | 无需搭建基础设施 |
| **规模化** | 并行运行多个浏览器实例 |
| **抗检测** | 代理轮换、指纹伪装 |
| **CAPTCHA 处理** | 内置 CAPTCHA 解决 |
| **内存管理** | 无需担心内存泄漏 |

. 混合使用

```python
使用开源库 + 云浏览器
agent = Agent(
    task="...",
    llm=ChatOpenAI(model='gpt-4o'),
    browser=Browser(use_cloud=True),  # 云浏览器
    tools=custom_tools,  # 自定义工具
)
```

---

. 生产环境部署

. 常见挑战

| 挑战 | 解决方案 |
|------|---------|
| **内存占用** | Chrome 消耗大量内存，使用云服务 |
| **并行管理** | 云服务处理扩缩容 |
| **反爬检测** | 使用 Browser Use Cloud 的 stealth 浏览器 |
| **CAPTCHA** | 使用云服务内置解决方案 |
| **状态管理** | 云服务提供持久化文件系统和记忆 |

. 云服务优势

Browser Use Cloud 提供：

- **可扩展的浏览器基础设施**
- **内存管理**
- **代理轮换**
- **Stealth 浏览器指纹**
- **高性能并行执行**
- **1000+ 集成**（Gmail、Slack、Notion 等）

---

. 故障排除

. 常见问题

| 问题 | 解决方案 |
|------|---------|
| **Chromium 未安装** | 运行 `uvx browser-use install` |
| **页面加载超时** | 增加 `timeout` 参数 |
| **元素点击失败** | 使用 `browser-use state` 查看实际元素 |
| **认证丢失** | 使用 `profile_dir` 复用 Chrome 配置 |
| **CAPTCHA 阻止** | 使用 Browser Use Cloud 的 stealth 模式 |

. 调试技巧

```python
启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

截图查看状态
browser.screenshot("debug.png")

打印页面 HTML
html = browser.get_page_content()
print(html)
```

---

. 总结

Browser-Use 是一个开源的 AI 浏览器自动化库，支持 OpenAI、Google、Anthropic 及本地模型，可通过 Claude Code Skill 实现自然语言控制浏览器。MIT License 开源免费，云服务提供企业级抗检测和规模化补充。

适用场景包括网页数据采集、自动填表、在线购物比价、浏览器测试自动化和个人效率助手。不适合需要人类视觉验证的复杂任务或对抗性网站（这些场景可考虑云服务的 stealth 模式），极简单的任务直接调 API 往往更快。

---

**附录：相关资源**

- GitHub：https://github.com/browser-use/browser-use
- 官方文档：https://docs.browser-use.com
- 云服务：https://cloud.browser-use.com
- 博客：https://browser-use.com/posts
- 基准测试：https://github.com/browser-use/benchmark