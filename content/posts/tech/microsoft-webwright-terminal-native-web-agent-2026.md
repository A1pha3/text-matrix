---
title: "Webwright：一个 Terminal 就够了——把 Coding Model 变成 Browser Agent 的 ~1.5k LoC 工程"
date: "2026-06-25T15:19:26+08:00"
slug: "microsoft-webwright-terminal-native-web-agent-2026"
description: "微软研究院（Microsoft Research）Lu Yadong 等人在 microsoft/Webwright（5.6k stars）里给出的反多 agent 框架 web agent 思路：把 LLM 放回终端，让它写 Python 脚本启动、检查、丢弃浏览器会话，最终把一次 web 任务压缩成一个 re-runnable Python script。本文拆解其 ~1.5k LoC 的 4 抽象（terminal/browser/script/skill）、与 SWE-agent 的设计血缘、对 Claude Code/Codex/OpenClaw/Hermes 的统一 skill 集成，以及在 Online-Mind2Web 86.7%、Odysseys 60.1% 的 long-horizon 基准上为什么 work、又为什么不适合 short interactive task。"
draft: false
categories: ["技术笔记"]
tags: ["Webwright", "Microsoft Research", "Browser Agent", "Playwright", "Code-as-Action", "Coding Agent", "SWE-agent", "Claude Code Plugin", "OpenAI Codex Plugin", "OpenClaw", "Hermes Agent", "Online-Mind2Web", "Odysseys", "Web Agent", "Terminal Native"]
hiddenFromHomePage: false
---

# Webwright：一个 Terminal 就够了——把 Coding Model 变成 Browser Agent 的 ~1.5k LoC 工程

## §1 先给判断

Webwright 是 2026 年 web agent 方向里**最不像 web agent 框架的 web agent 框架**。它由微软研究院 Lu Yadong、Xu Lingrui、Huang Chao、Awadallah Ahmed 在 2026-05-04 公开发布，截至本文动笔时（2026-06-25）已积累 5,628 GitHub stars、43 次 commit。仓库 README 的副标题是 *"Turn Your Coding Models to Be State-of-the-art Browser Agents"*——它假设你已经有一个能写代码的 coding model，然后用 **"一个 terminal + 一个 browser + 一个 model"** 三件套替代了所有多 agent 框架、图引擎、plugin layer 和 hidden orchestration。

核心判断只有一条：**当 LLM 已经能写代码、能 debug 代码、能用 Python 调用 Playwright 时，再把模型锁在一个"每步预测一个 DOM click 或 xy 坐标"的浏览器 session 里，是对模型能力的浪费**。Webwright 把 web 任务的"持久化产物"从浏览器 session 换成本地 workspace 里一个 re-runnable Python script——一次浏览历史就是一段可以重跑、可以改造、可以分享的代码。

它和 browser-use、Stagehand、agent-browser 同台但分叉——更接近 **SWE-agent 思路（"coding agent + terminal"）在 web 任务上的复刻**，和 mini-swe-agent 共享同一条"minimal agent loop"设计血缘。

## §2 阅读路径

- **只想看架构**：§3 总览图 → §4 4 个核心抽象 → §5 write code → execute → inspect 循环
- **想看任务怎么流过系统**：§7 一个 long-horizon task 的完整 trajectory
- **想看性能怎么读**：§9 Online-Mind2Web / Odysseys 的具体含义 + 不能推出什么
- **想看 plugin 集成**：§8 Claude Code / Codex / OpenClaw / Hermes 共享 `skills/webwright/`
- **想看采用顺序**：§13 谁该先用、谁可以等等

## §3 一张总览图：Webwright 和传统 web agent 的根本分歧

### 3.1 传统 web agent 的形态

今天绝大多数 web agent（browser-use、Stagehand、agent-browser）把浏览器 session 当成"工作区"。每一步：

1. 模型接收当前页面（截图 / DOM snapshot / accessibility tree）
2. 模型预测"下一步操作"——一个 click、一个 type、一个 DOM selector、或者一条 tool call
3. harness 执行操作，刷新观察
4. 循环直到任务完成

这个 harness 形态在 LLM 弱的时候是必要的——它把"web 交互"分解成模型可以预测的原子动作。但当模型已经能写能 debug Python 时，**这层 harness 本身成了瓶颈**。

### 3.2 Webwright 的反方向

Webwright 把模型从"逐动作预测器"升级成"程序作者"：

| 维度 | 传统 web agent | Webwright |
|------|----------------|-----------|
| 模型角色 | 预测下一个原子动作 | 写出整段可执行 Python |
| 浏览器角色 | 持久化工作区（state holder） | 一次性环境（spawn → inspect → discard） |
| 状态存哪 | browser session（session cookie、DOM、tab） | 本地 workspace（`final_script.py`、screenshots、logs） |
| 任务完成后产物 | 一段被遗忘的 session history | 一个 re-runnable Python script |
| Loop 形状 | observe → predict next action → execute → repeat | write code → execute → inspect screenshots → repair |
| Action space | Indexed click/type/select（原子动作） | Free-form Python（脚本本身） |
| 出错怎么办 | 重试同一个原子动作 | 修代码，重新跑 |
| 中断后能续吗 | 受 session state 限制 | 完整：脚本在文件系统里 |

### 3.3 系统地图

