---
title: "Agentic Video Editor：用多智能体架构重新定义视频剪辑"
date: "2026-04-17T16:10:00+08:00"
slug: "agentic-video-editor-ai-multi-agent-video-production"
github_repo: "poseljacob/agentic-video-editor"
description: "一个开源的 CLI 视频剪辑工具：把素材库和创意简报交给四个 AI 智能体——Director 选镜头、TrimRefiner 校准切点、Editor 渲染、Reviewer 打分返工——一条命令出成片。本文基于仓库源码拆解它的流水线编排、A-Roll/B-Roll 叙事机制与质量评审回路。"
draft: false
categories: ["技术笔记"]
tags: ["多智能体", "Gemini", "FFmpeg", "Python", "LLM"]
---

# Agentic Video Editor：用多智能体架构重新定义视频剪辑

> **一句话判断**：AVE 真正解决的，不是"用 AI 剪视频"这个口号，而是把剪辑从一次性的生成动作，改造成一条可观察、可返工、可积累版本的流水线——每个环节由独立智能体负责，失败能指认到具体环节，版本能逐个对比。

> **目标读者**：正在用 AI 做应用开发的工程师、常剪视频想提效的创作者、对"多个 AI 智能体怎么一起干活"感兴趣的技术读者。
> **核心问题**：视频剪辑涉及素材理解、镜头选择、节奏把控、质量评审多个环节，单个 AI 模型能否独立完成？如果不能，多智能体分工怎么设计？
> **事实边界**：本文基于 `poseljacob/agentic-video-editor` 仓库 2026-04-14 的源码与文档整理。未出现在源码里的行为、参数与性能数字，不写成事实。

## 阅读导航

### 完整目录

- §1 学习目标
- §2 背景与动机：为什么视频剪辑需要多智能体
- §3 核心架构：四大 Agent 体系
  - §3.1 整体架构图
  - §3.2 Director Agent（AI 导演）
  - §3.3 Trim Refiner Agent（裁剪优化）
  - §3.4 Editor Agent（视频渲染）
  - §3.5 Reviewer Agent（质量评审）
- §4 流水线系统：YAML 定义的多 Agent 协作
  - §4.1 流水线架构
  - §4.2 重试循环机制
  - §4.3 自定义 Pipeline 示例
- §5 Style Template：结构化的创意控制
- §6 预处理系统：素材理解与索引
  - §6.1 Preprocessor 职责
  - §6.2 footage_index.json 结构
  - §6.3 缓存机制
- §7 部署与使用
  - §7.1 环境准备
  - §7.2 快速开始
  - §7.3 Web UI（AVE Studio）
- §8 项目结构与技术栈
- §9 扩展与开发
- §10 常见问题
- §11 练习与自测
- §12 进阶路径
- §13 资料口径说明

### 按需跳转

- 只想了解多智能体架构：直接看 §3 核心架构
- 想动手运行：直接看 §7 部署与使用
- 想了解质量评审机制：重点看 §3.5 Reviewer Agent 和 §4.2 重试循环
- 想自定义流水线：重点看 §4.3 自定义 Pipeline 示例

## §1 学习目标

读完本文，你应该能：

1. 说清为什么视频剪辑不适合单个 AI 智能体独立完成，需要多智能体分工
2. 描述 AVE 的四个智能体（Director、TrimRefiner、Editor、Reviewer）各自的职责与协作方式
3. 用 YAML 文件定义一个 Pipeline 工作流程，并配置重试阈值
4. 解释 Style Template 怎么控制剪辑风格，让一批广告有统一的调性
5. 描述 Reviewer 的评分机制：分数不够怎么触发重试、重试次数怎么设、什么时候该停止
6. 把 AVE 跑起来：从安装依赖到出第一个视频

## §2 背景与动机：为什么视频剪辑需要多智能体

### §2.1 传统视频剪辑的耗时分布

| 环节 | 传统方式 | 痛点 |
|------|----------|------|
| 素材浏览 | 人工逐个查看 | 低效、易遗漏 |
| 镜头选择 | 凭直觉判断 | 主观性强、难以规模化 |
| 脚本撰写 | 人工编写 | 需要专业技能 |
| 质量评估 | 完成后 Review | 返工成本高、发现问题太晚 |

### §2.2 单智能体的瓶颈

现有 AI 视频工具大多是"生成式"路线：用户输入 prompt，模型生成一段视频。这条路对"从零生成"有效，却解决不了"用好我自己的素材"——你手上有几十段产品实拍，想剪成一支 30 秒广告，生成式工具无从下手。

单智能体去完成整条剪辑链路，也会遇到三个具体问题：

- **一个 Agent 负责所有决策**：镜头选择和节奏把控互相干扰，决策质量不稳定
- **缺乏质量门控**：成品可能不达标，只能人工返工，而且不知道问题出在哪个环节
- **无法迭代改进**：没有反馈循环，每次生成都是独立尝试，好与坏之间没有联系

### §2.3 多智能体协作的解决思路

**Agentic Video Editor（AVE）** 的做法，是像电影剧组那样分工：Director 读创意简报、挑镜头、定顺序；TrimRefiner 逐刀校准切点；Editor 只负责渲染；Reviewer 看完成品打分，分数不够就把具体意见退回给 Director 重来。

这样拆开有几个实际好处：

- 每个智能体只做一件事，决策边界清晰，问题能指认到具体环节
- 用 YAML 文件定义工作流程，流水线可见、可改、可调试
- Reviewer 打分并给出具体意见，形成反馈循环，而不是简单"重试"
- 每次尝试都存为独立版本（`_v1`、`_v2`），方便逐个对比选优

