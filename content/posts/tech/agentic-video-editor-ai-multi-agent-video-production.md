---
title: "Agentic Video Editor：用多智能体架构重新定义视频剪辑——从创意简报到成品广告的自动化之旅"
date: "2026-04-17T16:10:00+08:00"
slug: "agentic-video-editor-ai-multi-agent-video-production"
description: "一个获得233 Stars的开源项目，用多个AI智能体协同完成视频剪辑——从理解创意简报、选择镜头、优化剪辑点，到渲染成片和质量评审，全部自动化。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "视频剪辑", "多智能体", "Gemini", "FFmpeg", "Python", "LLM", "自动化生产"]
---

# Agentic Video Editor：用多智能体架构重新定义视频剪辑

这篇文章适合这样的你：正在用AI做应用开发、经常剪视频想提高效率、或者单纯对"多个AI智能体怎么一起干活"这个问题感兴趣。

需要提前知道的一些事：
- 会点Python（3.11以上版本）
- 大概知道LLM和AI Agent是什么
- 本地装了FFmpeg（没有的话待会会告诉你怎么装）
- 有个Google AI API Key（用来调Gemini）

这篇文章有点深度，不是那种看完就能上手的快餐文，但跟着做完一遍，你应该能理解整个系统是怎么跑起来的。

---

## §1 你能从这篇文章学到什么

读完这篇，你应该能搞懂这几件事：

1. 为什么一个AI智能体搞不定视频剪辑，需要多个智能体分工合作
2. AVE的四个智能体（Director、TrimRefiner、Editor、Reviewer）各自干什么、怎么配合
3. Pipeline系统是怎么用YAML文件定义工作流程的
4. Style Template怎么控制剪辑风格，让你的广告有统一的调性
5. Reviewer的评分机制：分数不够就重来，直到满意为止
6. 怎么把AVE跑起来：从安装依赖到出第一个视频

---

## §2 背景与动机：视频剪辑的自动化挑战

### 2.1 传统视频剪辑的局限性

| 环节 | 传统方式 | 耗时 | 痛点 |
|------|----------|------|------|
| 素材浏览 | 人工逐个查看 | 30%-50%工作时间 | 低效、易遗漏 |
| 镜头选择 | 凭直觉判断 | 主观性强 | 难以规模化 |
| 脚本撰写 | 人工编写 | 需要专业技能 | 效率低 |
| 质量评估 | 完成后 Review | 返工成本高 | 发现问题太晚 |

### 2.2 AI 单智能体的瓶颈

现有的 AI 视频工具（如 Runway、Pika）大多是"一键生成"模式：
- 用户输入 prompt → AI 生成视频
- 问题：无法精细控制、不适合"我的素材我做主"

单智能体的问题：
- 一个 Agent 负责所有决策 → 决策质量不稳定
- 缺乏质量门控 → 成品可能不达标
- 无法迭代改进 → 没有反馈循环

### 2.3 多智能体协作的解决思路

**Agentic Video Editor（AVE）** 的做法是：把视频剪辑这件事拆开，让不同的AI智能体各司其职。就像电影制作有导演、剪辑师、制片人一样，AVE用Director理解创意简报并挑选镜头，用TrimRefiner精细调整剪辑点，用Editor负责渲染，再用Reviewer打分决定是否重来。

这样做有几个好处：
- 每个智能体只做一件事，做得更专业
- 用YAML文件定义工作流程，清晰可见
- Reviewer会打分，分数不够就重试，形成反馈循环
- 每次尝试都保存版本，方便对比选优

---

## §3 核心架构：四大 Agent 体系

### 3.1 整体架构图

```
原始素材 + 创意简报
        │
        ▼
┌───────────────────┐
│   Preprocessor    │ ←─ 场景检测、转录、素材索引
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│     Director      │ ←─ Gemini驱动的镜头选择与脚本生成
│  (AI导演Agent)    │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Trim Refiner     │ ←─ 精细化裁剪边界调整
│  (裁剪优化Agent)  │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│      Editor       │ ←─ FFmpeg/MoviePy渲染
│  (视频编辑Agent)  │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│     Reviewer      │ ←─ 5维度评分，触发重试循环
│  (质量评审Agent)  │
└────────┬──────────┘
         │ 分数 < 阈值
         │ 反馈给Director
         └──────────────────┐
                            │ (重试循环)
                            ▼
                      最终成品 + 评分报告
```

