---
title: "CLIProxyAPI 上手与迁移指南：把 CLI 订阅变成 OpenAI 兼容 API"
date: "2026-04-12T18:00:00+08:00"
lastmod: 2026-10-02
slug: cliproxyapi-openai-compatible-api-proxy-guide
github_repo: "router-for-me/CLIProxyAPI"
source_key: "gh:router-for-me/CLIProxyAPI"
description: "CLIProxyAPI 把 Claude Code、Codex、Antigravity 等 CLI 订阅凭据包装成本地 OpenAI/Gemini/Claude 兼容 API。本文按当前 v8 版本梳理安装、配置、账号登录与客户端接入，并给出旧教程失效点的版本对照。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "OpenAI Codex", "API 代理", "Go"]
---

# CLIProxyAPI 上手与迁移指南：把 CLI 订阅变成 OpenAI 兼容 API

如果你手里有 Claude Code、Codex、Antigravity 这类工具的订阅账号，会发现这些凭据只能在各自的 CLI 里用——想在自己的程序、脚本或别的客户端里调用，没有现成的 API 可用。CLIProxyAPI（[router-for-me/CLIProxyAPI](https://github.com/router-for-me/CLIProxyAPI)）解决的就是这个问题：它在本地起一个代理服务，把这些 CLI 凭据包装成 OpenAI、Gemini、Claude、Codex 四种协议都兼容的 API 接口，任何兼容客户端或 SDK 都能直接接。

这个项目迭代很快。本文初稿写于 2026 年 4 月，半年内项目从 v5 走到 v8，配置结构和不少行为已经变了——当时流传的一批教程（包括本站旧稿的部分说法）今天照着做会直接失败。本文按 2026-10-02 的 v8.0.10 重写，文末给出旧说法与当前事实的对照表。

## 它解决什么问题

CLIProxyAPI 是一个 Go 写的代理服务器（MIT 协议），核心能力有三块：

- **凭据转协议**。用 OAuth 登录 Codex、Claude、Antigravity（Google 账号）、Kimi、xAI、Meta、Devin 等渠道后，这些订阅凭据变成标准 API 端点背后的上游。也支持直接配置各家 API key、Vertex AI 服务账号。
- **多账号轮询**。同一渠道可以登录多个账号，服务按 round-robin 负载均衡自动切换，单个账号配额耗尽时由路由层处理冷却与重试。
- **协议兼容**。对外同时暴露 OpenAI Chat Completions、OpenAI Responses、Gemini、Claude 四套协议，客户端不需要改代码就能切换上游模型。

2026-10-02 的读数：53,761 stars、8,107 forks，最新版本 v8.0.10（发版节奏接近日更）。

## 先分清两把钥匙

这是理解配置文件的关键，也是旧教程最容易搞错的地方：CLIProxyAPI 里有两类完全不同的密钥。

**访问密钥（`access.api-keys`）**是客户端访问这个代理时用的密码，由你自己随便定义，跟任何上游厂商无关。客户端带着它请求代理，代理验证身份。

**上游凭据**是代理替你去调各家服务用的：OAuth 登录产生的凭据文件、或者你在 `api-keys` 配置段里填的各家 API key。它们永远不会暴露给客户端。

旧教程里"把 Claude API Key 填进 keys 列表客户端就能用"之类的写法，混淆的正是这两层。

## 安装

官方文档站是 [help.router-for.me](https://help.router-for.me/)（有[中文版](https://help.router-for.me/cn/)）。注意：CLIProxyAPI 是 Go 二进制分发的项目，npm 上没有官方包，`npm install -g cliproxyapi` 装不到任何东西。可用的安装路径有五条。

macOS 用 Homebrew（官方仓库收录，当前 8.0.10）：

```bash
brew install cliproxyapi
brew services start cliproxyapi
```

Homebrew 的默认配置文件在 `$(brew --prefix)/etc/cliproxyapi.conf`。如果想像 Linux 习惯那样把配置放在 `~/.cli-proxy-api/config.yaml`，可以把它符号链接过去（目标文件必须先存在，否则服务起不来）。

Linux 一键脚本或 AUR：

```bash
curl -fsSL https://raw.githubusercontent.com/router-for-me/cliproxyapi-installer/refs/heads/master/cliproxyapi-installer | bash
# Arch 系也可以
yay -S cli-proxy-api-bin
```

脚本方式装完用 systemd 用户服务管理：

```bash
systemctl --user start cli-proxy-api
systemctl --user enable cli-proxy-api
```

Windows 从 [GitHub Releases](https://github.com/router-for-me/CLIProxyAPI/releases) 下载压缩包直接运行；或者用官方推荐的桌面客户端 [EasyCLIProxyAPI](https://github.com/router-for-me/EasyCLIProxyAPI)，带图形配置界面、托盘和一键启停。

Docker 方式（镜像 `eceasy/cli-proxy-api`）：

```bash
docker run --rm -p 8317:8317 \
  -v /path/to/config.yaml:/CLIProxyAPI/config.yaml \
  -v /path/to/auth-dir:/root/.cli-proxy-api \
  -v /path/to/plugins-dir:/CLIProxyAPI/plugins \
  eceasy/cli-proxy-api:latest
```

从源码构建需要 Go 1.26+，产物叫 `cli-proxy-api`：

```bash
git clone https://github.com/router-for-me/CLIProxyAPI.git
cd CLIProxyAPI
go build -o cli-proxy-api ./cmd/server
./cli-proxy-api --config config.yaml
```

没有 `start` 之类的子命令——它就是单个二进制，直接运行即启动服务；登录、导入等操作通过 flag 触发。

## 配置：v8 布局的关键字段

完整模板见仓库的 `config.example.yaml`（v8 版约 1200 行，大部分是注释掉的示例）。启动前只需要关心几个字段：

```yaml
config-version: 8

server:
  host: ""        # 留空绑定所有接口；只本机用就填 127.0.0.1
  port: 8317      # 默认端口，从 v5 时代到现在一直是 8317

access:
  api-keys:       # 客户端访问密钥（自己定义，不是上游 key）
    - "sk-my-local-key-1"

management:
  secret-key: ""  # 管理密钥；留空 = 管理 API 整个禁用（404）

oauth:
  auth-dir: "~/.cli-proxy-api"  # OAuth 凭据文件目录
```

几点说明：

- **默认端口是 8317**，不是某些教程写的 3000 或 8080。Docker 的端口映射、Homebrew 服务的配置、源码构建的默认值都是这个数。
- **`access.api-keys` 不能留模板值**。配置里还是 `your-api-key-1` 这类占位符时，服务会进入安全模式：代理端点全部禁用，只开放管理页面让你先改配置。这不是故障，是故意的。
- **模型列表不需要配置**。`/v1/models` 返回的是所有已登录上游凭据可用模型的聚合结果，配置文件里没有 `models` 字段。
- **旧配置文件可以继续用**。v8 加载时会接受旧的扁平写法（`api-keys`、`remote-management` 等顶层键），同一字段新旧两种写法并存时以 v8 值为准；通过管理 API 的 v8 接口成功写入一次配置后，旧写法会被迁移成新结构。

## 登录上游账号

OAuth 登录用 flag 触发，登录一次后凭据落在 `auth-dir`，之后服务启动自动加载并刷新 token：

```bash
./cli-proxy-api --config config.yaml --claude-login      # Claude 订阅
./cli-proxy-api --config config.yaml --codex-login       # ChatGPT/Codex 订阅
./cli-proxy-api --config config.yaml --antigravity-login # Google（Antigravity/Gemini）
./cli-proxy-api --config config.yaml --kimi-login        # Kimi
```

完整的渠道 flag：`--codex-login`（另有 `--codex-device-login` 设备码流程）、`--claude-login`、`--antigravity-login`、`--kimi-login`、`--kimi-ai-login`、`--xai-login`、`--devin-login`、`--meta-login`。`--no-browser` 禁止自动开浏览器，`--oauth-callback-port` 改回调端口。各家默认回调端口不同：Codex 用 1455，Claude 用 54545，Antigravity 用 51121，本机有端口冲突时需要留意。

Gemini 侧的另外两条路：Vertex AI 走 `--vertex-import` 导入服务账号 JSON；AI Studio 与 Gemini API key 则是普通 API key 上游，配在 `api-keys` 段的对应 provider 分组下。

## 接入客户端

服务起来后，OpenAI、Claude、Gemini、Codex 四套协议的端点挂在同一端口上，都接受 `Authorization: Bearer <访问密钥>` 认证：

| 客户端说的协议 | 端点 |
|---|---|
| OpenAI Chat Completions | `POST /v1/chat/completions` |
| OpenAI Responses | `POST /v1/responses` |
| Claude（Anthropic） | `POST /v1/messages` |
| Gemini | `POST /v1beta/models/<model>:<action>` |
| Codex CLI 直通 | `/backend-api/codex` |

拿 curl 验证服务是否就绪：

```bash
curl http://127.0.0.1:8317/healthz
curl http://127.0.0.1:8317/v1/models \
  -H "Authorization: Bearer sk-my-local-key-1"
```

以 Claude Code 为例，把 API Base URL 指到 `http://127.0.0.1:8317`、API Key 填 `access.api-keys` 里的任意一个即可。Gemini 协议的客户端把 base URL 指到 `/v1beta`。

## 管理面板与远程管理

浏览器访问 `http://127.0.0.1:8317/management.html` 可以打开内置管理面板（首次访问自动从 [CPAMC](https://github.com/router-for-me/Cli-Proxy-API-Management-Center) 仓库拉取面板资源），查看凭据状态、改配置、管理插件。三个要点：

- 面板和 API 跟主服务**同一个端口**，不存在独立的"管理端口"。
- `management.secret-key` 留空时管理 API 整体返回 404——面板打不开先查这个。
- `management.allow-remote` 默认 `false`，只有 localhost 能访问；要暴露给局域网需显式打开，并务必设置强密钥。

不想用浏览器的话，`--tui` 启动终端管理界面（`--standalone` 让它内嵌一个本地服务端，`--management-base-url` 连远程实例）。

管理 API 本身有两代路由（`/v0/management` 和 `/v8/management`），v0 兼容旧客户端，v8 配套 v8 配置结构。

## 使用统计：内置功能已移除

不少旧教程提到"内置统计、按 Key 按模型统计 Token"——这在 v6.10.0（2026-05-01）起已经移除。现在配置里的 `observability.usage.usage-statistics-enabled` 只控制一个内存中的聚合队列，默认关闭，仅供管理 API 短时读取（默认保留 60 秒），不落盘、没有历史曲线。

需要用量统计的话，官方 README 指向两个生态项目：[CPA Usage Keeper](https://github.com/Willxup/cpa-usage-keeper)（独立持久化与可视化服务，SQLite 存储）和 [CPA-Manager-Plus](https://github.com/seakee/CPA-Manager-Plus)（请求级监控加费用估算，可按账号、模型、渠道追踪）。

## 旧教程说法对照表

如果你是照着 2026 年上半年之前的教程过来的，这些说法今天需要修正：

| 旧教程常见说法 | 当前事实 |
|---|---|
| `npm install -g cliproxyapi` | npm 上没有官方包，装不出去。用 brew、安装脚本、Docker 或源码构建 |
| 默认端口 3000（或旧的 8080） | 一直是 8317 |
| `cliproxyapi start -c config.yaml` | 无子命令，二进制直接运行：`cli-proxy-api --config config.yaml` |
| 配置里写 `keys`、`models`、`clients` 字段 | 这些字段不存在。访问密钥在 `access.api-keys`，模型列表自动聚合 |
| `management_port: 3001` 开管理面板 | 管理面板与主服务同端口，路径 `/management.html`，靠 `management.secret-key` 启用 |
| 旧版本不支持 OAuth | 2026 年 4 月时 OAuth 登录已支持 Google、Codex、Claude、Qwen、iFlow、Antigravity、Kimi 七个渠道；v8 时代反而是 qwen、iflow 被移除，新增 xai、meta、devin |
| 旧版只能环境变量配置 | 项目一直用 YAML 配置文件，没有环境变量配置体系 |
| 内置按 Key/按模型的用量统计 | v6.10.0 起移除，改用生态项目 |
| 官方文档在 cliproxyapi.dev | 该域名无法访问，官方文档站是 [help.router-for.me](https://help.router-for.me/) |

真实的版本脉络：2026-04 旧稿写作时项目还在 v5 时代（配置是扁平结构，OAuth 渠道含 Google、Qwen、iFlow）；v6.10.0 于 2026-05-01 移除内置统计；v7.0.0 于 2026-05-09 发布；v8.0.0 于 2026-09-27 引入 `config-version: 8` 分组配置与 `/v8/management`。配置字段层面的兼容规则见前文——旧文件能跑，但新教程、新面板、新文档都按 v8 结构说话，迁移到新写法是迟早的事。

## 资源

- 仓库：[router-for-me/CLIProxyAPI](https://github.com/router-for-me/CLIProxyAPI)
- 官方文档：[help.router-for.me](https://help.router-for.me/)（[中文](https://help.router-for.me/cn/)）
- 管理面板项目：[Cli-Proxy-API-Management-Center](https://github.com/router-for-me/Cli-Proxy-API-Management-Center)
- 桌面客户端：[EasyCLIProxyAPI](https://github.com/router-for-me/EasyCLIProxyAPI)
- 用量统计：[CPA Usage Keeper](https://github.com/Willxup/cpa-usage-keeper)、[CPA-Manager-Plus](https://github.com/seakee/CPA-Manager-Plus)
