---
title: "deepclaude: Claude Code 自主 Agent 循环遇上 DeepSeek V4 Pro"
date: "2026-05-06T11:41:17+08:00"
slug: "deepclaude-claude-code-deepseek-autonomous-agent-guide"
github_repo: "aattaran/deepclaude"
source_key: "gh:aattaran/deepclaude"
description: "把 aattaran/deepclaude 的 10 个文件读尽、拿假上游实跑之后：proxy 里那层兼容处理确实写得细，remote 路径却断在 deepclaude.sh 的一次 head -1 上，而且代理启动后默认还站在 Anthropic 那一边。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "DeepSeek", "AI Agent", "OpenRouter", "API代理"]
lastmod: "2026-09-21T09:26:58+08:00"
---

deepclaude 做的事情很窄：在 Claude Code 成熟的执行框架外面加一层模型请求链路。后端换成 DeepSeek、OpenRouter 或 Fireworks 时，衔接由这层去补。文件编辑、Bash、Git、子智能体（agent）还是原来那套，变化集中在模型请求怎么走。

README 第一行写着 "Same UX, 17x cheaper"。17 倍是它自己那张价目表算出来的：输出单价 15.00 对 0.87 约 17.2 倍，输入侧只有 6.8 倍。但这不是这篇文章的重点。

我的判断有三层。第一层：deepclaude 真正下功夫的地方是本地代理（proxy）里那层兼容处理——路径重叠前缀、鉴权头分派、模型名改写、thinking block 清理、`usage` 补齐。这五项都是长会话才会撞上的东西，一轮问答的演示碰不到。第二层：主打功能 `--remote` 在 main 上有一处硬缺陷，启动脚本从代理那里读回的第一行是日志而不是端口号，于是导出的 base URL 变成一个含空格与箭头的畸形字符串。第三层：即使端口读对，代理启动后仍停在 `anthropic` 模式，模型请求并不像 README 说的那样先去 DeepSeek；控制侧还把端口写死成 3200。前两条在未合并分支里能找到修法，第三条连分支里也还是原样。

下面每条结论都标了出处：源码行号、实跑输出，或者明确写成未验证。

### 两条路径，一张图看清

| 维度 | 命令行工具（CLI）直连 | 远控 + 本地代理 |
|------|----------|---------------------------|
| 启动命令 | `deepclaude` | `deepclaude --remote` |
| 模型请求走向 | 直接打到后端 | 经本地代理，但默认落回 Anthropic 官方端点 |
| 需要的认证 | 后端密钥 | Anthropic OAuth + `claude.ai` 订阅，同时要有一个后端 key |
| 额外依赖 | 无 | Node.js，代理由它启动 |
| 热切换 (`--switch`) | ❌ 无 proxy 可切 | 控制平面在，但目标端口写死 3200 |
| bridge 链路 | 不涉及 | 直连 `wss://bridge.claudeusercontent.com` |

表里是 README 的两条路径。还有第三种用法：绕开启动脚本，手工跑无参 standalone 代理，配方在后文那一节。它不属于 README 的路径划分，却是本文唯一实测过的一种配置——会话看到的端口和 `--switch` 发的端口落在同一个进程上。

## 项目坐标

| 项 | 值 | 来源 |
|------|------|------|
| 许可证 | MIT，版权行 "Copyright (c) 2026 Ali Attaran" | `LICENSE` |
| 星标 / 复刻数 | 2254 / 160 | GitHub API（应用程序接口），2026-09-21 取 |
| 跟踪文件 | 10 个：2 个启动脚本、2 个 proxy JS、3 份文档、3 张截图 | `git ls-files` |
| 依赖声明 | 无 `package.json`、无 lockfile | 同上 |
| Release / tag | 无 | GitHub API |
| 分支 | 5 个，含 main | GitHub API |
| main 最新提交 | `70518b6`，2026-05-04 | `git log` |
| 仓库 `pushed_at` | 2026-07-23，来自 4 个未合并分支 | GitHub API |
| 未关闭 issue / PR | 19 / 13 | GitHub API |

10 个文件意味着这篇文章不存在"读不完的部分"，所以下面的机制描述都是读尽之后写的。

## 目录

