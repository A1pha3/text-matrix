---
title: "moeru-ai/airi：可自托管的 AI 虚拟伙伴项目"
date: "2026-07-14T03:14:51+08:00"
slug: "moeru-ai-airi-virtual-companion-ai"
description: "moeru-ai/airi 是受 Neuro-sama 启发的开源 AI VTuber 项目，支持 Live2D/VRM 渲染、ChatGPT/Claude 等多模型接入、可在浏览器/桌面/移动端运行，并自带 Minecraft/Factorio 等游戏 Agent 子项目。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "Live2D", "VRM", "VTuber", "WebGPU"]
---

## 核心判断

`moeru-ai/airi`（下文称 **AIRI**）是一份「**复刻 Neuro-sama**」的开源尝试。它把 AI 虚拟主播（VTuber）拆成「**渲染 + AI 对话 + 游戏 / 外部执行**」三条并行链路，在同一个调度框架（`@proj-airi/core`）内汇合，进而提供普通「AI 角色壳子」通常缺失的「实时感知 + 外部动作」能力。它特别值得关注的点是「**从第一天起就用 Web 技术栈打底**」：WebGPU、WebAudio、Web Workers、WebAssembly、WebSocket 全部内置；桌面端则用 HuggingFace 的 `candle` 在不需要复杂依赖管理的前提下接 NVIDIA CUDA 与 Apple Metal。

下文先回答「它是什么 / 在哪一层」、再拆技术栈与三条主链路，最后讲运行边界与风险。

## 项目定位

仓库主标语是 **「Re-creating Neuro-sama, a soul container of AI waifu / virtual characters to bring them into our world」**。换句话说，它不是单纯的聊天壳子，而是：

1. **一个 Live2D / VRM 虚拟角色渲染运行时**
2. **一个 LLM 对话前端**
3. **一个可被配置去「玩游戏 / 看屏幕 / 接入 Discord / Telegram」的 Agent 宿主**

主项目 README 把 AIRI 描述为「heavily inspired by Neuro-sama」。Neuro-sama 是当下最强的 AI 虚拟主播，能边玩游戏边和观众互动，但她是闭源的，直播结束就下线。AIRI 想做的就是把这种体验以开源 + 可自托管的方式带到本地。

## 能力地图：从 README 的「Current Progress & Roadmap」提取

按「Brain / Ears / Mouth / Body」四块组织：

| 维度 | 已完成能力 | 仍在 WIP |
|------|------------|----------|
| **Brain（决策）** | 玩 Minecraft、玩 Factorio（WIP）、接入 Telegram、接入 Discord | Helldivers 2 协作、纯浏览器本地推理（WebGPU）、Memory Alaya |
| **Ears（输入）** | 浏览器音频输入、Discord 音频输入、客户端语音识别、说话人检测 | — |
| **Mouth（输出）** | ElevenLabs、Microsoft/Azure Speech、OpenAI 兼容 TTS、阿里云 Model Studio、本地 Kokoro TTS | — |
| **Body（身体）** | VRM 模型控制与动画（自动眨眼 / 注视 / 闲置眼动）、Live2D 模型控制与动画 | — |
| **Memory（记忆）** | 纯浏览器数据库（DuckDB WASM / `pglite`） | Memory Alaya（受佛教阿赖耶识概念启发的记忆系统） |

注意「Memory」一栏在 README 中是 Brain 的子项，但工程上独立度足够高，所以社区通常单列。从能力完成度看：**Body / Mouth / Ears 三块接近生产可用，Brain 的游戏 / 记忆模块仍在快速迭代**。

## 技术栈拆解

### 三条并行主链路

AIRI 的工程价值在「**把三种异构技术收敛到同一调度框架**」，这是它与普通 VTuber 项目的根本差异。

1. **渲染链路**
   - 入口：`Stage Web`（浏览器）/ `Stage Tamagotchi`（Electron 桌面）/ `Stage Pocket`（Capacitor 移动）
   - 模型格式：VRM、Live2D
   - 关键依赖：`@proj-airi/stage-ui`、`@proj-airi/ui`、`@proj-airi/ui-transitions`、`@proj-airi/ui-loading-screens`
   - 桌面端额外使用 HuggingFace `candle` 调用 NVIDIA CUDA / Apple Metal

