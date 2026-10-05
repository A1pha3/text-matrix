---
title: "CUA：26.6k Star 的开源 Computer-Use 基础设施，让 AI Agent 拥有一台完整电脑"
date: "2026-05-14T15:22:32+08:00"
lastmod: "2026-09-27T00:00:00+08:00"
slug: "trycua-cua-open-source-computer-use-agents"
github_repo: "trycua/cua"
source_key: "gh:trycua/cua"
description: "CUA（trycua/cua）是 26.6k Star 的开源计算机使用基础设施：Rust 驱动器后台操控 macOS/Windows/Linux 桌面，云地统一的沙箱 SDK，gym 式基准环境与专用小模型 CUA-S1。本文拆解五大板块、一次任务的完整流转与采用边界。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Computer Use", "沙箱", "开源", "Rust"]
---

# CUA：26.6k Star 的开源 Computer-Use 基础设施，让 AI Agent 拥有一台完整电脑

## 一、学习目标

读完本文，你应该能判断 CUA 适不适合你的场景，以及从哪个入口上手：

- 说清 CUA 解决的问题与"Computer-Use 2.0"的含义
- 分清五个板块的职责边界：Driver、Fleets/Sandbox SDK、Bench、CUA-S1、Lume
- 看懂一次计算机使用任务如何穿过这套系统
- 知道许可证边界（MIT 之外的两个例外）与权限模式怎么选
- 根据自己的平台和团队情况，决定从哪个组件开始用

## 二、目录