## §3 核心架构：四大 Agent 体系

### §3.1 整体架构图

```
原始素材 + 创意简报
        │
        ▼
┌─────────────────────┐
│   Preprocessor       │ ←─ 场景检测 + 语音转写，产出 footage_index.json
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│     Director         │ ←─ Gemini 3.1 Pro：选镜头、定顺序、生成 EditPlan
│  (AI 导演 Agent)    │     （区分 A-Roll 叙事 / B-Roll 覆盖）
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Trim Refiner      │ ←─ 探针片段并行分析，逐刀收紧切点
│  (裁剪优化 Agent)   │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│      Editor          │ ←─ FFmpeg 渲染 + 自动字幕烧录（纯执行）
│  (视频编辑 Agent)   │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│     Reviewer         │ ←─ 4+1 维度评分，overall 低于阈值触发重试
│  (质量评审 Agent)   │
└────────┬────────────┘
         │ 反馈意见退回 Director
         └─────────────────────┐
                                  │ (重试循环，每次存为 _vN 版本)
                                  ▼
                            最终成品 + 评分报告
```

### §3.2 Director Agent（AI 导演）

Director 先读懂创意简报——卖什么产品、给谁看、什么风格、多长时长——然后到素材索引里找合适的镜头，决定顺序与裁剪区间，最后输出一份结构化的 `EditPlan`。它只做决策，不执行任何剪辑。

**模型**：`gemini-3.1-pro-preview`，基于 Google ADK（Agent Development Kit）构建。

**两个工具，成本一低一高**：

| 工具 | 做什么 | 成本 |
|------|--------|------|
| `search_moments` | 本地词法排序：把查询词与镜头的描述、转写文本、文件名分词后计算重合度，按 `min_relevance` 过滤、`max_results` 截断 | 低、确定、不联网 |
| `analyze_footage` | 把单个视频片段发给 Gemini 原生视频输入做逐场景深度分析，返回每个场景的 `energy_level`、`visual_quality`、`relevance_to_brief`、`key_quote` | 高，只对 2-4 个最强候选调用 |

源码中的真实构建方式（摘取真实签名）：

```python
# src/agents/director.py（真实代码结构）
from google.adk.agents import Agent
from src.models.schemas import CreativeBrief, EditPlan
from src.tools.analyze import analyze_footage, search_moments

_MODEL_ID = "gemini-3.1-pro-preview"

def build_director(brief: CreativeBrief) -> Agent:
    """构造一个把简报细节烧进指令的 Director Agent。"""
    return Agent(
        name="director",
        model=_MODEL_ID,
        instruction=build_runtime_instruction(brief),
        tools=[search_moments, analyze_footage],
        output_schema=EditPlan,   # 强制输出符合 Pydantic 契约
    )
```

**EditPlan 的真实数据结构**（`src/models/schemas.py`）：

```python
class EditPlanEntry(BaseModel):
    shot_id: str                    # 形如 "clip_001.mp4#12.5" 的镜头引用
    start_trim: float               # 入点（相对源文件，秒）
    end_trim: float                 # 出点（相对源文件，秒）
    position: int                   # 时间线槽位，0..N-1 必须连续无空洞
    text_overlay: str | None = None # 仅用于非语音标题卡，不用于对话字幕
    transition: str | None = None   # 进入本镜头的转场，默认 "cut"

class EditPlan(BaseModel):
    brief: CreativeBrief            # 原始简报原样带回
    entries: list[EditPlanEntry]    # 5-10 条，按播放顺序排列
    music_path: str | None = None   # 默认 null，音乐由 Editor 后选
    total_duration: float           # 仅 A-Roll 时长之和
```

注意 `shot_id` 的约定：`"{source_file}#{start_time}"`。Editor 拿到它时，按最后一个 `#` 拆分、把后缀解析成浮点秒数，再去 `FootageIndex.shots` 里按 `(source_file, start_time)` 匹配。选这个格式是为了不依赖素材索引里的排列顺序——索引每次预处理后顺序可能变化，但每个镜头的固有字段不变。

**A-Roll / B-Roll：这套系统最值得看的设计**

Director 的指令里有一组硬约束，理解它们才能真正看懂 AVE 的剪辑逻辑：

- 预处理时，每个镜头按所在目录名自动标记 `roll_type`：`a-roll`（出镜人物、口播）或 `b-roll`（产品特写、纹理、包装、环境空镜）
- **A-Roll 承载叙事**：被当作基础时间线，所有 A-Roll 镜头按顺序拼成一条有连续旁白音频的底片
- **B-Roll 是视觉覆盖层**：叠加在 A-Roll 之上，人物声音在下面继续播放，**不占用时间线时长**
- `EditPlan.total_duration` 只统计 A-Roll 时长之和，B-Roll 一律不算

落到创作规则上，Director 被要求：

- **节奏交替**：绝不连续排三个高能量或三个低能量镜头
- **开场即钩子**：前 3 秒必须用最高能量或最抓眼的镜头留住观众
- **叙事弧**：按"问题 → 解决方案 → 证明 → 行动号召"排布节拍（不是每个简报都需四拍，但顺序重要）
- **时长约束**：A-Roll 总时长需在目标时长的 ±10% 以内
- **条目数**：5-10 条，少于 5 缺少变化，多于 10 对短视频太碎
- **禁止伪造**：`shot_id` 必须来自 `search_moments` 的真实返回，不得臆造时间戳或源文件

### §3.3 Trim Refiner Agent（裁剪优化）

