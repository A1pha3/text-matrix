---
title: "ViMax 上手指南：从 API Key 到第一条成片"
date: "2026-05-19T20:25:00+08:00"
lastmod: 2026-10-01
slug: "vimax-agentic-video-generation-hku"
github_repo: "HKUDS/ViMax"
source_key: "gh:HKUDS/ViMax"
description: "ViMax 是香港大学 HKUDS 实验室的开源多智能体视频生成框架。本文是实操指南：三类 API Key 怎么配、TUI、脚本与 Web UI 三种入口怎么选、四条工作流各自适合什么、一次任务的钱花在哪，以及 macOS 用户和账单超支的应对。"
draft: false
categories: ["技术笔记"]
tags: ["AI视频生成", "AI Agent", "多智能体", "开源项目"]
---

## 先给判断

ViMax 不生成任何像素。它把视频创作流程拆成一串智能体（Agent）步骤——扩写故事、抽取角色、生成分镜、挑选参考图、逐镜头出片、最后拼接，每一步都去调你配置好的外部模型 API。所以它的画质上限就是你所接模型的画质上限，它自己负责的是中间那段最繁琐的编排：让角色跨镜头不换脸、让场景前后接得上。

这个定位决定了它的用法：你得先备好对话、图像、视频三类模型的 API Key，几乎每一步都在调付费服务。想清楚成本、选对入口、走对工作流，是跑通它的三道前置题，本文逐一过一遍。

读完这篇你能：配好一份可运行的 `idea2video` 配置、在 TUI、脚本和 Web UI 三种入口之间做出选择、知道四条工作流各自吃哪种输入、估算一次生成的账单构成，并且在遇到中断、超支、角色变脸时知道去哪查。

<!--more-->

本文基于 2026 年 10 月 1 日的仓库状态（v1.2.0，12,542 stars）与 main 分支源码写成。想理解它内部为什么这样设计——13 个智能体模块怎么分工、一致性机制怎么落地——请读站内另一篇[《ViMax 架构解读》](../vimax-agentic-video-generation-architecture/)；本文只管把它跑起来。

## 开始前的三件事

### 备好三类 API Key

ViMax 的每个环节都在调外部服务，配置里要填三段：

| 环节 | 干什么 | README 示例 | 备注 |
| ---- | ---- | ---- | ---- |
| 对话模型 | 扩写故事、写剧本、做首帧择优 | OpenRouter 的 Gemini 2.5 Flash Lite | 也可用 MiniMax（见下） |
| 图像生成 | 角色三视图、镜头首帧 | Nanobanana（Google 官方 API） | 见下方模型清单 |
| 视频生成 | 逐镜头片段 | Veo（Google 官方 API） | 见下方模型清单 |

对话模型经 LangChain 的 `init_chat_model` 接入，只要供应商兼容 OpenAI 协议就能配。MiniMax 从 2026 年 3 月起是一等公民：配置里写 `model_provider: minimax`，base URL 自动解析，API Key 也可以走 `MINIMAX_API_KEY` 环境变量而不写进配置文件。官方提供 `configs/idea2video_minimax.yaml` 和 `configs/script2video_minimax.yaml` 两个完整示例。

图像和视频模型全部走 `tools/` 目录下的适配器，当前 main 分支上有 10 个：

- 图像（4 个）：Nanobanana Google 官方 API、Nanobanana 云雾中转、豆包 Seedream 云雾中转、OpenRouter（GPT Image 2）
- 视频（5 个）：Veo Google 官方 API、Veo 云雾中转、豆包 Seedance 云雾中转、Google Omni 云雾中转、OpenRouter（Seedance 2.0 Fast）
- 辅助（1 个）：BGE 重排序适配器（默认模型 BAAI/bge-reranker-v2-m3，走 `/rerank` 端点），服务于参考图挑选

值得注意的是云雾（yunwu）中转的密度——图像和视频两类共 9 个生成器适配器里，云雾版占 5 个。项目方明显预期了大量国内用户：没有 Google API 也能用国产中转把整条链跑通，代价是生成质量随中转和模型而定，且要自行评估中转服务的稳定性。

### 确认你的环境

环境要求来自 README 与 `pyproject.toml`，两条都要看：