- [项目坐标](#项目坐标)
- [核查方法](#核查方法)
- [直连路径实际导出了什么](#直连路径实际导出了什么)
- [remote 路径断在端口握手](#remote-路径断在端口握手)
- [proxy 起来之后，先站在 Anthropic 一边](#proxy-起来之后先站在-anthropic-一边)
- [端口 3200 只是默认值，控制平面却把它当常量](#端口-3200-只是默认值控制平面却把它当常量)
- [standalone 模式：不带参数才能用](#standalone-模式不带参数才能用)
- [proxy 实际补了什么](#proxy-实际补了什么)
- [成本面板该怎么读](#成本面板该怎么读)
- [一次改类型错误，在两条路径下怎么走](#一次改类型错误在两条路径下怎么走)
- [能力的保留与限制](#能力的保留与限制)
- [上手顺序](#上手顺序)
- [常见误区](#常见误区)
- [该不该用，从哪儿开始用](#该不该用从哪儿开始用)
- [五道自测题](#五道自测题)
- [出错时先看哪几处](#出错时先看哪几处)
- [下一步读什么](#下一步读什么)
- [参考资料](#参考资料)

## 核查方法

结论分三种来源，正文里会指明是哪一种：

- **源码**：仓库 10 个文件全量读完，机制描述给到文件与行号。
- **实跑**：本机 Node.js `v26.3.0`。两种台子——把代理的上游指向一个本地假 HTTPS 服务，看它实际收到的请求路径、鉴权头与请求体；以及把一个只打印环境变量的桩脚本放在 `PATH` 前面冒充 `claude`，看启动脚本到底导出了什么。行为类断言一律以实跑为准。
- **未验证**：Windows 侧只有代码，本机没有 `pwsh`，所涉结论都停在"代码这么写"的层面，不宣称运行结果。视觉输入与 MCP 的限制来自 README 的自述，我没有跑通一条真实链路去反证。

## 直连路径实际导出了什么

普通启动路径没有中间层：脚本解析出目标 URL、key 和各档位模型名，`export` 到当前进程，然后 `exec claude`。用桩 `claude` 打印环境，实测拿到的是一份很干净的结果：

```text
ARGS: 
ANTHROPIC_BASE_URL=[https://api.deepseek.com/anthropic]
ANTHROPIC_AUTH_TOKEN=[sk-dsph]
ANTHROPIC_API_KEY=[]
ANTHROPIC_MODEL=[]
OPUS=[deepseek-v4-pro] SONNET=[deepseek-v4-pro] HAIKU=[deepseek-v4-flash]
SUBAGENT=[deepseek-v4-flash] EFFORT=[max]
```

对着 README 那张变量表看，下面四处差异最容易在排查时把人卡在"文档没写"上：

| README 的说法 | 脚本实际做的 | 位置 |
|------|------|------|
| 表里列了 6 个变量 | 还额外导出 `CLAUDE_CODE_EFFORT_LEVEL`，值写死 `max` | `deepclaude.sh:85`、`:217` |
| 没提 `ANTHROPIC_API_KEY` | 非 Anthropic 的直连与 remote 两条路都会 `unset` 它，免得与 `ANTHROPIC_AUTH_TOKEN` 两套鉴权打架；纯 `-b anthropic` 直连那一支反倒没清它 | `deepclaude.sh:218`、`:229`，对照 `:201-204` |
| 只说"设置这些变量" | `-b anthropic` 是反向操作：把上述变量全部 `unset` 后再 `exec claude` | `deepclaude.sh:199-205` |
| 只在 `--help` 的 usage 行露了一次 | 未识别的参数原样透传给 `claude`，实测 `deepclaude.sh --dangerously-skip-permissions -p "hi"` 得到 `ARGS: --dangerously-skip-permissions -p hi` | `deepclaude.sh:29` 的 `break` |

Windows 版在直连路径上多设一个变量：`$env:ANTHROPIC_MODEL = $p.opus`（`deepclaude.ps1:242`），POSIX 版没有这一行。两个脚本的子任务档位是一致的——DeepSeek 走 `deepseek-v4-flash`，OpenRouter 和 Fireworks 的四个档位全部指向同一个 Pro 模型名：

```bash
# deepclaude.sh:53-54（ds）与 :60-61（or）
opus="deepseek-v4-pro"; sonnet="deepseek-v4-pro"
haiku="deepseek-v4-flash"; subagent="deepseek-v4-flash"
# ...
opus="deepseek/deepseek-v4-pro"; sonnet="deepseek/deepseek-v4-pro"
haiku="deepseek/deepseek-v4-pro"; subagent="deepseek/deepseek-v4-pro"
```

所以"子 Agent 用 Flash 还是 Pro"取决于你走哪条路径，不是全局一致的设置。想确认就直接跑一次带桩的输出，或者读这两处赋值。

变量随进程走，不会长期污染环境：POSIX 版 `export` 之后 `exec`，进程换成了 `claude`，原来的 shell 什么都没收到；Windows 版在 `& claude` 返回后逐个 `Remove-Item Env:...`（`deepclaude.ps1:252-256`）。

## remote 路径断在端口握手

`--remote` 是本仓库的招牌功能，README 给的画面是"浏览器里开一个 Claude Code 会话，大脑换成 DeepSeek"。它的前置条件也确实写清了：先 `claude auth login`、要有 `claude.ai` 订阅（bridge 是 Anthropic 的基础设施）、本机有 Node.js 运行时。

问题出在启动脚本与代理之间那根管道。代理监听成功后会往 stdout 打一行日志，`start-proxy.js` 紧接着把端口号也打到同一个 stdout：

```js
// proxy/model-proxy.js:434-437
server.listen(port, '127.0.0.1', () => {
    const actualPort = server.address().port;
    console.log(`[MODEL-PROXY] Listening on 127.0.0.1:${actualPort} → ${targetUrl} (mode: ${state.mode})`);
    resolve({ port: actualPort, close: () => server.close(), switchMode });
});
```

```js
// proxy/start-proxy.js:23-29（legacy 分支，即 deepclaude.sh 走的那条）
    const { port } = await startModelProxy({
        targetUrl,
        apiKey,
        backends: hasBackends ? backends : undefined,
        defaultMode: hasBackends ? undefined : undefined,
    });
    console.log(port);
```

脚本把 stdout 重定向到临时文件，再取第一行当端口：

```bash
# deepclaude.sh:237-240、:254-256
    port_file=$(mktemp)
    node "$SCRIPT_DIR/proxy/start-proxy.js" "$RESOLVED_URL" "$RESOLVED_KEY" > "$port_file" &
# ...
    local proxy_port
    proxy_port=$(head -1 "$port_file")
```

于是 `head -1` 读到的是那行日志。把桩 `claude` 放进 `PATH`、跑一次 `bash deepclaude.sh --remote`，导出的值是：

```text
ARGS: remote-control
ANTHROPIC_BASE_URL=[http://127.0.0.1:[MODEL-PROXY] Listening on 127.0.0.1:3200 → https://api.deepseek.com/anthropic (mode: anthropic)]
ANTHROPIC_AUTH_TOKEN=[]
OPUS=[deepseek-v4-pro] SONNET=[deepseek-v4-pro] HAIKU=[deepseek-v4-flash]
```

脚本自己印出来的那行状态也带着同一个字符串（`Proxy on :[MODEL-PROXY] Listening ...`），说明这不是我的桩造成的假象。这里要说清验证边界：本机用一个只打印环境变量的脚本冒充 `claude`，所以定案的是"导出值是这个畸形字符串"，Claude Code 真身拿到它会报什么错我没有实测。

`deepclaude.ps1:187` 用的是 `Select-Object -First 1` 读同一份重定向输出，写法不同、结果同理，但我没有 Windows 环境实测这一条。

上游清楚这个 bug 在哪。未合并分支 `fix/audit-shared-bugs` 与 `feat/proxy-cherry-pick-jarvis` 的 `deepclaude.sh` 里，取值已经换成"只要纯数字那一行"：

```bash
# fix/audit-shared-bugs 分支的 deepclaude.sh:235
proxy_port=$(grep -oE '^[0-9]+$' "$port_file" 2>/dev/null | head -1 || true)
```

四个分支都还没进 main（`fix/audit-shared-bugs` 领先 4 个提交、`feat/proxy-cherry-pick-jarvis` 领先 12 个）。在 main 上，这一行的替代写法是自己打补丁，或者干脆绕开 `--remote`，用后文的 standalone 配方。

## proxy 起来之后，先站在 Anthropic 一边

这是第二处与 README 不符的地方，而且比端口那处更隐蔽。`--remote` 走的是 legacy 分支，此时环境里必然有 provider key（否则 `resolve_backend` 已经先退出了），`backends` 被注册，而 `defaultMode` 那行 `hasBackends ? undefined : undefined` 两个分支返回同一个值——写了等于没写。于是：

```js
// proxy/model-proxy.js:140-149
const initialName = defaultMode || (backends ? 'anthropic' : null);
const startBackend = initialName && initialName !== 'anthropic' && allBackends[initialName];

const state = {
    mode: initialName || '_single',
    ...
    hadNonAnthropicSession: !!startBackend,
};
```

```js
// proxy/model-proxy.js:273-276
const isAnthropicMode = state.mode === 'anthropic';
const isModelCall = !isAnthropicMode && MODEL_PATHS.includes(urlPath);
const dest = isModelCall ? state.target : new URL(ANTHROPIC_FALLBACK);
```

`mode` 是 `anthropic` 时 `isModelCall` 恒为假，目标端点一律取 `ANTHROPIC_FALLBACK`。实跑印证：按 legacy 方式（两个位置参数）启动时，进程的第一行输出就是 `(mode: anthropic)`，`/_proxy/status` 也回 `{"mode":"anthropic",...}`。

结论要说得比 README 更直白：**`deepclaude --remote` 启动的 proxy 默认把模型请求转给 Anthropic**，你看到的"DeepSeek 大脑"要等到有人 POST 一次 `/_proxy/mode` 才成立。补这一刀的命令是：

```bash
curl -sX POST http://127.0.0.1:3200/_proxy/mode -d "backend=deepseek"
curl -s http://127.0.0.1:3200/_proxy/status
```

前提是代理确实活着、且真的在 3200 上。`--remote` 那条路上 CLI 的 base URL 本身已经被前一个 bug 弄坏了，所以这条命令真正能派上用场的地方是下一节的 standalone 配方。

`feat/proxy-cherry-pick-jarvis` 分支的注释把这条因果写得很清楚。它反向查表得到 `bootName` 再传给 `defaultMode`，理由正是"否则启动会退化成 `_single`，切换、模型名改写、计价、去 key 全部失效"。这份注释本身也说明：main 上那行 `defaultMode` 是个未完成的口子。

`_single` 是第三种模式，也是这套逻辑里最容易踩空的一种。当 legacy 启动时环境里一个后端 key 都没有，`backends` 为空，`mode` 就落到 `_single`。此时请求确实会打给你传入的 `targetUrl`，但两个副作用跟着来：按当前模式查映射表必然落空（**模型名不改写**），计价回退到 `PRICING_PER_M._single`（**Fireworks 也按 DeepSeek 的价钱算**）。`/_proxy/mode` 这时也只剩一个能用的名字：切向 `deepseek` 会因为没有已注册后端报 `Unknown backend`，而 `anthropic` 在查表之前就被单独处理掉（`:190-197`），照样能切。

## 端口 3200 只是默认值，控制平面却把它当常量

proxy 绑不上 3200 时会向后顺延，最多 20 个端口：

```js
// proxy/model-proxy.js:426-433
function tryListen(port) {
    server.once('error', (err) => {
        if (err.code === 'EADDRINUSE' && port < startPort + 20) {
            tryListen(port + 1);
        } else {
            reject(err);
        }
    });
```

实测：先用一个占位服务占住 3200，再启 legacy proxy，它绑到 3201 并如实打印 `Listening on 127.0.0.1:3201`。问题在于控制侧全是硬编码：

```bash
# deepclaude.sh:164（--switch）与 :107（--status 的探测）
resp=$(curl -sX POST http://127.0.0.1:3200/_proxy/mode -d "backend=$backend" 2>/dev/null) || {
proxy_status=$(curl -s http://127.0.0.1:3200/_proxy/status 2>/dev/null) || proxy_status=""
```

3201 上跑着你的 proxy，`--switch` 却往 3200 发请求。那里若空着，你收到 `Proxy not running`；若被别的进程占着（另一个会话的 proxy、或任何恰好监听 3200 的服务），你会把切换指令发给别人。这条不算推测：同一个 `mktemp` 端口文件里读的是真实端口，`--switch` 里读的是字面量 3200，两者只有在"3200 恰好空闲"时才等价。

顺带两个控制平面的边界，都实测过：

- 端口被占而顺延的行为**只在默认 3200 起算**，standalone 的 `--port` 参数在 main 上是死路（下一段解释）。
- `/_proxy/mode` 的 body 上限 1024 字节，超了直接 `clientReq.destroy()`，客户端看到 `ECONNRESET`。非 POST 回 405（`{"error":"Use POST"}`），未知控制路径回 404。`Origin` 那条检查只在看得到它时生效：带 `https://evil.example` 是 403，带 `http://localhost:3000` 放行，而 `curl` 这类不带 `Origin` 的调用直接通过。

## standalone 模式：不带参数才能用

README 只交代了代理会随会话自动起停，`proxy/README.md` 给的则是编程接口（`import { startModelProxy }`）。真正的手工入口藏在 `start-proxy.js` 自己那段位置参数判断里：

```js
// proxy/start-proxy.js:11-14（main）
const targetUrl = process.argv[2] || process.env.CHEAPCLAUDE_TARGET_URL;
const apiKey = process.argv[3] || process.env.CHEAPCLAUDE_API_KEY;

if (targetUrl && apiKey) {
```

`--mode` / `--port` 的解析在 `else` 分支里。所以加上 `--mode deepseek --port 3200` 这组参数启动，`targetUrl` 就成了字符串 `--mode`、`apiKey` 成了 `deepseek`，走进 legacy 分支，然后在 `new URL('--mode')` 上抛 `TypeError: Invalid URL` 直接退出（本机实测，Node.js v26.3.0）。分支 `feat/proxy-cherry-pick-jarvis` 的守卫已经改成 `!targetUrl.startsWith('--')`，注释里写着"flag-style invocations (`--mode` …) must still fall through to standalone"。

不带参数就是可用的 standalone：三个后端从环境变量注册（key 允许为空），固定 3200，`mode` 仍是 `anthropic`：

```text
$ node proxy/start-proxy.js
Proxy on :3200 (mode: anthropic)
Switch: curl -sX POST http://127.0.0.1:3200/_proxy/mode -d backend=deepseek
Status: curl -s http://127.0.0.1:3200/_proxy/status
```

于是绕开 `--remote` 那根坏掉的管道，有了一条能落地的配方：终端 A 跑无参 standalone；另开终端导出 `ANTHROPIC_BASE_URL=http://127.0.0.1:3200` 与四个档位变量，再启动 `claude`。控制平面和命令行看到的端口这时都是 3200，`--switch` 也就不再指错地方。

## proxy 实际补了什么

下面五件事是代理在请求前后做的全部改动。逐条给源码位置与实跑到上游侧的结果。

### 1. 请求路径的重叠前缀

不同 provider 的 base path 不一致：

```text
DeepSeek     启动脚本 https://api.deepseek.com/anthropic    代理注册 同左
OpenRouter   启动脚本 https://openrouter.ai/api             代理注册 https://openrouter.ai/api/v1
Fireworks    启动脚本 https://api.fireworks.ai/inference    代理注册 https://api.fireworks.ai/inference/v1
```

客户端发来的是 `/v1/messages`。直接拼会得到 `https://openrouter.ai/api/v1/v1/messages` 这种地址，所以 proxy 先找 base 与请求路径的最长公共前缀再拼：

```js
// proxy/model-proxy.js:281-291
let fullPath;
if (isModelCall) {
    const base = state.target.pathname.replace(/\/$/, '');
    let overlap = '';
    for (let i = 1; i <= Math.min(base.length, urlPath.length); i++) {
        if (base.endsWith(urlPath.substring(0, i))) overlap = urlPath.substring(0, i);
    }
    fullPath = overlap ? base + urlPath.substring(overlap.length) : base + urlPath;
} else {
    fullPath = clientReq.url;
}
```

假上游侧收到的两条请求行，就是这段逻辑的验收结果：`/anthropic/v1/messages`（无重叠，原样拼）和 `/openrouter/api/v1/messages`（重叠的 `/v1` 被吃掉一个）。

### 2. 鉴权头按 URL 里的关键字分派

```js
// proxy/model-proxy.js:303-311
if (isModelCall) {
    delete headers['authorization'];
    delete headers['x-api-key'];
    if (state.useBearer) {
        headers['authorization'] = `Bearer ${state.apiKey}`;
    } else {
        headers['x-api-key'] = state.apiKey;
    }
}
```

`useBearer` 的判据是 URL 字符串里含 `openrouter` 或 `fireworks`（`:128`、`:136`）。实测两条：DeepSeek 模式的假上游只看到 `x-api-key: sk-ds`、授权头被删干净；OpenRouter 模式只看到 `Bearer sk-or`。

判据是拿 URL 字符串去猜的，没有一处按后端类型声明。我自己的测试里为了让假上游走 Bearer 分支，只要在路径里塞一个 `openrouter` 字样就生效了。反过来，接一个 URL 里两个词都没有的自建网关，代理只会走 `x-api-key` 那一支（`:309`）——它没有地方声明"我这个端点要 Bearer"。

只有被判定为模型调用的请求会替换鉴权头，其余请求原样透传——这正是 remote 模式能保住 bridge 认证的原因：OAuth 的头不动，只有 `/v1/messages` 换了 key。

### 3. 模型名映射是硬编码的

普通直连模式下档位名字由脚本写死（见前文）。proxy 路径再多一层 `MODEL_REMAP`，只在这几个 Anthropic 档位名上生效：

```js
// proxy/model-proxy.js:10-25
const MODEL_REMAP = {
    deepseek: {
        'claude-opus-4-6':    'deepseek-v4-pro',
        'claude-opus-4-7':    'deepseek-v4-pro',
        'claude-sonnet-4-6':  'deepseek-v4-flash',
        'claude-sonnet-4-5-20250929': 'deepseek-v4-flash',
        'claude-haiku-4-5-20251001':  'deepseek-v4-flash',
    },
    openrouter: {
        'claude-opus-4-6':    'deepseek/deepseek-v4-pro',
        'claude-opus-4-7':    'deepseek/deepseek-v4-pro',
        'claude-sonnet-4-6':  'deepseek/deepseek-v4-flash',
        'claude-sonnet-4-5-20250929': 'deepseek/deepseek-v4-flash',
        'claude-haiku-4-5-20251001':  'deepseek/deepseek-v4-flash',
    },
};
```

表里没有 Fireworks，也没有任何别的后端：查不到表就不改写。命中与未命中都实测过。proxy 侧的日志只有命中时才出现：

```text
[MODEL-PROXY] #2 model remap: claude-sonnet-4-6 → deepseek-v4-flash
```

假上游记录到的 `model` 字段分别是 `claude-opus-4-8`（未命中映射表，原样转发）和 `deepseek-v4-flash`（已改写）。

未命中不会报错，`claude-*` 字符串就这样发到 DeepSeek 的兼容端点上。仓库里 issue #39（2026-06-30 提出，仍未关闭）说的正是这件事：映射表过期时，用户以为自己在跑 DeepSeek，实际拿到的是后端对未知模型名的默认处理。这条边界的实操含义是：**Anthropic 出新档位名，deepclaude 不会自动跟上**。要么往表里加一行，要么自己导出档位变量、别让 Anthropic 的档位名出现在请求里（后文 standalone 配方走的就是第二条）。

### 4. thinking block 的三档清理

常见理解是"非 Anthropic 后端不认识 thinking block，发出去前删掉就行"。源码处理得更细，分成三档，而且差别是实测出来的：

| 模式 | 请求里的 thinking block | 上游实际收到 |
| ------ | ------ | ------ |
| Anthropic 模式，进程内还没碰过第三方 | 有签名 1 个、无签名 1 个 | 签名保留、无签名删除 |
| Anthropic 模式，之前切到第三方再切回来 | 有签名 1 个、无签名 1 个 | 两个都删 |
| 第三方模式（deepseek、openrouter、`_single`） | 任意 | 全部删除 |

对应的实现是 `stripUnsignedThinkingBlocks` 与 `stripAllThinkingBlocks`（`model-proxy.js:107-123`），选哪一个由 `hadNonAnthropicSession` 决定。源码注释给出的理由不是"有没有签名"，而是兼容性语义：第三方后端可能生成"带签名但 Anthropic 不认可"的 thinking block。只做半套过滤，切回 Anthropic 时会直接打出 400（`:333-336`）。

注意 `hadNonAnthropicSession` 只会置真、不会复位。代价是：同一个 proxy 进程里只要跑过一次第三方后端，之后所有 Anthropic 请求都会丢掉 thinking 块，包括 Anthropic 自己签过名、本来允许回传的那些。现象我用假上游差分确认过（切回之后签名块确实不见了）。留在桌面上的取舍是：牺牲跨后端会话的推理连续性，换一个不报 400、不用重开会话的请求通路。

### 5. `usage` 补齐，以及一个不补的例外

Claude Code 的词元（token）统计依赖 `usage` 字段。`model-proxy.js:35-38` 的注释写得很具体：DeepSeek/OpenRouter 的部分流式事件可能没有这块字段，缺了会让客户端报 `"$.input_tokens" is undefined`。这是仓库对上游行为的描述，我没有复现原始报错（那需要一个真实的 DeepSeek 流式响应），但补齐动作是实测到的。

流式走 `UsageNormalizer`，按 `\n\n` 分帧，只在缺字段时塞零值：

```js
// proxy/model-proxy.js:65-80
if (d.type === 'message_start' && d.message) {
    if (d.message.usage) {
        this._inputTokens = d.message.usage.input_tokens || 0;
    } else {
        d.message.usage = { input_tokens: 0, output_tokens: 0 };
        changed = true;
    }
}
if (d.type === 'message_delta') {
    if (d.usage) {
        this._outputTokens = d.usage.output_tokens || 0;
    } else {
        d.usage = { output_tokens: 0 };
        changed = true;
    }
}
```

让假上游故意不发 `usage`，客户端拿到的是 `message_start` 里带 `usage:{input_tokens:0,output_tokens:0}`、`message_delta` 里带 `usage:{output_tokens:0}`（补的是零值，不是估算值）。非流式走 `normalizeJsonBody()`，同一次测量里上游原始响应 90 字节、经 proxy 出去变成 135 字节，多出来的正是注入的那段 `usage`。

`MODEL_PATHS` 只有 `['/v1/messages']`，而且是精确匹配，这就留下了一个例外。所有其他路径——包括 `/v1/messages/count_tokens`——无论当前模式是什么，都落回 `api.anthropic.com`。实测在 `deepseek` 模式下请求它，假上游零记录，返回的是 Anthropic 的 `authentication_error`（我这条测试没带凭据）。换句话说，token 预估类请求走的是 Anthropic 那侧，不反映当前后端的分词与计量。我没有去推断 Claude Code 在哪些时机会调它，只把这个边界摆出来。

同一个文件里还留着一个上游自己承认的坑：`proxyReq.on('error')` 只在响应头还没发出去时才写 502（`:416-418`），但 `clientRes.end(...)` 是无条件的（`:419`）。SSE 已经开流、上游中途断掉时，那段 JSON 会被拼进事件流。分支 `fix/audit-shared-bugs` 的提交说明把后果写得很直白：这会污染事件流，"crashes Claude Code's SSE parser"。它的修法是在响应头已发出的分支里直接断开连接，不再补写。main 上仍是旧行为。

## 成本面板该怎么读

`/_proxy/cost` 的输入只有两样：proxy 自己累计的 token 数，和源码里写死的单价表。

```js
// proxy/model-proxy.js:27-33
const PRICING_PER_M = {
    deepseek:   { input: 0.44,  output: 0.87 },
    openrouter: { input: 0.44,  output: 0.87 },
    fireworks:  { input: 1.74,  output: 3.48 },
    anthropic:  { input: 3.00,  output: 15.00 },
    _single:    { input: 0.44,  output: 0.87 },
};
```

跑三条模型请求（假用量累计 2000 输入 / 1000 输出）之后：

```text
{"backends":{"deepseek":{"input_tokens":2000,"output_tokens":1000,"requests":3,"cost":0.0018,"anthropic_equivalent":0.021}},"total_cost":0.0018,"anthropic_equivalent":0.021,"savings":0.0192}
```

这张面板有三条阅读边界，README 没写，但从代码和实测都能定下来：

1. **Anthropic 模式的用量根本不进统计。** `recordUsage` 只在被认定为模型调用时才被调用（`:376`、`:389`），而 anthropic 模式下 `isModelCall` 恒假。实测把三个请求分别放在 anthropic 模式、`count_tokens` 路径和 deepseek 模式下：`/_proxy/status` 的 `requests` 计到 3，`/_proxy/cost` 里只有 1 条。为了让前两条的去向也能被看见，这次把 `ANTHROPIC_FALLBACK` 常量指到本地假服务，分流与计数逻辑没动。所以 `anthropic_equivalent` 是"这些第三方 token 按 Anthropic 单价折算"，不是"这一整场会话本会花多少"。
2. **上游不给 `usage` 时记零。** 补齐动作填的是 0，计费照收这个 0。实测第一轮全零用量的响应就是这种情况：`requests` 会涨，token 不动，面板上"省了多少"自然也跟着失真。
3. **单价是常数，不会跟着报价变。** `deepclaude --cost` 同理，它只是一串 `echo`：表里 DeepSeek `$0.44 / $0.87 / 缓存命中 $0.004`、Anthropic `$3.00 / $15.00 / $0.30`，最后一行 "Monthly estimate (heavy use, 25 days): $30-80" 也是写死的。README 的月度对照（轻度 ~$20、重度 ~$50、自动循环 ~$80，对应省 90%/75%/60%）同样是估算而非测量。真要用它做预算，价格得自己回各家官网核。

## 一次改类型错误，在两条路径下怎么走

举个具体的例子：你在 Python 项目里让 Claude Code "fix the type error in `src/utils.py` line 42"。

**直连路径**：Claude Code 用 Grep 找到文件、Read 读上下文、生成补丁、Bash 跑类型检查，工具循环不动。变的是每一步推理由谁做——主任务落到 `deepseek-v4-pro`，子任务与子 Agent 落到 `deepseek-v4-flash`。请求直接打到 `https://api.deepseek.com/anthropic`，中间没有跳转层。会话随进程结束而结束。

**remote 路径（把三处缺陷都补上之后）**：浏览器里的指令经 `wss://bridge.claudeusercontent.com` 下到本机 CLI，CLI 执行同样的工具循环，`/v1/messages` 先落到本地代理。这条链上代理改动的顺序是：算上游路径（吃掉重叠前缀）→ 判是不是模型调用 → 查 `MODEL_REMAP` 改模型名 → 删 thinking block → 换鉴权头 → 回传时给缺 `usage` 的 SSE 事件补字段。想中途换后端，还要额外确认两件事：CLI 与 `--switch` 指的是同一个端口，且那个端口上的代理已经不在 `anthropic` 模式。

选哪条，取决于你要不要那个控制平面。要热切换和成本面板，就得先把启动脚本的三处缺陷绕过去；不需要，直连这条路今天就是完整的。

## 能力的保留与限制

主体工作流基本没丢。README 列的"Works"清单是它的自述：文件读写与编辑、Bash / PowerShell、Glob / Grep、Git 操作、多步工具循环、子 Agent 派生、`/init`、thinking mode。这份清单我没有一条条跑通去反证，能对照的只有脚本侧——档位变量确实都设了。脚本还把 `CLAUDE_CODE_EFFORT_LEVEL` 固定设成 `max`，但仓库里没有任何一处说明它和 thinking mode 的关系，这个联系是 README 侧的事。跨后端会话里 thinking 块会被前面那套清理吃掉。

受限的部分按来源分开看，别混成一个"降级清单"：

| 能力 | README 的说法 | 这一条我能确认到哪一步 |
| ------ | ------ | ------ |
| 图片 / 视觉输入 | 不支持，DeepSeek 的 Anthropic 兼容端点不接图像 | 仓库自述，我未实测 |
| MCP server 工具 | 兼容层不透传 | 仓库自述；proxy 只分流 `/v1/messages`，其余路径都回 Anthropic，与"MCP 工具走不通"是两件事 |
| 并行工具调用 | DeepSeek 支持（每次最多 128），但 Claude Code 默认仍按顺序发 | 仓库自述 |
| Anthropic 提示词缓存（prompt caching） | DeepSeek 有自己的自动缓存，`cache_control` 被忽略 | 代码里没有任何处理 `cache_control` 的分支，忽略这点成立；缓存收益属仓库自述 |
| token 预估 | 未提及 | 实测：`/v1/messages/count_tokens` 永远落到 Anthropic |

README 还有一句"日常任务八成相当、复杂推理两成 Opus 更强"。这是作者的经验判断，没有任何测量支撑，我原样转述、不加权。

## 上手顺序

按复杂度递增，每步都有可核对的输出：

1. `export` 好 key，跑 `deepclaude --status`。它打印三个 key 的掩码状态（`set (****xxxx)` 或 `MISSING`）和一行 proxy 探测结果，全部是本地字符串，不发模型请求。
2. `deepclaude --cost` 读一遍静态价目表，心里有个"这是常量"的数。
3. 直连跑一次真实任务：小范围重构或一次批量修补，看工具循环与最终 diff 是否可接受。这一步同时验证了 key、端点与档位。
4. 需要热切换或成本面板时，用无参 standalone 起代理（命令见文末清单），确认 `/_proxy/status` 的 `mode`，再决定要不要 `--switch`。**别默认它是 deepseek。**
5. `--remote` 留到你能自己打补丁的时候再上，或者等这三处修复进 main。

## 常见误区

### 1. `claude auth login` 不是所有路径的通用前提

直连靠 provider API key；只有 remote 需要 Anthropic OAuth 和订阅。把两条混在一起，会让两分钟能跑通的场景多出一道登录门槛。

### 2. `--switch` 不启动 proxy，参数也不是 backend 别名

它是发给 `127.0.0.1:3200/_proxy/mode` 的一次 POST，且**写死端口**。CLI 侧会先把 `ds/or/fw` 展开成 `deepseek/openrouter/fireworks` 再发；但你自己 curl 时写 `backend=ds` 会得到 `Unknown backend: ds. Valid: anthropic, deepseek, openrouter, fireworks`（实测）。正则 `/backend=([a-z]+)/` 只认小写，`backend=DeepSeek` 报 `Missing backend= in body`。看到 `Proxy not running` 时，先确认会话是不是压根没挂到 3200。

### 3. `--benchmark` 在 macOS 上跑不完

README 把它写成"跨所有 provider 的延迟测试"。三处与措辞不符：循环体只有 `deepseek openrouter fireworks` 三个，Anthropic 不在内；POSIX 版在第一个后端请求之后就死在计时上；而且每个后端只发一次请求，测的是这一次非流式调用的端到端墙钟时间（`-o /dev/null`、`--max-time 30`），既不是首 token 延迟，也不区分排队与生成。

```text
$ DEEPSEEK_API_KEY=sk-bogus bash deepclaude.sh --benchmark
  Latency Benchmark (1 request each)
  ===================================
deepclaude.sh: line 188: 17899513753N: value too great for base (error token is "17899513753N")
```

根因是 `local start_ms=$(date +%s%3N 2>/dev/null || python3 ...)`（`:182`）：BSD `date` 不认 `%N`，但它**不报错**，而是把 `3N` 原样打印出来（本机 `date +%s%3N` 输出 `17899513513N`，退出码 0）。`||` 后面的 Python 兜底因此永远不触发，走到 `$((end_ms - start_ms))` 当场炸掉。注意这一段的入口条件：三个后端都没 key 时会先打印 `SKIP (no key)`，压根到不了计时那行，所以要复现这个报错得先随便给一个 key。GNU coreutils 的 `date` 支持 `%N`，Linux 上按理走不到这个分支——这一条我只在文档层面确认，没找 Linux 机器实跑。macOS 要么装 `coreutils` 用 `gdate`，要么直接自己 `curl` 一发看 HTTP 状态。

顺带一个真差异：POSIX 版 benchmark 对三个后端统一发 `x-api-key`（`:184`），而 proxy 与 `deepclaude.ps1:131-135` 对 OpenRouter / Fireworks 用 `Bearer` 形式的授权头。同一份"测通路"的脚本，两套鉴权头，别把它的失败当成后端挂了。

### 4. 跨 provider 切换后仍出 400，优先重开会话

proxy 清理的只有 thinking block 这一类，跨 provider 的历史上下文里别的不一致它管不到，而那一层本身就是最脆的。频繁在 Anthropic 与第三方之间来回切、又叠长上下文与多轮工具调用时，重开一次会话通常比硬扛当前上下文省时间。

### 5. 低档位模型在不同模式下不是一套

直连的 DeepSeek 用 `deepseek-v4-flash` 兜子任务，OpenRouter / Fireworks 的直连档位全是 Pro；proxy 的映射表又是第三套（`claude-sonnet-4-6` → flash）。在意子 Agent 跑什么型号，就读那两处赋值，别假设各路径同构。

## 该不该用，从哪儿开始用

把它当"直连换后端"来用，收益是实的：一条 `export` 链路、一份档位映射、一个已经在跑的 proxy 兼容层，你不需要碰 `--remote` 就能把日常编码挪到 DeepSeek 上。这类用法真正的门槛只有一处——映射表是硬编码的，Anthropic 出新档位名时它会先过期。

需要浏览器会话、热切换、成本统计的人，目前得自己动代码，一共三处：`head -1` 换成按纯数字行取值、`defaultMode` 补上反向查表、把控制侧写死的 3200 改成读真实端口。第一处两个分支都改了（`fix/audit-shared-bugs` 的 `deepclaude.sh:235`、`feat/proxy-cherry-pick-jarvis` 的 `:308`）；第二处只有后者改了，前者那份 `start-proxy.js:27` 仍是 `hasBackends ? undefined : undefined`；第三处在两个分支里都还是字面量 3200（`fix/audit-shared-bugs` 的 `deepclaude.sh:111`、`:168`），而同一份脚本的注释已经承认代理会"auto-increments if busy"。这三处都没进 main，所以 remote 目前更适合当待办清单来读，而不是当功能开。

依赖视觉输入、强 MCP、或者错一次代价很高的生产改动，本来就不在这套取舍的射程里。README 的 "17x cheaper" 只对词元输出那一侧成立。代理循环里更贵的是输入侧的重复上下文；DeepSeek 的自动缓存能吃掉多少，要看后端自己，这个仓库插手不了。

## 五道自测题

1. 为什么 proxy 只在 `isModelCall` 为真时才替换鉴权头？如果所有请求都换成 DeepSeek 的 key，remote 模式会先坏在哪一步？
2. `--switch` 的失败信息是 `Proxy not running`，但会话其实挂了 proxy。给出两种能让你看到这句话的真实原因，以及各自的确认命令。
3. 会话切到 `anthropic` 模式之后，`/_proxy/cost` 里为什么不涨？这对"省了多少"这个数字意味着什么？
4. 假设 Anthropic 明天把主力档位名换成 `claude-opus-4-9`。走直连和走 proxy 分别会发生什么？哪一条更隐蔽？
5. BSD `date` 让 `--benchmark` 崩掉，而 `date +%s%3N` 的退出码是 0。`||` 分支的兜底为什么救不了它？

## 出错时先看哪几处

按现象分类，逐条给判据。前两类是"根本没挂上"和"挂上了但模式不对"：

| 现象 | 先查 | 判据 |
| ------ | ------ | ------ |
| 启动 remote 就报 URL 非法 / 立刻退出 | `cat` 那个 `mktemp` 端口文件 | 第一行是 `[MODEL-PROXY] Listening ...` 就是命中端口 bug |
| 会话在跑，token 却按 Anthropic 计 | `curl -s 127.0.0.1:<port>/_proxy/status` | `mode: anthropic` 说明还没切 |
| `--switch` 说 Proxy not running，但 proxy 活着 | 比对实际端口与 3200 | 顺延过端口就会指错 |
| 后端回未知模型名 | proxy 日志有没有 `model remap` 行 | 没这行就是未命中映射表 |
| 切换后端后 400 | 是否跨 provider 的历史 thinking block | 重开会话比清理更快 |
| 上游连不上 | proxy 返回的 502 与 `Upstream connection error` | `model-proxy.js:413-420`，HTTP 502 带 JSON |

## 下一步读什么

- `proxy/model-proxy.js:210-276`：控制平面与分流判定都在这里，前面几节的每个结论最终都落回这两段。
- `deepclaude.sh:198-267`：两条启动路径的差别，端口取值那一刀的现场；控制侧写死的 3200 则在 `:107` 与 `:164`。
- 未合并分支 `fix/audit-shared-bugs` 与 `feat/proxy-cherry-pick-jarvis` 的 diff：能看清作者打算怎么修端口、`--mode` 守卫和 SSE 中途错误。
- issue #39：映射表过期时的静默误路由，是这类兼容层的通用失效模式。

## 参考资料

- [deepclaude 仓库](https://github.com/aattaran/deepclaude)（main `70518b6`，2026-05-04）
- [README](https://github.com/aattaran/deepclaude/blob/main/README.md) 与 [proxy/README](https://github.com/aattaran/deepclaude/blob/main/proxy/README.md)
- [deepclaude.sh](https://github.com/aattaran/deepclaude/blob/main/deepclaude.sh)、[deepclaude.ps1](https://github.com/aattaran/deepclaude/blob/main/deepclaude.ps1)
- [proxy/model-proxy.js](https://github.com/aattaran/deepclaude/blob/main/proxy/model-proxy.js)、[proxy/start-proxy.js](https://github.com/aattaran/deepclaude/blob/main/proxy/start-proxy.js)
- [issue #39：未命中的模型名被原样转发](https://github.com/aattaran/deepclaude/issues/39)
- [fix/audit-shared-bugs 分支的 deepclaude.sh](https://github.com/aattaran/deepclaude/blob/fix/audit-shared-bugs/deepclaude.sh)（端口取值修法）

复核用的命令，按文章顺序：

```bash
git clone https://github.com/aattaran/deepclaude.git && cd deepclaude
node --version                       # 本机 v26.3.0
bash deepclaude.sh --cost            # 静态价目表
DEEPSEEK_API_KEY=sk-bogus bash deepclaude.sh --benchmark   # 需要一个 key 才不进 SKIP 分支
date +%s%3N                          # 输出形如 17899513513N，退出码 0
node proxy/start-proxy.js https://api.deepseek.com/anthropic sk-x | head -1
                                     # 第一行是日志，不是端口
node proxy/start-proxy.js --mode deepseek   # TypeError: Invalid URL
node proxy/start-proxy.js            # 无参 standalone 才走到 --mode/--port 解析
curl -s http://127.0.0.1:3200/_proxy/status
curl -sX POST http://127.0.0.1:3200/_proxy/mode -d "backend=ds"
                                     # Unknown backend: ds（CLI 会先展开别名）
```

维护说明：本文的核对基线是 `main` 的 `70518b6`（提交于 2026-05-04），核对时间 2026-09-21。重看时优先复查五处。一是那三处缺陷是否已经进 main，尤其是 `--switch`/`--status` 里的字面量 3200，它在两个未合并分支里都还没动。二是 `MODEL_REMAP` 有没有补进新的 Anthropic 档位名，issue #39 关闭与否是一个直接信号。三是价目表：README、`deepclaude.sh` 的 `show_cost` 与 `PRICING_PER_M` 三处必须一致，而真实报价来自各家官网，不在本仓库的掌控内。四是那些平台性结论，`date +%s%3N` 的行为只在 BSD 与 GNU 之间成立，换 shell 或换 coreutils 后要重测。五是星标、复刻、issue 与 PR 数都是快照值，只当时间戳用，不当论据。
