---
title: "Agent Skills：AI Agent 能力扩展开放规范完全指南"
date: 2026-04-02T17:49:04+08:00
slug: "agent-skills-ai-agent-open-specification-guide"
description: "Agent Skills 是 Anthropic 主导的 AI Agent 能力扩展开放规范。本文详细介绍了 Skill 格式、工作原理、渐进式披露机制，以及如何创建、评估和部署生产级 Skill。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Anthropic", "Skill 扩展", "开放规范", "渐进式披露"]
---

# Agent Skills：AI Agent 能力扩展开放规范完全指南

## 学习目标

学完本指南后，你将掌握以下核心技能：

1. **理解 Agent Skills 核心概念**：理解什么是 Skill、为什么需要 Skill 扩展、以及 Agent Skills 与传统工具调用的区别
2. **掌握 Skill 格式规范**：熟练编写符合规范的 SKILL.md 文件，理解 frontmatter 字段的约束条件
3. **能够创建生产级 Skill**：从零创建一个功能完整的 Skill，包括指令、脚本和参考资料
4. **理解 Skill 工作原理**：深入理解 discovery、activation、progressive disclosure 的内部机制
5. **集成到 AI Agent 系统**：学会在任何兼容 Agent Skills 的系统中添加 Skill 支持
6. **遵循最佳实践**：掌握 Skill 描述优化、评估和迭代的方法论

---

## 一、项目概述

### 1.1 什么是 Agent Skills

**Agent Skills** 是由 Anthropic 主导的一个**开放规范**（open format），用于为 AI Agent 动态添加新的能力和专业知识。Skills 是包含指令、脚本和资源的文件夹，AI Agent 可以在运行时发现并使用这些 Skill 来更好地完成特定任务。

