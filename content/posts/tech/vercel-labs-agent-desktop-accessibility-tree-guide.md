---
title: "agent-desktop：不用截图，靠无障碍树驱动桌面——以及它把「动作到底送到了吗」变成契约"
date: "2026-11-10T03:30:16+08:00"
slug: "vercel-labs-agent-desktop-accessibility-tree-guide"
description: "vercel-labs/agent-desktop 用 Rust 读取 macOS/Windows/Linux 的无障碍树，把桌面 GUI 变成带 ref 的 JSON，供 agent 做观察—动作—验证循环。本文拆解 PlatformAdapter 分层、ref 身份契约、delivery 与 retry 语义、无头动作与交互租约，并给出接入建议与风险清单。"
draft: false
categories: ["技术笔记"]
tags: ["Rust", "无障碍", "Computer Use", "Vercel", "CLI"]
github_repo: "vercel-labs/agent-desktop"
source_key: "gh:vercel-labs/agent-desktop"
---

## 核心判断

大多数“computer use”（让 agent 操作电脑）工具走的是视觉路线：截图，让模型看图，给出坐标，再模拟点击。这条路的问题不在模型，而在**闭环的确定性**——像素会移动、控件会重排、一个按钮和它的兄弟长得一模一样，坐标随时会过期。

vercel-labs/agent-desktop 换了一条路：**读操作系统的无障碍树（accessibility tree），把每个可操作元素变成一个带 ref 的 JSON 节点**。动作不再是“点击 (320, 180)”，而是“点击 @s8f3k2p9:e8”。UI 变了，旧 ref 会明确报 `STALE_REF`，而不是悄悄点到别的东西上。

但真正让这个项目值得细看的，不是无障碍树这个选择本身，而是它围绕**“一个动作到底送到了没有”**建起来的一整套契约：`disposition.delivery` 区分未送达、送达未验证、送达已验证、送达不确定；`disposition.retry` 告诉你这次失败能不能重试。这套语义在别处很少见到——多数工具在失败时只给你一个错误码，然后让 agent 猜。

截至 2026 年 11 月 10 日，这个仓库有 20316 stars、1507 forks，Rust 为主，Apache-2.0，2026 年 2 月 19 日创建，最新版本 v1.2.0（2026 年 11 月 5 日发布），11 月 9 日仍有提交。

需要先说清一件事：**它不含模型**。README 写得很明确——“the loop lives in your agent; agent-desktop has no model inside”。观察、动作、验证这三步由你的 agent 编排，这个项目只负责把桌面变成结构化数据、把动作变成可寻址的调用。

## 系统地图

它是一个 Rust workspace，Cargo.toml 里列了成员：

```toml
[workspace]
members         = ["crates/core", "crates/macos", "crates/windows", "crates/linux", "crates/ffi", "src"]
default-members = ["crates/core", "crates/macos", "crates/windows", "crates/linux", "src"]
resolver        = "2"
```

| 层 | 内容 | 职责 |
|---|---|---|
| CLI / MCP | `src/`（cli、cli_args、dispatch、mcp、batch、command_policy、diagnostic、visual_debug） | 命令解析、JSON 封装、批量执行、MCP 服务 |
| Core | `crates/core`（adapter、snapshot、refs、ref_action、tree、actionability、locator、session、trace、wait 等） | 平台无关的词汇表、身份契约、动作前置检查 |
| 平台适配器 | `crates/macos` / `crates/windows` / `crates/linux` | 各自对接一个系统的无障碍 API |
| FFI（外部函数接口） | `crates/ffi` | C ABI（应用二进制接口），供进程内调用 |

core 里那个 trait 是整个设计的收口：

```rust
pub trait PlatformAdapter: ObservationOps + ActionOps + InputOps + SystemOps {}
impl<T: ObservationOps + ActionOps + InputOps + SystemOps> PlatformAdapter for T {}
```

**适配器只负责“读到什么、发出去什么”，不负责“这个元素叫什么、这个状态算不算开”。** core 拥有四套平台中立的词汇表——role（角色）、state（状态）、name evidence（名称证据）、native id——适配器把各平台的分类映射到这些词汇上，不允许发明新 token。

这套划分的收益在 CONCEPTS.md 里有具体体现。macOS 和 Windows 对同一个 toggle 控件的映射就不一样：macOS 保留 role 为 `button` 并把开关值读成 `pressed`；Windows 把任何声明支持 toggle 的 `Button` 重新分类成 `role: switch` 加状态 `checked`；Linux 把 toggle 按钮报成 `checked`，把 `pressed` 留给普通按钮。文档把这称为“两套正确的 role 映射相遇的后果，不是任何一方的缺陷”。