2. **AI 链路**
   - LLM 入口：自家包 [`xsai`](https://github.com/moeru-ai/xsai)（类似 Vercel AI SDK 但更小），已支持 AIHubMix、OpenRouter、vLLM、SGLang、Ollama、OpenAI、Azure OpenAI、Anthropic Claude、DeepSeek、Qwen、Gemini、xAI、Groq、Mistral、Cloudflare Workers AI、Together.ai、Fireworks.ai、Novita、智谱、SiliconFlow、Stepfun、百川、MiniMax、Moonshot、ModelScope、Player2、腾讯云、小米 MiMo 等二十余家
   - ASR/TTS：自建包 [`unspeech`](https://github.com/moeru-ai/unspeech)（`/audio/transcriptions` 与 `/audio/speech` 的通用端点代理，类 LiteLLM 但聚焦语音）
   - 记忆：浏览器 DuckDB WASM / `pglite`，未来接 Memory Alaya

3. **游戏链路**
   - Minecraft：通过 `Mineflayer` 直连服务器
   - Factorio：通过 [`autorio`](https://github.com/moeru-ai/airi-factorio) + RCON 自动化 mod + RESTful 封装层 `factorio-rcon-api`
   - 两个子项目分别为 `moeru-ai/airi-factorio` 与 `proj-airi/game-playing-ai-dome-keeper`

三条链路通过 `@proj-airi/core` 统一调度：

```
UI → stage-ui → Stage → Core
Core → STT, ServerRuntime, Memory, Realtime Audio, Prompt Engineering
ServerRuntime → Factorio Agent / Minecraft Agent
xsai → Core / Agent（统一 LLM 入口）
unspeech → STT（统一 ASR/TTS 入口）
```

### Web 技术栈优先策略

AIRI 的一个特殊立场是「**Day-1 Web Native**」：

> Unlike the other AI driven VTuber open source projects, アイリ was built with support of many Web technologies such as WebGPU, WebAudio, Web Workers, WebAssembly, WebSocket etc. from the first day.

直接后果是：

- 浏览器版能跑（[airi.moeru.ai](https://airi.moeru.ai) 在线 demo）；
- PWA 支持移动端；
- 桌面版（Tauri / Electron-based Tamagotchi）通过 `candle` 走原生 GPU；
- 插件系统仍以 Web 技术为主，但允许通过 TCP / Discord 等「非 Web」方式扩展。

### 安装与运行

主项目用 pnpm monorepo，三种入口：

```sh
# Stage Web（浏览器版）
pnpm i && pnpm dev

# Stage Tamagotchi（桌面版）
pnpm dev:tamagotchi
# NixOS 用户额外需要
nix develop .#fhs

# Stage Pocket（移动版）
pnpm dev:pocket:ios --target <DEVICE_ID_OR_SIMULATOR_NAME>
```

社区也提供多种安装通道：

- Windows：`winget install MoeruAI.AIRI` 或 `scoop bucket add airi https://github.com/moeru-ai/airi && scoop install airi/airi`
- macOS：`brew install --cask airi`
- 直接下载：[Releases](https://github.com/moeru-ai/airi/releases) 提供 Windows `.exe`、macOS `.dmg`、Linux 安装包

**注意**：README 顶部用醒目 WARNING 强调：**项目没有官方发行的加密货币 / 代币**。社区如出现同名代币均与本项目无关。

## 任务流案例：让 AIRI 玩 Minecraft

按 README「Current Progress & Roadmap」与 `moeru-ai/airi-factorio` 子项目 README 还原一条从「用户说话」到「游戏中执行」的链路：

1. **音频输入**：用户在浏览器 / 桌面客户端说话，浏览器麦克风采集音频流。
2. **ASR**：客户端或 Discord 端拾取音频，走 `unspeech` 代理到 STT（OpenAI Whisper / 自托管 Kokoro）。
3. **说话人检测（VAD）**：客户端侧区分人声 / 静音，避免空触发。
4. **LLM 决策**：识别后的文本送入 `xsai` 调用大模型（OpenAI、Claude、Qwen、Ollama 本地模型等任选），生成下一步动作或回复。
5. **记忆检索**：未来接 Memory Alaya 时，会先查 DuckDB WASM / `pglite` 中的长期记忆再拼 Prompt。
6. **动作分发**：
   - 走 TTS → 嘴型同步 → 渲染链路（VRM / Live2D 动画）
   - 走游戏 Agent → Minecraft 由 `Mineflayer` 发包、Factorio 由 `autorio` 调 RCON
7. **状态回流**：动作结果回写到记忆、Console 日志、Discord 频道等出口。

整条链路在 README 中呈现为「**可拆解的子系统组合**」，而不是「**一个巨型单体**」。这就是为什么读者能在 `Sub-projects Born from This Project` 一节里看到 `unspeech`、`hfup`、`xsai-transformers`、`webai-realtime-voice-chat`、`@proj-airi/drizzle-duckdb-wasm`、`@proj-airi/duckdb-wasm`、`autorio`、`tstl-plugin-reload-factorio-mod`、`velin`、`demodel`、`inventory`、`mcp-launcher` 等十几个独立仓库——它们都是 AIRI 链路上的可替换件。

## 适用人群

| 人群 | 这个项目的用法 |
|------|----------------|
| 想自托管 AI VTuber | 用 Stage Web / Tamagotchi / Pocket 三种入口任选 |
| 想搭实时语音 + LLM 应用 | 参考 `webai-realtime-voice-chat` 子项目（含 VAD + STT + LLM + TTS 完整示例） |
| 想做 AI 玩 Minecraft / Factorio | 直接基于 `Mineflayer` / `autorio` 接 AIRI 的调度层 |
| 想统一多家 LLM / TTS / STT API | 复用 `xsai`（LLM）与 `unspeech`（语音） |
| 想做本地化 AI 记忆 | 复用 `@proj-airi/duckdb-wasm` 与 `@proj-airi/drizzle-duckdb-wasm` |
| Live2D / VRM 模型作者 | 把模型喂给 Stage UI 即可驱动 |

## 运行边界与风险

下面这些边界是「**README 当前没说能保证**」或「**项目仍在 WIP**」的部分，读者在评估时要明确知道：

### 1. 项目阶段仍在「**早期 + 快速迭代**」

README 原话：

> We are still in the early stage of development where we are seeking out talented developers to join us and help us to make アイリ a reality.

这意味着：

- API 与目录结构可能随时变；
- 文档、Issue、PR 的响应节奏不如成熟框架稳定；
- 多数功能（Helldivers 2、Memory Alaya、纯浏览器本地推理）尚未交付。

### 2. 桌面端依赖较重

Stage Tamagotchi 在 NixOS 上需要 `nix develop .#fhs` 走 FHS shell，Electron 本身在非标准路径上需要额外配置。普通 macOS / Windows 用户用 Homebrew / winget / Scoop 安装通常没问题，但定制 Linux 发行版要预留排错时间。

### 3. 游戏 Agent 仅覆盖 Minecraft / Factorio

README 的 Brain 列表里：Minecraft ✅、Factorio ✅（PoC）、Kerbal Space Program（公告待发）、Helldivers 2（WIP）。如果你想让它玩其他游戏，需要自己写 Mineflayer 等价的桥接层。

### 4. 浏览器版 ≠ 桌面版

README 明确指出：

> The Web browser version is meant to give an insight into how much we can push and do inside browsers and webviews, we will never fully rely on this.

也就是说，浏览器 demo 是「**能力上限演示**」，真实稳定使用还是要走桌面 / 移动版本。

### 5. 第三方服务依赖

LLM / TTS / ASR 默认走云端 API（OpenAI、Anthropic、ElevenLabs、Azure 等），隐私敏感场景需要自行替换为本地模型（`xsai` 已支持 Ollama / vLLM）。WebGPU 纯浏览器推理目前在 WIP 状态。

### 6. 加密货币风险

README 顶部 WARNING 已强调「**没有官方代币**」。社区出现同名 token 时请保持警惕。

## 与同类项目对照

README 末尾「Similar Projects」里列了 9 个开源 + 3 个闭源同类项目。下表做最小对照（仅基于仓库自述）：

| 项目 | 仓库自述的强项 |
|------|----------------|
| `kimjammer/Neuro` | 7 天内复刻 Neuro-sama（README 原话「recreation of Neuro-Sama originally created in 7 days」），完成度高 |
| `SugarcaneDefender/z-waif` | 玩游戏、自主性、Prompt 工程 |
| `semperai/amica` | VRM + WebXR |
| `elizaOS/eliza` | Agent 与多系统集成示例 |
| `ardha27/AI-Waifu-Vtuber` | Twitch API 集成 |
| `InsanityLabs/AIVTuber` | UI / UX |
| `t41372/Open-LLM-VTuber` | Open LLM 路线 |
| `PeterH0323/Streamer-Sales` | 直播带货场景 |

AIRI 的相对位置是「**Web 技术栈优先 + 多游戏 Agent + 完整子项目矩阵**」，如果你最在意「**跨平台 + 自托管 + 多游戏 + 多模型**」，AIRI 是同类里覆盖最广的一份。

## 仓库与生态地址

- 主项目：<https://github.com/moeru-ai/airi>
- 在线 demo：<https://airi.moeru.ai>
- 文档站：<https://airi.moeru.ai/docs/en/>
- Discord：<https://discord.gg/TgQ3Cu2F7A>
- 子项目矩阵：`unspeech`、`hfup`、`xsai-transformers`、`@proj-airi/duckdb-wasm`、`@proj-airi/drizzle-duckdb-wasm`、`autorio`、`factorio-rcon-api`、`velin`、`demodel`、`mcp-launcher`、`inventory`、`@proj-airi/webai-realtime-voice-chat`、`moeru-ai/airi-factorio`、`proj-airi/game-playing-ai-dome-keeper`、`proj-airi/awesome-ai-vtuber`
- 相关组织：`@moeru-ai`、`@proj-airi`