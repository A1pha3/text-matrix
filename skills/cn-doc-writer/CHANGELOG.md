# 更新日志

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| v5.9.0 | 2026-05-25 | Codex | **主副本同步防漂移**。明确 `prompt_alpha` 中的 `agent/skills/my-skills/cn-doc-writer` 是主版本，`text-matrix/skills/cn-doc-writer` 只作为副本；新增 `scripts/check_skill_sync.py`，同步后可检查缺失、多余和内容不同的文件，并忽略本地缓存；README、SKILL 和 dogfooding 测试同步加入主从方向约束，防止后续优化在两个仓库间漂移。 |
| v5.8.0 | 2026-05-24 | Codex | **触发、外显与压测优化**。`SKILL.md` 的 description 改为中英混合触发描述，保留 `Use when...` 格式并补充“中文技术文档 / 技术翻译 / 去 AI 味 / 开源项目解读 / benchmark 解读”等中文检索词；新增“默认外显契约”，明确四个命令默认输出什么，减少过程话术泄漏；新增自动去 AI 味契约，要求 `write-cn-doc` 与 `optimize-cn-doc` 默认自动调用去 AI 味回路；将 `optimize-cn-doc` 报告拆成默认简版报告与发布级完整评审，普通优化不再默认展开完整五维评分表；将去 AI 味完整信号库与替换例下沉到 `references/examples.md`，主文件只保留三层回路、加载触发和红线；新增 `references/behavior-fixtures.md`，覆盖代码块保留、benchmark 作用范围、事实不足收缩、去 AI 味稳分和隐式自动去味五个行为压测场景；`skill.json` 新增 `terminology_version`，拆开 Skill 版本与术语表版本；补齐 reference 清单、引用存在性与 `commands.md` 外显契约回归测试。 |
| v5.7.0 | 2026-05-24 | Codex | **Skill 激活与交付边界优化**。同步 `SKILL.md`、`skill.json`、README 与术语表元数据；主文件加入五维评分摘要；默认将路由、评分和自检作为内部步骤；补充去 AI 味与 benchmark 校准短例；压缩重复红线，并修复测试中 HTML 注释断言位置。 |
| v5.4.0 | 2026-04-24 | GitHub Copilot | **加入“去 AI 味”启发式自动门槛**。新增 `scripts/check_ai_tone.py`，将模板腔、生成式转场、教学控制句、作者在场感和模板化标题中的高频信号转成可执行检查；支持单文件、目录、JSON 输出与 `--strict` 阻断模式。`ci/check-docs.yml` 新增“去 AI 味门槛检查”步骤；README 补齐 references / scripts 目录结构并加入脚本用法。目标：把“自然表达”从纯人工经验推进到“规则 + 脚本 + CI”闭环。 |
| v5.3.0 | 2026-04-24 | GitHub Copilot | **加入“去 AI 味但不降分”工作流**。SKILL.md 新增自然表达优先级说明、`Step 4.5 去 AI 味回路`、2 条必须规则、3 条禁止规则、2 条自检项；`references/commands.md` 为四个命令加入去模板腔 / 去机械翻译 / 去作者在场感的后处理步骤；`references/quality.md` 将自然表达并入可读性与教学性评分，新增“去 AI 味门槛（不新增维度）”，规定未通过门槛时可读性封顶 20/25、总分不超过 89；`skill.json` 同步更新描述与版本。目标：保留结构、准确性、教学性、实用性，同时让文档在通过门槛时仍可拿满分 100。 |
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
