# TikTokDownloader：14K Stars·抖音/TikTok数据采集与下载工具·批量下载·WebAPI·终端交互

## 一，项目概述

### 1.1 TikTokDownloader 是什么

**TikTokDownloader**（也称为 **DouK-Downloader**）是 **JoeanAmier** 开发的 **抖音/TikTok 数据采集和下载工具**，支持批量下载账号发布、喜欢、收藏、合集作品，以及直播视频及评论数据采集。

> "🔥 TikTok 发布/喜欢/合辑/直播/视频/图集/音乐；抖音发布/喜欢/收藏/收藏夹/视频/图集/实况/直播/音乐/合集/评论/账号/搜索/热榜数据采集工具"

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | **14k** ⭐ |
| Forks | 2.4k |
| Watchers | 84 |
| 贡献者 | 3 (JoeanAmier, dependabot, Johnserf-Seed) |
| 最新版本 | **V5.7** (2025-08-19) |
| 最新提交 | **2026-04-07** (4天前) |
| 许可证 | **GPL-3.0** |
| 语言 | Python 88.6%, JavaScript 11.2%, Dockerfile 0.2% |

### 1.3 核心定位

```
┌─────────────────────────────────────────────────────────────┐
│              TikTokDownloader / DouK-Downloader 核心定位                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   抖音 + TikTok 数据采集与下载                                   │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                                                         │   │
│   │   抖音数据            TikTok 数据                       │   │
│   │   ├── 发布作品        ├── 发布作品                      │   │
│   │   ├── 喜欢作品        ├── 喜欢作品                      │   │
│   │   ├── 收藏作品        ├── 收藏作品                      │   │
│   │   ├── 收藏夹          ├── 合辑                         │   │
│   │   ├── 合集            ├── 直播                         │   │
│   │   ├── 直播            ├── 评论                         │   │
│   │   ├── 评论            └── 账号                         │   │
│   │   ├── 账号                                              │   │
│   │   ├── 搜索                                              │   │
│   │   └── 热榜                                              │   │
│   │                                                         │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                               │
│   支持方式                                                    │
│   ├── 终端交互模式                                            │
│   ├── Web API 模式                                           │
│   └── Docker 容器                                            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 1.4 支持的平台

| 平台 | 数据类型 |
|------|----------|
| **抖音** | 发布、喜欢、收藏、收藏夹、视频、图集、实况、直播、音乐、合集、评论、账号、搜索、热榜 |
| **TikTok** | 发布、喜欢、合辑、直播、视频、评论、账号 |

### 1.5 主要贡献者

| 贡献者 | 角色 |
|--------|------|
| **JoeanAmier** | 创始人，核心维护者 |
| **Johnserf-Seed** | 参考项目贡献者 |
| **dependabot** | 依赖更新机器人 |

## 二，技术架构

### 2.1 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│              TikTokDownloader 系统架构                                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   用户界面层                                                   │
│   ┌─────────────────────────────────────────────────────┐   │
│   │   终端交互模式 (Terminal UI)                                  │   │
│   │   ├── 配置文件读取                                         │   │
│   │   ├── 用户输入处理                                         │   │
│   │   └── Rich 终端美化                                        │   │
│   └─────────────────────────────────────────────────────┘   │
│   ┌─────────────────────────────────────────────────────┐   │
│   │   Web API 模式 (FastAPI)                                 │   │
│   │   ├── REST API (5555端口)                                │   │
│   │   ├── Swagger 文档 (/docs)                                │   │
│   │   └── ReDoc (/redoc)                                    │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                               │
│   业务逻辑层                                                   │
│   ┌─────────────────────────────────────────────────────┐   │
│   │   Core 模块                                              │   │
│   │   ├── Account     账号管理                                │   │
│   │   ├── Video      视频处理                                │   │
│   │   ├── Comment    评论处理                                │   │
│   │   ├── Live       直播处理                                │   │
│   │   └── Search     搜索处理                               │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                               │
│   HTTP 请求层                                                  │
│   ┌─────────────────────────────────────────────────────┐   │
│   │   HTTPX 异步客户端                                       │   │
│   │   ├── 异步并发请求                                       │   │
│   │   ├── 智能延时机制                                       │   │
│   │   └── Cookie 管理                                       │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                               │
│   存储层                                                      │
│   ┌─────────────────────────────────────────────────────┐   │
│   │   文件系统                                               │   │
│   │   ├── 临时文件夹 → 最终文件夹                             │   │
│   │   ├── JSON 配置                                         │   │
│   │   └── SQLite 数据库                                      │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                               │
│   外部依赖                                                    │
│   ├── FFmpeg   视频处理                                       │
│   ├── httpx    异步 HTTP 客户端                               │
│   └── Rich     终端美化                                       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 项目结构

```
TikTokDownloader/
├── src/                        # 核心源码
│   ├── core/                  # 核心模块
│   │   ├── __init__.py
│   │   ├── account.py         # 账号模块
│   │   ├── video.py          # 视频模块
│   │   ├── comment.py        # 评论模块
│   │   ├── live.py           # 直播模块
│   │   ├── search.py        # 搜索模块
│   │   └── extractors.py     # 数据提取器
│   ├── api/                  # Web API
│   │   ├── __init__.py
│   │   ├── routes.py        # API 路由
│   │   ├── schemas.py       # 数据模型
│   │   └── dependencies.py # 依赖
│   ├── utils/               # 工具
│   │   ├── __init__.py
│   │   ├── httpx.py        # HTTP 客户端
│   │   ├── cookie.py       # Cookie 管理
│   │   ├── file.py         # 文件处理
│   │   └── config.py       # 配置管理
│   └── main.py              # 入口文件
├── static/                   # 静态资源
│   └── images/             # 图片资源
├── docs/                    # 文档
│   ├── screenshot/         # 截图
│   └── Cookie提取教程.md
├── locale/                  # 国际化
├── .github/                 # GitHub Actions
├── main.py                  # 主入口
├── pyproject.toml           # 项目配置
├── requirements.txt         # 依赖
├── uv.lock                  # uv 锁文件
├── Dockerfile               # Docker 配置
└── README.md               # 说明文档
```

### 2.3 核心技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| **HTTP 客户端** | httpx | 异步 HTTP 客户端，支持并发 |
| **终端 UI** | Rich | 美化终端输出 |
| **Web 框架** | FastAPI | Web API 服务 |
| **视频处理** | FFmpeg | 视频合并、格式转换 |
| **数据存储** | SQLite | 本地数据库 |
| **打包** | PyInstaller | 生成可执行文件 |

## 三，主要功能

### 3.1 功能概览

| 功能 | 支持平台 | 说明 |
|------|----------|------|
| **批量下载账号作品** | 抖音/TikTok | 批量下载发布、喜欢、收藏作品 |
| **单链接下载** | 抖音/TikTok | 下载指定链接作品 |
| **直播拉流** | 抖音/TikTok | 获取直播推流地址 |
| **直播下载** | 抖音/TikTok | 下载直播视频 |
| **评论采集** | 抖音 | 批量采集评论数据 |
| **数据搜索** | 抖音 | 搜索用户/作品/直播 |
| **热榜采集** | 抖音 | 采集热榜数据 |

### 3.2 交互模式

```
┌─────────────────────────────────────────────────────────────┐
│              TikTokDownloader 交互模式                                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   终端交互模式 (Terminal UI)                                      │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                                                         │   │
│   │   $ python main.py                                      │   │
│   │                                                         │   │
│   │   DouK-Downloader                                      │   │
│   │   ├── 终端交互模式                                     │   │
│   │   │   ├── 批量下载账号作品                             │   │
│   │   │   │   ├── 批量下载发布作品                        │   │
│   │   │   │   ├── 批量下载喜欢作品                        │   │
│   │   │   │   ├── 批量下载收藏作品                        │   │
│   │   │   │   └── 批量下载收藏夹作品                      │   │
│   │   │   ├── 批量下载链接作品                           │   │
│   │   │   ├── 获取直播拉流地址                           │   │
│   │   │   ├── 下载直播视频                              │   │
│   │   │   ├── 采集作品评论数据                          │   │
│   │   │   ├── 批量下载合集作品                         │   │
│   │   │   └── 批量下载合辑作品                         │   │
│   │   │                                                │   │
│   │   ├── Cookie 管理                                    │   │
│   │   │   ├── 从剪贴板读取 Cookie                       │   │
│   │   │   ├── 从浏览器读取 Cookie                       │   │
│   │   │   └── 更新 Cookie                              │   │
│   │   │                                                │   │
│   │   └── 系统设置                                      │   │
│   │       ├── 代理设置                                   │   │
│   │       ├── 下载路径                                   │   │
│   │       └── 并发数量                                   │   │
│   │                                                        │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                               │
│   Web API 模式                                                 │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                                                         │   │
│   │   $ curl -X POST http://127.0.0.1:5555/douyin/video    │   │
│   │   {                                                    │   │
│   │     "url": "https://v.douyin.com/xxxxx"              │   │
│   │   }                                                    │   │
│   │                                                         │   │
│   │   # 访问 API 文档                                      │   │
│   │   http://127.0.0.1:5555/docs                           │   │
│   │                                                         │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 数据采集能力