## 观察：快照与 ref

```bash
agent-desktop snapshot --app Finder -i      # 只留可交互节点，每个都带 ref
agent-desktop click @s8f3k2p9:e8            # 对某个快照里的 ref 动作
agent-desktop snapshot --app Finder -i      # 再读一次，验证结果
```

输出是一个 JSON 信封：

```json
{
  "version": "2.6",
  "ok": true,
  "command": "snapshot",
  "data": {
    "app": "Finder",
    "snapshot_id": "s8f3k2p9",
    "ref_count": 59,
    "complete": true,
    "tree": {
      "role": "window",
      "name": "Downloads",
      "children": [
        { "role": "treeitem", "name": "Documents", "ref_id": "@s8f3k2p9:e8", "available_actions": ["Click"] }
      ]
    }
  }
}
```

三点值得留意：

**ref 属于它出生的快照**。裸 `@e8` 会被拒绝并返回 `INVALID_ARGS`；UI 变了以后动作返回 `STALE_REF` 或 `AMBIGUOUS_TARGET`，必须重新快照。

**只有可操作的元素才分配 ref**。FAQ 里列出了会拿到 ref 的 role：button、textfield、checkbox、link、menuitem、tab、slider、combobox、treeitem、cell、radiobutton、incrementor、menubutton、switch、colorwell、dockitem、listbox、option。静态文本和惰性容器不拿。FAQ 还特意说明了为什么不把 focus、context-menu、scroll-into-view 算进去：网页运行时几乎每个节点都advertise 这几种能力。

**快照可以是不完整的，而且它会明说**。v2.2 起，超预算的快照不再报 `TIMEOUT`，而是返回 `ok: true` 加上 `complete: false`、`truncated: true`、`nodes_observed`；被截断的节点逐个带 `subtree_truncated: true`，读者可以从根一路走到每个边界。消费者必须读 `data.complete` 才知道拿到的是不是整棵树。

密集应用有专门的打法：先 `snapshot --skeleton --app Slack -i --compact` 画地图，再 `snapshot --root @s8f3k2p9:e3 -i --compact` 钻进一个区域。钻取会把子树里的 ref 换掉，所以旧 ref 会变成 `STALE_REF`——这是设计意图，不是 bug。

## 身份：ref 凭什么还能指到同一个元素

这是 v1.1.0 之后最大的变化，也是最容易被旧教程误导的地方。

**macOS**：ref 携带元素自己的无障碍地址（`retained_object`），后续命令直接转回那个元素，不需要搜索。地址只在元素还活着、且它的进程、role、记录的标识符都还匹配时才被接受——所以被移除的元素、应用重启后的相似元素，都是 stale ref 而不是“长得像的那个”；两个完全相同的孪生控件各自保留自己的 ref。

**Windows 与 Linux**：没有地址可用，走“捕获证明”路径。一个 ref 只有在满足这些条件时才可用——它的窗口被完整读过、且恰好一个观测元素匹配它的完整谓词（role + 每一个记录下来的稳定字段，即 native id、稳定名称、描述）——而且现在活着的元素里恰好还有一个匹配。**零个匹配是 stale ref，两个或更多是 ambiguous，一个字段读不出来就保持 unknown 而不是变成匹配。**

v1.1.0 的 changelog 写得很清楚，这是一个 breaking change：

> 在 Windows 和 Linux 上，指向若干个相同控件之一的 ref、来自快照没能读完的窗口的 ref、以及来自更早快照的 ref，现在返回 `AMBIGUOUS_TARGET` 与 `details.kind: identity_not_unique`，而以前这些是会执行动作的。

同时快照会带上 `data.identity_unproven: true`，告诉你“这次观察没能证明它的 refs”。

文档里把这件事的边界讲得很坦白：CONCEPTS.md 说，身份是元素的 role 与稳定字段，**不是它的实例**——“一个替换了原元素的相同元素会被作用到”。

## 交付：把“送到没有”写成契约

这是这个项目最值得学的地方，也是它和同类工具拉开差距的地方。

每一个动作结果和每一个错误都带 `disposition`：