### 3.2 Director Agent（AI 导演）

Director就像真人导演一样，先读懂你的创意简报——卖什么产品、给谁看、什么风格、多长时长。然后它会去素材库里找合适的镜头，决定哪个镜头放前面、哪个放后面，最后输出一个详细的剪辑计划（EditPlan），里面包含了每个镜头从哪切到哪、哪里加文字等信息。

**Powered By**：Google Gemini via ADK（Agent Development Kit）

```python
# Director Agent 伪代码逻辑
class DirectorAgent:
    def __init__(self, gemini_client):
        self.gemini = gemini_client
    
    def run(self, brief: CreativeBrief, footage_index: FootageIndex) -> EditPlan:
        # 1. 解析创意简报
        product = brief.product
        audience = brief.audience
        tone = brief.tone
        duration = brief.duration_seconds
        
        # 2. 搜索素材
        relevant_shots = self.gemini.search(
            footage_index,
            criteria=f"{product} for {audience} with {tone} tone"
        )
        
        # 3. 生成剪辑计划
        edit_plan = self.gemini.generate_edit_plan(
            shots=relevant_shots,
            duration=duration,
            style=brief.style_ref
        )
        
        return edit_plan
```

**EditPlan 数据结构**：

```python
class EditPlan(BaseModel):
    shots: List[Shot]           # 镜头列表（有序）
    text_overlays: List[TextOverlay]  # 文字叠加
    transitions: List[str]       # 转场效果
    music_mood: str             # 音乐风格
    
class Shot(BaseModel):
    footage_id: str             # 素材ID
    start_time: float           # 入点
    end_time: float             # 出点
    reason: str                 # 选择理由
```

### 3.3 Trim Refiner Agent（裁剪优化）

Director给出的剪辑计划有时候不够精细——可能切得不那么准，或者节奏还可以更紧凑。Trim Refiner就是干这个的：它拿到EditPlan后，会逐个检查每个镜头的切入点（start_time）和切出点（end_time），然后微调这些时间点。

比如，它不会在人物动作做到一半时切走，而是找到动作完成的那一帧再切。这样剪出来的视频看起来更舒服，节奏也更好。

```python
class TrimRefinerAgent:
    def run(self, edit_plan: EditPlan) -> EditPlan:
        refined_plan = EditPlan()
        
        for shot in edit_plan.shots:
            # 精细化裁剪边界
            new_start = find_best_cut_point(
                shot.start_time, 
                mode='forward'  # 向后找到最佳切点
            )
            new_end = find_best_cut_point(
                shot.end_time,
                mode='backward'  # 向前找到最佳切点
            )
            
            refined_plan.shots.append(Shot(
                footage_id=shot.footage_id,
                start_time=new_start,
                end_time=new_end,
                reason=f"Refined: {shot.reason}"
            ))
        
        return refined_plan
```

### 3.4 Editor Agent（视频渲染）

前面的Agent都是在"纸上谈兵"——做计划、优化计划。Editor才是真正动手的：它拿到最终的EditPlan，调用FFmpeg把素材剪辑、拼接、加转场、叠文字，最后渲染成一个MP4文件。

简单来说，Director决定"剪什么"，Editor负责"怎么剪出来"。底层用的是FFmpeg（行业标准的视频处理工具）和MoviePy（Python的视频编辑库）。

```python
class EditorAgent:
    def __init__(self, ffmpeg_path="/usr/bin/ffmpeg"):
        self.ffmpeg = ffmpeg_path
    
    def run(self, edit_plan: EditPlan, footage_dir: Path) -> Path:
        output_path = Path("output") / f"{edit_plan.name}_v{version}.mp4"
        
        # 构建FFmpeg命令
        ffmpeg_cmd = self.build_ffmpeg_cmd(edit_plan, footage_dir, output_path)
        
        # 执行渲染
        subprocess.run(ffmpeg_cmd, check=True)
        
        return output_path
    
    def build_ffmpeg_cmd(self, plan, footage_dir, output):
        # 1. 拼接视频片段
        # 2. 应用裁剪
        # 3. 添加转场
        # 4. 叠加文字
        # 5. 混音
        pass
```

