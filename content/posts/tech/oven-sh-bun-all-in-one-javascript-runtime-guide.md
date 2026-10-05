---
title: "Bun 三重变奏：被 Anthropic 收购、重写为 Rust、成为 Claude Code 的底座"
slug: oven-sh-bun-all-in-one-javascript-runtime-guide
github_repo: "oven-sh/bun"
source_key: "gh:oven-sh/bun"
date: 2026-07-12T02:58:14+08:00
lastmod: 2026-09-28T00:00:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["Bun", "Node.js", "Rust", "性能优化"]
description: "Bun 把 runtime、包管理器、bundler、test runner 压进一个二进制。2025 年底被 Anthropic 收购，2026 年年中用 11 天把 53.5 万行 Zig 重写为约 78 万行 Rust，v1.4 起成为 Claude Code 的运行底座。本文拆解重写动机、JavaScriptCore 的去留、文本 lockfile 与性能数字的读法。"
---

# Bun 三重变奏：被 Anthropic 收购、重写为 Rust、成为 Claude Code 的底座

面向在 Node.js 生态里做技术选型的工程师：写服务端、配 CI、管依赖，或者在给 agent 产品挑基础设施。前置知识：知道 Node.js 和 npm 怎么用，听说过 TypeScript 需要转译。

读完本文能说清：Bun 靠什么从「更快的 Node.js」变成 Anthropic 的基础设施；为什么 53 万行 Zig 值得推倒重写；`bun.lock` 取代 `bun.lockb` 换来了什么；官方性能数字里哪些能信、哪些不能直接推出；你的项目该现在试还是再等等。

## 目录

1. 一句话判断
2. 项目速览
3. 系统地图
4. 为什么从 Zig 重写为 Rust
5. JavaScriptCore 为什么留下
6. bun install：文本 lockfile 时代
7. 内置 TypeScript 与 test runner
8. v1.4 的内置库策略
9. 性能数字怎么读
10. 适用边界
11. 决策建议
12. 常见问题
13. 自测题
14. 参考与口径说明

## 一、一句话判断

Bun 起家的卖点是「快」：一个用 Zig 写的 JavaScript 运行时，把 runtime、包管理器、bundler、test runner 压进一个可执行文件，替代 `node` + `npm` + `tsx` + `webpack` + `jest` 这条五件套流水线。到 2026 年，它的故事换成了三层，每一层都比「快」更值得注意：

1. **2025 年 12 月，Anthropic 收购 Bun**，把它用作 Claude Code 和 Claude Agent SDK 的运行底座。一个开源运行时被顶级 AI 实验室选作 agent 基础设施，这是对它工程质量的背书。
2. **2026 年 5 月，整个代码库从 Zig 重写为 Rust**：11 天，6,502 个 commit，53.5 万行 Zig 换成约 78 万行 Rust。重写的主力是 Claude——这本身成了「AI 写基础设施软件」的第一个大规模公开案例。
3. **v1.4 起内建一批原 npm 依赖的替代品**（图像处理、无头浏览器、定时任务），all-in-one 的思路从工具链扩展到了常用库。

三层叠加之后，评估 Bun 的问题从「它比 Node.js 快多少」变成了「agent 时代的基础设施长什么样」。下面逐层拆。

## 二、项目速览

