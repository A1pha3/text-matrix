---
title: "Continue 终局观察：README 写着 read-only，仓库却从未挂上 Archived 标志"
date: "2026-06-17T21:05:57+08:00"
lastmod: "2026-10-04"
slug: "continuedev-continue-open-source-coding-agent-guide"
description: "continuedev/continue 以一句 README 斜体宣告终结：Final 2.0.0 三端收尾、移除遥测、剥离认证。但仓库既未归档，main 分支在声明之后又维护了五周。本文核对声明与仓库实况的差距，并拆解它留下的两层安全模型与 CLI 架构。"
draft: false
categories: ["技术笔记"]
tags: ["Coding Agent", "TypeScript", "VS Code", "CLI"]
---

# Continue 终局观察：README 写着 read-only，仓库却从未挂上 Archived 标志

2026 年 6 月，Continue 团队在仓库 README 开头放了一句斜体：

> _Note: The `continuedev/continue` repository is no longer actively maintained and is read-only for all users._

同一个 README 里，团队宣布做了 "a final 2.0.0 release"，移除匿名遥测、剥离认证、集中修 Bug，然后感谢社区：**"We hope this codebase continues to serve as a foundation for others."** 一段开源 AI 编程助手的早期历史，就这样用 63 行 README 收了尾。

有意思的是声明与仓库实况的差距。GitHub API 显示 `continuedev/continue` 的 `archived` 字段是 `false`——仓库从未挂上 Archived 标志；main 分支在声明发布之后又接了五周提交，最后一次停在 2026-07-21，内容是撤掉登录入口和迁移文档站域名。这是一种"软退出"：功能开发停止，README 承担了归档公告的职能，而仓库本身保持可写、可 fork、可克隆。

本文基于 2026-10-04 的仓库状态（36,102 Stars、5,445 Forks、Apache-2.0）与源码核对，回答三个问题：这次终版发布到底交付了什么、仓库里还剩哪些值得读的工程资产、以及现在拿它应该怎么用。

## 一、三端形态：一个 Core，三种壳

Continue 自述为 "pioneering open-source coding agent"。从 2023 年 5 月建仓到终版，它一直是三端并行的结构：CLI、VS Code 扩展、JetBrains 插件共享同一份 `core/` 代码与模型抽象，靠一个 monorepo 统一管理。终版时三端的状态并不对称：

| 形态 | 入口包 | 终版版本 | 分发渠道 | 现状 |
|------|--------|----------|----------|------|
| **CLI**（`cn`） | `@continuedev/cli`（npm） | 1.5.47（2026-06-18） | npm + 官方 install 脚本 | README 建议的默认入口 |
| **VS Code 扩展** | `Continue.continue` | 2.1.0（2026-06-19） | Marketplace + Open VSX | 随 Final 2.0.0 一并收尾 |
| **JetBrains 插件** | 仓库内 `extensions/intellij` | v1.0.67-jetbrains（2026-03-27） | JetBrains Marketplace（120.9 万次下载） | 官方建议改用 CLI |

两个容易读错的细节：

**"Final 2.0.0" 是对终版发布的统称，不是三端共同的版本号。** README 原话是 "did a final 2.0.0 release of the VS Code extension, CLI, and JetBrains plugin"，落到具体版本上，只有 VS Code 扩展拿到了 2.x 号（GitHub Releases 里 `v2.0.0-vscode` 与 `v2.1.0-vscode` 同在 2026-06-19 发布），CLI 停在 npm 的 1.5.47，JetBrains 停在 3 月底的 v1.0.67。如果你在 fork 里找"2.0.0 的 CLI"，找不到。

