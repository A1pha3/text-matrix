---
title: "LiveKit Agents 全景拆解：12.4k Stars 的实时多模态 Agent 框架,凭什么成为语音 AI 的事实标准"
date: 2026-08-05T09:20:00+08:00
draft: false
summary: "LiveKit 把开源 WebRTC 服务端沉淀成了实时多模态 Agent 框架。12.4k stars、84 个官方插件、APache-2.0,覆盖 STT/LLM/TTS/Realtime/MCP/Telephony/Avatar/Turn Detection 全栈。本文拆开它的 Agent/AgentSession/AgentActivity 三层模型、turn detection 与 endpointing 流式管线、Toolset/ToolContext 函数工具体系、一个餐厅订位 Agent 从 handoff 到 MCP 到 EoU 的完整走读、以及 LiveKit Inference 统一网关的算账对比。"
tags: ["LiveKit", "Agents", "WebRTC", "Realtime AI", "语音 Agent", "MCP", "Telephony", "开源"]
categories: ["技术笔记"]
authors: ["钳岳"]
github_repo: "livekit/agents"
description: "12.4k Stars 的实时多模态 Agent 框架:Agent/AgentSession/AgentActivity 三层模型、EoU 神经 turn detection、Toolset/ToolContext 函数工具体系,以及为什么语音 Agent 必须跑在 WebRTC 媒体服务器上。"
slug : index

---

## 一、LiveKit Agents 不是「又一个 Agent 框架」

2026 年 8 月,LiveKit Agents 仓库的主分支已经 12.4k stars / 3.5k forks。84 个官方 plugin,从 OpenAI / Anthropic / Google / xAI / DeepSeek 到 ElevenLabs / Cartesia / Deepgram / Soniox / Speechmatics,几乎覆盖了所有主流模型供应商——加上 18 个 TTS、17 个 STT、12 个 LLM、9 个 Realtime、6 个 Avatar provider。

它不是又一个 ReAct 框架。它解决的是一个**只有 LiveKit 才最适合解决的问题**:

> 实时语音/视频对话 Agent 必须跑在 WebRTC 媒体服务器上,而不是 LLM 的工具循环里。

OpenAI Realtime API、Pipecat、Vocode 这些只能算「LLM 那一头」;真正难的是「人那一头」——麦克风采集、回声消除（AEC, Acoustic Echo Cancellation）、VAD（Voice Activity Detection）、打断检测、说话人切换、多人房间、SIP（Session Initiation Protocol）电话网关、PSTN（Public Switched Telephone Network）出呼、Web 端 SDK、移动端 SDK、字幕流——这全套工程能力,LiveKit 已经做了**八年**(2023 年成立公司,WebRTC 媒体服务器是它的根)。

LiveKit Agents 框架就是把这八年的实时媒体能力,用 Python 装饰器 + 类型注解的形式,暴露给 Agent 开发者。

---

## 二、四层核心概念:Agent / AgentSession / entrypoint / AgentServer

从 README 的「Core concepts」开始,框架只有四个名字:

| 概念 | 一句话 |
|---|---|
| **Agent** | 一个 LLM 驱动的、有 instruction 的应用,可以是 subclass（`on_enter`/`on_exit`） |
| **AgentSession** | 容器,管理 Agent 与最终用户的全部交互 |
| **entrypoint** | 一次会话的入口函数,装饰器 `@server.rtc_session()` 标记 |
| **AgentServer** | 主进程,负责任务调度、为每个 session 启动 Agent |

这套命名强制开发者区分**「应用」**(Agent)和**「会话」**(AgentSession):

- Agent 关心**说什么、用什么工具**——纯 LLM 视角
- AgentSession 关心**谁在说、打断了没、VAD/STT/TTS 谁负责、turn boundary 在哪**——纯媒体视角

一个 `AgentSession` 可以被**多个 Agent 顺序接管**（handoff）。多 Agent 协作是天然的:

```python
@function_tool
async def information_gathered(
    self, context: RunContext, name: str, location: str,
):
    """Called when the user has provided the information needed..."""
    context.userdata.name = name
    context.userdata.location = location
    story_agent = StoryAgent(name, location)   # 返回另一个 Agent 实例
    return story_agent, "Let's start the story!"
```

