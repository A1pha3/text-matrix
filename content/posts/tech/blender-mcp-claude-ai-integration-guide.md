+++
date = '2026-04-13T23:51:22+08:00'
draft = false
title = 'BlenderMCP 技术文档：将 Claude AI 引入 Blender 的 Model Context Protocol 解决方案'
+++

# BlenderMCP 技术文档：将 Claude AI 引入 Blender 的 Model Context Protocol 解决方案

## 1. 项目概述

BlenderMCP 是一款开源的 Blender 与 AI 连接器，通过 Model Context Protocol（MCP）将 Claude AI 与 Blender 无缝对接，实现通过自然语言提示词直接控制 Blender 进行 3D 建模、场景创建和对象操作[^1]。

**核心价值**：让 AI 成为 3D 艺术家的智能助手，通过对话即可完成复杂的 3D 建模任务，无需手动编写 Python 脚本或记忆大量快捷键。

**GitHub 数据**：
- Stars：19.2k
- Forks：1.9k
- 贡献者：20 人
- 最新版本：v1.5.5
- 编程语言：Python 100%

**项目作者**：Siddharth（Twitter @sidahuj）

---

## 2. 核心架构

### 2.1 系统组成

BlenderMCP 由两个核心组件构成：

| 组件 | 文件 | 职责 |
|------|------|------|
| Blender 插件 | `addon.py` | 在 Blender 内部创建 Socket 服务器，接收并执行命令 |
| MCP 服务器 | `src/blender_mcp/server.py` | 实现 Model Context Protocol，与 Blender 插件通信 |

### 2.2 通信协议

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

## 3. 功能特性

### 3.1 五大核心能力

| 能力 | 说明 |
|------|------|
| **双向通信** | 通过 Socket 协议实现 Claude 与 Blender 的实时交互 |
| **对象操作** | 创建、修改、删除 3D 对象 |
| **材质控制** | 应用和修改材质与颜色 |
| **场景检查** | 获取当前 Blender 场景的详细信息 |
| **代码执行** | 在 Blender 中执行任意 Python 代码 |

### 3.2 高级能力

- **Poly Haven 资产集成**：搜索并下载 Sketchfab 和 Poly Haven 的 3D 模型、纹理、HDRI
- **Hyper3D Rodin 支持**：通过 AI 生成 3D 模型
- **远程运行**：支持在远程主机上运行 Blender MCP
- **远端 Blender 支持**：通过 `BLENDER_HOST` 环境变量连接远程 Blender 实例

### 3.3 示例命令

以下是官方示例中展示的一些可用指令：

```
"Create a low poly scene in a dungeon, with a dragon guarding a pot of gold"
"Create a beach vibe using HDRIs, textures, and models like rocks and vegetation from Poly Haven"
"Give a reference image, and create a Blender scene out of it"
"Generate a 3D model of a garden gnome through Hyper3D"
"Make this car red and metallic"
"Create a sphere and place it above the cube"
"Make the lighting like a studio"
"Point the camera at the scene, and make it isometric"
```

---

## 4. 安装配置

### 4.1 前置要求

- Blender 3.0 或更高版本
- Python 3.10 或更高版本
- `uv` 包管理器

**安装 uv**：

macOS/Linux：
```bash
brew install uv
```

Windows：
```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

### 4.2 Blender 插件安装

1. 从 GitHub 下载 `addon.py` 文件
2. 打开 Blender，进入 `Edit > Preferences > Add-ons`
3. 点击 `Install...` 并选择下载的 `addon.py` 文件
4. 勾选 `Interface: Blender MCP` 启用插件

### 4.3 Claude Desktop 配置

在 `~/Library/Application Support/Claude/claude_desktop_config.json` 中添加：

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

### 4.4 Cursor 配置

Settings > MCP > Add New Global Server：

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

### 4.5 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `BLENDER_HOST` | `localhost` | Blender Socket 服务器地址 |
| `BLENDER_PORT` | `9876` | Blender Socket 端口号 |

连接远程 Blender 示例：

```bash
export BLENDER_HOST='host.docker.internal'
export BLENDER_PORT=9876
uvx blender-mcp
```

---

## 5. 使用方法

### 5.1 启动连接

1. 在 Blender 中，按 `N` 打开 3D View 侧边栏
2. 找到 `BlenderMCP` 标签页
3. 如需使用 Poly Haven 资产，勾选相应选项
4. 点击 `Connect to Claude`
5. 确保终端中 MCP 服务器正在运行

### 5.2 在 Claude 中使用

配置完成后，Claude Desktop 将显示 Blender MCP 的工具图标，提供以下能力：

- 获取场景和对象信息
- 创建、删除和修改形状
- 应用或创建材质
- 在 Blender 中执行任意 Python 代码
- 通过 Poly Haven 下载资产
- 通过 Hyper3D Rodin 生成 3D 模型

---

## 6. 技术细节

### 6.1 匿名遥测

BlenderMCP 默认收集匿名使用数据以帮助改进工具。用户可通过以下方式控制：

**在 Blender 中**：
`Edit > Preferences > Add-ons > Blender MCP`，取消勾选遥测同意复选框

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

### 6.2 安全考虑

⚠️ **重要警告**：`execute_blender_code` 工具允许在 Blender 中执行任意 Python 代码，具有潜在危险性。请在生产环境中谨慎使用，并**始终在使用前保存工作**。

---

## 7. 故障排除

| 问题 | 解决方案 |
|------|----------|
| **连接问题** | 确保 Blender 插件服务器正在运行，MCP 服务器已在 Claude 端配置。不要在终端中运行 `uvx` 命令。首次命令可能不成功，后续会自动开始工作。 |
| **超时错误** | 尝试简化请求或将其分解为更小的步骤 |
| **Poly Haven 问题** | Claude 有时行为不稳定 |
| **重启大法** | 如仍有问题，尝试重启 Claude 和 Blender 服务器 |

---

## 8. v1.5.5 最新功能

- Hunyuan3D 支持
- Blender 视口截图，更好地理解场景
- Sketchfab 模型搜索和下载
- Poly Haven 资产 API 支持
- Hyper3D Rodin 生成 3D 模型
- 支持在远程主机上运行 Blender MCP
- 工具执行的匿名遥测（完全匿名）

---

## 9. 相关资源

- **完整教程视频**：[YouTube 教程](https://www.youtube.com/watch?v=lCyQ717DuzQ)
- **官方 Discord**：[加入社区](https://discord.gg/z5apgR8TFU)
- **赞助此项目**：[GitHub Sponsors](https://github.com/sponsors/ahujasid)

---

## 10. 总结

BlenderMCP 为 3D 艺术家和 AI 爱好者提供了一个强大的工具，将 Claude AI 的自然语言处理能力与 Blender 的专业 3D 建模功能相结合。通过 MCP 协议的标准实现，它不仅支持 Claude，还能与 Cursor、VS Code 等其他支持 MCP 的编辑器无缝集成。

无论您是想快速创建 3D 场景、自动化重复建模任务，还是探索 AI 与 3D 设计的边界，BlenderMCP 都是一个值得尝试的开源解决方案。

[^1]: https://github.com/ahujasid/blender-mcp