Director 给的入点出点通常是"大概准"。TrimRefiner 的任务是逐刀收紧——但它的做法不是简单前移后移，而是**探针分析**：

1. 对每个 entry 的 `start_trim` 和 `end_trim`，各截取一段约 6 秒的探针片段（切点两侧各保留 3 秒上下文）
2. 把探针片段**并行**发给 Gemini（最多 6 路并发）做帧级时序分析
3. 拿到更精确的切点，生成一份只改了时间的 `EditPlan`

关键约束：**它只收紧时间，绝不改变镜头选择、顺序或任何创作字段**。这是它和 Director 的边界。

```python
# src/agents/trim_refiner.py（真实常量与入口）
_PROBE_MARGIN_SECONDS = 3.0   # 每个切点两侧各取 3 秒上下文
_MAX_WORKERS = 6              # 并行探针分析的工作线程数

def refine_plan(edit_plan: EditPlan, footage_index_path: str) -> EditPlan:
    """返回一个 start_trim / end_trim 被收紧的新 EditPlan。"""
```

### §3.4 Editor Agent（视频渲染）

前面两个 Agent 都在"做计划、优化计划"。Editor 才是动手的：它拿到最终 `EditPlan`，机械地执行渲染——**不做任何创作决策**。Director 决定"剪什么"，Editor 负责"怎么剪出来"。

它挂了六个工具，对应六步操作：

| 工具 | 做什么 |
|------|--------|
| `cut_clip` | 用 stream copy 提取子片段（不重编码，快） |
| `sequence_clips` | 用 FFmpeg concat demuxer 按 `position` 顺序拼接 |
| `generate_ass_captions` | 按真实的逐词时间戳生成 TikTok 风格 ASS 字幕 |
| `burn_ass_subtitles` | 用 FFmpeg `ass` 滤镜把字幕烧进画面 |
| `add_music` | 在保留原音轨的前提下混入背景音乐 |
| `render_final` | H.264 MP4 导出，带宽高比安全缩放 |

有两个容易被忽略的细节：

- **字幕来自真实语音**：字幕不是模型编的，而是预处理阶段转写出的逐词时间戳（`words` 字段），所以口型、节奏天然对齐。这就是为什么 Director 指令要求 `text_overlay` 字段只用于标题卡——对话字幕交给 Editor 后置生成。
- **出错不猜**：如果某个镜头在计划里不存在、裁剪窗口越界、或任一工具调用失败，Editor 会把错误原样报出，而不是猜测或静默产出残缺文件。

Editor 返回的是纯文本路径（最终 MP4 的位置），不挂 `output_schema`——它不需要结构化输出。

### §3.5 Reviewer Agent（质量评审）

视频渲染完了，质量怎么样？Reviewer 只看不剪：它调用 `review_output` 工具，把渲染好的视频连简报一起交给 Gemini 原生视频输入，返回一个 `ReviewScore`。

**评分维度**（每项 0.0-1.0）：

- **Adherence（贴合度）**：成片是否忠于简报的产品、受众、语气
- **Pacing（节奏感）**：能量弧线、钩子强度、剪辑节奏
- **Visual Quality（视觉质量）**：构图、取景、色彩、清晰度
- **Watchability（观看体验）**：观众会不会看到最后——这是最重要的留存信号
- **Overall（综合评分）**：**整体判断，不是前四个维度的平均**。某个维度崩坏（尤其钩子太弱）就应当把整体分拉下来，而不是被其他高分稀释

这里要特别说清楚 `overall` 的语义。源码里的原话是 "holistic judgment, NOT a plain mean"——如果四个维度平均 0.9，但钩子很差，overall 就不该是 0.9。这是刻意的设计：防止"平均分好看、成品没人看"的虚假及格。

**反馈契约**：`feedback` 字段必须是具体、可操作的建议。当 `overall < 0.7` 时，反馈**必须**引用节拍、镜头编号或时间戳（例如"0:00-0:03 的钩子太弱，用 1 号镜头换成产品特写"）；像"还能更好"这种含糊话术会被运行时校验拒绝——空反馈直接抛错。

**一道安全防线**：简报文本是不可信的输入（它可能来自用户，甚至被注入），而 `review_output` 会让模型自行选择要读取的视频路径。为了防止简报诱导模型把任意本地文件（如 `/etc/passwd`）上传给 Gemini，`run_reviewer` 会在调用前把已经批准的成片路径解析成规范路径并绑定进 `ContextVar`，`review_output` 只接受这条路径，任何不匹配都拒绝。

```python
# src/agents/reviewer.py（真实入口签名）
def run_reviewer(brief: CreativeBrief, video_path: str) -> ReviewScore:
    """跑完整个评审：构建 Agent → 单轮会话 → 校验输出 → 返回 ReviewScore。"""
```

## §4 流水线系统：YAML 定义的多 Agent 协作

### §4.1 流水线架构

Pipeline 是 AVE 的核心编排机制，用 YAML 定义。每个 step 命名一个 Agent，可选地声明人工审批门（`gate`）或重试条件（`retry_if`）：

```yaml
# pipelines/ugc-ad.yaml（仓库自带的默认流水线）
name: ugc-ad
description: "用户生成内容广告流水线"

steps:
  - agent: director          # 第一步：导演选择镜头
  - agent: trim_refiner      # 第二步：收紧裁剪点
  - agent: editor            # 第三步：FFmpeg 渲染
  - agent: reviewer          # 第四步：质量评审
    retry_if:
      metric: overall        # 基于综合评分重试
      threshold: 0.65        # 低于 0.65 触发重试
      max_retries: 2         # 最多重试 2 次（共 3 次尝试）
      feedback_target: director  # 评审意见退回给导演
```

