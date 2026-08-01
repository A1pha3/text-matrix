# cn-doc-writer

> 专业级中文技术写作 Skill（文档 / 博客 / 视频解析 / 随笔） — v6.0.0

## 功能概述

为 AI 助手提供中文技术内容的**编写、翻译、优化、教学增强**全流程能力：技术文档、项目解读博客、视频解析、思想随笔共用同一条管线与去 AI 味回路，文体差异由 `references/styles/` 文体包按读者契约注入。

## 新增能力：主副本同步防漂移

- `prompt_alpha` 下的智能体（代理）技能路径 `agent/skills/my-skills/cn-doc-writer` 是主版本。
- `text-matrix/skills/cn-doc-writer` 只作为副本，根据主版本同步。
- 所有修改先落在主版本；同步后用 `scripts/check_skill_sync.py` 检查缺失、多余和内容不同的文件。
- 防漂移检查忽略 `__pycache__`、`.pytest_cache`、`.pyc` 等本地缓存，不隐藏真实文档、脚本或配置差异。
- `ci/check-docs.yml` 已接入可选 CI 防漂移步骤；配置 `CN_DOC_WRITER_SOURCE_DIR` 和 `CN_DOC_WRITER_TARGET_DIR` 后，PR 会在副本漂移时失败。

## 文体包架构

- 路由键是读者契约而非主题：带任务来 → `styles/doc.md`；带好奇来 → `styles/project-review.md`；转写稿成文 → `styles/video-digest.md`；要观点视角 → `styles/essay.md`。
- 每个文体包 = frontmatter 参数头（triggers / reader / band / gates）+ 手艺正文；`band` 与 `gates` 只能引用 `quality.md` 已注册的权重档与门槛。
- 四个命令 × 四个文体包正交组合，全部复用同一去 AI 味回路与分档评分。

## 新增能力：去 AI 味但不降分

- 采用三维评分体系（正确性、清晰度、实用性），权重随文体包分档（默认 30%/40%/30%），可读性作为一票否决门槛。
- "自然表达"不单独评分，作为可读性门槛处理，拿到 A/S 级乃至满分 100 的强制门槛。
- 所有命令都增加去 AI 味后处理步骤，但前提是先锁定事实、结构、术语与教学路径。
- 使用 `write-cn-doc` 或 `optimize-cn-doc` 时会默认自动调用去 AI 味回路，不需要用户额外提出。
- 去 AI 味后必须复评分；如果分数下降，则回滚低效润色，不用“更像人写的”换取信息损失。
- 重点治理对象包括：模板腔、生成式转场、自我声明堆积、标签化教学块、机械对称列表、过强作者在场感。
- 新增启发式脚本与 CI 接口，可对高频 AI 味信号做本地检查，不再完全依赖人工复核。

### 四个命令

| 命令 | 用途 |
|------|------|
| `write-cn-doc` | 从零编写中文技术文档（自动路由：快速/标准/完整模式；自动调用去 AI 味回路并复评分） |
| `translate-cn` | 将英文文档翻译成中文（前分析 → 翻译 → 去机械翻译/去 AI 味校验） |
| `optimize-cn-doc` | 优化现有文档（诊断 → 改进 → 自动调用去 AI 味回路 → 默认简版报告；发布级审查再展开完整评分表） |
| `enhance-learning` | 添加学习元素（目标、练习、评估、路径，并自然融入正文） |

### 三种模式

- **快速模式**：单页文档（README、API（应用程序接口）文档、代码注释）
- **标准模式**：多章节教程（选择路径和级别）
- **完整模式**：文档体系规划（路径 × 级别 × 评估）

## 文件结构

```text
cn-doc-writer/
├── SKILL.md                    # 核心指令（加载即生效）
├── skill.json                  # Skill 元数据
├── README.md                   # 本文件
├── references/                 # 知识层
│   ├── styles/                 # 文体包（frontmatter 参数头 + 手艺正文）
│   │   ├── doc.md              # 技术文档：教程 / 参考 / README
│   │   ├── project-review.md   # 项目解读 / 架构分析 / benchmark 解读
│   │   ├── video-digest.md     # 视频 / 演讲转写稿成文
│   │   └── essay.md            # 思想随笔 / 观点文章
│   ├── commands.md             # 命令执行流程
│   ├── quality.md              # 评分标准、权重档与门槛注册表、发布门槛
│   ├── examples.md             # 语气与正反例
│   ├── behavior-fixtures.md    # Skill 行为压测场景
│   ├── edge-cases.md           # 边界与恢复策略
│   ├── knowledge.md            # 教学框架与知识补充
│   ├── templates.md            # 四级文档模板 + 快速模板
│   ├── learning-paths.md       # 三条学习路径指南
│   ├── tools.md                # 路径规划工具集
│   ├── terminology.json        # 术语表（Single Source of Truth）
│   └── terminology.md          # 术语表可读版（自动生成）
├── scripts/                    # 工具层
│   ├── utils.py                # 共享工具模块
│   ├── check_format.py         # 格式检查 + 自动修复
│   ├── check_ai_tone.py        # AI 味门槛启发式检查
│   ├── pre_translate.py        # 翻译前分析
│   ├── post_translate.py       # 翻译后校验
│   ├── gen_terminology_md.py   # 从 JSON 生成 terminology.md
│   ├── check_skill_sync.py     # 主副本同步防漂移检查
│   └── test_scripts.py         # 单元测试
└── ci/                         # 集成层
    └── check-docs.yml          # GitHub Actions 文档检查模板
```