**JetBrains 插件一直在 JetBrains Marketplace 正常分发。** README 的 JetBrains 一节只给了 GitHub Releases 徽章，容易被读成"不走 Marketplace、本地安装为主"——实际插件 ID 22707 在 Marketplace 在架，截至 2026-10-04 累计约 120.9 万次下载；仓库的 `jetbrains-release.yaml` 工作流至今保留着完整的 Marketplace 发布流程（`PUBLISH_TOKEN` 加 Apple 签名证书全套，支持 EAP 和 Stable 双通道）。徽章只是 README 的展示选择。

## 二、终版发布与"软退出"时间线

把 main 分支的提交按时间排开，能看到一次收尾是如何执行的：

| 时间 | 动作 |
|------|------|
| 2026-06-15 | "Final release cleanup"：移除 CLI 横幅与 Generate Rule，默认配置改为显式模型定义 |
| 2026-06-15 | 同日修复：删除死掉的登录强制逻辑与 Login Required UI、隔离 GlobalContext 修复测试抖动 |
| 2026-06-18 | `fix(cli)`：默认配置改用显式模型定义，替代 Hub slug |
| 2026-06-18/19 | `fix(gui)` 两笔：移除 GitHub issue 反馈入口、修 onboarding 卡片滚动 |
| 2026-06-19 | `v2.0.0-vscode` 与 `v2.1.0-vscode` 同日发布；npm 发布 CLI 1.5.47 |
| 2026-07-21 | 三笔 docs 提交：文档站迁至 docs.continue.dev 根路径（`basePath ""` + CNAME）、移除 Sign in 链接（提交信息原话 "login flow retired"） |
| 此后 | main 分支静默；仓库 `archived` 保持 `false` |

三条值得记下的观察：

**移除遥测和剥离认证是真实动作。** 提交历史里能看到对应的痕迹——登录强制逻辑在 6-15 被当作"dead login requirement"删掉，7-21 连文档站的 Sign in 链接都撤了。README 说的 "removing anonymous telemetry, pulling out authentication" 不是修辞。（CLI 里仍保留 `cn login` 命令和 WorkOS 认证模块，用于对接 Continue Hub 的场景，详见下文。）

**"Final" 之后仍有五周维护。** 声明是 6 月上旬写进 README 的（era 快照与当前 README 逐字一致），但 6 月中下旬还有一批 GUI/CLI 修复，7 月还有文档站迁移。这不是"声明造假"，而是收尾工程的自然延续——但读者要知道"read-only"描述的是维护姿态，不是仓库的物理状态。

**fork 时没有单一锚点。** 三端版本号各异，"基于 2.0.0 tag 切分支"的说法不成立。更稳的做法是直接基于当前 main 末端的 commit（2026-07-21 的 `5522c6f4`）切分支——它就是事实上的终线。

## 三、仓库地图：哪些目录还在干活

根目录共 27 项。核心分层是 `core/`（共享内核）、`extensions/`（三端壳）、`packages/`（七个小包）：

```text
continuedev/continue/
├── core/                    # 共享内核：llm / context / edit / tools / config / indexing …
├── extensions/
│   ├── vscode/              # VS Code 扩展
│   ├── cli/                 # CLI（cn 二进制，@continuedev/cli）
│   └── intellij/            # JetBrains 插件
├── packages/                # 七个独立小包（见下表）
├── gui/                     # React 界面包（VS Code 侧的 webview 前端）
├── binary/                  # Node 打包产物（bin: out/index.js）
├── sync/                    # Rust 原生模块（cdylib），代码库同步/索引
├── docs/                    # Mintlify 风格文档源（docs.json + mdx）
├── docs-site/               # Next.js 文档站（docs.continue.dev）
├── eval/                    # 已清空，仅剩 .gitignore
├── skills/                  # cn-check（仓库自带的 CLI 检查 skill）
├── actions/  scripts/  manual-testing-sandbox/  media/
├── BUILD_DEPENDENCIES.md    # 全部构建密钥与发布令牌清单
├── TESTING.md  SECURITY.md  CONTRIBUTING.md  CLA.md  CODE_OF_CONDUCT.md
├── LICENSE  README.md  tsconfig.json  worktree-config.yaml
└── package.json             # 根编排：concurrently 并行四路 tsc --watch
```

