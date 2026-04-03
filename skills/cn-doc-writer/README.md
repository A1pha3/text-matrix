# cn-doc-writer

> 专业级中文技术文档编写 Skill — v5.1.0

## 功能概述

为 AI 助手提供中文技术文档的**编写、翻译、优化、教学增强**全流程能力。

### 四个命令

| 命令 | 用途 |
| ------ | ------ |
| `write-cn-doc` | 从零编写中文技术文档（自动路由：快速/标准/完整模式） |
| `translate-cn` | 将英文文档翻译成中文（前分析 → 翻译 → 后校验） |
| `optimize-cn-doc` | 优化现有文档（诊断 → 改进 → 量化评估） |
| `enhance-learning` | 添加学习元素（目标、练习、评估、路径） |

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
│   ├── templates.md            # 四级文档模板 + 快速模板
│   ├── learning-paths.md       # 三条学习路径指南
│   ├── tools.md                # 路径规划工具集
│   ├── terminology.json        # 术语表（Single Source of Truth）
│   └── terminology.md          # 术语表可读版（自动生成）
├── scripts/                    # 工具层
│   ├── utils.py                # 共享工具模块
│   ├── check_format.py         # 格式检查 + 自动修复
│   ├── pre_translate.py        # 翻译前分析
│   ├── post_translate.py       # 翻译后校验
│   ├── gen_terminology_md.py   # 从 JSON 生成 terminology.md
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

### 运行测试

```bash
cd scripts
python -m pytest test_scripts.py -v
# 或
python test_scripts.py
```

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
│  格式检查 · 翻译分析 · 翻译校验 · 生成   │
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

完整版本历史见 [CHANGELOG.md](CHANGELOG.md)。

| 版本 | 变更 |
| ------ | ------ |
| v5.1.0 | 核心 SKILL 重构为更清晰的 3 段路由、命令级按需加载表、原子化约束和异常恢复策略；同步 skill.json、README 与版本元数据。 |
| v3.7.0 | 代码修复（inline code/LaTeX 误报、变长围栏、CI 注入）、语气框架、发布门槛、增量模式约束、§3.6 文档治理、术语表 216 条（+5 新分类）、4 新模板（Changelog/迁移/故障排除/ADR）、反馈闭环 §1.10，测试 105→126 |
| v3.6.0 | Prompt（提示词）缓存/上下文管理策略（§2.0）、文档增量更新模式（§2.0.1）、多模型适配提示（§2.0.2）、可读性量化指标（`check_readability`）、CI/CD（持续集成/持续部署）集成模板（`ci/check-docs.yml`）、`--readability` CLI（命令行工具）参数 |
| v3.5.0 | AI 角色定义、自检循环、智能任务识别、跨文档检查、`is_in_inline_code` 多反引号支持、`_add_space` 保护行内代码/URL、`post_translate` 统一 `should_skip`、`pre_translate` 变长围栏修复、极端场景测试、版本号统一，测试 70→85+ |
| v3.4.0 | CommonMark 波浪号(~)围栏完整支持、修复 `is_in_latex` bug、消除 `post_translate` 死代码、新增 documentation 术语领域、测试 58→70 |
| v3.1.0 | 提取共享 utils.py、添加 gen_terminology_md.py、tools.md Mermaid 化、添加 README |
| v3.0.0 | 重大重构：执行指令、场景路由、量化评估、术语 JSON 单源、翻译脚本拆分、模板去重 |
| v2.3.0 | 精简主文档、删除冗余、消除重复 |

## 许可证

内部使用。