### 3.5 Reviewer Agent（质量评审）

视频渲染完了，但质量怎么样？Reviewer就是来做质量检查的。

它会从5个维度给视频打分（每个维度0-1分）：
- **Adherence（贴合度）**：视频有没有按照创意简报来？产品展示了吗？目标受众对得上吗？
- **Pacing（节奏感）**：镜头长短搭配合理吗？有没有拖沓或者太赶？
- **Visual Quality（视觉质量）**：剪辑点干净吗？转场自然吗？画面稳不稳？
- **Watchability（观看体验）**：你自己愿意看完吗？还是看两秒就想划走？
- **Overall（综合评分）**：前面几个维度的加权平均。

如果综合评分没达到设定的阈值（比如0.65），Reviewer就会把评分和改进建议反馈给Director，触发重试循环。

```python
class ReviewerAgent:
    def __init__(self, gemini_client):
        self.gemini = gemini_client
    
    def run(self, video_path: Path, brief: CreativeBrief) -> ReviewScore:
        # 让Gemini观看视频并评分
        scores = self.gemini.evaluate_video(
            video_path=video_path,
            criteria={
                "adherence": "是否符合创意简报要求",
                "pacing": "节奏是否流畅",
                "visual_quality": "视觉质量是否达标",
                "watchability": "观看体验"
            }
        )
        
        return ReviewScore(**scores)
    
    def should_retry(self, score: ReviewScore, threshold: float) -> bool:
        return score.overall < threshold
```

---

## §4 流水线系统：YAML 定义的多 Agent 协作

### 4.1 流水线架构

Pipeline 是 AVE 的核心编排机制，用 YAML 定义：

```yaml
# pipelines/ugc-ad.yaml
name: ugc-ad
description: "用户生成内容广告流水线"

steps:
  - agent: director          # 第一步：导演选择镜头
  - agent: trim_refiner      # 第二步：优化裁剪点
  - agent: editor            # 第三步：FFmpeg渲染
  - agent: reviewer          # 第四步：质量评审
    retry_if:
      metric: overall        # 基于综合评分重试
      threshold: 0.65        # 阈值：0.65
      max_retries: 2         # 最多重试2次（3次尝试）
      feedback_target: director  # 反馈给导演改进
```

### 4.2 重试循环机制

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
                 ▼ 反馈给Director
┌──────────────────────────────────────┐
│           第二次尝试                  │
│  Director(+feedback) → ...            │
│                  ↓                    │
│              Reviewer                │
│            评分: 0.67                 │
│         0.67 > 0.65? 是 → 通过       │
└──────────────────────────────────────┘
```

**版本命名规则**：
- 初次输出：`{name}_v1.mp4`
- 第一次重试：`{name}_v2.mp4`
- 第二次重试：`{name}_v3.mp4`

### 4.3 自定义 Pipeline 示例

```yaml
# pipelines/fast-promo.yaml
name: fast-promo
description: "快速促销视频流水线（无TrimRefiner）"

steps:
  - agent: director
  - agent: editor
  - agent: reviewer
    retry_if:
      metric: adherence
      threshold: 0.8
      max_retries: 1
```

**可用的 Agent 类型**：
| Agent | 说明 | 必需？ |
|-------|------|--------|
| `director` | 镜头选择与脚本生成 | 是 |
| `trim_refiner` | 裁剪边界优化 | 否 |
| `editor` | FFmpeg 渲染 | 是 |
| `reviewer` | 质量评分 | 否（但建议保留） |

---

## §5 Style Template：结构化的创意控制

### 5.1 Style Template 机制

Style Template 解决"如何让 AI 理解我的风格偏好"问题：

```yaml
# styles/dtc-testimonial.yaml
name: dtc-testimonial
description: "30秒DTC testimonial广告模板"

