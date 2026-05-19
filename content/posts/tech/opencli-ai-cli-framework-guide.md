---
title: "OpenCLI：把 Agent 的工具入口收成一棵命令树"
date: "2026-05-17T09:10:00+08:00"
lastmod: "2026-05-19T18:20:00+08:00"
slug: "opencli-ai-agent-browser-cli-framework"
description: "OpenCLI 把站点适配器、登录态浏览器、Electron 应用和本地 CLI 收进同一棵命令树。理解它，要先看命令优先、Browser Bridge、三层会话模型，以及哪些场景其实不该用它。"
summary: "OpenCLI 不只是 browser 子命令。更顺的用法是先查适配器命令，缺口再退到 browser 原语；用 profile、browser session、siteSession 分别处理身份、流程和站点页生命周期；重复出现的流程，再沉淀成 adapter、plugin 或 external CLI。"
draft: false
categories: ["技术笔记"]
tags: ["OpenCLI", "AI Agent", "CLI", "Browser Bridge", "浏览器自动化", "Electron"]
---

<!-- markdownlint-disable-file MD003 MD041 -->

OpenCLI 常被归到浏览器自动化工具里。这个归类抓住了 `opencli browser`，却漏掉了更值得看的部分：站点适配器、登录态浏览器、Electron 应用和本地 CLI，被放进同一棵命令树；使用顺序也被重新排好，先找稳定命令，命令不够再退到浏览器原语。

它和 Playwright 的分工也在这里拉开。Playwright 擅长测试、断言、隔离环境和可重复的浏览器脚本；OpenCLI 处理的是另一类问题：真实登录态里已经能做的事，怎样变成一条人和 Agent 都能调用的命令。前者把浏览器当测试运行时，后者把浏览器、桌面应用和本地二进制工具收进同一个调用面。

把 OpenCLI 放进工具链前，与其背浏览器子命令，不如先看 4 个问题：这件事有没有现成适配器命令？什么时候才退到 `browser` 原语？`--profile`、`browser <session>`、`siteSession` 三层状态各管什么？它和官方 API、Playwright、外部 CLI 的职责边界在哪里？

下面的命令和行为，以 2026 年 5 月 19 日可见的 `v1.7.22` 包元数据、README、Browser Bridge、Troubleshooting、Extending OpenCLI、`opencli-browser` skill 和相关文档交叉核对为准。OpenCLI 迭代很快，README、中文文档和 skill 文档里已经能看到少量新旧写法并存；遇到这种地方，文中会直接指出。

## 先看系统地图

OpenCLI 收拢的是工具入口和调用顺序，底层协议并不只有一种。

| 你面对的能力 | 首选入口 | 保留的状态 | 更适合谁 |
| --- | --- | --- | --- |
| 已有站点命令 | `opencli <site> <command>` | 命令 schema、输出列、退出码 | 人和 Agent |
| 临时网页操作或站点缺口 | `opencli browser <session> ...` | 命名 browser session、tab lease、当前目标页 | Agent，也适合调试 |
| 本机已有命令行工具 | `opencli gh ...`、`opencli docker ...`、`opencli external register ...` | 原生 stdio、原生退出码、统一发现面 | 人和 Agent |
| Electron / 桌面应用 | `opencli cursor ...`、`opencli codex ...` | CDP 目标、桌面应用当前状态 | 人和 Agent |

这张表最该看的，是“首选入口”。OpenCLI 的推荐顺序是先找现成命令，命令缺口才退到浏览器，再把反复出现的浏览器流程收敛成新命令。顺序错了，它会被用成一组脆弱的网页脚本；顺序对了，它就是一个命令运行面。

## 命令优先，是核心设计

OpenCLI 把“命令发现”做成了运行时可查询的注册表，而不是藏在 README 里的功能清单。对 Agent 来说，差别很实际：先枚举，再调用，少靠猜。

