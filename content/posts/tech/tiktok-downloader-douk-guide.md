---
title: "TikTokDownloader：14K Stars·抖音/TikTok数据采集与下载工具"
date: "2026-04-12T02:31:39+08:00"
slug: tiktok-downloader-douk-guide
description: "TikTokDownloader 是一个抖音和 TikTok 数据采集与下载工具，支持批量下载、Web API 和终端交互功能。"
draft: false
categories: ["技术笔记"]
tags: ["TikTok", "抖音", "下载", "爬虫", "Python"]
---

# TikTokDownloader：14K Stars·抖音/TikTok数据采集与下载工具

## 一，这篇文章要解决什么

TikTokDownloader（DouK-Downloader）真正对应的场景不是"偶尔下载一个视频"——单个视频用浏览器的开发者工具抓包就行。它的价值体现在**批量**：你要下载一个账号的全部发布作品、或者把某个话题下的评论导出做分析，而且希望这件事可重复、可脚本化、不依赖每次都手动操作浏览器。

读完这篇文章，你会：

- 分清抖音线和 TikTok 线的能力边界——什么时候必须配代理、评论采集在哪个平台能用
- 独立跑通一次「终端交互模式」的批量下载：从 Cookie 配置到文件导出
- 用 Web API 把下载能力集成到自己的脚本或定时任务里
- 根据实际场景（偶尔下载 / 定时采集 / 不想配 Python 环境）选对使用方式

下面先把两条线拆开——搞清它们的差异是后面一切操作的前提。

## 二，系统地图：抖音线 vs TikTok 线

TikTokDownloader 内部其实跑着两条采集主线，虽然共享同一套 HTTP 客户端和 Cookie 管理，但它们的 API 端点、数据返回格式和 Cookie 要求都不同：

| 维度 | 抖音线 | TikTok 线 |
|------|--------|-----------|
| 数据来源 | 抖音国内版 API | TikTok 国际版 API |
| 采集项 | 发布、喜欢、收藏、收藏夹、视频、图集、实况、直播、音乐、合集、评论、账号、搜索、热榜 | 发布、喜欢、合辑、直播、视频、评论、账号 |
| Cookie 要求 | 抖音网页版登录 Cookie | TikTok 网页版登录 Cookie |
| 代理需求 | 通常不需要 | 国内访问必须走代理 |
| 评论采集 | ✅ 支持 | ❌ 不支持 |
| 搜索/热榜 | ✅ 支持 | ❌ 不支持 |

两条线在代码层面共用 `src/core/` 下的同一套模块（`account.py`、`video.py`、`comment.py` 等），但实际请求时根据目标平台走不同的 API 端点。**不要混用 Cookie**——抖音的 Cookie 对 TikTok 接口无效，反过来也一样。

### 项目基本信息

| 指标 | 数值 |
|------|------|
| Stars | 14k ⭐ |
| Forks | 2.4k |
| 最新版本 | V5.7 (2025-08-19) |
| 最新提交 | 2026-04-07 |
| 许可证 | GPL-3.0 |
| 语言 | Python 88.6%, JavaScript 11.2%, Dockerfile 0.2% |
| 作者 | JoeanAmier（核心维护者） |

## 三，一次完整的批量下载怎么样流过系统

下面用一个具体任务——"批量下载某抖音账号的全部发布作品"——把三种使用方式串起来。这个案例能帮你判断哪种方式更适合自己的场景。

### 3.1 终端交互模式

最直接的方式。启动后按菜单选择，全程交互式操作：

```
$ python main.py
# 选择 1. 终端交互模式
# → 选择 1. 批量下载账号作品
#   → 选择 1. 批量下载发布作品
#     → 输入账号主页链接
#     → 选择并发数（默认 5）
#     → 开始下载
```

内部流程：程序读取 `settings.json` 中的 Cookie → 用 httpx 异步请求抖音 API 获取作品列表 → 按并发数分批下载视频文件 → 文件先写入临时目录，下载完成后移动到最终目录。如果中途 Cookie 过期，程序会提示重新输入。

### 3.2 Web API 模式

适合嵌入自己的脚本或服务。先启动 API 服务，再通过 HTTP 调用：

```bash
# 终端 1：启动服务
$ python main.py
# 选择 2. Web API 模式
# 服务跑在 http://127.0.0.1:5555

# 终端 2：调用 API
$ curl -X POST http://127.0.0.1:5555/douyin/video \
  -H "Content-Type: application/json" \
  -d '{"url": "https://v.douyin.com/xxxxx", "quality": "1080p"}'
```

