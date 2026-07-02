---
title: "openai/codex-plugin-cc 项目指南：在 Claude Code 中调用 Codex 做代码评审与任务委派"
date: "2026-07-02T21:02:26+08:00"
lastmod: "2026-07-02T21:02:26+08:00"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "Codex", "AI编程", "代码评审", "OpenAI"]
description: "OpenAI 官方插件 codex-plugin-cc：在 Claude Code 中嵌入 Codex 的 8 个 slash 命令与 rescue 子代理，覆盖评审、委派与 session 转交。"
weight: 1
author: text-matrix
---

# openai/codex-plugin-cc 项目指南：在 Claude Code 中调用 Codex 做代码评审与任务委派

> 一句话定位：OpenAI 出品的 Claude Code 插件，把 Codex 作为"第二双眼睛"和"后台救援队"嵌进 Claude Code 工作流。

## 这是什么

`openai/codex-plugin-cc`（仓库地址：<https://github.com/openai/codex-plugin-cc>）是 OpenAI 官方为 Claude Code 用户开发的插件。它解决一个具体问题：日常在 Claude Code 中写代码、调试、改实现，但希望在不离开当前工作流的前提下，调用另一个模型（Codex）做独立的代码评审，或者把复杂、长时间、跨多文件的调试任务交给 Codex 后台执行。

仓库当前 ★22,325（+72 today），主要语言 JavaScript（Node 18.18+），License Apache-2.0，`package.json` 声明的版本是 1.0.5。插件以 marketplace 形式发布，安装命令是 `/plugin marketplace add openai/codex-plugin-cc`，再 `/plugin install codex@openai-codex`，随后 `/reload-plugins`。

它提供的不是单一命令，而是一整套覆盖评审、委派、转移、监控、取消的指令集，外加一个 `codex:codex-rescue` 子代理。运行时不引入独立账号体系，直接复用本地 Codex CLI 的鉴权状态、配置和代码库 checkout。

## 八个 slash 命令，一张速查表

插件在 Claude Code 中注册的 slash 命令共 8 条，按用途可分为三组。

| 命令 | 用途 | 是否只读 | 是否支持后台 |
| --- | --- | --- | --- |
| `/codex:review` | 对当前工作树或指定 base 分支做 Codex 评审 | 是 | 是（`--background`） |
| `/codex:adversarial-review` | 在 `/codex:review` 基础上加入"挑战式"焦点，可附加 focus 文本 | 是 | 是 |
| `/codex:rescue` | 把调试、修复、深入调查委派给 Codex rescue 子代理 | 否（默认 `--write`） | 是（`--background`） |
| `/codex:transfer` | 把当前 Claude Code session 转成一个可 resume 的 Codex thread | 否 | — |
| `/codex:status` | 查看本仓库当前正在跑或最近完成的 Codex job | — | — |
| `/codex:result` | 拉取已完成 job 的最终输出，含 session id | — | — |
| `/codex:cancel` | 取消一个正在跑的 Codex 后台 job | 否 | — |
| `/codex:setup` | 检查 Codex 是否就绪，切换可选 review gate | — | — |

`/codex:review` 和 `/codex:adversarial-review` 只读，不会修改代码。`/codex:rescue` 默认开启 `--write`，会真的让 Codex 改文件——这是它和评审类的最大区别。

## 第一次使用：五步装好

下面是仓库 README 给出的最小可用回路。

```bash
# 1. 在 Claude Code 里添加 marketplace
/plugin marketplace add openai/codex-plugin-cc

# 2. 安装插件
/plugin install codex@openai-codex

# 3. 重载插件
/reload-plugins

# 4. 自检（如果 Codex 没装，它会提示安装）
/codex:setup

# 5. 第一次后台评审
/codex:review --background
/codex:status
/codex:result
```

前置条件：ChatGPT 订阅（含 Free）或 OpenAI API key，Node.js 18.18+，全局能跑 `codex`（缺失时 `/codex:setup` 会询问要不要 `npm install -g @openai/codex`）。鉴权沿用本地 Codex CLI：`!codex login` 即可，覆盖 ChatGPT 与 API key 两种登录方式。