```
Webwright
├── src/webwright/
│   ├── agents/
│   │   └── default.py            # ~450 行核心 agent loop（DefaultAgent）
│   ├── environments/             # ~570 行 Playwright browser workspace
│   ├── tools/                    # image_qa, self_reflection
│   ├── models/
│   │   ├── base.py               # Model 接口 + 统一错误归一化
│   │   ├── openai_model.py       # OpenAI backend（~150-200 行）
│   │   ├── anthropic_model.py    # Anthropic backend（~150-200 行）
│   │   └── openrouter_model.py   # OpenRouter backend（~150-200 行）
│   ├── config/
│   │   ├── base.yaml             # agent + environment 默认配置
│   │   ├── model_openai.yaml     # OpenAI backend 专属
│   │   └── model_claude.yaml     # Anthropic backend 专属
│   └── run/cli.py                # ~150 行 CLI 入口（Typer）
├── skills/webwright/             # 跨 host 的统一 skill 描述
│   ├── SKILL.md
│   └── commands/
│       ├── run.md                # /webwright:run（one-shot）
│       └── craft.md              # /webwright:craft（reusable CLI tool）
├── .claude-plugin/plugin.json    # Claude Code 插件清单
├── .codex-plugin/plugin.json     # OpenAI Codex 插件清单
├── assets/
│   └── task_showcase/            # Flask dashboard 展示可重复 task
└── tests/
```

整个仓库**主体 ~1,500 行代码**——这是仓库 README 的措辞："Footprint: ≤ ~1.5k LoC"。具体分布：核心 loop ~450 行、Playwright environment ~570 行、CLI ~150 行、3 个 model backend 每个 ~150-200 行。零 hidden framework——只依赖 `httpx`、`pydantic`、`playwright`、`typer`。

## §4 4 个核心抽象：terminal / browser / script / skill

Webwright 把整个系统压成 4 个正交抽象：

### 4.1 Terminal：模型看到的唯一入口

模型不是直接驱动浏览器，而是**面对一个 terminal**。每一步，模型在 terminal 里写一段 Python（`bash_command` / `python_code`），然后 harness 执行，把结果回给模型。Terminal 不是新概念——SWE-agent 和 mini-swe-agent 早就这么做了，**Webwright 把这条经验搬到了 web 任务上**。

具体的 prompt 模板（`src/webwright/agents/default.py`）长这样：

```yaml
agent:
  system_template: |
    You are a browser agent. You have access to a terminal where you can
    write Python code that uses Playwright to control a browser session.
    Each turn:
      1. Inspect the current page (screenshot or DOM).
      2. Write Python code that produces the next observation OR
         completes the task.
      3. Receive the observation and continue.
    When the task is done, set done=true and provide final_response.
  step_limit: 15
  debug_log: true
  keep_last_n_observations: 1   # 剥离旧 observation 里的 ARIA snapshot
```

> 注意 `keep_last_n_observations: 1`——只保留最近一条 observation 的 ARIA snapshot，旧的 observation 自动剪掉。这条配置是 `local_browser.yaml` 的默认，是把长 horizon task 上下文膨胀问题压下去的关键。

### 4.2 Browser：被脚本 spawn 的环境

浏览器**不是 state holder**，是环境。模型用 `playwright.async_api` 启动 Chromium、打开页面、操作 DOM、拿截图。完成一个 step 后可以关闭 session，也可以留着继续 inspect。

```python
# 典型的 Webwright 生成脚本片段
async def search_flights(page, origin, destination, depart, return_date):
    await page.goto("https://www.google.com/flights")
    await page.get_by_role("textbox", name="Where from?").fill(origin)
    await page.get_by_role("textbox", name="Where to?").fill(destination)
    await page.get_by_role("textbox", name="Departure").fill(depart)
    await page.get_by_role("textbox", name="Return").fill(return_date)
    await page.get_by_role("button", name="Search").click()
    await page.wait_for_load_state("networkidle")
    return await page.locator(".flight-result").all_text_contents()
```

关键是：**这段代码被模型写出来之后，就独立存在了**。下次同样任务，加载同样的脚本，传不同的参数。

### 4.3 Script：真正的持久化产物

一个 web task 的完整 trajectory = 一个 single code file。这个文件：

- 包含完整的 Playwright 操作
- 可以在没有 agent 的环境下 re-run（只要装好 Playwright 和 Python deps）
- 可以被参数化（用 `argparse` 包一层）变成 CLI tool
- 可以被人 review 和 fork

README 里 `/webwright:craft` 命令专门做这件事——把 one-shot 任务升级成可复用 CLI tool：

```python
# final_script.py（craft 模式产出）
"""Search flights on Google Flights.

Args:
    origin: Departure airport code (e.g. SEA).
    destination: Arrival airport code (e.g. JFK).
    depart_date: Departure date (YYYY-MM-DD).
    return_date: Return date (YYYY-MM-DD).
"""
import argparse, asyncio
from playwright.async_api import async_playwright


async def search(origin, destination, depart_date, return_date):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.google.com/flights")
        await page.get_by_role("textbox", name="Where from?").fill(origin)
        await page.get_by_role("textbox", name="Where to?").fill(destination)
        # ...
        await browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--origin", default="SEA")
    parser.add_argument("--destination", default="JFK")
    parser.add_argument("--depart-date", default="2026-08-15")
    parser.add_argument("--return-date", default="2026-08-20")
    asyncio.run(search(**vars(parser.parse_args())))
```

下次跑 `python final_script.py --origin LAX --destination SFO --depart-date 2026-07-01`，不需要 agent。

### 4.4 Skill：跨 host 的统一描述

