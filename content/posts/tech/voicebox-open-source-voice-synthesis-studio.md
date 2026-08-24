---
title: "Voicebox：把语音克隆、生成与听写都留在本地的开源语音工作室"
date: "2026-04-16T01:10:00+08:00"
slug: "voicebox-open-source-voice-synthesis-studio"
github_repo: "jamiepine/voicebox"
description: "Voicebox 是本地优先的开源 AI 语音工作室，用几秒音频零样本克隆音色，支持 7 个 TTS 引擎、23 种语言，内置全局听写、Stories 多轨编辑、REST 与 MCP API，作为 ElevenLabs 与 WisprFlow 的本地一体化替代方案运行在你自己的机器上。"
draft: false
categories: ["技术笔记"]
tags: ["语音合成", "TTS", "开源", "本地优先"]
---

# Voicebox：把语音克隆、生成与听写都留在本地的开源语音工作室

语音生意被两家云服务分成了两半：ElevenLabs 负责让机器说话，WisprFlow 负责听懂你说话。Voicebox 想做的，是把这两半合进一套开源应用，而且模型和数据都不离开你的机器。它定位成 ElevenLabs 和 WisprFlow 的本地替代，附带一个内置的本地大语言模型来润色语音和构造角色人格——这套东西不是某一家竞品的镜像，而是把「人说 → 字 → Agent 说 → 声」整条语音回路在单机上闭环的尝试。

先看它覆盖的能力边界，再进入细节：

| 语音回路的半边 | 云端头号玩家 | Voicebox 对应能力 |
|------|------|------|
| 输出（TTS 生成与克隆） | ElevenLabs | 7 个 TTS 引擎、零样本克隆、音效后处理 |
| 输入（听写与转录） | WisprFlow | 全局热键听写、Whisper 转录、Captures |
| 串联（Agent 语音、人格） | 各家 API | MCP `voicebox.speak`、本地 LLM 人格 |

后面 7 节依次讲：它到底是什么，7 个引擎怎么选，核心功能，技术架构，API 集成，部署方式，以及什么时候该用、什么时候不必用它。

## §1 定位：它真正在解决什么问题

云 TTS 与服务型听写各有各的约束，而这些约束在本地方案里可以同时消失。

**数据不出机器。** 声音采样、口述内容和生成音频都留在本机，不上传第三方。对声纹敏感的用户、有保密要求的商业旁白，这一点是硬需求，而不是卖点。

**成本随量不线性上升。** 云 API 的计价随生成字数增长。批量做有声书、长播客时，本地推理的成本基本恒定在电费和显存占用上。

**工具链可以闭环。** 云方案往往输入输出各用一家。Voicebox 把 TTS、STT、本地 LLM 和 Agent 语音输出放进同一处，Cursor、Claude Code 这类 MCP 客户端叫一次 `voicebox.speak` 就能用克隆声线说话。

**模型可选。** 不同的文本长度、语言、情感要求和显存预算对应不同引擎，每次都可在音色、成本和语言覆盖之间权衡。

## §2 项目概况与能力总览

| 属性 | 值 |
|------|------|
| **Stars** | 51,000+（持续增长） |
| **Forks** | 6,300+ |
| **技术栈** | TypeScript（前端）+ Python（后端）+ Rust（桌面壳） |
| **许可证** | MIT |
| **创建时间** | 2026-01-25 |
| **官网 / 仓库** | https://voicebox.sh / https://github.com/jamiepine/voicebox |

能力清单可以浓缩成四条主线，避免被罗列淹没：

1. **语音克隆与生成**——几秒参考音频零样本克隆；7 个引擎按需切换；每个档案还能挂一个自由描述的人格（persona）。
2. **无限时长与后处理**——长文本自动按句切分、跨 chunk 交叉淡化拼接；8 种由 Spotify pedalboard 驱动的声音特效。
3. **输入与编辑**——全局热键在任何应用里听写；Whisper 转录；Stories 多轨时间线做播客、对话和叙事。
4. **对外集成**——REST API 加内置 MCP server，任何 MCP 客户端都能让应用「开口」。

## §3 七大 TTS 引擎：按场景选，不是按名气选

Voicebox 目前接入 7 个引擎。选择的关键在语言、文本长度、表达需求和显存预算这几项，而不是谁更知名。