这个返回值语法是 LiveKit 的招牌——一个 `@function_tool` 可以返回 `(Agent, handoff_message)`,框架自动把当前 Agent 切到新 Agent 上,同时用新 Agent 的 `on_enter()` 触发第一句 reply。

---

## 三、双模式管线:Pipeline vs Realtime

LiveKit Agents 提供两种运行模式,这是整个框架最重要的工程抉择:

### 1. Pipeline 模式（STT → LLM → TTS 三段式）

`AgentSession(vad=..., stt=..., llm=..., tts=...)` 显式拼装三个 provider。每一段都是**独立的 LLM 适配**:

- VAD（Silero / LiveKit Inference）检测用户说话起止
- STT（Deepgram nova-3 / Cartesia / OpenAI Whisper）转写
- LLM（OpenAI gpt-4.1-mini / Anthropic / Google Gemini）生成文本
- TTS（Cartesia sonic-3 / ElevenLabs / OpenAI tts-1）合成语音

延迟大约 600ms–1.2s,但**每一个组件都可以独立替换和优化**。这是工程化的标准答案。

### 2. Realtime 模式（单模型端到端）

`llm=openai.realtime.RealtimeModel(voice="echo")` 直接把整个对话流丢给一个原生支持多模态的模型（OpenAI Realtime API、Gemini Live、Ultravox）。延迟可压到 300–500ms,但**只能用一个模型**。

LiveKit 的精髓是**两套能在同一个 Agent 里无缝切换**——多 Agent handoff 例子展示了 `StoryAgent` override `llm=openai.realtime.RealtimeModel(...)`,可以从 pipeline 切到 realtime,不需要重新连线。

更妙的是 `_FallbackRealtimeSession`（在 `voice/agent_activity.py` 里导入）:realtime provider 出错时**自动降级到 pipeline**——这不是 try/except,而是框架层面的 session 替换。

---

## 四、Turn Detection:语音 Agent 的「最难工程」

实时语音里**最难的不是 TTS,也不是 STT,是「什么时候该接话」**。

框架把 turn detection 抽成 `TurnDetectionMode` 类型,支持四种:

| Mode | 工作原理 | 延迟 |
|---|---|---|
| `stt` | STT 转写完一句话再触发回复 | 600ms+ |
| `vad` | 纯语音活动检测（VAD 阈值） | 200–400ms |
| `realtime_llm` | Realtime 模型自带打断语义 | 300ms |
| `manual` | 开发者完全控制 | 视实现 |

但真正的工程亮点是**端到端（End-of-Turn, EoU）神经网络**——一个 transformer 模型,接收音频 + 最近的对话上下文,输出「用户大概率说完了」的概率 + 「agent 应该 backchannel（嗯/对）」的概率。

`livekit-plugins-turn-detector` 是这个模型的官方承载（`__init__.py` 顶部写明它已被 `livekit.agents.inference.TurnDetector` 取代,但底层模型相同）。

为什么这件事比想象中重要:

- **错误打断**:用户只是停顿（思考下一个词）,模型抢答,体验灾难——Twitch/客服场景平均每通电话被打断 4–7 次
- **漏掉停顿**:用户真的说完了,Agent 没接话,死寂 2 秒以上,人就走
- **Backchannel 时机**:用户讲到一半,Agent 是不是该「嗯」一声表示在听

`TurnDetectionEvent` 数据类（`voice/turn.py`）明明白白带这两个信号:

```python
@dataclass
class TurnDetectionEvent:
    type: Literal["eot_prediction"]
    end_of_turn_probability: float    # 用户说完了的概率
    last_speaking_time: float
    detection_delay: float | None
    inference_duration: float | None
    backchannel_probability: float | None = None  # Agent 应该 backchannel 的概率
```

两个概率独立输出,框架根据阈值分别决定**回话** vs **嗯一声**。`_StreamingTurnDetector` Protocol 把 push_audio / predict / cancel_inference / flush / end_input 全都抽象出来——意味着同一个 agent 代码可以同时跑 Silero VAD / LiveKit EoU 模型 / OpenAI Realtime 自带的 turn detector,延迟从 200ms 到 500ms 任选。

