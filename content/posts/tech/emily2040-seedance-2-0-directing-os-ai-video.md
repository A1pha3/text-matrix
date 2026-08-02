---
title: "Seedance 2.0 Skill OS：把 AI 视频生成当电影片场来调度的智能体工作流"
date: 2026-08-03T03:26:34+08:00
slug: "emily2040-seedance-2-0-directing-os-ai-video"
description: "Emily2040/seedance-2.0 是一个围绕字节跳动 Seedance 2.0 视频生成模型构建的模块化智能体技能仓库。它把模糊创意想法路由到导演级提示词工作流，覆盖文本、图像、视频和参考视频四模态输入，提供六语言母语入口和专业制片流程支持。"
draft: false
categories: ["技术笔记"]
tags: ["AI 视频", "Seedance", "Prompt Engineering", "智能体技能", "ByteDance"]
---

## 核心判断

大多数 AI 视频工具的交互方式是：用户丢一句"cinematic shot of..."，模型返回一段还行的画面。Seedance 2.0 Skill OS（下称 Seedance OS）不接受这种模式。它把视频生成当成一次电影拍摄来调度——先读场景的戏剧功能，锁定一个导演意图，再让镜头、灯光、表演和声音全部服从这个意图。

这不是又一份 prompt 模板库。它是一套面向 AI 智能体的操作系统：定义什么时候该采访用户、什么时候该写提示词、什么时候该查技术参考、什么时候该做 IP 安全改写、什么时候该诊断生成失败。整个仓库 244 个 commit，v6.7.0，MIT 协议，2026-08-01 更新。

## 系统地图

Seedance OS 的核心设计是"六道独立车道"——每条车道负责一个维度，请求在入口处经过门控后路由到对应车道：

| 车道 | 职责 | 关键模块 |
|------|------|----------|
| 研究源 | 标注官方/学术/社区证据的新鲜度 | `research-2026-05-30.md`、`platform-surface-matrix.md` |
| 制片流水线 | 从创意简报到交付质检的完整链路 | `shot-list-continuity`、`delivery-qc` |
| 提示词路由 | 根据用户状态决定走采访、直写还是压缩 | `seedance-interview`、`seedance-prompt`、`seedance-prompt-short` |
| 多模态参考 | 给图片/视频/音频引用分配明确角色 | `reference-workflow`、`first-last-frame-guide` |
| 安全门控 | IP、肖像、品牌、声音安全改写 | `seedance-copyright` |
| 质量评测 | schema 校验、来源新鲜度、行为用例 | `validation/`、`evals/` |

这六条车道在入口处汇合。用户的输入先被判断"当前处于什么状态"，再路由到对应技能。这不是简单的 if-else 分发——每个技能模块本身包含了自己的子流程、参考文档和验证逻辑。

## 导演引擎：从"cinematic"到具体调度

这是整个仓库最核心的技术决策。

### 问题

当你向视频模型要"cinematic"，你得到的是一堆形容词堆砌：金色光线、缓慢推镜、史诗感。这些画面看起来都行，但没有一个在叙事。

### Seedance OS 的解法

导演引擎（directing-engine）在读到场景后做三件事：

1. **读取戏剧功能**：这个场景的转折是什么？视点是谁？张力在哪里？
2. **锁定一个意图**：不是"拍得好看"，而是一个具体的叙事动作
3. **推导视听配置**：镜头、灯光、走位、表演、声音全部服务于那个意图

README 给了一个精确对照：

> Ask for "cinematic": epic cinematic shot of a woman reading a letter, emotional, beautiful lighting
>
> Direct it: A woman at a kitchen table reads the letter twice, then her hands lower it and go still. Camera: medium close-up at eye level, a slow push-in that settles when her hands stop. Soft window light keeps her face plain. Sound: room tone, one chair scrape, near-silence — the realization lands in the stilled hands, not a word.

区别不在文采，在于后者把"她意识到什么"转化成了一个可执行的镜头方案——推镜在她手停下来时停住，声音留白让情绪落在动作上而不是台词上。

### 序列连贯性

单个场景导演到位还不够。对于跨多个生成片段的长故事，引擎会：

- 为整个故事锁定一个导演声音（directorial voice）
- 33 个端到端推导案例覆盖产品、MV、恐怖片、动画、动作、喜剧、纪录片、时尚、科幻等类型
- 每种类型展示了从意图到镜头方案的完整推导链

## 提示词路由：根据用户状态分流

Seedance OS 不假设用户来了就直写 prompt。它先判断用户处于什么状态：

| 用户说的 | 加载的技能 | 产出 |
|----------|-----------|------|
| "我有个模糊想法" | seedance-interview | 聚焦的创意简报 + 下一步路径 |
| "这是一个三段连贯故事" | seedance-sequence | 故事脊柱、连续性圣经、片段合同 |
| "继续这个视频" | seedance-continuation | 基于已接受画面的续写 |
| "我知道我要什么场景" | seedance-prompt | 可直接使用的生产级提示词 |
| "让它短而有力" | seedance-prompt-short | 压缩到 30-100 词的提示词 |
| "生成结果 80% 对，重做还是保留？" | retake-protocol | 五级判定 + 单变量重试预算 |

