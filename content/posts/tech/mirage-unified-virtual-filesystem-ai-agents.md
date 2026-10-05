---
title: "Mirage 解读：AI Agent 的虚拟终端，一次 grep 扫遍 S3、Slack 和本地内存"
date: "2026-05-22T11:10:00+08:00"
lastmod: "2026-09-29T00:00:00+08:00"
slug: "mirage-unified-virtual-filesystem-ai-agents"
github_repo: "strukto-ai/mirage"
source_key: "gh:strukto-ai/mirage"
description: "对照 main 分支 README、官方示例与源码拆解 strukto-ai/mirage：虚拟终端定位下的五条主线（VFS、虚拟 CLI、运行时路由、Profile 策略、两层缓存）各自解决什么问题，官方 OpenAI Agents SDK 示例的完整任务流，以及 preview 阶段的采用建议。版本、Stars、代码均核查于 2026-09-29。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "TypeScript", "Python"]
---

给 Agent 接外部数据，现在的常规做法是每接一个服务就写一层工具封装，或者挂一堆 MCP 服务器。strukto-ai/mirage 押的注不一样：它把 S3、Slack、Gmail、GitHub 这些后端挂到同一个目录树上，让模型用已经会的 `ls`、`grep`、`find`、`jq` 去够所有数据。仓库描述写的是 "The World's First Virtual Terminal for AI Agents"——虚拟终端，而不只是文件系统。这个说法有实指：文件系统只是它四条主线中的一条，虚拟 CLI、可路由的运行时和一套策略引擎同样在 `main` 分支里。

项目 2026 年 5 月 6 日建仓，截至 2026-09-29 有 3,666 stars、270 forks，处于 preview 阶段（README 徽章自述），Apache-2.0 协议，由 strukto.ai 团队开发。本文对照 main 分支 README（含官方简体中文版）、`examples/` 目录源码和 PyPI/npm 包信息写成，数字与代码均核查于 2026-09-29。

## 五条主线，先看分工

| 主线 | 回答的问题 | 关键机制 |
|---|---|---|
| 虚拟文件系统（VFS） | 数据从哪来、长什么样 | 各后端并排挂载在同一根目录下，应答同一套 POSIX 语义 |
| 虚拟 CLI | 命令由谁应答 | `git`、`slack`、`ntn` 等由 Mirage 自己应答，机器上无需安装真工具 |
| 虚拟运行时 | 计算在哪里跑 | Python、JavaScript 及任意命令可路由到进程内、沙箱或远程机器 |
| Profile 与策略引擎 | 什么能做、什么能看见 | `allow`/`ask`/`deny` 管命令，`hide`/`show` 管可见性，策略脚本兜底 |
| 两层缓存 | 为什么不必每次都打 API | 索引缓存（TTL 默认 10 分钟）加文件缓存（默认 512 MB），可切 Redis 共享 |

一条主命令串起前三条：

```python
ws = Workspace(
    {
        "/tmp":   (RAMVFS(), MountMode.EXEC),
        "/redis": (RedisVFS(url=redis_url), MountMode.WRITE),
        "/slack": (SlackVFS(SlackConfig(token=slack_bot_token)), MountMode.EXEC),
    },
    # monty 捕获 python，脚本在工作区内以沙箱方式运行
    runtimes=[MontyRuntime(captures=["python", "python3"]), "workspace"],
)

# 一次 grep 扫遍所有数据源
await ws.shell("grep -rln session /redis /tmp")

# 运行存放在 Slack 里的脚本，把报告写入 Redis
await ws.shell("python3 /slack/channels/general_.../files/example__F....py > /redis/report.txt")

# 以头部命令名安装一个类型化 CLI：按名称分发，而不是按路径，
# 并且像其他程序一样可以通过 `man`、`type`、`which` 发现
ws.register_cli("slack", SLACK, {"token": slack_bot_token})
await ws.shell('slack send-message --channel general --text "report is up"')
```

（代码取自官方 README。`MountMode` 决定每个挂载点的权限：上面给 `/tmp` 和 `/slack` 开了 EXEC，给 `/redis` 只开 WRITE。）

## VFS：所有后端说同一套方言

挂载之后，每个服务应答同样的读、写、列目录操作。官方按用途分组，主要覆盖：