`sills/webwright/SKILL.md` 是 Webwright 跨 host 的"操作手册"——它不是 Python 代码，是一个给 host agent（Claude Code、Codex、OpenClaw、Hermes）读的 description。当用户在 host 里说"用 Webwright 帮我查机票"，host agent 加载这个 skill 描述，按描述里的指令驱动 Webwright loop。

```markdown
# Webwright skill description

When the user asks for browser automation, web scraping, or a web task:

1. Read the user's task carefully.
2. Use the `webwright` CLI or the Playwright Python API directly.
3. For one-shot tasks: write a Python script that completes the task.
4. For repeatable tasks: package the script as a parameterized CLI tool.
5. Always save screenshots and logs to the workspace for review.
```

**一个 skill 描述、四种 host 通用**——这是 Webwright 把"webwright CLI"和"具体 host agent"解耦的关键。

## §5 核心机制：write code → execute → inspect → repair

### 5.1 一次 step 在 default.py 里发生的事

`DefaultAgent.forecast_step()`（约 450 行的核心 loop）的执行序列：

```
┌─ Step N 开始 ──────────────────────────────────┐
│ 1. 渲染 system prompt（注入 workspace_dir 等）   │
│ 2. 渲染 instance template（注入任务 + 历史）     │
│ 3. 调 model.query(messages)                       │
│    → model 返回 thought + python_code/bash_command │
│ 4. 把 assistant_message 写进 self.messages         │
│ 5. 在 debug log 里写 step_NNNN.json + steps.md    │
│ 6. 在 env 里执行 model 给出的代码                  │
│ 7. 拿到 outputs（截图 / 文本 / ARIA snapshot）     │
│ 8. 把 outputs 包装成 observation message          │
│ 9. 写 self.messages（user role = observation）     │
│ 10. 检查 step_limit / format_errors → 继续或停      │
└────────────────────────────────────────────┘
```

**关键不变量**：

- 每一步模型**必须**输出 thought + 可执行代码，不允许只输出文字
- Observation（截图 / ARIA / 文本）作为 user role 回流
- Debug log 写 step_NNNN.json 是 best-effort——失败不影响主流程
- `step_limit` 默认 15 步，超过就 abort（与 SWE-agent 默认值对齐）

### 5.2 上下文管理：剪掉旧 ARIA snapshot

长 horizon task 跑 50+ 步后，message 列表里堆满历史 observation，token 暴涨。`AgentConfig.keep_last_n_observations` 解决这个：

```python
# 简化后的剪枝逻辑
if config.keep_last_n_observations > 0:
    n_keep = config.keep_last_n_observations
    for msg in reversed(messages[:-n_keep]):
        if msg["role"] == "user" and "aria_snapshot" in msg:
            msg.pop("aria_snapshot")  # 只剪 ARIA，保留文本 observation
```

> 注意是 ARIA snapshot 被剪掉，不是整个 message 被删——文本 observation 保留供后续步骤参考，ARIA 树太占 token 直接 drop。这条配置是 `local_browser.yaml` 的甜区配置。

### 5.3 Summary 机制：每 N 步做一次上下文压缩

`AgentConfig.summary_every_n_steps` 是给超长任务用的"主动压缩"开关：

```python
# 每 N 步，model 走一次"总结模式"
summary_user_prompt = """
You are about to have your working context compacted.
Write a concise but COMPLETE summary of everything relevant so that
a fresh agent (with only this summary + system prompt + task) can
continue without losing progress:
- Original task goal + constraints
- Workspace dir + key files (plan.md, final_script.py, final_runs/)
- Which critical points satisfied, which open, known blockers
- Prior exploration findings (selectors, URLs, ARIA labels, pitfalls)
- Latest final_runs/run_<id>/ state + next action to take
"""
```

启用 `summary_every_n_steps=10` 后，每 10 步做一次 context compact——比"全扔 history 重来"温和，比"全保留 history 爆 token"省空间。

### 5.4 self_reflection：截屏后再看一眼

`tools/self_reflection.py` 是可选开关——模型写完一段代码、跑完一段操作后，强制再调一次 `image_qa` 看截图。这条路径在以下场景特别有用：DOM 结构看起来对、但页面有 overlay / modal / 异步渲染导致实际状态和 selector 假设不一致。模型既可以靠 DOM 选择器操作（精准路径），也可以靠视觉确认（兜底路径）。

## §6 模型后端：3 个 backend 的极简抽象

`src/webwright/models/` 目录下 3 个 backend，每个 ~150-200 行：

| Backend | 入口文件 | 关键差异 | token 流向 |
|---------|----------|----------|-----------|
| **OpenAI** | `openai_model.py` | 走 `httpx` 直连 `/v1/chat/completions`，流式 chunk | 自行计费，按 OpenAI token 表 |
| **Anthropic** | `anthropic_model.py` | 走 `httpx` 直连 `/v1/messages`，system block 单独 | 自行计费，按 Anthropic token 表 |
| **OpenRouter** | `openrouter_model.py` | OpenAI 兼容协议，模型路由层 | OpenRouter 聚合计费 |

**关键设计**：

- **零 LangChain / AutoGen**——直接 `httpx` 调 HTTP API，没有中间层
- **统一错误归一化**——`base.py` 里把三个 backend 的 rate limit / auth fail / timeout 归一化成 `ProviderError` 类型，agent loop 不需要 if/else 处理每个 backend 的特有错误
- **base64 image inline**——截图通过 `image_url: data:image/png;base64,...` 直接塞进 multimodal message，省一次文件 IO
- **Anthropic run 不需要 OpenAI key**——`image_qa` / `self_reflection` 复用同一个 model，所以"Anthropic 后端 + Anthropic 模型看图"是自洽的，不需要双 API key