官网地址：[https://agentskills.io](https://agentskills.io)
规范文档：[https://agentskills.io/specification](https://agentskills.io/specification)

GitHub 仓库：**agentskills/agentskills**（14.8k Stars，Anthropic 官方维护）

```bash
# 官方示例 Skill 库
anthropics/skills（109k Stars，12.2k Forks）
```

### 1.2 核心设计理念

Agent Skills 的诞生源于一个关键洞察：**传统工具调用的局限性**。在传统架构中，Agent 需要预先编译所有可能的工具能力，这导致：

- **能力膨胀**：Agent 体积随工具数量线性增长
- **上下文污染**：每次调用都加载所有工具描述
- **跨平台困难**：不同 Agent 实现各自的工具格式，互不兼容

Agent Skills 通过以下设计解决这些问题：

| 特性 | 传统工具调用 | Agent Skills |
|------|-------------|--------------|
| 能力加载时机 | 启动时全部加载 | 按需渐进式加载 |
| 上下文开销 | O(n)，n=工具数 | O(1)，仅加载激活的 Skill |
| 跨平台性 | 平台锁定 | 开放格式，一次编写处处运行 |
| 能力扩展 | 需修改核心代码 | 只需添加 Skill 文件夹 |

### 1.3 项目生态

```
┌─────────────────────────────────────────────────────────┐
│                    Agent Skills 生态                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────┐    ┌─────────────────────────┐    │
│  │  Specification  │    │   Official Repository    │    │
│  │  (规范定义)     │    │   agentskills/agentskills│   │
│  │  agentskills.io │    │   (14.8k Stars)         │    │
│  └────────┬────────┘    └────────────┬────────────┘    │
│           │                              │                │
│           ▼                              ▼                │
│  ┌─────────────────┐    ┌─────────────────────────┐    │
│  │   skills-ref    │    │   Example Skills       │    │
│  │  (Python SDK)   │    │   anthropics/skills    │    │
│  │  验证/读取/转换 │    │   (109k Stars)         │    │
│  └────────┬────────┘    └────────────┬────────────┘    │
│           │                              │                │
│           ▼                              ▼                │
│  ┌─────────────────────────────────────────────┐         │
│  │           兼容的 Agent 实现                  │         │
│  │  Claude Code │ Claude.ai │ OpenAI Codex │   │         │
│  │  VS Code Copilot │ 其他兼容实现              │         │
│  └─────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────┘
```

### 1.4 技术规格

| 指标 | 数值 |
|------|------|
| 规范版本 | v1.0 |
| 主仓库 Stars | 14,837 |
| 示例库 Stars | 108,862 |
| Forks | 871（主仓库）/ 12,170（示例库） |
| 贡献者 | 35 人（主仓库）|
| 最新提交 | 2026-03-28 |
| 许可证 | Apache-2.0 |
| 主要语言 | Python 99.1%, Shell 0.9% |

---

## 二、Skill 格式规范

### 2.1 目录结构

一个 Skill 本质上是一个文件夹，至少包含一个 `SKILL.md` 文件：

```bash
skill-name/
├── SKILL.md          # 必需：元数据 + 指令
├── scripts/          # 可选：可执行脚本
├── references/       # 可选：参考资料文档
├── assets/           # 可选：静态资源（模板、图片、数据文件）
└── ...               # 任意其他文件或目录
```

**命名约束**：
- Skill 目录名必须与 `SKILL.md` 中的 `name` 字段完全一致
- 只能包含小写字母（a-z）、数字（0-9）和连字符（-）
- 不能以连字符开头或结尾
- 不能包含连续两个连字符（--）

### 2.2 SKILL.md 格式

`SKILL.md` 采用 **YAML frontmatter + Markdown body** 的混合格式：

```yaml
---
name: pdf-processing
description: 提取 PDF 文本和表格、填写表单、合并文件。当处理 PDF 文档或用户提到 PDF、表单、文档提取时使用。
license: Apache-2.0
compatibility: 需要 Python 3.10+ 和 pdfplumber 库
metadata:
  author: example-org
  version: "1.0"
allowed-tools: Bash(python:*) Read
---

# PDF 处理 Skill

[你的指令内容...]
```

### 2.3 Frontmatter 字段详解

| 字段 | 必需 | 约束条件 |
|------|------|----------|
| `name` | **是** | 最多 64 字符，仅小写字母、数字、连字符 |
| `description` | **是** | 最多 1024 字符，描述 Skill 功能和激活时机 |
| `license` | 否 | 许可证名称或对打包许可证文件的引用 |
| `compatibility` | 否 | 最多 500 字符，说明环境要求 |
| `metadata` | 否 | 任意键值对，用于额外元数据 |
| `allowed-tools` | 否 | 空格分隔的预批准工具列表（实验性）|

#### name 字段规则

```yaml
# ✅ 合法示例
name: pdf-processing
name: data-analysis
name: code-review

# ❌ 非法示例
name: PDF-Processing      # 不能大写
name: -pdf                # 不能以连字符开头
name: pdf--processing     # 不能有连续连字符
```

#### description 字段最佳实践

```yaml
# ✅ 优秀描述：包含功能+激活时机+关键词
description: 提取 PDF 文本和表格、填写表单、合并多个 PDF。当处理 PDF 文档、填写表单或文档提取时使用。

# ❌ 差劲描述：信息不足
description: Helps with PDFs.
```

### 2.4 Body 内容

Markdown body 包含 Agent 激活 Skill 时执行的指令，**没有格式限制**。建议包含以下部分：

- **逐步指令**：清晰的操作步骤
- **输入输出示例**：具体的使用案例
- **边界情况处理**：错误处理和特殊情况

```markdown
## 使用步骤

1. 安装依赖：`pip install pdfplumber`
2. 使用 `pdfplumber.extract_text()` 提取文本
3. 使用 `pdfplumber.extract_tables()` 提取表格

## 示例

**输入**：`path/to/document.pdf`
**输出**：`{"text": "...", "tables": [...]}`

## 注意事项

- 扫描版 PDF 需要先 OCR
- 加密 PDF 需要先解密
```

---

## 三、Skill 工作原理

### 3.1 渐进式披露（Progressive Disclosure）

Agent Skills 的核心机制是**渐进式披露**，这是一种优化上下文使用的策略：

```
┌──────────────────────────────────────────────────────────┐
│                    渐进式披露流程                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  阶段 1：元数据（~100 tokens）                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │ name + description                                 │  │
│  │ 启动时加载，用于快速匹配和过滤                    │  │
│  └────────────────────────────────────────────────────┘  │
│                          │                               │
│                          ▼                               │
│  阶段 2：指令（< 5000 tokens，推荐）                     │
│  ┌────────────────────────────────────────────────────┐  │
│  │ SKILL.md body                                      │  │
│  │ 激活时加载，完整执行指令                           │  │
│  └────────────────────────────────────────────────────┘  │
│                          │                               │
│                          ▼                               │
│  阶段 3：资源（按需加载）                               │
│  ┌────────────────────────────────────────────────────┐  │
│  │ scripts/、references/、assets/                     │  │
│  │ 仅当执行到相关部分时才加载                         │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 3.2 Discovery（发现）机制

当 Agent 启动时，会执行 Discovery 阶段：

1. **扫描 Skill 目录**：默认扫描 `.agents/skills/`
2. **读取元数据**：仅读取 `name` 和 `description` 字段
3. **构建索引**：将所有 Skill 的元数据加入可用 Skill 列表
4. **等待激活**：仅保存索引，不加载完整内容

```bash
# 默认 Skill 目录结构
project/
├── .agents/
│   └── skills/           # 默认扫描此目录
│       ├── roll-dice/
│       │   └── SKILL.md
│       ├── pdf-processing/
│       │   └── SKILL.md
│       └── ...
```

### 3.3 Activation（激活）机制

当用户请求触发某个 Skill 时：

1. **匹配判断**：Agent 将用户请求与所有 Skill 的 `description` 匹配
2. **加载指令**：将匹配的 Skill 的完整 `SKILL.md` 加载到上下文
3. **执行指令**：Agent 按照指令执行任务
4. **按需加载资源**：执行过程中需要时，再加载 `scripts/`、`references/` 等

### 3.4 实际执行示例

以 VS Code + GitHub Copilot 为例：

```bash
# 1. 用户在 Copilot Chat 中输入
/Roll a d20

# 2. Copilot 发现 roll-dice skill 的 description 匹配
"Roll dice using a random number generator..."

# 3. 激活 Skill，加载完整 SKILL.md

# 4. 执行技能指令
# Agent 执行：echo $((RANDOM % 20 + 1))
# 返回：15
```

---

## 四、快速入门

### 4.1 环境准备

**前置条件**：
- VS Code
- GitHub Copilot 扩展（或其他兼容 Agent）

**安装命令**：

```bash
# 克隆 skills-ref 库
git clone https://github.com/agentskills/agentskills.git
cd agentskills/skills-ref

# 使用 uv 安装（推荐）
uv pip install skills-ref

# 或使用 pip
pip install skills-ref
```

### 4.2 创建第一个 Skill

**目标**：创建一个投骰子的 Skill

**步骤 1**：创建 Skill 目录

```bash
mkdir -p .agents/skills/roll-dice
```

**步骤 2**：编写 SKILL.md

```yaml
---
name: roll-dice
description: 使用随机数生成器投骰子。当被问到投骰子（d6、d20 等）、
             roll dice 或生成随机骰子点数时使用。
---

# 投骰子指令

## 使用方法

投掷任意面数的骰子，使用以下命令生成 1 到指定面数之间的随机数：

### Bash（Linux/macOS）
```bash
echo $((RANDOM % <sides> + 1))
```

### PowerShell（Windows）
```powershell
Get-Random -Minimum 1 -Maximum (<sides> + 1)
```

## 参数说明

- `<sides>`：骰子的面数
  - d6：`<sides>` = 6
  - d20：`<sides>` = 20
  - d100：`<sides>` = 100

## 示例

**请求**："Roll a d20"
**命令**：`echo $((RANDOM % 20 + 1))`
**结果**：返回 1-20 之间的随机整数
```

### 4.3 验证 Skill

```bash
# 使用 skills-ref 验证 Skill 格式
skills-ref validate .agents/skills/roll-dice
```

### 4.4 在 Agent 中使用

1. 打开 VS Code，进入 Copilot Chat
2. 选择 **Agent** 模式
3. 输入 `/skills` 确认 Skill 已注册
4. 输入 "Roll a d20"
5. Agent 自动激活 `roll-dice` Skill 并执行

---

## 五、skills-ref 参考库

### 5.1 简介

`skills-ref` 是 Agent Skills 官方提供的 Python 参考库，提供：

- **Skill 验证**：检查 SKILL.md 格式是否符合规范
- **属性读取**：提取 Skill 的 frontmatter 字段
- **Prompt 生成**：将 Skill 转换为适合 LLM 的 prompt 格式

GitHub：[https://github.com/agentskills/agentskills/tree/main/skills-ref](https://github.com/agentskills/agentskills/tree/main/skills-ref)

### 5.2 CLI 命令

```bash
# 验证 Skill 格式
skills-ref validate ./my-skill

# 读取 Skill 属性
skills-ref read-properties ./my-skill

# 生成 prompt
skills-ref to-prompt ./my-skill
```

### 5.3 Python API（基于通用模式推断）

skills-ref 包的 Python API 遵循典型的验证库模式。根据 CLI 命令和目录结构，可以推断其 Python API 形式如下（建议参考官方文档确认）：

```python
# 安装：pip install skills-ref
# 导入（包名在 pip 安装后可能转为下划线）
try:
    from skills_ref import validate, read_properties, to_prompt
except ImportError:
    from skills_ref_python as skills_ref  # 可能的替代导入

# 验证 Skill 格式
result = validate("./my-skill")
print(result.is_valid)  # True/False
if not result.is_valid:
    print(result.errors)     # 错误列表

# 读取属性
props = read_properties("./my-skill")
print(props.name)        # "my-skill"
print(props.description)  # "A description..."

# 生成 prompt（供 LLM 使用）
prompt = to_prompt("./my-skill")
print(prompt)  # 格式化的 prompt 字符串
```

**注意**：上述 API 为基于通用模式的推断。建议在实际使用前查阅 [skills-ref 官方文档](https://github.com/agentskills/agentskills/tree/main/skills-ref) 确认准确的 API 签名。

---

## 六、高级用法

### 6.1 脚本集成

Skill 可以包含可执行脚本，扩展其能力。脚本应：

- 保持自包含，或清晰文档化依赖
- 包含有用的错误信息
- 优雅处理边界情况

**目录结构示例**：

```bash
git-analysis/
├── SKILL.md
└── scripts/
    └── analyze.py    # 可执行的分析脚本
```

**SKILL.md 示例**：

```yaml
---
name: git-analysis
description: 分析 Git 仓库的提交历史、贡献者统计和代码变更。
---

## 使用分析脚本

运行 scripts/analyze.py 进行深度分析：

Bash 命令：
echo "请在 Skill 激活后使用以下命令："
echo "python scripts/analyze.py --repo ./ --format json"
```

**输出格式**（JSON）：

```json
{
  "total_commits": 1234,
  "contributors": 42,
  "top_contributors": [...]
}
```
```

目录结构：

```bash
git-analysis/
├── SKILL.md
└── scripts/
    └── analyze.py    # 可执行的分析脚本
```

### 6.2 参考资料分离

对于大型 Skill，建议将详细参考文档分离到 `references/` 目录：

```bash
pdf-processing/
├── SKILL.md
├── scripts/
│   ├── extract_text.py
│   └── extract_tables.py
└── references/
    ├── API_REFERENCE.md    # 详细的 API 文档
    ├── FORMATS.md         # 支持的 PDF 格式
    └── EXAMPLES.md        # 更多示例
```

在 SKILL.md 中引用：

```markdown
## 详细 API

请参阅 [API 参考文档](references/API_REFERENCE.md) 获取完整的函数签名。

## 示例

更多示例请查看 [示例集](references/EXAMPLES.md)。
```

### 6.3 资源管理

`assets/` 目录用于存储静态资源：

```bash
document-generator/
├── SKILL.md
└── assets/
    ├── templates/          # 文档模板
    │   ├── report.md
    │   └── memo.md
    ├── images/            # 示例图片
    │   └── flowchart.png
    └── data/             # 数据文件
        └── config.json
```

### 6.4 条件兼容性

使用 `compatibility` 字段声明环境要求：

```yaml
---
name: docker-deployment
description: 自动化 Docker 容器部署。当需要构建镜像、部署容器或管理 Docker 环境时使用。
compatibility: 需要 Docker daemon 运行、docker 和 docker-compose 命令可用
---
```

---

## 七、最佳实践

### 7.1 Skill 描述优化

**原则 1：包含触发关键词**

```yaml
# ✅ 包含多种触发方式
description: 提取 PDF 文本和表格、填写 PDF 表单、合并多个 PDF。
             当用户提到 PDF、表单、文档提取、文本提取时激活。

# ❌ 缺少触发词
description: 提取文档内容。
```

**原则 2：明确激活时机**

```yaml
# ✅ 清晰说明使用场景
description: 当需要创建符合公司品牌规范的文档（报告、备忘录、邮件）时使用。
             包含公司徽标、配色方案、字体要求。

# ❌ 模糊不清
description: 帮助创建文档。
```

**原则 3：保持简洁**

description 应控制在 1024 字符以内，优先使用主动语态：

```yaml
# ✅ 简洁主动
description: 验证 API 响应是否符合 OpenAPI 规范。当需要测试 API、
             验证 JSON 响应或检查 REST 端点时使用。

# ❌ 冗长被动
description: 这个 Skill 可以被用来进行 API 相关的验证工作，
             它将会检查输入的 JSON 数据是否...
```

### 7.2 指令编写规范

**保持 SKILL.md 在 500 行以内**

```markdown
# ✅ 精简指令（< 500 行）

## 核心功能
[2-3 句话概括]

## 使用方法
1. 步骤 1
2. 步骤 2

## 示例
[2-3 个典型案例]

## 注意事项
[关键边界情况]

# ❌ 冗长指令
[将详细参考全部写入 SKILL.md]
```

**分离详细参考文档**

```markdown
# SKILL.md - 仅保留摘要

## 功能
计算并验证国际标准书号（ISBN-10 和 ISBN-13）。

## 使用
1. 使用 `scripts/validate_isbn.py <isbn>`
2. 脚本返回验证结果

## 示例
- `python scripts/validate_isbn.py 0-306-40615-2` → 有效

## 详细参考
见 `references/isbn_standard.md`
```

### 7.3 评估与迭代

**评估维度**：

| 维度 | 指标 | 评估方法 |
|------|------|----------|
| 激活准确率 | 相关请求中 Skill 被正确激活的比例 | 日志分析 |
| 完成率 | 激活后任务成功完成的比例 | 用户反馈 |
| 上下文效率 | 平均使用的 token 数量 | 埋点统计 |
| 错误率 | 执行过程中的错误频率 | 监控告警 |

**迭代流程**：

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  编写   │───▶│  测试   │───▶│  评估   │───▶│  发布   │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
     │             │             │             │
     ▼             ▼             ▼             ▼
  初步实现    单元测试       A/B 测试      版本发布
            集成测试       用户反馈      监控迭代
```

---

## 八、开发扩展

### 8.1 创建兼容 Agent

如果你正在开发一个 AI Agent 系统，可以通过以下步骤添加 Agent Skills 支持：

**步骤 1：实现 Discovery**

```python
import os
from pathlib import Path
from typing import List, Dict

def discover_skills(skills_dir: Path) -> List[Dict[str, str]]:
    """发现目录中的所有 Skills"""
    skills = []
    
    for skill_path in skills_dir.iterdir():
        if not skill_path.is_dir():
            continue
            
        skill_md = skill_path / "SKILL.md"
        if not skill_md.exists():
            continue
        
        # 读取 frontmatter
        frontmatter = parse_frontmatter(skill_md.read_text())
        
        skills.append({
            "name": frontmatter.get("name"),
            "description": frontmatter.get("description"),
            "path": str(skill_path)
        })
    
    return skills
```

**步骤 2：实现 Activation**

```python
def activate_skill(skill_path: Path) -> str:
    """加载完整 Skill 内容"""
    skill_md = skill_path / "SKILL.md"
    return skill_md.read_text()
```

**步骤 3：实现渐进式加载**

```python
def load_skill_resources(skill_path: Path, resource_path: str) -> str:
    """按需加载 Skill 资源"""
    full_path = skill_path / resource_path
    if full_path.exists():
        return full_path.read_text()
    return ""
```

### 8.2 工具预批准机制

`allowed-tools` 字段允许 Skill 定义可使用的预批准工具：

```yaml
---
name: git-workflow
description: 执行标准 Git 工作流程。用于提交代码、创建分支、合并请求等。
allowed-tools: Bash(git:*) Bash(gh:*) Read
---

# Git 工作流 Skill

## 创建分支并提交

1. 使用 `gh auth` 验证 GitHub CLI
2. 执行 `git checkout -b feature/new-feature`
3. 执行 `git add . && git commit -m "feat: add new feature"`
```

### 8.3 Skill 市场集成

发布 Skill 到市场的标准流程：

1. **创建独立仓库**：`my-skill/` 格式
2. **添加 LICENSE**：明确许可证
3. **编写 README**：说明用途和使用方法
4. **提交到市场**：通过 GitHub PR 或社区提名

---

## 九、使用场景

### 9.1 企业内部工具

**场景**：为团队创建统一的代码审查 Skill

```yaml
---
name: enterprise-code-review
description: 按照公司安全规范进行代码审查。检查 SQL 注入、XSS、
             敏感信息暴露等安全问题。当需要进行代码审查、
             安全扫描或合规检查时激活。
compatibility: 需要 SonarQube CLI 和公司安全规则库
metadata:
  team: security
  tier: critical
---

# 企业代码审查 Skill

## 安全检查清单

- [ ] SQL 注入防护
- [ ] XSS 输出编码
- [ ] 敏感信息加密存储
- [ ] API 限流实现
```

### 9.2 领域专家助手

**场景**：创建法律文档分析 Skill

```yaml
---
name: contract-analysis
description: 分析商业合同条款，识别风险点。用于审阅采购合同、
             服务协议、劳动合同等。当用户提到合同审查、
             法律风险或条款分析时激活。
---

# 合同分析 Skill

## 风险识别

### 高风险条款
1. 无限责任条款
2. 竞业禁止过宽
3. 违约金不成比例

### 红旗标志
- "乙方自愿放弃一切诉讼权利"
- "甲方有权随时解除合同"
```

### 9.3 自动化工作流

**场景**：CI/CD 流水线 Skill

```yaml
---
name: ci-pipeline-debug
description: 诊断和修复 CI/CD 流水线问题。用于 GitHub Actions、
             GitLab CI 或 Jenkins 构建失败排查。当构建失败、
             流水线报错或部署问题时激活。
allowed-tools: Bash(git:*) Bash(docker:*) Read
---

# CI/CD 调试 Skill

## 诊断流程

1. 读取 `.github/workflows/*.yml`
2. 分析错误日志
3. 定位问题步骤
4. 提供修复建议
```

---

## 十、FAQ

### Q1：Skill 和普通的系统提示词有什么区别？

**核心区别**在于**动态性和可组合性**：

| 特性 | 系统提示词 | Agent Skills |
|------|-----------|--------------|
| 加载时机 | 固定加载 | 按需激活 |
| 上下文影响 | 全局污染 | 局部隔离 |
| 复用性 | 平台锁定 | 开放格式 |
| 版本管理 | 需修改代码 | 只需增删文件 |

### Q2：一个 Agent 可以同时激活多个 Skill 吗？

**可以**，但建议控制并发激活的 Skill 数量以优化上下文使用。通常：

- **简单任务**：1 个 Skill
- **复杂任务**：2-3 个相关 Skill
- **避免**：5+ 个 Skill 同时激活（上下文膨胀）

### Q3：Skill 的 token 开销是多少？

估算如下：

| 阶段 | 平均 Token | 触发时机 |
|------|-----------|----------|
| 元数据 | ~100 | 每次启动 |
| 指令 | ~500-2000 | 每次激活 |
| 资源 | 按需 | 执行中 |

### Q4：如何处理 Skill 之间的冲突？

**设计原则**：Skill 应该是**互补而非竞争**的。

如果存在冲突：
1. **优先级**：在 description 中明确使用范围
2. **互斥标识**：在 metadata 中添加 `conflicts-with` 字段
3. **Agent 决策**：让 Agent 根据上下文选择更合适的 Skill

### Q5：可以使用哪些脚本语言？

**取决于 Agent 实现**。常见支持：

- **Bash/PowerShell**：系统命令
- **Python**：通用脚本
- **JavaScript/Node**：Web 相关任务
- **Go**：高性能工具

### Q6：Skill 可以访问网络吗？

**取决于具体实现和 `compatibility` 设置**。

```yaml
# 声明网络需求
compatibility: 需要互联网访问，用于调用外部 API
```

---

## 十一、总结

### 核心要点

1. **Agent Skills 是开放规范**：由 Anthropic 主导，已获广泛支持
2. **渐进式披露**：通过分层加载优化上下文使用
3. **一次编写多处运行**：VS Code、Claude.ai、API 等全面兼容
4. **零成本扩展**：无需修改 Agent 核心代码即可添加能力

### 生态现状

- **官方库**：agentskills/agentskills（14.8k Stars）
- **示例库**：anthropics/skills（109k Stars）
- **社区**：Discord 服务器 + GitHub Discussions
- **文档**：agentskills.io（Mintlify 托管）

### 参与贡献

```bash
# 克隆官方仓库
git clone https://github.com/agentskills/agentskills.git

# 创建新 Skill
cd skills-ref/skills/
mkdir my-new-skill
cd my-new-skill
touch SKILL.md

# 提交 PR
git checkout -b feature/my-new-skill
git add .
git commit -m "feat: add my-new-skill"
git push origin feature/my-new-skill
```

---

## 相关链接

| 资源 | 地址 |
|------|------|
| 官网 | [https://agentskills.io](https://agentskills.io) |
| 规范文档 | [https://agentskills.io/specification](https://agentskills.io/specification) |
| 快速入门 | [https://agentskills.io/skill-creation/quickstart](https://agentskills.io/skill-creation/quickstart) |
| GitHub 主仓库 | [https://github.com/agentskills/agentskills](https://github.com/agentskills/agentskills) |
| 示例 Skill 库 | [https://github.com/anthropics/skills](https://github.com/anthropics/skills) |
| Discord 社区 | [https://discord.gg/MKPE9g8aUy](https://discord.gg/MKPE9g8aUy) |

---

*🦞 文档版本：2026-04-02 | 规范版本：v1.0 | 来源：[agentskills/agentskills](https://github.com/agentskills/agentskills)*