API 文档在 `http://127.0.0.1:5555/docs`（Swagger），可以直接在浏览器里试调。如果需要批量下载，在自己的脚本里循环调用就行，不用操作交互菜单。

### 3.3 Docker 模式

不想折腾 Python 环境时最简单的方式：

```bash
docker pull joeanamier/tiktok-downloader
docker run --name tiktok-downloader \
  -p 5555:5555 \
  -v tiktok_downloader_volume:/app/Volume \
  -it joeanamier/tiktok-downloader
```

容器启动后进入的仍然是终端交互界面，操作和 3.1 完全一样。下载的文件会保存在 Docker volume 里，可以通过 `docker cp` 导出。

### 三种方式怎么选

| 场景 | 推荐方式 |
|------|----------|
| 偶尔下载几个视频，不想写代码 | 终端交互 |
| 需要集成到自己的脚本或定时任务 | Web API |
| 不想装 Python 和 FFmpeg | Docker |
| 需要批量下载 + 后续自动化处理 | Web API |

## 四，技术架构

### 4.1 分层结构

```
用户界面层
├── 终端交互 (Rich 美化)
└── Web API (FastAPI, 端口 5555)

业务逻辑层
├── Account  账号管理
├── Video    视频处理
├── Comment  评论处理
├── Live     直播处理
└── Search   搜索处理

HTTP 请求层
├── httpx 异步客户端
├── 智能延时（避免被限流）
└── Cookie 管理

存储层
├── 文件系统（临时目录 → 最终目录）
├── JSON 配置文件
└── SQLite 数据库

外部依赖
├── FFmpeg  视频处理
├── httpx   异步 HTTP
└── Rich    终端美化
```

### 4.2 项目结构

```
TikTokDownloader/
├── src/
│   ├── core/                  # 核心模块
│   │   ├── account.py         # 账号模块
│   │   ├── video.py           # 视频模块
│   │   ├── comment.py         # 评论模块
│   │   ├── live.py            # 直播模块
│   │   ├── search.py          # 搜索模块
│   │   └── extractors.py      # 数据提取器
│   ├── api/                   # Web API
│   │   ├── routes.py          # API 路由
│   │   ├── schemas.py         # 数据模型
│   │   └── dependencies.py    # 依赖
│   ├── utils/                 # 工具
│   │   ├── httpx.py           # HTTP 客户端
│   │   ├── cookie.py          # Cookie 管理
│   │   ├── file.py            # 文件处理
│   │   └── config.py          # 配置管理
│   └── main.py                # 入口
├── static/images/             # 静态资源
├── docs/                      # 文档
├── main.py                    # 主入口
├── pyproject.toml             # 项目配置
├── requirements.txt           # 依赖
├── Dockerfile                 # Docker 配置
└── README.md
```

### 4.3 核心技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| HTTP 客户端 | httpx | 异步并发请求，比 requests 更适合批量下载 |
| 终端 UI | Rich | 美化终端输出，让交互菜单更可读 |
| Web 框架 | FastAPI | 轻量 API 服务，自带 Swagger 文档 |
| 视频处理 | FFmpeg | 视频合并、格式转换 |
| 数据存储 | SQLite | 本地数据库，记录下载历史 |
| 打包 | PyInstaller | 生成可执行文件，免安装 Python |

## 五，安装

### 5.1 环境要求

| 要求 | 版本 |
|------|------|
| Python | 3.12+ |
| FFmpeg | 最新版 |
| 内存 | 4GB+ |
| 磁盘 | 10GB+ |

### 5.2 安装 Python 依赖

```bash
# 推荐：用 uv 安装（速度快）
uv sync --no-dev

# 或者用 pip
pip install -r requirements.txt

# 从源码安装
git clone https://github.com/JoeanAmier/TikTokDownloader.git
cd TikTokDownloader
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

### 5.3 安装 FFmpeg

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# Windows
# 下载 https://ffmpeg.org/download.html，添加到 PATH
```

### 5.4 可执行文件