第一次安装时，先确认 Node.js，再装 CLI 和 Browser Bridge。这里已经有一个版本边界：`v1.7.22` 的 `package.json` 写的是 `engines.node >=20.0.0`，但 README 和中文 README 仍有“Node.js >=21”的旧表述。遇到这种快速迭代项目，别只盯一份文档；包元数据、当前 CLI 帮助和 release note 更可靠。

```bash
node --version
npm install -g @jackwener/opencli
opencli doctor
```

多 Chrome profile 共存时，尽早给 profile 起别名：

```bash
opencli profile list
opencli profile rename <contextId> work
opencli profile use work
opencli --profile work browser work state
```

如果你本机的 `opencli browser --help` 显示的是 `--session <name>` 写法，同一条探测命令应改成：

```bash
opencli --profile work browser --session work state
```

这一步不是整理洁癖，而是避免 OpenCLI 在工作号、个人号、测试号之间替你猜。Agent 一旦拿错 profile，后面的 selector、cookie、页面上下文都会变得像“偶发失效”。

接下来先看命令面：

```bash
opencli list
opencli list -f json
opencli hackernews top --limit 5 -f json
```

`opencli list -f json` 返回的是机器可读的命令注册表。对浏览器型适配器，通常能看到 `strategy`、`browser`、`columns`、`domain` 这类字段。一个典型条目大致是这样的：

```json
{
  "command": "1688/assets",
  "strategy": "cookie",
  "browser": true,
  "columns": ["offer_id", "title", "main_count", "sku_count", "detail_count", "video_count"],
  "domain": "www.1688.com"
}
```

命令一旦存在，认证方式、页面依赖、输出字段和失败形态已经被适配器作者收敛过。拿到的结果不再是“Agent 点完页面后的临时截图”，而是一份能进脚本、能接后续 Agent 的结构化输出。

公开命令里也能看到这个差异。`opencli hackernews top --limit 3 -f json` 直接返回结构化行数据：

```json
{
  "rank": 1,
  "id": 48175820,
  "title": "Why bambu_networking violates the AGPL in Bambu Studio",
  "score": 43,
  "author": "marcosscriven",
  "comments": 13
}
```

稳定字段、统一格式、Unix 风格退出码，才是自动化链路需要的东西。浏览器脚本也能拿数据，但每次都从 DOM、截图和选择器开始，Agent 的工作会停留在一次性操作层，很难变成团队里的公共工具。

## 三层状态模型

OpenCLI 的状态不止一层。`--profile`、`browser <session>` 和 `siteSession` 名字相近，管的却是 3 件不同的事。

| 概念 | 你在命令里看到什么 | 它决定什么 | 常见误解 |
| --- | --- | --- | --- |
| Browser profile | `--profile work`、`OPENCLI_PROFILE=work` | 这条命令路由到哪个 Chrome 身份 | 把它当成浏览器流程名 |
| Browser session | `opencli browser inbox ...` | 多步 browser 原语复用哪条 tab lease 和默认目标页 | 以为它等于某个站点账号 |
| Adapter `siteSession` | `--site-session persistent` / `ephemeral` | 浏览器型适配器沿用稳定站点 tab，还是每次开一次性 tab | 以为它就是通用 browser session |

我会这样记：`--profile` 管“哪个 Chrome 身份”，`browser <session>` 管“一段浏览器流程”，`siteSession` 管“浏览器型适配器是否延续同一站点页”。

### `browser <session>`：给多步浏览器流程命名

`opencli browser *` 命令需要显式 session，但近期资料里同时出现了两种写法。中文 README 和 `opencli-browser` skill 的一些段落使用位置参数：

```bash
opencli browser work open https://example.com
opencli browser work state
opencli browser work extract "main"
```

英文 README 和部分搜索索引里还能看到 `--session <name>`：

```bash
opencli browser --session work open https://example.com
opencli browser --session work state
opencli browser --session work extract "main"
```

这是文档漂移，不是概念差异。写教程或脚本时，以当前 CLI 帮助和本机 `opencli browser --help` 为准。下面统一采用位置参数写法，同时把这处漂移留下来，方便读者在版本切换时核对。