`retry_if` 的真实字段（来自 `src/pipeline/runner.py`）：

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `metric` | `overall` | 查看哪个评分维度，可选 `adherence` / `pacing` / `visual_quality` / `watchability` / `overall` |
| `operator` | `<` | 比较运算符，仅支持 `<` 和 `<=` |
| `threshold` | `0.7` | 触发重试的阈值 |
| `max_retries` | `2` | 最大重试次数 |
| `feedback_target` | `director` | 反馈退回给谁，目前只支持 `director` |

### §4.2 重试循环机制

```
┌──────────────────────────────────────┐
│           第一次尝试                  │
│  Director → TrimRefiner → Editor     │
│                  ↓                    │
│              Reviewer                │
│            评分: 0.58                 │
│         0.58 < 0.65? 是              │
└────────────────┬─────────────────────┘
                 │
                 ▼ 反馈退回给 Director
┌──────────────────────────────────────┐
│           第二次尝试                  │
│  Director(+feedback) → ...           │
│                  ↓                    │
│              Reviewer                │
│            评分: 0.67                 │
│         0.67 > 0.65? 是 → 通过       │
└──────────────────────────────────────┘
```

重试不是简单重跑。反馈是如何生效的：`run_director` 本身没有接收评审反馈的参数，所以 runner 里的 `_run_director_with_feedback` 会重新构建一个 Director Agent，把**历次评审反馈历史**追加到它的用户消息里，让导演在下一版里有针对性地改。所有反馈按时间顺序保存在 `PipelineResult.feedback_history` 里，方便排查"越改越差"的回归。

**版本命名**：每次重试迭代都存为独立版本，方便对比——

- 初次输出：`{name}_v1.mp4`
- 第一次重试：`{name}_v2.mp4`
- 第二次重试：`{name}_v3.mp4`

**失败语义**（这部分决定了流水线是"可容忍的工程"而非"一把梭"）：

- 重试预算耗尽、最终评分仍低于阈值：**不抛异常**，返回带 `warnings` 的最佳努力产物（best-effort），把"低分但完整"当作一种正常结局
- 人工审批门被拒绝：返回已生成的 `edit_plan`，但 `final_video_path` 和 `review` 置空，并记录一条警告
- 出现瞬时错误（Gemini 502/503/429）：按 30 秒 → 60 秒 → 120 秒指数退避重试
- 未知的 manifest 键：打印警告并忽略，而不是让流水线崩溃——写错字段不至于全盘皆输

### §4.3 自定义 Pipeline 示例

```yaml
# pipelines/fast-promo.yaml（自定义示例）
name: fast-promo
description: "快速促销视频流水线（无 TrimRefiner）"

steps:
  - agent: director
  - agent: editor
  - agent: reviewer
    retry_if:
      metric: adherence
      threshold: 0.8
      max_retries: 1
```

**可用的 Agent 类型与可选配置**：

| Agent | 说明 | 必需？ |
|-------|------|--------|
| `director` | 镜头选择与 EditPlan 生成 | 是 |
| `trim_refiner` | 裁剪边界收紧 | 否 |
| `editor` | FFmpeg 渲染 | 是 |
| `reviewer` | 质量评分 | 否（但建议保留） |

另外，任意 step 都可以加 `gate: human_approval` 挂一个人工审批点——导演给出剪辑计划后先由人确认再往下走，适合对成品有强把控需求的场景。

## §5 Style Template：结构化的创意控制

### §5.1 Style Template 机制

Style 文件解决"如何让 AI 理解我的风格偏好"：它不是把风格写成几个形容词，而是写成一段**逐节的结构性指导**，由 Director 加载后原样注入提示词。仓库自带的 `dtc-testimonial.yaml` 定义了一支 30 秒的 DTC（Direct-to-Consumer）客户证言广告：

```yaml
# styles/dtc-testimonial.yaml（真实结构）
name: dtc-testimonial
description: "DTC 品牌客户证言广告——钩子、痛点、解决方案、社会证明、行动号召，总时长 30 秒"

structure:
  - segment: hook                    # 开场钩子，3 秒
    duration_seconds: 3
    guidance: "用最高能量或最抓眼的镜头开场，前 3 秒必须留住滑屏用户……"
  - segment: problem                 # 点名痛点，5 秒
    duration_seconds: 5
    guidance: "说出产品解决的问题，优先口播或能展示摩擦感的 B-Roll……"
  - segment: solution                # 展示解决方案，10 秒（最长的一拍）
    duration_seconds: 10
    guidance: "展示产品使用并兑现承诺，让主角镜头喘口气……"
  - segment: social_proof            # 社会证明，7 秒
    duration_seconds: 7
    guidance: "真实客户的证言、评价或反应镜头，优先能说出具体结果的……"
  - segment: cta                     # 行动号召，5 秒
    duration_seconds: 5
    guidance: "清晰的行为号召并带上产品名，配合屏幕文字叠加……"

text_overlay:
  position: bottom-third
  notes: "只在 hook 和 cta 上使用文字叠加，文案不超过 6 个词，方便移动端阅读"

music:
  mood: warm, authentic, low-key
  notes: "选一首能量缓步上升的曲子，避免激进 EDM——这是建立信任的格式，不是炒热气氛的短片"

pacing:
  notes: "能量交替：高（hook）→ 中（problem）→ 高（solution）→ 中（social_proof）→ 高（cta），绝不连续三个低能量节拍"
```

