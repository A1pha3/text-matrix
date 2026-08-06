---
title: "Skill Prompt Generator：把 Prompt 工程变成 Skills 架构问题"
date: 2026-05-10
categories: ["技术文章"]
tags: ["Skills 系统", "Claude Code", "Prompt Engineering", "AI Agent", "Codex CLI"]
description: "一个 1445 Star 的开源项目，用 12 个专业 Skill 和 1246 个可复用元素构建 AI 图像提示词生成系统。本文从源码层面拆解其双层架构、跨 Domain 查询引擎和设计变量体系。"
slug: index
---

# Skill Prompt Generator：把 Prompt 工程变成 Skills 架构问题

大多数 AI 图像提示词工具做的是"接收描述，输出 Prompt"——本质上是一个模板拼接器。[Skill Prompt Generator](https://github.com/huangserva/skill-prompt-generator) 走了另一条路：它把提示词生成拆解成 12 个专业领域 Skill，配上一套 1246 个可复用元素的 SQLite 数据库，再通过框架驱动的智能引擎做语义推理和一致性校验。

这篇文章拆解它的架构设计、核心引擎实现，以及 v2.0 引入的跨 Domain 查询如何把数据库利用率从 40.3% 拉到 79.9%。

## 仓库信息卡

| 属性 | 值 |
|------|-----|
| 仓库 | [huangserva/skill-prompt-generator](https://github.com/huangserva/skill-prompt-generator) |
| Stars / Forks | 1,445 / 213 |
| 主语言 | Python |
| 首次提交 | 2026-01-05 |
| 最近 push | 2026-05-10 |
| 仓库大小 | 1,315 KB |
| 许可证 | MIT |
| 核心贡献者 | @Felictycf（Codex CLI 适配） |

## 项目定位：Skills 系统，不是 Python 工具

README 开头有一句容易滑过去的话："这不是一个普通的 Python 工具，而是一个完整的 Skills 系统"。这句话的含义需要拆开来看。

Claude Code 的 Skills 机制允许你定义一组 `.claude/skills/` 目录下的 Markdown 文件，每个文件描述一个专业领域的操作规程。当用户在 Claude Code CLI 中输入请求时，Claude Code 会根据请求内容路由到对应的 Skill，由 Skill 指导 LLM 完成任务。Skill 本身不是代码——它是一份给 AI Agent 的结构化指令。

Skill Prompt Generator 在这层之上做的事情是：定义了 12 个专业领域 Skill，每个 Skill 指向同一个元素数据库和同一套 Python 引擎。用户不需要知道哪个 Skill 被调用了，只需要用自然语言描述需求，系统自动路由。

### 12 个 Skills 的职责划分

| Skill | 职责 |
|-------|------|
| `intelligent-prompt-generator` | 人像提示词生成（主力 Skill） |
| `art-master` | 艺术风格（水墨、油画、插画等） |
| `design-master` | 平面设计（海报、PPT、UI） |
| `product-master` | 产品摄影 |
| `video-master` | 视频生成提示词 |
| `prompt-analyzer` | 提示词结构分析 |
| `prompt-extractor` | 从现有提示词中提取可复用元素 |
| `prompt-generator` | 通用生成器 |
| `prompt-master` | 主控调度，负责路由 |
| `prompt-xray` | X-Ray 分析（透视 Prompt 结构） |
| `domain-classifier` | 领域自动分类 |
| `universal-learner` | 学习系统，从新 Prompt 中积累元素 |

这 12 个 Skill 并非平行关系。`prompt-master` 承担主控调度角色，`domain-classifier` 负责识别用户需求属于哪个领域，其余 Skill 各自处理一个专业方向。`universal-learner` 和 `prompt-extractor` 构成系统的自我学习闭环——能从社区提示词中提取新元素并写入数据库。

### 双平台支持：Claude Code + Codex CLI

v2.0 之后，项目同时支持 Claude Code 和 OpenAI Codex CLI 两个 Agent 平台。实现方式是在项目根目录维护两套 Skill 定义：

```
.claude/skills/     # Claude Code 版本（12 个 Skill）
.codex/skills/      # Codex CLI 版本（12 个 Skill，由 @Felictycf 贡献）
```

两套 Skill 共享同一套 Python 引擎和数据层。Codex 版本额外包含一些平台适配文件，比如 `prompt-xray/xray_helper.py` 和 `prompt-extractor/preprocessor.py`，用于处理 Codex CLI 的输入输出差异。

## 架构总览：四层体系

从源码结构出发，整个系统可以分成四层：

```
┌───────────────────────────────────────────────┐
│  用户层                                        │
│  Claude Code CLI / OpenAI Codex CLI           │
└───────────────────┬───────────────────────────┘
                    │ 自然语言输入
┌───────────────────▼───────────────────────────┐
│  Skills 层                                     │
│  12 个专业 Skill（.claude/ + .codex/）        │
│  prompt-master 负责路由                       │
└───────────────────┬───────────────────────────┘
                    │ 结构化意图
┌───────────────────▼───────────────────────────┐
│  引擎层                                        │
│  ┌─────────────────┐  ┌────────────────────┐  │
│  │ v1.0 引擎       │  │ v2.0 引擎          │  │
│  │ IntelligentGen  │  │ CrossDomainGen     │  │
│  │ FrameworkLoader │  │ VariableSampler    │  │
│  │ ElementDB       │  │ DesignBridge       │  │
│  └─────────────────┘  └────────────────────┘  │
└───────────────────┬───────────────────────────┘
                    │ SQL 查询 / YAML 加载
┌───────────────────▼───────────────────────────┐
│  数据层                                        │
│  elements.db（1246 元素 + 675 条语料）        │
│  prompt_framework.yaml（7 大类模板）           │
│  variables/*.yaml（37 配色 + 边框 + 装饰）     │
└───────────────────────────────────────────────┘
```

v1.0 引擎和 v2.0 引擎共享数据层，但处理逻辑不同。v1.0 只走 portrait domain（502 个元素），v2.0 的 `CrossDomainGenerator` 能自动识别类型并路由到不同的生成策略。

## 数据层：元素数据库 + 框架模板 + 设计变量

### Universal Elements Library

核心数据存储在 `extracted_results/elements.db` 这个 SQLite 文件中。根据 README 统计和 `element_db.py` 的表结构，数据库包含：

| 表 | 作用 |
|----|------|
| `domains` | 领域定义（portrait, design, art 等 12 个） |
| `categories` | 每个领域下的元素类别 |
| `elements` | 核心表，每行一个可复用元素 |
| `tags` | 标签表 |
| `element_tags` | 元素-标签多对多关联 |
| `source_prompts` | 社区语料库（675 条原始 Prompt） |

`elements` 表的结构值得展开看：

```python
# 来自 element_db.py 的表定义
element_id          TEXT PRIMARY KEY    # 如 "portrait_expressions_010"
domain_id           TEXT                # 如 "portrait"
category_id         TEXT                # 如 "expressions"
name                TEXT                # 如 "serene_smile"
chinese_name        TEXT                # 如 "宁静微笑"
ai_prompt_template  TEXT                # 实际拼入 Prompt 的文本片段
keywords            TEXT (JSON)         # 如 ["serene", "gentle", "peaceful"]
reusability_score   REAL (0-10)         # 复用性评分，查询排序依据
source_prompts      TEXT (JSON)         # 溯源到哪些社区 Prompt
learned_from        TEXT                # 'manual' 或 'auto_learner'
```

每个元素都带 `reusability_score`，查询时按分数降序排列。`learned_from` 字段区分人工录入和自动学习两种来源，这给系统的自我扩展提供了追溯能力。

12 个领域的元素分布并不均匀，portrait 占了 40%（502 个），common 通用技术类占 17%（208 个），design 占 13%（166 个），其余 9 个领域分享剩下的 30%。这个分布在 v1.0 时代意味着非 portrait 领域的元素大量闲置。

### prompt_framework.yaml：7 大类模板

框架文件定义了人像 Prompt 的完整结构，分为 7 大类：

1. **Subject**（主体）— gender, ethnicity, age_range
2. **Facial**（面部）— eyes, skin_tone, skin_texture, face_shape, nose, lips
3. **Styling**（造型）— clothing, hairstyle, hair_color, makeup, accessories
4. **Expression**（表现）— facial_expression, pose
5. **Lighting**（光影）— lighting_type（必选）
6. **Scene**（场景）— era, background, atmosphere, director_style
7. **Technical**（技术）— art_style, camera, bokeh, quality

除了字段定义，框架还包含两组规则：

**依赖规则**（dependencies）处理字段间的自动推导。例如当 `scene.era = "ancient"` 时，自动设置 `styling.clothing = "traditional_chinese"`、`styling.hairstyle = "ancient_chinese"`、`styling.makeup = "traditional_chinese"`。当 `subject.ethnicity = "East_Asian"` 且 `facial.eyes = "auto"` 时，自动推导为 `almond`。

**验证规则**（validation）做逻辑一致性检查。例如古装场景搭配 K-Beauty 妆容会报 error 级别冲突，东亚人物搭配绿色/蓝色眼睛会报 warning。

### 设计变量库（v2.0 新增）

v2.0 在 SQLite 之外引入了一组 YAML 变量文件，用于设计类生成：

- `variables/colors.yaml` — 37 种配色方案（如"珊瑚粉色系"，主色 `#FF9AA2`）
- `variables/borders.yaml` — 边框样式（如"大圆角 20px"）
- `variables/decorations.yaml` — 装饰元素（如"星星"）

README 中提到这些变量组合可达 20 万种以上。这个数字的逻辑是：37 种配色 × 多种边框 × 多种装饰 × SQLite 设计元素，组合空间远超单维度排列。

## v1.0 引擎：框架驱动的智能生成

`intelligent_generator.py` 是 v1.0 的核心，43KB 代码实现了三层智能能力。

### 第一层：语义理解 + 元素选择

`select_elements_by_intent()` 方法接收解析后的意图字典，按字段从数据库选择元素。处理流程：

1. 先选人物属性（gender → age_range → ethnicity）
2. 根据人种自动选择匹配的眼型和发色（调用内置知识库）
3. 选择服装和发型（支持关键词映射和模糊搜索）
4. 选择其他面部属性（skin_tones, makeup_styles 等）
5. 收集风格关键词，从全库搜索匹配的风格元素

这里的"语义理解"体现在风格关键词的收集策略上。系统会从多个维度收集关键词——用户指定的 art_style、atmosphere theme、lighting type、era、director_style——然后用这些关键词在全库中搜索匹配的元素。搜索时排除了 `subject_attribute_categories`（gender, ethnicity 等人物属性类别），避免风格关键词误覆盖人物属性。

### 第二层：常识推理

`load_knowledge()` 方法内置了一个常识知识库，包含：

```python
# 人种 → 典型眼睛颜色
'ethnicity_typical_eyes': {
    'East_Asian': ['black', 'dark brown', 'brown'],
    'European': ['blue', 'green', 'brown', 'hazel', 'grey'],
    ...
}

# 人种 → 典型发色
'ethnicity_typical_hair': {
    'East_Asian': ['black', 'dark brown'],
    ...
}

# 导演风格 → 光影关键词
'director_lighting_styles': {
    'zhang_yimou': {
        'lighting_keywords': ['dramatic', 'shadow', 'rim', 'contrast',
                              'chiaroscuro', 'volumetric'],
        'required_elements': ['dramatic shadows', 'rim lighting'],
    },
    ...
}
```

当用户说"张艺谋电影风格"时，系统不只是搜索"张艺谋"这个关键词，而是自动扩展为 `['dramatic', 'shadow', 'rim', 'contrast', 'chiaroscuro', 'volumetric', 'traditional', 'red', 'gold', 'period drama']` 这些可被数据库检索的具体描述词。

### 第三层：一致性检查

`check_consistency()` 方法在元素选择完成后做逻辑校验。源码中实现的检查规则包括：

- **人种 vs 眼睛颜色**：东亚人物出现 green/blue/violet 眼睛 → severity: medium，建议修正为 almond 或 dark brown
- **人种 vs 发色**：类似规则，检测不合理的发色搭配

检查结果返回问题列表，每个问题包含 type、severity、description 和 suggestion。生成引擎可以据此自动修正，或在输出中给用户提示。

### 相关性评分

`search_style_elements()` 对搜索结果做相关性排序。计算方式：

```python
relevance = matched_keywords / total_keywords
final_score = relevance * reusability_score
```

即关键词命中率乘以元素自身的复用性评分。这个设计确保高频优质元素在相同匹配度下排名更高。

## v2.0 引擎：跨 Domain 查询 + 设计系统

v1.0 的局限很明显：只用 portrait domain 的 502 个元素，其余 744 个元素（59.7%）处于闲置状态。v2.0 通过三个新模块解决这个问题。

### CrossDomainGenerator：统一入口

`core/cross_domain_generator.py` 是 v2.0 的推荐入口。它的工作流程：

1. 接收用户自然语言输入
2. 自动识别生成类型（portrait / cross_domain / design）
3. 路由到对应的生成器
4. 返回统一格式的结果（prompt + type + metadata）

三种类型的判定逻辑基于输入文本的领域特征。纯人像描述走 portrait 模式，涉及多领域元素的复杂场景走 cross_domain 模式，设计海报类需求走 design 模式。

### CrossDomainQueryEngine：跨域组合

这是 v2.0 的核心创新。以 README 中的例子来说明——用户输入"龙珠悟空打出龟派气功"：

| 需求维度 | 查询的 Domain | 提供的元素 |
|---------|--------------|-----------|
| 人物基础 | portrait | Goku 的人物特征 |
| 动作姿势 | video | 龟派气功动作描述 |
| 视觉风格 | art | 3D/动漫渲染风格 |
| 光影效果 | common | 能量光效、动态光影 |

引擎自动识别这四个 domain 并组合元素，输出的 Prompt 包含人物、动作、特效、光影的完整描述。数据库利用率从 40.3%（502/1246）提升到 79.9%（995/1246），接近翻倍。

这个数字的提升路径很直接：v1.0 只查 portrait domain，v2.0 根据需求自动查询多个 domain 并组合。995 这个数字是所有非 exclusive 领域元素的总和。

### DesignVariableBridge：SQLite + YAML 融合

设计模式用了不同的数据策略。SQLite 提供基础元素（布局、技术参数），YAML 提供设计变量（配色、边框、装饰）。`DesignVariableBridge` 负责把两个数据源融合成完整的设计规范。

从 `README_v2.0.md` 的示例来看，设计模式的输出不是一段 Prompt 文本，而是一份结构化的设计规范：

```
Color scheme: 珊瑚粉色系
Primary color: 蜜桃粉 (#FF9AA2)
Decorative elements: 星星
Border style: 大圆角 20px
Lighting: soft natural window light
```

这种输出格式更适合设计类任务——用户需要的不是一段连续的 Prompt，而是可以直接应用到设计工具中的参数集合。

### 变量采样系统

`variable_sampler.py` 和 `yaml_sampler.py` 解决的是重复性问题。当系统需要从 37 种配色方案中选择时，采样器会考虑上下文（已经选过哪些变量），避免在同一批生成中重复选择相同的配色。源码中称之为"上下文感知采样"。

## 一个完整任务如何流过系统

用 README 中的第一个示例追踪一次完整调用：

**用户输入**：`生成电影级的亚洲女性，张艺谋电影风格`

**Step 1 — Skill 路由**：`prompt-master` 收到请求，`domain-classifier` 识别为人像摄影领域，路由到 `intelligent-prompt-generator` Skill。

**Step 2 — 意图解析**：Skill 指导 Claude Code 将自然语言解析为结构化意图：
```python
{
    'subject': {'gender': 'female', 'ethnicity': 'East_Asian', 'age_range': 'young_adult'},
    'styling': {'makeup': 'natural'},
    'lighting': {'lighting_type': 'cinematic'},
    'atmosphere': {'director_style': 'zhang_yimou'}
}
```

**Step 3 — 框架加载**：`framework_loader.py` 加载 `prompt_framework.yaml`，应用依赖规则。`scene.era` 未指定，默认 `modern`，不触发古装推导规则。`ethnicity = East_Asian` + `hair_color = auto` → 自动推导 `hair_color = black`。

**Step 4 — 元素选择**：`intelligent_generator.py` 的 `select_elements_by_intent()` 按字段查询数据库：
- portrait/gender → female 元素
- portrait/age_range → young_adult 元素
- portrait/ethnicity → East_Asian 元素
- portrait/eye_types → almond（东亚自动推导）
- portrait/hair_colors → black（东亚自动推导）
- portrait/clothing_styles → 现代服装（默认）
- portrait/makeup_styles → natural makeup
- common/lighting_techniques → cinematic lighting

**Step 5 — 风格扩展**：识别到 `director_style = zhang_yimou`，从知识库扩展关键词为 `['dramatic', 'shadow', 'rim', 'contrast', 'chiaroscuro', 'volumetric', 'traditional', 'red', 'gold', 'period drama']`，在全库中搜索匹配的风格元素。

**Step 6 — 一致性检查**：`check_consistency()` 检查元素组合的合理性。东亚人 + almond eyes + black hair → 通过。

**Step 7 — Prompt 组装**：将所有元素的 `ai_prompt_template` 拼接为最终输出：

```
Cinematic portrait of young East Asian woman, dramatic lighting with rim light
and chiaroscuro effect, Zhang Yimou's signature color palette with rich reds
and golds, 85mm lens, shallow depth of field, film grain texture...
```

## 社区语料库与学习闭环

数据库中除了 1246 个元素，还有 675 条 `source_prompts`——来自 260 多位社区创作者的原始提示词。按类别分布：

| 类别 | 数量 |
|------|------|
| 海报设计 | 163 |
| 人像摄影 | 112 |
| UI 设计 | 82 |
| 综合创意 | 65 |
| 产品摄影 | 7 |
| 其他 | 246 |

状态分为 `completed`（246 条已学习）和 `pending` + `metadata_only`（429 条待处理）。`universal-learner` Skill 负责处理 pending 状态的条目：调用 `prompt-extractor` 从原始 Prompt 中提取可复用元素，经 `domain-classifier` 分类后写入 `elements` 表，`learned_from` 字段标记为 `auto_learner`。

这构成了一个数据飞轮：用户使用系统生成 Prompt → 优质 Prompt 被收录进语料库 → learner 提取新元素 → 数据库扩充 → 生成质量提升。

## v1.0 到 v2.0 的数据对比

| 指标 | v1.0 | v2.0 | 变化 |
|------|------|------|------|
| 数据库利用率 | 40.3%（502/1246） | 79.9%（995/1246） | +98.2% |
| 生成模式 | 1 种（Portrait） | 3 种（Portrait / Cross-Domain / Design） | +200% |
| 可用组合 | ~1,000 | ~200,000+ | ~200x |
| 支持 Domain | 1（portrait） | 14（含跨 domain 和设计变量） | 14x |
| Agent 平台 | Claude Code | Claude Code + Codex CLI | +1 |

利用率提升的来源是跨 Domain 查询引擎——它把 portrait 之外闲置的 493 个元素（common 208 + design 166 + art 70 + video 49）纳入了可查询范围。

## 工程实现中的几个设计判断

### 为什么用 SQLite 而不是 JSON 文件

1246 个元素如果用 JSON 存储，全文搜索和条件查询需要加载到内存。SQLite 的优势在于：SQL 查询天然支持 `WHERE domain_id = ? AND category_id = ?` 这种条件组合，`ORDER BY reusability_score DESC LIMIT 1` 直接在数据库层完成排序，Python 层只接收最终结果。`element_db.py` 的表结构设计也支持溯源（`source_prompts` 字段记录元素来源）和自动学习（`learned_from` 字段区分手动/自动）。

### 为什么框架用 YAML 而不是 Python 代码

`prompt_framework.yaml` 定义的是领域规则而不是执行逻辑。依赖规则和验证规则用声明式 YAML 表达有两个好处：非程序员（比如 Prompt 工程师）可以直接编辑规则而不需要改 Python 代码；规则变更不需要重新部署引擎。`framework_loader.py` 的 `apply_dependencies()` 方法就是通用地遍历 YAML 中的 dependencies 列表，不需要为每条规则写专门的代码。

### 双轨制：元素级 vs 模板级

系统同时支持从单个元素组合生成（元素级）和从完整设计系统模板生成（模板级）。模板级生成用于有完整设计体系的场景，比如 README 中提到的"Apple 淡蓝商务 PPT 模板"——这类需求不适合从零拼元素，直接调用预定义的 12 元素完整系统更合理。

## 采用建议

**适合直接使用的场景**：

- 需要批量生成结构化人像摄影 Prompt 的团队，尤其是涉及多 ethnicity 和风格组合的场景
- 同时使用 Claude Code 和 Codex CLI 的开发者，一套 Skill 定义双平台复用
- 需要可扩展 Prompt 知识库的项目——学习闭环能持续积累领域元素

**需要评估的场景**：

- 如果你只需要偶尔生成几条 Prompt，直接用 ChatGPT/Claude 对话更轻量
- 如果你的需求完全在设计领域（非摄影），v2.0 的设计系统虽然能用，但 YAML 变量库的覆盖面取决于你手动维护的配色/边框/装饰文件
- 如果你需要实时生成（API 调用），这套系统目前是 Skill 驱动的，需要 Claude Code 或 Codex CLI 作为运行环境

### 一致性检查的覆盖范围

`check_consistency()` 目前的规则集中在人种特征维度——眼睛颜色、发色与人种的匹配。这是一个保守但稳妥的设计：只检查高置信度的生物学常识冲突，不做主观审美判断。源码中 severity 分为 `medium` 和 `low` 两档，没有 `high`——系统倾向于给出建议而非阻断生成。

如果要把一致性检查扩展到其他维度（比如服装与场景时代的匹配、光影与氛围的协调），`prompt_framework.yaml` 的 `validation.consistency_checks` 已经提供了声明式框架。添加一条新规则只需要指定 `when` 条件和 `suggestion`，不需要修改 Python 代码。这是声明式架构的回报。

### 模糊搜索与精确匹配的平衡

`get_element_by_category()` 方法有一个值得注意的实现细节：它先用 `LIKE` 做模糊搜索，但如果模糊匹配的 `name` 字段和 `value_filter` 不完全一致，会回退到精确匹配查询。源码注释提到了一个具体问题：搜索 `female` 时 `LIKE %female%` 可能匹配到 `male`（因为 `female` 包含 `male` 子串）。

这种防御性查询设计在元素数据库中很有必要。1246 个元素的 `name` 字段长度不一、命名风格不统一，纯模糊搜索会产生足够的误匹配来影响生成质量。

### 评分公式的局限

`final_score = relevance × reusability_score` 这个公式有一个隐含假设：relevance 和 reusability 是正交的、可线性加权的关系。实际中可能存在一种情况：某个元素相关性很高但复用性很低（针对特定场景的专用元素），而另一个元素相关性中等但复用性很高（通用元素）。当前公式倾向于后者，这对通用场景合理，但对特殊需求可能不是最优排序。

如果后续版本想改进，可以考虑加入用户反馈信号——比如记录哪些元素被用户采纳、哪些被修改或拒绝，作为第三维评分。

## 五个 Takeaway

1. **Skills 架构改变了 Prompt 工程的组织方式**。这个项目展示了一种思路：把 Prompt 生成的领域知识从单个人的经验变成可维护的系统资产。12 个 Skill 各管一个专业方向，共享一套数据层和引擎层。新增领域只需要加一个 Skill 定义和一个 domain 配置，不需要改其他 Skill 的代码。

2. **跨 Domain 查询是数据库利用率的关键跳跃**。v1.0 只用 portrait 的 502 个元素，不是因为其他元素没用，而是因为没有跨域组合的机制。`CrossDomainQueryEngine` 解决的是元素发现问题——让 79.9% 的数据库不再闲置。这个思路适用于任何基于元素库的生成系统。

3. **声明式框架让规则可维护**。`prompt_framework.yaml` 把依赖规则和验证规则从 Python 代码中抽出来，变成 YAML 配置。添加“赛博朋克场景不用暖色调”这类新规则只需要几行 YAML，不需要重新部署引擎。代价是调试时需要跨 YAML 和 Python 两层看问题。

4. **双平台适配的成本可控**。`.claude/skills/` 和 `.codex/skills/` 两套定义共享同一个 Python 引擎和 SQLite 数据库，平台差异被隔离在 Skill 定义层。@Felictycf 的 Codex 适配工作证明这种架构对第二个 Agent 平台的接入成本是可接受的。

5. **学习闭环是数据飞轮的基础**。675 条社区语料库中只有 246 条已完成学习，429 条待处理。`universal-learner` + `prompt-extractor` 的自动元素提取能力决定了这个飞轮能转多快。目前的提取速度（246/675 = 36.5%）说明系统还有大量未利用的社区知识。