# 段落结构
segments:
  - name: hook                    # 开场钩子
    duration: 0-3s
    pacing: high_energy
    text_overlay:
      position: bottom_center
      font_size: 48
      animation: fade_in
    music_mood: upbeat
    
  - name: problem                 # 问题痛点
    duration: 3-10s
    pacing: moderate
    text_overlay:
      position: top_center
      font_size: 36
    music_mood: tension_build
    
  - name: solution                 # 产品解决方案
    duration: 10-22s
    pacing: steady
    text_overlay:
      position: bottom_center
      font_size: 42
    music_mood: positive_reveal
    
  - name: social_proof             # 社会证明（用户评价）
    duration: 22-27s
    pacing: moderate
    text_overlay:
      position: center
      font_size: 32
    music_mood: warm
    
  - name: cta                      # 行动号召
    duration: 27-30s
    pacing: high_energy
    text_overlay:
      position: bottom_center
      font_size: 56
      animation: pulse
    music_momentum: build_to_end

# 全局规则
rules:
  max_shot_duration: 5s
  min_shot_duration: 1s
  transition_style: cut  # 可选: cut, fade, dissolve
```

### 5.2 Creative Brief Schema

```json
{
  "product": "Smart Water Bottle",
  "audience": "Health-conscious women 25-45",
  "tone": "authentic",
  "duration_seconds": 30,
  "style_ref": "styles/dtc-testimonial.yaml"
}
```

---

## §6 预处理系统：素材理解与索引

### 6.1 Preprocessor 职责

在 Director 工作之前，Preprocessor 完成素材理解：

```
原始素材文件夹
      │
      ▼
┌─────────────────────────────────┐
│  1. Scene Detection             │ ←─ 基于内容的场景切分
│     - 自动识别场景切换点          │
│     - 每个场景作为一个候选镜头      │
├─────────────────────────────────┤
│  2. Transcription               │ ←─ 语音转文字
│     - 提取所有对话/旁白           │
│     - 时间戳对齐                  │
├─────────────────────────────────┤
│  3. Shot Indexing                │ ←─ 镜头特征提取
│     - 视觉特征（场景复杂度等）     │
│     - 音频特征（能量级别等）       │
├─────────────────────────────────┤
│  4. Footage Index                │ ←─ 可搜索的素材数据库
│     - 结构化元数据                │
│     - 支持语义搜索                │
└─────────────────────────────────┘
      │
      ▼
footage_index.json
```

### 6.2 footage_index.json 结构

```json
{
  "footage_dir": "/path/to/footage",
  "shots": [
    {
      "id": "shot_001",
      "footage_file": "raw_clips/clip_001.mp4",
      "start_time": 0.0,
      "end_time": 15.3,
      "transcript": "This water bottle tracks my hydration...",
      "visual_features": {
        "scene_complexity": "low",
        "camera_motion": "static",
        "lighting": "natural"
      },
      "audio_features": {
        "energy": "medium",
        "has_speech": true,
        "has_music": false
      }
    }
  ],
  "generated_at": "2026-04-17T12:00:00Z"
}
```

### 6.3 缓存机制

Preprocessor 结果会被缓存：

```python
# 只有素材变化时才重新处理
if footage_index.exists() and is_cache_valid(footage_dir, footage_index):
    logger.info("Using cached footage index")
else:
    logger.info("Generating new footage index")
    footage_index = preprocess(footage_dir)
    footage_index.save()
```

---

## §7 部署与使用

### 7.1 环境准备

**前置条件**：
- Python 3.11+
- FFmpeg（必须安装并在 PATH 中）
- Google AI API Key（用于 Gemini）

**安装步骤**：

```bash
# 1. 克隆仓库
git clone https://github.com/poseljacob/agentic-video-editor.git
cd agentic-video-editor

# 2. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 安装依赖
pip install -e ".[dev]"

# 4. 配置API Key
cp .env.example .env
# 编辑.env，添加：GOOGLE_AI_API_KEY=your_key_here

# 5. 验证FFmpeg
ffmpeg -version
```

### 7.2 快速开始

```bash
# 基本用法
ave edit \
  --footage-dir /path/to/your/footage \
  --brief '{"product": "My Product", "audience": "Women 25-45", "tone": "authentic", "duration_seconds": 30}' \
  --pipeline pipelines/ugc-ad.yaml \
  --style styles/dtc-testimonial.yaml
