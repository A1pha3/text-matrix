---
title: "microcodex 源码解构：49 个 C++23 文件拼出一个终端编程智能体"
date: 2026-08-03T16:44:00+08:00
lastmod: "2026-09-26T01:35:00+08:00"
draft: false
slug: "microcodex-cpp-terminal-coding-agent-deep-dive-2026"
github_repo: "paoloanzn/microcodex"
source_key: "gh:paoloanzn/microcodex"
author: text-matrix
tags: ["cpp", "cpp23", "agent", "terminal", "open-source", "architecture", "libcurl", "termbox2", "md4c", "microcodex"]
categories: ["技术笔记"]
description: "paoloanzn/microcodex 用 C++23 手写了一个终端编程智能体：49 个源文件、9,745 行、808 KiB 单文件产物，运行时只链接 libcurl。本文以 main 分支 e511d45 为基准，在本机编译并跑通它自带的 44 个黑盒用例，逐条核对工具契约、上下文压缩粒度、失败语义、黑名单边界与打包链路。"
keywords: ["microcodex", "C++23", "终端智能体", "Responses API", "上下文压缩", "termbox2", "MD4C", "PKCE", "黑名单", "glibc 基线"]
---

microcodex 把「终端里的编程智能体（coding agent）」这件事整个用 C++23 手写了一遍：49 个源文件、9,745 行、一个 808 KiB 的可执行文件，运行时除了 libcurl 不链接任何第三方库。值得读它的理由不是「居然有人用 C++ 写这个」，而是它把平时被框架挡住的那批决策摊在了明面上——上下文压缩在什么时刻动手、以什么粒度动手，一次中途失败的工具调用要不要在记录里留下痕迹，OAuth 的套接字生命周期由谁负责回收。

本文的每条结论都来自 2026-09-26 在本机的一次完整走查：把仓库克隆到本机、`make` 编译、跑它自带的 44 个黑盒用例，再把文中每处代码引用回到文件与行号。核对基准是 main 分支 `e511d4513c022ede259c3e9421c4dab65953607c`，提交于 2026-09-25。仓库创建于 2026-07-30，那天它有 41 颗星、6 个未关闭的议题和 6 个未合并的合并请求，55 次提交出自两个人之手。这类数字隔天就变，所以只在这里出现一次。

## 目录