OpenCLI 自己创建的 owned session 会保留 tab lease，直到你显式 `opencli browser work close` 或等空闲清理。它适合一段需要连续上下文的临时网页工作，比如打开页面、读取状态、点击、再读取状态。

另一个常见误判来自 `tab new`。它只创建新 tab，不会自动变成后续命令的默认目标；要改变默认目标，需要 `tab select <targetId>`。漏掉这一步，后续命令看起来像“跑错页”，实际是 session 仍指向旧目标。

### `bind`：把已经打开的真实标签页借给 session

登录、SSO、验证码、复杂跳转已经由人手工完成时，重新让 OpenCLI 开一页并不划算。`bind` 做的事很简单：把当前真实 tab 显式交给某个 session：

```bash
opencli browser gmail bind
opencli browser gmail state
opencli browser gmail click "Search"
opencli browser gmail unbind
```

`bind` 并不复制用户 tab，它只是把已有 tab 作为当前 session 的操作对象。bound session 不拥有用户窗口，不会替你关闭用户 tab，也没有 owned session 的空闲自动关闭计时器；绑定会一直持续到 `unbind`、tab 关闭、窗口关闭或 daemon 重启。

它的边界也很直白：页面内导航和操作可以做，`tab new`、`tab select`、`tab close` 这类会改 tab 生命周期的动作会被阻止。借来的 tab 不该被工具擅自管理。

### `siteSession`：适配器是一次性页，还是持续站点页

浏览器型适配器和 `browser <session>` 的默认策略不同。普通 browser session 给交互流程复用；浏览器型适配器默认更接近一次性执行，命令结束后释放后台 adapter tab lease。只有需要连续上下文的交互式站点命令，才会声明 `siteSession: 'persistent'`。

这类命令常见于 ChatGPT Web、Claude Web、Gemini、Grok、Doubao 等对话型站点。Doubao 文档说得很直接：连续 `doubao ask`、`doubao read`、`doubao detail` 会默认延续同一个 Doubao 页面，也可以通过 `--site-session ephemeral` 改成一次性 tab。

于是会出现一个看似奇怪的现象：某些命令连续执行会自然留在同一个对话页，另一些命令每次像重新打开。差别来自会话策略，不是产品行为“飘”。

## Browser Bridge 的边界

Browser Bridge 常被概括成 CLI 和浏览器之间的桥。这个说法方向对，但太粗。网页路径实际上包含几层：

```text
opencli --profile work browser inbox open <url>
        │
        ├─ --profile work：选择哪个 Chrome 身份
        └─ browser inbox：选择哪条交互式 browser session

CLI
  -> 本地 micro-daemon
  -> Browser Bridge extension
  -> 当前 tab / 绑定 tab / OpenCLI 拥有的 tab lease
```

这条链路带来 4 个工程后果。

第一，登录态留在浏览器里。不必把 cookie 手工抄进 CLI 配置，也不必为了消费级网页流程去伪造一套并不存在的服务端认证。

第二，多 profile 是一等场景。`--profile` 和 `OPENCLI_PROFILE` 把“这次命令到底使用哪个 Chrome 身份”变成显式输入。

第三，页面所有权被区分出来。OpenCLI 自己创建的 owned session、手工打开后再绑定的 bound session、浏览器型 adapter 使用的后台窗口，生命周期和权限都不一样。

第四，扩展权限各有明确用途。`debugger` 用来向目标 tab 发送 CDP 命令，`tabs` / `tabGroups` 管 automation container 和 tab 元数据，`cookies` 服务 cookie-backed adapter，`downloads` 则让 `opencli browser wait download` 能感知 Chrome 下载生命周期，而不是盲等文件系统。

桌面应用适配器走的是另一条路径。Cursor、Codex、ChatGPT App 这类 Electron 应用更接近通过 CDP 连接桌面目标，不走 Browser Bridge 扩展。OpenCLI 收拢的是上层命令树，底层 transport 可以不同。