SWE-agent 默认绑 OpenAI 一个 backend；Webwright 从一开始就同时支持 3 个，且 Anthropic 后端的代码和 OpenAI 并列 first-class——不是后来补的兼容层。

## §7 一个任务流案例：从 `--start-url` 到 `final_script.py`

挑 README 里 Google Flights 那个例子——把一次 web 任务从 CLI 输入走到 final_script.py：

### 7.1 CLI 入口

```bash
python -m webwright.run.cli \
  -c base.yaml -c model_openai.yaml \
  -t "Search for flights from SEA to JFK on 2026-08-15 to 2026-08-20" \
  --start-url https://www.google.com/flights \
  --task-id demo_openai \
  -o outputs/default
```

flags 含义：

- `-c base.yaml -c model_openai.yaml`：配置文件叠加（base 提供 agent/environment，model_openai 提供 backend）
- `-t`：任务描述
- `--start-url`：起始 URL
- `--task-id`：输出子目录名
- `-o`：输出根目录

`run/cli.py:run_one()` 把这些参数 merge 进 config，然后 `model = get_model(...)`、`env = get_environment(...)`、`agent = get_agent(model, env, ...)` 三件套组装好。

### 7.2 env.prepare() 启动浏览器

`env.prepare()` 启动 Chromium（headless or headed，取决于 `debug`），访问 `--start-url`，把初始观察打包回传给 agent：

```
env.prepare(
  task="Search for flights from SEA to JFK on 2026-08-15 to 2026-08-20",
  task_id="demo_openai",
  start_url="https://www.google.com/flights",
)
```

初始 observation 一般包含：
- 当前 URL
- 页面 title
- 顶部 viewport 截图（base64）
- ARIA snapshot（accessibility tree）

### 7.3 agent 循环：典型 5 步走完

**Step 1**：模型观察首页——看到"Google Flights"主搜索表单，DOM 里 "Where from?"、"Where to?"、"Departure"、"Return" 4 个 input。生成代码：

```python
async def step_1(page):
    await page.get_by_role("textbox", name="Where from?").fill("SEA")
    await page.get_by_role("textbox", name="Where to?").fill("JFK")
    await page.get_by_role("textbox", name="Departure").fill("2026-08-15")
    await page.get_by_role("textbox", name="Return").fill("2026-08-20")
    await page.get_by_role("button", name="Search").click()
```

Observation：URL 跳转到搜索结果页、截图显示航班列表。

**Step 2**：模型观察搜索结果页——看到 N 条航班、每条带价格和时长。生成代码：

```python
async def step_2(page):
    await page.wait_for_load_state("networkidle")
    results = await page.locator(".flight-result").all()
    flights = []
    for r in results[:5]:
        airline = await r.locator(".airline-name").text_content()
        price = await r.locator(".price").text_content()
        duration = await r.locator(".duration").text_content()
        flights.append({"airline": airline, "price": price, "duration": duration})
    return flights
```

Observation：5 条 flight dict 序列化后的 JSON。

**Step 3**：模型写 final_script.py——把 step 1 + step 2 整合成单脚本，保存到 workspace：

```python
# final_script.py
async def search_flights(page, origin, destination, depart, return_date):
    # ... 上面 step 1 + step 2 的代码 ...
    return flights
```

**Step 4**：self_reflection——再调一次 image_qa 让模型看截图，确认输出格式正确。

**Step 5**：模型设 `done=true` + `final_response="Top 5 flights from SEA to JFK on 2026-08-15-2026-08-20: ..."`，harness 关浏览器，trajectory 写到 `outputs/default/demo_openai_<timestamp>/trajectory.json`。

### 7.4 输出目录长什么样

```
outputs/default/demo_openai_<timestamp>/
├── trajectory.json           # 完整 message 历史 + 每步 observation
├── runtime_errors.jsonl      # model 调用错误流
├── debug/
│   ├── steps/
│   │   ├── step_0001.json    # 每步 thought + code + outputs
│   │   ├── step_0002.json
│   │   └── ...
│   └── steps.md              # 人类可读的 step-by-step 汇总
├── final_script.py           # /webwright:craft 模式会生成
└── final_runs/
    └── run_<id>/
        ├── script.py
        └── screenshots/
```

**关键点**：trajectory.json 是 ground truth——可以 re-run、可以 diff、可以喂给 trajectory viewer 跟 Codex/Copilot 轨迹对比（README 的"Trajectory Comparison & Viewer"就是用这个做的）。

## §8 Plugin 集成：Claude Code + Codex + OpenClaw + Hermes 共享一个 skill

### 8.1 4 个 host 的安装矩阵

| Host | 清单文件 | 安装命令 | 用法 |
|------|----------|----------|------|
| **Claude Code** | `.claude-plugin/plugin.json` | `/plugin marketplace add microsoft/Webwright` 然后 `/plugin install webwright@webwright` | 自然语言触发，或 `/webwright:run` / `/webwright:craft` |
| **OpenAI Codex** | `.codex-plugin/plugin.json` | `codex plugin marketplace add microsoft/Webwright` 然后 `/plugins` 浏览器内安装 | 自然语言，或 `@webwright` 显式调用 |
| **OpenClaw** | （不需独立清单） | `openclaw plugins install /absolute/path/to/Webwright` + `openclaw gateway restart` | `/webwright run <task>` 触发 |
| **Hermes Agent** | （不需独立清单） | `ln -sfn /absolute/path/to/Webwright/skills/webwright ~/.hermes/skills/webwright` | 自然语言触发，或 `/webwright` |

