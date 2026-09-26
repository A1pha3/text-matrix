+++
github_repo = "ahujasid/mcp-for-blender"
source_key = "gh:ahujasid/mcp-for-blender"
date = '2026-04-13T23:51:22+08:00'
lastmod = '2026-09-26T20:10:00+08:00'
draft = false
title = 'BlenderMCP：通过 MCP 协议用 Claude 控制 Blender 3D 建模'
slug = 'blender-mcp-claude-ai-3d-modeling-guide'
description = 'BlenderMCP（现已更名为 MCP for Blender）通过 Model Context Protocol 把 Blender 接给 Claude 等 LLM，用自然语言控制 3D 建模、场景创建和对象操作，支持 Poly Haven 资产、Sketchfab、Poly Pizza 检索下载与 Hyper3D Rodin、Hunyuan3D、Tripo 模型生成。'
categories = ['技术笔记']
tags = ['Claude', 'MCP', 'Blender']
+++

## 学习目标

读完本文，你能够：

- 理解 BlenderMCP 的架构和通信协议（TCP Socket + JSON）
- 完成 Blender 插件和 MCP 服务器的安装配置
- 在 Claude Desktop、Claude Code 和 Cursor 中接入 BlenderMCP
- 用自然语言控制 Blender 做 3D 建模
- 使用 Poly Haven、Sketchfab、Poly Pizza 资产库和 Hyper3D Rodin、Hunyuan3D、Tripo 模型生成
- 按安全模式与遥测开关调整工具行为，排查常见连接问题

## 目录