这个路由表意味着：同一个用户在不同阶段会被路由到不同技能，而不是一直在同一个"写 prompt"界面里。

## 多生成片段的状态管理

长视频需要多次生成拼接。Seedance OS 对此有一个严格的状态模型：

> The project state is the source of truth. The clip contract is the current production task. The prompt is a compiled instruction for only that task.

工作流如下：

1. 描述完整创意和结局
2. 引擎拆分为连续片段
3. 生成片段 01
4. 返回生成结果或末帧
5. 引擎记录"实际发生了什么"（而非"预期发生什么"）
6. 基于真实结尾写片段 02
7. 重复直到完成

关键设计：续写基于已接受的生成画面，而非原始 prompt 的预期。因为模型不一定在预期位置结束——盲目续写原始 prompt 会导致接缝断裂。

## 平台事实的源日期管理

AI 视频平台的 API、定价、区域限制和模型 ID 变化很快。Seedance OS 用一套源日期管理机制来避免信息过期：

- `api-status.md`：所有平台事实标注 `last_verified` 日期
- `platform-surface-matrix.md`：按 Dreamina/Jimeng、Volcengine/Ark、BytePlus、Runway、fal 等分别记录
- `model-name-map.md`：区分 Seedance 2.0、Seedance 2.0 Fast、Seedance 2.0 Mini、Seedance V2 等命名

README 明确指出：2026-07-31 消费端上线了 Seedance 2.5，但本仓库只覆盖 2.0——平台数字是 2.0 的。这种主动声明边界而非含糊覆盖的做法，在 AI 视频工具仓库里相当少见。

## 六语言母语入口

v6 引入了六语言入口路径，不是简单翻译，而是为每种语言写了独立的提示词指南：

| 语言 | 入口 | 特色指导 |
|------|------|----------|
| 中文 | 中文指南 + seedance-vocab-zh | 角色锁定、首尾帧、运镜、动作节奏 |
| 日本語 | 日本語ガイド + seedance-vocab-ja | 人物同一性、衣装、构图、動きの終点 |
| 한국어 | 한국어 가이드 + seedance-vocab-ko | 인물 고정、카메라、조명、사운드 분리 |
| English | seedance-prompt + references/vocab/en.md | One visible beat, one camera move, real light |
| Español | multilingual-community-examples | 混合语言安全结构 |
| Русский | multilingual-community-examples | 混合语言安全结构 |

每种语言的指南都强调了同一个原则：保留参考标签原样（`@Image1`、`@图片1`），不把字幕交给模型生成。

## 专业制片流程支持

仓库覆盖了实际制片团队需要的产物，而不仅是 prompt：

| 角色 | 技能应产出 |
|------|-----------|
| 导演 | treatment、场景节拍、表演意图、覆盖方案 |
| 摄影指导 | 镜头合同、景别、镜头感、灯光连续性 |
| 制片/代理商 | 客户简报、权限地图、审批节点、风险日志 |
| 剪辑师 | 选素材方案、编辑/延展决策、连续性交接 |
| 调色师 | ACES 感知交接、HDR/SDR 注意事项 |
| 声音团队 | 对白图、环境/音效/音乐层、同步提示 |
| 本地化团队 | 字幕、SDH 字幕、配音指南、无文本版 |

这意味着 Seedance OS 不止于生成视频片段，还能辅助从创意到交付的完整制片流程。

## IP 安全改写

当用户的请求涉及名人、受保护 IP、品牌、歌曲或声音时，`seedance-copyright` 技能会做"功能等价的安全改写"——保留创意意图，替换不安全元素。同时处理平台安全过滤器的误判（false-positive repair），通过澄清良性的制作语境而非隐藏不安全意图。

## 仓库结构

```
seedance-2.0/
├── agents/          # 智能体配置
├── skills/          # 核心技能模块
├── data/            # 平台事实数据
├── docs/            # 文档
├── evals/           # 评测用例
├── examples/        # 示例
├── references/      # 参考资料（含多语言词汇表）
├── schemas/         # 校验 schema
├── scripts/         # 脚本
├── tests/           # 测试
└── validation/      # 质量校验
```

仓库自带 `SKILL.md`，兼容 Codex/Agent Skills 分发标准，可以作为智能体技能直接安装。

## 采用建议

**适合**：使用 Seedance 2.0（或兼容平台）做视频生成的智能体开发者、AI 视频创作者、对 prompt 工程感兴趣的技术团队。

**不适合**：需要实时视频生成的场景（这是一套离线创作工具）、非 Seedance 系列模型的用户（平台事实与模型行为均以 2.0 为基准）。

**注意**：仓库的 `api-status.md` 有 `last_verified` 日期，使用前请确认平台事实未过期。2026-07-31 后消费端已出现 Seedance 2.5，本仓库暂不覆盖。