1. [先把它跑起来](#先把它跑起来)
2. [仓库形状](#仓库形状)
3. [一次提问穿过哪些层](#一次提问穿过哪些层)
4. [五个工具的真实契约](#五个工具的真实契约)
5. [上下文压缩按整轮走](#上下文压缩按整轮走)
6. [272K 这组默认值从哪里来](#272k-这组默认值从哪里来)
7. [失败语义：可续接与必须回滚](#失败语义可续接与必须回滚)
8. [对话文件是三种记录的追加日志](#对话文件是三种记录的追加日志)
9. [bash 安全层的实际边界](#bash-安全层的实际边界)
10. [OAuth 与它复用的那套身份](#oauth-与它复用的那套身份)
11. [TUI 里多出来的一段输入解析](#tui-里多出来的一段输入解析)
12. [手写 JSON 层没有 DOM](#手写-json-层没有-dom)
13. [技能发现与它的扫描面](#技能发现与它的扫描面)
14. [构建、打包与那条七周的缝](#构建打包与那条七周的缝)
15. [值不值这套取舍](#值不值这套取舍)
16. [出错时先看哪几处](#出错时先看哪几处)
17. [下一步读哪几段代码](#下一步读哪几段代码)
18. [五个自测题](#五个自测题)
19. [参考](#参考)

## 先把它跑起来

源码构建只要三样：一个 C++23 编译器、`make`、libcurl 开发文件；Linux 还要 OpenSSL 开发文件。

```shell
git clone --recurse-submodules https://github.com/paoloanzn/microcodex.git
cd microcodex
make --jobs 4 all
```

在 Apple Silicon 的 macOS 上，用 CommandLineTools 自带的 clang++，从零编译 25 个 `.cpp` 加 vendored 的 `md4c.c` 实测 4.3 秒（用户时间 12.7 秒），产物 `build/microcodex` 是 827,304 字节的 Mach-O arm64 可执行文件。它动态链接的东西一共三条：

```text
/usr/lib/libcurl.4.dylib
/usr/lib/libc++.1.dylib
/usr/lib/libSystem.B.dylib
```

「零运行时依赖」这句话在这里是可验证的：termbox2 和 MD4C 都以源码形式编进产物，不参与链接；`otool -L` 看不到它们。

`make test` 是另一回事。它先调 `make all`，再把 `tests/run.sh` 拉起来，而这套夹具需要 Ruby：

```text
$ ruby -v          # macOS 自带的 /usr/bin/ruby
ruby 2.6.10p210 (2022-04-12) [universal.arm64e-darwin24]

$ make test
...
44 tests, 32 failures
```

32 个失败全部指向同一行——测试夹具里那个回环服务脚本的第 25 行用了 `Enumerable#filter_map`，这是 Ruby 2.7 才有的方法。`tests/TESTS.md` 只说夹具「只用 Ruby 标准库、没有包依赖」，没说版本下限；CI 里 macOS 那两个 job 用 `ruby/setup-ruby@v1` 钉在 3.3，所以这条下限在 CI 上永远不会暴露。给系统 Ruby 补一个 12 行的 `filter_map` 兼容层（通过 `RUBYOPT` 注入，不改仓库任何文件）之后：

```text
$ RUBYOPT=-r/tmp/rubypre/filter_map_compat.rb sh tests/run.sh
...
44 tests, 0 failures
```

9.8 秒跑完 44 个用例。这个兼容层只是把缺失的方法补上，没有改断言，因此可以把这 44 个绿点当作可信的基线；换到 Ruby 3.x 上不必注入任何东西。

## 仓库形状

`git ls-files` 有 80 条，其中 C++ 源文件 49 个：25 个 `.cpp` 加 24 个 `.h`，合计 9,745 行、400,960 字节。`.cpp` 占 8,699 行，头文件只占 1,046 行——声明写得薄，实现都堆在同一个平面上。所有源文件平铺在根目录，没有 `src/`、`include/`。

按字节降序取前九个：

| 文件 | 字节 | 行数 | 管什么 |
|---|---|---|---|
| `ui.cpp` | 63,348 | 1,583 | termbox 之上的交互界面 |
| `oauth.cpp` | 62,208 | 1,362 | 两种登录流、令牌刷新、凭证落盘 |
| `api.cpp` | 46,341 | 1,090 | Responses 应用程序接口（API）的流式调用与工具循环 |
| `conversation.cpp` | 24,757 | 553 | 追加式对话日志的读写 |
| `markdown.cpp` | 24,039 | 651 | Markdown 渲染：MD4C 事件到样式区间 |
| `json.cpp` | 19,164 | 498 | JSON 取值与转义 |
| `main.cpp` | 14,970 | 388 | 进程入口与命令分派 |
| `system-prompt.cpp` | 14,120 | 159 | 内嵌的基座提示词（prompt） |
| `bash.cpp` | 13,778 | 360 | 子进程执行与取消 |

`ui.cpp`、`oauth.cpp`、`api.cpp` 三个文件 4,035 行，占全部行数的 41.4%；按字节算是 171,897 / 400,960，即 42.9%。终端界面、授权、后端通信这三块公认最脏的活吃掉了近一半代码，而它们恰好都是没有合适库可依赖的部分。

第三方代码只有两个 git 子模块，`.gitmodules`（187 字节）里就是这两条：

```text
vendor/termbox2  https://github.com/termbox/termbox2.git
vendor/md4c      https://github.com/mity/md4c.git
```

`NOTICE`（322 字节）逐项列出归属：termbox2 版权 2021 归 termbox 开发者，MD4C 版权 2016-2024 归 Martin Mitáš，两者都是 MIT；仓库本身 Apache-2.0，版权行是 `Copyright 2026 Paolo Anzani`，且 49 个源文件每个头部都带 `SPDX-FileCopyrightText` 与 `SPDX-License-Identifier`。

## 一次提问穿过哪些层

`main.cpp:25` 那行常量是整条链路的起点：

```cpp
constexpr std::string_view default_model = "gpt-5.6-sol";
```

```text
microcodex [--model M] [resume ID] [PROMPT...]
   |
   +-- main.cpp        解析参数 -> AgentRequest{model, model_explicit, prompt, resume_id}
   +-- conversation.cpp  要续接就先读 <id>.jsonl 首行的元数据，继承 model、切回 working_directory
   +-- oauth.cpp       loadOAuthCredentials() -> auth.json；没有就报 "Not logged in."
   +-- agent.cpp       makeCodingAgentConfig(model)：instructions = 基座提示词 + 技能目录
   +-- model-catalog.cpp  GET /models?client_version=0.146.0，拿上下文窗口，失败则用内置兜底值
   +-- api.cpp         runPrompt() 或 ui.cpp 的 runInteractive()
```

命令行解析是手写的，参数不足时靠 `std::expected` 把错误传回 `main`，不引入任何解析库。几条错误路径可以直接复算：

```text
$ microcodex "hello"                       # 未登录
Not logged in. Run 'microcodex login' first.     exit=1
$ microcodex logout                                exit=0   # 已是登出状态
Already logged out.
$ microcodex --model
--model requires a model name                      exit=1   # 后跟用法说明
$ microcodex resume
resume requires a conversation ID                  exit=1
$ microcodex show
show requires one conversation ID                  exit=1
```

`resume` 有两条不那么显眼的行为：`conversationPath()` 先拒绝空值、含 `/`、`.`、`..`，再给 ID 补上 `.jsonl` 后缀，最后要求它是一个普通文件；命中之后如果用户没显式写 `--model`，就沿用元数据里记录的模型，并把进程当前目录切回那次对话保存的 `working_directory`（`main.cpp` 里对应 `std::filesystem::current_path`，失败提示 `Could not restore conversation working directory:`）。续接的语义因此是「回到那台机器上的那个目录，用那个模型继续」，而不只是「回放历史」。

## 五个工具的真实契约

`makeCodingTools()`（`agent.cpp:122`）注册五个工具：`read`、`write`、`edit`、`glob`、`bash`。每个都自带一段内联的 JSON Schema（模式声明），且一律 `"additionalProperties":false`。它们的描述文本本身就是给模型的约束，逐条读能发现不少细节：

```text
read   Read up to limit bytes from a file starting at offset.
write  Create a new file with content. Fails when the path already exists.
edit   Replace exact text in an existing file. replace_all defaults to false when omitted.
glob   Expand a filesystem glob pattern and return matching paths separated by newlines.
bash   Run a shell command in the user's login-shell environment and return JSON containing stdout, stderr, and exit_code.
```

`read` 的 `offset` 与 `limit` 是**字节**，不是行号，`bytesToRead()` 就是 `min(limit, size - offset)`，越界时报 `Offset is beyond file size`。也就是说模型拿到的一段文本可能从某行中间开始，边界要它自己判断。

`write` 与 `edit` 的分工是硬性的：前者只新建，路径已存在就返回 `Overwriting an existing file is not allowed`；后者只做已有文件里的精确替换，`replace_all` 省略时为 `false`。`write` 成功时返回的整数值恒为 0，适配器并不使用它，给模型的只有一句 `Created <path>`。这一层划分还在基座提示词里被单独重申了一次：

```text
Do not create or edit files with shell redirection, `cat`, or other bash write tricks.
```

工具的统一骨架在 `tool.h`。`ToolBase` 只有三个虚函数——`name()`、`toJsonString()`、`executeJson()`；具体工具是 `Tool<T, S...>` 模板的实例，把「一个普通 C++ 函数」和「一段 JSON 入参」之间的转换交给一个 `JsonExecutionAdapter`（`std::function`）。适配器从 `ToolArguments` 里按名字取值，缺哪个就把哪个的原始错误往上抛，然后在调用前后各查一次 `stop_token`。

骨架里最有信息量的一处是 `ToolResult` 的形状：

```cpp
struct ToolResult {
    std::string output;
    std::shared_ptr<const EditResult> edit;
};
```

`output` 是回给模型的内容，`edit` 是给界面画的差异块，两条分开，于是大段 diff 不会进对话历史。`edit.h` 里的 `EditHunk` 只存改动行加前后各一行上下文，注释写得很直白：`This is enough for the UI without retaining whole files.` 紧接着 `tool.h` 里还有一段 `NOTE: Yes, this smells a little.`——作者自己承认这个为 `edit` 单开的字段是个坏味道，并要求后来者别再为每个工具加一个专用字段。这类注释比任何架构文档都更能说明代码想往哪长。

## 上下文压缩按整轮走

这一层的单位是「轮次」：一次用户提问到模型交回控制权为止算一轮，一轮内部可以穿插任意多次工具调用与它们的输出。压缩要动的就是这些轮次的集合。

`ContextCompactor` 的策略全在 `context-compaction.cpp`，一共 181 行。它的输入是一份 `ContextView`（条目数组 + 已完成轮次边界 + 活动轮次的保护起点），输出是一份 `CompactionPlan`。

`needed()` 的判断是 `max(上报的输入词元数, 估算值) >= min(compact_at_tokens, context_limit_tokens)`，`compact_at_tokens` 为 0 即关闭压缩。估算不引分词器，`estimateContextTokens()` 把所有条目的字节数相加再除以 3 向上取整，注释给的理由是代码和 JSON 每字节比散文更费词元，取 3 是有意保守。

`plan()` 从最新一轮往旧遍历，累加到 `retained_context_tokens` 预算用完为止，保留边界永远落在 `TurnBoundary` 上。这段有对应注释，也是整套压缩设计的关键一句：

```cpp
// Walk complete turns from newest to oldest. Retention always follows
// turn boundaries, so a function call can never be separated from its output.
```

被压掉的部分换成一条用户消息，外面裹一层标签，`prepare()` 里拼的是 `"<conversation_summary>\n" + summary + "\n</conversation_summary>"`，然后把保留区间原样搬过来，并把每条轮次边界重算为 `1 + old.end - retained_start`。摘要文本本身有上限（`maximum_summary_bytes`），空摘要和超限摘要都直接判定失败而不是截断。

生成摘要靠另一次真实的模型调用：`requestSummary()` 把 `summary_instructions` 当作这一请求的 instructions，用户消息只有一句 `Produce the conversation summary now.`，并且 `emit_events=false`，界面看不到这段流。那段指令原文对「保留什么」列得很具体：

> Summarize the conversation for another coding agent that must continue the work. Preserve the user's goal and constraints, decisions and their reasons, files inspected and changed, important code behavior, commands and test results, unresolved errors, and remaining work. Do not include conversational filler.

`retain_recent_turns` 是 `plan()` 的第二个形参，默认 `true`；传 `false` 时保留遍历直接从 0 开始，也就是不留任何完整轮次。它控制的是「要不要保留最近若干整轮」，而不是保留几条。

还有一处容易漏：压缩不只由本地阈值触发。`requestWithToolExecution()` 里有一个 `retried_context_limit` 标志，当后端返回上下文超限错误时，强制压缩一次并重试这一请求，只试一次。用例 `T4.10: a provider context error compacts and retries once` 就是在钉这条行为。

## 272K 这组默认值从哪里来

`CodexApiConfig` 的默认压缩配置是四个硬编码数字：

```cpp
CompactionConfig compaction{
    .context_limit_tokens = 258'400,
    .compact_at_tokens = 244'800,
    .retained_context_tokens = 20 * 1024,
    .maximum_summary_bytes = 32 * 1024,
};
```

上方注释说明这是「离线兜底值，对应 Codex 对未知模型的 272K 描述符」。前两个数不是随手取的：`model-catalog.cpp` 里 `default_effective_context_window_percent = 95`、`default_auto_compact_percent = 90`，而 272,000 × 95% = 258,400、272,000 × 90% = 244,800。也就是说兜底值等价于「一个 272K 窗口、未提供百分比的模型」。

在线时这套值会被覆盖。`fetchModelContextLimits()` 把 Responses 端点尾部的 `/responses` 换成 `/models?client_version=0.146.0` 发一次 GET，空闲与总超时都是 5 秒，响应上限 2 MiB。它从每个模型对象里读 `slug`、`context_window`、`max_context_window`、`auto_compact_token_limit`、`effective_context_window_percent` 五个字段，但这五者的宽容度不一样：只有 `slug` 是硬性必填，另外四个缺失或写成 `null` 都会退化成默认值（百分比退到 95，压缩阈值退到窗口 90% 的换算值，窗口则从 `context_window` 换到 `max_context_window`，两个都拿不到就判定这个模型没有可用的上下文窗口）；反过来，只要字段存在却不是无符号整数，就整体报 `JSON member '...' is not an unsigned integer`。解析时还有一条收紧规则：

```cpp
const std::size_t default_compact_at = percentage(*resolved_window, default_auto_compact_percent);
const std::size_t resolved_compact_at = std::min(compact_at->value_or(default_compact_at), default_compact_at);
```

服务端给的自动压缩阈值只会「不晚于」本地 90% 换算值生效，不会被它调大。取到模型元数据后 `applyModelContextLimits()` 覆盖 `config.compaction`；拿不到（未登录、端点不通、模型不在列表里）就打印一行 `Warning: ... Using built-in context limits.` 继续跑。这条容错路径意味着：**离线路径上的压缩阈值和真实模型可能不一致**，只是它宁可偏保守也不让程序起不来。

两个阈值还能从环境外部改：`applyConversationEnvironment()` 读 `MICROCODEX_COMPACT_AT_TOKENS` 与 `MICROCODEX_RETAINED_CONTEXT_TOKENS`，非空则必须是纯无符号整数，否则报 `... must be an unsigned integer` 并退出。它排在模型元数据拉取**之后**，所以这两个变量覆盖的是刚刚算出来的那组值。

举一个可算的例子。假设某模型窗口 400,000 词元、未提供百分比，那么 `percentage(400000, 90)` 得 360,000，`percentage(400000, 95)` 得 380,000：

| 服务端返回的 `auto_compact_token_limit` | 生效的 `compact_at_tokens` | 生效的 `context_limit_tokens` |
|---|---|---|
| 缺失 | 360,000 | 380,000 |
| 370,000 | 360,000（被本地 90% 夹住） | 380,000 |
| 300,000 | 300,000（服务端更早，直接采用） | 380,000 |

三个数都按整数运算走 `percentage()` 那条表达式，与 272K 兜底值的推法一致。`retained_context_tokens` 与 `maximum_summary_bytes` 不参与覆盖，`applyModelContextLimits()` 把当时配置里的值原样传下去，也就是 `api.h` 默认的 20,480 与 32,768。

## 失败语义：可续接与必须回滚

下文会引用若干用例编号。`T4.10`、`T9.1` 这样的前缀是各测试文件写在用例描述里的自有标签，`tests/run.sh` 只另外累加一个全局三位序号，因此输出形如 `ok 039 - T9.3: …`；这些描述文本可以直接拿去 `grep tests/`。

`api.cpp` 对一次轮次的收场方式做了二分，这个分类是全文最值得抄走的东西。判据不在状态码，而在错误的来源与形状。

可续接的一类包括：用户中断、传输层失败（错误串以 `HTTP request failed: ` 开头）、任何 5xx、工具轮数耗尽，以及后端把回复标成未完成。最后一项的实现方式有点特别——它比对的是字符串：流里的 `response.incomplete` 事件会拼出 `The Codex response was incomplete: <reason>`，当 reason 是 `max_output_tokens` 时正好等于内部常量 `turn_usage_limit_error`，于是被识别成「额度用完但可以继续」。

必须回滚的一类是：4xx、流里的 `response.failed` 与 `error` 事件（错误文本直接取自服务端给出的 `message`），以及流断开却始终没等到 `response.completed`。

命中可续接那一类时，动作是：保留已经收到的全部完整条目和已流出的文本，追一条标记项，然后照常把这轮写进对话文件。

```cpp
std::string turnAbortedItem(const std::string_view error) {
    return microcodex::userMessageItem(
        "<turn_aborted>\n" + std::string(error) + "\n</turn_aborted>");
}
```

回滚那一类会把 `input_items_` 截回本轮起点，连本轮之前那些**成功执行过**的工具轮也一起丢掉，`turn_number_` 与 `turn_state_` 同步还原，不写盘。`sendUserMessage()` 里那段注释把理由说了：`Other failures remain transactional: restore the last terminal turn even after successful intermediate tool rounds.`

工具轮数耗尽的处理更细。超过 `maximum_tool_rounds` 时不是简单报错——那些 `function_call` 条目已经进了上下文，留下悬空调用会让下一轮变成非法输入。于是它给每条未执行的调用补一条明确的输出：

```cpp
"Error: Tool call was not executed because Codex exceeded the maximum number of tool rounds"
```

`T5.5` 与 `T5.6` 两个用例专门验证「撞上限的那一整轮被完整保存下来」。同理，5xx 不重试：`T9.1: an HTTP 503 aborts the turn instead of retrying` 直接把这个行为钉住，整条请求路径上没有任何退避重试逻辑。

并行执行的细节也值得单独看。一轮里的多个调用用 `std::async` 全部同时启动，超过 `maximum_parallel_tool_calls` 直接判定为错误而不是排队；但收集结果时按提交顺序逐个取回 future，注释说明这样「保持模型给出的调用顺序，同时不把它们串行化」。所以结果顺序是**请求顺序**，不是完成顺序，回传给模型的输出序列因此是确定的。

## 对话文件是三种记录的追加日志

对话存储路径由 `conversationDirectory()` 决定：`$CODEX_HOME/conversations`，未设置则 `~/.codex/conversations`。新建时 `::open(path, O_WRONLY | O_CREAT | O_EXCL, 0600)`——`O_EXCL` 让「文件已存在」直接成为一次失败而不是静默追加，权限一次给到 600。文件是 JSONL，每行一条记录，只有三种 `type`：

```text
{"type":"conversation","version":1,"id":...,"created_at":...,"working_directory":...,"model":...}
{"type":"turn","number":...,"id":...,"items":[<原始 Responses 条目>]}
{"type":"checkpoint","generation":...,"through_turn":...,"keep_from_turn":...,"summary":"<对话摘要>"}
```

第一条永远只有一行，`readConversationMetadata()` 读首行就返回，所以 `microcodex list` 不需要登录、不需要网络就能列出历史（用例 `T4.5` 断言的正是这点）。`version` 必须等于 1，否则 `Unsupported conversation file version N`；单条记录上限 16 MiB。

打开文件时它会扫一遍并建立 `TurnLocation{number, offset, length}` 索引，此后 `readTurnsBefore(cursor, maximum_bytes)` 就能按偏移从尾部倒着取若干轮，而不必先整文件载入——界面里「往上翻更早的历史」这件事因此不需要把整个对话读进内存。

有一条不变量被写进了测试而不是写进注释：`T4.8: compaction never removes turns from the durable transcript`。压缩只重写模型看到的输入序列，磁盘上的轮次一条不删。基座提示词里对应的那句话是 `When you run out of context, the conversation is automatically summarized for you, but you will see all prior user requests.`——模型被事先告知自己会看到摘要，并被要求「假设发生了压缩，继续往下做，不要重头再来」。

## bash 安全层的实际边界

`bash-safety.cpp` 只有 67 行：五个 POSIX 扩展正则，`std::regex::extended | std::regex::icase`，各自带一句理由文本，命中即返回。它不做引号、变量、子命令的解析。

| 正则拦截 | 理由文本 |
|---|---|
| 命令位置上的 `rm` 带 `--force` 或含 `f` 的短选项组 | `forced file removal is blocked` |
| 命令位置上的 `git reset --hard` | `git reset --hard is blocked` |
| `git clean` 带 `-f*` 或 `--force` | `forced git clean is blocked` |
| `git checkout --` | `git checkout -- is blocked` |
| `mkfs[.后缀]`、`fdisk`、`parted`、`shutdown`、`reboot`、`halt`、`poweroff` | `system or disk destructive command is blocked` |

「命令位置上」这四个字是全部边界的来源。把这份文件单独编一个探针就能看见它拦到哪、放过了什么：

```shell
clang++ -std=c++23 -O1 -o deny_probe deny_probe.cpp bash-safety.cpp
```

探针遍历十二个命令，`microcodex::deniedBashCommandReason()` 的输出（2026-09-26 实测）：

```text
rm -rf build                       | forced file removal is blocked
sudo rm -rf /tmp/x                 | forced file removal is blocked
echo hi; rm -f a.txt               | forced file removal is blocked
bash -c 'rm -rf /tmp/y'            | (allowed)
find . -name '*.o' -delete         | (allowed)
git reset --hard HEAD~1            | git reset --hard is blocked
git -c core.pager=cat reset --hard | (allowed)
git clean -fdx                     | forced git clean is blocked
git checkout -- src/main.cpp       | git checkout -- is blocked
mkfs.ext4 /dev/sdb1                | system or disk destructive command is blocked
shutdown -h now                    | system or disk destructive command is blocked
> important.txt                    | (allowed)
```

同一件事，`rm -rf` 直接写会被拦，套进 `bash -c '…'` 的引号里就过了——因为 `rm` 前面那个字符是单引号，不在 `^`、空白、`;`、`|`、`&`、`(` 这些位置标记里。`git -c` 插了一个配置参数也绕开。`find -delete` 和截断文件的重定向从来就不在名单上。

这套边界在三个地方各说了一遍，三处措辞并不相同，但口径一致：README 的 `> [!WARNING]` 段落（`not a shell parser and is not a complete security boundary`）、`bash-safety.h` 的 `This is a simple lexical guard.`、以及 README 的 Known bugs 列表（`indirect or unrecognized destructive commands may not be blocked`）。它同时还是一层模型行为的约束：基座提示词里单独写了一句

```text
Exercise caution when escaping text for bash calls: backticks and `$()` can execute.
```

把正则管不住的那部分交给模型自觉。

命令执行本身在 `bash.cpp` 的 `runProcess()`：建两条管道，派生子进程，子进程里 `setpgid(0, 0)` 自成一个进程组，`dup2` 接管标准输出与错误输出，再 `execvp`。父进程在 `poll` 与取消标记之间轮询，需要中止时对整组发 `SIGKILL` 再回收。这里注释里有一条很容易忽略的经验：`execvp` 失败后不能用 C++ 流报错，因为多线程进程里派生子进程之后的标准流不安全，所以那一行直接用 C 的系统调用写错误。

## OAuth 与它复用的那套身份

`OAuthOptions` 的默认值说明了一切：

```text
issuer        https://auth.openai.com
client_id     app_EMoamEEZ73f0CkXaXp7hrann
originator    codex_cli_rs
callback_port 1455        （被占用时试 1457）
token_request_timeout_seconds 30
```

`client_id` 和端口都是 Codex 那套本地回调注册的取值，`oauth.h` 的注释写着 `intentionally compatible with the credential file used by Codex`。后果是双向的：用户登录过 Codex 就不必再登录 MicroCodex，反之亦然；但这两个端口也因此是抢手资源，端口占用时能不能顺利退到 1457 取决于本机。

两条流最后都落到 `issuer + "/oauth/token"` 换令牌，中间过程却完全不同。本地回调流先绑定监听再构造 `/oauth/authorize` 的 URL（`OAuthLogin::start()` 的注释解释了这个顺序：绑定成功之后浏览器才能立刻打开），PKCE 按 RFC 7636 用 S256，自己生成 verifier，等回调默认 5 分钟。设备码流把验证页地址和一次性码打在终端上，然后轮询 `/api/accounts/deviceauth/token`；这里 PKCE 的 verifier 不由本地生成，注释说明是服务端在用户批准后随 `authorization_code` 一起返回，托管的回调地址顶替了原本机上的 1455。轮询对 403 与 404 都当作「用户还没在浏览器里点完」，按服务端给出的间隔重试，但单次睡眠不会越过整体截止时间——`finishOAuthDeviceLogin()` 的默认超时是 15 分钟，界面上还多印一句 `Continue only if you started this login in MicroCodex.`。

三处细节说明作者被这类问题咬过：

- `FileDescriptor`（`oauth.cpp:54`）统一回收套接字与文件描述符，注释给的理由是：

  ```text
  OAuth has many error exits, so centralizing close() here makes the rest of the flow much easier to audit.
  ```

- 账户 ID 从 `id_token` 的 JWT 载荷里解出来，注释明确 `this routine only decodes its payload`——不验签。这里的用途只是填 `ChatGPT-Account-ID` 请求头，不做授权判断。
- 刷新令牌时服务端可能只回部分字段，也可能显式回 JSON `null`，代码把这两种都当作「沿用旧值」，其他类型才报错。

凭证写入是原子的，且只给属主读写；哈希实现按平台条件编译，macOS 走 CommonCrypto 的 `CC_SHA256`，Linux 走 OpenSSL 的 `openssl/sha.h`——这也是 Linux 构建要装 OpenSSL 开发文件的原因。整个仓库主动抛出的异常只有一处地方：`throw` 只出现在 `bash.cpp`（管道、派生子进程等系统调用失败时抛 `std::runtime_error`）；`api.cpp`、`http.cpp`、`ui.cpp` 里的 `try` 只是把标准库可能抛出的异常（比如 `std::async` 起不来）就地转成 `std::unexpected`。除此之外全部走 `std::expected<T, std::string>`，`std::expected` 这个词在 49 个源文件里出现 194 次。

请求头那组值最能看出它想扮演谁：

```text
Authorization: Bearer <access_token>
Accept: text/event-stream
originator: codex_cli_rs
session-id / thread-id / x-client-request-id: <session_id>
x-codex-window-id: <session_id>:<turn_number-1>   # 请求体里的同名字段用的是压缩代次
ChatGPT-Account-ID: <account_id>
```

请求体里同时带 `"store":false`、`"stream":true`、`"include":["reasoning.encrypted_content"]` 和一个 `client_metadata`；`prompt_cache_key` 也取 `session_id`。端点默认是 `https://chatgpt.com/backend-api/codex/responses`，也就是 ChatGPT 订阅侧的 Codex 后端，而不是 `api.openai.com`。这条链路是否长期可用不取决于 MicroCodex 的代码——`main.cpp` 里留了一个 `MICROCODEX_API_ENDPOINT` 环境变量来覆盖端点（它的注释说明这是给黑盒测试指向回环服务用的），顺带也就此留下了一条风险提示：`tests/TESTS.md` 提醒不要把该变量指向不可信服务器，因为配置好的端点会收到承载令牌。

## TUI 里多出来的一段输入解析

`ui.cpp` 顶上有七个常量，构成交互层的容量约束：

```text
maximum_transcript_bytes                512 * 1024
maximum_tool_preview_bytes               16 * 1024
large_paste_character_threshold              1000
maximum_collapsed_tool_output_rows              5
animation_frame_milliseconds                     32
idle_poll_milliseconds                          250
maximum_prompt_rows                               6
```

`termbox.cpp`（98 行）不是 termbox2 的封装层——`tb_init()`、`tb_present()`、`tb_shutdown()` 都在 `ui.cpp` 里直接调用。它实际干的是两件事：一是用 `#define TB_IMPL` 把 termbox2 这个单头文件库的实现体落在唯一一个编译单元里（注释同时说明头文件必须排在系统头文件之前，好让它自己的 POSIX 特性宏生效）；二是通过 `tb_set_func(TB_FUNC_EXTRACT_PRE, extractCustomInput)` 在 termbox 的转义序列解析器之前插一段自己的输入解析，把 `\x1b[200~` / `\x1b[201~` 认成粘贴起止事件，并把终端发成 `Esc` 前缀的 Option+b、Option+f、Option+退格还原成带 `TB_MOD_ALT` 的一次按键。termbox2 没有粘贴事件，这个缺口就在这里补。对外它只暴露 `enableBracketedPaste()` 和 `disableBracketedPaste()` 两个函数。

颜色一律用索引色而不是真彩。`ui.cpp` 的注释给了理由：真彩要把 termbox 每个单元格的属性从 16 位扩到 32 位，为了一层低对比度的用户消息底色不值当。实际取值：

```text
界面底色 236   弱化前景 245   更弱前景 240   成功 10   错误 9
新增行底色 22  删除行底色 52

Markdown：代码 14   链接 14   引用 10   列表记号 12   次要文本 245   代码块底色 236
Shell 高亮：命令 14|bold   关键字 13|bold   选项 12   字符串 10   变量 14   操作符 13   注释 245|dim
```

引用块画的是 `│ ` 前缀加 `TB_DIM`。渲染缓存 `MarkdownRenderCache` 以「源文本字节数 + 终端宽度」为键，理由是助手输出只追加不改写，字节长度足够当版本号；宽度一变缓存自然失效。这个取舍比逐帧比较文本便宜得多。

## 手写 JSON 层没有 DOM

`json.h` 里只暴露八个函数，最关键的一条类型决定了这一层的形状：

```cpp
using JsonMember = std::expected<std::optional<std::string_view>, std::string>;
```

`findJsonMember()` 返回的是原缓冲区上的一个视图，不复制、不建对象树。`api.cpp` 和 `model-catalog.cpp` 的读法都是「知道要取哪个键，去切片」。序列化方向也只有一个 `appendJsonString()`，负责把字符串转义回 JSON 文本，包括 `\u00XX` 形式的控制字符。

它仍然是一个递归下降的合法解析器：`skipJsonValue()` 递归跳过对象与数组，深度超过 128 判定 `JSON is nested too deeply`；字符串解码支持 `\n`、`\t`、`\"`、`\\`、`\uXXXX`，代理对单独处理，并把三种错误分开报（`Missing low surrogate` / `Invalid low surrogate` / `Unexpected low surrogate`）。所以那些「手写解析器会不会被深嵌套打爆栈」的担心在这一层是有显式闸门的，128 就是那道闸门。代价是这套 API 只能满足 Responses 协议自己那几种读取模式，不适合被复用成一个通用 JSON 库。

HTTP 层同样薄得克制：`http.cpp`（180 行）封装 libcurl，设 `CURLOPT_HTTP_VERSION` 为 `CURL_HTTP_VERSION_2TLS`、`CURLOPT_NOSIGNAL`、`CURLOPT_USERAGENT` 为 `microcodex`，用 `LOW_SPEED_LIMIT=1` 加 `LOW_SPEED_TIME` 实现空闲超时，用 `XFERINFOFUNCTION` 进度回调同时做取消检查和字节数上限——SSE 每次读回调里就靠这条上限拦住无界响应。

## 技能发现与它的扫描面

`skills.cpp`（182 行）去找 Codex 装的技能：根目录是 `$CODEX_HOME/skills`，未设置则 `~/.codex/skills`。它用 `recursive_directory_iterator`，选项里带 `follow_directory_symlink` 和 `skip_permission_denied`，在深度达到 6 时对目录 `disable_recursion_pending()`，累计条目上限 20,000——注意这个数是**遍历条目**的闸门，不是「最多支持两万个技能」。命中 `SKILL.md` 才去读前置元数据，只认 `name` 和 `description` 两个键。

解析器是专门为这一件事写的：必须首行是 `---` 并且后续有闭合的 `---`；支持 `>`、`>-`、`|`、`|-` 折叠块（缩进行会被单空格拼接）；单引号标量按 YAML 规则把 `''` 折成一个 `'`，双引号标量只处理 `\n` 和 `\t` 两种转义。校验也全是硬闸门：单个文件超过 1 MiB 直接跳过，`name` 超 128 字节或 `description` 超 1024 字节、或者内含换行，整条技能被丢弃。最后按名称再按路径排序。

拼装出的目录追加在基座提示词末尾，形如 `### Available skills` 下面每行 `- 名称: 描述 (file: 绝对路径)`。基座提示词里对怎么用这些技能写了一整节，触发条件是「用户点名了某个可用技能，或者当前任务明确匹配某条描述」，并且要求先完整读完 `SKILL.md` 再动手，读截断了就继续读到文件末尾。

由于扫描只看目录树，`.gitignore` 对它没有任何意义，符号链接也照样跟。在把技能目录指向仓库子目录这类用法下，误放的 `SKILL.md` 会进目录、进而进模型上下文。

## 构建、打包与那条七周的缝

`Makefile` 56 行，没有生成器、没有配置探测：`$(wildcard *.cpp)` 收 C++ 源文件，C 源文件写死成 `vendor/md4c/src/md4c.c`，依赖追踪靠 `-MMD -MP`。平台分支只有两条，Darwin 用 `clang++` 并先用 `xcrun` 问出系统根路径，Linux 用 `g++` 并加 `-lcrypto`，其他系统 `$(error Unsupported operating system: ...)`。C++ 侧 `-std=c++23 -O2 -Wall -Wextra -pthread`，C 侧 `-std=c17`，`LDLIBS` 只有 `-lcurl`。

CI 的两个 job 分别覆盖四个目标。Linux 侧值得逐条看，因为它把「产物能跑在多老的系统上」写成了断言：

```text
runs-on: ubuntu-24.04 / ubuntu-24.04-arm
container: debian:12
test "$(getconf GNU_LIBC_VERSION)" = "glibc 2.36"
readelf --version-info build/microcodex  # 取最高的 GLIBC_* 与 GLIBCXX_*
  -> 不得高于 GLIBC_2.36 与 GLIBCXX_3.4.30
```

两侧都会在构建前跑 `sh -n install.sh`、`sh -n launcher.sh` 和 `./install.sh --help`，构建后先 `make test` 再打包。Actions 版本钉在 `actions/checkout@v6` 与 `upload-artifact@v7`。

发布这条链是**手动触发**的，不是标签触发。`release.yml` 的 `on:` 只有 `workflow_dispatch`，需要一个必填输入 `tag`，并且要求当前工作流跑在默认分支上、标签符合 `^v[0-9]+\.[0-9]+\.[0-9]+([.-][0-9A-Za-z.-]+)?$`、同名发布和同名标签都不存在；通过后对**当时的 HEAD** 执行 `gh release create --generate-notes --latest`，再把这个提交交给 CI 复用同一条构建链，最后连同 `install.sh`、`launcher.sh` 及各自的 `.sha256` 一起上传。

这条链上有一个可观测的后果：截至本文核对，最近一次发布仍是 `v0.1.11-alpha`，发布于 2026-08-06，绑定提交 `2d88e4f5…`；而 main 已经走到 2026-09-25 的 `e511d45…`。也就是说用户用一键脚本装到的二进制，落后 main 约七周。每个发布 16 个产物，正好是 4 个平台 × 3（归档、归档校验和、裸文件校验和）再加安装脚本与启动脚本的 4 个文件。

一键安装的脚本是 `install.sh`（301 行）。它按平台选归档，然后对归档、裸二进制、启动脚本**分别**下载并比对 `.sha256`（校验文件本身还要先过一次格式检查，不合法就报 `The downloaded checksum file is invalid.`），算哈希时依次尝试 `sha256sum`、`shasum -a 256`、`openssl dgst -sha256`。可执行文件装到 `~/.local/bin/microcodex-bin`，启动脚本装成同目录的 `microcodex` 命令；两者都先以 `.名字.$$` 落盘再 `mv -f` 换入，中途失败不会留下半个可执行文件。PATH 的处理是按 `$os:$SHELL` 选配置文件——macOS 上 zsh 写 `~/.zprofile`、bash 写 `~/.bash_profile`，Linux 上对应 `~/.zshrc` 与 `~/.bashrc`，其余落 `~/.profile`——并且在写入前先看当前 PATH 和目标行是否已存在，重复运行不会堆重复行。三个环境变量能改行为：`MICROCODEX_RELEASE`（钉版本）、`MICROCODEX_INSTALL_DIR`、`MICROCODEX_RELEASES_URL`（换下载源）。

`launcher.sh`（156 行）每次启动拉目标平台的 `.sha256` 与本地实文件哈希比，不同就询问是否更新；只有 `[ -t 0 ] && [ -t 2 ] && [ -r /dev/tty ] && [ -w /dev/tty ]` 全成立才问，否则静默跳过。`MICROCODEX_NO_UPDATE_CHECK=1` 关掉检查，`MICROCODEX_FORCE_UPDATE_CHECK=1` 强制走更新路径。真正更新时它不自己搬文件，而是把 `install.sh` 连同校验和重新下载，再以 `MICROCODEX_INSTALL_DIR="$script_dir" MICROCODEX_NO_UPDATE_CHECK=1 sh install.sh` 递归调用安装器，最后 `exec "$REAL_BINARY" "$@"`。更新逻辑因此只有一份实现。

## 值不值这套取舍

把「用 C++23 写终端智能体」当成一个技术选型来评，MicroCodex 换到的和付出的都很具体。

换到的：一个 808 KiB 的文件，`otool -L` 三条依赖，启动时没有解释器或运行时要拉起；构建 4.3 秒；没有 GC、没有打包器、没有 lockfile，也因此没有整类供应链事故面。`std::expected` 让错误在系统调用层与协议层之间同一种类型流动。

付出的：门槛落在用户的编译器上。`-std=c++23` 意味着 macOS 得用较新的 Xcode/CommandLineTools、Linux 得 GCC 14 或 Clang 18 以上；作者自己那台机器上能过的编译，在用户机器上是一次现场调试。测试夹具还悄悄要求 Ruby ≥ 2.7，这条约束在 CI 上被 `ruby/setup-ruby@v1` 完全遮住了。

真正让人犹豫的是别的东西：这个项目 55 次提交里 52 次来自一个人，两个 vendored 依赖，零抽象层的 49 个文件平铺。它没有多后端、没有 MCP 支持（README 的 Known bugs 一节明确写着 `MCP support is not implemented yet`），也没有标准 OpenAI 端点路径——它整个假设自己就是 Codex 的一个客户端。这两条意味着它的复用价值主要在**读**而不在**用**。

值得抄走的东西有五条，都不依赖 C++：

1. 上下文压缩以完整轮次为最小单位，绝不把一次调用和它的输出拆开；估算用「字节除以 3」这种可解释的粗口径，而不是引入分词器。
2. 失败分「可续接」与「必须回滚」两类，前者留 `<turn_aborted>` 标记并照常落盘，后者连成功的中间工具轮也撤掉。把这条分界写进注释，再用 `T5` 与 `T9` 两组共十四个用例钉住，是这套代码最成熟的一处。
3. 并行工具调用的**结果**按模型给出的顺序回收，不按完成顺序，从而让回传的序列可复现。
4. 能力边界在用户文档、头文件注释和模型提示词里各说一遍，措辞不同而口径一致：拦不住的到底是什么，别留给读者猜。
5. JSON 层只暴露切片 API，用类型（`expected<optional<string_view>>`）把「不建 DOM」这个决定钉死。

## 出错时先看哪几处

报错原文大致落在四类，最常见的是前两类：测试夹具的 Ruby 版本、子模块没拉——这两处的失败信息今天在这台机器上都完整复现过。另两类是编译器与系统库不够新，以及把黑名单当沙箱用，后者的边界由 README 与 `CONTRIBUTING.md` 自己写明。

| 现象 | 先看 | 依据 |
|---|---|---|
| `make test` 大面积失败，报 `undefined method 'filter_map'` | Ruby 版本，`ruby -v` 要 ≥ 2.7 | `tests` 目录下那个 608 行的回环服务脚本第 25 行 |
| 编译期找不到 `termbox2.h` | 子模块没拉，`git submodule update --init --recursive` | Makefile 的 `-isystem vendor/termbox2` |
| Linux 编译期报找不到 `openssl/sha.h` | 缺 OpenSSL 开发文件，链接期还会缺 `-lcrypto` | Makefile 平台分支与 `oauth.cpp` 的条件包含 |
| 构建时抛 `std::runtime_error`，说管道或子进程创建失败 | 文件描述符或进程数耗尽；这是全仓库唯一主动抛异常的地方 | `bash.cpp` 的 `runProcess()` |
| `Could not restore conversation working directory` | 换机器或目录被删后 `resume`，路径已不存在 | `main.cpp` |
| 每次启动都提示有新版本 | 比对的是远端 `.sha256` 与本地哈希，产物在移动而版本没跟上 | `launcher.sh` |
| 明明登录过，却报 `Not logged in.` | `CODEX_HOME` 是否在两个进程间一致 | `defaultOAuthCredentialsPath()` |
| 危险命令没被拦 | 引号、`bash -c`、`git -c` 都会改变命中位置 | 本文探针输出 |

## 下一步读哪几段代码

如果只想拿走一两个做法，性价比最高的顺序是：

1. `api.cpp:494` 的 `sendUserMessage()`：可续接与回滚两组分支、以及回滚时的状态还原全在这一段，读完就知道一个可续接的会话状态机长什么样。
2. `context-compaction.cpp:44` 的 `plan()`：不到 90 行、零 IO、纯策略，是全文最适合移植的一段。
3. `main.cpp`：一个不依赖任何命令行工具（CLI）框架的入口能写多短，顺便看它如何把端点选择留在进程边界上以便测试。
4. `tool.h`：`Tool<T, S...>` 加上函数指针与普通函数之间的适配器，比任何抽象层都薄；顺带读那段 `NOTE: Yes, this smells a little.`，体会注释怎么写才不浪费。
5. `tests/run.sh` 与 `tests/TESTS.md`：把编译产物当黑盒做契约测试的最小可行做法，`expect_process` 只用了一个把预期 stderr 走 fd 3 的小花招。

## 五个自测题

1. 上下文窗口 272,000 词元、服务端返回 `auto_compact_token_limit` 为 260,000 时，`compact_at_tokens` 实际取多少？如果这一项缺失呢？
2. 一轮里模型先执行了两次成功的工具调用，随后返回一个 4xx 错误。磁盘上会多出这条轮次吗？下一次请求的输入序列里还有那两次调用吗？
3. `find -delete` 和 `bash -c 'rm -rf x'` 都不会被拦。要给用户一个可操作的解释，「词法黑名单」和「不是沙箱」这两句话各自覆盖到哪一步？
4. `microcodex list` 在没有凭证、没有网络的机器上正常退出。它靠的是哪三个实现细节？
5. 把 `MICROCODEX_RETAINED_CONTEXT_TOKENS` 设成一个极小的正整数，压缩会更频繁还是每次留下的原文更少？判断依据在哪一行？

## 参考

- 仓库与源码：<https://github.com/paoloanzn/microcodex>（本文核对基准 `e511d45`，main，2026-09-25）
- 最近一次发布：<https://github.com/paoloanzn/microcodex/releases/tag/v0.1.11-alpha>（2026-08-06，目标提交 `2d88e4f`）
- 问题列表与已知缺陷：<https://github.com/paoloanzn/microcodex/issues>、README 的 Known bugs 一节
- 测试说明：<https://github.com/paoloanzn/microcodex/blob/main/tests/TESTS.md>
- vendored 依赖：<https://github.com/termbox/termbox2>（MIT）、<https://github.com/mity/md4c>（MIT）
- PKCE：<https://www.rfc-editor.org/rfc/rfc7636>
- 许可证全文：<https://github.com/paoloanzn/microcodex/blob/main/LICENSE>
