---
title: "Claw Code: 由 AI Agent 维护的 Rust CLI Harness（真实评测与局限）"
date: "2026-04-30T20:00:00+08:00"
slug: "claw-code-rust-ai-agent-cli"
description: "Claw Code 是 ultraworkers 团队开源的 Rust 实现的 CLI agent harness，但项目明确自述为「博物馆展品」而非生产级工具。本文解析其架构、能力边界、与 Claude Code 的区别，以及自主维护模式带来的局限。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Rust", "CLI工具", "Claw Code", "自主维护项目"]
---

## 快速信息卡

| 属性 | 值 |
|------|-----|
| **GitHub Stars** | 194,265+ |
| **GitHub Forks** | 109,894+ |
| **主要语言** | Rust |
| **开源协议** | MIT |
| **维护方式** | 完全由 AI Agent 自主维护 |
| **项目定位** | 研究性 artifacts / 博物馆展品 |

> ⚠️ **重要提示**：本项目明确自述为"博物馆展品"，代码完全由 AI Agent 生成维护，无人工校验。不建议作为生产工具使用。

---

## 学习目标

读完本文后，你应该能够：

- 理解 Claw Code 的真实定位：它是研究性 artifacts，不是生产级 CLI
- 成功从源码构建 `claw` CLI，并理解为什么 `cargo install claw-code` 会失败
- 区分 Claw Code 与 Anthropic Claude Code（两者无关联）
- 针对你的场景判断 Claw Code 是否合适，或应该转向 LazyCodex / Gajae-Code
- 理解"完全由 Agent 维护"意味着什么（文档漂移、功能不稳定、无人工校验）

---

## 先说结论

Claw Code 是一个**真实但非生产级**的开源项目。核心事实：