```

**输出**：
```
output/
├── dtc-ad_v1.mp4      # 第一次尝试
├── dtc-ad_v2.mp4      # 第二次尝试（如果需要）
├── dtc-ad_v3.mp4      # 第三次尝试（如果需要）
└── review_report.json  # 评分报告
```

### 7.3 Web UI（AVE Studio）

实验性功能，仍处于 pre-alpha 阶段：

```bash
# 终端1：启动FastAPI后端
source .venv/bin/activate
cd agentic-video-editor
uvicorn src.web.app:app --reload --port 8000

# 终端2：启动Next.js前端
cd src/web/studio
pnpm install  # 首次需要安装依赖
pnpm dev --port 3000
```

**Web UI 功能预览**：
- 项目浏览器（Project Picker）
- 源视频/节目监视器（Source/Program Monitor）
- 拖拽式时间线（Drag-and-drop Timeline）
- 素材浏览器（Media Browser）
- 属性检查器（Inspector）
- 评分雷达图（Review Radar Chart）

---

## §8 项目结构与技术栈

### 8.1 目录结构

```
agentic-video-editor/
├── .env.example                 # API Key模板
├── pyproject.toml               # Python项目配置
├── pipelines/                   # Pipeline YAML定义
│   └── ugc-ad.yaml
├── styles/                      # Style Template定义
│   └── dtc-testimonial.yaml
├── src/
│   ├── main.py                  # CLI入口（ave edit）
│   ├── agents/                  # AI Agents
│   │   ├── director.py          # Director Agent
│   │   ├── trim_refiner.py      # Trim Refiner Agent
│   │   ├── editor.py            # Editor Agent
│   │   └── reviewer.py          # Reviewer Agent
│   ├── models/                  # Pydantic数据模型
│   │   ├── creative_brief.py
│   │   ├── shot.py
│   │   ├── edit_plan.py
│   │   └── review_score.py
│   ├── pipeline/                # 流水线执行器
│   │   ├── preprocessor.py      # 素材预处理
│   │   └── runner.py            # 流水线运行器
│   ├── tools/                   # Gemini工具函数
│   │   ├── analyze_footage.py
│   │   ├── render_video.py
│   │   └── add_captions.py
│   └── web/                     # 实验性Web UI
│       ├── app.py              # FastAPI应用
│       ├── jobs.py             # 后台任务注册
│       ├── routes/             # REST API路由
│       └── studio/             # Next.js前端
├── tests/                       # 测试套件
└── README.md
```

### 8.2 技术栈

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| **AI 框架** | Google ADK | Agent Development Kit |
| **LLM** | Gemini 2.0 Flash | 多模态理解 |
| **视频处理** | FFmpeg | 底层渲染 |
| **视频编辑** | MoviePy | Pythonic 封装 |
| **数据验证** | Pydantic | 类型安全 |
| **Web 后端** | FastAPI | 异步 API |
| **Web 前端** | Next.js | React 框架 |
| **项目构建** | uv | 现代化 Python 包管理 |

---

## §9 扩展与开发

### 9.1 自定义 Agent 开发

添加新的 Agent 只需：

```python
# src/agents/my_agent.py
from .base import BaseAgent

class MyCustomAgent(BaseAgent):
    name = "my_custom_agent"
    description = "我的自定义Agent"
    
    def run(self, context: dict) -> dict:
        # 实现Agent逻辑
        result = self.do_something(context)
        return result
```

### 9.2 Gemini 工具函数扩展

```python
# src/tools/my_tools.py
from google.adk.tools import FunctionTool

@FunctionTool
def search_footage_by_emotion(footage_index: dict, emotion: str) -> list:
    """根据情感搜索素材片段"""
    # 实现搜索逻辑
    pass
