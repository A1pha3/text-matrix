---
title: "Modly：一张照片变 3D 模型，全程跑在你自己的 GPU 上"
date: 2026-08-18T03:22:27+08:00
description: "开源桌面应用 Modly 把图像转 3D 网格这件事搬到了本地：开源模型、本地推理、节点式工作流，还有一套给 Agent 用的 CLI 与 MCP 服务。本文拆解它的架构、模型生态与上手路径。"
tags: ["AI", "3D 生成", "开源工具", "桌面应用", "AI 工具"]
categories: ["技术笔记"]

github_repo: "lightningpixel/modly"
source_key: "gh:lightningpixel/modly"
slug: modly-local-ai-image-to-3d
---

# Modly：一张照片变 3D 模型，全程跑在你自己的 GPU 上

[Modly](https://github.com/lightningpixel/modly) 是一个本地运行的图像转 3D 网格桌面应用：丢进去一张照片，出来一个可以导出的 3D 网格模型，中间所有 AI 推理都发生在你自己的 GPU 上——不联网上传、不按次付费、不看服务商脸色。

桌面端用 TypeScript 写的 Electron 壳，后端是承载模型推理的 Python（FastAPI）服务，支持 Windows、Linux 和 Apple Silicon macOS 三个平台。截至 2026 年 8 月，项目已有 6,700+ star、650+ fork（派生仓库），并保持高频更新。

这篇文章的目标是讲清三件事：Modly 为什么坚持本地推理、它的扩展系统如何接入不同模型、以及它给脚本和 AI Agent（智能体）留了哪些自动化入口——包括 CLI（命令行工具）和 MCP 服务两条正门。

## 目录

- [为什么「本地」是关键差异](#为什么本地是关键差异)
- [架构拆解：Electron 前端与 Python 推理后端](#架构拆解electron-前端与-python-推理后端)
- [模型生态：manifest 约定与五个官方扩展](#模型生态manifest-约定与五个官方扩展)
- [上手路径：从安装到第一个模型](#上手路径从安装到第一个模型)
- [Modly CLI：给脚本和 Agent 留的正门](#modly-cli给脚本和-agent-留的正门)
- [MCP 服务：第二条自动化入口](#mcp-服务第二条自动化入口)
- [使用建议与边界](#使用建议与边界)
- [动手练习](#动手练习)
- [常见问题](#常见问题)
- [进阶方向](#进阶方向)
- [参考文献](#参考文献)

## 为什么「本地」是关键差异

市面上的图像转 3D 服务不少，但绝大多数是云端 API（应用程序接口）：上传图片、排队、出结果。这带来三个问题——

1. **成本**：按次计费，批量制作素材时费用快速失控；
2. **隐私**：产品原型图、客户素材上传到第三方服务器，未必符合你的数据合规要求；
3. **可定制性**：云端服务的模型版本、参数你说了不算。

Modly 把推理全部拉回本地。显存够的跑大模型，不够的跑 mini/fast 变体，全程数据不出机器。对独立游戏开发者、3D 素材创作者、产品原型设计者来说，这是一条确定性更高的工作流。

## 架构拆解：Electron 前端与 Python 推理后端

Modly 的工程结构并不复杂，但分层清晰：

- **桌面层**：Electron + TypeScript。负责 UI、节点式工作流编辑器、任务队列和本地服务管理。顶栏有一个来自主进程的实时内存（RAM）指示器，方便监控推理时的资源占用。
- **推理层**：Python 虚拟环境里的 FastAPI 后端，承载 3D 生成模型的加载与推理。前后端通过本地 HTTP 接口通信——这也是后文 CLI 与 MCP 服务能绕过 UI 直接调用它的基础。
- **工作流层**：采用节点图（node graph）组织生成流程。工作流在运行前会做连接校验，非法的图不会把你当前的网格视图丢掉，而是以内联提示或 toast 警告的形式反馈——这类工程细节对一个仍在快速迭代的项目来说相当扎实。

最基础的工作流只有三个节点：

```text
Image → Generate Mesh → Add to Scene
```

即读入一张图、生成网格、加入场景。更复杂的流程可以扩展节点。

另一个容易被忽略的能力：导入的外部网格可以在应用内做平滑（smoothing）和减面（decimation），优化后的结果直接写回工作区，省去了在 Blender 里来回导出的环节。

## 模型生态：manifest 约定与五个官方扩展

Modly 本体不带模型，而是通过**扩展系统**引入生成模型。每个扩展是一个独立的 GitHub 仓库，内含 `manifest.json` 和对应类型的运行时入口文件。官方目前提供五个扩展：

| 扩展 | 模型 |
|------|------|
| modly-hunyuan3d-mini-extension | Hunyuan3D 2 Mini |
| modly-hunyuan3d-mini-turbo-extension | Hunyuan3D 2 Mini Turbo |
| modly-hunyuan3d-mini-fast-extension | Hunyuan3D 2 Mini Fast |
| modly-triposg-extension | TripoSG |
| modly-trellis2-gguf-extension | Trellis2 GGUF |

这个设计有几个值得注意的地方：

- **模型选型开放**：Hunyuan3D（腾讯混元）、TripoSG、TRELLIS 都是社区里活跃的图像转 3D 开源模型。Modly 把它们做成官方扩展，说明定位是「本地推理的壳与工作流引擎」，而不是绑定某一个模型。
- **安装即填 URL**：在 Models 页面点「Install from GitHub」（从 GitHub 安装），粘贴扩展仓库的 HTTPS 地址即可安装；模型类扩展装完再下载模型权重或选定变体（variant），流程类扩展装完即用。
- **社区可扩展**：`manifest.json` 是一份公开约定，任何开发者都可以按约定发布自己的模型扩展，Modly 生态因此不被官方列表锁死。

## 上手路径：从安装到第一个模型

**方式一：直接装**。到 Releases 页下载对应平台的安装包（注意：macOS 版仅支持 Apple Silicon）。

**方式二：源码运行**（也适合二次开发），示例如下：

```bash
# 1. 安装 JS 依赖
npm install

# 2. 搭建 Python 后端
cd api
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. 启动开发模式
npm run dev
```

Windows 用户也可以直接双击 `launch.bat`，Linux/macOS 用 `./launch.sh` 免安装运行。

第一次出模型的推荐路径：装一个 mini 档位的扩展（显存要求低、出结果快），在 Workflows 页搭好「读图 → 生成网格 → 加入场景」三节点链，切到 Generate 页选中工作流后点「Generate 3D Model」。遇到问题直接看 Settings/Logs/Errors 面板，日志相当齐全，排查生成失败时第一入口就是这里。

## Modly CLI：给脚本和 Agent 留的正门

这是 Modly 最有意思的设计之一。它提供了一个 CLI（命令行工具），位于 `tools/modly-cli/agent.py`，**纯 Python 标准库实现**，允许外部脚本或 AI Agent 在不碰 UI 的情况下驱动一个运行中的 Modly 实例，且所有命令的机器可读 JSON 都走 stdout：

```bash
python tools/modly-cli/agent.py health                 # 健康检查
python tools/modly-cli/agent.py model list             # 列出已装模型
python tools/modly-cli/agent.py workflow-run status <run_id>   # 查询任务状态
python tools/modly-cli/agent.py generate --image ./input.png --output ./export.glb
```

其中 `generate` 是一条聚合命令：发起图像生成任务、轮询执行、导出最终网格，响应里还附带恢复元数据（如 `workflow-run cancel`），脚本侧可以做断点处理。

CLI 对命令面做了刻意的分层：

| 层级 | 命令 | 定位 |
|------|------|------|
| 规范命令 | `health`、`model`、`workflow-run`、`capability`、`process-run` | Modly 核心自动化契约 |
| 聚合命令 | `generate` | 发起任务 + 轮询 + 导出一条龙 |
| 兼容层 | `legacy` | 包裹旧版 `/generate/*` 任务端点 |
| 实验层 | `experimental` | ComfyUI 编排等外部能力，不算核心契约 |

这种「正门清晰、兼容层隔离」的设计意味着 Modly 不仅能给人用，也能被自动化流水线和 AI Agent 编排进更大的工作流——比如批量处理一批产品图生成 3D 素材。仓库里的 `tools/modly-cli/SKILL.md` 还专门定义了给 Agent 的工作流与输出契约。

## MCP 服务：第二条自动化入口

除了 CLI，Modly 的 `api/` 目录里还有一个 MCP（Model Context Protocol，模型上下文协议）服务：`api/mcp_server.py`。它把 Modly 的能力封装成 MCP 工具，暴露给 Claude Desktop、Codex CLI 这类支持 MCP 的外部 Agent——例如 `modly_list_models` 可以列出已下载就绪的 3D 生成模型。

使用前提有两个：Modly 的 FastAPI 后端要在本地 8765 端口运行，MCP 客户端（如 Claude Desktop）的配置里要注册这个服务的启动命令。CLI 走的是「脚本主动调用」，MCP 走的是「Agent 直接对话」，两条入口共用同一个后端，能力面保持一致。

对一个桌面应用来说，同时提供 CLI 与 MCP 两种自动化接入方式并不常见，这说明 Modly 从架构上就把「被自动化」当成了一等需求。

## 使用建议与边界

结合项目当前状态，几点务实建议：

- **显存先算账**：mini/fast/turbo 变体对显存友好；如果跑更高规格的模型，先确认 GPU 余量，顶栏 RAM 指示器和日志面板是第一排查入口。
- **macOS 用户注意**：只支持 Apple Silicon，Intel Mac 不在支持范围内。
- **许可证细节**：项目采用 MIT 协议，但附加了一条署名要求——fork（派生）并基于它构建自己的应用时，必须在应用 UI 或文档中保留对 [Modly](https://github.com/lightningpixel/modly) 及其作者 Lightning Pixel 的署名。商用二开前务必确认这一点。
- **合理预期**：开源图像转 3D 模型的网格质量与顶尖商业服务仍有差距，但对原型验证、游戏灰盒素材、快速视觉占位来说完全够用，且批量成本为零。

## 动手练习

想验证本文的说法，三条路线由浅入深：

1. **装起来跑一遍**：下载 Releases 安装包，装 modly-hunyuan3d-mini-extension，用手边任意一张轮廓清晰的照片生成第一个网格，观察顶栏 RAM 指示器的峰值。
2. **走一遍 CLI 正门**：应用保持运行，在仓库根目录执行 `python tools/modly-cli/agent.py health`，再依次试 `model list` 与 `generate`，体会 JSON 输出的结构化程度。
3. **读一份 manifest**：克隆任一官方扩展仓库，打开 `manifest.json` 与运行时入口文件，对照 Modly 的扩展安装流程，理解「壳 + 约定」的生态设计。

## 常见问题

**Q：没有独立显卡能用吗？**
推理发生在本地 GPU 上，显存是硬门槛。mini/fast 变体面向低显存场景，但具体数值以各扩展仓库的说明为准；纯核显机器大概率吃力。

**Q：生成的网格能直接用于生产吗？**
更适合原型验证与灰盒素材。对精度要求高的场景，建议在应用内先做平滑和减面，再导入 Blender 等工具精修。

**Q：CLI 和 MCP 该选哪个？**
脚本化批处理选 CLI（JSON 输出、可断点恢复）；想让对话式 Agent 直接调度 Modly，选 MCP 服务。两者共用同一个 FastAPI 后端，不冲突。

**Q：生成失败从哪里查起？**
Settings/Logs/Errors 面板保留了完整日志，常见原因是显存不足或模型权重未下载完成。

## 进阶方向

跑通基础流程后，下一步有几个方向值得探索：

- **自写扩展**：按 `manifest.json` 约定接入其他图像转 3D 模型，理解扩展系统的类型划分（模型类 vs 流程类）。
- **批量流水线**：用 CLI 的 `generate` 聚合命令串一条「目录扫描 → 批量生成 → 导出归档」的自动化管线。
- **Agent 编排**：参照 `tools/modly-cli/SKILL.md` 的契约，把 Modly 挂进更大的 Agent 工作流。

## 参考文献

- Modly 官方仓库与 README：[github.com/lightningpixel/modly](https://github.com/lightningpixel/modly)
- Modly Releases 下载页：[github.com/lightningpixel/modly/releases](https://github.com/lightningpixel/modly/releases)
- Hunyuan3D 2 模型仓库：[github.com/Tencent-Hunyuan/Hunyuan3D-2](https://github.com/Tencent-Hunyuan/Hunyuan3D-2)
- TripoSG 模型仓库：[github.com/VAST-AI-Research/TripoSG](https://github.com/VAST-AI-Research/TripoSG)
- TRELLIS 模型仓库：[github.com/microsoft/TRELLIS](https://github.com/microsoft/TRELLIS)
- Modly 社区 Discord：[discord.gg/BvjDCvS3yr](https://discord.gg/BvjDCvS3yr)

本文中的 star 数、fork 数与更新状态来自 GitHub API（查询时间 2026 年 8 月），架构与命令细节核对自仓库 README 与源码。