注意它的结构：**`structure` 是一个 segment 列表，每段只有 `segment`、`duration_seconds`、`guidance` 三个字段**。`guidance` 是给模型的自然语言指令；`text_overlay`、`music`、`pacing` 是顶层的全局规则。整个文件被 `load_style_skill` 加载后序列化回 YAML、以代码块形式注入 Director 的提示词，所以文件里的每一个字段都能被模型读到。

`load_style_skill` 有一个值得注意的容错设计：风格文件是可选的——简报可以不引用风格，也可以引用一个不存在或损坏的文件。此时它打印警告并返回 `None`，Director 退回到通用创作原则，**不会因为风格缺失而抛异常**。

### §5.2 Creative Brief Schema

简报是 `CreativeBrief` 的 JSON 表示，也是整条流水线的输入锚点：

```json
{
  "product": "Smart Water Bottle",
  "audience": "Health-conscious women 25-45",
  "tone": "authentic",
  "duration_seconds": 30,
  "style_ref": "styles/dtc-testimonial.yaml"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `product` | string | 产品名 |
| `audience` | string | 目标人群描述 |
| `tone` | string | 语气，如 `energetic`、`calm`、`professional` |
| `duration_seconds` | int | 目标时长（秒） |
| `style_ref` | string? | 风格模板路径，可省略 |

## §6 预处理系统：素材理解与索引

### §6.1 Preprocessor 职责

在 Director 工作之前，Preprocessor 先把素材文件夹变成可搜索的索引。它的管线在 `src/pipeline/preprocess.py` 里，共四步：

```
原始素材文件夹
      │
      ▼
┌─────────────────────────────────┐
│  1. 场景检测                    │ ←─ PySceneDetect ContentDetector（阈值 27.0）
│     每个检测出的场景 = 一个候选镜头 │
├─────────────────────────────────┤
│  2. 语音转写                    │ ←─ Faster-Whisper（默认 base 模型）
│     逐词时间戳，温度 0          │
├─────────────────────────────────┤
│  3. 词级时间戳对齐              │ ←─ 把单词按中点归属到镜头窗口
├─────────────────────────────────┤
│  4. roll_type 标注              │ ←─ 按父目录名推断 a-roll / b-roll / unknown
└─────────────────────────────────┘
      │
      ▼
footage_index.json
```

几个技术细节：

- **支持的格式**：`.mov`、`.mp4`、`.m4v`、`.mkv`，递归扫描整个输入目录
- **场景检测**：PySceneDetect 的 `ContentDetector`，默认阈值 27.0；如果一段视频没检出任何切点，就把它整体当作一个镜头
- **转写**：Faster-Whisper，默认 `base` 模型、CPU、int8 量化，开启 `word_timestamps=True` 拿到逐词时间戳；转写失败（比如纯音乐素材）不会中断，该镜头转写为空即可
- **roll_type 推断**：按文件所在目录名匹配 `a-roll` / `a_roll` / `aroll` → `a-roll`，`b-roll` / `b_roll` / `broll` → `b-roll`，否则 `unknown`。也就是说，素材文件夹的组织方式直接决定了 B-Roll 机制是否生效
- **容错**：单个文件处理出错会记录并跳过，不影响其他素材

### §6.2 footage_index.json 结构

```json
{
  "source_dir": "/path/to/footage",
  "shots": [
    {
      "source_file": "/path/to/footage/A-Roll/clip_001.mp4",
      "start_time": 0.0,
      "end_time": 12.4,
      "description": "",
      "energy_level": 0,
      "relevance_score": 0.0,
      "transcript": "This water bottle tracks my hydration...",
      "words": [
        { "word": "This", "start": 0.12, "end": 0.24 },
        { "word": "water", "start": 0.25, "end": 0.41 }
      ],
      "roll_type": "a-roll"
    }
  ],
  "total_duration": 123.45,
  "created_at": "2026-04-17T12:00:00Z"
}
```

对应 `FootageIndex` 的 Pydantic 模型：

| 字段 | 说明 |
|------|------|
| `source_dir` | 素材根目录 |
| `shots` | 镜头列表 |
| `total_duration` | 所有镜头时长之和 |
| `created_at` | 生成时间（UTC） |

每个 `Shot` 的核心字段：`source_file`（源文件路径）、`start_time` / `end_time`（镜头窗口，秒）、`description`（场景描述，预处理阶段为空，由 `analyze_footage` 补充）、`energy_level`（能量级）、`relevance_score`（词法相关度，预处理阶段为 0）、`transcript`（转写文本）、`words`（逐词时间戳，字幕数据源）、`roll_type`（素材类型）。

### §6.3 缓存机制

README 明确写了索引"会在运行间缓存"（Cached between runs）。实际表现是：预处理结果落到磁盘上的 `footage_index.json`，CLI 每次运行都会复用已存在的索引，避免重复转写——这也是为什么素材变化后需要重新运行预处理来重建索引。

## §7 部署与使用

### §7.1 环境准备

**前置条件**：

- Python 3.11+
- FFmpeg（必须安装并在 PATH 中）
- 一个 Google AI API Key（用于 Gemini）

**安装步骤**（两种方式任选）：

```bash
# 1. 克隆仓库
git clone https://github.com/poseljacob/agentic-video-editor.git
cd agentic-video-editor

# 2a. 虚拟环境 + pip
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# 2b. 或使用 uv（仓库自带 uv.lock）
uv sync
source .venv/bin/activate

# 3. 配置 API Key
cp .env.example .env
# 编辑 .env，添加：GOOGLE_API_KEY=your_api_key_here