```json
{
  "version": "2.6",
  "ok": false,
  "command": "click",
  "error": {
    "code": "STALE_REF",
    "message": "@s8f3k2p9:e7 not found in current RefMap",
    "suggestion": "Re-run a snapshot to obtain fresh refs, then retry with the new ref",
    "recovery": {
      "strategy": "refresh_snapshot_then_retry_original",
      "retryable": true,
      "requires_fresh_snapshot": true
    },
    "disposition": {
      "delivery": "not_delivered",
      "retry": "safe"
    }
  }
}
```

`delivery` 有五个取值：`unknown`、`not_delivered`、`delivery_uncertain`、`delivered_unverified`、`delivered_verified`。

`retry` 从 `delivery` 推导：**只有 `not_delivered` 是 `safe`，其他非 `unknown` 的值都是 `unsafe`**。

这条规则的实务含义很硬：一次 `toggle` 如果送达未验证就重试，可能把状态又翻回去；一次 click 重试可能点两次。文档里的指令是——“只在 `disposition.retry` 为 `safe` 时重试或替换动作”，其余情况要“读活的状态（`get`、`is` 或新快照）再决定”。

`unknown` 的定义也值得注意：它意味着命令对送达情况一无所知。文档明确说“把 `unknown` 当作不可自动重试”，并给了一个具体例子——一次可能已经生效的变更操作上的 `TIMEOUT`，会保持 `unknown`，而不是被乐观地当成“没送到”。

版本演进的方向也很清楚。v2.4 起，`set-value`、`type`、`clear`、`check`、`uncheck`、`toggle`、`expand`、`collapse` 这类状态型动作在一次投递后会**拒绝观测到的后置条件矛盾**，读回失败保留适配器的错误码并带 `details.kind: post_action_verification`。v2.5 更进一步，把一批命令里“每次成功都带的成功标志”整个删掉——changelog 的理由很直白：**“一个每次成功调用都带的标志，什么也证明不了。”**

## 无头、租约与并发

ref 动作默认无头（headless）：用语义化的无障碍调用，不移动指针、不抢焦点、不合成按键、不碰剪贴板。**没有语义路径时动作会失败关闭**，而不是退化成坐标点击。只有用户明确允许物理输入（双击、hover、drag、focus）时才用全局 `--headed`。文档里还专门写了一句：“永远不要为了恢复无头失败而切到 headed 模式。”

并发场景由“交互租约”（Interaction Lease）处理：机器级的桌面输入独占权，同一时刻只有一个进程持有。租约只覆盖派发本身，不覆盖派发之前的等待——等待一个元素变得可操作可能很久，把独占权贯穿等待会把整台机器上的所有调用者串行化。

CONCEPTS.md 里对这件事的解释很到位：等待期间解析出的元素是**在没有独占权的情况下**观测到的，所以拿到租约后要**重新解析一次**。“第二次解析才是正确性边界，不是冗余的工作。”

## 动作前置：可操作性电池

派发之前，core 会对解析出的元素跑一组统一的活体检查（Actionability Battery）：visible、stable、enabled、supported action、policy、editable、receiving events。

其中 `receives_events` 的做法是从元素边界里取五个候选点（中心加四个象限点），**任意一个**能命中目标就算通过——问的是“这个元素到底可不可达”，所以部分被遮挡的控件仍能通过。而指针管线问的是另一个问题：它已经解析出的那**单个**坐标上能不能命中。

文档特意强调这两种 hit-test 形态不能混为一谈：一个通过了可操作性电池的元素，仍然可能在那个单点检查上失败。

默认开启的 Auto-Wait 预算上限是 5000ms（`type` 额外按每个字符加 30ms）。瞬时检查（可见性、稳定性、启用状态、遮挡）轮询等待，终局检查（支持的动作、策略、可编辑性）快速失败，不浪费预算。

## 平台支持

| 平台 | 要求 | 无障碍 API |
|---|---|---|
| macOS | macOS 13 及以上，Intel 或 Apple Silicon | AX API（辅助功能接口） |
| Windows | Windows 10 1809 及以上，x64 或 ARM64 | UI Automation（UI 自动化接口） |
| Linux | Ubuntu 24.04 及以上，x86_64 或 aarch64，X11 或 Wayland | AT-SPI（无障碍技术规范接口） |

三个平台共用四套词汇表，靠 `PlatformAdapter` trait 收敛；每个二进制只为自己的平台编译——开发时用 `HOST_PKGS` 把 cargo 限定到宿主平台的包。