### 8.2 同一份 `skills/webwright/`，四种 host 共用

仓库根目录的 `skills/webwright/` 是**所有 host 共享的入口**——README 把它定义为"the shared skill"，加载方式由各 host 决定：

- **Claude Code + Codex**：通过 marketplace + plugin manifest 加载
- **OpenClaw**：通过 `openclaw plugins install` 把整个仓库注册成 plugin
- **Hermes**：symlink `skills/webwright/` 到 `~/.hermes/skills/webwright/`，Hermes 是 skills-compatible client，不需要专属 manifest

> Hermes 用户需要注意：`/webwright:run` 和 `/webwright:craft` 是 Claude Code / Codex 的命名约定，在 Hermes 里**inert**（README 明示）。Hermes 用户用自然语言或 `/webwright`（单层冒号，不是双层）。

### 8.3 slash command 的两个变体

`skills/webwright/commands/` 下两个文件：

- **`run.md`** —— one-shot 任务。"给我查 SEA→JFK 2026-08-15 的航班" → 生成 `final_script.py`，填好任务值。
- **`craft.md`** —— reusable CLI tool。"给我做一个查机票的命令行工具" → 生成带 `argparse` 包装的 `final_script.py`，flags 默认到具体任务值（`--origin` 默认 `SEA`），下次加 `--origin LAX` 就能复用。

两种模式都让 host agent 走"写 plan.md → 跑 instrumented Playwright scripts → 视觉 self-verify 关键点"的流程。

### 8.4 Token 成本的真实差距

README 给了一个对比表——同一个任务（"找最便宜的 2005-2015 年 25k-50k 美元 8 缸 BMW，里程 < 50k"）：

| Tokens | Webwright Harness（Local Browser Mode） | Codex Webwright Skill |
| --- | ---: | ---: |
| Input | 420,433 | 3,271,143 |
| Output | 3,593 | 20,040 |
| Reasoning | 0 | 4,410 |
| Cached | 217,216 | 3,081,3440 |
| Total | **424,026** | **3,291,183** |

Webwright Harness 直接跑（不经 host agent 中转）比 Codex 当 host 加载 Webwright skill 少 **7.7× token**——README 标注 "Individual runs and results may vary"，这个 7.7× 是单次 run 的样本，不是多次平均。

差距的来源不是模型差异，是**有没有 host agent 在中间包一层**——Codex 路径里 host agent 先把任务理解一遍、决定调 Webwright skill、然后 Webwright 内部的 agent 再跑一遍；Webwright Harness 路径里只有"Webwright 直接对任务"，省了 host 那层 token。

> 这是 plugin 集成模式的实际成本：让 Claude Code / Codex 当 host 时，每一步都要先说服 host agent "我应该调 Webwright skill"——这套 meta reasoning 在短任务里不划算。

## §9 Performance 解读：Online-Mind2Web / Odysseys 测的是什么、不能推出什么

README 的 Performance 段列了 4 个声明：

### 9.1 声明原文

- 🏆 **Online-Mind2Web（300 tasks）：86.7%** with GPT-5.4——开源 harness 中 AutoEval category 最高。Claude Opus 4.7 拿到 **84.7%**，但 hard split 上更强（**80.5% vs 76.6%**，N=100）。
- 🚀 **Odysseys（200 long-horizon tasks）：60.1%** with GPT-5.4（avg 76.1 步）——比 prior SOTA（Opus 4.6 at 44.5%，vision-based + persistent browser）高 **+15.6 points**，比 base GPT-5.4（33.5%，xy-coordinate prediction + persistent browser）高 **+26.6 points**。
- 🧠 **Code-as-action beats coordinate prediction**：复现的 GPT-5.4 screenshot+xy-coordinate baseline 在所有难度 split 上都被 Webwright 显著超过。
- 🧰 **小模型 + 可复用工具**：生成脚本可以打包成 parameterized CLI tool——**Qwen-3.5-9B** 在 5+ tools 可用的 Online-Mind2Web 站上也能完成任务。

### 9.2 这 4 条数字怎么读

**测的是什么**：

| 基准 | 类型 | 任务规模 | 评分方式（按 README 原文） |
|------|------|----------|----------|
| **Online-Mind2Web** | 多网站真实任务（AutoEval） | 300 个 task | AutoEval 类别下开源 harness 中 element-level 成功率 |
| **Odysseys** | long-horizon（avg 76.1 steps） | 200 个 task | 任务完成度（GPT-5.4 average step = 76.1） |
| **N=100 step budget** | 两个 benchmark 共用上限 | 单次任务最多 100 步 | 步数超限算失败 |

**数字反映 Webwright 的哪部分**：

- **86.7% / 60.1%** 是 **GPT-5.4 本身**的 coding ability × **Webwright 框架**的 terminal-native 形态 × **100 step budget** 三者乘积
- 不能单独归功于"框架好"——Opus 4.7 在同一框架下是 84.7%
- 不能单独归功于"模型好"——同一模型用 xy-coordinate 预测只有 33.5%

**不能推出什么**：

- ❌ "Webwright 让所有模型变强"——Qwen-3.5-9B 在 5+ tools 可用的站上能完成 task，但**没有数字**说它超过 GPT-5.4
- ❌ "Webwright 适合短任务"——两个 benchmark 都是 long-horizon（Online-Mind2Web 元素级 step 30+、Odysseys 76 步平均）；短交互任务（"点这个按钮"、"填这一格"）的可用性没测
- ❌ "Webwright 比 Computer Use / Operator 强"——benchmark 不重叠（Webwright 测 web task，Computer Use / Operator 测 GUI 任务）
- ❌ "60.1% 的 production 价值"——200 个 long-horizon task 的 success rate 不能直接推到"我的 X 业务 task 的 success rate"