1. [项目概述](#项目概述)
2. [核心架构](#核心架构)
3. [功能特性](#功能特性)
4. [安装配置](#安装配置)
5. [使用方法](#使用方法)
6. [技术细节](#技术细节)
7. [故障排除](#故障排除)
8. [近期演进与改名](#近期演进与改名)
9. [自测题](#自测题)
10. [练习](#练习)
11. [进阶路径](#进阶路径)

---

## 项目概述

BlenderMCP 是一款开源的 Blender 与 AI 连接器，通过 Model Context Protocol（MCP）把 Claude 等 LLM 与 Blender 对接，实现通过自然语言直接控制 Blender 进行 3D 建模、场景创建和对象操作[^1]。2026 年 9 月，项目更名为 **MCP for Blender**（仓库 `ahujasid/mcp-for-blender`，PyPI 包 `mcp-for-blender`），定位也从"接 Claude"扩展为"Connect Blender to any LLM"——Claude Desktop、Claude Code、Codex、Cursor、VS Code、OpenCode、Antigravity 等主流 MCP 客户端都有官方接入说明。截至 2026 年 9 月 26 日，仓库获得约 29,400 星标，按 MIT 许可发布。

---

## 核心架构

### 系统组成

BlenderMCP 由两个核心组件构成：

| 组件 | 文件 | 职责 |
|------|------|------|
| Blender 插件 | `addon.py` | 在 Blender 内部创建 Socket 服务器，接收并执行命令 |
| MCP 服务器 | `src/blender_mcp/server.py` | 实现 Model Context Protocol，与 Blender 插件通信 |

### 通信协议

系统采用基于 TCP Socket 的 JSON 协议进行双向通信：

```text
Claude Desktop ←→ MCP Server ←→ Socket ←→ Blender Addon ←→ Blender Python API
```

**命令格式**：
```json
{
  "type": "command_type",
  "params": { ... }
}
```

**响应格式**：
```json
{
  "status": "success|error",
  "result": { ... },
  "message": "..."
}
```

---

## 功能特性

### 五大核心能力

| 能力 | 说明 |
|------|------|
| **双向通信** | 通过 Socket 协议实现 Claude 与 Blender 的实时交互 |
| **对象操作** | 创建、修改、删除 3D 对象 |
| **材质控制** | 应用和修改材质与颜色 |
| **场景检查** | 获取当前 Blender 场景的详细信息 |
| **代码执行** | 在 Blender 中执行任意 Python 代码 |

### 高级能力

- **Poly Haven 资产集成**：搜索并下载 Poly Haven 的 HDRI、纹理和模型（全部 CC0，无需 API 密钥）
- **Sketchfab 模型**：搜索并下载 Sketchfab 上的模型
- **Poly Pizza 低多边形模型**：约 1.06 万个免费低多边形模型，含被抢救的 Google Poly 归档，单个自包含 `.glb`，几何负担比 Sketchfab 轻
- **AI 生成 3D 模型**：Hyper3D Rodin、腾讯 Hunyuan3D、Tripo 三家，支持文本或参考图生成后直接导入
- **场景导出**：`export_scene` 把整个场景、选中对象或指定对象导出为 GLB/FBX，交给其他应用
- **bpy API 查询**：`describe_node_type` 和 `bpy_api_lookup` 让 AI 先查节点结构和 API 参考，而不是凭记忆猜参数顺序和枚举名
- **视口截图**：`get_viewport_screenshot` 拿当前视口图像，便于基于画面继续调整
- **远程部署**：MCP 服务器可跑在 Docker 容器或远程主机上，用 `BLENDER_HOST`/`BLENDER_PORT` 或 `--host`/`--port` 参数连回本机 Blender

### 示例命令

以下是官方示例中展示的一些可用指令：

```text
"Create a low poly scene in a dungeon, with a dragon guarding a pot of gold"
"Create a beach vibe using HDRIs, textures, and models like rocks and vegetation from Poly Haven"
"Give a reference image, and create a Blender scene out of it"
"Get information about the current scene, and make a threejs sketch from it"
"Fill this room with low-poly furniture from Poly Pizza"
"Generate a 3D model of a garden gnome through Hyper3D"
"Make this car red and metallic"
"Create a sphere and place it above the cube"
"Make the lighting like a studio"
"Point the camera at the scene, and make it isometric"
```

---

## 安装配置

### 前置要求

- Blender 3.0 或更高版本
- Python 3.10 或更高版本
- `uv` 包管理器

**安装 uv**：用官方安装脚本，不要在报 `uvx` 缺失时改用 `pip install uv`——后者可能不生成 `uvx` 命令，还会把 uv 藏进客户端看不到的环境里。

macOS：
```bash
brew install uv
```

Linux：
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows：
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Windows 装完还需把 uv 加入用户 PATH（装完可能要重启 Claude Desktop）：

```powershell
$localBin = "$env:USERPROFILE\.local\bin"
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
[Environment]::SetEnvironmentVariable("Path", "$userPath;$localBin", "User")
```

### Blender 插件安装

推荐先用命令行自动安装。它把包内自带的插件副本复制进 Blender 的插件目录，落盘文件名为 `blender_mcp.py`，会打印写入路径，并在覆盖旧文件前保留一份 `.bak` 备份：

```bash
uvx mcp-for-blender install-addon
```

两个辅助入口：`uvx mcp-for-blender addon-paths` 列出检测到的 Blender 插件目录；设置 `BLENDERMCP_ADDONS_DIR=/path/to/scripts/addons` 可覆盖目标位置。

如果自动安装找不到 Blender，可手动下载本仓库的 `addon.py`：

1. 打开 Blender，进入 `Edit > Preferences > Add-ons`
2. 点击 `Install...` 并选择下载的 `addon.py`
3. 搜索并勾选启用 `Interface: MCP for Blender`

### Claude Desktop 配置

在 `~/Library/Application Support/Claude/claude_desktop_config.json` 中添加（也可通过 Claude → Settings → Developer → Edit Config 打开该文件）：

```json
{
  "mcpServers": {
    "blender": {
      "command": "uvx",
      "args": ["mcp-for-blender"]
    }
  }
}
```

### Cursor 配置

Settings → MCP → Add New Global Server（或写入项目根目录的 `.cursor/mcp.json`）：

```json
{
  "mcpServers": {
    "blender": {
      "command": "uvx",
      "args": ["mcp-for-blender"]
    }
  }
}
```

Windows 用户需使用：

```json
{
  "mcpServers": {
    "blender": {
      "command": "cmd",
      "args": ["/c", "uvx", "mcp-for-blender"]
    }
  }
}
```

### Claude Code 配置

Claude Code 用一条命令注册即可：

```bash
claude mcp add blender uvx mcp-for-blender
```

> **注意**：同一时间只跑**一个** MCP 服务器实例。Cursor 和 Claude Desktop 同时开启会端口冲突。

### uvx 找不到的排查

从 GUI 启动的客户端（Claude Desktop、Cursor 等）不继承终端的 `PATH`，用裸 `"command": "uvx"` 可能报 `spawn uvx ENOENT`，尽管终端里 `uvx` 正常。处理方式：用 `which uvx`（Windows 用 `where uvx`）取绝对路径填入 `"command"`，比如 macOS 的 `/opt/homebrew/bin/uvx`、Windows 的 `C:\Users\<你>\.local\bin\uvx.exe`。改完配置要彻底退出并重启客户端（macOS 用 Cmd+Q，Windows 从系统托盘退出）。

### 其他安装与运行方式

**固定 Python 版本**：机器上有 conda、pyenv 或 asdf 时，uv 可能选中一个装不上依赖的解释器。官方建议在客户端配置里固定 Python 3.11 并优先用 uv 托管解释器：

```json
{
  "mcpServers": {
    "blender": {
      "command": "uvx",
      "args": ["--python", "3.11", "mcp-for-blender"],
      "env": { "UV_PYTHON_PREFERENCE": "only-managed" }
    }
  }
}
```

之前装失败过、修复后配置仍反复报旧错误的，清一次缓存：`uv cache clean mcp-for-blender blender-mcp && uvx --refresh mcp-for-blender`。

**pipx 替代**：受限环境装不了 uv 时，`pipx install mcp-for-blender && pipx ensurepath`，再把 `which mcp-for-blender` 得到的绝对路径填进 `"command"`，`args` 留空。

**Docker 运行**：MCP 服务器可放进容器（Blender 仍在本机）。仓库根目录 `docker build -t mcp-for-blender .` 构建镜像，客户端配置 `"args": ["run", "-i", "--rm", "mcp-for-blender"]`（`-i` 必需，服务器走 stdin/stdout 通信）。镜像默认 `BLENDER_HOST=host.docker.internal`，macOS 和 Windows 的 Docker Desktop 开箱即用；Linux 上该域名不存在，改用 `--network=host` 加 `-e BLENDER_HOST=localhost`。

### 环境变量与连接参数

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `BLENDER_HOST` | `localhost` | Blender Socket 服务器地址 |
| `BLENDER_PORT` | `9876` | Blender Socket 端口号 |
| `BLENDER_MCP_SAFE_MODE` | 关 | 设为 `1` 时，脚本执行前先校验，阻断直接读写文件、启动外部程序、访问网络等危险操作 |

连接也可以用 CLI 参数 `--host`/`--port` 传递，且优先于环境变量。这对同时跑多个 Blender 实例有用——每个 MCP 客户端条目指向不同端口即可：

```bash
uvx mcp-for-blender --port 9877
```

Blender 侧插件面板里也要把对应实例的端口改成一致。

连接远程 Blender 示例：

```bash
export BLENDER_HOST='host.docker.internal'
export BLENDER_PORT=9876
uvx mcp-for-blender
```

> **安全边界**：Blender 插件的 Socket 服务器没有认证和加密，任何能访问该端口的进程都能在 Blender 里执行 Python。保持监听 `localhost`，跨机器连接优先走 SSH 隧道，而不是把 `--host`/`BLENDER_HOST` 直接指向远程地址。

---

## 使用方法

### 启动连接

1. 在 Blender 中，按 `N` 打开 3D View 侧边栏
2. 找到 `MCP for Blender` 标签页
3. 按需勾选要用的能力（Poly Haven、Poly Pizza 等）
4. 点击 `Connect to Claude`
5. 确保 MCP 服务器已在客户端配置好并运行

### 在 Claude 中使用

配置完成后，Claude 会显示 Blender MCP 的工具图标，提供以下能力：

- 获取场景和对象信息
- 创建、删除和修改形状
- 应用或创建材质
- 在 Blender 中执行任意 Python 代码
- 把场景或选中对象导出为 GLB/FBX
- 查询节点结构与 bpy API 参考
- 通过 Poly Haven 下载模型、资产和 HDRI
- 通过 Sketchfab、Poly Pizza 搜索下载模型
- 通过 Hyper3D Rodin、Hunyuan3D、Tripo 生成 3D 模型

MCP 服务器目前向客户端暴露 36 个工具，覆盖状态查询、检索、生成、导入与导出的完整链路。

### 使用 Poly Haven 资产

Poly Haven 收录约 2,400 个 HDRI、纹理和模型，全部 CC0 许可、免费，靠捐赠运营——没有 API 密钥、不需要账号、也没有需要担心的速率限制。在侧边栏勾选 **Poly Haven** 即完成全部配置。

AI 的检索是按语义而非关键词匹配（搜 "couch" 能找到沙发，中文描述也可以），可以先调 `get_polyhaven_asset_preview` 看缩略图再决定下载。模型一律从艺术家原始的 `.blend` 文件导入（glTF/FBX/USD 版本是生成的，会丢材质细节）；HDRI 会被打包进文件，灯光随 `.blend` 保存、异地打开不丢。导入时，`polyhaven_id`、`polyhaven_url`、`polyhaven_authors`、`polyhaven_resolution`、`polyhaven_licence` 会写进对象、材质、图像和世界的自定义属性，之后打开文件的人仍能溯源到资产与作者。

### 使用 Poly Pizza 资产

Poly Pizza 的模型约 69% 按 CC-BY 许可发布，这类模型**要求**在使用处署名作者。导入时，格式化好的署名行会写进每个根对象的自定义属性 `polypizza_attribution`（同时写入 `polypizza_id` 和 `polypizza_licence`），随 `.blend` 文件保存。若希望导入后免署名，可在提示词里加 `licence="CC0"` 过滤：

> 「Search Poly Pizza for a low-poly chair under a CC0 licence and import one at 1 metre tall」

API 密钥在 [poly.pizza/settings/api](https://poly.pizza/settings/api) 免费申请，填入 Blender 侧边栏的 **API Key** 字段。检索结果自带许可与三角面数，还支持按分类（动物、家具、载具、自然、建筑等 12 类）过滤或只看带动画的模型。

### 持久化 API 凭据

Sketchfab、Poly Pizza、Hyper3D、Hunyuan3D 的 API 密钥可在 **Edit → Preferences → Add-ons → MCP for Blender** 中保存，重启 Blender 后仍保留。无界面（headless）或 CI 场景可用环境变量注入，完整的六个是：`BLENDERMCP_SKETCHFAB_API_KEY`、`BLENDERMCP_POLYPIZZA_API_KEY`、`BLENDERMCP_HYPER3D_API_KEY`、`BLENDERMCP_HUNYUAN3D_SECRET_ID`、`BLENDERMCP_HUNYUAN3D_SECRET_KEY`、`BLENDERMCP_HUNYUAN3D_API_URL`。凭据是敏感信息，建议走环境变量而不是写进配置仓库。

Hunyuan3D 走腾讯云官方 API 时注意账号分区：大陆账号（cloud.tencent.com）调用 AI3D 3.0 服务、广州区域，侧边栏 **International (Pro) account** 保持关闭；国际账号（tencentcloud.com，Hunyuan-to-3D Professional）调用 hunyuan 服务、新加坡区域并启用 PBR，需要勾选该开关。国际凭据发到大陆端点会报 `AuthFailure.SignatureFailure` 或 `ResourceUnavailable`。

**Premium 通道**：官网提供付费选项，Hunyuan3D、Tripo、Hyper3D Rodin 生成可不经自带 API 密钥直接用，适合不想分别注册三家服务的用户。

---

## 技术细节

### 遥测

遥测是**选择加入（opt-in）**的，分两层：

**默认只收集最小匿名使用记录**：随机生成的安装 ID、会话 ID、工具名、是否成功、耗时、MCP for Blender 与 Blender 版本、操作系统和时间戳——用途是统计活跃用户、看哪些工具被使用。你的提示词、生成的代码、视口截图、场景数据和轨迹步骤**默认不收集**，只有在偏好设置里勾选遥测同意复选框（部分 MCP 客户端会在对话开始时弹一次性询问）后才加入收集范围，细节见仓库的 TERMS_AND_CONDITIONS.md。数据不与姓名或账号关联，可能用于改进项目、研究和训练 AI 模型。

**完全关闭**（连最小匿名记录也关）有两种方式。启动时设环境变量：

```bash
DISABLE_TELEMETRY=true uvx mcp-for-blender
```

或写进客户端配置：

```json
{
  "mcpServers": {
    "blender": {
      "command": "uvx",
      "args": ["mcp-for-blender"],
      "env": {
        "DISABLE_TELEMETRY": "true"
      }
    }
  }
}
```

服务器还内置了 `disable_telemetry` 工具，对话里直接让 AI 调用即可关闭。

### 安全考虑

**重要警告**：`execute_blender_code` 工具允许在 Blender 中执行任意 Python 代码，能力很强，但也可能危险。生产环境务必谨慎，**使用前先保存工作**。

若不希望 AI 在 Blender 里跑任意 Python 脚本，可开启安全模式：设置环境变量 `BLENDER_MCP_SAFE_MODE=1`。开启后每个脚本执行前都会校验，直接读写文件、启动外部程序、访问网络、安装常驻进程等高风险操作会被拦截，并把原因返回给 AI，让它改用更合适的脚本。常规建模、材质、渲染、保存、导入导出不受影响。容器场景给 `docker run` 参数加上 `"-e", "BLENDER_MCP_SAFE_MODE=1"` 即可。

---

## 故障排除

| 问题 | 解决方案 |
|------|----------|
| **连接问题** | 确认 Blender 插件服务器已运行、MCP 服务器已在 Claude 端配置。**不要**在终端里手动运行 `uvx` 命令。首次命令可能不成功，之后会自动正常。 |
| **超时错误** | 把请求拆小，或分成更小的步骤逐步执行 |
| **`spawn uvx ENOENT`** | 见上文「uvx 找不到的排查」，改用 `uvx` 的绝对路径 |
| **Poly Haven 下载时 Blender 卡住** | 资产下载在 Blender 主线程上执行，传输完成前 UI 无响应。文件体积每升一级分辨率约翻四倍，除非相机贴得很近，尽量只要 1k 或 2k |
| **Poly Pizza 下载受 Cloudflare 拦截** | `static.poly.pizza` 有反爬保护，会拦截数据中心 / VPN / 云 IP。API 密钥本身没问题（CDN 看不到）。换普通网络重试，或手动下载 `.glb` 后用 File → Import → glTF 2.0 导入 |
| **重启大法** | 仍不行就重启 Claude 和 Blender 服务器 |

---

## 近期演进与改名

2026 年 9 月 16 日，项目从 `blender-mcp` 更名为 **mcp-for-blender**（仓库与 PyPI 包同步更名）。旧配置无需改动：PyPI 上的 `blender-mcp` 现在是一个兼容壳，`uvx blender-mcp` 仍然可用；Python 导入路径仍是 `blender_mcp`，Blender 里插件名不变，重装不会产生重复条目。新安装建议直接用新包名。

更名前后一段时间的功能演进包括：

- Tripo 模型生成（与 Hyper3D Rodin、Hunyuan3D 并列的第三家 AI 生成服务）
- `export_scene` 场景导出（GLB/FBX）
- `describe_node_type` / `bpy_api_lookup` 节点结构与 bpy API 查询
- Blender 视口截图（`get_viewport_screenshot`）
- Sketchfab、Poly Pizza（含 Google Poly 归档）搜索下载
- Poly Haven 资产 API 深度集成（语义检索、分类树、预览、自定义属性溯源）
- Docker 运行支持与 CLI 连接参数（`--host`/`--port`）
- 新增 `disable_telemetry` 工具，遥测分为「默认最小匿名记录 + 内容收集需勾选同意」两层

---

## 自测题

1. **BlenderMCP 的通信协议是什么？**
   <details>
   <summary>查看答案</summary>
   答案：基于 TCP Socket 的 JSON 协议。Claude Desktop ↔ MCP Server ↔ Socket ↔ Blender Addon ↔ Blender Python API。
   </details>

2. **BlenderMCP 包含哪两个核心组件？**
   <details>
   <summary>查看答案</summary>
   答案：Blender 插件（`addon.py`）和 MCP 服务器（`src/blender_mcp/server.py`）。前者在 Blender 内创建 Socket 服务器，后者实现 MCP 协议与插件通信。
   </details>

3. **如何让 BlenderMCP 支持 Poly Haven 资产？**
   <details>
   <summary>查看答案</summary>
   答案：在 Blender 的 `MCP for Blender` 标签页中勾选 Poly Haven 选项即可——Poly Haven 资产全部 CC0，不需要 API 密钥。之后就能用自然语言搜索并下载 3D 模型、纹理和 HDRI。
   </details>

4. **`execute_blender_code` 工具存在什么安全风险？如何限制？**
   <details>
   <summary>查看答案</summary>
   答案：该工具允许在 Blender 中执行任意 Python 代码，具有潜在危险性，使用前应先保存工作。不想放开任意脚本时可设置 `BLENDER_MCP_SAFE_MODE=1` 开启安全模式，高风险操作会被拦截并返回原因。另外要记住插件 Socket 服务无认证无加密，端口不要暴露在不可信网络里。
   </details>

5. **如何完全关闭 BlenderMCP 的遥测？**
   <details>
   <summary>查看答案</summary>
   答案：设置环境变量 `DISABLE_TELEMETRY=true`（可写进 MCP 客户端配置的 env 字段），或直接让 AI 调用 `disable_telemetry` 工具。默认状态下遥测本来就只收集最小匿名使用记录，提示词、生成代码、截图等内容需要显式勾选同意才会收集。
   </details>

---

## 练习

1. **完成 BlenderMCP 的完整安装**：在自己的机器上安装 Blender 插件和 MCP 服务器，配置 Claude Desktop，并成功用自然语言创建一组简单场景（比如「创建一个红色金属球的低多边形场景」）。
2. **尝试 Poly Haven 集成**：通过 Claude 搜索并下载一个 Poly Haven 的 HDRI 贴图，应用到场景中，观察渲染效果变化；保存重开 `.blend`，确认 HDRI 灯光仍在。
3. **尝试 Hyper3D Rodin 生成**：通过 Claude 调用 Hyper3D Rodin 生成一个自定义 3D 模型（比如「一个花园侏儒」），并导入到当前场景中。
4. **开启安全模式做对照**：设 `BLENDER_MCP_SAFE_MODE=1` 后让 AI「用 Python 的 open() 读桌面上的一个文本文件」，观察拦截反馈，再让它改用 Blender 自身的能力完成同样的事。

---

## 进阶路径

1. **阅读源码**：深入理解 `addon.py` 和 `server.py` 的实现，理解 MCP 协议如何映射到 Blender Python API。
2. **扩展工具能力**：基于现有代码，添加新的 MCP 工具（比如批量导入、动画控制、材质节点编辑等），`export_scene` 的实现是现成的参照。
3. **集成到其他 MCP 客户端**：仓库 README 提供 Claude Desktop、Claude Code、Codex、Cursor、VS Code、OpenCode、Antigravity 七种客户端的官方配置说明，多数只需改一行启动命令。
4. **优化生成质量**：研究如何通过更好的 prompt 设计，让 Claude 生成更复杂的 3D 场景和模型；配合 `bpy_api_lookup` 减少 API 误用。
5. **贡献社区**：向 [mcp-for-blender 仓库](https://github.com/ahujasid/mcp-for-blender)提交 PR，修复 bug 或添加新功能，参与 [Discord 社区](https://discord.gg/SNqPn4TcKQ) 讨论。

---

## 资料口径说明

1. **信息来源与版本锚点**：本文以 2026 年 9 月 26 日的仓库状态为准（`ahujasid/mcp-for-blender`，PyPI 包 mcp-for-blender 2.1.0），对照官方 README、`addon.py`、`addon_manager.py`、`server.py` 源码与 issue #366（改名公告）编写。工具数量、环境变量、面板按钮文案均按当日源码核对。
2. **版本时效性**：BlenderMCP 处于活跃开发阶段，功能特性、配置方式和支持的 Blender 版本可能随版本变化，请以仓库最新代码为准。
3. **前置要求**：本文假设读者已安装 Blender 3.0+ 和 Python 3.10+，并了解基本的 3D 建模概念。
4. **MCP 客户端配置**：Claude Desktop 和 Cursor 的配置路径可能因操作系统和版本而异，请参考各自官方文档确认配置位置。
5. **第三方服务可用性**：Poly Haven、Sketchfab、Poly Pizza、Hyper3D、Hunyuan3D、Tripo 的 API 和许可条款可能变化，资产数量为官方 README 口径（Poly Haven 约 2,400、Poly Pizza 约 10,600、CC-BY 占比约 69%）。
6. **安全提醒**：`execute_blender_code` 允许执行任意 Python 代码，生产环境使用前请评估风险并考虑沙箱隔离；Blender 侧 Socket 服务无认证无加密，勿暴露在不可信网络。

---

## 相关资源

- **项目官网**：[mcp-for-blender.com](https://www.mcp-for-blender.com/)
- **完整教程视频**：[YouTube 教程](https://www.youtube.com/watch?v=lCyQ717DuzQ)
- **官方 Discord**：[加入社区](https://discord.gg/SNqPn4TcKQ)
- **赞助此项目**：[GitHub Sponsors](https://github.com/sponsors/ahujasid)

---

## 总结

BlenderMCP 把一个成熟的 3D 编辑器接进了 MCP 生态，让 Claude 等模型得以用自然语言直接操控 Blender；改名 MCP for Blender 之后，它也不再绑定某一家客户端。对 3D 建模师，它是省去重复操作的助手；对探索 AI 与设计边界的开发者，它是一套可扩展的开源方案，同一份配置也能用在 Cursor、Codex、VS Code 等支持 MCP 的编辑器上。需要留意的有两点：任意 Python 执行能力是把双刃剑，使用前先保存，必要时打开安全模式；插件 Socket 服务没有认证，端口别暴露在不可信网络里。

---

[^1]: https://github.com/ahujasid/mcp-for-blender