# 4. 验证 FFmpeg
ffmpeg -version
```

注意环境变量名是 `GOOGLE_API_KEY`——这是 `.env.example` 和 `src/tools/analyze.py` 里实际读取的名字，不是 `GOOGLE_AI_API_KEY`。

### §7.2 快速开始

```bash
# 基本用法
ave edit \
  --footage-dir /path/to/your/footage \
  --brief '{"product": "My Product", "audience": "Women 25-45", "tone": "authentic", "duration_seconds": 30}' \
  --pipeline pipelines/ugc-ad.yaml \
  --style styles/dtc-testimonial.yaml
```

几个要点：

- `--brief` 除了内联 JSON，也可以传一个 JSON 文件路径
- `--pipeline` 默认是 `pipelines/ugc-ad.yaml`，不传则走默认流水线
- 输出默认落在 `output/` 目录（可用 `--output` 覆盖）

**输出**：

```
output/
├── dtc-ad_v1.mp4      # 第一次尝试
├── dtc-ad_v2.mp4      # 第二次尝试（如果需要）
├── dtc-ad_v3.mp4      # 第三次尝试（如果需要）
└── review_report.json  # 评分报告
```

### §7.3 Web UI（AVE Studio）

AVE Studio 是实验性功能，README 明确标注 **pre-alpha，不是推荐使用方式**，功能可能不完整、会破坏性变更。CLI 才是受支持的主界面。想尝鲜的话：

```bash
# 安装前端依赖（需要 Node.js 18+ 和 pnpm）
cd src/web/studio
pnpm install
cd ../../..

# 终端 1：FastAPI 后端
source .venv/bin/activate
uvicorn src.web.app:app --reload --port 8000

# 终端 2：Next.js 前端
cd src/web/studio
pnpm dev --port 3000
```

然后打开 `http://localhost:3000`。后端在 `http://localhost:8000` 暴露 REST API（jobs、projects、footage、feedback、edit plan CRUD），另有 `/ws/jobs/{id}` WebSocket 推送实时进度。

**Web UI 功能预览**（传统非线性编辑器的布局）：

- 项目浏览器（Project Picker）
- 源视频/节目监视器（Source/Program Monitor）
- 拖拽式时间线（Drag-and-drop Timeline）
- 素材浏览器（Media Browser）
- 属性检查器（Inspector）
- 评分雷达图（Review Radar Chart）

## §8 项目结构与技术栈

### §8.1 目录结构

```
agentic-video-editor/
├── .env.example                 # GOOGLE_API_KEY 模板
├── pyproject.toml               # Python 项目配置（hatchling 构建）
├── uv.lock                      # uv 锁文件
├── pipelines/
│   └── ugc-ad.yaml              # 默认流水线
├── styles/
│   └── dtc-testimonial.yaml     # 30 秒 DTC 广告风格模板
├── src/
│   ├── main.py                  # Click CLI 入口（ave edit）
│   ├── agents/                  # 四个 ADK Agent
│   │   ├── director.py
│   │   ├── trim_refiner.py
│   │   ├── editor.py
│   │   └── reviewer.py
│   ├── models/
│   │   └── schemas.py           # 全部 Pydantic 数据模型
│   ├── pipeline/
│   │   ├── preprocess.py        # 场景检测 + 转写 + 索引
│   │   └── runner.py            # 流水线编排 + 重试循环
│   ├── tools/                   # Agent 可调用的工具函数
│   │   ├── analyze.py           # search_moments / analyze_footage / review_output
│   │   ├── captions.py          # ASS 字幕生成与烧录
│   │   ├── edit.py              # cut_clip / sequence_clips / add_music
│   │   └── render.py            # render_final
│   └── web/                     # 实验性 Web UI（pre-alpha）
│       ├── app.py               # FastAPI 应用
│       ├── jobs.py              # 后台任务注册
│       ├── routes/              # REST API 路由
│       └── studio/              # Next.js 前端
├── tests/                       # pytest 测试套件
└── README.md
```

### §8.2 技术栈

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| AI 框架 | Google ADK ≥1.0 | Agent、InMemoryRunner、结构化输出桥接 |
| LLM | Gemini 3.1 Pro（preview） | 多模态，原生视频输入 |
| 场景检测 | PySceneDetect | ContentDetector，阈值 27.0 |
| 语音转写 | Faster-Whisper | 默认 base 模型，词级时间戳 |
| 视频渲染 | FFmpeg | concat demuxer、ass 滤镜 |
| 字幕 | pysubs2 | ASS 字幕生成 |
| 视频编辑 | MoviePy ≥2.0 | 依赖声明，主要渲染路径走 FFmpeg |
| 数据验证 | Pydantic ≥2.0 | 结构化输出 schema |
| CLI | Click | `ave` 命令入口 |
| Web 后端 | FastAPI | REST + WebSocket |
| Web 前端 | Next.js | React 框架 |
| 包管理 | uv | uv.lock 锁定依赖 |
| 测试 | pytest | `tests/` 目录 |

## §9 扩展与开发

### §9.1 自定义 Agent 开发

新增 Agent 需要自己接入 ADK 的 `Agent` 类。真实项目的模式是：模块级导出一个默认 Agent 实例（供 ADK 自动发现和测试），另提供一个工厂函数（如 `build_director(brief)`）在真实运行时注入简报上下文。想加一个自定义 Agent，参考 `src/agents/` 下的四个文件即可。

### §9.2 自定义工具函数

仓库的工具函数遵循一个约定：**完整的类型注解 + Google 风格 docstring**，这样 ADK 的自动工具检测能直接拾取。一个真实的工具示例（`src/tools/analyze.py` 里的 `search_moments`）：

