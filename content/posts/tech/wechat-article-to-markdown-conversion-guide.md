---
title: "WeChat Article to Markdown：微信公众号文章转Markdown工具"
slug: "wechat-article-to-markdown-conversion-guide"
date: "2026-04-08T13:05:00+08:00"
lastmod: 2026-04-08T13:05:00+08:00
categories: ["技术笔记"]
tags: ["Python", "微信", "Markdown", "爬虫", "Camoufox", "反检测"]
description: "WeChat Article to Markdown 是一个 Python 编写的工具，用于抓取微信公众号文章并转换为干净的 Markdown 格式。支持反检测抓取、图片本地化、代码高亮保留，可作为 AI Agent Skill 使用。"
draft: false
---

# WeChat Article to Markdown：微信公众号文章转 Markdown 工具

## 1. 学习目标

通过本文你将掌握：

- 理解 WeChat Article to Markdown 的设计理念和关键价值
- 熟练安装和配置工具
- 掌握各种使用方式（CLI、Python API、AI Agent Skill）
- 理解反检测抓取原理
- 定制和扩展工具功能
- 实践建议和常见问题解决

## 2. 项目概述

### 2.1 什么是 WeChat Article to Markdown

WeChat Article to Markdown 是一个开源工具：

> **"Fetch WeChat Official Account articles and convert them to clean Markdown"**

**一句话解释**：输入微信公众号文章链接，输出干净的 Markdown 文件，图片自动下载到本地。

### 2.2 关键价值

| 痛点 | 解决方案 |
|------|---------|
| 微信公众号文章难以保存 | 转换为本地 Markdown 文件 |
| 文章图片容易失效 | 图片下载到本地 `images/` 目录 |
| 代码块格式丢失 | 保留语言标识和语法高亮 |
| 无法在 AI 工具中使用 | 输出兼容各种 Markdown 工具 |

### 2.3 技术栈

```
├── Python 100%
├── Camoufox（反检测浏览器）
├── Markdown 生成
├── 图片下载与本地化
└── MIT License
```

**关键依赖**：

| 库 | 用途 |
|----|------|
| Camoufox | 抗检测的浏览器自动化 |
| Markdown | HTML → Markdown 转换 |
| requests | HTTP 请求 |
| Pillow | 图片处理 |

## 3. 系统架构

### 3.1 整体架构

```
┌─────────────────────────────────────┐
│              用户层                     │
│  CLI 命令 / Python API / AI Agent     │
└─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────┐
│           核心处理层                    │
│  URL 解析 → HTML 获取 → 内容提取      │
│  Markdown 转换 → 图片处理            │
└─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────┐
│           底层服务层                   │
│  Camoufox（反检测抓取）               │
│  图片下载器                          │
│  格式转换引擎                        │
└─────────────────────────────────────┘
```

### 3.2 工作流程

**完整工作流程**：

```
1. 接收微信公众号文章 URL
   ↓
2. 使用 Camoufox 抓取页面（反检测）
   ↓
3. 解析 HTML，提取：
   - 文章标题
   - 公众号名称
   - 发布时间
   - 原文链接
   - 正文内容
   - 代码块
   ↓
4. 转换为 Markdown 格式
   ↓
5. 下载图片到本地 images/ 目录
   ↓
6. 输出文件：
   output/<文章标题>/
   ├── <文章标题>.md
   └── images/
       ├── img_001.png
       └── img_002.png
```

### 3.3 反检测机制

Camoufox 是一个抗检测的浏览器自动化库：

```python
from camoufox import Camoufox

with Camoufox() as browser:
    page = browser.new_page()
    page.goto("https://mp.weixin.qq.com/s/xxxxxxxx")
    # 自动注入随机 User-Agent
    # 自动处理 Cookie 和 Session
    # 模拟人类操作行为
```

**反检测策略**：

| 策略 | 说明 |
|------|------|
| 随机 User-Agent | 每次请求使用不同的浏览器标识 |
| 人类行为模拟 | 随机延迟、鼠标移动 |
| Cookie 管理 | 自动处理登录状态 |
| 请求间隔 | 避免频繁请求被封 |

## 4. 安装与配置

### 4.1 环境要求

- Python 3.8+
- pip 或 uv

### 4.2 安装步骤

**方式一：uv（推荐）**

```bash
# 安装 uv（如果没有）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 使用 uv 安装
uv tool install wechat-article-to-markdown
```

**方式二：pipx**

```bash
pipx install wechat-article-to-markdown
```

**方式三：源码安装**

```bash
git clone git@github.com:jackwener/wechat-article-to-markdown.git
cd wechat-article-to-markdown
uv sync
```

### 4.3 验证安装

```bash
# 检查版本
wechat-article-to-markdown --version

# 查看帮助
wechat-article-to-markdown --help
```