| 引擎 | 参数量 | 语言数 | 主要特点 |
|------|--------|--------|----------|
| **Qwen3-TTS** | 0.6B / 1.7B | 10 | 高质量多语言克隆，支持指令控制（如「慢点说」「耳语」） |
| **Qwen CustomVoice** | — | 10 | 9 个精修预设音色，用自然语言描述语速与情绪，无需参考音频 |
| **LuxTTS** | — | 英语 | 轻量（约 1 GB 显存），48 kHz 输出，CPU 可达 150 倍实时 |
| **Chatterbox Multilingual** | — | 23 | 语言覆盖最广（阿拉伯语、丹麦语、芬兰语、希腊语、希伯来语、印地语、马来语、挪威语、波兰语、斯瓦希里语、瑞典语、土耳其语等） |
| **Chatterbox Turbo** | 350M | 英语 | 速度快，理解 `[laugh]`、`[sigh]` 这类副语言标签 |
| **HumeAI TADA** | 1B / 3B | 10 | 语音-语言模型，可生成 700 秒以上连贯音频，文本-声学双对齐 |
| **Kokoro** | 82M | 8 | 50 个曲库预设音色，模型极小，CPU 推理快 |

### Qwen3-TTS：可指令的多语言克隆

阿里通义千问系列的语音模型，0.6B 偏快、1.7B 偏稳。它支持指令控制语速和风格，例如让模型「说得慢一点」「用耳语」：

```text
Speak slowly and whisper          # 控制语速与音量
Please emphasize the word IMPORTANT   # 强调某个词
```

支持英语、中文、西班牙语、法语、德语、韩语、俄语、葡萄牙语、意大利语、波兰语共 10 种语言。适合需要精确控制输出的产品演示和语音助手。

### Qwen CustomVoice：免参考音频的预设音色

同样是通义系，但它不需要上传参考片段。内置 9 个精修预设音色，语速和情绪通过自然语言描述控制。想要快速得到一个不那么「机器味」的默认声道，这是最省事的选择。

### LuxTTS：显存和 CPU 友好的英语专家

约 1 GB 显存即可跑，输出 48 kHz，CPU 上能到 150 倍实时。没有独显的开发机、或者在迭代测试阶段想快速出结果的场景，它最合适。

### Chatterbox Multilingual：语言覆盖最广

覆盖 23 种语言，含阿拉伯语、希伯来语、印地语、斯瓦希里语这类较冷门的语种。做全球化的本地化配音，以它为基底，用其他引擎兜底细节。

### Chatterbox Turbo：唯一理解情感标签的引擎

350M 参数，专为英语的情感表达优化。这里有一个容易踩的边界：**副语言标签只有 Chatterbox Turbo 会解释成笑声、叹息；Qwen3-TTS、LuxTTS、Chatterbox Multilingual 和 TADA 会把 `[laugh]` 这类标签按字面读出来。** 选中 Turbo 后，在文本输入框敲 `/` 会弹出标签插入器，可内联加入：

```
[laugh] [chuckle] [gasp] [cough] [sigh] [groan] [sniff] [shush] [clear throat]
```

例：
```text
Hello everyone [laugh] welcome to the show! [sigh] I'm so excited to be here today.
```

### HumeAI TADA：长文对齐

基于 Llama 3.2 的语音-语言模型，1B 侧重英语、3B 多语言。它由一个因果语言模型加流式匹配扩散解码器组成，能生成 700 秒以上的连贯音频，文本与声学的时间戳严格对齐。有声书、课程这类长文本，以及要求音素与时间精确对应的场景优先选它。

### Kokoro：最小最快的曲库

82M 参数，随包带 50 个曲库预设音色，CPU 就能飞快推理。对音质要求不苛求、想开箱即用得到一堆人声时，它最低成本。

### 引擎选择速查

| 需求 | 推荐引擎 |
|------|----------|
| 快速原型 / 无独显 | LuxTTS |
| 高质量英语配音 | Qwen3-TTS 1.7B |
| 免参考音频快速成声 | Qwen CustomVoice |
| 多语言覆盖 | Chatterbox Multilingual |
| 情感表达丰富 | Chatterbox Turbo |
| 超长文本、精确对齐 | HumeAI TADA |
| 曲库音色、轻量部署 | Kokoro |

## §4 核心功能

### 语音克隆与档案管理

从一个音频样本克隆音色是零样本的：上传 10-30 秒的 MP3、WAV 或 M4A，或在应用里直接录一段就能得到声音档案。想提升克隆质量，可以传多个内容不同的样本（朗读、对话、不同情绪），也让每个档案绑定默认的特效链。