## 脚本使用

### 格式检查

```bash
# 检查单个文件
python scripts/check_format.py docs/guide.md

# 检查整个目录
python scripts/check_format.py docs/

# 自动修复（中英文空格 + 行尾空格）
python scripts/check_format.py docs/guide.md --fix
```

### AI 味门槛检查

```bash
# 检查单个文档是否存在明显模板腔 / 生成式转场 / 作者在场感
python scripts/check_ai_tone.py docs/guide.md

# 目录批量检查
python scripts/check_ai_tone.py docs/

# 作为阻断性检查使用
python scripts/check_ai_tone.py docs/guide.md --strict
```

### 翻译工作流

```bash
# 步骤 1：分析原文（生成翻译计划）
python scripts/pre_translate.py README.md

# 步骤 2：AI 翻译（使用 SKILL.md 指导）

# 步骤 3：校验译文
python scripts/post_translate.py README_CN.md
python scripts/post_translate.py README_CN.md --original README.md
```

### 术语表维护

```bash
# 编辑 references/terminology.json 后，重新生成 .md
python scripts/gen_terminology_md.py --write
```

### 主副本同步防漂移

```bash
python scripts/check_skill_sync.py \
  /path/to/prompt_alpha/agent/skills/my-skills/cn-doc-writer \
  /path/to/text-matrix/skills/cn-doc-writer
```

该命令只用于校验。若失败，以 `prompt_alpha` 主版本为准，把 `text-matrix` 副本同步到主版本当前状态。

如需接入 CI，在 `ci/check-docs.yml` 中配置：

```yaml
env:
  SCRIPTS_DIR: agent/skills/my-skills/cn-doc-writer/scripts
  CN_DOC_WRITER_SOURCE_DIR: agent/skills/my-skills/cn-doc-writer
  CN_DOC_WRITER_TARGET_DIR: skills/cn-doc-writer
```

如果主版本和副本位于不同仓库，需要先在 CI 中把两个仓库检出到同一个工作区，再把上述路径改成对应目录。

### 运行测试

```bash
cd scripts
python -m pytest test_scripts.py -v
# 或
python test_scripts.py
```

`references/behavior-fixtures.md` 只在评审、回归测试或优化本 skill 时加载；普通写作、翻译和文档优化任务不需要读取。

## 架构设计

```text
┌─────────────────────────────────────────┐
│         SKILL.md（执行层）               │
│  场景路由 → 命令流程 → 量化评估          │
└────────────────┬────────────────────────┘
                 │ 引用
┌────────────────▼────────────────────────┐
│         references/（知识层）             │
│  模板 · 路径 · 术语 · 工具               │
└────────────────┬────────────────────────┘
                 │ 数据源
┌────────────────▼────────────────────────┐
│         scripts/（工具层）               │
│  格式检查 · 翻译分析 · 翻译校验 · 同步校验 · 生成 │
└────────────────┬────────────────────────┘
                 │ 自动化
┌────────────────▼────────────────────────┐
│         ci/（集成层）                    │
│  GitHub Actions · PR 自动检查            │
└─────────────────────────────────────────┘
```

### 术语表 Single Source of Truth

所有术语数据统一存储在 `references/terminology.json`：

- `check_format.py` — 从 JSON 加载术语进行一致性检查
- `pre_translate.py` — 从 JSON 加载术语进行翻译分析
- `post_translate.py` — 从 JSON 加载术语进行校验
- `gen_terminology_md.py` — 从 JSON 生成人可读的 Markdown 版本
- `terminology.md` — **不要手工编辑**，由脚本自动生成

## 更新日志

见 [CHANGELOG.md](CHANGELOG.md)。

## 许可证

内部使用。
