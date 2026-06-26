---
title: "ClaudeCode操控ComfyUI画涩图：ImageAutoPrompt与noobai画师串探索系统深度解读"
date: "2026-05-08T09:55:00+08:00"
slug: "claudecode-imageautoprompt-noobai-artist-exploration"
description: "深度解读VirtualAllocate的B站视频，介绍如何用ClaudeCode驱动ComfyUI结合noobai模型，通过ImageAutoPrompt工具系统化探索danbooru画师标签串，从单画师到多画师权重混合的完整方法论与工作流。"
draft: false
categories: ["视频精读"]
tags: ["AI绘图", "ComfyUI", "ClaudeCode", "noobai", "ImageAutoPrompt", "画师串", "danbooru", "prompt工程"]
---

## 视频信息卡

| 项目 | 内容 |
|------|------|
| 标题 | 我用 ClaudeCode 画涩图：如何探索 illustrious/noob 画师串 |
| UP 主 | [VirtualAllocate](https://space.bilibili.com/45884063) |
| 发布时间 | 2026-05-03 23:09:50 |
| 时长 | 61 分 20 秒 |
| 播放量 | 3562 |
| 点赞 | 134 |
| 收藏 | 535 |
| 硬币 | 48 |
| 评论 | 27 |
| 原视频 | [BV1L7RcBAEqN](https://www.bilibili.com/video/BV1L7RcBAEqN) |
| 相关仓库 | [crclz/ImageAutoPrompt](https://github.com/crclz/ImageAutoPrompt) |

## 前言

这篇视频是作者 VirtualAllocate 在 B 站发布的一套完整 AI 绘图 prompt 探索系统讲解。核心围绕一个用 ClaudeCode 驱动 ComfyUI+noobai 模型、自动探索 danbooru 画师标签串的开源工具[ImageAutoPrompt](https://github.com/crclz/ImageAutoPrompt)展开。视频时长超过 1 小时，干货密度极高，涵盖了从环境搭建、ComfyUI 工作流配置、到画师串系统化探索方法论的完整链路。

本文不只做视频摘要，而是结合作者提供的代码仓库、skill 系统、画师库，进行深度的技术解读与分析。

## 读完这篇文章你会知道

- ImageAutoPrompt 怎么把「显卡空转等人审美」变成双 buffer 流水线
- Episode 和 Timestep 怎么管理 prompt 探索轨迹
- 画师串从单画师到多画师带权重组合的渐进式探索流程
- 4 个 Agent Skill（format-noobai / artist-explore / episode / tag-assistant）各管什么
- RAG 建库怎么解决 invalid tag 问题

## 项目速览

| 字段 | 值 |
|------|-----|
| 仓库 | [crclz/ImageAutoPrompt](https://github.com/crclz/ImageAutoPrompt) |
| Stars | 12+ |
| Forks | 0+ |
| License | 未指定 |
| 主语言 | JavaScript |
| 核心依赖 | Flask、ComfyUI、noobai 模型、danbooru 标签库 |

## 1. 工具链全貌：ClaudeCode + ComfyUI + noobai + ImageAutoPrompt

视频演示的整个工具链涉及四个核心组件：

```
ClaudeCode (AI编程代理)
    ↓ 自然语言指令
ImageAutoPrompt (Flask Web + Agent Skills)
    ↓ API调用
ComfyUI (节点式工作流引擎)
    ↓ 
noobai (专门优化过danbooru标签的文生图模型)
    ↓
生成的图片 → 用户评估 → 反馈给ClaudeCode继续探索
```

**noobai** 是一类专门针对 danbooru 标签体系优化过的文生图模型（视频中使用的是`noobaiXLNAIXL_vPred10Version.safetensors`），其特点是：模型已经过标签对齐训练，使用 danbooru 标准 tag 可以直接触发准确的生成效果，不需要自然语言 prompt 的复杂描述。

**ImageAutoPrompt** 是作者自己开发的工具，核心是一个 Flask Web 服务器，配合 ClaudeCode/OpenCode 作为 AI 编程代理，系统化探索 prompt 空间。它的价值在于：把"显卡空转等人审美决策"的串行等待，变成了"人审美的同时 AI 已经在生成下一批候选"的双 buffer 流水线。

## 2. 环境搭建与 ComfyUI 工作流配置

### 2.1 依赖环境

ImageAutoPrompt 对硬件要求不高：
- Python 3.12+
- 有 GPU 可以加速 embedding 建库，无 GPU 也能运行基础功能
- 需要能访问 GitHub（或者配置代理）

安装步骤：
```bash
git clone https://github.com/crclz/ImageAutoPrompt.git
conda create -n imageautoprompt python=3.12
conda activate imageautoprompt
pip install toml
python export_requirements.py  # 从pyproject.toml导出依赖
pip install -r requirements.txt -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
```

### 2.2 ComfyUI 工作流配置

工具支持任意 ComfyUI 工作流，原理是在用户工作流中插入标志字符串，供程序进行替换。修改步骤：

1. **负面提示词**：固定为模型需要的质量词，探索过程中不对负向提示词进行探索
2. **正面提示词**：拆分为两个输入
   - 一个输入留前缀或后缀固定质量 tag
   - 另一个输入填写 `entropy:positive`（前后不能有空格），二者用 concat 节点连接
3. **图片输出**：仅支持 1 个图片输出，使用图片保存节点，将地址前缀改为 `entropy_out_placeholder`

配置示例（workflow.example.json 中的关键节点）：
```json
{
  "15": {
    "class_type": "StringConcatenate",
    "inputs": {
      "string_a": "entropy:positive",
      "string_b": "masterpiece, best quality, newest, absurdres, highres",
      "delimiter": ","
    }
  },
  "16": {
    "class_type": "ShowText|pysssss",
    "inputs": {
      "text_0": "entropy:positive,masterpiece,best quality,newest,absurdres,highres",
      "text": [...]
    }
  }
}
```

### 2.3 启动服务

```bash
flask --app server run
# 访问Web界面，开始episode探索
```

## 3. 核心概念：Episode 与 Timestep

ImageAutoPrompt 用**Episode**来管理一次完整的 prompt 优化轨迹，用**Timestep**来管理每个探索批次。

### 3.1 Episode

一个 Episode 代表对 prompt 进行优化的完整轨迹。用户需要给 Episode 起一个名字（必须是 snake_case，不能用中文）。所有数据存储在`runs/draft/<episode_name>/`目录下。

### 3.2 Timestep

每个 Episode 由多个 Timestep 组成，基本流程：

1. 基于之前的 prompt 和用户反馈，ClaudeCode 生成新 timestep，存入磁盘文件
2. 通知用户文件路径，用户自己运行文生图
3. 用户给出反馈（选择最喜欢的图片，或者跳过）
4. ClaudeCode 进入下一个 timestep

每个 timestep 生成 4-16 个不同的 prompt 供用户选择，用户可以选择其中一个作为下一个 timestep 的起点，也可以全部跳过。

timestep 文件的命名规则：`timestep_i.md`（i 从 0 开始，建议 2 位数字如 05、10）。

## 4. 画师串探索方法论（核心重点）

这是视频最核心的内容——一套从"无画师"到"多画师带权重组合"的系统化探索流程。

### 4.1 为什么需要画师串

单个画师（artist tag）的作用是有限的，因为每种画风都有其局限性。要达到用户满意的画风，需要叠加多名画师（aka 画师串）。经验总结：

- 单画师效果有限
- 2-5 名画师的组合效果通常更好
- 可以通过括号+权重精细化控制每名画师的影响程度

### 4.2 权重高级技巧

```
(artist:aaa:1.2)  ← 权重1.2，高于默认值，增强该画师影响
(artist:bbb:0.8)  ← 权重0.8，低于默认值，减弱该画师影响
```

权重约束：
- 必须在**0.5-1.2 闭区间**之间
- 调整步进为**0.1**
- 这是高级技巧，不要一上来就用，先从无权重组合开始探索

### 4.3 探索工作流（Artist Exploration Workflow）

作者设计了一套从简单到复杂的渐进式探索流程：

| 持续 timestep 数 | 策略 | prompt 数量/timestep | 备注 |
|----------------|------|---------------------|------|
| 1 | 单画师探索。从 artist library 中大范围选择，一次性生成 16 个候选 | 16 | artist_only 模式；用户无明显停留意图时主动推进到下一阶段 |
| 1 | 2 画师无权重混合。重点关注用户在单 artist 阶段更喜欢的 | 8 | 不要用上一阶段用户完全未看过的画师 |
| 1 | 2-3 画师带权重 | 8 | 注意：1 画师通常不如 2 画师好，但再往上就没这个规律了，得试错 |
| 2 | 2-3-4-5 画师带权重 | 8 | 最后一个 timestep 需平衡 exploration 和 exploitation。前 3 名都很重要 |
| 0 | 得出结论，报告前 3 个最优画师串 | - | 如果用户想进行其他探索，轮换使用前 3 个画师串 |

关键原则：**探索 artist 时，为了控制变量，不修改其他标签**。这确保了图片效果的改善都是因为 artist 的变化，而不是 tag 的干扰。

### 4.4 Free Exploration（自由探索阶段）

当画风收敛到满意情况后，进入自由探索阶段，可以探索：
- 自然环境、社会环境
- 外貌、语言、动作、心理、神态
- 整体外貌、容貌五官、衣着服饰、姿态神情

每次新增的 tag 不超过 6 个（步子太大会造成方差大，不可观测）。

## 5. Agent Skills 系统解析

ImageAutoPrompt 的`.agents/skills/`目录下有 4 个精心设计的 skill，共同构成了完整的 prompt 探索自动化系统。

### 5.1 format-noobai（格式规范）

定义 noobai 模型的 prompt 格式标准，是所有 prompt 生成的基础参考：

**正向提示词结构**：
```
[人数tag 1girl, solo], [角色名 optional], [系列名 optional], [画师tag artist:xxx], [一般tag], [质量词]
```

关键约束：
- **下划线变空格**：`medium_breasts` → `medium breasts`
- **括号需转义**：`lumine_(genshin_impact)` → `lumine \(genshin \impact)`
- **artist 必须添加`artist:`前缀**
- **不添加任何质量词**（masterpiece, best quality 等），后处理会自动添加
- **除了 artist 外不为主动其他 tag 添加权重**
- 正向 tag 不超过 80 个，绝对不超过 100 个

### 5.2 artist-explore（画师探索流程）

定义了画师探索的系统性方法论。核心 workflow：

1. 从无 artist 或指定 artist 开始
2. 从简单到复杂：单画师 → 2 画师无权重 → 2-3 画师带权重 → 多画师带权重
3. 根据用户反馈调整画师组合
4. 最终得到最优画师组合

关键原则：artist 必须从`library/artists.md`中寻找，不能脱离该文件范围。

### 5.3 episode（流程管理）

定义 episode 的文件格式与流程控制：
- 一个 episode 由多个 timestep 组成
- 每个 timestep 包含 exploration JSON 和多个 prompt
- ClaudeCode 生成 timestep 后告诉用户文件路径，用户自己跑图
- 用户反馈后进入下一个 timestep

### 5.4 tag-assistant（标签助手）

当用户需要推荐 danbooru tag 时，使用语义搜索系统：
```bash
uv run tag_semantic_search.py --query "query1" "query2"
```

流程：
1. 系统性分析需求和上一轮搜索结构
2. 进行语义搜索（最多 8 个 query）
3. 必要时进行关键词搜索（在 14 万行的 danbooru.txt 中查找）
4. 提供 tag 建议和灵感推荐

## 6. 画师库：70+名画师的精细化描述

ImageAutoPrompt 的`library/artists.md`收录了超过 70 名画师的详细中文描述，每条描述都精准捕捉了该画师的核心风格特征。这些描述是作者从大量图片中提炼出来的，可以直接用于 prompt 探索的参考。

### 6.1 典型画师风格分类

**通透治愈系**：
- `artist:torino aqua` — 极致逆光、丁达尔空气感、通透、细碎光斑
- `artist:anmi` — 唯美轻盈、逆光丁达尔、水润软糯
- `artist:hiten (hitenkei)` — 商业赛璐璐、冷暖邻近色、水下折射

**肉感厚涂系**：
- `artist:shigure s` — 极致丰腴、肉感曲线、勒痕挤压
- `artist:berserker r` — 极致肉感比例、脂肪挤压、幼态萌系
- `artist:swd3e2` — 极致盆骨大腿围、挤压肉感、韩系半厚涂

**赛博幻想系**：
- `artist:lirseven` — 赛博冷色调、RGB 色散霓虹、锐利边界
- `artist:yuumei` — 赛博幻想、强对比发光特效、靛青暖金碰撞
- `artist:swav` — 硬核机能、冷冽冰蓝钛白、过曝洁净

**幼态萌系**：
- `artist:shiratama (shiratamaco)` — 极致幼态 Loli、马卡龙色、婴儿肥小圆嘴
- `artist:40hara` — 极致幼化建模、短肢软糯、边缘光散景
- `artist:sironora` — 极幼态 Lolicon、剔透干净、巨大宝石眼

### 6.2 画师总结三阶段法

作者还提供了如何总结自己审美中的画师的方法：

**阶段 1**：收集 N 个画师，以自己的审美标准

**阶段 2**：对每个画师，选择喜欢的 5-6 张图，给 Claude/Gemini 分析：
```
1. 帮我详细分析、总结一下这位画师的画风，说明理由
2. 最后，用200字总结画风，不要求自然语言流畅，要求简要、分点答题、信息密度高
```

**阶段 3**：压缩。将所有画师信息一起给 Gemini 压缩：
```
将下列画师信息进行压缩，不谈属性只谈值（例如"人物偏可爱"=>"可爱"），
并保留最核心、最具特色的信息，让人直觉上能快速意会。
输出txt格式，每名画师尽量压缩在100字以内。
```

## 7. 系统设计亮点与工程思想

### 7.1 双 Buffer 打满显卡

作者提出的"双 buffer"技巧非常实用：当前一批图片正在生成时，可以同时把上一批的 prompt 复制给 Claude 让它生成下一批的候选。这样显卡永远有事情做，人和 AI 并行工作。

### 7.2 方差比偏差更重要

作者的核心工程哲学：当观察到用户明显的偏好时，依旧偶尔给出看上去次优的 prompt。只有充分探索，才能不被局限于信息茧房。

- **偏差高** = 不符合用户需求
- **方差高** = tag 不标准导致图像不稳定

通常应当保证方差优先。如果步子迈太大（一下子新增或修改很多 tag），会引入较大方差和不稳定性。稳扎稳打，逐步提升才是硬道理。

### 7.3 RAG 解决 invalid tag 问题

当自然语言 prompt 太多、标准 tag 少的时候，会出现 invalid tags 增多、图像不稳定的问题。ImageAutoPrompt 支持 RAG（检索增强生成）功能：

```bash
# 安装RAG功能：docs/install-rag.md
# 建库需要10-40分钟，有GPU会更快
# 会用embedding建立danbooru tag的语义索引
```

当出现 invalid tag 报错时，系统会推荐语义相关的标准 tag 作为替代。

## 8. 局限性与注意事项

1. **noobai 模型限制**：ImageAutoPrompt 针对 noobai 系列模型设计，对其他模型（如 Stable Diffusion 标准版本）的兼容性未测试
2. **ComfyUI 工作流**：需要用户自行配置适合自己模型的工作流，不能开箱即用
3. **画师库偏向**：从 70+画师的描述来看，库明显偏向二次元萌系/肉感系风格，对写实系画师覆盖较少
4. **RAG 依赖 GPU**：虽然基础功能不需要 GPU，但 RAG 建库需要 GPU 算力
5. **作者明确声明**：chenkin noob v0.5 并非评价最好的 noob，只是视频中演示使用的版本

## 9. 总结

这是一套相当完整的 AI 绘图 prompt 探索系统：
- **Flask Web 界面**提供了友好的交互入口
- **ClaudeCode Agent**让探索过程自动化
- **系统化的画师串探索方法论**从经验中提炼为可执行的 workflow
- **70+画师的精细化描述库**是多年审美积累的结晶
- **Episode/Timestep 的版本管理**让探索过程可追溯、可复现

关键价值在于：把"人工慢慢调参"的串行过程，变成了"AI 批量探索+人工选择"的并行过程。显卡不再空转，审美决策和 prompt 生成同时进行，效率大幅提升。

对于想要深入研究 AI 绘图 prompt 工程、特别是想系统化探索自己审美偏好的人来说，这套系统和视频值得仔细学习。

## 自测：检查你的理解

1. ImageAutoPrompt 的「双 buffer」具体指什么？为什么能让显卡不空转？
2. 画师串探索为什么要从「单画师」开始，而不是直接上「多画师带权重」？
3. `artist:aaa:1.2` 和 `artist:bbb:0.8` 的权重差异会造成什么不同的生成效果？
4. RAG 建库需要 GPU，但基础功能不需要——你现在的硬件能跑哪部分？
5. 负面提示词在探索过程中「固定不变」，这个设计选择有什么好处？

## 进阶路径

**阶段 1：跑通最小流程（1-2 天）**
先把环境搭起来，用一个你熟悉的画师 tag 跑通 Episode 0 → Timestep 0 → 生成 4 张图。重点是确认 ComfyUI 工作流配置正确，不用追求效果。

**阶段 2：复现视频中的画师串探索（3-7 天）**
按文章第 4 节的表格走一遍：单画师 → 2 画师无权重 → 2-3 画师带权重。把每一步你最喜欢的 prompt 记下来，这就是你的「审美基准线」。

**阶段 3：建立自己的画师库（1-2 周）**
文章提到的「画师总结三阶段法」值得单独做一遍。把你喜欢的 5-10 个画师，按阶段 1-3 处理，得到一份属于你自己的 `my-artists.md`。

**阶段 4：接入自己的模型或工作流（持续）**
如果你不用 noobai 而用其他模型，需要改 format-noobai skill 里的格式规则。如果你有更复杂的 ComfyUI 工作流（比如带 ControlNet、IP-Adapter），需要按文章 2.2 节的方法改工作流配置。

---

🦞 视频精读 | 2026-05-08