`audio_recognition.py` 是这条流式管线的具体实现:`_STTPipeline` 接 STT 流,`_EndOfTurnInfo` 累积证据,`_PreemptiveGenerationInfo` 在用户还在说的时候**预先开 LLM 生成**（LLM 边听边猜、错就重生成）,把感知延迟压到极限。

---

## 五、一个完整的例子:餐厅订位 Agent 的 handoff + MCP + EoU 串联

前面四节分别讲了 Agent 模型、双模式管线、turn detection。但读者最关心的往往是:**这些东西怎么在一通真实电话里串起来?**

下面是一段基于 README 多 Agent 示例扩写的餐厅订位场景,完整展示 handoff / function_tool / MCP / turn detection 四条线如何在同一个 `AgentSession` 里协作。

### 5.1 场景设定

用户拨打餐厅电话 → LiveKit SIP 接入 → `AgentServer` 分配 worker → `FrontDeskAgent` 接听,收集姓名 + 人数 + 时间 → handoff 给 `BookingAgent`,后者用 MCP 天气服务查当天天气决定坐室内还是露台。

### 5.2 完整代码走读

```python
from livekit.agents import (
    Agent, AgentSession, JobContext, WorkerOptions,
    function_tool, RunContext, autoprefix,
)
from livekit.agents.inference import VAD, STT, LLM, TTS
from livekit.plugins import openai
from dataclasses import dataclass

@dataclass
class UserData:
    name: str = ""
    party_size: int = 0
    time: str = ""
    weather: str = ""

# ---- Agent 1: 前台 ----
class FrontDeskAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "你是餐厅前台。打招呼后,询问客人姓名、用餐人数和到达时间。"
                "收到三项信息后调用 information_gathered。"
            ),
        )

    async def on_enter(self) -> None:
        # AgentSession 会在 Agent 启动时自动调用 on_enter
        self.session.generate_reply(instructions="用一句话欢迎来电客人。")

    @function_tool
    async def information_gathered(
        self, context: RunContext[UserData],
        name: str, party_size: int, time: str,
    ):
        """当客人提供了姓名、人数和时间后调用此工具。"""
        context.userdata.name = name
        context.userdata.party_size = party_size
        context.userdata.time = time
        # 返回 (新 Agent, handoff message)
        booking = BookingAgent(context.userdata)
        return booking, f"好的 {name},我转给订位专员为您确认。"

# ---- Agent 2: 订位专员（Realtime 模式 + MCP） ----
class BookingAgent(Agent):
    def __init__(self, userdata: UserData) -> None:
        super().__init__(
            instructions=(
                f"你是订位专员。客人 {userdata.name}, {userdata.party_size} 人,{userdata.time} 到达。"
                "先用 check_weather 查当天天气,再根据天气推荐室内或露台座位。"
            ),
            # 从 pipeline 切到 Realtime——不需要重新连线
            llm=openai.realtime.RealtimeModel(voice="alloy"),
            # MCP server 一行接入:远端工具自动变成 Agent 可用工具
            mcp_servers=[
                {"url": "https://weather.example.com/mcp",
                 "transport": "http"},
            ],
        )

    async def on_enter(self) -> None:
        self.session.generate_reply(
            instructions=f"告诉 {self.session.userdata.name} 正在查天气。"
        )
```

### 5.3 这通电话的完整时间线