| 维度 | 数据 |
|------|------|
| 仓库 | [oven-sh/bun](https://github.com/oven-sh/bun) |
| Stars / Forks | 96,064 / 5,070（2026-09-28，GitHub API） |
| 语言构成 | Rust 约 66%、C++ 约 19%、TypeScript 约 10%（按仓库字节数） |
| 最新版本 | v1.4.2（2026-09-05 发布） |
| 所属 | Anthropic（2025-12-02 官宣加入） |
| 许可证 | 本体 MIT；静态链接的 JavaScriptCore 为 LGPL-2 |
| 主页 | [bun.com](https://bun.com) |

两个数字值得停下来看。语言构成里已经没有 Zig——2026 年 5 月之前它还是主力语言。Stars 增速没有因为重写和收购放缓，说明社区对这两个大动作投了信任票。

## 三、系统地图

```text
┌──────────────────────────────────────────────────────────┐
│                        bun CLI                           │
├──────────────┬──────────────┬───────────────┬────────────┤
│  bun run     │  bun install │  bun test     │  bun build │
│  (执行脚本)   │  (包管理器)   │  (测试,Jest   │  (打包 +   │
│              │              │   兼容 API)   │   转译器)   │
├──────────────┴──────────────┴───────────────┴────────────┤
│              Bun 运行时(约 78 万行 Rust,约 100 个 crate)  │
├───────────────────────┬──────────────────────────────────┤
│  JavaScriptCore       │  Node 兼容层 + Web 标准           │
│  (C++ 静态链接,       │  (fetch / WebSocket /            │
│   LGPL-2)             │   ReadableStream / node:http…)   │
├───────────────────────┴──────────────────────────────────┤
│  v1.4 内置库:Bun.Image / Bun.WebView / Bun.cron /        │
│  Bun.markdown / Bun.Terminal(PTY) 等                     │
└──────────────────────────────────────────────────────────┘
```

读这张图先抓一个比例：Rust 约占仓库代码的 66%，剩下约 19% 是 C++，嵌着 JavaScriptCore、uWebSockets、BoringSSL、SQLite 这些成熟库。「重写为 Rust」没有把 C++ 依赖一并换掉——重写的是 Bun 自己的那部分代码。

## 四、为什么从 Zig 重写为 Rust

这是 2026 年 JS 工具链里最值得研究的一次重写，官方在《Rewriting Bun in Rust》里把动机讲得很直白：**大多数 bug 是内存管理错误**。

### 4.1 病根：GC 与手动内存管理的接缝

Bun 的宿主语言是 JavaScript（由 JavaScriptCore 托管，带垃圾回收），实现语言 Zig 是手动内存管理。两种内存模型之间有一条接缝，Zig 又没有析构函数（Rust 的 `Drop` 那种机制），资源释放只能靠 `defer` 在每个调用点手工写。use-after-free、double-free、漏释放，都是这条接缝上的典型事故。

官方尝试过补丁版 Zig 加 ASAN、全天候 Fuzzilli 模糊测试、自造智能指针，都不够——自造智能指针「人体工学不如 Rust，还没有 Rust 的保证」。Jarred Sumner 的结论是一句可以印在 T 恤上的话：**"Compiler errors are a better feedback loop than a style guide."**（编译器报错是比风格指南更好的反馈回路。）所有权检查挪进编译期之后，整类错误从「线上炸了再查」变成「编译不过就改」。

### 4.2 过程：11 天，64 个 Claude 并行

重写的时间线：

| 时间 | 事件 |
|------|------|
| 2021-04-16 | Sumner 写下第一行 Zig（Bun 最初是 esbuild 从 Go 到 Zig 的逐行移植） |
| 2025-12-02 | Anthropic 官宣收购 |
| 2026-05-03 → 05-14 | Rust 重写完成：11 天，6,502 个 commit |
| 2026-07-08 | 官方博客发布；v1.3.14 定为最后一个 Zig 版本 |
| 2026-08-20 | v1.4.0 发布，首个 Rust 版本 |

规模与成本，官方数字：原代码库 535,496 行 Zig、1,448 个文件；迁移产出约 100 万行（含重写），其中约 78 万行 Rust、约 100 个 crate。执行方式是约 50 个动态工作流，峰值 64 个 Claude 实例并行（4 个 worktree，每个 16 个），峰值速度约 1,300 行/分钟，每行代码过两道对抗性审查 agent。API 账单约 16.5 万美元。作者估算，三个熟悉代码库的工程师人工做要一年。

质量验证的底线是保守的：**零个测试被跳过或删除**，三个平台各约 100 万个 `expect()` 断言全部通过；已知引入 19 个回归，发布前全部修复。Sumner 的总结是 "barely anyone noticed. Boring is good."——重写的最高评价就是没人察觉。

### 4.3 结果：泄漏清零，二进制变小

对照 v1.3.14 与 v1.4.0：

- **内存**：可测量的泄漏全部修复。`Bun.build()` 循环 2,000 次的压测里，旧版内存一路涨到 6,745 MB，新版稳定在 609 MB。
- **体积**：Linux 二进制从 88 MB 降到 70 MB（约小 20%），Windows 从 94 MB 降到 76 MB。
- **速度**：整体提升 2%–5%，来自 Rust/C++ 跨语言链接时优化。速度不是这次重写的目标——保住性能不回退本身就是硬指标。

对使用者的含义：接缝类 bug 的修复速度会持续变快。这类 bug 过去依赖维护者逐个排查，现在编译器直接拦下一部分。

## 五、JavaScriptCore 为什么留下

重写动了实现语言，没动 JS 引擎。Bun 至今内嵌 JavaScriptCore（WebKit 的 JS 引擎），V8 从未进入选项。综合官方多年的说明，理由有三：

1. **冷启动快**。JSC 的启动路径比 V8 短，对 CLI 频繁冷启动的场景（`bun run xxx.ts`）收益直接。Bun 至今保持高频跟进 WebKit 上游——仓库里隔三差五出现 "Upgrade WebKit to xxx" 的提交。
2. **常驻内存低**。V8 的分层优化（hidden class、inline cache）为长时间运行的网页调校；serverless 和 CLI 这类短命进程用不上多少，JSC 的常驻开销更小。
3. **嵌入接口清爽**。JSC 是 C++ 库，Bun 用自己的 C++ 绑定层对接，Rust 侧通过 FFI 调用。这部分边界代码占仓库约 19%（C++），连同一个事实一起写在 LICENSE.md 里：JavaScriptCore 是 LGPL-2，Bun 以静态链接方式分发并按 LGPL 要求提供重链接指引。

代价照旧：极少数依赖 V8 内部特性的原生扩展无法工作。Bun 只支持走 N-API 的原生模块——这是 Node 官方的跨引擎 ABI，不碰 V8 私有接口。选型时如果你的依赖里有老的 `node-gyp` 模块，需要逐个确认。

## 六、bun install：文本 lockfile 时代

`bun install` 的速度来自三件事：并行解析与下载、全局内容寻址缓存（下载过的包全机器只存一份，项目里链接复用）、以及 lockfile 的高效读写。第三件事在 1.2 版本发生了一次方向反转，值得单独讲。

### 6.1 从 bun.lockb 到 bun.lock

Bun 早期用二进制 lockfile（`bun.lockb`）换解析速度，1.2 起改为默认生成文本格式 `bun.lock`（JSONC：支持注释和尾逗号）。官方列的二进制格式痛点都很实际：GitHub 上看不了 diff、合并冲突没法手工解、Dependabot 这类工具解析不了。换文本格式后 `bun install` 反而比 1.1 快了 30%——速度损失被解析优化补回来了还有富余。

存量项目的 `bun.lockb` 继续受支持，想迁移跑一次 `bun install --save-text-lockfile` 即可。v1.4 又加了一层供应链保障：GitHub 与 tarball 依赖现在记录 SHA-512 完整性哈希，并新增 `bun audit fix`、`bun pm diff`、`bun dedupe` 等命令。

### 6.2 一次 `bun install` 的完整路径

把上面的机制串起来。在新项目目录执行 `bun install`：

1. **没有 lockfile**：解析 `package.json`，并行下载依赖树，生成文本 `bun.lock`（可 review、可 merge）。
2. **包体落全局缓存**：`~/.bun/install/cache/` 按内容寻址存储，同一份包全机器只有一份。
3. **`node_modules` 组装**：从缓存链接到项目目录，第二个项目用到同一个包时不再重新下载解压。
4. **完整性校验**：有 lockfile 时按记录的哈希核对每个包，v1.4 起覆盖 GitHub 与 tarball 依赖。

CI 里的对应物是 `bun install --frozen-lockfile`：lockfile 与 `package.json` 不一致直接失败，等价于 `npm ci` 的语义。

## 七、内置 TypeScript 与 test runner

**TypeScript 直接执行**。`bun run index.ts` 不需要 `tsc` 预编译——Bun 内置转译器只做「去类型 + 语法转换」，不做类型检查。类型检查仍然交给 `tsc --noEmit`，这个分工是刻意的：转译在毫秒级，检查按项目规模以秒计，混在一起只会拖慢每一次启动。

**测试**。`bun test` 兼容 Jest 的 `describe` / `it` / `expect` / `mock` API，主流断言库风格可以平滑迁过来。v1.4 补齐了大规模测试套件需要的能力：`--parallel`、`--isolate`、`--shard`、`--changed`、`--retry`。给现有 Jest 套件换引擎时，这组 flag 决定了迁移是「换个命令」还是「改一堆配置」。

## 八、v1.4 的内置库策略

all-in-one 在 v1.4 里从工具链蔓延到了常用库，官方口径是这批内置库替代了 15 个 npm 依赖：

- **Bun.Image**：JPEG/PNG/WebP/GIF/BMP 解码缩放编码，API 对标 sharp。官方基准里 1080p PNG 转 400×400 JPEG 比 sharp 快 1.38 倍。
- **Bun.WebView**：不依赖 Puppeteer/Playwright 的无头浏览器自动化——导航、点击（真实用户输入）、执行 JS、截图，macOS 用系统 WebKit，也能驱动本机 Chrome/Edge，留有 `.cdp()` 原始协议出口。E2E 测试和网页抓取的「再装一个浏览器」成本被砍掉了。
- **Bun.cron()**：注册操作系统级定时任务（Linux crontab、macOS launchd、Windows 任务计划），语法兼容 Cloudflare Workers Cron，任务不重叠。
- 另有 Bun.markdown（GFM 支持）、Bun.Terminal（内置 PTY）、Bun.JSON5/XML/TOML/Archive。

这条路线的含义值得掂量：运行时开始替你做依赖决策。图像处理选了 sharp 的 API 形状，定时任务选了 Cloudflare 的语法——内置库快是快，但它绑定了 Bun 的选型。把这类依赖交给内置库之前，先确认你不需要换实现的自由。

## 九、性能数字怎么读

Bun 的宣传数字很多，直接引用容易失真。按三个问题过一遍 v1.4 发布说明里的关键数据：

**测的是什么？** 每个数字都有明确的测量对象：Linux 启动 5.1 ms（Node 27.2 ms），测的是 hello world 级脚本的冷启动；`bun install` 首装 1.41 s（npm 18.1 s），测的是冷缓存全新安装；Bun.serve 吞吐 177.7k req/s，测的是纯回环 HTTP 的极限吞吐。三个数字对应三种完全不同的工作负载。

**数字反映系统的哪部分？** 冷启动数字主要反映引擎选择和二进制体积（JSC + 70 MB 的二进制）；安装速度主要反映并行度和缓存设计；服务器吞吐反映 HTTP 栈的实现质量。Claude Code 的生产数据是更接近真实的参照：换用 Rust 版 Bun 后 Linux 启动快 10%，CPU p99 从 24% 降到 10%——真实负载下的收益是两位数百分比，不是 hello world 的五倍。

**不能推出什么？** 不能从这些数字推出「你的应用会快 N 倍」。业务应用的耗时大头通常在业务逻辑和 I/O，运行时只占其中一小段；安装速度的倍数取决于依赖树形态（冷缓存新装收益最大，热缓存增量安装收益小得多）；服务器吞吐是回环压测的上限，生产环境先到瓶颈的往往是数据库。

一个可靠的读法：把官方数字当「上界参考」，把自己的工作负载片段抽出来跑一遍——Bun 兼容 Node 的包生态，多数项目迁移试错的成本只是一次 `bun install`。

## 十、适用边界

**优先考虑 Bun**：

- CLI 工具和镜像体积敏感的容器服务：70 MB 的单二进制，无需 `node_modules` 即可部署。
- 冷启动主导延迟的场景：serverless、edge runtime、高频短命脚本。
- TypeScript 胶水脚本：省掉 ts-node/tsx 的配置，`bun run` 直接执行。
- agent 基础设施：Anthropic 用它跑 Claude Code，生产数据（启动 -10%、CPU p99 -14 个百分点）可查。

**暂缓上 Bun**：

- 依赖无 N-API 版本的 `node-gyp` 原生模块的项目：先逐个确认，别整仓迁移。
- 对 Node.js LTS 兼容承诺有硬约束的场景：Bun 迭代快，兼容性以测试套件百分比（node:http 等核心模块 97%–100%）而非 LTS 承诺给出。
- 团队没有精力处理运行时边缘差异的：绝大多数代码可以直接跑，但边缘差异需要有人兜底。

## 十一、决策建议

按项目类型给三条路径：

1. **新项目（无历史包袱）**：直接用。`bun init` 起步，工具链一步到位，遇到兼容问题再退 npm + node 的成本也低。
2. **存量服务**：从外围切入。先让 `bun install` 替代 npm（lockfile 迁移是一次性命令），再让 CI 里的测试换 `bun test`，最后才考虑生产环境换运行时。每一步独立可回退。
3. **agent / 平台团队**：重点跟踪。Bun 现在是 Claude Code 和 Claude Agent SDK 的底座，agent 生态的运行时约定大概率围绕它形成；Bun.WebView 这类内置能力（无头浏览器自动化开箱即用）就是朝这个方向铺的路。

短期 Bun 不取代 Node.js——Node 生态的惯性和 LTS 承诺还在。但「工具链整合 + Anthropic 背书 + 内存安全重写」三件事叠加，让它在 2026 年的选型清单里从「可选项」变成了「默认要评估的选项」。

## 常见问题

**Q：Bun 现在到底是 Zig 还是 Rust 写的？**

A：v1.4.0（2026-08-20）起是 Rust。仓库当前语言构成约 Rust 66%、C++ 19%（JavaScriptCore 等 C++ 库及绑定）、TypeScript 10%。2026 年 5 月 11 天完成迁移，v1.3.14 是最后一个 Zig 版本。

**Q：被 Anthropic 收购后，Bun 还是开源的吗？**

A：仓库仍在 GitHub 上以 MIT（本体）许可公开开发，收购后提交活跃。Anthropic 把它用作 Claude Code 和 Claude Agent SDK 的基础设施——自用需求本身保证了持续投入。

**Q：老的 `bun.lockb` 还能用吗？要迁移吗？**

A：能用，1.2 起 `bun.lock`（文本 JSONC）只是新生成 lockfile 的默认格式，存量 `bun.lockb` 继续受支持。建议找低风险窗口跑一次 `bun install --save-text-lockfile` 完成迁移——可 diff、可解冲突的 lockfile 对团队协作的收益是长期的。

**Q：Rust 版和 Zig 版性能有差别吗？**

A：整体提升 2%–5%（跨语言 LTO 的贡献），更重要的是内存行为：可测量的泄漏清零，`Bun.build()` 长时间运行的内存从持续上涨（6,745 MB）变为稳定（609 MB）。这次重写买的是稳定性，不是速度。

**Q：`npm ci` 在 Bun 里对应什么命令？**

A：`bun install --frozen-lockfile`。lockfile 与 `package.json` 不同步时直接报错，语义与 `npm ci` 一致，适合放在 CI 里。

## 自测题

**问题 1：Bun 在 2025-2026 年经历了哪三重变化？**

<details>
<summary>参考答案</summary>

2025 年 12 月被 Anthropic 收购（成为 Claude Code 的运行底座）；2026 年 5 月用 11 天把约 53.5 万行 Zig 重写为约 78 万行 Rust；v1.4 起内置一批原 npm 依赖的替代库（Bun.Image / Bun.WebView / Bun.cron 等）。

</details>

**问题 2：为什么说 Zig 的 `defer` 是重写动机里的病根？**

<details>
<summary>参考答案</summary>

Bun 的宿主语言 JavaScript 有 GC，实现语言 Zig 是手动内存管理，两者接缝处容易出 use-after-free、double-free。Zig 没有析构函数，释放只能靠 `defer` 在每个调用点手写，漏写或重复写就是 bug。Rust 的所有权和 `Drop` 把这类检查挪进编译期，整类错误变成编译错误。

</details>

**问题 3：重写为什么保留了 JavaScriptCore？**

<details>
<summary>参考答案</summary>

三点：JSC 冷启动路径短，适合 CLI 频繁冷启动；常驻内存比 V8 低，适合短命进程；C++ 嵌入接口清晰，Bun 的绑定层已稳定。重写只换了 Bun 自己的代码（Zig→Rust），C++ 部分照旧。

</details>

**问题 4：`bun.lock` 取代 `bun.lockb` 解决了什么问题？性能受影响吗？**

<details>
<summary>参考答案</summary>

二进制 lockfile 无法在 GitHub 上看 diff、无法手工解合并冲突、第三方工具解析不了。文本 JSONC 格式解决了这三点，且 `bun install` 反而比 1.1 快 30%。存量 `bun.lockb` 继续支持，可用 `--save-text-lockfile` 迁移。

</details>

**问题 5：读 Bun 官方性能数字时，哪三类数字不能混着比？**

<details>
<summary>参考答案</summary>

冷启动（hello world 级，反映引擎与体积）、安装速度（冷缓存全新安装，反映并行与缓存设计）、服务器吞吐（回环压测上限，反映 HTTP 栈）。业务应用的大头在业务逻辑和 I/O，官方数字只能当上界参考，真实收益要用自己的负载测。Claude Code 生产数据（启动 -10%、CPU p99 24%→10%）是更接近真实的参照。

</details>

## 参考与口径说明

1. **数据来源**：Stars/Forks/语言构成取自 GitHub API（快照 2026-09-28）；版本号取自 Releases（v1.4.2，2026-09-05）。
2. **重写细节**：《Rewriting Bun in Rust》官方博客（2026-07-08）：行数、commit 数、AI 工作流规模、API 成本、性能对照均出自该文。
3. **v1.4 数据**：Bun 1.4 发布说明（2026-08-20）：启动/内存/吞吐、内置库、Node 兼容百分比、安装对比均出自该文。
4. **lockfile 历史**：Bun 1.2 发布说明：`bun.lock` 默认化、迁移命令、痛点列表。
5. **收购时间**：官方博客《Bun is joining Anthropic》（2025-12-02）。
6. **许可证**：仓库 LICENSE.md：本体 MIT，JavaScriptCore LGPL-2（含重链接指引）。
7. **更新状态**：Bun 迭代很快，读到本文时若数据有变，以 [官方博客](https://bun.com/blog) 和 [GitHub 仓库](https://github.com/oven-sh/bun) 为准。
