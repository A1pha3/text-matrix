---
title: "Modly：一张照片变 3D 模型，全程跑在你自己的 GPU 上"
date: 2026-08-18T03:22:27+08:00
draft: false
description: "开源桌面应用 Modly 把图像转 3D 网格这件事搬到了本地：开源模型、本地推理、节点式工作流，还有一套给 Agent 用的 CLI。本文拆解它的架构、模型生态与上手路径。"
tags: ["AI", "3D 生成", "开源工具", "桌面应用", "AI 工具"]
categories: ["技术笔记"]
github_repo: "lightningpixel/modly"
source_key: "gh:lightningpixel/modly"
slug : modly-local-ai-image-to-3d
---

## 一句话认识 Modly

[Modly](https://github.com/lightningpixel/modly) 是一个本地运行的图像转 3D（image-to-3D mesh）桌面应用：丢进去一张照片，出来一个可以导出的 3D 网格模型，中间所有 AI 推理都发生在你自己的 GPU 上——不联网上传、不按次付费、不看服务商脸色。

用 TypeScript 写的 Electron 桌面端，配一个 Python（FastAPI）后端承载模型推理，支持 Windows、Linux 和 Apple Silicon macOS 三平台。截至本文写作时，项目已积累 6,200+ star，并且仍在高频更新。

它解决的核心痛点很直接：图像转 3D 这件事，云服务要么按次收费，要么对你的图片数据有留存风险。Modly 的答案是「开源模型 + 本地推理 + 可扩展的模型生态」，让你在自己的显卡上完成整条流水线。

## 为什么「本地」是关键差异

市面上的图像转 3D 服务不少，但绝大多数是云端 API：上传图片、排队、出结果。这带来三个问题——

1. **成本**：按次计费，批量制作素材时费用快速失控；
2. **隐私**：产品原型图、客户素材上传到第三方服务器，未必符合你的数据合规要求；
3. **可定制性**：云端服务的模型版本、参数你说了不算。

Modly 把推理全部拉回本地。显存够的跑大模型，不够的跑 mini/fast 变体，全程数据不出机器。对独立游戏开发者、3D 素材创作者、产品原型设计者来说，这是一条确定性更高的工作流。

## 架构拆解：Electron 壳 + Python 推理芯

Modly 的工程结构并不复杂，但分层清晰：

- **桌面层**：Electron + TypeScript。负责 UI、节点式工作流编辑器、任务队列和本地服务管理。顶栏有一个来自主进程的实时内存（RAM）指示器，方便监控推理时的资源占用。
- **推理层**：Python 虚拟环境里的 FastAPI 后端，承载 3D 生成模型的加载与推理。前后端通过本地 HTTP 接口通信——这也是后文 CLI 能绕过 UI 直接调用它的基础。
- **工作流层**：采用节点图（node graph）组织生成流程，例如最基础的 `Image → Generate Mesh → Add to Scene` 三节点链。工作流在运行前会做连接校验，非法的图不会把你当前的网格视图丢掉，而是以内联提示或 toast 警告的形式反馈——这类工程细节对一个仍在快速迭代的项目来说相当扎实。

## 模型生态：五个官方扩展，一份 manifest 约定

Modly 本体不带模型，而是通过**扩展系统**引入生成模型。每个扩展是一个独立的 GitHub 仓库，内含 `manifest.json` 和对应类型的运行时入口文件。官方目前提供五个扩展：

| 扩展 | 模型 |
|------|------|
| modly-hunyuan3d-mini-extension | Hunyuan3D 2 Mini |
| modly-hunyuan3d-mini-turbo-extension | Hunyuan3D 2 Mini Turbo |
| modly-hunyuan3d-mini-fast-extension | Hunyuan3D 2 Mini Fast |
| modly-triposg-extension | TripoSG |
| modly-trellis2-gguf-extension | Trellis2 GGUF |

这个设计有几个值得注意的地方：

- **模型选型开放**：Hunyuan3D（腾讯混元）、TripoSG、TRELLIS 都是社区里活跃的图像转 3D 开源模型，Modly 选它们作为官方扩展，说明定位是「本地推理的壳与工作流引擎」，而不是绑定某一个模型。
- **安装即填 URL**：在 Models 页面点「Install from GitHub」，粘贴扩展仓库的 HTTPS 地址即可安装；模型类扩展装完再下载模型权重或选定变体（variant），流程类扩展装完即用。
- **社区可扩展**：`manifest.json` 是一份公开约定，任何开发者都可以按约定发布自己的模型扩展，Modly 生态因此不被官方列表锁死。

## 上手路径：从安装到出第一个模型

**方式一：直接装**。到 Releases 页下载对应平台的安装包（注意：macOS 版仅支持 Apple Silicon）。

**方式二：源码运行**（也适合二次开发）：

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

第一次出模型的推荐路径：装一个 mini 档位的扩展（显存要求低、出结果快），在 Workflows 页搭好 `Image → Generate Mesh → Add to Scene` 基础链，切到 Generate 页选中工作流后点「Generate 3D Model」。遇到问题直接看 Settings/Logs/Errors 面板，日志相当齐全。

另一个实用功能：导入的外部网格可以在应用内做平滑（smoothing）和减面（decimation），优化后的结果直接写回工作区，省去了在 Blender 里来回导出的环节。

## Modly CLI：给 Agent 和脚本留的正门

这是 Modly 最有意思的设计之一。它提供了一个**纯标准库实现**的 CLI（`tools/modly-cli/agent.py`），允许外部脚本或 AI Agent 在不碰 UI 的情况下驱动一个运行中的 Modly 实例，且所有命令的机器可读 JSON 都走 stdout：

```bash
python tools/modly-cli/agent.py health                 # 健康检查
python tools/modly-cli/agent.py model list             # 列出已装模型
python tools/modly-cli/agent.py workflow-run status <run_id>   # 查询任务状态
python tools/modly-cli/agent.py generate --image ./input.png --output ./export.glb
```

其中 `generate` 是一条聚合命令：发起图像生成任务、轮询执行、导出最终网格，响应里还附带恢复元数据（如 `workflow-run cancel`），脚本侧可以做断点处理。

CLI 对命令面做了刻意的分层：`health` / `model` / `workflow-run` / `capability` / `process-run` 是规范命令（canonical）；`legacy` 包裹旧版任务端点；`experimental` 下的 ComfyUI 编排属于外部实验能力，不算 Modly 核心契约。这种「正门清晰、兼容层隔离」的 API 设计，对一个开源桌面项目来说相当超前——它意味着 Modly 不仅能给人用，也能被自动化流水线和 AI Agent 编排进更大的工作流（比如批量处理一批产品图生成 3D 素材）。

## 使用建议与边界

结合项目当前状态，几点务实建议：

- **显存先算账**：mini/fast/turbo 变体对显存友好；如果跑更高规格的模型，先确认 GPU 余量，顶栏 RAM 指示器和日志面板是第一排查入口。
- **macOS 用户注意**：只支持 Apple Silicon，Intel Mac 不在支持范围内。
- **许可证细节**：项目采用 MIT 协议，但有一条署名要求——fork 并基于它构建自己的应用时，必须在应用 UI 或文档中保留对 [Modly](https://github.com/lightningpixel/modly) 及其作者的署名。商用二开前务必确认这一点。
- **合理预期**：开源图像转 3D 模型的网格质量与顶尖商业服务仍有差距，但对原型验证、游戏灰盒素材、快速视觉占位来说完全够用，且批量成本为零。

## 写在最后

Modly 的价值不在于发明了新的 3D 生成模型，而在于把「开源模型 + 本地推理 + 可扩展生态 + 可自动化接口」这四件事拼成了一个开箱即用的桌面产品。节点式工作流给了人操作的灵活性，manifest 扩展约定给了模型生态生长空间，CLI 则把它接入了正在到来的 Agent 自动化时代。

对于需要频繁产出 3D 素材又在意成本与数据隐私的创作者，值得装一个试试。

项目地址：[github.com/lightningpixel/modly](https://github.com/lightningpixel/modly)