- **操作系统只有 Linux 和 Windows**。README 的 Environment 一栏只列这两个，`pyproject.toml` 里 PyTorch 的安装源也只为 `linux` 和 `win32` 配置了索引。macOS 用户不是"没测试过"，是官方没有提供安装路径，强跑需要自己解决依赖，出问题无解可查。
- **Python 3.12 及以上，用 [uv](https://docs.astral.sh/uv/getting-started/installation/) 管理依赖**。uv 负责建虚拟环境和装包，不需要手动 pip install。

一个有意思的细节：`pyproject.toml` 里的项目内部名是 `autolongvideogeneration`——包名还留着项目早期的代号，README 和发布版本早已统一叫 ViMax。翻它的配置时不要求甚解，照抄即可。

### 对成本有个预期

ViMax 的计费模型是"按环节调 API"：一次 Idea2Video 任务，至少包含 1 次故事扩写、每个角色 3 张肖像、每个镜头的图像生成加视频生成、镜头之间的转场视频。成本随镜头数线性增长，镜头数又随场景数和分镜密度走。

还有一处容易漏的默认值：**首帧图像默认一次生成 2 张候选，再由视觉模型（VLM）挑一张**。配置键是 `image_selection.num_candidates`，设为 `1` 可关掉择优。这个开关直接让帧图像的 API 花费翻倍或减半，第一次试跑建议关掉。

压成本的三个手段，按见效程度排：把场景数压少（官方示例用"不超过 3 个场景"）、关掉首帧双候选、角色数量控制。断点续跑机制（后文详述）保证中断重跑不重复计费，但不能让总价变便宜。

## 安装

```bash
git clone https://github.com/HKUDS/ViMax.git
cd ViMax
uv sync
```

三条命令在任何入口下都一样。跑完 `uv sync`，仓库根目录会多一个 `.venv`，所有后续命令都在仓库根目录执行。

## 三种入口怎么选

v1.2.0 之后 ViMax 有三种用法，共用同一套底层管线，差别在交互方式：

| 入口 | 适合 | 交互方式 |
| ---- | ---- | ---- |
| Agent TUI | 日常主力用法 | 终端对话，改需求、续会话 |
| 脚本直跑 | 理解管线、固定任务复跑 | 改配置文件和脚本变量 |
| Web UI | 想要看板、预览分镜和渲染进度 | 浏览器操作，与 TUI 同一套运行时 |

### Agent TUI（推荐入口）

TUI 是 2026 年 6 月上线的交互工作流：你跟一个 Agent 对话，讨论想法、修改剧本、决定何时开始渲染，会话可以存下来下次继续。终端界面用 React 的终端渲染框架 Ink 实现，仓库根目录的 `vimax` 脚本是启动入口：

```bash
cp configs/agent.example.yaml configs/agent.local.yaml
# 编辑 agent.local.yaml，填 llm / image / video 三段
./vimax tui
```

会话管理是 TUI 的核心能力：

```bash
./vimax tui new              # 新建会话
./vimax tui resume           # 恢复当前活跃会话
./vimax tui resume <id>      # 恢复指定会话
```

配置文件 `agent.local.yaml` 分 `llm`、`image`、`video` 三段，每段填 `model`、`base_url`、`api_key`。API Key 也可以不落盘，改用环境变量 `VIMAX_LLM_API_KEY`、`VIMAX_IMAGE_API_KEY`、`VIMAX_VIDEO_API_KEY`。

TUI 背后是 `agent_runtime/` 目录的运行时，它把三条已落地的工作流包装成两个对话工具：`vimax_narrative_planning` 吃 idea 或 script，`vimax_novel_planning` 吃长篇小说文本。你不需要记这些名字——在 TUI 里说"根据这段小说做分集视频规划"，运行时会自己选。

### 脚本直跑（理解管线用）

仓库根目录的 `main_idea2video.py` 和 `main_script2video.py` 是最原始的入口。用法分两步：先配 `configs/idea2video.yaml`，再把创意写进脚本变量。

配置文件三段结构：

```yaml
chat_model:
  init_args:
    model: google/gemini-2.5-flash-lite-preview-09-2025
    model_provider: openai
    api_key: <YOUR_API_KEY>
    base_url: https://openrouter.ai/api/v1

image_generator:
  class_path: tools.ImageGeneratorNanobananaGoogleAPI
  init_args:
    api_key: <YOUR_API_KEY>

video_generator:
  class_path: tools.VideoGeneratorVeoGoogleAPI
  init_args:
    api_key: <YOUR_API_KEY>

working_dir: .working_dir/idea2video
```

`image_generator` 和 `video_generator` 的 `class_path` 就是上节列的适配器类名，换成云雾版只需改这一行。然后打开 `main_idea2video.py`，把 idea、user_requirement、style 三个变量改成你的内容——**注意它们是写在文件里的变量，不是命令行参数**，`python main_idea2video.py --idea "..."` 这样跑不会有任何效果。README 的示例是：

```python
idea = \
"""
If a cat and a dog are best friends, what would happen when they meet a new cat?
"""
user_requirement = \
"""
For children, do not exceed 3 scenes.
"""
style = "Cartoon"
```

`user_requirement` 不只是提示词，它是硬约束：示例里"不超过 3 个场景"会直接约束剧本生成的场景数量，第一次跑照抄这句，把账单压到最低。

### Web UI（要看板就用它）

v1.2.0 新增，与 TUI 共用同一套运行时、会话和配置文件，多了项目命名、文件上传、分镜预览、渲染进度这些可视化能力。需要 Node.js 18 或更新版本：

```bash
cd web
npm install
npm run dev
```

浏览器打开 `http://127.0.0.1:4173`。服务默认只监听本机回环地址，跑在远程服务器时用 SSH 端口转发：

```bash
ssh -N -L 4173:127.0.0.1:4173 <user>@<server>
```

端口冲突时用 `VIMAX_WEB_PORT=4174 npm run dev` 换端口。构建产物可以用 `./vimax web start` 启动正式服务，日常体验用 dev 模式即可。

## 四条工作流怎么选

ViMax 的功能按"你手里有什么输入"分成四条，README 宣传口径与代码实情有出入的，下面如实标注：

| 工作流 | 输入 | 现状 |
| ---- | ---- | ---- |
| Idea2Video | 一句话创意 + 要求 + 风格 | 完整可用，TUI/脚本/Web UI 三入口都支持 |
| Script2Video | 完整剧本（场景 + 对白） | 完整可用，三入口都支持 |
| Novel2Video | 长篇小说或节选 | 可用，但经 TUI/Web UI 的小说规划工具进入 |
| AutoCameo | 一张人物或宠物照片 | **宣传已就位，代码还没有** |

前三条的关系值得说一句：Idea2Video 不是与 Script2Video 并列的平行选项——它生成完故事和剧本后，逐场景调用 Script2Video 的管线完成渲染。选 Idea2Video 等于把前面两步也交给系统。

Novel2Video 的管线在代码里叫 `novel2movie_pipeline.py`，没有独立脚本入口。使用方式是走 TUI 或 Web UI 的 Agent 对话，把小说文本传给规划工具，系统产出小说压缩、事件抽取、场景切分这些中间工件，再进入逐场景渲染。网文改编场景用它，短的原创创意用 Idea2Video 更直接。

AutoCameo 需要单独提醒。README 把它列在四大特性里："把参考照片里的人物或宠物放进生成的故事，保持外观一致"，听起来像现成功能。但截至 2026 年 10 月 1 日的 main 分支，代码里搜不到任何 cameo 相关实现——没有对应管线，没有对应工具，仓库 5 月的 README 也确实把它标在 "Coming Soon" 里。现在的状态是宣传从路线图挪进了特性列表，实现仍未落地。想做数字人客串的读者，等 commit 出现再试。

## 第一次跑：官方猫狗示例

按官方 README 的路径走一遍最小任务，三种入口选 TUI 或脚本都行，下面以脚本直跑为例（最透明，每一步看得见）：

**第一步，装环境。** 上文的 clone + `uv sync`，确认系统是 Linux 或 Windows。

**第二步，填配置。** 编辑 `configs/idea2video.yaml`，三段 API Key 填好。第一次跑建议：对话模型用便宜的（Gemini Flash Lite 级别即可），图像和视频用你预算内最好的——画质上限在这里。

**第三步，写创意。** 把 `main_idea2video.py` 里的 idea 换成你的，`user_requirement` 保留"不超过 3 个场景"级别的约束，风格随意。

**第四步，跑。**

```bash
python main_idea2video.py
```

**第五步，看产物。** 全部中间产物落在 `working_dir` 指定的 `.working_dir/idea2video/` 下，每一步一个文件：

- `story.txt` — 扩写后的完整故事
- `characters.json` — 结构化的角色清单（含是否在画面中出现的标记）
- 角色三视图肖像与注册表 — 每个可见角色正、侧、背三张参考图
- `script.json` — 按场景组织的结构化剧本
- 逐场景子目录 — 分镜、镜头树、首末帧、镜头视频、转场
- `final_video.mp4` — moviepy 拼接的成片

这套"每步落盘"的设计是 ViMax 对使用者最实际的友好：API 超时、限流、手动 Ctrl-C 之后重新跑同一条命令，已存在的产物直接跳过，只补缺的环节。源码里的实现很朴素——每个环节开头检查产物文件是否存在，存在就打印一行 "skipping" 进下一步。中断重跑不重复烧钱，靠的就是它。

## 账单构成与省钱点

一次 Idea2Video 的调用量可以列成清单：

1. 故事扩写，1 次对话模型调用
2. 角色抽取，1 次
3. 每个可见角色 3 张肖像（正、侧、背），多角色并行
4. 剧本改写，1 次
5. 每个镜头 2 张首帧候选（默认 `num_candidates: 2`），由视觉模型择优
6. 每个镜头 1 段视频
7. 相邻镜头之间的转场视频
8. 最终拼接，本地 moviepy 完成，不产生 API 费用

三个省钱旋钮，对应上面清单：`num_candidates` 设为 1（第 5 项减半）、场景数压少（第 5-7 项的镜头总数随之下降）、对话模型选便宜的（第 1、2、4 项和择优调用都受益）。图像和视频模型不要省，它们直接决定成片质量。

## 常见问题

**macOS 能跑吗？** 官方不支持。PyTorch 依赖源只配了 Linux 和 Windows，README 环境栏也没列 macOS。云服务器或 Windows 机器是稳妥选择，远程跑 Web UI 配合 SSH 端口转发体验无损。

**跑一半断了，会重复扣费吗？** 不会，前提是 `working_dir` 没删。重跑同一条命令，已有产物全部跳过。手动删除某个中间文件，可以强制重做该环节——这也是"这个角色三视图不满意，只重生成它"的操作方式。

**成片里角色变脸怎么办？** 先查三视图质量：肖像本身就是敷衍的，后面全链都会漂。三视图正常但成片漂，换更强的图像或视频模型。ViMax 的参考图和镜头树机制能锁住的部分有限，超出底层模型能力的一致性问题，编排层救不回来。

**账单超预期怎么办？** 回看上节三个旋钮，重点检查 `user_requirement` 是否给了场景数上限——没写约束，系统会按剧本需要拆尽量多的场景和镜头，费用线性膨胀。

**成片有声音吗？** README 的卖点表宣传"音画绑定"（角色语音、音效与画面融合），但 `tools/` 目录至今没有音频适配器，账单清单里也没有任何语音调用。动手前把它当成待验证能力，用小案例实测，别按"自带配音"做计划。

**Roadmap 上的功能什么时候有？** 官方路线图当前挂着两项进行时：MiniMax H3 视频生成器、基于 Skill 的自定义工作流扩展。标注是进行中，没有时间表。前文说的 AutoCameo 已经从路线图消失（进了特性列表），但代码未见，这类"宣传先行"在追新功能时要留意。

## 适用边界

**适合现在就上手**：研究多智能体编排的开发者（逐环节落盘和适配器设计都可以直接参考）、手握剧本或小说想快速看动态分镜的作者、能接受秒级片段拼接质感的内容创作者。

**建议再等等**：要商业交付质量的内容团队——天花板压在底层视频模型上，人工修帧成本可能高于省下的制作费；预算敏感的个人玩家——先拿免费额度小成本试跑，确认效果再上量；macOS 本地用户——官方不支持，另找环境。

## 仓库信息

**仓库**：[HKUDS/ViMax](https://github.com/HKUDS/ViMax) | Stars: 12,542 | License: MIT | 语言：Python | 当前版本：v1.2.0（2026-07-20）| 读数截至 2026-10-01

**相关阅读**：[ViMax 架构解读：多智能体如何把一句话变成成片](../vimax-agentic-video-generation-architecture/)——源码级拆解 13 个智能体模块的分工、一次 Idea2Video 任务的完整流转与一致性机制。