第一次跑通后，Claude Code 的 `/agents` 列表里会出现一个 `codex:codex-rescue` 子代理，仓库根目录的 `.claude-plugin/marketplace.json` 也会显示 `openai-codex` 已注册。

## 八条命令的差异点

### 评审类：只读，但要看场合

`/codex:review` 与 `/codex:adversarial-review` 都不改文件，区别在于"审什么"。

- `/codex:review`：通用评审，看 working tree 改动或 `git diff <base>...HEAD`。参数支持 `--base <ref>`（分支对比）、`--wait`（前台等）、`--background`（后台跑）、`--scope auto|working-tree|branch`（评审范围）。不支持自定义 focus text。
- `/codex:adversarial-review`：在通用评审之上，允许追加一段自然语言 focus，比如 "challenge whether this was the right caching and retry design" 或 "look for race conditions and question the chosen approach"。它专门用来质疑设计取舍、隐藏假设、替代方案。仓库 README 明确推荐在"发货前的方向性 review"和"对 auth / 数据丢失 / 回滚 / 竞态 / 可靠性等高风险区"用 adversarial。

两个命令对多文件改动都建议加 `--background`，因为 Codex 评审耗时长。`/codex:status` 和 `/codex:cancel` 只对后台运行有效。

### 委派类：rescue 是主力

`/codex:rescue` 是真正干活的入口。它调用 `codex:codex-rescue` 子代理（一个 `model: sonnet` 的极简转发 wrapper），由后者执行一次 `node ${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs task ...`。子代理的契约写得非常严格：只调一次 `task`、把 stdout 原样返回、不检查仓库、不做后处理。

可传参数：

- `--background` / `--wait`：决定 Claude Code 这边跑前台还是后台。
- `--resume` / `--fresh`：继续最近一次 rescue 线程 vs 全新开线程。省略时插件会跑一次 `task-resume-candidate --json` 探测，再问一次用户。
- `--model <name>`：直接传模型名，比如 `gpt-5.4-mini`。`spark` 是别名，会映射到 `gpt-5.3-codex-spark`。
- `--effort <level>`：推理强度，合法值 `none / minimal / low / medium / high / xhigh`，省略时由 Codex 自行选默认。

调用形式可以是结构化参数，也可以是自然语言委派："Ask Codex to redesign the database connection to be more resilient."——rescue 会把整段自然语言作为 prompt 转给 Codex。

### 转移与状态：把工作交回 Codex

`/codex:transfer` 用于把当前 Claude Code 对话落成一个 Codex 持久 thread，输出里会带 `codex resume <session-id>` 命令。插件通过 `SessionStart` hook 自动注入当前 transcript 路径（`~/.claude/projects/-Users-me-repo/<session-id>.jsonl`），必要时可手动 `--source` 覆盖。它走 Codex 的 external-agent session importer，遵循 Codex App 导入 Claude 历史时同样的转换规则。

`/codex:status`、`/codex:result`、`/codex:cancel` 是配套的状态机入口，对应"看进度 / 取结果 / 终止"。`/codex:result` 在有结果时还会顺带返回 Codex session id，方便直接 `codex resume` 接上。

### setup：自检 + review gate 开关

`/codex:setup` 除了"装没装、登没登"的自检，还负责一个可选特性：Stop hook review gate。

```bash
/codex:setup --enable-review-gate
/codex:setup --disable-review-gate
```

打开后，插件在 Claude 即将 `Stop` 时调用 `scripts/stop-review-gate-hook.mjs`，对 Claude 的最新一轮回复做一次定向 Codex 评审。如果发现问题，会阻止 stop，让 Claude 先去改。仓库 README 明确警告："review gate 可能让 Claude/Codex 陷入长循环并快速消耗用量额度，只在你打算主动盯 session 时才打开。"

## 工作流典型用法

仓库 README 在"Typical Flows"小节给了三个最小流程，可以直接套用。

### 发货前评审

```bash
/codex:review
```

或者对分支做对比：`/codex:review --base main`。多文件改动先 `/codex:review --background`，再用 `/codex:status` 轮询、`/codex:result` 取结果。