```python
def search_moments(
    footage_index_path: str,
    query: str,
    min_relevance: float = 0.2,
    max_results: int = 5,
) -> list[dict]:
    """在 FootageIndex 上做本地词法排序检索。

    对镜头的描述、转写文本、roll_type 与文件名分词，与查询词计算
    token 重合度，过滤低于 min_relevance 的结果，按相关度降序返回
    最多 max_results 条。纯本地、确定性、不调用模型。
    """
```

给 Agent 挂工具也很直接——在 `Agent(..., tools=[search_moments, analyze_footage])` 里列出即可，不需要额外包装。

### §9.3 与其他系统集成

以下方向仓库当前没有内置，属于基于其架构的自然扩展点：

| 集成方向 | 思路 | 场景 |
|----------|------|------|
| 素材管理 | 接入云存储或素材 API | 云端素材库 |
| 自动字幕 | 更换/升级转写引擎 | 多语言内容 |
| 配音 | 接入 TTS 服务 | AI 配音生成 |
| 社交发布 | 对接视频平台 API | 一键发布 |

## §10 常见问题

**Q1：跑一条流水线要花多少钱？**

A：成本主要由 Gemini 调用构成——Director、TrimRefiner、Reviewer 各至少一次，重试还会翻倍，加上视频上传流量。具体费用取决于素材时长、镜头数量和 `max_retries` 设置，需要按实际用量评估，仓库没有公布参考数字。

**Q2：支持哪些视频格式输入？**

A：预处理阶段支持 `.mov`、`.mp4`、`.m4v`、`.mkv`，FFmpeg 能处理的更多格式理论上也能喂给 Editor。

**Q3：可以处理长视频吗？**

A：可以，但预处理阶段要对每个文件做场景检测和逐词转写，素材越长耗时和成本越高。仓库示例都是短视频广告，长素材需要评估性价比。

**Q4：Reviewer 的重试次数可以无限吗？**

A：`max_retries` 默认 2，README 建议 2-3 次封顶。重试会显著增加成本（每轮多一次 Director + TrimRefiner + Reviewer 的 Gemini 调用），且收益递减。即使重试预算耗尽、评分仍不达标，流水线也会返回最佳努力的产物而不是报错。

**Q5：Web UI 什么时候能用？**

A：目前是 pre-alpha 状态，README 明确不推荐生产使用，请用 CLI。

**Q6：Reviewer 是怎么"看"视频的？**

A：走 Gemini 的原生视频输入：`review_output` 把视频传给 Gemini 3.1 Pro（小于 20 MB 内联上传，更大的走 File API 并轮询到 ACTIVE 状态），模型返回结构化评分。这也是为什么 `run_reviewer` 需要提前批准视频路径——防止不可信的简报文本诱导模型读取其他文件。

## §11 练习与自测

### 练习 1：理解多智能体协作

假设你有一个 5 分钟的产品介绍视频素材，想要剪辑成 30 秒的广告。请描述 AVE 的四个 Agent 分别会做什么，以及它们是如何协作的。

<details>
<summary>参考答案</summary>

1. **Preprocessor**：用 PySceneDetect 切出场景、Faster-Whisper 转写台词，把镜头和词级时间戳写进 `footage_index.json`，并按目录名标注 A-Roll / B-Roll
2. **Director**：读简报，用 `search_moments` 按节拍检索候选镜头、`analyze_footage` 深挖 2-4 个最强候选，生成 5-10 条的 `EditPlan`（A-Roll 串起叙事，B-Roll 做覆盖）
3. **Trim Refiner**：对每个切点截探针片段并行送 Gemini，收紧入点出点，不改镜头选择和顺序
4. **Editor**：按计划用 FFmpeg 渲染，自动从真实词级时间戳生成并烧录 ASS 字幕
5. **Reviewer**：把成片连简报交给 Gemini 打分（4+1 维）。`overall` 低于阈值时，反馈意见退回给 Director 触发重试，每次尝试存为独立版本

协作方式：通过 YAML 定义的 Pipeline 串联，Reviewer 的评分决定是否触发重试循环。

</details>

### 练习 2：自定义 Pipeline 配置

你想创建一个快速剪辑流水线，只需要 Director 选择镜头、Editor 渲染，不需要 TrimRefiner 优化，也不需要 Reviewer 评分。请写出这个 Pipeline 的 YAML 配置。

<details>
<summary>参考答案</summary>

```yaml
name: quick-edit
description: "快速剪辑流水线（无优化、无评审）"

steps:
  - agent: director
  - agent: editor
```

不需要配置 `retry_if`，因为不需要 Reviewer。

</details>

### 练习 3：Style Template 设计

你要为一个健身 App 制作广告，目标受众是 25-35 岁的都市男性，风格要有活力、激励人心。请按 AVE 的真实格式设计这个广告的 Style Template（至少 3 个段）。

<details>
<summary>参考答案</summary>

```yaml
name: fitness-app
description: "健身 App 广告——对比开场、痛点、解决方案、行动号召"

structure:
  - segment: hook
    duration_seconds: 3
    guidance: "用健身前后的对比画面开场，前 3 秒必须抓眼球"
  - segment: problem
    duration_seconds: 7
    guidance: "展示没时间健身、没动力的日常场景"
  - segment: solution
    duration_seconds: 12
    guidance: "App 登场，展示训练计划与效果，这是最长的一拍"
  - segment: cta
    duration_seconds: 8
    guidance: "清晰的行为号召，配合下载 App 的文字叠加"

text_overlay:
  position: bottom-third
  notes: "在 hook 和 cta 上使用文字叠加，文案不超过 6 个词"

music:
  mood: energetic, driving
  notes: "选一首有冲击力的曲目，能量持续上升"

pacing:
  notes: "能量交替：高 → 中 → 高 → 高，避免连续低能量"
```