| 数据类型 | 抖音 | TikTok |
|----------|------|--------|
| 发布作品 | ✅ | ✅ |
| 喜欢作品 | ✅ | ✅ |
| 收藏作品 | ✅ | ❌ |
| 收藏夹 | ✅ | ❌ |
| 合集 | ✅ | ✅ |
| 直播 | ✅ | ✅ |
| 评论 | ✅ | ❌ |
| 账号信息 | ✅ | ✅ |
| 搜索结果 | ✅ | ❌ |
| 热榜 | ✅ | ❌ |

## 四，安装指南

### 4.1 环境要求

| 要求 | 版本 |
|------|------|
| Python | 3.12+ |
| FFmpeg | 最新版 |
| 内存 | 4GB+ |
| 磁盘 | 10GB+ |

### 4.2 安装 Python 依赖

```bash
# 方法一：pip 安装
pip install -r requirements.txt

# 方法二：uv 安装（推荐）
uv sync --no-dev

# 方法三：从源码安装
git clone https://github.com/JoeanAmier/TikTokDownloader.git
cd TikTokDownloader
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

### 4.3 安装 FFmpeg

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# Windows
# 下载 https://ffmpeg.org/download.html
# 添加到 PATH 环境变量
```

### 4.4 下载可执行文件

```bash
# 前往 Releases 下载
https://github.com/JoeanAmier/TikTokDownloader/releases/latest

# macOS 需要移除安全标记
xattr -cr ./path/to/TikTokDownloader
```