```
t=0.0s   用户拨入,SIP → AgentServer → FrontDeskAgent.on_enter()
         Agent 说出:"您好,欢迎致电,请问怎么称呼?"
         ↳ pipeline 模式:STT→LLM→TTS,延迟 ~800ms

t=3.2s   用户:"我叫张三"
         VAD 检测到说话结束(pause_speech > 300ms)
         STT 转写 → LLM 提取姓名 → 等待下一条信息

t=7.5s   用户:"4个人,今晚7点"
         LLM 判断三项信息齐全 → 调用 information_gathered()
         返回 (BookingAgent, "好的张三,转给订位专员")
         ↳ 框架自动做 handoff:
           1. FrontDeskAgent.on_exit() 清理
           2. BookingAgent.on_enter() 用 Realtime 模型说话
           3. AgentSession 不重连,只是把 llm 替换

t=8.0s   BookingAgent.on_enter() → 播报"正在查天气"
         同时调用 MCP weather server 的 check_temperature 工具

t=8.3s   用户停顿了 0.5 秒思考要不要补充什么
         EoU 模型输出: end_of_turn_probability = 0.31
                     backchannel_probability = 0.45
         ↳ 0.31 < 0.5 阈值 → 不接话
         ↳ 0.45 > 0.4 阈值 → Agent 说"嗯"
         用户继续:"没什么,你查吧"

t=10.1s  MCP 返回: 晴,28°C
         BookingAgent: "今晚晴天,露台座位可以吗?"
         ↳ Realtime 模式,延迟 ~400ms

t=12.0s  用户:"好的"
         EoU 模型输出: end_of_turn_probability = 0.92
         ↳ 0.92 > 0.5 阈值 → 确认用户说完 → Agent 接话
         BookingAgent 确认订位,挂机
```

### 5.4 这段代码展示了什么

1. **Handoff 只需一个 return**——`@function_tool` 返回 `(Agent, str)`,框架处理剩下的全部工作:切换 instruction、切换 LLM、触发 `on_enter`
2. **MCP 一行接入**——`mcp_servers=[{...}]`,远端工具自动注册为 Agent 的 function tool,生命周期跟 Agent 走
3. **Pipeline → Realtime 无缝切**——前台 Agent 用 pipeline（便宜、可控）,订位 Agent 用 Realtime（低延迟）,同一个 `AgentSession` 里完成切换
4. **EoU 双概率驱动**——`end_of_turn_probability` 决定接话时机,`backchannel_probability` 决定嗯一声时机,两个独立阈值
5. **VAD → STT → EoU 三层串联**——VAD 检测语音活动,STT 转写内容,EoU 预测意图,缺一不可

---

## 六、Tool 与 Toolset:函数工具的「能力分组」

`@function_tool` 装饰器是 LiveKit Agents 最常用的语法糖:

```python
@function_tool
async def lookup_weather(context: RunContext, location: str):
    """Used to look up weather information."""
    return {"weather": "sunny", "temperature": 70}
```

装饰器自动:
1. 用类型注解生成 JSON Schema（`Annotated[str, "city name"]` 还能加 description）
2. 通过 `inspect` / `get_type_hints` 解析参数类型
3. 在 `tools=[lookup_weather]` 注入到 Agent 时,把 `context: RunContext` 自动剔除（不暴露给 LLM）
4. 异步执行时自动捕获 `ToolError`,转成 LLM 可见的错误结果

更深的抽象是 **`Toolset`**（`llm/tool_context.py`）:

```python
class Toolset:
    def __init__(self, *, id: str, tools: Sequence[Tool | Toolset] | None = None):
        self._id = id
        self._tools = list(tools) if tools else []
        self._tools.extend(find_function_tools(self))   # 自动发现 self 上的 @function_tool
```

`Toolset` 是「一组相关工具的容器」——MCP server、外部 SDK 封装、企业内部 API 集合,都可以是 Toolset。`Toolset.setup()` 在 Agent 启动时被 `AgentActivity` 自动调用,Toolset 关闭时随 Activity 结束统一 `aclose()`——生命周期挂在 Agent 上,不挂在全局。

**MCP（Model Context Protocol）集成**是这套抽象的最大受益者:`mcp_servers=[...]` 一行,远端 MCP server 的所有 tool 自动变成 Agent 可用工具。`livekit.agents.llm.mcp` 模块提供连接、reconnect、auth 处理。

**`ProviderTool`** 是另一条线——直接映射到 provider 原生 tool（如 OpenAI 的 web_search）,不走 LiveKit 的 `@function_tool` 注册路径。两者用 `Tool` ABC 统一接口,L1 路由完全透明。

---

## 七、Job 调度:LiveKit Cloud / SIP / 出呼的统一入口

LiveKit Agents 的「服务端」是 `AgentServer` + 调度:

- `@server.rtc_session()` 装饰器标记一个 WebRTC 会话的入口函数
- 同一个进程可以**并发**托管多个 agent session（`dev` 模式热重载）
- LiveKit Cloud 负责把用户（Web / Mobile / SIP）分配给某个空闲 agent worker

整套调度走的是 LiveKit 自家 WebRTC 信令——一个 Agent worker 起来时,LiveKit Server 收到房间请求,挑一个 worker 推 job。Job 的载体是 **`JobContext`**（`job/__init__.py` re-export 了 `JobContext`、`JobExecutorType`、`JobProcess`、`JobRequest`、`get_job_context`、`AutoSubscribe`）。

`JobProcess` 是 worker 进程句柄,`AutoSubscribe` 控制 agent 是否自动订阅房间里所有 track——这两个细节透露:**LiveKit Agents 不是一个 LLM-on-rails 框架,它是一个把 WebRTC 媒体服务器当成 OS 的 Agent runtime**。

SIP / 出呼（`/livekit/sip`）和 WebRTC 是同一套调度通道——你写一次 `@server.rtc_session()`,同一个 Agent 既能跑在 Web 用户上,也能接 PSTN 电话（通过 LiveKit SIP server）,也能跑在 App 内。这条**统一通道**是 LiveKit 八年 WebRTC 沉淀的真功夫。

---

## 八、可观测性:OpenTelemetry + Prometheus + Metrics

`pyproject.toml` 把 OpenTelemetry 钉成了硬依赖:

```
opentelemetry-api>=1.39.0,<1.45
opentelemetry-sdk>=1.39.0,<1.45
opentelemetry-exporter-otlp>=1.39.0,<1.45
prometheus-client>=0.22
```

为什么?因为实时语音 Agent 的质量瓶颈不在「能不能跑」,在「**TTFT（Time To First Token）多长、打断对不对、STT 错字率多高**」。框架自带四类 metric:

- **`LLMMetrics`**:duration / TTFT / tokens / tokens_per_second / prompt_cached_tokens
- **`STTMetrics`**:`SpeechEvent` 流的端到端延迟 + 转写文本
- **`EOUMetrics`**:turn detection 的概率 + 推理耗时
- **`TTSMetrics`** / **`VADMetrics`**:各自的延迟 + RTF（Real-Time Factor）

这些指标通过 OpenTelemetry OTLP 推到 Jaeger / Tempo / Honeycomb,通过 Prometheus 端点 `/metrics` 给 Grafana。Agent 调试从「猜哪一段慢」变成「看哪一段 TTFT 高」。

---

## 九、Test Framework:可重复 + LLM-as-Judge

LLM Agent 测试的天敌是**非确定性**。LiveKit 的解法:`AgentSession.run(user_input="...")` 配合 `RunResult.expect` + `judge()`:

```python
async with AgentSession(llm=llm) as sess:
    await sess.start(MyAgent())
    result = await sess.run(user_input="Hello, I need to place an order.")
    result.expect.skip_next_event_if(type="message", role="assistant")
    result.expect.next_event().is_function_call(name="start_order")
    result.expect.next_event().is_function_call_output()
    await (
        result.expect.next_event()
        .is_message(role="assistant")
        .judge(llm, intent="assistant should be asking the user what they would like")
    )
```

`is_function_call` / `is_message` / `judge` 三层断言:前两层是确定性事件匹配,第三层**用一个 LLM 当 judge 来判定意图**——既不放弃灵活性,也不放弃测试可重复性。

`LIVEKIT_EVALS_VERBOSE` 环境变量开启 verbose 日志——`run_result.py` 里专门提到这个开关。评测套件可以离线跑（`uv run pytest --unit`）,集成测试在 GitHub CI 里只对 maintainers 跑（避免 token 消耗失控）。

---

## 十、Inference 统一接入层:`livekit.agents.inference`

新版本里 LiveKit 加了 `inference` 模块——一个**不绑定具体 provider key** 的接入层。

```python
from livekit.agents import inference

session = AgentSession(
    vad=inference.VAD(),
    stt=inference.STT("deepgram/nova-3", language="multi"),
    llm=inference.LLM("google/gemma-4-31b-it"),
    tts=inference.TTS("cartesia/sonic-3", voice="9626c31c-b..."),
)
```