| 分组 | 代表后端 |
|---|---|
| 对象存储 | S3、R2、GCS、OCI、Supabase、MinIO、Ceph、阿里云 OSS、腾讯云 COS、Backblaze B2 等 |
| 文件与文档 | Google Drive、Docs、Sheets、Slides、OneDrive、SharePoint、Box、Dropbox、Nextcloud |
| 消息与协作 | Slack、Discord、Gmail、IMAP/SMTP 邮件、GitHub、Linear、Notion、Trello、Google Calendar |
| 数据库与数据平台 | PostgreSQL、MongoDB、Redis、LanceDB、Qdrant、Chroma、Databricks Volumes、Hugging Face 数据集 |
| 本地与远程 | 内存（RAM）、本地磁盘、浏览器 OPFS、SSH 远程 |

两点值得注意。其一，`hide` 隐藏的路径不只是"不可读"，而是在 Agent 看到的文件系统里根本不存在——可见性本身成了安全边界，这是它和"读之前先检查权限"的常规做法的实质区别。其二，和 Telegram 有关系的只有架构图 SVG：README 正文的数据源清单里没有 Telegram，引用这张表时别把图当证据。

## 虚拟 CLI 与运行时：命令不落在真机器上

`register_cli` 之后，`slack send-message` 这样的命令按名称分发到 Mirage 的实现，不查找 `$PATH`。同一个 CLI 可以装多份、各用一套凭据，让每个 Agent 只拿到分给它的账号。官方当前虚拟化的 CLI 覆盖 `git`、`gh`、`slack`、`discord`、`himalaya`（邮件）、`linear`、`ntn`（Notion）、`gws`（Google Workspace）、`hf`（Hugging Face）。

运行时走的是同一路数。`runtimes=[MontyRuntime(captures=["python", "python3"]), "workspace"]` 把 python 命令截给进程内的 Monty——Pydantic 用 Rust 从零实现的极简 Python 解释器，默认零权限，脚本与外界交互的唯一途径是显式注册的外部函数；其他命令留给 workspace 自身；也可以路由到 WASI CPython、Pyodide、QuickJS，或经 SSH 送到远程机器，沙箱后端支持 Docker、E2B、Daytona、Apple Container 等。计算与存储因此解耦：换沙箱供应商不动挂载配置，反过来也一样。

## 安全：三层收紧

1. **Profile 规则**：`allow`、`ask`、`deny` 管命令和 CLI，`hide`、`show` 管文件与目录。
2. **策略脚本**：规则表达不了的限制写成脚本，在每次命令执行前应答 allow、deny 或 ask——并且只能收紧，不能放宽。
3. **策略引擎**：宿主可注册自己的策略栈，每次命令、VFS 操作和会话写入都会过一遍。

凭据方面，Mirage 的环境变量可以解析到 AWS Secrets Manager、1Password、Auth0 或 dotenv 里已存的密钥，密钥不必复制进工作区。

## 一次真实任务怎么流过系统

抽象机制看腻了，看官方示例 `examples/python/agents/openai_agents/sandbox_agent.py`（模型名等细节原样照录）：

```python
import asyncio
import os

from agents import Runner
from agents.run import RunConfig
from agents.sandbox import SandboxAgent, SandboxRunConfig
from dotenv import load_dotenv

from mirage import MountMode, Workspace
from mirage.agents.openai_agents import MirageSandboxClient
from mirage.vfs.ram import RAMVFS
from mirage.vfs.s3 import S3VFS, S3Config
from mirage.vfs.slack import SlackConfig, SlackVFS

load_dotenv(".env.development")

ws = Workspace(
    {
        "/": (RAMVFS(), MountMode.WRITE),
        "/s3": (S3VFS(S3Config(
            bucket=os.environ["AWS_S3_BUCKET"],
            region=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        )), MountMode.READ),
        "/slack": (SlackVFS(config=SlackConfig(
            token=os.environ["SLACK_BOT_TOKEN"],
            search_token=os.environ.get("SLACK_USER_TOKEN"),
        )), MountMode.READ),
    },
    mode=MountMode.WRITE,
)

client = MirageSandboxClient(ws)
agent = SandboxAgent(
    name="Mirage Sandbox Agent",
    model="gpt-5.5",
    instructions=ws.file_prompt,
)

task = ("1. Find the date of the latest Slack message in the general channel. "
        "2. Summarize the parquet file in /s3/data/. "
        "Write your findings to /report.txt.")

async def main():
    result = await Runner.run(
        agent,
        task,
        run_config=RunConfig(sandbox=SandboxRunConfig(client=client)),
    )
    print(result.final_output)

asyncio.run(main())
```

模型的动作链是这样的：先 `ls /slack`（首次调用远端 API，结果进索引缓存），定位 general 频道文件；再 `grep` 或 `cat` 拿最新消息（命中缓存，零网络）；然后转向 `/s3/data/` 找 parquet 文件——Mirage 的系统提示词 `ws.file_prompt` 会告诉模型挂载了什么；最后把结论写进根目录下的 `/report.txt`。整个过程中模型没有调用任何 S3 或 Slack 专属工具，它只是在跑 shell 命令。