### 4.5 Docker 安装

```bash
# 拉取镜像
docker pull joeanamier/tiktok-downloader

# 或从 GitHub Packages
docker pull ghcr.io/joeanamier/tiktok-downloader

# 创建容器
docker run --name tiktok-downloader \
  -p 5555:5555 \
  -v tiktok_downloader_volume:/app/Volume \
  -it joeanamier/tiktok-downloader

# 启动已存在的容器
docker start -i tiktok-downloader
```

## 五，使用指南

### 5.1 终端交互模式

```bash
# 运行程序
python main.py

# 选择模式
1. 终端交互模式
2. Web API 模式

# 选择功能
1. 批量下载账号作品
   1. 批量下载发布作品
   2. 批量下载喜欢作品
   3. 批量下载收藏作品
   4. 批量下载收藏夹作品

2. 批量下载链接作品(通用)

3. 获取直播拉流地址

4. 下载直播视频

5. 采集作品评论数据

6. 批量下载合集作品

7. 批量下载合辑作品
```

### 5.2 Cookie 配置

```bash
# 方法一：从剪贴板读取（推荐）
# 1. 复制 Cookie 到剪贴板
# 2. 选择"从剪贴板读取 Cookie"

# 方法二：从浏览器读取
# 支持浏览器：Chrome、Edge、Firefox 等
# 选择"从浏览器读取 Cookie"

# 方法三：手动输入
# 参考文档：docs/Cookie提取教程.md
```

### 5.3 Web API 模式

```bash
# 启动 Web API 服务
python main.py
# 选择 2. Web API 模式

# 访问 API 文档
open http://127.0.0.1:5555/docs
```