### 把棘手问题扔给 Codex

```bash
/codex:rescue investigate why the build is failing in CI
/codex:rescue fix the failing test with the smallest safe patch
/codex:rescue --resume apply the top fix from the last run
/codex:rescue --model gpt-5.4-mini --effort medium investigate the flaky integration test
/codex:rescue --background investigate the regression
```

`--resume` 会接上最近一次 rescue 线程；`--fresh` 强制开新线程。

### 长任务先放后台

```bash
/codex:adversarial-review --background
/codex:rescue --background investigate the flaky test
```

完成后通过 `/codex:status` 看进展、`/codex:result` 拿最终结果。如果发现方向不对，`/codex:cancel` 立即终止（需要 job id，可从 `/codex:status` 取）。

## 架构：codex-companion.mjs + Codex app-server

插件的运行时分两层：上层的 8 个 slash 命令 + 1 个 rescue 子代理是 Claude Code 的指令层；下层是一个 Node 脚本 `plugins/codex/scripts/codex-companion.mjs`，它是所有命令的统一入口，负责参数解析、job 状态管理、Codex 进程编排与结果渲染。

`codex-companion.mjs` 不直连任何 OpenAI 端点，而是通过 [Codex app-server](https://developers.openai.com/codex/app-server) 启动后台 Codex 进程。仓库把这层关系写得很明确：

> The Codex plugin wraps the Codex app server. It uses the global codex binary installed in your environment and applies the same configuration.

也就是说，本地 `codex` 二进制 + 你机器上的 `~/.codex/config.toml` 配置 + 当前仓库的 checkout，这三样被 Codex CLI 读到的东西，插件原样继承。账号、API key、模型选择、推理强度全部走 Codex 自己的鉴权和配置，不存在"插件专属账号"或"插件专属 runtime"。

## 配置：和 Codex 共用 config.toml

如果想为某个项目固定默认模型或推理强度，写到 `.codex/config.toml` 即可：

```toml
model = "gpt-5.4-mini"
model_reasoning_effort = "high"
```

加载顺序是：

- user-level `~/.codex/config.toml`
- project-level `.codex/config.toml`（仅当项目被加入 trusted 时生效）

如果你需要把 OpenAI provider 指到自建网关，在 Codex 配置里设置 `openai_base_url` 即可，插件不会绕开。

## 适用边界

值得装的场景：

- 你日常用 Claude Code 写代码，但希望评审由独立模型做（避免"Claude 审自己"的盲点）。
- 你有大量需要后台长跑的调试/重构任务，希望 Claude 主线不被打断。
- 你经常在 Claude Code 和 Codex App 之间切换，希望通过 `/codex:transfer` 把上下文平滑移交。
- 你愿意用 ChatGPT 订阅或 API key，已经在本地装好了 Codex。

不适合的场景：

- 你目前没装 Codex CLI，也没订阅 ChatGPT 或 OpenAI API——插件本身不会替代 Claude Code 的模型。
- 你希望"双模型对比"或"模型 A/B 评审"——插件只调度 Codex，不接其他供应商。
- 你对后台 agent 的耗时和用量消耗非常敏感，且没人盯 session——review gate 与 rescue 都可能拉长一轮对话并消耗大量额度。
- 你的工作流完全在 Codex App 里——这种情况下 `/codex:transfer` 的目标用户是 Claude Code 端，Codex-only 流程用不到。

## 结语

`codex-plugin-cc` 不是"另一个 AI 编程助手"，而是一个**编排层**：把 Claude Code 当前端、把 Codex 当后端 reviewer / worker，用 8 条 slash 命令和 1 个 rescue 子代理在两者之间搬运任务和上下文。它的价值不在单条命令多强大，而在把这些命令统一收口到一个 `codex-companion.mjs` 入口，让评审、委派、转移、监控、取消共享同一套 job 状态机和 Codex 配置。

如果你已经在用 Claude Code，并且希望"评审独立化、任务后台化、上下文可移交"，它是一个值得 5 分钟装上试一下的官方插件。