同一仓库的 `examples/python/agents/` 下还有 LangChain、Pydantic AI、CAMEL、OpenHands、Agno 的 Python 示例；TypeScript 侧的 `@struktoai/mirage-agents` 提供 Vercel AI SDK、OpenAI Agents SDK、LangChain、Mastra 适配器，另有面向 Claude Code、Codex、OpenCode 等编码 Agent 的接入文档。注意该包顶层是空导出，一切从子路径导入，比如 `import { mirageTools } from '@struktoai/mirage-agents/vercel'` 会拿到 `execute`、`readFile`、`writeFile`、`editFile`、`ls` 五个工具。

## 缓存：远端后端敢用 grep 的前提

对远端数据跑 `grep -r` 意味着大量列目录和读取。Mirage 用两层缓存压平这部分开销：

- **索引缓存**：目录列表和元数据。首次遍历调 API，TTL 过期前（默认 10 分钟）都读本地索引。
- **文件缓存**：对象字节。首次读取从源端流式拉取，之后的管道直接读缓存（默认 512 MB）。

两层默认都在进程内 RAM 里，零配置。多进程或分布式部署时切到 Redis：

```ts
import { RedisFileCacheStore, S3VFS, Workspace } from '@struktoai/mirage-node'

const ws = new Workspace(
  { '/s3': new S3VFS({ bucket: 'my-bucket' }) },
  {
    cache: new RedisFileCacheStore({ url: 'redis://localhost:6379/0', cacheLimit: '8GB' }),
    index: { type: 'redis', url: 'redis://localhost:6379/0', ttl: 600 },
  },
)
```

## 安装与版本锚点

```bash
# Python（同时安装 mirage 库和 mirage CLI 二进制）
uv add mirage-ai

# TypeScript（两个运行时包都会自动引入 @struktoai/mirage-core）
npm install @struktoai/mirage-node      # Node.js 服务器和 CLI
npm install @struktoai/mirage-browser   # 浏览器 / edge 运行时
npm install @struktoai/mirage-agents    # OpenAI / Vercel AI / LangChain / Mastra 适配器

# 独立 CLI，四选一
curl -fsSL https://strukto.ai/mirage/install.sh | sh
npm install -g @struktoai/mirage-cli
uvx mirage-ai
npx @struktoai/mirage-cli
```

2026-09-29 核查的锚点：PyPI `mirage-ai` 与 npm 各包最新版均为 0.0.6（PyPI 另有 0.0.7a1/a2 预发布）；Python ≥ 3.11，Node.js ≥ 20（npm engines 精确到 ≥ 20.10.0）；基于 FUSE 的真实挂载点需要 macOS 或 Linux。不装 SDK 也能用 CLI 走完整流程：`mirage workspace create` 建工作区、`mirage execute` 跑命令、`mirage workspace snapshot`/`load` 存取快照。

## 采用建议

版本号还在 0.0.x、官方自述 preview，README 明确 API 可能变化——这个前提决定了建议的形状：

- **可以现在就上手**：给多后端数据聚合类 Agent 找工具层的团队。价值主张（一次 grep 扫所有源）在 RAMVFS 上就能本地验证，不碰生产数据。
- **值得跟进但别急**：想给 Claude Code、Codex 这类编码 Agent 挂数据源的团队，先在非关键链路试点，盯 0.1.0 的 API 稳定信号。
- **建议观望**：把核心业务流程压在上面的生产系统。策略引擎和 Profile 设计是为受限执行准备的，但 0.0.x 阶段的兼容性承诺为零，升级成本现在还没法定价。

判断的落点：Mirage 赌的是"LLM 最大的存量技能是 bash"这件事继续成立。只要主流编码 Agent 仍以 shell 为核心工具，把外部服务收敛进文件系统语义的路线就比逐家写 SDK 少维护一层适配；反之，如果 Agent 的工具调用彻底转向结构化接口，它的杠杆会变短。目前前一种趋势没有逆转的迹象，而这个项目把两条主线——数据面（VFS）和控制面（策略引擎）——放在了同一个界面里，这在同类项目里并不多见。

文档在 [docs.mirage.strukto.ai](https://docs.mirage.strukto.ai)，缓存命中与失效的完整生命周期、权限配置的细节都在那里；仓库 [strukto-ai/mirage](https://github.com/strukto-ai/mirage) 的 `examples/` 目录按后端分组，六十多个示例可以直接对照运行。