### 9.3 与 xy-coordinate baseline 的对比最有说服力

+26.6 points 这个数字（Odysseys 上 Webwright vs GPT-5.4 xy-coordinate）是**最有说服力的对比**——同一模型、同一 task、同一 budget，只换 harness 形态：

| Harness 形态 | Odysseys 60.1% | 关键差异 |
|--------------|----------------|----------|
| **GPT-5.4 + Webwright**（code-as-action） | 60.1% | 模型写 Python 脚本，DOM selector + Playwright API |
| **GPT-5.4 + xy-coordinate prediction**（persistent browser） | 33.5% | 模型预测像素坐标，每次 screenshot 后点 |

这个对比**单独隔离了"harness 形态"这一个变量**。结果是 26.6 个百分点的差距。结论：把模型锁在"逐动作预测"里，是模型能力的瓶颈，不是模型能力的边界。

## §10 适用边界：long-horizon web task 是甜区，其他场景有代价

Webwright 不是"universal web agent"——它有明确的甜区和边界。

### 10.1 甜区：long-horizon web task

匹配条件：

- 任务需要 ≥ 10 步交互（搜索 + 选日期 + 填表 + 提交 + 验证）
- 任务完成后产物可重跑（航班搜索、价格监控、表单填写、CRM 操作）
- 用户愿意为一次任务接受 1-5 分钟延迟
- 模型可以接受 OpenAI / Anthropic / OpenRouter 后端

甜区典型场景：

- 跨多个表单页面的预订流程（机票、酒店、租车）
- 重复性的网页数据抽取（odysseys 任务：deals / inventory / listings / job boards / weather）
- 自动化办公（CRM 操作、企业内部系统、表单审批）
- Coding agent 扩展出的"先 web 调研后写代码"工作流

### 10.2 边界外：短交互任务

不匹配场景：

- 单步操作（"点这个按钮"、"改这个 dropdown 的值"）
- 需要 sub-second latency 的 UI 操作
- CAPTCHA 验证、登录墙、bot detection 严重的网站
- 需要真实浏览器 user-agent + cookie 持久化的 SPA（虽然 Playwright 支持 profile，但 harness 还没做 profile 隔离）

### 10.3 边界外：需要视觉理解 > 代码理解的任务

Webwright 默认让模型写 Playwright 代码 + DOM selector——这是**结构化查询路径**。如果任务本质是"看图判断"（电商选款、设计审稿、医学影像标注），Webwright 不是首选——直接 multi-modal 视觉模型更合适。

### 10.4 边界外：需要 persistent state 的 multi-session workflow

Webwright 的 browser 是 disposable 的——每次任务结束关 session。如果你的 workflow 是"先登录一次、cookie 保持、再做 N 个 task"，Webwright 需要你显式在脚本里处理 persistent context（Playwright `storage_state`），但 harness 没有默认 profile 隔离。

### 10.5 cost / latency 不友好的场景

| 场景 | Webwright cost | 备注 |
|------|----------------|------|
| 1 个一次性任务 | 模型 API 费 + ~1-5 min 延迟 | 太重 |
| 1000 个 task/天 | 模型 API 费 + compute | 除非用 caching，否则 token 成本是关键变量 |
| 实时 UI 测试 | 不适合 | harness 设计就不是实时场景 |

## §11 与 SWE-agent / mini-swe-agent / Operator / Computer Use 的关系

把 Webwright 放进 web agent 的生态里看：

### 11.1 与 SWE-agent 家族的关系

Webwright **直接借鉴** SWE-agent / mini-swe-agent 的 minimal agent loop 设计——README Credits 段明确：

> [SWE-agent/mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent/tree/main) — design inspiration for the minimal agent loop.

SWE-agent 是给 SWE-bench 任务（Python repo 修复）写的 web agent。Webwright 是同一思路搬到 web 任务：

| 维度 | SWE-agent | Webwright |
|------|-----------|-----------|
| 目标环境 | local Python repo + bash | remote browser |
| Action space | bash / python code | python + Playwright |
| 持久化产物 | patch file | re-runnable script |
| 任务规模 | SWE-bench 单 bug | long-horizon web task |
| 后端 | OpenAI 为主 | OpenAI + Anthropic + OpenRouter |

mini-swe-agent 是 SWE-agent 的进一步简化版（更少的 scaffold、更通用的 prompt），Webwright 可以理解为"mini-swe-agent + Playwright"。

### 11.2 与 Operator / Computer Use 的关系

OpenAI Operator 和 Anthropic Computer Use 是 **GUI 通用 agent**——它们不绑定 web 任务，可以做桌面软件、远程桌面、移动 app 等。

| 维度 | Webwright | Operator | Computer Use |
|------|-----------|----------|--------------|
| 作用域 | web only | GUI 通用 | GUI 通用 |
| Action space | Playwright Python | 鼠标键盘 + API | 鼠标键盘 |
| 状态载体 | workspace 文件 | 屏幕截图 + DOM | 屏幕截图 |
| 长 horizon | 强（code-as-action） | 中（受 vision 限制） | 中（受 vision 限制） |
| 编程可控 | 强（脚本可重跑） | 弱 | 弱 |
| 部署成本 | 低（Python + Playwright） | 高（云端服务） | 中（API） |