1. **它是 Rust 实现的 `claw` CLI agent harness 的公开版本**，规范实现在 `rust/` 目录。
2. **项目自述是"博物馆展品"**：代码完全由 AI Agent 自主开发维护，无人工干预。这意味着文档可能过时、功能可能不稳定。
3. **不是 Anthropic Claude Code**：项目明确声明不主张对 Claude Code 源码的任何所有权，两者是独立项目。
4. **如果你想要生产级工具**：作者建议优先选 [LazyCodex](https://github.com/code-yeongyu/lazycodex) 或 [Gajae-Code](https://github.com/Yeachan-Heo/gajae-code)。
5. **支持多模型**：Anthropic API、OpenAI 兼容接口、本地 Ollama（2026-06 新增原生支持）。

---

## 目录

- [学习目标](#学习目标)
- [先说结论](#先说结论)
- [项目背景：为什么叫"博物馆展品"](#项目背景为什么叫博物馆展品)
- [为什么会有这个项目](#为什么会有这个项目)
- [快速开始：从源码构建](#快速开始从源码构建)
- [核心架构](#核心架构)
- [与 Anthropic Claude Code 的区别](#与-anthropic-claude-code-的区别)
- [能力边界：什么能做，什么不能](#能力边界什么能做什么不能)
- [常见问题](#常见问题)
- [自测题](#自测题)
- [练习](#练习)
- [进阶阅读路径](#进阶阅读路径)

---

## 项目背景：为什么叫"博物馆展品"

Claw Code 的 GitHub README 描述这个项目的方式跟常见的开源项目不太一样：

> 本仓库展示的是一个由智能体管理的博物馆展品。无人工干预，完全由智能体自主开发、维护。

这句话直接说明了几件事：

- **代码是 Agent 写的**：功能、文档、测试都可能由 AI 生成，不是人类手写之后交出去的。
- **没有人工校验**：你看到的文档可能跟实际代码对不上。
- **定位是研究性 artifacts**：它展示的是"claw CLI agent harness"的 Rust 实现，不是一个稳定的开发者工具。

如果你想要一个能日常用的 AI Agent CLI，这个项目可能不满足你的预期。作者自己在 README 里列了替代方案。

---

## 为什么会有这个项目

Claw Code 解决的是一个具体问题：怎么用 Rust 写一个 CLI harness，让 LLM 能调用工具、维持多轮会话、接入不同的模型 API。

一个能用的 AI Agent CLI 至少要处理这些事：

1. **多轮会话管理**：上下文怎么维护，历史存在哪、怎么恢复
2. **工具调用编排**：`ls`、`grep`、编译器输出怎么接进 LLM 的 function calling
3. **跨模型适配**：Anthropic / OpenAI / 本地 Ollama 的 API 差异怎么抹平
4. **部署形态**：纯 CLI、带 Daemon、还是容器化

Claw Code 的做法是：**Rust 写 CLI harness，`#[tool]` 宏注册工具，SQLite 持久化会话，多 Provider trait 抹平后端差异**。

设计本身没问题，但维护方式有问题：代码完全由 Agent 生成，没有人工校验，文档和代码可能不一致。

## 快速开始：从源码构建（弃用 `cargo install claw-code`）

> ⚠️ **不要执行 `cargo install claw-code`！** crates.io 上的 `claw-code` 是一个早已废弃的空壳包，只会打印 `"claw-code has been renamed to agent-code"`，不会安装真正的 claw 工具。

正确做法是从源码构建：

### 环境要求

- **Rust**（建议通过 [rustup.rs](https://rustup.rs/) 安装，需要 1.75+）
- **API Key**：支持 `ANTHROPIC_API_KEY`、`OPENAI_API_KEY`，或本地 Ollama（设置 `OLLAMA_HOST` 即可，无需 API Key）

### 构建步骤

```bash
# 1. 克隆仓库
git clone https://github.com/ultraworkers/claw-code
cd claw-code/rust

# 2. 构建整个 Rust workspace（Debug 模式，首次约 3-5 分钟）
cargo build --workspace

# 3. 设置 API Key（以 Anthropic 为例）
export ANTHROPIC_API_KEY="sk-ant-..."

# 4. 运行健康检查（首次使用必做，检查 API Key 和依赖）
../target/debug/claw doctor

# 5. 运行第一个 Prompt
../target/debug/claw prompt "say hello"
```

### Windows（PowerShell）注意事项

```powershell
# 设置 API Key
$env:ANTHROPIC_API_KEY = "sk-ant-..."

# 构建
cargo build --workspace

# 运行
..\target\debug\claw.exe doctor
..\target\debug\claw.exe prompt "say hello"
```

Windows 下如果报"不是内部或外部命令"，先确认 Rust 已正确安装：

```powershell
cargo --version
```

如果报错，需要安装 [Rust](https://rustup.rs/) 并重启 PowerShell。

---

## 核心架构

Claw Code 的代码组织如下（以 `rust/` 目录为规范实现）：

```
claw-code/
├── rust/                          # 规范 Rust workspace
│   ├── Cargo.toml                 # workspace 根
│   ├── claw/                      # 主二进制：`claw` CLI
│   ├── claw-core/                 # 核心库：会话、工具注册、LLM 调用
│   ├── claw-mcp/                  # MCP 协议支持（部分实现）
│   └── ...
├── src/ + tests/                  # 配套 Python 参考工作区（非主运行时）
├── USAGE.md                       # 任务导向的使用指南（推荐优先阅读）
├── PARITY.md                      # Rust 移植进度与迁移说明
├── ROADMAP.md                     # 路线图与待办事项
└── docs/container.md              # 容器优先工作流文档
```

**请求流转路径**（理解这个对读源码很重要）：

```
用户输入 Prompt
    ↓
CLI 入口 (claw/src/main.rs)
    ↓
会话管理 (claw-core/src/session.rs) → SQLite 持久化
    ↓
工具注册表 (claw-core/src/tools.rs) → #[tool] 宏生成 JSON Schema
    ↓
Provider trait (claw-core/src/provider.rs) → 统一 Anthropic/OpenAI/Ollama API
    ↓
LLM API → 流式响应 (SSE) → 返回给用户
```

### 关键设计

| 设计点 | 实现方式 | 说明 |
|--------|----------|------|
| 会话持久化 | SQLite | 对话历史存 `~/.config/claw/sessions/`，随时恢复 |
| 工具注册 | `#[tool]` 宏 | 自动生成 JSON Schema，注册到 LLM |
| 多模型适配 | 统一 Provider trait | Anthropic / OpenAI / Ollama 统一接口 |
| 流式响应 | SSE（Server-Sent Events） | token 逐字返回，支持中断 |
| MCP 支持 | 部分实现 | 完整 MCP 支持在路线图中，当前版本可能不稳定 |

---

## 与 Anthropic Claude Code 的区别（重要）

**Claw Code ≠ Anthropic Claude Code**。两者完全独立：

| 维度 | Claw Code | Anthropic Claude Code |
|------|-----------|----------------------|
| 开发者 | ultraworkers 团队 | Anthropic |
| 语言 | Rust | 未知（Anthropic 官方闭源） |
| 开源情况 | 开源（MIT） | 官方 CLI 工具（部分开源） |
| 定位 | 研究性 artifacts / 博物馆展品 | 生产级 AI 编程助手 |
| 维护方式 | 完全由 Agent 自主维护 | Anthropic 官方团队维护 |
| 获取方式 | `git clone` + `cargo build` | `npm install -g @anthropic-ai/claude-code` |

如果你想要的是 Anthropic 官方的 Claude Code，去 [Anthropic 官网](https://www.anthropic.com/) 或 [Claude Code 文档](https://docs.anthropic.com/en/docs/claude-code) 找，不是这个项目。

---

## 能力边界：什么能做，什么不能

### 能做

- 作为 **AI Agent 原型开发的参考实现**：Rust 实现、会话管理、工具注册这些代码有参考价值
- 作为 **CLI harness 的学习样本**：想了解怎么用 Rust 写一个 Agent CLI，可以读它的源码
- 作为 **多模型适配的测试床**：支持 Anthropic / OpenAI / Ollama，可以测不同模型在同一个 harness 上的表现

### 不能做（或不建议）

- **作为日常开发工具**：项目自述是"博物馆展品"，文档可能过时，功能可能不稳定
- **用于生产环境**：完全由 Agent 维护意味着没有人工负责，出问题没人修
- **期望稳定的 MCP 支持**：MCP 支持在路线图中，当前版本可能不完整

---

## 实践案例

### 案例1：用 Claw Code 对接 OpenAI 模型

假设你已经有 OpenAI API Key，想用 Claw Code 作为 CLI harness：

```bash
# 1. 设置 OpenAI API Key
export OPENAI_API_KEY="sk-..."

# 2. 运行健康检查
../target/debug/claw doctor

# 3. 用 OpenAI 模型运行 Prompt
../target/debug/claw prompt "用 Python 写一个快速排序" --provider openai --model gpt-4o

# 4. 查看会话历史
../target/debug/claw sessions list
```

**关键点**：Claw Code 的多 Provider trait 让你可以无缝切换 between Anthropic 和 OpenAI，不需要改代码。

### 案例2：本地 Ollama 运行（无需 API Key）

如果你想在离线环境使用：

```bash
# 1. 启动 Ollama（确保已安装 Ollama）
ollama serve

# 2. 在新终端中拉取模型
ollama pull llama3

# 3. 配置 Claw Code 使用 Ollama
export OLLAMA_HOST="http://localhost:11434"

# 4. 运行 Prompt
../target/debug/claw prompt "解释 Rust 的所有权机制" --provider ollama --model llama3
```

**关键点**：Ollama 不需要 API Key，适合隐私敏感场景或离线开发。

### 案例3：会话管理与恢复

Claw Code 的 SQLite 持久化让你可以恢复之前的对话：

```bash
# 1. 创建一个带名称的会话
../target/debug/claw prompt "帮我设计一个 Rust CLI 工具" --session-name "rust-cli-design"

# 2. 查看所有会话
../target/debug/claw sessions list

# 3. 恢复会话，继续之前的对话
../target/debug/claw prompt "继续刚才的设计，加上错误处理" --session-name "rust-cli-design"
```

**关键点**：会话持久化让你可以跨多次运行维护上下文，不需要把所有历史都放在一个 Prompt 里。

---

## 常见问题

### Q: `claw doctor` 报告 API Key 无效怎么办？

确认你用的是正确的 Key：

- **Anthropic API Key**（`ANTHROPIC_API_KEY`）：在 [Anthropic Console](https://console.anthropic.com/) 申请，不是 Claude 网页版的登录 Session
- **OpenAI API Key**（`OPENAI_API_KEY`）：在 [OpenAI Platform](https://platform.openai.com/) 申请
- **Ollama**（无需 Key）：设置 `OLLAMA_HOST=http://localhost:11434`，本地运行 Ollama 即可

调试步骤：

```bash
# 1. 确认环境变量已设置
echo $ANTHROPIC_API_KEY

# 2. 测试 Anthropic API Key 是否有效
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 10,
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

如果返回 401 错误，说明 API Key 无效或已过期。

### Q: 构建速度太慢怎么办？

```bash
# Release 模式（运行时性能更好，编译更慢）
cargo build --workspace --release

# 仅构建 claw 包
cargo build -p claw --release

# 使用 sccache 缓存编译产物
cargo install sccache
export RUSTC_WRAPPER=sccache
cargo build --workspace
```

### Q: `claw` 命令找不到？

二进制不在 PATH 中，需要手动配置：

```bash
# 方式1：软链接（Linux/macOS）
sudo ln -s $(pwd)/rust/target/debug/claw /usr/local/bin/claw

# 方式2：cargo install --path
cd claw-code/rust
cargo install --path . --force
# 安装到 ~/.cargo/bin/，确保这个路径在 PATH 中

# 方式3：添加到 shell 配置文件
echo 'export PATH="$PATH:'$(pwd)'/rust/target/debug"' >> ~/.zshrc
source ~/.zshrc
```

### Q: 支持 Windows 吗？

支持，但需要注意：

- 推荐使用 PowerShell，Git Bash 和 WSL 也可行
- 路径分隔符是 `\`，二进制文件名是 `claw.exe`
- Windows 有 260 字符路径限制，可以启用长路径支持（需要管理员权限）：

```powershell
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1
```

### Q: 会话数据存储在哪？

默认存储在 `~/.config/claw/sessions/` 目录下，每个会话一个 SQLite 文件。可以通过 `--session-path` 指定其他位置：

```bash
../target/debug/claw prompt "hello" --session-path /path/to/session.db
```

---

## 自测题

检验你对 Claw Code 的理解，回答下面 4 个问题：

1. Claw Code 和 Anthropic Claude Code 的区别是什么？如果误装了 `cargo install claw-code`，会发生什么？
2. 为什么项目自述是"博物馆展品"？这给使用者带来了什么风险？
3. `claw doctor` 的作用是什么？如果报告 API Key 无效，你应该检查哪几个地方？
4. 如果你想用 Claw Code 做日常开发工具，作者给出的建议是什么？有什么替代方案？

3 题以上答不准的话，建议重看"项目背景"和"能力边界"两节。

<details>
<summary>参考答案</summary>

**题 1**：Claw Code 是 ultraworkers 团队开源的 Rust CLI harness，Anthropic Claude Code 是 Anthropic 官方的 AI 编程助手，两者完全独立。`cargo install claw-code` 会安装一个早已废弃的空壳包，只会打印 `"claw-code has been renamed to agent-code"`，不会安装真正的 claw 工具。正确做法是从源码构建。

**题 2**："博物馆展品"意味着代码完全由 AI Agent 自主开发维护，无人工干预。这带来的风险是：文档可能过时、功能可能不稳定、代码和文档可能不一致，而且没有人类负责维护。

**题 3**：`claw doctor` 检查环境配置，包括 API Key 是否有效、依赖是否完整、工具是否能正常调用。如果报告 API Key 无效，应检查：(1) 环境变量是否设置正确（echo $ANTHROPIC_API_KEY）；(2) API Key 是否过期（用 curl 测试）；(3) 是否混淆了 Claude 网页版登录 Session 和 API Key。

**题 4**：作者不建议把 Claw Code 作为日常开发工具，因为它是"博物馆展品"而非生产级工具。替代方案：优先选 [LazyCodex](https://github.com/code-yeongyu/lazycodex) 或 [Gajae-Code](https://github.com/Yeachan-Heo/gajae-code)。

</details>

---

## 练习

### 练习一：从源码构建并运行第一个 Prompt

**目标**：完成环境配置，成功运行 `claw doctor` 和 `claw prompt "say hello"`。

**步骤**：

1. 安装 Rust（如果还没有）：`curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
2. 克隆仓库：`git clone https://github.com/ultraworkers/claw-code`
3. 进入 Rust 目录：`cd claw-code/rust`
4. 构建：`cargo build --workspace`（首次约 3-5 分钟）
5. 设置 API Key：`export ANTHROPIC_API_KEY="sk-ant-..."`
6. 运行健康检查：`../target/debug/claw doctor`
7. 运行第一个 Prompt：`../target/debug/claw prompt "say hello"`

**通过标准**：`claw doctor` 显示所有检查通过，`claw prompt "say hello"` 返回有效回复。

### 练习二：阅读 `rust/README.md`，画出架构层次

**目标**：理解 Claw Code 的代码组织，建立阅读源码的路线图。

**步骤**：

1. 打开 [rust/README.md](https://github.com/ultraworkers/claw-code/blob/main/rust/README.md)
2. 识别 `claw`、`claw-core`、`claw-mcp` 三个 crate 的职责
3. 画出一个简化的架构图：CLI 入口 → 核心库 → Provider → LLM API
4. 对照 PARITY.md，找出 Rust 移植的已知差异

**通过标准**：你的架构图能解释"用户输入 Prompt 后，请求如何流过系统并最终调用 LLM API"。

---

## 进阶阅读路径

下面给出阅读顺序与每篇为什么放在这个位置的理由：

1. **[Claw Code GitHub 仓库](https://github.com/ultraworkers/claw-code)**（先读）。这是理解项目的起点，重点关注 README 中的"博物馆展品"自述、USAGE.md 和 ROADMAP.md。先读这个，建立对项目定位的完整认知，再决定是否深入。

2. **[USAGE.md](https://github.com/ultraworkers/claw-code/blob/main/USAGE.md)**（第二读）。当你想知道"claw CLI 支持哪些命令"、"怎么配置会话"时，这个文档是最直接的参考。注意：因为项目由 Agent 维护，文档可能和代码有出入，遇到矛盾时以代码为准。

3. **[LazyCodex](https://github.com/code-yeongyu/lazycodex) 或 [Gajae-Code](https://github.com/Yeachan-Heo/gajae-code)**（第三读，如果你想要生产级工具）。这是 Claw Code 作者推荐的替代方案，功能更完整、维护更稳定。对比两者的设计取舍，帮你判断哪个更适合你的场景。

4. **[Anthropic Claude Code 文档](https://docs.anthropic.com/en/docs/claude-code)**（第四读，如果你混淆了这两个项目）。当你想了解"Anthropic 官方的 AI 编程助手是什么"时，读这个。注意：Claw Code ≠ Claude Code。

5. **[PARITY.md](https://github.com/ultraworkers/claw-code/blob/main/PARITY.md)**（最后读，可选）。当你想深入 Rust 移植的进度和已知差异时读这个。如果你打算基于 Claw Code 做二次开发，这个文档能帮你避开已踩过的坑。

---

## 总结

Claw Code 是一个有意思的研究项目：它展示了用 Rust 写 AI Agent CLI 的一种实现方式，代码完全由 AI Agent 生成。这在技术上有参考价值，但作为日常工具，它的"博物馆展品"定位意味着文档可能过时、功能可能不稳定。

如果你想要一个能日常用的 AI Agent CLI，作者的建议是选 LazyCodex 或 Gajae-Code。如果你是想学习 Rust CLI harness 的实现，或者需要多模型适配的测试床，Claw Code 的源码值得读。

关键要点：

1. 不要用 `cargo install claw-code`，从源码构建
2. Claw Code ≠ Anthropic Claude Code，两者完全独立
3. 文档可能和代码不一致，遇到矛盾时以代码为准

---

## 参考链接

- Claw Code GitHub：https://github.com/ultraworkers/claw-code
- USAGE.md：https://github.com/ultraworkers/claw-code/blob/main/USAGE.md
- ROADMAP.md：https://github.com/ultraworkers/claw-code/blob/main/ROADMAP.md
- PARITY.md：https://github.com/ultraworkers/claw-code/blob/main/PARITY.md
- LazyCodex（推荐替代）：https://github.com/code-yeongyu/lazycodex
- Gajae-Code（推荐替代）：https://github.com/Yeachan-Heo/gajae-code

---

*本文基于 ultraworkers/claw-code 公开仓库信息撰写（2026-06-24 核实）。项目定位为研究性 artifacts，功能描述以源码为准，文档可能过时。*