档案与生成记录都存在本地 SQLite，理论上不上传任何服务器。档案支持导入导出，方便备份或分享。

### 语音人格：让声音「有人设」

给任何一个档案附加一段自由描述——这是谁、怎么说话、在意什么。设置后生成框会出现两个动作，由一个本地 Qwen3 大模型驱动，全程不出机器：

- **Compose（写一句）**：点一下，模型为这个人设现写一句台词进文本框，可编辑后合成，也可再点换一句。
- **Speak in character（入戏）**：打开开关后，输入文本会先经人设 LLM 改写成该声音的口吻，再送进 TTS。

Agent 端通过 MCP 传 `personality: true` 复用同一条改写管线，等于把 `voicebox.speak` 变成「文本 → 人设 LLM → TTS」的三段式通道。本地 LLM 可选 Qwen3 0.6B / 1.7B / 4B，与 TTS 共用同一套推理运行时。

### 无限时长生成

模型对单次输入长度有上限。Voicebox 的解法是先把文本按句边界切开，每段独立生成再交叉淡化拼接：

- 自动分 chunk，长度可在 100-5,000 字符间配置
- 相邻 chunk 的 crossfade 时长 0-200 ms 可调
- 单次最大 50,000 字符
- 分句时能识别缩写（C.O.D.、Mr.）、CJK 标点，并保持 `[标签]` 完整

### 8 种音效后处理

由 Spotify 的 `pedalboard` 库驱动，生成后可实时预览，也能存成可复用预设：

| 效果 | 说明 |
|------|------|
| Pitch Shift | 上下最多 12 个半音 |
| Reverb | 房间大小、阻尼、干湿混合可调 |
| Delay | 延迟、反馈与混合比可调的回声 |
| Chorus / Flanger | 金属感或丰润质感的调制延迟 |
| Compressor | 动态范围压缩 |
| Gain | 音量调整（-40 到 +40 dB） |
| High-Pass Filter | 切除低频 |
| Low-Pass Filter | 切除高频 |

内置 4 套预设（Robotic、Radio、Echo Chamber、Deep Voice），支持自定义，也允许把特效链设成档案默认。

### Stories 多轨时间线

做对话、播客、多角色叙事的编辑器：多轨拖拽排布、时间线上直接裁剪分割、播放头全轨同步、每个轨道片段可固定到某个版本。角色配音、旁白、背景音乐分层放置，是一次性拼出多角色对话的可视化方式。

### 录音、听写与 Captures

语音输入的半边是一个全局热键：在任何应用里按住键说话，松开后 macOS 上字幕会直接粘进当前聚焦的输入框（带目标感知粘贴，并原子化保存/还原剪贴板）。按住说话、点按切换两种触发方式都可重新绑定；压住 Push-to-Talk 时再拍一下空格，能把会话无缝升级成持续听写，中间不丢音频。

转录由 Whisper 驱动，按平台走 MLX（Apple Silicon）或 PyTorch（CUDA / ROCm / DirectML / CPU）。Base / Small / Medium / Large 是标准质量阶梯，Turbo 比 Large 快约 8 倍且质量损失较小。每次听写、录音和上传的文件都会落在 Captures 页：可以回放、换任意 Whisper 尺寸重新转写，或把原始转写经本地 LLM 用不同标志再清洗一遍（去掉语气词、去自我修正、保留术语）。点一个按钮，还能把某条 capture 直接转成某个克隆声线的语音样本。

### 生成版本与队列

每次生成都保留版本：

- **Original**：干净的原始输出，始终保留
- **Effects versions**：从任一源版本套不同特效链
- **Takes**：换随机种子重新生成出变体
- **Source tracking**：每个版本记录它的来源
- **Favorites**：给常用生成加星

生成全程非阻塞：提交后立刻可以写下一条。串行执行队列避免显存争抢，SSE 流式回报状态，失败可重试，崩溃遗留的陈旧任务在下次启动时自动恢复。

## §5 技术架构

### 三层结构