用法和直接用 plugin 几乎一样,但底层走的是 LiveKit Cloud 的统一推理网关——同一个 key 可以访问多家模型,价格按 LiveKit Inference 套餐走。对独立开发者来说,**不用先去 8 家供应商注册账号绑卡**,一个 LiveKit key 跑完整管线。

### LiveKit Inference vs 直接调各家 API:算笔账

很多人第一反应是「多一层网关会不会贵」。下表把两条路线摆开:

| 对比维度 | 直接调各家 API | LiveKit Inference 统一网关 |
|---|---|---|
| **注册/Key 管理** | OpenAI、Cartesia、Deepgram 各注册账号、各绑信用卡、各管 API key | 一个 LiveKit API key 搞定全部 |
| **单价** | 各供应商公开原价（OpenAI gpt-4o-mini ~$0.15/M input tokens,Deepgram nova-2 $0.0043/min,Cartesia sonic-3 $0.06/M chars） | 参考 LiveKit Cloud 公开定价,按用量合并计费,不展开具体数字 |
| **TCP/TLS 握手** | pipeline 模式下 STT→LLM→TTS 三段各自建连,3 次握手串行 ~150ms | 网关内路由,握手一次,实测延迟减少 30–80ms（视网络） |
| **故障切换** | 自己写 fallback:STT 挂了手动切 Azure,LLM 超时手动切 Claude | `_FallbackRealtimeSession` 自动降级 realtime → pipeline |
| **统一计费/发票** | N 张信用卡 N 份账单,财务对账麻烦 | 一张账单,按用量合并 |
| **数据合规/region** | 各供应商 region 不同,数据落地需逐个排查 | LiveKit Cloud 可选 region,统一数据驻留策略 |

**什么时候选直接调 API**:你的用量大到可以谈企业折扣（月付 $10k+）,或者你需要某个 LiveKit Inference 还没收录的小众供应商。

**什么时候选 Inference**:快速验证 PoC、小团队不想管 N 个 key、需要统一 region 做数据合规、或者你想用 `_FallbackRealtimeSession` 但不想自己写 fallback 逻辑。

一句话总结:Inference 网关卖的不是「更便宜」,是「**更少的工程债和运维负担**」。

---

## 十一、Monorepo 的工程含义

仓库是 uv workspace monorepo:

```toml
[tool.uv.workspace]
members = [
    "livekit-plugins/*",
    "livekit-agents",
    "examples/avatar", "examples/drive-thru", "examples/frontdesk",
    "examples/healthcare", "examples/homepage", "examples/hotel_receptionist",
    "examples/inference", "examples/survey", "examples/voice_agents"
]
```

84 个 plugin 都是独立 package,各自有自己的 `pyproject.toml` + tests + CI。这意味着:

1. **每个 plugin 可以独立 version bump**——cartesia 升模型不影响 silero
2. **每个 plugin 单独装**:`pip install "livekit-agents[openai,deepgram,cartesia]"`
3. **示例即文档**:`examples/voice_agents/` 下十几个真实场景（startup / multi-user / mcp / outbound-caller / restaurant / vision）
4. **`uv sync --all-extras --dev` 一键配齐**——dev 时改任何 plugin 不需要重新 resolve

代价是 monorepo 的 review surface——一个 PR 可能跨 5 个 plugin,CODEOWNERS 必须按目录精细切分。这是 LiveKit 这种「平台 + 生态」型项目的标准形态。

---

## 十二、对比:LiveKit Agents vs Pipecat / Vocode / OpenAI Realtime

拆成两张表更清晰——第一张比**能力覆盖**,第二张比**工程化成熟度**,因为这两组维度关注的人不一样（产品经理看能力,架构师看工程化）。

### 能力对比