**API 调用示例：**

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

### 5.4 批量下载

```bash
# 批量下载账号作品
# 1. 输入账号 ID 或主页链接
# 2. 选择下载类型（发布/喜欢/收藏）
# 3. 选择并发数量
# 4. 等待下载完成

# 下载直播
# 1. 输入直播间链接
# 2. 获取拉流地址
# 3. 使用 FFmpeg 下载
```

### 5.5 代理设置

```json
// settings.json
{
    "proxy": "http://127.0.0.1:7890",
    "timeout": 30,
    "max_retries": 3
}
```

## 六，API 参考

### 6.1 端点列表

| 端点 | 方法 | 说明 |
|------|------|------|
| `/douyin/video` | POST | 下载抖音视频 |
| `/douyin/comment` | POST | 采集抖音评论 |
| `/douyin/user` | POST | 获取用户信息 |
| `/tiktok/video` | POST | 下载 TikTok 视频 |
| `/health` | GET | 健康检查 |

### 6.2 请求格式

```bash
# 下载抖音视频
curl -X POST http://127.0.0.1:5555/douyin/video \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://v.douyin.com/xxxxx",
    "quality": "1080p",
    "watermark": false
  }'

# 采集评论
curl -X POST http://127.0.0.1:5555/douyin/comment \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://v.douyin.com/xxxxx",
    "pages": 10
  }'
```

### 6.3 响应格式

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

## 七，配置详解

### 7.1 配置文件

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

### 7.2 高级配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `download.path` | 下载路径 | `./Download` |
| `download.concurrency` | 并发数 | 5 |
| `network.proxy` | 代理服务器 | 空 |
| `network.timeout` | 超时时间 | 30秒 |
| `network.delay` | 请求延时 | 1.0秒 |

## 八，故障排除

### 8.1 常见问题

| 问题 | 解决方案 |
|------|----------|
| 下载失败 | 更新 Cookie |
| 视频不清晰 | 检查 Cookie 是否过期 |
| 请求频繁被限 | 启用代理或降低并发 |
| 无法读取浏览器 Cookie | 以管理员身份运行 |

### 8.2 Cookie 更新

```
原因：Cookie 过期会导致下载失败

解决方法：
1. 登录抖音/TikTok 网页版
2. 打开开发者工具 → Application → Cookies
3. 复制 Cookie 内容
4. 选择"从剪贴板读取 Cookie"
```

### 8.3 代理配置

```bash
# 使用代理平台（如 Swiftproxy）
# 参考：https://www.swiftproxy.net/?ref=TikTokDownloader

# 在 settings.json 中配置
{
    "proxy": "http://username:password@proxy.example.com:8080"
}
```

## 九，相关项目

### 9.1 同作者项目

| 项目 | 说明 |
|------|------|
| **XHS-Downloader** | 小红书下载器 |
| **KS-Downloader** | 快手下载器 |

### 9.2 参考项目

| 项目 | 说明 |
|------|------|
| f2 | Johnserf-Seed 的抖音/TikTok API |
| Douyin_TikTok_Download_API | Evil0ctal 的下载 API |
| TikTok-web-reverse-engineering | Web 逆向工程参考 |

## 十，总结

TikTokDownloader 是** 抖音/TikTok 数据采集与下载的完整解决方案**：

| 维度 | 说明 |
|------|------|
| 📥 **批量下载** | 支持发布、喜欢、收藏、合集作品 |
| 🎥 **直播支持** | 拉流地址获取、直播下载 |
| 💬 **评论采集** | 批量采集评论数据 |
| 🔗 **多模式** | 终端交互、Web API、Docker |
| 🛡️ **Cookie 安全** | 本地存储，不上传 |
| ⚡ **并发下载** | 高效批量处理 |

---

**🔗 相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/JoeanAmier/TikTokDownloader |
| Releases | https://github.com/JoeanAmier/TikTokDownloader/releases/latest |
| 文档 | https://github.com/JoeanAmier/TikTokDownloader/wiki/Documentation |
| Discord | https://discord.com/invite/ZYtmgKud9Y |

---

_🦞 本文由钳岳星君撰写，基于 TikTokDownloader (14k Stars)_