## 5. 使用指南

### 5.1 CLI 使用

**基础用法**：

```bash
# 转换文章
wechat-article-to-markdown "https://mp.weixin.qq.com/s/xxxxxxxx"
```

**指定输出目录**：

```bash
wechat-article-to-markdown "https://mp.weixin.qq.com/s/xxxxxxxx" \
    --output ./my-articles
```

**使用 uv 运行**：

```bash
uv run wechat-article-to-markdown "https://mp.weixin.qq.com/s/xxxxxxxx"
```

### 5.2 Python API

**基础用法**：

```python
from wechat_article_to_markdown import WeChatArticle

article = WeChatArticle(
    url="https://mp.weixin.qq.com/s/xxxxxxxx"
)
article.fetch()
article.save("output-dir")
```

**获取元数据**：

```python
article = WeChatArticle(url="...")

# 获取文章信息
info = article.get_metadata()
print(info)
# {
#     "title": "文章标题",
#     "account": "公众号名称",
#     "publish_time": "2024-01-01 12:00:00",
#     "source_url": "原文链接"
# }
```

**自定义处理**：

```python
article = WeChatArticle(
    url="...",
    download_images=True,      # 下载图片
    preserve_code_lang=True,    # 保留代码语言标识
    output_format="markdown"    # 输出格式
)
```

### 5.3 输出结构

**默认输出**：

```
output/
└── <文章标题>/
    ├── <文章标题>.md      # Markdown 文件
    └── images/            # 图片目录
        ├── img_001.png
        ├── img_002.jpg
        └── img_003.gif
```

**Markdown 内容示例**：

```markdown
---
title: "微信公众号文章标题"
author: "公众号名称"
date: "2024-01-01 12:00:00"
source: "https://mp.weixin.qq.com/s/xxxxxxxx"
---

# 文章标题

这是文章正文...

## 代码示例

```python
def hello():
    print("Hello, WeChat!")
```

![图片描述](../images/img_001.png)
```

## 6. AI Agent Skill 集成

### 6.1 什么是 AI Agent Skill

WeChat Article to Markdown 自带 `SKILL.md`，可供 AI Agent 自动发现和使用。

**支持的 AI Agent**：
- Claude Code
- Cursor
- Continue
- 其他支持 `.agents/skills/` 约定的 Agent

### 6.2 使用 Skills CLI 安装（推荐）

```bash
npx skills add jackwener/wechat-article-to-markdown
```

**参数说明**：

| 参数 | 说明 |
|------|------|
| `-g` | 全局安装（用户级别，跨项目共享） |
| `-a <agent>` | 指定目标 Agent（如 claude-code） |
| `-y` | 非交互模式 |

**示例**：

```bash
# 全局安装
npx skills add jackwener/wechat-article-to-markdown -g

# 安装到 Claude Code
npx skills add jackwener/wechat-article-to-markdown -a claude-code
```

### 6.3 手动安装

**创建技能目录**：

```bash
# 创建目录
mkdir -p ~/.claude/skills/wechat-article-to-markdown

# 下载 SKILL.md
curl -o ~/.claude/skills/wechat-article-to-markdown/SKILL.md \
    https://raw.githubusercontent.com/jackwener/wechat-article-to-markdown/main/SKILL.md
```

**重启 Agent**：安装后重启 Claude Code 使技能生效。

### 6.4 在 AI 对话中使用

**Claude Code 示例**：

```
用户：帮我抓取这篇文章并转换为 Markdown
https://mp.weixin.qq.com/s/xxxxxxxx

Agent：正在使用 wechat-article-to-markdown 抓取文章...

抓取完成！
文章标题：xxx
公众号：xxx
保存在：output/xxx/xxx.md
```

## 7. 高级用法

### 7.1 批量转换

```python
from wechat_article_to_markdown import WeChatArticle
import asyncio

async def batch_convert(urls: list[str], output_dir: str):
    tasks = []
    for url in urls:
        article = WeChatArticle(url=url, output_dir=output_dir)
        tasks.append(article.fetch_and_save())
    
    await asyncio.gather(*tasks)

# 使用
urls = [
    "https://mp.weixin.qq.com/s/xxx1",
    "https://mp.weixin.qq.com/s/xxx2",
    "https://mp.we.weixin.qq.com/s/xxx3",
]
asyncio.run(batch_convert(urls, "./articles"))
```

### 7.2 自定义图片处理

```python
article = WeChatArticle(
    url="...",
    image_processor=custom_processor  # 自定义图片处理函数
)

def custom_processor(img_url: str, img_data: bytes) -> str:
    # 自定义下载逻辑
    # 返回本地保存的路径
    return local_path
```

### 7.3 代码块处理