`packages/` 下七个包的分工：

| 包 | 职责 |
|------|------|
| `config-types` | 配置类型定义（被其余包依赖的根） |
| `config-yaml` | `config.yaml` 的 Zod schema 解析与校验 |
| `fetch` | 统一 HTTP 客户端 |
| `llm-info` | 模型能力元数据 |
| `openai-adapters` | OpenAI 兼容协议适配 |
| `terminal-security` | 终端命令安全评估（下文详解） |
| `continue-sdk` | Continue 平台 SDK（API key 认证、assistant slug、组织支持） |

三个和预期不符的地方，值得在克隆之前知道：

**`eval/` 已经空了。** 一些旧介绍把 `eval/` 描述为"团队的评估集，值得研究"——当前 HEAD 里它只剩一个 `.gitignore`，内容已在终版前清空。

**`sync/` 不是脚本，是 Rust。** `Cargo.toml` 显示它是个 cdylib 原生模块（"Continue Codebase Syncing"），承担代码库同步/索引的性能敏感部分，不是 shell 脚本合集。

**构建编排比典型 monorepo 手工。** 根目录没有 npm workspaces，根 `package.json` 里主要值得看的是 `tsc:watch`：用 `concurrently -n gui,vscode,core,binary -c cyan,magenta,yellow,green` 并行跑四路 `tsc --watch`，用颜色区分输出。真正的依赖顺序构建脚本 `build:local-deps` 在 `extensions/cli/package.json` 里，按 `config-types → fetch → llm-info → terminal-security → config-yaml → openai-adapters → core → cli` 的顺序逐包 `npm i && npm run build`——先子后父，避免并行编译时的类型找不到。各包独立维护 `package-lock.json`，每个小包有自己的 semantic-release 发布流水线（`release-fetch.yml`、`release-config-yaml.yml` 等）。

## 四、CLI 架构：一个二进制，三种运行模式

`extensions/cli` 是终版时最活跃的一端，`AGENTS.md`（写给 AI 编码代理的开发指引，也是目前最准确的架构自述）把它拆成五块：

1. **入口** `src/index.ts`：三种模式——Headless（无 TTY 自动化）、TUI（Ink/React 终端界面）、Standard（readline 聊天）。
2. **认证** `src/auth/`：WorkOS 体系（`workos.ts` 管配置与 token）。这就是"剥离认证"的落点：与 Continue Hub 相关的身份链路被隔离在这个目录与 `continue-sdk` 包里，不与 Agent 执行路径纠缠。
3. **SDK 集成** `src/continueSDK.ts`：API key 认证、assistant slug、组织支持。
4. **终端 UI** `src/ui/`：React/Ink 组件（`TUIChat.tsx` 等）。
5. **工具系统** `src/tools/`：文件读写、搜索、终端执行、diff 查看，外加一个只在 headless 模式存在的 Exit 工具。

命令面（出自 CLI README）：

```bash
# 安装（官方主推脚本，npm 需 Node.js 20+）
curl -fsSL https://raw.githubusercontent.com/continuedev/continue/main/extensions/cli/scripts/install.sh | bash
npm i -g @continuedev/cli   # 备选

cn                      # 交互式聊天
cn -p "…"               # headless 模式（无 TUI，适合脚本/CI/Docker）
cn -p "…" --format json # JSON 输出，供脚本消费
cn --resume             # 恢复本终端最近一次会话
cn ls [--json]          # 列出会话
cn login / cn logout    # Continue Hub 认证
cn serve                # HTTP 服务器模式
cn remote               # 远程实例
```