Webwright 的精确象限是"web-only + code-as-action + 程序员可改"——这象限里目前没有第二个完全开源的同类实现。它的直接对手不是 Operator / Computer Use，而是 browser-use / Stagehand / agent-browser 这类 web 专用框架。

### 11.3 在 web agent 生态里的位置

| 框架 | Action space | State | 适用 |
|------|--------------|-------|------|
| **Webwright** | Free-form Python | workspace + 脚本 | long-horizon + 重跑需求 |
| **Stagehand** | Playwright code + NL primitives | browser session | 短到中等任务 + NL 友好 |
| **agent-browser (Vercel)** | CLI 子命令 | browser session（daemon） | host agent 调用 web task |
| **browser-use** | Indexed click/type | browser session | 短到中等任务 + 自动 loop |

Webwright 和 browser-use 在用户场景上**有重叠也有分叉**——browser-use 在中等长度任务（数步到 30 步左右）用 DOM snapshot 跑得很顺，long-horizon 场景（多步累积、跨页持久化、失败重试）下 Webwright 的 code-as-action 路线会拉开差距。差距的根因是 Webwright 把 selector 和操作持久化到脚本里，失败可以改代码重跑；DOM snapshot 路径每次重新从截图开始推断。

## §12 Task Showcase：可重复任务的 dashboard

`assets/task_showcase/` 是 Webwright 的"长期任务可见性"组件——一个 Flask dashboard 展示所有"被 Webwright 跑过的可重复 task"。

### 12.1 工作机制

每个 repeatable task = `assets/task_showcase/tasks/<short_id>/` 下两个文件：

- **`task.json`**：metadata（task 描述、起始 URL、创建日期）
- **`report.json`**：curated output（结构化结果——sources + result sections，比如 tables / lists / summaries）

Flask app 读取这些 JSON，用模板渲染成 HTML。

### 12.2 触发方式

默认 base.yaml run 只产出 trajectory + debug artifacts，**不**写 `report.json`。要触发 report 模式，叠加 `task_showcase.yaml`：

```bash
python -m webwright.run.cli \
  -c base.yaml -c model_openai.yaml -c task_showcase.yaml \
  -t "Find weekly deals on RTX 4070 laptops in Seattle" \
  --task-id weekly_deal_4070 \
  -o outputs/default
```

`-c task_showcase.yaml` 让 harness 在 run 结束时把结果写入 `task_showcase/tasks/<short_id>/` 下。

### 12.3 单独跑 dashboard

```bash
pip install flask
python assets/task_showcase/app.py    # http://127.0.0.1:5005
```

dashboard 渲染本地 task 文件夹里所有 task。**没有数据库、没有用户系统、没有云端**——纯本地 Flask 模板。

### 12.4 与 trajectory viewer 的关系

`assets/compare_trajectory/` 提供 trajectory 对比工具：上传 Webwright harness 的 `raw_responses.jsonl` 和 `trajectory.json`，另一端上传 Codex / GitHub Copilot 的 trace，**可视化对比 token 流向**和 step-by-step 决策。

这是 §8.4 那个 7.7× token 差距数字的来源——同任务不同 harness 的真实可视化对比。

## §13 采用顺序：谁该先用、谁可以等等

读完 Webwright 的设计、代码、benchmark 和边界，给一个直接的判断：

### 13.1 现在就试 Webwright 的团队

- 已经在做 long-horizon web automation（航班 / 表单 / 监控 / CRM），希望脚本可重跑、可 fork、可维护
- 已经在用 Claude Code 或 Codex 作为 host agent，想给它加 web 能力（plugin 装上即可）
- 想要一个 **< 2k LoC** 的可读 web agent 框架，能自己改、能 debug、能 fork
- 在做 coding agent 扩展，想给它加"先 web 调研后写代码"的工作流
- 在做 browser-use / Stagehand 的 long-horizon 痛点研究，需要一个 code-as-action 的 baseline

### 13.2 等等再看的团队

- 只做短交互任务（1-3 步），browser-use 的 DOM snapshot 路径足够
- 需要 Operator / Computer Use 那种 GUI 通用能力
- 已经有成熟的 web automation pipeline，不愿意重写
- 团队不熟悉 Python / Playwright
- 任务对 latency 敏感（< 5s 端到端），Webwright 的多步 loop 不适合

### 13.3 决策矩阵

| 你的场景 | 推荐方案 | 备注 |
|----------|----------|------|
| Long-horizon + 可重跑 + 程序员可改 | **Webwright** | 甜区，1.5k LoC 可改 |
| Long-horizon + 不可重跑 + 一次性研究 | Webwright 也行，但 browser-use 更轻 | 看 token 预算 |
| 短到中等（< 30 步）+ auto loop | **browser-use** | harness 更简单 |
| 短到中等 + NL primitives 友好 | **Stagehand** | `act` / `extract` / `agent` API |
| Host agent（Claude Code / Codex）调用 web | **Webwright 作为 plugin** | 装一次跨 host 通用 |
| GUI 通用（不只 web） | **Operator / Computer Use** | 不在 Webwright 作用域 |
| 实时 UI 测试 | **Playwright 直接 + 编程** | Webwright harness 太重 |

### 13.4 第一次试的最小路径

如果你决定试 Webwright，按这个顺序：