```
┌──────────────────────────────────────────────┐
│  桌面客户端（Tauri + React）                 │
│  生成面板 / 声音档案 / Stories 关键位置        │
├──────────────────────────────────────────────┤
│  状态层：Zustand + React Query               │
├──────────────────────────────────────────────┤
│  后端（FastAPI）                             │
│  routes（校验输入） → services（业务逻辑）    │
│  → backends（TTS/STT 推理） → utils（音频）  │
├──────────────────────────────────────────────┤
│  推理运行时：MLX / PyTorch（CUDA·ROCm·DirectML·CPU）│
└──────────────────────────────────────────────┘
```

用 Tauri 而不是 Electron 做桌面壳：安装包小、内存占用低、启动快，前端在系统 WebView 里跑；推理逻辑在 Python 的 FastAPI 里，利用成熟的数据科学生态。代价是跨了 Rust + Python + 前端三套工具链，首次构建配置项偏多——这是本地优先架构愿意付的成本。

请求路径很清晰：HTTP 请求进 `routes/` 做校验，落到 `services/` 处理业务逻辑，再由 `backends/` 里的 TTS/STT 引擎接管，最后 `utils/` 做音频处理。可观测的入口有 `app.py`（FastAPI 应用工厂）、`main.py`（uvicorn 入口）、`server.py`（Tauri sidecar 启动器与父进程看门狗）。

### 一次生成任务怎么过系统

把抽象结构串起来看：你在生成框输入一段话并选中档案 Morgan。

1. 后端把请求收进串行的任务队列，返回任务 ID，界面立刻可以输入下一条。
2. `services/generation.py` 若发现文本超长，按句边界切成 chunk。
3. `backends/` 里你选的引擎分 chunk 生成音频，chunk 间交叉淡化。
4. 若该档案挂了默认特效链，`utils/` 用 pedalboard 加上音效。
5. 结果落盘并在 SQLite 里写入一条生成记录，附带原始版本、来源与时间戳。
6. 页面经 SSE 收到完成事件，Stories 编辑器里可直接拖进时间线。

一次「说话」也能从键鼠端起头：按住全局热键说话 → Whisper 转写（可走 LLM 清洗）→ 粘回输入框 → 选引擎与档案生成语音；Agent 走同一条通道，用 MCP 调 `voicebox.speak` 把结果直接播给用户。

### GPU 支持矩阵

| 平台 | 后端 | 说明 |
|------|------|------|
| macOS Apple Silicon | MLX（Metal） | 借助神经网络单元约 4-5 倍加速 |
| Windows/Linux NVIDIA | PyTorch CUDA | `just setup` 自动识别并配置 |
| AMD GPU | PyTorch ROCm | Windows/Linux 均支持 |
| 通用 Windows/其余 GPU | DirectML | 无专用后端时兜底 |
| 任意平台 | CPU | 通用支持，速度较慢 |

## §6 REST API 与 MCP 集成

Voicebox 是 API-first 的。后端在本机跑起来后默认工作流的地址是 `http://127.0.0.1:17493`，完整字段以 `/docs`（OpenAPI）为准。

**生成语音：**

```bash
curl -X POST http://127.0.0.1:17493/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test of the Voicebox API.",
    "voice": "Morgan"
  }'
```

具体请求/响应字段因引擎而异，调试时打开 `http://127.0.0.1:17493/docs` 查看交互式 schema，比套用任何固定模板都可靠。

**让 Agent 说话：**

MCP 客户端（Claude Code、Cursor、Cline、Windsurf、VS Code）装好协议后，一条工具调用即可：

```ts
await voicebox.speak({
  text: "Deploy complete.",
  profile: "Morgan",
});
```

非 MCP 的一方（脚本、自制 harness）通过 `POST /speak` 拿到同样能力。每个客户端还能在 Settings → MCP 里绑定固定的声线（比如 Claude Code 用 Morgan、Cursor 用 Scarlett），靠提示浮层和 `last_seen_at` 判断声音到底从哪个 Agent 出来，避免静默后台发声。转录走 `/transcribe`，健康检查走 `/health`。

## §7 部署与安装

| 平台 | 安装方式 |
|------|----------|
| macOS Apple Silicon / Intel | 官方 DMG，Apple Silicon 走 MLX |
| Windows | 官方 MSI / Setup，CUDA 或 DirectML |
| Linux | 暂无预编译包，源码编译（见 voicebox.sh/linux-install） |
| Docker | 仓库内 `docker compose up` |

开发者环境在官方推荐 `just` 工作流下最省事：

```bash
git clone https://github.com/jamiepine/voicebox.git
cd voicebox
just setup   # Python venv + JS 依赖 + 开发 sidecar，自动识别平台后端
just dev     # 后端 + Tauri 桌面应用
```

