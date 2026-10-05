---
title: "Browserbase Skills：让 Claude Code 拥有浏览器自动化能力"
date: "2026-05-05T10:03:56+08:00"
lastmod: "2026-09-30T12:00:00+08:00"
slug: browserbase-skills-claude-code-browser-automation-guide
github_repo: "browserbase/skills"
source_key: "gh:browserbase/skills"
band: "review"
gates: ["事实性", "去AI味", "观点依据"]
description: "Browserbase Skills 是 Browserbase 官方的 Agent 技能集，围绕 browse CLI 提供浏览器自动化、反爬与 CAPTCHA 处理、登录态同步、CDP 全量追踪和无服务器部署。本文按 2026 年 9 月的仓库状态拆解其运行模型、18 个技能的分工与采用边界。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Claude Code", "浏览器自动化", "Browserbase", "开源"]
---

# Browserbase Skills：让 Claude Code 拥有浏览器自动化能力

AI agent 操作浏览器，真正卡住任务的往往不是"会不会点按钮"，而是三类工程问题：目标站点有 bot 检测，自动化指纹一眼就被识别；任务需要登录态，而 agent 每次都从干净会话开始；跑挂之后没有证据可查，只能重试碰运气。[Browserbase Skills](https://github.com/browserbase/skills) 的解法是把这三件事交给平台侧——本仓库给 Claude Code 装上一组技能和统一 CLI（`browse`），简单站点走本地 Chrome，有防护的站点切 Browserbase 云端会话，反爬、CAPTCHA、住宅代理、会话持久化都是平台能力。仓库自我定位是 "Browserbase's official collection of agent skills to access the web"。

它的价值取决于你是否需要"protected 站点"这层能力。如果你的目标页面用 `curl` 就能拿到，这套东西是杀鸡用牛刀；如果你要长期维护一批需要登录、有 Cloudflare 防护的自动化任务，它把"每次挂了从零调"变成"有层级地兜底"。

## 快速信息卡

| 项目 | 信息 |
|------|------|
| **Stars** | 3,730（2026-09-30 读数） |
| **Forks** | 240 |
| **许可证** | MIT（各 SKILL.md frontmatter 声明，仓库根无独立 LICENSE 文件） |
| **语言** | JavaScript / TypeScript |
| **仓库创建** | 2025-10-12 |
| **安装** | `npx skills add browserbase/skills`，或 Claude Code 内 `/plugin install browse@browserbase` |
| **仓库** | [browserbase/skills](https://github.com/browserbase/skills) |

## 目录

- [半年三次变形：先对版本，再读功能](#半年三次变形先对版本再读功能)
- [系统地图：18 个技能的六条主线](#系统地图18-个技能的六条主线)
- [browse CLI 运行模型](#browse-cli-运行模型)
- [反爬与登录态：平台能力与 cookie-sync](#反爬与登录态平台能力与-cookie-sync)
- [任务流案例：被拦截的抓取怎么救回来](#任务流案例被拦截的抓取怎么救回来)
- [functions：把重复任务搬出本地](#functions把重复任务搬出本地)
- [ui-test 与 autobrowse：让 agent 自己测试、自己改进](#ui-test-与-autobrowse让-agent-自己测试自己改进)
- [安装与配置](#安装与配置)
- [采用建议：从哪一层进，谁可以不用](#采用建议从哪一层进谁可以不用)
- [常见问题](#常见问题)
- [资料口径说明](#资料口径说明)

## 半年三次变形：先对版本，再读功能

这个仓库半年来结构变化很大，读任何二手资料（包括本文的旧版）之前先对版本。三次关键节点：

| 时间 | 变化 |
|------|------|
| 2026-05-05 | 本文初版发布时，README 宣传 11 个技能，CLI 分两条线：`bb`（`@browserbasehq/cli`）管平台 API，`browse` 管浏览器交互 |
| 2026-05-17 | [#111](https://github.com/browserbase/skills/pull/111) 把两套 CLI 引用统一为 `browse`，npm 包 [browse](https://www.npmjs.com/package/browse)（现为 0.11.0，自述 "Unified Browserbase CLI for browser automation and cloud APIs"） |
| 2026-07-07 | [#142](https://github.com/browserbase/skills/pull/142) 移除已弃用的 browserbase-cli 技能，`bb` 时代结束 |

此后技能集持续扩张：5 月底加入 agent-experience，6 月加入 competitor-analysis、webmcp-gen、browser-use-to-stagehand，8 月加入 optimize-agent-prompt，9 月加入 add-webmcp。到 2026-09-30，`skills/` 目录下共 18 个技能，marketplace 提供 6 个可安装插件（browse、functions、browser-trace、safe-browser、webmcp-gen、add-webmcp）。

还有一个值得单独说的教训：初版 README 表格里列过 `site-debugger` 和 `bb-usage` 两个技能，但对照当时的仓库文件树，`skills/` 目录下从来没有过这两个目录——README 宣传在前、实现从未落地，后来 README 也把这两行撤掉了。读这个仓库时，以 `skills/` 目录的实际内容为准，README 表格只是宣传层。

## 系统地图：18 个技能的六条主线

18 个技能不是平铺的清单，按职责可以分成六组：

| 主线 | 技能 | 职责 |
|------|------|------|
| 驱动浏览器 | browser、autobrowse、safe-browser | 交互自动化、自改进循环、域名白名单受限运行时 |
| 观测与调试 | browser-trace、optimize-agent-prompt | CDP 全量追踪、Agent 提示词迭代优化 |
| 无会话轻量层 | fetch、search | REST API 直接取页面/搜索结果，不占浏览器会话 |
| 平台化与登录态 | functions、cookie-sync | 无服务器部署、本地 Cookie 同步到云端上下文 |
| 业务工作流 | company-research、competitor-analysis、event-prospecting、agent-experience | 用前几层拼装的销售线索研究、竞品分析、大会讲师挖掘、Agent 友好度审计 |
| WebMCP 与迁移 | webmcp-gen、add-webmcp、browser-use-to-stagehand | 给站点生成 WebMCP 工具、从 browser-use 迁移到 Stagehand |

```text
                    Claude Code（自然语言驱动）
                              │
                    browse CLI（npm install -g browse）
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   本地 Chrome           Browserbase 云端        直接 REST API
 （--local /          （--remote：Identity、     （fetch / search，
  --auto-connect）      CAPTCHA、住宅代理）       无浏览器会话）
                              │
                    browser-trace 只读观测
                 （CDP firehose + 截图 + DOM）
```

下面按主线拆开讲。

## browse CLI 运行模型

所有浏览器交互都经过 `browse` 命令（`npm install -g browse`）。理解它有三个要点：守护进程、snapshot 优先、环境用 flag 显式选。

**守护进程模型**。第一条浏览器命令会启动一个 daemon，后续命令复用同一个会话。`browse status` 查看当前状态和已解析的模式，`browse stop` 结束会话——它同时会清除环境覆盖，让下一条命令回到默认判定。

**snapshot 优先于截图**。`browse snapshot` 返回页面的可访问性树，每个元素带 ref（如 `@0-5`），点击、输入都引用这些 ref：

```bash
browse open https://example.com
browse snapshot                        # 页面结构 + 元素 ref
browse click @0-5                      # 按 ref 点击，不是按选择器
browse get title
browse stop
```

`browse screenshot --path <path>` 是慢路径，消耗视觉 token，官方建议只在需要视觉上下文（布局检查、图片、调试）时用。文本提取走 `browse get text <selector>` 或 `browse get markdown`。

**环境选择**。四个 flag 控制浏览器跑在哪：

| flag | 行为 |
|------|------|
| `--local` | 启动干净的隔离本地浏览器，不复用任何已有状态 |
| `--auto-connect` | 附着到本机已在运行的调试态 Chrome，复用其登录态与 Cookie |
| `--remote` | 开 Browserbase 云端会话 |
| `--cdp <port\|url>` | 附着到任意 CDP 目标（本地端口或 WebSocket 地址） |

不显式传 flag 时，设置了 `BROWSERBASE_API_KEY` 就默认云端，否则默认本地。flag 只在会话启动时生效；`browse stop` 之后，下一条命令回落到环境变量自动判定。本地模式失败且症状是 bot 检测或拒绝访问时，官方建议直接切远程。

交互命令还包括 `browse fill <selector> <value>`（需要回车加 `--press-enter`）、`browse type`、`browse select`、`browse upload`、`browse press`、`browse wait <load|selector|timeout>`、`browse tab list/switch/close`，以及独立于 daemon 的 `browse cdp <target>`——它把任意 CDP 目标的事件流以 NDJSON 输出，可按 `--domain Network` 过滤、可管道给 jq。

## 反爬与登录态：平台能力与 cookie-sync

`--remote` 背后是 Browserbase 平台的三层能力，全部在云端会话里生效：

- **CAPTCHA 自动解决**：自动处理 reCAPTCHA 和 hCaptcha（browser 技能的 Mode Comparison 表明确列出本地模式没有这项）。
- **住宅代理**：覆盖 201 个国家，支持地理定位。
- **Browserbase Identity 与 Verified browser**：2026-05-18 引入的机制，用经过验证的浏览器指纹改善受保护站点（如 Google 这类强指纹检测站点）的访问成功率。

什么时候该切远程，SKILL.md 给了明确的信号清单：页面出现 CAPTCHA（reCAPTCHA、hCaptcha、Turnstile）、"Checking your browser..." 拦截页、HTTP 403/429、或者本该有内容的页面渲染成空白。反之，文档站、维基、公开 API、localhost 这些简单目标不值得开远程会话——本地更快，云端稍慢且计费。

**登录态**由 cookie-sync 技能解决。它是一个 Node 脚本（需要 Node.js 22+），从本地 Chrome 导出 Cookie 注入 Browserbase 持久化上下文（persistent context）：

```bash
# 前置：Chrome 需开启远程调试（chrome://flags/#allow-remote-debugging，
# 或以 --remote-debugging-port=9222 启动并设 CDP_URL）
node .claude/skills/cookie-sync/scripts/cookie-sync.mjs --domains x.com,twitter.com
# 输出 Context ID: ctx_abc123

# 用上下文开云端会话，--persist 让会话中的新状态回写上下文
SESSION_JSON="$(browse cloud sessions create --context-id ctx_abc123 --persist --keep-alive)"
CONNECT_URL="$(echo "$SESSION_JSON" | jq -r .connectUrl)"

browse open https://x.com/messages --cdp "$CONNECT_URL"
```

`--domains` 只同步需要的站点（含子域），`--context ctx_xxx` 在 Cookie 过期后向已有上下文重注入而不新建，`--verified` 启用 Identity + Verified browser，`--proxy "San Francisco,CA,US"` 让出口 IP 地理位置贴近本地，避免登录态因 IP 突变被拒。Cookie 一次性同步、上下文跨会话持久，这让定时任务可以不带本地 Chrome 跑：脚本里 `browse cloud sessions create` 挂上下文即可。

成本上这套体系有个天然的阶梯：`search` 和 `fetch` 走 REST API，不产生浏览器会话费用；本地浏览器免费；云端会话按时长与配置计费。官方给的经验法则就按这个阶梯排：能 search 不 fetch，能 fetch 不开浏览器，能本地不远程。

## 任务流案例：被拦截的抓取怎么救回来

把上面的机制串成一次真实排障。假设要让 Claude Code 从一个有 Cloudflare 防护的站点提取数据：

```bash
# 1. 先按默认走本地（未设 BROWSERBASE_API_KEY 时）
browse open https://target-site.com --local
browse snapshot
# 现象：页面空白 / 出现 "Checking your browser..." / HTTP 403

# 2. 命中切远程的官方信号，改走云端（CAPTCHA、住宅代理自动生效）
browse open https://target-site.com --remote
browse snapshot

# 3. 站点还需要登录态：同步 Cookie 到上下文，再开带上下文的云端会话
node .claude/skills/cookie-sync/scripts/cookie-sync.mjs --domains target-site.com
SESSION_JSON="$(browse cloud sessions create --context-id ctx_xxx --persist --keep-alive)"
CONNECT_URL="$(echo "$SESSION_JSON" | jq -r .connectUrl)"
browse open https://target-site.com/dashboard --cdp "$CONNECT_URL"

# 4. 仍然失败：挂只读追踪，复跑一次拿证据
node .claude/skills/browser-trace/scripts/bb-capture.mjs --new my-run
# 复现自动化操作……
node .claude/skills/browser-trace/scripts/stop-capture.mjs my-run
node .claude/skills/browser-trace/scripts/bisect-cdp.mjs my-run
# 在 .o11y/my-run/ 下按 Network / Console / DOM 分桶排查：
# 是 selector 时序问题，还是请求层就被 CAPTCHA 拦下

# 5. 收尾
browse stop
node .claude/skills/browser-trace/scripts/bb-finalize.mjs my-run --release
```

browser-trace 的工作方式值得单独一提：它不给浏览器发任何指令，而是作为第二个只读 CDP 客户端附着到会话上，把完整 DevTools 事件流（firehose）写入 NDJSON，同时以默认 2 秒间隔轮询截图和 DOM dump，结束后按 CDP 方法和页面导航边界切分成可 grep 的分桶文件。用 Playwright、Stagehand 或裸 `browse` 驱动的会话都能挂。有个平台细节容易踩坑：Browserbase 会话在最后一个 CDP 客户端断开时立即结束，所以追踪远端会话要像上面那样用 `--keep-alive` 创建。

## functions：把重复任务搬出本地

browser 技能解决"现在这次怎么做"，functions 解决"以后每次自动做"。它把浏览器自动化部署成 Browserbase 云端的函数，官方描述的场景就是定时任务和 webhook 端点：

```bash
browse functions init my-function     # 生成 index.ts / package.json / .env
cd my-function
echo "BROWSERBASE_API_KEY=$BROWSERBASE_API_KEY" >> .env
pnpm install

browse functions dev index.ts         # 本地开发服务器，默认 127.0.0.1:14113，热重载
```

函数用 TypeScript 写，`defineFn` 定义入口，通过 Playwright 连接平台分配的会话：

```typescript
import { defineFn } from "@browserbasehq/sdk-functions";
import { chromium } from "playwright-core";

defineFn("my-function", async (context) => {
  const { session, params } = context;
  const browser = await chromium.connectOverCDP(session.connectUrl);
  const page = browser.contexts()[0]!.pages()[0]!;
  await page.goto(params.url || "https://example.com");
  return { success: true, title: await page.title() };
});
```

开发期用 curl 打本地服务器模拟调用（`POST http://127.0.0.1:14113/v1/functions/my-function/invoke`，body 传 `{"params": {...}}`），验证后 `browse functions publish index.ts` 部署，拿到 Function ID 用于后续调用。配合 cookie-sync 的持久化上下文，"每天登录态抓一次数据"这类任务可以完全脱离本地机器运行。

## ui-test 与 autobrowse：让 agent 自己测试、自己改进

这两个技能代表另一种思路：不是帮 agent 写自动化，而是让 agent 自己验证和迭代自动化。

**ui-test**（v0.4.0，自 5 月以来基本未变）是对抗式 UI 测试技能，开场第一句就是立场："Your job is to try to break things, not confirm they work"。三种工作流：分析 git diff 只测改动（diff-driven）、全站自主探索找开发者没想到的 bug（exploratory）、把独立测试组分发到多个 Browserbase 浏览器并行跑（parallel）。

它的编排结构是"主 agent 规划、子 agent 执行"：主 agent 先自己完成三轮规划（功能流 → 对抗视角：错误路径、空状态、竞态、边界输入 → 覆盖缺口：axe-core 无障碍、键盘导航、移动视口、console 错误），去重分组后一次性派发子 agent；每个子 agent 带显式步数预算（约 25/40/75 步三档起步），只执行分配到的测试清单，用 `STEP_PASS|<id>|<evidence>` / `STEP_FAIL|<id>|<expected> → <actual>` 结构化断言汇报，失败必须附截图。主 agent 合并成文本报告（如 `Tests: 20 | Passed: 14 | Failed: 4 | Skipped: 2 | Agents: 3 | Pass rate: 70%`）。

要注意的边界：它是交互式技能，官方 SKILL.md 没有提供 CI/CD 集成——想进流水线需要自己封装。

**autobrowse** 是自改进循环：内层 agent 反复执行目标站点的浏览任务（`evaluate.ts`），外层 agent 读 trace 和失败记录，修改导航策略（`strategy.md`），直到任务稳定通过，默认 5 轮迭代，可 `--iterations` 调整。用法形如：

```bash
/autobrowse --task google-flights --iterations 10 --env remote
```

`--browser-trace` 开关让每轮迭代附带 CDP 证据（仅限远程模式），`--env local|remote` 选环境。它和 safe-browser 的分工值得分清：autobrowse 负责"造出一个可靠的技能"，safe-browser 负责"造出一个受限的运行时"——后者生成 Claude Agent SDK 应用，唯一的浏览器工具是 `safe_browser`，通过 CDP Fetch 拦截强制域名白名单，白名单外一律 `Fetch.failRequest`，专门用来演示提示注入遏制和带域名策略的抓取。

## 安装与配置

主流 coding agent 用 npm 方式：

```bash
npx skills add browserbase/skills
```

Claude Code 专用：

```bash
/plugin marketplace add browserbase/skills
/plugin install browse@browserbase
# 重启 Claude Code 生效
```

偏好图形界面的话：`/plugin` → 选 `3. Add marketplace` → 输入 `browserbase/skills` → 选中 `browse` 插件回车安装 → 再按一次回车确认 → 重启。

前置条件按用途分三档：

- **本地模式**：`browse` CLI（`npm install -g browse`）+ 本机 Chrome/Chromium。
- **云端模式**：另需 [BROWSERBASE_API_KEY](https://browserbase.com/settings)。
- **cookie-sync**：Node.js 22+，Chrome 开远程调试。

装完后用自然语言验证，README 给的样例：

> "Go to Hacker News, get the top post comments, and summarize them"
> "QA test http://localhost:3000 and fix any bugs you encounter"
> "Use `browse` to list my Browserbase projects and show the output as JSON"

第三条会走 browse 的平台 API 能力（会话、项目、上下文管理都已并入 browse CLI）。

## 采用建议：从哪一层进，谁可以不用

按任务形态选进入层，别从"全家桶"开始：

1. **只需要页面内容和搜索结果**：不装插件，直接用 Browserbase 的 Fetch/Search API（POST `https://api.browserbase.com/v1/fetch` 与 `/v1/search`，`X-BB-API-Key` 头带 key；fetch 的 `allowRedirects` 默认关闭需要显式开启，search 的 `numResults` 取值 1–25）。
2. **Claude Code 里有反复出现的浏览/测试任务**：装 browse 插件，本地模式起步，遇到 bot 检测按信号清单切远程。
3. **核心诉求是登录态自动化**：cookie-sync + 持久化上下文是这套仓库里最不可替代的部分，`--persist` 的状态回写和 `--context` 的重注入值得先吃透。
4. **有定时抓取/QA 需求**：在 2、3 的基础上加 functions 和 ui-test。

两类团队可以先等等：目标页面全是公开静态内容、纯 HTTP 就能搞定的（成本阶梯的最底层已经覆盖）；以及不允许页面数据经过第三方云端的合规敏感场景——远程模式的页面内容必然流经 Browserbase 会话，这是架构决定的边界，不是配置能绕开的。

另外值得留意 WebMCP 这条支线（webmcp-gen、add-webmcp）：思路是给目标站点生成第一方 MCP 工具（基于站点的路由、表单、schema），让 agent 用结构化工具而不是视觉操作来干活。如果目标站点是自家产品，这可能比反爬对抗更治本。

## 常见问题

**Q：本地模式报 "Chrome not found"？**

安装 Chrome：macOS/Windows 从 [google.com/chrome](https://www.google.com/chrome/)，Linux 用 `sudo apt install google-chrome-stable`。如果本机已有调试态 Chrome，也可以直接 `browse open <url> --auto-connect` 附着。

**Q：守护进程状态异常（"No active page"）？**

SKILL.md 的处理：先 `browse stop` 再 `browse status`；若仍显示 running，`pkill -f "browse.*daemon"` 清掉僵尸进程后重试。

**Q：Cookie 过期了怎么刷新？**

两种情况：刷新本地配置用 README 的办法 `rm -rf .chrome-profile` 后重新登录；刷新云端上下文不用动本地，直接 `cookie-sync.mjs --context ctx_xxx` 向已有上下文重注入。

**Q：用量和费用怎么盯？**

会话用量在 [Browserbase 控制台](https://docs.browserbase.com)查看；控制用量最有效的手段是任务前的分层决策——search/fetch 能解决的不要开浏览器会话。

## 资料口径说明

- 本文按 2026-09-30 的 main 分支核实：18 个技能目录、marketplace 6 插件、npm `browse` 0.11.0；Stars/Forks 为当日 GitHub API 读数。
- 文章初版写于 2026-05-05，当时 CLI 尚为 `bb` 与 `browse` 双轨、README 宣传 11 个技能；本版已按当前结构整体更新。命令形态变化较快（如早期的 `browse env local` 子命令已改为 per-command flag），若与你本机版本不符，以 `browse --help` 和所装技能目录内的 SKILL.md 为准。
- 初版 README 表格中的 site-debugger 与 bb-usage 两个技能在仓库历史上从未有对应实现文件，README 现已撤下这两行，本版正文不再收录。
- 文中命令、flag、端口、错误处理表均逐条对照 `skills/*/SKILL.md` 与仓库 README 原文；引用的外链当日全部可访问。