```python
article = WeChatArticle(url="...")

# 配置代码块处理
article.config.code_block_lang_map = {
    "python": "python",
    "javascript": "javascript",
    "java": "java",
    "cpp": "cpp",
    # 自定义映射
}
```

### 7.4 代理设置

```python
article = WeChatArticle(
    url="...",
    proxy="http://127.0.0.1:7890"  # HTTP 代理
)
```

## 8. 测试

### 8.1 单元测试

```bash
# 运行单元测试
uv run --with pytest pytest -q -m "not e2e"
```

### 8.2 端到端测试

```bash
# 设置测试文章 URL
export WECHAT_E2E_URLS="https://mp.weixin.qq.com/s/xxx1,https://mp.weixin.qq.com/s/xxx2"

# 运行 E2E 测试
uv run --with pytest pytest -q -m e2e -s
```

**注意**：E2E 测试需要网络和浏览器，会调用真实的微信公众号接口。

## 9. 实践建议

### 9.1 抓取策略

| 场景 | 建议 |
|------|------|
| 快速测试 | 使用 `--output` 指定输出目录 |
| 批量抓取 | 添加请求间隔，避免频繁请求 |
| 图片密集文章 | 确保磁盘空间充足 |
| 代码文章 | 验证代码块语法高亮正确 |

### 9.2 文件管理

```bash
# 按公众号整理
wechat-article-to-markdown "url1" --output "./公众号名/文章1"
wechat-article-to-markdown "url2" --output "./公众号名/文章2"

# 按时间整理
./2024-01/
    ├── article1/
    └── article2/
```

### 9.3 错误处理

```python
from wechat_article_to_markdown import WeChatArticle, WeChatException

try:
    article = WeChatArticle(url="...")
    article.fetch()
except WeChatException as e:
    if e.code == "URL_INVALID":
        print("无效的微信公众号 URL")
    elif e.code == "ARTICLE_NOT_FOUND":
        print("文章不存在或已被删除")
    elif e.code == "NETWORK_ERROR":
        print("网络错误，请检查网络连接")
```

### 9.4 性能优化

| 优化项 | 方法 |
|--------|------|
| 并发抓取 | 使用 `asyncio` 并发处理多个 URL |
| 图片压缩 | 添加 `--compress-images` 压缩图片 |
| 缓存 | 设置 `--cache-dir` 缓存已抓取的内容 |

## 10. 常见问题

**Q: 抓取失败，提示"页面不存在"？**

```bash
# 检查 URL 是否正确
# 微信公众号文章 URL 格式：
# https://mp.weixin.qq.com/s/xxxxxxxx
# 确保是完整的 URL，不是缩写的
```

**Q: 图片下载失败？**

```bash
# 检查网络代理设置
# 有些网络需要代理才能访问微信图片
export https_proxy="http://127.0.0.1:7890"
wechat-article-to-markdown "..."
```

**Q: 如何抓取多篇文章？**

```python
# 使用 Python API 批量处理
urls = ["url1", "url2", "url3"]
for url in urls:
    article = WeChatArticle(url=url)
    article.fetch_and_save()
```

**Q: 输出的 Markdown 有乱码？**

```bash
# 指定编码
wechat-article-to-markdown "..." --encoding utf-8
```

**Q: 如何保留原始格式？**

```bash
# 不转换特殊格式
wechat-article-to-markdown "..." --preserve-formatting
```

**Q: Camoufox 报错？**

```bash
# 确保已安装 Chrome/Chromium
# 或者指定浏览器路径
wechat-article-to-markdown "..." --browser-path /usr/bin/chromium
```

## 11. 与类似工具对比

| 工具 | 语言 | 反检测 | 图片处理 | AI Skill |
|------|------|--------|---------|---------|
| WeChat Article to Markdown | Python | Camoufox | 本地化 | ✅ SKILL.md |
| 微信公众号导出 | JavaScript | 无 | Base64 | ❌ |
| Wechat-Article-Markdown | Python | Selenium | 外部链接 | ❌ |

**WeChat Article to Markdown 优势**：
- Camoufox 反检测，成功率高
- 图片本地化，避免失效
- 自带 AI Agent Skill 支持
- 活跃维护（472 Stars）

## 12. 总结

WeChat Article to Markdown 是微信公众号文章转换的利器：

| 特性 | 说明 |
|------|------|
| 反检测抓取 | Camoufox 支持，高成功率 |
| Markdown 输出 | 兼容各种工具和平台 |
| 图片本地化 | 避免图片失效问题 |
| AI Skill 集成 | Claude Code 等 Agent 可直接使用 |
| 开源免费 | MIT 许可证 |

**适用场景**：
- 微信公众号文章备份
- 内容迁移和二次编辑
- AI 工具输入源
- 知识库建设

---

*🦞 每日 08:00 自动更新*