```

### 9.3 与其他系统集成

| 集成方向 | 方案 | 场景 |
|----------|------|------|
| **素材管理** | 连接 Pexels/Unsplash API | 云端素材库 |
| **自动字幕** | Whisper API 集成 | 全球化内容 |
| **配音** | ElevenLabs API | AI 配音生成 |
| **社交发布** | YouTube/TikTok API | 一键发布 |

---

## §10 FAQ

**Q1：需要多少费用的 API Key？**
A：使用 Gemini 2.0 Flash，价格相对低廉。一次 30 秒广告视频的典型消耗约$0.1-0.3。

**Q2：支持哪些视频格式输入？**
A：FFmpeg 支持的所有格式（MP4、MOV、AVI、MKV 等）。

**Q3：可以处理长视频吗？**
A：可以，但建议素材时长在 5 分钟内效果最佳。太长的素材会增加处理时间和成本。

**Q4：Reviewer 的重试次数可以无限吗？**
A：建议设置 2-3 次。过多重试会显著增加成本，且收益递减。

**Q5：Web UI 什么时候能用？**
A：目前是 pre-alpha 状态，生产使用建议用 CLI。Web UI 预计在后续版本完善。

---

## 练习与自测

### 练习1：理解多智能体协作
假设你有一个5分钟的产品介绍视频素材，想要剪辑成30秒的广告。请描述AVE的四个Agent分别会做什么，以及它们是如何协作的。

<details>
<summary>参考答案</summary>

1. **Preprocessor**：先分析素材，做场景检测、语音转文字，建立可搜索的素材索引
2. **Director**：读懂你的创意简报（产品、受众、风格、时长），从素材索引中找到合适的镜头，生成EditPlan
3. **Trim Refiner**：拿到EditPlan后，精细调整每个镜头的切入点切出点，让剪辑更流畅
4. **Editor**：根据EditPlan调用FFmpeg渲染成MP4文件
5. **Reviewer**：观看渲染好的视频，从5个维度打分。如果分数不够，反馈给Director重试

协作方式：通过YAML定义的Pipeline串联，Reviewer的评分决定是否触发重试循环。
</details>

### 练习2：自定义Pipeline配置
你想创建一个快速剪辑流水线，只需要Director选择镜头、Editor渲染，不需要TrimRefiner优化，也不需要Reviewer评分。请写出这个Pipeline的YAML配置。

<details>
<summary>参考答案</summary>

```yaml
name: quick-edit
description: "快速剪辑流水线（无优化、无评审）"

steps:
  - agent: director
  - agent: editor
```

不需要配置`retry_if`，因为不需要Reviewer。
</details>

### 练习3：Style Template设计
你要为一个健身App制作广告，目标受众是25-35岁的都市男性，风格要有活力、激励人心。请设计这个广告的Style Template段落结构（至少3个段落）。

<details>
<summary>参考答案</summary>

```yaml
segments:
  - name: hook                    # 开场：展示健身前后的对比
    duration: 0-3s
    pacing: high_energy
    text_overlay:
      position: center
      font_size: 52
      animation: zoom_in
    music_mood: energetic
    
  - name: problem                 # 痛点：没时间健身、没动力
    duration: 3-10s
    pacing: moderate
    text_overlay:
      position: bottom_center
      font_size: 40
    music_mood: tension
    
  - name: solution                 # 解决方案：App登场
    duration: 10-20s
    pacing: steady
    text_overlay:
      position: bottom_center
      font_size: 44
    music_mood: uplifting
    
  - name: cta                     # 行动号召：下载App
    duration: 20-30s
    pacing: high_energy
    text_overlay:
      position: center
      font_size: 56
      animation: pulse
    music_mood: peak_energy
```

设计要点：开场要抓眼球，中间展示价值，结尾促使行动。
</details>

### 练习4：分析Reviewer评分
如果一个广告视频的Adherence得分0.9（很高），但Watchability只有0.4（很低），可能是什么原因？你会如何改进？

<details>
<summary>参考答案</summary>

**可能原因**：
- 完全按照简报做了，但太说教、太广告化，让人不想看下去
- 镜头选择没错，但剪辑节奏不好，拖沓或者跳跃太大
- 文字叠加太多、太密集，干扰了观看

**改进方向**：
- 让Director在下次尝试时更多考虑"观看体验"，而不仅仅是"符合简报"
- 调整Style Template，让段落节奏更有变化
- 减少文字叠加，或者让文字出现的时间更短、更精致
</details>

---

## 相关资源

- **GitHub 仓库**：https://github.com/poseljacob/agentic-video-editor
- **Google ADK 文档**：https://adk.dev/
- **Gemini API Key**：https://aistudio.google.com/apikey
- **FFmpeg 官网**：https://ffmpeg.org/
