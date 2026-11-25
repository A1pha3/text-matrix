---
title: "magpie：把 90 个 AI agent 客户端的模型配置，收进一个本地网关"
date: "2026-11-25T13:34:32+08:00"
slug: "yetone-magpie-local-gateway-agent-model-routing"
description: "magpie 是一个 Go 写的本地 LLM 网关，用 127.0.0.1:3425 把 Claude Code、Codex 等 90 个 agent 的模型配置收进一处，做协议互译与多账号故障转移。本文拆解它的接线层、路由引擎与插件运行时。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "LLM 网关", "Go", "模型路由"]
github_repo: "yetone/magpie"
source_key: "gh:yetone/magpie"
---

## 核心判断

每个 AI 编程工具都把模型配置存在自己的文件里，用自己的格式，带自己的 Key 和 base URL。你为 Claude Code 买的订阅，在 Codex 里用不了；反过来也一样。于是产生了今天这种局面：模型能力在涨，工具在分裂，而每个工具都在问同一个问题——「我该用哪个模型」。

magpie（[yetone/magpie](https://github.com/yetone/magpie)）的答案分两步：

**第一步是接线。** 它不要求 agent 支持某种新协议，而是去改 agent 自己的配置文件——`~/.claude/settings.json`、`~/.codex/config.toml`、`opencode.jsonc`、`config.yaml`——把 endpoint 指向 `http://127.0.0.1:3425`，把模型名换掉。改的时候只动那一个 key，注释、缩进、字段顺序全部保留。

**第二步是网关。** 本地这个 `127.0.0.1:3425` 同时说 OpenAI Chat、OpenAI Responses、Anthropic Messages 和 Gemini 四种协议，在中间做互译——流式、工具调用、思考块一并翻译。Claude Code 以为自己在跟 Anthropic 说话，底下其实可能是 DeepSeek；Codex 以为自己在跟 OpenAI 说话，底下可能是 Kimi。

真正把「换模型」变成「换供应商」的，是第三层：**多账号与路由组**。同一个 provider 的多个 Key、同一个模型的多个中转站、乃至不同厂商的同一档模型，可以组成一个组，配一条路由策略。配额耗尽时请求落到下一个账号，agent 看不见那个错误。

需要说清楚的边界：**这不是一个模型聚合站，也不是新的前端**。它跑在你自己机器上，管的是「请求该发给谁」，不生产模型，也不托管别人的 Key。仓库自己的判断是：「如果你只用一个 agent、用它自己厂商的套餐且额度够用，你不需要它。」

截至 2026 年 11 月 25 日，这个仓库有 41155 stars、3769 forks，Go 为主，MIT 许可，2026 年 9 月 23 日创建。仓库树里有 11009 个文件，其中 6990 个是 Go 文件，`internal/` 下有 105 个子目录——绝大多数是 9 月以来写出来的。

## 系统地图：三层结构

理解 magpie 的关键是分清三层，它们的职责边界互不重叠。

| 层 | 干什么 | 代码位置 |
|---|---|---|
| 接线层（agent wiring） | 改每个 agent 自己的配置文件，把 endpoint 和模型指到网关；断开时按原样还原 | `internal/agent/`（714 个 Go 文件，基本一个 agent 一个文件） |
| 网关层（gateway） | 接请求 → 找候选 → 翻译协议 → 转发 → 计费记账 | `internal/gateway/`（1816 个 Go 文件）、`internal/provider/`（1069 个）、`internal/routes/`（13 个） |
| 插件层（plugin runtime） | 可插拔的中间件、路由策略、页面、观察点 | `internal/pluginrt/`、`plugins/`、`internal/middleware/` |

再叠一层是**目录（catalog）**：magpie 不硬编码模型列表，而是拿 Key 去问厂商「你有哪些模型」，再用 [models.dev](https://models.dev) 补上上下文长度、推理档位这些厂商自己不说清楚的字段。厂商没列的模型，仍以厂商的拼写为准。

`docs/subsystems/` 下的 18 篇子系统文档是这个项目少见的优点：每个子系统都有一张「职责与事实来源」表，把每个判断钉到具体文件和具体函数名上。这在开源项目里不常见，也是本文下面几个结论能查到出处的根本原因。

## 接线层：改配置，而不是接管 agent

magpie 最保守也最关键的设计，是**不要求 agent 支持任何东西**。它只做一件事：找到 agent 的配置文件，改一个字段。

仓库的 `docs/subsystems/agent-wiring.md` 给出了一个清晰的抽象：每个 agent 是一个 `Agent` 结构体，带 `Path`（配置在哪）、`Fields`（哪些字段可改）、`Native`（哪些字段是 agent 原生的、不是 magpie 塞进去的）。`Field` 有三个方法：`Get`、`Set`、`Options`——`Set("")` 表示把这个字段还原成 agent 自己的默认值，同时把 magpie 的接线撤掉。

这带来几个具体后果：

**改写是原子的，且不破坏原格式。** `settings.json` 里的注释、`config.toml` 里的字段顺序、YAML 的缩进风格，改完还在。

**magpie 记得自己改过什么。** `applied.json` 记录每次写入，另有 `stash.json` 存改动前的原值。所以「断开」不是猜——它把原值放回去，而不是重新推导一个默认值。

**用户手改过的配置会被识别为 drift。** `Drift` 有五个状态：`unwired`（没接线）、`replaced`（被别的程序改掉了）、`unreachable`（网关地址变了）、`proxied`（走了代理）、`bypassed`（绕过了网关）。

**magpie 写的每一行都带撤销说明。** 源码里 `edit.Mark` 给写入 TOML、YAML、env 的每行上方加一条 `# magpie:` 注释，写明怎么还原。即使配置文件被留下，读者也知道那不是用户写的。

`Own` 字段是这套设计里最细致的部分。Claude Code 的 `permission_mode` 归用户所有：magpie 不写它、profile 不保存它、断开时不碰它，「Take it out」只删 magpie 自己写的部分——但因为它从来没写过，所以实际效果是用户的设置原样保留。同一批文件里，magpie 自己的模型字段则相反：断开就还原。

**支持 90 个 agent 客户端**，包括 Claude Code、Codex、Gemini CLI、OpenCode、Cursor CLI、Copilot CLI、Cline、Goose、Zed、JetBrains 系，以及中文工具链里的 Qoder、Kimi Code、OpenClaw 等——也包括 Cherry Studio、AstrBot 这类不专做编程的客户端。magpie 只显示本机装了的那些。它自己还给 OpenClaw 打了招呼——所以这个网关和 OpenClaw 可以并存，不冲突。

## 路由引擎：候选、顺序、失败转移

这一层是 magpie 真正的技术含量所在。`docs/subsystems/gateway-routing.md` 有 800 多 KB，一行一行都是规则。

### 模型解析有六层优先级

一次请求进来，模型名要先被解析成「谁服务它」。顺序大致是：

1. **Claude 分层占位**（tier stand-in）——Claude Code 发来的 `claude-haiku-…` 可能要落到具体某个模型
2. **路由组**——用户自己建的组，或 magpie 自动发现的组
3. **自动占位**（auto stand-in）——比如 Codex 的 `codex-auto-review`
4. **agent 自己的占位**——比如 Codex 的 `config.toml` 里写的 `model`
5. **裸模型 id**——用户手写的
6. **provider 解析**——最终按 provider 列表顺序找第一个能服务的

第 5 层和第 6 层之间有一条值得注意的规则：magpie 往 agent 配置里写的**永远是 `provider/model` 形式**，裸 id 只在用户手写时出现。这解决了「同一个模型名被多个 provider 服务」时的歧义。

### 自动发现的组

magpie 会自己建组。多个 provider 都提供 `glm-5.3-flash` 时，它建一个 `auto/glm-5.3-flash` 组，把这些 provider 都塞进去。这个组的 id 用 `models.dev` 给这个拼写的「规范拼写」——不管成员们自己用的是 `glm-5-3-flash`、带日期的 id 还是 `glm-5.3-flash`，组的 id 都是前者，不受 provider 加入顺序影响。而组的**名字**是另一个选择：`models.dev` 给这个拼写的名字，厂商自己的名字，都没有就用拼写本身。所以会看到 id 是 `auto/glm-5.3-flash`、名字却是 `glm-5-3-flash` 的组。

组会自己消失：如果其中一个 provider 被删，或它不再提供这个模型，这个组就没了。这时 magpie 的 `AutoStandIn` 机制接管——**同一个模型、绝不换模型**，只是换一个还服务它的 provider。用户自己建的组不享受这个待遇。

### 路由策略是一个可注册的接口

内置的路由策略共 12 种，其中 9 种可用于 provider，3 种只能用于组：

| 策略 | 排序依据 | 可用于 |
|---|---|---|
| smart（空串，即 Quota first，默认） | 配额剩得多的优先 | provider / 组 |
| order | 列表顺序 | provider / 组 |
| rotate | 轮换 | provider / 组 |
| usage | 用得少的优先（半衰期 `usageHalfLife` 默认 1 小时） | provider / 组 |
| pace | 按配额消耗速率 | provider / 组 |
| weight | 平滑加权轮询 | provider / 组 |
| free | 免费的先用（依据模型实际花费） | provider / 组 |
| fast | 速度优先（近期首字延迟 + 输出速率） | provider / 组 |
| drain | 一直用一个直到用完再换 | provider / 组 |
| cheap | 价格优先 | 仅组 |
| expiring | 先用快过期的免费额度 | 仅组 |
| fit | 小上下文优先 | 仅组 |

`cheap`、`expiring`、`fit` 只能用在组上，不能用在单个 provider 上——因为一个 provider 的所有 Key 付的是同一个价、共享同一套上下文窗口，只有把多个 provider 放进一个池子里，这三个维度才有意义。这条限制是逻辑自洽的，不是随意加的。

`fast` 的实现值得一看：它维护一个衰减的移动平均（半衰期 20 分钟），记录每个候选的首字延迟（TTFT）和输出速率（每秒 token）。关键细节是——**没测过的候选不会被饿死**：一个池子里既有测过的也有没测过的，每五个请求里有一个给没测过的（代码里叫 `probes`）。

`free` 也有个前提：只有当策略自己声明了「按免费排序」（`routes.Strategy.ByFree`）才会去读模型列表，否则一个池子路由到别的策略时根本不会关心模型贵不贵。

### 失败转移的边界

仓库在这一点上写得非常明确，也是这个项目少有的地方：

> 「链接在输出任何正文之前失败会被整段丢弃，切换对调用方不可见。」

也就是说，一旦上游已经吐出了第一个字节，失败就不再转移——响应已经开始了，硬切会让 agent 拿到半截 JSON。这是协议层的硬约束，不是实现偷懒。

配套的是几组限流：每个 Key/账号有并发上限（`MaxConcurrency`）、每分钟请求上限（`MaxRPM`）、排队长度和排队时间上限。超了返回 429 和 `Retry-After`。

等待中的请求不绑定在最初的候选上——只要有别的候选腾出位置，等待者会换过去。仓库的测试里有一条专门覆盖这个：「等待中的请求会坐到退回来的账号上」。

### 谁能被识别成谁

这一节读起来像技术日志，但恰恰暴露了真实世界的复杂度。magpie 需要从请求里判断「这是谁发来的」，依据包括：路径里的 agent 名、token 形式（`magpie-<agent>`）、User-Agent、乃至某些 agent 的原生会话头。

有几个案例：

- **VS Code 的 Agents 窗口**跑 `codex app-server`，User-Agent 是 `vscode_agent_host`，所以算 VS Code 的请求；但它的 turn 又是 Codex 形状的，所以 Codex 的规则对它生效
- **Claude Code 跑在 OpenMausBot 里**，User-Agent 是 Claude Code 的，但算 OpenMausBot 的；「对 Claude Code 的分层与 helper 调用」仍然是 Claude Code 的
- **omp** 发 Claude Code 的头，它自己的 system prompt 第一行又写着「You are omp's trusted coding assistant.」，magpie 两边都看，判定为 omp
- **Codex 的 Claude Code 插件**（`/codex:rescue`）用 `clientInfo "Claude Code"` 启动 `codex app-server`，靠 `x-codex-window-id` 区分

这些不是炫技，是同一个请求在现实里可能以很多身份出现，判错身份会导致计费、限流、模型替换全错位。

## 插件层：P0 到 P6 的扩展点

magpie 把「大多数人用不到的部分」做成可关掉的插件。`docs/subsystems/plugin-runtime.md` 定义了一个分阶段的扩展模型：

| 阶段 | 扩展点 | 例子 |
|---|---|---|
| P0 | 插件注册与生命周期 | 内置插件的开关 |
| P1 | 窗口内核 | Gateway 页面作为第一个自己画页面的插件 |
| P2 | 整页搬出核心 | Sessions、Library、Routing、Usage |
| P3 | 网关扩展点 | 观察者（OTel）、路由策略、中间件、工具、预算 |
| P4 | 社区插件挂在 P3 各点 | — |
| P5 | 社区面板 | 插件贡献页面到 magpie 自己的页面里 |
| P6 | provider / agent 行菜单里的插件项 | — |

插件的边界由测试守着：`TestPluginsImportOnlyCore` 保证 `plugins/` 以外的包不会 import 插件，插件之间也不互相 import——它们只能通过服务（`Provide` / `Service`）通信。

生命周期是 `off → pending → active → failed → disposed`。一个插件失败不影响其他插件；它注册过的东西会被撤销。

**中间件跑在 Go 进程里的 JavaScript 引擎上**（moejs）。原因是它要挂在每一个请求和每一个流式事件上，所以必须快。中间件可以改请求、也可以改回复，还能注册自己的路由策略。

## 一个请求的完整旅程

假设你在 Claude Code 里让它跑一个重构。

**第一步：接线。** 你在 magpie 里选了 `deepseek/deepseek-v4-pro` 作为 Claude Code 的模型。magpie 改 `~/.claude/settings.json` 里的 `model` 字段和 base URL，在上面留 `# magpie:` 注释，并把原值存进 `stash.json`。

**第二步：请求到达。** Claude Code 发一个 Anthropic Messages 请求到 `127.0.0.1:3425`，token 是 `magpie-claude`（每个 agent 一个）。

**第三步：认身份。** 网关看路径、token、User-Agent，判定这是 Claude Code。如果是 Windows 上的 WSL 发行版里的 Claude Code，还多一层 `wsl-` 密钥和网卡地址判断。

**第四步：解析模型。** 请求里的模型 id 可能是 `claude-sonnet-…`。magpie 依次尝试：是不是 Claude 分层占位？是不是某个组？是不是 Codex 那样的 agent 占位？最后落到裸 id 解析。

**第五步：找候选。** 如果命中了 `auto/deepseek-v4-pro` 这个自动组，候选就是所有提供这个模型的 provider，按组的路由策略排序。每个 provider 下面还有它的 Key 和账号，再按 provider 自己的策略排。

**第六步：协议翻译。** 候选是 OpenAI 兼容的 DeepSeek，但请求是 Anthropic Messages 格式。magpie 把 messages 转成 chat 格式、把 `thinking` 块转成 `reasoning_content`、把工具 schema 对齐，上游回的是 SSE，转回 Anthropic 的事件格式。

**第七步：流式转发。** 上游开始吐字节。一旦吐了，失败就不再转移——这是协议的硬边界。

**第八步：记账。** 响应头写回 `X-Magpie-Provider` 和 `X-Magpie-Model`，用量进 `usage` 表，路由页上能看到这次请求走了哪条路、试过谁、为什么落到这个候选。

**第九步：模型变更后的同步。** 你把模型换成 Kimi 之后，magpie 要把新模型写进 Codex 的配置，同时更新 Codex 那份模型列表。仓库在这里踩过一个坑并做了修正：Codex 的列表条目是每小时向 ChatGPT 后端问一次的，而以前只要模型列表内容有变就重写整个文件，结果逼得用户一天重开好几次 app——现在只写真正变了的字段。

## 这个项目适合谁，不适合谁

README 的自我定位是诚实的：

> 「如果你用超过一个 agent、超过一个 provider，或超过一个账号，它就是给你的。如果你只用一个 agent、用它自己厂商的套餐且额度够用，你不需要它。」

具体一点：

**值得考虑的场合**——你同时用 Claude Code 和 Codex，且手里有不止一家厂商的额度；你想在不改 agent 配置的前提下随时切模型做对比；你的订阅经常在关键任务中途撞墙；你需要在 WSL、Windows、macOS 之间让同一套 agent 配置保持一致。

**可以不考虑的场合**——你只用一个 agent 且额度充足；你要求请求绝不出本机（magpie 会把请求转发给上游厂商，这是它的工作方式）；你在意「agent 配置文件的每一个字节都由我自己控制」。

**需要额外留意的两点**：

一是**签名账号的发现**。magpie 默认会读 Claude Code 和 Codex 的登录态文件、系统钥匙串，把你已登录的订阅变成可用的 provider。可以在 Settings → Privacy 关掉，或用 `MAGPIE_NO_ACCOUNTS=1` 单次关闭。

二是**隐私遮蔽默认关闭**。Settings → Privacy 里打开后，Key、密码、邮箱会在请求离开本机前被遮蔽，回复里再还原。这是 magpie 自己加的一层，和上游厂商的数据处理政策是两回事——遮蔽了不代表上游不记录。

## 跑起来要做什么

如果你只想试，步骤很短：

```sh
# 装（macOS / Linux / Windows）
curl -fsSL https://usemagpie.ai/install.sh | sh
```

macOS 的构建包是签名并公证过的，每个 release 文件都带 GitHub Actions 的构建证明（`gh attestation verify <file> -R yetone/magpie-releases`），且每次构建都会自动更新自己。Linux 上没有 WebKitGTK 4.1 会先装它；没有桌面环境或没有终端可交互时，会改装终端版并告诉你缺哪个包。Nix 用户可以 `nix profile install github:yetone/magpie-releases`（终端版用 `#magpie-cli`），也可以直接 `go install github.com/yetone/magpie@latest`，或用 Docker 镜像。

装完三步：

1. **加一个 provider** —— 打开 magpie 进 Providers → Add provider，选个预设粘 Key，或者直接用已登录的订阅
2. **给每个 agent 选模型** —— 在 Agents 页面上选，开个新会话就生效
3. **（可选）确认网关活着** —— `magpie quota` 看各个套餐还剩多少

全命令行也行：

```sh
magpie provider add deepseek sk-…              # 预设只需一个 key
magpie claude deepseek/deepseek-v4-pro          # Claude Code 跑在 DeepSeek 上
magpie codex moonshot/kimi-k2.5                 # Codex 跑在 Kimi 上
magpie group add "Opus anywhere" models=claude/claude-opus-5-5,copilot/claude-opus-5.5 routing=smart
magpie claude group/opus-anywhere               # 在订阅之间做故障转移
magpie save work && magpie use work             # profile：一键切回一套配置
magpie quota                                    # 每个套餐还剩多少
magpie tui                                      # 全套功能开在终端里
```

不用 magpie 也能接：任何能接受 base URL 的客户端，指向本机网关就行。

```sh
export OPENAI_BASE_URL=http://127.0.0.1:3425/v1     OPENAI_API_KEY=magpie
export ANTHROPIC_BASE_URL=http://127.0.0.1:3425     ANTHROPIC_API_KEY=magpie
export GOOGLE_GEMINI_BASE_URL=http://127.0.0.1:3425 GEMINI_API_KEY=magpie
```

## 维护节奏：一个值得注意的信号

magpie 的发布节奏快得不像一个两个月大的项目：写作时点的最新版本是 v0.1.4779，而往前几个小时还有 v0.1.4778、v0.1.4777、v0.1.4776——**一天能发好几个版本**。版本号本身也是信号：v0.1.x 还在 0.1，没有进 1.0。

这意味着两件事。

一是**迭代极快**，上周读到的某个配置项或路由行为，这个月可能已经变了。文档里大量引用具体函数名（`AutoStandIn`、`provider.GoneAutoGroup`、`rests.json`），读的时候要意识到它们对应的是一个每天都在动的代码库。

二是**接口还没有冻结**。0.1 的版本号和这种发版频率叠在一起，意思基本就是「接口会变」。要依赖它，把 magpie 当成一个自己会升级的依赖，而不是一个稳定的底层设施。

## 排查：按现象定位

| 现象 | 先查这里 |
|---|---|
| 改了模型，agent 还是用旧的 | Codex 的模型列表每小时向后台问一次，且只写真正变了的字段；先确认改的是 magpie 管理的那个 Codex 配置 |
| 请求返回 404 且提示 `unknownModel` | 模型拼写对不上，或它原本所在的自动组已经消失（某个 provider 被删、或不再提供该模型） |
| 列表里看不到某个 agent | magpie 只显示本机已安装的；先确认可执行文件在 PATH 上，Windows 下还要在注册表卸载项里能查到 |
| WSL 里的 agent 连不上 | NAT 网络下要用 magpie 的 WSL 密钥（`wsl-` 开头，0600）；桥接网络下要填 Windows 在桥接网卡上的地址 |
| 配额耗尽后没有自动切换 | 只有一个账号且没建组时，错误会直接到 agent；需要一个组或同 provider 的第二个账号 |
| 遮蔽密钥没生效 | Settings → Privacy 里的遮蔽默认关闭，需要手动打开 |
| 想让 agent 恢复原状 | 用 magpie 的断开 / 卸载，而不是手删配置文件——手删会让 Codex 的 base_url 指向一个不存在的网关，每轮 502 |
| 写的中间件没跑起来 | 中间件要先在 `plugins.json` 里启用，`middleware` 插件开着才会加载 |
| 某个插件加载失败 | 失败状态是 `failed`，只影响它自己；其余插件照常工作，看 Plugins 页的加载错误 |
| 卸载后 agent 全挂 | `magpie uninstall` 会先断开每个 agent、还原配置，再删文件；手删文件夹跳过了这一步 |

## 参考

- 仓库：<https://github.com/yetone/magpie>
- 官方站点与文档：<https://usemagpie.ai>
- 子系统文档（本文引用的规则主要出处）：仓库 `docs/subsystems/` 下 18 篇
- 模型元数据目录：<https://models.dev>
- 本仓库其它相关文章：`new-api`（把多个 LLM API 收进一个网关）和 `9router`（给 AI 编程工具套一层免费用量的路由）——前者是服务端计费网关，后者是单点中转，与本文的「本地网关 + 改 agent 配置 + 多账号路由」是三件不同的事