1. **读一遍 README**——特别是 "How Webwright Differs From Other Browser-Agent Repos" 表格，确认它符合你的预期
2. **跑 Quick Start 的 Google Flights demo**——确认基本 loop 在你的环境 work
3. **读 `src/webwright/agents/default.py`**——450 行核心 loop，30 分钟读懂
4. **读 `skills/webwright/SKILL.md`**——如果你打算用 host agent 集成
5. **读 §9 的 benchmark 解读**——不要把数字直接搬到生产
6. **把你的第一个真实 task 改成 `task_showcase.yaml` 模式**——跑一遍 dashboard，看 output 格式

### 13.5 进阶路径

**如果你是想理解 web agent 设计的研究者**：

- §3 总览 + §4 4 抽象 → 理解"为什么 code-as-action"
- §9 benchmark 解读 → 理解"怎么读 web agent 数字"
- §11 与 SWE-agent 关系 → 把 web agent 和 SWE-bench agent 看作同一思路的不同域

**如果你是想给 coding agent 加 web 能力的开发者**：

- §7 一个任务流案例 → 看到"agent 怎么写代码"
- §8 plugin 集成 → 选你的 host
- §10 边界 → 确认你的任务在甜区

**如果你是想 fork / 改 Webwright 的开发者**：

- §5 核心机制 → 看 default.py 怎么 step
- §6 模型后端 → 看 base.py 的统一错误归一化
- §11 SWE-agent 血缘 → 知道可以借什么、改什么

## §14 附录

### 14.1 仓库元信息

| 项目 | 内容 |
|------|------|
| **仓库** | github.com/microsoft/Webwright |
| **Stars** | 5,628（5.6k） |
| **Commits** | 43（截至 2026-06-25） |
| **首次公开** | 2026-04-08（创建日期）/ 2026-05-04（首次 release） |
| **最近 release** | 2026-05-11（Task2UI mode） |
| **License** | MIT |
| **语言** | Python 3.10+ |
| **依赖** | httpx / pydantic / playwright / typer（无 LangChain / AutoGen） |
| **代码量** | ~1,500 LoC（agents ~450 / environment ~570 / CLI ~150 / 3 model backends × 150-200） |
| **作者** | Lu Yadong、Xu Lingrui、Huang Chao、Awadallah Ahmed（Microsoft Research） |

### 14.2 三个 model backend 对比

| Backend | HTTP 协议 | Image handling | 默认 model | 适用场景 |
|---------|-----------|----------------|-----------|----------|
| **OpenAI** | `/v1/chat/completions` 直连 | base64 inline | GPT-5.4（benchmark 默认） | Online-Mind2Web 86.7% / Odysseys 60.1% 都用这个 |
| **Anthropic** | `/v1/messages` 直连 | base64 inline | Claude Opus 4.7（benchmark 对照） | Online-Mind2Web 84.7% / hard split 80.5% |
| **OpenRouter** | OpenAI 兼容协议 | 透传 | 任意 OpenRouter 支持的模型 | 不想直连 OpenAI/Anthropic 时 |

### 14.3 与 xy-coordinate baseline 的 +26.6 points 是最有说服力的对比

| Harness 形态 | Odysseys 60.1% | 关键差异 |
|--------------|----------------|----------|
| **GPT-5.4 + Webwright**（code-as-action） | 60.1% | 模型写 Python 脚本，DOM selector + Playwright API |
| **GPT-5.4 + xy-coordinate prediction**（persistent browser） | 33.5% | 模型预测像素坐标，每次 screenshot 后点 |

同一模型、同一 task、同一 budget，只换 harness 形态：+26.6 个百分点。这个数字**单独隔离了"harness 形态"一个变量**，是 Webwright 论文级论证里最有说服力的对比。

### 14.4 已知边界（README 显式声明）

- ❌ Hermes Agent 不支持 `/webwright:run` / `/webwright:craft` 双冒号命名
- ❌ Trajectory viewer 单独跑（`cd assets/compare_trajectory/ && python3 -m http.server`），不是 Webwright 主进程一部分
- ❌ Webwright 不解决 CAPTCHA / bot detection / login wall
- ❌ Browser profile 不持久化——每次任务新 session

### 14.5 引用格式

```bibtex
@misc{webwright2026,
  title        = {Webwright: A terminal is all you need for web agents},
  author       = {Lu, Yadong and Xu, Lingrui and Huang, Chao and Awadallah, Ahmed},
  year         = {2026},
  howpublished = {\url{https://github.com/microsoft/Webwright}},
  note         = {GitHub repository}
}
```

### 14.6 参考链接

- [microsoft/Webwright 仓库](https://github.com/microsoft/Webwright)
- [Webwright Blog: A Terminal Is All You Need For Web Agents](https://www.microsoft.com/en-us/research/articles/webwright-a-terminal-is-all-you-need-for-web-agents/)（Microsoft Research 官方 blog）
- [microsoft.github.io/Webwright 项目页](https://microsoft.github.io/Webwright/)
- [SWE-agent/mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent/tree/main) —— 设计灵感来源
- [Playwright](https://playwright.dev/) —— 底层浏览器自动化

---

**写作说明**：本文 14 个 H2 章节覆盖 Webwright 的核心判断、系统地图、4 个抽象、核心机制、3 个模型后端、完整任务流案例、4 种 host 的 plugin 集成、benchmark 解读、适用边界、生态定位、采用决策矩阵。Performance 段严格按 README 原文引用 86.7% / 60.1% / +15.6 / +26.6 等数字，并显式标注"不能推出什么"——避免把 benchmark 直接推到生产负载。所有跨 host 集成、token 对比、模型后端选择都有具体可验证的来源。