## 一次任务怎样从网页动作沉淀成命令

只看静态结构，很容易把 OpenCLI 读成“能开浏览器的 CLI”。看一条任务怎么流过系统，更接近它的设计意图。

假设目标是“检查工作账号里的小红书通知，并把结果交给后续 Agent 处理”。我会按这个顺序走：

```text
先找现成命令
  -> 命令有缺口时退到 browser 原语
  -> 确认流程会重复发生
  -> 沉淀成 user adapter / plugin / external CLI
```

第一步，直接找站点命令：

```bash
opencli xiaohongshu notifications -f json
```

如果这一步已经拿到所需字段，任务到这里就结束。留下来的是结构化输出，而不是一次页面演示。

第二步，命令缺一个细节时再退到 browser 层。例如你只想看某个筛选条件下的未读通知：

```bash
opencli --profile work browser xhs-inbox open https://www.xiaohongshu.com/
opencli --profile work browser xhs-inbox state
opencli --profile work browser xhs-inbox click ".notification-entry"
opencli --profile work browser xhs-inbox extract ".notification-item"
```

这里的 browser 原语负责探索和补洞：定位页面、确认字段、观察网络请求。长期运行的自动化不适合一直停在这一层。

第三步，流程开始重复后，把它写回命令面：

```bash
opencli browser init xiaohongshu/unread-notices
opencli browser verify xiaohongshu/unread-notices
opencli xiaohongshu unread-notices
```

到这一步，浏览器自动化仍然存在，但它已经变成 adapter 生成过程的一部分；最后留下的是一条可以被别人发现、复查和复用的命令。

扩展路径可以按维护方式来选：

| 需求 | 更合适的路径 |
| --- | --- |
| 只在本机快速写一个命令 | `~/.opencli/clis/<site>/<command>.js` 的 user adapter |
| 要放进 Git、长期维护或共享 | plugin |
| 要改官方 adapter 的本地行为 | `opencli adapter eject <site>` / `opencli adapter reset <site>` |
| 只是把已有二进制纳入发现面 | `opencli external register <name>` |

浏览器动作是中间态，命令才是长期形态。用 OpenCLI 时，最好一直记着这条线。

## 排障先看边界

OpenCLI 的常见坑，多半落在状态、页面上下文和文档漂移上，未必是 parser 或桥接层出了问题。

### `opencli doctor` 只证明 Browser Bridge 基本连通

`opencli doctor` 主要检查 daemon、扩展、Chrome profile 连通性，以及一条真实浏览器探测。它不会替所有 adapter、plugin、external CLI 背书。

因此，`doctor` 不绿，`opencli list`、`opencli hackernews top`、`opencli gh pr list` 这类命令仍可能正常运行；反过来，`doctor` 绿，也不能说明某个 browser-backed adapter 已经读到当前页面上下文。

### 空数据和权限错误，优先查身份与页面上下文

browser-backed adapter 出现空数据、`Unauthorized`，或者“页面开着却读不到上下文”时，先查 4 件事：

1. 命令是否路由到了正确的 Chrome profile。
2. 目标站点是否已经在这个 profile 里登录。
3. 当前 tab 是否落在 adapter 预期的 host / page context 上。
4. 登录态、同意弹窗、地理限制、风控页是否挡住了真实页面。

以 `1688 item` 这类命令为例，页面已经打开，不等于商品上下文可读。目标页过宽、host 不对、详情页没有进入商品上下文，都会让失败看起来像“桥接坏了”，实际问题却在页面定位。

### 文档漂移时，以包元数据、CLI 帮助和源码为准

这次核对里，至少有 3 个漂移点容易误导读者。

第一，Node.js 版本。`v1.7.22` 的 `package.json` 是 `>=20.0.0`，Troubleshooting 文档也写 `Node.js >=20`；README 和中文 README 仍写 `>=21`。写教程时要把它标成文档漂移，不能把其中一个页面当唯一真相。