两个容易被忽略的环境变量：`FORCE_NO_TTY` 强制无 TTY 模式（测试与自动化用）；`CONTINUE_CLI_DISABLE_COMMIT_SIGNATURE` 关闭 CLI 给生成 commit 信息追加的 Continue 签名。默认模型在 `src/services/ConfigService.ts` 里定义为一个 Hub slug：`anthropic/claude-sonnet-4-6`。

`spec/` 目录下还有 12 篇设计文档（permissions、modes、shell-mode、tty-less-support、otlp-metrics、config-loading 等），是理解 CLI 设计取舍的最短路径——比读源码快得多，而且大多短小。

## 五、两层安全模型：permissions 管工具，terminal-security 管命令

Continue 的 Agent 安全控制分两层，各自的粒度和机制完全不同。这是仓库里最值得精读的部分。

**第一层：工具级 permissions 系统。** 每个工具有三态权限——`allow`（自动执行）、`ask`（先问用户）、`exclude`（对模型完全隐藏）。优先级五层，从高到低：

1. 模式策略（`plan` / `auto`，绝对覆盖，见下）
2. 命令行旗标：`--allow` / `--ask` / `--exclude`，支持 glob 匹配（如 `Read(**/*.ts)` 只匹配读 `*.ts` 文件的调用）
3. `config.yaml` 配置
4. `~/.continue/permissions.yaml`
5. 内置默认策略

默认策略（`src/permissions/defaultPolicies.ts`）的真实取值：写工具（`Edit` / `MultiEdit` / `Write`）默认 `ask`；读工具（`Read` / `List` / `Search` / `Fetch` / `Diff` 等）默认 `allow`；`Bash` 和其余所有工具在 TUI 模式默认 `ask`，**在 headless 模式默认 `allow`**——官方为自动化场景选择了放行，把这个默认值当作采用决策的一部分来评估，是必要的。

三个模式里，`normal` 走上述配置；`plan`（`--readonly`）绝对覆盖为只读——`Edit` / `MultiEdit` / `Write` 全部 `exclude`，但保留 `Bash`（源码注释里写着 "TODO address bash read only concerns"，官方自己承认这不算严格的只读）；`auto`（`--auto`）绝对放行一切。聊天中用 Shift+Tab 切换。

**第二层：命令字符串级 terminal-security。** `packages/terminal-security` 的输入不是工具名，而是待执行的命令行文本。它用 `shell-quote` 做分词（正确处理管道、`&&`、glob、注释），多行命令逐行评估后取最严格的结论，对每个子命令给出三态结论：

- `disabled`：命中 critical 模式。实际判断是组合式的——`mkfs` 系命令；`rm` 配上 `-rf`/`-fr`/任何同时含 r 和 f 的 flag，且路径落在 `/`、`~`、`/usr`、`/etc`、`/bin`、`/sbin` 等危险目标上。
- `allowedWithPermission`：高风险命令，或 `$var` 开头的变量命令（内容不可预判，一律升权）。
- `allowedWithoutPermission`：其余命令按基础策略放行。

一个容易低估的设计：**变量展开会被双重评估**。`shell-quote` 分词遇到空 token 时（往往是 `$VAR` 展开的结果），实现会按"有变量"和"无变量"两种解释各评一遍，再取更严格的一个——防止 `rm $HOME/...` 这类命令借着变量绕过静态检查。

两层的衔接点在 `src/tools/runTerminalCommand.ts`：permissions 系统决定 `Bash` 工具是否可调用，工具执行前再把具体命令交给 `evaluateTerminalCommandSecurity` 评估。工具级放行了，命令级仍可能拦下。

## 六、任务流案例：一次 `cn -p` 调用穿过哪些层

以一条真实的自动化调用为例：

```bash
cn -p "把 README 里的安装命令改成 uv" --allow Read --ask Bash
```

