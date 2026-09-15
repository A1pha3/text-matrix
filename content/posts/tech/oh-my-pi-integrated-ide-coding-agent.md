---
title: "oh-my-pi：把 IDE 接进 Agent 循环的终端 Coding Agent"
date: "2026-05-20T20:00:00+08:00"
lastmod: 2026-09-15T00:00:00+08:00
slug: "oh-my-pi-integrated-ide-coding-agent"
github_repo: "can1357/oh-my-pi"
source_key: "gh:can1357/oh-my-pi"
description: "oh-my-pi（omp）是一个用 TypeScript/Rust 编写的终端 AI Coding Agent，把 LSP、DAP 调试器、进程内 shell 和搜索直接接进 Agent 循环：hashline 内容哈希编辑、60+ 模型服务商接入、子 Agent 并行与会话记忆。Fork 自 Mario Zechner 的 Pi，约 8 万行 Rust 核心把搜索、shell、AST 全部做进进程内。本文梳理其架构主线、benchmark 数字的正确读法和采用建议。"
draft: false
categories: ["技术笔记"]
tags: ["AI 编程", "Terminal", "LSP", "TypeScript", "Rust"]
---

# oh-my-pi：把 IDE 接进 Agent 循环的终端 Coding Agent

## 它解决的是 harness 问题，不是模型问题

同一个模型，换一个 agent 外壳，编辑成功率可能相差十倍——oh-my-pi（下称 omp）的作者把这称为 harness 问题：瓶颈往往不在模型，而在模型之外的那层执行环境。多数 coding agent 的编辑工具靠行号或旧文本做锚点，模型一旦找错位置就进入"改错—重试—再改错"的循环；调试靠在代码里插 print；搜索要 fork 一个 grep 子进程。这些损耗全部发生在模型之外。