- [一、学习目标](#一学习目标)
- [二、目录](#二目录)
- [三、项目概览](#三项目概览)
- [四、判断：CUA 解决的不是点击，是给 agent 一台完整的电脑](#四判断cua-解决的不是点击是给-agent-一台完整的电脑)
- [五、板块地图：先分清五个东西](#五板块地图先分清五个东西)
- [六、核心机制](#六核心机制)
- [七、一次任务如何流过 CUA](#七一次任务如何流过-cua)
- [八、许可证与安全边界](#八许可证与安全边界)
- [九、采用判断](#九采用判断)
- [十、自测题](#十自测题)
- [十一、练习](#十一练习)
- [十二、进阶路径](#十二进阶路径)
- [十三、资料口径说明](#十三资料口径说明)

## 三、项目概览

**CUA**（[trycua/cua](https://github.com/trycua/cua)，官网 [cua.ai](https://cua.ai)）是 Cua AI 公司开源的计算机使用（Computer-Use）基础设施：给 AI agent 提供可驱动的桌面、隔离的运行环境、可验证的评测任务，以及配套的专用小模型。仓库自 2025 年 1 月创建，迭代速度很快，nightly 通道每天都在发版。

| 指标 | 数值（2026-09-27 GitHub API 快照） |
|------|------|
| Stars | 26,580 |
| Forks | 1,842 |
| 代码构成 | HTML 19.3 MB、Rust 13.3 MB、Python 11.3 MB、TypeScript 3.4 MB、Go 2.7 MB |
| 许可证 | MIT（两个例外，见第八节） |
| 主页 | [cua.ai](https://cua.ai)，云桌面在 [run.cua.ai](https://run.cua.ai) |
| 最近推送 | 2026-09-27（持续活跃） |

代码构成里最值得注意的是 Rust：桌面驱动的核心用 Rust 实现，通过 UniFFI 绑定暴露给 Python 和 TypeScript，这不是一个纯 Python 项目。

## 四、判断：CUA 解决的不是点击，是给 agent 一台完整的电脑

计算机使用（computer use）这件事，过去分散在三处：驱动桌面的自动化工具、隔离运行的虚拟化环境、评测 agent 能力的学术基准。三者互不相通——评测环境不能直接上生产，自动化工具不管隔离，托管方案绑定厂商自己的模型。

CUA 的做法是把这三件事拆成一组各自可用、也能拼装的开源件，并且给了一个统一的说法，叫 **Computer-Use 2.0**：agent 在同一个任务里穿行于代码、API 和图形界面——能用 API 就调 API，必须点界面时再去点屏幕，而不是把"操作 GUI"当成唯一手段。

这个定位决定了它的工程气质：驱动器说 MCP 协议、权限分档管理、评测环境给到 gym 风格接口。它不是演示项目，而是按"agent 的操作系统底层"来设计的。

## 五、板块地图：先分清五个东西

README 把仓库分成五个板块，加上独立发布的 Python SDK，一共六样东西。先看清楚边界，再谈机制：

| 板块 | 职责 | 形态 |
|------|------|------|
| Cua Driver | 在后台检查和操作原生应用与浏览器 | Rust 运行时，跑在 macOS / Windows / Linux，通过 MCP 或 CLI 供 agent 调用 |
| Cua Fleets | 云端隔离桌面，按池取用 | 托管服务（run.cua.ai），用 Sandbox SDK 操作 |
| Sandbox SDK | 云端与本地统一的沙箱 API | `pip install cua-sandbox` |
| Cua Bench | 造任务、评 agent、导出训练轨迹 | `cua-bench` Python 包，gym 风格接口 |
| CUA-S1 | 专用小模型，做"快而有界"的界面决策 | 源码在仓库，权重在 Hugging Face |
| Lume | 在 Apple Silicon 上本地跑 macOS / Linux 虚拟机 | 独立 CLI |

一句话概括关系：Driver 管"动手"，Sandbox/Fleets 管"在哪台电脑上动手"，Bench 管"动手能力怎么打分"，CUA-S1 是官方提供的"动手决策"模型，Lume 是本地虚拟化的底座。

## 六、核心机制

### 6.1 Cua Driver：后台控制与 MCP 边界

Driver 是整个项目最有差异化的部分。它在后台驱动原生应用，不抢光标、不抢焦点、不占屏幕——前提是应用和平台支持这种投递方式；不支持的场景会退回常规前台操作，官方文档对每条平台的边界都有对照表。

几个值得展开的设计：

- **Rust 内核，多语言皮**。核心逻辑是 Rust，通过 UniFFI 生成的绑定暴露类型化的 Python（`cua_driver`）和 TypeScript（`@trycua/cua-driver`）SDK，底层是一个带版本号的 C ABI。应用直接嵌入时不需要守护进程。
- **MCP 是 agent 的接入边界**。支持 MCP 的 agent（Claude Code、Cursor 等）直接连 `cua-driver mcp`；偏好 shell 的场景用 `cua-driver call`。agent 走 MCP，应用程序走语言 SDK，两条通道不混。
- **权限三档**。`standard` 是默认档，正常自动化无感；`bounded` 只放行审阅过的清单里的工具和资源；`unrestricted` 需要 `--dangerously-bypass-approvals` 显式绕过。权限档在进程启动时固定，改档要重启。
- **操作历史（macOS 预览）**。nightly 构建提供可选的加密操作历史，只存一份严格的元数据允许清单，全部留在本地；截图、输入文本、剪贴板内容这些敏感数据一律不落盘。

安装（macOS / Linux）：

```bash
/bin/bash -c "$(curl -fsSL https://cua.ai/driver/install.sh)"
```

Windows（PowerShell）：

```powershell
irm https://cua.ai/driver/install.ps1 | iex
```

### 6.2 Sandbox SDK 与 Cua Fleets：云和本地同一套 API

Sandbox SDK 回答的问题是"agent 在哪台电脑上操作"。同一套 API 覆盖本地沙箱和云端 Fleet，共享的是接口，不同的是凭证、镜像、可用操作和运行时要求：

- **本地**：`Sandbox.ephemeral(Image.linux(), local=True)` 起一个临时沙箱，底层可以是容器或 QEMU 虚拟机。
- **云端 Fleet**：在 run.cua.ai 开通后，代码从一个桌面池里认领（claim）一台机器，用完按教程释放资源。官方文档特别提醒：池子里认领结束后的容量可能继续计费，清理步骤不能省。

需要类型化的桌面控制时，装 `cua-sandbox[driver]` 附加项，通过 `sb.driver.connect()` 把 Driver 接进沙箱——这个附加项会固定 driver 的兼容版本，沙箱镜像里也要跑对应的 Driver 服务，版本对不上就连不上，这是排障时最容易踩的坑。

### 6.3 Agent SDK：把 LLM 接上沙箱

`cua` 总包是面向 agent 开发者的入口，把沙箱和 LLM 编排包在一起：

```bash
pip install cua
```

要求 Python 3.12 或 3.13（3.11 可以直接装 `cua-sandbox`）。官方 Quick Start：

```python
from cua import Sandbox, Image, ComputerAgent

# Ephemeral local sandbox with an agent
async with Sandbox.ephemeral(Image.linux(), local=True) as sb:
    await sb.shell.run("uname -a")

    agent = ComputerAgent(model="anthropic/claude-sonnet-4-5", tools=[sb])
    async for response in agent.run("Open the browser and go to example.com"):
        print(response)
```

`ComputerAgent` 底层是 liteLLM 集成，OpenAI、Anthropic、Gemini 的 API 后端默认可用，模型随便换——这正是它和厂商托管方案的根本区别：CUA 只提供"电脑"，不绑定"脑子"。视觉定位（把模型输出的坐标落到屏幕元素上）可以通过附加项扩展：`cua[omni]` 装 SOM 方案，`cua[uitars-mlx]`、`cua[uitars-hf]` 分别接 UiTars 的 MLX 和 HuggingFace 版本。

一个要注意的默认行为：匿名使用统计默认开启，介意的话按文档里的一行配置关掉。

### 6.4 Cua Bench：可验证的任务环境

Cua Bench 定位是"给 computer-use agent 造可验证的跨平台任务"。它的设计借鉴了强化学习的 gym 接口：`make()` 建环境、`reset()` 回到初始态、`step()` 执行动作、`evaluate()` 打分，奖励是可判定的（比如某个字段是否被正确填写），环境跑在 Playwright 模拟的浏览器里。

对个人开发者友好的一点是入门零依赖：模拟任务不需要虚拟机、不需要 Docker、不需要模型 API key。官方推荐的起手式：

```bash
uv tool install 'cua-bench[browser]'
uv tool run --from 'cua-bench[browser]' playwright install chromium
```

跑通后做三件事：创建一个小任务，运行它的参考解法，确认评估器给出的 reward 是 `1.0`；再亲手做一遍同一个任务。读分数时要记住边界：模拟环境里的 reward 只判定任务是否完成，不能直接推出 agent 在真实桌面、真实应用上的泛化能力。跑分之外，Bench 能导出操作轨迹——评测环境同时是训练数据的产地。Bench 另有独立官网 [cuabench.ai](https://cuabench.ai/)。

### 6.5 CUA-S1：给"快决策"专用的小模型

CUA-S1 是项目新开辟的一条线：不用通用大模型做每一步界面决策，而是训练小型专用模型（官方叫 System 1 模型，借认知科学里"快思考"的类比）处理那些高频、有界、答案确定的决策——比如表单里某个字段该填哪个值、某个元素该不该碰。

需要分清的是：它不替代通用 agent 的规划与推理，只接管其中"快而有界"的那部分；应用代码负责排布动作，Driver 负责执行。第一个公开的研究方向是表单填写（CUA-S1-FORMS）：模型从结构化的界面元素和文档取值里打分决策，而不是逐 token 生成回复。

目前的状态是早期研究发布：Python 源码、合成数据生成、训练与评估代码都在仓库里（MIT），模型权重和数据集单独放在 Hugging Face（[cua-ai/cua-s1-forms](https://huggingface.co/cua-ai/cua-s1-forms)），每个模型卡和数据卡里写明各自的适用范围与许可证。

### 6.6 Lume：Apple Silicon 上的本地虚拟机

Lume 用苹果的 Virtualization.Framework 在 Apple Silicon 上创建和管理 macOS、Linux 虚拟机，性能接近原生。它和 Sandbox SDK 是互补关系：Lume 管本机虚拟机的生命周期，Sandbox SDK 之上做统一操作。

```bash
/bin/bash -c "$(curl -fsSL https://cua.ai/lume/install.sh)"
```

官方教程的示例是从苹果恢复镜像创建一个原版 macOS Tahoe 虚拟机、启动、用 SSH 连上去。仓库里另有 lumier、qemu-docker、kasm 等配套组件目录。

## 七、一次任务如何流过 CUA

把组件串起来看一次真实任务。目标来自官方教程：让 agent 在 Calculator 里算出 6 × 7，并验证界面显示 42。

1. **选运行时**。想省事，在 run.cua.ai 的 Fleet 里认领一台 Linux 桌面；想全本地，用 Lume 起一台虚拟机，或者直接在本机装 Driver。
2. **接 agent**。Claude Code、Cursor 这类 MCP 客户端连 `cua-driver mcp`；自己写的 agent 用 `cua` 总包，把沙箱作为 tools 传给 `ComputerAgent`。
3. **执行**。agent 发出"打开 Calculator"的指令，Driver 在后台驱动应用——前台你的终端照常用，光标不动、焦点不丢。每一步动作都有明确的边界：哪次截屏授权了哪次点击。
4. **验证**。Driver 读回界面状态，agent 确认显示 42，任务闭环。
5. **沉淀**。如果这是用 Cua Bench 造的任务，`evaluate()` 给出可判定的 reward；整个会话可以导出成轨迹，回头喂给训练流程，或者变成回归测试——改了 agent 之后重放一遍，看行为有没有退化。

这条链路说明了各组件的分工：Driver 负责"动"，Sandbox/Fleets 负责"在哪动"，Bench 负责"动得对不对"，轨迹把三者的产出串成可复用的数据。

## 八、许可证与安全边界

主体是 MIT，但有两处例外，商用或二次分发前必须分清：

1. **`cua-som`**（可选的视觉定位包）采用 AGPL-3.0-or-later，其 Ultralytics 依赖另有自己的许可证。
2. **`cua-perception` 扩展**（Driver 的可选视觉感知扩展）不是 MIT：它组合了 AGPL-3.0-only 的 OmniParser 图标检测模型、Apache-2.0 的 PP-OCR 模型和独立打包的 ONNX Runtime。装来自己用没问题；但再分发或通过网络向用户提供服务，可能触发 AGPL 的开源义务。官方原话很直接：如果组织不接受 AGPL 组件，就不要安装这个扩展。不带模型产物的 Driver 本体不受影响。

安全机制上，Driver 的权限三档（standard / bounded / unrestricted）决定了 agent 能碰什么；连接用户已登录的 Chromium 配置文件这类敏感操作需要显式授权（`--grant existing-profile`）。用云端 Fleet 时还要补一条成本边界：认领结束后的池容量可能继续计费，按教程清理。

## 九、采用判断

把 CUA 放进同类方案里看定位：

| 方案 | 性质 | 与 CUA 的关系 |
|------|------|--------------|
| 学术基准（OSWorld 等） | 提供任务集与评估器，重在评测打分 | Cua Bench 与之互补：任务可交互、奖励可判定，评测之外还提供生产可用的驱动与沙箱 |
| 厂商托管能力（Anthropic computer use、OpenAI Operator 等） | 绑定自家模型与基础设施 | CUA 模型无关，bring your own agent and model；可以接这些模型，但不依赖它们 |
| 系统辅助功能 API（macOS AX、Windows UIA） | 单平台的底层自动化通道 | Driver 以这类通道为底座，封装出跨平台接口、后台投递与权限管理 |

据此给三类团队的建议：

- **现在就值得上手**：在做桌面自动化或 agent 评测的团队，从 Cua Bench 的模拟任务和 Driver 的 Calculator 教程起步，一天内能看到完整闭环；Apple Silicon 用户想本地跑虚拟机，直接装 Lume。
- **可以先用起来但别急着上生产**：想构建"操作电脑的 agent"产品的团队，Sandbox SDK 加 Agent SDK 的组合能快速出原型，但 Driver 对各平台、各应用的支持程度参差，先查官方的平台支持对照表，再决定目标场景。
- **暂时不用碰**：纯 API 调用就能完成的任务（不需要看屏幕、点界面），引入 computer use 是白付沙箱与延迟的成本；不接受 AGPL 组件的组织，绕开 `cua-perception` 扩展即可，Driver 本体不受影响。

## 十、自测题

**问题 1：Computer-Use 2.0 指的是什么？**

<details>
<summary>参考答案</summary>

agent 在同一个任务里穿行于代码、API 和图形界面：能用 API 就调 API，必要时才去操作 GUI。它是对"操作图形界面"这种单一手段的修正，而不是更炫的点击方式。

</details>

**问题 2：Driver 的"后台控制"有没有前提？**

<details>
<summary>参考答案</summary>

有。后台投递要求应用和平台本身支持；不支持的场景退回前台操作。另外权限档在进程启动时固定，standard / bounded / unrestricted 三档的能力边界不同，改档要重启。

</details>

**问题 3：为什么 `cua-perception` 扩展不能再分发？**

<details>
<summary>参考答案</summary>

它包含 AGPL-3.0-only 的 OmniParser 模型产物。再分发或通过网络提供服务可能触发 AGPL 的对应源码义务，而 Cua 只拥有 Driver 本体的 MIT 授权，无法替第三方放松模型侧的条款。

</details>

**问题 4：云端 Fleet 和本地沙箱在代码层面有多大差别？**

<details>
<summary>参考答案</summary>

API 层面是同一套 Sandbox SDK，`local=True` 与否只切换运行时。差别在凭证、镜像、可用操作和运维要求上——比如 Fleet 需要管理认领与资源清理，本地需要自己管虚拟机生命周期。

</details>

**问题 5：CUA-S1 和通用 agent 是什么关系？**

<details>
<summary>参考答案</summary>

分工而非替代。CUA-S1 接管高频、有界、答案确定的快决策（如表单取值），通用 agent 保留规划与推理；应用代码排布动作，Driver 执行。

</details>

## 十一、练习

**练习 1：驱动 Calculator 完成一次闭环**

1. 按 macOS / Linux 安装脚本装好 Cua Driver，按官方教程给 agent 配好权限。
2. 让 agent 在 Calculator 里计算 6 × 7，并验证界面显示 42。
3. 全程在前台开一个终端打字，确认光标和焦点没有被抢走（前提是你的应用与平台支持后台投递；不支持时观察前台行为差异）。

**练习 2：跑通 Agent SDK 的最小任务**

1. `pip install cua`（确认 Python 3.12 或 3.13）。
2. 把第六节的 Quick Start 代码跑起来，观察沙箱内 `uname -a` 的输出与 agent 操作浏览器的过程。
3. 换一个模型后端（改 `ComputerAgent` 的 `model` 参数），对比行为差异。

**练习 3：用 Cua Bench 验证一个任务**

1. `uv tool install 'cua-bench[browser]'` 并安装 Playwright 的 Chromium。
2. 按官方教程创建一个模拟任务，运行参考解法，确认评估器报告 reward 为 `1.0`。
3. 把这个任务亲手做一遍，体会"参考解、评估器、轨迹"三者在评测里的分工。

## 十二、进阶路径

1. **过一遍官方四个入门教程**：[驱动第一个应用](https://cua.ai/docs/tutorials/drive-your-first-app)、[第一个云 Fleet](https://cua.ai/docs/tutorials/your-first-cloud-fleet)、[第一个 Lume 虚拟机](https://cua.ai/docs/tutorials/create-your-first-lume-vm)、[第一个 Bench 任务](https://cua.ai/docs/tutorials/your-first-cua-bench-task)。四个教程正好对应四个板块。
2. **读 Driver 的协议与权限文档**：[MCP 协议与技能](https://github.com/trycua/cua/blob/main/libs/cua-driver/docs/mcp-protocol-and-skills.md)讲清 stdio 配置与 HTTP 限制；权限模式参考决定你的部署形态。
3. **评估 CUA-S1 的适用性**：读 [模型卡](https://github.com/trycua/cua/blob/main/libs/cua-s1/MODEL_CARD.md)与[安全与部署指引](https://github.com/trycua/cua/blob/main/libs/cua-s1/SECURITY.md)，再决定是否引入表单场景。
4. **进社区**：[Discord](https://discord.com/invite/mVnXXpdE85) 问问题，GitHub Issues 报缺陷；平台支持矩阵、perception 边界这类随版本变动的细节，以仓库内文档为准。

## 十三、资料口径说明

1. **数据来源**：Stars、Forks、语言构成、最近推送取自 GitHub API，快照时间 2026-09-27；各板块的能力描述与安装命令取自仓库 `main` 分支 README 及 `libs/` 下各组件 README（同日快照）。
2. **版本状态**：Driver 与 Lume 走 nightly 通道持续发版（写作时 nightly 为 cua-driver-rs 0.30.2、lume 0.5.4）；正文不给 stable 版本号，安装时以官方发布页为准。
3. **许可证**：主仓库 MIT；`cua-som` 为 AGPL-3.0-or-later；`cua-perception` 扩展含 AGPL-3.0-only 模型产物，非 MIT。学术引用的元数据见仓库 `CITATION.cff`。
4. **未验证项**：本文不含独立性能测试；Driver 在各平台、各应用上的后台投递支持程度以官方[平台支持对照表](https://cua.ai/docs/reference/cua-driver/platform-support)为准；云端 Fleet 的计费与清理以官方教程为准。
5. **时效提醒**：该项目迭代快，API 与命令可能随后续版本变化；发现本文与官方文档不一致时，以[官方仓库](https://github.com/trycua/cua)与[文档站](https://cua.ai/docs)为准。

---

CUA 把"给 agent 一台电脑"拆成了驱动、沙箱、评测、模型四件可独立使用的事，MIT 主许可降低了试错成本，Rust 驱动和 gym 式评测又把工程上限抬高了一截。如果你正在为 agent 补上"动手能力"这一环，从这里开始比从零造轮子划算得多。

延伸阅读：[官网](https://cua.ai) | [文档](https://cua.ai/docs) | [GitHub](https://github.com/trycua/cua) | [Discord 社区](https://discord.com/invite/mVnXXpdE85)
