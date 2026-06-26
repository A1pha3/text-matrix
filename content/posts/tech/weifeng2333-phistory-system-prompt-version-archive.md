---
title: "Phistory：把 7 个 agent 的 system prompt 变成 git 式可追溯的考古档案"
date: 2026-06-27T02:34:00+08:00
draft: false
categories:
  - 技术笔记
tags:
  - AI-Agent
  - 系统提示词
  - 开源项目
  - 可观测性
slug: weifeng2333-phistory-system-prompt-version-archive
author: 钳岳星君
description: "WEIFENG2333 的 Phistory v0.1.0（MIT，259 stars），把 Claude Code / Codex / OpenClaw / Hermes / Kimi / opencode / Pi 7 个 agent CLI 的 system prompt 自动抓取成版本化快照；用 claude-tap 拦截 + tree-sitter 静态提取 + volatile text 脱敏 + GitHub Actions 每小时抓取，是 agent system prompt 的「git 式考古档案」。"
---

# Phistory：把 7 个 agent 的 system prompt 变成 git 式可追溯的考古档案

## 核心判断

[WEIFENG2333/phistory](https://github.com/WEIFENG2333/phistory) 是 2026 年 5 月下旬开源的 agent system prompt 归档工具，发布 5 周到 259 stars / 20 forks。它解决的问题很具体：**agent CLI 每次发版，system prompt 都会改——新工具、新权限检查、新模型默认值、新确认规则——但没人留历史档案**。Phistory 把这件事做成 git 式版本化仓库：每个 agent 每次发版抓取一次，存到 `captures/<agent>/<version>/`，产物包括 `prompt.md` / `trace.jsonl` / `meta.json`，全 7 个 agent 跑下来 18 MB，截至 2026-06-25 共 615 次抓取。

支撑这个判断的是这个项目的规模和自动化深度：

| Agent | 最新版本 | 快照数 | 抓取时间 |
|---|---|---:|---|
| Claude Code | 2.1.193（2026-06-25）| 351 | 每小时 |
| opencode | 1.17.11（2026-06-25）| 77 | 每小时 |
| OpenClaw | 2026.6.10（2026-06-24）| 66 | 每小时 |
| Codex CLI | 0.142.2（2026-06-25）| 59 | 每小时 |
| Pi | 0.80.2（2026-06-23）| 26 | 每小时 |
| Kimi CLI | 1.48.0（2026-06-22）| 20 | 每小时 |
| Hermes Agent | v2026.6.19（2026-06-19）| 16 | 每小时 |
| **合计** | — | **615** | — |

GitHub Actions 每小时自动检查新版本，发现就抓取并 commit。托管的静态网页查看器 [phistory.cc](https://phistory.cc/) 把这些快照渲染成可对比的 diff 视图——任何研究者、审计者、写作者都可以在文章里「引用稳定的 prompt 快照」（README 自己的原话）。

把 Phistory 放进 agent 基础设施四联篇来看，它的卡位很清晰：

- **SkillSpector** 解决「skill 安不安全」（部署前扫描 + MCP runtime gating）
- **Virtue AI / DAO Code** 解决「agent 本身做得好不好」（人才 + 工程）
- **FTShare SDK** 解决「skill 怎么拿数据」
- **Phistory** 解决「agent 的 system prompt 怎么被研究、怎么被审计、怎么被引用」

它不是 agent 框架、不是 prompt 工程工具、不是 LLM 可观测性平台——它是一个 **prompt 考古档案**，类比 npm / PyPI 是 agent prompt 的版本化索引。CLAUDE.md / AGENTS.md 这些项目级指令每发版都在变，但没有公共存档；Phistory 是第一个把这件事做扎实的项目。

## 学习目标

读完本文后，你应当能够：

1. 说出 Phistory 在 agent 基础设施生态里的卡位（不是 agent 框架、不是 prompt 工具、不是可观测性平台——是 prompt 考古档案），以及它和 SkillSpector / Virtue AI / DAO Code / FTShare SDK 的关系。
2. 解释 claude-tap 怎么在不调用真实模型的前提下拦截 agent CLI 的 HTTP 请求、提取 system prompt，以及为什么这种「capture-only」模式比 mock LLM API 更可靠。
3. 列出 9 类 volatile text 替换模式（cch hash / OS version / 日期 / 时区 / 路径 / Bearer token 等），并解释为什么这些脱敏让不同时间、不同机器抓取的快照仍能稳定 diff。
4. 描述 Claude Code 静态 prompt 提取（tree-sitter + 12 条正则 + 已知 prompt 哈希数据库）怎么抓到 capture 时**没有出现在 HTTP 请求里**的 prompt（比如条件分支另一侧或拼字符串模板）。
5. 说出 GitHub Actions 每小时抓取的具体流水线（捕获最新版本 → 写入 captures/ → render-index → render-site → commit 到 main），以及为什么 archive 仓库要随 source 同步 push。
6. 用 `phistory capture --latest --agents ...` 跑一次本地抓取，看 5 个文件落在 `captures/<agent>/<version>/` 里，理解每个文件的作用。

## 目录

- [核心判断](#核心判断)
- [学习目标](#学习目标)
- [生态卡位：prompt 考古档案](#生态卡位prompt-考古档案)
- [总览图：一次抓取的 5 步流水线](#总览图一次抓取的-5-步流水线)
- [claude-tap capture-only 模式](#claude-tap-capture-only-模式)
- [9 类 volatile text 替换：让 diff 可复现](#9-类-volatile-text-替换让-diff-可复现)
- [任务如何流过系统：一次完整抓取](#任务如何流过系统一次完整抓取)
- [Claude Code 静态 prompt 提取](#claude-code-静态-prompt-提取)
- [GitHub Actions 自动化流水线](#github-actions-自动化流水线)
- [Python 模块结构与依赖图](#python-模块结构与依赖图)
- [决策启示：研究者 / agent 作者 / 审计 / 普通用户各看什么](#决策启示研究者--agent-作者--审计--普通用户各看什么)
- [采用顺序与边界](#采用顺序与边界)
- [参考资料](#参考资料)

## 生态卡位：prompt 考古档案

Phistory 的卡位要先从「不是什么」讲起。它不是：

- **agent 框架**——它不调用 LLM、不编排工作流、不跑工具
- **prompt 工程工具**——它不优化 prompt、不做 A/B、不评估质量
- **LLM 可观测性平台**——它不记录请求 / 响应 / token 用量 / 延迟

Phistory 是 **prompt 考古档案**——一个 git 式版本化仓库，把 agent 每次发版的 system prompt 当作源码一样归档。它做的事不是分析，而是「让 prompt 变得可引用、可对比、可追溯」。

类比几个熟悉的工具会更清楚：

| 工具 | 类比物 | 类比维度 |
|---|---|---|
| **npm registry** | Phistory | 第三方包 + 版本化 + 可下载 |
| **crates.io** | Phistory | 包元数据 + 版本历史 + tarball |
| **npm view <pkg> versions** | Phistory capture | 列出所有版本号 |
| **npm diff x.y.z a.b.c** | Phistory site | 跨版本 diff |
| **GitHub Archive (GH Archive)** | Phistory captures/ | 全量事件流 |
| **PEP 8 / RFC 2119** | Phistory captures/ | 标准文本的版本化归档 |

特别值得注意的是 README 里那句：「在文章、研究笔记、审计或排障记录里引用稳定的提示词快照」——这是一个被低估的写作场景。**研究 agent 行为时引用的 prompt 必须可追溯到具体版本号，否则论证不成立**。Phistory 把这变成 `https://txtmix.com/posts/...` 风格的稳定 URL。

## 总览图：一次抓取的 5 步流水线

```text
GitHub Actions / phistory capture --latest
                  │
                  ▼
        ┌──────────────────────┐
        │ packages.latest_     │ npm / PyPI / GitHub release
        │ version(agent)       │ 查 latest 版本号 + tarball
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ packages.install_    │ 装到 .phistory-cache/installs/
        │ agent(version)       │ 不污染全局 npm/pip
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ capture.capture_     │ 跑 claude-tap 拦截 HTTP
        │ target()             │ 不调用真实模型
        └──────────┬───────────┘
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
   prompt.md   trace.jsonl  meta.json
   （prompt    （完整 SSE    （版本 +
   文本）      请求日志）    时间 + 命令）
                   │
                   ▼
        ┌──────────────────────┐
        │ static_prompts.      │ Claude Code 专属：
        │ extract_static_      │ tree-sitter 解析 JS
        │ prompts()            │ 抓 HTTP 里没出现的 prompt
        └──────────┬───────────┘
                   │
                   ▼
   static-prompts.md / .json / candidates.json
                   │
                   ▼
        ┌──────────────────────┐
        │ capture_normalize    │ volatile text 脱敏
        │ _VOLATILE_TEXT_      │ cch / OS / 日期 / 时区 / 路径 / Bearer
        │ PATTERNS             │
        └──────────┬───────────┘
                   │
                   ▼
            captures/<agent>/<version>/
            全部文件已稳定字节，可 diff
```

每一步都对应一个具体工程问题：

| 步骤 | 问题 | 方案 |
|---|---|---|
| `packages.latest_version` | 怎么知道 agent 出了新版本？| 查 npm / PyPI / GitHub release 元数据 |
| `packages.install_agent` | 装包怎么不污染全局环境？| `.phistory-cache/installs/<agent>/<version>/` |
| `capture_target` | 怎么拿 system prompt 不花 token 钱？| `claude-tap --tap-no-live` 拦截 HTTP |
| 静态提取 | HTTP 请求里只有运行时 prompt，模板呢？| tree-sitter + 12 条正则 + 已知 hash |
| volatile 替换 | 不同时间抓的快照怎么 diff？| 9 类正则替换为 `$PHISTORY_*` 占位符 |

## claude-tap capture-only 模式

Phistory 的核心依赖是 [claude-tap](https://github.com/liaohch3/claude-tap)——一个 Python 编写的「agent CLI HTTP 拦截器」。它的工作机制：

1. 启动 agent CLI 子进程
2. 拦截所有出向 HTTP 请求（向 Anthropic / OpenAI / 自家 endpoint 的）
3. 把 HTTP 请求里的 system prompt 提取到本地文件
4. **不调用真实 LLM**——直接返回 mock response，让 agent CLI 正常退出

`registry.py` 里给每个 agent 写的 `run_args` 就是这个 capture-only 命令的精确参数：

```python
CLAUDE_CODE = AgentSpec(
    id="claude-code",
    package="@anthropic-ai/claude-code",
    tap_client="claude",
    fake_env={"ANTHROPIC_API_KEY": "fake"},
    run_args=(
        "--no-yolo",
        "--",
        "--no-session-persistence",
        "-p", "Reply with one short sentence.",
    ),
)
```

`"-p Reply with one short sentence."` 是关键——它给 agent 一个最小 prompt，让 agent 启动并发出请求，但不真的执行任务。`--no-session-persistence` 让 agent 跑完不留任何状态文件。

`capture.py:62-78` 处理两类重试：

```python
if _needs_claude_session_persistence_retry(target, result):
    remove_if_exists(tap_output_dir)
    prompt_path.unlink(missing_ok=True)
    argv = _without_arg(argv, "--no-session-persistence")
    result = run(argv, cwd=Path(work_dir), env=env, ...)

if _needs_codex_api_key_retry(target, result):
    remove_if_exists(tap_output_dir)
    prompt_path.unlink(missing_ok=True)
    env = {**env, "OPENAI_API_KEY": "phistory-fake-api-key"}
    result = run(argv, cwd=Path(work_dir), env=env, ...)
```

Claude Code 某些版本会因为 `--no-session-persistence` flag 不存在而失败——去掉重跑。Codex CLI 某些版本会因为缺 `OPENAI_API_KEY` 而提前退出——注入 fake key 重跑。这两个 retry 是「agent 行为跨版本漂移」的工程应对：**agent 越成熟，参数化越多，capture 脚本必须跟着调**。

**测的是什么、不能推出什么**：capture-only 模式测的是「agent 启动时发送的 system prompt」。**不能推出**「agent 在交互过程中根据上下文动态拼接的 prompt」（比如 Claude Code 的 `claude.md` 项目指令、用户消息中的工具结果、hook 注入的系统提醒）。这些动态部分在 archive 快照里看不到，但确实是 agent 实际运行时收到的。

## 9 类 volatile text 替换：让 diff 可复现

`capture.py:18-32` 列出的 `_VOLATILE_TEXT_PATTERNS` 是这个项目最让人拍案的设计：

```python
_VOLATILE_TEXT_PATTERNS = (
    (re.compile(r"\bcch=[^;\s]+"), "cch=<normalized>"),
    (re.compile(r"(?m)^ - OS Version: .+$"), " - OS Version: $PHISTORY_OS_VERSION"),
    (re.compile(r"Today's date is \d{4}[-/]\d{2}[-/]\d{2}\."), "Today's date is $PHISTORY_DATE."),
    (re.compile(r"The current date and time in ISO format is `[^`]+`\."), 
                "The current date and time in ISO format is `$PHISTORY_DATETIME`."),
    (re.compile(r"(?m)^Conversation started: .+$"), "Conversation started: $PHISTORY_DATETIME"),
    (re.compile(r"<current_date>\d{4}-\d{2}-\d{2}</current_date>"), "<current_date>$PHISTORY_DATE</current_date>"),
    (re.compile(r"<timezone>[^<]+</timezone>"), "<timezone>$PHISTORY_TIMEZONE</timezone>"),
    (re.compile(r"\$PHISTORY_HOME/\.claude/projects/-tmp-phistory-work-[^/\s]+"),
                "$PHISTORY_HOME/.claude/projects/$PHISTORY_PROJECT"),
    (re.compile(r"Bearer phistory-[A-Za-z0-9_-]+"), "Bearer <redacted>"),
)
```

9 类替换覆盖了 agent prompt 里**所有和时间、环境、机器相关的不稳定信号**：

| 类别 | 不稳定源 | 替换为 |
|---|---|---|
| Anthropic cache hash | `cch=<token>` 每次请求新生成 | `cch=<normalized>` |
| OS 指纹 | `- OS Version: macOS 14.5.1 ...` | `$PHISTORY_OS_VERSION` |
| 日期 | `Today's date is 2026-06-26.` | `$PHISTORY_DATE.` |
| 时间戳（英文）| `The current date and time in ISO format is 2026-06-26T...` | `$PHISTORY_DATETIME` |
| 会话启动时间 | `Conversation started: ...` | `$PHISTORY_DATETIME` |
| 日期（XML 包装）| `<current_date>2026-06-26</current_date>` | `<current_date>$PHISTORY_DATE</current_date>` |
| 时区 | `<timezone>Asia/Shanghai</timezone>` | `<timezone>$PHISTORY_TIMEZONE</timezone>` |
| 项目路径 | `$PHISTORY_HOME/.claude/projects/-tmp-phistory-work-<random>` | `$PHISTORY_HOME/.claude/projects/$PHISTORY_PROJECT` |
| Bearer token | `Bearer phistory-<random>` | `Bearer <redacted>` |

这些替换让 `diff 2026-06-25-claude-code-2.1.193 prompt.md` 在不同机器、不同时刻抓取的结果**字节相同**——这是 agent prompt 在 archive 场景下的字节稳定纪律。

「Diff 可复现」是 Phistory 这种 archive 类工具的核心质量指标。如果两次抓取的 prompt.md 字节不同，archive 的可信度就崩了——研究者引用 `2.1.193 prompt.md` 时怎么知道他引用的是哪个版本的「2.1.193」？Phistory 用这套替换模式把「时间/机器相关」的不确定性从 archive 里彻底剔除。

`capture.py:411` 把这些 pattern 应用到 prompt.md：

```python
for pattern, replacement in _VOLATILE_TEXT_PATTERNS:
    text = pattern.sub(replacement, text)
```

## 任务如何流过系统：一次完整抓取

为了让 5 步流水线抽象落地，看一个具体的「抓 Claude Code 最新版」怎么走完整流程。

**命令**：

```bash
uv run phistory capture --latest --agents claude-code
```

**Step 1：解析参数 + 注册表查找**

`cli.main()` 解析 `--latest --agents claude-code`，调 `capture_latest(['claude-code'], ...)`。`registry.get_agent('claude-code')` 返回 `CLAUDE_CODE` 这个 `AgentSpec`（含 npm 包名、tap_client、fake_env、run_args、node_runtime 等）。

**Step 2：查最新版本**

```python
def latest_version(agent):
    if agent.source == "npm":
        return _npm_latest(agent)
```

`_npm_latest(CLAUDE_CODE)` 查 `https://registry.npmjs.org/@anthropic-ai/claude-code/latest`，拿到 `{"version": "2.1.193", "published_at": "2026-06-25T19:05:08.367Z", "tarball_url": "..."}`。

**Step 3：装包到隔离目录**

```python
install_dir = (cache_dir / "installs" / "claude-code" / "2.1.193").resolve()
bin_dir = packages.install_agent(CLAUDE_CODE, "2.1.193", install_dir)
```

`_install_npm()` 跑 `npm install --no-audit --no-fund @anthropic-ai/claude-code@2.1.193` 到 `install_dir`。**不污染全局 npm**——这是 archive 工具的关键 hygiene 纪律。

**Step 4：跑 capture_target**

```python
result = capture_target(CaptureTarget(agent, version, root), cache_dir=cache_dir, ...)
```

`capture_target()` 走完整 capture 逻辑：

```python
try:
    with (TemporaryDirectory(prefix="phistory-home-") as home_dir,
          TemporaryDirectory(prefix="phistory-work-") as work_dir):
        env = _capture_env(target, bin_dir, Path(home_dir))
        env["PWD"] = str(Path(work_dir))
        argv = _capture_command(target, prompt_path, tap_output_dir)
        result = run(argv, cwd=Path(work_dir), env=env, 
                     timeout=CAPTURE_TIMEOUT_SECONDS, check=False)
        if _needs_claude_session_persistence_retry(target, result):
            ... # retry without --no-session-persistence
        if _needs_codex_api_key_retry(target, result):
            ... # retry with fake API key
```

两个 `TemporaryDirectory` 是 `~/.phistory-home-<random>` 和 `~/.phistory-work-<random>`——临时 HOME 和临时工作目录，capture 完就清。`CAPTURE_TIMEOUT_SECONDS = 1800`（30 分钟），防止 agent hang 死锁。

**Step 5：拷贝 trace + 写 meta + 静态提取（Claude Code）**

```python
copy_trace(latest_trace(tap_output_dir), target)
write_meta(target, meta_data)
```

`copy_trace()` 把 claude-tap 生成的 `trace_<n>.jsonl` 拷到 `captures/claude-code/2.1.193/trace.jsonl`。`write_meta()` 写 14 字段的元信息（含 `tarball_url`、`captured_at`、`command` 完整 argv、`duration_seconds` 等）。

`extract_static_prompts()` 仅对 Claude Code 触发（`if target.agent.id != "claude-code": return None`），输出 3 个文件到同目录。

最后，`_normalize_volatile_text()` 把 9 类 volatile 文本替换为 `$PHISTORY_*` 占位符，让 prompt.md 在字节级稳定。

## Claude Code 静态 prompt 提取

Claude Code 比其他 agent 多一步——`extract_static_prompts()` 用 tree-sitter 解析 npm 包里的 JS 源码，从**模板字符串字面量**里抓 system prompt 候选。

这条路径解决的具体问题是：**claude-tap 抓到的 prompt 是 agent 运行时实际发给 LLM 的，但 npm 包里很多 prompt 是模板字符串、条件分支、循环拼接出来的——这些在运行时可能因为分支条件不同根本没被发送**。

`extract.py` 的核心是 12 条正则，覆盖模板字符串里各种 prompt-like 模式：

```python
STATIC_PROMPT_DOUBLE_TERNARY_EXPR_RE = re.compile(
    r'\$\{[^{}\n?]{1,400}\?"(?P<yes>(?:[^"\\\n]|\\.)*)":"(?P<no>(?:[^"\\\n]|\\.)*)"\}'
)
STATIC_PROMPT_SINGLE_TERNARY_EXPR_RE = re.compile(
    r"\$\{[^{}\n?]{1,400}\?'(?P<yes>(?:[^'\\\n]|\\.)*)':'(?P<no>(?:[^'\\\n]|\\.)*)'\}"
)
# ... 10 条更多
```

比如 `STATIC_PROMPT_DOUBLE_TERNARY_EXPR_RE` 匹配 `${condition ? "yes-prompt" : "no-prompt"}` 这种模板——如果运行时分到 `condition=false`，claude-tap 抓到的只有 `no-prompt`，但 `yes-prompt` 也是 agent 设计的一部分，archive 里应该留底。

`_prune_static_candidates()` 用「已知 prompt 哈希数据库」过滤：

```python
def _prune_static_candidates(agent_id, candidates):
    known_hashes = known_content_hashes(agent_id)
    return [c for c in candidates if _keep_static_candidate(c, known_hashes)]

def _keep_static_candidate(candidate, known_hashes):
    if candidate.score > 0:
        return True
    if content_hash(candidate.content) in known_hashes:
        return True
    if _has_short_instruction_marker(candidate.content):
        return True
```

3 类保留：

1. **高评分候选**——自动评分 > 0（可能是真的 prompt）
2. **已知 prompt 哈希匹配**——`known_content_hashes` 数据库里的稳定 prompt（版本间不变）
3. **短指令标记**——含 "you are" / "always" / "never" 等强 prompt-like 标记

`phistory/static_prompts/catalogs/claude-code/known-prompts.json` 是这个哈希数据库——它记录了「这条 prompt 在历史上多个版本出现过，是稳定 prompt」。这避免每次发版都要人工标注新 prompt。

`STATIC_CANDIDATES_MIN_LENGTH = 20`——少于 20 字符的候选直接丢弃，过滤掉日志字符串、错误消息等非 prompt 内容。

最终静态提取输出 3 个文件：

- `static-prompts.md` — 人类可读的高分候选
- `static-prompts.json` — 机器可读的结构化结果（StaticPromptMatch 列表）
- `static-candidates.json` — 原始候选（refresh-candidates 时用）

`refresh-candidates` 是关键开关——默认从归档里的 `static-candidates.json` 重放（旧版本不重装 npm），加 `--refresh-candidates` 才重装 + 重新 tree-sitter 解析。这是 archive 工具的「快速重读」模式。

## GitHub Actions 自动化流水线

Phistory 的自动化很轻——单个 workflow 每小时跑一次：

1. **捕获最新版本**（`phistory capture --latest --agents ...`）
2. **回填区间**（可选，针对新发现的 agent 类型）
3. **重建静态 prompt**（Claude Code 专属，`phistory extract-static claude-code --latest-captured 10`）
4. **重建索引**（`phistory render-index`，生成 README.md + README_zh.md + docs/captures.md + captures/index.json）
5. **重建网站**（`phistory render-site`，生成 index.html 单文件 HTML）
6. **commit 到 main**（README 和 captures/ 都跟 source 同步）

`render.py:render_index` 同时生成中英两个 README——这个双语文档生成是 archive 类工具的最佳实践，让中文研究者不用翻译就能引用。

`site.py:render_site` 生成单文件 HTML——把 manifest 嵌进 `__PHISTORY_MANIFEST__` 占位符，浏览器端 JS 解析。这样静态网站不依赖后端 API、不依赖外部 CDN，离线可用。

`index.json` 让第三方可以拉原始数据——例如有人想写个 Python 脚本分析 Claude Code 351 个版本的 prompt 演化，可以直接 `curl https://phistory.cc/captures/index.json` 拿数据。

## Python 模块结构与依赖图

```text
                cli.py
                  │
        ┌─────────┼─────────┐
        │         │         │
        ▼         ▼         ▼
    workflow  packages    registry
        │         │         │
        │         │         │
        ├────┬────┴────┬────┤
        │    │         │    │
        ▼    ▼         ▼    ▼
    capture  models  storage  subprocesses
        │
        ├────┬────┐
        │    │    │
        ▼    ▼    ▼
   storage  static_prompts/  trace-copy
                │
                ├── javascript.py (tree-sitter)
                ├── bun.py
                ├── catalog.py
                └── models.py
```

每个模块职责清晰：

| 模块 | 职责 | 测试覆盖 |
|---|---|---|
| `cli.py` | argparse + 5 个子命令 dispatch | 集成测试 |
| `capture.py` | capture_target + volatile 替换 + retry | 完整 |
| `registry.py` | 7 个 AgentSpec 静态注册表 | 部分 |
| `models.py` | `@dataclass(frozen=True)` 类型 | 间接 |
| `packages.py` | npm / PyPI / GitHub release 版本解析 | 部分 |
| `subprocesses.py` | subprocess.run 包装 | 间接 |
| `storage.py` | 文件 I/O + 目录准备 | 间接 |
| `render.py` | README/中英 README/JSON/捕获文档生成 | 部分 |
| `site.py` | 单文件 HTML 静态网站生成 | 部分 |
| `workflow.py` | capture_latest / backfill / iter_backfill | 完整 |
| `static_prompts/` | Claude Code 静态 prompt tree-sitter 提取 | 部分 |

`registry.py` 的设计值得注意——**所有 agent 元数据都是模块级常量**，加新 agent 只在 `registry.py` 加一个 `AgentSpec`、再在 `AGENTS` 字典里 register 一次即可。`capture_target` 拿到的 agent 配置完全是声明式的，命令构造、retry 策略、env 设置都从 AgentSpec 字段读。这种「配置即代码」让新 agent 接入控制在 30 行代码 + 测试的范围。

## 决策启示：研究者 / agent 作者 / 审计 / 普通用户各看什么

Phistory 对四类读者的信号不同：

**研究者**——agent 行为研究、文章写作、教学示例引用的稳定 prompt 来源。具体动作：

- 引文写作：「Claude Code 在 2.1.193（2026-06-25）的 system prompt 是……（见 phistory.cc/captures/claude-code/2.1.193/prompt.md）」，任何读者都能复现
- 对比研究：写脚本跨多个版本拉 `prompt.md`，分析「Anthropic 何时加入 hook 提醒」「Codex 何时加入文件锁机制」
- 跨 agent 对比：同一时间点对比 7 个 agent 的 prompt 设计差异，写「agent 安全策略对比」

**Agent 作者**——发布新版本时要注意 prompt 变化的可追溯性。具体动作：

- 在 `CHANGELOG.md` 里记录「system prompt 改了哪些段」，对应 phistory.cc 上的 diff 链接
- 如果你的 agent 不在 Phistory 列表（phistory 支持 7 个主流 agent，其他 agent 也可加入），给 phistory 提 PR 加 `AgentSpec`
- 静态 prompt（模板字符串里的 prompt）容易在发版时无意修改，Phistory 的 `static-prompts.json` diff 是检查这类变动的工具

**审计 / 合规**——企业 agent 部署的 prompt 留痕。具体动作：

- 在 CI 里加 `phistory capture --agents <your-agent>` 检查 prompt 是否被意外修改
- 对外包 agent 做 prompt baseline，diff 出「第三方在你环境里实际用了什么 prompt」
- 在合规报告里附 prompt snapshot 链接，证明「agent 在 X 日期确实是这个行为」

**普通用户**——观察 agent 设计演化、写博客 / 教学文章引用。具体动作：

- 看 [phistory.cc](https://phistory.cc/) 的「跨版本 diff」视图
- 用 `phistory capture --latest --agents openclaw` 在自己机器跑一次本地抓取（5-10 分钟），看自己版本和 archive 里有什么差异
- 写「我用的 agent 和 archive 不一致」报告 → 给 phistory 提 issue

## 采用顺序与边界

对想用 Phistory 的读者，按以下顺序最经济：

**第一步：访问 [phistory.cc](https://phistory.cc/) 看 diff 视图**——5 分钟入门，看 Claude Code 跨 351 个版本 prompt 演化路径，理解这个工具能解决什么问题。

**第二步：本地跑 `uv sync && uv run phistory capture --latest --agents claude-code`**——确认工具链通，看 5 个文件落到 `captures/claude-code/<version>/`。这一步会下载 ~50 MB npm 包。

**第三步：跑 `phistory render-site` 看本地 HTML**——把 `index.html` 在浏览器打开，对比托管的 phistory.cc，看自己机器抓的快照是否一致（验证 volatile text 替换的正确性）。

**第四步：跨版本对比自己关心的 prompt 段**——写一个小 Python 脚本拉 `captures/claude-code/<v1>/prompt.md` 和 `captures/claude-code/<v2>/prompt.md`，diff 出关心的段。

**第五步：贡献给 archive**——发现新 agent / 发现 volatile text 漏了 / 发现 capture 脚本有 bug，给 phistory 提 PR。

**不一定要做的事**：

- 不要把 Phistory 当 agent 框架用——它不发 prompt、不跑 agent、不评估响应
- 不要假设 archive 完整覆盖 agent 行为——archive 只捕获启动时的 system prompt，不捕获动态拼接
- 不要在 archive 之外引用 prompt「片段」——必须带版本号和 commit hash，否则论证不成立
- 不要把 `static-candidates.json` 当权威 prompt 列表——它是 raw 候选，需要人工 / catalog 过滤

**边界**：Phistory 主要覆盖「主流 agent CLI 的 system prompt 快照」，对以下场景只能部分覆盖：

- **私有 / 自建 agent**——不在 7 个支持列表里，可以提 PR 加 AgentSpec
- **运行时动态 prompt**——根据 user message / tool result / hook 拼接的 prompt 不在 archive 范围
- **prompt 效果评估**——archive 只看 prompt 文本，不评估「这个 prompt 让 agent 表现更好」
- **多语言 / 多区域 prompt 变体**——archive 是单一 snapshot，不区分 locale

最后一个边界对未来 agent 作者特别重要——如果你发布 agent 时有「英文 prompt」和「中文 prompt」两个版本，archive 工具还没准备好同时抓两个版本。可以给 phistory 提需求扩展。

## 参考资料

- [WEIFENG2333/phistory GitHub 仓库](https://github.com/WEIFENG2333/phistory)，MIT 协议，截至 2026-06-27 共 259 stars / 20 forks，v0.1.0
- [phistory.cc 静态网页查看器](https://phistory.cc/)——7 个 agent 615 个快照的可对比 diff 视图
- [claude-tap](https://github.com/liaohch3/claude-tap)——Phistory 核心依赖，agent CLI HTTP 拦截器
- [src/capture.py](https://github.com/WEIFENG2333/phistory/blob/main/phistory/capture.py)——capture_target 主体 + `_VOLATILE_TEXT_PATTERNS`
- [src/registry.py](https://github.com/WEIFENG2333/phistory/blob/main/phistory/registry.py)——7 个 agent 的 AgentSpec 注册表
- [src/models.py](https://github.com/WEIFENG2333/phistory/blob/main/phistory/models.py)——AgentSpec / VersionInfo / CaptureTarget dataclass 定义
- [src/static_prompts/extract.py](https://github.com/WEIFENG2333/phistory/blob/main/phistory/static_prompts/extract.py)——Claude Code 静态 prompt 提取
- [src/site.py](https://github.com/WEIFENG2333/phistory/blob/main/phistory/site.py)——单文件 HTML 静态网站生成
- [captures/claude-code/2.1.193/prompt.md](https://github.com/WEIFENG2333/phistory/blob/main/captures/claude-code/2.1.193/prompt.md)——Claude Code 最新版 prompt 快照（带 volatile text 替换）
- [captures/openclaw/2026.6.10/prompt.md](https://github.com/WEIFENG2333/phistory/blob/main/captures/openclaw/2026.6.10/prompt.md)——OpenClaw 当前版本 prompt 快照
- [NVIDIA SkillSpector：让 26% 不安全的 agent skill 无处藏身](https://txtmix.com/posts/tech/nvidia-skillspector-agent-skill-security-scanner/)——agent skill 安全（系列）
- [Meta 挖角 Virtue AI 三位创始人](https://txtmix.com/posts/tech/meta-poaches-virtue-ai-agent-security-talent-war/)——agent 安全人才战（系列）
- [FTShare Python SDK](https://txtmix.com/posts/tech/ftshare-python-sdk-financial-data-agent-access-layer/)——agent skill 数据接入（系列）
- [DAO Code：在 DeepSeek V4 上做 cache engineering 的终端编码 agent](https://txtmix.com/posts/tech/tigicion-dao-code-deepseek-coding-agent-cache-engineering/)——agent 工程（系列）