第二，browser session 写法。近期资料里同时出现 `opencli browser <session> ...` 和 `opencli browser --session <name> ...`。脚本以当前 CLI 帮助为准；文章里可以解释漂移，但同一组命令不要混用两种风格。

第三，External CLI 注册入口。当前管理入口是：

```bash
opencli external register my-tool
```

调用入口仍在根命令树里：

```bash
opencli gh pr list
opencli docker ps
opencli longbridge quote TSLA.US
```

注册在 `external` 下，执行在根命令树下。这个区别看起来小，写错后读者会直接走到不存在的命令路径。

## 适用边界

判断 OpenCLI 时，先看它该不该出现在这条链路里。

| 任务类型 | 更合适的工具 | 判断理由 |
| --- | --- | --- |
| 官方 API 完整、服务端认证清晰 | API / SDK | 少一层浏览器状态，更轻、更稳 |
| 端到端测试、断言、隔离回归 | Playwright | 测试语义、断言模型、隔离环境更成熟 |
| 需要复用真实网页登录态 | OpenCLI | 不必外搬 cookie，也不必重写认证流程 |
| 需要把消费级网页能力沉淀成命令 | OpenCLI | 先 browser 探索，后 adapter 固化 |
| 想统一调用本地 CLI、网站和桌面应用 | OpenCLI | 同一命令树对人和 Agent 都更友好 |

面对官方 API、后端服务账户和 CI 回归测试时，OpenCLI 通常不是最经济的第一层。问题落在消费级网站、真人登录态、桌面客户端、高频但缺少官方接口的操作上，它的优势才会明显。

## 更稳的采用顺序

团队里落地 OpenCLI，可以按下面顺序推进：

1. 先跑 `opencli list`，确认能力是否已经存在。
2. 涉及浏览器型命令时，再跑 `opencli doctor`、`opencli profile list`、`opencli profile use <name>`。
3. 适配器没有覆盖时，使用 `opencli browser <session> ...` 做临时探索、字段定位和页面校准。
4. 某个流程开始重复，就升格为 user adapter、plugin 或 external CLI。
5. 写入文档或自动化脚本前，用 `opencli <command> --help` 和当前包元数据复核命令写法。

这套顺序把 OpenCLI 放在运行面的位置，而不是把它当一组网页点击命令。它收拢的是能力被发现、被调用、被验证、被沉淀的路径。

## 结语

OpenCLI 把登录态网页、桌面应用、本地 CLI 放回一棵确定性的命令树里。对 Agent 来说，这意味着少猜测、少临时脚本、少一次性 DOM 操作；对人来说，同样的能力不用在 API、桌面端和网页之间来回换交互模型。

需要测试隔离、回归断言或官方 API 编排时，它不该排在第一层。需要处理真实会话、消费级网站、桌面客户端，以及高频但难以接口化的操作时，OpenCLI 补上的正是那层命令面。

## 参考资料

- [OpenCLI GitHub 仓库](https://github.com/jackwener/OpenCLI)
- [OpenCLI package.json](https://raw.githubusercontent.com/jackwener/opencli/main/package.json)
- [README 中文版](https://github.com/jackwener/OpenCLI/blob/main/README.zh-CN.md)
- [Getting Started](https://opencli.info/docs/guide/getting-started.html)
- [Browser Bridge 设置指南](https://opencli.info/docs/guide/browser-bridge.html)
- [Extending OpenCLI](https://opencli.info/docs/guide/extending-opencli.html)
- [Troubleshooting](https://opencli.info/docs/guide/troubleshooting.html)
- [opencli-browser skill](https://github.com/jackwener/opencli/blob/main/skills/opencli-browser/SKILL.md)
- [Doubao adapter 文档](https://opencli.info/docs/adapters/browser/doubao.html)
- [Chrome Web Store 扩展页](https://chromewebstore.google.com/detail/opencli/ildkmabpimmkaediidaifkhjpohdnifk)
