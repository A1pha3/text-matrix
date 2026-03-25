# 更新日志

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| v5.0.1 | 2026-03-01 | skill-optimize | **精简优化**。YAML description 去冗余修饰词（-58%）；删除 Quick Start 失败恢复示例（已覆盖于 edge-cases.md）；核心原则 4 条列表压缩为 1 行（术语统一已由 §4 自检 #3 保障）；§3 删除与 §7 重复的"按需加载"列；§5 产物骨架移至 commands.md 按需加载（-70 行）；§6 删除与 §4 红线重复的禁止项；§7 合并低频条目。字符数 6400→4898（↓23.5%），语义保真率 100%。 |
| v4.1.0 | 2026-03-01 | Sisyphus | **Skill-Optimize 增强迭代（3 轮）**。新增 Quick Start 示例（3 正例 + 反例，覆盖 write/translate/optimize）；新增独立 §7 规则章节（适用边界 + 必须/禁止双向清单 + 异常输入处理表）；§2 场景路由增强为多维度按序判断规则；§4 命令入口表新增输入/输出列；§6 新增 2 个产物骨架模板（write-cn-doc + optimize-cn-doc）；精简 §7 规则与 §5 自检重叠条目。加权评分 33→39.5/40。 |
| v3.8.0 | 2026-03-01 | Sisyphus | **架构重构：懒加载优化**。将 SKILL.md 从 ~15K tokens 的单体文件拆分为瘦核心（~3.5K tokens）+ 5 个按需加载模块。新增 `references/commands.md`（命令流程）、`references/quality.md`（评估标准）、`references/examples.md`（示例与语气）、`references/edge-cases.md`（边界与恢复）、`references/knowledge.md`（知识与框架）。典型调用 token 消耗降低 60-76%，功能零损失。 |
| v3.7.0 | 2026-07-27 | Sisyphus | **Phase 1 代码修复**：`post_translate._check_format` 新增行内代码/LaTeX 跳过（消除误报）；`_check_preservation` 重写为 `_extract_code_blocks` + `_parse_fence`（修复变长围栏）；补充 11 个 CLI `main()` 测试；修复 CI shell 注入漏洞。**Phase 2 Skill 设计**：§1.0 新增语气框架表（5 类受众）；§1.9 新增发布门槛与强制评分规则；§2.0.1 新增增量模式行为约束（4 条）；新增 §3.6 文档治理指南（生命周期/跨文档一致性/废弃流程/代码同步）。**Phase 3 知识层**：术语表扩展至 216 条（+5 新分类：云计算/设计模式/可观测性/网络/移动）；`translation_dict` 集成到 `post_translate`；模板库新增 4 类（Changelog/迁移指南/故障排除/ADR）；§1.10 反馈闭环机制。测试 105→126 |
| v3.6.0 | 2026-03-01 | Sisyphus | 新增上下文管理策略（分片/合并/校验）；新增文档增量更新模式（diff-based 输出）；新增多模型适配提示（窗口策略表）；可读性量化指标；`check_readability()` 方法 + `--readability` CLI 参数；CI/CD 集成模板 `ci/check-docs.yml`（GitHub Actions PR 自动检查） |
| v3.5.0 | 2026-03-01 | Sisyphus | 添加 AI 角色定义和行为约束；添加输出前自检循环；添加智能任务识别；添加跨文档一致性检查策略；`post_translate` 改用 `should_skip`；`pre_translate` 改用 `_parse_fence` 支持变长围栏；补充极端场景测试；测试 70→85+ |
| v3.4.0 | 2026-03-01 | Sisyphus | CommonMark 波浪号围栏完整支持；修复 `is_in_latex` bug；消除死代码；新增 documentation 领域术语表；测试 58→70 |
| v3.1.0 | 2026-02-28 | Sisyphus | 提取共享 utils.py；添加 gen_terminology_md.py；tools.md Mermaid 化；添加 README.md；测试 28→40 |
| v3.0.0 | 2026-02-28 | Sisyphus | 重大重构：执行指令和场景路由、量化评估标准、术语表 JSON 单源、重构翻译脚本、模板 Mermaid 支持 |
| v2.3.0 | 2026-02-27 | Sisyphus | 精简主文档、删除冗余文件、消除内容重复 |
| v2.2.0 | 2026-02-27 | Sisyphus | 修复 YAML frontmatter 格式、统一标签、修复链接 |
| v2.1.0 | 2026-02-05 | Sisyphus | 完善渐进式学习体系：三条学习路径、四级文档模板 |
| v2.0.0 | 2026-02-05 | Sisyphus | 增加学习目标设计、认知负荷管理、刻意练习、专家心智模型 |
| v1.0.0 | 2023-06-01 | Sisyphus | 初始版本 |

## 推荐学习资源

- [Google 开发者文档风格指南](https://developers.google.com/style)
- [Write the Docs 指南](https://writethedocs.org/guide)
- [Bloom 分类学](https://en.wikipedia.org/wiki/Bloom%27s_taxonomy)
- [认知负荷理论](https://en.wikipedia.org/wiki/Cognitive_load)