omp 的做法是把这层执行环境直接重写：LSP、调试器、shell、文件搜索、AST 重写全部做成 agent 的内置工具，其中搜索、shell、AST 等热路径用约 8 万行 Rust 实现，运行在进程内，没有 fork/exec 开销。它 fork 自 Mario Zechner 的开源项目 [Pi](https://github.com/badlogic/pi-mono)，由 Can Bölük（GitHub 用户 can1357）重写为 coding-first 形态，MIT 协议，版权归属作者与 Stencil Labs, Inc.。

衡量这套重写是否有效，最直接的证据是编辑基准：Grok Code Fast 1 的编辑一次通过率从 6.7% 提升到 68.3%，换的只是编辑格式，模型权重没动。下文的 benchmark 一节会解释这组数字该怎么读。

## 项目速览

| 项 | 数据（截至 2026-09-15） |
|------|------|
| GitHub Stars | 31,135（仓库 2025 年 12 月 31 日创建） |
| 语言构成 | TypeScript（agent 层）+ Rust（原生核心，约 8 万行，另有约 8 万行 vendored 代码） |
| 运行时 | Bun ≥ 1.3.14（推荐）；提供 Node SDK |
| 平台 | macOS · Linux · Windows（同一二进制，无 WSL 桥接） |
| 模型接入 | 60+ providers、上千模型、9 个角色槽位 |
| 内置能力 | 31 个内置工具 · 14 个 LSP 操作 · 28 个 DAP 调试操作 |
| 开源协议 | MIT |
| 官网 | [omp.sh](https://omp.sh) |
| npm 包 | [@oh-my-pi/pi-coding-agent](https://www.npmjs.com/package/@oh-my-pi/pi-coding-agent)（版本已推进到 18.x） |

两个值得注意的项目状态：更新非常频繁（2026 年 9 月中旬仍在活跃推送），生产环境建议锁定版本；贡献治理上，PR 目前处于向所有人开放的试验期——此前的 vouch（老成员担保）要求暂时取消，官方声明后续可能恢复。

## 系统地图：一个引擎，四种入口

所有能力都挂在同一个会话引擎上，外面套四种包装：

| 入口 | 命令 | 用途 |
|------|------|------|
| 交互式 TUI | `omp` | 默认入口，工具调用渲染成卡片，编辑先预览后落盘 |
| 一次性执行 | `omp -p "prompt"` | 回答单个 prompt 后退出，适合脚本和 CI |
| Node SDK | `@oh-my-pi/pi-coding-agent` | 把会话嵌进自己的 Node/TypeScript 进程 |
| RPC / ACP | `omp --mode rpc` / `omp acp` | 通过 stdio 交给别的程序驱动 |

SDK 暴露 `ModelRegistry`、`SessionManager`、`createAgentSession` 等接口，会话以类型化事件对外广播：

```ts
import {
  ModelRegistry,
  SessionManager,
  createAgentSession,
  discoverAuthStorage,
} from "@oh-my-pi/pi-coding-agent";

const auth = await discoverAuthStorage();
const models = new ModelRegistry(auth);
await models.refresh();

const { session } = await createAgentSession({
  sessionManager: SessionManager.inMemory(),
  authStorage: auth,
  modelRegistry: models,
});
await session.prompt("list .ts files");
```

RPC 模式面向非 Node 环境，NDJSON 命令进出：

```text
$ omp --mode rpc --no-session
> {"id":"r1","type":"prompt","message":"list .ts files"}
< {"id":"r1","type":"response", ...}
```

ACP（Agent Client Protocol，Zed 主导的 JSON-RPC 协议）让 omp 跑在编辑器里：读你正在看的 buffer，走编辑器的 save 路径写文件，在编辑器终端里起 shell。`bash` 路由到 `terminal/create`，`read` 路由到 `fs/read_text_file`，破坏性操作统一过 `session/request_permission` 权限门。没有桥接层，也没有需要另外维护的同步副本。

## 主线一：编辑与代码智能

omp 内部其实有几条相对独立的主线。第一条围绕"改代码"这件事：编辑格式、语言服务、结构化重写、调试器。

### hashline：用内容哈希做锚点

传统 diff 编辑靠行号或原文匹配定位，模型要逐字复述要改的行，写错一个空白字符就匹配失败。hashline 让模型只指向内容哈希锚点，不再复述行内容——空白对齐问题和"字符串找不到"的循环从根上消失。改到过期的文件时锚点会失配，补丁在污染文件之前就被拒绝。

另一处收益直接反映在账单上：Grok 4 Fast 做同样的工作，输出 token 少 61%——坏 diff 触发的重试循环没有了。

### LSP 写进每一次编辑

omp 的重命名走 `workspace/willRenameFiles`，所以 barrel 文件的重导出、别名导入都会在文件移动前更新。agent 调的就是 IDE 的语言服务，14 个 LSP 操作覆盖诊断、跳转、符号查找、代码动作。效果可以概括为一句话：IDE 知道什么，agent 就知道什么。

### ast_edit：先预览，后落盘

基于 ast-grep 的结构化重写，覆盖 50+ 种 tree-sitter 语法。`ast_edit` 先返回一张 (proposed) 卡片和替换计数，改动处于暂存态；agent 往 `xd://resolve` 写一行理由后，TUI 生成 Accept 卡片，替换原子化落盘——要么全部生效，要么不动。

### DAP：真的调试器，真的断点

omp 通过 DAP（Debug Adapter Protocol）驱动真实调试器，共 28 个调试操作：

- **lldb**：attach 到 C/C++/Rust 原生二进制，单步到出错指针、读栈帧
- **dlv**：attach 到 Go 服务，遍历 goroutine 栈
- **debugpy**：暂停 Python 进程、检查变量、求值表达式

多数 agent 还停留在 print 调试，这里 agent 可以直接对运行中的进程下断点。

### 16 个内部 scheme：GitHub 也是文件系统

`read`、`grep`、`glob` 这些文件工具对 16 个内部 scheme 透明解析：`pr://1428` 返回的内容和 `read src/foo.ts` 同构，`grep` 能像遍历目录一样遍历一个 diff，`agent://<id>/findings.0.path` 能按路径直接取子 Agent 输出里的字段。常用的还有 `issue://`、`skill://`、`rule://`、`ssh://`、`conflict://N`。

## 主线二：进程内执行层

第二条主线是"工具怎么跑"。其他 agent 大多 shell out 到 `rg`、`grep`、`find`、`bash`——很多机器上这些二进制根本不存在，存在的每次调用也要付一次 fork-exec 往返。omp 把真实实现链接进了进程。

约 8 万行 Rust 分布在六个 crate，挂在一个平台标注的 N-API 插件上：

| Crate | 职责 | 约行数 |
|------|------|------:|
| pi-shell | 内嵌 bash 引擎 · 持久会话 · 进程内 coreutils 分发 | 38,000 |
| pi-natives | N-API 接口层：grep、桌面控制、文本处理、PTY、剪贴板等 | 25,000 |
| pi-walker | 并行文件遍历 + 扫描缓存，grep/glob/workspace/shell 共享 | 5,200 |
| pi-iso | 工作区隔离：APFS clone、btrfs/zfs reflink、overlayfs | 3,300 |
| pi-ast | tree-sitter + ast-grep 匹配与结构化摘要 | 2,900 |
| pi-voice | 音频采集播放 · Opus · WebRTC | 1,000 |

shell 语义来自 vendored 的 brush bash fork；coreutils、findutils、sed、jq、ripgrep 后端的 grep、fd、diff 等工具被移植进 builtins crate，随主程序一起编译。`bash` 工具本身提供 46 个进程内 coreutils、可选 PTY 和后台任务调度，会话跨调用存活。二进制覆盖 linux/darwin/win32 各 x64/arm64 六个平台目标，x64 附带 AVX2 与基线两个构建——Windows 上直接跑，不需要 WSL。

`eval` 工具提供持久的 Python 和 JavaScript（Bun）执行单元格，两者共享 prelude，并且能通过 loopback 桥回调 agent 自己的工具：在 Python 里用 `read` 加载 CSV，到 JavaScript 里画图，全程不离开单元格。

桌面与 Web 能力也在这条主线上：`browser` 驱动 Chromium 或 Electron（Puppeteer 标签页，可接管你已打开的 Chrome），stealth 默认开启；`computer` 枚举窗口、截屏、发原生输入、走系统无障碍树；`web_search` 一条查询串起 23 个搜索后端，按站点定制 extractor，GitHub、arXiv、Stack Overflow、npm/PyPI 等注册表页面转成保留锚点的结构化 markdown，另有 NVD、OSV、CISA KEV 三个漏洞数据库直查。注意 `github`、`security_scan`、`generate_image`、`tts` 等工具默认关闭，需在配置里显式开启。

## 主线三：模型接入与路由

第三条主线决定"哪个模型干哪件事"。60+ providers 分三类：直连 API（Anthropic、OpenAI、Gemini、xAI、DeepSeek、Bedrock、Azure、OpenRouter 等）、订阅式 coding plan（Cursor、GitHub Copilot、Kimi Code、GLM/Z.AI、MiniMax、阿里、Qwen、小米 MiMo 等）、本地推理（Ollama、LM Studio、llama.cpp、vLLM、LiteLLM）。

路由围绕 9 个角色槽位组织：`default` 日常、`smol` 便宜的子 agent 扇出、`slow` 深度推理、`plan` 规划模式、`commit` 写变更日志，其余 `vision`、`task`、`advisor`、`tiny` 各司其名。会话里 `/model` 随时切换，`Ctrl+P` 在当前角色的备选模型间循环。

让这套路由真正可用的四个配置项：

- **自定义 provider**——任何支持 `openai-completions`、`anthropic-messages`、`bedrock-converse-stream`、`google-generative-ai` 等协议的服务端都能在 `~/.omp/agent/models.yml` 里声明
- **fallback 链**——`retry.fallbackChains` 按角色或模型配置，主模型 429 或配额耗尽时同轮切换到下一个，冷却后自动恢复
- **按路径定模型**——`enabledModels`/`disabledProviders` 可限定 `path:` 前缀，单个仓库用不同模型集，不动全局配置
- **凭据轮转**——同一 provider 堆多个 API key，带会话亲和与按凭据退避

自定义 provider 的最小配置（README 原例）：

```yaml
providers:
  spark:
    baseUrl: http://192.168.10.223:8000/v1
    api: openai-completions
    apiKey: dummy
    models:
      - id: minimax-m3
        name: MiniMax M3
        contextWindow: 100000
        maxTokens: 32000
```

## 主线四：多 agent、规则与记忆

第四条主线解决"一个上下文装不下、一个模型看不全、一条会话记不住"。

**子 agent**。`task` 把工作扇出到隔离的 worker（可选独立 worktree，靠 pi-iso 的文件系统克隆实现），每个 worker 有自己的工具面，最终产出是经 schema 校验的对象，父 agent 直接读字段，不解析散文，兄弟之间也不会互相改脏文件。`Alt+A` 打开 Agent Hub，能看每个子 agent 的实时转录、发引导消息、复活或终止卡住的 worker。

**Advisor**。把第二个模型配到 advisor 角色，它会读主 agent 的每一步动作，在旁注里给出提醒、疑虑或硬阻断。它有自己的上下文和模型，能抓住执行者赶进度时漏掉的问题。

**TTSR（时间旅行式流规则）**。规则文件平时静默，不占上下文；模型的输出流命中正则时，流被中途掐断，规则以 system reminder 注入，从同一点重试。注入在 context 压缩后依然存活，所以修复是持久的。官方示例：模型准备写 `Box::leak` 时规则触发，模型改用 `Arc<str>` 并向用户确认。

**记忆**。`retain` 写入事实、`learn` 沉淀可复用经验（可提升为受管 skill）、`recall` 检索、`reflect` 综合回答，每次会话压缩成心智模型供下次首回合加载。引擎经 `memory.backend` 选择：本地 SQLite（pi-mnemopi）、Hindsight 或 Mnemopi，默认按项目隔离——这个仓库学到的事留在这个仓库。

**协作**。`/collab` 把当前会话挂上中继，返回链接和二维码；队友用 `omp join` 从另一个终端加入，或在浏览器里打开。`/collab view` 给只读链接。帧在客户端加密，中继看不到你的密钥。

## 一次真实调试任务的完整路径

把四条主线串起来，看一个 C 二进制段错误从发现到提交的全过程：

1. agent 通过 `bash`（进程内 shell）编译并运行二进制，捕获到 segfault
2. 调用 `debug` 工具 attach lldb，下断点、单步到坏指针、读栈帧——DAP 会话的适配器、状态、指令指针都渲染在 TUI 卡片里
3. 定位到问题函数后，用 `edit` 的 hashline 补丁修掉，锚点哈希保证落在正确的位置
4. 需要重命名函数时，LSP rename 经 `workspace/willRenameFiles` 更新所有引用，包括 barrel 文件里的重导出
5. 收尾跑 `omp commit`：它经 `git_overview`/`git_file_diff`/`git_hunk` 读工作树，把无关变更按依赖顺序拆成原子提交，出现循环依赖则在写入前拒绝，源码文件排在测试、文档、配置之前，锁文件不参与分析

每一步用到的都是内置工具，没有一步需要 agent"灵机一动"拼外部命令。

## 编辑基准：这组数字该怎么读

官方给出的模型对比数据：

| 模型 | 指标 | 说明 |
|------|------|------|
| Grok Code Fast 1 | 6.7% → 68.3% | 编辑格式修好后一次通过率提升十倍 |
| Gemini 3 Flash | +5 个百分点 | 相对 str_replace 格式，超过 Google 自己给出的最佳格式方案 |
| Grok 4 Fast | 输出 token −61% | 坏 diff 重试循环消失后输出坍缩 |
| MiniMax | 2.1× | 同权重、同 prompt 下通过率翻倍 |

读这组数字前先回答三个问题。

**测的是什么**：同一批编辑任务在不同 edit 工具格式下的一次通过率和输出 token，测的对象是 harness 而非模型。仓库里的 `typescript-edit-benchmark` 包表明基准建立在 TypeScript 源码变异之上，完整方法论见官方博客 [The Harness Problem](https://stencil.so/blog/the-harness-problem/)。

**数字反映系统的哪部分**：变化集中在 `edit` 工具的锚点设计与重试策略上。6.7% → 68.3% 这种量级的变化来自格式而非模型——对照组里模型权重没有动。

**不能推出什么**：不能推出这些模型整体编码能力的排序——通过率只针对"按 hashline 格式输出编辑"这一件事；也不能把 −61% 的输出 token 直接换算成账单节省，输入侧 token 和会话长度不在统计里。另外这些数字由项目方自己测得，第三方复测结果尚未见到。

## 规则继承与扩展

第一次运行时，omp 直接读取磁盘上已有的规则、skills 和 MCP 配置，来源包括 `.claude`、`.cursor`、`.windsurf`、`.gemini`、`.codex`、`.cline`、`.github/copilot`、`.vscode`——共 8 种格式以原生形态支持（Cursor MDC、Cline `.clinerules`、Codex `AGENTS.md`、Copilot `applyTo` 等），没有迁移脚本，也没有"支持子集"的脚注。团队上季度写的配置今晚就能用。

扩展侧，一个 extension 就是一个 TypeScript 模块，用的是与内置功能相同的工具 API、斜杠命令注册表、快捷键表和 TUI 原语。让 omp 自己写一块缺失的功能，然后 `/reload-plugins` 生效；可以留在本地、放进 marketplace 或发到 npm。

几个改变会话行为的控制入口：

- 提示词里的 `ultrathink`（深度思考）、`orchestrate`（并行子 agent 编排）、`workflowz`（确定性多 agent 工作流）——只在你输入的正文里触发，代码块和路径里不生效
- `/vibe` 进入导演模式：以只读工具集驱动持久的 `fast`/`good` worker 会话
- `/fresh` 重置 provider 流状态（陈旧的 prompt 缓存、卡死的流），不动本地转录
- `/review` 拉起评审子 agent，并行扫分支、单提交或未暂存的工作，每个问题标 P0–P3 和置信度，最后给出能否合入的明确结论

## 快速开始

macOS / Linux：

```bash
curl -fsSL https://omp.sh/install | sh
```

Homebrew：

```bash
brew install can1357/tap/omp
```

Bun（推荐）：

```bash
bun install -g @oh-my-pi/pi-coding-agent
```

Nix（免安装试用）：

```bash
nix run github:can1357/oh-my-pi
```

Windows（PowerShell）：

```powershell
irm https://omp.sh/install.ps1 | iex
```

版本锁定可用 `mise use -g github:can1357/oh-my-pi`。两个环境注意点：Alpine/musl 的预编译二进制动态链接 `libstdc++`/`libgcc`，需先 `apk add libstdc++ libgcc`；shell 补全由 omp 按实际命令元数据生成，bash/zsh/fish 分别执行 `omp completions <shell>` 挂载即可，模型名和 `--resume` 会话名都能补全。

日常高频命令集中在会话层：`/model` 切模型、`/login` 接入订阅、`/collab` 发起协作、`/review` 评审、`/debug` 打开调试与性能面板。

## 适用边界与采用建议

适合现在就上的情况：

- **重度终端工作流**：omp 的全部能力以 TUI 为第一入口，编辑器只经 ACP 接入
- **需要真实调试**：要在 agent 循环里 attach 调试器，而不是靠 print 猜
- **多模型策略**：想在同一个会话里按角色混用多家模型、本地推理和订阅 plan
- **Windows 原生环境**：同一二进制直接跑，不依赖 WSL
- **已有规则资产**：Cursor/Cline/Codex/Copilot 规则零迁移继承

可以先观望的情况：项目 2025 年 12 月底才创建，版本号已推进到 18.x，接口和配置面仍在快速变动，追求长期稳定 API 的团队需要自己锁版本、跟 changelog；依赖厂商商业支持的团队目前没有该选项。治理上 vouch 机制可能回归，贡献流程存在不确定性。

建议的采用顺序：先用 Homebrew 或安装脚本在个人项目里跑通一次编辑—调试—`omp commit` 闭环，感受 hashline 和 DAP 与现有工具的差异；然后把现有规则目录交给它的 discovery 机制继承，对比规则行为是否一致；最后才考虑在团队仓库里启用子 agent 隔离、记忆后端和按路径的模型路由这类需要配置投入的能力。

## 结语

omp 的判断很明确：agent 竞争的下一层不在模型，而在 harness——编辑格式、语言服务、调试器、进程内执行、模型路由，每一层都值得重写。它把"IDE 知道什么，agent 就知道什么"从口号做成了 14 个 LSP 操作和 28 个 DAP 操作；把 8 万行 Rust 塞进一个二进制，换掉 fork-exec 的老路。对在终端里写代码的人来说，它是目前把这条路线走得最完整的一个实现。

参考链接：

- GitHub：[can1357/oh-my-pi](https://github.com/can1357/oh-my-pi)
- 官网与文档：[omp.sh](https://omp.sh)（[工具参考](https://omp.sh/docs/tools) · [provider 路由](https://omp.sh/docs/providers) · [SDK](https://omp.sh/docs/sdk)）
- 设计博文：[The Harness Problem](https://stencil.so/blog/the-harness-problem/)
- Discord：[discord.gg/4NMW9cdXZa](https://discord.gg/4NMW9cdXZa)
- 上游项目：[badlogic/pi-mono](https://github.com/badlogic/pi-mono)（Mario Zechner 的 Pi）