```text
1. src/index.ts 入口
   检测到 -p 走 headless 模式；解析 --allow Read / --ask Bash
   追加进权限策略表（仅次于模式策略）
        │
2. ConfigService 加载配置
   无自定义配置时落到默认模型 slug（anthropic/claude-sonnet-4-6）
   config.yaml 存在时经 packages/config-yaml 的 Zod schema 校验解析
        │
3. 会话循环（src/ 内，SDK 客户端对接模型）
   按 config.models 的 provider 定义路由请求
   core/llm/llms/ 下 62 个 provider 实现覆盖
   OpenAI / Anthropic / Ollama / Gemini / vLLM 等主流形态
        │
4. 模型返回工具调用（CLI 层 src/tools/ 执行）
   BUILT_IN_TOOL_NAMES 列出 17 个 CLI 工具（Read / Write /
   Bash / Search / Subagent …）；core 层另有 core/tools/
   definitions/ 的 20 个共享工具定义
        │
5. 权限检查（src/permissions/）
   Read 按 --allow Read 直接放行；
   Bash 按 --ask Bash 需要用户确认
        │
6. 命令级评估（packages/terminal-security）
   runTerminalCommand 执行前调 evaluateTerminalCommandSecurity：
   shell-quote 分词 → 逐行评估 → 变量展开双解释 → 三态结论
        │
7. 结果落地
   文件编辑经 core/edit/（streamDiffLines 流式应用 diff）
   命令输出回喂模型；模型给出最终答复后，
   headless 模式把文本打到 stdout 退出
```

这条链路解释了"Core 是事实来源"的具体含义：第 3、4、6、7 步对三端完全共享——VS Code 和 JetBrains 换掉的只是入口（IDE 命令而非 argv）与 UI 载体（webview / Swing 而非 Ink）。provider 怎么换，Agent 循环、工具路由、命令安全评估都不感知具体模型。

另外注意 headless 模式与 TUI 模式在默认策略上的分岔（第五节）：同一条 Bash 命令，交互式终端里要确认，进了 CI 就默认放行。把 Continue 放进自动化流水线之前，这个差异值得专门过一遍。

## 七、这个仓库今天还值得读什么

功能上它已经不是选项，但作为"一个跑完完整产品周期的开源 Coding Agent"样本，几块资产仍然有参考价值：

1. **两层安全模型的完整实现。** permissions 的三态 × 五层优先级 × 三模式，加上 terminal-security 的分词评估与变量展开防御，是 Agent 命令执行安全的少见的完整开源参考——两层粒度（工具级/命令级）的分工尤其清楚。
2. **CLI 工程化范式。** contract / unit / e2e / smoke 四套测试配置（`vitest.config.ts`、`vitest.e2e.config.ts`、`smoke-test.mjs`、`vitest.smoke-api.config.ts`）各自对应一种触发环境；`spec/` 目录把设计决策写成短文档；`AGENTS.md` 展示了如何给 AI 编码代理写仓库指引。
3. **多端共享内核的 monorepo 切法。** 业务壳（`extensions/`）+ 共享核（`core/`）+ 原子包（`packages/`）三段清晰，`build:local-deps` 的显式构建顺序可直接抄。
4. **发布基建清单。** `BUILD_DEPENDENCIES.md` 把三个端所有发布密钥列成表——VS Code/Open VSX 的发布 token、JetBrains 的签名证书与 `PUBLISH_TOKEN`、各 npm 包的 semantic-release 凭证、Continue API 的环境变量。给"发布一个多端产品需要哪些凭证"这个问题提供了一份现成答案。
5. **退场姿势本身。** 用 README 承担归档公告、保留可写仓库、发布终版后维护到文档站迁移完毕——对比常见的"直接 archived"或"无声烂尾"，这是一种对 fork 者更友好的收尾。

## 八、采用建议

**只是想找个能用的 Coding Agent：** 不要从 Continue 开始。终版之后没有新功能、没有模型适配更新、没有安全修复，社区 issue 也不再有人处理。同类活跃项目很多，选一个还在演进的。