macOS 适配器还有个专门处理：Electron 与 Chromium 应用需要先打开无障碍树（设 `AXManualAccessibility` 或 `AXEnhancedUserInterface`），然后在请求截止时间内等属性报告就绪。benchmark README 里说明了原因——**设置成功不代表树已经就绪**。

Linux 上有个 Wayland 限制值得记住：只有 `--headed mouse-click --xy X,Y` 能选择孪生元素中的一个，它会占用前台，而 **Linux Wayland 会话直接拒绝这个做法**。

## 接入方式

```bash
npm install -g agent-desktop
agent-desktop status                # 平台、权限、支持的 surface
agent-desktop permissions --guide   # macOS：走一遍辅助功能授权
```

Homebrew 也可以：`brew install agent-desktop`。没有官方 Scoop 包。

MCP（v1.2.0 新增）把每个叶子命令暴露成一个 stdio 工具，工具名就是命令名：

```json
{ "mcpServers": { "agent-desktop": { "command": "agent-desktop", "args": ["mcp"] } } }
```

给 `mcp` 的全局参数（`--session`、`--headed`、`--trace`）对每次调用都生效。

二进制自带与版本匹配的指南：

```bash
agent-desktop skills get desktop      # 循环、ref、验证与重试规则
agent-desktop skills get platform     # 你当前系统上的差异
agent-desktop <command> --help
```

也可以装进 agent harness：

```bash
npx skills add https://github.com/vercel-labs/agent-desktop --skill agent-desktop
```

还有一条进程内调用的路子：每个 release 都带 `libagent_desktop_ffi`，程序可以直接在进程内调用，不必 fork CLI 进程：

```python
import ctypes
lib = ctypes.CDLL("./lib/libagent_desktop_ffi.dylib")
lib.ad_adapter_create.restype = ctypes.c_void_p
lib.ad_adapter_destroy.argtypes = [ctypes.c_void_p]
assert lib.ad_init(7) == 0  # 头文件的 AD_ABI_VERSION_MAJOR 与库一致时返回 AD_RESULT_OK
adapter = lib.ad_adapter_create()
lib.ad_adapter_destroy(adapter)
```

但要注意一处**版本断点**：v1.1.0 把 C ABI 主版本提到了 7，`ad_resolve_element_exact` 与 `ad_execute_ref_action_exact_with_policy` 现在**永远拒绝**并返回 `ACTION_NOT_SUPPORTED`（`details.kind: exact_entry_unsupported`）——理由是 C 调用方无法提供 ref 现在赖以解析的捕获证明，所以请改用快照 ref 走动作。从源码构建时要用 `cargo build --profile release-ffi -p agent-desktop-ffi`（只有 `release-ffi` 这个 profile 会在边界处捕获 panic 并转成 `AD_RESULT_ERR_INTERNAL`，普通 `--release` 不会）。

命令总数 60 个，其中 56 个是可操作的，另外四个（`key-down`、`key-up`、`mouse-down`、`mouse-up`）会拒绝执行，直到有守护进程能释放被按住的键或按钮。

## 风险清单

这一节是给要把它放进生产链路的团队看的，README 里的原话不算重——“Snapshots, clipboard reads, screenshots, command output, and debug artifacts can contain private desktop content. Keep them out of public logs and uploads.”

**桌面内容会进你的日志**。快照、窗口标题、剪贴板、通知、截图、命令结果，全都含有你让它读的内容。FAQ 里说得更细：session trace 会脱敏结构化字段，但**仍可能保留证据类产物**；“脱敏不会让截图变成可以公开的东西”。

**原生 CLI 不需要远程模型服务**，但可选的 JEV helper 会把你的目标和屏幕描述发给你配置的模型提供方——用之前得想清楚那个提供方能看到什么。

**别把 `--headed` 当兜底**。它会真的动鼠标、真的抢焦点，用户会看见。

**开发时按平台裁剪构建**。每个平台适配器只在自己的 OS 上构建，仓库提供了 `cargo test` / `cargo clippy` 的 `HOST_PKGS` 用法。

## 排查：仓库里有一整层失败档案

`docs/solutions/runtime-errors/` 里放着一批真实故障的复盘文档，读法很有意思：每篇都写明现象、根因、修法和证据（指向具体的测试名与源码位置）。这类东西在开源项目里罕见，通常意味着作者真的在生产里调过。以下几条能帮你省掉重复踩坑的时间。