常用命令：`just dev-backend` 只起后端、`just build` 构建、`just check` 做静态检查、`just docs` 打开 `http://127.0.0.1:17493/docs`、`just db-reset` 重置数据库。

## §8 扩展：接入新 TTS 引擎

多引擎架构让接新模型成为标准动作，官方还提供了让 AI 编码助手代劳的 agent skill。手工接入的核心三步：

**后端实现：**

```python
# backend/backends/my_engine.py
from .base import TTSEngine

class MyEngine(TTSEngine):
    name = "my-tts"
    supported_languages = ["en", "zh"]

    async def generate(self, text: str, voice_profile: str, **kwargs) -> bytes:
        """生成音频，返回 WAV 字节"""
        ...

    async def clone_voice(self, audio_samples: list[bytes]) -> str:
        """克隆声音，返回档案 ID"""
        ...
```

**注册到引擎字典：**

```python
# backend/backends/__init__.py
from .my_engine import MyEngine

ENGINES = {"my-tts": MyEngine(), ...}
```

**前端接入选择器：** 在引擎下拉里加一项，并把 `supported_languages`、显存占用等元数据补齐。之后把「为 Voicebox 接入 XTTS v2」这类需求交给 agent skill，它会自己研究依赖、写后端协议、连前端并配置打包。

## §9 常见问题

**Q1：Voicebox 和 ElevenLabs 比效果如何？**
定位不同。Voicebox 换的是自由与隐私：完全免费、本地运行、开源可控。音质在多数场景已经接近商业方案，但想要超越性高质量克隆时，云方案在极窄的需求下仍有优势。先跑通了自己的数据链路，再判断值不值当。

**Q2：需要什么硬件？**
最低：能跑 Python 的机器就能用 CPU 推理。推荐：macOS 用 Apple Silicon（MLX 加速），Windows 用 NVIDIA GPU（4 GB+ 显存，CUDA）。16 GB+ 内存、主频高一点的 CPU 体验最好。

**Q3：支持中文语音克隆吗？**
支持。Qwen3-TTS 与 Chatterbox Multilingual 都覆盖中文；LuxTTS 和 Chatterbox Turbo 仅英语。

**Q4：长文本怎么处理？**
自动按句切 chunk、chunk 间交叉淡化拼接，单次上限 50,000 字符。跨 chunk 的参数在设置里可调。

**Q5：可以商用吗？**
Voicebox 本体是 MIT，可商用。但每套 TTS 引擎各有自己的模型许可证，接新引擎或换模型前要分别核对；克隆他人声音涉及授权与法律问题，只对自己的声音或已获授权的声音做克隆。

**Q6：怎么在服务器上跑？**
两种方式：`docker compose up` 跑完整应用；或只用后端起一个纯 API 服务（不带 GUI），暴露 `/generate`、`/speak` 给下游集成。注意远程访问时后端默认只绑 `127.0.0.1`，需要显式绑 `0.0.0.0`。

## §10 采用建议与适用边界

Voicebox 不是所有人都该立刻迁移。判断标准看两件事：一是你的声纹数据能否出机器，二是你会不会长期做语音创作。

- **现在就值得用的**：隐私敏感的内容团队、长期做播客/有声书/H5 配音的创作者、想把固定声线交给 Cursor/Claude Code 的开发者和 Agent 用户。本地推理的回本点在于高频批量生成，量越大越划算。
- **可以再等等的**：只为偶尔一两次合成、且能接受云 MSI 账单的个人用户；对某个云模型「忠于原厂音色」有硬性依赖、不容许音质偏差的商用项目。
- **动手顺序**：先装桌面端跑通一次克隆与生成，确认音质过线；再按需试不同的引擎和音效；稳定后把 `POST /speak` 或 MCP 接进自己的应用。没有现成需求的，不必为「接一个框架」而接。

一句话收束：这东西不是让你换一家 TTS，而是让你把语音输入、生成和 Agent 语音都搬回自己的机器，把语音的支配权留在本地。

## 相关资源

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/jamiepine/voicebox |
| 官网 | https://voicebox.sh |
| 文档 | https://docs.voicebox.sh |
| 安装（含 Linux 源码） | https://voicebox.sh/linux-install |
| API 文档 | http://127.0.0.1:17493/docs（本地启动后） |