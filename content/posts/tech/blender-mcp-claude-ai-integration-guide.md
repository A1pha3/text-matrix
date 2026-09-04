+++
github_repo = "ahujasid/blender-mcp"
date = '2026-04-13T23:51:22+08:00'
draft = false
title = 'BlenderMCP：通过 MCP 协议用 Claude 控制 Blender 3D 建模'
slug = 'blender-mcp-claude-ai-3d-modeling-guide'
description = 'BlenderMCP 通过 Model Context Protocol 将 Claude AI 与 Blender 对接，实现用自然语言控制 3D 建模、场景创建和对象操作，支持 Poly Haven 资产集成和 Hyper3D Rodin 模型生成。'
categories = ['技术笔记']
tags = ['Claude', 'MCP']
+++

## 学习目标

通过本文，你将掌握以下核心能力：

- 理解 BlenderMCP 的架构和通信协议（TCP Socket + JSON）
- 掌握 Blender 插件和 MCP 服务器的安装配置
- 学会在 Claude Desktop 和 Cursor 中配置 BlenderMCP
- 能够使用自然语言控制 Blender 进行 3D 建模
- 理解 Poly Haven 资产集成和 Hyper3D Rodin 模型生成的使用方式
- 掌握常见问题的排查方法

## 目录

1. [项目概述](#项目概述)
2. [核心架构](#核心架构)
3. [功能特性](#功能特性)
4. [安装配置](#安装配置)
5. [使用方法](#使用方法)
6. [技术细节](#技术细节)
7. [故障排除](#故障排除)
8. [自测题](#自测题)
9. [练习](#练习)
10. [进阶路径](#进阶路径)

---

## 项目概述

BlenderMCP 是一款开源的 Blender 与 AI 连接器，通过 Model Context Protocol（MCP）把 Claude AI 与 Blender 对接，实现通过自然语言直接控制 Blender 进行 3D 建模、场景创建和对象操作[^1]。

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

```
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

- **Poly Haven 资产集成**：搜索并下载 Poly Haven 的 HDRI、纹理和模型
- **Sketchfab 模型**：搜索并下载 Sketchfab 上的模型
- **Poly Pizza 低多边形模型**：约 1.06 万个免费低多边形模型，含被抢救的 Google Poly 归档，单个自包含 `.glb`，几何负担比 Sketchfab 轻
- **Hyper3D Rodin 支持**：通过 AI 生成 3D 模型
- **Hunyuan3D 支持**：腾讯推出的 AI 3D 模型生成
- **远程运行**：支持在远程主机上运行 Blender MCP
- **远端 Blender 支持**：通过 `BLENDER_HOST` 环境变量连接远程 Blender 实例

### 示例命令

以下是官方示例中展示的一些可用指令：

```
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

**安装 uv**：推荐用 uv 官方安装脚本（`brew install uv`），不要在报 `uvx` 缺失时改用 `pip install uv`，后者可能让 GUI 客户端找不到 `uvx` 命令。

macOS/Linux：
```bash
brew install uv
```

Windows：
```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

### Blender 插件安装

推荐先用命令行自动安装，它会复制 `addon.py` 到 Blender 的插件目录并打印目标路径，可能还生成一个 `.bak` 备份：

```bash
uvx blender-mcp install-addon
```

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
      "args": ["blender-mcp"]
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
      "args": ["blender-mcp"]
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
      "args": ["/c", "uvx", "blender-mcp"]
    }
  }
}
```

### Claude Code 配置

Claude Code 用一条命令注册即可：

```bash
claude mcp add blender uvx blender-mcp
```

> **注意**：同一时间只跑**一个** MCP 服务器实例。Cursor 和 Claude Desktop 同时开启会端口冲突。

### uvx 找不到的排查

从 GUI 启动的客户端（Claude Desktop、Cursor 等）不继承终端的 `PATH`，用裸 `"command": "uvx"` 可能报 `spawn uvx ENOENT`，尽管终端里 `uvx` 正常。处理方式：用 `which uvx`（Windows 用 `where uvx`）取绝对路径填入 `"command"`，比如 macOS 的 `/opt/homebrew/bin/uvx`。改完配置要彻底退出并重启客户端（macOS 用 Cmd+Q）。

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `BLENDER_HOST` | `localhost` | Blender Socket 服务器地址 |
| `BLENDER_PORT` | `9876` | Blender Socket 端口号 |
| `BLENDER_MCP_SAFE_MODE` | 关 | 设为 `1` 时，脚本执行前先校验，阻断直接读写文件、启动外部程序、访问网络等危险操作 |

连接远程 Blender 示例：

```bash
export BLENDER_HOST='host.docker.internal'
export BLENDER_PORT=9876
uvx blender-mcp
```

---

## 使用方法

### 启动连接

1. 在 Blender 中，按 `N` 打开 3D View 侧边栏
2. 找到 `MCP for Blender` 标签页
3. 如需使用 Poly Haven 资产，勾选相应选项
4. 点击 `Connect to Claude`
5. 确保终端中 MCP 服务器正在运行

### 在 Claude 中使用

配置完成后，Claude 会显示 Blender MCP 的工具图标，提供以下能力：

- 获取场景和对象信息
- 创建、删除和修改形状
- 应用或创建材质
- 在 Blender 中执行任意 Python 代码
- 通过 Poly Haven 下载模型、资产和 HDRI
- 通过 Sketchfab、Poly Pizza 搜索下载模型
- 通过 Hyper3D Rodin、Hunyuan3D 生成 3D 模型

### 使用 Poly Pizza 资产

Poly Pizza 的模型按 CC-BY 等许可发布。若希望导入后免署名，可在提示词里加 `licence="CC0"`：

> 「Search Poly Pizza for a low-poly chair under a CC0 licence and import one at 1 metre tall」

关键在于拿到免费 API 密钥：在 [poly.pizza/settings/api](https://poly.pizza/settings/api) 申请后，把密钥填入 Blender 侧边栏的 **API Key** 字段。导入时，模型归属信息会写入每个根对象的自定义属性 `polypizza_attribution`，随 `.blend` 文件保存。

### 持久化 API 凭据

Sketchfab、Poly Pizza、Hyper3D、Hunyuan3D 的 API 密钥可在 **Edit → Preferences → Add-ons → MCP for Blender** 中保存，重启 Blender 后仍保留。无界面（headless）或 CI 场景可用 `BLENDERMCP_POLYPIZZA_API_KEY`、`BLENDERMCP_SKETCHFAB_API_KEY`、`BLENDERMCP_HYPER3D_API_KEY`、`BLENDERMCP_HUNYUAN3D_SECRET_ID` 等环境变量注入。凭据是敏感信息，建议走环境变量而不是写进配置仓库。

---

## 技术细节

### 匿名遥测

BlenderMCP 默认开启匿名使用数据收集，用于改进工具。可通过两种方式关闭：

**在 Blender 中**：`Edit > Preferences > Add-ons > MCP for Blender`，取消勾选遥测同意复选框

**通过环境变量禁用**：
```bash
DISABLE_TELEMETRY=true uvx blender-mcp
```

或在配置文件中：
```json
{
  "mcpServers": {
    "blender": {
      "command": "uvx",
      "args": ["blender-mcp"],
      "env": {
        "DISABLE_TELEMETRY": "true"
      }
    }
  }
}
```

### 安全考虑

**重要警告**：`execute_blender_code` 工具允许在 Blender 中执行任意 Python 代码，能力很强，但也可能危险。生产环境务必谨慎，**使用前先保存工作**。

若不希望 AI 在 Blender 里跑任何 Python 脚本，可开启安全模式：设置环境变量 `BLENDER_MCP_SAFE_MODE=1`。开启后每个脚本执行前都会校验，直接读写文件、启动外部程序、访问网络、安装常驻进程等高风险操作会被拦截，并把原因返回给 AI，让它改用更合适的脚本。常规建模、材质、渲染、保存、导入导出不受影响。

---

## 故障排除

| 问题 | 解决方案 |
|------|----------|
| **连接问题** | 确认 Blender 插件服务器已运行、MCP 服务器已在 Claude 端配置。**不要**在终端里手动运行 `uvx` 命令。首次命令可能不成功，之后会自动正常。 |
| **超时错误** | 把请求拆小，或分成更小的步骤逐步执行 |
| **`spawn uvx ENOENT`** | 见上文「uvx 找不到的排查」，改用 `uvx` 的绝对路径 |
| **Poly Haven 集成不稳** | Claude 有时行为不稳定，重试或换更明确的指令 |
| **Poly Pizza 下载受 Cloudflare 拦截** | `static.poly.pizza` 有反爬保护，会拦截数据中心 / VPN / 云 IP。API 密钥本身没问题（CDN 看不到）。换普通网络重试，或手动下载 `.glb` 后用 File → Import → glTF 2.0 导入 |
| **重启大法** | 仍不行就重启 Claude 和 Blender 服务器 |

---

## 最近的新能力

- Hunyuan3D 支持
- Blender 视口截图
- Sketchfab 模型搜索和下载
- Poly Pizza 低多边形模型（含 Google Poly 归档）搜索下载
- Poly Haven 资产 API 支持
- Hyper3D Rodin 生成 3D 模型
- 支持在远程主机上运行 Blender MCP
- 完全匿名的工具执行遥测

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
   答案：在 Blender 的 `MCP for Blender` 标签页中勾选相应选项，然后在 Claude 中就可以用自然语言搜索并下载 Poly Haven 的 3D 模型、纹理和 HDRI。
   </details>

4. **`execute_blender_code` 工具存在什么安全风险？**
   <details>
   <summary>查看答案</summary>
   答案：该工具允许在 Blender 中执行任意 Python 代码，具有潜在危险性。生产环境中使用前应先保存工作，并谨慎授予权限。
   </details>

5. **如何禁用 BlenderMCP 的匿名遥测？**
   <details>
   <summary>查看答案</summary>
   答案：两种方法：在 Blender 偏好设置中取消勾选遥测同意复选框；或在启动时设置环境变量 `DISABLE_TELEMETRY=true`。
   </details>

---

## 练习

1. **完成 BlenderMCP 的完整安装**：在自己的机器上安装 Blender 插件和 MCP 服务器，配置 Claude Desktop，并成功用自然语言创建一组简单场景（比如「创建一个红色金属球的低多边形场景」）。
2. **尝试 Poly Haven 集成**：通过 Claude 搜索并下载一个 Poly Haven 的 HDRI 贴图，应用到场景中，观察渲染效果变化。
3. **尝试 Hyper3D Rodin 生成**：通过 Claude 调用 Hyper3D Rodin 生成一个自定义 3D 模型（比如「一个花园侏儒」），并导入到当前场景中。

---

## 进阶路径

1. **阅读源码**：深入理解 `addon.py` 和 `server.py` 的实现，理解 MCP 协议如何映射到 Blender Python API。
2. **扩展工具能力**：基于现有代码，添加新的 MCP 工具（比如批量导入、动画控制、材质节点编辑等）。
3. **集成到其他 MCP 客户端**：研究如何让 BlenderMCP 在更多支持 MCP 的编辑器（VS Code、Cursor 等）中工作。
4. **优化生成质量**：研究如何通过更好的 prompt 设计，让 Claude 生成更复杂的 3D 场景和模型。
5. **贡献社区**：向 BlenderMCP 仓库提交 PR，修复 bug 或添加新功能，参与 [Discord 社区](https://discord.gg/SNqPn4TcKQ) 讨论。

---

## 资料口径说明

1. **信息来源**：本文基于 BlenderMCP 仓库的 README、官方教程视频和可验证的代码示例编写。
2. **版本时效性**：BlenderMCP 处于活跃开发阶段，功能特性、配置方式和支持的 Blender 版本可能随版本变化，请以仓库最新代码为准。
3. **前置要求**：本文假设读者已安装 Blender 3.0+ 和 Python 3.10+，并了解基本的 3D 建模概念。
4. **MCP 客户端配置**：Claude Desktop 和 Cursor 的配置路径可能因操作系统和版本而异，请参考各自官方文档确认配置位置。
5. **Poly Haven 和 Hyper3D 的可用性**：这些第三方服务的 API 和集成方式可能变化，本文仅描述写作时的集成方式。
6. **安全提醒**：`execute_blender_code` 允许执行任意 Python 代码，生产环境使用前请评估风险并考虑沙箱隔离。

---

## 相关资源

- **完整教程视频**：[YouTube 教程](https://www.youtube.com/watch?v=lCyQ717DuzQ)
- **官方 Discord**：[加入社区](https://discord.gg/SNqPn4TcKQ)
- **赞助此项目**：[GitHub Sponsors](https://github.com/sponsors/ahujasid)

---

## 总结

BlenderMCP 把一个成熟的 3D 编辑器接进了 MCP 生态，让 Claude 等模型得以用自然语言直接操控 Blender。对 3D 建模师，它是省去重复操作的助手；对探索 AI 与设计边界的开发者，它是一套可扩展的开源方案，同一份配置也能用在 Cursor、VS Code 等支持 MCP 的编辑器上。需要留意的只有一点：任意 Python 执行能力是把双刃剑，使用前先保存，必要时打开安全模式。

---

---

[^1]: https://github.com/ahujasid/blender-mcp