**“ref_count 有数，但没有哪个元素拿到 ref”**。Linux 上最典型的一例是 GNOME Shell 的托盘、通知与快捷设置面板。这些 surface 由虚拟节点构成，属性跟普通应用不同：core 会丢弃标识符种类为 `Unknown` 的条目（`validate_ref_entry` 拒绝它，分配返回 `SkippedInvalidEntry` **且不报错**），而适配器自己写的测试是手工构造 `RefEntry` 的，压根走不到这道闸——所以适配器测试全绿，只有 CLI 输出的 `ref_count` 暴露出问题。教训很直接：**验证新虚拟节点要读 CLI 的 JSON 里的 `ref_count` 和 `ref_id`，而不是在测试里造一个条目。**

**菜单搜不到，但菜单其实开着**。一次真实故障是：全应用菜单搜索在第一个不完整分支就中断了，于是在一个 6984 项的网格里，一个只加载了部分子项的分支把兄弟分支里开着的菜单给藏了。修法是改成广度优先并推迟 `AppUnresponsive` 分支错误，先把兄弟分支看完。相关的一条铁律是：**不完整的分支不能证明菜单不存在。**

**滚动条的值不能当身份**。滚动条的值一变就变，早期把它当身份，结果一次合法滚动就让活的滚动条解析失败。修法是给 `scrollbar` 和 `handle` 两个 role 补进可变值列表——文档特别强调，**没有放宽任何超时、模糊匹配、路径信任或歧义规则**。

**写操作返回成功，不代表状态变了**。AT-SPI 上有一次写入返回成功但什么都没变的案例；Xcode 的项目导航器过滤框上，`clear` 之后返回的是 `delivered_unverified` 而不是确认。这种情况下正确的做法是**不重发写入**，改用另一次读取（`get`）去确认。

还有一类不是 bug 而是测量纪律：仓库的探针文档里反复强调，一次监控试验中如果**前台有用户的其它活动**，那些输入事件就不能归因给 agent，这种试验不构成无头成功的证据。

## 采用建议

**先上**：已经在用 agent 驱动桌面 GUI、并且被“点了两下”或“toggle 把自己撤销了”坑过的团队。`disposition` 这套语义能直接省掉一类事故——因为你可以把“能不能重试”变成程序判断，而不是让模型从错误消息里猜。

**要做的准备**：在 macOS 上先把辅助功能权限授好（`agent-desktop permissions --guide` 会走完流程），并且在 `AGENTS.md` 里写清楚循环规则——“用 `agent-desktop` 观察和操作桌面应用；首次使用前先跑 `agent-desktop skills get desktop` 与 `agent-desktop skills get platform`”。

**要测试的**：先在无头模式下测。你会先撞上 `STALE_REF` 与 `AMBIGUOUS_TARGET`，这正是它该有的行为；如果你的 agent 一上来就频繁需要 `--headed`，那多半是流程设计有问题，而不是权限问题。

**可以等等**：网页自动化场景。FAQ 明确说了——“它不做网页自动化，网页请用 agent-browser”。这个项目是桌面侧的补充，不是替代。

**一个要记住的版本事实**：v1.1.0 之前的快照 ref 在 Windows 和 Linux 上**全部失效**，会返回 `AMBIGUOUS_TARGET`。升级后必须重新快照。macOS 上 ref 仍能解析，前提是它指向的元素还活着。

## 结尾判断

agent-desktop 真正贡献的不是“用无障碍树替代截图”这个技术选择——那是个聪明的选择，但它只是手段。手段背后是三个更值钱的设计决定：

**把身份契约显式化**（ref 属于快照、必须唯一、匹配谓词是什么），**把送达语义显式化**（五种 delivery、retry 只在 not_delivered 时为 safe）、**把平台差异收进 core**（角色、状态、名称证据、native id 四套中立词汇，适配器不发明 token）。

前两个让 agent 的循环变得可推理——它知道下一步该做什么。第三个让“再支持一个平台”变成一个工程任务而不是一次重写。

从“agent 会用电脑”这条路看，这条路目前的瓶颈几乎不在模型，而在**语义和确定性**：agent 需要知道自己点的是哪个按钮、需要知道刚才那一下送没送到、需要知道换台机器行为有什么不同。agent-desktop 在这三点上都给了可验证的答案——虽然代价是一套相当重的概念体系，CONCEPTS.md 那种密度本身就是学习成本的度量。

上手路径建议：先装上、跑 `agent-desktop status`、然后在 Finder 上完成上面那三条 snapshot → click → snapshot，用眼睛核对返回的 JSON 和真实界面是不是一致。理解了这三步，剩下的命令都是细节。
