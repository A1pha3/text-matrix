---
triggers: [教程, 参考文档, README, API 文档, 上手指南]
reader: 带任务来的工程师：要照着做、照着查
band: doc-default
gates: [事实性, 去AI味]
deliverables: [完整可运行示例, 前置条件与验证步骤, 学习目标（标准/完整模式）]
---

# doc 文体包：技术文档

> 教程、参考文档、README、API 文档、上手指南。frontmatter 参数受回归测试守护，手艺见正文。

## 读者契约

读者带着任务来：装起来、跑起来、查参数、排错。文章成功的标准是读者合上文档就能动手，动手卡住时能在 30 秒内找到对应段落。

## 写作要点

- 结构服务检索与操作：先结论后展开，标题即任务。
- 核心概念先答"为什么需要它"，再给怎么做。
- 示例完整可运行；前置条件与验证步骤成对出现。
- 模板按 commands.md 的级别从 `references/templates.md` 选择；学习元素用 `references/learning-paths.md`。

## 档位细分（在 commands.md 文体判断中选定）

| 细分类型 | 档 ID |
|----------|-------|
| 教程 / 入门 | tutorial |
| 参考 / API 文档 | reference |
| README / 快速上手 | readme |
| 未分类 | doc-default |