前往 [Releases](https://github.com/JoeanAmier/TikTokDownloader/releases/latest) 下载对应平台的可执行文件。macOS 用户需要先移除安全标记：

```bash
xattr -cr ./path/to/TikTokDownloader
```

## 六，使用

### 6.1 Cookie 配置（必须先做）

Cookie 是项目的命门——抖音和 TikTok 的大部分接口都需要登录态。过期或无效的 Cookie 会导致下载失败。

```
获取 Cookie 的步骤：
1. 浏览器登录抖音/TikTok 网页版
2. 打开开发者工具 → Application → Cookies
3. 复制全部 Cookie 内容到剪贴板
4. 在程序中选择"从剪贴板读取 Cookie"
```

程序也支持从浏览器直接读取 Cookie（Chrome、Edge、Firefox），但需要以管理员权限运行。

### 6.2 终端交互模式

```bash
python main.py
# 选择 1. 终端交互模式
# 然后按菜单选择功能：
# 1. 批量下载账号作品（发布/喜欢/收藏/收藏夹）
# 2. 批量下载链接作品
# 3. 获取直播拉流地址
# 4. 下载直播视频
# 5. 采集作品评论数据
# 6. 批量下载合集作品
# 7. 批量下载合辑作品
```

### 6.3 Web API 模式

```bash
# 启动服务
python main.py
# 选择 2. Web API 模式

# 访问文档
open http://127.0.0.1:5555/docs
```

API 调用示例（Python）：

```python
from httpx import post
from rich import print

def demo():
    headers = {"token": ""}
    data = {
        "url": "https://v.douyin.com/xxxxx",
        "quality": "1080p"
    }
    api = "http://127.0.0.1:5555/douyin/video"
    response = post(api, json=data, headers=headers)
    print(response.json())

demo()
```

### 6.4 代理设置

访问 TikTok 必须配置代理。在 `settings.json` 中设置：

```json
{
    "proxy": "http://127.0.0.1:7890",
    "timeout": 30,
    "max_retries": 3
}
```

## 七，API 参考

| 端点 | 方法 | 说明 |
|------|------|------|
| `/douyin/video` | POST | 下载抖音视频 |
| `/douyin/comment` | POST | 采集抖音评论 |
| `/douyin/user` | POST | 获取用户信息 |
| `/tiktok/video` | POST | 下载 TikTok 视频 |
| `/health` | GET | 健康检查 |

请求示例：

```bash
# 下载抖音视频
curl -X POST http://127.0.0.1:5555/douyin/video \
  -H "Content-Type: application/json" \
  -d '{"url": "https://v.douyin.com/xxxxx", "quality": "1080p", "watermark": false}'

# 采集评论
curl -X POST http://127.0.0.1:5555/douyin/comment \
  -H "Content-Type: application/json" \
  -d '{"url": "https://v.douyin.com/xxxxx", "pages": 10}'
```

响应格式：

```json
{
  "status": "success",
  "data": {
    "aweme_id": "1234567890",
    "title": "视频标题",
    "author": "作者昵称",
    "download_url": "https://example.com/video.mp4",
    "cover_url": "https://example.com/cover.jpg"
  }
}
```

## 八，配置详解

```json
// settings.json
{
    "download": {
        "path": "./Download",
        "concurrency": 5,
        "chunk_size": 1048576,
        "retry": 3
    },
    "network": {
        "proxy": "",
        "timeout": 30,
        "delay": 1.0
    },
    "cookie": {
        "douyin": "",
        "tiktok": ""
    },
    "ffmpeg": {
        "path": "ffmpeg",
        "threads": 4
    }
}
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `download.path` | 下载路径 | `./Download` |
| `download.concurrency` | 并发数（建议 3-8） | 5 |
| `network.proxy` | 代理地址，TikTok 必填 | 空 |
| `network.timeout` | 请求超时（秒） | 30 |
| `network.delay` | 请求间隔（秒），避免被限流 | 1.0 |

## 九，故障排除

### 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 下载失败 | Cookie 过期 | 重新登录网页版，更新 Cookie |
| 视频清晰度低 | Cookie 过期，降级到无水印低清 | 同上 |
| 请求频繁被限 | 并发太高或请求间隔太短 | 降低并发数，增大 `network.delay` |
| 无法读取浏览器 Cookie | 权限不足 | 以管理员权限运行，或改用剪贴板方式 |
| TikTok 访问超时 | 未配置代理 | 在 `settings.json` 中设置 `network.proxy` |

### Cookie 更新的触发信号

当你发现下载的视频清晰度明显下降、或者程序反复提示"下载失败"时，Cookie 大概率已经过期。抖音和 TikTok 的登录态通常保持几小时到几天不等，取决于账号活跃度。建议在批量下载前先检查一次。

## 十，相关项目

同作者维护的另外两个下载器，结构类似，如果同时需要采集小红书和快手数据可以考虑：

| 项目 | 说明 |
|------|------|
| **XHS-Downloader** | 小红书下载器 |
| **KS-Downloader** | 快手下载器 |

参考项目（如果你需要更底层的 API 封装）：

| 项目 | 说明 |
|------|------|
| f2 | Johnserf-Seed 的抖音/TikTok API |
| Douyin_TikTok_Download_API | Evil0ctal 的下载 API |
| TikTok-web-reverse-engineering | Web 逆向工程参考 |

## 十一，采用建议

TikTokDownloader 适合以下场景：

- **数据采集**：你需要批量下载某个账号的全部作品，或者导出评论做内容分析。用终端交互模式就够了。
- **自动化流水线**：你要把下载能力集成到自己的脚本或服务里，定时拉取数据。用 Web API 模式，调 HTTP 接口比操作菜单稳定得多。
- **快速体验**：不想折腾 Python 和 FFmpeg 的环境配置。用 Docker，一条命令启动。

不太适合的场景：

- 只需要偶尔下载一两个视频——浏览器开发者工具抓包更轻量。
- 需要绕过平台的反爬机制——TikTokDownloader 依赖有效的 Cookie，不提供绕过登录或验证码的能力。
- 需要 TikTok 的评论、搜索或热榜数据——目前这些能力只在抖音线支持。

如果你刚开始用，建议的路径是：**先跑通终端交互模式下载一个视频 → 确认 Cookie 和代理都正常 → 再尝试批量下载**。等熟悉了流程，再决定是否需要切到 Web API 或 Docker。

## 十二，场景问答（FAQ）

**Q：我只需要下载 3 个视频做剪辑素材，用这个工具合适吗？**

不太合适。单个视频用浏览器开发者工具（F12 → Network → 搜索 `.mp4`）直接抓链接更快。TikTokDownloader 的价值在「批量」——要下载几十上百个视频才有必要折腾 Cookie 和环境。

**Q：Cookie 配好了但还是下载失败，按什么顺序排查？**

先跑一个最小验证：下载单个视频，看报错信息。如果提示 Cookie 相关，大概率是登录态过期——抖音的 Cookie 短则几小时、长则几天，重新从浏览器复制一次。如果是 TikTok 超时，检查 `settings.json` 里的 `network.proxy` 是否已填。如果报错跟视频文件有关，检查 FFmpeg 是否在 `PATH` 里（命令行输入 `ffmpeg -version` 验证）。

**Q：想每天凌晨自动下载某个抖音账号的新作品，怎么做？**

Web API 模式。步骤：先启动 API 服务并常驻后台，然后在脚本里调 `/douyin/user` 获取作品列表，遍历列表逐个调 `/douyin/video` 下载。脚本挂到 cron 或 systemd timer 上就行。注意：Cookie 会过期，定时任务跑几天后大概率要更新 Cookie——可以在脚本里加一个失败告警。

**Q：Docker 模式下下载的文件怎么取出来？**

默认存在 Docker volume 里，用 `docker cp tiktok-downloader:/app/Volume ./本地目录` 导出。更好的做法是启动时直接挂载宿主机目录：`-v /你的本地目录:/app/Volume`，文件会直接出现在本地。

**Q：抖音和 TikTok 的 Cookie 能混用吗？**

不能。两条线对应完全不同的 API 端点，抖音的 Cookie 对 TikTok 接口无效，反过来一样。如果你想同时采集两边数据，需要分别登录并分别保存 Cookie——`settings.json` 里给两条线留了独立的 Cookie 字段。

## 自查

读完这篇文章，试试回答下面几个问题。如果能不翻上文答出来，说明核心点已经抓住了：

1. 抖音线和 TikTok 线在评论采集、搜索/热榜能力上有什么差异？
2. TikTok 下载一直超时，应该检查哪个配置项？
3. Web API 模式下，批量下载一个账号的全部发布作品，大致流程是什么？
4. Cookie 过期时，程序通常会有什么表现？应该怎么更新？

---

**相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/JoeanAmier/TikTokDownloader |
| Releases | https://github.com/JoeanAmier/TikTokDownloader/releases/latest |
| 文档 | https://github.com/JoeanAmier/TikTokDownloader/wiki/Documentation |
| Discord | https://discord.com/invite/ZYtmgKud9Y |

---

_🦞 本文由钳岳星君撰写，基于 TikTokDownloader (14k Stars)_