设计要点：开场抓眼球，中间展示价值，结尾促行动。能量曲线要体现交替原则。

</details>

### 练习 4：分析 Reviewer 评分

如果一个广告视频的 Adherence 得分 0.9（很高），但 Watchability 只有 0.4（很低），可能是什么原因？这会怎样影响 `overall`？

<details>
<summary>参考答案</summary>

**可能原因**：

- 完全按简报来，但太说教、太广告化，观众不想看下去
- 镜头选择没错，但节奏拖沓或跳跃太大
- 文字叠加太多、太密，干扰观看

**对 overall 的影响**：按 AVE 的设计，`overall` 不是四个维度的平均——Watchability 只有 0.4 会把整体分明显拉低。如果钩子（前 3 秒）很弱，即使其余维度高分，`overall` 也不该虚高，因为弱钩子意味着大部分观众根本看不到后面的内容。

**改进方向**：

- 让 Director 在下一轮更多考虑"观看体验"而不仅是"贴合简报"——Reviewer 的具体反馈（引用节拍、镜头编号或时间戳）会帮助它定位问题
- 调整 Style Template，让段落节奏更有变化
- 减少文字叠加，或让文字出现得更短、更精致

</details>

## §12 进阶路径

### 12.1 深入理解多智能体协作

AVE 的四个 Agent 是最小可行架构，实际生产中可在此基础上扩展：加一个专门写解说词的 ScriptWriter Agent、加一个按情绪选背景乐的 MusicSelector Agent、加一个检查字幕与可访问性的 Accessibility Agent。但要注意，每加一个 Agent 就多一条可返工、可出错的链路，职责边界要像 TrimRefiner 那样划清楚（只改时间，不动创作）。

### 12.2 改进 Reviewer 评分质量

单模型的评分天然不稳定。改进方向：多模型投票交叉验证、让 Reviewer 输出评分理由供人工复核、沉淀历史评分数据来校准标准。这些在 AVE 里都是可行的扩展点——`ReviewScore` 的结构化输出和 `feedback_history` 已经为它们铺好了路。

### 12.3 接入生产素材管理系统

AVE 的 Preprocessor 目前处理本地文件系统。生产环境可以接入云存储、素材管理 API、用向量数据库建立素材特征库。注意 `search_moments` 目前是本地词法排序，接素材库时可以考虑替换为语义检索，但会引入额外的模型成本。

### 12.4 参考资源

- [AVE GitHub 仓库](https://github.com/poseljacob/agentic-video-editor)
- [Google ADK 文档](https://adk.dev/)
- [Gemini API Key 获取](https://aistudio.google.com/apikey)
- [FFmpeg 官方文档](https://ffmpeg.org/)
- [MoviePy 文档](https://zulko.github.io/moviepy/)
- [PySceneDetect 文档](https://www.scenedetect.com/)
- [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper)

## §13 资料口径说明

本文基于 Agentic Video Editor（AVE）项目的 GitHub 仓库（[poseljacob/agentic-video-editor](https://github.com/poseljacob/agentic-video-editor)）在 2026-04-14 的 `main` 分支源码撰写，主要来源：

1. **README.md**：项目定位、架构图、Agent 职责表、使用命令
2. **`src/agents/`**：director.py、trim_refiner.py、editor.py、reviewer.py 的模块 docstring 与真实签名
3. **`src/models/schemas.py`**：全部 Pydantic 数据模型的真实字段
4. **`src/pipeline/`**：preprocess.py（场景检测、转写、roll_type 推断）与 runner.py（manifest 校验、重试循环、失败语义）
5. **`src/tools/`**：analyze.py（search_moments / analyze_footage / review_output，含 prompt-injection 防御）、captions.py、edit.py、render.py
6. **`styles/dtc-testimonial.yaml`**：风格模板的真实结构
7. **`pyproject.toml`**：依赖与技术栈
8. **`.env.example`**：环境变量名（GOOGLE_API_KEY）

**局限性说明**：

- 项目仍处于早期阶段（2026-04-14 首次开源，截至 2026-09-05 GitHub Stars 481），部分功能可能不稳定或未完成。撰写时仓库共 6 个提交。
- 文中所有 Agent 均使用 `gemini-3.1-pro-preview`，模型参数与行为可能随 Google 侧更新而变化。
- Web UI（AVE Studio）处于 pre-alpha 阶段，功能和界面可能变化。
- Reviewer 的评分质量取决于 Gemini 的多模态理解能力，实际评分可能与人工评审有差距。
- 文中的代码展示以真实签名和常量为主，省略了与主旨无关的上下文；完整实现以仓库源码为准。

## 相关资源

- **GitHub 仓库**：https://github.com/poseljacob/agentic-video-editor
- **Google ADK 文档**：https://adk.dev/
- **Gemini API Key**：https://aistudio.google.com/apikey
- **FFmpeg 官网**：https://ffmpeg.org/
- **MoviePy 文档**：https://zulko.github.io/moviepy/

## 文档信息

- 难度：⭐⭐⭐
- 类型：开源项目解读
- 更新日期：2026-04-17
- 预计阅读时间：25 分钟
- 前置知识：Python 基础、FFmpeg 基本概念、LLM 多模态理解