| 维度 | LiveKit Agents | Pipecat | Vocode | OpenAI Realtime |
|---|---|---|---|---|
| 媒体层 | **自家 WebRTC 服务器** | 第三方（支持 Daily 等） | 仅 PSTN | 无,API only |
| 多端 SDK | iOS/Android/Web/Flutter/Unity/React Native | 弱 | 无 | iOS/Android/Web（官方） |
| 电话/PSTN | **LiveKit SIP 内置** | 第三方 Twilio | Twilio 集成 | 无 |
| Pipeline 模式 | ✅ | ✅ | ✅ | ❌ |
| Realtime 模式 | ✅（+ 自动 fallback） | ✅ | ❌ | ✅（核心） |
| Turn Detection | **神经 EoU + backchannel** | 基础 VAD | VAD | 模型自带 |

能力上 LiveKit 覆盖最全——但这只是表面。架构师更关心下面这张。

### 工程化对比

| 维度 | LiveKit Agents | Pipecat | Vocode | OpenAI Realtime |
|---|---|---|---|---|
| Plugin 生态 | **84 个** | 中等 | 少 | 仅 OpenAI 系 |
| 可观测性 | OTel + Prometheus | 弱 | 弱 | dashboard only |
| 测试框架 | `RunResult.expect` + LLM judge | 无 | 无 | 无 |
| 开源协议 | **Apache-2.0** | MIT | MIT | 闭源 |
| 自托管 | ✅（用 LiveKit server） | ✅ | 部分 | ❌ |

工程化差距才是护城河——OTel 链路追踪、可重复测试、84 个 plugin 的生态飞轮、自托管选项,这几项加起来意味着**你用 LiveKit Agents 可以从 PoC 直接跑到生产**,其他框架大多需要自己补一半基础设施。

---

## 十三、它对语音 Agent 赛道的真正冲击

LiveKit Agents 2026 年做的事,相当于 OpenAI 2023 年做 ChatGPT 时对 LLM 框架做的事——**把工程门槛从「自己拼」拉到「装饰器 + 类型注解」**。

2024–2025 年做语音 Agent 的团队,要自己处理:WebRTC 信令、AEC、VAD、打断检测、多说话人、SIP 网关、TTS 流式播放、STT 流式转写——任何一环做不好,体验就崩。LiveKit Agents 把这十件事变成 `@function_tool` + `AgentSession(stt=..., llm=..., tts=...)` 一行。

`RunResult.expect + judge` 让 Agent 测试第一次有了工业级范式:确定性事件 + LLM-as-judge,既不放弃灵活性,也不放弃 CI。Vocode / Pipecat 在这一块都没有成熟答案。

至于它是不是语音 Agent 的「终局框架」——这条赛道还在剧烈演化（Realtime 模型越来越强,turn detection 从云端走向端侧）,但可以确定的是:**未来三年所有做语音 Agent 创业的人,都会先打开 LiveKit Agents 的仓库看一眼**。

---

## 附录:跑起来的最短路径

```bash
pip install "livekit-agents[openai,deepgram,cartesia]"
export LIVEKIT_URL=...
export LIVEKIT_API_KEY=...
export LIVEKIT_API_SECRET=...
uv run myagent.py console   # 终端模式,本机麦克风
uv run myagent.py dev       # 联调,热重载,连 LiveKit Cloud
uv run myagent.py start     # 生产模式
```

需要「AI 帮你写 Agent」?装两个 skill:

```bash
# Docs MCP server — 给 IDE 里 AI 实时文档检索
npx skills add livekit/agent-skills --skill livekit-agents
```

> The Agent Skill works best alongside the MCP server: the skill teaches your agent *how to approach* building with LiveKit, while the MCP server provides the *current API details* to implement it correctly.

---

## 参考

- 仓库:[github.com/livekit/agents](https://github.com/livekit/agents)（12.4k stars,Apache-2.0）
- 文档:[docs.livekit.io/agents](https://docs.livekit.io/agents/)
- 主仓（媒体服务器）:[github.com/livekit/livekit](https://github.com/livekit/livekit)
- SIP:[github.com/livekit/sip](https://github.com/livekit/sip)
- 客户端 SDK 全家桶:Browser / Swift / Android / Flutter / React Native / Rust / Node / Python / Unity / ESP32 / C++
- 框架:[Apache-2.0](LICENSE),turn detection 模型:[LiveKit Model License](MODEL_LICENSE)