**在生产环境已经依赖 Continue：** 三端安装物仍在原渠道可下载（npm / Marketplace / Open VSX / JetBrains Marketplace），现有部署不会"明天失效"，但要把"永无更新"当作前提重新评估风险敞口——尤其当你的用法涉及自动执行命令时。长期看，要么 fork 自维护，要么规划迁移。

**想 fork 或参考着搭自己的 Agent：** 按 `BUILD_DEPENDENCIES.md` 备齐密钥；基于 main 末端 commit（2026-07-21 的 `5522c6f4`）切分支；先跑通 `build:local-deps` 再动代码。要接自己公司的认证，改造点在 `extensions/cli/src/auth/`（WorkOS）与 `packages/continue-sdk`，`core/` 里没有认证模块需要绕开。第五节的两层安全模型建议原样保留——terminal-security 的变量展开防御在自研时非常容易漏。

**想研究 Agent 安全设计：** 直接读四个文件——`extensions/cli/spec/permissions.md`、`src/permissions/defaultPolicies.ts`、`packages/terminal-security/src/evaluateTerminalCommandSecurity.ts`、`spec/modes.md`。加起来不到一千行，覆盖了大部分设计决策。

## 九、FAQ 与常见排查

**Q1：`npm i -g @continuedev/cli` 后 `cn` 找不到？**

先确认 npm 全局 bin 目录在 `PATH` 里（`npm config get prefix` 看前缀，bin 在其 `bin/` 子目录）。nvm 用户切换 Node 版本后全局包不跟随，需要重装。更省事的办法是改用官方 `install.sh`，它不依赖 Node 环境。

**Q2：headless 模式跑 Bash 命令没有弹出确认？**

这是默认策略的刻意行为：`defaultPolicies.ts` 里 headless 模式下 `Bash` 与其余工具默认 `allow`。要收紧，用 `--ask Bash`（或 `--exclude Bash`）显式覆盖，别依赖模式记忆。交互式 TUI 里默认是 `ask`，两种环境行为不同。

**Q3：想加一个本地模型（如 vLLM），改哪里？**

多数情况不用改代码。`config.yaml` 的 `models` 数组加一条即可——`core/llm/llms/` 里现成有 `Vllm.ts`、`Ollama.ts` 和 OpenAI 兼容适配（`packages/openai-adapters`），OpenAI 兼容端点直接复用。只有协议不兼容的 provider 才需要在 `core/llm/llms/` 新增一个类（继承基类并实现 `streamChat` / `streamFim`，基类在 `core/llm/index.ts`）。

**Q4：JetBrains 插件还能装吗？**

能。JetBrains Marketplace（插件 ID 22707）和 GitHub Releases 都有终版安装物，官方建议新用户走 CLI。已在 IntelliJ 生态深度使用的可以继续用 v1.0.67，同样永无更新。

**Q5：fork 之后怎么跟上游？**

跟不了——上游已停。基线选定 main 末端 commit（`5522c6f4`，2026-07-21），之后当自己的项目维护。遇到 Bug 只能自己修，或在 fork 网络里找现成修复（GitHub 上已有 5,400+ fork，但活跃度需逐一甄别）。

**Q6：`plan` 模式真的只读吗？**

对文件写工具是真的——`Edit` / `MultiEdit` / `Write` 被 `exclude`。但 `Bash` 在 plan 模式下是 `allow` 的，模型仍然可以执行 shell 命令（源码注释自认 "TODO address bash read only concerns"）。把它当"防误写"而不是"安全沙箱"来用。

---

> 核对基准：仓库结构、权限策略、安全机制引自 2026-10-04 的 main 分支（commit `5522c6f4`）；Stars/Forks/下载量为 2026-10-04 GitHub API 与 JetBrains Marketplace 读数；era 读数（34,210 Stars）取自 Wayback Machine 2026-06-17 快照。该项目已停止维护，使用前请以仓库当前状态为准。
